# EQ-S-HP1-AH connection and service-space review — 2026-11-17

The outdoor drawing datums are in
[`flexx_ultra_outdoor_geometry.md`](flexx_ultra_outdoor_geometry.md).

The horizontal-left cabinet has an open supply aperture and return end, schematic
connection markers and a 24-inch front service zone. Its two fabricated plenums now have
sheet-metal shells cut at their declared air ports, replacing the generic ERV massing
(including its fictitious raised top). Viewer, GLB and IFC use the same cut sheets.
These are design openings, not approved shop drawings or drilling templates.

## Evidence and certainty

- [FXU24 submittal, GREE_FXU24_230V_R32_SUB_01272026](https://www.greecomfort.com/assets/our-products/flexx-ultra-r32/documents/flexx-ultra-r32-submittal-24mbh-a.pdf),
  pp.2,4,6: cabinet 18 1/8 × 43 1/2 × 21 1/4 inches as shipped; supply A11 5/8 × B16 3/4.
  Horizontal-left is the factory configuration; front clearance is 24 inches.
- [Indoor installation manual](https://www.greecomfort.com/assets/our-products/flexx-ultra-r32/documents/flexx-ultra-r32-installation-owner-s-manual-indoor-a.pdf),
  printed pp.8,25–27: cabinet table, condensate trap diagram, ductwork and heat kit.
  **Correction:** the supposed cabinet-dimension conflict was a merged-table misreading.
  Visual inspection of PDF page 14 confirms FXU12/18/24 share the smaller cabinet;
  48 3/16 inches belongs to FXU36. The submittal and manual agree.

The horizontal product frame is 43 1/2 along x, 21 1/4 along y and 18 1/8 high.
Local -x discharges, +x returns and -y services. Catlin uses rotation 0: west, east,
south respectively. Neither air-opening setback nor return clear size is dimensioned;
front-face connection stations remain approximate. Verify the ordered unit revision.

| Interface | Size basis | Station basis |
| --- | --- | --- |
| Supply | 11 5/8 across × 16 3/4 high, published | Rear-biased centre inferred from perspective |
| Return | 20 × 16 provisional, not a published aperture | East face, provisional centre |
| Liquid / vapor | 3/8 / 3/4 tube, published | Schematic front-face markers |
| Primary / secondary condensate | 3/4 nominal PVC | Schematic; neither thread nor fitting OD verified |
| Power / controls | 208–230 V / 24 VAC | Entry allowances, not located knockouts |

## Air-side assembly now represented

`EQ-A-HP1-SUP-BOX`: 22 1/2 × 14 × 27 inches, on the attic deck.
Its east opening meets `DU-A-HP1-SUP-NECK` (11 5/8 × 16 3/4);
its bottom opening is 12 × 12, at x234/y344, matching `DU-S-HP-SUP-DROP`.
The old bottom port incorrectly sat at the box centre, 2 1/4 inches east of the drop.

`EQ-S-ERV-MIX`: **27 1/2 × 40 × 27 inches**, west/east faces x298/325.5,
south/north faces y328/368, base z240.75 (all project inches). It grew one inch south
from the previous 39-inch depth in the 2026-11-15 review, keeping the north face and
branch stations fixed. The later rail/pitch change moved only the west cabinet neck.
The provisional cabinet neck originally left only 3/16 inch at that south corner.
After the rail/pitch change the flat design opening leaves about **1.09 inches** there,
reserving a nominal one-inch connection land. The rotated cabinet section and actual
seam/flange requirement still need a fabricator's detail.

| Port | Face | Centre in project inches (x/y/z) | Section | Duct |
| --- | --- | --- | --- | --- |
| return | West | 298 / 339.09253 / 257.23518 | 20 × 16 | `DU-A-HP1-RET-NECK` |
| hall | Bottom | 304.5 / 360 / 240.75 | 12 × 10 | `DU-S-HP-RET` |
| suite | Bottom | 312.5 / 344 / 240.75 | 6 × 4 | `DU-S-HP-SUITE-RET-UP` |
| bed3 | North | 317.5 / 368 / 243.75 | 12 × 6 | `DU-S-HP-BED3-RET` |
| attic | South | 311.75 / 328 / 254 | 12 × 12 | `DU-A-HP1-EAST-RET` |
| fresh | South | 310 / 328 / 244 | 6 round | `DU-S-ERV-HP-FEED` |

The ERV feed enters horizontally through the south face, **not the floor** as previous
notes claimed. The four returns carry 455 + 80 + 80 + 35 = 650 cfm; the ERV adds 100,
making the nominal 750 cfm supply. Attic return balancing remains 35 cfm.

`mep.plenum_openings` tests each declared face opening against a duct crossing its centre,
normal to the face, with matching service, shape and section. Missing ducts, wrong sizes
and offsets fail even when their endpoints remain inside the equipment envelope.
Matching provisional openings report UNKNOWN, preserving the shop-drawing hold.
This check does not grade pressure loss, flange fit, installation access or omitted ports.

## Installation geometry now represented

The installed type carries the cabinet, pan, two rails, tapered bearing shims, primary
feeder and U-trap, capped upstream cleanout, open downstream vent and float-switch allowance.
Viewer, GLB and IFC share these parts. The loose installation parts are billed once on
`EQ-S-HP1-AH`; the routed drain takeoff begins at the trap outlet.

| Component | Design setout (inches) |
| --- | --- |
| Existing platform | 49 1/2 × 27 1/4; top z245, 4 1/4 above deck |
| Shop galvanized emergency pan | 49 1/2 × 27 1/4 outside, 2 high, 1/16 design sheet; no outlet |
| Two galvanized tube rails | 3 high × 1 1/2 wide × 1/8 wall; 21 1/4 long; x254.25 / 290.25 |
| Cabinet low front bearing | z248.0625, **7 5/16 above deck** |
| Cabinet pitch | 1/8 inch/ft toward south drain face; rear about 0.221 inch higher |
| Primary inlet | x288.25 / y328.55208 / z249.06245; inherited schematic station |
| Trap inlet / outlet | x299.5, y324.5 / 321.5; outlet z247.06245 |
| Trap | 2 inlet-to-outlet drop, 3 seal; 1.05 pipe OD / 1.375 fitting allowance; bottom z243.37495 |
| Cleanout / downstream vent top | z251.56245 before cleanout cap; 2 1/2 above inlet |
| Supply neck centre | y343.90477 / z257.28531 |
| Return neck centre | y339.09253 / z257.23518 |

The reserved trap/fitting exterior is **2.62495 inches above the attic deck** (z240.75), east of the
platform and the 24-inch front service rectangle. Its feeder turns east close to the
cabinet face before dropping outside the platform. The former 3 1/2-inch trap allowance
remains withdrawn: the drawn trap/fitting envelope extends 5.6875 inches below the inlet. Returning the
cabinet to its former 4 1/4-inch elevation puts that exterior below the deck and puts the
pan inside the platform; the installation check fails both conditions.

Both deck-mounted plenums grew from 23 to 27 inches high; only their cabinet-neck
openings moved. Their other openings and associated risers remain fixed. The flat necks
meet the centres of the pitched cabinet openings; fabricator must resolve their slightly
rotated sections and connector lands rather than treating centre alignment as flange fit.

Selected float switch: **RectorSeal SS3 Gen3, 97089**.
[Manufacturer page](https://rectorseal.com/safe-t-switch-ss3-new/) and
[R50109-0724 product data](https://rectorseal.bynder.com/asset/58f18ce3-df8f-47fe-9339-fbd9b53152f5/Spec-Sheet-English.pdf):
tested to UL 508, 24 VAC / 1.25 A, 1–2-inch auxiliary pans. The current body drawing has
no dimensions. The model therefore reserves a **provisional 1.6 × 1.58 × 3.55-inch**
body/bracket allowance at x265 on the south pan rim, with a design trip depth of one inch
above the inner floor. Confirm the delivered envelope, adjustment and free travel.
Wet-test shutdown before overflow. The owner’s pan + float shutdown arrangement remains;
there is no second line. Final wiring must stop cooling at `EQ-M-HP1-OD` while preserving
Gree’s blower delay and R32 mitigation controls; the wire route is not modeled.

`mep.air_handler_installation` checks the drawn stack, platform seating, trap/deck and
platform clearance, service-zone location, drain start and float level. Missing geometry
is UNKNOWN; dimensional violations fail. Successful geometry retains a separate UNKNOWN
for schematic drain stations, pan/rail fabrication and the float-switch allowance. It
does not certify the delivered installation. Rail bearing stations, pan sheet/seams and
point loads, PVC socket takeouts and access for cap removal require installer review.

## Remaining design holds

1. **Supply connector:** the specified Duro Dyne MFN has a nominal 3-inch fabric section.
   The manual's first-six-inches sheet-metal wording needs resolution before fabrication.
   The bottom outlet begins 10 1/2 inches west of the cabinet discharge plane; a solid
   floor strip alone does not establish that the fabric connector is acceptable.
2. **Heat kit:** `FLEXA2LHTR05KWD` is specified and placed inside the raised cabinet, but its drawn
   envelope is schematic. Obtain its installation envelope and resolve the main manual's
   supply-duct clearance wording against the drop through the wood floor assembly.
3. **ERV backdraft damper:** required in the 6-inch feed but has no selected product or
   independently verified blade/body/service envelope here. The drawn feed invert is only
   1/4 inch above the box bottom, so a flanged collar cannot be assumed to fit there;
   coordinate the damper/collar assembly and final deck-leg height. A shell opening adds none.
4. **Refrigerant pair and controls:** outdoor pairing is declared; the 3/8 + 3/4 lineset,
   insulation, fitting access and actual control route are not modeled. The cabinet's
   markers reserve none of this space.
5. **Filtering and static pressure:** return filter grilles are specified; the cabinet's
   internal filter choice and combined losses still need coordination. Submittal fan
   data are for a dry coil with factory filter. Its 0.96 wet-coil factor makes speed 3
   at 0.5-inch ESP about 730 cfm, below the nominal 750. Do not treat 760 dry-coil cfm
   as confirmation of delivered design airflow.
6. **Service access:** front panels face south onto open deck. The 24-inch zone follows the
   pitched cabinet; the trap is east of it. Confirm panel removal, cap-removal access,
   pan-rim footing and future lineset geometry. Passageway/level workspace is not graded.

Software/design work is tracked in `plans/TODO.md`; measurements, submittals and
manufacturer confirmations belong in [`construction_holds.md`](construction_holds.md).
