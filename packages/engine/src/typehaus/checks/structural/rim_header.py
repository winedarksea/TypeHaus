"""``structural.rim_header`` — a 2-ply LSL rim header over a floor-band opening, a published read.

**Subject.** Every ``Door.header_in_band`` (``resolve/band_headers``): the floor's edge rim plus
the ply behind it carry the opening, because the wall's rough head stands under its plates.
None is N/A, from every door examined. Retires ``band_header/<door>`` (the LVL plies), decision
12.

**Four separate findings per opening**, because a table assumes uniform load and says nothing of
what a seat does to it:

1. **header** — Weyerhaeuser TJ-8000 (March 2025) p.7 2-ply 1 1/4" row at the next span at or
   past the span c-c of bearing, against the floor strip plus the door seats' reactions carried
   as the equivalent uniform load (``engineering/band_header``). UNKNOWN until the plies are the
   rim's own stock and 4 1/2" of bearing is there (TJ-8000 p.6).
2. **ply fastening** — p.7's top-load row (10d, 3 rows, 12" o.c., one face).
3. **seat load introduction** — each seat's reaction over its length against p.7's side row, and
   the seat screws' own combined grade from the door's record.
4. **jamb bearing, the band to the foundation** — the stacked pack on the plate above, on the
   rim and ply, on the host plates, the rim's p.5 rows, the pack on the plate under it, and
   IRC R602.7.5's studs each end.

**Closure:** the table's uniform-load condition rests on a ForteWEB run the owner retains
(``notes/engineering_review_2026-11-22/forteweb_D-B-SUNKEN.md`` is its exact input); this check
carries the same loads as the largest equivalent uniform. Oracle:
``houses/catlin/notes/sunken_door_band_header.md`` §2-§6, ``tests/test_rim_header.py``.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.engineering import band_header as bh
from typehaus.engineering import band_header_seats as seats
from typehaus.engineering.item import LimitState
from typehaus.findings import Finding, failed, not_applicable, passed, unknown
from typehaus.resolve.band_headers import _frame, band_header, band_header_doors
from typehaus.resolve.framing.profiles import cross_section

_ID = "structural.rim_header"
_CODE = "TJ-8000 pp.5-7; IRC R602.7.5, Table R301.7, R301.5"
_IN = 0.0254
_FT = 0.3048


def _finding(door: str, tags, title: str, states: list[LimitState], detail: str = "") -> Finding:
    graded = [s for s in states if not s.is_detailing] or states
    worst = max(graded, key=lambda s: s.ratio)
    rows = "; ".join(f"{s.name} {s.demand:,.4g} of {s.capacity:,.4g} {s.unit} "
                     f"({s.ratio:.3f})" for s in states)
    text = (f"{door} {title}: governs {worst.name} at d/c {worst.ratio:.3f} — {rows}"
            + (f". {detail}" if detail else ""))
    if any(s.ratio > 1.0 + 1e-9 for s in states):
        return failed(_ID, text, tags, code=_CODE,
                      fix="deepen or add to the header, or re-read the next table row")
    return passed(_ID, text, tags, code=_CODE)


_JOINT_MIN_IN = 12.0


def _joint_finding(ctx: CheckContext, door: str, tags, wall, header, floor) -> Finding:
    """TJ-8000 p.5: a rim board joint stands at least 12" beyond the opening. A joint is where
    two edge rims on the band line meet (the floors' seam), within 24" of the opening."""
    _u, along, across = _frame(wall.axis)
    band = sum(across(p.p0) for p in header.plies) / len(header.plies)
    ends = []
    z0 = min(p.z0_m for p in header.plies)
    for other in ctx.model.floors:
        for m in other.members:
            if (m.child_key.startswith("edge-rim-") and abs(m.z0_m - z0) < 1.5 * _IN
                    and abs(across(m.p0) - band) < 3 * _IN
                    and abs(across(m.p0) - across(m.p1)) < 1e-6):
                ends += [(along(m.p0), other.tag, m.child_key), (along(m.p1), other.tag,
                                                                  m.child_key)]
    joints = []
    for i, (s, ftag, key) in enumerate(ends):
        if any(abs(s - t) < 2 * _IN and (ftag, key) != (f2, k2)
               for j, (t, f2, k2) in enumerate(ends) if j != i):
            d = ((header.ro_lo - s) if s <= header.ro_lo else (s - header.ro_hi)) / _IN
            if abs(d) < 24.0 and s not in [x for x, _ in joints]:
                joints.append((s, d))
    if not joints:
        return passed(_ID, f"{door} rim joints: none within 24\" of the opening", tags,
                      code=_CODE)
    near = min(joints, key=lambda j: j[1])
    if near[1] >= _JOINT_MIN_IN - 1e-6:
        return passed(_ID, f"{door} rim joint {near[1]:.2f}\" from the opening, at least "
                           f"{_JOINT_MIN_IN:g}\" (TJ-8000 p.5)", tags, code=_CODE)
    return unknown(
        _ID, f"{door} rim joint: the floors' seam puts two edge rims' ends {near[1]:.2f}\" "
             f"from the opening's jamb (outside the pack), under TJ-8000 p.5's {_JOINT_MIN_IN:g}\" "
             f"for a rim header; the header ply stops at the floor outline too, so nothing "
             f"bridges it", tags, code=_CODE,
        fix="move the seam, or have Weyerhaeuser confirm the splice (ForteWEB models one piece)")


def _one(ctx: CheckContext, door) -> list[Finding]:
    tags = (door.tag, door.header_in_band)
    header = band_header(ctx.model, door.tag)
    if isinstance(header, str):
        return [unknown(_ID, header, tags, code=_CODE)]
    wall = ctx.model.wall(header.wall)
    floor = next(f for f in ctx.model.floors if f.tag == header.floor)
    tags += (header.wall,)
    rim = bh.edge_rim(floor, wall, header)
    section = cross_section(rim.profile) if rim is not None else None
    stock = {p.profile for p in header.plies}
    if (rim is None or len(header.plies) != 1 or stock != {rim.profile}
            or abs(section.width_m / _IN - bh.RIM_THICKNESS_IN) > 1e-3
            or abs(section.depth_m / _IN - bh.RIM_DEPTH_IN) > 1e-3):
        return [unknown(
            _ID, f"{door.tag}: the header is not the floor's 1 1/4\" x 11 7/8\" LSL edge rim "
                 f"and one ply of the same stock, the rows TJ-8000 p.7 publishes", tags,
            code=_CODE)]
    out: list[Finding] = []
    inside, seated = seats.loads_on_band(ctx, wall, header)
    if inside:
        return [unknown(_ID, f"{door.tag}: {', '.join(inside)} stand on the band inside the "
                             f"clear span; a published header row is uniform load only", tags,
                        code=_CODE)]
    clear_in = (header.ro_hi - header.ro_lo) / _IN
    bearing_lo, bearing_hi = (header.ro_lo - header.pack_lo) / _IN, (
        header.pack_hi - header.ro_hi) / _IN
    span_in = clear_in + (bearing_lo + bearing_hi) / 2.0
    if min(bearing_lo, bearing_hi) < 4.5 - 1e-6:
        return [unknown(_ID, f"{door.tag}: {min(bearing_lo, bearing_hi):.2f}\" of end bearing, "
                             f"under TJ-8000 p.6's 4 1/2\"", tags, code=_CODE)]
    trib_ft, strip = bh.strip_plf(floor, wall, header)
    seat_loads = bh.seat_loads(ctx, header, wall)
    points = [(bearing_lo / 2.0 + s.offset_in if i % 2 == 0
               else span_in - bearing_hi / 2.0 - s.offset_in, s.lb)
              for i, s in enumerate(seat_loads)]
    shear, moment, delta = bh.equivalent_uniform_plf(strip, span_in, points)
    equivalent = max(shear, moment, delta)
    row = bh.two_ply_row(span_in / 12.0)
    if row is None:
        return [unknown(_ID, f"{door.tag}: {span_in / 12:.2f} ft c-c is past TJ-8000 p.7's "
                             f"published spans", tags, code=_CODE)]
    note = (f"{trib_ft * 12:.2f}\" of floor, {strip:.2f} plf; "
            + (f"{len(points)} seat loads of {', '.join(f'{p:,.1f}' for _x, p in points)} lb "
               f"=> equivalent uniform {shear:.1f} (shear) / {moment:.1f} (moment) / "
               f"{delta:.1f} (deflection) plf" if points else "no seat loads"))
    out.append(_joint_finding(ctx, door.tag, tags, wall, header, floor))
    out.append(_finding(door.tag, tags, f"2-ply 1 1/4\" LSL rim header over {clear_in:.2f}\" "
                                        f"({span_in / 12:.3f} ft c-c, the {row[0]:g} ft row)",
                        [LimitState("header, total load", equivalent, row[1], "plf",
                                    f"{bh.TJ8000} p.7: {row[0]:g} ft, 1 1/4\" 1.3E LSL 11 7/8\"")],
                        note))
    fastening, missing = seats.fastening_states(ctx, header, header.floor, seat_loads)
    top = [s for s in fastening if s.is_detailing]
    side = [s for s in fastening if not s.is_detailing]
    out.append(_finding(door.tag, tags, "ply fastening", top) if top else
               unknown(_ID, f"{door.tag}: {'; '.join(missing)}", tags, code=_CODE))
    intro = side + seats.seat_screw_state(seat_loads)
    if seat_loads and intro:
        out.append(_finding(door.tag, tags, "seat load introduction", intro))
    _u, along, across = _frame(wall.axis)
    (ux, uy) = _u
    x0, y0 = wall.axis[0]
    end_reaction = max(0.0, strip * span_in / 12.0 / 2.0 + sum(p for _x, p in points) / 2.0)
    jamb, _inputs, jamb_missing, _notes = seats.jamb_states(
        ctx, header, wall, floor, seated, end_reaction, along,
        lambda s: (x0 + ux * s, y0 + uy * s))
    studs, stud_missing = seats.stud_states(ctx, header, wall, clear_in / 12.0)
    if jamb_missing or stud_missing:
        needs = "; ".join(jamb_missing + stud_missing)
        out.append(unknown(_ID, f"{door.tag}: jamb bearing needs {needs}", tags, code=_CODE))
    else:
        out.append(_finding(door.tag, tags, "jamb bearing, band to foundation", [*jamb, *studs]))
    return out


@check(Tier.STRUCTURAL, _ID)
def rim_header(ctx: CheckContext) -> list[Finding]:
    doors = band_header_doors(ctx.plan)
    if not doors:
        return [not_applicable(_ID, f"no opening names a floor band as its header, of "
                                    f"{len(ctx.model.openings)} openings examined", code=_CODE)]
    return [f for door in doors for f in _one(ctx, door)]
