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
  gable, where the reference draws nothing.

Every run is cut back at the four rake corners (``mitred_span``) so the eave and rake pieces
tile each corner exactly once instead of doubling up in it.
"""

from __future__ import annotations

import math

from typehaus.model.enums import LayerFunction
from typehaus.model.spatial import Roof
from typehaus.model.trim import EaveGutter, EaveTrim
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof, ResolvedWall
from typehaus.resolve.roof_edge_geometry import (
    CLOSURE_TOLERANCE_M,
    METERS_PER_INCH,
    EdgeRun,
    mating_faces,
    mitred_span,
    roof_edge_runs,
    roof_slope,
    wall_face_inset,
)
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

# A fascia board is envelope trim by category, but it is also the nailer the carpenter hangs
# off the rafter tails — so it has to show up under a framing view toggle too.
_FASCIA_TRADE = "framing"


def roof_trim_members(
    model: ResolvedModel, roof: ResolvedRoof, walls: tuple[ResolvedWall, ...]
) -> tuple[FramedMember, ...]:
    """The derived fascia/soffit/gutter and the roof-edge cladding band for one roof."""
    return _eave_trim_members(model, roof, walls) + _edge_cladding_members(model, roof)


# --- eave / rake trim --------------------------------------------------------------------

def _eave_trim_members(
    model: ResolvedModel, roof: ResolvedRoof, walls: tuple[ResolvedWall, ...]
) -> tuple[FramedMember, ...]:
    element = model.plan.by_tag(roof.tag)
    trim = element.eave_trim if isinstance(element, Roof) else None
    if trim is None or not trim.fascia:
        return ()
    members: list[FramedMember] = []
    for run in roof_edge_runs(roof):
        members.extend(_edge_trim(roof, trim, run, walls))
    return tuple(members)


def _edge_trim(
    roof: ResolvedRoof, trim: EaveTrim, run: EdgeRun, walls: tuple[ResolvedWall, ...],
) -> tuple[FramedMember, ...]:
    members: list[FramedMember] = []
    # Boards stack outward from the roof edge: the first (a wood nailer) hangs directly under
    # the deck edge, each later board laps over the one before it.
    inner = -trim.fascia[0].thickness.meters
    for index, board in enumerate(trim.fascia):
        outer = inner + board.thickness.meters
        depth = board.depth.meters
        # Faces as distances *inboard* of the footprint edge, which is what the corner miter
        # is measured in; a board hung outboard of the edge reads negative.
        span = mitred_span(run, -outer, -inner)
        if span is not None:
            center = (inner + outer) / 2.0
            a, b = _offset(span.p0, run.normal, center), _offset(span.p1, run.normal, center)
            members.append(FramedMember(
                parent_uid=roof.uid, child_key=f"{run.key}-fascia-{index}", category="fascia",
                profile=panel_profile(board.thickness.meters / METERS_PER_INCH,
                                      depth / METERS_PER_INCH),
                p0=a, p1=b, z0_m=span.z0_m - depth, z1_m=span.z0_m,
                length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
                z0_end_m=span.z1_m - depth, z1_end_m=span.z1_m,
                connection=f"eave-trim:{board.material}",
                material=board.material, trade=_FASCIA_TRADE,
            ))
        inner = outer
    # After the loop ``inner`` is the outermost board's outer face — the plane the gutter and
    # anything else hung off the stack registers against.
    soffit = _soffit_member(roof, trim, run, walls)
    gutter = _gutter_member(roof, trim, run, fascia_outer_m=inner)
    return tuple(members) + tuple(m for m in (soffit, gutter) if m is not None)


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
    outer = -trim.fascia[0].thickness.meters  # inner face of the innermost fascia board
    width = outer - inset
    if width <= CLOSURE_TOLERANCE_M:
        return None  # a flush (zero-overhang) edge has no underside to close
    span = mitred_span(run, -outer, -inset)
    if span is None:
        return None
    center = (inset + outer) / 2.0
    drop = trim.fascia[0].depth.meters
    thickness = trim.soffit_thickness.meters
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


def _gutter_member(
    roof: ResolvedRoof, trim: EaveTrim, run: EdgeRun, fascia_outer_m: float,
) -> FramedMember | None:
    """The hung gutter channel, outboard of the fascia stack on a level eave.

    A rake sheds *along* its run into the eave below it, so a gutter there would be catching
    nothing; only the level eaves get one. Which of them is authored on the declaration
    (``EaveGutter.edges``) — a garage tucked against a breezeway wants the channel on the side
    that would otherwise dump into the gap, not on both.
    """
    gutter: EaveGutter | None = trim.gutter
    if gutter is None or not run.is_eave:
        return None
    if gutter.edges and run.edge_name not in gutter.edges:
        return None
    # The channel hangs off the fascia face, and stops where the rake fascia's outer face is —
    # running it further would leave it cantilevered past the roof edge into open air.
    span = mitred_span(run, -fascia_outer_m, -fascia_outer_m)
    if span is None:
        return None
    thickness = gutter.thickness.meters
    depth = gutter.depth.meters
    center = fascia_outer_m + thickness / 2.0
    top = span.z0_m - gutter.top_drop.meters
    top_end = span.z1_m - gutter.top_drop.meters
    a, b = _offset(span.p0, run.normal, center), _offset(span.p1, run.normal, center)
    return FramedMember(
        parent_uid=roof.uid, child_key=f"{run.key}-gutter", category="gutter",
        profile=panel_profile(thickness / METERS_PER_INCH, depth / METERS_PER_INCH),
        p0=a, p1=b, z0_m=top - depth, z1_m=top,
        length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
        z0_end_m=top_end - depth, z1_end_m=top_end,
        connection=(f"eave-trim:gutter{':' + gutter.slope if gutter.slope else ''}"),
        material=gutter.material,
    )


# --- roof edge cladding band -------------------------------------------------------------

def _edge_cladding_members(
    model: ResolvedModel, roof: ResolvedRoof
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
