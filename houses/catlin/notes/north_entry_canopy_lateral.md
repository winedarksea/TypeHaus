# North entry canopy — §8, the rest of the lateral path, hand-worked

**This is §8 of `north_entry_structure.md`**, split out because that note was 429 lines and
this section is 200 more. It is the **oracle for the collector, anchorage and torsion rows of
`engineering/lateral_system.py`** (with `engineering/holdown_anchor.py` and
`engineering/torsion.py`), reproduced by `tests/test_lateral_system_calcs.py`.

`entry_column_base_fixity.md` §7 is the other half and comes first: it works the wind, the
propped shafts, the three stiffnesses, the rigid/flexible test, the shares, and the deck and
panel limit states. Everything below starts from §7's own numbers and adds nothing to them.

Geometry, read off the model (feet, house coordinates):

| | |
|---|---|
| roof footprint | x 4.667 → 31.333 (26.667' wide), y 37.219 → 43.219 (6.000' deep) |
| N-S lines | `W-BW-SCREEN` at x = 6.000; `PT-BW-RE` + `PT-BW-RNE` at x = 30.000 |
| E-W lines | `PT-BW-RE` at y = 37.500, `PT-BW-RNE` at y = 42.479 |
| stiffnesses | columns 1,567.7 lb/in each (gross) / 1,097.4 (0.70 I_g); panel 9,970.5 lb/in at its settled N-S share, 10,315.3 at the cracked-column share |
| shears at the deck | E-W 821.3 lb, N-S 1,189.4 lb ASD, of which 192.0 lb is the two columns' propped head reactions (96.0 lb each, at x = 30 / at their own y) |

## 8a. What §7 left ungraded, and why each of these is a row

§7 graded the deck and the panel. Four things it named and did not grade:

1. the **chord force**, 594.7 lb N-S / 19.2 lb E-W, printed as an input;
2. the **collectors** — `DiaphragmSpec.collector_refs` names two headers and nothing grades
   the member or, more to the point, the **connection at each end of it**;
3. the **concrete under the hold-down** — ESR-1622 §5.6 puts the anchor bolt and its footing
   outside its own scope, so the `ABU66SS` row stops at the stirrup;
4. **torsion** — §7d decided the deck is RIGID in both directions (0.68× N-S, 0.12× E-W), and
   a rigid deck distributed by rigidity alone is only in equilibrium if the load resultant
   passes through the stiffness centroid. It does not (§8g), and the note in
   `diaphragm_basis.rigidity_shares` saying two lines "cannot resist a torsional moment at
   all" is wrong: two parallel lines resist a torsional moment as a **couple**. What they
   cannot resist is translation across themselves, which is a different sentence.

## 8b. The chord — delegated to the truss fabricator, not computed

The N-S chords are the **top chords of the two end trusses**: 24 feet of 2x4, one plated
splice at the peak, carrying `V L / (8 W)` = 1,189.4 × 24.0 / (8 × 6.0) = **594.7 lb** of
axial force, tension in one chord and compression in the other, **in addition to the gravity
and drift case the chord is already designed for**. The E-W chords are the 3-ply 2x12 headers
at 821.3 × 4.979 / (8 × 26.667) = **19.2 lb**, which is nothing.

A truss chord is not a member this engine may size: its axial capacity comes out of the
fabricator's own plate, web and lateral-brace layout at the same section, and the combined
axial + bending interaction is the fabricator's chart. So the 595 lb goes on the **truss
order** (S-001) through the existing `rafter/RF-BW-CANOPY` deferral rather than into a limit
state here — the fabricator who seals the component design is the same person who answers it.

Two things ride with it and are stated on the order, not assumed:

* **the splice.** One plated splice at the peak has to carry the full 595 lb in tension.
* **0.03" of splice slip is an ASSUMPTION and it is load-bearing.** It is the third term of
  SDPWS 4.2.2 (`ShearPanelSpec`/`DiaphragmSpec.chord_splice_slip`), it is 30% of the deck's
  N-S deflection (0.030" of 0.099"), and the deflection is what decides the rigid/flexible
  call at 0.68× of the 2.0× threshold. A fabricator's splice detail that slips materially
  more moves §7d, and §7d moves the shares. It cannot be quietly relaxed.

## 8c. The west collector — zero drag, and it is geometry that makes it zero

A collector drags the deck's boundary shear along the support line into the part of the line
that actually resists. The west line's resisting element is `W-BW-SCREEN`, which runs from
y = 36.646 to y = 43.219: **6.573' long against a 6.000' deck depth**, and the 6.000' of deck
edge lies entirely within it. Every foot of the deck's west boundary lands directly on the
panel's top plate, so the drag length is zero and the drag force is

```
drag = v x (W - L_panel over W) = 150.8 plf x 0.000' = 0 lb
```

Graded at zero, and the row is a **detailing** row (deck edge covered / panel run overlapping
it, 6.000' / 6.000' = 1.00) rather than a force, because there is no force. The panel's own
top plate is the chord and the collector both, and the shear enters it through the same
boundary nailing §7 already graded.

## 8d. The east collector — the connection, not the member

The east line is `BM-BW-RE`, a 3-ply 2x12 spanning 4.979' between the two cast columns and
running 8 7/8" past the north one. In the **N-S** case it is the collector: it gathers the
deck's east boundary shear over 6.000' of depth and delivers it to two columns. The member
itself is a 4.5" x 11.25" section carrying a few hundred pounds of axial force — 0.007 ksi,
not a question. The connection is.

Each column's head takes its own share, **with torsion (§8g)**:

```
N-S, per column   direct 0.1196 x 1,189.4 = 142.3 lb  +  torsion 200.2 lb  =  342.5 lb
E-W, per column   direct 0.500  x   821.3 = 410.7 lb  +  torsion   0.4 lb  =  411.1 lb
```

The head is an `SS316-SHIM-35` pack and a **cast-in `HETA20Z` pair** (`params/column_heads.py`,
Simpson FL11473 Table 3, double HETA into concrete, 2- or 3-ply SP: uplift 2,560, F1 1,350,
F2 1,430 lb, the +60% wind increase already in them). FL11473-R4 §9 Limitations item 4 states
the interaction directly, and it is the interaction that has to be graded rather than the
lateral alone, because the same connector is carrying uplift in the same wind:

```
uplift    0.6D + 0.6W on 40.0 ft2 of roof             433.2 lb  / 2,560 = 0.169
F1  (parallel to the header, N-S)                     342.5 lb  / 1,350 = 0.254
F2  (perpendicular, the torsional couple's own share)   27.3 lb  / 1,430 = 0.019
                                                               unity  =  0.442
```

0.44 against 1.0. The **E-W** case, where the same connector sees 411 lb perpendicular to the
header and the same uplift, reads 0.169 + 411/1,430 = 0.456 on the true F2 and 0.169 +
411/1,350 = **0.473** as `column_head_joint/PT-BW-RE` grades it — that record takes the lower
of F1/F2 so no direction needs knowing. E-W is the governing direction for the connector and
is already on that record, which is why this row is written for the N-S case the collector is
about.

## 8e. The north line — no canopy member, so the collector is the strap line

The **E-W** case's support line at the north is y = 42.479 (the north columns), and the load
has to reach `PT-BW-RNE` along it. There is no canopy member on that line: the fourth truss
was dropped in 2026-09-11 (§1), so what carries in-plane force across the north edge is the
**seven `LSTA24` straps `CN-BW-JOINT-1..7`** at 4'-0" o.c. into `RF-GARAGE`'s gable truss,
which is the E-W member that collects it.

```
E-W reaction at the north line        411 lb (0.500 x 821.3, torsion +0.4)
strap line, first strap to last       24.0'
                                      411 / 24.0 = 17.1 plf   (the JOINT_TIES comment's
                                                               "near 18 plf", now computed)
per strap                             411 / 7    = 58.7 lb   vs 1,235 lb allowable
```

`allowable_for_model("LSTA24")` is **ICC-ES ESR-2105 (reissued January 2026) Table 3**:
20 ga, 18–10d×2½ common, 1,235 lb at C_D 1.6, footnote 5 (the value is governed by steel
strength and carries no duration increase), footnote 2 (wood of assigned SG ≥ 0.50 — these
land in southern pine). d/c **0.048**: nominal continuity, exactly as it was sized to be.

Three things this row states rather than hides:

* **The force is ALONG the joint, not across it, and ESR-2105 publishes tension.** A strap
  laid across a joint and loaded parallel to it works through the same nail group: footnote 4
  derives the tabulated connection strength as the nail count times the NDS yield-mode value,
  and for a 0.148" nail (d < 1/4") NDS dowel bearing is independent of the angle to grain, so
  the group is no weaker this way. The tabulated 1,235 lb is itself the **steel** value, below
  that group. At 58.7 lb per strap none of this is close.
* **The E-W north-line path crosses into `RF-GARAGE`.** The canopy is freestanding for
  gravity and for the N-S case; this one E-W reaction is collected by the garage's gable
  truss and returned across the strap line. `houses/catlin/CLAUDE.md`'s "freestanding" is
  amended to say so.
* **`H2.5ASS` is not a collector.** Those are truss-to-header uplift ties (110 lb F1/F2 in
  the stainless parity letter) and nothing here asks them to drag anything.

## 8f. The concrete under the hold-down — ACI 318-19 Ch. 17

`W-BW-SCREEN`'s hold-downs are the two `ABU66SS` bases `CN-BW-BASE-W`/`-NW` under
`PT-BW-CW`/`-CNW`, standing on the tops of the 12" round piers `PT-BW-W` and `PT-BW-GW`, each
on one cast-in **`AB-058-10-SS`, 5/8" x 10", 304 stainless**. ESR-1622 §5.6: "The design of
anchor bolts and the concrete footings is outside the scope of this report." So it is a
design, and this is it.

**The embedment, derived rather than assumed.** 10" of bolt, less the projection above the
pour (7 ga base plate 0.179" + washer 0.134" + heavy hex nut 0.609" + two threads 0.18", call
it 1½" with the adjustment the ABU wants), less the embedded nut's own thickness 0.609":
**h_ef = 7.891"**. f'c = 5,000 psi (`PIER_CONCRETE_12`), **cracked**, condition B (no
supplementary reinforcement credited — the (4) #5 cage is not developed as anchor
reinforcement), λ = 1.0.

**The edge distance is the whole calculation.** A 12" round pier with the bolt at its centre
gives **c_a = 6" in every direction**, on all sides at once.

```
17.6.2.1.2   three or more edges under 1.5 h_ef, so h_ef' = max(c_a,max/1.5) = 4.000"
             A_Nc = pi (6.0)^2 = 113.1 in2   A_Nco = 9 (4.0)^2 = 144.0    ratio 0.785
             psi_ed,N = 1.0 (c_a = 1.5 h_ef')     N_b = 24 sqrt(5000) (4.0)^1.5 = 13,576 lb
             N_cb = 10,663 lb        phi N_cb = 0.70 x 10,663 = 7,464 lb
unreduced    A_Nc / A_Nco = 113.1 / 9(7.891)^2 = 0.202   psi_ed,N = 0.852
             N_b = 37,452 lb         phi N_cb = 4,528 lb
```

**The unreduced reading is the one graded, and that is a deliberate choice.** §17.6.2.1.2
exists because the 1.5h_ef projection over-predicts the loss of capacity in a narrow member,
and applying it is correct and gives 7,464 lb. Taking the **lower** of the two is a bound
rather than a reading, in the same spirit as the solid-sign wind surrogate this canopy's whole
demand is built on, and 4,528 lb is still four times the demand — so the conservatism costs
nothing and the record prints both terms.

```
pullout     A_brg = 0.866(1.0625)^2 - pi/4 (0.625)^2 = 0.671 in2 (5/8" heavy hex nut)
            N_p = 8 (0.671)(5,000) = 26,835 lb      phi N_p  = 18,784 lb
steel, T    A_se 0.226 in2 x f_uta 57,000 psi       phi N_sa = 9,662 lb
side-face   17.6.4 does NOT apply: it is for h_ef > 2.5 c_a1, i.e. 7.89" > 15.0" — false
shear, brk  l_e = min(h_ef, 8 d_a) = 5.000"
            V_b = min(7 (5/0.625)^0.2 sqrt(0.625), 9) sqrt(5000) (6.0)^1.5 = 8,717 lb
            A_Vc/A_Vco = (12.0 x 9.0)/(4.5 x 36) = 0.667   psi_ed,V = 0.900
            V_cb = 5,230 lb                          phi V_cb = 3,661 lb
pryout      k_cp 2.0 x the GRADED N_cb              phi V_cp = 9,056 lb
steel, V    0.6 x 0.226 x 57,000                     phi V_sa = 5,024 lb
```

**f_uta = 57 ksi is the conservative read of "304 stainless".** ASTM A193 Gr. B8 Cl. 1 is
75 ksi tensile / 30 ksi yield, and ACI 17.6.1.2 caps f_uta at 1.9 f_ya = 57 ksi. An ASTM F593
CW1 bolt at this diameter is 100 ksi and would nearly double the steel rows; neither steel row
governs either way, so the submittal's bolt spec does not change the answer — it is recorded
because it is the kind of assumption that would matter on a bigger anchor.

**The demand, strength level, no dead-load credit.**

```
tension   overturning couple      609.3 lb ASD  (981 lb x 4.083' / 6.573', §7f)
        + net roof uplift         433.2 lb ASD  (0.6D + 0.6W on 40.0 ft2, the same
                                                 surrogate column_head_joint spends)
                                1,042.5 / 0.6 = 1,737.5 lb
shear     half the panel's base shear, 980.7 / 2 = 490.4 / 0.6 =  817.3 lb
```

```
tension  1,737.5 / 4,528 = 0.384        shear  817.3 / 3,661 = 0.223
17.8.3   both over 0.2, so (0.384 + 0.223) / 1.2 = 0.506
```

**0.506, governed by concrete breakout in tension.** Three cautions on the page:

* **The shear is split evenly between the two bases and that is an assumption about a sill.**
  `BM-BW-SCSILL` spans between the two columns and both ends are nailed; a wildly uneven split
  would need one end to be much stiffer than the other, which the detail does not offer. Put
  the whole 980.7 lb on one anchor and the shear row reads 0.446 and the interaction 0.692 —
  still under 1.0, which is the reason this is a caution and not a second row.
* **The panel's own N-S share is taken at the cracked-column distribution (0.825), not at the
  torsion-corrected one.** §8g shows torsion RELIEVES the panel to about 0.42 of the deck's
  shear. The relief is not credited anywhere, here or in §7f.
* **The anchor and the stirrup are graded against different tensions**, and deliberately:
  §7f's `ABU66SS` row is the overturning couple alone (609 lb / 2,190 = 0.28), because that is
  the panel's own limit state; the anchor carries the column's roof uplift through the same
  bolt in the same gust, which is why the roof's 433 lb is added here. Both tensions on the
  stirrup would read 1,042.5 / 2,190 = 0.48 — worth knowing, still not governing.

## 8g. Torsion — the centre of rigidity is not under the load

`rigidity_shares` splits in proportion to stiffness, which is only in equilibrium if the load
resultant passes through the stiffness centroid. On this deck it does not.

**The N-S case, at the gross-column stiffnesses.**

```
centre of rigidity   x_r = (9,970.5 x 6.000 + 3,135.3 x 30.000) / 13,105.8  = 11.742'
load resultant       997.4 lb of gable-end triangle at the footprint centre x = 18.000'
                     +  192.0 lb of column head reactions at x = 30.000'
                     x_V = (997.4 x 18.000 + 192.0 x 30.000) / 1,189.4      = 19.937'
eccentricity         e = 19.937 - 11.742 = 8.195'
torsional moment     M_t = 1,189.4 x 8.195 = 9,747.9 lb-ft
torsional inertia    J = sum k d^2 over EVERY line, both directions
                     panel   9,970.5 (6.000 - 11.742)^2   =   328,730
                     columns 3,135.3 (30.000 - 11.742)^2  = 1,045,180   (N-S)
                     columns 3,135.3 (2.4896)^2           =    19,430   (E-W couple)
                                                          J = 1,393,345 lb/in x ft2
```

```
line            direct        M_t k d / J      total      multiplier
W-BW-SCREEN     904.9 lb       -400.5 lb       504.4 lb      0.56  (RELIEF — not credited)
PT-BW-RE        142.3 lb       +200.2 lb       342.5 lb      2.41
PT-BW-RNE       142.3 lb       +200.2 lb       342.5 lb      2.41
each column, E-W                +27.3 lb                     (the couple that closes it)
                               sum N-S = 1,189.4 lb  ✓
```

**98.6% of J is the two N-S lines' own couple.** The E-W columns' 4.979' lever contributes
1.4%, so the "correction" is not a correction at all — it is the arithmetic putting the
distribution back where statics wanted it. With a load resultant at 19.94' between lines at
6.00' and 30.00', the lever rule gives the panel (30.00 − 19.94)/24 = 42% and the columns 58%;
the torsion-corrected split is 42.4% / 57.6%. **The uncorrected rigidity split (76.1% / 23.9%)
was not in equilibrium**, and the moment it left over is exactly the M_t above.

Run at the cracked-column stiffnesses the same arithmetic gives x_r = 10.211', e = 9.727',
M_t = 11,569 lb-ft, J = 1,055,990, and the panel lands at **504.9 lb** and each column at
**342.3 lb** — within a pound of the gross case, because once torsion is in, the answer is
statics and the stiffnesses have almost nothing left to decide. That is the strongest evidence
that the correction is right.

**The E-W case, for completeness.** The two column lines sit at y = 37.500 and 42.479, so
y_r = 39.990; the load (629.3 lb on the roof and headers at the footprint centre y = 40.219,
plus 192.0 lb of head reactions at the columns) resolves at y_V = 40.165, e = 0.176',
M_t = 144.2 lb-ft and **±0.4 lb per column** on a 410.7 lb direct share. The headers' own
projection bands sit 0.14' north of the footprint centre and are not tracked separately; doing
so moves M_t by about 25 lb-ft and the per-line force by under 0.1 lb.

**Stability.** Two N-S lines and two E-W lines at four distinct stations: the system resists
translation both ways and rotation, and J > 0. A canopy with its two columns on ONE station
and no second E-W line would be a mechanism about the vertical axis, and that is what the
torsion row is for — it is a stability statement first and a magnitude second.

## 8h. What §8 moves, and what it does not

**Nothing governing moves.** The canopy record is still governed by `diaphragm span-to-depth`
at **4.00 / 4.00 = 1.00** (§7f), and every row added here is well under it:

| new row | d/c |
|---|---|
| west line collector (zero drag, detailing) | 1.00 (6.000' of deck edge over 6.573' of panel) |
| east collector end connection, HETA20Z interaction, N-S | 0.443 (E-W 0.476) |
| north line LSTA24 strap | 0.048 |
| hold-down anchorage, tension (breakout) | 0.384 |
| hold-down anchorage, shear (breakout) | 0.223 |
| hold-down anchorage, interaction §17.8.3 | 0.506 |

**One thing does move and it is recorded rather than propagated.** The columns' N-S share
goes from 142.3 lb to 342.5 lb once torsion is in. `engineering/roof_moment.py` still
distributes the columns' own base demands by rigidity WITHOUT the torsional term, so its N-S
base moment for each column is 2,908 lb-ft where the corrected one is

```
M = 342.5 x 16.563 + 552.6 = 6,225 lb-ft      base shear 342.5 + 85.5 = 428 lb at 14.5'
```

against the **E-W** case's 7,354 lb-ft at 496 lb, which governs both columns on both records
(`column_base`, `pier_basis`) either way. `column_head_joint` takes the worse axis and that is
E-W's 410.7 lb, above the corrected N-S 342.5 lb. So no verdict anywhere moves, and feeding
torsion back into `roof_moment` would change no printed d/c — which is the only reason it is
left alone and said out loud here rather than done quietly.

**And the panel's rows stay where §7f put them.** Torsion relieves the panel by nearly half,
and crediting that relief would take a graded member's demand down on the strength of an
arithmetic refinement. Relief is not credited; only the increment is.

## Sources

* AWC SDPWS-2015 §4.2, §4.3 and Tables 4.2A / 4.2.4 / 4.3A / 4.3.4.
* IBC 2018 §1604.4 (distribution in proportion to rigidity); ASCE 7-16 §26.2.
* ACI 318-19 Ch. 17: §17.5.3 (φ), §17.6.2 (breakout in tension, incl. §17.6.2.1.2),
  §17.6.3 (pullout), §17.6.4 (side-face blowout), §17.7.2 (breakout in shear), §17.7.3
  (pryout), §17.8.3 (interaction).
* ICC-ES ESR-2105, reissued January 2026, Table 3 and footnotes 1–5 (LSTA straps).
* ICC-ES ESR-1622 §5.6 and Table 2 footnote 3 (the ABU's anchor is out of scope).
* Simpson Strong-Tie FL11473 Table 3 and §9 Limitations item 4 (the HETA pair).
* ASTM A193 Gr. B8 Cl. 1 / ASTM F593 CW1 (the stainless anchor's strength).
