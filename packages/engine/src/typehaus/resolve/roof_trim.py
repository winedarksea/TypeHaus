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
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.flashing_config import FLASHING
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof, ResolvedWall
from typehaus.resolve.roof_drip_edge import (
    deck_edge_m,
    deck_top_m,
    drip_spec,
    fascia_drip_edge,
    wrapped_drip_edge,
)
from typehaus.resolve.roof_edge_geometry import (
    CLOSURE_TOLERANCE_M,
    EdgeRun,
    continuous_skin_cladding,
    mating_faces,
    mitred_span,
    roof_edge_runs,
    roof_slope,
    skin_layers,
    wall_face_inset,
)
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.resolve.roof_panel_trim import (
    panel_profile_for_layer,
    rake_panel_trim,
)
from typehaus.resolve.roof_ridge_trim import ridge_vent_members as _ridge_vent_members
from typehaus.resolve.trim_bands import formed_edge_bands, open_channel_bands

# A fascia board is envelope trim by category, but it is also the nailer the carpenter hangs
# off the rafter tails — so it has to show up under a framing view toggle too.
_FASCIA_TRADE = "framing"

# The corner trim capping a wrapped (continuous standing-seam) roof edge: a formed angle
# read as a box straddling the wall-cladding/roofing joint. Its plan thickness clears the
# roofing's drip lap (the metal runs ~0.6" proud of the furring); its vertical leg laps down
# over the top of the wall panels.
_CORNER_TRIM_THICKNESS_M = inch(1.25).meters
# 4", not 2". On a zero-overhang gable this piece is the
# only thing standing at the rake, so its leg *is* the barge board: at 2" it showed a 2-1/2"
# face, which against a wall of the same metal read as no edge at all. 4" gives a 4-1/2"
# band with a 1-1/4" projection to throw a shadow — still ordinary brake-formed stock off
# the same coil, a longer flange and nothing else, bounded only by coil width. Only roofs
# taking the continuous-skin path have this piece at all (a roof with an overhang gets
# fascia + soffit instead), so this is the rake trim of a wrapped edge and nothing else.
_CORNER_TRIM_LEG_M = inch(4).meters


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
    # A wrapped edge takes its drip edge in place of the corner trim (_corner_trim_members).
    drip = None
    if trim.drip_edge is not None and not continuous_skin_cladding(model, roof, walls):
        drip = (layers, slope_factor, _edge_trim_material(element, _roofing_material(layers)))
    members: list[FramedMember] = []
    for run in roof_edge_runs(roof):
        edge_trim = (trim.model_copy(update={"fascia": ()})
                     if trim.fascia_edges and run.edge_name not in trim.fascia_edges
                     else trim)
        members.extend(_edge_trim(roof, edge_trim, run, walls, fascia_rise, drip))
    return tuple(members)


def _roofing_material(layers) -> str | None:
    roofing = next((layer for layer in reversed(layers)
                    if layer.function is LayerFunction.CLADDING), None)
    return roofing.material_ref if roofing is not None else None


def _edge_trim(
    roof: ResolvedRoof, trim: EaveTrim, run: EdgeRun, walls: tuple[ResolvedWall, ...],
    fascia_rise_m: float, drip=None,
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
        # ``inner``/``outer`` are faces measured along the *outward* normal, which is the
        # frame ``_offset`` works in. ``mitred_span`` measures inboard-positive, so the same
        # faces are handed to it negated.
        span = mitred_span(run, -outer, -inner)
        if span is not None:
            center = (inner + outer) / 2.0
            a, b = _offset(span.p0, run.normal, center), _offset(span.p1, run.normal, center)
            members.append(FramedMember(
                parent_uid=roof.uid, child_key=f"{run.key}-fascia-{index}", category="fascia",
                profile=panel_profile(board.thickness.meters / M_PER_IN,
                                      (depth + rise) / M_PER_IN),
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
    spec = drip_spec(trim, run) if drip is not None else None
    if spec is not None:
        layers, slope_factor, material = drip
        members.extend(fascia_drip_edge(
            roof, run, spec, trim, slope=roof_slope(roof),
            deck_top=deck_top_m(layers, slope_factor), bend=deck_edge_m(roof, layers, run),
            fascia_outer=inner, fascia_rise=fascia_rise_m, material=material))
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
        profile=panel_profile(width / M_PER_IN, thickness / M_PER_IN),
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
            profile=panel_profile(band_t / M_PER_IN,
                                  (bottom_drop - top_drop) / M_PER_IN),
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
        element = model.plan.by_tag(roof.tag)
        members = _corner_trim_members(roof, cladding, mating, slope_factor, element, layers, walls)
        profile = panel_profile_for_layer(model, cladding)
        if profile:
            members += rake_panel_trim(roof, profile, mating.cladding_under,
                                       _edge_trim_material(element, cladding.material_ref))
        return members
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
            profile=panel_profile(thickness / M_PER_IN, height / M_PER_IN),
            p0=a, p1=b, z0_m=z0, z1_m=z0 + height,
            length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
            z0_end_m=z1, z1_end_m=z1 + height,
            connection="roof:edge-cladding", material=cladding.material_ref,
        ))
    return tuple(members)


# --- corner trim (continuous standing-seam edge) -----------------------------------------

def _edge_trim_material(element, default: str | None) -> str | None:
    """The coil the formed edge trim is ordered in: the roof's own, else the panels' stock.

    ``Roof.edge_trim_material`` is how a standing-seam roof says its rake/eave/ridge trim is a
    different colour from its panels — the ordinary way that roof gets an accent edge. It has
    to be authored per roof rather than assumed: on this repo's two roofs the house wants a
    charcoal rake against white panels and the garage wants its white fascia left alone.
    """
    named = getattr(element, "edge_trim_material", None) if isinstance(element, Roof) else None
    return named or default


def _corner_trim_members(
    roof: ResolvedRoof, cladding, mating, slope_factor: float,
    element=None, layers=(), walls: tuple[ResolvedWall, ...] = (),
) -> tuple[FramedMember, ...]:
    """The formed cleat-and-hemmed-drip capping a wrapped roof edge, per eave/rake run.

    Where the wall and roof share one continuous cladding skin (the catlin house's
    standing-seam siding-and-roofing) there is no fascia and no drip-edge band — the wall
    panels run up the stack edge to the roofing underside and the only trim is a formed
    piece lapped over the joint. It is hung just outboard of the wall face, deep enough to
    clear the roofing's proud drip lap, its top flush with the roofing's top surface and its
    leg lapping down over the head of the wall panels.

    Composed, not extruded: :func:`~typehaus.resolve.trim_bands.formed_edge_bands` gives it
    the cleat / face / hem the fabricator actually folds, the same way
    :func:`_gutter_members` gets its open-top U from ``open_channel_bands``. The whole piece
    still mitres as one — the corner is resolved on the trim's *envelope*, so the bands share
    a span and cannot tile a rake corner differently from each other.

    A declared ``EaveTrim.drip_edge`` replaces this piece on its edges with the formed drip
    edge (:mod:`typehaus.resolve.roof_drip_edge`), on the same face plane and leg.
    """
    # Eave pan/hem stays at the membrane, independent of the seam crown.
    # Image II guide pp. 20–23; hot-roof design currently leaves rib ends open,
    # with no vent closure. Manufacturer rib-end sealing remains a design TODO.
    top = (mating.cladding_under + cladding.thickness.meters) * slope_factor
    z_lo = mating.cladding_under * slope_factor - _CORNER_TRIM_LEG_M
    bands = formed_edge_bands(_CORNER_TRIM_THICKNESS_M, top - z_lo, FLASHING.sheet_m)
    material = _edge_trim_material(element, cladding.material_ref)
    trim = element.eave_trim if isinstance(element, Roof) else None
    slope = roof_slope(roof)
    shell = min(FLASHING.sheet_m, _CORNER_TRIM_THICKNESS_M / 3.0)
    members: list[FramedMember] = []
    for run in roof_edge_runs(roof):
        spec = drip_spec(trim, run)
        if spec is not None:
            # The nose clears the wall cladding's closure head, which is level at its own
            # centreline's height (resolve/roof_edge.py::_closure_segment).
            head = mating.cladding_under * slope_factor + (
                slope * _wall_cladding_m(walls) / 2.0 if run.is_eave else 0.0)
            members.extend(wrapped_drip_edge(
                roof, run, spec, slope=slope, deck_top=deck_top_m(layers, slope_factor),
                bend=deck_edge_m(roof, layers, run), nose_floor=head,
                face_in=_CORNER_TRIM_THICKNESS_M - shell, face_bottom=z_lo, shell=shell,
                material=material))
            continue
        # Inner face on the footprint edge (the wall cladding's outer face), outer face
        # clear of the roofing edge. ``mitred_span`` measures faces *inboard*-positive, so
        # the outboard face reads negative there; ``_offset`` measures along the outward
        # normal, where the same face reads positive. Signing the centre the mitre's way put
        # the trim inboard of the edge — buried in the wall cladding it is meant to lap over.
        span = mitred_span(run, -_CORNER_TRIM_THICKNESS_M, 0.0)
        if span is None:
            continue
        for key, offset, band_t, bottom_drop, top_drop in bands:
            # Offsets run outboard from the footprint edge, which is the section's inboard
            # end; drops run down from the piece's top, which is flush with the roofing.
            center = offset + band_t / 2.0
            a = _offset(span.p0, run.normal, center)
            b = _offset(span.p1, run.normal, center)
            members.append(FramedMember(
                parent_uid=roof.uid, child_key=f"{run.key}-corner-trim-{key}",
                category="corner_trim",
                profile=panel_profile(band_t / M_PER_IN,
                                      (bottom_drop - top_drop) / M_PER_IN),
                p0=a, p1=b,
                z0_m=span.z0_m + top - bottom_drop, z1_m=span.z0_m + top - top_drop,
                length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
                z0_end_m=span.z1_m + top - bottom_drop,
                z1_end_m=span.z1_m + top - top_drop,
                connection="roof:corner-trim",
                material=material,
            ))
    return tuple(members)


def _wall_cladding_m(walls: tuple[ResolvedWall, ...]) -> float:
    """The thickest wall cladding layer under the roof — the closure head's width."""
    return max((layer.thickness_m for wall in walls for layer in skin_layers(wall)
                if layer.function == LayerFunction.CLADDING.value), default=0.0)
