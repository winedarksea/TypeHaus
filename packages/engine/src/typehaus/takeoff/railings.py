"""Railing product takeoff, grouped by catalog type and storey.

Prices key on ``length_ft`` and that stays the order quantity, but a guard is not only its
run: the same 38 feet of guard line is a different order as 92 pickets, as 8 cable runs, or
as 7 glass lites. Those quantities are *derived* — read back off the geometry the resolver
drew, or off the same algebra it drew it with — so the bill and the model cannot disagree
about how many pickets there are.

Masonry guards (``Wall.guard``) get their own rows. Their volume already bills through
``wall_structure`` by the cubic yard, so their rate here is zero on purpose: the
"price it in one table only" rule in ``prices.toml`` applies directly, and a guard that is a
wall is bought as a wall.
"""

from __future__ import annotations

import math

from typehaus.model.elements import Wall
from typehaus.model.structure import Railing
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.railings.infill import derived_infill_count
from typehaus.resolve.railings.parts import (
    RAILING_GLASS_CATEGORY,
    RAILING_INFILL_CATEGORY,
    resolve_parts,
)
from typehaus.resolve.sweep import sweep_length_m

_M_TO_FT = 3.280839895013123
_M2_TO_SQFT = 10.763910416709722

#: The key an untyped railing groups under. It is also what lands in the emitted ``type``,
#: which used to be the raw ``None`` — so the key the reader saw and the key the estimator
#: matched on were different strings, and 30 LF of handrail could only be priced by a
#: ``"None"`` entry in prices.toml working around it.
UNTYPED_RAILING = "(untyped railing)"
#: Masonry guard rows. Named rather than left blank so the estimate shows the line and its
#: zero rate, instead of the guard quietly not appearing in the railing section at all.
MASONRY_GUARD_TYPE = "(masonry guard wall)"


def _path_length_ft(railing: Railing) -> float:
    """The guard line's run, walked point to point — what a railing is *bought* by.

    A count alone cannot price a railing: one balcony guard and one stair guard are both
    "1" and are not the same order. The path is already the geometry the resolver frames
    posts and rails along, so its length is the honest order quantity.

    The path is a *plan* polyline, so a stair guard's run is its horizontal projection —
    the rail itself is longer by 1/cos(slope) (~19% on a 7.5"/11" stair). That is the
    resolver's own datum, not a rounding: correcting it here would put this takeoff at
    odds with the posts and rails the model actually draws. ``top_rail_length_ft`` below is
    where the true sloped run is reported.
    """
    points = [point.xy_m for point in railing.path]
    return sum(math.dist(a, b) for a, b in zip(points, points[1:])) * _M_TO_FT


def _centroid(outline) -> tuple[float, float]:
    return (sum(x for x, _y in outline) / len(outline),
            sum(y for _x, y in outline) / len(outline))


def _plan_run_m(outline) -> float:
    """The long side of a band's plan rectangle — how far along its run the solid reaches."""
    xs = [x for x, _y in outline]
    ys = [y for _x, y in outline]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def _posts(model: ResolvedModel, tag: str) -> list[ResolvedSolid]:
    """This railing's post solids, in the order the resolver walked its stations."""
    return _by_part(model, tag, "POST")


def _brackets(model: ResolvedModel, tag: str) -> list[ResolvedSolid]:
    """This railing's wall brackets — what carries it where posts would be the wrong item.

    A wall-mounted handrail is bought as a rail and a box of brackets, and it has no posts
    at all. Until ``Railing.mount`` was read (2026-08-22) the resolver drew posts under one
    anyway, so this section counted them and nobody noticed the order was for the wrong
    part; when the posts went away, the *station* walk this file reads went with them and
    took the sloped rail length with it.
    """
    return _by_part(model, tag, "BRACKET")


def _by_part(model: ResolvedModel, tag: str, part: str) -> list[ResolvedSolid]:
    return sorted((s for s in model.solids
                   if s.category == "railing" and s.tag.startswith(f"{tag}-{part}")),
                  key=lambda s: s.uid)


def _stations(model: ResolvedModel, tag: str) -> list[ResolvedSolid]:
    """Whatever this railing is carried on, post or bracket, in station order."""
    return _posts(model, tag) or _brackets(model, tag)


def _top_rail_length_ft(model: ResolvedModel, tag: str) -> float:
    """The top rail's *true* run, following the walking surface rather than its projection.

    The rail carries its own 3D polyline now (:class:`~typehaus.resolve.model.SolidSweep`),
    so this is the developed length of that polyline — the cap stock a rake actually
    consumes, about 19% over the plan run on a code stair — read straight off the drawn
    geometry. It used to be recovered by summing post-to-post hypotenuses, which was the best
    a stack of level bands could offer: the stations track the rake and the walk puts one at
    every path vertex, but between two stations the sum is a chord across whatever the
    surface does, and a wall-mounted rail had to borrow its brackets to have stations at all.

    ``rail_count > 1`` puts more than one bar on the same path; the *top* rail is the one
    this row prices, so the longest is taken rather than the sum. Falls back to the station
    walk for a rail drawn without a sweep.
    """
    lengths = [sweep_length_m(solid.sweep) for solid in _by_part(model, tag, "RAIL")
               if solid.sweep is not None]
    if lengths:
        return max(lengths) * _M_TO_FT
    stations = _stations(model, tag)
    total = 0.0
    for a, b in zip(stations, stations[1:]):
        (ax, ay), (bx, by) = _centroid(a.outline), _centroid(b.outline)
        total += math.hypot(math.dist((ax, ay), (bx, by)), b.z0_m - a.z0_m)
    return total * _M_TO_FT


def _infill_solids(model: ResolvedModel, tag: str) -> list:
    return [s for s in model.solids
            if s.category in (RAILING_INFILL_CATEGORY, RAILING_GLASS_CATEGORY)
            and s.tag.startswith(f"{tag}-")]


def _infill_quantities(model: ResolvedModel, element: Railing) -> dict[str, object]:
    """The one quantity that prices this railing's infill, keyed by its style."""
    solids = _infill_solids(model, element.tag)
    if element.infill == "balusters":
        return {"baluster_count": len(solids)}
    if element.infill == "cable":
        # Cable is bought by the foot of cable, which is the run times the number of runs.
        # The count comes from the same algebra the resolver drew it with rather than from
        # the solid count, because a raking guard bands each cable into several solids.
        parts = resolve_parts(model, element)
        gap = element.baluster_spacing.meters if element.baluster_spacing else 0.0
        clear_height = element.height.meters - parts.rail_section_m
        count = derived_infill_count(clear_height, parts.cable_diameter_m, gap)
        return {"cable_count": count,
                "cable_length_ft": round(_path_length_ft(element) * count, 1)}
    if element.infill in ("panel", "mesh"):
        area = sum(_plan_run_m(s.outline) * (s.z1_m - s.z0_m) for s in solids)
        return {"panel_count": len(solids),
                "panel_area_sqft": round(area * _M2_TO_SQFT, 1)}
    return {}


def _add_infill(row: dict[str, object], quantities: dict[str, object]) -> None:
    for key, value in quantities.items():
        row[key] = (row.get(key) or 0) + value


def railing_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Count railing instances by their explicit product reference, with their run."""
    groups: dict[tuple[str, str], dict[str, object]] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, Wall) and element.guard:
                _accumulate_guard_wall(model, groups, element, storey.tag)
                continue
            if not isinstance(element, Railing):
                continue
            type_ref = element.type_ref or UNTYPED_RAILING
            key = (type_ref, storey.tag)
            row = groups.setdefault(key, {
                "type": type_ref,
                "style": element.infill or "frame only",
                "storey": storey.tag,
                "count": 0,
                "length_ft": 0.0,
                "post_count": 0,
                "bracket_count": 0,
                "top_rail_length_ft": 0.0,
                "tags": [],
            })
            row["count"] = int(row["count"]) + 1
            row["length_ft"] = float(row["length_ft"]) + _path_length_ft(element)
            row["post_count"] = int(row["post_count"]) + len(_posts(model, element.tag))
            row["bracket_count"] = (int(row["bracket_count"])
                                    + len(_brackets(model, element.tag)))
            row["top_rail_length_ft"] = (float(row["top_rail_length_ft"])
                                         + _top_rail_length_ft(model, element.tag))
            _add_infill(row, _infill_quantities(model, element))
            tags = row["tags"]
            assert isinstance(tags, list)
            tags.append(element.tag)
    return [_finish(groups[key]) for key in sorted(groups)]


def _accumulate_guard_wall(model: ResolvedModel, groups: dict, element: Wall,
                           storey: str) -> None:
    """A masonry guard's row: its run, and nothing that would price it twice.

    The wall's masonry volume is already in ``structural_solids``/``wall_structure``, so
    this row exists to make the guard *visible* in the railing schedule — a reader looking
    for "what guards the porch" should not have to know it is filed as a wall — not to
    charge for it a second time.
    """
    wall = next((w for w in model.walls if w.tag == element.tag), None)
    if wall is None:
        return
    key = (MASONRY_GUARD_TYPE, storey)
    row = groups.setdefault(key, {
        "type": MASONRY_GUARD_TYPE,
        "style": "masonry",
        "storey": storey,
        "count": 0,
        "length_ft": 0.0,
        "post_count": 0,
        "bracket_count": 0,
        "top_rail_length_ft": 0.0,
        "note": "volume bills through wall_structure; priced at zero here, not twice",
        "tags": [],
    })
    (ax, ay), (bx, by) = wall.axis
    run_ft = math.dist((ax, ay), (bx, by)) * _M_TO_FT
    row["count"] = int(row["count"]) + 1
    row["length_ft"] = float(row["length_ft"]) + run_ft
    row["top_rail_length_ft"] = float(row["top_rail_length_ft"]) + run_ft
    tags = row["tags"]
    assert isinstance(tags, list)
    tags.append(element.tag)


def _finish(row: dict[str, object]) -> dict[str, object]:
    out = dict(row)
    out["length_ft"] = round(float(row["length_ft"]), 1)
    out["top_rail_length_ft"] = round(float(row["top_rail_length_ft"]), 1)
    tags = row["tags"]
    assert isinstance(tags, list)
    out["tags"] = sorted(tags)
    return out
