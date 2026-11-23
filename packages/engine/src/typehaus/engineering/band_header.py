"""The rim header over a band opening (``Door.header_in_band``): loads and its published reads.

A 2-ply LSL rim board over D-B-SUNKEN (decision 12): the floor's edge rim plus one ply of the
same stock behind it, read as a PUBLISHED header, so it is not an engineering kind and registers
nothing (``band_header/<door>`` retired with the LVL plies). ``structural.rim_header`` formats
the rows; the arithmetic is here, the oracle is
``houses/catlin/notes/sunken_door_band_header.md`` §2-§6.

**Four separate grades** (a published table assumes uniform load and says nothing of the rest):
the header itself (Weyerhaeuser TJ-8000, March 2025, p.7 2-ply row, read at the next published
span at or past the span c-c of bearing); the plies' fastening (p.7, top and side load); the seat
load introduction (each door seat's eccentric reaction against the nailing and the screws' own
record); and the jamb bearing from the band down to the foundation (``band_header_seats``).

**What loads it.** The floor strip the edge line carries at IRC R301.5's 40 + 10 psf (TJ-8000
p.6: neglect the header's own weight), and the sill beam's seat reactions where the opening
above is a door whose girt sill beam bears on this rim, as concentrated loads at their screw
groups from that door's own placement record, BOTH seats at the worst reaction at once. Point
loads are not in the table, so they are carried as the uniform load with the same end shear,
midspan moment and midspan deflection (the largest of the three); the retained ForteWEB input
(``notes/engineering_review_2026-11-22/forteweb_D-B-SUNKEN.md``) closes the table's
uniform-load condition.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.loads import FLOOR_DEAD_LOAD_PSF, FLOOR_LIVE_LOAD_PSF
from typehaus.resolve.band_headers import _frame
from typehaus.resolve.geometry import opening_center
from typehaus.resolve.model import EDGE_RIM_PREFIX, on_joist_line

_IN = 0.0254
_FT = 0.3048
TJ8000 = "Weyerhaeuser Trus Joist Rim Board Specifier's Guide TJ-8000 (March 2025)"
#: TJ-8000 p.7, 2-ply 1 1/4" 1.3E TimberStrand LSL 11 7/8", floor 100%, total load (plf) by
#: clear span (ft); the live-load row never governs ("*" in every row at these spans).
TWO_PLY_1_25_11_875 = ((3.0, 3175.0), (3.5, 2720.0), (4.0, 2378.0), (4.5, 2113.0),
                       (5.0, 1900.0), (5.5, 1726.0), (6.0, 1582.0), (6.5, 1459.0),
                       (7.0, 1351.0), (7.5, 1176.0), (8.0, 1032.0))
RIM_THICKNESS_IN = 1.25
RIM_DEPTH_IN = 11.875


@dataclass(frozen=True)
class SeatLoad:
    """One door seat's reaction on the rim: ``offset_in`` from the opening's near edge to the
    screw group's centroid, ``nailing_in`` the seat's length along the rim."""

    offset_in: float
    lb: float
    eccentricity_in: float
    nailing_in: float
    door: str
    rotation_dcr: float | None


def tributary_m(floor, wall, plies) -> float:
    """Floor strip the band line carries: half-way to the next line + deck outboard of it."""
    _u, _along, across = _frame(wall.axis)
    band = sum(across(p.p0) for p in plies) / len(plies)
    lines = sorted({round(across(m.p0), 6) for m in floor.members if on_joist_line(m)
                    and abs(across(m.p0) - across(m.p1)) < 1e-6})
    host = min(lines, key=lambda line: abs(line - band))
    inboard = 1.0 if band >= host else -1.0
    others = [line for line in lines if (line - host) * inboard > 1e-6]
    half = abs(min(others, key=lambda line: abs(line - host)) - host) / 2.0 if others else 0.0
    edge = [across(p) for p in floor.deck_outline]
    outboard = max(0.0, (host - min(edge)) if inboard > 0 else (max(edge) - host)) if edge else 0.0
    return half + outboard


def strip_plf(floor, wall, header) -> tuple[float, float]:
    """``(tributary ft, total plf)`` of the floor strip at R301.5's live + dead."""
    trib_ft = tributary_m(floor, wall, header.plies) / _FT
    return trib_ft, (FLOOR_LIVE_LOAD_PSF + FLOOR_DEAD_LOAD_PSF) * trib_ft


def edge_rim(floor, wall, header):
    """The floor's edge rim beside the plies, or ``None``."""
    _u, _along, across = _frame(wall.axis)
    faces = [across(p.p0) for p in header.plies]
    return next((m for m in floor.members if m.child_key.startswith(EDGE_RIM_PREFIX)
                 and min(abs(across(m.p0) - f) for f in faces) < 3 * _IN), None)


def seat_loads(ctx, header, wall) -> list[SeatLoad]:
    """The door seats of an opening above this one: both ends, the worst reaction each."""
    _u, along, _across = _frame(wall.axis)
    out: list[SeatLoad] = []
    mid = (header.ro_lo + header.ro_hi) / 2.0
    top = max(p.z1_m for p in header.plies)
    for opening in ctx.model.openings:
        host = ctx.model.wall(opening.host_wall)
        placement = getattr(getattr(opening, "doorway", None), "exterior_placement", None)
        report = ((getattr(placement, "installation_report", None) or {}).get("support")
                  or {}) if placement else {}
        centre = opening_center(host, opening) if host is not None else None
        if (not report.get("seat_reaction_max_lb") or centre is None or host.tag == wall.tag
                or abs(along(centre) - mid) > 2 * _IN
                or abs(host.frame_base_z_m - top) > 2 * _IN):
            continue
        length = report["girt_course_length_in"]
        stations = [s for s, _z in report["seat_screws"]]
        near = [s for s in stations if s < length / 2]
        far = [length - s for s in stations if s >= length / 2]
        for offset in (sum(near) / len(near), sum(far) / len(far)):
            out.append(SeatLoad(offset, report["seat_reaction_max_lb"],
                                report["seat_eccentricity_in"], report["seat_width_in"],
                                opening.tag, report.get("seat_rotation_dcr")))
    return out


def equivalent_uniform_plf(w_plf: float, span_in: float,
                           points: list[tuple[float, float]]) -> tuple[float, float, float]:
    """The uniform load (plf) with the same end shear, midspan moment and midspan deflection
    as ``w_plf`` plus point loads ``(distance from the left support in, lb)`` on a simple span."""
    length, w = span_in, w_plf / 12.0
    left = w * length / 2 + sum(p * (length - x) / length for x, p in points)
    right = w * length / 2 + sum(p * x / length for x, p in points)
    moment = w * length ** 2 / 8 + sum(p * min(x, length - x) / 2 for x, p in points)
    delta = sum(p * min(x, length - x) * (3 * length ** 2 - 4 * min(x, length - x) ** 2) / 48
                for x, p in points)
    return (12.0 * 2.0 * max(left, right) / length, 12.0 * 8.0 * moment / length ** 2,
            w_plf + 12.0 * delta * 384.0 / (5.0 * length ** 4))


def two_ply_row(span_ft: float) -> tuple[float, float] | None:
    """The first published clear span at or past ``span_ft`` (read up: conservative)."""
    return next(((s, w) for s, w in TWO_PLY_1_25_11_875 if s >= span_ft - 1e-9), None)
