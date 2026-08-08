"""Railing product takeoff, grouped by catalog type and storey."""

import math

from typehaus.model.structure import Railing
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895013123


def _path_length_ft(railing: Railing) -> float:
    """The guard line's run, walked point to point — what a railing is *bought* by.

    A count alone cannot price a railing: one balcony guard and one stair guard are both
    "1" and are not the same order. The path is already the geometry the resolver frames
    posts and rails along, so its length is the honest order quantity.

    The path is a *plan* polyline, so a stair guard's run is its horizontal projection —
    the rail itself is longer by 1/cos(slope) (~19% on a 7.5"/11" stair). That is the
    resolver's own datum, not a rounding: correcting it here would put this takeoff at
    odds with the posts and rails the model actually draws.
    """
    points = [point.xy_m for point in railing.path]
    return sum(math.dist(a, b) for a, b in zip(points, points[1:])) * _M_TO_FT


def railing_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Count railing instances by their explicit product reference, with their run."""
    groups: dict[tuple[str, str], dict[str, object]] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, Railing):
                continue
            type_ref = element.type_ref or "(untyped railing)"
            key = (type_ref, storey.tag)
            row = groups.setdefault(key, {
                "type": element.type_ref,
                "storey": storey.tag,
                "count": 0,
                "length_ft": 0.0,
                "tags": [],
            })
            row["count"] = int(row["count"]) + 1
            row["length_ft"] = float(row["length_ft"]) + _path_length_ft(element)
            tags = row["tags"]
            assert isinstance(tags, list)
            tags.append(element.tag)
    return [
        {**groups[key], "length_ft": round(float(groups[key]["length_ft"]), 1),
         "tags": sorted(groups[key]["tags"])}
        for key in sorted(groups)
    ]
