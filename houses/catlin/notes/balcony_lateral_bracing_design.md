# The balcony's lateral bracing — engineering basis for an engineer's review and stamp

**House:** catlin, Ramsey County, Minnesota (Minnesota Residential Code 2020, adopting the
2018 IRC).
**Structure:** the sunken garden's balcony — a 21'-0" × 9'-8" deck at +10'-0", carried on six
6x6 pillars on pinned standoff post bases, braced by eight 2x6 knee braces.
**Written:** 2026-08-30. Every number below is recomputed here from first principles with the
arithmetic shown, so a reviewer can check the whole chain without opening the model.
**What is asked of the reviewer:** this is a screening lateral design under IRC R301.1.3
engineered design. It is offered for a licensed engineer's check and stamp. It is **not** a
stamped design and nothing in the model treats it as one — `structural.lateral_racking`
reports UNKNOWN against every one of these joints and will keep doing so until
`KneeBrace.engineering_spec` carries a real design.

**One input came from outside and could not be sourced.** See §3.

---

## 0. Why this structure needs the calculation at all

The balcony has no shear walls. `W-SG-ARCH` and the three `W-SG-RAIL-*` parapets were removed
when the arch was dropped, and with them went the only element resisting east-west load; the
two side walls `W-SG-W1`/`E1` run north-south and brace that direction only. What is left is
six posts on `ABU66SS` standoff bases and eight knee braces. Simpson state the limit of a
standoff base in their own reports (ESR-1622, ESR-3050): post bases *"do not provide adequate
resistance to prevent members from rotating about the base"* and are *"not recommended for
non-top-supported installations."* Both bases and the beam bearings above are pins. **The
braces are the entire lateral system**, which is why an unrated connector in them was worth
finding.

---

## 1. Design wind

`plan/site.py`, authored 2026-08-30 from **MN Rules 1309.0301**, the state's amendment to IRC
Table R301.2(1): *"ULTIMATE DESIGN WIND SPEED (mph) — 115"*, statewide, with topographic
effects to be *considered* per R301.2.1.5 and *"wind exposure category … determined on a
site-specific basis in accordance with Section R301.2.1.4."*

| quantity | value | source |
|---|---|---|
| V<sub>ult</sub> | 115 mph, 3-s gust | MN Rules 1309.0301 (IRC Fig. R301.2(5)A = ASCE 7-16 Fig. 26.5-1B) |
| Risk Category | II | ASCE 7-16 Table 1.5-1 — a dwelling |
| Exposure | **B** | ASCE 7-16 §26.7.3; suburban parcel, buildings and trees in every upwind sector |
| K<sub>zt</sub> | 1.0 | §26.8.2 — flat parcel, none of §26.8.1's three conditions |
| K<sub>d</sub> | 0.85 | Table 26.6-1 |
| K<sub>e</sub> | 1.0 | §26.9 permits it; the tabulated value at 830 ft is 0.97, so 1.0 is conservative |
| G | 0.85 | §26.11.1, rigid structure |

`notes/catlin_truss_engineering.md` §2 carries Exposure **C** for the cladding stand-off, and
that stays. It is a deliberate ~40 % margin on a screw-withdrawal check where the margin is
nearly free, it prints its own Exposure B number alongside, and V<sub>ult</sub> does not
change with exposure in any case — only K<sub>z</sub> does.

### Velocity pressure

The appurtenance tops out at the balcony guard, +13'-7 1/2". The ground beneath it is the
**sunken garden floor at −9'-4"**, not the site grade at −2'-10": z in ASCE 7 is height above
the ground *there*, and taking the grade would shorten z by 6'-6" and understate q.

```
h   = 13.625 - (-9.333)                    = 22.96 ft
K_z = 2.01 · (22.96 / 1200) ^ (2/7)        = 0.649        (Table 26.10-1, Exposure B)
q_h = 0.00256 · 0.649 · 1.0 · 0.85 · 115²  = 18.7 psf     (eq. 26.10-1, strength level)
```

The same arithmetic reproduces `catlin_truss_engineering.md` §2's independently hand-worked
K<sub>z</sub> = 0.98 / q<sub>h</sub> = 28.2 psf at Exposure C and 0.70 / 20.1 psf at Exposure
B, h = 30 ft. `tests/test_wind_loads.py` pins that agreement; the note is the oracle, not the
code.

---

## 2. Projected area

ASCE 7-16 **§29.3**, solid freestanding walls and solid signs. It is the right provision by
elimination: Ch. 27 and 28 want an enclosure classification this open structure does not have,
and Components & Cladding sizes cladding suction, not a storey shear.

Every dimension below is read off the model, not authored — deepen `TR-SG-FASCIA` or retype a
rail and the demand moves with it.

| band | depth | run | area | wind direction it faces |
|---|---|---|---|---|
| `TR-SG-FASCIA` + deck edge | 9.0" | 21.0' | 15.7 sf | N-S |
| `BM-SG-RAIL-F` (2x8) | 7.25" | 20.0' | 12.1 sf | N-S |
| `BM-SG-RAIL-R` (2x8) | 7.25" | 20.0' | 12.1 sf | N-S |
| **N-S total** | | | **39.9 sf** | |
| `TR-SG-FASCIA` + deck edge | 9.0" | 9.7' | 7.2 sf | E-W |
| `BM-SG-BLW` (3-2x12) | 11.25" | 9.7' | 9.1 sf | E-W |
| `BM-SG-BLE` (3-2x12) | 11.25" | 9.7' | 9.1 sf | E-W |
| **E-W total** | | | **25.4 sf** | |

**The guard is excluded, and that is a decision.** `RL-SG-BALCONY` is a 42" aluminium guard
with 2x2 posts at 60" and balusters at 4" clear — roughly 25-30 % solid. Fig. 29.3-1's
opening reduction, `C_f × (1 − (1 − ε)^1.5)`, is written for a sign whose openings are *under
30 % of gross*, which is the opposite condition. Pushing 0.28 through it would return about
0.39 and look like a code result. An open guard is §29.4 territory (open signs and lattice
frameworks), a different figure this calculation does not hold. **A reviewer should price the
guard separately.** Its gross area is 73.5 sf N-S — larger than everything above — so at a
solidity of 0.28 it plausibly adds on the order of 20 sf of effective area to the N-S case,
which would roughly halve the margins in §4. That is the single largest uncertainty in this
note and it is not resolved here.

The centre beam `BM-SG-BLC` is also excluded from the E-W bands: it stands inboard, in the
wake of `BM-SG-BLW`, and §29.3 has no shielding provision to claim credit for either way.

---

## 3. The force coefficient — the one input that is not sourced

`F = q_h · G · C_f · A_s` (eq. 29.3-1), and C<sub>f</sub> comes from Fig. 29.3-1, a two-way
table on B/s and s/h. **ASCE 7-16 is a copyrighted standard and that grid is not published in
any freely accessible authoritative source.** Three individual cells were verified on
2026-08-30 from independent vendors' worked examples:

| B/s | s/h | C<sub>f</sub> (Cases A & B) | source |
|---|---|---|---|
| 2.50 | 0.25 | 1.80 | Struware, *Guide to Wind Load Procedures* Ex. 5.1 |
| 2.00 | 0.50 | 1.70 | Meca Enterprises, *Wind Loads on Solid Signs* |
| 20.0 | 1.00 | 1.30 | Meca Enterprises, *Wind Loads on Freestanding Walls* |

This balcony reads B/s ≈ 3.7, s/h ≈ 0.11 (E-W) and B/s ≈ 10.7, s/h ≈ 0.09 (N-S). Neither is a
cell above, and **nothing here interpolates, curve-fits or assumes across the gap.**

So the calculation is inverted instead. §4 reports, for each joint, the **critical
C<sub>f</sub>** at which it exactly reaches its allowable, against **1.80** — the largest
coefficient Cases A and B are known to produce. A joint whose critical C<sub>f</sub> clears
1.80 is adequate for every value the table can hold, and the missing cell cannot change the
answer. A reviewer with the standard on the desk reads one number and confirms it in a minute.

**Case C is not covered.** It is required when B/s ≥ 2, which both directions are, and its
leading-edge strip carries a much larger coefficient — published examples show 2.25 and 4.07.
It applies to a strip of width s, and s here is 1.5'-2.9', so it is a **local member** question
(the end bay's fascia, the rail's end span) rather than a storey-shear one. It is not worked
here and a reviewer should.

---

## 4. Demand to capacity, joint by joint

### The free body

Post pinned at base, shear V delivered at the beam at height h, brace meeting the post a below
that at 45°. Moments about the base — the brace's vertical component acts along the post axis
and takes no moment:

```
V · h = P · cos45° · (h − a)      ->      P = V · h · √2 / (h − a)
```

At h = 9.23' (rear pillars) and a = 3.00': **P = 2.10 V**. At h = 9.06' (front): **P = 2.11 V**.
The brace sees more than double the shear delivered above it, which is the opposite of the
intuition that a brace "takes its share."

### Distribution — a stated assumption, not a derivation

Shear is split **equally among the four braces resisting each direction**. This assumes the
deck sheathing and the two continuous brace rails act as a collector delivering load to the
braced end bays. `plans/TODO.md` has flagged that diaphragm claim as unengineered since
2026-08-18 and it remains so: nothing here checks the deck's in-plane stiffness, its
fastening, or the rails' connection into the corner posts. **It is the second-largest
uncertainty in this note.** The two centre pillars `PT-SG-BR2`/`BF2` carry no brace and take
no share in this distribution.

### The connectors

Both ends of each brace: **Simpson KBS1Z**, one per end (Simpson's connection type 2 — *"for
2x knee brace, install single KBS1Z on each end"*; type 1's two-per-end is for equal-width
members, and a 2x6 into a 6x6 is not that). IAPMO UES ER-280 rev. 04/28/2026 Table 7,
SPF/HF column, in-service moisture ≤ 19 %:

```
F1, brace angle = 45°        = 540 lbf     (DF/SP 630)
F1, brace angle = 30° or 60° = 440 lbf     (DF/SP 510)
```
Footnote 2: already increased for wind at C<sub>D</sub> = 1.60, no further increase.
Footnote 3 permits interpolation between the two angles. These braces are at a true 45°.

### The result

| direction | A<sub>s</sub> | at C<sub>f</sub> 1.80 | per brace | brace axial | KBS1Z F1 | critical C<sub>f</sub> |
|---|---|---|---|---|---|---|
| E-W | 25.4 sf | F<sub>ASD</sub> 436 lb | 109 lb | 229 lb | 540 lbf | **4.23 – 4.26** |
| N-S | 39.9 sf | F<sub>ASD</sub> 685 lb | 171 lb | 360 lb | 540 lbf | **2.69 – 2.71** |

(F<sub>ASD</sub> = 0.6 · q<sub>h</sub> · G · C<sub>f</sub> · A<sub>s</sub>, ASCE 7-16 §2.4.1
combinations 5 and 6.)

**Every one of the eight joints clears 1.80 with margin — 1.5× in the governing N-S direction
and 2.4× E-W.** The bracing is adequate for any value Fig. 29.3-1 can hold, and the unread
cell cannot change that. The 1.5× N-S margin is, however, roughly what the excluded guard
(§2) could consume, which is why the guard is called out rather than quietly dropped.

### The connector substitution this calculation forced

These joints carried **`APVKB45-6`**, Simpson's Outdoor Accents Avant *decorative* knee brace,
from the day the balcony was framed. It has no published allowable load of any kind. That was
established from the reports, not assumed:

- **IAPMO UES ER-102** rev. 08/21/2026, the stamped/welded connector cross-reference index,
  enumerates the whole AP/APV series it covers — APL/APVL, APT/APVT, APA/APVA, APB3.75,
  APB44…APB1010 and their APV twins, APDJT, APLH, APHH — and points them at ER-280. **APVKB
  appears nowhere in it.**
- **ER-280** rev. 04/28/2026, the report that index points to, has no APVKB section, table or
  figure. Its knee-brace product is the KBS1Z (§3.1.7, Table 7).
- Simpson's own Outdoor Accents literature tabulates uplift and download for the Avant **post
  bases** (APVB44 1,035/6,725 lbf; APVB66 1,260/11,450 lbf) and prints no load row for the
  knee brace.

An unrated connector in the *entire* lateral system of a freestanding deck at storey height is
a hole in the load path, not a documentation gap. The braces now take KBS1Z, which is
Simpson's purpose-built structural knee-brace stabilizer, was already in this house's catalog
and price file for the breezeway beams, and is the only knee-brace connector anywhere in the
catalog with a code-report allowable — published *by brace angle*, which is precisely the
capacity a 45° brace needs.

**It is also cheaper.** 16 KBS1Z at $3.50–6.50 is $56–104, against the 8 APVKB45-6 they
replace at $22–45, $176–360. Net material saving **$72–304**, and the rated part is the one
that costs less. The 2x6 diagonal, its 3'-0" leg, its geometry and its 1/2" through-bolts are
all unchanged; only the steel at the ends moved.

---

## 5. The through-bolts

`APVB12-6` — 1/2" HDG hex bolt, 6" long, with washer, two per brace (one each end). NDS 2018
Ch. 12 yield-limit design, single shear, 1-1/2" side member (the 2x6 brace) into a 5-1/2" main
member (the 6x6 post / the 2x8 rail), SPF at G = 0.42 both sides, F<sub>yb</sub> = 45,000 psi:

```
F_e∥    = 11,200 · G                = 11,200 · 0.42        = 4,704 psi     (Table 12.3.3)
Mode I_s: Z = D · l_s · F_es / R_d  = 0.5 · 1.5 · 4,704 / 4 =   882 lb     (R_d = 4K_θ, K_θ = 1)
Mode I_m: Z = D · l_m · F_em / R_d  = 0.5 · 5.5 · 4,704 / 4 = 3,234 lb
```

Against a maximum demand of **360 lb** (N-S, C<sub>f</sub> 1.80), the bolt uses 41 % of Mode
I<sub>s</sub>.

**This is not a complete bolt check and must not be read as one.** NDS requires the *minimum*
across all six yield modes, and modes II, III<sub>m</sub>, III<sub>s</sub> and IV — which need
the full k<sub>1</sub>/k<sub>2</sub>/k<sub>3</sub> set — are not worked here. Two modes give an
upper bound on capacity, not a lower one. NDS **Table 12E** tabulates this exact geometry
directly and a reviewer should read the row rather than trust the two modes above. What can be
said without it: the demand is 41 % of the mode most likely to govern for a thin side member,
and the geometry (a 1/2" bolt in a 1-1/2" side member) is not one where the modes typically
spread by the 2.4× that would be needed to overturn the result. **That last sentence is an
engineering judgement, not a calculation, and is flagged as one.**

Also unchecked here and belonging to the same reviewer: end and edge distance and spacing per
NDS Table 12.5.1 (a 1/2" bolt wants 4D = 2" edge and 7D = 3.5" end in tension), and the
group-action factor C<sub>g</sub> of Table 11.3.6A — which is 1.0 for a single bolt per row,
so it does not reduce anything here, but would the moment a second bolt is added.

---

## 6. The rails as struts

`BM-SG-RAIL-R` / `BM-SG-RAIL-F` — continuous 2x8 KDAT, face-bolted to the inboard face of all
three posts in each row with 2 × 1/2" HDG bolts per post (12 bolts total). They are the E-W
collector: they gather the two centre pillars' share and deliver it to the braced end bays.

**Tension.** The largest axial a rail collects is one centre pillar's share of the E-W storey
shear, ≈ 436/6 = **73 lb**. Gross section 1.5 × 7.25 = 10.875 in²; SPF No. 2 F<sub>t</sub> =
450 psi × C<sub>D</sub> 1.6 = 720 psi → **7,830 lb** gross, and well over 5,000 lb on any
reasonable net section through a bolt row. Two orders of magnitude of margin. Not close.

**Compression, and here the screening finds something.** The same 73 lb runs the other way
under reversed wind. The rail is 1-1/2" thick about its weak axis and is restrained only where
it bolts to a post, at 10'-0" centres:

```
l_e / d = 120" / 1.5" = 80
```

NDS 3.7.1.4 caps l<sub>e</sub>/d at **50** for a compression member. At 80 this rail is
outside the limit as a column, by a wide margin. In practice the load is 73 lb, the member is
bolted flat against a post face and sheathed against on one side, and no engineer would size
this as a free column — but **the model states the geometry and the geometry does not satisfy
3.7.1.4 as drawn**, and that is exactly the sort of thing a screening exists to surface rather
than to talk itself out of. The cheap fixes if a reviewer wants one are a mid-span block back
to the post line (halving l<sub>e</sub> to 60/1.5 = 40) or laying the rail flat. Neither is
authored; the decision is the consultant's.

**The bolt schedule itself remains assumed.** Two 1/2" bolts per post is a carpenter's
schedule, not a designed one. It is what `plans/TODO.md` has flagged as open since the
brace-rail redesign and it stays flagged.

---

## 7. What this note does NOT do

- **It does not compute Case C**, the near-windward-edge zone breakdown Fig. 29.3-1 requires
  at B/s ≥ 2. That is a local member check on the end bay.
- **It does not price the guard's wind load.** §2 says why, and estimates the effect as
  potentially halving the N-S margin.
- **It does not check the diaphragm.** The equal split to four braces assumes the deck and
  rails collect and deliver; nothing verifies in-plane stiffness, sheathing or fastening.
- **It does not check the post bases against the brace reaction.** ESR-1622 publishes ABU66
  uplift and download and **no lateral value at all**, and in any case the ten bases here are
  `ABU66SS` — which ESR-1622 does not cover (§3.2.1 evaluates ASTM A653 galvanised steel; the
  stainless model is in no table in the report, despite retailers citing it). The anchor bolts
  are outside the report's scope entirely (§5.6). This is the least-answered link in the chain.
- **It does not check the posts as columns**, the beams for the vertical load, or anything
  seismic — Minnesota is SDC A/B and wind governs, but that is stated, not demonstrated.
- **It does not check frost, bearing or overturning of the concrete below.** Those belong with
  `notes/sunken_garden_retaining_screening.md`, which is a companion ask to the same
  consultant, not a separate problem.
- **It is not a stamped design.** `structural.lateral_racking` reports UNKNOWN on every joint
  here and will until `KneeBrace.engineering_spec` carries a real one. That is the same
  discipline `catlin_truss_engineering.md` and `notes/uplift_load_path.md` already keep: a
  hand-worked calculation in this repository never flips a check green on its own strength.

## 8. Where the numbers live

| what | where |
|---|---|
| the wind basis | `plan/site.py` — `design_wind_speed_mph`, `wind_exposure`, `risk_category` |
| q<sub>z</sub> and K<sub>z</sub> | `packages/engine/src/typehaus/wind.py` |
| the three verified C<sub>f</sub> cells | `checks/structural/_asce_29_3_table.py` |
| the demand-to-capacity chain | `checks/structural/lateral_racking.py` |
| the KBS1Z allowable, transcribed | `library/hardware.py::KBS1Z_KNEE_BRACE` |
| the braces themselves | `params/sunken_garden.py::KNEE_BRACES` |
| the oracle for §1's arithmetic | `notes/catlin_truss_engineering.md` §2 |
