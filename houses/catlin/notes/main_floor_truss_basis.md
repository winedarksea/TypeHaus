# Main-floor truss field FS-M-NE — basis and hand check

2026-11-01, decision #112; **amended 2026-11-02: 16" o.c. on the published TRIFORCE row, the 316 and 332
lines doubled under the peninsula, two strongbacks.** Replaces `SL-M-DECK` (BuildDeck; basis in `DESIGN-LOG.md`, "Main
deck goes wood"). Model: `params/main_deck.py` (`NE_FLOOR`), `params/second_deck.py`
(`TRIFORCE_OJ418S_FLOOR_SPAN`), `plan/storeys/basement.py` (`W-B-CS2`/`-CN2`/`-CN`),
`plan/assemblies/interior.py` (`STAIRWELL_INT_2X6_BRG_FURRED`). Independent of the engine: every
number below is worked by hand from the model's geometry. The owner's goal is a floor with no
bounce, not 60 psf: the 12" o.c. / 60 psf order had no published row.

## 1. Geometry

- Field x 18'-36', y 13'-36'. **19 open-web floor trusses**, 11 7/8" deep, 2x4 chords flat
  (3 1/2" wide, 1 1/2" thick), at 16" o.c. from the y=13' seam: y = 156, 172, ... 396 (16
  lines), then 408, 420, 432 (`line_overrides` 412 -> 408, 428 -> 420, so the three bays at
  W-B-N1 stay 12" and a 0.5" slit at 428-432 is avoided). Warren webs at 24" pitch, 13" clear,
  12" offset (`FS-S-WEST`'s drawing).
- Count: (396 - 156)/16 + 1 = 16, plus 3 = **19**, plus two sisters: 332 at 328.5" and 316 at 319.5" (section 3a).
- Truss ends x = 215 1/4" .. 430 1/4": **17'-11"**, the same blank as `FS-S-WEST`.
  - West: 3 1/2" onto the x=18' 2x6 double top plate (studs 213 1/4"..218 3/4"); the TJIs
    west of it take the other 2". 3 1/2" + 2" = 5 1/2", the plate exactly.
  - East: across the PT mudsill on `W-B-E1`/`E2` (pour 420"..432") to the 1 1/4" rim at
    430 1/4"..431 1/2".
- Clear span (plate face 218 3/4" to pour face 420"): **201 1/4" = 16'-9 1/4"**. Centre to
  centre of bearings, about 217" to 425" = **208" = 17'-4"** (17.33').
- The y=13' seam with `FS-M-EAST` (TJI 230 @ 16") is a doubled member: the TJI field stops
  (2 5/16" + 3 1/2")/2 = 2 29/32" short, so the TJI flange and the truss chord sit face to
  face. Same depth, no movement joint, one ceiling plane.

## 2. Loads, the truss demand and a deflection estimate

Basis: **40 psf live, 15 psf dead, 16" o.c.** Dead 15 psf (truss ~3, 23/32" ply 2.3, 5/8"
gypsum below 2.5, LVP ~1, allowance for services and the cabinets' kick zone); the published
row's own dead column is 25 psf, so 15 sits inside it.

- w = (40 + 15) x 16/12 = **73.3 plf** per truss.
- R = 73.33 x 17.333 / 2 = **635 lb** per end.
- M = 73.33 x 17.333^2 / 8 = 73.33 x 300.4 / 8 = **2,754 ft-lb**.
- Published row's own demand, for scale: (40 + 25) x 16/12 = 86.7 plf, 18'-0": R = 780 lb,
  M = 86.7 x 18^2 / 8 = 3,510 ft-lb. The field is under it on both.
- Live limit L/480 = 208/480 = 0.433". The order asks **L/720** live: 208/720 = **0.289"**.

**Deflection, scaled from the maker's rows (no truss properties are published).** Flexure
governs, so Delta ~ w L^4 / EI, and for one truss Delta/L ~ w L^3.
- From the 12" o.c. row (p. 6, glued and nailed, L/480, 100 psf live, OJ418S, 17'-2" c-c = 206"):
  Delta_ref = 206/480 = 0.429" at w = 100 plf. Here w = 40 x 16/12 = 53.3 plf, L = 208":
  Delta = 0.429 x (53.3/100) x (208/206)^4 = 0.429 x 0.533 x 1.039 = **0.238"** = **L/874**
  (~L/875) under 40 psf live. That clears L/480 by 1.8x and the L/720 order by 1.2x.
  Under the full 55 psf: 874 x 40/55 = L/636.
- Cross-check from the p. 5 row (16" o.c., 18'-0", 40 live / 25 dead): the two rows agree if p. 5's
  L/480 is read on the **total** 65 psf: Delta/L ~ 86.7 x 18^3 against 100 x 17.17^3 is 0.999.
  Scaled to 55 psf at 17.33': 480 / ((55/65) x (17.333/18)^3) = 480 / 0.756 = L/635, matching
  the 636 above. Read **live-only** it would be L/480 x (18/17.333)^3 = **L/538**, the floor of
  the estimate. Either way the field clears L/480; L/720 is a request to the fabricator, not a
  published fact.

Concentrated loads the truss drawing must carry at their stations:
- `APPL-M-FRIDGE`/`-FREEZER`: stand against the x=18' bearing wall (x 18'-3" to 20'-6", y
  328.6-394.4), ~700 lb over four lines (332-380), ~175 lb a truss within 2'-3" of the seat.
- The peninsula (section 3a), which governs the point-load list.
- `W-M-PAN-S`: a 2x4 partition 1" off the y=33' (396) truss line, parallel; light, and a truss
  is under it. `W-M-PAN-E` is perpendicular, so every truss it crosses shares it.

## 3. Published span read: the row covers the field

TRIFORCE (Open Joist) U.S. Specifier Guide, 2023-05-11, p. 5, "Maximum Allowable Spans",
glued and nailed 23/32" panels: OJ418S, 11 7/8", 16" o.c., **40 psf live / 25 psf dead, L/480:
18'-0"** (18' stock). The field's trusses are 17'-11" tip to tip and 17'-4" c-c, inside the
row, so `FS-M-NE` is a prescriptive read like the TJI fields (`TRIFORCE_OJ418S_FLOOR_SPAN`,
`structural.ijoist_span`). The row's conditions: uniform load only, 1 1/2" minimum bearing
(3 1/2" here), the 25 psf dead column. Point loads are outside it, answered by section 3a and
the fabricator's drawing. The p. 6 row (100/15 at 12" o.c.) is not used for the read.

### 3a. Peninsula load to the doubled line (by hand)

Boxes: B36 + B24 + B24 = 84", x 303.4"-387.4", y 319.4"-343.4" (24" deep, centre 331.4"). The
stone is one notched slab, 40 5/8" deep with a 15" back cantilever (the `y < 319.4"` side)
carried by five hidden flat bars (12" over the box, 12" out). Dead load, hand-weighed:
- Stone 3 cm (1.181", 150 pcf): 84 x 40.625 = 3,412 in^2 = 23.7 ft^2 x 14.8 psf = **350 lb**.
- Five 1/2 x 2 1/2 x 24 bars: 30 in^3 x 0.284 = 8.5 lb each = **43 lb**.
- 3/4" ply sub-top: 84 x 24 = 14.0 ft^2 x 2.2 psf = **31 lb**.
- Three bases, fronts, panels and contents allowance: 14.0 ft^2 x (12 + 20) psf = **448 lb**.
- D = 350 + 43 + 31 + 448 = **872 lb**.

Stool users: three, each putting ~100 lb on the stone edge (the other ~150 lb of a 250 lb
person goes down the stool legs onto the 40 psf floor) = **300 lb** at the cantilever tip,
y = 319.4 - 15 = 304.4". (Assumption, not a code number; a full 250 lb each would be 750 lb.)

Load path: the boxes stand on SEKTION legs 2" in from the back and front edges, y = 321.4" and
341.4", 20" apart. Moments about the front legs: R_back x 20 = 872 x 10 + 300 x 37 = 19,820,
so R_back = **991 lb**, R_front = 872 + 300 - 991 = **181 lb**. Trusses near the box: 316,
328.5/332 (the pair, effective 330.25") and 348. Linear split to the nearest lines:
- Back legs (321.4") between 316 and 330.25 (14.25"): 316 takes 8.85/14.25 = 0.621 -> **616 lb**;
  the pair takes 0.379 -> 376 lb.
- Front legs (341.4") between 330.25 and 348 (17.75"): the pair takes 0.372 x 181 = 67 lb;
  348 takes 0.628 -> **114 lb**.
- Totals: 316: 616; pair: 443 (221 a ply); 348: 114. Sum 1,173 = 872 + 300. OK.

Each is a patch over 84", centroid x = 345", from the west bearing (217") a = 128", from the
east (425") b = 80" on L = 208". Patch moment = P a b / L; the uniform 73.3 plf (6.11 lb/in) at
x = 345" gives w a b / 2 = 6.11 x 128 x 80 / 2 = 31,290 in-lb = **2,607 ft-lb**.
- **No sharing (worst single ply, line 316):** 616 x 128 x 80 / 208 = 30,330 in-lb = 2,527
  ft-lb; total **5,134 ft-lb**, 1.9x the uniform midspan M of 2,754 and 1.5x the row's 3,510.
- **Shared across the four plies** (subfloor, glued 3/4" sub-top and the box frames tie the
  lines; equal stiffness, 1,173/4 = 293 lb a ply): 293 x 128 x 80 / 208 = 14,420 in-lb =
  1,202 ft-lb; total **3,809 ft-lb**, 1.4x uniform, 1.09x the row's 3,510.
- East-end reaction of the 316 ply, unshared: 635 + 616 x 128/208 = 1,014 lb (PT SYP, Fc-perp
  565 psi, over 3 1/2" x 3 1/2": 83 psi, d/c 0.15).

Reading: the doubled 332 line is under the box centre and carries the dead mass; the cantilever
couple loads 316, 3.4" from the back edge. The truth is between the two cases.

**316 is doubled too** (owner, 2026-11-02; sister on the box side at 319.5"):
- **No sharing:** 616 / 2 = 308 lb a ply: 308 x 128 x 80 / 208 = 15,163 in-lb = 1,264 ft-lb;
  total **3,871 ft-lb**, 1.10x the row's 3,510.
- **Shared across five plies** (316 pair, 332 pair, 348; 1,173 / 5 = 235 lb): 11,550 in-lb =
  963 ft-lb; total **3,570 ft-lb**, 1.02x the row.

Closer to the row, but it does not clear it, and the stool load is an assumption. The engine cannot
grade this (the row is uniform only); the fabricator's drawing carries the point loads and
confirms both doubled pairs (`plans/TODO.md`).

## 3b. Strongbacks (TRIFORCE pp. 20-22)

TRIFORCE pp. 20-22, "Strongbacks", Detail 5 Option #1: a 2x6 on edge on the bottom chords,
"attached to diagonal web and chord"; the table calls for one at this depth and spacing and
recommends them for "superior floor systems"; a strongback "can be cut between two joists for
ducts or pipes". The owner's bounce goal, so two:
- 2x6 on edge (5 1/2" tall, 1 1/2" thick) on the chord tops: z = -11 7/8" + 1 1/2" = -10 3/8"
  to -4 7/8". Top chord underside at -1 1/2": 3 3/8" clear above.
- **A** at x = 317.75" (317"-318.5") in the 26' web opening, hard against the 27' web, beside
  `CD-B-PLAY-SPARE` at 311.2". **B** at x = 330.25" (329.5"-331") in the 28' opening, 1.5" clear of
  `CD-B-DATA-MEDIA` at 333". Webs sit on odd feet, 13" openings on even feet, so each piece fits an
  opening and never crosses a web. Both are within about 6" of mid-span (the 208" span's middle is
  x = 321").
- **Four cut bays**, where an x-running lane crosses at the strongback's height: 172-188
  (`PR-B-CW-TRUNK`, y 180 after its move from 186), 188-204 (`PR-B-HW-KITCH`, 196), 284-300
  (`CD-B-DATA-MEDIA`'s x-leg at y 296.5, z -9.21" to -8.29": a bore would sit ~1.2" off the
  strongback's bottom edge, short of R502.8.1's 2", so the bay is cut) and 408-420 (the kitchen
  drain, 414). Omit stations 180, 196, 292, 414.
- Pieces per strongback, line centre to line centre: 156-172 (16"), 204-284 (80"), 300-408 (108"),
  420-432 (12"): **8 pieces in all**, the longest 108", far inside 20' stock.
- Hand-derived from the omit list; the resolver and the crossings checks are the confirmation.

## 4. Seat, ties and wall-top restraint

- **Seat bearing**, x=18' plate (SPF, Fc⊥ 425 psi): 635 / (3.5 x 3.5) = 52 psi. d/c 0.12.
- **The x=18' plate ends are toe-nailed** (`UpliftTieRules`), as every interior floor seat
  is: a floor sees no net uplift, and the H2.5A that stood here are gone.
- **Minn. R. 1309.0404 wall-top restraint — CLOSED 2026-11-02** (`code.MN_1309_0404_wall_top`,
  which this section oracles). Sources, read 2026-11-02:
  - Rule text (revisor.mn.gov/rules/1309.0404). Subp. 1: "Floor joists and blocking shall be
    connected to the sill plate at the top of wall with an approved connector with listed
    capacity meeting the top of wall reaction in Table R404.1(1)." Footnote e: the reaction
    is the "minimum load to be used for the sizing of accepted anchors or fasteners".
    Footnote f: full-depth blocking in the first three joist spaces, connected per note e,
    "within 8 inches of an anchor bolt location".
  - Table R404.1(1), all nine rows (wall / backfill / soil pcf -> reaction plf, bolts, blocking):
    8'/7'-6": 30 -> 260, 72, 72; 45 -> 400, 72, 72; 60 -> 530, 48, 48.
    9'/8'-6": 30 -> 340, 72, 72; 45 -> 510, 48, 48; 60 -> 680, 32, 32.
    10'/9'-6": 30 -> 430, 64, 64; 45 -> 640, 40, 40; 60 -> 860, 24, 24.
  - ICC-ES ESR-3096 (reissued Jan 2026) Table 5: A35 with 6-SD9112 + 6-SD9112, **F1 695 /
    F2 845 lbf, identical in the C_D 1.0, 1.15 and 1.25/1.6 columns**, "not permitted to be
    adjusted for other load durations" (fn. 2); directions do not combine (fn. 3). §3.2.2:
    wood SG >= 0.50 only.
  - Simpson C-C-2026 p. 310 (LTP4/LTP5/A34/A35 table): SPF/HF over DF/SP reads 0.86 on every
    comparable row (A34 SD 550/640 and 425/495; A35 joists-to-plate 510/590). Fn. 6: A34/A35
    "onto 1 1/4" LSL material will achieve 0.90 of the listed F1 and F2 loads". No row puts
    an angle on an I-joist flange; at a TJI end it lands on the LSL rim/blocking, which is
    Weyerhaeuser's joist-end detail.
- **Capacity of one A35Z** (6+6 SD9112), sustained soil load, lesser of F1/F2 because the
  installer, not the model, picks the face:
  - C_D for lateral earth pressure is 0.9 (permanent, NDS Table 2.3.2), below the lowest
    published column (1.0): 695 x 0.9 = 625.5 lb.
  - Onto a truss chord or sawn block of unstated species, x 0.86: **537.9 lb**.
  - Onto the LSL rim at a TJI end, x 0.90: **563.0 lb**.
- **Every backfilled wall that carries a floor.** All are 8'-0" BASEMENT_8/12 pours (top
  -13 7/16", bottom -109 7/16"), grade -2'-10", so 75 7/16" = 6.3' of fill: the 8'/7'-6" row,
  GM soil, **400 plf**. Anchors are MASA at 4' (<= the row's 72").

  Perpendicular (one A35Z per end, `JoistSpec.sill_tie`):

  | wall | field | ends | spacing | demand / end | capacity | d/c |
  |---|---|---|---|---|---|---|
  | W-B-E1 | FS-M-EAST, TJI | 10 | 16" | 400 x 1.333 = 533 lb | 563 | 0.95 |
  | W-B-E1 | FS-M-NE, truss | 4 | 16" | 400 x 1.333 = 533 lb | 538 | 0.99 |
  | W-B-E2 | FS-M-NE, truss | 13 | 16" | 533 lb | 538 | 0.99 |
  | W-B-E2 | FS-M-NE, 2-ply pack (316, 332) | 2 | 16" | 533 lb | 2 x 538 | 0.50 |
  | W-B-W1 | FS-M-MECH, TJI | 10 | 16" | 533 lb | 563 | 0.95 |
  | W-B-W1 | FS-M-WEST, TJI | 2 | 16" | 533 lb | 563 | 0.95 |
  | W-B-W1 | FS-M-WEST, 2-ply pack (240, the bath) | 1 | 16" | 533 lb | 2 x 563 | 0.47 |
  | W-B-W2 | FS-M-WEST, TJI | 14 | 16" | 533 lb | 563 | 0.95 |

  56 ends, **59 A35Z**: one an end (37 TJI + 19 truss), plus one on each sister ply that lands on
  a sill (the 316 and 332 trusses, and `FS-M-WEST`'s bath ply at y 240").
  A second angle is not needed for demand anywhere.
  Hand count of the truss ends: W-B-E1's axis runs y 0..216", so lines 156, 172, 188, 204 = 4;
  W-B-E2 (216"..432") takes 220, 236, ... 396 = (396 - 220)/16 + 1 = 12, plus 408, 420, 432 = **15**.
  **A sistered pack takes one A35Z on each OUTER face** (owner, 2026-11-02): Subp. 1 connects
  each joist, an angle cannot fit between plies, and the 16" tributary does not grow, so a 2-ply
  pack reads 533 / 1,076 = 0.50 (`joints/bearing.py`, the outer-face rule). (The engine's finding
  splits the 19 as 5 + 12 + 2 packs; the per-end d/c, 533/538 = 0.99, is the same either way.) The 533 lb is also
  the bound for the three 12" bays at the north wall, whose tributary is smaller.

  Parallel (footnote f): blocking in the first three joist spaces (two blocked lines a
  station, so four), each station tied by **five A35Z** on the edge member's inboard face
  (`plan/wall_top_ties.py`): 5 x 538 = 2,690 lb (truss), 5 x 563 = 2,815 lb (TJI). A
  station's demand is 400 plf over its tributary, midpoint to midpoint and out to the wall's
  ends; no gap and no end distance over 72".

  | wall | field | span along wall | stations | worst tributary | demand | d/c |
  |---|---|---|---|---|---|---|
  | W-B-N1 | FS-M-NE | 1.8"..216" | x 21'/27'/33' | 72" | 2,400 lb | 0.89 |
  | W-B-S1 | FS-M-WEST | 1.7"..118" | x 3'/7' | 58.3" | 1,943 lb | 0.69 |
  | W-B-S4 | FS-M-EAST | 0..116.2" | x 29'-2"/33'-2" | 60" | 2,000 lb | 0.71 |
  | W-B-N3 | FS-M-MECH | 0..48" | x 8' / 5'-10" | 11" (1 A35Z) | 367 lb | 0.65 |
  | W-B-N4 | FS-M-MECH | 0..70.3" | x 5'-10" | 70.3" | 2,343 lb | 0.83 |

  W-B-N4's station is at its east end, x=5'-10": `FO-M-ERV-OA` (x 6"..48 1/2") and
  `DU-ERV-RISER-SUP` (6", west through the third space over x 17"..68") leave no other spot.
  It is also W-B-N3's west-end station (N3 runs east to west, so along 50"): N3's x=8' station
  takes 0..37", 1,233 lb / 2,815 = 0.44, and the end station 37..48", 400 x 11/12 = 367 lb
  on N3's one tie within 18" (x=7', 563 lb), 0.65. A station counts only its own wall's ties.
  Each station has a MASA within 8": where the pitch left none, one is added (eight in all,
  69 -> 77 billed; `joints/sills._snap_to_blocking`). Moving one instead stranded the plate ends.
- **W-B-N2 — UNKNOWN, a design.** `FO-M-STAIR` runs y 26'..35'-4 7/8" against the 36' wall, so
  its first three joist spaces are the stair well for x 10'-3"..17'-6" and no footnote f
  block can stand there. The wall top (400 x 8' = 3,200 lb) goes into the well's edge
  framing, which spans flat between the headers: an approved-equivalent design for the EOR
  (plans/TODO.md).
- With trusses, "full depth" blocking is the fabricator's truss blocking panel.
- **Kitchen drain bores the 27' and 21' blocks** (`PR-B-KITCH-DRAIN`, 2" PVC, OD 2.375", in
  the 34'-35' bay). Assumes the panel is solid lumber, 1.5" x 11 7/8" in section, 8 1/2"
  long along the strut; **if the fabricator's panel is webbed, the pipe passes its opening
  and none of this applies.** Hole 2 1/2", centres 104.3" (x=27') and 101.7" (x=21'); truss
  bottom 97.56", mid-depth 103.5".
  - Gross 1.5 x 11.875 = 17.8 in^2. Net at x=21': 1.5 x (11.875 - 2.5) = **14.06 in^2**
    (ligaments 2.88" below, 6.50" above).
  - Strut 2,400 lb, taken whole (blocks in series along the bay line): 2,400 / 14.06 =
    **171 psi** against SPF Fc 1,150 psi (Cp = 1.0: le/d = 8.5/1.5 = 5.7). d/c **0.15**.
  - Eccentricity of the net centroid from the gross: 0.48". M = 2,400 x 0.48 = 1,150 in-lb;
    I = 1.5 x (11.875^3 - 2.5^3) / 12 = 207 in^4; fb = 1,150 x 6.4 / 207 = **36 psi**
    against Fb ~875 psi. Combined 0.15 + 0.04 = **0.19**. Passes with margin; the load goes
    in at the subfloor nailing, not through the hole. The slope there is 0.43"/ft (>= 1/4").
  - Not engine-graded: `mep.run_through_floor_member` reports it UNKNOWN (the truss chart).

## 5. The framed centreline (W-B-CS2 / -CN2 / -CN)

2x6 SPF studs at 16" o.c., 8'-0" plate top at the -13 7/16" seat, on the existing 20" strip
footings (`FT-B-CS2`/`-CN`/`-CN2`). They are re-centred on the stud axis by
`params/foundations._FRAMED_WALLS`, projecting 7 1/4" a side, within R403.1.1's
2" <= P <= T = 8".

Tributary line load, 9' each side per floor, ASD D + L. The roof comes through `RB-HOUSE`:
half of each 18' rafter.

| source | D (plf) | L or S (plf) |
|---|---|---|
| main floor, TJI west 9' (12 / 40 psf) + truss east 9' (15 / 40) | 243 | 720 |
| second floor 18' (12 / 40) | 216 | 720 |
| attic floor 18' (12 / 30, habitable) | 216 | 540 |
| roof 18' (15 D / 35 Pf) | 270 | 630 S |
| walls above, three storeys | 280 | — |
| **total** | **1,225** | **1,980 L + 630 S** |

- **D + L = 1,225 + 1,980 = 3,205 plf.** D + 0.75L + 0.75S = 1,225 + 0.75 x 2,610 = 3,183.
- **Stud buckling.** le = 91.5", le/d = 16.6. Fc* = 1,150 x 1.1 = 1,265 psi.
  FcE = 0.822 x 510,000 / 16.6^2 = 1,521. Cp = 0.750, so Fc' = 949 psi.
  - Per stud: 7,830 lb, so 5,870 plf at 16". 3,205 / 5,870 = **d/c 0.55.**
- **Plate bearing** (SPF Fc⊥ 425 psi, Cb = (1.5 + 0.375) / 1.5 = 1.25):
  - Per stud: 4,383 lb, so 3,287 plf at 16". 3,205 / 3,287 = **d/c 0.98** in SPF, with
    no margin (it was 1.03 at the old 60 psf east bay). `W-B-CS`/`-CS3` carry the same
    stack on the same stud.
  - **Cure, 2026-11-02: DF-L No. 2 top plates** (NDS Table 4A Fc⊥ 625 psi): 625 x 1.25 x
    (5.5 x 1.5) = 6,445 lb per stud, 3,205 x 1.333 / 6,445 = 4,273 / 6,445 = **d/c 0.66**. One field
    (`FramingSpec.top_plate_material_ref`) on all five segments, so the stud grid stays
    `layout_origin="line"` and stacks basement to attic; 12" o.c. (d/c 0.77) would have broken
    it. The sole plate is the PT SYP sill (Fc⊥ 565), already denser.
- **Footing.** The 12" pour weighed 150 x 1.0 x 8 = 1,200 plf; the framed wall ~80. The
  strip carries ~1,100 plf less than it did. `structural.bearing_wall_footing` passes all
  three.

## 6. Stair face

`W-B-CN`'s stair face is furred back to the pour's old x=17'-6": 2x3 on edge at 16" o.c. plus
3/4" painted plywood = 3 1/4" off the stud face (209.98" measured). That keeps several things
where they were:
- `FO-M-STAIR`'s east edge stays carried;
- `ST-B2M`'s east lane stays closed;
- `RL-M-HANDRAIL-E` stays at a 3.58" projection (R311.7.1, 4 1/2" allowed).

`P-M-STRLAND-SE`'s squash block lands over this furring, so a doubled 2x3 stands under it to
the slab.
