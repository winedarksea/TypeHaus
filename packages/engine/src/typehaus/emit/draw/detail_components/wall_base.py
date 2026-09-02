"""The base of a wall where it meets its foundation and the slab beside it.

References: ``basement_to_framed_wall_detail_ifc.png`` (Z-flashing at the sill, L-flashing
returning onto the basement foam, insect screen, sill gasket, sealant beads) and
``garage_wall_detail_side_ifc.png`` (the same base treated for an unheated slab-on-grade:
an interior drip flashing turning water in onto the sloped slab, and a protection board over
the foundation foam wherever it surfaces above grade).

Every component here derives its position from the resolved layer faces at the junction, so
a change to the wall build-up moves the flashing with the plane it laps.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import (
    BASEMENT_TO_FRAMED_WALL,
    FOUNDATION_FACE,
    INTERIOR_SLAB_DRIP,
    SLAB_EDGE,
)
from typehaus.emit.draw.detail_components.geometry import (
    face_of,
    flashing_nodes,
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    path_from_steps,
    rect_region,
    slab_at_junction,
    vent_face,
    wall_cut_bounds_m,
)
from typehaus.emit.draw.scene import IRNode
from typehaus.quantities import M_PER_IN
from typehaus.resolve.accessories import BUG_SCREEN_HEIGHT_IN, BUG_SCREEN_MATERIAL
from typehaus.resolve.model import ResolvedLayer, ResolvedWall

# How near a banded layer's top must land on the wall top to read as "runs to the top" —
# a protection panel is ordered flush with the wall it faces, not to a course line.
_PANEL_TOP_TOL_M = 0.5 * M_PER_IN


def basement_framed_wall(model, framed, concrete, crop, direction,
                         station) -> list[IRNode]:
    """Flashings + air-seal components at the basement→framed-wall transition."""
    is_outboard_high = outboard_is_high(framed, direction, station)
    if is_outboard_high is None or crop is None:
        return []
    # The top of the POUR, which is where the flashings, the gasket and the mudsill all
    # land. It was read off ``framed.z0_m`` — "top of concrete == bottom of framed wall" —
    # and that equality died on 2026-08-23: catlin's basement walls top out on the bearing
    # seat at -13 7/16" while the framed wall above them still starts at the storey datum,
    # so the whole detail drew 13 7/16" above the concrete it is a detail of. The garage
    # stem, where the two ARE the same elevation, is unchanged by reading the concrete.
    junction_z = concrete.z1_m / M_PER_IN
    intervals = layer_intervals(framed, direction, station)
    out_sign = 1.0 if is_outboard_high else -1.0

    nodes: list[IRNode] = []
    nodes += _l_flashing_and_bead(intervals, is_outboard_high, out_sign, junction_z)
    nodes += _z_flashing_and_screen(framed, intervals, is_outboard_high, out_sign,
                                    junction_z)

    # Sill gasket under the treated mudsill, sealing the stud line to the concrete — the
    # authored ``FramingSpec.sill_gasket`` thickness when the assembly carries one, else
    # the pinned reference. Both are the compressed, in-place joint (1/16"), not the roll.
    stud = outermost_with_function(intervals, "structure")
    if stud is not None:
        # Filled with the no-overlay ``metal`` pattern rather than a hatch family: at 1/16"
        # any hatch collapses into a smear, but the fill is what carries the material colour
        # to the writers, and an outline alone reads as an empty gap in the drawing.
        gasket_in = sill_gasket_in(model, framed)
        nodes += rect_region(stud[0], junction_z, stud[1], junction_z + gasket_in,
                             "sill-gasket", "rubber", "metal", lineweight=0.35)

    if concrete is not None:
        # Discrete 1" break where a slab edge meets the foundation wall, protection over
        # any foundation foam that surfaces above grade, and the interior drip at an
        # unheated slab-on-grade. All self-gate on their subject being in frame, so a
        # junction without one draws nothing rather than guessing.
        nodes += slab_thermal_break(model, concrete, crop, direction, station)
        nodes += interior_slab_drip_flashing(model, concrete, crop, direction, station)
        nodes += foam_protection_board(model, concrete, crop, direction, station)
    return nodes


def _l_flashing_and_bead(intervals, is_outboard_high, out_sign, junction_z) -> list[IRNode]:
    """L-flashing from the sheathing face turning down onto the foundation foam, sealed.

    This is the interface flashing the notes call for: it terminates the framed wall's
    drainage plane *within* the foam plane below, so water leaving the sheathing cannot run
    behind the foundation insulation.
    """
    cfg = BASEMENT_TO_FRAMED_WALL
    sheath = outermost_with_function(intervals, "sheathing")
    foam = outermost_with_function(intervals, "insulation")
    if sheath is None or foam is None:
        return []
    sheath_out = face_of(sheath, is_outboard_high, outer=True)
    foam_out = face_of(foam, is_outboard_high, outer=True)
    path = path_from_steps((sheath_out, junction_z + cfg.l_flashing_rise_in),
                           [(0.0, -cfg.l_flashing_drop_in),
                            ((foam_out - sheath_out), 0.0)])
    nodes = flashing_nodes(path, tag="l-flashing")
    # Spray-foam sealant bead at the outer end, so the flashing terminates sealed rather
    # than open — an unsealed end is an insect path straight into the foam.
    bead_back = foam_out - out_sign * cfg.sealant_bead_in
    nodes += rect_region(bead_back, junction_z, foam_out,
                         junction_z + cfg.sealant_bead_height_in,
                         "sealant-bead", "spray-foam", "foam", lineweight=0.3)
    return nodes


def _z_flashing_and_screen(wall, intervals, is_outboard_high, out_sign,
                           junction_z) -> list[IRNode]:
    """Z-flashing with a drip at the bottom of the rainscreen, screened above it.

    The rainscreen cavity has to drain and vent at its base; the Z-flashing kicks the water
    out and the bug screen keeps the open cavity from becoming an insect route.

    The screen band is the same corrugated vent strip the resolver derives as geometry and
    the take-off bills by the lineal foot, so its height comes from
    ``BUG_SCREEN_HEIGHT_IN`` rather than from a drawing-only constant: the section shows the
    product that is actually on the order. It carries the material tag so the writers colour
    it as the polypropylene section it is instead of leaving it an unfilled outline.

    **It spans the vented GAP, not the furring band.** Those are the same thing on an empty
    band and are not the same thing on a truss wall, where 2-1/2" of the 3-1/2" band is
    packed with foam: drawn band-wide the strip is 3-1/2" of screen against the 1" the
    resolver builds and the take-off orders. ``vent_face`` is the shared reading.

    The Z-flashing itself still starts at the band's back — it is the pan under the whole
    outrigger zone, foam and gap both, and it laps the L-flashing that comes out from the
    sheathing face. Only the screen closes the part that is open.
    """
    cfg = BASEMENT_TO_FRAMED_WALL
    furring = outermost_with_function(intervals, "furring")
    clad = outermost_with_function(intervals, "cladding")
    if furring is None or clad is None:
        return []
    fur_in = face_of(furring, is_outboard_high, outer=False)
    clad_out = face_of(clad, is_outboard_high, outer=True)
    path = path_from_steps((fur_in, junction_z + cfg.z_flashing_rise_in), [
        (0.0, -cfg.z_flashing_drop_in),
        ((clad_out - fur_in), 0.0),
        (out_sign * cfg.z_flashing_lip_in, 0.0),
        (0.0, -cfg.z_flashing_face_in),
        (out_sign * cfg.z_flashing_kick_in, -cfg.z_flashing_kick_drop_in),
    ])
    nodes = flashing_nodes(path, tag="z-flashing")
    fur_out = face_of(furring, is_outboard_high, outer=True)
    gap_in = vent_face(wall, furring, is_outboard_high)
    nodes += rect_region(gap_in, junction_z + cfg.screen_rise_in, fur_out,
                         junction_z + cfg.screen_rise_in + BUG_SCREEN_HEIGHT_IN,
                         "bug-screen", BUG_SCREEN_MATERIAL, "rigid", lineweight=0.3)
    return nodes


def sill_gasket_in(model, wall) -> float:
    """The drawn sill-gasket thickness (inches) for this wall.

    Prefers the authored ``FramingSpec.sill_gasket`` on the wall assembly's structure
    layer — the model field that owns the fact — and falls back to the pinned reference
    when no layer carries one. Both are the **compressed** thickness since 2026-08-24:
    what the joint measures once the plate is bolted down, not the roll it came off.
    """
    assembly = model.plan.library.resolve_assembly(wall.assembly)
    if assembly is not None:
        for layer in assembly.layers:
            spec = getattr(layer, "framing", None)
            if spec is not None and getattr(spec, "sill_gasket", None) is not None:
                return spec.sill_gasket.meters / M_PER_IN
    return BASEMENT_TO_FRAMED_WALL.sill_gasket_in


def thermal_break_spec(model, slab_solid):
    """The authored ``SlabThermalBreak`` on the cut slab's plan source, or None."""
    source = model.plan.by_tag(slab_solid.tag)
    return getattr(source, "perimeter_thermal_break", None)


def slab_thermal_break(model, wall, crop, direction, station) -> list[IRNode]:
    """Discrete rigid thermal break + polyurethane sealant cap at the slab→wall edge.

    Its own labelled component, distinct from the roof→wall spray-foam wedge. Derived from
    the resolved slab and wall face, drawn only when a slab edge is genuinely in frame.
    The break's thickness and how far it runs down the slab edge prefer the authored
    ``Slab.perimeter_thermal_break`` when the slab carries one; the pinned reference
    (1" XPS, full slab depth, 1/2" sealant cap) is the fallback.
    """
    is_outboard_high = outboard_is_high(wall, direction, station)
    if is_outboard_high is None:
        return []
    u_lo, u_hi = wall_cut_bounds_m(wall, direction, station)
    if u_lo is None:
        return []
    inboard_face_m = u_lo if is_outboard_high else u_hi
    in_sign = -1.0 if is_outboard_high else 1.0
    slab = slab_at_junction(model, crop, direction, station, inboard_face_m)
    if slab is None:
        return []
    face = inboard_face_m / M_PER_IN
    slab_top, slab_bottom = slab.z1_m / M_PER_IN, slab.z0_m / M_PER_IN
    spec = thermal_break_spec(model, slab)
    thickness_in = (spec.thickness.meters / M_PER_IN if spec is not None
                    else SLAB_EDGE.thermal_break_in)
    if spec is not None and spec.depth is not None:
        slab_bottom = max(slab_bottom, slab_top - spec.depth.meters / M_PER_IN)
    inner_edge = face + in_sign * thickness_in
    nodes = rect_region(face, slab_bottom, inner_edge, slab_top,
                        "thermal-break", "xps", "rigid", lineweight=0.35)
    nodes += rect_region(face, slab_top, inner_edge, slab_top + SLAB_EDGE.sealant_cap_in,
                         "thermal-break-sealant", "sealant", "metal", lineweight=0.3)
    return nodes


def slab_is_on_grade(model, slab) -> bool:
    """True when no enclosed space sits beneath the slab — a genuine slab-on-grade.

    Discriminated from the model, never from the assembly name: a resolved room on a lower
    storey whose clear face covers the slab's centroid, with that storey's floor below the
    slab's underside, means the "slab" is really a suspended deck over occupied space (the
    main-floor deck over the basement), and the on-grade vocabulary would be fiction there.
    """
    from shapely.geometry import Polygon

    if len(slab.outline) < 3:
        return True
    centroid = Polygon(slab.outline).centroid
    for room in model.rooms:
        if len(room.clear_face) < 3:
            continue
        storey = model.plan.storey(room.storey)
        if storey is None or storey.elevation.meters >= slab.z0_m:
            continue
        if Polygon(room.clear_face).covers(centroid):
            return False
    return True


def interior_slab_drip_flashing(model, wall, crop, direction, station) -> list[IRNode]:
    """Interior drip flashing turning water in onto an unheated slab-on-grade.

    The garage reference's remaining piece: water coming down the stem's interior face
    (blown past the overhead door, or condensation on the cold concrete) is turned out onto
    the sloped slab instead of wicking into the wall base. Gated on the cut slab genuinely
    being on grade — a suspended deck over occupied space below (the main-floor deck over
    the conditioned basement) drains to no apron, so drawing the drip there would lie.
    """
    is_outboard_high = outboard_is_high(wall, direction, station)
    if is_outboard_high is None or crop is None:
        return []
    u_lo, u_hi = wall_cut_bounds_m(wall, direction, station)
    if u_lo is None:
        return []
    inboard_face_m = u_lo if is_outboard_high else u_hi
    in_sign = -1.0 if is_outboard_high else 1.0
    slab = slab_at_junction(model, crop, direction, station, inboard_face_m)
    if slab is None or not slab_is_on_grade(model, slab):
        return []
    cfg = INTERIOR_SLAB_DRIP
    face = inboard_face_m / M_PER_IN
    slab_top = slab.z1_m / M_PER_IN
    path = path_from_steps((face, slab_top + cfg.rise_in),
                           [(0.0, -cfg.rise_in),
                            (in_sign * cfg.run_in, 0.0),
                            (in_sign * cfg.kick_in, -cfg.kick_drop_in)])
    return flashing_nodes(path, tag="interior-drip-flashing")


def _authored_protection_band(wall: ResolvedWall) -> ResolvedLayer | None:
    """The resolved layer that *is* the protection panel, when the assembly models one.

    A protection panel is an ordinary outboard layer carrying a ``Layer.extent`` — a band
    off the GRADE datum — so once an assembly authors one the drawing must read it rather
    than deriving a second band beside it. Two derivations of one detail diverge: the
    drawing showed 2'-6" of trim while the order billed a parge coat over the whole 9'.
    Consolidating here is the same move ``wall_base`` already made for the bug screen, whose
    material and height it imports straight from ``resolve/accessories.py``.

    **"The last banded layer" is not the test, and used to be.** A band is a general
    mechanism — an interior thermal barrier above grade, a brick ledge below it — and only
    a band that both stands OUTBOARD OF THE INSULATION it protects and runs UP TO THE WALL
    TOP is the panel this component draws. Catlin's garage ICF stem carries an interior
    ``gwb-stem`` band (code.R316_4) and, on its two brick-ledged east segments, an outboard
    ``brick-ledge`` band that runs from the wall base up to one course above grade. The old
    rule read the gypsum on one and the concrete ledge on the other, drawing a "protection
    board" over a buried shelf. Neither is a protection panel; both walls fall through to
    the derived band below, which is grade-to-top on the outboard foam face — the same
    answer the gypsum coincidentally gave.
    """
    layers = [layer for layer in wall.layers if not getattr(layer, "is_cavity", False)]
    last_foam = max((index for index, layer in enumerate(layers)
                     if layer.function == "insulation"), default=None)
    if last_foam is None:
        return None
    wall_top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    for layer in reversed(layers[last_foam + 1:]):
        if not getattr(layer, "is_banded", False):
            continue
        _band_z0, band_z1 = layer.band(wall)
        if abs(band_z1 - wall_top) <= _PANEL_TOP_TOL_M:
            return layer
    return None


def _foam_is_already_covered(wall: ResolvedWall) -> bool:
    """Whether a full-height layer stands outboard of the wall's outermost insulation.

    A latent trap worth naming, surfaced by houses/catlin on 2026-09-02. That house's
    sunken-garden curbs used to return True here (a full-height parge coat sat outboard of
    their XPS) and now return False — their outboard face is bare foam inside a ventilated
    brick cavity. They draw no protection board anyway, but only because ``site.grade`` is a
    single house-wide number: the curb tops are 5'-8" below it, so the derived branch's
    ``height_in`` comes out negative and falls under ``min_exposed_height_in``.

    That gate knows nothing about an excavation. A wall standing in an open court whose floor
    is nine feet below grade reads as deeply buried, and if this dispatch ever changes — or a
    curb like that is ever authored near grade — the derived branch will happily draw
    protection board on a face inside a brick cavity, where nothing hits it and nothing sees
    it. The fix, when it is needed, is local grade, not a wider tolerance here.
    """
    layers = [ly for ly in wall.layers if not getattr(ly, "is_cavity", False)]
    last_foam = max((index for index, ly in enumerate(layers)
                     if ly.function == "insulation"), default=None)
    if last_foam is None:
        return False
    return any(not getattr(ly, "is_banded", False) for ly in layers[last_foam + 1:])


def foam_protection_board(model, wall, crop, direction, station) -> list[IRNode]:
    """Protection board over foundation insulation wherever it surfaces above grade.

    Rigid foam left exposed above grade fails: UV degrades it and the first wheelbarrow
    damages it, so both the basement notes and the garage reference call for a coating or
    trim over the exposed height.

    Where the assembly *models* the panel — an outboard layer with a ``Layer.extent`` off
    the grade datum — its own resolved band and thickness are drawn, so the sheet and the
    order are the same piece of material. Otherwise the band is derived, running from the
    site grade to the top of the foundation wall on whichever side the outboard insulation
    actually is; either way it draws nothing at all when no foam surfaces in frame.
    """
    site = model.plan.project.site
    if site.grade is None or crop is None:
        return []
    is_outboard_high = outboard_is_high(wall, direction, station)
    if is_outboard_high is None:
        return []
    intervals = layer_intervals(wall, direction, station)
    foam = outermost_with_function(intervals, "insulation")
    if foam is None:
        return []
    (_cu0, cz0), (_cu1, cz1) = crop
    wall_top = (wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m)
    authored = _authored_protection_band(wall)
    if authored is not None:
        band_z0, band_z1 = authored.band(wall)
        thickness_in = authored.thickness_m / M_PER_IN
        panel = intervals.get(authored.name)
        face_in = (face_of(panel, is_outboard_high, outer=False) if panel is not None
                   else face_of(foam, is_outboard_high, outer=True))
    elif _foam_is_already_covered(wall):
        # Something full-height already stands outboard of the foam — catlin's south
        # basement wall wears a parge coat over its whole nine feet, because the sunken
        # garden exposes it over its whole nine feet. Drawing a protection board on top of
        # that is a second skin over a face that has one, and an order for material nobody
        # applies. The rule is "protect foam that surfaces *bare*", not "surfaces".
        return []
    else:
        band_z0, band_z1 = site.grade.meters, wall_top
        thickness_in = FOUNDATION_FACE.protection_board_in
        face_in = face_of(foam, is_outboard_high, outer=True)
    exposed_top = min(band_z1, max(cz0, cz1))
    exposed_bottom = max(band_z0, min(cz0, cz1))
    height_in = (exposed_top - exposed_bottom) / M_PER_IN
    if height_in < FOUNDATION_FACE.min_exposed_height_in:
        return []
    out_sign = 1.0 if is_outboard_high else -1.0
    return rect_region(face_in, exposed_bottom / M_PER_IN,
                       face_in + out_sign * thickness_in,
                       exposed_top / M_PER_IN,
                       "foam-protection-board", "metal-dark", "SOLID", lineweight=0.4)
