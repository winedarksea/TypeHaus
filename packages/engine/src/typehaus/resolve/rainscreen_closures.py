"""Rainscreen insect closures: the screen where a cavity begins, and the head spans.

The vented cavity behind the cladding is a sheltered void that ants, wasps and mice will use
if they can reach it, and the only protection a ccSPF face in it has is physical. The base of
a cavity is its inlet: a perforated aluminium inverted U on the base Z, captive under the
raised steel base trim, so air and water pass and insects do not
(``notes/metal_trim_kit.md`` "Wall base stack"). Window and door heads are drained, not
vented: a head cap floors the cavity above each one (``opening_flashing``), and the panel end
sits on a perforated strip (``rainscreen_strips``). The cavity TOP stays closed by the roof
deck oversailing the girt face (``roof_layer_setbacks``), so nothing is derived there.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace

from typehaus.model.enums import LayerFunction, TrimKind
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import clip_half_plane, length, sub, wall_frame
from typehaus.resolve.model import (
    ResolvedLayer,
    ResolvedModel,
    ResolvedOpening,
    ResolvedSolid,
)

# Perforated 0.032" aluminium, 3 mm holes on a 5 mm 60-degree stagger: holes under 1/8" keep
# insects out, and the stagger leaves pi/(2*sqrt(3)) * (3/5)^2 = 32.6% open. The base screen
# is an inverted U across the 2" cavity, 2" tall, braked from the sheet.
BUG_SCREEN_MATERIAL = "perforated-aluminum-insect-closure"
BUG_SCREEN_HOLE_IN = 3.0 / 25.4
BUG_SCREEN_OPEN_FRACTION = math.pi / (2.0 * math.sqrt(3.0)) * (3.0 / 5.0) ** 2
BUG_SCREEN_SHEET_IN = 0.032
BUG_SCREEN_HEIGHT_IN = 2.0
BUG_SCREEN_STOCK_IN = 120.0
BUG_SCREEN_LAP_IN = 2.0
#: DIN 18516-1's minimum net free area for a rainscreen cavity's inlet and outlet.
MIN_NET_FREE_AREA_CM2_PER_M = 50.0
BASE_SCREEN_PRODUCT = "BASE_SCREEN"
_STACK_TOLERANCE_M = 0.05   # a storey's walls land exactly on the one below; this is slop
_STACK_PLAN_TOL_M = 0.5     # two stacked walls share a plan line within a wall's thickness


def net_free_area_cm2_per_m(open_height_m: float) -> float:
    """Net free area of a perforated face ``open_height_m`` tall, per metre of run."""
    return max(0.0, open_height_m) * 100.0 * BUG_SCREEN_OPEN_FRACTION * 100.0


@dataclass(frozen=True)
class CavityBaseRun:
    wall: object
    outline: tuple[tuple[float, float], ...]
    depth_m: float
    direction: tuple[float, float]
    outward: tuple[float, float]
    inner_offset: float
    outer_offset: float
    start: float
    end: float


def cavity_base_run(model, wall) -> CavityBaseRun | None:
    """The mitred cavity at a true base, shared by flashing, screen and purchasing."""
    if not screens_rainscreen_base(model, wall):
        return None
    from typehaus.resolve.cladding_trim.runs import cladding_face

    band = rainscreen_band(wall.layers)
    if band is None:
        return None
    furring, depth = band
    outline = _vented_band(wall, furring, depth, _cavity_airgap(wall.layers, furring))
    cladding = next((layer for layer in reversed(wall.layers)
                     if layer.function == LayerFunction.CLADDING.value), None)
    face = cladding_face(wall, cladding) if cladding and cladding.polygon else None
    if len(outline) < 3 or face is None:
        return None
    d, n = face.d, face.n
    offsets = [x*n[0] + y*n[1] for x, y in outline]
    outer = max(offsets)
    # The outside edge sets the finished length, including its corner mitres.
    outside = [x*d[0] + y*d[1] for (x, y), off in zip(outline, offsets, strict=True)
               if abs(off - outer) < 1e-7]
    if len(outside) < 2:
        return None
    return CavityBaseRun(wall, tuple(outline), depth, d, n, min(offsets), outer,
                         min(outside), max(outside))


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

    **An AIRGAP layer immediately inboard of the band belongs to the same cavity.** The
    catlin truss's outer girt band is 1-1/2" of solid KDAT — nothing vents inside it — with
    the 1/2" vent gap authored as its own layer behind it. Read band-only, that wall would
    report a 1-1/2"
    cavity that is actually wood, and no cavity at all where the air is. Read together they
    are the 2" of drained, vented, insect-screened space the wall really has, open to the
    outside between the girt courses: 1/2" behind the girts plus the 1-1/2" between them.
    Everything downstream — the bug screen, ``vent_face``, the envelope take-off, the roof
    layer setbacks — follows this one number.

    **A STRUCTURE layer between the band and the cladding cancels the band**, for the
    reason spelled out at the branch below: nothing vents through the wall's own structure.

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
        elif layer.function == LayerFunction.STRUCTURE.value:
            # **A cavity cannot vent to the outside through the wall's own structure.** A
            # furring band INBOARD of the structure is a liner or service batten, and a
            # cladding layer on the far side of 8" of concrete does not turn it into a
            # rainscreen. Without this, catlin's `SAUNA_LINER_ON_BASEMENT_8` — the sauna's
            # T&G-on-furring liner inboard of a buried pour, with the above-grade acrylic
            # protection band (function CLADDING, deliberately) outboard of it — resolved a
            # 1/2" rainscreen and an insect closure at the bottom of a wall standing under
            # 6'-4" of soil, and billed it.
            band, depth = None, 0.0
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


def pan_top_z(wall, spec, run: CavityBaseRun, offset: float) -> float:
    """The base Z's upper face at an outward ``offset``: it falls ``spec.slope`` outward."""
    return (wall.z0_m + spec.sheet_thickness.meters * math.sqrt(1.0 + spec.slope ** 2)
            - spec.slope * (offset - run.inner_offset))


def base_flashing_spec(model, wall):
    assembly = model.plan.library.resolve_assembly(wall.assembly)
    return assembly.rainscreen_base_flashing if assembly else None


def apply_girt_starter_rise(model: ResolvedModel) -> None:
    """Lift the starter girt clear of the base Z wherever a cavity begins (before framing).

    The girts go on the flat wall before tilt-up and the Z after the foam, so a starter on
    the seat could not be built, and it would put KDAT on aluminium (AWC DCA6)."""
    walls = []
    for wall in model.walls:
        spec = base_flashing_spec(model, wall)
        if spec is not None and screens_rainscreen_base(model, wall):
            wall = replace(wall, girt_starter_rise_m=spec.starter_rise.meters)
        walls.append(wall)
    model.walls = walls


def resolve_bug_screens(model: ResolvedModel) -> None:
    """A perforated inverted U on the base Z wherever a rainscreen cavity begins.

    Derived rather than authored: the screen exists because of how the wall is built, so the
    next exterior wall someone draws cannot ship an open cavity for wasps. It spans the vented
    band (:func:`_vented_band`) from the Z upstand to the girt plane, its legs seated on the
    sloped pan, and it is cut from stock and mitred at corners like the Z under it. Only the
    *bottom* of a cavity is screened (:func:`_continues_cavity_below`).
    """
    from typehaus.resolve.cladding_trim.members import split_stock_run
    from typehaus.resolve.cladding_trim.section import folded_section_mesh
    from typehaus.resolve.rainscreen_base_flashing import _mitre_mesh

    sheet = BUG_SCREEN_SHEET_IN * M_PER_IN
    height = BUG_SCREEN_HEIGHT_IN * M_PER_IN
    for wall in model.walls:
        run = cavity_base_run(model, wall)
        spec = base_flashing_spec(model, wall)
        if spec is None:
            _boxed_screen(model, wall, run, height)
            continue
        if run is None:
            continue
        depth = run.outer_offset - run.inner_offset
        inner_z = pan_top_z(wall, spec, run, run.inner_offset)
        section = ((0.0, 0.0), (0.0, height), (depth, height), (depth, -depth * spec.slope))
        total = run.end - run.start
        for index, (start, end, stock) in enumerate(split_stock_run(
                total, (BUG_SCREEN_STOCK_IN * M_PER_IN,), BUG_SCREEN_LAP_IN * M_PER_IN)):
            station = run.start + start
            origin = (station * run.direction[0] + run.inner_offset * run.outward[0],
                      station * run.direction[1] + run.inner_offset * run.outward[1], inner_z)
            mesh = folded_section_mesh(section, origin, (*run.outward, 0.0), (0.0, 0.0, 1.0),
                                       (run.direction[0] * (end - start),
                                        run.direction[1] * (end - start), 0.0), sheet)
            mesh = _mitre_mesh(mesh, run, start, end, total)
            xs, ys, zs = zip(*mesh.positions, strict=True)
            model.solids.append(ResolvedSolid(
                uid=f"{wall.uid}-bugscreen-{index}", tag=f"{wall.tag}-BUGSCREEN-{index + 1}",
                storey=wall.storey, category=TrimKind.BUG_SCREEN.value,
                material=BUG_SCREEN_MATERIAL, product=BASE_SCREEN_PRODUCT, host_ref=wall.tag,
                outline=((min(xs), min(ys)), (max(xs), min(ys)),
                         (max(xs), max(ys)), (min(xs), max(ys))),
                z0_m=min(zs), z1_m=max(zs), assembly=wall.assembly, body_mesh=mesh,
                trim_length_m=end - start,
                trim_stock_length_in=round(stock / M_PER_IN, 6)))


def _boxed_screen(model, wall, run, height) -> None:
    """With no formed Z to seat a U on, the screen is drawn as a box filling the vented band."""
    found = rainscreen_band(wall.layers)
    if found is None or not screens_rainscreen_base(model, wall):
        return
    furring, vent = found
    outline = _vented_band(wall, furring, vent, _cavity_airgap(wall.layers, furring))
    if len(outline) < 3:
        return
    _origin, tangent, _across, _length = wall_frame(wall)
    along = [x * tangent[0] + y * tangent[1] for x, y in outline]
    model.solids.append(ResolvedSolid(
        uid=f"{wall.uid}-bugscreen", tag=f"{wall.tag}-BUGSCREEN", storey=wall.storey,
        category=TrimKind.BUG_SCREEN.value, material=BUG_SCREEN_MATERIAL,
        product=BASE_SCREEN_PRODUCT, host_ref=wall.tag, outline=tuple(outline),
        z0_m=wall.z0_m, z1_m=wall.z0_m + height, assembly=wall.assembly,
        trim_length_m=run.end - run.start if run else max(along) - min(along)))


def opening_head_spans(model: ResolvedModel, wall
                       ) -> list[tuple[ResolvedOpening, float, float, float]]:
    """``(opening, s0, s1, z)`` for the cavity over each window/door head on a rainscreen wall.

    The span the head cap and the head strip share: the RO plus one stock face past each jamb,
    over the jamb posts, at the top of the head course (the RO head where there is none).
    Stations are along the wall axis from its start. A rough opening is a penetration and
    takes a seal, not a cap.
    """
    if rainscreen_band(wall.layers) is None:
        return []
    from typehaus.resolve.framing.truss_girts import GIRT_MEMBER, truss_girt_bands

    bands = truss_girt_bands(model.plan, wall.assembly)
    face = 0.0
    if bands is not None:
        spec = bands[1].framing
        face = cross_section(spec.member if spec is not None else GIRT_MEMBER).depth_m
    spans = []
    for opening in model.openings:
        if opening.host_wall != wall.tag or opening.kind not in ("window", "door"):
            continue
        half = opening.width_m / 2.0 + face
        z = wall.base_ref_z_m + opening.sill_m + opening.height_m + face
        spans.append((opening, opening.center_along_m - half,
                      opening.center_along_m + half, z))
    return spans


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

