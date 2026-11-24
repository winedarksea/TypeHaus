"""The balcony's loads that no tributary area carries, and the beam statics under the columns.

Three things live here because the four kinds that grade the balcony (``glulam_beam``,
``deck_post``, ``column_support``, ``column_head_joint``) must read ONE answer to each:

* **The deck basis, stated** (owner decision 5, 2026-11-22). The decks are designed on the
  Minnesota basis as adopted: 40 psf live + 10 psf dead, no snow, no drift. The owner's
  reasoning is wind-swept and elevated. That is a judgement about the site, so it is printed as
  the stated basis and listed under "not covered — owner"; **no snow path is built**.
  :func:`deck_basis_text` is the wording a criteria page prints.
* **The planters** (decision 6): over the beam lines only, on a dimensioned support bearing
  directly on the beam, so no planter weight enters decking or joists. The house authors the
  allowance (``preferences.toml [structural] balcony_planter``); its saturated weight is a
  DEAD load on the beam's back span, cased with a planter over neither beam, one, or both.
* **Beam statics** (review B-03). A beam on two bearings with overhangs does not split its
  load equally between its columns; :func:`column_statics` gives each column the reaction
  the beam's own statics put on it, dead and patterned live apart, planter apart.

**Oracle.** ``houses/catlin/notes/balcony_moment_columns.md`` §5b (beam statics), §20 (planter).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any

from typehaus.loads import DECK_DEAD_LOAD_PSF, DECK_LIVE_LOAD_PSF

#: The owner's stated basis for the two garden decks, verbatim in intent (decision 5).
DECK_BASIS_STATED = (
    f"Minnesota deck basis as adopted: {DECK_LIVE_LOAD_PSF:g} psf live + "
    f"{DECK_DEAD_LOAD_PSF:g} psf dead, no snow, no drift (IRC Table R301.5, with MN Rule "
    f"1309.0507's \"Live load = 40 psf\" footnote). The owner's reasoning is that the decks "
    f"are elevated and wind-swept, so occupancy live load and not snow is what they carry."
)
#: The porch curtains (owner, 2026-11-23): retractable soft goods, not wind-rated.
CURTAIN_OWNER_BASIS = (
    "The porch curtains are retractable soft goods and are NOT wind-rated. Owner basis: they "
    "are retracted and stowed above the curtain maker's rated wind speed (the specification: "
    "retract and stow before that wind), so the porch is OPEN for wind design and the curtains "
    "are not a wind-resisting element. No curtain load is carried by the balcony's joists, "
    "beams, columns, stems or head ties, and no internal pressure is taken under the sealed "
    "deck. The maker publishes no closed-in-wind load held here, so none is graded."
)
#: What that basis does not cover, for a "not covered — owner" list.
NOT_COVERED_OWNER = (
    "Snow on the balcony and porch decks, balanced or drifted against the house's south gable: "
    "the owner's judgement (wind-swept, elevated) is the stated basis; no snow load path is "
    "built into the joists, beams, columns or stems. ALSO NOT COVERED: the design neither "
    "relies on nor grades closed porch curtains in design wind (they are stowed, "
    "see the curtain basis); a reviewer may question reliance on an "
    "operable closure being retracted."
)

_PLANTER_KEYS = ("soil_width_in", "soil_depth_in", "soil_saturated_pcf", "box_and_support_plf")


@dataclass(frozen=True)
class PlanterAllowance:
    """One planter run over a beam line, per foot of beam."""

    soil_width_in: float
    soil_depth_in: float
    soil_saturated_pcf: float
    box_and_support_plf: float

    @property
    def soil_plf(self) -> float:
        return self.soil_width_in * self.soil_depth_in / 144.0 * self.soil_saturated_pcf

    @property
    def plf(self) -> float:
        return self.soil_plf + self.box_and_support_plf

    def describe(self) -> str:
        return (f"saturated planter over the beam: {self.soil_width_in:g}\" x "
                f"{self.soil_depth_in:g}\" of soil at {self.soil_saturated_pcf:g} pcf = "
                f"{self.soil_plf:.1f} plf, plus {self.box_and_support_plf:g} plf box and support "
                f"= {self.plf:.1f} plf on the back span")


def planter_allowance(ctx: Any) -> PlanterAllowance | None:
    """The house's planter allowance, or ``None`` where none is authored."""
    structural = getattr(getattr(ctx, "preferences", None), "structural", None)
    table = getattr(structural, "balcony_planter", None) or {}
    if not table or any(key not in table for key in _PLANTER_KEYS):
        return None
    return PlanterAllowance(**{key: float(table[key]) for key in _PLANTER_KEYS})


def deck_basis_text(ctx: Any) -> str:
    """The stated basis with the balanced-snow comparison, once, reconciled with the house's
    ``deck_snow_psf`` (the figure ``structural.deck_joist_span`` grades the table against)."""
    structural = getattr(getattr(ctx, "preferences", None), "structural", None)
    balanced = getattr(structural, "deck_balanced_snow_psf", None)
    authored = getattr(structural, "deck_snow_psf", None)
    text = DECK_BASIS_STATED
    if balanced is not None:
        text += (f" Comparison only, applied to no member: ASCE 7-16 §7.3 balanced flat-roof "
                 f"snow at the site's ground snow would be {balanced:g} psf, above the "
                 f"{DECK_LIVE_LOAD_PSF:g} psf live load.")
    if authored is not None:
        text += (f" (The joist-span table screen, IRC Table R507.6, reads a {authored:g} psf "
                 f"figure from the house's preferences: it is under the table's "
                 f"{DECK_LIVE_LOAD_PSF:g} psf live, so the live load governs there. It is a "
                 f"screen, not a design snow.)")
    return text + " " + NOT_COVERED_OWNER + " " + CURTAIN_OWNER_BASIS


@dataclass(frozen=True)
class ColumnStatics:
    """What one beam's statics put on one column, lb. ``dead_lb`` has no planter in it."""

    beam_tag: str
    dead_lb: float
    live_lb: float
    planter_lb: float
    #: The deck area this column carries by the beam's statics under the FULL uniform load
    #: (reaction / 50 psf), the area an uplift on the plank reaches the column through.
    area_ft2: float = 0.0


def beam_reactions(a_ft: float, span_ft: float, b_ft: float, tributary_ft: float,
                   planter_plf: float) -> tuple[tuple[float, float], tuple[float, float],
                                                tuple[float, float]]:
    """``(dead, live, planter)`` reactions ``(lo support, hi support)``, lb: dead alone, the
    live increment at its worst pattern (ASCE 7-16 §4.3.3, the eight patterns), and a planter
    line load over the back span. The live increment is per support, each at its own worst."""
    from typehaus.engineering.overhang_beam import _state

    dead_plf = DECK_DEAD_LOAD_PSF * tributary_ft
    live_plf = DECK_LIVE_LOAD_PSF * tributary_ft
    dead = _state((dead_plf,) * 3, a_ft, span_ft, b_ft)[:2]
    planter = _state((0.0, planter_plf, 0.0), a_ft, span_ft, b_ft)[:2]
    live = [0.0, 0.0]
    for pattern in product((0.0, 1.0), repeat=3):
        r = _state(tuple(live_plf * on for on in pattern), a_ft, span_ft, b_ft)[:2]  # type: ignore[arg-type]
        live = [max(live[0], r[0]), max(live[1], r[1])]
    return (dead[0], dead[1]), (live[0], live[1]), (planter[0], planter[1])


def column_statics(ctx: Any) -> dict[str, ColumnStatics]:
    """``post tag -> ColumnStatics`` for every post a graded glulam deck beam bears on.

    Empty for a beam this pass cannot grade (not exactly two bearings). The tributary is
    ``deck_tributary.beam_tributary_ft``, the rule ``glulam_beam`` loads the beam with.
    """
    from typehaus.engineering import glulam_beam as gb
    from typehaus.engineering.deck_tributary import beam_tributary_ft

    allowance = planter_allowance(ctx)
    out: dict[str, ColumnStatics] = {}
    for tag, (beam, deck) in sorted(gb._glulam_deck_beams(ctx).items()):
        stations = gb._bearing_stations(ctx, beam)
        trib = beam_tributary_ft(ctx, deck, beam)
        if isinstance(stations, str) or trib is None:
            continue
        (_lo_t, lo_post), (_hi_t, hi_post), (a_ft, span_ft, b_ft) = stations
        dead, live, planter = beam_reactions(a_ft, span_ft, b_ft, trib,
                                             allowance.plf if allowance else 0.0)
        from typehaus.engineering.overhang_beam import _state

        total_plf = (DECK_DEAD_LOAD_PSF + DECK_LIVE_LOAD_PSF) * trib
        full = _state((total_plf,) * 3, a_ft, span_ft, b_ft)[:2]
        total_psf = DECK_DEAD_LOAD_PSF + DECK_LIVE_LOAD_PSF
        for i, post in enumerate((lo_post, hi_post)):
            out[post] = ColumnStatics(tag, dead[i], live[i], planter[i], full[i] / total_psf)
    return out
