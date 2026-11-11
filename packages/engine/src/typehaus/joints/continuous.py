"""A member bedded on its support for its whole length: where it is tied down."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.hardware.config import FT_TO_M, UpliftTieRules
from typehaus.joints.hosts import member_storeys
from typehaus.resolve.framing.roof_ridge_closure import RIDGE_PLATE_CONNECTION
from typehaus.resolve.model import ResolvedModel


@dataclass(frozen=True)
class ContinuousBearing:
    """A member bedded on its support for its whole length, and the stations along it.

    ``bearing_connections`` above locates member ENDS, which is the right rule for every
    rafter, truss heel and joist in the house and the wrong one for a beam that never leaves
    its wall — catlin's ridge is the case, and nothing else in the load path covers it.
    """

    category: str
    profile: str
    storey: str
    length_m: float
    #: One station per tie, in metres from ``p0``. Ends included: a run is a fencepost count,
    #: not a division — which is why this is a list of places and not just a number.
    stations_m: tuple[float, ...]
    p0: tuple
    p1: tuple
    z_m: float
    member_key: str = ""


def continuous_bearing_members(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """Every continuously supported member, with its ties' stations.

    The pitch is the house's own; both it and the part are commodity choices recorded in
    ``houses/catlin/notes/ridge_beam_detail.md``, not an engineered uplift design. This
    derives a *schedule* — how many ties, where — and no part of it reads a wind field,
    computes a tributary uplift, or compares one against the tie's allowable.
    """
    pitch_m = max(rules.continuous_bearing_pitch_ft, 0.5) * FT_TO_M
    storeys = member_storeys(model)
    found = []
    for member in model.all_members():
        if not member.continuously_supported or member.connection == RIDGE_PLATE_CONNECTION:
            continue  # a 2-1/8" bevel edge has no room for a tie; it takes plate screws
        count = int(math.floor(member.length_m / pitch_m + 1e-9)) + 1
        found.append(ContinuousBearing(
            category=member.category, profile=member.profile,
            storey=storeys.get(member.parent_uid, ""),
            length_m=member.length_m,
            stations_m=tuple(min(index * pitch_m, member.length_m) for index in range(count)),
            p0=member.p0, p1=member.p1, z_m=member.z0_m,
            member_key=f"{member.parent_uid}:{member.child_key}"))
    return found
