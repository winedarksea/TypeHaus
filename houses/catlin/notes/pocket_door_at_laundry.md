# D-M-LAUN — the laundry pocket door

The 36" leaf replaces the former 56" bifold and slides east from `W-M-HS3` through
`N-M-E3` into `W-M-HS4`. Both segments have the same wall section. Their node exists
because `W-M-LS` tees into the line, so the pocket framing crosses it while the top and
bottom plates remain continuous. `resolve/framing/pockets.py` finds the full travel;
`integrity.opening_fits` rejects a cavity that runs out of wall.

The opening is x=9'-1"..12'-1" on the y=22'-4" datum; the 2x4 wall and leaf sit
1" north of that axis so their hall-side gypsum is flush with `W-M-HS2`. Its position
balances access to the stacked washer and the 24" utility tub: both fixture center lines
fall within the opening. The tub's north face is 25.05" south of the doorway's inside
face, giving standing room at its front. The washer is operated from the hall. The tub remains the
air-gap receptor for `PR-M-DRYER-COND`.

The leaf runs 37" east of the opening. Its end stays short of `N-M-C2`, where bearing
`W-M-C3` and `BM-M-HALL` begin. `W-M-LS` meets the continuous top and bottom plates;
its vertical gypsum edge floats against the split jamb. No fastener over the pocket may
exceed the 1" limit in `resolve/framing/tables.py`. No box, pipe, duct, register, or
backing may occupy the leaf's travel; `mep.pocket_occupancy` checks both wall segments.

`DT-POCKET-INT-36` uses a Johnson 1500PF frame for this 2x4 host. The hardware takeoff
bills part `153068PF` per door.
