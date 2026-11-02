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
- **Seat ties** (`JoistSpec.seat_ties`, derived, one per truss end). There are 48:
  - 24 H2.5A on the dry x=18' plates;
  - 24 **H2.5AZ** on the PT mudsill, under IRC R317.3.1.

  Catalog: 615 lbf uplift in SPF, 110 lbf lateral. A floor sees no net uplift. The tie is
  the connector Minn. R. 1309.0404 asks for, from joist to sill.
- **Minn. R. 1309.0404 lateral reaction — OPEN.** Table R404.1(1), 8'-0" wall, 7'-6"
  backfill, GM (45 pcf/ft):
  - **400 plf** top-of-wall reaction;
  - 1/2" anchor bolts at 72";
  - blocking at 72".

  Per truss at 12" o.c. that is **400 lb along the truss**, against the H2.5A's 110 lbf
  lateral. **Not met by the H2.5A.** The candidate is an A35Z per seat: 695 lbf F1 / 845
  lbf F2 (DF/SP), less for SPF; confirm the direction and the SPF value.

  This is **house-wide**, not new. The TJI fields on the perimeter pours are toe-nailed
  today (`UpliftTieRules.tie_floor_joists_on_walls = False`), and at 16" o.c. they need
  533 lb per joist.
- **Parallel wall `W-B-N1`** (footnote f): full-depth blocking in the first three joist
  spaces at 72", sheathing nailed to it 8d at 3".
  - Authored as blocking in the four bays y 32'..36', at x 21'/27'/33'.
  - Each station collects 400 x 6 = **2,400 lb**. Its connection to the sill (footnote e,
    "sized to the reaction") is OPEN with the item above.
  - Footnote f also wants each block within 8" of an anchor bolt: set the MASA layout to
    the block stations.
  - With trusses, "full depth" blocking is the fabricator's truss blocking panel.

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
  - Per stud: 4,383 lb, so 3,287 plf at 16". **d/c 1.03.** It is 0.98 with the code's
    40 psf on the east bay instead of the 60 psf design.
  - **Marginal, and not new.** `W-B-CS`/`-CS3` already carry the same stack on the same
    stud. Cheap cures:
    - studs at 12" o.c. (4,383 plf, d/c 0.77), at the cost of the one-grid centreline;
    - DF-L plates (Fc⊥ 625, d/c 0.70). The engine restocks sole plates only, so a top-plate
      species would need a `FramingSpec` field.

    Owner / EOR call (plans/TODO.md).
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
