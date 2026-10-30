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
| PBR base | 1.25 in Base 58138XX raised 1 in over the K2 Z-flashing; panel end on a perforated strip (6460800 is the fallback, taped both faces) | PBR p. 69, adapted (wall base stack) |
| BBD75 base | Vertical Base Trim 55545XX raised 1 in over the K2 Z-flashing; panel end on a perforated strip, no C-Closure | BBD75 p. 22, open and drained |
| Corrugated base | 1.25 in Base over the aluminium stem Z (`TR-G-STEMZ-*`), profile-matched vented closure | Corrugated P7/8-3 |
| House outside corner | Wide Outside Corner 58132XX (10 ft 2 in) or 58136XX (20 ft 3 in), 5.5 in legs; PBR-to-BBD75, one leg on each face; C-Closure on BBD75 side | PBR and BBD75 corner details, BBD75 pp. 30–31 |
| Garage corner | Corrugated Outside Corner | Corrugated manual |
| BBD75 horizontal joint | Transition Trim 55536XX, pop rivets at 12 in o.c.; the cavity's vented outlet (below) | BBD75 p. 40 |
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

Re-struck 2026-10-29 (owner-approved). The base of the cavity was neither drained nor vented:
the trim's back leg stood 1/16 in off the screen with its foot flush on the Z pan, so it
dammed the pan edge; the starter girt and its blocks started on the seat, KDAT on the
aluminium Z (AWC DCA6), the blocks through the Z and the girt inside the screen, and it could
not be built (girts go on before tilt-up, the Z after the foam). Metal Sales draws PBR's base
as a closed termination for open framing (pp. 69-70) and BBD75's as open and drained with
**no closure** (pp. 22, 28); this note used to read the latter as "C-Closure".

On a house wall, bottom to top, S = the bearing seat at −1'-1 7/16":

1. **K2 Z-flashing (`RAINSCREEN_BASE_Z`), the drip owner** ([basement
   detail](basement_to_framed_wall_detail.md)). 0.040 in aluminium: a 2 in upstand on the foam
   face, stripped in to the foam 2 in each way; a pan across the full 2 in cavity falling 1/4
   in/ft; a 3/4 in drip over the coated XPS band's head, hemmed. Unchanged.
2. **Base screen**, a perforated aluminium **inverted U, 2 x 2 in**, on the pan, captive between
   the Z upstand and the trim's leg. 0.032 in sheet, 3 mm holes on a 5 mm stagger (under 1/8
   in, 32.6% open). Custom: the 6013981 L gives only 44 cm2/m, which fails.
3. **Steel base trim** (58138XX PBR, 55545XX BBD75), **foot raised to S+1 in**. Air comes up
   between the Z's drip and the trim kick, passes under the foot (0.98 in clear over the pan
   edge) and through the U's outer leg; water runs out over the drip. The trim leg laps the U
   1 in on a **1/16 in EPDM strip** (S+1 in to the U top at S+2.04 in), so no steel touches
   aluminium. There is no EPDM on the drip leg.
4. **Starter girt and blocks raised to S+2-1/4 in ... S+5-3/4 in**, clear of the Z upstand and
   the U top (S+2.04 in). No KDAT touches aluminium.
5. **Panel end on a flat perforated aluminium strip** on the trim foot, cut 1/32 in short of
   each leg so its edges touch no steel (at a head or the band, no KDAT girt either). The panel
   end bears on the strip directly, painted aluminium against Galvalume, with **no EPDM pads**
   (owner, 2026-10-29; see "Strip bearing" below). It replaces 6460800 on PBR (polyethylene, chewable,
   and it holds water against the panel end); BBD75 publishes none. The fallback is 6460800
   taped on both faces.

Net free area, by hand: the U's outer leg is open from the pan (S−0.002 in at the girt plane)
to the EPDM at S+1 in, 1.002 in. 1.002 in x 2.54 cm x 0.326 x 100 cm/m = **83 cm2/m**, against
DIN 18516-1's 50 cm2/m. The engine reads 83 (`integrity.rainscreen_cavity`, off the
Material's `perforation_hole_in` and `open_area_fraction`); the plan's "about 84" counted a
full 1 in at 33%. At 20% open the base would read 51 cm2/m and the band outlet 47, which
fails: the band needs 21.1%, so order the 33% sheet and ask the supplier for at least 22%.

Hand count, W-M-W4: the U runs 162 in (mitred at the corners), cut 120 + 44 in with a 2 in
lap; the Z the same. The base trim runs 164.75 in as two sticks (122 + 42.75 in), foot at
−12 7/16" (S+1), hem kick to −12.90". The strip runs 164.75 in (120 + 44.75), seated on the foot. The
starter girt is −11 3/16" to −7 11/16".

The garage has no separate cavity, because the corrugation is the rainscreen. There the
vented corrugated closure on the aluminium stem Z closes both.

### Band outlet (N/S walls, +17 ft 4 in)

The cavity breathes in at the base and out at the BBD75 band, the existing Transition Trim
55536XX at +17'-4" (208 in) on the N/S walls. E/W walls stay bottom-vented only; eaves, rakes,
sills and heads are not outlets (owner, 2026-10-28).

- The lower panel stops at least 1 in below the trim seat (implicit, hidden behind the trim's
  2-1/2 in face leg).
- A 1 in perforated strip spans from the girt plane to the trim's face leg under the seat,
  over the lower panel's top end (`BAND_OUTLET_STRIP`), cut 1/32 in short of the steel
  each side: 0.934 in x 2.54 x 0.326 x 100 = **77.4 cm2/m** (the edge gaps, open but under
  1/8 in, are not counted).
- The 1/2 in gap behind the band girt stays open, so the upper cavity is fed from below.
- The upper panel's batten ends open into the upper cavity at the seat, so they get the same
  strip, on the seat (`PANEL_END_STRIP`).
- Left out where an opening is framed through the trim's height (`WIN-S-HALL-N`,
  `WIN-S-STAIR-N`, `AO-S-ERV-EA`): their heads govern there. Seven walls, 61.4 LF of outlet.

### Strip bearing (owner, 2026-10-29)

Panel ends bear on the perforated aluminium strip with no EPDM pads, and the strip lies
directly on the trim leg. Basis: Metal Sales puts painted aluminium against Galvalume at its
PBR vented ridge, so the pairing is the manufacturer's own. EPDM stays where the steel base
trim's leg laps the U (item 3). The model draws and bills no pads
(`resolve/rainscreen_strips.py`).

### Closure inventory

| Condition | State |
|---|---|
| Base | Screened inlet (above) |
| Window and door heads | Capped and drained; panel end on a strip (`opening_flashing_spec.md` §3 step 4a) |
| BBD75 band | Vented outlet (above) |
| Jamb buck returns | Hold point |
| Sills | Closed (6460800 / 55548XX) |
| Eaves and rakes | Closed by the deck oversail |
| Outside corners | Closed |
| ERV, hydrant and VR-M-STACK sleeves | Sealed |
| `D-S-DECK-E` head | Its catalog unit's; hold point |

### Open with suppliers (not blocking)

| Who | Question |
|---|---|
| Metal Sales | Hole size on 6013981 |
| Metal Sales | Panel end on a perforated strip, instead of the 1/4 in gap and closure |
| Metal Sales | Raising the base trim 1 in off the Z |
| Metal Sales | K6 braked from their coil |
| Membrane maker | The substrate letter covers the Z and K6 strip-ins |
| Amrize (foam) | OnePass HFO sprayed over cured FastFlash (the window raccoon), plus a jobsite adhesion mock-up (`opening_flashing_spec.md` §5) |
| Screen supplier | Holes ≤ 1/8 in, **at least 22% open** (33% specified; the band outlet needs 21.1%), 0.032–0.040 aluminium |

## Openings

The outie window frame face is on the panel back plane. Rib depths are 1.25 in PBR,
0.75 in BBD75, and 0.875 in corrugated. Buck, membrane and shim between frame and
rough opening occupy 0.645 in, or 0.6875 in at the Andersen sizes.

- Head: 1.5 in Sill/Head 58114XX at every window head, with 2.5 in back leg and 1.5 in throat.
  On a rainscreen wall the panel end sits in it on a perforated strip, not a closure, under the
  K6 head cap's face leg (`opening_flashing_spec.md` §3 step 4a). Rough-opening heads keep the
  closure. PBR pp. 68–72 and BBD75 pp. 24–29 show
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
| Window head, jamb, sill | 1.5 in Sill/Head 58114XX at every head; PBR jamb 58208XX (unpriced); BBD75 and corrugated jambs and every sill: site-brake (`WINDOW_JAMB_CUSTOM` 146.9 LF, `WINDOW_SILL_CUSTOM` 87.3 LF) | 43 heads / 86 jambs / 43 sills; heads and PBR jambs pooled FFD from 10'-2" stock (heads 42 cuts, 91.5 LF, 10 sticks) |
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
