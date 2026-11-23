"""The rim header's fastening, seats and jamb bearing (``structural.rim_header``).

Separate grades, each a table read or stated arithmetic (``band_header`` carries the header):

* **Ply fastening**, TJ-8000 (March 2025) p.7, 1 1/4" plies, 10d (0.128-0.131" x 3"), 3 rows at
  12" o.c. from one face: TOP load for the floor over the header, and SIDE load (560 plf on
  either outside member) for what a door seat puts on the rim's face.
* **Seat load introduction**: each seat's reaction over its own length against the side row,
  and the screws' own combined-load grade (the door's placement record, NDS 12.4.1).
* **Jamb bearing** from the band down to the foundation (NDS §3.10.2 Fc-perp, SPF 425 psi, C_b
  1.0): the stacked pack on the plate above, that plate on the rim and its ply, the rim and ply
  on the host plates, the rim's TJ-8000 p.5 vertical rows under the pack (rim alone, the ply
  behind not credited), and the pack's own studs on the plate under them.
* **IRC R602.7.5**: full-height studs at each end of the header, and a jack stud each end.

Oracle: ``houses/catlin/notes/sunken_door_band_header.md`` §4-§6.
"""

from __future__ import annotations

from typehaus.engineering.band_header import RIM_DEPTH_IN, RIM_THICKNESS_IN, SeatLoad
from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.jamb_takedown import GABLE_ROOF_STRIP_FT, WALL_DEAD_PSF, seat_takedown
from typehaus.library.rim_boards import MIN_BEARING_IN, TJ8000, rim_board
from typehaus.resolve.band_headers import _frame
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import EDGE_RIM_PREFIX

_IN = 0.0254
#: Sawn plates (SPF), dry: NDS Supplement Table 4A; TJ-9000's own bearing tables use it too.
SAWN_FC_PERP_PSI = 425.0
#: TJ-8000 p.5 note 2: the rim's vertical load capacity is limited to 360 psi (ASTM D7672).
RIM_BEARING_PSI = 360.0
_NDS = "AWC NDS 2018 §3.10.2"
_VERTICALS = ("stud", "king", "jack", "cripple")
_STUD_REACH_M = 2.75 * _IN
#: TJ-8000 p.7, 2-ply connection: (1 1/4" plies, 10d) top load rows and o.c.; side load plf by rows.
TOP_ROWS, TOP_SPACING_IN = 3, 12.0
SIDE_PLF = {2: 370.0, 3: 560.0}
_R602_7_5 = ((6.0, 2, 1),)  # (header span ft, full-height studs: <140 mph Exp B, <=115 mph Exp B)


def loads_on_band(ctx, wall, header):
    """``(inside, seated)``: members of walls standing on the band, inside the clear span or on
    a seat (a seat's load bypasses the span)."""
    _u, along, across = _frame(wall.axis)
    faces = [across(p.p0) + s * cross_section(p.profile).width_m / 2 for p in header.plies
             for s in (-1, 1)]
    lo, hi = min(faces) - _STUD_REACH_M, max(faces) + _STUD_REACH_M
    top = max(p.z1_m for p in header.plies)
    inside, seated = [], []
    for other in ctx.model.walls:
        if other.is_foundation or abs(other.frame_base_z_m - top) > 2 * _IN:
            continue
        for member in other.members:
            if (member.category not in _VERTICALS or not lo <= across(member.p0) <= hi
                    or member.z0_m > other.frame_base_z_m + 2 * _IN):
                continue
            station = along(member.p0)
            if header.ro_lo + 1e-4 < station < header.ro_hi - 1e-4:
                inside.append(f"{other.tag}:{member.child_key}")
            elif header.pack_lo - 1e-4 <= station <= header.pack_hi + 1e-4:
                seated.append(f"{other.tag}:{member.child_key}")
    return inside, seated


def fastening_states(ctx, header, floor_tag, seats: list[SeatLoad]) -> tuple[list, list[str]]:
    """``(states, missing)``: the ply fastening, top and side, and the seat's nailing share."""
    spec = next((f for f in ctx.plan.all_elements() if getattr(f, "tag", None) == floor_tag),
                None)
    fastening = next((r.fastening for r in getattr(spec, "reinforcements", ()) or ()
                      if r.fastening is not None and r.member and "rim" in r.member), None)
    if fastening is None or fastening.fastener != "10d":
        return [], [f"the plies' 10d fastening per {TJ8000} p.7 (1 1/4\" plies)"]
    states = [
        LimitState("ply fastening rows", TOP_ROWS, fastening.rows, "rows",
                   f"{TJ8000} p.7, top load, 1 1/4\" plies: 10d in {TOP_ROWS} rows, one face",
                   is_detailing=True),
        LimitState("ply fastening spacing", fastening.spacing.meters / _IN, TOP_SPACING_IN,
                   "in o.c.", f"{TJ8000} p.7: {TOP_SPACING_IN:g}\" o.c. maximum",
                   is_detailing=True)]
    side = SIDE_PLF.get(fastening.rows)
    if side and seats:
        worst = max(seats, key=lambda s: s.lb)
        states.append(LimitState(
            "seat load into the ply, nailing (side load)", worst.lb / (worst.nailing_in / 12.0),
            side, "plf", f"{TJ8000} p.7, side load, 10d, {fastening.rows} rows: {side:g} plf on "
                         f"either outside member; the whole seat reaction over its "
                         f"{worst.nailing_in:g}\" is taken as reaching the ply"))
    return states, []


def seat_screw_state(seats: list[SeatLoad]) -> list:
    """The door's own combined lateral + withdrawal grade at its seat screws, read not redone."""
    rot = [s.rotation_dcr for s in seats if s.rotation_dcr is not None]
    if not rot:
        return []
    return [LimitState("seat screws, combined lateral and withdrawal", max(rot), 1.0, "d/c",
                       "the door's placement record (notes/exterior_door_sill_beam.md §3, "
                       "NDS 12.4.1, ESR-1078 §4.1.6)")]


def stud_states(ctx, header, wall, span_ft: float) -> tuple[list, list[str]]:
    """IRC R602.7.5: the full-height studs each end, and the jack(s) holding the header."""
    from typehaus import wind

    basis = wind.wind_basis(ctx.plan.project.site)
    if basis is None:
        return [], ["the site's ultimate design wind speed and exposure for IRC Table R602.7.5"]
    row = next((r for r in _R602_7_5 if r[0] >= span_ft - 1e-9), None)
    if row is None:
        return [], [f"IRC Table R602.7.5 past {_R602_7_5[-1][0]:g} ft"]
    mild = basis.speed_mph <= 115 and str(basis.exposure).upper().startswith("B")
    need = row[2] if mild else row[1]
    _u, along, _across = _frame(wall.axis)
    states = []
    for name, lo, hi in (("west", header.pack_lo, header.ro_lo), ("east", header.ro_hi,
                                                                  header.pack_hi)):
        kings = jacks = 0
        for m in wall.members:
            if m.opening_tag == header.door and lo - 1e-4 <= along(m.p0) <= hi + 1e-4:
                kings += m.category == "king"
                jacks += m.category == "jack"
        states += [
            LimitState(f"full-height studs, {name} end", need, kings, "studs",
                       f"IRC R602.7.5, Table R602.7.5: {need} at {basis.speed_mph:g} mph "
                       f"Exposure {basis.exposure}, header span up to {row[0]:g} ft",
                       is_detailing=True),
            LimitState(f"jack stud holding the header, {name} end", 1, jacks, "studs",
                       "IRC R602.7.5: one or more jack studs", is_detailing=True)]
    return states, []


def jamb_states(ctx, header, wall, floor, seated, end_reaction_lb, along, frame):
    """``(states, inputs, missing, notes)`` for the stacked jamb under the heavier seat."""
    states, inputs, missing, notes = [], [], [], []
    if not seated:
        return states, inputs, missing, ["no framing above stands on the seats"]
    seated_wall = ctx.model.wall(seated[0].split(":")[0])
    king = next(m for m in seated_wall.members if m.child_key == seated[0].split(":")[1])
    wall_depth = cross_section(king.profile).depth_m
    band_in = (len(header.plies) + 1) * RIM_THICKNESS_IN
    best = None
    for lo, hi, outer in ((header.pack_lo, header.ro_lo, header.pack_lo),
                          (header.ro_hi, header.pack_hi, header.pack_hi)):
        trib = (header.ro_hi - header.ro_lo) / 2 + (hi - lo)
        terms, crossings = seat_takedown(ctx.plan, ctx.model, seated_wall,
                                         _project(seated_wall, frame(outer)), along,
                                         (lo, hi), trib)
        total = sum(t.lb for t in terms)
        if best is None or total > best[0]:
            best = (total, hi - lo, terms, crossings, trib)
    total, seat, terms, crossings, trib = best
    seat_in = seat / _IN
    cap = min(SAWN_FC_PERP_PSI, RIM_BEARING_PSI)
    below = total + end_reaction_lb
    rim = rim_board(RIM_THICKNESS_IN, RIM_DEPTH_IN)
    states += [
        LimitState("bearing, jamb pack on the wall plate above",
                   total / (seat_in * wall_depth / _IN), SAWN_FC_PERP_PSI, "psi",
                   f"{_NDS}: Fc-perp {SAWN_FC_PERP_PSI:.0f} psi SPF plate, C_b 1.0"),
        LimitState("bearing, wall plate on the rim and its ply", total / (seat_in * band_in),
                   cap, "psi", f"{_NDS}: the plate ({SAWN_FC_PERP_PSI:.0f} psi) and "
                               f"{TJ8000} p.5 ({RIM_BEARING_PSI:.0f} psi, D7672) govern"),
        LimitState("bearing, rim and ply on the host wall's plates", below / (seat_in * band_in),
                   cap, "psi", f"{_NDS}; {TJ8000} p.5 note 2: {cap:.0f} psi")]
    if rim is not None and seat_in >= MIN_BEARING_IN - 1e-6:
        states += [
            LimitState("rim, concentrated vertical load under the pack", total,
                       rim.concentrated_lb, "lb", rim.source),
            LimitState("rim, vertical load under the pack", total / (seat_in / 12.0),
                       rim.vertical_plf, "plf",
                       rim.source + "; the ply behind is not credited")]
    else:
        missing.append(f"a published vertical capacity for the rim under a {seat_in:.2f}\" pack "
                       f"({TJ8000} p.5 wants {MIN_BEARING_IN:g}\" of bearing)")
    packs = sum(1 for m in wall.members if m.opening_tag == header.door
                and m.category in ("king", "jack")
                and header.pack_lo - 1e-4 <= along_of(wall, m) <= header.ro_lo + 1e-4)
    if packs:
        states.append(LimitState(
            "bearing, jamb pack studs on the plate under them", below
            / (packs * 1.5 * (wall_depth / _IN)), SAWN_FC_PERP_PSI, "psi",
            f"{_NDS}: {packs} studs of {wall_depth / _IN:g}\" x 1 1/2\" on the plate, "
            f"Fc-perp {SAWN_FC_PERP_PSI:.0f} psi, C_b 1.0 (the PT sill is taken at SPF's value)"))
    for crossing in crossings:
        if crossing.solid_width_m <= 0:
            missing.append(f"squash blocks under the stacked jamb packs in {crossing.floor}")
            continue
        area = seat_in * min(crossing.solid_width_m, wall_depth) / _IN
        rims = [m for m in crossing.members if m.startswith(EDGE_RIM_PREFIX)]
        states.append(LimitState(
            f"bearing, upper jamb pack on {crossing.floor}'s "
            f"{'edge rim' if rims else 'squash plies'}", crossing.above_lb / area,
            SAWN_FC_PERP_PSI, "psi", f"{_NDS}: the SPF plate on {', '.join(crossing.members)}"))
        row = rim_board(RIM_THICKNESS_IN, RIM_DEPTH_IN) if rims else None
        if rims and row is not None and seat_in >= MIN_BEARING_IN - 1e-6:
            states += [
                LimitState(f"{crossing.floor}'s edge rim, concentrated vertical load",
                           crossing.above_lb, row.concentrated_lb, "lb", row.source),
                LimitState(f"{crossing.floor}'s edge rim, vertical load under the pack",
                           crossing.above_lb / (seat_in / 12.0), row.vertical_plf, "plf",
                           row.source)]
    inputs += [Quantity("wall_dead", WALL_DEAD_PSF, "psf", 0.1),
               Quantity("gable_roof_strip", GABLE_ROOF_STRIP_FT, "ft", 0.01),
               Quantity("jamb_tributary", trib / _IN, "in", 0.01),
               Quantity("seat_load", total, "lb", 1.0)]
    notes.append("stacked jamb takedown on the governing seat: "
                 + "; ".join(f"{t.label} {t.lb:,.1f} lb" for t in terms))
    return states, inputs, missing, notes


def along_of(wall, member) -> float:
    _u, along, _across = _frame(wall.axis)
    return along(member.p0)


def _project(wall, point):
    (x0, y0), (x1, y1) = wall.axis
    dx, dy = x1 - x0, y1 - y0
    t = ((point[0] - x0) * dx + (point[1] - y0) * dy) / ((dx * dx + dy * dy) or 1.0)
    return (x0 + t * dx, y0 + t * dy)
