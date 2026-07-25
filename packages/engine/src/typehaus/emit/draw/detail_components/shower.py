"""Shower detail vocabulary — recess, tile over backer, glass panel, HRV takeoff.

Reference: ``sauna_shower_basement_detail_ifc.png``; dimensions from
``saunashowerdetail.json`` ``shower`` via ``config``.

There is no shower *assembly* — a shower is a fixture standing in a room — so the
recognition gate is the fixture itself: a resolved canvas object whose ``FixtureType``
publishes ``plan_symbol="shower"``, cut by the section plane. Everything is then derived
from that footprint and the walls around it:

* **recess** — the 4" drop in the floor structure that makes the pan curbless, finished
  with a mortar bed falling to a center drain;
* **tile over backer** — 3/4" tile on 1" cement board, on whichever footprint edge a wall
  face actually abuts (read from the resolved walls, never assumed);
* **glass** — the 1/2" frameless panel on the open edge, floated a 1" gap above the pan
  so the drawn enclosure ventilates the way the built one must;
* **HRV takeoff** — drawn from ``model.ducts``: a resolved run crossing the cut over the
  shower is the exhaust that keeps the enclosure from growing things. Its *size* comes
  from the resolved duct; only its drawn elevation is a convention, because a
  ``ResolvedDuct`` carries no z.

Every part self-gates on its subject being in the cut, and none of it mutates construction
geometry. Nodes are ``Polyline``/``Hatch`` only, tagged ``detail-component:<name>``.
Section coordinates: ``u`` is the in-section axis, ``z`` is world z, both in model inches.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components import config as cfg
from typehaus.emit.draw.detail_components.config import M_TO_IN
from typehaus.emit.draw.detail_components.geometry import (
    rect_region,
    wall_cut_bounds_m,
)
from typehaus.emit.draw.scene import IRNode


def _fixture_type(model, type_ref):
    return next((t for t in model.plan.library.fixture_types if t.tag == type_ref), None)


def shower_objects_in_cut(model, direction: str, station: float):
    """``(canvas_object, fixture_type, (u_lo_m, u_hi_m))`` per shower the plane crosses."""
    out = []
    for obj in model.canvas_objects:
        ftype = _fixture_type(model, obj.type_ref)
        if ftype is None or getattr(ftype, "plan_symbol", None) != "shower":
            continue
        if not obj.footprint:
            continue
        xs = [p[0] for p in obj.footprint]
        ys = [p[1] for p in obj.footprint]
        # ``direction`` is the u-axis; the cut plane is at ``station`` on the other axis.
        cross_lo, cross_hi = (min(xs), max(xs)) if direction == "y" else (min(ys), max(ys))
        if not (cross_lo <= station <= cross_hi):
            continue
        span = (min(ys), max(ys)) if direction == "y" else (min(xs), max(xs))
        out.append((obj, ftype, span))
    return out


def _walled_sides(model, direction: str, station: float, u_lo_m: float, u_hi_m: float,
                  z_lo_m: float, z_hi_m: float) -> set:
    """Which footprint ends ("low"/"high") a wall face abuts — those take backer + tile."""
    sides: set = set()
    tol = cfg.SHOWER_WALL_ABUT_TOLERANCE_M
    for wall in model.walls:
        wall_top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
        if wall.z0_m > z_hi_m or wall_top < z_lo_m:
            continue
        lo, hi = wall_cut_bounds_m(wall, direction, station)
        if lo is None:
            continue
        if lo <= u_lo_m <= hi or 0.0 <= u_lo_m - hi <= tol:
            sides.add("low")
        if lo <= u_hi_m <= hi or 0.0 <= lo - u_hi_m <= tol:
            sides.add("high")
    return sides


def shower_recess(u_lo: float, u_hi: float, floor_z: float) -> list[IRNode]:
    """The 4" curbless recess: a mortar bed dropped into the floor, draining at center."""
    nodes = rect_region(u_lo, floor_z - cfg.SHOWER_RECESS_IN, u_hi, floor_z,
                        "shower-recess", "sealant", None, lineweight=0.35)
    center = (u_lo + u_hi) / 2.0
    nodes += rect_region(center - cfg.SHOWER_DRAIN_WIDTH_IN / 2.0,
                         floor_z - cfg.SHOWER_RECESS_IN - cfg.SHOWER_DRAIN_DEPTH_IN,
                         center + cfg.SHOWER_DRAIN_WIDTH_IN / 2.0,
                         floor_z - cfg.SHOWER_RECESS_IN + cfg.SHOWER_DRAIN_DEPTH_IN,
                         "shower-drain", "metal-dark", "SOLID", lineweight=0.4)
    return nodes


def shower_wall_lining(u_lo: float, u_hi: float, floor_z: float, height: float,
                       walled: set) -> list[IRNode]:
    """Tile over cement backer on each walled side, plus the tiled pan surface.

    The backer goes against the wall face, the tile inboard of it, both running from the
    recess bottom to the enclosure top — tile stopping at the floor line would put the
    seam exactly where the water stands.
    """
    z0 = floor_z - cfg.SHOWER_RECESS_IN
    z1 = floor_z + height
    nodes: list[IRNode] = []
    linings = {"low": 0.0, "high": 0.0}
    for side, in_sign, face_u in (("low", 1.0, u_lo), ("high", -1.0, u_hi)):
        if side not in walled:
            continue
        backer_in = face_u + in_sign * cfg.SHOWER_BACKER_IN
        nodes += rect_region(face_u, z0, backer_in, z1,
                             "shower-backer", "gwb", "gypsum", lineweight=0.3)
        nodes += rect_region(backer_in, z0, backer_in + in_sign * cfg.SHOWER_TILE_IN, z1,
                             "shower-tile", "tile", "metal", lineweight=0.35)
        linings[side] = cfg.SHOWER_BACKER_IN + cfg.SHOWER_TILE_IN
    # Pan surface: tile across the recess top, between whatever wall linings exist.
    nodes += rect_region(u_lo + linings["low"], floor_z - cfg.SHOWER_TILE_IN,
                         u_hi - linings["high"], floor_z,
                         "shower-tile", "tile", "metal", lineweight=0.35)
    return nodes


def shower_glass(u_lo: float, u_hi: float, floor_z: float, height: float,
                 walled: set) -> list[IRNode]:
    """The 1/2" frameless panel on each open edge, floated 1" above the pan."""
    nodes: list[IRNode] = []
    for side, in_sign, edge_u in (("low", 1.0, u_lo), ("high", -1.0, u_hi)):
        if side in walled:
            continue
        nodes += rect_region(edge_u, floor_z + cfg.SHOWER_GLASS_GAP_IN,
                             edge_u + in_sign * cfg.SHOWER_GLASS_IN, floor_z + height,
                             "shower-glass", None, "glass", lineweight=0.35)
    return nodes


def _duct_crossing_u(duct, direction: str, station: float):
    """Where (in u, metres) a duct's path crosses the cut plane, or None."""
    for (x0, y0), (x1, y1) in zip(duct.path, duct.path[1:]):
        cross0, cross1 = (x0, x1) if direction == "y" else (y0, y1)
        u0, u1 = (y0, y1) if direction == "y" else (x0, x1)
        lo, hi = min(cross0, cross1), max(cross0, cross1)
        if not (lo <= station <= hi):
            continue
        if hi - lo < 1e-9:
            return (u0 + u1) / 2.0
        t = (station - cross0) / (cross1 - cross0)
        return u0 + (u1 - u0) * t
    return None


def shower_hrv_duct(model, direction: str, station: float, u_lo_m: float, u_hi_m: float,
                    top_z_in: float) -> list[IRNode]:
    """The exhaust takeoff over the shower, drawn from the resolved duct that serves it.

    A run in ``model.ducts`` whose path crosses the cut within reach of the shower
    footprint is the HRV pull; its cross-section draws at its resolved width x depth.
    No crossing run means no takeoff is drawn — inventing one would be a drawing that
    lies about the ventilation the house actually has.
    """
    nodes: list[IRNode] = []
    for duct in model.ducts:
        u_m = _duct_crossing_u(duct, direction, station)
        if u_m is None:
            continue
        if not (u_lo_m - cfg.SHOWER_DUCT_REACH_M <= u_m <= u_hi_m + cfg.SHOWER_DUCT_REACH_M):
            continue
        u = u_m * M_TO_IN
        width = duct.width_m * M_TO_IN
        depth = duct.depth_m * M_TO_IN
        z0 = top_z_in + cfg.SHOWER_HRV_CLEAR_IN
        nodes += rect_region(u - width / 2.0, z0, u + width / 2.0, z0 + depth,
                             "shower-hrv-duct", "metal", "metal", lineweight=0.35)
    return nodes


def shower_components(model, crop, direction: str, station: float) -> list[IRNode]:
    """Everything the shower draws for one cut — recess, linings, glass, HRV takeoff."""
    if crop is None:
        return []
    (cu0, cz0), (cu1, cz1) = crop
    crop_u_lo, crop_u_hi = min(cu0, cu1) * M_TO_IN, max(cu0, cu1) * M_TO_IN
    crop_z_lo, crop_z_hi = min(cz0, cz1) * M_TO_IN, max(cz0, cz1) * M_TO_IN
    nodes: list[IRNode] = []
    for obj, ftype, (u_lo_m, u_hi_m) in shower_objects_in_cut(model, direction, station):
        u_lo, u_hi = u_lo_m * M_TO_IN, u_hi_m * M_TO_IN
        if u_hi <= crop_u_lo or u_lo >= crop_u_hi:
            continue
        floor_z = obj.z_m * M_TO_IN
        if not (crop_z_lo <= floor_z <= crop_z_hi):
            continue
        height = getattr(ftype, "height", None)
        height_in = height.meters * M_TO_IN if height is not None else cfg.SHOWER_ENCLOSURE_H_IN
        walled = _walled_sides(model, direction, station, u_lo_m, u_hi_m,
                               obj.z_m + 0.1, obj.z_m + 1.5)
        nodes += shower_recess(u_lo, u_hi, floor_z)
        nodes += shower_wall_lining(u_lo, u_hi, floor_z, height_in, walled)
        nodes += shower_glass(u_lo, u_hi, floor_z, height_in, walled)
        nodes += shower_hrv_duct(model, direction, station, u_lo_m, u_hi_m,
                                 floor_z + height_in)
    return nodes


def shower_overlay_for_slice(model, view) -> list[IRNode]:
    """Shower vocabulary for an authored ``Slice`` (documentation-only path).

    Same shape as ``sauna_overlay_for_slice``: the authored-Slice pipeline bypasses the
    derived detail machinery, so a hand-authored shower section would otherwise get none
    of the enclosure vocabulary. Self-gated on a shower fixture genuinely being in the
    cut; adds nothing to any other Slice and never mutates construction geometry.
    """
    if view.crop is None or view.cut_origin is None:
        return []
    direction = view.cut_direction or "x"
    station = view.cut_origin.xy_m[1] if direction == "x" else view.cut_origin.xy_m[0]
    crop = (view.crop[0].xy_m, view.crop[1].xy_m)
    return shower_components(model, crop, direction, station)
