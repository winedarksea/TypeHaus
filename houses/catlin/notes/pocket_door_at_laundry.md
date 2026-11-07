# D-M-LAUN — the laundry pocket door

The 36" leaf replaces the former 56" bifold and slides east from `W-M-HS3` through
`N-M-E3` into `W-M-HS4`. Both segments have the same wall section. Their node exists
because `W-M-LS` tees into the line, so the pocket framing crosses it while the top and
bottom plates remain continuous. `resolve/framing/pockets.py` finds the full travel;
`integrity.opening_fits` rejects a cavity that runs out of wall.

The opening is x=10'-1 1/2"..13'-1 1/2" on the y=22'-4" datum (11 1/2" east of its old
9'-2"..12'-2" since 2026-11-07, owner); the 2x4 wall and leaf sit 1" north of that axis so
their hall-side gypsum is flush with `W-M-HS2`. The move puts the strike king and jack
(x 118 1/2..121 1/2") under `BM-S-BATH-E`'s hung south end at x=10'-0", so the header carries
uniform load only (`header_spans_r602_7.md` §4). The east jamb meets `W-M-LS`'s laundry face,
which takes that casing leg.

The tower stands 1" off `W-M-LS`, wholly inside the opening, and is operated from the hall.
The tub moved west of it, 1/4" off `W-M-BA2E`, with 25" of standing room in front, reached
through the doorway's west half; its drain, supplies, vent and cleanout moved with it. The
washer box is recessed in `W-M-CLN` behind the tower (valves 5" behind the rear inlets,
`PR-M-WASH-CW`/`-HW`), and the washer drains over the tub's rim into the tub's trap
(`PR-B-LSINK-DRAIN`); the old standpipe and box on `W-M-BA2E` are gone, so nothing of the
washer is on BATH2's wall (owner, 2026-11-07). LG's installation guide (WKHC252H*A p.20-23)
allows "a standpipe or laundry tub", hose end 24"-96" over the base and <= 41" on the
dryer-condensate connector; the tub's rim is 34". Minn. R. 4714.1001 lets a laundry tub
receive an adjacent clothes washer; the AHJ confirms it against 4714.0804. The guide also asks
4" behind the machine and 1" at the sides; the tower sits against `W-M-CLN`, so the inlets
want 90-degree hoses (open). The switch is inside the strike jamb on `W-M-HS3`.
(`PR-M-DRYER-COND` is retired: the dryer drains with the washer.)

The cavity runs 38 1/2" east of the opening, to x=16'-4" (the Eclisse RO). Its end stays short of `N-M-C2`, where bearing
`W-M-C3` and `BM-M-HALL` begin. `W-M-LS` meets the continuous top and bottom plates;
its vertical gypsum edge floats against the split jamb. No fastener over the pocket may
exceed the 1" limit in `resolve/framing/tables.py`. No box, pipe, duct, register, or
backing may occupy the leaf's travel; `mep.pocket_occupancy` checks both wall segments.

`DT-POCKET-INT-36` hangs in an Eclisse EKC3680 steel cassette for this 2x4 host
(`pocket_frame_eclisse.md`); the hardware takeoff bills it per door.
