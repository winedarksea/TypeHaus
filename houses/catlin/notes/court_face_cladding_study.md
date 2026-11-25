# Court face cladding study: brick, metal panel, or poured concrete (2026-11-24)

A design study for the owner, on branches. **Outcome (2026-11-24): the owner took B's approach in LP SmartSide smooth panel, painted Potters Clay, with brick kept one switch away (variant `court-face-brick`)** — `court_face_lp_panel.md` is the live note; the branch names below are history.

| Branch | What it holds |
|---|---|
| `study-cladding` | the engine changes both options needed, and this note. The reference house is unchanged on it: 0 FAIL, all 32 register ratios identical to main |
| `study-cladding-b` | option B, the metal panel (one commit on top of `study-cladding`) |
| `study-cladding-c` | option C, poured concrete (two commits: as drawn, then the winter fix) |

The face in question is the house's basement wall inside the sunken court, between `W-SG-W1` and
`W-SG-E1`, behind `D-B-SUNKEN` and `WIN-B-SAUNA`. Today it is `W-B-BRICK`, an anchored brown brick
wythe on the grade beam `W-SG-BRKBM`.

Every number below came from the engine on these branches (`haus engineering`, `haus check`,
`haus takeoff`) or from the hand arithmetic shown. Costs are the takeoff's net installed rows from
`prices.toml`, before waste, contingency and tax. **ESTIMATE** marks any number I added by hand. The
soil is the specified soil (bed friction 0.43 to 1.00, at-rest 60 psf/ft), as in every court record.

## The answer in one table

| | A. Brick (today) | B. BBD75 metal panel | C. Poured concrete wall |
|---|---|---|---|
| Register items | 32 | 31 (`veneer_anchor` gone) | 31 (`veneer_anchor` gone) |
| Approvals needed | 2024 IRC adoption or an R104.11 request (the ties) | none: BBD75 is a published table read | none, unless it is used to retire the porch prop (then an engineered plate) |
| `haus check` FAIL | 0 | 5, one root cause (see B) | 1 as drawn; **0** with one #4 at each edge of FT-SG-W1/E1 |
| UNKNOWNs retired | — | veneer_anchor, veneer_cavity_width, sauna window flashing | veneer_anchor, veneer_cavity_width |
| Cost against A (takeoff) | — | **−$2,424 to −$4,694** | **+$845 to +$2,094** (with the winter fix) |
| Cost against A (with my additions) | — | about −$2,200 to −$4,300 | about +$1,100 to +$2,500 |
| retaining_system (governs) | 0.981 | 0.981 | 0.936 |
| thermal_break_transfer (governs) | 0.998 | 0.967 | 0.814 with the fix (1.086 without it) |
| Trades | mason on the court | mason off the court; spray foam, girts, siding take two more walls | mason off the court; concrete takes one more wall in a pour it already makes |
| Look | brown brick accent | the house's white board and batten comes down into the court | a fourth white-washed concrete wall; the court becomes a box |

**Recommendation: B.** It is the cheapest option, and it removes the only approval the court
still needs. It also removes the brick's five dependent parts (the beam, its board, the masonry
anchor item, the weeps and soft joints, and the slab void). Taking the beam's board out of the
house's slab-edge path drops the two highest house-side break rows by a lot (0.676 → 0.230 and
0.400 → 0.204). Its five FAILs share one cause, which is detailing: the engine runs the panel's
base flashing through the door. C is the most durable face and the best for daylight, but it costs
money and it pushes the winter tension over. It does not retire the porch prop by itself either
(see C.5).

## A. Brick, as drawn: the baseline

| Item | Value | Source |
|---|---|---|
| `veneer_anchor/W-B-BRICK` | no calc; waits on MN adopting the 2024 IRC, else an R104.11 request | `haus engineering` |
| Cavity, brick back to studs | 6 1/2" against the 2024 table's 6 5/8" (W2.8): 1/8" of margin | `structural.veneer_cavity_width` |
| Airspace | 1.94" | same |
| Ties, HB-213-2X with 400H-2X hooks | 182.4 lb of 200: **0.91**, on a friction upper bound of 1.0 that is UNVERIFIED | `sunken_garden_veneer_beam.md` §6n |
| Lintels | 2 × L3x3x1/4 HDG, 7.78 LF, IRC Table R703.8.3.1 | `BM-B-BRICK-LINTEL-*` |
| Flashing | Type 316 stainless at the base and both heads, an EPDM strip under each head sheet; bond break = the dry base sheet | `FL-B-BRICK-*` |
| Weeps | open head joints at 33" maximum; not modelled | R703.8.6 |
| Bed under the beam | peak 1,217 psf, 0.61 of 2,000 | §6m |
| Mason | one checkpoint (`court`) on the masonry visit | `tasks.toml` |

**What the brick costs (net installed, the rows B removes):** brick 88.5 SF $1,682-2,655; lintels
$249-513; soft joints $179-372; the beam `SG_VENEER_BEAM_14` $429-718 and its bar; flashings
$125-276; the Trex box sides $227-398; bed stone $120-180; the two reveal openings $315-795. That
is about **$3,400 to $6,100**. Two costs are not counted. The 316 stainless sheet is billed at the
aluminium drip rate, so it is under-priced. The ties and weeps sit inside the brick's $/SF rate.

## B. Metal panel: BBD75 board and batten on the house's girts (`study-cladding-b`)

### B.1 What was drawn

- `W-B-S3-FR` takes `EXT_2X6_BOARD_BATTEN`, the house's own south-facade stack: 2x6 studs, CDX,
  4" ccSPF, a 1/2" vent gap, KDAT girts at 24" on TimberLOKs, and BBD75-1212 in Linen White (81).
  `W-B-S2-FR` takes the same stack with the sauna liner inboard of the studs
  (`SAUNA_LINER_ON_EXT_2X6_BB`). Both still align on the sheathing face, so nothing indoors moves.
- **Removed:** `W-B-BRICK`, both soft joints, both lintels, all six brick flashings, both reveal
  openings, `W-SG-BRKBM`, its 2" board, its bed `FB-SG-BRKBM`, the tread-bed recess
  `AO-SG-BRKBM-TREAD-BED`, and the rim void `FO-SG-BRKBM`.
- **Does anything else need the beam? Checked, and no.** It reinforces nothing: W1/E1 pass on their
  own, and the court's sliding body never counted it. Three things did lean on it:
  1. D-B-SUNKEN's tread drain slot, which ran down the beam's joint. In B the slot names no outlet,
     and the engine reports it as a new UNKNOWN. The tread drains onto the rim slab's edge instead;
     the door is under the porch roof.
  2. The 14" strip between the beam and the house. The rim slab now runs on to 1/2" off the curb's
     coated foam (y −4 3/4"). Add 17 LF of sealant there, at the movement-joint rate: **ESTIMATE
     +$200-425**.
  3. FT-SG-W1/E1's 0.685" north extension. It is now unneeded but harmless, so I left it.

### B.2 The two conditions the brief asked about

**The base, in the splash and salt zone.** The panel stops on the 7 1/4" concrete curb. The
house's rainscreen base Z (Una-Clad aluminium) and bug screen close it. Aluminium is the right
metal where salt arrives on boots and cannot leave the court. The curb's 4" XPS had sat behind the
brick; now it faces the court, so it takes the house's tinted acrylic skin (Tuff II), as BASEMENT_8
does above grade (+8.6 SF). The steel panel's lowest cut edge sits 7 1/4" above the court floor,
under the porch roof. Whether Metal Sales' warranty excludes salt splash at that height is
UNVERIFIED.

**Opening trim.** D-B-SUNKEN keeps its foam-bed Trex tread, and its jambs and head are trimmed like
D-M-PORCH: a Captivate jamb extension and casing, and a dark metal wrap. WIN-B-SAUNA now gets the
house's window flashing and trim. The old "no opening flashing" advisory on it is retired. The
house's head cap and custom jamb and sill trims bill automatically.

### B.3 Results

| Row | A | B |
|---|---|---|
| `structural.cladding_wind` (BBD75, published table) | — | PASS: zone 5, 19.9 psf outward against 58 allowable |
| thermal_break_transfer, winter side run | 0.998 | **0.967** (hand: (129,306 − 3,994) / 2 = 62,656 against 64,800) |
| house slab-edge peak sustained load | 0.676 | 0.230 |
| house global sliding | 0.400 | 0.204 |
| house near-line plan flexure | 0.253 | 0.216 |
| retaining_system | 0.981 | 0.981 (deep plane 0.941 → 0.940) |
| column_support, base_rotation, retaining_wall | unchanged | unchanged |
| `haus check` | 0 FAIL | 5 FAIL |

**The 5 FAILs share one cause.** The engine derives the panel's base Z, its EPDM strip and the bug
screen along the whole wall base, and D-B-SUNKEN's opening reaches the curb top. So the tread and
the jamb returns "intersect" them, and the KDAT jamb strapping lands on the bug screen. The real
detail stops all three at the jambs and laps the door pan over them. The engine cannot express that
yet. It needs `resolve/rainscreen_base_flashing.py` to split its run at a door whose opening reaches
the base.

### B.4 Cost, trades and visits

- **Takeoff −$2,424 to −$4,694.** The brick bundle is −$3.4-6.1k (the A list above). Against it:
  BBD75 +84 SF (+$451-749), ccSPF +84 SF (+$336-505), girts, TimberLOKs and plates (≈ +$350-550),
  the panel trims (≈ +$470-700), and the curb coating (+$54-100). Also removed: the framed walls'
  membrane and XPS (−$487-945) and the mineral wool (fibreglass replaces it).
- Adding the joint sealant (B.1) gives **about −$2,200 to −$4,300**. B also adds five unpriced row
  groups, all D-B-SUNKEN's door trim kit (Captivate casing, the same keys the house's other doors
  use).
- **Trades:** the mason leaves the court; the fireplace keeps the masonry visit. The spray foam and
  girt crew and the siding crew add two short walls to visits they already make. The waterproofing
  visit loses those two walls. Placement 2 loses the beam's blockout.

### B.5 Durability and look

- **Durability:** a 24 ga PVDF panel, sheltered by the porch roof. It dents at body height in a
  court people live in, but one board replaces at a time. The cavity behind it stays reachable,
  which the brick's does not. The coated curb takes the splash.
- **Look:** the court's house face becomes the house itself, the same white board and batten as
  the main storey above, and every court face reads white. The brown accent is gone. A coil colour
  could bring a different accent back as a `LayerMaterial` on these two walls.

## C. Poured concrete, cast with the court (`study-cladding-c`)

### C.1 What was drawn

- `W-SG-BRKBM` grows into the court's north wall: the same 12" EXPOSED_MIX section, from its bed at
  −120 3/16" to −13 1/3" (the brick's old top, 2 1/12" under the porch joists). It is washed white
  on the court face, as the other four walls are. Its 2" board is **banded to the old beam's
  17 3/4"** against the house strips. Above that, the north face stands 1.94" clear of the walkout's
  foam, the old brick cavity. There are no ties, and it moves with the court.
- **Cage:** #4 @ 16" each face, both ways, which is the court's own T&S read (`_RET_STEM_STEEL`).
  The horizontals are hooked round both corners into W1/E1 (`continues_into`).
- `AO-B-BRICK-WIN` and `-DOOR` move onto the wall at the same plan and elevations. A third CD-B-SPA
  sleeve goes where the wall runs into W1. Removed: the brick, the soft joints, the lintels and the
  flashings.
- **Is the beam a real footing tied to FT-SG-W1/E1? Yes.** It is the bottom 17 3/4" of the wall
  itself, on its own stone. Sizing (hand): the wall plus plinth weigh 150 × (7.425 + 1.479) =
  1,336 plf on a 12" bed. That is 1,336 psf, **0.67 of 2,000**, concentric. The brick's eccentric
  0.61 reached nearly the same with far less weight. The 12" width stands, and nothing is added.

### C.2 What the engine had to learn (on `study-cladding`)

1. A footing-less wall on its own bed whose bars name a loop wall now slides with the court, by its
   concrete, net of its openings (`retaining_system_body.bedded_tied_walls`).
2. A banded board is only as tall as its band. Without this fix the record counted the north wall's
   full 8'-11" as board, which put the house slab-edge rows up for no reason.
3. Two openings on one span (the door over the tread's blind recess) cut their union. Before, one
   opening's sill band filled the other's hole.
4. A cast reveal wall in front of the host is trimmed like brick: the returns cross the cavity to
   its back.
5. The clash test honours a layer's band.
6. A foundation wall's horizontals may name the walls they turn into. The corner bars are not laid
   out, so I bill them by hand.

On the reference house none of this moves a number.

### C.3 The court records, old to new

| Record / row | A | C as drawn | C + fix |
|---|---|---|---|
| **retaining_system** (governing) | **0.981** staged | 0.936 fallback staged | **0.936** |
| staged backfill FS | 1.529 | 1.603 | 1.603 |
| dry sliding FS | 1.930 | 2.014 | 2.014 |
| perched FS / flooded FS | 1.568 / 1.702 | 1.637 / 1.783 | same |
| deep plane, lip | 1.594 | 1.640 | same |
| **thermal_break_transfer**, winter side run | **0.998** | **1.086 OVER** | **0.814** |
| winter spliced joint | 0.391 | 0.426 | 0.426 |
| retaining_wall × 3, stem flexure | 0.865 | 0.865 | 0.865 |
| retaining_wall × 3, base restraint | 0.777 | 0.745 | 0.745 |
| column_support W1/E1 | 0.578 | 0.578 | 0.578 (the engine has no corner path; see C.6) |
| base_rotation BR1/BR3 | 0.309 | 0.309 | 0.309 (same) |
| `haus check` | 0 FAIL | 1 FAIL (the winter row) | **0 FAIL** |

**Oracle arithmetic.** The engine adds 15,409 lb, the wall and plinth net of the openings and of
the parts standing on W1/E1's stems and toes.

```
wall above plinth, gross      17.0 x 7.425 x 1.0 x 150                    = 18,934 lb
less door 63.3 x 80 / 144 = 35.17 sf, window 1.94 sf: 37.12 x 150           = -5,568
plinth (A's beam, 17 ft clear)  17.0 x 1.479 x 150                           =  3,772
                                                                              17,138 lb gross of overlaps
engine, stem overlaps (x 9-9.5, 26.5-27) out and the plinth's ends on the
toes raised to the footing top                                               = 15,409 lb
staged   0.43 x (317,855.5 + 15,409) / 89,375.4 = 0.43 x 333,264.5 / 89,375.4 = 1.603
dry      0.43 x (350,788 + 15,409) / 78,173                                  = 2.014
winter   house side 129,306 - 3,994 (A's beam, counted before) + 15,409    = 140,721 lb
         at mu_max 1.00: 140,721 / 2 lines = 70,361 lb per line
         6 #4:  0.9 x 1.20 x 60,000 = 64,800    -> 1.086
```

### C.4 The winter tension: the two fixes, both graded

| Fix | Arithmetic | d/c | Cost |
|---|---|---|---|
| **(a) one more bar per side run** (hand) | 7 #4 = 1.40 in², 0.9 × 1.40 × 60,000 = 75,600 | 0.931 | ≈ 13 lb |
| **(a) as modelled: one #4 at each edge** (engine) | 8 #4 = 1.60 in², 86,400 | **0.814** | 26.7 lb, **+$36-60** |
| (b) seat the wall on a bond break | the plinth must also come off the toes, or it carries the wall's weight onto its bed anyway. T = (125,312 + μ_bb × 11,415) / 2 ≤ 64,800 needs μ_bb ≤ 0.376 | ≈ 0.99 at μ_bb 0.3 | no published bond-break friction (UNVERIFIED); the sliding rows lose the 15,409 lb credit |

(a) is the fix, and it is drawn on `study-cladding-c`. The bars lap class B into FT-SG-W2/E2's edge
bundle at the joint.

### C.5 Can the porch-joist soil prop retire? The most important question

**No, not by the north wall alone.** It can retire, in any option, by giving W1/E1 W2's stem steel.

**What I relied on.** The engine has no two-way plate path, and `analytical/shells.py` refuses on
this house because no subgrade modulus is authored. So I used:

- a hand strip check; and
- a PyNite 3.1 plate model, script in the session scratchpad (`fem/box.py`), run on gross sections:
  - E = 57,000√5,000 = 4.03e6 psi (ACI 318-19 19.2.2.1), ν 0.2, 6" quad mesh;
  - W1 and E1 on their axes, the north wall on its centreline, W2/E2 and W-SG-S included;
  - W2/E2/S fixed at the base, W1/E1 **pinned** at the base (see below), all tops free;
  - soil at 1.6 × 60 psf/ft from grade (−2'-10", the engine's basis) on W1/E1, and from the wall
    top on W2/E2/S;
  - moments read as Wood-Armer (|M| + |Mxy|).

**Why W1/E1 are pinned at the base: a finding.** In the laid-out rebar, W1's 5 #6 verticals start
3" above its base (z −106.44"). No bar crosses the cold joint into FT-SG-W1, and W1 carries no
horizontals. As drawn, W1 has no base moment capacity. Yet `column_support/W-SG-W1`'s "stem as a
cantilever under E-W wind" row credits φMn 5,342 lb-ft/ft of #6 @ 38" at that joint. This holds on
main today, not only in C.

**Validation.** First I ran W1 alone as a fixed-base cantilever.

```
hand  Mu = 1.6 x 60 x 6.287^3 / 6 = 3,976 lb-ft/ft;  V = 1.6 x 60 x 6.287^2 / 2 x 10 ft = 18,970 lb
FEM   base My 4,040 (+1.6%, plate Poisson), base FX 18,946 lb
```

**Hand strip, spanning to the corner.** A horizontal strip of W1 2 ft above the base carries
1.6 × 60 × 4.29 = 412 psf. As a cantilever off the corner over 10 ft, that is
412 × 10² / 2 = **20,580 lb-ft/ft**, against 5,510 for #4 @ 16". The corner alone cannot carry
W1. W1 is 10'-0" long, and its south end runs into W2, a cantilever that is no support.

**Two-way plate, construction stage (soil only, W1/E1 backfilled before the porch).** Without the
north wall, W1 on a pinned base is a mechanism: the model is singular. With it, W1 is stable:

| | Wood-Armer, lb-ft/ft | W1 has | d/c |
|---|---|---|---|
| W1 vertical, earth face (at the corner) | 2,939 | #6 @ 38", φMn 5,342 | 0.55 |
| W1 vertical, **court face** (mid-length) | 2,109 | **no bar** | — |
| W1 horizontal, earth face at the corner | 2,892 | **no bar** | — |
| W1 horizontal, court face (mid-span) | 2,337 | **no bar** | — |
| north wall horizontal at the corner | 3,979 | #4 @ 16" EF, d 8.25", φMn 5,510 | 0.72 |
| W1 top deflection, worst | 0.027" | | |

```
#4 @ 16" each face: As 0.15 in2/ft, a = 0.15 x 60,000 / (0.85 x 5,000 x 12) = 0.176"
phi Mn = 0.9 x 0.15 x 60,000 x (8.25 - 0.088) / 12 = 5,510 lb-ft/ft
```

So the corner path works only if W1/E1 get a second curtain: #4 @ 16" horizontals each face, plus
court-face verticals, ≈ 440 LF, about 294 lb of #4 HDG, **ESTIMATE $400-660**. With that, the
worst row is 0.72 (the north wall's corner). It is an engineered plate that no table publishes, which the owner's rules
discourage.

**The simpler path, in any option.** Give W1/E1 W2's stem: #5 @ 10" with a hooked foot in the
footing mat, plus #4 @ 16" each face.

```
d = 12 - 3 - 0.3125 = 8.6875";  As 0.372;  a = 0.4376
phi Mn = 0.9 x 0.372 x 60,000 x (8.6875 - 0.219) / 12 = 14,177 lb-ft/ft
soil alone 3,976 -> 0.28;  with the balcony's E-W wind (the column_support row's 1,495) 5,471 -> 0.39
```

This costs about +385 lb of bar over today's #6 @ 38", **ESTIMATE $500-830**. It is the same
R404.4 cantilever `retaining_wall` already grades for W2/E2/S. It retires the AN-SG-BACKFILL
conditions on W1/E1: they may be backfilled before the porch framing, and need not be filled
together with each other. If they are filled early, the staged rule must take them in. W1 and E1
push opposite ways (½ × 60 × 7.29² × 10.5 = 16.7 kip each), so they go up together, inside H/2 of
each other. It also gives column_support's cantilever row a real base.

### C.6 BR1/BR3, 2.5 ft from the new corner

The engine's records do not change (column_support 0.578, base_rotation 0.309). The plate model,
with E-W wind only on all four columns (no soil, W1 pinned at the base):

| | without the north wall | with it |
|---|---|---|
| W1 top deflection at the north end | 0.043" | 0.002" |
| W1 Wood-Armer below the dowels (z < −48") | My 4,110, Mx 3,272 (into W2, no bars) | My 982, Mx 754 |
| north wall corner, horizontal | — | 3,680 |

The north wall takes BR1/BR3's wind as a shear wall, so the corner is a real gain for the rear
columns. In service with the prop retired and soil and wind together, the north wall's top corner
reads 7,522 lb-ft/ft. That is over #4 @ 16" (1.37); #5 @ 8" in the top 2 ft at each corner reads
0.45 (φMn 16,700).

### C.7 The top: is porch bracing needed? No

The wall retains nothing. Its loads are self weight, wind on a face under the porch, and in-plane
corner reactions. As a pure cantilever off its plinth, with no help from the corners:

```
phi Mn = 5,510 lb-ft/ft (vertical #4 @ 16", the same section) ;  h = 7.43 ft
w allowed = 2 x 5,510 / 7.43^2 = 200 psf at 1.0W
```

That is far above any wall pressure this house sees. The corners suffice, and the porch framing
stays clear of the wall top by 2 1/12".

### C.8 Openings

The model carries no trim bars, so these are added by hand: 2 #5 each side and over the head of
each opening, and a diagonal #4 at each corner. That is ≈ 70 LF #5 and 16 LF #4, plus the corner
L-bars, 2 corners × 2 faces × 7 rows × 5.5 ft = 154 LF #4: **ESTIMATE +$250-415**.

The door head is 9.1" of concrete over a 63.3" opening, carrying only itself:

```
w = 150 x 9.1 / 12 = 114 plf;  Mu = 1.2 x 114 x 5.44^2 / 8 = 507 lb-ft
```

That is trivial for 2 #5.

### C.9 The forming sequence, against S-100 / AN-SG-PLACEMENTS

The north wall is cast in **placement 2**, with the five walls, in the walls visit. In
`tasks.toml`, `task/framing/building/frame` depends on every concrete visit. So the back form
stands in open air above the house curb, is stripped from the house side, and is gone before
W-B-S2-FR/S3-FR are framed. **This works.** It forces one thing the brick did not.

The framed walls' membrane and 4" XPS then go on with a 6" slot between the sheathing plane and
the concrete. The brick, by contrast, was laid after them. Two ways through:

- frame the walkout as tilt-up panels with the sheathing, membrane and foam already on; or
- apply them from a 6" slot, which is impractical.

The cavity is closed for good afterwards, as it is today behind the brick. This cost is not priced
(ESTIMATE: a framer's half day). The AN-SG-PLACEMENTS and AN-SG-BLOCKOUTS texts still describe the
beam and must be rewritten if C is taken.

### C.10 Cost, trades, durability, look

- **Takeoff +$809 to +$2,034 as drawn, +$845 to +$2,094 with the fix.** The north wall is 4.56 cy
  at the court walls' rate (an estimate by reuse, ESTIMATE in `prices.toml`): +$2,307-4,150. Two
  formed openings add +$500-1,200, #4 bar +$305-508, and the wash on the court face +123 SF,
  +$411-784. Against that, the brick, the beam, the lintels, the joints and the flashings come out.
  With C.8 the total is **about +$1,100 to +$2,500**. If C is also used to retire the prop (C.5),
  add $400-660.
- **Trades:** the mason leaves the court. Concrete pours one more wall in a placement it already
  makes. The painter washes 123 SF more. No visit is added or removed.
- **Durability:** the best of the three. It is EXPOSED_MIX (F3/C2, w/cm 0.40), with galvanized bar
  at 3" cover, and nothing to maintain but the wash. There is no sealant joint, no tie and no
  flashing.
- **Look:** a fourth white wall. The court closes into a box, and the door and window read as deep
  punched openings (12" + 1.94" reveal). Daylight to the basement improves: a white wash in place
  of brown brick, with the same apertures. The accent is lost unless the owner tints the wash on
  this one wall.

## Open questions for the owner

1. **B or C, or keep A.** B saves money and an approval. C costs about $1-2.5k and gives the most
   durable, brightest court.
2. **W1/E1's base (a finding on main).** No bar crosses W1/E1's stem-to-footing joint, yet
   `column_support`'s cantilever row credits #6 @ 38" there. I recommend W2's hooked #5 @ 10" stem
   for W1/E1 in every option, about $500-830. That would also retire the porch-prop sequence.
3. **B's door base detail.** Should `rainscreen_base_flashing` learn to stop at a door, so B can
   read 0 FAIL? The real detail is standard.
4. **Salt and the steel panel's bottom edge (B).** Ask Metal Sales whether a 7 1/4" curb under a
   roof is inside its warranty in a court that pools chlorides. A taller curb, or the aluminium base
   Z run higher, are the fallbacks.
5. **The tilt-up walkout (C)**, if C is chosen.

## Sources

- IRC 2018 / 2024 Table R703.8.4(1) and R703.8.3.1, R703.8.5, R703.8.6, R404.1.7, R404.4, as already
  cited in `sunken_garden_veneer_beam.md` and `sunken_garden_court_free_body.md`. No new code text
  was read for this note.
- ACI 318-19 19.2.2.1 (Ec), 11.6.1 (T&S, the house's existing read), 21.2.2 (φ 0.90).
- Metal Sales BBD75-1212 published allowable loads, as graded by `structural.cladding_wind`.
- PyNite 3.1.0 (the engine's `dev`/`fea` oracle) for the plate model.
