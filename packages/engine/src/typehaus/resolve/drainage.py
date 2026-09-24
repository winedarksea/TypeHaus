"""Authored site drainage → solids: interceptor trenches and soakaways.

The rest of the stormwater family is derived from something else — a gutter from a roof
edge, a bedding's tile from the excavation it lies in. These two are authored, because
where an interceptor trench runs and where a drywell goes are decisions about the site, not
consequences of the building. They resolve here rather than in :mod:`.accessories` because
that module is envelope trim and hardware; a trench across the yard is neither.
"""

from __future__ import annotations

import dataclasses

from typehaus.findings import Finding, element_error
from typehaus.model.landscape import RainGarden
from typehaus.model.stormwater import AreaDrain
from typehaus.model.structure import Drywell, FrenchDrain
from typehaus.model.trim import Downspout
from typehaus.resolve.drain_tile import drain_tile_solids, resolved_spec
from typehaus.resolve.geometry import circle_outline, rect_between
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.overlay import difference, union_all
from typehaus.resolve.rain_garden import floor_z_m

#: Overlap a basin may leave outside its slab and still count as inside it: grid noise.
_BASIN_SLACK_M2 = 1e-8

#: A drywell is a cylinder; the solid IR extrudes a plan outline, so the bore is faceted.
#: Matched to the vent/downspout risers so round things read alike in the viewer.
_DRYWELL_FACETS = 16

#: A soakaway is a hole full of STONE — ``Drywell.aggregate`` says which stone in prose, and
#: the modelled volume is the void the stone fills. Without this the solid names no material
#: at all, and ``resolve/assembly_material.solid_material_ref``'s last-resort default hatched
#: 4.35 cy of #57 washed rock as cast-in-place concrete in every section it was cut in. The
#: ref is the one the drawing palette already carries for below-grade stone
#: (``emit/draw/palette.py``: ``aggregate`` → gravel hatch, #7f7f7f), not a catalog
#: ``Material``: washed rock is bought by the yard, not specified by an R-value.
_AGGREGATE = "aggregate"


def resolve_drainage(model: ResolvedModel) -> list[Finding]:
    """Append french-drain and drywell solids. Findings report unresolvable references."""
    findings: list[Finding] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, FrenchDrain):
                findings.extend(_resolve_french_drain(model, element, storey.tag))
            elif isinstance(element, Drywell):
                findings.extend(_resolve_drywell(model, element, storey.tag))
            elif isinstance(element, RainGarden):
                findings.extend(_resolve_rain_garden(model, element, storey.tag))
            elif isinstance(element, Downspout) and element.extension is not None:
                _resolve_leader_extension(model, element, storey.tag)
            elif isinstance(element, AreaDrain):
                findings.extend(_resolve_area_drain(model, element, storey.tag))
    return findings


def _resolve_area_drain(model: ResolvedModel, el: AreaDrain, storey: str) -> list[Finding]:
    """The basin in its slab, and the solid riser from the basin floor to the outlet.

    The basin voids its host slab, so the pour is billed and drawn net of the hole.
    """
    index = next((i for i, s in enumerate(model.solids)
                  if s.tag == el.host_ref and s.category == "slab"), None)
    if index is None:
        return [element_error("integrity.area_drain_host",
                              f"area drain {el.tag} is set in {el.host_ref!r}, which is not "
                              f"a resolved slab", el.tag)]
    host = model.solids[index]
    rim = el.rim_elevation.meters if el.rim_elevation is not None else host.z1_m
    floor = rim - el.basin_depth.meters
    sizes = (el.grate_size.meters, el.basin_depth.meters, el.outlet_diameter.meters)
    if min(sizes) <= 0.0 or el.outlet_invert.meters > floor + 1e-9:
        return [element_error("integrity.area_drain_geometry",
                              f"area drain {el.tag} needs a positive grate, basin and "
                              f"outlet, and an outlet invert at or below its basin floor",
                              el.tag)]
    x, y = el.position.xy_m
    half = el.grate_size.meters / 2.0
    ring = rect_between((x - half, y), (x + half, y), -half, half)
    if not _inside_net_slab(host, ring):
        return [element_error("integrity.area_drain_host",
                              f"area drain {el.tag}'s basin is not wholly inside "
                              f"{el.host_ref}'s poured area (outline less its voids)", el.tag)]
    model.solids[index] = dataclasses.replace(
        host, voids=(*host.voids, tuple(tuple(p) for p in ring)))
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-00", tag=el.tag, storey=storey, category="area_drain",
        outline=ring, z0_m=floor, z1_m=rim, material="polyethylene"))
    if floor > el.outlet_invert.meters:
        r = el.outlet_diameter.meters / 2.0
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-RS", tag=f"{el.tag}-RISER", storey=storey,
            category="area_drain_riser",
            outline=rect_between((x - r, y), (x + r, y), -r, r),
            z0_m=el.outlet_invert.meters, z1_m=floor, material=el.outlet_material))
    return []


def _inside_net_slab(host: ResolvedSolid, ring: list[tuple[float, float]]) -> bool:
    """Is the basin inside the slab's outline less its existing voids (to a micron)?"""
    from shapely.geometry import Polygon

    net = difference(Polygon(host.outline), union_all(Polygon(v) for v in host.voids))
    return difference(Polygon(ring), net).area <= _BASIN_SLACK_M2


#: Planting soil, keyed into the drawing palette's existing ``soil`` hatch; the stone under
#: it is the drywell's ``aggregate``.
_MEDIA = "soil"


def _resolve_rain_garden(model: ResolvedModel, el: RainGarden, storey: str) -> list[Finding]:
    """Media under the whole rim (it runs up the side slopes), stone under the media."""
    ring = [point.xy_m for point in el.outline]
    if len(ring) < 3 or el.media_depth.meters <= 0.0:
        return [element_error("integrity.rain_garden_geometry",
                              f"rain garden {el.tag} needs a rim outline and media depth",
                              el.tag)]
    top = floor_z_m(el)
    bottom = top - el.media_depth.meters
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-00", tag=el.tag, storey=storey, category="rain_garden_media",
        outline=ring, z0_m=bottom, z1_m=top, material=_MEDIA))
    if el.stone_depth is not None and el.stone_depth.meters > 0.0:
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-01", tag=f"{el.tag}-STONE", storey=storey,
            category="rain_garden_stone", outline=ring,
            z0_m=bottom - el.stone_depth.meters, z1_m=bottom, material=_AGGREGATE))
    return []


def _resolve_leader_extension(model: ResolvedModel, el: Downspout, storey: str) -> None:
    """The buried pipe on its fall, plus the riser from the leader's foot down to it."""
    ext = el.extension
    assert ext is not None
    path = [point.xy_m for point in ext.path]
    if len(path) < 2:
        return
    diameter = ext.diameter.meters
    path, inverts = _densified(path, ext.inlet_invert.meters, ext.outlet_invert.meters)
    model.solids.extend(drain_tile_solids(
        el.uid, f"{el.tag}-EXT", storey, path, ext.inlet_invert.meters, _pipe_spec(ext),
        closed=False, segment_floor_z_m=inverts, category="leader_extension", bedding_m=0.0))
    x, y = path[0]
    half = diameter / 2.0
    if el.bottom_elevation.meters > ext.inlet_invert.meters:
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-RS", tag=f"{el.tag}-EXT-RISER", storey=storey,
            category="leader_extension",
            outline=[(x - half, y - half), (x + half, y - half), (x + half, y + half),
                     (x - half, y + half)],
            z0_m=ext.inlet_invert.meters, z1_m=el.bottom_elevation.meters,
            material=ext.material))


def _pipe_spec(ext):
    from typehaus.resolve.model import ResolvedDrainTile

    return ResolvedDrainTile(diameter_m=ext.diameter.meters, material=ext.material,
                             sock=False, discharge=None, rock_width_m=None, rock_depth_m=None)


def _resolve_french_drain(model: ResolvedModel, el: FrenchDrain,
                          storey: str) -> list[Finding]:
    """The trench as a band per segment, with the tile derived inside it."""
    path = [point.xy_m for point in el.path]
    if len(path) < 2:
        return [element_error("integrity.french_drain_path",
                              f"french drain {el.tag} needs at least two path points",
                              el.tag)]
    half = el.trench_width.meters / 2.0
    # ** THE TRENCH FOLLOWS ITS FALL, AND UNTIL 2026-09-14 IT COULD NOT. ** ``FrenchDrain``
    # carried one scalar invert and every segment came out at it, so a run that fell was
    # drawn level and read level to every consumer — the sections, the sitework take-off and
    # the drainage checks alike. ``end_invert`` is the far end; the segments interpolate
    # between the two by plan distance along the path, which is what a laid pipe does.
    #
    # A run with no ``end_invert`` is still dead level, which is a real thing an interceptor
    # trench is, and comes out byte-identical to before.
    path, inverts = _densified(
        path, el.invert.meters,
        el.end_invert.meters if el.end_invert is not None else None)
    for index, (start, end) in enumerate(zip(path[:-1], path[1:], strict=True)):
        if start == end:
            continue
        z0 = min(inverts[index], inverts[index + 1])
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-{index:02d}", tag=f"{el.tag}-{index + 1}", storey=storey,
            category="french_drain", outline=rect_between(start, end, -half, half),
            z0_m=z0, z1_m=max(inverts[index], inverts[index + 1]) + el.trench_depth.meters,
            material=_AGGREGATE,
        ))
    # The pipe is not the trench: the trench is the excavation and the stone, and the tile
    # is the product inside it — billed separately, and the thing that actually carries.
    if el.tile is not None:
        model.solids.extend(drain_tile_solids(
            el.uid, el.tag, storey, path, el.invert.meters, resolved_spec(el.tile),
            closed=False, segment_floor_z_m=inverts))
    return []


#: The most a single drawn band may rise across its own length, metres. A ``ResolvedSolid``
#: is a PRISM — one z0 and one z1 — so a sloping trench can only be drawn as a staircase,
#: and the step height is what decides how close the staircase is to the ramp.
#:
#: ** IT IS A TAKE-OFF NUMBER BEFORE IT IS A DRAWING ONE. ** A falling run drawn as ONE box
#: from the low invert to the high one bills ``fall + trench_depth`` of excavation instead of
#: ``trench_depth``: on catlin's field lateral, 28" + 8" against 8", a **4.5x over-bill** of
#: the trench. One inch per step keeps that error under an inch of depth on any run.
_MAX_BAND_RISE_M = 1.0 * 0.0254


def _densified(path, start_m: float, end_m: float | None):
    """``(path, inverts)`` with falling segments split so no drawn band rises far.

    A level run is returned untouched and resolves byte-identically to before
    ``end_invert`` existed, which is every footing ring and every genuine interceptor.
    """
    import math

    inverts = _segment_inverts(path, start_m, end_m)
    if end_m is None or abs(end_m - start_m) <= _MAX_BAND_RISE_M:
        return path, inverts
    dense_path = [path[0]]
    dense_inverts = [inverts[0]]
    for index in range(len(path) - 1):
        (x0, y0), (x1, y1) = path[index], path[index + 1]
        z0, z1 = inverts[index], inverts[index + 1]
        steps = max(1, math.ceil(abs(z1 - z0) / _MAX_BAND_RISE_M))
        for step in range(1, steps + 1):
            ratio = step / steps
            dense_path.append((x0 + (x1 - x0) * ratio, y0 + (y1 - y0) * ratio))
            dense_inverts.append(z0 + (z1 - z0) * ratio)
    return dense_path, dense_inverts


def _segment_inverts(path, start_m: float, end_m: float | None) -> list[float]:
    """The trench floor at every vertex, interpolated by plan distance along the run.

    By DISTANCE and not by vertex count, because a run whose legs are 2 ft and 40 ft does
    not lose half its fall in the first two feet. ``None`` at the far end is a level run and
    returns the start invert throughout.
    """
    import math

    if end_m is None or len(path) < 2:
        return [start_m] * len(path)
    spans = [math.dist(a, b) for a, b in zip(path[:-1], path[1:], strict=True)]
    total = sum(spans)
    if total <= 0.0:
        return [start_m] * len(path)
    run = 0.0
    out = [start_m]
    for span in spans:
        run += span
        out.append(start_m + (end_m - start_m) * run / total)
    return out


def _resolve_drywell(model: ResolvedModel, el: Drywell, storey: str) -> list[Finding]:
    radius = el.diameter.meters / 2.0
    depth = el.depth.meters
    if radius <= 0.0 or depth <= 0.0:
        return [element_error("integrity.drywell_dimensions",
                              f"drywell {el.tag} needs a positive diameter and depth",
                              el.tag)]
    z1 = _drywell_top_m(model, el, storey)
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-00", tag=el.tag, storey=storey, category="drywell",
        outline=circle_outline(el.position.xy_m, radius, _DRYWELL_FACETS),
        z0_m=z1 - depth, z1_m=z1, material=_AGGREGATE,
    ))
    return []


def _drywell_top_m(model: ResolvedModel, el: Drywell, storey: str) -> float:
    """Top of stone: authored, else site grade, else the storey datum.

    Grade before the datum because a soakaway is dug from the ground. A well outside the
    garage recorded on the basement storey would otherwise begin at the basement floor and
    be drawn hanging in the excavation.
    """
    if el.top_elevation is not None:
        return el.top_elevation.meters
    grade = model.plan.project.site.grade
    if grade is not None:
        return grade.meters
    storey_def = model.plan.storey(storey)
    return storey_def.elevation.meters if storey_def is not None else 0.0
