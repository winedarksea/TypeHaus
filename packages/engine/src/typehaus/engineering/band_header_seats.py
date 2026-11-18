"""The band header's seats and connections (``band_header``, BASIS_VERSION 2).

The stacked jambs' load is taken down by ``jamb_takedown`` and graded in bearing (NDS
§3.10.2, no C_D) at every interface it crosses; the plies' fastening and the filler to the
I-joist beside them are published reads (Weyerhaeuser TJ-9000 p.30, TJ-4000 p.28); an LSL edge
rim, under a stacked pack or beside the plies over the opening, reads TJ-8000's own rows.
Oracle: ``houses/catlin/notes/sunken_door_band_header.md`` §5.
"""

from __future__ import annotations

from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.jamb_takedown import GABLE_ROOF_STRIP_FT, WALL_DEAD_PSF, seat_takedown
from typehaus.library.rim_boards import MIN_BEARING_IN, TJ8000, header_row, rim_board
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import EDGE_RIM_PREFIX

_IN = 0.0254
#: Sawn plates (SPF), dry: NDS Supplement Table 4A; TJ-9000's own bearing tables use it too.
SAWN_FC_PERP_PSI = 425.0
#: TJ-9000 (July 2026) p.5, 2.0E Microllam beam; not increased for load duration.
LVL_FC_PERP_PSI = 750.0
_NDS = "AWC NDS 2018 §3.10.2"
_TJ9000 = "Weyerhaeuser TJ-9000 (July 2026)"
_TJ4000 = "Weyerhaeuser TJ-4000 (July 2025)"
#: TJ-9000 p.30, multiple-member connections for top-loaded beams, 1 3/4" pieces:
#: plies -> fastener -> (rows, max o.c. in, faces). Nails take one more row at d >= 14".
_TOP_LOADED = {
    2: {"10d": (3, 12.0, "one"), "12d-16d": (2, 12.0, "one"), "screw": (2, 24.0, "one")},
    3: {"10d": (3, 12.0, "both"), "12d-16d": (2, 12.0, "both"), "screw": (2, 24.0, "both")},
}
#: TJ-4000 p.28, filler blocks for the 9 1/2"-11 7/8" and 14"-16" depths: series ->
#: (shallow stock, deep stock); 15 nails (0.131" x 3") for every series listed here.
_FILLER = {"110": ("2x6", "2x8"), "210": ("2x6 + 3/8\" sheathing", "2x8 + 3/8\" sheathing"),
           "230": ("2x6 + 1/2\" sheathing", "2x8 + 1/2\" sheathing"),
           "360": ("2x6 + 1/2\" sheathing", "2x8 + 1/2\" sheathing")}
_FILLER_NAILS = 15


def seat_states(ctx, header, wall, floor, seated, shear_lb, along, frame):
    """``(states, inputs, missing, notes)`` for the seats under the stacked jambs."""
    states, inputs, missing, notes = [], [], [], []
    if not seated:
        return states, inputs, missing, ["no framing above stands on the seats"]
    seated_wall = ctx.model.wall(seated[0].split(":")[0])
    king = next(m for m in seated_wall.members if m.child_key == seated[0].split(":")[1])
    wall_depth = cross_section(king.profile).depth_m
    ply_width = sum(cross_section(p.profile).width_m for p in header.plies)
    seats = ((header.pack_lo, header.ro_lo, header.pack_lo),
             (header.ro_hi, header.pack_hi, header.pack_hi))
    best = None
    for lo, hi, outer in seats:
        point = _project(seated_wall, frame(outer))
        trib = (header.ro_hi - header.ro_lo) / 2 + (hi - lo)
        terms, crossings = seat_takedown(ctx.plan, ctx.model, seated_wall, point, along,
                                         (lo, hi), trib)
        total = sum(t.lb for t in terms)
        if best is None or total > best[0]:
            best = (total, hi - lo, terms, crossings, trib)
    total, seat, terms, crossings, trib = best
    seat_in = seat / _IN
    pack_area = seat_in * wall_depth / _IN
    ply_area = seat_in * ply_width / _IN
    states += [
        LimitState(name="bearing, jamb pack on the wall plate above", demand=total / pack_area,
                   capacity=SAWN_FC_PERP_PSI, unit="psi",
                   citation=f"{_NDS}: Fc-perp {SAWN_FC_PERP_PSI:.0f} psi SPF plate, C_b 1.0"),
        LimitState(name="bearing, wall plate on the plies", demand=total / ply_area,
                   capacity=min(SAWN_FC_PERP_PSI, LVL_FC_PERP_PSI), unit="psi",
                   citation=f"{_NDS}: the plate ({SAWN_FC_PERP_PSI:.0f} psi) governs the "
                            f"plies ({_TJ9000} p.5, {LVL_FC_PERP_PSI:.0f} psi)"),
        LimitState(name="bearing, plies on the seat's plates",
                   demand=(total + shear_lb) / ply_area, capacity=SAWN_FC_PERP_PSI, unit="psi",
                   citation=f"{_NDS}: Fc-perp {SAWN_FC_PERP_PSI:.0f} psi SPF plate, C_b 1.0"),
    ]
    for crossing in crossings:
        if crossing.solid_width_m <= 0:
            missing.append(f"squash blocks under the stacked jamb packs in {crossing.floor} "
                           f"({_TJ4000} p.27 detail CS: a TJI loaded from above)")
            continue
        area = seat_in * min(crossing.solid_width_m, wall_depth) / _IN
        rims = [m for m in crossing.members if m.startswith(EDGE_RIM_PREFIX)]
        solid = "edge rim" if rims else "squash plies"
        states.append(LimitState(
            name=f"bearing, upper jamb pack on {crossing.floor}'s {solid}",
            demand=crossing.above_lb / area, capacity=SAWN_FC_PERP_PSI, unit="psi",
            citation=(f"{_NDS}: the SPF plate on {', '.join(rims)}" if rims else
                      f"{_NDS}; {_TJ4000} p.27 detail CS ({', '.join(crossing.members)})")))
        if rims:
            row = _rim_row(floor_members(ctx, crossing.floor, rims[0]))
            if row is None or seat_in < MIN_BEARING_IN - 1e-6:
                missing.append(f"a published vertical capacity for {crossing.floor}'s edge rim"
                               f" (a {seat_in:.2f}\" pack; {TJ8000} p.5 wants "
                               f"{MIN_BEARING_IN:g}\" of bearing)")
                continue
            states += [
                LimitState(name=f"{crossing.floor}'s edge rim, concentrated vertical load",
                           demand=crossing.above_lb, capacity=row.concentrated_lb, unit="lb",
                           citation=row.source),
                LimitState(name=f"{crossing.floor}'s edge rim, vertical load under the pack",
                           demand=crossing.above_lb / (seat_in / 12.0),
                           capacity=row.vertical_plf, unit="plf", citation=row.source)]
    inputs += [Quantity("wall_dead", WALL_DEAD_PSF, "psf", 0.1),
               Quantity("gable_roof_strip", GABLE_ROOF_STRIP_FT, "ft", 0.01),
               Quantity("jamb_tributary", trib / _IN, "in", 0.01),
               Quantity("seat_load", total, "lb", 1.0),
               Quantity("fc_perp_plate", SAWN_FC_PERP_PSI, "psi", 1.0)]
    notes.append("stacked jamb takedown on the governing seat: "
                 + "; ".join(f"{t.label} {t.lb:,.1f} lb" for t in terms))
    return states, inputs, missing, notes


def connection_states(ctx, header, floor, across, w_total_plf, span_ft):
    """``(states, missing)``: the ply fastening and the filler (or the edge rim beside the
    plies, over the opening as a 1-ply header on the whole strip), read against the maker."""
    states, missing = [], []
    reinforcement = _authored(ctx, header)
    plies = len(header.plies)
    depth_in = cross_section(header.plies[0].profile).depth_m / _IN
    row = _TOP_LOADED.get(plies, {})
    fastening = reinforcement.fastening if reinforcement else None
    if fastening is None or fastening.fastener not in row:
        missing.append(f"the plies' fastening per {_TJ9000} p.30 (top-loaded)")
    else:
        rows, spacing, faces = row[fastening.fastener]
        rows += 1 if depth_in >= 14 and fastening.fastener != "screw" else 0
        provided = fastening.rows * (1.0 if faces == "one" or fastening.faces == "both" else 0.5)
        states += [
            LimitState(name="ply fastening rows", demand=rows, capacity=provided, unit="rows",
                       citation=f"{_TJ9000} p.30: {plies} plies of 1 3/4\", "
                                f"{fastening.fastener} in {rows} rows, {faces} face",
                       is_detailing=True),
            LimitState(name="ply fastening spacing", demand=fastening.spacing.meters / _IN,
                       capacity=spacing, unit="in o.c.",
                       citation=f"{_TJ9000} p.30: {spacing:g}\" o.c. maximum",
                       is_detailing=True)]
    rim = _edge_rim_beside(floor, header, across)
    if rim is not None:
        row = _rim_row(rim)
        seat_in = min(header.ro_lo - header.pack_lo, header.pack_hi - header.ro_hi) / _IN
        read = header_row(row, span_ft) if row is not None else None
        if read is None or seat_in < MIN_BEARING_IN - 1e-6:
            missing.append(f"a {TJ8000} header row for {rim.profile} over {span_ft:.2f} ft "
                           f"on {MIN_BEARING_IN:g}\" seats")
        else:
            states.append(LimitState(
                name="edge rim over the opening, 1-ply header", demand=w_total_plf,
                capacity=read[1], unit="plf",
                citation=f"{row.source}: the {read[0]:g} ft row (c-c of bearing), uniform "
                         "load only"))
    beside = _ijoist_beside(floor, header, across)
    if beside is not None:
        series = beside.profile.split("TJI")[-1].strip()
        stocks = _FILLER.get(series)
        want = stocks[0 if cross_section(beside.profile).depth_m / _IN <= 11.875 + 1e-6
                      else 1] if stocks else None
        filler = reinforcement.filler if reinforcement else None
        if want is None or filler is None or filler.stock != want:
            missing.append(f"the filler to {beside.profile} beside the plies per {_TJ4000} "
                           f"p.28 ({want or 'no published row'})")
        else:
            states.append(LimitState(
                name="filler block nails", demand=_FILLER_NAILS, capacity=filler.nails,
                unit="nails", citation=f"{_TJ4000} p.28: {want}, ({_FILLER_NAILS}) "
                                       "0.131\" x 3\"", is_detailing=True))
    return states, missing


def _authored(ctx, header):
    spec = next((f for f in ctx.plan.all_elements() if getattr(f, "tag", None) == header.floor),
                None)
    for reinforcement in getattr(spec, "reinforcements", ()) or ():
        if reinforcement.fastening is not None or reinforcement.filler is not None:
            return reinforcement
    return None


def _ijoist_beside(floor, header, across):
    faces = [across(p.p0) for p in header.plies]
    for member in floor.members:
        if member.category == "joist" and "TJI" in member.profile and \
                min(abs(across(member.p0) - f) for f in faces) < 3 * _IN and \
                abs(across(member.p0) - across(member.p1)) < 1e-6:
            return member
    return None


def _edge_rim_beside(floor, header, across):
    faces = [across(p.p0) for p in header.plies]
    for member in floor.members:
        if member.child_key.startswith(EDGE_RIM_PREFIX) and \
                min(abs(across(member.p0) - f) for f in faces) < 3 * _IN:
            return member
    return None


def _rim_row(member):
    section = cross_section(member.profile)
    return rim_board(section.width_m / _IN, section.depth_m / _IN)


def floor_members(ctx, floor_tag, key):
    floor = next(f for f in ctx.model.floors if f.tag == floor_tag)
    return next(m for m in floor.members if m.child_key == key)


def _project(wall, point):
    (x0, y0), (x1, y1) = wall.axis
    dx, dy = x1 - x0, y1 - y0
    t = ((point[0] - x0) * dx + (point[1] - y0) * dy) / ((dx * dx + dy * dy) or 1.0)
    return (x0 + t * dx, y0 + t * dy)
