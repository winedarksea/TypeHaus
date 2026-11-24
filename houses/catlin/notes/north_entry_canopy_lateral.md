# North entry canopy — §8, the rest of the lateral path, hand-worked

**House:** catlin
**Basis:** the built canopy as of 2026-11-14 (`EAST_POST_SYSTEM = "kdat"`, wind of 2026-10-31: delivered E-W
670.77 lb, N-S 1,034.49 lb, from `canopy_garage_diaphragm.md` §2). §8f and §8g are generic arithmetic for the
`steel`/`cast` alternatives and are worked on the frame `tests/test_lateral_system_calcs.py` reproduces (stated
in each section); the current alternatives' own shears are in `canopy_garage_diaphragm.md`.
**Oracle for:** the collector, anchorage and torsion rows of `engineering/lateral_system.py` and
`lateral_collectors.py`, with `engineering/holdown_anchor.py` (§8f) and `engineering/torsion.py` (§8g/§8h);
reproduced by `tests/test_lateral_system_calcs.py`.
**Companions:** `entry_column_base_fixity.md` §7 (the cast variant's wind, propped shafts, stiffnesses, the
rigid/flexible test, the shares and the deck's and panel's limit states: this note starts from its numbers and
adds nothing to them); `canopy_west_band.md` (the built west line); `canopy_garage_diaphragm.md` (the delivery).

## §8a. What §8 grades, and where each stands on the built canopy

1. **The chord force.** N-S: the first and last canopy trusses' top chords, 764 lb (§8b). E-W: the glulam headers, 88.07 lb
   (`canopy_west_band.md` §6).
2. **The collectors.** `DiaphragmSpec.collector_refs` names `BM-BW-RW` and `BM-BW-RE`; what is graded is the
   connection at each end, not the member (§8c-§8e).
3. **The concrete under a hold-down.** The built chord bases are cast-in `CBSTQ66Z-SDS2`, whose cracked uplift row
   (ESR-3050 Table 2, 3,060 lb) is measured through the concrete: no ACI Ch. 17 row stands in for it
   (`canopy_west_band.md` §4b, 0.729). §8f is the anchor calculation for a hold-down that does not carry its own.
4. **Torsion.** A rigid deck split by stiffness alone is in moment equilibrium only if the load passes through the
   centre of rigidity (§8g). The built canopy's east posts are pinned and resist no storey shear, so it has no
   column lines and no torsion couple; its record carries only the delivery's stability row.

## §8b. The chord — delegated to the truss fabricator, not computed

**Amended 2026-11-23 (review C-2, C-8; decision 19).** The N-S chords are the **top chords of the first and last
canopy truss**, y 37.3333' and 41.3333', **4.000' apart** (not the deck's 6.0' depth): 24 feet of 2x4, one plated
splice at the peak, carrying `V L / (8 d)` of axial force, tension in one chord and compression in the other, **in
addition to the gravity and drift case the chord is already designed for**. L is the strap line from the screen's
end to the east end strap, 23.2604' (the screen at 100% is in equilibrium only as that simple span):

```
N-S, built canopy      1,051.72 x 23.2604 / (8 x 4.000) = 764.5 lb       (was 1,034.49 x 24.0 / (8 x 6.0) = 517.2)
unit test (§7f of the cast frame's V 1,189.4 lb)                           = 594.7 lb
```

The engine prints it as `chord_force_y` on `lateral_system/RF-BW-CANOPY` (`diaphragm_chord.py`) and the order asks
every canopy truss for it. The garage gable truss (y 43.281) is not named as the north chord: it would take a canopy
force through a nailed deck edge (505 lb at its 5.95' spacing, if it were). The E-W chords are the glulam headers,
88.07 lb, which is nothing.

A truss chord is not a member this engine may size: its axial capacity comes out of the fabricator's own plate,
web and lateral-brace layout at the same section, and the combined axial + bending interaction is the
fabricator's chart. So the chord force goes on the **truss order** (S-001, the TRUSS CRITERIA block) through the
existing `rafter/RF-BW-CANOPY` deferral rather than into a limit state here. **The splice slip is no longer on the
order**: both N-S paths are graded at 100% (the double envelope), so the rigid/flexible split never enters a ratio;
`DiaphragmSpec.chord_splice_slip` survives only for the `cast` variant's deflection. The **end-strap couple** the
same equilibrium needs is graded: `canopy_garage_diaphragm.md` §12c (549.4 lb at the end straps, 0.774).

## §8c. The west collector — the header, fed by the eave clips

The west line's collector is `BM-BW-RW` itself: the deck's boundary shear reaches it through the trusses' heel
blocking and six `LTP4Z` plates, 1,034.49 / 6 = 172.42 lb each against 450 (0.383), and the band between the
header and the panel is braced by the corner-to-corner 6x6 knees. All of it is `canopy_west_band.md` §2-§4;
`engineering/lateral_band.py` makes an unbridged band INCOMPLETE rather than zero.

The panel stops on `W-G-S`'s cladding face, 7/8" short of the deck edge drawn to that wall's outer face. The strip
between is the garage wall, not a drag length: `lateral_collectors._skin_gaps_ft` counts a gap another wall's own
layers fill, so the panel-collector row on a line with column cases still reads 1.00.

## §8d. The east collector — the connection, not the member (cast variant)

The east header is a collector in the N-S case only where its posts are fixed columns: it gathers the deck's east
boundary shear over 6.000' of depth and delivers it to two columns. The glulam carries a few hundred pounds of
axial force, which is not a question; the connection is. On the built canopy the east header is no collector
(its chord rows are `canopy_west_band.md` §6).

For the cast columns each head takes its own share, **with torsion (§8g)**, on the frame of §8g's table:

```
N-S, per column   direct 0.1196 x 1,189.4 = 142.3 lb  +  torsion 200.2 lb  =  342.5 lb
E-W, per column   direct 0.500  x   821.3 = 410.7 lb  +  torsion   0.4 lb  =  411.1 lb
```

The head is an `SS316-SHIM-35` pack and a **cast-in `HETA20Z` pair** (`params/column_heads.py`, Simpson FL11473
Table 3, double HETA into concrete, 2- or 3-ply SP: uplift 2,560, F1 1,350, F2 1,430 lb, the +60% wind
increase already in them). FL11473 §9 Limitations item 4 states the interaction directly, and it is the
interaction that is graded, because the same connector carries uplift in the same wind:

```
uplift    0.6D + 0.6W on 40.0 ft2 of roof             433.2 lb  / 2,560 = 0.169
F1  (parallel to the header, N-S)                     342.5 lb  / 1,350 = 0.254
F2  (perpendicular, the torsional couple's own share)   27.3 lb  / 1,430 = 0.019
                                                               unity  =  0.442
```

The **E-W** case, where the same connector sees 411 lb perpendicular to the header and the same uplift, reads
0.169 + 411/1,430 = 0.456 on the true F2 and 0.169 + 411/1,350 = **0.473** as `column_head_joint/PT-BW-RE` grades
it: that record takes the lower of F1/F2 so no direction needs knowing.

## §8e. The north line — the strap line is the delivery

On the built canopy the canopy's E-W shear (670.77 lb) crosses the garage joint through continuous deck panels
nailed to the garage gable's top chord (28.88 plf along the joint vs 190, 0.152), and the six `LSTA24` straps
`CN-BW-JOINT-1..3, -5..7` at 4'-0" o.c. take the N-S shear across it (172.4 lb vs 823.3, 0.209) and the rotation
couple (56.8 lb, 0.069). `diaphragm_delivery` owns those rows, graded at 100% (`canopy_garage_diaphragm.md` §3b);
the strap-line row of `lateral_collectors._strap_line` is not emitted where a `delivers_to` is declared. The
straps are otherwise ordinary: nominal continuity, sized as the delivery asks.

For a roof with no declared delivery the row is the generic one: the E-W line reaction R over the strap line
(first strap to last) gives R/L plf, and each strap takes R/n against `allowable_for_model("LSTA24")`, **ICC-ES
ESR-2105 (reissued January 2026) Table 3**: 20 ga, 18-10d x 2 1/2 common, 1,235 lb at C_D 1.6, footnote 5 (steel
strength, no duration increase), footnote 2 (SG >= 0.50); installed on 12 of 18 nails it is 823.3 lb. Three things
the row states rather than hides:

* **The force is ALONG the joint, not across it, and ESR-2105 publishes tension.** For a 0.148" nail (d < 1/4")
  NDS dowel bearing is independent of the angle to grain (footnote 4 derives the table as nail count times the
  NDS yield-mode value), so the group is no weaker this way; the tabulated value is itself the steel value.
* **The E-W north-line path crosses into `RF-GARAGE`.** The canopy is freestanding for gravity; this reaction is
  collected by the garage's gable truss and returned across the strap line.
* **`H2.5ASS` is not a collector.** Those are truss-to-header uplift ties (110 lb F1/F2 in the stainless parity
  letter) and nothing here asks them to drag anything.

## §8f — hold-down anchorage (oracle for holdown_anchor.py; not on the current house, whose CBSTQ66Z-SDS2 carries its own rated anchorage)

`engineering/holdown_anchor.py` grades the concrete under a hold-down whose report declines to: ICC-ES ESR-1622
§5.6, "The design of anchor bolts and the concrete footings is outside the scope of this report", for an
`ABU66SS` base on a cast-in **`AB-058-10-SS`, 5/8" x 10", 304 stainless**, on the top of a 12" round pier. It is
the oracle for that function and for the single centred bolt `steel_post.py` uses to bound a steel post's pair
from below. The arithmetic is worked on a 12" round pier (`PIER_CONCRETE_12`, f'c 5,000 psi).

**The embedment, derived rather than assumed.** 10" of bolt, less the projection above the pour (7 ga base plate
0.179" + washer 0.134" + heavy hex nut 0.609" + two threads 0.18", call it 1 1/2" with the adjustment the ABU
wants), less the embedded nut's own thickness 0.609": **h_ef = 7.891"**. f'c = 5,000 psi, **cracked**, condition B
(no supplementary reinforcement credited: the cage is not developed as anchor reinforcement), λ = 1.0.

**The edge distance is the whole calculation.** A 12" round pier with the bolt at its centre gives **c_a = 6" in
every direction**, on all sides at once.

```
17.6.2.1.2   three or more edges under 1.5 h_ef, so h_ef' = max(c_a,max/1.5) = 4.000"
             A_Nc = pi (6.0)^2 = 113.1 in2   A_Nco = 9 (4.0)^2 = 144.0    ratio 0.785
             psi_ed,N = 1.0 (c_a = 1.5 h_ef')     N_b = 24 sqrt(5000) (4.0)^1.5 = 13,576 lb
             N_cb = 10,663 lb        phi N_cb = 0.70 x 10,663 = 7,464 lb
unreduced    A_Nc / A_Nco = 113.1 / 9(7.891)^2 = 0.202   psi_ed,N = 0.852
             N_b = 37,452 lb         phi N_cb = 4,528 lb
```

**The unreduced reading is the one graded, and that is a deliberate choice.** §17.6.2.1.2 exists because the
1.5h_ef projection over-predicts the loss of capacity in a narrow member, and applying it is correct and gives
7,464 lb. Taking the **lower** of the two is a bound rather than a reading, in the same spirit as the solid-sign
wind surrogate in `roof_moment`, and 4,528 lb is still four times the demand below, so the conservatism costs
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

**f_uta = 57 ksi is the conservative read of "304 stainless".** ASTM A193 Gr. B8 Cl. 1 is 75 ksi tensile / 30 ksi
yield, and ACI 17.6.1.2 caps f_uta at 1.9 f_ya = 57 ksi. An ASTM F593 CW1 bolt at this diameter is 100 ksi and
would nearly double the steel rows; neither steel row governs either way, so the submittal's bolt spec does not
change the answer.

**The demand, strength level, no dead-load credit** (the original ABU66SS frame: panel base shear 980.7 lb, the
overturning couple 981 lb x 4.083' / 6.573', and 40.0 ft² of roof at the frame's wind):

```
tension   overturning couple      609.3 lb ASD
        + net roof uplift         433.2 lb ASD  (0.6D + 0.6W on 40.0 ft2)
                                1,042.5 / 0.6 = 1,737.5 lb
shear     half the panel's base shear, 980.7 / 2 = 490.4 / 0.6 =  817.3 lb
```

```
tension  1,737.5 / 4,528 = 0.384        shear  817.3 / 3,661 = 0.223
17.8.3   both over 0.2, so (0.384 + 0.223) / 1.2 = 0.506
```

**0.506, governed by concrete breakout in tension.** The shear is split evenly between the two bases, which is an
assumption about a sill: `BM-BW-SCSILL` spans between the columns and both ends are nailed, so a wildly uneven
split would need one end much stiffer than the other. Put the whole 980.7 lb on one anchor and the shear row reads
0.446 and the interaction 0.692, still under 1.0.

## §8g. Torsion — the centre of rigidity is not under the load

`rigidity_shares` splits in proportion to stiffness, which is only in equilibrium if the load resultant passes
through the stiffness centroid. Worked on the cast alternative's frame, the one the unit tests reproduce
(feet, house coordinates):

| | |
|---|---|
| roof footprint | x 4.667 to 31.333 (26.667' wide), y 37.219 to 43.219 (6.000' deep) |
| N-S lines | `W-BW-SCREEN` at x = 6.000; `PT-BW-RE` + `PT-BW-RNE` at x = 30.000 |
| E-W lines | `PT-BW-RE` at y = 37.500, `PT-BW-RNE` at y = 42.479 |
| stiffnesses | columns 1,567.7 lb/in each (gross); panel 9,970.5 lb/in |
| shears at the deck | E-W 821.3 lb, N-S 1,189.4 lb ASD, of which 192.0 lb is the two columns' propped head reactions (96.0 lb each, at x = 30) |

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

**98.6% of J is the two N-S lines' own couple.** Two parallel lines at different stations resist a torsional
moment as a **couple**; what they cannot resist is translation across themselves. The E-W columns' 4.979' lever
contributes 1.4%, so the "correction" is the arithmetic putting the distribution back where statics wanted it.
With a load resultant at 19.94' between lines at 6.00' and 30.00', the lever rule gives the panel
(30.00 - 19.94)/24 = 42% and the columns 58%; the torsion-corrected split is 42.4% / 57.6%. **The uncorrected
rigidity split (76.1% / 23.9%) is not in equilibrium**, and the moment it leaves over is exactly M_t.

At the cracked-column stiffnesses the same arithmetic gives x_r = 10.211', e = 9.727', M_t = 11,569 lb-ft,
J = 1,055,990, and the panel lands at **504.9 lb** and each column at **342.3 lb**: within a pound of the gross
case, because once torsion is in, the answer is statics and the stiffnesses have almost nothing left to decide.

**The E-W case.** The two column lines sit at y = 37.500 and 42.479, so y_r = 39.990; the load (629.3 lb on the
roof and headers at the footprint centre y = 40.219, plus 192.0 lb of head reactions at the columns) resolves at
y_V = 40.165, e = 0.176', M_t = 144.2 lb-ft and **±0.4 lb per column** on a 410.7 lb direct share.

**Stability.** Two N-S lines and two E-W lines at four distinct stations: the system resists translation both
ways and rotation, and J > 0. Two columns on ONE station with no second E-W line would be a mechanism about the
vertical axis, and that is what the torsion row is for: a stability statement first and a magnitude second
(`test_two_lines_on_one_station_with_nothing_across_are_a_mechanism`).

## §8h. An increment is added and a relief is not credited

Torsion relieves the panel to about 0.42 of the deck's shear, and crediting that would take a graded member's
demand down on the strength of an arithmetic refinement. Relief is never credited; only the increment is
(`Torsion.multipliers` floors at 1.0). The column force is ONE function, `torsion.column_forces_lb` (direct
share + `max(torsion, 0)`), which `roof_moment`, `lateral_system.column_head_reactions` and the collector rows
all read, so no two modules pin different forces for one column.

*Equilibrium check, N-S, signed forces (§8g's own values):*

```
                    k/Σk alone                      with torsion
panel  W-BW-SCREEN  904.98                          904.98 - 400.61 = 504.37 lb
each column         142.22                          142.22 + 200.31 = 342.52 lb
ΣF_y                904.98 + 2(142.22) = 1,189.41   504.37 + 2(342.52) = 1,189.41   ✓ both

ΣM about the column line x = 30.000' (vertical axis):
load                1,189.41 x (30.000 - 19.937) = 11,968.8 lb-ft
panel               904.98 x 24.000 = 21,719.5      504.37 x 24.000 = 12,104.9
E-W couple          —                               27.31 x (42.479 - 37.500) = 136.0 (opposing)
residual            21,719.5 - 11,968.8 = 9,750.7   12,104.9 - 136.0 - 11,968.8 = 0.1   ✓
```

The k/Σk residual is exactly M_t = 1,189.41 x 8.198 = 9,750.7 lb-ft (§8g); with torsion it closes to rounding.
The graded column demand floors the relief: E-W gives `PT-BW-RE` -0.40 lb and `PT-BW-RNE` +0.40 lb, so RE keeps
410.66 and RNE takes 411.06, ΣF over by 0.40 lb: the price of never crediting a relief, not an equilibrium error.
The N-S column demand is 342.5 lb at the roof plane; `north_entry_piers.md` §9e takes it as its lever's load
(342.52 / 0.6 x 2.25" / 12 = 107.04 lb-ft of column torsion).

## Not graded here / still open

* The truss end chords (§8b, 764 lb): the truss fabricator's sealed design, an external deliverable; the splice
  slip is not asked for.
* The cast and steel variants' current shears and base moments: `canopy_garage_diaphragm.md`.
* The soils report: the soil class is presumed, and every record that reads it says so.

## Sources

* AWC SDPWS-2015 §4.2, §4.3 and Tables 4.2A / 4.2.4 / 4.3A / 4.3.4.
* IBC 2018 §1604.4 (distribution in proportion to rigidity); ASCE 7-16 §26.2.
* ACI 318-19 Ch. 17: §17.5.3 (φ), §17.6.2 (breakout in tension, incl. §17.6.2.1.2), §17.6.3 (pullout), §17.6.4
  (side-face blowout), §17.7.2 (breakout in shear), §17.7.3 (pryout), §17.8.3 (interaction).
* ICC-ES ESR-2105, reissued January 2026, Table 3 and footnotes 1-5 (LSTA straps); ICC-ES ESR-1622 §5.6 (the
  ABU's anchor is out of scope).
* Simpson Strong-Tie FL11473 Table 3 and §9 Limitations item 4 (the HETA pair).
* ASTM A193 Gr. B8 Cl. 1 / ASTM F593 CW1 (the stainless anchor's strength).
