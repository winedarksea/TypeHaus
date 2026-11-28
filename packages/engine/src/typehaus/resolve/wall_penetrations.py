"""Every service crossing of a profiled-metal wall, with its kit (decision #142).

A crossing is found by geometry: each routed run (``run_polylines``, absolute z) and each
bonding conductor's path, intersected with the wall's band from the sheathing out to the
cladding. It takes a sleeve at the foam plane (the WRB) off ``PenetrationStandard`` and a
panel closure by kind:

* ``lineset`` (a refrigerant run): the cover system's wall inlet;
* ``behind_device`` (inside a derived block or strut pair): the block hides the hole; at a
  strut each nipple takes a boot;
* ``round`` (vent, radon, conduit, bond, a hydrant's barrel): an EPDM boot sized by OD, or
  the hydrant's own escutcheon when a fixture stands over it.

Skipped: a duct's crossing sealed by its ``serves_duct`` sleeve, or one in a rough opening of
6" or more (trimmed four sides by ``cladding_trim/openings``). An authored framed-wall sleeve
round a crossing wins: the record names it and mints no second solid.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.resolve.mount_blocks import penetration_standard, station_of, wall_face_frame

#: A segment this near parallel to the wall runs IN it (a cavity run), not through it.
_MIN_CROSSING_SINE = 0.5
_TOL_M = 0.0254
_CLEAR_M = 0.125 * 0.0254  # a block's foot over a boot base's edge


@dataclass(frozen=True)
class ResolvedWallPenetration:
    uid: str
    tag: str
    run_tag: str
    run_kind: str  # pipe | duct | conduit | bond
    system: str | None
    wall_tag: str
    storey: str
    kind: str  # lineset | round | behind_device
    station_m: float
    z_m: float
    #: What passes the panel: the pipe, the lagged bundle or the conductor.
    outside_d_m: float
    origin: tuple[float, float]
    tangent: tuple[float, float]
    normal: tuple[float, float]
    #: Sheathing face to cladding face: the sleeve's run through the foam and cavity.
    depth_m: float
    sleeve_d_m: float | None
    sleeve_product: str | None
    #: boot | inlet | escutcheon | block | strut_boot | None (no row fits)
    closure: str | None
    closure_product: str | None = None
    boot_size: str | None = None
    boot_base_m: tuple[float, float] | None = None
    boot_height_m: float = 0.0
    boot_conforms: bool = False
    min_trimmed_seal_m: float | None = None
    sleeve_ref: str | None = None
    opening_ref: str | None = None
    device_ref: str | None = None

    def point(self, out: float = 0.0) -> tuple[float, float, float]:
        return (self.origin[0] + self.tangent[0] * self.station_m + self.normal[0] * out,
                self.origin[1] + self.tangent[1] * self.station_m + self.normal[1] * out,
                self.z_m)


def metal_walls(model: Any) -> list[Any]:
    from typehaus.resolve.cladding_trim.openings import is_profiled_metal_wall
    from typehaus.resolve.panel_flats import cladding_layer

    return [w for w in model.walls if is_profiled_metal_wall(model, w)
            and cladding_layer(model, w) is not None]


def _band(wall: Any) -> Any:
    """Plan polygon from the outermost sheathing out to the cladding."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    index = max((i for i, ly in enumerate(wall.layers) if ly.function == "sheathing"),
                default=None)
    layers = [ly for ly in wall.layers[index or 0:] if not ly.is_cavity and len(ly.polygon) >= 3]
    return union_all([Polygon(ly.polygon) for ly in layers])


def _depth(wall: Any) -> float:
    index = max((i for i, ly in enumerate(wall.layers) if ly.function == "sheathing"),
                default=0)
    return sum(ly.thickness_m for ly in wall.layers[index + 1:] if not ly.is_cavity)


def _polylines(model: Any) -> list[tuple[str, str, tuple, tuple, str | None]]:
    from typehaus.resolve.mep_envelopes import run_polylines, run_systems

    systems = run_systems(model)
    out = [(kind, tag, path, z, systems.get(tag, (kind, None))[1])
           for kind, tag, path, z in run_polylines(model) if z]
    out += [("bond", b.tag, tuple(p[:2] for p in b.path), tuple(p[2] for p in b.path), None)
            for b in model.grounding.bonds if len(b.path) >= 2]
    return out


def _crossings(model: Any, walls: list[Any]):
    """Yield ``(wall, kind, tag, system, (x, y), z)`` per run segment through a wall band."""
    from shapely.geometry import LineString

    from typehaus.resolve.geometry_walls import body_top_at

    bands = [(w, _band(w)) for w in walls]
    for kind, tag, path, z, system in _polylines(model):
        for a, b, za, zb in zip(path, path[1:], z, z[1:], strict=False):
            seg = LineString([a, b])
            if seg.length < 1e-4:
                continue
            for wall, band in bands:
                if band.is_empty or not seg.intersects(band):
                    continue
                (x0, y0), (x1, y1) = wall.axis
                wl = math.hypot(x1 - x0, y1 - y0) or 1.0
                sine = abs(((b[0] - a[0]) * (y1 - y0) - (b[1] - a[1]) * (x1 - x0))
                           / (seg.length * wl))
                if sine < _MIN_CROSSING_SINE:
                    continue
                hit = seg.intersection(band)
                c = hit.centroid
                t = math.dist(a, (c.x, c.y)) / seg.length
                zc = za + (zb - za) * t
                if wall.z0_m - 1e-3 <= zc <= body_top_at(wall, c.x, c.y) + 1e-3:
                    yield wall, kind, tag, system, (c.x, c.y), zc


def derive_wall_penetrations(model: Any) -> None:
    from typehaus.resolve.mount_blocks import derive_mount_blocks

    derive_mount_blocks(model)
    standard = penetration_standard(model.plan)
    if standard is None:
        return
    walls = metal_walls(model)
    from typehaus.resolve.mep_envelopes import insulation_thickness_m, run_radii

    # What passes the panel is the run's SURFACE: run_radii is bare of lagging, so add it
    # (a lineset's bare radius plus its lagging is the bundle circle).
    lagging = {r.tag: insulation_thickness_m(r.insulation) or 0.0 for r in model.pipe_runs}
    radii = {tag: r + lagging.get(tag, 0.0) for tag, r in run_radii(model).items()}
    bonds = {b.tag: b for b in model.grounding.bonds}
    seen: dict[tuple[str, str], int] = {}
    for wall, kind, tag, system, xy, z in _crossings(model, walls):
        station = station_of(wall, xy)
        if _skipped(model, wall, tag, station, z):
            continue
        key = (tag, wall.tag)
        seen[key] = seen.get(key, 0) + 1
        suffix = "" if seen[key] == 1 else f"-{seen[key]}"
        model.wall_penetrations.append(_record(
            model, standard, wall, kind, tag, system, station, z, radii, bonds, suffix))
    _lift_blocks_off_boots(model)
    from typehaus.resolve.wall_penetration_solids import penetration_solids

    penetration_solids(model, standard)


def _lift_blocks_off_boots(model: Any) -> None:
    """A strap block whose foot would sit on a boot's base stands on the base's top edge."""
    from dataclasses import replace

    for i, block in enumerate(model.mount_blocks):
        if block.kind != "strap_block":
            continue
        for pen in model.wall_penetrations:
            if pen.wall_tag != block.wall_tag or not pen.boot_base_m:
                continue
            half = pen.boot_base_m[0] / 2
            top = pen.z_m + half
            if (abs(pen.station_m - (block.station_lo_m + block.station_hi_m) / 2)
                    < half + block.width_m / 2 and pen.z_m < block.z0_m < top):
                rise = top + _CLEAR_M - block.z0_m
                block = replace(block, z0_m=block.z0_m + rise, z1_m=block.z1_m + rise,
                                top_z=None if block.top_z is None
                                else tuple(z + rise for z in block.top_z))
        model.mount_blocks[i] = block


def _record(model: Any, standard: Any, wall: Any, kind: str, tag: str, system: str | None,
            station: float, z: float, radii: dict, bonds: dict,
            suffix: str) -> ResolvedWallPenetration:
    from typehaus.resolve.grounding import AWG_OD_IN

    origin, tangent, normal = wall_face_frame(wall)
    bond = bonds.get(tag) if kind == "bond" else None
    od = (AWG_OD_IN.get(bond.size, 0.0) * 0.0254 if bond is not None
          else 2 * radii.get(tag, 0.0))
    sleeve = (standard.bond_sleeve_for(bond.size) if bond is not None
              else standard.sleeve_for(od))
    authored = _authored_sleeve(model, wall, xy=_xy(origin, tangent, station), z=z)
    opening = _opening(model, wall, tag, station, z)
    mount = next((m for m in model.mount_blocks if m.wall_tag == wall.tag
                  and m.kind in ("block", "flat", "strut")
                  and m.station_lo_m - 1e-6 <= station <= m.station_hi_m + 1e-6
                  and m.z0_m - 1e-6 <= z <= m.z1_m + 1e-6), None)
    fixture = _fixture_over(model, wall, station, z)
    if system == "refrigerant":
        cls, closure = "lineset", "inlet"
    elif mount is not None:
        cls, closure = "behind_device", ("strut_boot" if mount.kind == "strut" else "block")
    else:
        cls, closure = "round", ("escutcheon" if fixture is not None else "boot")
    boot = standard.boot_for(od) if closure in ("boot", "strut_boot") else None
    inlet = standard.lineset_inlet if closure == "inlet" else None
    product = (boot.product_ref if boot is not None
               else inlet.product_ref if inlet is not None
               else mount.product if mount is not None else None)
    if (closure in ("boot", "strut_boot") and boot is None) or (closure == "inlet"
                                                                  and inlet is None):
        closure = None  # no row: graded by integrity.wall_penetration_closure
    return ResolvedWallPenetration(
        uid=f"{wall.uid}-pen-{tag}{suffix}", tag=f"WP-{tag}-{wall.tag}{suffix}", run_tag=tag,
        run_kind=kind, system=system, wall_tag=wall.tag, storey=wall.storey, kind=cls,
        station_m=station, z_m=z, outside_d_m=od, origin=origin, tangent=tangent,
        normal=normal, depth_m=_depth(wall),
        sleeve_d_m=sleeve.sleeve_diameter.meters if sleeve is not None else None,
        sleeve_product=sleeve.product_ref if sleeve is not None else None,
        closure=closure, closure_product=product,
        boot_size=boot.size if boot is not None else None,
        boot_base_m=((boot.base_width.meters, boot.base_height.meters)
                     if boot is not None else None),
        boot_height_m=boot.cone_height.meters if boot is not None else 0.0,
        boot_conforms=bool(boot and boot.conforms_to_ribs),
        min_trimmed_seal_m=(boot.min_trimmed_seal.meters
                            if boot is not None and boot.min_trimmed_seal else None),
        sleeve_ref=authored, opening_ref=opening,
        device_ref=(mount.holds[0] if mount is not None
                    else fixture if fixture is not None else None))


def _xy(origin: tuple[float, float], tangent: tuple[float, float],
        station: float) -> tuple[float, float]:
    return origin[0] + tangent[0] * station, origin[1] + tangent[1] * station


def _skipped(model: Any, wall: Any, tag: str, station: float, z: float) -> bool:
    """A duct's own sealed sleeve, or a rough opening big enough to be trimmed."""
    from typehaus.resolve.cladding_trim.openings import SMALL_PENETRATION_M

    if any(s.serves_duct == tag and s.host_slab == wall.tag for s in model.sleeves):
        return True
    return any(max(o.width_m, o.height_m) >= SMALL_PENETRATION_M
               for o in _openings_at(model, wall, station, z))


def _openings_at(model: Any, wall: Any, station: float, z: float) -> list[Any]:
    out = []
    for o in model.openings:
        if o.host_wall != wall.tag:
            continue
        z0 = wall.base_ref_z_m + o.sill_m
        if (abs(station - o.center_along_m) <= o.width_m / 2 + _TOL_M
                and z0 - _TOL_M <= z <= z0 + o.height_m + _TOL_M):
            out.append(o)
    return out


def _opening(model: Any, wall: Any, tag: str, station: float, z: float) -> str | None:
    els = {el.tag: el for el in model.plan.all_elements() if el.element_kind == "RoughOpening"}
    return next((o.tag for o in _openings_at(model, wall, station, z)
                 if tag in getattr(els.get(o.tag), "penetration_for", ())), None)


def _authored_sleeve(model: Any, wall: Any, xy: tuple[float, float], z: float) -> str | None:
    for s in model.sleeves:
        if s.host_slab != wall.tag or s.host_category != "framed_wall" or s.serves_duct:
            continue
        if (math.dist(s.center, xy) <= 0.3 and s.center_z_m is not None
                and abs(s.center_z_m - z) <= s.sleeve_d_m / 2 + _TOL_M):
            return s.tag
    return None


def _fixture_over(model: Any, wall: Any, station: float, z: float) -> str | None:
    """An exterior fixture (a hydrant) whose body stands over the crossing."""
    _origin, _tangent, normal = wall_face_frame(wall)
    (x0, y0), (x1, y1) = wall.axis
    left = (-(y1 - y0), x1 - x0)
    outer = "left" if left[0] * normal[0] + left[1] * normal[1] > 0 else "right"
    for obj in model.canvas_objects:
        if (obj.kind != "Fixture" or obj.attachment_wall != wall.tag
                or obj.attachment_face != outer or obj.body_z1_m is None):
            continue
        stations = [station_of(wall, p) for p in obj.footprint]
        if (min(stations) - _TOL_M <= station <= max(stations) + _TOL_M
                and obj.body_z0_m - _TOL_M <= z <= obj.body_z1_m + _TOL_M):
            return obj.tag
    return None
