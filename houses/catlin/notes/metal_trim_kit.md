# Metal cladding and roof trim design basis

2026-10-27. This is the selected design and procurement basis; consult the model and
checks for implementation status. Confirm the printed part-number anomalies with the
supplier before ordering. XX denotes the colour code. Sections are 24 ga PVDF unless
otherwise stated; standard stock is 10 ft 2 in unless a different length is stated.

## Sources

- [PBR installation guide, April 2024](sources/metal-sales-pbr-install-2024.pdf),
  trim tables pp. 10–21, wall details pp. 44–73.
- [BBD75 installation guide, October 2025](sources/metal-sales-bbd75-install-2025.pdf),
  trim pp. 14–18, details pp. 22–45.
- [Residential design manual, May 2024](sources/metal-sales-residential-design-2024.pdf),
  Image II 24 ga PVDF parts pp. 6–12, details pp. 30–41. This supersedes the
  [2021 Image II PIM](sources/metal-sales-image-ii-pim-2021.pdf) for part numbers.
- [7/8 in corrugated manual](sources/metal-sales-corrugated-2011.pdf), profile
  dimensions; it does not publish part numbers.
- [General information manual](sources/metal-sales-general-information.pdf), PGI-10:
  custom flashings are available on request; brake limits are not published.

## Wall edges

| Condition | Selected termination | Basis |
|---|---|---|
| PBR base | 1.25 in Base 58138XX over the K2 Z-flashing, tape and inside closure 6460800 | PBR p. 69 |
| BBD75 base | Vertical Base Trim 55545XX and C-Closure 55548XX, over the K2 Z-flashing | BBD75 p. 22 |
| Corrugated base | 1.25 in Base over the aluminium stem Z (`TR-G-STEMZ-*`), profile-matched vented closure | Corrugated P7/8-3 |
| House outside corner | Wide Outside Corner 58132XX (10 ft 2 in) or 58136XX (20 ft 3 in), 5.5 in legs; PBR-to-BBD75, one leg on each face; C-Closure on BBD75 side | PBR and BBD75 corner details, BBD75 pp. 30–31 |
| Garage corner | Corrugated Outside Corner | Corrugated manual |
| BBD75 horizontal joint | Transition Trim 55536XX, pop rivets at 12 in o.c. | BBD75 p. 40 |
| PBR under eave | Inside closure flush with panel top under box gutter | PBR p. 46 |
| BBD75 under rake | Universal Closure 6411499 taped to slope-cut panel, covered by rake face | PBR p. 61 method |
| Corrugated under soffit | 1.5 in Sill to Soffit | Corrugated manual |
| Screen open ends | Corrugated Jamb candidate; 2.5 in back leg, 1 in throat and 1 in return; check against the actual two-face screen thickness | Corrugated manual p. P7/8-4 |

The north and south BBD75 band is at +17 ft 4 in, supported by a girt. Lower and
upper panel runs are approximately 18 ft 5 in and 14 ft, within the 20 ft maximum.
The band is also the head drip where it meets the two north window heads and the
D-S-DECK-E casing. PBR east and west panel runs are approximately 22 ft 2 in,
within the 45 ft maximum. Garage corners are approximately 8 ft 4 in high.

### Wall base stack

The Metal Sales closures and the insect screen close different voids, so neither replaces
the other. The closures fill the panel's rib voids. The screen closes the 2 in cavity
behind the panel (1/2 in vent gap plus 1-1/2 in girt band). On a house wall, bottom to top,
at the bearing seat (−1'-1 7/16"):

1. **K2 Z-flashing, the drip owner** ([basement detail](basement_to_framed_wall_detail.md)).
   Its upper leg runs up the foam face, its horizontal leg floors the full 2 in cavity, and
   its drip leg laps over the coated XPS band's head. The base trim can't take this job: its
   back leg is on the girt face, outboard of the cavity, so without the Z the cavity would
   drain onto the bearing seat.
2. **Perforated aluminium insect screen** (holes 1/8 in or less), sitting on the Z's
   horizontal leg. It runs foam face to girt face, 1-1/2 in tall.
3. **Base trim**, with its vertical leg 1/16 in outboard of the girt plane on the isolation
   strip, up to 2-5/8 in above the seat. Its foot and hem kick about 1.75 in outboard of
   the girt plane, so panel water drips
   clear of the Z. It never crosses the cavity mouth. Keep the steel trim off an aluminium
   Z with tape or EPDM, per the corrosion rule in `garage_wall_detail_side.md`.
4. **Profile closure** in the ribs, on the trim foot: PBR 6460800 on butyl tape, or the
   BBD75 C-Closure 55548XX.

The BBD75 guide (p. 22 base detail) shows no rat guard or perforated piece, so the screen is
the only cavity closure on the N/S walls. The garage has no separate cavity, because the
corrugation is the rainscreen. There the vented corrugated closure on the aluminium stem Z
closes both.

Hand count, W-M-W4: the screen runs 162 in (mitred at the corners) on the sloping Z pan,
about 1-1/2 in tall from the bearing seat. The base trim runs 164.8 in as two sticks (122 + 42.75 in) from −13.90" (hem) to
−10 13/16". The Z follows the 162 in mitred screen, continuous beneath openings; the steel
base follows the longer panel edge.

## Openings

The outie window frame face is on the panel back plane. Rib depths are 1.25 in PBR,
0.75 in BBD75, and 0.875 in corrugated. Buck, membrane and shim between frame and
rough opening occupy 0.645 in, or 0.6875 in at the Andersen sizes.

- Head: 1.5 in Sill/Head 58114XX at every window head, with 2.5 in back leg, 1.5 in throat and
  the matching closure. The membrane strip-in remains. PBR pp. 68–72 and BBD75 pp. 24–29 show
  trim-first installations; this head accommodates the window-first outie. BBD75 windows take the
  same head. The BBD75 Head Trim 58720XX (4 in return, BBD75 p. 28) is the open alternative, not billed.
- Jamb, PBR: stock Jamb 58208XX, a 1 in C-hem over the rib and a 1-3/8 in leg, with the 3-1/8 in
  flange lapping the frame face (PBR pp. 21, 68). The Head/Jamb Cover 58124XX is not billed.
- Jamb and sill, BBD75 and corrugated; sill, PBR: site-brake from 24 ga PVDF flat
  (`WINDOW_JAMB_CUSTOM`, `WINDOW_SILL_CUSTOM`). Each piece is graded against a 10'-6" hand brake:
  24 in girth, four bends or fewer. The reveal, the rib closure and the frame set the legs.
- Frame lap: none required by the fit check. The frame is set last, with tube sealant at the frame
  face (BBD75 pp. 24–26). The 3/4 in lap the check used to hold was Catlin's own rule.
- Doors: BBD75 Panel Starter 58728XX at the jambs. Corrugated Jamb (`CORRUGATED_JAMB`, no part
  number) at the garage door jambs and screen ends. Door heads are a site-brake drip cap (legacy
  drip geometry, about 6 to 6.5 in girth, three bends), over the 0.75 in casing projection plus 1/4 in.
- Five small rough openings receive four-side trim or their hood's trim ring, as
  appropriate to the product. Brick openings D-B-PATIO and WIN-B-SAUNA are excluded.

## Roof edges

| Condition | Selected termination | Basis |
|---|---|---|
| House eave / box gutter | Extended Eave 52124XX, pan hemmed round its lip; PBR 5 x 4 box gutter 58079XX (20 ft 3 in), installed level, back behind the eave face, 3-1/2 in roof flange under the eave's pitched leg; end caps 58081XX / 58082XX, straps 58092XX | Residential manual pp. 12, 30–41; PBR install pp. 12, 46, 63; Image II PIM-11 |
| House rake | Residential Rake 52126XX and Rake Cleat 52132XX, stock 2-5/8 in leg; bottom 1.0 in under the BBD75 wall head | Residential manual pp. 9, 33 |
| House closed ridge | 7 in Ridge/Hip Cover 52131XX, specify 6:12; Z-Closure 58603XX both sides; double-bead tape 6403899 | Residential manual pp. 30–41 |
| Garage and canopy eaves | Extended Eave 52124XX on Offset Cleat over metal fascia | Residential manual pp. 30–41 |
| Garage and canopy rakes | Residential Rake and Rake Cleat over fascia/barge; Flat Cleats 5806199 at 18 in | Residential manual pp. 30–41 |
| Garage vented ridge | 13 in Step Ridge/Hip Cover over the Cobra vented closure, material `standing-seam-image-ii-garage-vented`; part numbers and net free area unconfirmed | Image II PIM p. 20 |
| Canopy closed ridge | 7 in Ridge/Hip Cover 52131XX, specify 4:12; Z-Closure 58603XX | Residential manual pp. 30–41 |

The house rake is the stock piece. Its 2-5/8 in leg is fitted with the bottom 1.0 in under the BBD75
wall head, so 2.12 in of face runs down from the roof top. That clears the roofing and hides the
0.75 in Universal Closure with 1/4 in to spare. No manual publishes a lap over the wall head; the
1.0 in is a Catlin rule. The custom 4 in rake is deleted: the general information manual publishes no
brake limits for it, and the stock leg fits.

The garage's vented ridge is the Image II PIM p. 20 step cover (13 in, 6-1/2 in legs at pitch, 1 in
hems) over the Cobra vented closure, with double-bead tape and rivets at every rib, 3:12 minimum and a
2 in maximum deck slot. The PIM prints no part number and no net free area for either piece. The 2024
manual shows its 7 in cover only in a non-vented detail.

Gutter and eave relationship: PIM-11 shows only a gutter by others behind the eave face, and PBR p. 46 shows the box gutter's roof flange under eave flashing on a PBR roof. Neither shows the combination; the house documents it (`roof_wall_eave_detail.md`). The flange lies on the field membrane under the eave leg, with the membrane strip-in over both; no field bend, stock part identity kept. The eave's Offset Cleat is not part of the house eave.

The house box gutter is the PBR 5 x 4 catalog box. Its capacity passes the SMACNA 10-yr 5-min design
intensity (7.54 in/hr) in `notes/box_gutter_sizing.md`; the custom 6 x 5 is retired.

Specify pitch for eave, peak and ridge. Extended Eave and Residential Rake have
lips intended to satisfy the drip condition; verify the installed detail against
[the FORTIFIED roof note](fortified_roof_cert.md). Garage and canopy fascia, soffit
and K-gutters remain. The house, garage and canopy ridges are closed, vented and
closed respectively.

## Laps and procurement arithmetic

Use 1/4 in-14 × 7/8 in stitch screws or 1/8 in pop rivets for trim. PBR corner
laps are at least 3 in, with rivets at 2 in o.c.; other PBR trim laps are 2 in
with tube sealant. Notch BBD75 trim hems 2 in at laps and put no fastener through
a BBD75 trim lap. Notch Image II eaves 3 in at laps. Rakes over 3:12 use Universal
Closure 6411499. The printed anomalies (58937XX, 59904XX, 58974XX, duplicate 58206XX) DROP: none is on an ordered piece (Stage 1 outcomes, below).

For a uniform stock length, pieces = ceil((run − lap)/(stock − lap)); a run no
longer than stock takes one piece. Compare available stock combinations on waste,
including laps, rather than assuming uniform lengths.

- One 22 ft 4.4 in house corner: one 20 ft 3 in plus one 10 ft 2 in, with 3 in
  lap, covers 30 ft 2 in; 7 ft 9.6 in of purchased length remains after coverage
  and lap. One piece cannot cover the run.
- South band: the nominal 36 ft wall line needs four 10 ft 2 in lengths with three
  2 in laps, covering 40 ft 2 in. Exact cut lengths depend on resolved face endpoints
  and any head integration; verify the field run before ordering.
- WIN-S-STUDY1 has a nominal 30 × 48 in unit. Each of its head, sill and two jamb
  runs fits in one 10 ft 2 in length; four separately cut pieces are required in the
  model. Procurement may combine short cuts from stock if the shop cutting plan and
  allowances permit it; do not assume four full sticks per window in a pooled order.

## Billing boundaries

| Scope | Explicit purchase | Remove overlap when implemented |
|---|---|---|
| Wall panel | Profiled sheet only | Embedded trim load in panel $/SF |
| Base, corners, bands, openings | Named trim or custom coil by cut/stock, with laps | Legacy wall-corner, edge-cladding and closure allowances |
| Closure and seal | Profile closure, tape and tube sealant by installed length | Lump profile-closure allowances |
| Fastening | Stitch screws and rivets by trim role and spacing | Any included trim-fastener allowance |
| Roof perimeter and ridge | Image II pieces, cleats, closures, vent and fasteners | Replaced generic drip, ridge-cap and corner-trim allowances |
| Gutters | PBR 5 x 4 box, end caps and straps, by part, after the SMACNA capacity check | The custom 6 x 5 box and the fabricated box band in `[drainage]` |

A change of wall profile also moves the cladding plane and affects the breezeway gap,
garage lines, sleeves and devices. Corrugated substitution needs its own exposed-fastener
rules; preserve the standing-seam skin family used for roof classification.

## Implementation status (2026-10-27)

What the model derives and bills, with the counts the tests pin
(`test_cladding_trim_walls.py`, `test_cladding_trim_takeoff.py`):

| Condition | Resolved as | Count |
|---|---|---|
| Wall base | kit base (`PBR_BASE` / `BBD_BASE` / `CORRUGATED_BASE`) under every wall stack whose panel bottom is free, one run per wall segment and per span between floor-level openings | 11 / 10 / 12 sticks |
| House K2 base | 0.040 in aluminium Z, 120 in stock with 2 in laps, continuous under each base screen; EPDM at the steel trim | 14 runs / 21 sticks; 148 LF isolation |
| Wall tops | PBR inside closure 6460800; BBD75 Universal Closure 6411499; corrugated Sill to Soffit at garage eaves; corrugated outside closure at garage panel tops | 74.25 / 83.01 / 48.29 / 99.04 LF |
| Outside corners | Wide corner (PBR↔BBD75), corrugated corner | 8 / 4 |
| BBD75 band | Transition Trim at +17'-4", one run per N/S wall segment | 10 |
| Window head, jamb, sill | 1.5 in Sill/Head 58114XX at every head; PBR jamb 58208XX (unpriced); BBD75 and corrugated jambs and every sill: site-brake (`WINDOW_JAMB_CUSTOM` 146.9 LF, `WINDOW_SILL_CUSTOM` 87.3 LF) | 43 heads / 86 jambs / 43 sills |
| Door jambs | Panel Starter 58728XX (BBD75); Corrugated Jamb at the garage door jambs (stock, no part number) | 6 + 4 |
| Door heads | site-brake drip cap, legacy head section swept at stock; none on catalog unit D-S-DECK-E, whose head is the band | 5 |
| Small rough openings | 4-side window kit on the niche and both ERV hoods; the two 2.5 in hydrant bores are closed by the fixture's flange and sealant | 3 |
| Screen ends | Corrugated Jamb on both open ends of W-BW-SCREEN and its skirt | 4 |
| Roof eaves | Extended Eave 52124XX, pan hemmed to its lip (no cleat) | 16 sticks |
| Roof rakes | House: stock Residential Rake 52126XX with its bottom 1.0 in under the wall head; Rake Cleat 52132XX. Garage and canopy: Flat Cleat 5806199 at 18 in | House 4 runs / 16 ea 52126XX; 5806199 40 ea |
| Closed ridges | 7 in cover 52131XX, Z-Closure 58603XX each side, double-bead tape 6403899 | 5 sticks |
| Garage vented ridge | 13 in step cover and Cobra closure (`IMAGE_II_VENTED_STEP_RIDGE`, `cobra-vented-closure`), unpriced until the part numbers are in | 25.4 ft |
| Box gutter | PBR 5 x 4 `58079XX`, 20 ft 3 in sticks; end caps `58081XX` / `58082XX` and straps `58092XX` unpriced | 4 sticks |
| Closed ridges | 7 in cover 52131XX, Z-Closure 58603XX each side, double-bead tape 6403899 | 5 sticks |

Hand counts: a 164.8 in PBR base run (W-M-W4) takes two 10'-2" sticks with a 2 in lap, because
ceil((164.8 − 2)/(122 − 2)) = 2. The same wall's screen is 162 in on the Z's leg, inboard of
the trim (see "Wall base stack"); there are 14 base screens house-wide. The garage ridge is
25.4 ft of cap, unchanged.

Decisions this pass:

- **Base is panel-bottom, not floor-level.** A door sill above the panel bottom leaves the base
  unbroken beneath it; only an opening reaching the base's 2-5/8 in upstand cuts it
  (D-G-OVERHEAD, whose two 48.9 in piers match the old stem Z).
- **`TR-G-STEMZ-*` stays aluminium** (owner, 2026-10-27). The stem-top Z is aluminium by the
  corrosion rule in `garage_wall_detail_side.md`; the base trim above it is the panel's steel coil.
- **Hydrant bores stay untrimmed** (owner, 2026-10-27). An opening under 6 in is a penetration through
  the fixture's own flange (`SMALL_PENETRATION_M`); the check records it N/A.
- **The house rake is the stock 52126XX**, with its bottom 1.0 in under the wall head. The custom
  4 in rake is deleted (see Roof edges).
- **The box gutter is the PBR 5 x 4 catalog piece.** SMACNA capacity passes; the custom 6 x 5 is retired.
- **D-G-SERVICE sill threshold is 1 in** (owner, 2026-10-27): a coordination envelope (frame depth
  6-9/16 in, 1 in composite sill); MMI publishes no sill section. 1 in rather than 1-1/2 in because the
  outswing allowance in R311.3.2 is 1-1/2 in above the landing.

Still open, all printed as UNKNOWN by the checks: the garage's vented ridge (part numbers and the
Cobra net free area), `code.R806_2_attic_ventilation` for the garage (its soffit and Cobra net free
area), and the corrugated Sill to Soffit break. Prices in `prices.toml [cladding_trim]` are estimates.


The K2 section has a 2 in upstand, a pan spanning the resolved cavity at a 1/4 in per foot
outward fall, a 3/4 in drip and a 1/4 in hem. The pan underside starts at the bearing seat;
the screen sits on its upper face. The steel base is held off the aluminium by 1/16 in EPDM.
At W-M-W4 the cavity runs from 4 to 6 in outboard of sheathing; the coated foundation face
is 4.185 in outboard, leaving about 1.815 in from the drip to that face. The 162 in Z run
uses 120 and 44 in cuts with a 2 in lap. The screen order now includes its corner mitres.

The corrugated garage panel tops use a solid outside closure, separate from the vented base
closure. The eave soffit's underside is at +84.17 in, below the panel extension's +91.5 in
top; Sill to Soffit sits at that soffit, and the outside closure seals the higher panel edge.
Top closure lengths follow the resolved panel edge and include roof-generated extensions;
overlapping stacked extensions are counted once.

**Soffit attachment remains UNKNOWN:** the corrugated wall skin is modeled continuously
through the soffit height. The Sill to Soffit crosses that skin in the model, so the panel
break and installation order still need a coordinated detail before the junction is graded
as fitting. Its bill is an estimate of the selected trim, not evidence of a resolved joint.

## Stage 1 outcomes (2026-10-27)

**Part-number anomalies: all four DROP.** None is on a part Catlin orders.

- **58937XX** (PBR 24 ga inside corner): the Catlin BOM has no inside corner. The 24 ga pattern
  predicts 58917XX for the printed 10'-2" row.
- **59904XX / 58904XX** (PBR step rake): the house roofs take Image II rakes. The pattern gives 58904XX.
- **58974XX / 58794XX** (PBR 13 in step ridge): 58974XX matches its own 10'-2" row. The 20'-3" row
  should read 58975XX. No PBR step ridge is on the building.
- **58206XX** (printed for both the PBR C-Closure and the Double Angle): neither is on the building.
  The PBR closure is 6460800.

**Openings survey.** A published section is used where it clears the reveal and the frame: the PBR
jamb 58208XX, and the 1.5 in Sill/Head 58114XX at heads. Every other jamb, sill and door head is a
site brake from 24 ga flat, graded against the 10'-6" hand brake (24 in girth, four bends or fewer;
71 sections pass the fit check). Stock BBD75 jambs and sills (58718XX) and the BBD75 Head Trim
(58720XX) were surveyed and are not billed. The Corrugated Jamb is billed only at the garage door
jambs and screen ends.

## Supplier confirmation

Two items, plus one optional:

1. The part number for the 13 in Step Ridge/Hip Cover (garage vented ridge). Image II PIM p. 20 and
   the 2024 manual print none.
2. The Cobra vented closure's net free area. R806.2 needs it before the garage attic can pass. The
   garage soffit's net free area is a vent product's figure and is not on this list.
3. Optional: stock part numbers for the Corrugated Jamb and the 1.5 in Sill/Head, if stock is preferred
   over the site bends.
