"""A wall-mounted placeable stands on a wall face, and under the ceiling and the wall top.

Promoted from the catlin contract test that used to be the only thing catching a device
left inside the studs after a retype. The body is graded, not the authored point:

* ``integrity.wall_mount_on_face`` — the body neither reaches more than 1/4" into its host
  (a recessed body is allowed to) nor floats more than 1/4" beyond the ``normal_gap`` its
  attachment declares (a rod on brackets). A host is any wall whose layers are present at
  the body's height, a column solid, or a soffit's side. Hosts are searched by z, never by
  storey — a garden wall is filed on the storey that builds it, a device on its feeder's.
* ``integrity.wall_mount_below_ceiling`` — the body's top stays under the surface above it
  and under its host wall's top at that station. ``Mount.elevation`` is the BASE, so a
  cabinet mounted "high on the wall" can stand through the deck with nothing else noticing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import inch
from typehaus.resolve.geometry_walls import wall_top_at
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedModel
from typehaus.resolve.overhead import OverheadIndex
from typehaus.resolve.overlay import union_all
from typehaus.resolve.placeable_bodies import bodied

_ON_FACE = "integrity.wall_mount_on_face"
_BELOW = "integrity.wall_mount_below_ceiling"
_TOL_M = inch(0.25).meters
_EPS = 1e-6
#: Stand-off a bodied-equipment host allows on top of the declared gap (a grille on a box).
_EQUIPMENT_STANDOFF_M = inch(0.5).meters


@dataclass(frozen=True)
class Host:
    tag: str
    overlap_m2: float
    gap_m: float
    wall: object | None  # the ResolvedWall, or None for a column
    standoff_m: float = 0.0  # allowed gap for this host kind, beyond the declared one


def wall_mounts(model: ResolvedModel) -> list[ResolvedCanvasObject]:
    return [obj for obj in model.canvas_objects
            if obj.mount is not None and obj.mount.kind.value == "wall"]


_HostRow = tuple[str, object, object | None, float]


def _hosts_at(model: ResolvedModel, z: float) -> list[_HostRow]:
    """(tag, solid, wall, standoff) for every wall, column and soffit at ``z``."""
    out: list[_HostRow] = []
    for wall in model.walls:
        if wall.z1_m <= z + _EPS or wall.z0_m >= z + _EPS:
            continue
        present = [Polygon(layer.polygon) for layer in wall.layers
                   if len(layer.polygon) >= 3
                   and (layer.z0_m is None or layer.z0_m <= z + _EPS)
                   and (layer.z1_m is None or layer.z1_m >= z - _EPS)]
        present = [p for p in present if p.is_valid and p.area > 1e-9]
        if present:
            out.append((wall.tag, union_all(present), wall, 0.0))
    for solid in model.solids:
        if (solid.category == "column" and len(solid.outline) >= 3
                and solid.z0_m <= z + _EPS and solid.z1_m >= z - _EPS):
            out.append((solid.tag, Polygon(solid.outline), None, 0.0))
    # A soffit's side is a face too: a side-wall grille on a dropped box hangs on it.
    for soffit in model.soffits:
        if (len(soffit.outline) >= 3
                and soffit.z0_m <= z + _EPS and soffit.z1_m >= z - _EPS):
            out.append((soffit.tag, Polygon(soffit.outline), None, 0.0))
    return out


def _fallback_hosts(model: ResolvedModel, obj: ResolvedCanvasObject,
                    z: float) -> list[_HostRow]:
    """Bodies a mount may hang on when no wall, column or soffit is there: equipment (a
    return grille on a plenum's side, with its 1/2" stand-off) and the mount's own duct stub."""
    out = [(unit.tag, Polygon(unit.footprint), None, _EQUIPMENT_STANDOFF_M)
           for unit in bodied(model)
           if unit.tag != obj.tag and len(unit.footprint) >= 3
           and unit.body_z0_m is not None and unit.body_z1_m is not None
           and unit.body_z0_m <= z + _EPS and unit.body_z1_m >= z - _EPS]
    return out + _own_stub_hosts(model, obj, z)


def _own_stub_hosts(model: ResolvedModel, obj: ResolvedCanvasObject,
                    z: float) -> list[_HostRow]:
    """The register's own duct, when it is a short straight stub: a grille on its boot."""
    plan = getattr(model, "plan", None)
    ref = getattr(plan.by_tag(obj.tag), "duct_ref", None) if plan is not None else None
    duct = next((d for d in model.ducts if d.tag == ref), None) if ref else None
    if duct is None or len(duct.path) != 2 or duct.diameter_m is not None or not duct.z_m:
        return []
    top = obj.body_z1_m if obj.body_z1_m is not None else z
    if duct.z_m[0] - duct.depth_m / 2 > top + _EPS or duct.z_m[0] + duct.depth_m / 2 < z - _EPS:
        return []
    ring = LineString(duct.path).buffer(duct.width_m / 2, cap_style="flat")
    return [(duct.tag, ring, None, 0.0)]


def best_host(model: ResolvedModel, obj: ResolvedCanvasObject) -> Host | None:
    """The host the body bears on: most overlap, then least gap."""
    z = obj.body_z0_m if obj.body_z0_m is not None else obj.z_m
    body = Polygon(obj.footprint)
    if obj.kind == "Furniture" and obj.host_fixture_ref is not None:
        host = next((item for item in model.canvas_objects
                     if item.tag == obj.host_fixture_ref and item.kind == "Fixture"
                     and item.storey == obj.storey and item.room == obj.room), None)
        if (host is None or host.body_z0_m is None or host.body_z1_m is None
                or host.body_z0_m > z + _EPS
                or host.body_z1_m < (obj.body_z1_m or z) - _EPS):
            return None
        fixture_types = getattr(getattr(getattr(model, "plan", None), "library", None),
                                "fixture_types", ())
        fixture_type = next((entry for entry in fixture_types
                             if entry.tag == host.type_ref), None)
        cabinet = getattr(fixture_type, "cabinet_body_footprint", None)
        if cabinet is not None:
            from typehaus.model.placeable_symbols import place_local

            solid = Polygon(place_local([point.xy_m for point in cabinet.points],
                                        host.position, host.rotation_degrees))
        else:
            solid = Polygon(host.footprint)
        return Host(host.tag, solid.intersection(body).area, solid.distance(body), None)
    best = _best_of(_hosts_at(model, z), body, None)
    if best is None or (best.overlap_m2 <= 1e-9 and best.gap_m > _TOL_M):
        best = _best_of(_fallback_hosts(model, obj, z), body, best)  # only when none bears
    return best


def _best_of(rows: list[_HostRow], body: Polygon, best: Host | None) -> Host | None:
    for tag, solid, wall, standoff in rows:
        overlap = solid.intersection(body).area
        gap = solid.distance(body)
        if best is None or (overlap, -gap) > (best.overlap_m2, -best.gap_m):
            best = Host(tag, overlap, gap, wall, standoff)
    return best


def _borne_at(model: ResolvedModel, obj: ResolvedCanvasObject, z: float) -> bool:
    """Something still stands behind the body at ``z``: a wall stacked on its host."""
    body = Polygon(obj.footprint)
    return any(solid.distance(body) <= _TOL_M for _, solid, _, _ in _hosts_at(model, z))


@check(Tier.INTEGRITY, _ON_FACE)
def wall_mount_on_face(ctx: CheckContext) -> list[Finding]:
    mounts = wall_mounts(ctx.model)
    if not mounts:
        return [not_applicable(_ON_FACE, "no placeable is wall-mounted")]
    out: list[Finding] = []
    for obj in mounts:
        host = best_host(ctx.model, obj)
        if host is None:
            out.append(failed(_ON_FACE, f"{obj.tag} is wall-mounted but no wall or column "
                                        "stands at its mounting height", tags=(obj.tag,)))
            continue
        body = Polygon(obj.footprint)
        # Positions are authored to 1/8": grade how far the body reaches past the face.
        reach = host.overlap_m2 / math.sqrt(body.area) if body.area > 0 else 0.0
        recessed = obj.mount.recessed_into_host_surface
        if reach > _TOL_M and not recessed:
            out.append(failed(
                _ON_FACE, f"{obj.tag} is buried {reach / inch(1).meters:.2f}\" into "
                          f"{host.tag}", tags=(obj.tag, host.tag),
                fix="host it with location=Location(attachment=WallAttachment(...))"))
        elif (host.overlap_m2 <= 1e-9
              and host.gap_m > max(_declared_gap(ctx, obj), host.standoff_m) + _TOL_M):
            out.append(failed(
                _ON_FACE, f"{obj.tag} floats {host.gap_m / inch(1).meters:.1f}\" off "
                          f"{host.tag}", tags=(obj.tag, host.tag),
                fix="host it with location=Location(attachment=WallAttachment(...))"))
    if not out:
        return [passed(_ON_FACE, f"all {len(mounts)} wall-mounted bodies bear on a face")]
    return out


def _declared_gap(ctx: CheckContext, obj: ResolvedCanvasObject) -> float:
    """The stand-off an attachment states on purpose; 0 for a free point."""
    element = ctx.plan.by_tag(obj.tag)
    attachment = getattr(getattr(element, "location", None), "attachment", None)
    return max(0.0, attachment.normal_gap.meters) if attachment is not None else 0.0


@check(Tier.INTEGRITY, _BELOW)
def wall_mount_below_ceiling(ctx: CheckContext) -> list[Finding]:
    mounts = wall_mounts(ctx.model)
    if not mounts:
        return [not_applicable(_BELOW, "no placeable is wall-mounted")]
    index = OverheadIndex(ctx.model, finishes=True)
    out: list[Finding] = []
    graded = 0
    for obj in mounts:
        if obj.body_z0_m is None or obj.body_z1_m is None:
            continue  # a type with no stated height has no top to grade
        graded += 1
        top = obj.body_z1_m
        over = index.lowest_above(*obj.position, obj.body_z0_m)
        if over is not None and top > over.z_m + _TOL_M:
            out.append(failed(
                _BELOW, f"{obj.tag}'s top stands {(top - over.z_m) / inch(1).meters:.2f}\" "
                        f"above the underside of {over.tag}", tags=(obj.tag, over.tag),
                fix="lower its Mount.elevation — it is the BASE of the body"))
            continue
        host = best_host(ctx.model, obj)
        if host is not None and host.wall is not None:
            wall_top = wall_top_at(host.wall, *obj.position)
            if top > wall_top + _TOL_M and not _borne_at(ctx.model, obj, top - _TOL_M):
                out.append(failed(
                    _BELOW, f"{obj.tag}'s top stands {(top - wall_top) / inch(1).meters:.2f}\""
                            f" above the top of its host wall {host.tag}",
                    tags=(obj.tag, host.tag),
                    fix="lower its Mount.elevation — it is the BASE of the body"))
    if not out:
        return [passed(_BELOW, f"{graded} wall-mounted bodies stand under their ceiling and "
                               f"host wall top ({len(mounts) - graded} state no height)")]
    return out
