"""Breezeway glazing vocabulary — the parts of the enclosure that are not model geometry.

The breezeway's structure (posts, beams, rafters, joists, decking) and its sheets and
extrusions are all real resolved elements, so the section cuts them without help. What it
cannot cut is everything that makes the enclosure *work*:

* the **weep holes** drilled through the bottom U-channel, without which the flutes hold the
  water the channel exists to release;
* the **glazing bar** and **F-channel** sections, drawn as profiles rather than as the flat
  boxes their solids resolve to;
* the **gasketed stainless fastener**, which seals through an oversize hole rather than
  clamping — the single most misbuilt part of a polycarbonate roof;
* the **breather tape** between each joist top and the decking above it.

All of it is documentation, none of it mutates construction geometry, and the whole module
self-gates on a breezeway glazing panel actually being in the cut — an authored detail
anywhere else in the house gets nothing from here.

Every dimension comes from :data:`~...config.BREEZEWAY_GLAZING`. Nodes are ``Polyline`` and
``Hatch`` only (``tests/test_detail_vocabulary.py`` enforces it), tagged
``detail-component:<name>``.

Section coordinates: ``u`` is the in-section axis, ``z`` is world z, both in model inches.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import (
    BREEZEWAY_GLAZING as CFG,
)
from typehaus.emit.draw.detail_components.config import LAYER
from typehaus.emit.draw.detail_components.geometry import closed_region, rect_region
from typehaus.emit.draw.scene import IRNode, Polyline
from typehaus.quantities import M_PER_IN

_ALUMINUM = "aluminum-extrusion"


def _in_frame(u: float, z: float, crop) -> bool:
    (cu0, cz0), (cu1, cz1) = crop
    return cu0 - 1e-9 <= u <= cu1 + 1e-9 and cz0 - 1e-9 <= z <= cz1 + 1e-9


def _cut_solids(model, category: str, direction: str, station: float, crop):
    """Resolved solids of ``category`` the cut plane actually crosses, inside the crop.

    ``crop`` is in metres here (the Slice's own units); the returned spans are in inches,
    which is what every component below draws in.
    """
    (cu0, cz0), (cu1, cz1) = crop
    out = []
    for solid in model.solids:
        if solid.category != category:
            continue
        ring = list(solid.outline)
        perp = [p[1] if direction == "x" else p[0] for p in ring]
        if not (min(perp) - 1e-9 <= station <= max(perp) + 1e-9):
            continue
        along = [p[0] if direction == "x" else p[1] for p in ring]
        u0, u1 = max(min(along), cu0), min(max(along), cu1)
        z0, z1 = max(solid.z0_m, cz0), min(solid.z1_m, cz1)
        if u1 - u0 <= 1e-9 or z1 - z0 <= 1e-9:
            continue
        out.append((solid, u0 / M_PER_IN, u1 / M_PER_IN, z0 / M_PER_IN, z1 / M_PER_IN))
    return out


def weeping_u_channel(u_center: float, z_top: float, crop_in) -> list[IRNode]:
    """The eave U-channel drawn as a section, with its weep hole shown.

    The hole is the entire point of the part: a multiwall sheet's flutes drain to their low
    end, and an unvented channel there turns the flute into a standing-water column that
    grows algae behind the glazing.
    """
    if not _in_frame(u_center, z_top, crop_in):
        return []
    t = CFG.extrusion_draw_in
    lip = 1.5
    nodes = rect_region(u_center - t, z_top - lip, u_center + t, z_top,
                        "breezeway-u-channel", _ALUMINUM, None)
    # The weep hole: a short break drawn in the channel's bottom leg.
    half = CFG.weep_diameter_in / 2.0
    nodes.append(Polyline(
        points=((u_center - half, z_top - lip), (u_center + half, z_top - lip)),
        layer=LAYER, closed=False, lineweight=0.5,
        tag="detail-component:breezeway-weep-hole"))
    return nodes


def shared_h_channel(u_center: float, z_joint: float, roof_sign: float,
                     crop_in) -> list[IRNode]:
    """The H channel where a standing sheet's head meets the roof sheet's edge.

    It matters that it draws as a *joint*: ``_resolve_edge_run`` renders every glazing-trim
    profile as the same solid box, so in 3D an H is indistinguishable from a U, and the
    section here is the only place a reader can see that one extrusion now receives two
    sheets — the wall sheet rising into the lower slot, the roof sheet entering the upper
    one from the side.

    ``roof_sign`` is which way the roof sheet runs from the channel (+1 at the west edge,
    -1 at the east), so the corner turns the right way at both ends of the cut.
    """
    if not _in_frame(u_center, z_joint, crop_in):
        return []
    t = CFG.extrusion_draw_in
    half, lap, web = CFG.h_slot_in / 2.0, CFG.h_lap_in, CFG.h_web_in
    outer, inner = u_center - roof_sign * (half + t), u_center + roof_sign * half
    web_top = z_joint + web / 2.0
    web_bottom = z_joint - web / 2.0
    nodes: list[IRNode] = []
    # Outboard leg: the long one. It grips the wall sheet below and turns the corner over
    # the roof sheet's outer edge, which is what makes the sheet's end weathertight now that
    # nothing oversails it.
    nodes += rect_region(min(outer, outer + roof_sign * t), web_bottom - lap,
                         max(outer, outer + roof_sign * t), web_top + half + t,
                         "breezeway-h-channel-outer-leg", _ALUMINUM, None)
    # Inboard leg: shorter, stopping under the web — the roof sheet passes over it.
    nodes += rect_region(min(inner, inner + roof_sign * t), web_bottom - lap,
                         max(inner, inner + roof_sign * t), web_bottom,
                         "breezeway-h-channel-inner-leg", _ALUMINUM, None)
    # The web between the two slots.
    nodes += rect_region(min(outer, inner), web_bottom, max(outer, inner), web_top,
                         "breezeway-h-channel-web", _ALUMINUM, None)
    # The upper flange, lapping in over the roof sheet.
    flange_far = u_center + roof_sign * lap
    nodes += rect_region(min(u_center, flange_far), web_top + half,
                         max(u_center, flange_far), web_top + half + t,
                         "breezeway-h-channel-flange", _ALUMINUM, None)
    return nodes


def crown_glazing_bar(u_center: float, z_top: float, crop_in) -> list[IRNode]:
    """The concealed-fastener aluminium bar capping both sheets' high flute ends.

    Drawn as the two legs a glazing bar actually has — a base that the sheets land on and a
    cap that clamps them — because the resolved solid is a single box and a reader has to be
    able to tell a capped bar from a strip of flashing laid over the joint.
    """
    if not _in_frame(u_center, z_top, crop_in):
        return []
    t = CFG.extrusion_draw_in
    half = 1.25
    nodes = rect_region(u_center - half, z_top - t, u_center + half, z_top,
                        "breezeway-glazing-bar-cap", _ALUMINUM, None)
    nodes += rect_region(u_center - half, z_top - 3 * t, u_center + half, z_top - 2 * t,
                         "breezeway-glazing-bar-base", _ALUMINUM, None)
    return nodes


def gasketed_fastener(u: float, z_top: float, crop_in) -> list[IRNode]:
    """A #12 stainless screw with its bonded EPDM washer, through an oversize hole.

    Drawn oversize on purpose: the sheet has to be free to move under the washer, and a
    fastener detailed as a clamp is how a polycarbonate roof gets cracked at every screw.
    """
    if not _in_frame(u, z_top, crop_in):
        return []
    nodes = rect_region(u - CFG.fastener_head_in / 2.0, z_top,
                        u + CFG.fastener_head_in / 2.0, z_top + CFG.fastener_head_in,
                        "breezeway-panel-fastener-head", "metal", None)
    nodes += rect_region(u - CFG.fastener_washer_in / 2.0, z_top - 0.15,
                         u + CFG.fastener_washer_in / 2.0, z_top,
                         "breezeway-panel-fastener-washer", "rubber", None)
    nodes.append(Polyline(points=((u, z_top), (u, z_top - CFG.fastener_shank_in)),
                          layer=LAYER, closed=False, lineweight=0.3,
                          tag="detail-component:breezeway-panel-fastener-shank"))
    return nodes


def breather_tape(joists, crop_in) -> list[IRNode]:
    """Vented tape over every joist top, between the wood and the decking above it.

    A composite board laid straight onto a joist traps water on the joist's top face, which
    is the first place a KDAT deck frame fails. The tape is 1/16" of material — invisible in
    the model, and the reason the frame lasts.
    """
    nodes: list[IRNode] = []
    for index, (u0, u1, z_top) in enumerate(joists):
        if not _in_frame((u0 + u1) / 2.0, z_top, crop_in):
            continue
        nodes += rect_region(u0, z_top, u1, z_top + 0.0625,
                             f"breezeway-breather-tape-{index}", "membrane", None)
    return nodes


def _wedge_rise_in(model, direction: str, station: float) -> float:
    """The crown depth of the tapered wedges the cut plane crosses, in inches (0 if none)."""
    rise = 0.0
    for brace in getattr(model, "braces", ()):
        if getattr(brace, "kind", "brace") != "wedge":
            continue
        for member in brace.members:
            perp = ([member.p0[1], member.p1[1]] if direction == "x"
                    else [member.p0[0], member.p1[0]])
            if min(perp) - 0.05 <= station <= max(perp) + 0.05:
                rise = max(rise, (member.z1_m - member.z0_m) / M_PER_IN)
    return rise


def breezeway_components(model, direction, station, crop) -> list[IRNode]:
    """The whole vocabulary, derived from what the cut actually crosses."""
    roof_panels = [item for item in _cut_solids(model, "glazing", direction, station, crop)
                   if (item[0].assembly or "").endswith("ROOF_GLAZING")]
    if not roof_panels:
        return []
    crop_in = ((crop[0][0] / M_PER_IN, crop[0][1] / M_PER_IN),
               (crop[1][0] / M_PER_IN, crop[1][1] / M_PER_IN))

    nodes: list[IRNode] = []
    # No drainage wedge here any more. It used to be synthesised from BREEZEWAY_GLAZING
    # because a ``Beam`` is a prism and nothing in the model could hold a taper. A ``Wedge``
    # can, so the six shims are resolved members now and ``_emit_member_cuts`` cuts them like
    # every other stick — drawing them here as well would draw each one twice.
    panel_underside = min(z0 for _s, _u0, _u1, z0, _z1 in roof_panels)

    spans = sorted((u0, u1) for _s, u0, u1, _z0, _z1 in roof_panels)
    panel_top = max(z1 for _s, _u0, _u1, _z0, z1 in roof_panels)
    if len(spans) >= 2:
        crown = (spans[0][1] + spans[1][0]) / 2.0
        # Two flat sheets meeting at a bar are drawn at their own eave height, so the bar
        # rides the crown a wedge above them. That rise is the model's now, read off the
        # wedges this cut actually crosses rather than repeated as a drawing constant.
        nodes += crown_glazing_bar(crown, panel_top + _wedge_rise_in(model, direction, station),
                                   crop_in)
    # The two roof edges land on the standing sheets' own line, in a shared H channel.
    for u_edge, roof_sign in ((spans[0][0], 1.0), (spans[-1][1], -1.0)):
        nodes += shared_h_channel(u_edge, panel_underside, roof_sign, crop_in)
        nodes += gasketed_fastener(u_edge + roof_sign * 2.0, panel_top, crop_in)

    # The sill U-channel is the assembly's only drainage path, so the detail draws it
    # wherever the cut crosses one. Read off the resolved trim solid rather than offset
    # from the sheet: the sill sits at the deck surface, which the sheet passes on its way
    # down to the floor-beam soffit, so there is no fixed distance between the two to
    # hard-code.
    for solid, u0, u1, _z0, z1 in _cut_solids(model, "glazing_trim", direction, station, crop):
        if "-SILL-" not in solid.tag:
            continue
        nodes += weeping_u_channel((u0 + u1) / 2.0, z1, crop_in)

    joists = []
    for floor in model.floors:
        if not floor.tag.startswith("FS-BW-"):
            continue
        for member in floor.members:
            if member.category != "joist":
                continue
            perp = [member.p0[1], member.p1[1]] if direction == "x" else [member.p0[0],
                                                                          member.p1[0]]
            if not (min(perp) - 0.05 <= station <= max(perp) + 0.05):
                continue
            along = ([member.p0[0], member.p1[0]] if direction == "x"
                     else [member.p0[1], member.p1[1]])
            joists.append((min(along) / M_PER_IN, max(along) / M_PER_IN,
                           member.z1_m / M_PER_IN))
    nodes += breather_tape(joists, crop_in)
    return nodes


def breezeway_overlay_for_slice(model, view) -> list[IRNode]:
    """Breezeway vocabulary for an authored ``Slice`` (documentation-only path).

    Self-gated on a breezeway roof panel being in the cut, exactly like
    ``sauna_overlay_for_slice``: a non-breezeway authored detail is byte-identical to the
    plain ``build_section`` output.
    """
    if view.crop is None or view.cut_origin is None:
        return []
    direction = view.cut_direction or "x"
    station = view.cut_origin.xy_m[1] if direction == "x" else view.cut_origin.xy_m[0]
    crop = (view.crop[0].xy_m, view.crop[1].xy_m)
    return breezeway_components(model, direction, station, crop)
