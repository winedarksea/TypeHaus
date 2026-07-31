"""The zero-overhang eave: box gutter, drip edge, apron flashing, screened vent path.

Reference: ``roof_wall_eave_detail_ifc.png``. Catlin's attic is a hot-roofed cathedral space
with **zero overhang**, so there is no soffit to hang a gutter under and no soffit vent to
draw. Water is caught by a fascia-mounted box gutter, and the roof's ventilation path enters
at the eave through an insect-screened slot in the wall plane rather than through a soffit.
Neither reads in the drawing unless they are drawn, because neither is a model element.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import M_TO_IN, SHEET_METAL
from typehaus.emit.draw.detail_components.geometry import (
    face_of,
    flashing_nodes,
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    path_from_steps,
    rect_region,
)
from typehaus.emit.draw.scene import IRNode
from typehaus.resolve.roof_geometry import roof_height_at


def zero_overhang_eave(model, wall, crop, direction, station) -> list[IRNode]:
    """Box gutter + drip edge + apron + screened eave vent at the wall→roof junction.

    Derived from the wall's outermost weather face at the junction elevation, so the whole
    assembly moves with the cladding plane rather than sitting at authored coordinates.
    """
    is_outboard_high = outboard_is_high(wall, direction, station)
    if is_outboard_high is None or crop is None:
        return []
    (_cu0, cz0), (_cu1, _cz1) = crop
    intervals = layer_intervals(wall, direction, station)
    weather_face = (outermost_with_function(intervals, "cladding")
                    or outermost_with_function(intervals, "furring"))
    if weather_face is None:
        return []
    out_sign = 1.0 if is_outboard_high else -1.0
    clad_out = face_of(weather_face, is_outboard_high, outer=True)
    roof = _roof_over(model, direction, station, clad_out)
    junction_z = _junction_z_in(roof, wall, direction, station, clad_out)
    cfg = SHEET_METAL

    nodes: list[IRNode] = []
    # Apron flashing: laps down off the roof edge over the head of the wall cladding, behind
    # the drip edge — the reference's roofing-membrane-return-to-wall executed in metal. It
    # is drawn even where a derived corner trim already caps the edge (the flush
    # continuous-cladding case, resolve/roof_trim.py::_corner_trim_members): the trim is cut
    # into the drawing as a plain rectangle of roof member, and this is the piece that
    # carries the *name* and the lap direction a builder reads the detail for.
    apron = path_from_steps(
        (clad_out - out_sign * cfg.apron_back_in, junction_z + cfg.apron_run_in - 0.2),
        [(out_sign * cfg.apron_run_in, 0.0), (0.0, -cfg.apron_drop_in)])
    nodes += flashing_nodes(apron, tag="apron-flashing")

    # Authored eave-water trim (a Gutter element with its drip, e.g. the Catlin house's
    # params/roof_trim.py pair riding the roofing plane) is already cut into the drawing.
    # The overlay's schematic gutter + drip hang off the *plate top*, a storey of roof
    # stack lower, so drawing both puts two gutters on one eave at different heights.
    if not _authored_gutter_at(model, clad_out, direction):
        # Drip edge: turns down off the roof deck edge onto the fascia, so run-off leaves
        # the deck clear of the wall instead of tracking back under the roofing.
        drip = path_from_steps(
            (clad_out - out_sign * cfg.drip_edge_back_in, junction_z + 1.0),
            [(out_sign * cfg.drip_edge_run_in, 0.0), (0.0, -cfg.drip_edge_drop_in)])
        nodes += flashing_nodes(drip, tag="drip-edge")
        nodes += box_gutter(clad_out, junction_z, out_sign)

    nodes += eave_vent_screen(clad_out, junction_z, out_sign, cz0 * M_TO_IN)
    return nodes


def _cut_point(direction: str, station: float, u_in: float) -> tuple[float, float]:
    """A plan point from the section's own frame: ``u`` across the cut, ``station`` along it."""
    u_m = u_in / M_TO_IN
    return (u_m, station) if direction == "x" else (station, u_m)


def _roof_over(model, direction: str, station: float, clad_out_in: float):
    """The roof whose footprint covers the eave point, or ``None``.

    Containment is given an inch of slop deliberately: on a zero-overhang roof the wall's
    cladding face *is* the footprint edge, so an exact test lands on the boundary and its
    answer is a rounding coin-flip. Where roofs overlap the highest wins, which is the one
    the eave is under.
    """
    point = _cut_point(direction, station, clad_out_in)
    tolerance = 1.0 / M_TO_IN
    covering = []
    for roof in model.roofs:
        xs = [p[0] for p in roof.footprint]
        ys = [p[1] for p in roof.footprint]
        if (min(xs) - tolerance <= point[0] <= max(xs) + tolerance
                and min(ys) - tolerance <= point[1] <= max(ys) + tolerance):
            covering.append(roof)
    return max(covering, key=lambda r: roof_height_at(r, point)) if covering else None


def _junction_z_in(roof, wall, direction: str, station: float, clad_out_in: float) -> float:
    """The elevation the eave assembly hangs from, in inches — the **roof plane**, not the plate.

    A wall stops at its top plate; the roof deck at the eave sits the rafter's own rise above
    that (on catlin, the I-joist's 10" of depth less its seat drop). Registering the gutter,
    drip and vent slot on ``wall.top_z1_m`` therefore drew the whole assembly most of a foot
    below the eave it belongs to — floating mid-wall, with the authored gutter it is supposed
    to work with a storey of roof stack above it. Only a wall with no roof over it, which has
    no eave to detail anyway, falls back to its plate.
    """
    if roof is not None:
        return roof_height_at(roof, _cut_point(direction, station, clad_out_in)) * M_TO_IN
    return (wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m) * M_TO_IN


def _authored_gutter_at(model, clad_out_in: float, direction: str) -> bool:
    """Whether an authored Gutter element runs along this eave (within a foot of it).

    The gutter's path rides a constant plan coordinate just outboard of the cladding
    face; matching on that coordinate keeps the garage eave (no authored gutter yet)
    drawing the schematic one while the house eaves defer to theirs.
    """
    for element in model.plan.elements_of_kind("Gutter"):
        path = getattr(element, "path", None)
        if not path:
            continue
        xy = path[0].xy_m
        coord_in = (xy[0] if direction == "x" else xy[1]) * M_TO_IN
        if abs(coord_in - clad_out_in) <= 12.0:
            return True
    return False


def box_gutter(clad_out: float, junction_z: float, out_sign: float) -> list[IRNode]:
    """A U-section trough hung just outboard of the fascia.

    A zero-overhang eave has no soffit for a hung gutter to bear on, so the trough is a box
    fixed to the fascia with its back pan standing clear of the cladding for drainage.
    """
    cfg = SHEET_METAL
    back_u = clad_out + out_sign * cfg.gutter_standoff_in
    front_u = back_u + out_sign * cfg.gutter_depth_in
    top_z = junction_z - 1.5
    trough = [
        (back_u, top_z),
        (back_u, top_z - cfg.gutter_height_in),
        (front_u, top_z - cfg.gutter_height_in),
        (front_u, top_z + 0.5),
    ]
    return flashing_nodes(trough, thickness=cfg.gutter_wall_thickness_in,
                          material="gutter", tag="box-gutter")


def eave_vent_screen(clad_out: float, junction_z: float, out_sign: float,
                     crop_bottom_z: float) -> list[IRNode]:
    """The wall→eave→ridge ventilation path, screened where it enters at the eave.

    Zero overhang means the intake is a slot in the wall plane, not a vented soffit. The
    screen band is what tells a builder the slot is an intended opening rather than a gap.
    """
    cfg = SHEET_METAL
    inboard = clad_out - out_sign * 3.0
    band_z = junction_z - 3.0
    if band_z <= crop_bottom_z:  # slot below the crop — drawing it would float off the sheet
        return []
    return rect_region(min(clad_out, inboard), band_z, max(clad_out, inboard),
                       band_z + cfg.screen_band_in,
                       "insect-screen", None, "rigid", lineweight=0.3)
