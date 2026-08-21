"""The zero-overhang eave: box gutter, drip edge, apron flashing, screened vent path.

Reference: ``roof_wall_eave_detail_ifc.png``. Catlin's attic is a hot-roofed cathedral space
with **zero overhang**, so there is no soffit to hang a gutter under and no soffit vent to
draw. Water is caught by a fascia-mounted box gutter, and the roof's ventilation path enters
at the eave through an insect-screened slot in the wall plane rather than through a soffit.
Neither reads in the drawing unless they are drawn, because neither is a model element.
"""

from __future__ import annotations

from typehaus.emit.draw.annotate import LabelSpec, dodge, place_column, wrap_label
from typehaus.emit.draw.typography import TEXT_PT
from typehaus.emit.draw.detail_components.config import SHEET_METAL
from typehaus.emit.draw.detail_components.geometry import (
    face_of,
    flashing_nodes,
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    path_from_steps,
    rect_region,
)
from typehaus.emit.draw.scene import IRNode, Leader, NamedPoint
from typehaus.quantities import M_PER_IN
from typehaus.resolve.roof_geometry import roof_height_at
from typehaus.resolve.roof_layer_setbacks import (
    assembly_layer_spans,
    structure_datum_m,
)


def zero_overhang_eave(model, wall, crop, direction, station,
                       scale=None) -> list[IRNode]:
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

    nodes += eave_vent_intake(model, roof, clad_out, junction_z, out_sign, cz0 / M_PER_IN)
    nodes += eave_labels(model, roof, clad_out, junction_z, out_sign,
                         direction, station, scale)
    return nodes


def _cut_point(direction: str, station: float, u_in: float) -> tuple[float, float]:
    """A plan point from the section's own frame: ``u`` across the cut, ``station`` along it."""
    u_m = u_in * M_PER_IN
    return (u_m, station) if direction == "x" else (station, u_m)


def _roof_over(model, direction: str, station: float, clad_out_in: float):
    """The roof whose footprint covers the eave point, or ``None``.

    Containment is given an inch of slop deliberately: on a zero-overhang roof the wall's
    cladding face *is* the footprint edge, so an exact test lands on the boundary and its
    answer is a rounding coin-flip. Where roofs overlap the highest wins, which is the one
    the eave is under.
    """
    point = _cut_point(direction, station, clad_out_in)
    tolerance = 1.0 * M_PER_IN
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
        return roof_height_at(roof, _cut_point(direction, station, clad_out_in)) / M_PER_IN
    return (wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m) / M_PER_IN


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
        coord_in = (xy[0] if direction == "x" else xy[1]) / M_PER_IN
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


def _above_structure_bands(model, roof) -> list:
    """``(layer, z_lo_in, z_hi_in)`` for every layer outboard of the roof's structure,
    measured up from ``roof_height_at`` — which is the top of the structure, not the top of
    the roofing. Empty when the roof has no framed structure layer to measure from."""
    if roof is None:
        return []
    asm = model.plan.library.resolve_assembly(roof.assembly)
    spans = assembly_layer_spans(asm)
    if not any(layer.function.value == "structure" for (layer, _lo, _hi) in spans):
        return []
    base = structure_datum_m(asm)
    return [(layer, (lo - base) / M_PER_IN, (hi - base) / M_PER_IN)
            for (layer, lo, hi) in spans if lo >= base - 1e-9]


def eave_vent_intake(model, roof, clad_out: float, junction_z: float, out_sign: float,
                     crop_bottom_z: float) -> list[IRNode]:
    """The screened intake for whatever air gap the roof assembly actually carries.

    This used to be a slot in the *wall* plane, which is where a vented-batten roof takes its
    intake: the air came up behind the cladding and into a gap sitting straight on the foam.
    Catlin's roof no longer vents there. Its only gap is a ~1/4" mat rolled *above* the top
    deck, under the standing seam, so the intake is a screened opening at the eave edge of
    that band and the wall plane below it is continuous air barrier. Drawing the old wall
    slot on this assembly told a builder to leave a hole through the air barrier.

    A roof with no air gap at all is unvented by design and gets no screen, rather than a
    screen over an opening that does not exist.
    """
    cfg = SHEET_METAL
    gaps = [(lo, hi) for (layer, lo, hi) in _above_structure_bands(model, roof)
            if layer.function.value == "airgap"]
    if not gaps:
        return []
    lo, hi = gaps[-1]
    band_z = junction_z + lo
    if band_z <= crop_bottom_z:  # slot below the crop — drawing it would float off the sheet
        return []
    inboard = clad_out - out_sign * 2.0
    height = max(hi - lo, cfg.screen_band_in)
    return rect_region(min(clad_out, inboard), band_z, max(clad_out, inboard),
                       band_z + height, "insect-screen", None, "rigid", lineweight=0.3)


def _water_anchor(model, direction: str, station: float, clad_out: float,
                  category: str, fallback: tuple[float, float]) -> tuple[float, float]:
    """Centre of the resolved gutter/drip solids this cut passes through, or ``fallback``.

    The eave water chain is authored where the house has one (``params/roof_trim.py`` derives
    the gutter and drip off the deck datum) and drawn schematically where it does not. Both
    end up on the sheet, but at different elevations — the authored gutter's rim sits *above*
    the deck datum, while the schematic trough hangs below the roof plane. A label anchored on
    a guessed offset therefore points at the right piece on one eave and at empty paper on the
    other, so the anchor is read back off the geometry that was actually drawn.
    """
    axis, cross = (0, 1) if direction == "x" else (1, 0)
    us: list[float] = []
    zs: list[float] = []
    for solid in model.solids:
        if solid.category != category:
            continue
        along = [p[cross] / M_PER_IN for p in solid.outline]
        across = [p[axis] / M_PER_IN for p in solid.outline]
        if not (min(along) <= station / M_PER_IN <= max(along)):
            continue
        if min(abs(min(across) - clad_out), abs(max(across) - clad_out)) > 24.0:
            continue
        us += across
        zs += [solid.z0_m / M_PER_IN, solid.z1_m / M_PER_IN]
    if not us:
        return fallback
    return ((min(us) + max(us)) / 2.0, (min(zs) + max(zs)) / 2.0)


def eave_labels(model, roof, clad_out: float, junction_z: float, out_sign: float,
                direction: str, station: float, scale=None) -> list[IRNode]:
    """Name the eave water chain on the drawing, not only in the notes.

    The chain is a *lap order* — deck, drip edge, underlayment over the drip, metal, gutter
    back behind the trim — and a lap order that is not written on the piece it applies to is
    the thing that gets built backwards.
    """
    bands = {layer.function.value: (lo, hi)
             for (layer, lo, hi) in _above_structure_bands(model, roof)}

    def mid(function: str) -> float:
        lo, hi = bands.get(function, (0.0, 0.0))
        return junction_z + (lo + hi) / 2.0

    cfg = SHEET_METAL
    deck_top = junction_z + max((hi for (_lo, hi) in bands.values()), default=0.0)
    # Each anchor sits ON the piece it names. Anchoring them all at the eave corner — the
    # obvious thing, since that is where the chain is — collapses five leaders into one
    # unreadable blob, because the whole stack is under 8" deep at a scale where 8" is a
    # couple of millimetres of paper.
    gutter = _water_anchor(
        model, direction, station, clad_out, "gutter",
        (clad_out + out_sign * (cfg.gutter_standoff_in + cfg.gutter_depth_in / 2.0),
         junction_z - 1.5 - cfg.gutter_height_in / 2.0))
    drip = _water_anchor(
        model, direction, station, clad_out, "flashing",
        (clad_out + out_sign * cfg.drip_edge_run_in / 2.0, deck_top - 0.3))
    # A label for a layer the assembly does not have is worse than no label: the garage roof
    # is a plain vented-attic deck with no rain-screen gap, and an inherited "vent mat intake"
    # leader on it points at nothing and contradicts its own section.
    entries = []
    if "cladding" in bands:
        entries.append(((clad_out - out_sign * 6.0, mid("cladding")),
                        "standing seam on concealed floating clips"))
    if "airgap" in bands:
        entries.append(((clad_out - out_sign * 3.0, mid("airgap")),
                        "vent mat intake, insect screened — the roof's only outward "
                        "drying path"))
    entries += [
        (drip, "drip edge lies ON the top deck; underlayment laps OVER it"),
        (gutter, "box gutter, back edge tucked BEHIND the trim face"),
        # The apron is drawn from its own back/run/drop legs, so its mid-height is derived
        # the same way rather than guessed off the roof plane.
        ((clad_out + out_sign * cfg.apron_run_in / 2.0,
          junction_z + cfg.apron_run_in - 0.2 - cfg.apron_drop_in / 2.0),
         "apron flashing over the cladding head, behind the drip"),
    ]
    specs = [LabelSpec(text=wrap_label(text), target=target) for (target, text) in entries]
    placed = place_column(specs, x=clad_out + out_sign * 15.0, z_top=deck_top + 1.0,
                          step_pt=14.0, height_pt=TEXT_PT, scale=scale,
                          align="left" if out_sign > 0 else "right")
    return [Leader(anchor=NamedPoint(xy=label.spec.target), at=label.at,
                   to=label.spec.target, text=label.spec.text, height_pt=label.height_pt)
            for label in dodge(placed, scale=scale)]
