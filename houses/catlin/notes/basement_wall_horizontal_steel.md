# Basement and garage stems — horizontal steel, and what the vertical cells read

**House:** catlin.
**Written:** 2026-09-17, by hand (decision #75, D8/D10).
**Closes:** `notes/rebar_backout.md` §4 items 1 and 2.
**Authored in:** `plan/storeys/basement.py` (`_B8_STEEL`, `_B12_STEEL`),
`params/foundations.py` (`_ICF_STEM_STEEL`).

## 1. IRC Table R404.1.2(1): where the horizontal bars go

The table is not a schedule by spacing. It places **rows** of #4 by the wall's unsupported
height: a wall **≤ 8'** takes one #4 within 12" of the top of the wall story and one near
mid-height; a wall **> 8'** takes one within 12" of the top and one near each third point.
Every basement run here pours from −9'-1 7/16" to −1'-1 7/16", **exactly 8'-0"**
(`basement.py`, the R404.1.2(8) row note), so the ≤ 8' row governs and asks for **two**.

**Authored: three rows** — top − 6", mid-height, and 6" off the base (decision D8). The
third is the > 8' row's extra bar, bought on purpose: the 8'-0" reading sits on the
boundary, and a pour that finishes 1/2" proud of the seat would read the other row. One more
#4 on 30 LF of wall is cheap next to a re-inspection. Schema: `BarSpec(role="horizontal",
bar=4, count=3)`, where a wall's `count` is rows (`model/rebar.py`).

Row heights above the base, 96" wall: **6", 48", 90"**. Cover 2" (`BURIED_MIX`), so on an
8" wall a row stands behind the `#5 @ 41"` verticals on the one face they occupy; on a 12"
wall with no verticals it sits at cover. ⚠ This reading of R404.1.2(1) is from the code
language as recalled, not a printed ICC copy. Check the row text against the printed table
before the permit set.

## 2. W-B-E1/E2 — 12", verticals NR

`structural.foundation_unbalanced_fill` reads IRC Table R404.1.2(8) at 12" / 45 psf/ft /
8' wall / 7' backfill: **NR**, no vertical reinforcement, plain concrete (f'c ≥ 2,500 psi;
`BURIED_MIX` is 5,000). So the east walls author **horizontals only**, `_B12_STEEL`: the
same three #4 rows. R404.1.2(1) is not conditioned on the vertical cell, and NR does not
waive it.

## 3. GARAGE_ICF_6 — footnote d

The nine garage stems are a 6" nominal core in a stay-in-place ICF form, 5'-4" tall, filled
to grade on both sides (`unbalanced_fill = 0`). At 6" nominal, R404.1.2(8) reads NR for
every row this wall could index. **Footnote d** is the exception: a 6" wall formed with a
stay-in-place system takes **#4 @ 48"** vertical where the cell reads NR
(`checks/structural/foundation.py` prints it).

**Authored: #4 @ 16" vertical and #4 @ 16" horizontal**, `_ICF_STEM_STEEL`, one layer at the
core's centre. 16" is the form's own web and course module — the spacing
`MasonrySpec.rebar_spacing` used to state with no bar size (now retired) — and three times
footnote d's minimum. The horizontal bar rides in each 16" course's web saddles, the way ICF
forms are placed, which also puts a row within 12" of the top as R404.1.2(1) asks.

**Cover 1 1/2", authored on the schedule.** `BURIED_MIX` states 3", which is ACI 318-19
Table 20.5.1.3.1's cast-against-earth row. The core is formed against EPS, so the formed
face row governs: 1 1/2" for #5 and smaller exposed to ground. 3" a side would also leave
0" for bars in a 6" core (`integrity.reinforcement_layout` caught it on first layout).

**No dowels (D10).** The stems bear on crushed-stone footings (`params/foundations.py`,
R403.5), so there is no pour below to lap into. `W-GF-N-DR`, lowered at the overhead door,
is an ordinary stem on the same stone strip and takes the same schedule.

## Sources

* 2021 IRC Table R404.1.2(1) (horizontal reinforcement), Table R404.1.2(8) and footnote d
  (vertical reinforcement, 6" stay-in-place forms), §R403.5 (crushed-stone footings).
* `notes/rebar_backout.md` §4, `notes/basement_to_framed_wall_detail.md`.
