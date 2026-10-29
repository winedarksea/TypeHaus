"""What carries the eave gutter: eave blocking, gutter girt, standoffs, TLOK08s, hanger.

All read off resolved members (``Roof.eave_blocking`` and ``resolve/roof_eave_girt.py``),
so a detail over a roof without them draws nothing here. The blocking and girt are cut
by the section already; the standoff sits at a bay centre, usually off the cut plane, so it
and its screws draw as HIDDEN lines beyond. The hanger is not a model element (not billed)
and draws schematically off the authored catalog gutter.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import LAYER
from typehaus.emit.draw.detail_components.geometry import flashing_nodes, rect_points
from typehaus.emit.draw.lineweights import LIGHT, PROFILE
from typehaus.emit.draw.scene import IRNode, Polyline
from typehaus.emit.draw.section_clip import clip_rect, clip_segment
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section

_BLOCKING = "eave:blocking"
_GIRT = "eave:gutter-girt"
#: How far from the cladding face a member may sit and still belong to this eave (inches).
_REACH_IN = 14.0
#: The girt sits directly behind the cladding it carries (PBR is 1 1/4").
_GIRT_TO_FACE_IN = 2.0
#: Screw inset from the standoff's top and bottom edges (notes/eave_gutter_girt.md §3).
_SCREW_INSET_IN = 1.0


def _span(member, direction: str):
    """``(u_lo, u_hi, along_lo, along_hi)`` in inches for a member running along the eave."""
    u_ax, a_ax = (0, 1) if direction == "x" else (1, 0)
    half = cross_section(member.profile).width_m / 2.0
    u = member.p0[u_ax]
    along = sorted((member.p0[a_ax], member.p1[a_ax]))
    return ((u - half) / M_PER_IN, (u + half) / M_PER_IN,
            along[0] / M_PER_IN, along[1] / M_PER_IN)


def _nearest(members, direction: str, station_in: float):
    def gap(m):
        _u0, _u1, a0, a1 = _span(m, direction)
        return 0.0 if a0 <= station_in <= a1 else min(abs(a0 - station_in),
                                                       abs(a1 - station_in))
    return min(members, key=gap) if members else None


def _hidden(points, tag: str, closed: bool = False) -> Polyline:
    return Polyline(points=tuple(points), layer=LAYER, closed=closed, lineweight=LIGHT,
                    linetype="HIDDEN", tag=f"detail-component:{tag}")


def _hidden_clipped(points, tag: str, crop_in) -> list[Polyline]:
    """A two-point hidden line trimmed to the crop (inches), or nothing if it lies outside."""
    seg = clip_segment(points[0], points[1], crop_in)
    return [] if seg is None else [_hidden(seg, tag)]


def eave_gutter_support(model, clad_out: float, out_sign: float, direction: str,
                        station: float, crop=None) -> tuple[list[IRNode], list]:
    """``(nodes, label entries)`` for the gutter's load path back to the eave blocking.

    ``crop`` (metres, the detail's window) clips the hidden lines, which otherwise run on
    to the block wherever the window stops short of it.
    """
    station_in = station / M_PER_IN
    crop_in = None if crop is None else tuple(
        (u / M_PER_IN, z / M_PER_IN) for (u, z) in crop)

    def near(m) -> bool:
        u0, u1, _a0, _a1 = _span(m, direction)
        return min(abs(u0 - clad_out), abs(u1 - clad_out)) <= _REACH_IN

    ours = [m for m in model.all_members() if m.connection in (_BLOCKING, _GIRT) and near(m)]
    blocks = [m for m in ours if m.connection == _BLOCKING]
    girts = [m for m in ours if m.connection == _GIRT and m.category == "strapping"]
    standoffs = [m for m in ours if m.connection == _GIRT and m.category != "strapping"]
    block = _nearest(blocks, direction, station_in)
    girt = _nearest(girts, direction, station_in)
    standoff = _nearest(standoffs, direction, station_in)
    if block is None or girt is None:
        return [], []

    nodes: list[IRNode] = []
    entries = []
    b0, b1, *_ = _span(block, direction)
    bz0, bz1 = block.z0_m / M_PER_IN, block.z1_m / M_PER_IN
    entries.append((((b0 + b1) / 2.0, (bz0 + 2.0 * bz1) / 3.0),
                    f"{block.profile} eave block on the plate; ccSPF over it"))
    g0, g1, *_ = _span(girt, direction)
    gz0, gz1 = girt.z0_m / M_PER_IN, girt.z1_m / M_PER_IN
    girt_outer = g1 if out_sign > 0 else g0
    block_inner = b0 if out_sign > 0 else b1
    if not 0.0 <= out_sign * (clad_out - girt_outer) <= _GIRT_TO_FACE_IN:
        return [], []  # this cut's weather face is not the eave the girt carries
    if standoff is not None:
        s0, s1, *_ = _span(standoff, direction)
        sz0, sz1 = standoff.z0_m / M_PER_IN, standoff.z1_m / M_PER_IN
        box = clip_rect(s0, s1, sz0, sz1, crop_in)
        if box is not None:
            nodes.append(_hidden(rect_points(box[0], box[2], box[1], box[3]), "girt-standoff",
                                 closed=True))
        entries.append((((g0 + g1) / 2.0, (gz0 + gz1) / 2.0),
                        f"{girt.profile} gutter girt on a {standoff.profile} standoff "
                        f"each bay (beyond)"))
        for z in (sz1 - _SCREW_INSET_IN, sz0 + _SCREW_INSET_IN):
            nodes += _hidden_clipped(((girt_outer, z), (block_inner, z)), "tlok08", crop_in)
        entries.append((((s0 + s1) / 2.0, sz1 - _SCREW_INSET_IN),
                        "2 TLOK08 per standoff into the block"))

    hanger = _hanger(model, clad_out, out_sign, direction, station, girt, girt_outer, crop_in)
    if hanger is not None:
        hanger_nodes, target, label = hanger
        nodes += hanger_nodes
        entries.append((target, label))
    return nodes, entries


#: The back clip: drawn gauge, how far it rises above the screw, and its foot along the floor.
_CLIP_T_IN = 0.06
_CLIP_ABOVE_SCREW_IN = 0.75
_CLIP_FOOT_IN = 1.0
#: The gutter's own sheet, which the clip sits inside of.
_GUTTER_SHEET_IN = 0.024
#: Washer under the sealed screw head, drawn on the clip's face.
_WASHER_IN = 0.5
_SCREW_EDGE_IN = 0.25


def gutter_under_eave(model, clad_out: float, direction: str, station: float):
    """``(gutter, roof)`` for the authored catalog gutter at this eave cut, else ``None``."""
    from typehaus.model.trim import Gutter

    u_ax, a_ax = (0, 1) if direction == "x" else (1, 0)
    for el in model.plan.all_elements():
        if not isinstance(el, Gutter) or not el.product:
            continue
        a, b = el.path[0].xy_m, el.path[-1].xy_m
        if abs(a[u_ax] - b[u_ax]) > 1e-6 or abs(a[u_ax] / M_PER_IN - clad_out) > _REACH_IN:
            continue
        if min(a[a_ax], b[a_ax]) <= station <= max(a[a_ax], b[a_ax]):
            roof = next((r for r in model.roofs if r.tag == el.host_ref), None)
            return (el, roof) if roof is not None else None
    return None


def hanger_screw(model, clad_out: float, out_sign: float, direction: str, station: float,
                 girt) -> tuple[float, float, float, bool] | None:
    """``(back_u, screw_z, crest_z, reaches_girt)`` in inches for the provisional hanger.

    The face and its kick hang inside the trough, so a p. 46 strap from the front lip back
    up the roof cannot pass; the hanger sits below the face, and its screw goes through the
    back *below the crest* into the eave girt, mid-way through what the two share.
    ``reaches_girt`` is False when the back does not overlap the girt at all.
    """
    found = gutter_under_eave(model, clad_out, direction, station)
    if found is None:
        return None
    el, _roof = found
    u_ax = 0 if direction == "x" else 1
    back = el.path[0].xy_m[u_ax] / M_PER_IN
    crest = el.top_elevation.meters / M_PER_IN
    floor = crest - el.depth.meters / M_PER_IN
    lo, hi = max(floor, girt.z0_m / M_PER_IN), min(crest, girt.z1_m / M_PER_IN)
    if hi - lo < 2.0 * _SCREW_EDGE_IN:
        return back, floor + _SCREW_EDGE_IN, crest, False
    return back, (lo + hi) / 2.0, crest, True


def _hanger(model, clad_out, out_sign, direction, station, girt, girt_outer, crop_in=None):
    """The provisional hanger, schematically: a clip on the back's inner face, low in the
    trough, with one sealed screw through clip, back and cladding into the girt.

    Nothing spans the trough: the eave face blocks a front-lip strap, and the bracket that
    replaces this is still to be selected (``notes/roof_wall_eave_detail.md``).
    """
    screw = hanger_screw(model, clad_out, out_sign, direction, station, girt)
    found = gutter_under_eave(model, clad_out, direction, station)
    if screw is None or found is None:
        return None
    back, fix_z, crest, reaches = screw
    el, _roof = found
    floor = crest - el.depth.meters / M_PER_IN
    half = _CLIP_T_IN / 2.0
    leg = back + out_sign * (_GUTTER_SHEET_IN + half)
    foot_z = floor + _GUTTER_SHEET_IN + half
    top = min(fix_z + _CLIP_ABOVE_SCREW_IN, crest - 1.0)
    clip = [(leg, top), (leg, foot_z), (leg + out_sign * _CLIP_FOOT_IN, foot_z)]
    nodes = flashing_nodes(clip, thickness=_CLIP_T_IN, material="metal", tag="gutter-hanger",
                           lineweight=PROFILE)
    face = leg + out_sign * half
    washer = ((face, fix_z - _WASHER_IN / 2.0), (face, fix_z + _WASHER_IN / 2.0))
    nodes.append(Polyline(points=washer, layer=LAYER, lineweight=LIGHT,
                          tag="detail-component:hanger-washer"))
    nodes += _hidden_clipped(((face, fix_z), (girt_outer - out_sign * 1.25, fix_z)),
                             "hanger-screw", crop_in)
    where = (f"into the {girt.profile} eave girt" if reaches
             else "short of the eave girt (no common depth)")
    label = (f"gutter hanger, pending bracket selection; sealed fastener through the gutter "
             f"back {crest - fix_z:.1f}\" below the crest, {where}")
    return nodes, (leg, (fix_z + top) / 2.0), label
