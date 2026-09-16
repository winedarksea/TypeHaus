"""What carries the eave gutter: eave blocking, gutter girt, standoffs, TLOK08s, hanger.

All read off resolved members (``Roof.eave_blocking`` and ``resolve/roof_eave_girt.py``),
so a detail over a roof without them draws nothing here. The blocking and girt are cut
by the section already; the standoff sits at a bay centre, usually off the cut plane, so it
and its screws draw as HIDDEN lines beyond. The hanger is not a model element (not billed)
and draws schematically off the resolved gutter.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import LAYER
from typehaus.emit.draw.detail_components.geometry import flashing_nodes, rect_points
from typehaus.emit.draw.lineweights import LIGHT
from typehaus.emit.draw.scene import IRNode, Polyline
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


def eave_gutter_support(model, clad_out: float, out_sign: float, direction: str,
                        station: float) -> tuple[list[IRNode], list]:
    """``(nodes, label entries)`` for the gutter's load path back to the eave blocking."""
    station_in = station / M_PER_IN

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
        nodes.append(_hidden(rect_points(s0, sz0, s1, sz1), "girt-standoff", closed=True))
        entries.append((((g0 + g1) / 2.0, (gz0 + gz1) / 2.0),
                        f"{girt.profile} gutter girt on a {standoff.profile} standoff "
                        f"each bay (beyond)"))
        for z in (sz1 - _SCREW_INSET_IN, sz0 + _SCREW_INSET_IN):
            nodes.append(_hidden(((girt_outer, z), (block_inner, z)), "tlok08"))
        entries.append((((s0 + s1) / 2.0, sz1 - _SCREW_INSET_IN),
                        "2 TLOK08 per standoff into the block"))

    hanger = _hanger(model, clad_out, out_sign, direction, station, girt_outer,
                     (gz0 + gz1) / 2.0)
    if hanger is not None:
        hanger_nodes, target = hanger
        nodes += hanger_nodes
        entries.append((target, "hidden hanger at each standoff, screwed to the girt"))
    return nodes, entries


def _hanger(model, clad_out, out_sign, direction, station, girt_outer, girt_mid):
    """A hidden hanger across the trough's rim, fixed through the back sheet into the girt."""
    u_ax, a_ax = (0, 1) if direction == "x" else (1, 0)
    us: list[float] = []
    rim = None
    for solid in model.solids:
        if solid.category != "gutter":
            continue
        along = [p[a_ax] for p in solid.outline]
        if not min(along) <= station <= max(along):
            continue
        across = [p[u_ax] / M_PER_IN for p in solid.outline]
        if min(abs(min(across) - clad_out), abs(max(across) - clad_out)) > _REACH_IN:
            continue
        us += across
        rim = max(rim or -1e9, solid.z1_m / M_PER_IN)
    if not us or rim is None:
        return None
    back, front = (min(us), max(us)) if out_sign > 0 else (max(us), min(us))
    z = rim - 0.4
    # Fixed at the girt's mid-height, clear of the TLOK08s near its edges.
    fix_z = min(z - 1.25, girt_mid)
    strap = [(front - out_sign * 0.6, z), (back + out_sign * 0.6, z),
             (back + out_sign * 0.6, fix_z)]
    nodes = flashing_nodes(strap, thickness=0.12, material="metal", tag="gutter-hanger",
                           lineweight=LIGHT)
    nodes.append(_hidden(((back + out_sign * 0.6, fix_z),
                          (girt_outer - out_sign * 1.25, fix_z)), "hanger-screw"))
    return nodes, ((back + front) / 2.0, z)
