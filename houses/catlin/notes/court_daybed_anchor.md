# Court hanging daybed anchors — hand-worked basis

**House:** catlin
**Structure:** `HA-SG-DAYBED-SW/SE/NE/NW` carrying `FURN-SG-DAYBED` (`plan/court_daybed.py`),
framed as FS-SG-PORCH's joist lines 003 and 006, each built up to `3-2x12:kdat`.
**Written:** 2026-10-13, by hand, before the multi-load calculation it oracles was encoded.
**Oracle for:** `checks/structural/_suspension_math.py` (`SimpleSpan` with several loads,
`deflection_at`, `connection_shear` with a raised bolt row), reported by
`structural.suspension_anchor`; reproduced by `tests/test_suspension_anchor.py` and
`tests/test_catlin_court_daybed.py`.
**Companions:** `notes/hanging_seat_anchor.md` (the hammock chair, the same load path
indoors).
**What is asked of the reviewer:** the per-rope share in §2, and the ledger question in §5,
which is open.

> ⚠ The saddle bolts sit **2 1/2" below the line's top**, not at mid-depth (§3.6). The two west
> ropes are 32" off the ledger, inside NDS §3.4.3.3's 5d, and only the depth above a hung bolt
> counts there. At mid-depth that state is OVER (1.18).
>
> ⚠ The hangers on the two 3-ply lines are **LUS210-3Z (ZMAX), not stainless**. No stainless
> LUS210-3 is listed; the rest of the porch hangs on LUS210SS. Owner to accept or name another
> part.
>
> ⚠ The rating is the design basis. The Atlantic Swing Co. Simon this bed is sized from
> publishes no rating; the bed bought must state **500 lb or more**.

This is furniture, not engineering. No seal is asked for and nothing here is on the
`haus engineering` register.

---

## 1. Geometry

| term | working | value |
|---|---|---|
| bed | Simon twin, 80 x 43 x 29 in, long axis east-west | centre (185", -59.25") |
| hang points | 76 x 36 in, on the arms: x = 185 ∓ 38, y = -59.25 ∓ 18 | x 147" / 223", y -77.25" / -41.25" |
| lines | FS-SG-PORCH at 12" o.c. from -113.25": 003 at -77.25", 006 at -41.25" | exact hits, no line moves |
| span L | ledger axes BM-SG-LDGW (x = 114.875") to BM-SG-LDGE (317.125") | 202.25" (16.85') |
| load stations | 147 − 114.875; 223 − 114.875 | a₁ = 32.125", a₂ = 108.125" |
| member | 3 plies of 2x12 KDAT southern pine | b = 4.5", d = 11.25" |
| S, I | 4.5 × 11.25² / 6; 4.5 × 11.25³ / 12 | 94.92 in³, 533.9 in⁴ |
| tributary | half of each 12" bay | 12" |
| clear | joist underside -11.25", court floor -109.4375" | 98.2" |
| rope | 98.19 − (18" seat + 29" body) | 51.2" (kit 24-84") |
| wall clearance | NW/NE rope to W-B-BRICK's face (y -13.675"); SW to W-SG-W1's face | 27.6", 32.9" ≥ 12" |

**Why lines 003 and 006, 36" apart, and not 003 and 007 at 48".** A rope 4" off a line moves
the line to it. The ledger's Titen HDs (`CN-SG-LDG*`) sit mid-bay on the AUTHORED lines, so a
line moved 4" brings its 3-ply end 2" from an anchor, behind the hanger's face flange. On
exact lines every anchor is 6" off the line's centre, clear of a 4 5/8" hanger.

## 2. The demand, per rope

| term | working | value |
|---|---|---|
| rated load | owner | 500 lb |
| per rope | one occupant on a long edge: the whole 500 lb on two ropes | 250 lb |
| impact factor | `preferences.toml [structural] hanging_seat_impact_factor` | 2.0 |
| saddle | `SADDLE-4.5-2x58-HDG` | 7.0 lb |
| shackle | Crosby G-209 1/2" | 0.7 lb |
| bed share | (100 lb frame + ~25 lb cushion) / 4 | 31.25 lb |
| **P** | 250 × 2.0 + 7.0 + 0.7 + 31.25 | **538.95 lb** |
| floor w | (40 live + 10 dead psf) × 12/12 ft; deck snow 35 < 40 | 50 plf = 4.167 lb/in |

Both ropes of a line carry P together, so each line takes two point loads plus the floor.
That is the case the check grades: one anchor graded as the only load on its line would
read low by half.

## 3. Capacity and the limit states

Design values: AWC NDS 2018 Supplement Table 4B, Southern Pine No. 2, 2x12 (the grade IRC
Table R507.6 publishes the porch span for): Fb 750, Fv 175, Fc⊥ 565, E 1.4×10⁶ psi.
**Wet service** (an exterior deck under a gapped plank): C_M 1.0 on Fb (Fb C_F ≤ 1,150), 0.97
on Fv, 0.67 on Fc⊥, 0.9 on E → **Fb 750, Fv 169.75, E 1.26×10⁶**. C_F is in the table
values; C_r is not taken; C_D = 1.0, because the impact factor is already on the load.

### 3.1 Reactions
R₁ = P(L − a₁)/L + P(L − a₂)/L + wL/2 = 453.34 + 250.82 + 421.35 = **1,125.5 lb** (LDGW)
R₂ = P(a₁ + a₂)/L + wL/2 = 373.74 + 421.35 = **795.1 lb** (LDGE)

### 3.2 Bending
M(a₁) = 1,125.52 × 32.125 − 4.167 × 32.125²/2 = 36,157 − 2,150 = 34,007 lb-in.
M(a₂) = 1,125.52 × 108.125 − 4.167 × 108.125²/2 − 538.95 × 76.0 = 121,697 − 24,357 − 40,960
= **56,380 lb-in = 4,698 lb-ft**. The shear zeros fall outside their segments (x = 140.8"
between the loads, 11.4" past both), so a₂ governs.
M' = 750 × 94.92 = 71,191 lb-in = **5,933 lb-ft**. Ratio **0.79**.
Two plies (S = 63.28) would give M' = 47,461 lb-in and a ratio of **1.19**. That is why the
line is three plies.

### 3.3 Shear
f_v = 1.5 × 1,125.5 / 50.625 = **33.3 psi** against 169.75. Ratio **0.20**.

### 3.4 Bearing: the hangers
Each 3-ply end hangs in an LUS210-3Z on the ledger. Simpson C-C-2021 p. 105, DF/SP, TPL 2x12,
LUS210-3 row: floor (100) **1,830 lb**, through (8) + (6) 0.162 x 3-1/2 nails. Simpson direct
NDS C_M in wet service: 0.70 for dowel-type fasteners → **1,281 lb**.
LDGW: 1,125.5 / 1,281 = **0.88**. **This governs.** LDGE: 795.1 / 1,281 = 0.62.

### 3.5 Deflection under the two loads
By superposition, E' = 1.26×10⁶, I = 533.9:
at a₂, own load P a₂²(L − a₂)² / (3EIL) = 0.1368", plus the a₁ load
P a₁ (L − a₂)(2La₂ − a₂² − a₁²) / (6EIL) = 0.0619" → **0.199"**;
at a₁, 0.0394 + 0.0619 = 0.101".
Worst 0.199" against L/480 = 0.421". Ratio **0.47**. Sawn-lumber E is apparent, so there is
no separate shear term.

### 3.6 The bolts, and where they sit
Two 5/8" A307 HDG bolts, double shear, 1/4" A36 side plates, load perpendicular to grain.
NDS 2018 §12.3.1, θ = 90° so K_θ = 1.25, G = 0.55 (Table 12.3.3A, southern pine), l_m = 4.5".

| term | working | value |
|---|---|---|
| F_em | 6,100 × 0.55^1.45 / √0.625 | 3,242.8 psi |
| R_e | 3,242.8 / 87,000 | 0.03727 |
| Mode I_m | 0.625 × 4.5 × 3,242.8 / 5 | 1,824.1 lb |
| Mode I_s | 2 × 0.625 × 0.25 × 87,000 / 5 | 5,437.5 lb |
| k₃ | −1 + √(2(1+R_e)/R_e + 2F_yb(2+R_e)D²/(3F_em l_s²)) | 12.17 |
| Mode III_s | 2 k₃ D l_s F_em / ((2+R_e) 3.2 K_θ) | **1,513.4 lb** |
| Mode IV | (2D²/(3.2K_θ)) √(2F_em F_yb/(3(1+R_e))) | 1,891.5 lb |

Z = 1,513.4 lb (mode III_s); 2 bolts × C_M 0.70 = **2,118.8 lb** against 538.95. Ratio **0.25**.

NDS §3.4.3.3. The west ropes sit at a₁ = 32.1", inside 5d = 56.25" of the ledger, so
V_r' = ⅔ F_v b d_e (d_e/d)². V there is the larger side, R₁ − w a₁ = **991.7 lb**.
- Bolts at mid-depth: d_e = 11.25/2 + 0.3125 = 5.94"; V_r' = ⅔ × 169.75 × 4.5 × 5.94 ×
  (5.94/11.25)² = **842 lb** → **1.18, OVER**.
- Bolt row centred **2 1/2" below the top**: d_e = 11.25 − (2.5 − 0.3125) = 9.06";
  V_r' = 4,615 × (9.06/11.25)² = **2,995 lb** → **0.33**.
- The east ropes at a₂ (94.1" from LDGE) are clear of 5d. V = |R₁ − w a₂ − 2P| = 402.9 lb
  against 4,615 lb, ratio **0.09**.

Edges (NDS Table 12.5.1A, perpendicular to grain): unloaded (top) 2.5" ≥ 1.5D = 0.94";
loaded (bottom) 8.75" ≥ 4D = 2.5". The saddle's legs run to 10 3/4" for this row.

### 3.7 The hardware
Crosby G-209 1/2" WLL 2 t = 4,409 lb against 538.95: ratio **0.12**. A shackle, never a
swivel: a 4-rope bed must not spin. The saddle has no published WLL and is graded through its
bolts. It is HDG to match the shackle, so there is no dissimilar pair.

## 4. Comparison (each line; both lines are the same)

| limit state | demand | capacity | ratio |
|---|---|---|---|
| bending | 4,698 lb-ft | 5,933 lb-ft | 0.79 |
| shear | 33.3 psi | 169.75 psi | 0.20 |
| LUS210-3Z at LDGW, C_M 0.70 | 1,125.5 lb | 1,281 lb | **0.88** |
| LUS210-3Z at LDGE | 795.1 lb | 1,281 lb | 0.62 |
| deflection under both loads | 0.199" | 0.421" | 0.47 |
| bolts, C_M 0.70 | 539 lb | 2,119 lb | 0.25 |
| NDS 3.4.3.3, west rope | 992 lb | 2,995 lb | 0.33 |
| NDS 3.4.3.3, east rope | 403 lb | 4,615 lb | 0.09 |
| shackle WLL | 539 lb | 4,409 lb | 0.12 |

**The west hanger governs at 0.88.**

## 5. Open: the ledger's Titen HDs under a concentrated reaction

`BM-SG-LDGW`'s anchors are a published read (`_LEDGER_ROW`, Simpson letter
L-A-THDSSLDGR23: 19" o.c. under a uniform 40 + 10 psf on an 18' joist span). The letter
publishes a spacing, not a per-anchor allowable, and no THD50600H6SS allowable is catalogued.
So this is an **estimate, not a grade**.
- The letter's own basis implies 50 × 18/2 = 450 plf of ledger, 450 × 19/12 = **712 lb per
  anchor**.
- At line 003 (and 006) the 3-ply end lands mid-way between two anchors 12" apart. The point
  part of R₁ is 1,125.5 − 421.4 = 704 lb, half to each, plus each anchor's own 450 lb of
  uniform: **~802 lb, about 1.13 of the implied figure** (~1.18 with §6's ply weight).
- The ledger's sole published spacing is exceeded locally, so this is an **owner and engineer
  question**. The cheap answer is one added THD50600H6SS each side of each 3-ply hanger, four
  in all, at the letter's own 4"-8" from the hanger and its edge distances. That fix is **not
  taken** in the model.

## 6. What is NOT graded here

- **The two added plies' self weight.** At 37.5 pcf, 4.4 plf a ply, 8.8 plf more than the
  10 psf dead load holds. It raises bending to ~0.84 and the west hanger to ~0.94. The
  hammock note leaves its LVL's weight out the same way.
- **Lateral sway.** The ropes hang plumb; a swing's horizontal component reaches the line as
  a sideways pull on the saddle, and nothing grades it. The plank diaphragm braces the line.
- **Load sharing** through the composite plank onto the 2x12s either side (beneficial, ignored).
- **Fatigue**, and the padeye weld, which the fabricator proof-loads to 2 × P.

## Sources

- AWC NDS 2018 Supplement Table 4B (Southern Pine, size-specific), its wet service factors;
  NDS 2018 §3.4.3.3, §12.3.1, Tables 11.3.3, 12.3.3A, 12.3.3B, 12.5.1A.
- Simpson Strong-Tie C-C-2021 p. 105, Face-Mount Hangers - Solid Sawn Lumber (DF/SP), LUS210-3
  row, read 2026-10-13 (the distributor copy of the Simpson table).
- Simpson Strong-Tie letter L-A-THDSSLDGR23 (the porch ledger's published spacing).
- Kito Crosby G-209 screw-pin anchor shackle, 1/2" (stock no. 1018455), read 2026-10-13.
- Atlantic Swing Co. Simon daybed swing, twin (theporchswingcompany.com), read 2026-10-13.
