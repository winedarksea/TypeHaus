# D-M-LAUN — the laundry pocket door

*Replaces the 56" four-leaf bifold that stood here.*

## Why

A bifold eats its own opening — four leaves stack at both jambs, so a 56" unit really gave
about 50" of clear width — and it demanded 8¾" of clear floor in front of the track. That
margin is not incidental: `plan/fixtures.py` records it as *the* constraint that sized the
room move, and it is why the 40"-deep stacked washer/dryer could not be deeper.

The pocket gives 48" clear — a ~2" loss — and hands the 8¾" back.

## Where the leaf goes

All stations on y = 22'-4". `N-M-D1` 8'-0", `N-M-E3` 13'-4", `N-M-C2` 18'-0".

```
     8'-4"                    12'-4"      13'-4"        16'-5"   18'-0"
hall ──┼════ 48" clear ═════════┼═════ 49" pocket ═════════┼──1'-7"──┼
       │        W-M-HS3         │    │     W-M-HS4         │
    strike                    mouth  W-M-LS             closed    W-M-C3
     jamb                     (split  tee                 end     BEARING
    (solid)                    jamb)                    (solid)
```

**4'-0" is the widest leaf that fits.** The cavity runs east from the rough opening and the
jamb pack that closes it has to clear `N-M-C2`, where the **bearing** `W-M-C3` corners in
and `BM-M-HALL` starts: `8'-4" + leaf + (leaf + 1") ≤ 17'-6"` caps the leaf at 54½". 4'-0"
is also a real product size — see *The kit* below.

**The cavity crosses `N-M-E3`, and that is deliberate.** Wall segmentation at a tee is an
authoring convention: `classify_storey_junctions` builds junctions from wall *endpoints*, so
a partition teeing in has to split the wall it lands on. W-M-HS3 and W-M-HS4 are one plane,
one assembly and one pair of plates. `resolve/framing/pockets.py` owns the walk that says so,
and `integrity.opening_fits` refuses a pocket whose run leaves the colinear chain.

## The tie at W-M-LS — read this before touching either wall

A pocket occupies **floor to 6'-8" only**. Above and below it the band is solid, which is the
whole reason a partition may die into it:

- **Top.** W-M-LS's double top plate laps the band's double top plate at 9'-0" — continuous
  framing entirely above the cavity. This is the primary tie.
- **Bottom.** W-M-LS's bottom plate fastens to the band's bottom plate, which runs unbroken
  under the pocket; the frame's split studs sit *on* it.
- **Between.** W-M-LS's end stud is its own. Its vertical edge floats against the split jamb
  and its gypsum terminates on a floating corner bead. Nothing is fastened through.

`test_catlin_contract_m3.py::test_the_laundry_pocket_clears_the_bearing_corner_and_owns_its_wall`
pins the split studs stopping below the plate line. If that ever changes, this tie is gone.

## Two things that will ruin it after the drywall

- **No fastener over the pocket may exceed 1"** — `resolve/framing/tables.py::POCKET_MAX_FASTENER`.
  Past that it reaches the leaf. This governs the drywall screws too.
- **Nothing hangs on this wall again, and nothing goes in it.** No towel bar, no art, no
  blocking, no outlet, no switch, no pipe, no register — from 12'-4" to 16'-5" there is no
  stud to fasten to and no depth to recess into. `mep.pocket_occupancy` enforces it on both
  W-M-HS3 and W-M-HS4. W-M-HS4 hosted nothing when this was built, which is what made it
  possible at all; the only solid framing in the run is the pack at the closed end.

## What it costs

~9" of the utility tub's east end sits behind fixed wall — the appliance run is 53" (28"
stack + 1" + 24" tub) against a 48" opening. Shifting the rough opening east only trades
that for hiding the stack instead, which is worse. A 52" leaf would cut it to ~5" and still
fits the geometry, but it is past the published frame ladder.

## The kit

`DT-POCKET-INT-48` (`library/doors.py`) is **not** a commodity size. The Johnson 1500PF
series — the ladder the 24"–36" family is dimensioned from — stops at 36" and 125 lb, and a
4'-0" solid-core leaf is past both. This one is a heavy-duty timber-framed cavity unit
(`POCKET_FRAME_KIT_HEAVY`, `library/hardware.py`), billed as a counted part in the BOM's
hardware section rather than swept into the `finish-door-*` allowance. Ordering a 1500PF kit
for this door gets a frame the leaf will pull off the wall.
