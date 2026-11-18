"""Backers behind the edge rim at each door sill seat (owner, 2026-11-18).

A seat's HeadLOK HLGM10s need 2.0" of embedded thread (ESR-1078 Table 2); the 1 1/4" LSL rim
holds 1 1/4", so 3/4" must land in wood behind it (`notes/exterior_door_sill_beam.md` §3).
D-M-PORCH: D-B-SUNKEN's band-header LVL plies are already nailed to the rim. D-S-BALCONY: a
10" piece of the rim stock on the rim's inner face, a 2-ply rim board, nailed per TJ-8000
p.7 (side load, 10d, 3 rows). D-M-ENTRY: a 1/2" LSL filler closing the gap to FO-M-ERV-OA's
LVL trimmer pack, the three nailed together per IRC R602.3(1) item 10 (16d at 16" o.c. each
edge, the built-up header with 1/2" spacer). Each backer is the seat's own 10" station; the
connection grade refuses a seat whose screws miss it (`resolve/girt_sill_connection.py`).
"""

from typehaus import JoistReinforcement, inch, pt

_SEAT_IN = 10.0
_BACKER = "1.25x11.875 rim"
_FILLER = "0.5x11.875:lsl"


def _backers(ro_edges_in, rim_inner_y_in, inward, member, source):
    """One ply on the rim's inner face behind each end seat of a door whose RO spans
    ``ro_edges_in`` (x, inches)."""
    lo, hi = ro_edges_in
    return tuple(
        JoistReinforcement(
            at=pt(inch((s0 + s1) / 2), inch(rim_inner_y_in + inward)), plies=2,
            member=member, blocking=False, extent=(inch(s0), inch(s1)), source=source)
        for s0, s1 in ((lo, lo + _SEAT_IN), (hi - _SEAT_IN, hi)))


#: D-S-BALCONY's RO (x 224 11/32"..287 21/32") over FS-S-EAST's y=0 rim (inner face 1 3/4").
BALCONY_SEAT_BACKERS = _backers(
    (224.34375, 287.65625), 1.75, 1.0, _BACKER,
    "D-S-BALCONY sill seat backer: 1 1/4\" LSL rim stock on the rim's inner face, a 2-ply "
    "rim board nailed per TJ-8000 (March 2025) p.7, side load, 10d, 3 rows at 12\" o.c.; "
    "notes/exterior_door_sill_beam.md section 3")
#: D-M-ENTRY's RO (x 75 5/8"..114") over FS-M-MECH's north rim (inner face 430 1/4").
ENTRY_SEAT_BACKERS = _backers(
    (75.625, 114.0), 430.25, -1.0, _FILLER,
    "D-M-ENTRY sill seat filler: 1/2\" LSL rip closing the gap from the rim to FO-M-ERV-OA's "
    "LVL trimmer pack, nailed through per IRC R602.3(1) item 10 (16d common at 16\" o.c. "
    "each edge); notes/exterior_door_sill_beam.md section 3")
