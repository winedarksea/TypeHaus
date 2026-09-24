# The sidewalk and its planting pockets — hand-worked basis

**House:** catlin
**Structure:** `SL-WK-A`..`-D` (`params/landscape_walk.py`), their `FO-WK-*` pockets,
`PB-WK-POCKETS`, and the four `walk *` impervious surfaces.
**Written:** 2026-09-21, by hand from the leg rectangles.
**Oracle for:** the `slab:SIDEWALK_FRC_CLASS5` and `mndot-class-5-base` takeoff rows and
`code.R401_3_impervious` on the four walk surfaces; reproduced by
`tests/test_catlin_gardens.py`.
**What is asked of the reviewer:** §2's areas and §3's pocket count.

> ⚠ Every slab is modelled FLAT at its high edge, -2'-9". Leg D's south end meets
> SL-SG-STAIRPAD (-2'-8") at a 1/2" isolation joint, 1" low; the stair pad, not a walk
> leg, carries the walk from D to the porch flight. The fall is on the impervious surfaces only. Two joints are therefore
> not flush in the field and are set by the finisher: walk A's west edge stands 1 3/4" over
> the driveway at the flare, falling to 1" at its north end (on the two impervious falls;
> 2" in the flat model), a curb at the drive's edge that is ACCEPTED (§2a), and walk C meets the paver approach's -3'-0 1/2" east edge about 3" high.
> Grade both by hand at the pour; neither is modelled.

---

## 1. Section

Full: 12 band | 16 pocket | 36 walk | 16 pocket | 12 band = 92" (leg A).
One-sided: 36 walk | 16 pocket | 12 band = 64", walk against the building (legs B and D) —
the house to lot line is 6'-4", so 92" does not fit east of the house anywhere, nor south of
it, where the court and the porch stair own the ground; and east of the garage the strip
beyond 64" is RG-E-BASIN's, the west basin's mirror (2026-09-23; B was 92" until then). C is
walk only.

Pockets are 16" sonotube voids, drawn as 16-gons (1.3605 sf each), centred 20" in from
each edge (44" off the house on D). Along the run they are 4'-0" o.c., **centred in the
leg**: the slack left over is split evenly between the two ends, never less than 2'-0" at
either. **Leg A is the exception — it is anchored to the corner it turns** (§3). Control
joints fall on the same stations.

## 2. Legs (feet, plan frame)

| leg | outline | gross sf | pockets | net sf |
|---|---|---|---|---|
| A garage north | x 24.04..35.45 × y 67.33..75.00, less the 2.0 sf flare notch (§2a) | 11.40 × 7.67 = 87.4 − 2.0 = 85.4 | 4 | 80.0 |
| B garage east | x 30.11..35.45 × y 43.02..67.33 | 5.33 × 24.31 = 129.7 | 6 | 121.5 |
| C landing connector | x 30.04..42.04 × y 39.60..43.02, less the 0.50 × 1.08 notch at PT-BW-RNE | 41.04 − 0.54 = 40.5 | 0 | 40.5 |
| D house east | x 36.70..42.04 × y −9.00..39.60 | 5.33 × 48.60 = 259.2 | 9 | 247.0 |
| **total** | | **514.8** | **19** | **488.9** |

Concrete at 4": 488.9 / 3 / 27 = **6.04 cy**. Class 5 at 6" bills by the net slab area,
**488.9 sf**. Impervious area counts the GROSS 514.8 sf — the pockets are not subtracted,
which is conservative for the coverage table.

### 2a. Leg A against the driveway (2026-09-23)

The drive (`params/driveway.py`, notes/driveway_layout.md) flares 45° from x = 26' at its
south edge to x = 24' two feet north. A's SW corner is cut on that line offset 1/2" square
to it: the line x + y = 26 + Y0 + 0.5/12·√2 = 93.386, so A's south edge starts at
x = 93.386 − 67.332 = **26.054** and its west edge at y = 93.386 − 24.042 = **69.344**. The
notch is ½ · (26.054 − 24.042) · (69.344 − 67.332) = ½ · 2.012 · 2.012 = **2.02 sf**.
A's westmost pocket, (29.445, 69.00), is 3.58' from that line, past the 2'-0" end inset, so
`_A_STATIONS` does not move.

**The step is kept.** Along x = 24' the drive's fall reaches −35.5" at y = 69.34 and −37.0"
at y = 75.00; A's reaches −33.8" and −36.0". That is 1 3/4" to 1" with the walk high. A flush
A at −2'-11" would open a 2" lip where A meets leg B, on the walking line, and the flare puts
a tyre leaving the door's east 2' on drive, not on A.

## 3. Pocket stations

Inset = (run − (n−1) × 4'-0") / 2, with n the most stations the run holds at 2'-0" clear
of each end.

- **A is anchored to the corner, not centred.** Its two rows (y = 69.00 and 73.33) run
  across the whole width of leg B, so its first station IS leg B's pocket column — x = 33.78
  (44" off the stem, 20" in from the shared east edge) — and the next is 29.45, one 52" step
  west, the full section's own row pitch. → **4**, less **A01** (x 29.45, south row),
  struck 2026-09-23 beside `TR-G-LEADER-E`'s drop at the garage NE corner → **3**.
  West inset 5.40', east inset
  1.67' × 12 = 20", the section inset, so 12" of concrete at the end like every side band.
  **This is what keeps the L walkable.** Leg B's 36" walk runs x 30.11..33.11 against the
  stem; A's south-row pockets stop at 30.11 (A01, now struck) and start again at 33.11,
  tangent to both lane edges, so the turn out of A into B crosses **36.0" of open
  concrete** — more on the west side since A01 went.
- **B** (run 24.31', n = 6, inset 2.16'): y = 45.18, 49.18, 53.18, 57.18, 61.18, 65.18 on
  its one column (x = 33.78) → **6**.
- **D** (run 48.60', n = 12, inset 2.30', column x = 40.37): y = −6.7, −2.7, 1.3, 5.3, 9.3,
  13.3, 17.3, 21.3, 25.3, 29.3, 33.3, 37.3 → 12, less the three whose centres fall in the
  retired patio's y 10'..22' (13.3, 17.3, 21.3) → **9**.

**NO POCKET SITS AT A LEADER'S FOOT, and neither east leader can have one.**
`TR-RF-LEADER-E` stands at x = 36'-10 9/16", over leg D's 36" walking band: a 16" void
centred there leaves **1.6"** of concrete at the slab's house-side edge, against the 12"
every grid pocket keeps, and it is 2.9' off the pocket column. Both leaders' risers pass
down through the walk to buried extensions into RG-E-BASIN (§5).

**`TR-G-LEADER-E` drops on the garage north wall, not under its outlet** (2026-09-23).
Straight down from the trough's north end (31.27, 68.49) it stood in the turn from A into
B, inside B's 36" lane. A gooseneck under the soffit (1.96' of offset, two elbows) brings
the drop to (29.58, 67.58): 2" off the north cladding face, 4 3/8" west of the NE corner,
inside A's 12" edge band. Its riser crosses that band, not a walk.

The D pocket at y = 9.3 stands **0.40"** north of the retired patio's north edge. That is
a measurement, not a constraint — the skip is a centre test over y 10'..22', so the count
does not turn on it — but it is the one station that would move if leg D's ends did.

18 pockets cycle Allium, Sporobolus, Salvia, Calamintha in A-B-D order: **5 · 5 · 4 · 4**.
The cycle was Calamintha-first until A01 (a Calamintha) was struck; rotating it one place
kept every surviving pocket's species.

## 4. Fall (R401.3: 2% within 10' of the foundation)

| surface | near → far | run R401.3 reads | slope |
|---|---|---|---|
| walk A | −33" → −36" | 10.9' | 2.3% |
| walk B | −33" → −36" | outside the 10' band | — |
| walk C | −33" → −36" | 12.0' | 2.1% |
| walk D | −33" → −35" | 7.2' | 2.3% |

## 5. What is NOT graded here

Joint layout beyond the pocket stations, the pour sequence, the concrete's fibre dosage
(EXPOSED_MIX's 4 pcy macro-synthetic), and the two non-flush joints in the warning above.

Also: **the east leaders' risers pass through the slab, and nothing models the hole.**
Since 2026-09-23 `TR-RF-LEADER-E` and `TR-G-LEADER-E` stop at +1'-0" / −1'-6" and run on as
4" PVC risers through legs D and A to buried extensions (notes/rain_garden_sizing.md §6);
each crossing wants a sleeve cast in, and no `FloorOpening` is authored for it. The
extensions pass under the walks' Class 5 base with their crowns at about −3'-8", and nothing
grades a buried pipe against a slab's base either.

## Sources

- IRC 2018 R401.3 — drainage; 2% for impervious surfaces within 10 ft.
- MnDOT Standard Specifications, 3138 (aggregate base, Class 5).
