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
    M_TO_IN,
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
    wall_cut_bounds_m,
)
from typehaus.emit.draw.scene import IRNode
from typehaus.resolve.accessories import BUG_SCREEN_HEIGHT_IN, BUG_SCREEN_MATERIAL


def basement_framed_wall(model, framed, concrete, crop, direction,
                         station) -> list[IRNode]:
    """Flashings + air-seal components at the basement→framed-wall transition."""
    is_outboard_high = outboard_is_high(framed, direction, station)
    if is_outboard_high is None or crop is None:
        return []
    junction_z = framed.z0_m * M_TO_IN  # top of concrete == bottom of framed wall
    intervals = layer_intervals(framed, direction, station)
    out_sign = 1.0 if is_outboard_high else -1.0
    cfg = BASEMENT_TO_FRAMED_WALL

    nodes: list[IRNode] = []
    nodes += _l_flashing_and_bead(intervals, is_outboard_high, out_sign, junction_z)
    nodes += _z_flashing_and_screen(intervals, is_outboard_high, out_sign, junction_z)

    # Sill gasket under the treated mudsill, sealing the stud line to the concrete — the
    # authored ``FramingSpec.sill_gasket`` thickness when the assembly carries one, else
    # the pinned reference 1/4".
    stud = outermost_with_function(intervals, "structure")
    if stud is not None:
        # Filled with the no-overlay ``metal`` pattern rather than a hatch family: at 1/4"
        # any hatch collapses into a smear, but the fill is what carries the material colour
        # to the writers, and an outline alone reads as an empty gap in the drawing.
        gasket_in = sill_gasket_in(model, framed)
        nodes += rect_region(stud[0], junction_z, stud[1], junction_z + gasket_in,
                             "sill-gasket", "rubber", "metal", lineweight=0.35)

    if concrete is not None:
        # Discrete 1" break where a slab edge meets the foundation wall, and protection over
        # any foundation foam that surfaces above grade. Both self-gate on their subject
        # being in frame, so a junction without one draws nothing rather than guessing.
        nodes += slab_thermal_break(model, concrete, crop, direction, station)
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
                            (out_sign * (foam_out - sheath_out), 0.0)])
    nodes = flashing_nodes(path, tag="l-flashing")
    # Spray-foam sealant bead at the outer end, so the flashing terminates sealed rather
    # than open — an unsealed end is an insect path straight into the foam.
    bead_back = foam_out - out_sign * cfg.sealant_bead_in
    nodes += rect_region(bead_back, junction_z, foam_out,
                         junction_z + cfg.sealant_bead_height_in,
                         "sealant-bead", "spray-foam", "foam", lineweight=0.3)
    return nodes


def _z_flashing_and_screen(intervals, is_outboard_high, out_sign,
                           junction_z) -> list[IRNode]:
    """Z-flashing with a drip at the bottom of the rainscreen, screened above it.

    The rainscreen cavity has to drain and vent at its base; the Z-flashing kicks the water
    out and the bug screen keeps the open cavity from becoming an insect route.

    The screen band is the same corrugated vent strip the resolver derives as geometry and
    the take-off bills by the lineal foot, so its height comes from
    ``BUG_SCREEN_HEIGHT_IN`` rather than from a drawing-only constant: the section shows the
    product that is actually on the order. It spans the furring cavity — the strip is cut to
    the cavity depth — and carries the material tag so the writers colour it as the
    polypropylene section it is instead of leaving it an unfilled outline.
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
        (out_sign * (clad_out - fur_in), 0.0),
        (out_sign * cfg.z_flashing_lip_in, 0.0),
        (0.0, -cfg.z_flashing_face_in),
        (out_sign * cfg.z_flashing_kick_in, -cfg.z_flashing_kick_drop_in),
    ])
    nodes = flashing_nodes(path, tag="z-flashing")
    fur_out = face_of(furring, is_outboard_high, outer=True)
    nodes += rect_region(fur_in, junction_z + cfg.screen_rise_in, fur_out,
                         junction_z + cfg.screen_rise_in + BUG_SCREEN_HEIGHT_IN,
                         "bug-screen", BUG_SCREEN_MATERIAL, "rigid", lineweight=0.3)
    return nodes


def sill_gasket_in(model, wall) -> float:
    """The drawn sill-gasket thickness (inches) for this wall.

    Prefers the authored ``FramingSpec.sill_gasket`` on the wall assembly's structure
    layer — the model field that owns the fact — and falls back to the pinned reference
    1/4" when no layer carries one.
    """
    assembly = model.plan.library.resolve_assembly(wall.assembly)
    if assembly is not None:
        for layer in assembly.layers:
            spec = getattr(layer, "framing", None)
            if spec is not None and getattr(spec, "sill_gasket", None) is not None:
                return spec.sill_gasket.meters * M_TO_IN
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
    face = inboard_face_m * M_TO_IN
    slab_top, slab_bottom = slab.z1_m * M_TO_IN, slab.z0_m * M_TO_IN
    spec = thermal_break_spec(model, slab)
    thickness_in = (spec.thickness.meters * M_TO_IN if spec is not None
                    else SLAB_EDGE.thermal_break_in)
    if spec is not None and spec.depth is not None:
        slab_bottom = max(slab_bottom, slab_top - spec.depth.meters * M_TO_IN)
    inner_edge = face + in_sign * thickness_in
    nodes = rect_region(face, slab_bottom, inner_edge, slab_top,
                        "thermal-break", "xps", "rigid", lineweight=0.35)
    nodes += rect_region(face, slab_top, inner_edge, slab_top + SLAB_EDGE.sealant_cap_in,
                         "thermal-break-sealant", "sealant", "metal", lineweight=0.3)
    return nodes


def foam_protection_board(model, wall, crop, direction, station) -> list[IRNode]:
    """Protection board over foundation insulation wherever it surfaces above grade.

    Rigid foam left exposed above grade fails: UV degrades it and the first wheelbarrow
    damages it, so both the basement notes and the garage reference call for a coating or
    trim over the exposed height. Derived — the band runs from the site grade to the top of
    the foundation wall, on whichever side the outboard insulation actually is, and draws
    nothing at all when no foam surfaces in frame.
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
    grade_z = site.grade.meters
    wall_top = (wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m)
    exposed_top = min(wall_top, max(cz0, cz1))
    exposed_bottom = max(grade_z, min(cz0, cz1))
    height_in = (exposed_top - exposed_bottom) * M_TO_IN
    if height_in < FOUNDATION_FACE.min_exposed_height_in:
        return []
    out_sign = 1.0 if is_outboard_high else -1.0
    foam_out = face_of(foam, is_outboard_high, outer=True)
    return rect_region(foam_out, exposed_bottom * M_TO_IN,
                       foam_out + out_sign * FOUNDATION_FACE.protection_board_in,
                       exposed_top * M_TO_IN,
                       "foam-protection-board", "metal-dark", "SOLID", lineweight=0.4)
