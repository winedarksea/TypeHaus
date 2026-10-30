# RM-B-GYM echo: what was considered and what would work

**House:** catlin
**Structure:** `RM-B-GYM`, `CEIL-RM-B-GYM-FS-M-EAST`, `W-B-CE`, `D-B-PLAY`, `ED-B-GYM-LT`
**Written:** 2026-10-30, from three independent web-research passes. The owner decided
from it.
**Decision:** the floor is now 3/4" stall mats (`catlin-rubber-stall-mat`). The absorber
panels are **research only**: nothing is authored, and `prices.toml` carries a
`finish-gym-acoustic-panels` allowance. Hang them only if a clap test after move-in calls
for it (`plans/TODO.md`).

> ⚠ Rubber does not reduce echo. The room rings because every surface is hard. Only
> porous absorber (mineral wool or fibreglass behind fabric) changes that.

---

## 1. The room and its reverberation (Sabine, mid-frequency)

Clear face 16'-9" x 17'-2" (286 SF, 26.5 m2). The ceiling is 94 5/8"-96 3/16" over the
mats, so V ~ 64 m3. RT60 = 0.161 V / A.

| surface | finish | m2 | alpha (500-1k Hz) | A, m2 sabins |
|---|---|---|---|---|
| floor | rubber on slab | 26.5 | 0.04 | 1.06 |
| ceiling | painted 5/8" gwb | 26.5 | 0.05 | 1.33 |
| walls, gypsum | W-B-CE, W-B-CS, W-B-CS3, W-B-S3-FR above the curb | ~18 | 0.05 | 0.90 |
| walls, bare concrete | W-B-E1, W-B-S4, W-B-CS2, W-B-S3 curb | ~23 | 0.02 | 0.46 |
| glazing | D-B-PATIO | 3.4 | 0.15 | 0.51 |
| door leaves | D-B-PLAY, D-B-SAUNA | 4.7 | 0.08 | 0.38 |
| open doorway | D-B-GYM, 36" x 80", no leaf | 1.9 | 0.5-1.0 | 0.9-1.9 |
| **empty room** | | | | **~5.6-6.5 -> RT60 ~1.6-1.9 s** |
| + 14 panels, 2'x4'x2" mineral wool | 14 x 0.74 | 10.4 | ~0.95, less ~0.04 covered | +9.5 -> **~0.65-0.7 s** |

The doorway's alpha is 1.0 for sound that leaves and never returns; the hard hall sends
some back, hence the range. Equipment and people add 1-2 m2, so the furnished room sits
around 1.2-1.6 s today. Twelve panels give ~0.7-0.75 s and sixteen ~0.6 s. A home gym is
comfortable at 0.6-0.8 s.
The alpha values are typical published table values for these surface types, not
measurements. A tape-and-clap or phone RT60 app reading after move-in replaces this table.

## 2. The three ideas from TODO

**Drop ceiling: declined.** Acoustically it would work: lay-in tile at NRC 0.55-0.70 over
286 SF adds ~15 m2 sabins. It fails on two other counts:
- The 5/8" gwb on FS-M-EAST's 11 7/8" I-joists is the IRC R302.13 membrane
  (`code.R302_13_floor_protection`). Ordinary lay-in tile is not an equivalent. The one
  tested route (Armstrong's I-joist report: 5/8" tile in a residential fire-rated grid)
  still hangs the grid below the joists, so it costs the same headroom as option b.
- Hung below the kept gwb, a grid needs about 4" of drop. That takes the ceiling at the
  fan from 96 3/16" to ~92", the Gallegos body to ~6'-9 5/8", and the blades to ~7'-0 1/4".
  It also takes overhead room out of a gym.

**Slat wall replacing W-B-CE's gym-side drywall: declined.** It absorbs no more than the
same fabric and batts with slats laid over the drywall that stays. Removing the board takes
W-B-CE (staggered 2x6, two faces of 1/2" gwb) from about STC 42 to about 28-31 toward the
media room. With D-B-PLAY in the composite, that is a 2-7 dB loss *(estimate; uncertain)*.
It also needs box extenders on every device (NEC 314.20), FR fabric, kraft-free batts, and
it opens the wet-wall cavity of a plumbing wall.

**Floor: kept as rubber, now stall mats.** Rubber is echo-neutral (alpha ~0.03-0.05,
same as the 8 mm roll). 3/4" stall mats are still the better gym floor: they survive
dropped weights, and they cost ~$1.25-2.50/SF loose-laid against the roll's $3-8/SF plus
$1.50-3.50/SF to glue it down.

## 3. The fix that works: absorber panels

- **What:** 12-16 DIY panels, 2' x 4' x 2". Use mineral wool (Rockwool Comfortboard 80 or
  Safe'n'Sound) or 3 pcf fibreglass board (OC 703 class). Use a 1x3 or 1x4 frame, wrapped in
  **Guilford of Maine FR701** or an equal ASTM E84 Class A fabric. Budget ~$300-700 DIY.
- **Never foam** (polyurethane foam is a fire load in a room people use, and IRC R316
  wants it behind a thermal barrier). **Never burlap or plain cotton** (combustible,
  untreated).
- **Where:** one wall of each parallel pair, because the flutter is between parallel hard
  faces:
  - E-W pair: the bare-concrete east wall (W-B-E1/E2) against the west centre wall.
    Panels go on the **east** wall (4-5), the hardest surface in the room.
  - N-S pair: W-B-CE against the south walkout. Panels go on **W-B-CE** (3-4), clear of
    D-B-PLAY's swing and the switch at 66 1/2". The south wall has the patio glass and
    EQ-B-HP2-GYM.
  - Floor-ceiling pair: **ceiling** (4-6), hung flat on Z-clips or cleats into the joists.
- **Wall band:** panels long-side vertical, spanning about 2'-0" to 7'-0" AFF. That is the
  ear zone standing and on the floor, and above what a dropped bar or a swung kettlebell
  reaches.
- **Ceiling clearances:** keep ceiling panels out of a ~38" radius circle around the fan at
  (27', 9'): the 52" sweep is 26" in radius, plus a 12" margin. Keep them off the four cans
  at (22'/32', 6'/12') and REG-B-SUP1 at (19', 13'). Keep them off the overhead-lift spot,
  which is not modelled: wherever the rack or press is, leave a bar's arc over it bare.
- Fix to concrete with Tapcons through a cleat. Fix to gypsum with impaling clips or a
  French cleat into the studs. Nothing is glued to the board.

## 4. Isolation toward the media room

The cheapest upgrade is a **gasket kit on D-B-PLAY**: perimeter seals on the stops, an
astragal seal at the meeting stiles, and an automatic door bottom. The undercut and the
pair's meeting gap leak more than W-B-CE's wall does. Air transfer is not lost, because
D-B-GYM is a doorless opening to the hall.

## 5. Stall-mat practicalities

- 4' x 6' x 3/4", ~94-100 lb each. Lay them with two people. 13 mats (312 SF) cover the
  ~287 SF field, at 9% waste (`floor_waste_fraction`).
- **Moisture first:** run a taped-down plastic-sheet test on the slab (ASTM D4263 style,
  16-24 h). If the sheet fogs, lay 6-mil poly under the mats.
- **Air them out 1-2 weeks** (garage or outside, flipped once). Recycled rubber smells
  strongly at first.
- Cut with a straightedge and a fresh utility blade, scoring repeatedly. Bend the mat open
  as you go, and soapy water helps. Mats are not square to the inch, so dry-lay and trim
  to the walls last.
- **Reducers** where the mats stop 3/4" above sealed concrete: the open edge to the hall
  (D-B-GYM) and the sauna doorway (D-B-SAUNA, stepped across barefoot). A 3/4" rubber ramp.
  At D-B-PLAY the carpet sits 1/4" lower, and a flat transition strip covers it.
- The leaf bottoms re-derive from the higher floor. D-B-SAUNA and D-B-PLAY rose 7/16" and
  1/4"; nothing else moved.

## 6. What is NOT graded here

No engine check reads reverberation, STC, or fan blade height. `ED-B-GYM-LT`'s
blade bottom (~7'-4 1/4" over the mats, from Hunter's 7.97" flush ceiling-to-blade
dimension) is guarded only by the comment in `plan/mep_electrical.py`.

## Sources

- IRC R302.13 / APA I-joist fire assemblies: https://www.apawood.org/i-joist-fire-assemblies
- Armstrong, I-joist fire test results (suspended ceiling as R302.13 equivalent):
  https://direct-www.armstrongceilings.com/content/dam/armstrongceilings/residential/brochures/i-joist-fire-test-results.pdf
- Armstrong fire-rated grid: https://armstrongceilings.com/residential/en-us/suspended-ceiling-systems/fire-rated-ceiling-grid.html
- Owens Corning 700 series absorption (703 2": NRC 1.00), reproduced copy, not the maker's
  current sheet: https://confluence.cornell.edu/download/attachments/161661743/OwensCorneing%20700%20Series%20fiberglass%20board.pdf?api=v2
- Absorption coefficients for hard surfaces (secondary tables; the bands vary by source):
  https://www.engineeringtoolbox.com/accoustic-sound-absorption-d_68.html,
  https://sengpielaudio.com/calculator-RT60Coeff.htm
- Guilford of Maine FR701 (Class A, ASTM E84):
  https://mage.acousticalsolutions.com/media/productattach/a/s/as-guilford-of-maine-fr701-acoustic-fabric-data-sheet.pdf
- Tractor Supply 4x6x3/4 stall mat (94 lb; regional prices seen at $30-55):
  https://tractorsupply.com/tsc/product/4-ft-x-6-ft-x-3-4-in-thick-rubber-stall-mat-2219003
- Hunter Gallegos 51583 spec sheet (flush: 7.97" to blade, 9.64" to fan bottom; AC motor):
  https://image.hunterfan.com/51583_specification_sheet.pdf
- *Uncertain:* the W-B-CE STC figures (42 -> 28-31) and the composite loss. These are
  estimates from published values for similar assemblies, not a test of this wall.
  Greatmats' stall-mat and roll pricing was quoted by the research passes and not
  re-checked here.
