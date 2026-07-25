"""Breezeway glazing vocabulary — the parts of the enclosure that are not model geometry.

The breezeway's structure (posts, beams, rafters, joists, decking) and its sheets and
extrusions are all real resolved elements, so the section cuts them without help. What it
cannot cut is everything that makes the enclosure *work*:

* the tapered **drainage wedge** on every rafter — a ``Beam`` is a prism, so the crown that
  sheds water off this roof cannot be a member;
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
from typehaus.emit.draw.detail_components.config import LAYER, M_TO_IN
from typehaus.emit.draw.detail_components.geometry import closed_region, rect_region
from typehaus.emit.draw.scene import IRNode, Polyline

_GLAZING = "polycarbonate-multiwall"
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
        out.append((solid, u0 * M_TO_IN, u1 * M_TO_IN, z0 * M_TO_IN, z1 * M_TO_IN))
    return out


def drainage_wedges(panels, rafter_top_in: float) -> list[IRNode]:
    """The tapered sleepers that crown the roof from each eave to the ridge bar.

    One wedge per glazing panel: zero at the panel's eave edge, ``wedge_rise_in`` at the
    crown it shares with its neighbour. Which end is which is read off the panels themselves
    — the crown is the edge the two panels have in common — so the wedge follows a geometry
    edit instead of freezing a hand-picked apex.
    """
    if len(panels) < 2:
        return []
    spans = sorted((u0, u1) for _solid, u0, u1, _z0, _z1 in panels)
    crown = (spans[0][1] + spans[1][0]) / 2.0
    nodes: list[IRNode] = []
    for index, (u0, u1) in enumerate(spans):
        eave = u0 if abs(u0 - crown) > abs(u1 - crown) else u1
        points = ((eave, rafter_top_in),
                  (crown, rafter_top_in),
                  (crown, rafter_top_in + CFG.wedge_rise_in))
        nodes += closed_region(points, f"breezeway-drainage-wedge-{index}", "spf", "lumber")
    return nodes


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


def breezeway_components(model, direction, station, crop) -> list[IRNode]:
    """The whole vocabulary, derived from what the cut actually crosses."""
    roof_panels = [item for item in _cut_solids(model, "glazing", direction, station, crop)
                   if (item[0].assembly or "").endswith("ROOF_GLAZING")]
    if not roof_panels:
        return []
    crop_in = ((crop[0][0] * M_TO_IN, crop[0][1] * M_TO_IN),
               (crop[1][0] * M_TO_IN, crop[1][1] * M_TO_IN))

    nodes: list[IRNode] = []
    # The rafters the wedges sit on: the beam solids directly under the glazing.
    panel_underside = min(z0 for _s, _u0, _u1, z0, _z1 in roof_panels)
    beams = _cut_solids(model, "beam", direction, station, crop)
    rafter_tops = [z1 for _s, _u0, _u1, _z0, z1 in beams if z1 <= panel_underside + 1e-6]
    if rafter_tops:
        nodes += drainage_wedges(roof_panels, max(rafter_tops))

    spans = sorted((u0, u1) for _s, u0, u1, _z0, _z1 in roof_panels)
    panel_top = max(z1 for _s, _u0, _u1, _z0, z1 in roof_panels)
    if len(spans) >= 2:
        crown = (spans[0][1] + spans[1][0]) / 2.0
        nodes += crown_glazing_bar(crown, panel_top + CFG.wedge_rise_in, crop_in)
    for u_edge in (spans[0][0], spans[-1][1]):
        nodes += weeping_u_channel(u_edge, panel_top, crop_in)
        nodes += gasketed_fastener(u_edge + 2.0 if u_edge == spans[0][0] else u_edge - 2.0,
                                   panel_top, crop_in)

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
            joists.append((min(along) * M_TO_IN, max(along) * M_TO_IN,
                           member.z1_m * M_TO_IN))
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
