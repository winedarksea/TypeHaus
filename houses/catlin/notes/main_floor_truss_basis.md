# Main-floor truss field FS-M-NE — basis and hand check

2026-11-01, decision #112; **amended 2026-11-02: 16" o.c. on the published TRIFORCE row, the 316 and 332
lines doubled under the peninsula, two strongbacks.** Replaces `SL-M-DECK` (BuildDeck; basis in `DESIGN-LOG.md`, "Main
deck goes wood"). Model: `params/main_deck.py` (`NE_FLOOR`), `params/second_deck.py`
(`TRIFORCE_OJ418S_FLOOR_SPAN`), `plan/storeys/basement.py` (`W-B-CS2`/`-CN2`/`-CN`),
`plan/assemblies/interior.py` (`INT_2X6_BRG_HALF_DFL`). Independent of the engine: every
number below is worked by hand from the model's geometry. The owner's goal is a floor with no
bounce, not 60 psf: the 12" o.c. / 60 psf order had no published row.

## 1. Geometry

- Field x 18'-36', y 13'-36'. **18 open-web floor trusses**, 11 7/8" deep, 2x4 chords flat
  (3 1/2" wide, 1 1/2" thick), at 16" o.c. from the y=13' seam: y = 156, 172, ... 396 (16
  lines), then 408, 420, and the north gable edge at 432 laid as a 1 1/4" x 11 7/8" LSL rim
  flush with the stud face, inner face 430 1/4" (`edge_rims`, owner 2026-11-18)
  (`line_overrides` 412 -> 408, 428 -> 420, so the three bays at W-B-N1 stay 12" and a 0.5"
  slit at 428-432 is avoided). Webs: TRIFORCE publishes one 7 1/4" round
  opening (`TRIFORCE_OJ_WEB_OPENINGS`); the 24" Warren pitch, symmetric about mid-span, is assumed
  until the shop drawing (`notes/open_web_truss_geometry.md` §4).
- Count: (396 - 156)/16 + 1 = 16, plus 408 and 420 = **18** (432 is the rim), plus two sisters: 332 at 328.5" and 316 at 319.5" (section 3a).
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
- **A** at x = 309.5" and **B** at x = 334.75", each in its own bottom-chord web pocket: with a bottom
  node at mid-span (x = 322.75") the pockets are centred 12" either side (310.75", 334.75"); a pocket
  is ~8" wide at the 2x6's height, so two pieces cannot share one. A is nudged 1 1/4" west to clear
  `CD-B-PLAY-SPARE` at 311.2"; B stands 0.5" clear of `CD-B-DATA-MEDIA` at 333". They moved from
  317.75"/330.25" (the old 13" openings) and are now 12" from mid-span, not 6": an assumed pitch
  decides that, TRIFORCE's drawing may not.
- **Four cut bays**, where an x-running lane crosses at the strongback's height: 172-188
  (`PR-B-CW-TRUNK`, y 180 after its move from 186), 188-204 (`PR-B-HW-KITCH`, 196), 284-300
  (`CD-B-DATA-MEDIA`'s x-leg at y 296.5, z -9.21" to -8.29": a bore would sit ~1.2" off the
  strongback's bottom edge, short of R502.8.1's 2", so the bay is cut) and 408-420 (the kitchen
  drain, 414). Omit stations 180, 196, 292, 414.
- Pieces per strongback, line centre to line centre: 156-172 (16"), 204-284 (80"), 300-408 (108"),
  420-430 1/4" (10 1/4", butting the north rim's inner face): **8 pieces in all**, the longest
  108", far inside 20' stock.
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
  - Onto an LVL ply, x 1.00: **625.5 lb**. C-C-2026 p. 20 general note f lists LVL (DF/SP) at
    SG 0.50, DF-L's, inside §3.2.2's SG >= 0.50; the house's LVL hanger rows read it so too.
- **Every backfilled wall that carries a floor.** All are 8'-0" BASEMENT_8/12 pours (top
  -13 7/16", bottom -109 7/16"), grade -2'-10", so 75 7/16" = 6.3' of fill: the 8'/7'-6" row,
  GM soil, **400 plf**. Anchors are MASA at 4' (<= the row's 72").

  Perpendicular (one A35Z per end, `JoistSpec.sill_tie`):

  | wall | field | ends | spacing | demand / end | capacity | d/c |
  |---|---|---|---|---|---|---|
  | W-B-E1 | FS-M-EAST, TJI | 9 | 16" | 400 x 1.333 = 533 lb | 563 | 0.95 |
  | W-B-E1 | FS-M-NE, truss | 4 | 16" | 400 x 1.333 = 533 lb | 538 | 0.99 |
  | W-B-E1 | seam pack: FS-M-EAST TJI 153 3/32" + FS-M-NE truss 156" | 2 | 15.45" trib. | 515 lb | 2 x 538 | 0.48 |
  | W-B-E2 | FS-M-NE, truss | 13 | 16" | 533 lb | 538 | 0.99 |
  | W-B-E2 | FS-M-NE, 2-ply pack (316, 332) | 2 | 16" | 533 lb | 2 x 538 | 0.50 |
  | W-B-W1 | FS-M-MECH, TJI | 8 | 16" | 533 lb | 563 | 0.95 |
  | W-B-W1 | FS-M-WEST, TJI | 1 | 16" | 533 lb | 563 | 0.95 |
  | W-B-W1 | seam pack: FS-M-WEST 256", 259 1/16" + FS-M-MECH 261 3/8" | 3 | 21.375" trib. | 712.5 lb | 2 x 563 | 0.63 |
  | W-B-W1 | FS-M-WEST, 2-ply pack (240, the bath) | 1 | 16" | 533 lb | 2 x 563 | 0.47 |
  | W-B-W2 | FS-M-WEST, TJI (includes BATH2 drain bay's added line) | 14 | 16" max | 533 lb | 563 | 0.95 |
  | W-B-W1 | FS-M-MECH, `FO-M-ERV-OA` south trimmer pack, 2-ply LVL (398 7/8", 400 5/8") | 2 | 18.19" trib. | 606 lb | 2 x 626 | 0.48 |

  **A trimmer ending square on a tied sill takes ties like a joist** (2026-11-20, owner;
  `UpliftTieRules.sill_tied_floor_categories`). `FO-M-ERV-OA`'s south pack ends on W-B-W1's
  sill north of the 389 3/8" joist, so W1's top from there to the corner was held by toe-nails
  alone. Plies 1 3/4" LVL at 398 7/8" and 400 5/8" -> 398..401 1/2", one pack; ties on its
  outer faces, leaves y 395 3/4..398 and 401 1/2..403 3/4", clear of the joist (390 17/32) and
  of everything else on the sill. Nothing is tied north of it, so its tributary runs half way to
  W-B-N4's inner face, y 424", where the return wall holds the top:
  (400.625 + 424)/2 - (389.375 + 398.875)/2 = 412.3125 - 394.125 = 18.1875":
  400 x 18.1875/12 = **606.3 lb** on 2 x 625.5 (LVL, DF/SP column) = 1,251.0, **0.48**
  (0.56 if read as sawn SPF, x 0.86).
  The north pack (426 1/4"..429 3/4") lies along the N3/N4 sill, held by it like a rim, and
  its end is the corner: no angle (its north leaf would lie under the LSL edge rim).
  No other trimmer in the house ends on a tied sill; no other wall gains or loses a tie, and
  the return-wall bound moves no other pack (each has a tied end beyond it).

  57 joist ends + 2 trimmer ends, **59 A35Z** (57 until 2026-11-20): one an end (37 TJI + 18 truss), less the seam pack's middle end, plus one
  on each sister ply that lands on a sill (the 316 and 332 trusses, and `FS-M-WEST`'s bath ply
  at y 240"). (Until 2026-11-20 the 6" coincident-bearing grid merged the 153 3/32"/156" and
  256"/259 1/16" ends, so 53 ends, 56 ties, one drawn through framing.) Since 2026-11-18 the
  four gable-end edge lines on concrete (FS-M-EAST and FS-M-WEST at y=0, FS-M-MECH and FS-M-NE at
  y=36') are LSL rim boards seated along their parallel walls, whose stations tie them; their
  ends take no angle.
  A second angle is not needed for demand anywhere.
  Hand count of the truss ends: W-B-E1's axis runs y 0..216", so lines 156, 172, 188, 204 = 4;
  W-B-E2 (216"..432") takes 220, 236, ... 396 = (396 - 220)/16 + 1 = 12, plus 408, 420 = **14**
  (432 is the rim).
  **A sistered pack takes one A35Z on each OUTER face** (owner, 2026-11-02): Subp. 1 connects
  each joist, an angle cannot fit between plies, and the 16" tributary does not grow, so a 2-ply
  pack reads 533 / 1,076 = 0.50 (`joints/bearing.py`, the outer-face rule). (The engine's finding
  splits the 18 as 5 + 11 + 2 packs; the per-end d/c, 533/538 = 0.99, is the same either way.) The 533 lb is also
  the bound for the three 12" bays at the north wall, whose tributary is smaller.
  **Ends closer than a tie's slot are one pack, tied on its two outer faces** (owner,
  2026-11-20; `resolve/connector_geometry/sill_tie_pack.py`): the slot is the A35's 1 7/16"
  plus 1/8" each side, 1 11/16". The outermost tied end at each side owns that face's tie; the
  pack's demand is 400 plf from midpoint to midpoint with the ends either side.
  - W-B-W1, x=0 (TJI 2 5/16"): 256" -> 254 27/32..257 5/32; 259 1/16" -> 257 29/32..260 7/32;
    261 3/8" (FS-M-MECH) -> 260 7/32..262 17/32. Gaps 3/4" and 0, both < 1 11/16": one pack,
    254 27/32..262 17/32. Clear beyond: 11 3/8" to the 240" pack (sister to 243 15/32"),
    13 11/16" to 277 3/8". Ties on the rim face at y 254 27/32 - 1/8 - 23/32 = **254"** and
    262 17/32 + 1/8 + 23/32 = **263 3/8"**. Tributary (261.375 + 277.375)/2 - (240 + 256)/2 =
    269.375 - 248 = 21.375": 400 x 21.375/12 = **712.5 lb** on 2 x 563.0 = 1,125.9, **0.63**.
  - W-B-E1, x=36': TJI 153 3/32" (151 15/16..154 1/4) and the 3 1/2" truss at 156"
    (154 1/4..157 3/4) touch: a pack. The TJI's tie on the rim face, the truss's on its side
    face. Tributary (156 + 172)/2 - (144 + 153.094)/2 = 164 - 148.547 = 15.453": **515.1 lb**
    on 2 x min(563.0, 537.9) = 1,075.9, **0.48**.
  Every tie's flat leaf is tested against the framing on its sill: one with a member over it
  grades `code.MN_1309_0404_wall_top` UNKNOWN, naming the member, never PASS.

  Parallel (footnote f): blocking in the first three joist spaces (two blocked lines a
  station, so four), each station tied by **five A35Z** on the edge member's inboard face
  (`JoistSpec.station_ties`, derived): 5 x 538 = 2,690 lb (truss), 5 x 563 = 2,815 lb (TJI).
  Each is an L, 1 7/16" along the rim, one leaf up its face and one on the sill top, laid
  1/8" clear of the block end at 6" o.c., nearest first, within 18" of the station
  (`joints/wall_top.station_tie_points`). A
  station's demand is 400 plf over its tributary, midpoint to midpoint and out to the wall's
  ends; no gap and no end distance over 72".

  | wall | field | span along wall | stations | worst tributary | demand | d/c |
  |---|---|---|---|---|---|---|
  | W-B-N1 | FS-M-NE | 1.8"..216" | x 21'/27'/33' | 72" | 2,400 lb | 0.89 |
  | W-B-S1 | FS-M-WEST | 1.7"..118" | x 3'/7' | 58.3" | 1,943 lb | 0.69 |
  | W-B-S4 | FS-M-EAST | 0..116.2" | x 29'-2"/33'-2" | 60" | 2,000 lb | 0.71 |
  | W-B-N3 | FS-M-MECH | 0..48" | x 8' | 48" | 1,600 lb | 0.57 |
  | W-B-N4 | FS-M-MECH | 0..70.3" | x 5'-10" | 70.3" | 2,342 lb | 0.83 |

  W-B-N4's station is at its east end, x=5'-10": `FO-M-ERV-OA` (x 6"..48 1/2") and
  `DU-ERV-RISER-SUP` (6", west through the third space over x 17"..68") leave no other spot.
  W-B-N3 also sees it (along 50", past its 48" span), but it stands on N4's sill: N3's and
  N4's sills butt at x=6', so N3's thrust cannot reach ties on N4's. Each run grades only the
  stations its own span holds, so the station is tied once, from N4: 400 x 70.25/12 =
  2,342 lb on five A35Z, 2,342 / 2,815 = 0.83; N3's x=8' station takes all 48", 1,600 lb /
  2,815 = 0.57. (The authored x=72" tie stood on the N3/N4 node, N4's span end, half over
  each sill.)
  **`FO-M-ERV-OA`'s north pack stops past its header (2026-11-20, owner).** Its two LVL plies
  (y 426 1/4"..429 3/4") stand on the N3/N4 sill, 1/2" off the rim, so a tie's flat leaf
  (430 1/4" - 2 1/4" = 428") lay under them. A pack on a wall top spans nothing: it carries
  the header's HHUS410 straight into the sill, so it needs no bearing line beyond it
  (`resolve/floor_opening_packs.py`). It stops 3" past the header's far face: header x
  48 1/2"..52", HHUS410 W 3 5/8" + 2" flanges (C-C-2026 p. 155) centred at 50 1/4" ->
  flange edge 50.25 + 1.8125 + 2 = 54 1/16", pack end 52 + 3 = **55"**, 15/16" of LVL past
  the flange for its nails. The south pack spans the field and still runs to x=10'.
  - N4, block x 68 27/32..71 5/32 (TJI 2 5/16"): first tie 68 27/32 - 1/8 - 23/32 = 68";
    the span ends at x=72", so all five fall west. A tie may not lie on framing, so the
    pitch closes until the fifth clears the pack: 68 - 4p - 23/32 >= 55 -> p <= 3.07 -> **3"**
    (the 1/8" ladder), x 68, 65, 62, 59, 56; reach 70 - 56 = 14" <= 18". Leaf 55 9/32"..,
    9/32" clear of the pack end; the hanger flange is on the pack's opening face, y 426 1/4",
    1 3/4" off the leaf's inner edge, so the two never meet.
  - N3, block x 94 27/32..97 5/32: D-M-ENTRY's two 10" rim-stock backers (x 75 5/8"..85 5/8",
    104"..114", y 429"..430 1/4", `params/sill_seat_backers.py`) also stand on the leaf's
    strip. West ties 94 - kp, leaf >= 85 5/8 -> kp <= 7.66; east 98 + kp, leaf <= 104 ->
    kp <= 5.28. At 3 7/8" only four fit; at **3 3/4"**: x 86 1/2, 90 1/4, 94, 98, 101 3/4.
  - **Nothing else is owed on x 0..55".** Footnote f asks for stations at the table spacing;
    N4's one station is 70" from W-B-W1's corner (the wall end) and 2" from N4's east end,
    both <= 72", so the spacing is met without a station where the pack stands. The pack is
    parallel to the wall, so it is not footnote f blocking and is not credited; the wall top
    beneath it reaches the x=5'-10" station through the anchored sill, the reading every
    tributary in this table takes. The header carries floor load only.
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

2x6 SPF studs at 16" o.c., 8'-0" plate top at the -13 7/16" seat, on the existing strip
footings (`FT-B-CS2`/`-CN`/`-CN2`). They are re-centred on the stud axis by
`params/foundations._FRAMED_WALLS`, projecting 9 3/4" a side on the 25" x 10" strips (2026-11-05), within R403.1.1's
2" <= P <= T = 10".

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

Since 2026-11-09 `W-B-CN`'s stair face is 1/2" abrasion-resistant gypsum directly on the studs,
x=212 3/4" (studs 213 1/4"), the plane `W-M-C5` and `FO-S-STAIR` hold one storey up. It replaced
3 1/4" of 2x3 furring and plywood that held the retired pour's x=17'-6".
- `FO-M-STAIR`'s east edge and `ST-B2M`'s east lane are struck off that face: two 42 1/2" lanes
  and a 4 1/2" partition centred at x=14'-0".
- `RL-M-HANDRAIL-E` moved with it, centreline x=17'-6" at the same 3.58" projection; `BK-B-CN-HANDRAIL-*`
  back its two returns and its mid bracket, none of which falls on a stud.
- `P-M-STRLAND-SE`, the squash block that landed on that furring, is retired: the ST-M2S landing
  rim's ledger now runs through the `W-M-C5`/`-C5B` split.
