# Column base rotation — the fixed base as a spring, hand-worked

**Oracle for** `engineering/base_rotation.py`, `engineering/base_supports.py` and
`engineering/base_spring.py`; reproduced by `tests/test_base_rotation_calcs.py`. Worked
2026-09-20 in a separate pass from the code, with a calculator and no engine import.

**What this is about.** `deck_post` magnifies each lateral-system column's moment for sway at
ACI Table R6.2.5's `k = 2.1` — a base that does not turn. `column_base` grades whether the
ground can hold the column up (strength). Neither says how far the base ROTATES first, and
on a shallow pole in presumptive soil that turns out to be the question that decides it.

---

> ⚠ **WITHDRAWN 2026-09-21 for the four LANDING columns** (`PT-BW-W`/`-E`/`-GW`/`-GE`): the landing
> is tied to the garage stem (`north_entry_piers.md` §10), so they lean and are no longer
> lateral columns; `base_rotation` stops enumerating them. Their rows below are history. `PT-BW-RE`/`-RNE`
> are untouched — the tie does not reach them (they stand 20' east, on the canopy's own line).

## 0. The answer

> **2026-09-21: `PT-BW-RE`/`-RNE` are graded OK (0.81) on a PRESUMED n_h, 8.10 pci —
> Terzaghi's loose dry sand (§10).** The band table below is still the no-report answer.

| column | base | δ_ref 0.25" | δ_ref 1.0" | verdict | turns at |
|---|---|---:|---:|---|---:|
| `PT-BW-RE` | 8.33' pole, 1.5' pad | δ 1.305 | δ 1.953 | **straddles** | 0.40" |
| `PT-BW-RNE` | 8.33' pole, 2.0' pad | δ 1.295 | δ 1.868 | **straddles** | 0.43" |
| `PT-BW-W` | 7.12' pole, 1.5' pad | δ 1.110 | δ 1.442 | **straddles** | 0.92" |
| `PT-BW-E` | 7.12' pole, 1.5' pad | δ 1.034 | δ 1.106 | ok — magnified d/c 0.157 | 3.2" |
| `PT-BW-GW` | 4.50' pole, 2.0' pad | δ **1.456** | **mechanism** | **OVER at both ends** | 0.23" |
| `PT-BW-GE` | 4.50' pole, 1.5' pad | δ 1.099 | δ 1.538 | **straddles** | 0.81" |
| `PT-SG-BF1`/`BF3` | W-SG-W1/E1 top | δ 1.044 | δ 1.045 | ok — d/c 0.169 | never |
| `PT-SG-BR1`/`BR3` | W-SG-W1/E1 top | δ 1.045 | δ 1.046 | ok — d/c 0.172 | never |

`δ` is ACI 318-19 §6.6.4.5.2's magnifier at the column's own `1.2D + 1.6L`; the verdict
fails where `δ > 1.4` (§6.2.5.3), where `Pu ≥ 0.75 Pc`, or where the magnified moment
exceeds φMn. With the base rigid, `deck_post` has these at δ 1.012–1.174.

**The balcony columns close; the north entry's do not close on presumptive soil.** Four
straddle the band — a measured modulus decides them — and `PT-BW-GW` is over §6.2.5.3 even
at the stiff end. That is a finding, not a tuning problem: §8 says what closes it.

## 1. The column on a spring

A free-top cantilever of length `L` and stiffness `EI` on a base spring `k_θ`:

```
R = k_θ L / EI
exact:   (μL) tan(μL) = R,  k = π / (μL)            R -> inf gives k = 2.0
graded:  Pc,flex = Pc,rigid · Δ_flex / Δ_total = Pc,rigid / (1 + 3/R)
         Δ_flex = PL³/3EI,  Δ_base = PL²/k_θ
```

`Pc,rigid` is `deck_post`'s own, at `k = 2.1`, and is **not changed**: it is the rigid-base
bound this record cites. The graded form is the smaller of the two at every `R` (at `R → 0`
it is `0.746 k_θ/L` against the exact `k_θ/L`; at `R → ∞` it keeps deck_post's 2.1 against
2.0), so the exact root is printed beside it and never graded.

`EI = 0.4 E_c I_g / (1 + β_dns)` with `β_dns = 1.2D / Pu` — deck_post's, verbatim.
`E_c = 57,000 √5,000 = 4.0305e6 psi`, `I_g = π·12⁴/64 = 1,017.9 in⁴`.

## 2. The soil, anchored in the code

No report is on file. IBC §1806.3.4 permits **two times** Table 1806.2's lateral bearing where
**1/2" of motion at the ground surface** is acceptable. Read as a secant:

```
n_h = 2 S1 / δ_ref          S1 = 150 psf/ft (class 4, GM)
δ_ref 0.25"  n_h = 300 / (0.25/12) = 14,400 lb/ft⁴   (8.33 pci at b = 1 ft)
δ_ref 0.50"                           7,200            (4.17 pci)
δ_ref 1.00"                           3,600            (2.08 pci)
δ_ref 2.00"  (sensitivity only)       1,800            (1.04 pci)
```

`p(z) = n_h · z · u(z) · b(z)`, per foot of width as §1807.3.2.1 is. Taking `u` at grade as
`δ_ref` everywhere is conservative: below grade a turning pole moves less, so the real secant
at depth is stiffer. For scale, Terzaghi (1955) gives n_h ≈ 7 tons/ft³ ≈ 8.1 pci for LOOSE dry
sand: the whole band sits at or below loose sand.

**The plan anchored on `S1`, not `2 S1`, and this note disagrees.** "n_h = k/δ_ref = 3,600
lb/ft⁴ at 0.5"" pairs the TABULAR value with the half inch; the section pairs the DOUBLED one
with it. The plan's reading equals this note's at twice the δ_ref, so under it every straddle
above moves stiffer-ward by a factor of two and `PT-BW-RE`/`-RNE` straddle harder (δ 1.467 at
the plan's own 0.25", 5.80 at its 1.0"). Neither reading closes the north entry.

The strip footing's vertical modulus is the same idea on the other axis: `k_v = q_a / δ_ref`,
`q_a = 2,000 psf`, the 1" end being Terzaghi & Peck's settlement criterion. §4 shows it barely
matters.

## 3. The pole, worked

A rigid pole from grade to the pad bottom, the shaft `b = 1.0'` and the pad at its LEAST plan
width (a column buckles about its own weakest axis). `u = u0 − θz`:

```
I1 = ∫ b z dz    I2 = ∫ b z² dz    I3 = ∫ b z³ dz    det = I1 I3 − I2²
ΣH = 0:  n_h (u0 I1 − θ I2) = H          ->  u0 = H (I3 + I2 h) / (n_h det)
ΣM = 0:  n_h (θ I3 − u0 I2) = H h        ->  θ  = H (I1 h + I2) / (n_h det)
```

The pad counts because `deck_post` grades the dowels developed into it (d/c 0.76); without
that the shaft stands alone. `k_θ = L² / Δ_base`, `Δ_base = u0 + θ h_head` under 1 lb at the
column head — the base spring that gives the same head drift.

### 3a. `PT-BW-RE`, δ_ref 1.0"

Grade −2'-10" (−2.8333'), pad −10'-2" to −11'-2": shaft 7.3333', pole 8.3333', pad 1.5'.
Head `198.75/12 − 7.3333 = 9.2292'` above grade.

```
I1 = 7.3333²/2 + 1.5(8.3333² − 7.3333²)/2                    = 38.639
I2 = 7.3333³/3 + 1.5(8.3333³ − 7.3333³)/3                    = 223.63
I3 = 7.3333⁴/4 + 1.5(8.3333⁴ − 7.3333⁴)/4                    = 1,446.97
det = 38.639 × 1,446.97 − 223.63²                            = 5,901
u0 = (1,446.97 + 223.63 × 9.2292) / (3,600 × 5,901)          = 1.653e-4 ft = 0.001983 in/lb
θ  = (38.639 × 9.2292 + 223.63) / (3,600 × 5,901)            = 2.731e-5 rad/lb
Δ_base = 0.001983 + 2.731e-5 × 9.2292 × 12                   = 0.005008 in/lb
k_θ = 198.75² / 0.005008                                     = 7.887e6 lb-in/rad
β = 1.2 × 2,351.2 / 7,538.3 = 0.3743    EI = 0.4 × 4.0305e6 × 1,017.9 / 1.3743 = 1.1941e9
R = 7.887e6 × 198.75 / 1.1941e9                              = 1.313
Pc,rigid = π² × 1.1941e9 / (2.1 × 198.75)²                   = 67,653 lb   (deck_post: δ 1.174)
Pc,flex  = 67,653 / (1 + 3/1.313)                            = 20,593 lb
δ = 1 / (1 − 7,538.3 / (0.75 × 20,593))                      = 1.953   > 1.4
```

At δ_ref 0.25" everything above scales by 4 in `n_h`: `k_θ = 3.155e7`, `R = 5.251`,
`Pc = 43,056`, `δ = 1.305`, magnified `12,257 × 1.305 / 25,380 = 0.630`. **One end passes,
one does not.** The exact spring root at 1.0" is `k = 3.32` — the base more than halves the
column's buckling load against the rigid 2.1.

> ⚠ **WITHDRAWN 2026-09-21 for the four LANDING columns** (`PT-BW-W`/`-E`/`-GW`/`-GE`): the landing
> is tied to the garage stem (`north_entry_piers.md` §10), so they lean and are no longer
> lateral columns; `base_rotation` stops enumerating them. Their rows below are history. `PT-BW-RE`/`-RNE`
> are untouched — the tie does not reach them (they stand 20' east, on the canopy's own line).

### 3b. `PT-BW-GW`, δ_ref 0.25" — over at the STIFF end

Pad −6'-4" to −7'-4": shaft 3.5000', pole 4.5000', pad 2.0' square. Head
`60.5/12 − 3.5 = 1.5417'` above grade. `Pu = 7,389.7 lb` (1.2D + 1.6L, as deck_post reads
it), `D = 1,319.1 lb`.

```
I1 = 3.5²/2 + 2(4.5² − 3.5²)/2 = 6.125 + 8.000           = 14.125
I2 = 3.5³/3 + 2(4.5³ − 3.5³)/3 = 14.292 + 32.167         = 46.458
I3 = 3.5⁴/4 + 2(4.5⁴ − 3.5⁴)/4 = 37.516 + 130.000        = 167.52
det = 14.125 × 167.52 − 46.458²                          = 207.78
per lb at the head, n_h 14,400:
u0 = (167.52 + 46.458 × 1.5417) / (14,400 × 207.78)      = 0.000959 in
θ  = (14.125 × 1.5417 + 46.458) / (14,400 × 207.78)      = 2.281e-5 rad
Δ_base = 0.000959 + 2.281e-5 × 18.5                      = 0.001381 in/lb
k_θ = 60.5² / 0.001381                                   = 2.650e6 lb-in/rad
β = 1.2 × 1,319.1 / 7,389.7 = 0.2142   EI = 1.3515e9 lb-in²
R = 2.650e6 × 60.5 / 1.3515e9                            = 0.1186
Pc,rigid = π² EI / (2.1 × 60.5)²                         = 826,366 lb   (deck_post: δ 1.012)
Pc,flex  = 826,366 / (1 + 3/0.1186)                      = 31,438 lb
δ = 1 / (1 − 7,389.7 / 23,578)                           = 1.456   > 1.4  -> d/c (0.456/0.4) 1.14
```

At 1.0" `Pc,flex = 8,090 lb` and `0.75 Pc = 6,068 < Pu`: a mechanism. The magnified MOMENT is
harmless (0.148) — it is the sensitivity §6.2.5.3 exists to forbid that fails. The exact
spring root gives `δ 1.305` at 0.25", under 1.4; the graded series form is 25% more
conservative at this small `R`, and it is what is graded because it keeps deck_post's 2.1.
**Read GW as at the edge at loose-sand stiffness and past it at anything softer.**

### 3c. The rest, same arithmetic

| column | δ_ref | n_h pci | R | Pc,flex lb | δ | magnified d/c |
|---|---:|---:|---:|---:|---:|---:|
| `PT-BW-RNE` | 0.25 / 1.0 | 8.33 / 2.08 | 5.639 / 1.410 | 44,160 / 21,628 | 1.295 / 1.868 | 0.625 / 0.902 |
| `PT-BW-W` | 0.25 / 1.0 | | 1.292 / 0.323 | 104,474 / 33,733 | 1.110 / 1.442 | 0.149 / 0.193 |
| `PT-BW-E` | 0.25 / 1.0 | | 1.591 / 0.398 | 97,668 / 32,990 | 1.034 / 1.106 | 0.147 / 0.157 |
| `PT-BW-GE` | 0.25 / 1.0 | | 0.135 / 0.034 | 29,603 / 7,647 | 1.099 / 1.538 | 0.118 / 0.165 |

Inputs as deck_post reads them: `W` Pu 7,760.0, D 1,627.7, φMn 25,438; `E` Pu 2,377.5, D 1,072.9,
φMn 24,029 (both L 91.94", Mu 1.6 × 2,132.3 guard); `GE` Pu 2,007.1, D 764.3, φMn 23,932, pad
1.5'; `RNE` as RE with a 2.0' pad. Pad bottoms −9.953' (W/E), −7.333' (GW/GE).

## 4. The wall-borne balcony columns, worked

`PT-SG-BF1` stands on `W-SG-W1`: 12" concrete at f'c 5,000, 109.44" from footing to head,
held at its head by the porch diaphragm (`lateral_support="top_and_bottom"`), on the 84" × 12"
`FT-SG-W1`. The strip is the column's own 12" — no spread credited.

```
EI_wall = 0.35 × 4.0305e6 × (12 × 12³/12)                = 2.4377e9 lb-in²   (Table 6.6.3.1.1(a))
4EI/H = 8.9097e7    2EI/H = 4.4549e7    3EI/H = 6.682e7   lb-in/rad
k_v (1.0") = 2,000 / (1/12) = 24,000 lb/ft³
k_f = k_v · b · B³/12 = 24,000 × 1 × 7³/12 = 686,000 lb-ft = 8.232e6 lb-in/rad
k_θ = 8.9097e7 − (4.4549e7)² / (8.9097e7 + 8.232e6)      = 6.8707e7 lb-in/rad
β = 1.2 × 1,544.8 / 4,947.2 = 0.3747   EI_col = 1.1937e9
R = 6.8707e7 × 108.125 / 1.1937e9                        = 6.223
Pc,rigid = 228,514    Pc,flex = 228,514 / (1 + 3/6.223)  = 154,187 lb
δ = 1 / (1 − 4,947.2 / 115,640)                          = 1.0447
magnified = 4,003.3 × 1.0447 / 24,702.5                  = 0.169
```

At 0.25" `k_f = 3.293e7`, `R = 6.597`, `δ = 1.0438`. A footing that resisted no rotation at
all (`3EI/H`) still gives `R = 6.05`. **The soil does not decide the balcony**; the wall's
own flexibility does, and it is small. `PT-SG-BR1` (L 109.96", Pu 4,968.7, D 1,562.8):
`R 6.341`, `δ 1.0463`, magnified 0.172. This answers `column_support`'s third sub-question —
the foundation's rotational restraint — and not its first two.

## 5. Where the sway comes from, and the motion at grade

`PT-BW-GW` under the R301.5 guard push, 200 lb at 8.04' above its base (4.54' above grade),
pad width normal to the motion 2.0':

| δ_ref | u0 at grade | at the column head, ground | column's own flexure |
|---:|---:|---:|---:|
| 0.25" | 0.304" | 0.440" | 0.0207" |
| 0.50" | 0.607" | 0.881" | 0.0207" |
| 1.00" | 1.214" | 1.762" | 0.0207" |

Flexure: `200 × 60.5³/(3 EI) + 200 × 36 × 60.5²/(2 EI) = 0.0109 + 0.0098 = 0.0207"`, the push
taken at the head with its 36" rail arm. **All of this column's sway is the ground turning** —
twenty to eighty-five times its flexure. Grading it at `k = 2.1` was numerically harmless (δ 1.012)
and conceptually backwards.

**The motion at grade is not independent evidence for §1806.3.4.** At 0.5" the push moves the
ground surface 0.61" — but the modulus was calibrated on the half inch, so a pole loaded near
its §1807.3.2.1 capacity reproducing roughly that motion is the calibration agreeing with
itself, to about 20%. The plan predicted 0.21" here; see §7.

Rigid-pole validity (Matlock & Reese, rigid below about `D/T = 2`, `T = (EI/n_h)^(1/5)`):
GW `T = 3.65'` at 0.25", `D/T = 1.23`; RE at 1.0" `T = 4.70'`, `D/T = 1.77`. Rigid holds where
the verdict is decided; at RE's stiff end `D/T ≈ 2.3` and the shaft's own bending would soften
it slightly, which is the passing end.

## 6. Where it turns

The δ_ref at which each verdict changes, by bisection on the same arithmetic: RE 0.40",
RNE 0.43", W 0.92", E 3.2", GW **0.23"**, GE 0.81"; the balcony never. At the 2.0" sensitivity
RE is δ 5.80 (d/c 2.80), GW is a mechanism, GE is δ 3.29 and E is still δ 1.22. Recorded,
never a band end.

## 7. Where this note and the plan disagree

The plan predicted `PT-BW-RE`/`-RNE` d/c 0.567 → **0.635** at 0.5", `PT-BW-GW` 0.103 →
**0.135**, "0.044" of flexure against 0.73" of base rotation" and "0.21" at grade", and every
verdict passing the band. Worked here: at its stated `n_h = 3,600 lb/ft⁴` RE is δ 1.953 (d/c
0.943, over §6.2.5.3) and GW is a mechanism. The plan's RE figure is approximately
reproduced at `n_h ≈ 14,400` — four times its stated modulus, this note's STIFF end (RE
0.630) — and its GW figures at no single modulus (at 14,400: d/c 0.148, 0.30" at grade, 0.44"
at the head). **This note is believed**: the two-equation solve is checked in §3a line by
line, and the plan's figures are not reachable from its own stated inputs. The plan also did not grade §6.2.5.3's 1.4, which is what decides three of the six.

## 8. What closes it

- **A geotechnical report** — and until one, a presumed table row (§10, done 2026-09-21).
  `Site.lateral_subgrade_modulus = SubgradeModulus(n_h_pci=…,
  source=…, basis=…)` re-grades every record with no code change. At the turning points of
  §6 (`n_h = 2 S1 / δ_ref`): RE needs about 5.2 pci, RNE 4.8, W 2.3, GE 2.6, E 0.6 — and GW
  about 9.2, denser than Terzaghi's loose sand.
- **A stiffer base**: deeper or wider pads on the landing pair. Deepening GW also lengthens
  it, so at δ_ref 1.0" a 6.0' pole gives δ 1.88 and a 7.0' pole 1.41 — W's depth, and W
  itself straddles. It reaches the hydrant cone the entry note records
  (`entry_column_base_fixity.md` §6e). A measured modulus is the cheaper answer.
- **The storey sum** of §6.6.4.6.2 for the four landing columns, which share one deck: at
  1.0" `ΣPu = 19,534`, `0.75 ΣPc = 61,845`, δ_s 1.46 — still over 1.4, so it helps W and GE
  and does not close the storey. Not graded (the record magnifies each column alone, as
  deck_post does).

## 9. What this does NOT settle

- **How the base moment splits between the buried shaft and the pad.** The pole carries it
  wholly in lateral bearing; the pad's own bearing on the soil below is a second, parallel
  spring and is left out (conservative for sway). Counting the pad as part of the pole
  (`column_base`, 2026-09-20) makes it part of one body; it does not divide one moment
  between two mechanisms, and that division is a soil-structure interaction problem.
- **The coupling with the §1604.4 split.** Flexible bases make the canopy columns less rigid,
  so they would take LESS of the canopy's shear — conservative for them, unconservative for
  `W-BW-SCREEN` and the deck, which `lateral_system` grades at the share a rigid base gave
  them. The split is not re-run.
- A linear secant stands in for a p-y curve; creep under sustained load; `β_ds` (deck_post's
  `β_dns` is used, conservative for wind); group effect.
- For the balcony: the wall top's capacity and the dowels' development
  (`column_support/W-SG-*`), and the diaphragm at the wall head, taken as declared.

## 10. The presumed n_h — RE and RNE close as draft (2026-09-21)

**No report still.** The owner's call: grade on a presumptive PUBLISHED value, marked
presumed, so the rows close as draft and the gap register keeps the report owed.

**The value.** Terzaghi (1955), Géotechnique 5(4), n_h for piles in cohesionless soil, row
**"dry or moist sand, loose": 7 tons/ft³** (as reproduced in Table 2 of
https://gnpgroup.com.my/wp-content/uploads/Publication/2009_11.pdf). `7 × 2,000 / 1,728 =
8.10 pci`. Two presumptions, both stated on the record: GM (silty gravel, glacial till) is
read at the LOOSEST cohesionless row, and it is **above groundwater** — none is established;
the submerged loose row, 4 tons/ft³ = 4.63 pci, would be under RE's 5.2 turn (§8) and would
condemn both columns. Authored on `Site.lateral_subgrade_modulus` beside workstream C's
presumed k_v, `provenance="presumed"`.

**Width.** Terzaghi's is `k_h = n_h z / B`: the reaction per unit length `n_h z y` does not
grow with width. So a STATED n_h is integrated at 1 ft on every segment — exact for the 12"
shaft, and the pad earns no width credit (basis 2). The IBC band keeps its width scaling,
because §1807.3.2.1 is a pressure.

`PT-BW-RE`, n_h = 14,000 lb/ft⁴ at b = 1 ft; shaft 7.3333', pole 8.3333', head 9.2292':

```
I1 = 8.3333²/2 = 34.722   I2 = 8.3333³/3 = 192.90   I3 = 8.3333⁴/4 = 1,205.6
det = 34.722 × 1,205.6 − 192.90²                          = 4,651
u0 = (1,205.6 + 192.90 × 9.2292) / (14,000 × 4,651)       = 4.586e-5 ft = 5.503e-4 in/lb
θ  = (34.722 × 9.2292 + 192.90) / (14,000 × 4,651)        = 7.884e-6 rad/lb
Δ_base = 5.503e-4 + 7.884e-6 × 9.2292 × 12                = 1.4234e-3 in/lb
k_θ = 198.75² / 1.4234e-3                                 = 2.775e7 lb-in/rad
R = 2.775e7 × 198.75 / 1.1941e9                           = 4.618
Pc,flex = 67,653 / (1 + 3/4.618)                          = 41,015 lb
δ = 1 / (1 − 7,538.3 / (0.75 × 41,015))                   = 1.3246
```

Second-order increment `0.3246 / 0.40 = 0.81` (governs); sway stability `7,538 / 30,761 =
0.245`; magnified moment `12,257 × 1.3246 / 25,380 = 0.640`. **OK.** `PT-BW-RNE` is the same
column on the same pole — the 2.0' pad earns no width — so the same numbers, **OK at 0.81**.
The balcony's wall-borne columns take the presumed k_v (88.4 pci) and stay OK at 0.17.

**What stays open, and says so.** Each record carries `n_h_presumed = 1` and a PRESUMED note,
and `out/calcs/03-open-items.md` lists both under "D. Graded on a presumed input" until a
report replaces the value. Two cautions: (1) Matlock & Reese's rigid-pole check at 8.10 pci
on the column's reduced EI gives `T = (8.29e6 / 14,000)^0.2 = 3.59'`, `D/T = 2.32` — just
past "rigid below about 2", so the pole's own flexure is not zero; (2) a report that finds
groundwater within the pole's depth moves the row to the submerged column.

## Sources

- ACI 318-19 §6.2.5.3 (second-order moment ≤ 1.4 first-order), §6.6.4.4.4, §6.6.4.5.2,
  Table 6.6.3.1.1(a), Table R6.2.5.
- IBC 2018 §1806.2, Table 1806.2, §1806.3.4, §1807.3.2.1.
- Terzaghi, K. (1955), "Evaluation of coefficients of subgrade reaction", Géotechnique 5(4).
- Terzaghi & Peck, *Soil Mechanics in Engineering Practice* — the 1" settlement criterion.
- Matlock & Reese (1960), rigid/flexible pile classification by `T = (EI/n_h)^(1/5)`.
- Tan et al. (2009), Table 2 (Terzaghi 1955 n_h, dry/submerged sand): https://gnpgroup.com.my/wp-content/uploads/Publication/2009_11.pdf
- Timoshenko & Gere, *Theory of Elastic Stability* — the cantilever on an elastic base.

## Addendum 2026-09-22 — the balcony columns at the 17'-0" court

The balcony joists span 18'-0" on two beams, so each corner column's P_u is 7,886 lb (BF) and
7,907 lb (BR) where §4 worked a smaller load. By §4's own method the magnifier δ at the band
ends is **1.0686 / 1.0701 (BF1/BF3)** and **1.0710 / 1.0725 (BR1/BR3)**, up from 1.044–1.046.
No verdict moves; `tests/test_base_rotation_calcs.py` carries the re-derived figures.
