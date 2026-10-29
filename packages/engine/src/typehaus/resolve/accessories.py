"""Resolve modeled accessories into geometry (→ take-off / glTF / IFC).

Dowels, connectors, guard rails, sump pits, vent risers, and edge trim all resolve into
plain :class:`ResolvedSolid` prisms in the shared IR, so the existing glTF and IFC solid
paths render and export them without a bespoke emitter per kind. Authored elevations are
project-frame absolute; the resolver derives geometry from authored intent and never
invents a position or a route.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding, Result, Severity, element_error
from typehaus.model.braces import SlatBrace, StrapBrace
from typehaus.model.enums import ConnectorKind
from typehaus.model.mep import Sump, VentRun
from typehaus.model.structure import (
    Connector,
    Dowel,
    IsolationBoard,
    KneeBrace,
    Railing,
    Wedge,
)
from typehaus.model.trim import (
    Downspout,
    EaveSoffit,
    Fascia,
    Flashing,
    GlazingTrim,
    Gutter,
    MovementJoint,
)
from typehaus.quantities import inch
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.edge_runs import resolve_downspout, resolve_edge_run
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import (
    bar,
    circle_outline,
    nominal_actual_m,
    rect_between,
    square,
)
from typehaus.resolve.model import (
    FramedMember,
    ResolvedBrace,
    ResolvedModel,
    ResolvedSolid,
)
from typehaus.resolve.railings import resolve_railing
from typehaus.resolve.rainscreen_closures import resolve_bug_screens
from typehaus.resolve.slat_braces import resolve_slat_brace
from typehaus.resolve.solid_categories import in_slab_family
from typehaus.resolve.strap_braces import resolve_strap_brace

# Round-section faceting lives in resolve/round_solids.py, shared with pipe runs.
# ``_PIPE_SWEEP_BANDS`` is re-exported rather than used here: ``test_accessories.py`` imports
# it from this module to assert the horizontal jog is swept on the SAME band boundaries as the
# vertical risers. A tidy-up that drops it as an unused import breaks that test.
from typehaus.resolve.round_solids import (  # noqa: F401  # isort: skip  (see above)
    PIPE_BUNDLE_SPACING as _PIPE_BUNDLE_SPACING,
    PIPE_FACETS as _PIPE_FACETS,
    PIPE_SWEEP_BANDS as _PIPE_SWEEP_BANDS,
    round_run_bands as _round_run_bands,
)
from typehaus.resolve.vent_termination import RISER_LEGS, riser_polylines


def resolve_accessories(model: ResolvedModel) -> list[Finding]:
    """Append accessory solids to ``model.solids``. Geometry only, so the findings it can
    return are WARN-tier reports of geometry it could not derive — never a build failure."""
    findings: list[Finding] = []
    for storey in model.plan.storeys:
        for el in model.plan.storey_elements(storey.tag):
            if isinstance(el, Dowel):
                _resolve_dowel(model, el, storey.tag)
            elif isinstance(el, IsolationBoard):
                _resolve_isolation_board(model, el, storey.tag)
            elif isinstance(el, Connector):
                if el.roof_mount is not None:
                    from typehaus.resolve.connector_geometry.ties import STRAPS

                    roof = next((r for r in model.roofs if r.tag == el.roof_mount), None)
                    dimensions = STRAPS.get(el.size.upper().removesuffix("Z"))
                    if (roof is None or dimensions is None or dimensions.length_in <= 0
                            or el.elevation is not None or el.axis is not None):
                        findings.append(element_error(
                            "integrity.connector_roof_mount",
                            f"{el.tag}: roof_mount requires a resolved roof and a fixed-length "
                            "flat strap, with elevation and axis supplied by that roof", el.tag))
                        continue
                _resolve_connector(model, el, storey.tag)
            elif isinstance(el, KneeBrace):
                _resolve_knee_brace(model, el, storey.tag)
            elif isinstance(el, StrapBrace):
                findings.extend(resolve_strap_brace(model, el, storey.tag))
            elif isinstance(el, SlatBrace):
                findings.extend(resolve_slat_brace(model, el, storey.tag))
            elif isinstance(el, Wedge):
                _resolve_wedge(model, el, storey.tag)
            elif isinstance(el, Railing):
                if (el.type_ref is not None
                        and not any(product.tag == el.type_ref
                                    for product in model.plan.library.railing_types)):
                    findings.append(element_error(
                        "integrity.unknown_railing_type",
                        f"railing {el.tag} references missing type {el.type_ref!r}", el.tag))
                findings.extend(resolve_railing(model, el, storey.tag))
            elif isinstance(el, Sump):
                _resolve_sump(model, el, storey)
            elif isinstance(el, VentRun):
                findings.extend(_resolve_vent(model, el, storey.tag))
            elif isinstance(el, Downspout):
                resolve_downspout(model, el, storey.tag)
            elif isinstance(el, (EaveSoffit, Fascia, Gutter, Flashing, GlazingTrim,
                                 MovementJoint)):
                resolve_edge_run(model, el, storey.tag)
    resolve_bug_screens(model)
    from typehaus.resolve.rainscreen_base_flashing import resolve_rainscreen_base_flashing

    resolve_rainscreen_base_flashing(model)
    return findings


# --- per-kind ---------------------------------------------------------------
def _resolve_isolation_board(model: ResolvedModel, el: IsolationBoard, storey: str) -> None:
    """One board, thin along ``axis`` — the same solid a Dowel's foam block resolves."""
    cx, cy = el.position.xy_m
    z, h = el.elevation.meters, el.height.meters
    half_t, half_l = el.thickness.meters / 2.0, el.length.meters / 2.0
    half_x, half_y = (half_l, half_t) if el.axis == "y" else (half_t, half_l)
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-board", tag=el.tag, storey=storey, category="thermal_break",
        outline=square(cx, cy, half_x, half_y), z0_m=z - h / 2.0, z1_m=z + h / 2.0,
        material=el.material))


def _resolve_dowel(model: ResolvedModel, el: Dowel, storey: str) -> None:
    cx, cy = el.position.xy_m
    z = el.elevation.meters
    dia = el.diameter.meters
    run = el.length.meters
    spacing = el.spacing.meters if el.spacing is not None else 0.0
    perp = "x" if el.axis == "y" else "y"  # bars are spaced perpendicular to their run
    row_span = spacing * max(el.count - 1, 0)
    # Foam thermal-break block the dowels pass through. The block *is* the joint: its thin
    # dimension is the dowel axis (the direction the bars cross it) and its long dimension
    # runs along the joint line, spanning the row of bars. Swapping those two turns the block
    # 90° and it stops separating the two structures it is breaking the bridge between.
    # ...and it is FOAM. Named here rather than left to ``solid_material_ref``'s
    # concrete default, which drew the one block whose job is to interrupt the pour in the
    # same grey stipple as the pour on either side of it.
    if el.foam_thickness is not None:
        ft_m = el.foam_thickness.meters
        fh = (el.foam_height.meters if el.foam_height is not None else inch(12).meters)
        block_along_joint = (el.foam_length.meters if el.foam_length is not None
                             else max(row_span + 8 * dia, inch(12).meters))
        half_x, half_y = (block_along_joint / 2.0, ft_m / 2.0) if el.axis == "y" else \
            (ft_m / 2.0, block_along_joint / 2.0)
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-foam", tag=f"{el.tag}-FOAM", storey=storey,
            category="thermal_break",
            outline=square(cx, cy, half_x, half_y),
            z0_m=z - fh / 2.0, z1_m=z + fh / 2.0, material="xps",
        ))
    # Individual dowel bars, spaced across the joint.
    for i in range(max(el.count, 1)):
        off = (i - (el.count - 1) / 2.0) * spacing
        bx = cx + off if perp == "x" else cx
        by = cy + off if perp == "y" else cy
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-{i:02d}", tag=f"{el.tag}-{i + 1}", storey=storey,
            category="dowel", outline=bar(bx, by, el.axis, run, dia),
            z0_m=z - dia / 2.0, z1_m=z + dia / 2.0,
        ))


#: Connection hardware whose *product* is not a structural fastener, and which therefore
#: neither labels nor routes like one (→ emit/trades.py). Everything else keeps the generic
#: ``connector`` category: a hanger, a tie, a post base and a hold-down are all one family to
#: a reader, and all of them ride the framing toggle.
_CONNECTOR_CATEGORY = {
    ConnectorKind.SNOW_GUARD: "snow_guard",
    ConnectorKind.STANDING_SEAM_CLAMP: "seam_clamp",
    # Named for the STRAP and the panel it penetrates, deliberately not for the pipe it
    # holds: a category starting "pipe_" means a ROUTED PIPE RUN everywhere else in the
    # model (emit/trades.py keys the plumbing trade off that prefix), and a fixing filed
    # under it would render a bracket as plumbing.
    ConnectorKind.PIPE_STRAP: "panel_strap",
}


#: Plan half-extent and half-height of the marker box each connector kind draws, in inches.
#:
#: Hardware bills from the ELEMENT, never from this solid (see ``_resolve_connector``), so
#: nothing about a quantity depends on these numbers — they are what the viewer, the GLB and
#: the section detail show, and the only question they answer is "does that look like the
#: part". A 5" x 5" x 6" box is a fair hanger and a fair post base. It is not a fair seam
#: clamp: an S-5! clamp is 1.60" long, 0.76" deep and 0.39" wide, so the default drew each
#: of the 137 resolved clamps roughly forty times its real volume — a rash of grey cubes
#: down every standing-seam wall, over the one piece of hardware a reader is most likely to
#: mistake for a defect.
#:
#: Every kind not listed keeps the original box, deliberately: a hanger and a post base are
#: within sight of it and moving them would be a change to the drawings for its own sake.
_CONNECTOR_MARKER_IN = {
    # S-5! S-5-S / VersaBracket class seam clamp: 1.60 L x 0.76 D x 0.39 W. Drawn as its
    # real footprint, half-extents, with the long axis in plan.
    ConnectorKind.STANDING_SEAM_CLAMP: (0.80, 0.38, 0.20),
    # A two-hole pipe strap on a standoff block: wider than a seam clamp because it spans
    # the pipe, and deeper because the block holds it off the rib crowns. Still far short
    # of the 5" default box, which is what matters — these run down a wall in fours.
    ConnectorKind.PIPE_STRAP: (1.50, 1.25, 0.50),
    # A 1/2" rod through a 3" square plate washer, drawn as the 10" bolt it is. The default
    # box would draw a bolt the size of a post base, along every sill run in the house.
    ConnectorKind.ANCHOR_BOLT: (1.50, 1.50, 5.00),
    # A 3/8" lag through a ~1" bonded sealing washer, drawn as the 4" fastener it is. The
    # default box would put a 5" x 5" x 6" grey cube on the deck under each 2" stand leg —
    # a marker wider than the thing it holds down, over a detail whose whole point is that
    # the penetration is small and countable.
    ConnectorKind.EQUIPMENT_ANCHOR: (0.50, 0.50, 2.00),
    # A 3-1/2" square, 1" tall stack of stainless plates. Drawn at its real size because
    # the whole point of the part is the GAP it holds open under the beam soffit: a 5" x 5"
    # x 6" default box would fill that gap and hide the detail it exists to show.
    ConnectorKind.BEARING_STANDOFF: (1.75, 1.75, 0.50),
    # The kind spans a face strap and a reinforcing angle, and the marker is drawn at the
    # larger of the two in each direction: 5" square in plan (an L50Z's leg — catlin's
    # CN-SG-BASE-*2-N/-S) and 12" tall (an MSTA12Z's length — CN-SG-BASE-*2-W, 6" of strap
    # into each member, so the box is centred on the bearing plane the same way the strap
    # is). It was 5-1/2" x 5-1/2" x 14" while this kind meant an inverted column cap that
    # wrapped the whole joint; that part could not be built at either pillar and is gone.
    # A box drawn at the WRONG part is the error worth avoiding here, because the only
    # reason this kind exists is to tell a reader the joint is not the standoff post base
    # it replaced.
    ConnectorKind.TENSION_TIE: (2.50, 2.50, 6.00),
    # A 3-1/2" KDAT cube, drawn at its size (catlin's landing tie blocks).
    ConnectorKind.TIE_BLOCK: (1.75, 1.75, 1.75),
}
_CONNECTOR_MARKER_DEFAULT = (2.5, 2.5, 3.0)

#: Nail-strip clamps by product, as (half-L along the seam, half-W, half-H, centre z offset),
#: inches. The connector sits at the seam top; the body spans ~1" below it to the clamp top.
#: S-5-N 2.00 L x 1.57 W x 1.77 H; S-5-N Mini is 1.18 L on the same section.
_SEAM_CLAMP_PRODUCT_IN = {
    "S-5-N": (1.00, 0.785, 0.885, -0.115),
    "S-5-N Mini": (0.59, 0.785, 0.885, -0.115),
}


def _seam_clamp_on_roof(model: ResolvedModel, el: Connector, outline, z_mid: float,
                        half_z: float):
    """A roof seam clamp's marker raked to its roof's pitch, so it rides the seam rather
    than a level box cutting into the pan upslope; ``None`` off a roof."""
    if el.kind is not ConnectorKind.STANDING_SEAM_CLAMP:
        return None
    roof = next((r for r in model.roofs if r.tag in el.connects), None)
    if roof is None:
        return None
    from typehaus.resolve.geometry_ir import GBox
    from typehaus.resolve.geometry_slice_box import _box_mesh
    from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_coordinate

    def rise(x: float, y: float) -> float:
        return (roof_plane_z(roof, roof_slope_coordinate(roof, (x, y)))
                - roof_plane_z(roof, roof_slope_coordinate(roof, el.position.xy_m)))

    bottom = tuple((x, y, z_mid - half_z + rise(x, y)) for x, y in outline)
    top = tuple((x, y, z + 2 * half_z) for x, y, z in bottom)
    return _box_mesh(GBox(bottom, top))


def seam_clamp_half_length_m(size: str) -> float:
    """Half a seam clamp's length along its seam, as the marker draws it."""
    half = _SEAM_CLAMP_PRODUCT_IN.get(size, _CONNECTOR_MARKER_IN[ConnectorKind.STANDING_SEAM_CLAMP])
    return inch(half[0]).meters


def _resolve_connector(model: ResolvedModel, el: Connector, storey: str) -> None:
    if el.hanger_spec_pair(model.plan) is not None:
        return  # names a part for every hung end of a floor; the derived joints draw those
    cx, cy = el.position.xy_m
    z = el.elevation.meters if el.elevation is not None else \
        next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)
    # A compact marker box at the connection point. Hardware is billed from the element, not
    # measured off this solid, so the marker only has to read at the right place — and at
    # roughly the right size, which is what ``_CONNECTOR_MARKER_IN`` is for.
    half_x, half_y, half_z = _CONNECTOR_MARKER_IN.get(el.kind, _CONNECTOR_MARKER_DEFAULT)
    z_shift = 0.0
    if el.kind is ConnectorKind.STANDING_SEAM_CLAMP and el.size in _SEAM_CLAMP_PRODUCT_IN:
        half_x, half_y, half_z, z_in = _SEAM_CLAMP_PRODUCT_IN[el.size]
        z_shift = inch(z_in).meters
    # ``axis`` is the part's own in-plane run direction, and the table's two plan
    # half-dimensions are (along, across) that run — the same convention
    # ``connector_markers._marker_outline`` applies to every DERIVED marker, where
    # orientation is what makes five hundred siblings legible. An authored connector went
    # without it until 2026-09-15 for no better reason than that the field's docstring said
    # "for braces". ``None`` keeps the project-axis box, so every connector that does not
    # claim an orientation draws exactly as before.
    if el.axis in ("y", "-y"):
        half_x, half_y = half_y, half_x
    outline = square(cx, cy, inch(half_x).meters, inch(half_y).meters)
    body = _seam_clamp_on_roof(model, el, outline, z + z_shift, inch(half_z).meters)
    if body is not None:
        zs = [p[2] for p in body.positions]
        model.solids.append(ResolvedSolid(
            uid=el.uid or f"{el.tag}-conn", tag=el.tag, storey=storey, category="seam_clamp",
            outline=outline, z0_m=min(zs), z1_m=max(zs), body_mesh=body,
            product=el.size or None))
        return
    model.solids.append(ResolvedSolid(
        uid=el.uid or f"{el.tag}-conn", tag=el.tag, storey=storey,
        category=_CONNECTOR_CATEGORY.get(el.kind, "connector"),
        outline=square(cx, cy, inch(half_x).meters, inch(half_y).meters),
        z0_m=z + z_shift - inch(half_z).meters, z1_m=z + z_shift + inch(half_z).meters,
        # The part number the take-off bills, so a click on the marker names the hardware.
        product=el.size or None,
    ))


def _resolve_knee_brace(model: ResolvedModel, el: KneeBrace, storey: str) -> None:
    """A 45-degree brace: one raked wood member plus a wrap band for each end's hardware.

    The diagonal is a :class:`FramedMember` rather than a swept solid so it bills as the
    stick of lumber it is. ``ResolvedSolid`` only extrudes a plan outline vertically, so a
    diagonal would otherwise have to be faked as a stack of bands — and the solids take-off
    would then count each band as its own piece of structure.

    ``KneeBrace.foot_lap`` runs the foot back *past* the post face instead of stopping at it,
    for a brace that is not in its post's own plane and so has nothing to bear on there. The
    run and the rise both grow by the lap, because the member stays at 45 degrees: the head
    does not move, the foot drops. ``leg`` therefore keeps meaning what the free body in
    ``checks/structural/lateral_racking`` reads it as — the distance below the soffit at
    which the brace meets the post — and reads it conservatively, since the bolt group that
    actually delivers the force sits half a lap lower again.
    """
    cx, cy = el.position.xy_m
    ux, uy = (el.direction, 0.0) if el.axis == "x" else (0.0, el.direction)
    # The brace's own plane, square to its run: zero for an in-plane brace, and the rail's
    # face offset for one coplanar with a face-bolted member (see KneeBrace.plane_offset).
    if el.plane_offset is not None:
        cx, cy = (cx, cy + el.plane_offset.meters) if el.axis == "x" \
            else (cx + el.plane_offset.meters, cy)
    # Start at the post *face*: a brace end buried in the column overlaps it in plan by more
    # than the interference check's tolerance, and the butt-joint exemption does not reach an
    # endpoint that far inside the column's centroid.
    offset = nominal_actual_m(el.post_size) / 2.0
    lap = el.foot_lap.meters if el.foot_lap is not None else 0.0
    p0 = (cx + ux * (offset - lap), cy + uy * (offset - lap))
    leg = el.leg.meters
    run = leg + lap
    p1 = (p0[0] + ux * run, p0[1] + uy * run)
    # At 45 degrees the member's own depth, measured square to its axis, opens up to
    # ``depth / cos(45)`` when read vertically — the cut a carpenter sees on the end grain.
    thickness_z = cross_section(el.member).depth_m * math.sqrt(2.0)
    soffit = el.soffit_elevation.meters
    model.braces.append(ResolvedBrace(
        uid=el.uid or f"{el.tag}-brace", tag=el.tag, storey=storey,
        members=(FramedMember(
            parent_uid=el.uid or el.tag, child_key="brace", category="brace",
            profile=el.member, p0=p0, p1=p1,
            z0_m=soffit - run - thickness_z, z1_m=soffit - run,
            length_m=run * math.sqrt(2.0),
            z0_end_m=soffit - thickness_z, z1_end_m=soffit,
            connection=f"kneebrace:{el.connector}",
            # An authored finish assembly (POST_WHITE_PAINT on the balcony braces) reduces
            # to its structure layer's material, exactly as a solid's assembly does in the
            # palette — without it the diagonal renders bare category lumber while the
            # pillars it braces read white.
            material=assembly_structure_material(model.plan, el.assembly),
        ),),
    ))
    # The hardware as what it is: a knee-brace stabiliser is a wrap-around strap — one band
    # at each end of the diagonal. The top band ties the brace to the beam/rail soffit it
    # rises to; the bottom band ties it to the post face it leaves from. Each band hugs the
    # member's own plan run and the z-band the wood occupies at that end, so the hardware
    # reads at both joints instead of as one floating marker box at the top. Billing still
    # comes from the element (takeoff/anchors.py::knee_brace_rows), never off these solids.
    #
    # A LAPPED foot has no bottom band, and that is the point rather than an omission: the
    # brace does not butt anything there, it lies on the post's face and is bolted through
    # it. There is no strap to draw, and drawing one would put a wrap band around a joint
    # nobody is going to install one at.
    band_run = inch(3).meters  # strap width, measured along the brace's plan run
    band_half = cross_section(el.member).width_m / 2.0 + inch(0.25).meters  # wrap clearance
    uid_base = el.uid or el.tag
    ends = [("TOP", ((p1[0] - ux * band_run, p1[1] - uy * band_run), p1), soffit)]
    if el.foot_lap is None:
        ends.insert(0, ("BOT", (p0, (p0[0] + ux * band_run, p0[1] + uy * band_run)),
                        soffit - run))
    for end, (near, far), band_top in ends:
        model.solids.append(ResolvedSolid(
            uid=f"{uid_base}-band-{end.lower()}", tag=f"{el.tag}-{el.connector}-{end}",
            storey=storey, category="connector",
            outline=rect_between(near, far, -band_half, band_half),
            z0_m=band_top - thickness_z, z1_m=band_top, product=el.connector,
        ))


def _resolve_wedge(model: ResolvedModel, el: Wedge, storey: str) -> None:
    """A tapered rip: one raked ``FramedMember`` that feathers to nothing.

    ``member_box`` already builds the hexahedron this needs — the piece is full ``rise`` deep
    at ``position`` and zero deep ``run`` away, which is the ``z1_end_m == z0_end_m`` case its
    docstring names ("a tapered band that grows from heel to ridge"). The feathered end
    collapses to ``MINIMUM_EXTENT_M`` there rather than to a degenerate face.

    The member hosts itself on a :class:`ResolvedBrace`, the record for framing that belongs
    to no wall, floor, roof or stair — ``kind="wedge"`` so nothing labels it a knee brace.
    ``plan_width_m`` is authored because a taper's vertical extent cannot classify it: see
    ``FramedMember.plan_width_m``.
    """
    cx, cy = el.position.xy_m
    ux, uy = (el.direction, 0.0) if el.axis == "x" else (0.0, el.direction)
    run = el.run.meters
    p0 = (cx, cy)
    p1 = (cx + ux * run, cy + uy * run)
    base = el.base_elevation.meters
    model.braces.append(ResolvedBrace(
        uid=el.uid or f"{el.tag}-wedge", tag=el.tag, storey=storey, kind="wedge",
        members=(FramedMember(
            parent_uid=el.uid or el.tag, child_key="wedge", category="blocking",
            profile=el.member, p0=p0, p1=p1,
            z0_m=base, z1_m=base + el.rise.meters,
            z0_end_m=base, z1_end_m=base,
            length_m=run,
            # Ripped from stock laid flat, so the wide face is what the plan sees.
            plan_width_m=cross_section(el.member).depth_m,
            material=assembly_structure_material(model.plan, el.assembly),
        ),),
    ))


def _resolve_sump(model: ResolvedModel, el: Sump, storey) -> None:
    """The pit, and the round hole it makes in its slab.

    The basin voids its host the way an area drain does (``resolve/drainage.py``): what rises
    out of the lid crosses no concrete, and the pour is billed net of the hole. Slab layers
    resolve later and inherit the void."""
    cx, cy = el.position.xy_m
    index = next((i for i, s in enumerate(model.solids)
                  if s.tag == el.host_ref and in_slab_family(s.category)),
                 None) if el.host_ref else None
    host = model.solids[index] if index is not None else None
    z1 = host.z1_m if host is not None else storey.elevation.meters
    z0 = (host.z0_m if host is not None else z1) - el.depth.meters
    ring = circle_outline((cx, cy), el.diameter.meters / 2.0, _PIPE_FACETS)
    model.solids.append(ResolvedSolid(
        uid=el.uid or f"{el.tag}-sump", tag=el.tag, storey=storey.tag,
        category="sump", outline=ring, z0_m=z0, z1_m=z1,
        # A radon sump is a moulded basin set in the slab, not a second pour inside it: the
        # solid is the pit, and without a ref it fell to ``solid_material_ref``'s concrete
        # default and hatched as the flatwork it interrupts.
        material="polyethylene",
    ))
    if host is not None:
        model.solids[index] = replace(host, voids=(*host.voids, tuple(tuple(p) for p in ring)))


def _resolve_vent(model: ResolvedModel, el: VentRun, storey: str) -> list[Finding]:
    """The bundled risers as solids — a **reader** of :func:`riser_polylines`.

    The route itself is derived once, in ``resolve/vent_termination``, because an envelope
    and a router obstacle read the same polyline: solids that drifted from the envelope
    would put the viewer's pipe somewhere the collision checker's pipe is not.
    """
    risers = riser_polylines(model, el)
    if not risers:
        return [Finding(
            severity=Severity.WARN, check_id="integrity.vent_termination_unresolved",
            message=(f"vent {el.tag} clears no derivable roof and authors no "
                     "roof_termination_elevation — its exterior riser is not resolved"),
            element_tags=(el.tag,), result=Result.FAIL)]
    radius = el.diameter.meters / 2.0
    for tag, path, z in risers:
        sysname = tag.rsplit("-", 1)[-1]
        key = f"{el.uid}-{sysname}"
        for leg, (uid_part, tag_part, horizontal) in enumerate(RISER_LEGS):
            a, b, za, zb = path[leg], path[leg + 1], z[leg], z[leg + 1]
            if horizontal:
                # A leg the vent does not have — the jog on a riser authoring none — is
                # degenerate, not absent, so the roles line up by index either way.
                if a == b:
                    continue
                for band, (outline, z0, z1) in enumerate(_round_run_bands(a, b, radius, za)):
                    model.solids.append(ResolvedSolid(
                        uid=f"{key}-{uid_part}{band:02d}",
                        tag=f"{el.tag}-{sysname}-{tag_part}{band + 1}",
                        storey=storey, category="vent", outline=outline, z0_m=z0, z1_m=z1))
                continue
            if za == zb:
                continue
            model.solids.append(ResolvedSolid(
                uid=f"{key}-{uid_part}", tag=f"{el.tag}-{sysname}-{tag_part}", storey=storey,
                category="vent", outline=circle_outline(a, radius, _PIPE_FACETS),
                z0_m=min(za, zb), z1_m=max(za, zb)))
    return []
