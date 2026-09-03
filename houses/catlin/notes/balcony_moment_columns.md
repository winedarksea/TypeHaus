# The balcony's four moment columns — engineering basis for an engineer's review and stamp

**House:** catlin, Ramsey County, Minnesota (Minnesota Residential Code 2020, adopting the
2018 IRC).
**Structure:** the sunken garden's balcony — a 21'-0" × 9'-8" deck at +10'-0", carried on
**four 12" round reinforced-concrete columns fixed at the base** (PT-SG-BR1, PT-SG-BR3,
PT-SG-BF1, PT-SG-BF3) and two 6x6 wood centre pillars on pinned standoff bases, under three
treated structural-glulam beams.
**Written:** 2026-09-03. It **supersedes `balcony_lateral_bracing_design.md`**, which
designed the eight knee braces and two brace rails this replaced.
**What is asked of the reviewer:** this is a screening design under IRC R301.1.3 engineered
design. It is offered for a licensed engineer's check and stamp. It is **not** a stamped
design, and nothing in the model treats it as one: `haus engineering` reports these items as
`draft` — this engine's own calculation checks out — and `sealed` stays unset until
`engineering.toml` carries a stamp.
**What this note is FOR.** Every number below is worked here from first principles with the
arithmetic shown, and `engineering/deck_post.py` and `engineering/glulam_beam.py` are then
checked against it. A calculation that only agrees with itself is not verified. Where the
hand working and the engine differ, the difference is stated (§4a).

---

## 0. Why the braces went, and why this is not just "the same deck with fatter posts"

`balcony_lateral_bracing_design.md` opened by saying the balcony has no shear walls: six
posts on `ABU66SS` standoff bases, and Simpson's own reports (ESR-1622, ESR-3050) say a
standoff base *"does not provide adequate resistance to prevent members from rotating about
the base."* Both the bases and the beam bearings were pins. Eight 2x6 knee braces were the
entire lateral system, and **every one of their joints came back UNKNOWN** — the E-W feet
were lapped bolt groups with no product rating at all.

The owner asked for a more durable structure for a hundred-year freeze-thaw exposure, the
clean open look kept, and off-the-shelf parts. Three routes were priced:

| route | why it lost / won |
| --- | --- |
| **Catalog metal moment base under the wood posts** | **No stock base publishes a base moment.** The only one that does is Simpson's MPB66Z, for a WOOD post — and it needs 5" side cover (about 16" of concrete, cast in) and its wet-service cap is 2,610 lb-ft (ESR-3050 Table A), **below the guard case in §3 below**. It cannot go in a 12" round or on a 12" wall top as published. Foreclosed, not deferred. |
| **Stock HDG steel tube columns** | New Castle Steel's 6x6x3/16" with a welded base plate, ~$458 per 10'. Kept as the written **fallback** if forming and caging four tall tubes proves too much labour. Its base still needs a fabricated saddle on a 12" wall top, which is a shop drawing this note does not carry. |
| **Reinforced concrete columns** ✅ | The one braceless design built entirely from catalog parts: a Sonotube, a stock cage, dowels into the wall it stands on. The house already carries the beam-on-concrete detail at PT-SG-COL and PT-SG-FCOL, and the engine already grades cast columns. |

**The lateral system is now the four corner columns' own base fixity.** The two centre
pillars stay wood and stay leaning columns, tied in by the deck diaphragm — the same claim
the old note made about them, and the same one that stays unproven here.

---

## 1. Geometry, and where every dimension comes from

Read off `params/sunken_garden.py` rather than restated:

```
deck walking surface            +10'-1 1/2"  (balcony_level_ft + 1 1/2" plank)
beam soffit / column top          9'-0 1/8"  = 10' − 11 7/8" glulam depth
corner column base                0'-0"      = the porch top, W-SG-W1/E1's 12" wall tops
column unbraced length lu         9'-0 1/8"  = 108.125"
guard top                       +13'-7 1/2"  = walking surface + 42"
sunken garden floor               −9'-0"     — the ground this structure stands over
appurtenance height h            23.0'       = guard top − garden floor
column diameter                    12"       round; A_g = π·6² = 113.10 in²
```

**Why 12" and not 10".** Cover. ACI 318-19 §20.5.1.3's 1-1/2" is a code minimum, not a
hundred-year number — MnDOT uses 2.5"-3" in the same deicing regime. Two inches of cover on
a #5 vertical inside a #3 tie puts the bar circle at

```
bar-circle radius = 6" − 2" cover − 0.375" tie − 0.625"/2 bar = 3.3125"   (Ø 6 5/8")
```

which needs a 12" round to hold. 12" also drops the slenderness ratio and gives the beam
seat its edge distance for free: an HGAM10's Titen Turbo lands ~3-3/4" from the face where a
10" round would leave 2-3/4", against Simpson's 1-1/2" minimum. And centred on the 12" wall
axis the round is **flush with both wall faces** — no ledge to pond on, and BF3's 3" east
leader keeps 1-1/2" clear. The extra concrete over four columns is about 0.3 cy.

---

## 2. Loads

### 2a. Gravity

IRC R507.1 / Table R301.5: **40 psf live + 10 psf dead = 50 psf.** Deck plan area 21'-0" ×
9'-8" = 203 ft², divided among the six posts its beams name = **33.83 ft² each.**

```
live   40 × 33.83 =  1,353 lb
dead   10 × 33.83 + column self weight
factored (1.2D + 1.6L, ASCE 7-16 §2.3.1)  =  3,845 lb
```

**No equipment dead load.** The two Gree condensers (330 lb the pair) left this deck on
2026-09-02 for a poured pad in the yard pocket east of the porch — see
`heat_pump_ground_pad.md`. They were negligible on a 203 ft² deck before that, so no member
changed when they went; what changed is that `FS-SG-DECK`'s aluminium plank now carries
**zero penetrations**, which is what keeps RL-SG-BALCONY on fascia brackets (§7).

### 2b. Wind — ASCE 7-16 §29.3, on the same basis as the superseded note

`plan/site.py`, from **MN Rules 1309.0301**: V_ult 115 mph statewide, Exposure B, Risk
Category II. Height is measured from the **sunken garden floor**, the ground actually beneath
this structure, not from the site grade nine feet higher — the conservative reading and the
physical one.

```
q_h at h = 23.0'                        18.7 psf        (typehaus/wind.py)
G (rigid, §26.11.1)                     0.85
ASD factor (§2.4.1)                     0.6
```

**Solid area, derived from the model and not authored.** The brace rails are gone, so the
bands are the fascia and the three glulam beams:

```
E-W wind (the beams present their faces):
  fascia + deck edge   9"      × 9.67'   =  7.25 sf
  BM-SG-BLW/BLC/BLE   11 7/8"  × 9.67' ×3 = 28.69 sf
                                     A_s = 35.94 sf
N-S wind (the beams run along the wind and present nothing):
  fascia + deck edge   9"      × 21.0'  = 15.75 sf
                                     A_s = 15.75 sf
```

**E-W governs**, which is the reverse of the braced design's N-S 15.7 / E-W 25.4 split
because the beams got 5/8" deeper and the two 2x8 rails left the E-W band.

**C_f could not be sourced, and is spent rather than left open.** ASCE 7-16 Fig. 29.3-1 is
copyrighted and this repository holds three verified cells of it. The superseded note
*inverted* — reporting the coefficient at which a joint reaches capacity. Here the demand is
taken at **C_f = 1.80**, the largest value Cases A and B are known to reach, so a column
adequate at 1.80 is adequate for any legitimate reading of the figure.

```
F = 0.6 × q_h × G × C_f × A_s
  = 0.6 × 18.7 × 0.85 × 1.80 × 35.94  =  616 lb   storey shear, E-W
split over 4 fixed columns             =  154 lb  each, delivered at the deck plane
base moment  M_w = 154 × 9.01'         =  1,388 lb-ft
```

**The three-beam band is an over-count and is kept deliberately.** Three N-S beams seen from
the east stand behind one another and a real open-frame analysis would shield the second and
third. Counting all three is conservative, it is what `checks/structural/lateral_racking`
already did with the rails, and at d/c 0.07 the margin is not worth an argument about
shielding factors.

### 2c. Guard — IRC R301.5, and it is what governs

Table R301.5 note f: a **200 lb concentrated load in any direction** at the top of the
guard. Its lever to a column base is the whole column plus the guard height:

```
M_g = 200 lb × (9.01' + 3.5')  =  2,502 lb-ft
```

Two columns bound each end bay of the guard and would share this in any real distribution
(~1,250 lb-ft each). **It is taken wholly on one column**: halving it is a diaphragm claim
this note has no standing to make, and the margin is there to spend.

**The two are not summed.** ASCE 7-16 §2.4.1 pairs W with L at 0.75, and a guard load is not
a storey live load in the first place. The guard case governs at **2,502 lb-ft**.

---

## 3. Slenderness and magnification

```
r = d/4 = 3.0"                     (circular section)
k = 2.1                            ACI 318-19 Table R6.2.5, fixed base / free top —
                                   2.1 rather than the ideal 2.0, for real fixity
k·lu/r = 2.1 × 108.125 / 3.0 = 76  against §6.2.5's SWAY limit of 22
```

So it is a slender column and the moment must be magnified. It barely moves, because
magnification needs axial load to bite and there is almost none:

```
E_c = 57,000 √3,000            = 3.12e6 psi
I_g = π·12⁴/64                 = 1,018 in⁴
β_dns = 1.2 D / P_u = 1.2×1,400/3,845 = 0.437
EI = 0.4 E_c I_g /(1+β_dns)    = 8.84e8 lb-in²
P_c = π² EI /(k·lu)²           = π² × 8.84e8 / (227.06)² = 1.69e5 lb
δ  = 1/(1 − P_u/0.75 P_c) = 1/(1 − 3,845/126,900) = 1.031
```

**Magnified design moment M_u = 2,502 × 1.031 = 2,580 lb-ft.**

---

## 4. Capacity — the section, worked by hand

12" round, (4) #5 hot-dip galvanized verticals, #3 galvanized ties @ 10" o.c., 2" cover,
f'c 3,000 psi (see §4a), f_y 60,000 psi.

```
A_s = 4 × 0.31 = 1.24 in²        ρ = 1.24/113.10 = 1.096%
                                 §10.6.1.1 floor 1% = 1.131 in²  ✓ (and ceiling 8% = 9.05)
bar count 4                      §10.7.3.1(b) minimum within circular ties  ✓ exactly
tie #3                           §25.7.2.1, for #10 and smaller  ✓
tie spacing 10"                  §25.7.2.2 least of 16d_b = 10.0", 48d_t = 18.0", h = 12"  ✓
```

Every one of those is **at its limit, not above it**. This is the minimum legal cage on a 12"
round: (4) #4 = 0.80 in² is 29% short of the floor, and four bars is already the count
minimum, so neither the size nor the number can come down.

**Bar orientation.** The four bars are taken at ±45° to the bending axis — the WEAK
orientation of a four-bar cage, about 8% below the strong one. Deliberate: a round column is
built in a round tube and nothing on site orients the cage to the wind. Each bar then sits
3.3125 × cos45° = **2.343"** from the section centre.

**Strain compatibility, P-M interaction at P_u = 3,845 lb.** β₁ = 0.85 at 3,000 psi.
Bisecting the neutral axis to satisfy φP_n = P_u lands at **c = 3.21"**, a = β₁c = 2.73":

```
concrete segment, depth a = 2.73" into a 12" circle
  chord offset above centre  = 6 − 2.73          = 3.27"
  A_seg = 36·acos(3.27/6) − 3.27·√(36−3.27²)     = 35.80 − 16.45 = 19.35 in²
  ȳ_seg = (2/3)(36−3.27²)^1.5 / A_seg            = 4.385" above the centre
  C_c   = 0.85 × 3,000 × 19.35                   = 49,340 lb   at +4.385"

tension pair, offset −2.343" (depth from compression fibre 8.343")
  ε = 0.003 (3.21 − 8.343)/3.21 = −0.00480       yielded
  F = −60,000 × 0.62                             = −37,200 lb  at −2.343"

compression-side pair, offset +2.343" (depth 3.657" > a, no concrete deduction)
  ε = 0.003 (3.21 − 3.657)/3.21 = −0.000418
  F = −29e6 × 0.000418 × 0.62                    =  −7,510 lb  at +2.343"

P_n = 49,340 − 37,200 − 7,510                    =   4,630 lb
M_n = 49,340(4.385) + (−37,200)(−2.343) + (−7,510)(2.343)
    = 216,360 + 87,160 − 17,600 = 285,920 lb-in  =  23,830 lb-ft
ε_t = 0.00480  →  φ = 0.88   (Table 21.2.2, transition on ε_ty = 0.00207)
φP_n = 4,070 lb ≈ P_u ✓        φM_n = 0.88 × 23,830  =  20,970 lb-ft
```

### The verdict

| case | demand | φM_n | d/c |
| --- | ---: | ---: | ---: |
| wind, E-W | 1,388 lb-ft | 20,900 | **0.07** |
| guard, R301.5, unshared | 2,502 lb-ft | 20,900 | **0.12** |
| guard magnified, δ 1.031 | 2,580 lb-ft | 20,900 | **0.12** |
| axial, §22.4.2.1 | 3,845 lb | 187,000 lb | **0.02** |

**Bending governs and the guard governs the bending, at an eighth of capacity.** The column
is not sized by any of these — it is sized by the 2" of cover the durability case asked for
(§1) and by the 1% steel floor, which is a creep, shrinkage and accidental-moment rule and
not a strength one. That is worth saying plainly, because a reviewer reading d/c 0.12 will
otherwise ask why the column is not smaller. It cannot be: 10" fails the cover case, and no
column may be plain (§14.1.5).

### 4a. Where this note and the engine differ

**f'c.** The mix specified in `SUNKEN_GARDEN_COLUMN_12` is **5,000 psi** (§6). The engine
carries no strength on an Assembly, so `engineering/deck_post.py` reads one presumptive
**3,000 psi** for every concrete calculation in the house, and both this note and the record
are worked at 3,000. The capacity above is therefore **understated** against what will be
poured — the safe direction. Reconcile against the drawing, not against this table.

**φM_n.** An earlier sketch of this design put φM_n near 13 kip-ft. That was a pure-flexure
estimate that dropped the compression-side bar pair and took a shorter lever arm. The worked
value above is 20.9 kip-ft, and `haus engineering --item deck_post/PT-SG-BF1` reports
**20,877 lb-ft** — agreement to 0.4%, which is round-off in the bisection. The verdict does
not turn on it either way.

---

## 5. The glulam beams

**Product:** preservative-treated southern yellow pine structural glulam, **3-1/2" ×
11-7/8", 24F-V5M1/SP** (Anthony Power Preserved / Boise Cascade, stocked through Lakeville),
clear-finished. They replaced three site-built 3-ply KDAT 2x12s. IRC Table R507.5(1)
publishes sawn plies only, so these are engineered items under `deck_beam/BM-SG-BL*`.

**Spans.** BM-SG-BLW and BLE run corner column to corner column at **7.77'**. BM-SG-BLC runs
PT-SG-BR2 to PT-SG-BF2 at **6.75'** — its back span shortened when BF2 moved north onto the
porch deck (see §6), which leaves a rear overhang of 20.0" against R507.5.1's quarter-span
limit of 20.25" and a south cantilever of 15". **Legal, by a quarter of an inch, and nothing
in the engine checks a beam overhang** — `checks/structural/deck.py` grades beam SPAN only —
so it is written down here instead.

**Wet service is applied, and it is the difference between this and a supplier's span
table.** AWC NDS 2018 Table 5.3.1: C_M = 0.80 on F_b, 0.875 on F_v, 0.53 on F_c⊥, 0.833 on E.
C_D = 1.0 (Table 2.3.2, occupancy live — not 1.15 snow, and emphatically not 1.6 wind).
C_V = 1.0: the §5.3.6 volume factor computes to 1.07 at this size and is capped. C_L is 1.0
with the compression edge held by a joist field at 16" o.c., and §5.3.6 takes the lesser of
C_L and C_V, so C_V governs.

```
w = 50 psf × 10.00' joist span                     = 500 plf
S = 3.5 × 11.875²/6 = 82.24 in³   I = 488.4 in⁴

BM-SG-BLW / BLE, L = 7.77'
  M   = 500 × 7.77²/8 = 3,773 lb-ft = 45,280 lb-in
  f_b = 45,280 / 82.24 = 551 psi     vs F_b' = 2,400 × 0.80 = 1,920 psi   d/c 0.29
  V at d: 500 (7.77/2 − 0.99) = 1,448 lb
  f_v = 1.5 × 1,448 / 41.56 = 52 psi vs F_v' = 300 × 0.875 = 263 psi      d/c 0.20
  bearing: R = 1,943 lb over 3.5" × 3" (R507.6 on concrete) = 185 psi
                                     vs F_c⊥' = 740 × 0.53 = 392 psi      d/c 0.47
  Δ_live = 5 (400/12) 93.25⁴ / (384 × 1.499e6 × 488.4) = 0.045"
                                     vs L/360 = 0.259"                    d/c 0.17

BM-SG-BLC, L = 6.75'  — every ratio lower; bearing governs at d/c 0.41
```

**Bearing governs, at under half.** 11-7/8" over the slimmer 9-1/2" option is the owner's
planter margin — 9-1/2" would run about 48% in bending against 31% here — and is a decision,
not a calculation. Recorded so nobody "optimises" the depth back out.

Black locust for the two centre pillars remains an option (IRC R202 naturally durable; mill
order; engineered values) and is **not** taken here.

---

## 6. What else moved, and why

**PT-SG-BF2 came north onto the porch deck**, 3" inside the front beam axis — the exact
mirror of PT-SG-BR2's 3" inside the back one. It stood on PT-SG-FCOL's top, which made it
19-1/2" longer than its five neighbours and forced that column to a 20" round so one pour
could span from the beams' north face to the pillar's south face. With BF2 on the deck,
**PT-SG-FCOL shrinks to 12" centred on the beam axis** and the whole 20" sizing essay
retires with it. 3" is the minimum that keeps the 5-1/2" post on the deck (the porch outline
ends on the beam axis) and it also keeps the base off TR-SG-CAP-FRW/FRE and its butyl.

**PT-SG-FCOL at 12", not 10":** it leaves 3-3/4" of concrete beside each beam end for the
HGAM10's Titen screws where 10" would leave 2-3/4". The rejected variant — BF2 on the column
south of the beams, north face flush with the rim line — fits a 12" only at 4.7" anchor edge
distance against ESR-1622's 4-5/8" minimum, with the beam ends bearing at the circle's
tangent.

**The front row stays on one line.** A 12" column's top runs 3-1/4" past the beam end there.
That is a concrete top with the assembly's ≥15° wash and drip lip, not the exposed end grain
the old 2-3/4" wood offset was written for, so the row is not re-solved.

---

## 7. Durability, the detail, and constructability

**Exposure class F3 + C2, not F2.** Deicing salt reaches the porch below and planter runoff
reaches the balcony above: that is external chloride on a freeze-thaw member. **w/cm ≤ 0.40,
f'c ≥ 5,000 psi, 6% ±1.5 air**, SCM caps per ACI 318-19 §19.3.3.4. IRC R402.2 asks the same
of a salt-exposed porch. **Do not reuse the retired 20" column's 4,000 psi / w/cm 0.45 F2
mix here.**

**Bar protection: hot-dip galvanized (ASTM A767 class 1, chromate-passivated, or A1094
continuous)** — the owner's 2026-09-02 call, house-wide. Epoxy delaminates. Stainless is the
only coating that buys a century independent of cover, at 4-6× the cost and with an
austenitic thermal coefficient (~16e-6/°C) fighting concrete's ~10-12e-6 (carbon steel is
~12e-6). Galvanized already sacrifices zinc at any coating break. Sika/Vector Galvashield XPX
embedded zinc anodes (330 g zinc, 20+ yr, ~$1,400 per box of 20) are a possible
sunken-garden-**wide** addition for the salt-splash walls; on these columns, over galvanized
bar at 2" cover, they are a belt on braces and are not taken.

**Note on the lap:** ψ_e is **1.0** for galvanized bar (§25.4.2.5). It is EPOXY that takes
1.2-1.5, and reading the epoxy row here would lengthen every lap in this house by half.

```
ld  = (60,000 / (25 √3,000)) × 0.625 = 27.4"     §25.4.2.4, #6 and smaller
class B lap = 1.3 × 27.4             = 35.6"     §25.5.2.1 — every bar spliced at one section
authored: 4 #5 galvanized dowels projecting ~30"+ from the wall pour
```

**The wall-top cold joint is the wettest, saltiest elevation on the column** and a documented
chloride path. Roughen it to 1/4" amplitude, remove laitance, set a bentonite or crystalline
waterstop strip inside the dowel circle. A 12" round on a 12" wall is flush on both faces, so
there is no ledge to pond on.

**No grout island at the beam seat.** An exposed non-shrink grout island is a 10-20 year
element — not air-entrained, sitting at the wettest point. Cast the top **to line** under the
beam footprint, screed the ≥15° wash and drip lip around it (BIA Tech Note 36A), and take up
tolerance in the 1/2"-1" **stainless** standoff's shim pack. If a levelling bed proves
unavoidable it is an **epoxy** grout confined under the standoff plate, never a cementitious
island with exposed shoulders. The HGAM10 stays — value-engineered in already, and on a 12"
round its Titen Turbos sit at ~3-3/4" edge against Simpson's 1-1/2" minimum, where a 10"
round would have left no margin. Isolate the gusset from the stainless standoff with EPDM or
HDPE. (PT-SG-COL keeps its grout island for now; aligning that one is a follow-up.)

**Sequence.** Dowels cast with the wall pour (4 #5 galvanized projecting ~30" per column).
Tube seated over them in a **plywood saddle collar screwed to the wall FACES** — a flush tube
leaves no wall top to Tapcon a collar to — top kicked with two 2x4s to the porch deck framing
(~8' kickers, never down to the garden floor), and the four tubes tied together with a
temporary stick. Cage tied flat, dropped and wired to the dowels, 2" cover held by plastic
wheel spacers. **~0.26 cy per column, ~1.05 cy for the four** (0.785 ft²/ft × 9.01'), plus
PT-SG-FCOL's 0.29 cy: a bucket, or one small pump call. 12-18" lifts with a 1" pencil
vibrator in the core, never on the cage. Air verified at the point of placement; 3/4" or 3/8"
aggregate. Broom or float finish on the wash, never steel-trowelled (NRMCA CIP 2 — troweling
drives the entrained air out of exactly the layer that scales). Two-person day to form, an
hour to pour, strip at two days, wet-cure 7 days protected from freezing to 3,600 psi
(ACI 306), a week's cure before the glulam lands. Silane at 28 days, re-applied ~10-yearly —
maintenance, not a substitute for cover. Optional mineral paint to match the white centre
posts.

**If forming is unwanted:** precast the four columns off site with dowel sleeves and grout
them on. The stock steel posts stay the fallback.

---

## 8. The guards

Both guards became **Williams Architectural Products, ICC-ES ESR-3485, 42" black** (Menards;
Eagan MN, the Ultralox factory) on 2026-09-02, with **Fortress Al13 Home** as the alternate.
Same 6063/6005A alloys and an AAMA-grade powder coat at ~$30-45/LF material against Trex
Signature's $72-98: Signature's premium buys sightline, not life. ESR-3485's maximum post
spacing at 42" is **91.3"**; the model's 60" complies with room to spare. A China import
lands at $45-60/LF after Section 232 (50%) + 301 (25%) and carries no evaluation report:
rejected on the report, not on the price.

**The two mounts split, and the substrate is why.**

- **RL-SG-PORCH → surface mount.** Its west and east legs run along the inner face of
  W-SG-W1/E1, so each 5×5 baseplate lands on a 12" concrete wall top and takes ESR-3485's
  concrete-baseplate row: four 1/4" × 3" corrosion-resistant anchors, no bracket, no
  through-bolt. Top mount is cheaper and is taken wherever the substrate allows it. The
  SOUTH leg has no wall under it — it runs over BM-SG-FRW/FRE, whose tops carry
  TR-SG-CAP-FRW/FRE and their butyl — so those five posts bolt through the composite plank
  into solid blocking in the joist bay just north of the beam. **Never anchor through a beam
  cap:** a 304-stainless plate on 0.019" aluminium coil in a wet exterior location pits the
  aluminium (it is anodic), and the fastener pierces the butyl that IS the dielectric between
  that coil and the copper-treated framing.
- **RL-SG-BALCONY stays fascia mount.** `FS-SG-DECK`'s aluminium plank is the porch roof and
  carries **no penetrations at all** since the heat pumps went to grade. Surface posts would
  put ~36 holes through the one waterproof plane in this structure to save bracket money.
  Brackets through-bolt the PVC fascia and the 2x8 rim per **Ultralox's own fascia-mount
  instructions** — four 5/16" × 4" bolts with washers and nuts per bracket, bracket top 1/2"
  below the rim top, a foot block mid-panel — with nuts on the rim's inside face, reachable
  from the open joist bays below. Manufacturer's instructions are the accepted basis under
  IRC R106 / R301.1.3; no PE letter. A solid block between the rim and the first joist at
  each post stops the rim rolling under the 200 lb load, and is authored in
  `FS-SG-DECK.reinforcements`.

ESR-3485's fascia-bracket row is written for **concrete**, which is why the wood-rim detail
above comes from the manufacturer's instructions rather than from the report.

---

## 9. What this note does NOT cover

- **Base fixity itself.** The doweled lap is detailed to deliver it; no calculation here
  proves the wall top's own capacity to receive the moment, nor the foundation's rotational
  stiffness. That is the first thing a stamp should look at.
- **Shear in the column** (the section is enormous against a few hundred pounds, but
  "enormous" is a judgement), torsion, and the diaphragm claim that delivers storey shear to
  four corners rather than six posts.
- **C_f.** §2b spends it at the Case A/B ceiling rather than reading the figure. An engineer
  with ASCE 7-16 to hand should read the real cell.
- **The two wood centre pillars**, which stay prescriptive under IRC R507.4 and are graded
  there.
- **A shielding factor** on the three-beam E-W band (§2b), which would only reduce a demand
  already at d/c 0.07.
- **The Simpson round-footing letters** — an unverified lead: Simpson publish engineering
  letters for some connectors on round concrete, which might supersede the edge-distance
  arithmetic in §7 if one covers the HGAM10. Not located.

---

## 10. Where the model reports this

```
haus engineering houses/catlin
haus engineering houses/catlin --item deck_post/PT-SG-BF1     # a corner column, term by term
haus engineering houses/catlin --item deck_beam/BM-SG-BLC     # the centre glulam
haus engineering houses/catlin --fingerprint deck_post/PT-SG-BF1
```

Four `deck_post/PT-SG-B{R,F}{1,3}` records and three `deck_beam/BM-SG-BL*` records, all
`draft`, all `unsealed`. `structural.lateral_racking` now names each corner column as the
deck's lateral system and delegates to the same `deck_post/<tag>` item — one design, one
stamp, two checks.
