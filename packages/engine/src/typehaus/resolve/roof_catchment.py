"""Which roof area each leader carries — the catchment a rain garden is sized against.

A gable's footprint (overhang included) splits at its ridge into two eave halves. A half is
carried by the leaders that claim it, shared equally:

* a leader whose ``gutter_ref`` names the ROOF (a derived ``EaveGutter``) carries the half
  on its side of the ridge;
* a leader named by an authored ``Gutter`` hosted on the roof carries the half that gutter
  runs along;
* a roof whose ``EaveGutter.downspout_ref`` names leaders, with no leader naming the roof
  back, sends each named leader the half on its side — a half no named leader stands on is
  UNCOUNTED, and is reported as such rather than guessed onto a leader nobody named.

A shed has one half: its whole footprint. A leaf: reads ``model`` and ``resolve`` only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Polygon, box

from typehaus.model.trim import Downspout, Gutter, downspout_refs


@dataclass
class Catchment:
    by_leader: dict[str, float] = field(default_factory=dict)  # leader tag -> m²
    #: ``(roof tag, side, m²)`` for every half no leader claims.
    uncounted: list[tuple[str, str, float]] = field(default_factory=list)


def _halves(roof) -> dict[str, Polygon]:
    shape = Polygon(roof.footprint)
    minx, miny, maxx, maxy = shape.bounds
    if roof.form != "gable":
        return {"all": shape}
    if roof.ridge_direction == "y":
        mid = (minx + maxx) / 2.0
        return {"west": shape.intersection(box(minx, miny, mid, maxy)),
                "east": shape.intersection(box(mid, miny, maxx, maxy))}
    mid = (miny + maxy) / 2.0
    return {"south": shape.intersection(box(minx, miny, maxx, mid)),
            "north": shape.intersection(box(minx, mid, maxx, maxy))}


def _side_of(halves: dict[str, Polygon], xy) -> str:
    from shapely.geometry import Point

    point = Point(xy)
    return min(halves, key=lambda side: halves[side].distance(point))


def roof_catchments(model) -> Catchment:
    """Every leader's catchment, and every roof half nobody carries."""
    plan = model.plan
    leaders = {e.tag: e for e in plan.all_elements() if isinstance(e, Downspout)}
    gutters = {e.tag: e for e in plan.all_elements() if isinstance(e, Gutter)}
    out = Catchment()
    for roof in model.roofs:
        halves = _halves(roof)
        claims: dict[str, list[str]] = {side: [] for side in halves}
        for leader in leaders.values():
            ref = leader.gutter_ref
            if ref == roof.tag:
                claims[_side_of(halves, (leader.outlet or leader.position).xy_m)].append(
                    leader.tag)
            elif ref in gutters and gutters[ref].host_ref == roof.tag:
                path = [p.xy_m for p in gutters[ref].path]
                mid = ((path[0][0] + path[-1][0]) / 2.0, (path[0][1] + path[-1][1]) / 2.0)
                claims[_side_of(halves, mid)].append(leader.tag)
        element = plan.by_tag(roof.tag)
        eave = getattr(getattr(element, "eave_trim", None), "gutter", None)
        if not any(claims.values()):
            for named in downspout_refs(eave):
                if named in leaders:
                    leader = leaders[named]
                    claims[_side_of(halves, (leader.outlet or leader.position).xy_m)].append(
                        named)
        for side, polygon in halves.items():
            area = polygon.area
            if not claims[side]:
                if area > 0.0:
                    out.uncounted.append((roof.tag, side, area))
                continue
            share = area / len(claims[side])
            for tag in claims[side]:
                out.by_leader[tag] = out.by_leader.get(tag, 0.0) + share
    return out


def leader_catchment_m2(model, leader_tag: str) -> float | None:
    """The roof area one leader carries, or ``None`` when no roof names it."""
    return roof_catchments(model).by_leader.get(leader_tag)
