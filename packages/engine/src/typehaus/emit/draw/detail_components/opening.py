"""Opening-perimeter detail vocabulary — head flashing, sill pan, concrete bucks, liner returns.

The derived opening detail cuts vertically through the opening's center, so the cut plane
contains the **head and the sill** (the jambs live in the plan cut, not this one). What gets
applied there depends on the wall the opening pierces:

* a framed **weather wall** takes a head flashing lapped behind the WRB and a sill pan with a
  back dam — the two pieces of sheet metal that decide whether the rough opening rots;
* a **concrete** opening takes a treated buck (the lumber a frame can actually fasten to)
  sealed to the concrete at both faces;
* the **sauna liner** opening returns the foil vapour-control face into the head reveal and
  seals it, because a butt joint there is a hole in the hot side's vapour control;
* a **humid-room liner** opening (the plant room) does the same for its Class I membrane and
  adds the drained sill pan that a room at 70% RH needs under every unit.

Everything self-gates on its subject genuinely being in the cut: the head vocabulary only
draws when the head elevation is inside the crop, a windowless-weather-wall recipe on an
interior partition draws nothing, and no function here mutates construction geometry.

Dimensions come from :data:`~typehaus.emit.draw.detail_components.config.OPENING_DETAIL`.
Section coordinates: ``u`` is the in-section axis, ``z`` is world z, both in model inches.

``out_sign`` multiplies a length that does not already carry a direction. The difference
between two ``face_of`` readings DOES carry one — it is signed by which side is outboard —
so multiplying that by ``out_sign`` again flips it on a wall whose outboard face is the LOW
side and runs every flashing inboard, through the wall it is supposed to shed water off.
Only the loose dimensions (a lip, a bead, a drop) take the sign.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import (
    OPENING_DETAIL,
    SAUNA_MEMBRANE_IN,
)
from typehaus.emit.draw.detail_components.geometry import (
    face_of,
    flashing_nodes,
    is_weather_exposed,
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    path_from_steps,
    rect_region,
    vent_face,
)
from typehaus.emit.draw.scene import IRNode
from typehaus.quantities import M_PER_IN


def opening_z_in(wall, opening) -> tuple[float, float]:
    """``(sill, head)`` elevations in section inches. ``sill_m`` is storey-relative, so the
    wall's own base carries it to world z; ``height_m`` already includes any arch rise."""
    sill = (wall.base_ref_z_m + opening.sill_m) / M_PER_IN
    return sill, sill + opening.height_m / M_PER_IN


def _in_crop_z(z_in: float, crop) -> bool:
    (_cu0, cz0), (_cu1, cz1) = crop
    return min(cz0, cz1) / M_PER_IN <= z_in <= max(cz0, cz1) / M_PER_IN


def window_head_jamb_sill(model, wall, opening, crop, direction, station) -> list[IRNode]:
    """Head flashing + sill pan at a framed weather-wall opening.

    The head flashing starts behind the water-control plane (the sheathing/WRB face), runs
    out past the cladding and drips, so water in the drainage plane is delivered *outside*
    the opening. The sill pan spans from the framing's interior face, turns up a back dam,
    and drips clear of the cladding — the pan is what keeps an eventual frame leak from
    becoming a rough-sill leak. Gated on the wall actually presenting a weather face: an
    interior opening gets neither, because there is no water to manage.
    """
    if not is_weather_exposed(wall):
        return []
    is_outboard_high = outboard_is_high(wall, direction, station)
    if is_outboard_high is None:
        return []
    intervals = layer_intervals(wall, direction, station)
    sheath = outermost_with_function(intervals, "sheathing")
    clad = outermost_with_function(intervals, "cladding")
    if sheath is None or clad is None:
        return []
    out_sign = 1.0 if is_outboard_high else -1.0
    sheath_out = face_of(sheath, is_outboard_high, outer=True)
    clad_out = face_of(clad, is_outboard_high, outer=True)
    sill_z, head_z = opening_z_in(wall, opening)
    cfg = OPENING_DETAIL

    nodes: list[IRNode] = []
    if _in_crop_z(head_z, crop):
        path = path_from_steps((sheath_out, head_z + cfg.head_flashing_rise_in), [
            (0.0, -cfg.head_flashing_rise_in),
            ((clad_out - sheath_out) + out_sign * cfg.head_flashing_lip_in, 0.0),
            (0.0, -cfg.head_flashing_drop_in),
        ])
        nodes += flashing_nodes(path, tag="opening-head-flashing")
        # Sealant at the cladding-to-frame joint, tucked under the flashing's drip.
        nodes += rect_region(clad_out - out_sign * cfg.sealant_bead_in,
                             head_z - cfg.sealant_bead_in, clad_out, head_z,
                             "opening-sealant", "sealant", "metal", lineweight=0.3)
    if _in_crop_z(sill_z, crop):
        stud = outermost_with_function(intervals, "structure")
        back = (face_of(stud, is_outboard_high, outer=False) if stud is not None
                else sheath_out - out_sign * 4.0)
        pan = path_from_steps((back, sill_z + cfg.sill_pan_back_dam_in), [
            (0.0, -cfg.sill_pan_back_dam_in),
            ((clad_out - back) + out_sign * cfg.sill_pan_lip_in, 0.0),
            (0.0, -cfg.sill_pan_drop_in),
        ])
        nodes += flashing_nodes(pan, tag="opening-sill-pan")
    return nodes


def outie_window_truss(model, wall, opening, crop, direction, station) -> list[IRNode]:
    """Head flashing + sill pan at an OUTIE window in a truss wall.

    The innie recipe above measures both pieces from ``sheath_out``, because that is where an
    innie unit sits: in the stud plane, behind the insulation, with the flashing lapped onto
    the WRB. A truss wall has neither of those things. The unit sits five or six inches
    further out, in the MOUNT plane, its flanges bearing on the standoff framing and on the
    head/sill blocking; the water plane is the spray foam, not a sheet; and between the
    mount plane and the cladding there is a drained and back-vented gap for the pan to
    discharge into.

    So both pieces move out with the window:

    * the **head flashing** starts on the FOAM face above the head blocking — the foam is the
      water plane, so lapping onto it is what makes the head continuous — turns out over the
      head blocking, and laps past the cladding to a drip. That face is the one the vented
      gap EXPOSES (``vent_face``), 1" behind the truss plane, not the band's own back 3-1/2"
      behind it: the foam is sprayed *after* the truss and *before* the flashing, so the
      band's back is 2-1/2" inside a cured solid at the moment this piece goes on and an
      upstand there would have to be cut into it;
    * the **sill pan** lies on the sill buck with its back dam turned up against the buck's
      inboard leg, runs out to the truss plane, and turns down into the rainscreen gap. It
      discharges BEHIND the cladding, not past it: an outie pan that ran out to a visible
      drip would put a metal lip under every window on the facade.

    The buck, the head/sill blocking and the standoff framing itself are not drawn here.
    They are real resolved members now (``resolve/framing/truss_wall.py``), so the cut
    already carries them, and convention linework over a solid is a second, disagreeing
    drawing of the same wood.

    **One recipe, two truss walls.** Everything above is read off the resolved stack rather
    than named — the mount plane is the outermost furring band's outer face (5" on a
    Swinburne wall, 6" on a girt wall), and the foam face is whatever the vent gap exposes
    (1" behind the plane, or 2") — so the catlin truss needed exactly one number telling it
    apart: how tall the head/sill blocking is, which is 1-1/2" for a 2x4 on edge and 3-1/2"
    for the same board laid flat. ``truss_kind`` picks it.
    """
    from typehaus.resolve.framing.truss_wall import truss_kind

    if not is_weather_exposed(wall):
        return []
    is_outboard_high = outboard_is_high(wall, direction, station)
    if is_outboard_high is None:
        return []
    intervals = layer_intervals(wall, direction, station)
    sheath = outermost_with_function(intervals, "sheathing")
    band = outermost_with_function(intervals, "furring")
    clad = outermost_with_function(intervals, "cladding")
    if sheath is None or band is None or clad is None:
        return []
    out_sign = 1.0 if is_outboard_high else -1.0
    sheath_out = face_of(sheath, is_outboard_high, outer=True)
    foam_face = vent_face(wall, band, is_outboard_high)        # what the vent gap exposes
    truss_plane = face_of(band, is_outboard_high, outer=True)  # the mount plane
    clad_out = face_of(clad, is_outboard_high, outer=True)
    clad_in = face_of(clad, is_outboard_high, outer=False)
    sill_z, head_z = opening_z_in(wall, opening)
    cfg = OPENING_DETAIL

    nodes: list[IRNode] = []
    if _in_crop_z(head_z, crop):
        blocking_in = (cfg.girt_blocking_in
                       if truss_kind(model.plan, wall.assembly) == "girt"
                       else cfg.truss_blocking_in)
        block_top = head_z + blocking_in
        path = path_from_steps((foam_face, block_top + cfg.outie_head_rise_in), [
            (0.0, -cfg.outie_head_rise_in),
            ((clad_out - foam_face) + out_sign * cfg.head_flashing_lip_in, 0.0),
            (0.0, -cfg.head_flashing_drop_in),
        ])
        nodes += flashing_nodes(path, tag="opening-head-flashing")
        # Sealant at the cladding-to-frame joint, tucked under the flashing's drip. The
        # joint is at the mount plane now, which is the cladding's own inner face.
        nodes += rect_region(clad_in - out_sign * cfg.sealant_bead_in,
                             head_z - cfg.sealant_bead_in, clad_in, head_z,
                             "opening-sealant", "sealant", "metal", lineweight=0.3)
    if _in_crop_z(sill_z, crop):
        pan = path_from_steps((sheath_out, sill_z + cfg.sill_pan_back_dam_in), [
            (0.0, -cfg.sill_pan_back_dam_in),
            ((truss_plane - sheath_out), 0.0),
            (0.0, -cfg.outie_pan_drop_in),
        ])
        nodes += flashing_nodes(pan, tag="opening-sill-pan")
    return nodes


def concrete_opening_bucks(model, wall, opening, crop, direction, station) -> list[IRNode]:
    """Treated buck + sealant at an opening cast into concrete.

    A frame cannot fasten to bare concrete; the buck is the treated 2x lining the rough
    opening that takes the screws, sealed to the concrete at both wall faces so the joint
    is not an air path. The head always gets one; the sill only when the opening actually
    has a raised sill (a door threshold is not a buck).
    """
    intervals = layer_intervals(wall, direction, station)
    concrete = outermost_with_function(intervals, "structure")
    if concrete is None:
        return []
    lo, hi = min(concrete[0], concrete[1]), max(concrete[0], concrete[1])
    sill_z, head_z = opening_z_in(wall, opening)
    cfg = OPENING_DETAIL

    nodes: list[IRNode] = []
    if _in_crop_z(head_z, crop):
        nodes += rect_region(lo, head_z - cfg.buck_in, hi, head_z,
                             "opening-buck", "spf", "lumber", lineweight=0.35)
        for face_u, in_sign in ((lo, 1.0), (hi, -1.0)):
            nodes += rect_region(face_u, head_z - cfg.buck_in,
                                 face_u + in_sign * cfg.sealant_bead_in, head_z,
                                 "opening-sealant", "sealant", "metal", lineweight=0.3)
    if opening.sill_m > 0.0 and _in_crop_z(sill_z, crop):
        nodes += rect_region(lo, sill_z, hi, sill_z + cfg.buck_in,
                             "opening-buck", "spf", "lumber", lineweight=0.35)
    return nodes


def sauna_liner_opening_return(model, wall, opening, crop, direction,
                               station) -> list[IRNode]:
    """Foil vapour-control face returned into the opening head reveal and sealed.

    The sauna's hot side keeps its steam out of the assembly with a foil-faced polyiso
    plane; the door punches a hole in it. The liner membrane is therefore returned across
    the head reveal (and the raised sill, if the opening has one) rather than butted, so
    the vapour control is continuous around the opening.
    """
    intervals = layer_intervals(wall, direction, station)
    bands = [iv for iv in (outermost_with_function(intervals, "finish"),
                           outermost_with_function(intervals, "furring"),
                           outermost_with_function(intervals, "insulation"))
             if iv is not None]
    if not bands:
        return []
    lo = min(min(iv[0], iv[1]) for iv in bands)
    hi = max(max(iv[0], iv[1]) for iv in bands)
    sill_z, head_z = opening_z_in(wall, opening)

    nodes: list[IRNode] = []
    if _in_crop_z(head_z, crop):
        nodes += rect_region(lo, head_z - SAUNA_MEMBRANE_IN, hi, head_z,
                             "sauna-foil-return", "air-barrier", "membrane",
                             lineweight=0.3)
    if opening.sill_m > 0.0 and _in_crop_z(sill_z, crop):
        nodes += rect_region(lo, sill_z, hi, sill_z + SAUNA_MEMBRANE_IN,
                             "sauna-foil-return", "air-barrier", "membrane",
                             lineweight=0.3)
    return nodes


# The plant-room liner's three layer *names* (plan/assemblies.py::_HUMID_LINER). Named rather
# than found by function, unlike the sauna's return above: this liner's control layer is a
# MEMBRANE and its host wall carries another one outboard (the WRB), so
# ``outermost_with_function`` would pick the wrong one and draw a return spanning the whole
# wall depth.
_HUMID_LINER_LAYERS = ("pvc-panel", "liner-furring", "humid-membrane")


def humid_liner_opening_return(model, wall, opening, crop, direction,
                               station) -> list[IRNode]:
    """Class I membrane returned into the head and sill reveals, plus a drained sill pan.

    A continuously humid room's vapour barrier has no redundancy — there is no thickness of
    exterior insulation that would keep the sheathing above that room's dew point — so an
    opening is a hole in the only thing preventing rot. The membrane is therefore returned
    across the reveal and sealed to the frame, never butted at the panel edge.

    The sill gets a pan as well as a return. It drains *into the room*, which is the whole
    point of it: water that gets past a frame here has to be given somewhere to go that is
    not framing, and the room below the sill is a coved vinyl tray with a floor drain.
    """
    intervals = layer_intervals(wall, direction, station)
    bands = [intervals[name] for name in _HUMID_LINER_LAYERS if name in intervals]
    if not bands:
        return []
    lo = min(min(iv[0], iv[1]) for iv in bands)
    hi = max(max(iv[0], iv[1]) for iv in bands)
    sill_z, head_z = opening_z_in(wall, opening)

    nodes: list[IRNode] = []
    if _in_crop_z(head_z, crop):
        nodes += rect_region(lo, head_z - SAUNA_MEMBRANE_IN, hi, head_z,
                             "humid-membrane-return", "air-barrier", "membrane",
                             lineweight=0.3)
    if _in_crop_z(sill_z, crop):
        nodes += rect_region(lo, sill_z, hi, sill_z + SAUNA_MEMBRANE_IN,
                             "humid-membrane-return", "air-barrier", "membrane",
                             lineweight=0.3)
        nodes += rect_region(lo, sill_z + SAUNA_MEMBRANE_IN, hi,
                             sill_z + SAUNA_MEMBRANE_IN + OPENING_DETAIL.sill_pan_lip_in,
                             "humid-sill-pan", "metal-dark-exterior", "flashing",
                             lineweight=0.35)
    return nodes
