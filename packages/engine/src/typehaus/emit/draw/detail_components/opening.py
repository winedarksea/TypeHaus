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

The head flashing and sill pan take their dimensions from
:data:`~typehaus.resolve.flashing_config.FLASHING`, exactly as the 3D opening flashing does;
the rest come from :data:`~typehaus.emit.draw.detail_components.config.OPENING_DETAIL`.
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
from typehaus.emit.draw.lineweights import PROFILE
from typehaus.emit.draw.scene import IRNode
from typehaus.quantities import M_PER_IN
from typehaus.resolve.flashing_config import FLASHING
from typehaus.resolve.framing.truss_common import BUCK_THICKNESS_IN
from typehaus.resolve.geometry_openings import (
    _WINDOW_TRIM_FACE_WIDTH_M,
    _WINDOW_TRIM_PROUD_DEPTH_M,
)
from typehaus.resolve.opening_flashing import is_overhead


def _in(meters: float) -> float:
    return meters / M_PER_IN


def _head_path(back_u, seat_z, run_u, rise_in):
    """The head flashing: up the water plane, sloped out over the seat, down to a drip."""
    fall = abs(run_u) * FLASHING.drainage_slope
    return path_from_steps((back_u, seat_z + fall + rise_in), [
        (0.0, -rise_in), (run_u, -fall), (0.0, -_in(FLASHING.head_drop_m))])


def _pan_path(back_u, seat_z, outlet_u, out_sign):
    """The sill pan: back dam on its strip, sloped across the seat, turned down at the outlet."""
    dam_u = back_u + out_sign * _in(FLASHING.back_dam_strip_m)
    fall = abs(outlet_u - dam_u) * FLASHING.drainage_slope
    back_dam = _in(FLASHING.back_dam_m)
    return path_from_steps((dam_u, seat_z + back_dam), [
        (0.0, fall - back_dam), (outlet_u - dam_u, -fall), (0.0, -_in(FLASHING.pan_drop_m))])


def _drip_throw_in(opening) -> float:
    """How far the head drip stands past the cladding: clear of a window's casing face."""
    proud = _WINDOW_TRIM_PROUD_DEPTH_M if opening.kind == "window" else 0.0
    return _in(proud + FLASHING.head_projection_m)


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
    throw = out_sign * _drip_throw_in(opening)

    nodes: list[IRNode] = []
    if _in_crop_z(head_z, crop):
        casing = _in(_WINDOW_TRIM_FACE_WIDTH_M) if opening.kind == "window" else 0.0
        nodes += flashing_nodes(_head_path(sheath_out, head_z + casing,
                                           (clad_out - sheath_out) + throw,
                                           _in(FLASHING.head_rise_m)),
                                tag="opening-head-flashing")
        # Sealant at the cladding-to-frame joint, tucked under the flashing's drip.
        nodes += rect_region(clad_out - out_sign * cfg.sealant_bead_in,
                             head_z - cfg.sealant_bead_in, clad_out, head_z,
                             "opening-sealant", "sealant", "metal", lineweight=PROFILE)
    if _in_crop_z(sill_z, crop) and not is_overhead(model, opening):
        stud = outermost_with_function(intervals, "structure")
        back = (face_of(stud, is_outboard_high, outer=False) if stud is not None
                else sheath_out - out_sign * 4.0)
        nodes += flashing_nodes(_pan_path(back, sill_z, clad_out + throw, out_sign),
                                tag="opening-sill-pan")
    return nodes


def outie_window_truss(model, wall, opening, crop, direction, station) -> list[IRNode]:
    """Head flashing + sill pan at an OUTIE window or door in a truss wall.

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
    * the **sill pan** lies ON the sill buck (which lines the RO), its back dam turned up a
      rigid strip at the sheathing face, falls 1/4"/ft out to the truss plane, and turns
      down over the buck's front edge onto the sill course face and the cladding's back,
      behind the sill trim. The buck spans the 1/2" vent gap, so that is the outlet, not
      the gap. It discharges BEHIND the cladding: an outie pan that ran out to a visible
      drip would put a metal lip under every window on the facade. A DOOR's pan does run
      past the cladding, because a threshold has no sill trim to hide behind.

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
        casing = _in(_WINDOW_TRIM_FACE_WIDTH_M) if opening.kind == "window" else 0.0
        seat = head_z + max(blocking_in, casing)
        nodes += flashing_nodes(_head_path(foam_face, seat, (clad_out - foam_face)
                                           + out_sign * _drip_throw_in(opening),
                                           _in(FLASHING.outie_head_rise_m)),
                                tag="opening-head-flashing")
        # Sealant at the cladding-to-frame joint, tucked under the flashing's drip. The
        # joint is at the mount plane now, which is the cladding's own inner face.
        nodes += rect_region(clad_in - out_sign * cfg.sealant_bead_in,
                             head_z - cfg.sealant_bead_in, clad_in, head_z,
                             "opening-sealant", "sealant", "metal", lineweight=PROFILE)
    if _in_crop_z(sill_z, crop):
        # The pan lies on the buck. A window's discharges at the mount plane, behind the
        # cladding; a door's runs past the cladding to a drip.
        outlet = (clad_out + out_sign * _drip_throw_in(opening) if opening.is_door
                  else truss_plane)
        nodes += flashing_nodes(_pan_path(sheath_out, sill_z + BUCK_THICKNESS_IN, outlet,
                                          out_sign), tag="opening-sill-pan")
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
                             "opening-buck", "spf", "lumber", lineweight=PROFILE)
        for face_u, in_sign in ((lo, 1.0), (hi, -1.0)):
            nodes += rect_region(face_u, head_z - cfg.buck_in,
                                 face_u + in_sign * cfg.sealant_bead_in, head_z,
                                 "opening-sealant", "sealant", "metal", lineweight=PROFILE)
    if opening.sill_m > 0.0 and _in_crop_z(sill_z, crop):
        nodes += rect_region(lo, sill_z, hi, sill_z + cfg.buck_in,
                             "opening-buck", "spf", "lumber", lineweight=PROFILE)
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
                             lineweight=PROFILE)
    if opening.sill_m > 0.0 and _in_crop_z(sill_z, crop):
        nodes += rect_region(lo, sill_z, hi, sill_z + SAUNA_MEMBRANE_IN,
                             "sauna-foil-return", "air-barrier", "membrane",
                             lineweight=PROFILE)
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
    not framing, and the room below the sill is a coved vinyl tray with a sealed
    reducer at its doorway and no floor drain.
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
                             lineweight=PROFILE)
    if _in_crop_z(sill_z, crop):
        nodes += rect_region(lo, sill_z, hi, sill_z + SAUNA_MEMBRANE_IN,
                             "humid-membrane-return", "air-barrier", "membrane",
                             lineweight=PROFILE)
        nodes += rect_region(lo, sill_z + SAUNA_MEMBRANE_IN, hi,
                             sill_z + SAUNA_MEMBRANE_IN + OPENING_DETAIL.humid_sill_pan_in,
                             "humid-sill-pan", "metal-dark", "flashing",
                             lineweight=PROFILE)
    return nodes
