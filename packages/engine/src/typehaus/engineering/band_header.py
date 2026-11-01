"""A flush LVL header in a floor band over a wall opening — ``band_header/<Door tag>``.

``Door.header_in_band`` hands an opening's header to the floor above it: the host wall frames
none, and the floor's ``JoistReinforcement`` plies (``resolve/band_headers.py``) are the beam,
seated on the jamb packs through the plates. catlin's D-B-PATIO is the case: W-B-S3-FR bears
FS-M-EAST's edge line but runs PARALLEL to its joists (geometry review C3-E2).

**What loads it, from the model.** The floor strip the edge line carries — half the way to
the next joist line plus any deck outboard of it — at IRC R301.5's 40 + 10 psf, and the plies'
own weight (TJ-9000 p.4). Every stud, king, jack or cripple of a wall standing on the band is
located: inside the clear span it is a concentrated load this engine cannot take down, and the
record goes INCOMPLETE naming it; on a seat it bypasses the span and is listed, not graded.

**Capacity** is the maker's own: Weyerhaeuser TJ-9000 (July 2026) p.5 Microllam LVL 2.0E —
Fb 2,600 psi at 12" x (12/d)^0.136, Fv 285 psi, E 2.0e6 psi, 100% duration (floor live) — and
its p.5 deflection equation with the shear term, at IRC Table R301.7's L/360 live.

**Not graded here:** bearing (Fc_perp) under the stacked jamb loads at the seats, the ply
connection, and lateral support (the subfloor sheathes the top edge). Oracle:
``houses/catlin/notes/patio_band_header.md``.
"""

from __future__ import annotations

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.loads import FLOOR_DEAD_LOAD_PSF, FLOOR_LIVE_LOAD_PSF
from typehaus.resolve.band_headers import _frame, band_header, band_header_doors
from typehaus.resolve.framing.profiles import cross_section

KIND = "band_header"
BASIS_VERSION = "1"
BASIS = ("AWC NDS 2018 §3.3-3.4 on Weyerhaeuser TJ-9000 (July 2026) p.5 Microllam LVL 2.0E "
         "design stresses; IRC R301.5 floor loads, Table R301.7 L/360")
_SOURCE = "Weyerhaeuser TJ-9000 Specifier's Guide (July 2026)"

_IN = 0.0254
_FT = 0.3048
#: TJ-9000 p.5, Microllam LVL 2.0E beam orientation, 100% load duration.
_FB_PSI = 2600.0
_FV_PSI = 285.0
_E_PSI = 2.0e6
_FB_DEPTH_EXP = 0.136
_PLY_WIDTH_IN = 1.75
#: TJ-9000 p.4 "Weight (plf)" of one 1 3/4" Microllam ply, by depth (in).
_PLY_PLF = {5.5: 2.8, 7.25: 3.7, 9.25: 4.7, 9.5: 4.8, 11.25: 5.7, 11.875: 6.1, 14.0: 7.1,
            16.0: 8.2, 18.0: 9.2, 20.0: 10.2}
_DEFLECTION_DENOMINATOR = 360.0
_VERTICALS = ("stud", "king", "jack", "cripple")
#: Half a 2x6's depth: a stud this far across from a ply face still bears on it.
_STUD_REACH_M = 2.75 * _IN


def _incomplete(door: str, tags, missing: str, summary: str) -> EngineeringRecord:
    return EngineeringRecord(
        item_id=item_id(KIND, door), kind=KIND, key=door, basis_version=BASIS_VERSION,
        basis=BASIS, status=Status.INCOMPLETE, summary=summary, element_tags=tags,
        missing=(missing,))


def _tributary_m(floor, wall, plies) -> float:
    """Floor strip the band line carries: half-way to the next line + deck outboard of it."""
    _u, along, across = _frame(wall.axis)
    band = sum(across(p.p0) for p in plies) / len(plies)
    lines = sorted({round(across(m.p0), 6) for m in floor.members if m.category == "joist"
                    and abs(across(m.p0) - across(m.p1)) < 1e-6})
    host = min(lines, key=lambda line: abs(line - band))
    inboard = 1.0 if band >= host else -1.0
    others = [line for line in lines if (line - host) * inboard > 1e-6]
    half = abs(min(others, key=lambda line: abs(line - host)) - host) / 2.0 if others else 0.0
    edge = [across(p) for p in floor.deck_outline]
    outboard = max(0.0, (host - min(edge)) if inboard > 0 else (max(edge) - host)) if edge else 0.0
    return half + outboard


def _loads_on_band(ctx, floor, wall, header, plies):
    """(members inside the clear span, members on a seat) of walls standing on the band."""
    _u, along, across = _frame(wall.axis)
    faces = [across(p.p0) + s * cross_section(p.profile).width_m / 2 for p in plies
             for s in (-1, 1)]
    lo, hi = min(faces) - _STUD_REACH_M, max(faces) + _STUD_REACH_M
    top = max(p.z1_m for p in plies)
    inside, seated = [], []
    for other in ctx.model.walls:
        if other.is_foundation or abs(other.frame_base_z_m - top) > 2 * _IN:
            continue
        for member in other.members:
            if (member.category not in _VERTICALS or not lo <= across(member.p0) <= hi
                    or member.z0_m > other.frame_base_z_m + 2 * _IN):
                continue  # not a member standing on this wall's bottom plate
            station = along(member.p0)
            if header.ro_lo + 1e-4 < station < header.ro_hi - 1e-4:
                inside.append(f"{other.tag}:{member.child_key}")
            elif header.pack_lo - 1e-4 <= station <= header.pack_hi + 1e-4:
                seated.append(f"{other.tag}:{member.child_key}")
    return inside, seated


def _one(ctx: EngineeringContext, door) -> EngineeringRecord:
    header = band_header(ctx.model, door.tag)
    tags = (door.tag, door.header_in_band)
    if isinstance(header, str):
        return _incomplete(door.tag, tags, "a band reinforcement covering the opening", header)
    wall = ctx.model.wall(header.wall)
    floor = next(f for f in ctx.model.floors if f.tag == header.floor)
    sections = {(round(cross_section(p.profile).width_m / _IN, 3),
                 round(cross_section(p.profile).depth_m / _IN, 3)) for p in header.plies}
    width_in, depth_in = next(iter(sections))
    ply_plf = _PLY_PLF.get(depth_in)
    if (len(sections) != 1 or abs(width_in - _PLY_WIDTH_IN) > 1e-3 or ply_plf is None
            or not all("LVL" in p.profile for p in header.plies)):
        return _incomplete(door.tag, tags, "published design values for the band's section",
                           f"{door.tag}: the band plies are {sorted(sections)}, not a "
                           "1 3/4\" Microllam LVL depth TJ-9000 tabulates")
    inside, seated = _loads_on_band(ctx, floor, wall, header, header.plies)
    if inside:
        return _incomplete(door.tag, tags + tuple(sorted({s.split(':')[0] for s in inside})),
                           "a load takedown for the framing standing inside the span",
                           f"{door.tag}: {', '.join(inside)} stand on the band inside the "
                           "clear span; their load is not derivable here")

    plies = len(header.plies)
    clear_ft = (header.ro_hi - header.ro_lo) / _FT
    seat_lo_in = (header.ro_lo - header.pack_lo) / _IN
    seat_hi_in = (header.pack_hi - header.ro_hi) / _IN
    span_ft = clear_ft + (seat_lo_in + seat_hi_in) / 2.0 / 12.0  # seat centre to seat centre
    trib_ft = _tributary_m(floor, wall, header.plies) / _FT
    w_live = FLOOR_LIVE_LOAD_PSF * trib_ft
    w_total = (FLOOR_LIVE_LOAD_PSF + FLOOR_DEAD_LOAD_PSF) * trib_ft + plies * ply_plf
    b = plies * width_in
    fb = _FB_PSI * (12.0 / depth_in) ** _FB_DEPTH_EXP
    moment = w_total * span_ft ** 2 / 8.0
    moment_cap = fb * b * depth_in ** 2 / 6.0 / 12.0
    shear = w_total * span_ft / 2.0
    shear_cap = 2.0 / 3.0 * _FV_PSI * b * depth_in
    deflection = (270.0 * w_live * span_ft ** 4 / (_E_PSI * b * depth_in ** 3)
                  + 28.8 * w_live * span_ft ** 2 / (_E_PSI * b * depth_in))
    limit = span_ft * 12.0 / _DEFLECTION_DENOMINATOR
    states = (
        LimitState(name="bending", demand=moment, capacity=moment_cap, unit="lb-ft",
                   citation=f"{_SOURCE} p.5: Fb {_FB_PSI:,.0f} psi x (12/d)^0.136, C_D 1.0"),
        LimitState(name="shear", demand=shear, capacity=shear_cap, unit="lb",
                   citation=f"{_SOURCE} p.5: Fv {_FV_PSI:.0f} psi, V = 2/3 Fv b d"),
        LimitState(name="deflection", demand=deflection, capacity=limit, unit="in",
                   citation=(f"IRC Table R301.7 L/{_DEFLECTION_DENOMINATOR:.0f} live; "
                             f"{_SOURCE} p.5 bending + shear deflection, E {_E_PSI:,.0f}")),
    )
    governing = max(states, key=lambda state: state.ratio)
    return EngineeringRecord(
        item_id=item_id(KIND, door.tag), kind=KIND, key=door.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OK if governing.ratio <= 1.0 else Status.OVER,
        summary=(f"{door.tag}: {plies}-ply {width_in:g}x{depth_in:g} LVL in {header.floor}'s "
                 f"band over {clear_ft:.2f} ft clear ({span_ft:.2f} ft seat to seat), "
                 f"{trib_ft * 12:.1f}\" of floor — d/c {governing.ratio:.3f} on "
                 f"{governing.name}"),
        inputs=(
            Quantity("plies", float(plies), "plies", 1.0),
            Quantity("ply_width", width_in, "in", 0.001),
            Quantity("ply_depth", depth_in, "in", 0.001),
            Quantity("clear_span", clear_ft, "ft", 0.01),
            Quantity("seat_lo", seat_lo_in, "in", 0.01),
            Quantity("seat_hi", seat_hi_in, "in", 0.01),
            Quantity("tributary", trib_ft, "ft", 0.01),
            Quantity("floor_live", FLOOR_LIVE_LOAD_PSF, "psf", 0.1),
            Quantity("floor_dead", FLOOR_DEAD_LOAD_PSF, "psf", 0.1),
            Quantity("ply_weight", ply_plf, "plf", 0.1),
            Quantity("fb", _FB_PSI, "psi", 1.0),
            Quantity("fv", _FV_PSI, "psi", 1.0),
            Quantity("e", _E_PSI, "psi", 1000.0),
            Quantity("loads_inside_span", 0.0, "members", 1.0),
        ),
        limit_states=states,
        notes=(("framing seated on the packs, bypassing the span: " + ", ".join(seated))
               if seated else "no framing above stands on the seats",),
        element_tags=tags + (header.wall,),
    )


oracled_by(KIND, Oracle(note="patio_band_header.md", section="§3",
                        test="tests/test_band_header.py"))


@keys(KIND)
def enumerate_band_headers(ctx: EngineeringContext) -> list[str]:
    return [door.tag for door in band_header_doors(ctx.plan)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, door) for door in band_header_doors(ctx.plan)]
