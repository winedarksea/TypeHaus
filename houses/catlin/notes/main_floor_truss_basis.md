# Main-floor truss field FS-M-NE — basis and hand check

2026-11-01, decision #112. Replaces `SL-M-DECK` (BuildDeck; basis in `DESIGN-LOG.md`, "Main deck
goes wood"). Model: `params/main_deck.py` (`NE_FLOOR`), `plan/storeys/basement.py`
(`W-B-CS2`/`-CN2`/`-CN`), `plan/assemblies/interior.py` (`STAIRWELL_INT_2X6_BRG_FURRED`).
Independent of the engine: every number below is worked by hand from the model's geometry.

## 1. Geometry

- Field x 18'-36', y 13'-36'. 24 open-web floor trusses, 11 7/8" deep, 2x4 chords flat
  (3 1/2" wide), 12" o.c. on lines y = 13'..36'. Warren webs at 24" pitch, 13" clear, 12"
  offset (`FS-S-WEST`'s drawing).
- Truss ends x = 215 1/4" .. 430 1/4": **17'-11"**, the same blank as `FS-S-WEST`.
  - West: 3 1/2" onto the x=18' 2x6 double top plate (studs 213 1/4"..218 3/4"); the TJIs
    west of it take the other 2". 3 1/2" + 2" = 5 1/2", the plate exactly.
  - East: across the PT mudsill on `W-B-E1`/`E2` (pour 420"..432") to the 1 1/4" rim at
    430 1/4"..431 1/2".
- Clear span (plate face 218 3/4" to pour face 420"): **201 1/4" = 16'-9 1/4"**. Centre to
  centre of bearings, about 217" to 425" = **~208" = 17'-4"**.
- The y=13' seam with `FS-M-EAST` (TJI 230 @ 16") is a doubled member: the TJI field stops
  (2 5/16" + 3 1/2")/2 = 2 29/32" short, so the TJI flange and the truss chord sit face to
  face. Same depth, no movement joint, one ceiling plane.

## 2. Loads and the truss demand (for the fabricator)

Design basis (owner): **60 psf live, L/480**. Dead 15 psf (truss ~3, 23/32" ply 2.3, 5/8"
gypsum below 2.5, LVP ~1, allowance for the tile medallion study and services).

- w = (60 + 15) x 1.0 ft = **75 plf** per truss.
- R = 75 x 17.33 / 2 = **650 lb** per end (on the 18'-0" grid, 675 lb).
- M = 75 x 17.33^2 / 8 = **2,820 ft-lb**.
- Live deflection limit L/480 = 208 / 480 = **0.43"**.

Concentrated loads the truss drawing must carry at their stations:
- `FX-M-KRF1`/`KFZ1`: the fridge/freezer pair on the north wall, ~350 lb each loaded.
- The peninsula: cantilevered quartz plus stool users at the overhang.
- `W-M-PAN-S`: a 2x4 partition 1" off the y=33' truss line, parallel. It is light, and the
  12" field puts a truss under it, so there is no doubled truss.
- `W-M-PAN-E`: perpendicular, so it is shared by every truss it crosses.

## 3. Published span read: none exists

No maker publishes an 11 7/8" open-web row at 12" o.c. for 60 psf. The nearest is TRIFORCE
(Open Joist) U.S. Specifier Guide, 2023-05-11, p. 6, "Maximum Allowable Spans", glued and
nailed, L/480:
- At 100 psf live / 15 dead, 12" o.c., OJ418S gives **17'-2"** centre to centre.
- That is shorter than this field's ~17'-4". The row does not cover it, so it is not
  authored as a `PublishedSpan`.

So `structural.ijoist_span` reports UNKNOWN on `FS-M-NE` (its advisory table is 16" o.c.
only). The **fabricator's sealed truss design** closes it (plans/TODO.md). Order it to
section 2.

## 4. Seat, ties and wall-top restraint

- **Seat bearing**, x=18' plate (SPF, Fc⊥ 425 psi): 650 / (3.5 x 3.5) = 53 psi. d/c 0.12.
- **The x=18' plate ends are toe-nailed** (`UpliftTieRules`), as every interior floor seat
  is: a floor sees no net uplift, and the 24 H2.5A that stood here are gone.
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
  | W-B-E1 | FS-M-NE, truss | 6 | 12" | 400 lb | 538 | 0.74 |
  | W-B-E2 | FS-M-NE, truss | 18 | 12" | 400 lb | 538 | 0.74 |
  | W-B-W1 | FS-M-MECH, TJI | 10 | 16" | 533 lb | 563 | 0.95 |
  | W-B-W1 | FS-M-WEST, TJI | 3 | 16" | 533 lb | 563 | 0.95 |
  | W-B-W2 | FS-M-WEST, TJI | 14 | 16" | 533 lb | 563 | 0.95 |

  61 ends, one A35Z each (37 TJI + 24 truss). A second angle is not needed anywhere.

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
  | W-B-N3 | FS-M-MECH | 0..48" | x 8' | 48" | 1,600 lb | 0.57 |
  | W-B-N4 | FS-M-MECH | 0..70.3" | x 5' | 70.3" | 2,343 lb | 0.83 |

  W-B-N4's station is at x=5', east of `FO-M-ERV-OA` (x 6"..48 1/2"), whose trimmers the
  blocks are cut around. Each station has a MASA within 8": the nearest anchor on that sill
  moves to it, the count unchanged (`joints/sills._snap_to_blocking`).
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
| main floor, TJI west 9' (12 / 40 psf) + truss east 9' (15 / 60) | 243 | 900 |
| second floor 18' (12 / 40) | 216 | 720 |
| attic floor 18' (12 / 30, habitable) | 216 | 540 |
| roof 18' (15 D / 35 Pf) | 270 | 630 S |
| walls above, three storeys | 280 | — |
| **total** | **1,225** | **2,160 L + 630 S** |

- **D + L = 3,385 plf.** D + 0.75L + 0.75S = 3,318.
- **Stud buckling.** le = 91.5", le/d = 16.6. Fc* = 1,150 x 1.1 = 1,265 psi.
  FcE = 0.822 x 510,000 / 16.6^2 = 1,521. Cp = 0.750, so Fc' = 949 psi.
  - Per stud: 7,830 lb, so 5,870 plf at 16". **d/c 0.58.**
- **Plate bearing** (SPF Fc⊥ 425 psi, Cb = (1.5 + 0.375) / 1.5 = 1.25):
  - Per stud: 4,383 lb, so 3,287 plf at 16". **d/c 1.03** in SPF (0.98 with the code's
    40 psf on the east bay instead of the 60 psf design). `W-B-CS`/`-CS3` carry the same
    stack on the same stud.
  - **Cure, 2026-11-02: DF-L No. 2 top plates** (NDS Table 4A Fc⊥ 625 psi): 625 x 1.25 x
    (5.5 x 1.5) = 6,445 lb per stud, 3,385 x 1.333 / 6,445 = **d/c 0.70**. One field
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
