"""Trim hung off the resolved roof plane: fascia, soffit, gutter, edge cladding (→ B2).

Everything here is *derived* from ``Roof.eave_trim`` and the resolved plane rather than
authored at an absolute elevation, so a raised-heel truss lift or a re-pitched roof carries
the trim with it instead of leaving it hanging in mid-air. The wall→roof closure band is the
other half of the roof edge and lives in :mod:`typehaus.resolve.roof_edge`.

Three pieces:

* **eave / rake trim** — the fascia boards, the soffit panel that closes an overhang's
  underside, and the hung gutter, derived along all four roof edges.
* **roof edge cladding** — the strip of stack edge between the wall cladding's top and the
  roofing: the reference's drip edge and behind-the-gutter flashing, and the rake trim at a
  gable, where the reference draws nothing. Where the wall and roof share one continuous
  cladding skin over a flush edge, this becomes a corner trim piece instead.
* **vented ridge cap** — the formed cap over a vented gable ridge, keyed off the plane's own
  ``ridge_z_m`` so a truss roof (no ridge beam) carries one exactly like a rafter roof.

Every run is cut back at the four rake corners (``mitred_span``) so the eave and rake pieces
tile each corner exactly once instead of doubling up in it.
"""

from __future__ import annotations

import math

from typehaus.model.enums import LayerFunction
from typehaus.model.spatial import Roof
from typehaus.model.trim import EaveGutter, EaveTrim
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof, ResolvedWall
from typehaus.resolve.roof_edge_geometry import (
    CLOSURE_TOLERANCE_M,
    METERS_PER_INCH,
    EdgeRun,
    continuous_skin_cladding,
    mating_faces,
    mitred_span,
    roof_edge_runs,
    roof_ridge_run,
    roof_slope,
    wall_face_inset,
)
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.resolve.trim_bands import open_channel_bands

# A fascia board is envelope trim by category, but it is also the nailer the carpenter hangs
# off the rafter tails — so it has to show up under a framing view toggle too.
_FASCIA_TRADE = "framing"

# Vented ridge cap defaults (no schema field carries these): a formed metal cap wide enough
# to cover the vent slot plus a fastening flange each side, standing a couple of inches over
# the roofing on its vent riser.
#
# The cap is *formed*, not a flat bar, but the member IR is boxes only and a stepped
# composition of risers/shoulders/skirts read as a stack of ledges rather than as trim. One
# box straddling the peak reads better: it spans the full width, seats where the roof plane
# has fallen away under its outer edges, and stands a little proud of the ridge — the wedge
# of air it encloses over the slope is what gives the impression of the raised vent space.
# It carries the roofing's own material, so it reads as the same metal as the roof.
_RIDGE_CAP_HALF_WIDTH_IN = 6.0                                    # 12" edge to edge
_RIDGE_CAP_STAND_IN = 2.0                                         # proud of the ridge
_RIDGE_CAP_WIDTH_M = inch(2.0 * _RIDGE_CAP_HALF_WIDTH_IN).meters
_RIDGE_CAP_HEIGHT_M = inch(_RIDGE_CAP_STAND_IN).meters

# The corner trim capping a wrapped (continuous standing-seam) roof edge: a formed angle
# read as a box straddling the wall-cladding/roofing joint. Its plan thickness clears the
# roofing's drip lap (the metal runs ~0.6" proud of the furring); its vertical leg laps down
# over the top of the wall panels.
_CORNER_TRIM_THICKNESS_M = inch(1.25).meters
_CORNER_TRIM_LEG_M = inch(2).meters


def roof_trim_members(
    model: ResolvedModel, roof: ResolvedRoof, walls: tuple[ResolvedWall, ...]
) -> tuple[FramedMember, ...]:
    """The derived fascia/soffit/gutter, edge closure and ridge cap for one roof."""
    return (_eave_trim_members(model, roof, walls)
            + _edge_cladding_members(model, roof, walls)
            + _ridge_vent_members(model, roof))


# --- eave / rake trim --------------------------------------------------------------------

def _eave_trim_members(
    model: ResolvedModel, roof: ResolvedRoof, walls: tuple[ResolvedWall, ...]
) -> tuple[FramedMember, ...]:
    element = model.plan.by_tag(roof.tag)
    trim = element.eave_trim if isinstance(element, Roof) else None
    if trim is None:
        return ()
    # The deck (and whatever else sits under the roofing) presents an exposed edge above the
    # trim plane: the fascia rides up over it, stopping at the underside of whatever closes
    # the band above — the roofing itself on a deck-and-metal roof, or the roof foam (where
    # the edge-cladding band takes over) on a layered one. Without the rise the sheathing
    # edge shows as a raw strip between the fascia top and the roofing.
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    slope_factor = math.hypot(1.0, roof_slope(roof))
    fascia_rise = mating_faces(layers).foam_under * slope_factor if layers else 0.0
    members: list[FramedMember] = []
    for run in roof_edge_runs(roof):
        members.extend(_edge_trim(roof, trim, run, walls, fascia_rise))
    return tuple(members)


def _edge_trim(
    roof: ResolvedRoof, trim: EaveTrim, run: EdgeRun, walls: tuple[ResolvedWall, ...],
    fascia_rise_m: float,
) -> tuple[FramedMember, ...]:
    members: list[FramedMember] = []
    # Boards stack outward from the roof edge: the first (a wood nailer) hangs directly under
    # the deck edge, each later board laps over the one before it. An empty fascia stack is a
    # legal declaration — a soffit/gutter-only edge — and everything then registers against
    # the roof edge itself.
    inner = -trim.fascia[0].thickness.meters if trim.fascia else 0.0
    for index, board in enumerate(trim.fascia):
        outer = inner + board.thickness.meters
        depth = board.depth.meters
        # Only a board hung clear of the footprint edge can ride up over the deck edge — the
        # innermost nailer sits directly *under* the deck and must keep topping out at the
        # plane, or it would rise into the deck itself.
        rise = fascia_rise_m if inner >= -CLOSURE_TOLERANCE_M else 0.0
        # Faces as distances *inboard* of the footprint edge, which is what the corner miter
        # is measured in; a board hung outboard of the edge reads negative.
        span = mitred_span(run, -outer, -inner)
        if span is not None:
            center = (inner + outer) / 2.0
            a, b = _offset(span.p0, run.normal, center), _offset(span.p1, run.normal, center)
            members.append(FramedMember(
                parent_uid=roof.uid, child_key=f"{run.key}-fascia-{index}", category="fascia",
                profile=panel_profile(board.thickness.meters / METERS_PER_INCH,
                                      (depth + rise) / METERS_PER_INCH),
                p0=a, p1=b, z0_m=span.z0_m - depth, z1_m=span.z0_m + rise,
                length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
                z0_end_m=span.z1_m - depth, z1_end_m=span.z1_m + rise,
                connection=f"eave-trim:{board.material}",
                material=board.material, trade=_FASCIA_TRADE,
            ))
        inner = outer
    # After the loop ``inner`` is the outermost board's outer face — the plane the gutter and
    # anything else hung off the stack registers against.
    soffit = _soffit_member(roof, trim, run, walls)
    gutters = _gutter_members(roof, trim, run, fascia_outer_m=inner)
    return tuple(members) + tuple(m for m in (soffit,) if m is not None) + gutters


def _offset(point: tuple[float, float], normal: tuple[float, float],
            distance: float) -> tuple[float, float]:
    return (point[0] + normal[0] * distance, point[1] + normal[1] * distance)


def _soffit_member(
    roof: ResolvedRoof, trim: EaveTrim, run: EdgeRun, walls: tuple[ResolvedWall, ...],
) -> FramedMember | None:
    """The panel closing the overhang underside, fascia back to the wall face."""
    if trim.soffit_thickness is None:
        return None
    inset = wall_face_inset(run.normal, run.p0, walls)
    # Inner face of the innermost fascia board — or the roof edge itself when the trim
    # declares no fascia at all (the soffit is not the fascia's dependent).
    outer = -trim.fascia[0].thickness.meters if trim.fascia else 0.0
    width = outer - inset
    if width <= CLOSURE_TOLERANCE_M:
        return None  # a flush (zero-overhang) edge has no underside to close
    span = mitred_span(run, -outer, -inset)
    if span is None:
        return None
    center = (inset + outer) / 2.0
    thickness = trim.soffit_thickness.meters
    # The panel hangs at the fascia's underside; with no fascia it tucks directly under the
    # roof edge instead (its own thickness down, so it closes against the plane).
    drop = trim.fascia[0].depth.meters if trim.fascia else thickness
    a, b = _offset(span.p0, run.normal, center), _offset(span.p1, run.normal, center)
    return FramedMember(
        parent_uid=roof.uid, child_key=f"{run.key}-soffit", category="soffit",
        profile=panel_profile(width / METERS_PER_INCH, thickness / METERS_PER_INCH),
        p0=a, p1=b, z0_m=span.z0_m - drop, z1_m=span.z0_m - drop + thickness,
        length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
        z0_end_m=span.z1_m - drop, z1_end_m=span.z1_m - drop + thickness,
        connection=("eave-trim:vented-soffit" if trim.soffit_vented
                    else f"eave-trim:{trim.soffit_material}"),
        material=trim.soffit_material,
    )


def _gutter_members(
    roof: ResolvedRoof, trim: EaveTrim, run: EdgeRun, fascia_outer_m: float,
) -> tuple[FramedMember, ...]:
    """The hung gutter channel, outboard of the fascia stack on a level eave.

    A rake sheds *along* its run into the eave below it, so a gutter there would be catching
    nothing; only the level eaves get one. Which of them is authored on the declaration
    (``EaveGutter.edges``) — a garage tucked against a breezeway wants the channel on the side
    that would otherwise dump into the gap, not on both.

    The channel is an open-top U built from three thin bands — the back sheet against the
    fascia, the flat bottom, and the front face — because the member IR is boxes only: a
    single solid bar reads as a beam of aluminum, not as something rain can fall into.
    """
    gutter: EaveGutter | None = trim.gutter
    if gutter is None or not run.is_eave:
        return ()
    if gutter.edges and run.edge_name not in gutter.edges:
        return ()
    # The channel hangs off the fascia face, and stops where the rake fascia's outer face is —
    # running it further would leave it cantilevered past the roof edge into open air.
    span = mitred_span(run, -fascia_outer_m, -fascia_outer_m)
    if span is None:
        return ()
    top = span.z0_m - gutter.top_drop.meters
    top_end = span.z1_m - gutter.top_drop.meters
    connection = f"eave-trim:gutter{':' + gutter.slope if gutter.slope else ''}"
    # Offsets are measured from the back of the channel, which here is the fascia face.
    members: list[FramedMember] = []
    for key, offset, band_t, bottom_drop, top_drop in open_channel_bands(
            gutter.thickness.meters, gutter.depth.meters):
        center = fascia_outer_m + offset + band_t / 2.0
        a, b = _offset(span.p0, run.normal, center), _offset(span.p1, run.normal, center)
        members.append(FramedMember(
            parent_uid=roof.uid, child_key=f"{run.key}-gutter-{key}", category="gutter",
            profile=panel_profile(band_t / METERS_PER_INCH,
                                  (bottom_drop - top_drop) / METERS_PER_INCH),
            p0=a, p1=b, z0_m=top - bottom_drop, z1_m=top - top_drop,
            length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
            z0_end_m=top_end - bottom_drop, z1_end_m=top_end - top_drop,
            connection=connection, material=gutter.material,
        ))
    return tuple(members)


# --- roof edge cladding band -------------------------------------------------------------

def _edge_cladding_members(
    model: ResolvedModel, roof: ResolvedRoof, walls: tuple[ResolvedWall, ...]
) -> tuple[FramedMember, ...]:
    """Close the strip of stack edge left between the wall cladding and the roofing.

    The reference's own answer to this band is the drip edge and the flashing behind the box
    gutter ("stainless steel flashing behind gutter over wall furring and under drip edge"):
    the wall cladding dies at the roof foam's underside, the roofing turns down over the
    furring, and metal bridges what is left. This is that piece — at a gable rake, where the
    reference draws nothing, it is the rake trim doing the same job.

    It therefore starts exactly where :class:`MatingFaces` puts the wall cladding's top and
    stops under the roofing, so the two runs of standing seam are continuous. It sits flush
    with the roofing's outer edge, which laps over it — no coplanar faces to fight.
    """
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    if not layers:
        return ()
    cladding = next((layer for layer in reversed(layers)
                     if layer.function is LayerFunction.CLADDING), None)
    if cladding is None:
        return ()
    # Layer offsets are perpendicular to the slope but the band is measured vertically, so a
    # perpendicular `d` needs `d / cosθ` of vertical band to reach the same face.
    mating = mating_faces(layers)
    slope_factor = math.hypot(1.0, roof_slope(roof))
    # A continuous standing-seam skin (flush edge, same cladding material wall and roof)
    # needs no band at all: the wall→roof closure carries the wall's own metal up to the
    # roofing underside, and the joint gets a corner trim piece instead of a drip-edge band.
    if continuous_skin_cladding(model, roof, walls):
        return _corner_trim_members(roof, cladding, mating, slope_factor)
    base = mating.foam_under * slope_factor          # where the wall cladding stops
    height = mating.cladding_under * slope_factor - base
    if height <= CLOSURE_TOLERANCE_M:
        return ()  # deck-and-metal: the wall cladding already reaches the roofing
    setbacks = {entry["layer"]: entry for entry in (roof.layer_edge_setbacks or ())}
    thickness = cladding.thickness.meters
    members: list[FramedMember] = []
    for run in roof_edge_runs(roof):
        # Positive setbacks are inward, so the cladding's outer edge sits `-setback` outward
        # of the footprint edge; hang the band's outer face there.
        entry = setbacks.get(cladding.name)
        outer = -entry[run.edge_name] if entry else 0.0
        span = mitred_span(run, -outer, -outer + thickness)
        if span is None:
            continue
        z0, z1 = span.z0_m + base, span.z1_m + base
        center = outer - thickness / 2.0
        a, b = _offset(span.p0, run.normal, center), _offset(span.p1, run.normal, center)
        members.append(FramedMember(
            parent_uid=roof.uid, child_key=f"{run.key}-edge-cladding", category="cladding",
            profile=panel_profile(thickness / METERS_PER_INCH, height / METERS_PER_INCH),
            p0=a, p1=b, z0_m=z0, z1_m=z0 + height,
            length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
            z0_end_m=z1, z1_end_m=z1 + height,
            connection="roof:edge-cladding", material=cladding.material_ref,
        ))
    return tuple(members)


# --- corner trim (continuous standing-seam edge) -----------------------------------------

def _corner_trim_members(
    roof: ResolvedRoof, cladding, mating, slope_factor: float
) -> tuple[FramedMember, ...]:
    """The formed angle capping a wrapped roof edge, one run per eave/rake.

    Where the wall and roof share one continuous cladding skin (the catlin house's
    standing-seam siding-and-roofing) there is no fascia and no drip-edge band — the wall
    panels run up the stack edge to the roofing underside and the only trim is a corner
    piece lapped over the joint. The box IR cannot fold an angle, so the piece is drawn as
    a single vertical-leg box: hung just outboard of the wall face, deep enough to clear the
    roofing's proud drip lap, its top flush with the roofing's top surface and its leg
    lapping down over the head of the wall panels.
    """
    top = (mating.cladding_under + cladding.thickness.meters) * slope_factor
    z_lo = mating.cladding_under * slope_factor - _CORNER_TRIM_LEG_M
    height = top - z_lo
    thickness_in = _CORNER_TRIM_THICKNESS_M / METERS_PER_INCH
    members: list[FramedMember] = []
    for run in roof_edge_runs(roof):
        # Inner face on the footprint edge (the wall cladding's outer face), outer face
        # clear of the roofing edge — outboard values are negative inboard distances.
        span = mitred_span(run, -_CORNER_TRIM_THICKNESS_M, 0.0)
        if span is None:
            continue
        center = -_CORNER_TRIM_THICKNESS_M / 2.0
        a, b = _offset(span.p0, run.normal, center), _offset(span.p1, run.normal, center)
        members.append(FramedMember(
            parent_uid=roof.uid, child_key=f"{run.key}-corner-trim", category="corner_trim",
            profile=panel_profile(thickness_in, height / METERS_PER_INCH),
            p0=a, p1=b, z0_m=span.z0_m + z_lo, z1_m=span.z0_m + top,
            length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
            z0_end_m=span.z1_m + z_lo, z1_end_m=span.z1_m + top,
            connection="roof:corner-trim", material=cladding.material_ref,
        ))
    return tuple(members)


# --- vented ridge cap --------------------------------------------------------------------

def _ridge_vent_members(model: ResolvedModel, roof: ResolvedRoof) -> tuple[FramedMember, ...]:
    """A vented ridge cap along a gable's ridge, when the roof breathes through it.

    Two constructions call for one, and both appear on catlin: a vented attic (the garage —
    its vented soffits feed the truss space, which exhausts through a slot cut at the ridge),
    and an over-deck vent channel (the house — the furring/batten gap between the foam and
    the standing seam runs eave to ridge and exhausts at the top). Either way the cap is a
    formed metal member riding the roofing surface, centred on the ridge line. A truss roof
    has no ridge beam, so everything keys off ``ResolvedRoof.ridge_z_m`` — the plane's own
    peak — never off a framing member.

    "Formed" is composed rather than swept: see ``_RIDGE_CAP_BANDS``. Every band keeps the
    ``ridge_cap`` category, the ``ridge:vented-cap`` connection and the roofing's own
    material, so the IFC covering map, the glTF skin routing and the viewer's material
    lookup all key off the cap exactly as they did when it was one box.
    """
    ridge = roof_ridge_run(roof)
    if ridge is None:
        return ()
    element = model.plan.by_tag(roof.tag)
    trim = element.eave_trim if isinstance(element, Roof) else None
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    vented_attic = trim is not None and trim.soffit_vented
    vented_over_deck = any(
        layer.function in (LayerFunction.AIRGAP, LayerFunction.FURRING) for layer in layers)
    if not (vented_attic or vented_over_deck):
        return ()
    # The cap sits on the roofing's top surface at the peak: the stack is offset
    # perpendicular to the slope, so its vertical height over the ridge is slope-corrected.
    slope_factor = math.hypot(1.0, roof_slope(roof))
    stack = sum(layer.thickness.meters for layer in layers) * slope_factor
    cladding = next((layer for layer in reversed(layers)
                     if layer.function is LayerFunction.CLADDING), None)
    z0 = ridge.z_m + stack
    slope = abs(roof_slope(roof))
    length = math.hypot(ridge.p1[0] - ridge.p0[0], ridge.p1[1] - ridge.p0[1])
    material = cladding.material_ref if cladding is not None else "aluminum"
    # The plane falls away from the peak, so the cap's underside is set by its outer edges.
    bottom = z0 - inch(_RIDGE_CAP_HALF_WIDTH_IN).meters * slope
    top = z0 + inch(_RIDGE_CAP_STAND_IN).meters
    return (FramedMember(
        parent_uid=roof.uid, child_key="ridge-vent-cap", category="ridge_cap",
        profile=panel_profile(2.0 * _RIDGE_CAP_HALF_WIDTH_IN, (top - bottom) / METERS_PER_INCH),
        p0=ridge.p0, p1=ridge.p1, z0_m=bottom, z1_m=top, length_m=length,
        connection="ridge:vented-cap", material=material,
    ),)
