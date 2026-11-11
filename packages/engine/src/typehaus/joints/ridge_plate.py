"""A roof seated on a beveled ridge plate: the tie its joists take and the screws under it."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.hardware.catalog import ROLE_HURRICANE_TIE, ROLE_IJOIST_ROOF_TIE
from typehaus.hardware.config import UpliftTieRules
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.roof_ridge_closure import RIDGE_PLATE_CONNECTION
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof
from typehaus.resolve.roof_geometry import roof_slope_factor

#: NW-D217 note 1 limits the H2.5A family on a roof I-joist to this rise in 12.
H25A_IJOIST_MAX_RISE_IN_12 = 3.0
_STATION_TOL_M = 1e-3


def is_steep_ijoist_roof(roof: ResolvedRoof, profile: str) -> bool:
    """A roof I-joist pitched past the H2.5A family's NW-D217 limit."""
    if cross_section(profile).shape != "i_joist":
        return False
    rise_in_12 = 12.0 * math.sqrt(max(roof_slope_factor(roof) ** 2 - 1.0, 0.0))
    return rise_in_12 > H25A_IJOIST_MAX_RISE_IN_12 + 1e-6


def roof_tie_role(assembly, member: FramedMember, treated: bool) -> str:
    """The part a bearing end takes. H8 is G90 only, so a treated bearing keeps the H-tie."""
    if isinstance(assembly, ResolvedRoof) and not treated \
            and is_steep_ijoist_roof(assembly, member.profile):
        return ROLE_IJOIST_ROOF_TIE
    return ROLE_HURRICANE_TIE


def ridge_seat_point(member: FramedMember, half_width_m: float) -> tuple:
    """Where a ridge end's tie sits: mid-bearing on its own side, on the plate's bevel."""
    frac = half_width_m / 2.0 / math.dist(member.p0, member.p1)
    x = member.p1[0] + (member.p0[0] - member.p1[0]) * frac
    y = member.p1[1] + (member.p0[1] - member.p1[1]) * frac
    return (x, y), member.z0_end_m + (member.z0_m - member.z0_end_m) * frac


def ridge_plate_of(roof: ResolvedRoof) -> FramedMember | None:
    return next((m for m in roof.members if m.connection == RIDGE_PLATE_CONNECTION), None)


@dataclass(frozen=True)
class RidgePlateScrews:
    """The screws holding one ridge plate down, counted by the bays between joist stations."""

    profile: str
    bays: int
    count: int


def ridge_plate_screws(model: ResolvedModel, rules: UpliftTieRules) -> list[RidgePlateScrews]:
    found = []
    for roof in model.roofs:
        plate = ridge_plate_of(roof)
        if plate is None:
            continue
        axis = 0 if roof.ridge_direction == "x" else 1
        stations = sorted({round(m.p1[axis] / _STATION_TOL_M)
                           for m in roof.members if m.category == "rafter"})
        bays = max(len(stations) - 1, 0)
        found.append(RidgePlateScrews(plate.profile, bays, bays * rules.ridge_plate_screws_per_bay))
    return found
