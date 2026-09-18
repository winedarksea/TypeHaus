"""What size a duct has to be to carry its air — the one derivation, two readers.

`checks/mep/erv_static.py` already computed the pressure drop of an **authored** run:
Darcy-Weisbach over the developed length with a Colebrook friction factor, the bore and the
roughness read off the run's own ``DuctProductType``. That answers "does the duct you drew
still move the air", which is the right question about a finished design and the wrong one
for a router: a campaign that *creates* a branch has no authored size to grade, and picking
2" because it is the constant at the top of the file is the defect Phase 0 deleted from the
drain side.

So the physics moves here, where `routing/` may read it — the same move `mep_envelopes.py`
made for what a run occupies, and for the same reason: a router that sized a duct by
different arithmetic from the check that grades it makes the loop impossible to close.
`erv_static` now reads :func:`friction_factor` and :func:`leg_drop_in_wg` from here.

**The rule is a friction rate, not a velocity.** Residential trunk sizing is done at a
constant pressure gradient — the ASHRAE/ACCA Manual D equal-friction method — because that
is what keeps a branch's share of the fan's static proportional to its length. The rate is
the house's to set (``[mep.routing] duct_friction_in_wg_per_100ft``); 0.08 in. w.g. per 100
ft is the residential default Manual D is worked at.

**Only a real product may be proposed.** :func:`size_for_cfm` picks from the library's own
``DuctProductType`` rows, smallest first, and returns the first whose rate lands under the
target. A cfm no row can carry is a refusal line naming the largest that was tried — never
the largest row silently, and never an interpolated bore nobody stocks.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

#: Kinematic viscosity of dry air at 70 F, ft^2/s. Air properties enter only through the
#: Reynolds number, and a static budget is a room-temperature calculation — see the note in
#: ``erv_static``, which this value moved from unchanged.
NU_FT2_S = 1.63e-4

#: Colebrook is a TURBULENT correlation and a 5 cfm branch in 4" pipe runs at Re ~1,950.
#: Below 2,300 the flow is laminar and Hagen-Poiseuille (f = 64/Re) is exact; between 2,300
#: and 4,000 there is no correlation at all and the conservative read is the turbulent value
#: at the top of the band.
LAMINAR_RE = 2300.0
MIN_TURBULENT_RE = 4000.0

#: The equal-friction design rate, in. w.g. per 100 ft. Manual D's residential default, and
#: the value ``[mep.routing] duct_friction_in_wg_per_100ft`` overrides.
DEFAULT_FRICTION_IN_WG_PER_100FT = 0.08

_M_TO_FT = 3.280839895013123


def friction_factor(reynolds: float, relative_roughness: float) -> float:
    """Darcy friction factor across all three flow regimes — see :data:`LAMINAR_RE`."""
    if reynolds < LAMINAR_RE:
        return 64.0 / reynolds
    reynolds = max(reynolds, MIN_TURBULENT_RE)
    factor = 0.03
    for _ in range(80):
        factor = (-2.0 * math.log10(relative_roughness / 3.7
                                    + 2.51 / (reynolds * math.sqrt(factor)))) ** -2
    return factor


def leg_drop_in_wg(cfm: float, bore_m: float, roughness_m: float,
                   developed_m: float) -> float:
    """Darcy-Weisbach drop over a straight length of round duct, in. w.g.

    Fittings are the caller's: ``erv_static`` adds each elbow's published equivalent length
    to ``developed_m`` before calling, because an equivalent length is a reading off the
    product's own sheet and not something this can derive.
    """
    bore_ft = bore_m * _M_TO_FT
    area_ft2 = math.pi * bore_ft * bore_ft / 4.0
    velocity_fpm = cfm / area_ft2
    velocity_pressure = (velocity_fpm / 4005.0) ** 2
    reynolds = (velocity_fpm / 60.0) * bore_ft / NU_FT2_S
    factor = friction_factor(reynolds, roughness_m * _M_TO_FT / bore_ft)
    return factor * (developed_m * _M_TO_FT / bore_ft) * velocity_pressure


def friction_rate_in_wg_per_100ft(cfm: float, bore_m: float, roughness_m: float) -> float:
    """The pressure gradient this flow makes in this bore — the equal-friction criterion."""
    return leg_drop_in_wg(cfm, bore_m, roughness_m, 100.0 / _M_TO_FT)


def velocity_fpm(cfm: float, bore_m: float) -> float:
    bore_ft = bore_m * _M_TO_FT
    return cfm / (math.pi * bore_ft * bore_ft / 4.0)


@dataclass(frozen=True)
class DuctSize:
    """A size a router may actually propose, with the numbers that chose it.

    ``rate_in_wg_per_100ft`` and ``velocity_fpm`` are carried rather than re-derived because
    a proposal has to be arguable: "6" semi-rigid, 0.062 in. w.g./100 ft at 612 fpm" is a
    sentence an installer can disagree with, and "6"" is not.
    """

    type_tag: str
    material: str
    nominal_m: float
    bore_m: float
    rate_in_wg_per_100ft: float
    velocity_fpm: float

    def basis(self) -> str:
        from typehaus.quantities import M_PER_IN
        return (f'{self.nominal_m / M_PER_IN:.3g}" {self.material} ({self.type_tag}): '
                f"{self.rate_in_wg_per_100ft:.3f} in. w.g./100 ft at "
                f"{self.velocity_fpm:.0f} fpm")


def _rows(library: Any, material: str | None) -> list[Any]:
    rows = list(getattr(library, "duct_product_types", ()) or ())
    if material is not None:
        rows = [r for r in rows if r.material == material]
    return sorted(rows, key=lambda r: r.nominal_diameter.meters)


def size_for_cfm(library: Any, cfm: float, *,
                 material: str | None = None,
                 rate_in_wg_per_100ft: float = DEFAULT_FRICTION_IN_WG_PER_100FT,
                 ) -> tuple[DuctSize | None, str]:
    """The smallest stocked round duct that carries ``cfm`` under the design gradient.

    Returns ``(size, basis)`` on success and ``(None, reason)`` on refusal. The refusal is a
    sentence, not a fallback size: a branch the catalog cannot carry is a design question
    (a second branch, a bigger product line, less air) and the router does not get to pick.
    """
    if cfm is None or cfm <= 0:
        return None, "no design cfm: a duct with no air in it has no derivable size"
    rows = _rows(library, material)
    if not rows:
        return None, ("the library states no DuctProductType"
                      + (f" in {material!r}" if material else "")
                      + ", so no size can be proposed from a published bore")
    largest: DuctSize | None = None
    for row in rows:
        bore_m = row.bore_diameter.meters
        rate = friction_rate_in_wg_per_100ft(cfm, bore_m, row.roughness_m)
        size = DuctSize(row.tag, row.material, row.nominal_diameter.meters, bore_m,
                        rate, velocity_fpm(cfm, bore_m))
        largest = size
        if rate <= rate_in_wg_per_100ft + 1e-12:
            return size, size.basis()
    assert largest is not None
    return None, (f"{cfm:.0f} cfm needs more than the largest published row: "
                  f"{largest.basis()}, over the {rate_in_wg_per_100ft:.3f} "
                  "in. w.g./100 ft design rate")


def friction_rate_from_preferences(table: dict[str, Any]) -> float:
    """``[mep.routing] duct_friction_in_wg_per_100ft``, or the Manual D default."""
    try:
        rate = float(table.get("duct_friction_in_wg_per_100ft",
                               DEFAULT_FRICTION_IN_WG_PER_100FT))
    except (TypeError, ValueError):
        return DEFAULT_FRICTION_IN_WG_PER_100FT
    return rate if rate > 0 else DEFAULT_FRICTION_IN_WG_PER_100FT


def candidate_summary(library: Any, material: str | None = None) -> Iterable[str]:
    """One line per stocked row, for ``--explain``'s sizing table."""
    from typehaus.quantities import M_PER_IN
    for row in _rows(library, material):
        yield (f'{row.nominal_diameter.meters / M_PER_IN:>5.3g}" {row.material:<12} '
               f'bore {row.bore_diameter.meters / M_PER_IN:.3g}"')
