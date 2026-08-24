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
"""


from __future__ import annotations

from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.furring import EDGE, VERTICAL
from typehaus.resolve.framing.truss_frame import (  # noqa: F401 - the package's public names
    BLOCK_CATEGORY,
    BLOCK_LENGTH,
    BLOCK_SPACING,
    BUCK_CATEGORY,
    BUCK_THICKNESS_IN,
    DOUBLE_HEADER_SPAN,
    FILLER_CATEGORY,
    FILLER_LIMIT,
    FLANGE_BEARING,
    LADDER_CATEGORY,
    TAB_CATEGORY,
    TAB_THICKNESS_IN,
    TRUSS_CATEGORIES,
    TrussFrame,
    Vec,
    nearest_bearing_gap,
)
from typehaus.resolve.model import (
    FramedMember,
    ResolvedModel,
    ResolvedOpening,
    ResolvedWall,
)

#: The package face. Everything a caller outside ``resolve/framing`` needs is importable from
#: here whichever side of the truss_wall/truss_frame split it actually lives on, so the split
#: is an internal file-size decision and not an API.
__all__ = [
    "BLOCK_CATEGORY",
    "BLOCK_LENGTH",
    "BLOCK_SPACING",
    "BUCK_CATEGORY",
    "BUCK_THICKNESS_IN",
    "DOUBLE_HEADER_SPAN",
    "FILLER_CATEGORY",
    "FILLER_LIMIT",
    "FLANGE_BEARING",
    "LADDER_CATEGORY",
    "TAB_CATEGORY",
    "TAB_THICKNESS_IN",
    "TRUSS_CATEGORIES",
    "TrussFrame",
    "Vec",
    "frame_truss_walls",
    "frame_wall_truss",
    "nearest_bearing_gap",
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
    """
    by_host: dict[str, list[ResolvedOpening]] = {}
    for opening in model.openings:
        by_host.setdefault(opening.host_wall, []).append(opening)

    findings: list[Finding] = []
    framed: list[ResolvedWall] = []
    for wall in model.walls:
        members, loose = frame_wall_truss(plan, wall, by_host.get(wall.tag, []))
        framed.append(replace(wall, members=wall.members + members) if members else wall)
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


def truss_layer_name(plan: PlanModel, assembly_tag: str | None) -> str | None:
    """The name of the FURRING layer that is a truss wall's outrigger band, or ``None``.

    The signature is a vertical FURRING layer whose ``FramingSpec`` stands the stick on edge:
    a batten laid flat is a rainscreen strip and frames nothing but itself. Read off the
    *authored* assembly, so a check can ask the question without a resolved wall in hand.
    """
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


def frame_wall_truss(plan: PlanModel, wall: ResolvedWall,
                     openings: list[ResolvedOpening]
                     ) -> tuple[tuple[FramedMember, ...], tuple[str, ...]]:
    """Every truss piece on one wall, or ``()`` if the wall is not a truss wall.

    Order matters and is the whole of the sequencing here. The jamb outriggers come first,
    because they are outriggers and carry packs like any other; the packs come next, because
    where their tabs land is not knowable until they are placed; and the ladder blocking and
    the bucks come last, because both have to give way to a tab rather than run through one.
    """
    layer_name = truss_layer_name(plan, wall.assembly)
    if layer_name is None:
        return (), ()
    band = next((layer for layer in wall.layers if layer.name == layer_name
                 and layer.polygon), None)
    if band is None:
        return (), ()
    frame = TrussFrame.build(plan, wall, band)
    if frame is None:
        return (), ()

    field = [member for member in wall.members
             if member.child_key.startswith(f"strapping-{layer_name}-")]
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
              wall.z0_m + opening.sill_m,
              wall.z0_m + opening.sill_m + opening.height_m)
             for opening in openings]
    packs, tabs, loose = frame.pack_all(packable, voids)
    members.extend(packs)

    for index, opening in enumerate(openings):
        members.extend(frame.ladder(supports[index], opening, index, tabs))
        members.extend(frame.buck(opening, index))
    return tuple(members), loose


