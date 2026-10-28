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

- Head: 1.5 in Sill/Head 58114XX, with 2.5 in back leg and 1.5 in throat,
  plus the matching closure. The membrane strip-in remains. PBR pp. 68–72 and
  BBD75 pp. 24–29 show trim-first installations; this head accommodates the
  window-first outie. BBD75 Head Trim 58720XX's 4 in return conflicts with the frame.
- Jamb: custom J with back leg on girt or buck, return equal to rib depth and 1 in
  leg onto frame face, sealed at the K7 joint. The frame lap covers the buck strip.
- Sill: custom cap with upstand on buck behind the pan turn-down, height 1/8 in
  below frame sill rise, top sloped 1/4 in per ft, matching closure, and 1/2 in
  drip and hem beyond the rib tip. These custom sections have girth under 12 in
  and at most three bends; the supplier must confirm its brake capability.
- Doors: custom head drip crosses the 0.75 in casing projection plus 1/4 in;
  panel J against casing at jambs (BBD75 58728XX or corrugated Jamb). The band
  serves as the D-S-DECK-E head. Door sills retain the threshold/pan path.
- Five small rough openings receive four-side trim or their hood's trim ring, as
  appropriate to the product. Brick openings D-B-PATIO and WIN-B-SAUNA are excluded.

## Roof edges

| Condition | Selected termination | Basis |
|---|---|---|
| House eave / box gutter | Extended Eave 52124XX on Offset Cleat 5806499; evaluate Box Gutter 58077XX / 58079XX (20 ft 3 in), end caps 58081XX / 58082XX and straps 58092XX against drainage capacity before replacing the custom gutter | Residential manual pp. 30–41; PBR box gutter detail |
| House rake | Residential Rake 52126XX and Rake Cleat 52132XX; panel edge turned up 1 in; verify coverage of the deck edge and 1.5 in drop over wall head | Residential manual pp. 30–41 |
| House closed ridge | 7 in Ridge/Hip Cover 52131XX, specify 6:12; Z-Closure 58603XX both sides; double-bead tape 6403899 | Residential manual pp. 30–41 |
| Garage and canopy eaves | Extended Eave 52124XX on Offset Cleat over metal fascia | Residential manual pp. 30–41 |
| Garage and canopy rakes | Residential Rake and Rake Cleat over fascia/barge; Flat Cleats 5806199 at 18 in | Residential manual pp. 30–41 |
| Garage vented ridge | Image II PIM's 13 in step ridge/hip cover with Cobra vented closure; confirm current availability and part numbers with Metal Sales | Image II PIM p. 20 |
| Canopy closed ridge | 7 in Ridge/Hip Cover 52131XX, specify 4:12; Z-Closure 58603XX | Residential manual pp. 30–41 |

The plan assumed a 4 in rake face, but the 2024 manual p. 9 depicts a 2 5/8 in main leg and a 4 3/4 in stretch-out for 52126XX. The existing house detail requires a 4 in face: verify the installed coverage before substituting the stock rake. The plan's garage ridge selection 52134XX is a one-sided residential peak flashing, which the manual p. 41 shows at a vertical end wall. For the gable, the older Image II PIM p. 20 shows a 13 in step ridge/hip cover and Cobra vented closure, double-bead tape and 1/8 × 3/16 in rivets at every rib, with a maximum 2 in deck slot; its alternate uses perforated vent drip and outside closures. It warns that snow loads can require additional screws. The 2024 residential manual shows its 7 in ridge/hip cover only in a non-vented detail; availability and current part numbers for the older vented assembly need confirmation. The existing vented ridge remains modeled until the vented assembly's fit is established.

A custom-brake rake with a 4 in face is geometrically possible in principle: extend the 2 5/8 in main leg of the published rake by 1 3/8 in, preserving its 1 in upper return, lower kick and hem, for an approximate 6 1/8 in stretch-out. The general information manual states that custom flashings are available but publishes no brake limits. The proposed extended leg still needs to be located against the actual rake deck edge, wall head, cleat and panel turn-up before it can replace the existing modeled detail.

The catalog box gutter is 5 in wide by 4 in deep (PBR guide p. 12), while the existing house gutter is 6 in wide by 5 in deep. The drainage checks resolve leaders and discharge paths but do not compute gutter flow capacity, so they cannot establish whether the smaller gutter handles the design storm. The existing gutter remains pending a hydraulic capacity calculation and outlet review.

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
Closure 6411499. Confirm supplier readings of 58937XX, 59904XX versus 58904XX,
58974XX versus 58794XX, and the duplicated 58206XX for C-Closure and Double Angle.

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
| Gutters | Catalog gutter and components only after capacity check | Authored custom gutter only if catalog replacement is accepted |

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
| Window head, jamb, sill | stock 1.5 in Sill/Head; custom jamb and sill | 43 / 86 / 43 |
| Door jambs | Panel Starter (BBD75), Corrugated Jamb (garage) at the casing edge | 6 + 4 |
| Door heads | custom drip cap, the legacy head section swept at stock; none on catalog unit D-S-DECK-E, whose head is the band | 5 |
| Small rough openings | 4-side window kit on the niche and both ERV hoods; the two 2.5 in hydrant bores are closed by the fixture's flange and sealant | 3 |
| Screen ends | Corrugated Jamb on both open ends of W-BW-SCREEN and its skirt | 4 |
| Roof eaves | Extended Eave 52124XX on Offset Cleat 5806499 | 16 sticks |
| Roof rakes | house: custom 4 in face; garage and canopy: Residential Rake 52126XX; Rake Cleat 52132XX; Flat Cleat 5806199 at 18 in | 4 runs / 16 sticks |
| Closed ridges | 7 in cover 52131XX, Z-Closure 58603XX each side, double-bead tape 6403899 | 5 sticks |

Hand counts: a 164.8 in PBR base run (W-M-W4) takes two 10'-2" sticks with a 2 in lap, because
ceil((164.8 − 2)/(122 − 2)) = 2. The same wall's screen is 162 in on the Z's leg, inboard of
the trim (see "Wall base stack"); there are 14 base screens house-wide. The garage ridge is
25.4 ft of cap, unchanged.

Decisions this pass:

- **Base is panel-bottom, not floor-level.** A door sill above the panel bottom leaves the base
  unbroken beneath it; only an opening reaching the base's 2-5/8 in upstand cuts it
  (D-G-OVERHEAD, whose two 48.9 in piers match the old stem Z).
- **`TR-G-STEMZ-*` stays.** The stem-top Z is aluminium by the corrosion rule in
  `garage_wall_detail_side.md`; the base trim above it is the panel's steel coil.
- **Hydrant bores take no trim.** An opening under 6 in is a penetration through the fixture's
  own flange (`SMALL_PENETRATION_M`); the check records it N/A.
- **The house rake keeps its modeled drip edge under the 4 in rake.** The billed piece is the
  rake; the drip edge beneath it is geometry only until `fortified_roof.py` is re-pointed at
  the catalog rake's lip.
- **Box gutters stay custom.** The catalog gutter (5 × 4 in) is smaller than the authored
  6 × 5; the hydraulic capacity and outlet review in the paragraph above is still open.
- **D-G-SERVICE has a `sill_design`**: a coordination envelope (frame depth 6-9/16 in, 1 in
  composite sill); MMI publishes no sill section. 1 in rather than 1-1/2 in because the outswing
  allowance in R311.3.2 is 1-1/2 in above the landing.

Still open (the checks print these as UNKNOWN): the vented Image II ridge and its part numbers,
the 4 in custom rake and the custom jamb/sill/head brake limits, and the five printed
part-number anomalies, all for Metal Sales. Prices in `prices.toml [cladding_trim]` are estimates.

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
