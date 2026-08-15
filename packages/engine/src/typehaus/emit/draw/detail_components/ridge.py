"""LVL-ridge hanger vocabulary (``lvl-ridge-hanger``).

The derived ridge detail cuts perpendicular to the ridge beam, so the cut shows the beam's
cross-section with the rafter planes falling away each side. The one thing the model cannot
show there is the *connection*: the rafters hang off the beam's faces on face-mount
adjustable-slope hangers (``connection="ridge:adjustable-slope-hanger"`` on the members),
which are stamped steel far too thin to survive the cut. This module draws that hanger —
a side plate on each beam face with a seat leg under the carried rafter — at schematic
sheet-metal thickness so the load path reads.

Self-gates on the roof actually carrying a ridge beam inside the crop; a hangerless ridge
board or an out-of-frame beam draws nothing. Dimensions from
:data:`~typehaus.emit.draw.detail_components.config.RIDGE_HANGER`.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import RIDGE_HANGER
from typehaus.emit.draw.detail_components.geometry import flashing_nodes, path_from_steps
from typehaus.emit.draw.scene import IRNode
from typehaus.quantities import M_PER_IN


def ridge_beam_member(roof):
    """The roof's resolved ridge-beam member, or None (a ridge board takes no hangers)."""
    if roof is None:
        return None
    return next((m for m in roof.members if m.category == "ridge_beam"), None)


def beam_width_in(profile: str) -> float:
    """Drawn beam width from a member profile ("3-1.75x11.875 LVL" → 5.25).

    A multi-ply LVL spells itself ``<plies>-<ply width>x<depth>``; a sawn member is plain
    ``<width>x<depth>``. Falls back to a 2x nominal width when the profile is opaque.
    """
    head = profile.split()[0] if profile else ""
    width = head.split("x", 1)[0] if "x" in head else ""
    try:
        if "-" in width:
            plies, ply = width.split("-", 1)
            return float(plies) * float(ply)
        return float(width)
    except ValueError:
        return 1.5


def lvl_ridge_hanger(model, roof, crop, direction, station) -> list[IRNode]:
    """Face-mount hanger each side of the ridge beam: side plate + seat under the rafter."""
    member = ridge_beam_member(roof)
    if member is None or crop is None:
        return []
    (_cu0, cz0), (_cu1, cz1) = crop
    top = member.z1_m / M_PER_IN
    bottom = member.z0_m / M_PER_IN
    # The beam band has to genuinely overlap the crop — a hanger floating below an
    # out-of-frame beam would be a drawing that lies.
    if top < min(cz0, cz1) / M_PER_IN or bottom > max(cz0, cz1) / M_PER_IN:
        return []
    center_u = (member.p0[0] if direction == "x" else member.p0[1]) / M_PER_IN
    half_width = beam_width_in(member.profile) / 2.0
    cfg = RIDGE_HANGER
    plate_drop = min(cfg.plate_drop_in, max(top - bottom - cfg.top_offset_in, 1.0))

    nodes: list[IRNode] = []
    for out_sign in (-1.0, 1.0):
        face_u = center_u + out_sign * half_width
        path = path_from_steps((face_u, top - cfg.top_offset_in), [
            (0.0, -plate_drop),
            (out_sign * cfg.seat_in, 0.0),
        ])
        nodes += flashing_nodes(path, tag="ridge-hanger")
    return nodes


def ridge_overlay_for_slice(model, view) -> list[IRNode]:
    """Ridge-hanger vocabulary for an authored ``Slice`` (documentation-only path).

    The authored ridge section (``SL-D-RIDGE``) bypasses the derived detail machinery;
    self-gated on a ridge beam being inside the crop and the cut actually crossing it,
    so any other authored detail gets nothing.
    """
    if view.crop is None or view.cut_origin is None:
        return []
    direction = view.cut_direction or "x"
    station = view.cut_origin.xy_m[1] if direction == "x" else view.cut_origin.xy_m[0]
    (cu0, _cz0), (cu1, _cz1) = view.crop[0].xy_m, view.crop[1].xy_m
    crop = (view.crop[0].xy_m, view.crop[1].xy_m)
    nodes: list[IRNode] = []
    for roof in model.roofs:
        member = ridge_beam_member(roof)
        if member is None:
            continue
        # The cut must cross the beam's run, and the beam must sit inside the u-window.
        (x0, y0), (x1, y1) = member.p0, member.p1
        along = (y0, y1) if direction == "x" else (x0, x1)
        if not (min(along) <= station <= max(along)):
            continue
        center_u = member.p0[0] if direction == "x" else member.p0[1]
        if not (min(cu0, cu1) <= center_u <= max(cu0, cu1)):
            continue
        nodes += lvl_ridge_hanger(model, roof, crop, direction, station)
    return nodes
