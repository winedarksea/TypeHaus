"""The layout against the arithmetic it replaced: ``area / spacing`` (decision #75 D3).

Before the layout, ``takeoff/reinforcement.py`` billed a spaced bar as ``area / spacing`` over
the plane it lies in — the run length cancels. That arithmetic survives here as a
TOLERANCE ORACLE. The layout counts ``ceil(L/s) + 1`` bars where the area reads ``L/s``, so
the expected count is one bar per layer over the area figure, ±1 bar per layer for the ceil
and the cover strip the area ignores: ``[area/s − 1, area/s + 2]`` bars a layer, each bar
the longest the role lays. A layout that dropped a row, doubled a face or ran bars through
the cover lands outside it. Two things the old arithmetic never knew are taken out first:
the leg of a vertical continued into the pour below, and the part of a mat's outline that a
larger overlapping pour reinforces instead.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.model.enums import LayerFunction
from typehaus.resolve.geometry import polygon_area

_M_TO_FT = 1.0 / 0.3048
_SPACED = {"vertical", "horizontal", "top-x", "top-y", "bottom-x", "bottom-y"}


def _wall_area_m2(model, wall) -> float:
    """The old module's face: run × mean height of the concrete band, less openings."""
    from typehaus.resolve.geometry import length, sub

    run = length(sub(wall.axis[1], wall.axis[0]))
    layer = next(ly for ly in wall.layers if ly.function == LayerFunction.STRUCTURE.value)
    z0, z1 = layer.band(wall)
    top = ((wall.top_z0_m or z1) + (wall.top_z1_m or z1)) / 2.0
    area = run * (min(z1, top) - z0)
    for o in model.openings:
        if o.host_wall == wall.tag:
            area -= o.width_m * o.height_m
    return max(0.0, area)


def _solid_area_m2(model, solid) -> float:
    from shapely.geometry import Polygon

    own = Polygon(solid.outline)
    area = abs(polygon_area(list(solid.outline))) - sum(
        abs(polygon_area(list(v))) for v in solid.voids)
    reinforced = {s.host_tag for s in model.rebar}
    for other in model.solids:
        if (other.tag != solid.tag and other.tag in reinforced and not other.derived
                and other.category in ("footing", "pad", "slab")
                and other.z0_m < solid.z1_m and solid.z0_m < other.z1_m
                and (Polygon(other.outline).area, other.tag) > (own.area, solid.tag)):
            area -= own.intersection(Polygon(other.outline)).area
    return area


def test_every_spaced_role_is_within_one_bar_per_layer_of_area_over_spacing(
        catlin_model_ro) -> None:
    model = catlin_model_ro
    plan = model.plan
    misses: list[str] = []
    checked = 0
    for rebar_set in model.rebar:
        element = plan.by_tag(rebar_set.host_tag)
        spec = element.reinforcement
        placed: dict[str, float] = defaultdict(float)
        longest: dict[str, float] = defaultdict(float)
        wall = model.wall(rebar_set.host_tag)
        for bar in rebar_set.bars:
            below = 0.0
            if wall is not None and bar.role == "vertical":
                below = max(0.0, wall.z0_m - min(p[2] for p in bar.path))
            placed[bar.role] += bar.placed_length_m - below
            longest[bar.role] = max(longest[bar.role], bar.placed_length_m + bar.lap_length_m)
        if wall is not None:
            area = _wall_area_m2(model, wall)
        else:
            area = _solid_area_m2(model, next(s for s in model.solids
                                              if s.tag == rebar_set.host_tag))
        for entry in spec.bars:
            if entry.role not in _SPACED or entry.spacing is None:
                continue
            area_here = area
            layers = max(1, entry.layers)
            bar = longest[entry.role]
            expected = area_here / entry.spacing.meters * layers
            tolerance = layers * bar
            got = placed[entry.role]
            checked += 1
            if not expected - tolerance - 1e-6 <= got <= expected + 2 * tolerance + 1e-6:
                misses.append(f"{rebar_set.host_tag} {entry.role} #{entry.bar}: laid "
                              f"{got * _M_TO_FT:.1f} LF, area/spacing "
                              f"{expected * _M_TO_FT:.1f} LF, tolerance "
                              f"{tolerance * _M_TO_FT:.1f} LF")
    assert checked > 45  # a coverage floor: 49 spaced roles since W-GF-N-DR retired (2026-09-23)
    assert not misses, "\n".join(misses)
