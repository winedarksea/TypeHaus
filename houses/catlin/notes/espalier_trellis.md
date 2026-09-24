# The espalier frame in the west strip — hand-worked basis

**House:** catlin
**Structure:** `TRL-W-S`, `TRL-W-N` (`params/landscape_gardens.py`), `PL-W-APPLE-1..4`
(`plan/landscape.py`), the power service `UtilityLine` (`plan/site.py`).
**Written:** 2026-09-21, by hand.
**Oracle for:** `resolve/landscape.py::trellis_post_stations`, `site.utility_clearance`,
and the trellis rows of the `planting` table; reproduced by `tests/test_catlin_gardens.py`.
**What is asked of the reviewer:** §2's clearances.

---

## 1. Posts

Posts are evenly spaced with no bay over 8'-0": bays = ⌈L / 8⌉, posts = bays + 1.

| trellis | path x=−5' | L | bays | posts at y |
|---|---|---|---|---|
| TRL-W-S | y 1'..14' | 13' | 2 | 1.0, 7.5, 14.0 |
| TRL-W-N | y 25'..38' | 13' | 2 | 25.0, 31.5, 38.0 |

**6 posts**, 4x4 KDAT, 7'-0" above grade and 3'-0" embedded. Wire: 4 courses (18", 36",
54", 72") × (13 + 13) = **104 LF**. The runs mirror about y=19'-6".

## 2. Utility clearance (24" locate tolerance, Minn. Stat. ch. 216D)

The power service runs y=18' from the west line to the house at 3' deep. Nearest posts:
TRL-W-S at y=14 → 4.0' less the 1 3/4" half post = 3.85'; TRL-W-N at y=25 → 6.85'. Apple
planting holes (18" radius): PL-W-APPLE-2 at y=11 → 7 − 1.5 = 5.5'; PL-W-APPLE-3 at y=28 →
10 − 1.5 = 8.5'; PL-W-APPLE-4 at y=35 → 15.5'. All clear 2'. The sewer (x=3') and water
(x=11') are further.

## 3. Espaliers

Four dwarf apples (Honeycrisp on Bud 9, Zestar! on M9, Haralson and SnowSweet on Bud 9) —
four cultivars so they cross-pollinate — at y = 4', 11' (TRL-W-S) and 28', 35' (TRL-W-N),
each trained 6' wide in the wire plane: 1'..7' and 8'..14' on the south run, 25'..31' and
32'..38' on the north, so every arm ends at a post.

## 4. Neighbours of the north run's extension (2026-09-23)

TRL-W-N's end post at y=38 stands 4.6' west of SL-M-HP3PAD (x=−0.25'), 2.6' past HP3's
24" side clearance; HP3 discharges north, not west. The west leader extension runs at x=−1.5', 3.5'
east. RG-W-BASIN starts at y=47.

## 5. What is NOT graded here

Post embedment against wind on the fruit load, and the silt fence, which moved 1' west to
x=−6' so it no longer runs down the trellis line during construction.
