"""Sauna detail vocabulary — the liner base, and the room-scale fit-out.

References: ``sauna_basement_wall_detail_ifc.png`` and ``sauna_shower_basement_detail_ifc.png``.
Dimensions come from ``saunashowerdetail.json`` via ``config``.

Two scales live here, and the distinction is what keeps them from drawing in the wrong crop:

* **Per wall** — ``sauna_liner_base``: the bottom 6" of the hot-side liner is fiber-cement
  baseboard rather than furring + T&G, flashed at its top, with the liquid floor membrane
  run up its face.
* **Per room** — benches, heater clearance, sloped floor and drop ceiling. These read the
  sauna's interior u-span between the innermost faces of the walls the cut crosses, plus the
  floor slab and ceiling structure in frame, and draw once for the room.

Both self-gate on their subject being genuinely cut, so a wall-top junction crop gets nothing
while a floor-to-ceiling sauna section gets the full room.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components import config as cfg
from typehaus.emit.draw.detail_components.config import LAYER
from typehaus.emit.draw.detail_components.geometry import (
    closed_region,
    flashing_nodes,
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    path_from_steps,
    rect_points,
    rect_region,
    slab_at_junction,
    wall_cut_bounds_m,
    wall_in_frame,
)
from typehaus.emit.draw.scene import IRNode, Polyline
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals


def sauna_liner_base(model, wall, crop, direction, station) -> list[IRNode]:
    """Fiber-cement baseboard + flashing + up-turned floor membrane at the liner base.

    A sauna's hot side runs wet at the floor, and T&G cedar sitting in that water rots. The
    bottom 6" is therefore fiber cement, flashed at its head so water sheds out of the wall
    rather than behind the liner, with the floor membrane returned up its face.
    """
    is_outboard_high = outboard_is_high(wall, direction, station)
    if is_outboard_high is None:
        return []
    u_lo, u_hi = wall_cut_bounds_m(wall, direction, station)
    if u_lo is None:
        return []
    hot_face_m = u_hi if is_outboard_high else u_lo  # liner's finished (interior) face
    slab = slab_at_junction(model, crop, direction, station, hot_face_m)
    if slab is None:
        return []
    intervals = layer_intervals(wall, direction, station)
    bands = [iv for iv in (outermost_with_function(intervals, "finish"),
                           outermost_with_function(intervals, "furring")) if iv is not None]
    if not bands:
        return []
    lo = min(min(iv[0], iv[1]) for iv in bands)
    hi = max(max(iv[0], iv[1]) for iv in bands)
    hot_face = hot_face_m / M_PER_IN
    in_sign = -1.0 if is_outboard_high else 1.0  # toward the wall core, away from the room
    slab_top = slab.z1_m / M_PER_IN
    board_top = slab_top + cfg.SAUNA_BASEBOARD_IN

    nodes = rect_region(lo, slab_top, hi, board_top,
                        "sauna-baseboard", "fiber-cement", "metal", lineweight=0.35)
    band_width = abs(hi - lo)
    flash = path_from_steps((hot_face - in_sign * band_width,
                             board_top + cfg.SAUNA_FLASH_IN),
                            [(in_sign * band_width, 0.0),
                             (0.0, -cfg.SAUNA_FLASH_IN * 2.0)])
    nodes += flashing_nodes(flash, tag="sauna-baseboard-flashing")
    nodes += rect_region(hot_face, slab_top, hot_face - in_sign * cfg.SAUNA_MEMBRANE_IN,
                         board_top, "sauna-membrane", "air-barrier", "membrane",
                         lineweight=0.25)
    return nodes


# --- room scale ---------------------------------------------------------------

def sauna_room_interval(walls, direction: str, station: float):
    """Interior u-span (inches) between the innermost faces of the two sauna walls cut."""
    spans: list[tuple[float, float]] = []
    for wall in walls:
        lo, hi = wall_cut_bounds_m(wall, direction, station)
        if lo is not None:
            spans.append((lo / M_PER_IN, hi / M_PER_IN))
    if len(spans) < 2:
        return None
    spans.sort(key=lambda s: (s[0] + s[1]) / 2.0)
    u_lo = spans[0][1]   # inner (high) face of the leftmost wall
    u_hi = spans[-1][0]  # inner (low) face of the rightmost wall
    if u_hi - u_lo < cfg.SAUNA_MIN_ROOM_WIDTH_IN:
        return None
    return u_lo, u_hi


def ceiling_underside_over(model, crop, direction, station, u_lo_in, u_hi_in):
    """The elevation of whatever forms the sauna's ceiling, in metres, or ``None``.

    Two structures can be over this room and the drop ceiling hangs the same way under
    either: a concrete deck's soffit, or a framed floor's joist soffit. Catlin's sauna sat
    under the 9" cast deck until 2026-08-21, and under FS-M-WEST's I-joists since — asking
    only about slabs, which is all this did, silently drew no drop ceiling at all the moment
    the deck over it became wood. The room's own detail note says it in as many words:
    "primary structure above may be joists or concrete deck; hang drop framing accordingly".

    Whichever is lowest wins, so a room straddling a boundary reads its own ceiling plane.
    ``None`` only when nothing at all is over the room, and then the drop ceiling draws
    nothing rather than guessing an elevation.
    """
    plane = CutPlane(axis=direction, station_m=station)
    (_cu0, cz0), (_cu1, cz1) = crop
    lo_z, hi_z = min(cz0, cz1), max(cz0, cz1)
    mid_z = (lo_z + hi_z) / 2.0
    best: float | None = None

    def _consider(z0_m: float, ring) -> None:
        nonlocal best
        if not (mid_z < z0_m <= hi_z + 0.05):
            return
        for (a, b) in ring_intervals(ring, plane):
            lo, hi = min(a, b) / M_PER_IN, max(a, b) / M_PER_IN
            if lo <= u_hi_in and hi >= u_lo_in:
                if best is None or z0_m < best:
                    best = z0_m
                return

    for solid in model.solids:
        if solid.category == "slab":
            _consider(solid.z0_m, solid.outline)
    for floor in model.floors:
        joists = [m for m in floor.members if m.category == "joist"]
        if not joists:
            continue
        points = [p for m in joists for p in (m.p0, m.p1)]
        x_lo, x_hi = min(p[0] for p in points), max(p[0] for p in points)
        y_lo, y_hi = min(p[1] for p in points), max(p[1] for p in points)
        ring = ((x_lo, y_lo), (x_hi, y_lo), (x_hi, y_hi), (x_lo, y_hi))
        _consider(min(m.z0_m for m in joists), ring)
    return best


def sauna_benches(u_lo: float, u_hi: float, floor_z: float) -> list[IRNode]:
    """Two-tier benches: lower seat at 18", upper at 36", 20" deep, 1.5" boards.

    Cantilevered off the room's high-u wall and projecting into the room, each seat carried on
    a front leg so it reads as a bench rather than a floating board.
    """
    wall_u = u_hi
    front = wall_u - cfg.SAUNA_BENCH_DEPTH_IN
    nodes: list[IRNode] = []
    for top_in in (cfg.SAUNA_BENCH_LOWER_TOP_IN, cfg.SAUNA_BENCH_UPPER_TOP_IN):
        z_top = floor_z + top_in
        z_bottom = z_top - cfg.SAUNA_BENCH_THK_IN
        nodes += rect_region(front, z_bottom, wall_u, z_top,
                             "sauna-bench", "sauna-shiplap", "lumber", lineweight=0.4)
        nodes += rect_region(front, floor_z, front + cfg.SAUNA_BENCH_THK_IN, z_bottom,
                             "sauna-bench-leg", "sauna-shiplap", "lumber", lineweight=0.3)
    return nodes


def sauna_heater_clearance(u_lo: float, _u_hi: float, floor_z: float) -> list[IRNode]:
    """The heater's required clearance envelope against the room's low-u wall.

    Drawn as an open dashed box, not a filled one: it is a keep-clear zone, not built fabric,
    and filling it would read as a cabinet.
    """
    return [Polyline(points=rect_points(u_lo, floor_z, u_lo + cfg.SAUNA_HEATER_W_IN,
                                        floor_z + cfg.SAUNA_HEATER_H_IN),
                     layer=LAYER, closed=True, lineweight=0.35, linetype="DASHED",
                     tag="detail-component:sauna-heater")]


def sauna_floor_slope(u_lo: float, u_hi: float, floor_z: float) -> list[IRNode]:
    """Sloped mortar screed over the floor slab: 1" fall over an 8' run, draining at high-u.

    Drawn as the screed wedge plus the drain grate at the low point, so the fall to drain
    reads at a glance rather than having to be inferred from a note.
    """
    width = u_hi - u_lo
    rise = min(cfg.SAUNA_FLOOR_RISE_IN,
               width / cfg.SAUNA_FLOOR_RUN_IN * cfg.SAUNA_FLOOR_RISE_IN)
    nodes = closed_region(((u_lo, floor_z), (u_hi, floor_z), (u_lo, floor_z + rise)),
                          "sauna-floor-slope", "sealant", None, lineweight=0.35)
    nodes += rect_region(u_hi - cfg.SAUNA_FLOOR_DRAIN_WIDTH_IN,
                         floor_z - cfg.SAUNA_FLOOR_DRAIN_DEPTH_IN, u_hi,
                         floor_z + cfg.SAUNA_FLOOR_DRAIN_LIP_IN,
                         "sauna-floor-drain", "metal-dark", "SOLID", lineweight=0.4)
    return nodes


def sauna_drop_ceiling(u_lo: float, u_hi: float,
                       ceiling_underside_z: float) -> list[IRNode]:
    """Suspended ceiling hung below the structural slab: a 3.5" panel with a 1" gap above.

    The gap is the point — a sauna is heated by keeping the löyly under a low ceiling, and the
    void above it is what lets the panel be an insulated liner rather than a finish on concrete.
    """
    z_top = ceiling_underside_z - cfg.SAUNA_DROP_GAP_IN
    z_bottom = z_top - cfg.SAUNA_DROP_DEPTH_IN
    nodes = rect_region(u_lo, z_bottom, u_hi, z_top,
                        "sauna-drop-ceiling", "sauna-shiplap", "lumber", lineweight=0.4)
    for fraction in cfg.SAUNA_HANGER_FRACTIONS:
        u = u_lo + (u_hi - u_lo) * fraction
        nodes.append(Polyline(points=((u, z_top), (u, ceiling_underside_z)),
                              layer=LAYER, lineweight=0.2,
                              tag="detail-component:sauna-ceiling-hanger"))
    return nodes


def build_sauna_room_components(model, walls, crop, direction, station) -> list[IRNode]:
    """Per-room sauna vocabulary (benches, heater clearance, floor slope, drop ceiling)."""
    interval = sauna_room_interval(walls, direction, station)
    if interval is None:
        return []
    u_lo, u_hi = interval
    (cu0, _cz0), (cu1, _cz1) = crop
    crop_lo, crop_hi = min(cu0, cu1) / M_PER_IN, max(cu0, cu1) / M_PER_IN
    if u_hi <= crop_lo or u_lo >= crop_hi:  # room interior not in frame
        return []
    floor = slab_at_junction(model, crop, direction, station,
                             (u_lo + u_hi) / 2.0 * M_PER_IN)
    if floor is None:
        return []
    floor_z = floor.z1_m / M_PER_IN
    nodes: list[IRNode] = []
    nodes += sauna_floor_slope(u_lo, u_hi, floor_z)
    nodes += sauna_benches(u_lo, u_hi, floor_z)
    nodes += sauna_heater_clearance(u_lo, u_hi, floor_z)
    ceiling_z = ceiling_underside_over(model, crop, direction, station, u_lo, u_hi)
    if ceiling_z is not None:
        nodes += sauna_drop_ceiling(u_lo, u_hi, ceiling_z / M_PER_IN)
    return nodes


def sauna_components(model, walls, crop, direction, station) -> list[IRNode]:
    """Everything the sauna draws for a cut that crosses ``walls`` — per wall, then per room."""
    from typehaus.emit.draw.detail_components.wall_base import slab_thermal_break

    nodes: list[IRNode] = []
    for wall in walls:
        nodes += sauna_liner_base(model, wall, crop, direction, station)
        nodes += slab_thermal_break(model, wall, crop, direction, station)
    if walls:
        nodes += build_sauna_room_components(model, walls, crop, direction, station)
    return nodes


def sauna_overlay_for_slice(model, view) -> list[IRNode]:
    """Sauna vocabulary for an authored floor-section ``Slice`` (documentation-only path).

    The authored-Slice pipeline (``section.build_section``) bypasses the derived
    detail-component machinery, so a hand-authored sauna floor section would otherwise get
    none of the liner base, thermal break or room-scale vocabulary. Self-gated on sauna walls
    actually being in the cut, so it adds nothing to a non-sauna Slice and never mutates
    construction geometry.
    """
    if view.crop is None or view.cut_origin is None:
        return []
    direction = view.cut_direction or "x"
    station = view.cut_origin.xy_m[1] if direction == "x" else view.cut_origin.xy_m[0]
    crop = (view.crop[0].xy_m, view.crop[1].xy_m)
    sauna_walls = [w for w in model.walls
                   if "SAUNA" in (w.assembly or "")
                   and wall_in_frame(w, direction, station, crop)]
    if not sauna_walls:
        return []
    return sauna_components(model, sauna_walls, crop, direction, station)
