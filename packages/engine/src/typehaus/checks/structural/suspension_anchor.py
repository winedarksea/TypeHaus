"""A hung seat's load path, graded by arithmetic: the joist line, its bearings, the bolts,
the hardware, and the seat's own product limits (``model/suspension.py``).

Furniture, not engineering: a normal check, never ``engineered()``, never on the register.
Oracle: the house's ``notes/hanging_seat_anchor.md``; ``_suspension_math`` holds the sums.
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
    point_deflection,
)
from typehaus.findings import Finding
from typehaus.hardware.catalog import structural_hardware_catalog
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
    out += _rated_load(seats, anchors)
    factor = getattr(getattr(ctx.preferences, "structural", None),
                     "hanging_seat_impact_factor", None)
    for record in ctx.model.suspension_anchors:
        out.append(_grade(ctx, anchors[record.tag], record, seats, factor))
    return out


def _hung_seats(ctx: CheckContext) -> dict[str, tuple]:
    types = {t.tag: t for t in ctx.plan.library.furniture_types
             if isinstance(t, HangingSeatType)}
    return {item.tag: (item, types[item.type_ref]) for item in ctx.model.canvas_objects
            if item.type_ref in types}


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


def _grade(ctx, anchor: SuspensionAnchor, record, seats, factor) -> Finding:
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
    parts = [_part(tag) for tag in anchor.hardware]
    item, seat = seats.get(anchor.carries, (None, None))
    weights = [p.weight_lb for p in parts if p is not None] + [getattr(seat, "weight_lb", 0.0)]
    missing = [t for t, p in zip(anchor.hardware, parts, strict=True)
               if p is None or p.weight_lb is None]
    if missing:
        return unknown(CID, f"{anchor.tag}: hardware {', '.join(missing)} is not catalogued "
                       "with a weight", tags)
    if not _spans_bearing_to_bearing(ctx, record):
        return unknown(CID, f"{anchor.tag}: line {record.line_key} of {record.floor} does not "
                       "run bearing to bearing (an opening cuts it), so it is not the simple "
                       "span graded here", tags)
    bearings = _bearing_lengths(ctx, record)
    if None in bearings:
        return unknown(CID, f"{anchor.tag}: no bearing length read at "
                       f"{' / '.join(str(t) for t in record.bearings)}", tags)
    p = anchor.design_load_lb * factor + sum(weights)
    states, notes = _states(anchor, record, grade, p, bearings, parts)
    notes += _product(ctx, record, item, seat)
    head = (f"{anchor.tag} on {record.floor} line {record.line_key} ({record.member}, "
            f"{(record.span_m[1] - record.span_m[0]) / _IN / 12:.2f}' span): P = "
            f"{anchor.design_load_lb:,.0f} lb x {factor:g} + {sum(weights):.1f} lb own "
            f"weight = {p:,.0f} lb")
    worst = max(states, key=lambda s: s.ratio)
    body = "; ".join(s.text() for s in states)
    over = [s for s in states if s.ratio > 1 + _TOL]
    bad = [n for n in notes if n.startswith("FAIL")]
    if over or bad:
        return failed(CID, f"{head}. {body}. " + " ".join(
            [f"{s.name} is over" for s in over] + bad), tags,
            fix="deepen or double the line, add bolts, or lower the rated load")
    return passed(CID, f"{head}. {body}. Governs: {worst.name} {worst.ratio:.2f}. "
                  + " ".join(notes), tags)


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


def _bearing_lengths(ctx, record) -> tuple[float | None, float | None]:
    """Inches of seat at each end: the floor's authored ``end_bearing``, else the wall's
    structure layer."""
    system = ctx.plan.by_tag(record.floor)
    authored = dict(system.joists.end_bearing) if isinstance(system, FloorSystem) else {}
    out = []
    for tag in record.bearings:
        if tag in authored:
            out.append(authored[tag].meters / _IN)
            continue
        wall = ctx.model.wall(tag) if tag else None
        core = [ly.thickness_m for ly in getattr(wall, "layers", ()) if ly.function == "structure"]
        out.append(core[0] / _IN if core else None)
    return tuple(out)


def _states(anchor, record, grade, p, bearings, parts) -> tuple[list[LimitState], list[str]]:
    section = cross_section(record.member)
    b, d = section.width_m / _IN, section.depth_m / _IN
    span = (record.span_m[1] - record.span_m[0]) / _IN
    a = (record.along_m - record.span_m[0]) / _IN
    w = (FLOOR_LIVE_LOAD_PSF + FLOOR_DEAD_LOAD_PSF) * record.tributary_m / _IN / 144
    beam = SimpleSpan(p=p, a=a, span=span, w=w)
    left, right = beam.reactions
    deflection = point_deflection(p, a, span, grade.e_psi, b, d, grade.shear_deflection_k)
    z, mode = bolt_double_shear(anchor.bolt_diameter.meters / _IN, b, _SIDE_PLATE_IN,
                                grade.bolt_g_perp)
    clear = min(a, span - a) >= 5 * d
    vr, de = connection_shear(grade.fv_psi, b, d, anchor.bolt_diameter.meters / _IN, clear)
    states = [
        LimitState("bending", beam.max_moment / 12, grade.fb_adjusted_psi(d) * b * d * d / 6
                   / 12, "lb-ft"),
        LimitState("shear", 1.5 * max(left, right) / (b * d), grade.fv_psi, "psi"),
        *(LimitState(f"bearing at {tag}", r / (b * length), grade.fc_perp_psi, "psi")
          for tag, r, length in zip(record.bearings, (left, right), bearings, strict=True)),
        LimitState(f"deflection under P (L/{DEFLECTION_LIMIT})", deflection,
                   span / DEFLECTION_LIMIT, "in"),
        LimitState(f"{anchor.bolts} bolts double shear (mode {mode})", p, anchor.bolts * z,
                   "lb"),
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
    return states, notes


def _product(ctx, record, item, seat) -> list[str]:
    """The seat's own limits: wall clearance from the hang point and the suspension's reach."""
    if seat is None or item is None:
        return []
    notes = []
    room = next((r for r in ctx.model.rooms if r.tag == item.room), None) or room_owning(
        ctx.model, item.storey, record.xy)
    if room is not None and len(room.clear_face) >= 3:
        gap = Polygon(room.clear_face).exterior.distance(Point(record.xy)) / _IN
        need = seat.wall_clearance.meters / _IN
        notes.append(f"{'FAIL: ' if gap < need - _TOL else ''}hang point {gap:.1f}\" from "
                     f"{room.tag}'s finish face (needs {need:.1f}\").")
    if item.suspension_m is not None:
        lo, hi = (x.meters / _IN for x in seat.suspension_range)
        rope = item.suspension_m / _IN
        inside = lo - _TOL <= rope <= hi + _TOL
        notes.append(f"{'' if inside else 'FAIL: '}suspension {rope:.1f}\" to "
                     f"{item.suspended_from} (kit {lo:.0f}-{hi:.0f}\").")
    return notes
