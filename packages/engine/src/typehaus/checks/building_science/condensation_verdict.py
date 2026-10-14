"""One envelope surface's condensation verdict, derived once for the check and the displays.

The check (:mod:`.condensation`), the model.json payload the UI card reads and
``haus explain --card`` all ask the same question of a stack, so all three read this.
They used to disagree: the displays plotted the 99%-design-hour walk and badged its
crossing RISK while the check graded that walk as a screen only and passed the wall on the
monthly gate (EXT_2X6), or deferred it to R806.5 (ROOF). ``status`` here is the GATE's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.checks.building_science.glaser import (
    CondensationAnalysis,
    MonthlyAssessment,
    analyze_layers,
    analyze_layers_monthly,
    glaser_layers,
    layer_permeance_perms,
)
from typehaus.checks.code.unvented_roof import r806_5_compliance
from typehaus.model.assembly import Assembly, Layer
from typehaus.model.plan import Library

if TYPE_CHECKING:
    from typehaus.checks.registry import Preferences
    from typehaus.model.site import Site

R806_5_CHECK_ID = "code.R806_5_unvented_roof"


def r806_5_deferral_message(layers: tuple[Layer, ...] | list[Layer], assembly: Assembly | None,
                            library: Library, *, is_roof: bool) -> str | None:
    """Why the gate defers this roof to R806.5, or None when it does not.

    **A steady-state Glaser walk cannot grade an assembly sealed on its cold side.** Under a
    0-perm panel every plane inboard reads interior vapour pressure by construction — the
    correct limit of the method and a useless verdict. R806.5 items 5.1.1/5.1.3 replace the
    criterion: air-impermeable insulation bonded to the deck at the Table R806.5 R-value IS
    the condensation control. Earned, not assumed: only where the code check PASSES and the
    stack really has no drying path (a walk truncated at a vent plane still has something to
    say, and so does a stack whose outermost layer is not a barrier).
    """
    if not is_roof or assembly is None:
        return None
    result = r806_5_compliance(assembly, library)
    if not (result.deck_contact_insulation and result.complies):
        return None
    truncated = glaser_layers(list(layers))
    outermost = truncated[-1] if truncated else None
    if outermost is None or len(truncated) < len(layers):
        return None
    permeance = layer_permeance_perms(outermost, library)
    if permeance is None or permeance > 0.0:
        return None
    assert result.deck_contact_r is not None
    return (
        f"monthly gate (ISO 13788-style): the stack is sealed on its cold side by "
        f"{outermost.name} (0 perm), so a steady-state Glaser walk has no outward flux to "
        f"grade and reads every plane at interior vapour pressure by construction. "
        f"R806.5 item {result.item} replaces that criterion: R-{result.deck_contact_r:.1f} "
        f"of air-impermeable, Class {result.air_impermeable_class} insulation bonded to the "
        f"sheathing underside is the condensation control, and outward drying is not "
        f"required. Graded by {R806_5_CHECK_ID}"
    )


@dataclass(frozen=True)
class EnvelopeVerdict:
    """The gate (or its R806.5 deferral) and the cold-snap screen for one surface."""

    label: str
    gate: MonthlyAssessment | None
    deferral: str | None
    screen: CondensationAnalysis
    screen_boundary: str

    @property
    def status(self) -> str:
        """``deferred | unknown | risk | safe`` — the GATE's verdict, never the screen's."""
        if self.deferral is not None:
            return "deferred"
        if self.gate is None or not self.gate.analysis.known:
            return "unknown"
        return "risk" if self.gate.analysis.has_risk else "safe"

    @property
    def shown(self) -> CondensationAnalysis:
        """The profile a display plots: the worst month, or the screen when there is none."""
        if self.deferral is None and self.gate is not None:
            return self.gate.analysis
        return self.screen

    def as_dict(self) -> dict[str, object]:
        shown = self.shown.as_dict()
        screen = self.screen
        return {
            **shown,
            "assembly": self.label,
            "status": self.status,
            "gate_month": self.gate.month if self.gate is not None else None,
            "gate_boundary": self.gate.boundary if self.gate is not None else None,
            "deferred_to": R806_5_CHECK_ID if self.deferral is not None else None,
            "deferral": self.deferral,
            "screen": {
                "status": ("unknown" if not screen.known
                           else "risk" if screen.has_risk else "safe"),
                "crossing_layer": screen.crossing_layer,
                "crossing_fraction": screen.crossing_fraction,
                "crossing_description": screen.crossing_description,
                "boundary": self.screen_boundary,
            },
        }


def assess_layers(label: str, layers: tuple[Layer, ...] | list[Layer],
                  assembly: Assembly | None, library: Library, *, site: Site,
                  preferences: Preferences, is_roof: bool,
                  interior_relative_humidity: float | None = None) -> EnvelopeVerdict:
    """Gate + screen for one interior->exterior stack (lining included, untruncated).

    ``interior_relative_humidity`` is a humid room's design RH; None takes the house
    preferences — the design-hour value for the screen, the monthly value for the gate.
    """
    walked = glaser_layers(list(layers))
    heating = site.design_temp_heating
    temperature_f = heating.fahrenheit if heating is not None else None
    screen_rh = (interior_relative_humidity if interior_relative_humidity is not None
                 else preferences.interior_relative_humidity)
    gate_rh = (interior_relative_humidity if interior_relative_humidity is not None
               else preferences.monthly_interior_relative_humidity)
    # Every finding states its boundary condition: a Glaser crossing is only meaningful
    # against the design temperature and interior humidity that produced it.
    boundary = (f"{temperature_f:.0f} F design / {screen_rh:.0%} interior RH"
                if temperature_f is not None else "the design heating temperature")
    deferral = r806_5_deferral_message(layers, assembly, library, is_roof=is_roof)
    gate = None if deferral is not None else analyze_layers_monthly(
        label, walked, library, monthly_normals=site.monthly_normals,
        interior_setpoint_f=preferences.interior_setpoint_f,
        interior_relative_humidity=gate_rh,
    )
    screen = analyze_layers(
        label, walked, library, heating_design_temp_f=temperature_f,
        interior_setpoint_f=preferences.interior_setpoint_f,
        interior_relative_humidity=screen_rh,
        exterior_relative_humidity=preferences.exterior_relative_humidity,
    )
    return EnvelopeVerdict(label, gate, deferral, screen, boundary)
