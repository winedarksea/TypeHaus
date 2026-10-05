# Living-room hammock chair anchor — hand-worked basis

**House:** catlin
**Structure:** `HA-M-HAMMOCK` carrying `FURN-M-HAMMOCK` (`plan/living_hammock.py`), framed as
FS-S-EAST's joist line 003 upgraded to a `2-1.75x11.875 LVL`.
**Written:** 2026-10-05, by hand, before the calculation it oracles was encoded.
**Oracle for:** `checks/structural/_suspension_math.py`, reported by
`structural.suspension_anchor`; reproduced by `tests/test_suspension_anchor.py`.
**Companions:** `notes/framing_bore_limits.md` — what a trade may cut from the same field.
**What is asked of the reviewer:** whether the impact factor in §2 is the right dynamic
basis for a hung seat. The arithmetic in §3–§4 is the NDS's and ESR-1387's own.

> ⚠ The saddle's bolts sit at the LVL's **mid-depth, never lower** (§3.6). NDS §3.4.3.3
> credits only the depth above a hanging connection, so a bolt row near the bottom edge
> gives up more than half the member's shear capacity there.
>
> ⚠ The rating is the design basis, not the size reference. The La Siesta Habana Comfort
> the chair is sized from is rated 285 lb. The chair bought must state **360 lb or more**.

This is furniture, not engineering. No seal is asked for and nothing here is on the
`haus engineering` register. The check exists so the hang point is graded, not assumed.

---

## 1. Geometry

| term | working | value |
|---|---|---|
| hang point | chair at (26'-10", 4'-0"), offset 0 | x = 322", y = 48" |
| joist line | FS-S-EAST lines at 0, 16, 32, **48**, 64" ... : the station is on line 003 | upgraded, not moved |
| span L | bearing axes W-M-C2 (x = 18'-0") to W-M-E1 (x = 36'-0") | 216" |
| load station a | 322 − 216 | 106" from W-M-C2 |
| b | 216 − 106 | 110" |
| member | 2 plies of 1.75 x 11.875 Microllam LVL | b = 3.5", d = 11.875" |
| S | 3.5 × 11.875² / 6 | 82.26 in³ |
| I | 3.5 × 11.875³ / 12 | 488.4 in⁴ |
| tributary | half of each 16" bay | 16" |
| bearing at W-M-C2 | `end_bearing` authored in `params/second_deck.py` | 2.0" |
| bearing at W-M-E1 | the wall's 2x6 structure layer | 5.5" |
| wall clearance | 48 − 6 5/8 (south finish face) | 41.4" ≥ 35.5" |

## 2. The demand

| term | working | value |
|---|---|---|
| rated occupant load | owner, two people | 360 lb |
| impact factor | `preferences.toml [structural] hanging_seat_impact_factor` | 2.0 |
| chair | Habana Comfort reference, 2.6 kg | 5.7 lb |
| swivel | Crosby 3-S-5, 3.86 kg | 8.5 lb |
| saddle | 16.5 in³ plate × 0.284 lb/in³ + bolts | 6.0 lb |
| **P** | 360 × 2.0 + 5.7 + 8.5 + 6.0 | **740.2 lb** |
| floor w | (40 live + 10 dead psf) × 16/12 ft | 66.7 plf = 5.556 lb/in |

**Why 2.0.** A load applied suddenly from rest, with no drop height, produces twice the
static force in a linear member: the classical suddenly-applied-load result. That is a
person dropping into the seat. A swing at small amplitude adds less than that. ASCE 7-16
§4.6 publishes no factor for a hung seat, so the house authors one.

The 40 psf floor live load is taken concurrent with the occupants, which is conservative.

## 3. Capacity and the limit states

Design values: ICC-ES ESR-1387 Table 1, Microllam LVL 2.0E-2600Fb WS, joist orientation:
Fb 2,600, Fv 285, Fc⊥ 750, E 2.0×10⁶ psi. C_D = 1.0 throughout, because the impact factor
is already on the load.

### 3.1 Reactions
R₁ = P·b/L + wL/2 = 740.2 × 110/216 + 5.556 × 108 = 376.9 + 600.0 = **976.9 lb** (W-M-C2)
R₂ = P·a/L + wL/2 = 740.2 × 106/216 + 600.0 = **963.3 lb** (W-M-E1)

### 3.2 Bending
M at the load = R₁·a − w·a²/2 = 976.9 × 106 − 5.556 × 106²/2 = 103,557 − 31,213
= 72,344 lb-in = **6,029 lb-ft**. (The shear zero of each segment lies outside it, so the
load point is the maximum.)
C_V = (12/11.875)^0.136 = 1.0014 → Fb' = 2,603.7 psi; M' = 2,603.7 × 82.26 = 214,178 lb-in
= **17,848 lb-ft**. Ratio **0.34**.

### 3.3 Shear
f_v = 1.5 R₁ / (b d) = 1.5 × 976.9 / 41.56 = **35.3 psi** against 285. Ratio **0.12**.

### 3.4 Bearing
W-M-C2: 976.9 / (3.5 × 2.0) = **139.6 psi** against 750, ratio **0.19**.
W-M-E1: 963.3 / (3.5 × 5.5) = **50.0 psi**, ratio **0.07**.

### 3.5 Deflection under P alone
Bending at the load point: P a² b² / (3 E I L)
= 740.2 × 106² × 110² / (3 × 2.0×10⁶ × 488.4 × 216) = **0.159"**.
Shear (ESR-1387 Table 1 note 5 gives 28.8 W L²/(E b d) for a uniform load, which fixes
κG = 1.5E/28.8 = E/19.2): P a b / (L κG A) = 740.2 × 106 × 110 × 19.2 / (216 × 2.0×10⁶
× 41.56) = **0.009"**.
Total **0.168"** against L/480 = 0.450". Ratio **0.37**, about L/1,290. **This governs.**

### 3.6 The bolts, and where they sit
Two 5/8" A307 bolts, double shear, 1/4" A36 side plates, load perpendicular to grain.
NDS 2018 §12.3.1, θ = 90° so K_θ = 1.25; ESR-1387 Table 2: bolts in the face, G = 0.50.

| term | working | value |
|---|---|---|
| F_em | 6,100 × 0.50^1.45 / √0.625 | 2,824 psi |
| R_e | 2,824 / 87,000 | 0.0325 |
| Mode I_m | D l_m F_em / (4 K_θ) = 0.625 × 3.5 × 2,824 / 5 | **1,235.6 lb** |
| Mode I_s | 2 D l_s F_es / (4 K_θ) = 2 × 0.625 × 0.25 × 87,000 / 5 | 5,437.5 lb |
| k₃ | −1 + √(2(1+R_e)/R_e + 2F_yb(2+R_e)D²/(3F_em l_s²)) = −1 + √(63.61 + 134.94) | 13.09 |
| Mode III_s | 2 k₃ D l_s F_em / ((2+R_e) 3.2 K_θ) | 1,421 lb |
| Mode IV | (2D²/(3.2 K_θ)) √(2 F_em F_yb / (3(1+R_e))) | 1,769 lb |

Z = 1,235.6 lb per bolt (mode I_m); 2 bolts = **2,471 lb** against 740.2. Ratio **0.30**.
The two bolts are one row ACROSS the load, so C_g = 1.0; 4" apart (6.4D) and 5.9" from
either edge clears every NDS Table 12.5.1 minimum.

NDS §3.4.3.3, connection more than 5d (59") from either end: V_r' = ⅔ F_v b d_e, with d_e
the depth below the unloaded TOP edge to the bolt hole's top: 11.875/2 + 0.625/2 = 6.25".
V_r' = ⅔ × 285 × 3.5 × 6.25 = **4,156 lb**. V at the connection = max(R₁ − w a, R₂ − w b)
= max(976.9 − 588.9, 963.3 − 611.1) = **388.0 lb**. Ratio **0.09**. A row at the 4D minimum
edge distance above the bottom would leave d_e = 11.875 − (11.875 − 2.5 − 0.3125) = 2.81" and
V_r' = 1,870 lb: still passing here, at less than half the capacity. That is the warning above.

### 3.7 The hardware
Crosby 3-S-5 WLL 3 t = 6,614 lb (5:1 design factor) against 740.2: ratio **0.11**. The
saddle has no published WLL and is graded through its bolts (§3.6); its padeye weld is the
fabricator's, proof-loaded to 2 × P.

## 4. Comparison

| limit state | demand | capacity | ratio |
|---|---|---|---|
| bending | 6,029 lb-ft | 17,848 lb-ft | 0.34 |
| shear | 35.3 psi | 285 psi | 0.12 |
| bearing, W-M-C2 | 139.6 psi | 750 psi | 0.19 |
| bearing, W-M-E1 | 50.0 psi | 750 psi | 0.07 |
| deflection under P | 0.168" | 0.450" | **0.37** |
| bolts | 740 lb | 2,471 lb | 0.30 |
| NDS 3.4.3.3 | 388 lb | 4,156 lb | 0.09 |
| swivel WLL | 740 lb | 6,614 lb | 0.11 |

**Deflection governs at 0.37.** Everything passes with room for a rating to 2× this one.

## 5. What is NOT graded here

- **The LVL's extra self weight.** A 2-ply line weighs about 12 plf against an I-joist's 3 plf,
  which the 10 psf dead load already holds. The extra 9 plf raises bending to about 0.36.
- **Load sharing.** The subfloor spreads P onto the I-joists either side (beneficial, ignored),
  and the stiffer LVL draws a little floor load off them (adverse, ignored). Both are small at
  these ratios.
- **Fatigue and vibration.** A swing is cyclic; nothing grades it, and at 0.37 of an L/480 limit
  it is not a question that needs one.
- **The padeye weld and the swivel's shackle**, which the fabricator and Crosby's own pin rating
  carry.

## 6. The ceiling

The main-floor ceiling under FS-S-EAST is 5/8" gypsum screwed straight to the joists. The
saddle's 1/4" bottom plate sits under the LVL, so the board is cut round it and the swivel
eye drops through a trim escutcheon (drawn by `resolve/suspension.py` as the canopy). The
gypsum carries nothing; nothing hangs from a screw in it.

## Sources

- ICC-ES ESR-1387 (Weyerhaeuser), reissued Feb 2025, revised Jul 2026 — Table 1 (Microllam
  LVL design values, note 5 deflection, note 7 C_V) and Table 2 (fastener specific gravity).
- AWC NDS 2018 §3.4.3.3 (shear at connections), §12.3.1 (yield limit equations), Table 12.3.3
  footnote 2 (dowel bearing perpendicular to grain), Table 12.3.3B (A36 F_e = 87,000 psi),
  Table 12.5.1 (spacing, edge and end distances).
- Kito Crosby, S-5 Eye & Eye product page, 3-S-5 / stock no. 297057, read 2026-10-05.
- La Siesta, Habana Comfort hammock chair product data (lasiesta.com), read 2026-10-05.
