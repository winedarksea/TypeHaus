"""Resolve countertops: one derived slab per authored ``Countertop`` (→ model/millwork.py).

Split out of ``resolve/millwork.py``. A slab is a record — its polygon, area and cantilever —
never a solid; ``geometry_countertops.py`` draws it for the viewer and the GLB.
"""

from __future__ import annotations

import math
from typing import NamedTuple

from shapely.geometry import Polygon

from typehaus.findings import Finding, Result, Severity, element_error
from typehaus.model.millwork import Countertop
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedCountertop, ResolvedModel, Ring
from typehaus.resolve.overlay import union_all
from typehaus.resolve.placeable_groups import (
    RUN_GAP_TOLERANCE_M,
    run_gap_m,
    run_is_contiguous,
)

_M_TO_IN = 39.37007874
#: Half the filler tolerance — the buffer radius that closes a run's leftovers into one slab.
_FILLER_CLOSE_M = RUN_GAP_TOLERANCE_M / 2.0


class _Size(NamedTuple):
    """A placeable type's plan size, how much of its depth is BOX, and its L (if any)."""

    width_m: float
    depth_m: float
    carcass_m: float
    shape: tuple[tuple[float, float], ...] | None = None


def resolve_countertops(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Populate ``model.countertops``: one derived slab per authored ``Countertop``."""
    findings: list[Finding] = []
    materials = {material.tag for material in plan.library.materials}
    placeables = {obj.tag: obj for obj in model.canvas_objects}
    sizes = _placeable_sizes(plan)

    for storey in plan.storeys:
        for el in plan.storey_elements(storey.tag):
            if not isinstance(el, Countertop):
                continue
            hosts = [placeables.get(tag) for tag in el.hosts]
            missing = [tag for tag, obj in zip(el.hosts, hosts, strict=True) if obj is None]
            if not el.hosts or missing or el.material_ref not in materials:
                findings.append(element_error(
                    "integrity.countertop_ref",
                    f"countertop {el.tag} names no material {el.material_ref!r}"
                    if el.material_ref not in materials else
                    f"countertop {el.tag} names no placeable "
                    f"{', '.join(repr(tag) for tag in missing)}"
                    if missing else f"countertop {el.tag} covers no placeable", el.tag))
                continue
            run = [obj for obj in hosts if obj is not None]
            if not run_is_contiguous([obj.footprint for obj in run]):
                findings.append(element_error(
                    "integrity.countertop_run",
                    f"countertop {el.tag}'s hosts are not one unbroken run "
                    f"({' -> '.join(obj.tag for obj in run)}): a slab does not jump a gap "
                    f"wider than the {RUN_GAP_TOLERANCE_M * _M_TO_IN:g}\" filler tolerance. "
                    "Author one countertop per run", el.tag))
                continue
            unsized = [obj.tag for obj in run if (obj.type_ref or "") not in sizes]
            if unsized:
                findings.append(Finding(
                    severity=Severity.WARN, check_id="millwork.countertop_depth",
                    message=(f"countertop {el.tag} carries no depth: host(s) "
                             f"{', '.join(unsized)} name no type in any placeable catalog"),
                    element_tags=(el.tag,), result=Result.UNKNOWN,
                    fix_hint="give the host placeable a type, or drop it from the run"))
                continue
            record, record_findings = _slab(el, run, storey.tag, sizes)
            findings.extend(record_findings)
            if record is not None:
                model.countertops.append(record)
    return findings


def _placeable_sizes(plan: PlanModel) -> dict[str, _Size]:
    """Type tag -> its plan size, across every catalog a countertop can sit on.

    Only a ``FurnitureType`` splits carcass from footprint (an island or a peninsula draws
    as one rectangle and is box for part of it); every other catalog's footprint depth *is*
    its carcass, because a dishwasher and a vanity are boxes all the way to the front.
    """
    sizes: dict[str, _Size] = {}
    for ftype in plan.library.furniture_types:
        width, depth = ftype.footprint
        carcass = ftype.carcass_depth if ftype.carcass_depth is not None else depth
        shape = (tuple(point.xy_m for point in ftype.footprint_shape.points)
                 if ftype.footprint_shape is not None else None)
        sizes[ftype.tag] = _Size(float(width.meters), float(depth.meters),
                                 float(carcass.meters), shape)
    for catalog in (plan.library.fixture_types, plan.library.appliance_types,
                    plan.library.equipment_types):
        for ptype in catalog:
            width, depth = ptype.footprint
            sizes[ptype.tag] = _Size(float(width.meters), float(depth.meters),
                                     float(depth.meters))
    return sizes


def _slab(el: Countertop, run: list[ResolvedCanvasObject], storey: str,
          sizes: dict[str, _Size]) -> tuple[ResolvedCountertop | None, list[Finding]]:
    """The derived slab: its polygon, its area, and the cantilever the check reads."""
    carcass = sizes[run[0].type_ref or ""].carcass_m
    overhang = el.overhang.meters
    depth = el.depth.meters if el.depth is not None else carcass + overhang
    unsupported = (el.unsupported_overhang.meters if el.unsupported_overhang is not None
                   else max(0.0, depth - carcass))
    # Where the slab's back edge sits, measured forward from the host's back face. A top
    # that starts at the carcass back has offset 0; the reference house's bar top is 15"
    # deep and 15" of it is cantilever, so it starts at the carcass FACE — which is what
    # this puts it at, rather than needing a second authored coordinate.
    offset = carcass - (depth - unsupported)
    if el.cantilever_side == "back":
        # The cantilever hangs behind the back face, the slab running forward from there.
        offset = -unsupported

    covered = [sizes[obj.type_ref or ""].width_m for obj in run]
    length = sum(covered) + sum(
        run_gap_m(first.footprint, second.footprint)
        for first, second in zip(run, run[1:], strict=False))
    extension = 0.0
    if el.length is not None and el.length.meters > length:
        # Longer than the run: the slab carries on past the last host's far end.
        extension = el.length.meters - length
        length = el.length.meters
    elif el.length is not None:
        # An authored length trims the LAST host from its far end: the slab keeps the start
        # of ``hosts[0]``, which is the end a run is measured from.
        remaining = el.length.meters - (length - covered[-1])
        if remaining <= 0.0:
            return None, [element_error(
                "integrity.countertop_run",
                f"countertop {el.tag}'s authored length is shorter than the hosts before "
                f"its last one, so the slab covers nothing of {run[-1].tag}", el.tag)]
        covered[-1] = min(covered[-1], remaining)
        length = el.length.meters

    last_angle = math.radians(run[-1].rotation_degrees)
    reverse_travel = len(run) > 1 and (
        (run[-1].position[0] - run[0].position[0]) * math.cos(last_angle)
        + (run[-1].position[1] - run[0].position[1]) * math.sin(last_angle)
    ) < 0
    # A run can travel against local +x (north-facing peninsula cabinets do).
    # Keep the last host's near end when trimming, or the slab acquires a gap.
    rects = [_covered_l(obj, sizes[obj.type_ref or ""], overhang)
             if sizes[obj.type_ref or ""].shape is not None
             else _covered_rect(obj, width, sizes[obj.type_ref or ""], offset, depth,
                                sizes[obj.type_ref or ""].width_m - width
                                if reverse_travel and obj is run[-1] else 0.0)
             for obj, width in zip(run, covered, strict=True)]
    if extension > 0.0:
        rects.append(_extension_rect(run, sizes[run[-1].type_ref or ""], extension, offset,
                                     depth))
    outline, area = _slab_outline(rects)
    return ResolvedCountertop(
        uid=el.uid, tag=el.tag, storey=storey, room=run[0].room,
        hosts=tuple(obj.tag for obj in run), material_ref=el.material_ref,
        thickness_m=el.thickness.meters, depth_m=depth, length_m=length,
        overhang_m=overhang, unsupported_overhang_m=unsupported, support=el.support,
        profile=el.profile, outline=outline, area_m2=area), []


def _covered_rect(obj: ResolvedCanvasObject, width: float, size: _Size,
                  offset: float, depth: float, start: float = 0.0) -> Polygon:
    """The slab's footprint over one host, in world coordinates.

    Local +y is the host's BACK — ``model/placeable_symbols`` draws every counter's front
    edge at local -y — so the slab runs forward from the back face by ``offset`` and covers
    ``depth``. ``width`` is measured from ``start`` along the host's local +x, counted from
    its local -x end, which is where an authored length starts.
    """
    angle = math.radians(obj.rotation_degrees)
    along = (math.cos(angle), math.sin(angle))
    back = (-math.sin(angle), math.cos(angle))
    origin = (obj.position[0] - along[0] * size.width_m / 2.0 + back[0] * size.depth_m / 2.0,
              obj.position[1] - along[1] * size.width_m / 2.0 + back[1] * size.depth_m / 2.0)
    corners = [(origin[0] + along[0] * step - back[0] * dive,
                origin[1] + along[1] * step - back[1] * dive)
               for step, dive in ((start, offset), (start + width, offset),
                                  (start + width, offset + depth), (start, offset + depth))]
    return Polygon(corners)


def _extension_rect(run: list[ResolvedCanvasObject], size: _Size, extension: float,
                    offset: float, depth: float) -> Polygon:
    """The slab carried ``extension`` past the last host, on the side the run travels to."""
    last = run[-1]
    angle = math.radians(last.rotation_degrees)
    along = (math.cos(angle), math.sin(angle))
    first = run[0].position if len(run) > 1 else (last.position[0] - along[0],
                                                  last.position[1] - along[1])
    travel = ((last.position[0] - first[0]) * along[0]
              + (last.position[1] - first[1]) * along[1])
    start = size.width_m if travel >= 0.0 else -extension
    return _covered_rect(last, extension, size, offset, depth, start)


def _covered_l(obj: ResolvedCanvasObject, size: _Size, overhang: float) -> Polygon:
    """The slab over an L host: its whole ring, oversailing only the faces inside its box.

    A leg's end and the two backs lie on the bounding box; the notch faces lie inside it, so
    buffering the ring and clipping back to the box puts ``overhang`` on the doors alone.
    """
    angle = math.radians(obj.rotation_degrees)
    cos, sin = math.cos(angle), math.sin(angle)

    def world(x: float, y: float) -> tuple[float, float]:
        return (obj.position[0] + x * cos - y * sin, obj.position[1] + x * sin + y * cos)

    ring = Polygon([world(x, y) for x, y in size.shape or ()])
    hw, hd = size.width_m / 2.0, size.depth_m / 2.0
    box = Polygon([world(-hw, -hd), world(hw, -hd), world(hw, hd), world(-hw, hd)])
    return ring.buffer(overhang, join_style=2).intersection(box)


def _slab_outline(rects: list[Polygon]) -> tuple[Ring, float]:
    """One polygon and its area, with the run's fillers closed over.

    A leftover under the filler tolerance is not a hole in the stone — the slab is cut
    straight across it — so the union is morphologically closed at half that width. Mitred,
    because every rectangle here is a rectangle and a rounded join would shave the corners.
    """
    merged = union_all(rects)
    closed = merged.buffer(_FILLER_CLOSE_M, join_style=2).buffer(-_FILLER_CLOSE_M,
                                                                join_style=2)
    if closed.geom_type != "Polygon" or closed.is_empty:
        closed = merged if merged.geom_type == "Polygon" else max(
            merged.geoms, key=lambda part: part.area)
    return tuple((float(x), float(y)) for x, y in closed.exterior.coords[:-1]), closed.area
