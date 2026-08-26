"""The intermittent truss that holds a truss wall's cladding off the sheathing (→ 11 §Framing).

A Swinburne truss wall replaces continuous rigid insulation and its 8" structural screws with
spray foam and a *discontinuous* wooden truss. Three pieces make one node:

* a **block** — a 2x4 laid flat against the sheathing, long axis vertical, 3-1/2" on the wall
  and 1-1/2" out from it, slid sideways so one side face is flush with the stud's face. Its
  screws land squarely over the stud;
* a **tab** — 1/2" plywood lying against that flush face, the only piece that crosses the
  insulation zone, and intermittent even there;
* the **outrigger** — a KDAT 2x4 stood on edge in the furring band, lap-screwed to the tab's
  inner face, which lands it centred on the stud line.

The outriggers themselves are not framed here: they are a FURRING layer with a ``FramingSpec``
carrying ``laid="edge"``, and ``framing/furring.py`` lays them out on their own grid like any
other batten. This pass runs *after* it and reads what it framed, which is what keeps the
blocks under the outriggers they actually carry rather than on a grid of their own that would
drift the moment a wall's length or a window's position changed.

Openings get the rest of it. A truss wall's windows are **outie**: the unit sits in the truss
plane with its flanges bearing on the outriggers, not in the stud plane. So every rough
opening also needs

* head and sill **blocking** between the two flanking outriggers, in the truss plane;
* a **jamb outrigger** wherever the 16" field grid puts no outrigger within flange-bearing
  distance of the RO edge — with its own block and tab, over the king stud beside the jack —
  or, where the gap is too small to stand one in without its pack landing on the pack next
  door, a **filler**: plies of the same 2x4 laminated to the member beside it;
* a non-structural 3/8" plywood **buck** lining the RO on all four sides, sheathing face out
  to the truss plane. It closes the foam, faces the reveal, and carries the pan and the head
  flashing.

Everything here is derived. Nothing about a truss wall is authored on a wall or a window, and
no window carries a wall-normal coordinate: the mount plane *is* the outer face of the
outermost FURRING layer, so it follows the assembly.

The placement geometry — where each of those pieces goes on one wall, and every dimension of
them — is ``framing/truss_frame.py``. This module is the pass: which walls, in what order,
and what it reports. The names other packages use are re-exported here.

**There are two truss walls now.** The Swinburne pack above is one; the **catlin truss**
(``framing/truss_girts.py``, 2026-08-26) is the other — two tiers of flat horizontal 2x4
girts at 24" o.c., each bearing on 3-1/2" blocks at the stud module, no tab and no
chirality. Nothing vertical was deleted for it: the two are siblings, selected per wall off
the assembly by :func:`truss_kind` (``laid="edge"`` + vertical → the outrigger pack,
``standoff="block"`` → the girts), and reverting is swapping one assembly's layer tuple.
This module dispatches; neither frame imports the other, and what they share is
``framing/truss_common.py``.
"""


from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.corners import CornerJunctions, corner_junctions
from typehaus.resolve.framing.furring import (
    EDGE,
    VERTICAL,
    _furring_module_signature,
    course_elevations,
    opening_margin,
)
from typehaus.resolve.framing.solver import continuation_roles
from typehaus.resolve.framing.truss_common import (  # noqa: F401 - the package's public names
    BLOCK_CATEGORY,
    BUCK_CATEGORY,
    BUCK_THICKNESS_IN,
    FLANGE_BEARING,
    JAMB_PREFIX,
    LADDER_CATEGORY,
    Vec,
    nearest_bearing_gap,
)
from typehaus.resolve.framing.truss_frame import (  # noqa: F401 - the package's public names
    BLOCK_LENGTH,
    BLOCK_SPACING,
    CORNER_CAP_CATEGORY,
    CORNER_CAP_THICKNESS_IN,
    DOUBLE_HEADER_SPAN,
    FILLER_CATEGORY,
    FILLER_LIMIT,
    TAB_CATEGORY,
    TAB_THICKNESS_IN,
    TRUSS_CATEGORIES,
    TrussFrame,
)
from typehaus.resolve.framing.truss_girts import (  # noqa: F401 - the package's public names
    GIRT_MEMBER,
    INNER,
    OUTER,
    STUDLIKE,
    GirtFrame,
    _by_elevation,
    _standoff_layers,
    girt_block_tier,
    truss_girt_bands,
)
from typehaus.resolve.model import (
    FramedMember,
    ResolvedLayer,
    ResolvedModel,
    ResolvedOpening,
    ResolvedWall,
)

#: What ``_girt_context`` hands back: ``wall_tag -> (layout line, continuation roles)``.
#: Named because the pass threads it straight into ``frame_wall_girts``'s last two
#: parameters and an unnamed nested callable type reads as noise at the call site.
_GirtContext = Callable[[str], tuple[object | None, tuple[str | None, str | None]]]

#: The package face. Everything a caller outside ``resolve/framing`` needs is importable from
#: here whichever side of the truss_wall/truss_frame split it actually lives on, so the split
#: is an internal file-size decision and not an API.
__all__ = [
    "BLOCK_CATEGORY",
    "BLOCK_LENGTH",
    "BLOCK_SPACING",
    "BUCK_CATEGORY",
    "BUCK_THICKNESS_IN",
    "CORNER_CAP_CATEGORY",
    "CORNER_CAP_THICKNESS_IN",
    "DOUBLE_HEADER_SPAN",
    "FILLER_CATEGORY",
    "FILLER_LIMIT",
    "FLANGE_BEARING",
    "GIRT_MEMBER",
    "GirtFrame",
    "JAMB_PREFIX",
    "LADDER_CATEGORY",
    "TAB_CATEGORY",
    "TAB_THICKNESS_IN",
    "TRUSS_CATEGORIES",
    "TrussFrame",
    "Vec",
    "frame_truss_walls",
    "frame_wall_truss",
    "frame_wall_girts",
    "girt_band_findings",
    "girt_block_tier",
    "nearest_bearing_gap",
    "truss_girt_bands",
    "truss_kind",
    "truss_layer_name",
]


def frame_truss_walls(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Attach blocks, tabs, opening ladders and bucks to every truss wall in the model.

    Nearly silent: there is no authoring mistake this pass can catch that ``frame_furring``
    has not already reported, and the one real design question (does every RO jamb reach an
    outrigger?) is a *check*, ``structural.truss_wall_opening_support``, not a resolve-time
    finding.

    The exception is an outrigger left with **no block and no tab**. Every other piece here
    is derived and self-consistent; that one is a stick of wood the model shows fastened to
    nothing, and it happens where two verticals stand within a pack's width of each other —
    at a band end, or beside a jamb outrigger — so the pack next door genuinely does hold
    both. It is a WARN rather than an error for exactly that reason, and it is reported
    rather than swallowed because the number is the thing worth watching: a handful is the
    geometry being crowded, and a hundred is this pass being broken, which is what it was
    until 2026-08-23.

    The one crowding this pass now *resolves* instead of reporting is the band END strip
    against the last module outrigger (``TrussFrame.crowded_end_neighbours``): on a wall
    that is not a whole number of modules long the two land two or three inches apart, the
    end strip cannot move, and the module one is simply omitted — which is what is framed.
    Those members are dropped from the wall's field here, so the BOM and the 3D model lose
    the stick as well as the finding.
    """
    by_host: dict[str, list[ResolvedOpening]] = {}
    for opening in model.openings:
        by_host.setdefault(opening.host_wall, []).append(opening)
    corner_caps = _frame_corner_caps(plan, model, corner_junctions(model))
    girts = _girt_context(plan, model)

    findings: list[Finding] = []
    framed: list[ResolvedWall] = []
    for wall in model.walls:
        if truss_kind(plan, wall.assembly) == "girt":
            members, wall_findings = frame_wall_girts(
                plan, wall, by_host.get(wall.tag, []), *girts(wall.tag))
            findings.extend(wall_findings)
            framed.append(replace(wall, members=wall.members + members)
                          if members else wall)
            continue
        members, loose, dropped = frame_wall_truss(plan, wall, by_host.get(wall.tag, []))
        members = members + tuple(corner_caps.get(wall.tag, ()))
        kept = (tuple(member for member in wall.members
                      if member.child_key not in dropped) if dropped else wall.members)
        framed.append(replace(wall, members=kept + members)
                      if members or dropped else wall)
        if loose:
            findings.append(Finding(
                check_id="structural.truss_wall_unpacked_outrigger",
                severity=Severity.WARN, result=Result.UNKNOWN,
                message=(f"{wall.tag}: {len(loose)} outrigger(s) took no block or tab — "
                         "each stands within a pack's width of one that did, at a band end "
                         "or beside a jamb outrigger, so the pack there carries both"),
                element_tags=(wall.tag,),
                fix_hint=("nail the two together, or move the band's end strip; the model "
                          "cannot say which, so it does not grade it")))
    model.walls = framed
    return findings


def truss_kind(plan: PlanModel, assembly_tag: str | None) -> str | None:
    """Which truss an assembly builds: ``"outrigger"``, ``"girt"``, or ``None``.

    One reading, so the four places that branch on it — this pass, the fastener take-off,
    the opening-support check and the outie-window detail — cannot come to four different
    answers about the same wall. The girt band is tested first because it is the more
    specific signature: ``standoff="block"`` says the band bears on blocks, which no
    outrigger band ever says, while ``laid`` alone is a property an ordinary batten has too.
    """
    if truss_girt_bands(plan, assembly_tag) is not None:
        return "girt"
    return "outrigger" if _outrigger_layer_name(plan, assembly_tag) else None


def truss_layer_name(plan: PlanModel, assembly_tag: str | None) -> str | None:
    """The FURRING layer that IS the truss wall — outrigger band, or OUTER girt, or ``None``.

    One spelling for both frames, because every caller outside this package wants the same
    thing from it: the band the cladding lands on and the window's mount plane is the outer
    face of. ``takeoff/fasteners.py`` uses it as the "this wall has no screwed-strip
    condition" predicate, ``checks/structural/truss_wall.py`` as the band to read jamb
    bearing off, and the outie-window detail as the layer to draw from.

    The outrigger signature is a vertical FURRING layer whose ``FramingSpec`` stands the
    stick on edge: a batten laid flat is a rainscreen strip and frames nothing but itself.
    The girt signature is ``truss_girt_bands``. Both read off the *authored* assembly, so a
    check can ask the question without a resolved wall in hand.
    """
    bands = truss_girt_bands(plan, assembly_tag)
    if bands is not None:
        return bands[1].name
    return _outrigger_layer_name(plan, assembly_tag)


def _outrigger_layer_name(plan: PlanModel, assembly_tag: str | None) -> str | None:
    assembly = plan.library.resolve_assembly(assembly_tag) if assembly_tag else None
    if assembly is None:
        return None
    for layer in assembly.layers:
        spec = layer.framing
        if (layer.function is LayerFunction.FURRING and spec is not None
                and spec.laid == EDGE
                and (spec.direction or VERTICAL).strip().lower() == VERTICAL):
            return layer.name
    return None


def _girt_context(plan: PlanModel, model: ResolvedModel) -> _GirtContext:
    """``wall_tag -> (layout line, continuation roles)`` for the girt bands, computed once.

    A girt course runs THROUGH a collinear seam, and knowing which seams those are is a
    whole-model reading (``solver.continuation_roles``) that would be wasteful to redo per
    wall and wrong to skip: without it every tee in a facade puts a 3" notch in every course
    and doubles the block at the seam. The layout line comes along because the blocks land
    on the STUD module, whose phase is a property of the line and not of the wall.
    """
    from typehaus.resolve.layout_lines import lines_by_wall

    lines_for_wall = lines_by_wall(model.layout_lines)
    resolved_by_tag = {wall.tag: wall for wall in model.walls}
    roles_by_layer: dict[str, dict[tuple[str, str], str]] = {}

    def roles_for(layer_name: str) -> dict[tuple[str, str], str]:
        if layer_name not in roles_by_layer:
            roles_by_layer[layer_name] = continuation_roles(
                model, lambda tag: _furring_module_signature(
                    plan, resolved_by_tag.get(tag), lines_for_wall.get(tag), layer_name))
        return roles_by_layer[layer_name]

    def context(wall_tag: str) -> tuple[object | None,
                                        tuple[str | None, str | None]]:
        wall = resolved_by_tag.get(wall_tag)
        bands = truss_girt_bands(plan, wall.assembly) if wall is not None else None
        if bands is None:
            return lines_for_wall.get(wall_tag), (None, None)
        roles = roles_for(bands[1].name)
        return (lines_for_wall.get(wall_tag),
                (roles.get((wall_tag, "start")), roles.get((wall_tag, "end"))))

    return context


def _outrigger_band(wall: ResolvedWall, layer_name: str) -> ResolvedLayer | None:
    return next((layer for layer in wall.layers
                if layer.name == layer_name and layer.polygon), None)


def _corner_cap_frame(plan: PlanModel, wall: ResolvedWall) -> TrussFrame | None:
    """This wall's ``TrussFrame``, only if its outrigger band opted into the corner box."""
    layer_name = truss_layer_name(plan, wall.assembly)
    if layer_name is None:
        return None
    assembly = plan.library.resolve_assembly(wall.assembly)
    spec = next((ly.framing for ly in (assembly.layers if assembly else ())
                if ly.name == layer_name and ly.framing is not None), None)
    if spec is None or spec.corner_cap != "plywood-box":
        return None
    band = _outrigger_band(wall, layer_name)
    if band is None:
        return None
    return TrussFrame.build(plan, wall, band)


def _frame_corner_caps(plan: PlanModel, model: ResolvedModel,
                       corners: CornerJunctions) -> dict[str, list[FramedMember]]:
    """The plywood corner box's two rips (one per wall), keyed by the OWNER that emits both.

    ``junction.framing_owner`` (``corners.owner``, read off the same topology
    ``solver.frame_model`` uses for the stud pack) is the deterministic tiebreak: exactly
    one wall per corner builds both pieces, so the corner is never doubled or skipped
    because both incident walls thought it was the other one's job. The second rip stands
    on the NEIGHBOUR's own band, but is still returned under the owner's key — it is one
    corner box, and the owner is who models it.
    """
    by_tag = {wall.tag: wall for wall in model.walls}
    caps: dict[str, list[FramedMember]] = {}
    for wall_tag, endpoints in corners.owner.items():
        wall = by_tag.get(wall_tag)
        if wall is None:
            continue
        frame = _corner_cap_frame(plan, wall)
        if frame is None:
            continue
        for endpoint in endpoints:
            neighbour_tag, neighbour_endpoint = corners.neighbours.get(
                (wall_tag, endpoint), ("", ""))
            neighbour = by_tag.get(neighbour_tag)
            if neighbour is None:
                continue
            neighbour_frame = _corner_cap_frame(plan, neighbour)
            if neighbour_frame is None:
                continue
            own_band = _outrigger_band(wall, truss_layer_name(plan, wall.assembly) or "")
            neighbour_band = _outrigger_band(
                neighbour, truss_layer_name(plan, neighbour.assembly) or "")
            if own_band is None or neighbour_band is None:
                continue
            pieces = [
                frame.corner_box(endpoint == "start", neighbour_band.polygon),
                neighbour_frame.corner_box(neighbour_endpoint == "start", own_band.polygon),
            ]
            caps.setdefault(wall_tag, []).extend(
                member for member in pieces if member is not None)
    return caps


def frame_wall_truss(plan: PlanModel, wall: ResolvedWall,
                     openings: list[ResolvedOpening]
                     ) -> tuple[tuple[FramedMember, ...], tuple[str, ...], tuple[str, ...]]:
    """Every truss piece on one wall, plus the loose and dropped field keys.

    ``()`` for all three if the wall is not a truss wall.

    Order matters and is the whole of the sequencing here. The jamb outriggers come first,
    because they are outriggers and carry packs like any other; the packs come next, because
    where their tabs land is not knowable until they are placed; and the ladder blocking and
    the bucks come last, because both have to give way to a tab rather than run through one.
    """
    layer_name = truss_layer_name(plan, wall.assembly)
    if layer_name is None:
        return (), (), ()
    band = next((layer for layer in wall.layers if layer.name == layer_name
                 and layer.polygon), None)
    if band is None:
        return (), (), ()
    frame = TrussFrame.build(plan, wall, band)
    if frame is None:
        return (), (), ()

    field = [member for member in wall.members
             if member.child_key.startswith(f"strapping-{layer_name}-")]
    members, loose = _frame_field(frame, wall, openings, field)
    # A band end strip and the last module outrigger can land inches apart. Where that left
    # the end strip with no block and no tab, the module one is the stick that goes — omitted
    # rather than framed and left hanging — and the wall is framed again without it
    # (→ ``TrussFrame.crowded_end_neighbours``).
    dropped = frame.crowded_end_neighbours(field, loose)
    if dropped:
        field = [member for member in field if member.child_key not in dropped]
        members, loose = _frame_field(frame, wall, openings, field)
    return members, loose, dropped


def _frame_field(frame: TrussFrame, wall: ResolvedWall,
                 openings: list[ResolvedOpening], field: list[FramedMember]
                 ) -> tuple[tuple[FramedMember, ...], tuple[str, ...]]:
    """Jambs, packs, ladders and bucks for one outrigger field, and its unpacked keys."""
    # (station, z0, z1) — the elevation band matters: an outrigger inside an opening's own
    # width was cut around it, so it is not wood at that opening's jamb (→ nearest_bearing_gap).
    stations = sorted((frame.station_of(member), member.z0_m, member.z1_m)
                      for member in field)

    members: list[FramedMember] = []
    packable: list[tuple[FramedMember, float]] = [(member, 1.0) for member in field]
    supports: list[tuple[float, float]] = []
    for index, opening in enumerate(openings):
        jambs, added, fillers = frame.jamb_outriggers(opening, index, stations)
        supports.append(jambs)
        members.extend(member for member, _prefer in added)
        members.extend(fillers)
        packable.extend(added)

    # The rough openings, as plan-and-elevation voids no block or tab may reach into. A
    # field outrigger is already cut around an opening, so its pack cannot land in one; a
    # JAMB outrigger runs past the RO from the sole plate to the head, and without this its
    # 3-1/2" block would swing straight across the glass whenever the hand it wanted was
    # taken by the pack next door.
    voids = [(opening.center_along_m - opening.width_m / 2.0,
              opening.center_along_m + opening.width_m / 2.0,
              wall.base_ref_z_m + opening.sill_m,
              wall.base_ref_z_m + opening.sill_m + opening.height_m)
             for opening in openings]
    packs, tabs, loose = frame.pack_all(packable, voids)
    members.extend(packs)

    for index, opening in enumerate(openings):
        members.extend(frame.ladder(supports[index], opening, index, tabs))
        members.extend(frame.buck(opening, index))
    return tuple(members), loose


# --- the girt wall (``framing/truss_girts.py`` places the pieces; this drives it) ------


def girt_band_findings(plan: PlanModel, wall_tag: str,
                       assembly_tag: str | None) -> list[Finding]:
    """WARN for an assembly that asks for girts but does not describe a pair of them.

    A girt band is only meaningful as one of two: the inner tier is what block-2 screws into
    and the outer tier is what the cladding lands on, and either alone is a band of wood
    standing in foam holding nothing. Turning one on edge, or laying it vertically, is the
    same mistake spelled differently — ``integrity.assembly_layers`` already refuses
    ``laid="edge"`` outright, and this catches the rest at the wall that uses it, where the
    tag an owner can act on is in hand.
    """
    bands = _standoff_layers(plan, assembly_tag)
    if not bands or truss_girt_bands(plan, assembly_tag) is not None:
        return []
    names = ", ".join(layer.name for layer in bands)
    return [Finding(
        check_id="structural.truss_girt_bands",
        severity=Severity.WARN, result=Result.UNKNOWN,
        message=(f"{wall_tag}: assembly {assembly_tag} carries {len(bands)} "
                 f'standoff="block" FURRING layer(s) ({names}); a catlin truss is exactly '
                 "two, both horizontal and both laid flat — no girts were framed"),
        element_tags=(wall_tag,),
        fix_hint=('author an inner and an outer girt band, each with '
                  'direction="horizontal" and the default laid="flat"'))]


# --- the girt wall's per-wall entry point ---------------------------------------------


def frame_wall_girts(plan: PlanModel, wall: ResolvedWall, openings: list[ResolvedOpening],
                     line: object | None,
                     continuations: tuple[str | None, str | None],
                     ) -> tuple[tuple[FramedMember, ...], list[Finding]]:
    """Every catlin-truss piece on one wall: blocks, jamb posts, head/sill courses, bucks.

    ``()`` if the wall is not a girt wall, or if either band failed to resolve a polygon —
    a band mitred away to nothing at a corner frames nothing, and that is not an error.
    """
    bands = truss_girt_bands(plan, wall.assembly)
    if bands is None:
        return (), girt_band_findings(plan, wall.tag, wall.assembly)
    resolved = {layer.name: layer for layer in wall.layers if layer.polygon}
    inner = resolved.get(bands[0].name)
    outer = resolved.get(bands[1].name)
    if inner is None or outer is None:
        return (), []
    frame = GirtFrame.build(plan, wall, inner, outer, line, continuations)
    if frame is None:
        return (), []

    field = {tier: [member for member in wall.members
                    if member.child_key.startswith(f"strapping-{name}-")]
             for tier, name in ((INNER, inner.name), (OUTER, outer.name))}
    voids = [(op.center_along_m - op.width_m / 2.0,
              op.center_along_m + op.width_m / 2.0,
              wall.base_ref_z_m + op.sill_m,
              wall.base_ref_z_m + op.sill_m + op.height_m)
             for op in openings]
    # Where a field course stops against an opening's jamb post rather than in open wall —
    # the post's outer face, which is the RO edge plus exactly the margin the field is held
    # back by (``furring.opening_margin``). Read from the same function the courses were cut
    # with, so the two cannot drift apart by a sixteenth and quietly reinstate the end block.
    margin = opening_margin(bands[1].framing)
    butts = tuple(x for op in openings
                  for x in (op.center_along_m - op.width_m / 2.0 - margin,
                            op.center_along_m + op.width_m / 2.0 + margin))
    # The wall's own vertical framing, so a block near an opening lands on the stick that
    # is actually there rather than on the module station the opening displaced.
    verticals = tuple(
        (frame.station_of(member), member.z0_m, member.z1_m)
        for member in wall.members if member.category in STUDLIKE)
    members, findings = frame.blocks(field, voids, butts, verticals)
    elevations = course_elevations(wall, bands[1].framing, frame.stock_face)
    for index, opening in enumerate(openings):
        members.extend(frame.opening_frame(opening, index, elevations))
        members.extend(frame.buck(opening, index))
    return tuple(members), findings
