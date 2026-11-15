"""A hung machine's strut trapeze, off ``Equipment.hangers`` (``model/equipment_hangers.py``).

Two struts run under the case's short sides (more, evenly between), each the short side plus
``overhang`` at both ends; a rod stands mid-overhang at each strut end. The case bottom is
the strut top (``Mount.elevation`` via the canvas object's ``body_z0_m``); a rod's drop is
the host member's underside less that. The host is the member over the rod
(``_MemberIndex.member_over``, as the duct hangers find theirs); the top fixing is a strut
bridge from it to the nearest parallel member on the rod's far side, cut between their webs
and bearing on the tops of both bottom flanges (inside the bay, clear of a ceiling under the
joists; a flangeless member takes it underneath), the rod's load split by the lever rule. A
rod with no host, no far member or standing in a flange keeps its ``gap`` for
``structural.equipment_hangers``. Solids are drawn here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_part_solids import ROD_DIAMETER_M
from typehaus.resolve.duct_supports import _MemberIndex

#: P1000-class strut section, drawn and added to the rod length.
STRUT_SECTION_M = 1.625 * M_PER_IN
#: Rod below the trapeze strut for its washer and two nuts.
ROD_TAIL_M = 1.0 * M_PER_IN
#: Under a flangeless (sawn) member the bridge runs this far past each joist centre.
BRIDGE_END_M = 1.5 * M_PER_IN
#: A rod may hang this far below its host (a basement machine on a long drop).
MAX_DROP_M = 120 * M_PER_IN
#: Plan search for the bridge's far member: a 24" o.c. bay with slop.
BRIDGE_REACH_M = 30 * M_PER_IN
#: A strut slides inward (still under the case) this far, in these steps, for its rods to
#: clear the flanges a bridge bears on and its parts the run envelopes.
NUDGE_MAX_M, NUDGE_STEP_M = 4.0 * M_PER_IN, 0.25 * M_PER_IN
#: A rod's clear gap to a flange edge.
FLANGE_CLEAR_M = 0.125 * M_PER_IN
THROUGH_FLANGE = "through its flange"
#: A trapeze hangs from the floor framing, never a partition's top plate.
HOSTS = frozenset({"joist", "sister_joist", "rim", "blocking", "header", "strongback"})
_PARALLEL_SIN = math.sin(math.radians(5.0))
_SAME_LEVEL_M = 0.01


@dataclass(frozen=True)
class BridgeSeat:
    """One joist a bridge bears on: its key, profile, share of the rod, station, and the side
    of its web the bridge sits (+1/-1 across the member's direction)."""

    member: str
    profile: str | None
    share: float
    along_m: float
    side: int = 1


@dataclass(frozen=True)
class ResolvedEquipmentHanger:
    """One trapeze rod. ``drop_m`` is host underside to strut top; ``load_lb`` the case
    weight over ``count`` (None where the type publishes no weight)."""

    equipment_tag: str
    storey: str
    rod: int
    strut: int
    point: tuple[float, float]
    strut_top_z_m: float
    strut_length_m: float
    rod_product_ref: str
    strut_product_ref: str
    fixing_product_ref: str
    load_lb: float | None
    hangs_from: str | None = None
    drop_m: float = 0.0
    rod_length_m: float = 0.0
    bridge: tuple[BridgeSeat, ...] = ()
    bridge_length_m: float = 0.0
    #: The bridge's plan ends: the two web faces (or past each joist line, under a sawn one).
    bridge_ends: tuple[tuple[float, float], ...] = ()
    #: The bridge's bottom: a flange top, or the host underside less the strut.
    bridge_z_m: float = 0.0
    gap: str | None = None


def resolve_equipment_hangers(plan: Any, model: Any) -> None:
    hung = {el.tag: el for el in plan.all_elements()
            if getattr(el, "hangers", None) is not None and el.tag}
    if not hung:
        return
    from typehaus.resolve.equipment_hanger_clearance import RunEnvelopes
    from typehaus.resolve.equipment_hanger_solids import hanger_solids

    runs = RunEnvelopes(model)
    types = {t.tag: t for t in plan.library.equipment_types}
    index = _MemberIndex(model)
    for item in sorted((o for o in model.canvas_objects if o.tag in hung),
                       key=lambda o: o.tag):
        spec = hung[item.tag].hangers
        weight = getattr(types.get(item.type_ref), "weight_lb", None)
        load = weight / spec.count if weight is not None else None
        corners = list(item.footprint)[:4]
        mid = (sum(c[0] for c in corners) / 4.0, sum(c[1] for c in corners) / 4.0)
        for strut, (axis, half_length) in enumerate(strut_axes(item, spec), start=1):
            model.equipment_hangers.extend(_strut_rods(
                index, item, spec, strut, axis, half_length, load, mid, runs))
    hanger_solids(model, [h for h in model.equipment_hangers if h.equipment_tag in hung])


def _strut_rods(index: _MemberIndex, item: Any, spec: Any, strut: int, axis: Any,
                half_length: float, load: float | None, mid: tuple[float, float],
                runs: Any = None) -> list[ResolvedEquipmentHanger]:
    """The strut's two rods, the strut slid toward the case centre (``NUDGE_MAX_M`` at most)
    until neither rod stands in a flange its bridge bears on and no rod, bridge or the strut
    is inside a run envelope (``runs``). No station clears both: the first clear of the
    flanges (sliding to shave a run would put a rod through another's metal), else the
    nominal station; ``structural.equipment_hanger_clearance`` grades what is left."""
    (cx, cy), (ux, uy) = axis
    inward = (mid[0] - cx, mid[1] - cy)
    along = inward[0] * -uy + inward[1] * ux
    nx, ny = (-uy, ux) if along >= 0 else (uy, -ux)
    reach = half_length - spec.overhang.meters / 2.0
    first: list[ResolvedEquipmentHanger] | None = None
    seated: list[ResolvedEquipmentHanger] | None = None
    for step in range(int(round(NUDGE_MAX_M / NUDGE_STEP_M)) + 1):
        d = step * NUDGE_STEP_M
        rods = [_rod(index, item, spec, strut, 2 * (strut - 1) + end,
                     (cx + d * nx + side * reach * ux, cy + d * ny + side * reach * uy),
                     2.0 * half_length, load)
                for end, side in enumerate((-1.0, 1.0), start=1)]
        first = first or rods
        if any(r.gap and THROUGH_FLANGE in r.gap for r in rods):
            continue
        seated = seated or rods
        if runs is None or runs.worst(rods) == 0.0:
            return rods
    return seated or first


def strut_axes(item: Any, spec: Any) -> list[tuple[tuple[tuple[float, float],
                                                        tuple[float, float]], float]]:
    """Per strut: ((centre xy, unit along it), half length), short sides first."""
    corners = list(item.footprint)[:4]
    edges = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    lengths = [math.dist(a, b) for a, b in edges]
    first = 0 if lengths[0] <= lengths[1] else 1
    (a, b), (_, c) = edges[first], edges[first + 1]
    short, long_ = lengths[first], lengths[first + 1]
    u = ((b[0] - a[0]) / short, (b[1] - a[1]) / short)
    v = ((c[0] - b[0]) / long_, (c[1] - b[1]) / long_)
    mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
    n = spec.count // 2
    inset = STRUT_SECTION_M / 2.0
    stations = [inset + k * (long_ - 2.0 * inset) / (n - 1) for k in range(n)]
    half = short / 2.0 + spec.overhang.meters
    return [(((mid[0] + s * v[0], mid[1] + s * v[1]), u), half) for s in stations]


def _rod(index: _MemberIndex, item: Any, spec: Any, strut: int, rod: int,
         point: tuple[float, float], strut_length: float,
         load: float | None) -> ResolvedEquipmentHanger:
    top = item.body_z0_m
    base = dict(equipment_tag=item.tag, storey=item.storey,
                rod=rod, strut=strut, point=point, strut_top_z_m=top, strut_length_m=strut_length,
                rod_product_ref=spec.rod_product_ref, strut_product_ref=spec.strut_product_ref,
                fixing_product_ref=spec.top_fixing_product_ref, load_lb=load)
    host, drop = index.member_over(point, top, MAX_DROP_M, HOSTS)
    if host is None:
        return ResolvedEquipmentHanger(**base, gap=(
            f"no framing within {MAX_DROP_M / M_PER_IN:.0f}\" above or 16\" beside the rod"))
    flange, web, flange_w = _flange_web(host)
    bridge_z = top + drop + (flange if flange else -STRUT_SECTION_M)
    rod_length = bridge_z + 2.0 * (STRUT_SECTION_M + ROD_TAIL_M) - top
    hosted = dict(hangs_from=index.key(host), drop_m=drop, rod_length_m=rod_length,
                  bridge_z_m=bridge_z)
    found = _far_member(index, host, point)
    if found is None:
        return ResolvedEquipmentHanger(**base, **hosted, gap=(
            f"no member parallel to {index.key(host)} within "
            f"{BRIDGE_REACH_M / M_PER_IN:.0f}\" across the rod for its bridge"))
    far, far_offset = found
    side = _offset(host, point)
    span = abs(side) + abs(far_offset)
    clear = flange_w / 2.0 + ROD_DIAMETER_M / 2.0 + FLANGE_CLEAR_M
    if flange and min(abs(side), abs(far_offset)) < clear:
        near = host if abs(side) <= abs(far_offset) else far
        return ResolvedEquipmentHanger(**base, **hosted, gap=(
            f"rod {min(abs(side), abs(far_offset)) / M_PER_IN:.2f}\" off "
            f"{index.key(near)}'s centre: {THROUGH_FLANGE}"))
    seats = tuple(BridgeSeat(index.key(m), m.profile, share, _along(m, point),
                             1 if _offset(m, point) >= 0 else -1)
                  for m, share in ((host, abs(far_offset) / span), (far, abs(side) / span)))
    hx, hy = _direction(host)
    normal = (-hy, hx)
    # Host line at n = -side from the rod, far line at n = -far_offset: between the webs on
    # the flanges, else past both lines underneath.
    lo, hi = sorted((-side, -far_offset))
    reach = -web / 2.0 if flange else BRIDGE_END_M
    ends = tuple((point[0] + n * normal[0], point[1] + n * normal[1])
                 for n in (lo - reach, hi + reach))
    return ResolvedEquipmentHanger(**base, **hosted, bridge=seats, bridge_ends=ends,
                                   bridge_length_m=span + 2.0 * reach)


def _flange_web(member: Any) -> tuple[float | None, float, float]:
    """(bottom-flange thickness, web thickness, flange width) of an I-joist or truss chord;
    (None, 0, 0) for a sawn member or an unparsed profile, whose bridge goes underneath."""
    from typehaus.resolve.framing.profiles import cross_section

    try:
        section = cross_section(member.profile or "")
    except (ValueError, KeyError):
        return None, 0.0, 0.0
    if section.shape not in ("i_joist", "floor_truss") or not section.flange_thickness_m:
        return None, 0.0, 0.0
    return (section.flange_thickness_m, section.web_thickness_m or 0.0,
            section.flange_width_m or section.width_m)


def _direction(member: Any) -> tuple[float, float]:
    (x0, y0), (x1, y1) = member.p0, member.p1
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    return (x1 - x0) / length, (y1 - y0) / length


def _offset(member: Any, point: tuple[float, float]) -> float:
    """Signed plan distance from the member's line to ``point``."""
    dx, dy = _direction(member)
    return (point[0] - member.p0[0]) * -dy + (point[1] - member.p0[1]) * dx


def _along(member: Any, point: tuple[float, float]) -> float:
    dx, dy = _direction(member)
    return (point[0] - member.p0[0]) * dx + (point[1] - member.p0[1]) * dy


def _far_member(index: _MemberIndex, host: Any,
                point: tuple[float, float]) -> tuple[Any, float] | None:
    """(member, the rod's offset from it in the host's frame): the nearest member parallel
    to ``host``, level with it, across ``point`` from it."""
    from shapely.geometry import Point

    hx, hy = _direction(host)
    side = _offset(host, point)
    best: tuple[float, Any] | None = None
    for i in index.tree.query(Point(point).buffer(BRIDGE_REACH_M)):
        member = index.members[int(i)]
        if (member is host or member.category not in HOSTS
                or abs(member.z0_m - host.z0_m) > _SAME_LEVEL_M):
            continue
        mx, my = _direction(member)
        if abs(hx * my - hy * mx) > _PARALLEL_SIN:
            continue
        if not 0.0 <= _along(member, point) <= math.dist(member.p0, member.p1):
            continue
        offset = _offset(member, point) * math.copysign(1.0, hx * mx + hy * my)
        if offset * side > 0:
            continue  # on the host's side of the rod (offsets in the host's frame)
        if best is None or abs(offset) < abs(best[1]):
            best = (member, offset)
    return best
