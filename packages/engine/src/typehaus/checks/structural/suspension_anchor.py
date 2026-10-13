"""A hung seat's load path, graded by arithmetic: the joist line, its bearings, the bolts,
the hardware, and the seat's own product limits (``model/suspension.py``).

Member states (bending, shear, bearing, deflection) take every anchor on the line; the
connection states (bolts, NDS 3.4.3.3, hardware) are the anchor's own. Wet service (an
exterior deck, or ``SuspensionAnchor.wet_service``) wants a wet grade row and takes NDS
C_M 0.70 on the bolts and a hanger.

Furniture, not engineering: a normal check, never ``engineered()``, never on the register.
Oracles: the house's ``notes/hanging_seat_anchor.md`` and ``notes/court_daybed_anchor.md``;
``_suspension_math`` holds the sums.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._suspension_math import (
    LimitState,
    SimpleSpan,
    bolt_double_shear,
    connection_shear,
    deflection_at,
)
from typehaus.findings import Finding
from typehaus.hardware.catalog import structural_hardware_catalog
from typehaus.joints.authored import authored_hanger_item, hanger_specs
from typehaus.library.member_grades import MEMBER_GRADES
from typehaus.loads import FLOOR_DEAD_LOAD_PSF, FLOOR_LIVE_LOAD_PSF
from typehaus.model.floors import FloorSystem
from typehaus.model.suspension import HangingSeatType, SuspensionAnchor, suspension_anchors
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.room_lookup import room_owning

CID = "structural.suspension_anchor"
_IN = 0.0254
#: Deflection under the hung load alone. Owner-tunable later; a swinging seat should not
#: crack the ceiling it hangs through.
DEFLECTION_LIMIT = 480
_SIDE_PLATE_IN = 0.25
_TOL = 1e-6
#: How far a joist tip may stop short of its bearing axis and still bear on it.
_SEAT_M = 6 * _IN
#: NDS 2018 Table 11.3.3, dowel-type fasteners in wet service; Simpson defer to it.
WET_SERVICE_CM = 0.70
#: NDS 2018 Table 12.5.1A, load perpendicular to grain: loaded edge 4D, unloaded edge 1.5D.
_LOADED_EDGE_D, _UNLOADED_EDGE_D = 4.0, 1.5
#: An anchor's offset may sit this far off its type's hang point (fmt rounds to 1/64").
_HANG_POINT_TOL_M = _IN / 16


@check(Tier.STRUCTURAL, CID)
def suspension_anchor(ctx: CheckContext) -> list[Finding]:
    """Every hung seat hangs from an anchor, and every anchor's load path holds."""
    anchors = {a.tag: a for a in suspension_anchors(ctx.plan)}
    seats = _hung_seats(ctx)
    if not anchors and not seats:
        return [not_applicable(CID, "no SuspensionAnchor and no HangingSeatType placed")]
    out = [failed(CID, f"{item.tag}: a hung seat with no SuspensionAnchor carrying it",
                  (item.tag,), fix="author a SuspensionAnchor with carries=its tag")
           for item, _ in seats.values()
           if not any(a.carries == item.tag for a in anchors.values())]
    out += _unanchored_points(seats, anchors)
    out += _rated_load(seats, anchors)
    factor = getattr(getattr(ctx.preferences, "structural", None),
                     "hanging_seat_impact_factor", None)
    lines: dict[tuple, list] = {}
    for record in ctx.model.suspension_anchors:
        if record.reason is None:
            lines.setdefault((record.floor, record.line_key), []).append(record)
    for record in ctx.model.suspension_anchors:
        partners = [r for r in lines.get((record.floor, record.line_key), ())
                    if r.tag != record.tag]
        out.append(_grade(ctx, anchors, record, partners, seats, factor))
    return out


def _hung_seats(ctx: CheckContext) -> dict[str, tuple]:
    types = {t.tag: t for t in ctx.plan.library.furniture_types
             if isinstance(t, HangingSeatType)}
    return {item.tag: (item, types[item.type_ref]) for item in ctx.model.canvas_objects
            if item.type_ref in types}


def _unanchored_points(seats, anchors) -> list[Finding]:
    out = []
    for item, seat in seats.values():
        held = [a for a in anchors.values() if a.carries == item.tag]
        if not held:
            continue
        loose = [p for p in seat.hang_points
                 if not any(_on_point(a.offset, p) for a in held)]
        if loose:
            out.append(failed(CID, f"{item.tag}: {len(loose)} of {seat.tag}'s "
                              f"{len(seat.hang_points)} hang points carry no anchor",
                              (item.tag, seat.tag),
                              fix="author a SuspensionAnchor at each hang point's offset"))
    return out


def _on_point(offset, point) -> bool:
    """Two item-frame points (``Point2D`` or metre pairs) within 1/16" of each other."""
    (x, y), (px, py) = (getattr(v, "xy_m", v) for v in (offset, point))
    return abs(x - px) <= _HANG_POINT_TOL_M and abs(y - py) <= _HANG_POINT_TOL_M


def _rated_load(seats, anchors) -> list[Finding]:
    out = []
    for item, seat in seats.values():
        held = sum(a.design_load_lb for a in anchors.values() if a.carries == item.tag)
        if held and seat.rated_load_lb > held + _TOL:
            out.append(failed(CID, f"{item.tag}: {seat.tag} is rated {seat.rated_load_lb:,.0f}"
                              f" lb and its anchors answer {held:,.0f} lb",
                              (item.tag, seat.tag),
                              fix="raise the anchors' design_load_lb and re-grade"))
    return out


def _demand(anchor: SuspensionAnchor, seats, factor) -> tuple[float, float] | str:
    """``(P, own weight)`` for one anchor, or why it has none."""
    parts = [_part(tag) for tag in anchor.hardware]
    missing = [t for t, p in zip(anchor.hardware, parts, strict=True)
               if p is None or p.weight_lb is None]
    if missing:
        return f"hardware {', '.join(missing)} is not catalogued with a weight"
    _, seat = seats.get(anchor.carries, (None, None))
    share = getattr(seat, "weight_lb", 0.0) / max(1, len(getattr(seat, "hang_points", ())))
    weight = sum(p.weight_lb for p in parts) + share
    return anchor.design_load_lb * factor + weight, weight


def _grade(ctx, anchors, record, partners, seats, factor) -> Finding:
    anchor = anchors[record.tag]
    tags = (anchor.tag, anchor.carries) + ((record.floor,) if record.floor else ())
    if record.reason:
        return unknown(CID, f"{anchor.tag}: {record.reason}", tags)
    if factor is None:
        return unknown(CID, f"{anchor.tag}: no impact factor to apply to its "
                       f"{anchor.design_load_lb:,.0f} lb", tags,
                       fix="author preferences.toml [structural] hanging_seat_impact_factor")
    grade = MEMBER_GRADES.get(anchor.member_grade)
    if grade is None:
        return unknown(CID, f"{anchor.tag}: no published design values for grade "
                       f"{anchor.member_grade!r}", tags)
    wet = _wet(ctx, anchor, record)
    if wet and grade.service != "wet":
        return unknown(CID, f"{anchor.tag}: {record.floor} is in wet service and grade "
                       f"{grade.tag} is stated dry", tags, fix="name a wet grade row")
    demands = {r.tag: _demand(anchors[r.tag], seats, factor) for r in (record, *partners)}
    bad = next(((t, d) for t, d in demands.items() if isinstance(d, str)), None)
    if bad is not None:
        return unknown(CID, f"{anchor.tag}: {bad[0] + ' ' if bad[0] != anchor.tag else ''}"
                       f"{bad[1]}", tags)
    if not _spans_bearing_to_bearing(ctx, record):
        return unknown(CID, f"{anchor.tag}: line {record.line_key} of {record.floor} does not "
                       "run bearing to bearing (an opening cuts it), so it is not the simple "
                       "span graded here", tags)
    p, weight = demands[anchor.tag]
    others = tuple((demands[r.tag][0], (r.along_m - r.span_m[0]) / _IN) for r in partners)
    states, notes = _states(ctx, anchor, record, grade, p, others, wet)
    if isinstance(states, str):
        return unknown(CID, f"{anchor.tag}: {states}", tags)
    item, seat = seats.get(anchor.carries, (None, None))
    notes += _product(ctx, record, item, seat, anchor)
    head = (f"{anchor.tag} on {record.floor} line {record.line_key} ({record.member}, "
            f"{(record.span_m[1] - record.span_m[0]) / _IN / 12:.2f}' span"
            f"{', wet' if wet else ''}): P = {anchor.design_load_lb:,.0f} lb x {factor:g} + "
            f"{weight:.1f} lb own weight = {p:,.0f} lb")
    if partners:
        head += "; the line also carries " + ", ".join(
            f"{r.tag} ({demands[r.tag][0]:,.0f} lb)" for r in partners)
    worst = max(states, key=lambda s: s.ratio)
    body = "; ".join(s.text() for s in states)
    over = [s for s in states if s.ratio > 1 + _TOL]
    bad_notes = [n for n in notes if n.startswith("FAIL")]
    if over or bad_notes:
        return failed(CID, f"{head}. {body}. " + " ".join(
            [f"{s.name} is over" for s in over] + bad_notes), tags,
            fix="deepen or double the line, add bolts, or lower the rated load")
    return passed(CID, f"{head}. {body}. Governs: {worst.name} {worst.ratio:.2f}. "
                  + " ".join(notes), tags)


def _wet(ctx, anchor, record) -> bool:
    if anchor.wet_service is not None:
        return anchor.wet_service
    return getattr(ctx.plan.by_tag(record.floor), "service", None) == "deck"


def _spans_bearing_to_bearing(ctx, record) -> bool:
    """One joist member on the anchor's line covers its whole span (tips within 6\")."""
    floor = next((f for f in ctx.model.floors if f.tag == record.floor), None)
    axis = 0 if getattr(floor, "direction", "x") == "x" else 1
    ends = [sorted((m.p0[axis], m.p1[axis])) for m in getattr(floor, "members", ())
            if m.category == "joist" and m.child_key.split("-")[2] == record.line_key]
    lo, hi = record.span_m
    return any(a <= lo + _SEAT_M and b >= hi - _SEAT_M for a, b in ends)


def _part(tag: str):
    return next((h for h in structural_hardware_catalog() if h.tag == tag), None)


def _bearing_states(ctx, record, grade, b, reactions, wet) -> list[LimitState] | str:
    """At each end: the hanger it hangs in against its published download, else the seat
    (the floor's authored ``end_bearing``, else the wall's structure layer) in Fc-perp."""
    system = ctx.plan.by_tag(record.floor)
    authored = dict(system.joists.end_bearing) if isinstance(system, FloorSystem) else {}
    specs = hanger_specs(ctx.model)
    cm = WET_SERVICE_CM if wet else 1.0
    out = []
    for tag, r in zip(record.bearings, reactions, strict=True):
        spec = specs.get((tag, record.floor))
        if spec is not None:
            part = authored_hanger_item(spec, record.member)
            allow = getattr(getattr(part, "allowable", None), "download_lb", None)
            if allow is None:
                return f"{spec} at {tag} carries no published download for {record.member}"
            out.append(LimitState(f"{part.model} at {tag}"
                                  + (f" (C_M {cm:g})" if wet else ""), r, allow * cm, "lb"))
            continue
        if tag in authored:
            length = authored[tag].meters / _IN
        else:
            wall = ctx.model.wall(tag) if tag else None
            core = [ly.thickness_m for ly in getattr(wall, "layers", ())
                    if ly.function == "structure"]
            if not core:
                return f"no bearing length read at {tag}"
            length = core[0] / _IN
        out.append(LimitState(f"bearing at {tag}", r / (b * length), grade.fc_perp_psi, "psi"))
    return out


def _states(ctx, anchor, record, grade, p, others, wet):
    section = cross_section(record.member)
    b, d = section.width_m / _IN, section.depth_m / _IN
    span = (record.span_m[1] - record.span_m[0]) / _IN
    a = (record.along_m - record.span_m[0]) / _IN
    w = (FLOOR_LIVE_LOAD_PSF + FLOOR_DEAD_LOAD_PSF) * record.tributary_m / _IN / 144
    beam = SimpleSpan(p=p, a=a, span=span, w=w, others=others)
    left, right = beam.reactions
    bearings = _bearing_states(ctx, record, grade, b, (left, right), wet)
    if isinstance(bearings, str):
        return bearings, []
    deflection = max(deflection_at(beam.loads, at, span, grade.e_psi, b, d,
                                   grade.shear_deflection_k) for _, at in beam.loads)
    diameter = anchor.bolt_diameter.meters / _IN
    cm = WET_SERVICE_CM if wet else 1.0
    z, mode = bolt_double_shear(diameter, b, _SIDE_PLATE_IN, grade.bolt_g_perp)
    clear = min(a, span - a) >= 5 * d
    top = anchor.bolt_top_distance.meters / _IN if anchor.bolt_top_distance else None
    vr, de = connection_shear(grade.fv_psi, b, d, diameter, clear, top)
    row = d / 2 if top is None else top
    parts = [_part(tag) for tag in anchor.hardware]
    under = "P" if not others else f"the line's {len(beam.loads)} loads"
    states = [
        LimitState("bending", beam.max_moment / 12, grade.fb_adjusted_psi(d) * b * d * d / 6
                   / 12, "lb-ft"),
        LimitState("shear", 1.5 * max(left, right) / (b * d), grade.fv_psi, "psi"),
        *bearings,
        LimitState(f"deflection under {under} (L/{DEFLECTION_LIMIT})", deflection,
                   span / DEFLECTION_LIMIT, "in"),
        LimitState(f"{anchor.bolts} bolts double shear (mode {mode}"
                   + (f", C_M {cm:g}" if wet else "") + ")", p, anchor.bolts * z * cm, "lb"),
        LimitState(f"NDS 3.4.3.3 shear at the bolts (d_e {de:.2f}\")", beam.shear_at_load,
                   vr, "lb"),
        *(LimitState(f"{part.model} WLL", p, part.allowable.wll_lb, "lb") for part in parts
          if part.allowable is not None and part.allowable.wll_lb is not None),
    ]
    floor = (f"floor {w * 12:.1f} plf over {record.tributary_m / _IN:.1f}\" tributary, "
             f"load {a / 12:.2f}' from {record.bearings[0]}")
    graded_through_bolts = [part.model for part in parts if part.allowable is None]
    notes = [floor + "."] + ([f"{', '.join(graded_through_bolts)}: no published WLL, graded "
                              "through its bolts."] if graded_through_bolts else [])
    if top is not None:  # a mid-depth row clears both edges on any joist this check grades
        short = [f"{name} edge {have:.2f}\" < {k:g}D" for name, have, k in
                 (("unloaded", row, _UNLOADED_EDGE_D), ("loaded", d - row, _LOADED_EDGE_D))
                 if have < k * diameter - _TOL]
        notes.append(f"FAIL: bolt row {row:.2f}\" below the top: " + "; ".join(short) + "."
                     if short else f"bolt row {row:.2f}\" below the top (edges clear "
                     f"{_UNLOADED_EDGE_D:g}D / {_LOADED_EDGE_D:g}D).")
    return states, notes


def _product(ctx, record, item, seat, anchor) -> list[str]:
    """The seat's own limits: the hang point is one of its own, its wall clearance, and the
    suspension's reach at that point."""
    if seat is None or item is None:
        return []
    notes = []
    if not any(_on_point(anchor.offset, point) for point in seat.hang_points):
        notes.append(f"FAIL: offset is not one of {seat.tag}'s hang points.")
    need = seat.wall_clearance.meters / _IN
    room = next((r for r in ctx.model.rooms if r.tag == item.room), None) or room_owning(
        ctx.model, item.storey, record.xy)
    if room is not None and len(room.clear_face) >= 3:
        gap = Polygon(room.clear_face).exterior.distance(Point(record.xy)) / _IN
        notes.append(f"{'FAIL: ' if gap < need - _TOL else ''}hang point {gap:.1f}\" from "
                     f"{room.tag}'s finish face (needs {need:.1f}\").")
    else:
        near = _nearest_wall(ctx, item, record.xy)
        if near is not None:
            gap, tag = near
            notes.append(f"{'FAIL: ' if gap < need - _TOL else ''}hang point {gap:.1f}\" "
                         f"from {tag}'s face (needs {need:.1f}\"; no room).")
    rope = _rope_at(item, anchor)
    if rope is not None:
        lo, hi = (x.meters / _IN for x in seat.suspension_range)
        inside = lo - _TOL <= rope <= hi + _TOL
        notes.append(f"{'' if inside else 'FAIL: '}suspension {rope:.1f}\" to "
                     f"{item.suspended_from} (kit {lo:.0f}-{hi:.0f}\").")
    return notes


def _rope_at(item, anchor) -> float | None:
    """The cable at this anchor's hang point, inches; the item's one cable without points."""
    for x, y, cable in getattr(item, "suspension_points", ()):
        if _on_point(anchor.offset, (x, y)):
            return cable / _IN
    return item.suspension_m / _IN if item.suspension_m is not None else None


def _nearest_wall(ctx, item, xy) -> tuple[float, str] | None:
    """Inches to the nearest wall face whose height spans the hung body, and its tag."""
    z0 = item.body_z0_m if item.body_z0_m is not None else item.z_m
    z1 = item.body_z1_m if item.body_z1_m is not None else z0
    point, best = Point(xy), None
    for wall in ctx.model.walls:
        if wall.z1_m < z0 or wall.z0_m > z1:
            continue
        for layer in wall.depth_layers():
            if len(layer.polygon) >= 3:
                gap = Polygon(layer.polygon).distance(point) / _IN
                if best is None or gap < best[0]:
                    best = (gap, wall.tag)
    return best
