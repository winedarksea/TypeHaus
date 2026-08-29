"""Resolve modeled accessories into geometry (→ take-off / glTF / IFC).

Dowels, connectors, guard rails, sump pits, vent risers, and edge trim all resolve into
plain :class:`ResolvedSolid` prisms in the shared IR, so the existing glTF and IFC solid
paths render and export them without a bespoke emitter per kind. Authored elevations are
project-frame absolute; the resolver derives geometry from authored intent and never
invents a position or a route.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from typehaus.findings import Finding, Result, Severity, element_error
from typehaus.model.enums import ConnectorKind, LayerFunction, TrimKind
from typehaus.model.mep import Sump, VentRun
from typehaus.model.structure import Connector, Dowel, KneeBrace, Railing
from typehaus.model.trim import Downspout, EaveSoffit, Fascia, Flashing, GlazingTrim, Gutter
from typehaus.quantities import inch
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import (
    bar,
    circle_outline,
    clip_half_plane,
    length,
    nominal_actual_m,
    rect_between,
    square,
    sub,
    wall_frame,
)
from typehaus.resolve.model import (
    FramedMember,
    ResolvedBrace,
    ResolvedLayer,
    ResolvedModel,
    ResolvedSolid,
)
from typehaus.resolve.railings import resolve_railing
from typehaus.resolve.trim_bands import drip_edge_bands, open_channel_bands
from typehaus.resolve.vent_termination import (
    derived_termination_elevation,
    exterior_riser_point,
)

# Round-section faceting lives in resolve/round_solids.py, shared with pipe runs.
# ``_PIPE_SWEEP_BANDS`` is re-exported rather than used here: ``test_accessories.py`` imports
# it from this module to assert the horizontal jog is swept on the SAME band boundaries as the
# vertical risers. A tidy-up that drops it as an unused import breaks that test.
from typehaus.resolve.round_solids import (  # noqa: F401
    PIPE_BUNDLE_SPACING as _PIPE_BUNDLE_SPACING,
    PIPE_FACETS as _PIPE_FACETS,
    PIPE_SWEEP_BANDS as _PIPE_SWEEP_BANDS,
    round_run_bands as _round_run_bands,
)

# Trim ``TrimKind`` values collapse onto a small render/IFC category set.
_TRIM_CATEGORY = {
    "fascia": "fascia",
    "soffit": "soffit",
    "gutter": "gutter",
    "downspout": "downspout",
    "drip_flashing": "flashing",
    "wrb_counterflashing": "flashing",
    "beam_cap": "flashing",
    # The glazing extrusions share the edge-run shape but not the flashing category: they
    # are an aluminium order billed by the lineal foot, and the take-off groups on this.
    "glazing_channel": "glazing_trim",
    "glazing_bar": "glazing_trim",
}

# Rainscreen base closure. The strip is a stock corrugated section: 1-1/2" tall, sold by the
# lineal foot, cut to the cavity's own depth. Only the height is a constant here — the depth
# is read off the wall's furring layer, so a change to the batten size moves the order with
# it instead of leaving a strip that no longer fills the cavity.
BUG_SCREEN_MATERIAL = "corrugated-vent-strip"
BUG_SCREEN_HEIGHT_IN = 1.5
_STACK_TOLERANCE_M = 0.05   # a storey's walls land exactly on the one below; this is slop
_STACK_PLAN_TOL_M = 0.5     # two stacked walls share a plan line within a wall's thickness


def resolve_accessories(model: ResolvedModel) -> list[Finding]:
    """Append accessory solids to ``model.solids``. Geometry only, so the findings it can
    return are WARN-tier reports of geometry it could not derive — never a build failure."""
    findings: list[Finding] = []
    for storey in model.plan.storeys:
        for el in model.plan.storey_elements(storey.tag):
            if isinstance(el, Dowel):
                _resolve_dowel(model, el, storey.tag)
            elif isinstance(el, Connector):
                _resolve_connector(model, el, storey.tag)
            elif isinstance(el, KneeBrace):
                _resolve_knee_brace(model, el, storey.tag)
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
                _resolve_downspout(model, el, storey.tag)
            elif isinstance(el, (EaveSoffit, Fascia, Gutter, Flashing, GlazingTrim)):
                _resolve_edge_run(model, el, storey.tag)
    _resolve_bug_screens(model)
    return findings


def rainscreen_band(
        layers: Sequence[ResolvedLayer]) -> tuple[ResolvedLayer, float] | None:
    """``(band layer, vented depth)`` for a wall's rainscreen, or ``None`` if it has none.

    A rainscreen is not any furring — it is a FURRING layer with CLADDING *outboard* of it,
    which is what makes the gap a drained and vented cavity rather than a service chase. The
    predicate is read off the assembly, so every wall built on a rainscreen stack qualifies
    automatically and an interior partition (no cladding at all) never does. Where a wall
    carries two furring layers — the plant room has a liner batten inboard and an outrigger
    band outboard — the one the CLADDING is outboard of is the rainscreen, and this returns
    the layer as well as the number so a caller cannot pick a different one by taking the
    first it finds.

    A furring band packed with insulation vents only what is left over. The Swinburne truss
    wall's outrigger is 3-1/2" deep with 2-1/2" of closed-cell foam behind it, so the drained
    and vented cavity in front of the foam is 1" — not 3-1/2", which is what the band's own
    thickness says and what would size a 3-1/2" insect closure at the bottom of every wall.
    The fill resolves as a cavity layer of its own (``topology.py``) sharing the band's
    depth position, so subtract it where it names the band as its host. A band packed SOLID
    vents nothing, and is no more a rainscreen than a stud bay is: ``None``, not zero, or the
    take-off ships a run of 0"-deep insect strip and the resolver draws the whole band.

    **An AIRGAP layer immediately inboard of the band belongs to the same cavity**, and this
    is where the catlin truss (2026-08-26) parts company with the outrigger it replaced. Its
    outer girt band is 1-1/2" of solid KDAT — nothing vents inside it — with the 1/2" vent
    gap authored as its own layer behind it. Read band-only, that wall would report a 1-1/2"
    cavity that is actually wood, and no cavity at all where the air is. Read together they
    are the 2" of drained, vented, insect-screened space the wall really has, open to the
    outside between the girt courses: 1/2" behind the girts plus the 1-1/2" between them.
    Everything downstream — the bug screen, ``vent_face``, the envelope take-off, the roof
    layer setbacks — follows this one number.

    ``layers`` is ``ResolvedWall.layers`` — every resolved layer interior→exterior,
    cavity fills included, since a fill is exactly what this has to subtract. Passing
    ``depth_layers()`` (which drops them) reports the band's gross depth.
    """
    band = None
    depth = 0.0
    airgap = 0.0
    for layer in layers:
        if getattr(layer, "is_cavity", False):
            if band is not None and layer.cavity_host == band.name:
                depth -= layer.thickness_m
            continue
        if layer.function == LayerFunction.AIRGAP.value:
            # Held, not returned: it only counts as part of the rainscreen if the very next
            # body layer is the furring band it feeds. An air gap anywhere else in a stack
            # (the brick veneer's 1" cavity behind its own wythe) is a different cavity.
            airgap = layer.thickness_m
            continue
        if layer.function == LayerFunction.FURRING.value:
            band, depth = layer, layer.thickness_m + airgap
        elif layer.function == LayerFunction.CLADDING.value and band is not None:
            return (band, depth) if depth > 1e-9 else None
        airgap = 0.0
    return None


def rainscreen_cavity_m(layers: Sequence[ResolvedLayer]) -> float | None:
    """Depth of a wall's drained and vented rainscreen cavity — see :func:`rainscreen_band`."""
    found = rainscreen_band(layers)
    return found[1] if found is not None else None


def _point_segment_distance(p: tuple[float, float], a: tuple[float, float],
                            b: tuple[float, float]) -> float:
    run = sub(b, a)
    span = run[0] * run[0] + run[1] * run[1]
    if span <= 0.0:
        return length(sub(p, a))
    t = min(1.0, max(0.0, ((p[0] - a[0]) * run[0] + (p[1] - a[1]) * run[1]) / span))
    return length(sub(p, (a[0] + run[0] * t, a[1] + run[1] * t)))


def _continues_cavity_below(model: ResolvedModel, wall) -> bool:
    """Is this wall's rainscreen cavity fed from a rainscreen wall directly beneath it?

    Platform framing stacks a storey's walls on the one below, and the cladding and its
    vent cavity run past that joint uninterrupted — there is no cladding start there and so
    no screen. A wall only gets one where the cavity genuinely begins: at grade, or on top
    of something that is not itself a rainscreen (a concrete stem wall, a garage curb).

    The test is that some rainscreen wall's top lands on this wall's base *and* shares its
    plan line; matching elevation alone would suppress the screen on every wall in a storey
    the moment one of them stacked.
    """
    for other in model.walls:
        if other.tag == wall.tag or abs(other.z1_m - wall.z0_m) > _STACK_TOLERANCE_M:
            continue
        if rainscreen_cavity_m(other.layers) is None:
            continue
        mid = ((wall.axis[0][0] + wall.axis[1][0]) / 2.0,
               (wall.axis[0][1] + wall.axis[1][1]) / 2.0)
        if _point_segment_distance(mid, other.axis[0], other.axis[1]) <= _STACK_PLAN_TOL_M:
            return True
    return False


def _resolve_bug_screens(model: ResolvedModel) -> None:
    """A vented insect closure where a rainscreen cavity opens at the base of the cladding.

    Derived rather than authored: the screen exists because of how the wall is built, not
    because of anything about a particular wall, so hand-authoring one run per wall would
    mean the next exterior wall someone draws silently ships an open cavity for wasps. The
    strip fills the furring layer's own plan band — its depth *is* the cavity depth, by
    construction — and sits at the bottom of that cavity.

    Only the *bottom* of a cavity is screened: see :func:`_continues_cavity_below`.

    Geometry only: the solid renders and exports, and
    :func:`typehaus.takeoff.envelope.bug_screen_takeoff` bills the same runs by the lineal
    foot off the same predicate.
    """
    height = inch(BUG_SCREEN_HEIGHT_IN).meters
    for wall in model.walls:
        if not screens_rainscreen_base(model, wall):
            continue
        found = rainscreen_band(wall.layers)
        if found is None:
            continue
        furring, vent = found
        outline = _vented_band(wall, furring, vent, _cavity_airgap(wall.layers, furring))
        if len(outline) < 3:
            continue
        model.solids.append(ResolvedSolid(
            uid=f"{wall.uid}-bugscreen", tag=f"{wall.tag}-BUGSCREEN", storey=wall.storey,
            category=TrimKind.BUG_SCREEN.value, outline=outline,
            z0_m=wall.z0_m, z1_m=wall.z0_m + height, assembly=wall.assembly,
        ))


def _cavity_airgap(layers: Sequence[ResolvedLayer],
                   furring: ResolvedLayer) -> ResolvedLayer | None:
    """The AIRGAP layer immediately inboard of ``furring``, or ``None``.

    The other half of the reading :func:`rainscreen_band` takes: it adds that gap's depth to
    the cavity, and this is the polygon that depth is actually in, so the screen the model
    draws and the screen the take-off bills are one strip.
    """
    previous = None
    for layer in layers:
        if getattr(layer, "is_cavity", False):
            continue
        if layer is furring:
            return (previous if previous is not None
                    and previous.function == LayerFunction.AIRGAP.value else None)
        previous = layer
    return None


def _vented_band(wall, furring, vent: float,
                 airgap: ResolvedLayer | None = None) -> list[tuple[float, float]]:
    """The plan polygon of the cavity actually open at the base of the cladding.

    Three cases, and each is a wall the house has actually built:

    * **An unfilled band** vents over its whole depth — every rainscreen wall built before
      the truss wall, and why this returns the band unchanged there.
    * **A band packed with 2-1/2" of closed-cell foam** (the Swinburne outrigger) vents only
      the 1" in front of it, and drawing the screen across the foam too would put a 3-1/2"
      insect closure where a 1" one goes — the same overstatement
      :func:`rainscreen_cavity_m` corrects for the order.
    * **A solid band with its gap authored behind it** (the catlin truss's outer girt, with
      the 1/2" vent as its own AIRGAP layer) vents over BOTH, and the strip has to span the
      two polygons or the model draws a 1-1/2" closure where a 2" one goes.

    The fill's own polygon is no help in the second case:
    ``topology._synchronize_cavity_polygons`` makes every cavity layer share its host's ring
    by convention, so the fill's *depth* is the only thing it can be measured by. Which end
    of the band that depth is packed against is read off the stack — the cladding is
    outboard, so the vent is the slice nearest it.
    """
    ring = list(furring.polygon)
    if airgap is not None and airgap.polygon:
        # Two adjacent bands of one cavity. Unioned through ``resolve/overlay`` rather than
        # with a bare ``unary_union``: the grid-size guard there is what keeps this from
        # being fatal on the web app's GEOS 3.12 and silently wrong on the venv's 3.13.
        merged = _merge_bands(ring, list(airgap.polygon))
        if merged is not None:
            ring = merged
    if vent >= furring.thickness_m + (airgap.thickness_m if airgap is not None else 0.0) \
            - 1e-9:
        return ring
    _origin, _tangent, across, axis_length = wall_frame(wall)
    if axis_length <= 0.0:
        return ring
    def mean_offset(polygon) -> float:
        return sum(x * across[0] + y * across[1] for x, y in polygon) / len(polygon)

    outermost = [layer for layer in wall.layers if not layer.is_cavity and layer.polygon]
    if not outermost:
        return ring
    outward = across if mean_offset(outermost[-1].polygon) >= mean_offset(ring) \
        else (-across[0], -across[1])
    cut = max(x * outward[0] + y * outward[1] for x, y in ring) - vent
    return clip_half_plane(ring, (outward[0] * cut, outward[1] * cut), outward)


def _merge_bands(a: list[tuple[float, float]],
                 b: list[tuple[float, float]]) -> list[tuple[float, float]] | None:
    """``a`` and ``b`` as one ring, or ``None`` if they do not merge into a simple one."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    merged = union_all([Polygon(a), Polygon(b)])
    if merged.is_empty or merged.geom_type != "Polygon":
        return None
    return [(float(x), float(y)) for x, y in merged.exterior.coords[:-1]]


def screens_rainscreen_base(model: ResolvedModel, wall) -> bool:
    """Does this wall carry a bug-screen run? Shared by the resolver and the take-off, so
    the geometry and the order can never disagree about which walls are screened."""
    return (rainscreen_cavity_m(wall.layers) is not None
            and not _continues_cavity_below(model, wall))


# --- per-kind ---------------------------------------------------------------
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
        block_along_joint = max(row_span + 8 * dia, inch(12).meters)
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
}
_CONNECTOR_MARKER_DEFAULT = (2.5, 2.5, 3.0)


def _resolve_connector(model: ResolvedModel, el: Connector, storey: str) -> None:
    cx, cy = el.position.xy_m
    z = el.elevation.meters if el.elevation is not None else \
        next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)
    # A compact marker box at the connection point. Hardware is billed from the element, not
    # measured off this solid, so the marker only has to read at the right place — and at
    # roughly the right size, which is what ``_CONNECTOR_MARKER_IN`` is for.
    half_x, half_y, half_z = _CONNECTOR_MARKER_IN.get(el.kind, _CONNECTOR_MARKER_DEFAULT)
    model.solids.append(ResolvedSolid(
        uid=el.uid or f"{el.tag}-conn", tag=el.tag, storey=storey,
        category=_CONNECTOR_CATEGORY.get(el.kind, "connector"),
        outline=square(cx, cy, inch(half_x).meters, inch(half_y).meters),
        z0_m=z - inch(half_z).meters, z1_m=z + inch(half_z).meters,
    ))


def _resolve_knee_brace(model: ResolvedModel, el: KneeBrace, storey: str) -> None:
    """A 45-degree brace: one raked wood member plus a wrap band for each end's hardware.

    The diagonal is a :class:`FramedMember` rather than a swept solid so it bills as the
    stick of lumber it is. ``ResolvedSolid`` only extrudes a plan outline vertically, so a
    diagonal would otherwise have to be faked as a stack of bands — and the solids take-off
    would then count each band as its own piece of structure.
    """
    cx, cy = el.position.xy_m
    ux, uy = (el.direction, 0.0) if el.axis == "x" else (0.0, el.direction)
    # Start at the post *face*: a brace end buried in the column overlaps it in plan by more
    # than the interference check's tolerance, and the butt-joint exemption does not reach an
    # endpoint that far inside the column's centroid.
    offset = nominal_actual_m(el.post_size) / 2.0
    p0 = (cx + ux * offset, cy + uy * offset)
    leg = el.leg.meters
    p1 = (p0[0] + ux * leg, p0[1] + uy * leg)
    # At 45 degrees the member's own depth, measured square to its axis, opens up to
    # ``depth / cos(45)`` when read vertically — the cut a carpenter sees on the end grain.
    thickness_z = cross_section(el.member).depth_m * math.sqrt(2.0)
    soffit = el.soffit_elevation.meters
    model.braces.append(ResolvedBrace(
        uid=el.uid or f"{el.tag}-brace", tag=el.tag, storey=storey,
        members=(FramedMember(
            parent_uid=el.uid or el.tag, child_key="brace", category="brace",
            profile=el.member, p0=p0, p1=p1,
            z0_m=soffit - leg - thickness_z, z1_m=soffit - leg,
            length_m=leg * math.sqrt(2.0),
            z0_end_m=soffit - thickness_z, z1_end_m=soffit,
            connection=f"kneebrace:{el.connector}",
            # An authored finish assembly (POST_WHITE_PAINT on the balcony braces) reduces
            # to its structure layer's material, exactly as a solid's assembly does in the
            # palette — without it the diagonal renders bare category lumber while the
            # pillars it braces read white.
            material=assembly_structure_material(model.plan, el.assembly),
        ),),
    ))
    # The hardware as what it is: an APVKB-style knee-brace kit is a pair of wrap-around
    # straps — one band at each end of the diagonal. The top band ties the brace to the
    # beam/girt soffit it rises to; the bottom band ties it to the post face it leaves
    # from. Each band hugs the member's own plan run and the z-band the wood occupies at
    # that end, so the hardware reads at both joints instead of as one floating marker box
    # at the top. Billing still comes from the element (takeoff/anchors.py::
    # knee_brace_rows), never off these solids.
    band_run = inch(3).meters  # strap width, measured along the brace's plan run
    band_half = cross_section(el.member).width_m / 2.0 + inch(0.25).meters  # wrap clearance
    uid_base = el.uid or el.tag
    for end, (near, far), band_top in (
            ("BOT", (p0, (p0[0] + ux * band_run, p0[1] + uy * band_run)), soffit - leg),
            ("TOP", ((p1[0] - ux * band_run, p1[1] - uy * band_run), p1), soffit)):
        model.solids.append(ResolvedSolid(
            uid=f"{uid_base}-band-{end.lower()}", tag=f"{el.tag}-{el.connector}-{end}",
            storey=storey, category="connector",
            outline=rect_between(near, far, -band_half, band_half),
            z0_m=band_top - thickness_z, z1_m=band_top,
        ))


def _resolve_sump(model: ResolvedModel, el: Sump, storey) -> None:
    cx, cy = el.position.xy_m
    host = next((s for s in model.solids if s.tag == el.host_ref and s.category == "slab"),
                None) if el.host_ref else None
    z1 = host.z1_m if host is not None else storey.elevation.meters
    z0 = (host.z0_m if host is not None else z1) - el.depth.meters
    half = el.diameter.meters / 2.0
    model.solids.append(ResolvedSolid(
        uid=el.uid or f"{el.tag}-sump", tag=el.tag, storey=storey.tag,
        category="sump", outline=square(cx, cy, half, half), z0_m=z0, z1_m=z1,
        # A radon sump is a moulded basin set in the slab, not a second pour inside it: the
        # solid is the pit, and without a ref it fell to ``solid_material_ref``'s concrete
        # default and hatched as the flatwork it interrupts.
        material="polyethylene",
    ))


def _resolve_vent(model: ResolvedModel, el: VentRun, storey: str) -> list[Finding]:
    cx, cy = el.chase_position.xy_m
    ox, oy = el.exit_offset.xy_m
    ex, ey = exterior_riser_point(el)
    z_start, z_exit = el.start_elevation.meters, el.exit_elevation.meters
    # The termination is a *derived* dimension: 12" above the roof plane at the riser, not
    # an independent input. Authored elevations only stand in where no roof is derivable.
    derived_top = derived_termination_elevation(model, el)
    authored_top = (el.roof_termination_elevation.meters
                    if el.roof_termination_elevation is not None else None)
    z_top = derived_top if derived_top is not None else authored_top
    if z_top is None:
        return [Finding(
            severity=Severity.WARN, check_id="integrity.vent_termination_unresolved",
            message=(f"vent {el.tag} clears no derivable roof and authors no "
                     "roof_termination_elevation — its exterior riser is not resolved"),
            element_tags=(el.tag,), result=Result.FAIL)]
    radius = el.diameter.meters / 2.0
    # Parallel risers, one per bundled system, offset perpendicular to the horizontal jog.
    perp_x = abs(oy) >= abs(ox)  # offset in x when the jog is mostly along y
    n = max(len(el.systems), 1)
    for i, system in enumerate(el.systems or (None,)):
        d = (i - (n - 1) / 2.0) * el.diameter.meters * _PIPE_BUNDLE_SPACING
        dx, dy = (d, 0.0) if perp_x else (0.0, d)
        sysname = system.value if system is not None else "vent"
        key = f"{el.uid}-{sysname}"
        # 1) up the chase
        model.solids.append(ResolvedSolid(
            uid=f"{key}-riser", tag=f"{el.tag}-{sysname}-CHASE", storey=storey,
            category="vent", outline=circle_outline((cx + dx, cy + dy), radius, _PIPE_FACETS),
            z0_m=z_start, z1_m=z_exit))
        # 2) 90° out through the wall
        for band, (outline, z0, z1) in enumerate(
                _round_run_bands((cx + dx, cy + dy), (ex + dx, ey + dy), radius, z_exit)):
            model.solids.append(ResolvedSolid(
                uid=f"{key}-out{band:02d}", tag=f"{el.tag}-{sysname}-OUT{band + 1}", storey=storey,
                category="vent", outline=outline, z0_m=z0, z1_m=z1))
        # 3) 90° up the siding to 12" above the roof
        model.solids.append(ResolvedSolid(
            uid=f"{key}-term", tag=f"{el.tag}-{sysname}-TERM", storey=storey,
            category="vent", outline=circle_outline((ex + dx, ey + dy), radius, _PIPE_FACETS),
            z0_m=z_exit, z1_m=z_top))
    return []


def _resolve_edge_run(model: ResolvedModel, el, storey: str) -> None:
    path = [p.xy_m for p in el.path]
    if len(path) < 2:
        return
    category = _TRIM_CATEGORY.get(el.kind.value, "flashing")
    top = el.top_elevation.meters
    z0 = top - el.depth.meters
    half = el.thickness.meters / 2.0
    # Two of the kinds are *formed* metal, not extruded stock, and the boxes-only solid IR
    # can only say so by composing the section out of bands (see :mod:`.trim_bands`). The
    # rest are genuinely one band and fall through to the plain extrusion below.
    recipe = _BANDED_SECTIONS.get(el.kind)
    if recipe is not None:
        _resolve_banded_run(model, el, storey, path, category, top, half,
                            recipe(2.0 * half, el.depth.meters))
        return
    for i, (a, b) in enumerate(zip(path[:-1], path[1:])):
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-{i:02d}", tag=f"{el.tag}-{i + 1}", storey=storey,
            category=category, outline=rect_between(a, b, -half, half), z0_m=z0, z1_m=top,
            material=el.material,
        ))


#: Which edge-run kinds resolve as a composed section rather than as one extruded band.
#: A gutter is an open-top U — the single bar it used to get read as a solid billet of
#: aluminium, nothing rain could fall *into*. A drip edge is a bent angle: a flat leg lapped
#: under the roofing and a turn-down that throws the water clear. Both are the same recipes
#: the roof's *derived* trim uses, so an authored run and a derived one cannot drift into
#: different-looking metal on the same house.
_BANDED_SECTIONS = {
    TrimKind.GUTTER: open_channel_bands,
    TrimKind.DRIP_FLASHING: drip_edge_bands,
}


def _resolve_banded_run(model: ResolvedModel, el, storey: str, path, category: str,
                        top: float, half: float, bands) -> None:
    """Lay a composed section's bands across the ``[-half, +half]`` span the bar occupied.

    The run stays exactly where it was authored; only its cross-section stops being solid.
    """
    for key, offset, band_t, bottom_drop, top_drop in bands:
        left, right = _cross_span(half, offset, band_t, el.back_side)
        for i, (a, b) in enumerate(zip(path[:-1], path[1:])):
            model.solids.append(ResolvedSolid(
                uid=f"{el.uid}-{i:02d}-{key}", tag=f"{el.tag}-{i + 1}-{key.upper()}",
                storey=storey, category=category,
                outline=rect_between(a, b, left, right),
                z0_m=top - bottom_drop, z1_m=top - top_drop,
                material=el.material,
            ))


def _resolve_downspout(model: ResolvedModel, el, storey: str) -> None:
    """The leader as a round prism from the gutter outlet down to its discharge.

    Faceted exactly like the vent riser (:func:`_resolve_vent`) so the two read as the same
    kind of round metal on the elevation rather than one being smooth and the other a prism.
    """
    z0, z1 = el.bottom_elevation.meters, el.top_elevation.meters
    if z1 - z0 <= 0.0:
        return
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-00", tag=el.tag, storey=storey, category="downspout",
        outline=circle_outline(el.position.xy_m, el.diameter.meters / 2.0, _PIPE_FACETS),
        z0_m=z0, z1_m=z1, material=el.material))


def _cross_span(half: float, offset: float, band_t: float,
                back_side: str) -> tuple[float, float]:
    """A band's ``[left, right]`` offsets, given where its inboard end sits.

    The band recipes measure offsets from the section's *inboard* end. ``rect_between``
    measures from the path's left-hand normal, so when the building is on the left the two
    frames run in opposite directions and the offsets have to be mirrored — not merely
    relabelled.
    """
    if back_side == "left":
        right = half - offset
        return right - band_t, right
    left = -half + offset
    return left, left + band_t
