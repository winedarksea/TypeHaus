# EQ-S-HP1-AH connection and service-space review — 2026-11-15

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

`EQ-A-HP1-SUP-BOX`: 22 1/2 × 14 × 23 inches, on the attic deck.
Its east opening meets `DU-A-HP1-SUP-NECK` (11 5/8 × 16 3/4);
its bottom opening is 12 × 12, at x234/y344, matching `DU-S-HP-SUP-DROP`.
The old bottom port incorrectly sat at the box centre, 2 1/4 inches east of the drop.

`EQ-S-ERV-MIX`: **27 1/2 × 40 × 23 inches**, west/east faces x298/325.5,
south/north faces y328/368, base z240.75 (all project inches). It grew one inch south
from the previous 39-inch depth, keeping the north face and every duct station fixed.
The provisional cabinet neck otherwise left only 3/16 inch between its aperture and
that south corner. The revised lip is 1 3/16 inches, reserving a nominal one-inch
connection land; the fabricator must confirm the actual seam/flange requirement.

| Port | Face | Centre in project inches (x/y/z) | Section | Duct |
| --- | --- | --- | --- | --- |
| return | West | 298 / 339.1875 / 254.0625 | 20 × 16 | `DU-A-HP1-RET-NECK` |
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

## Incomplete installation geometry and design holds

1. **Emergency pan, support rails, float switch:** specified but still not drawn.
   `secondary_drain_pan=True` is a declaration, not dimensional evidence. The existing
   49 1/2 × 27 1/4 platform reserves space but no selected pan/rail assembly establishes
   cabinet elevation. Keep the owner's pan + float-shutdown arrangement; no second line.
2. **Primary trap:** `PR-A-COND-HP1` starts with a nearly level pipe, not a trap.
   The manual's diagram shows a 2-inch inlet-to-outlet drop and 3-inch seal depth,
   implying about 5 inches below the inlet before pipe/fitting thickness. The previous
   3 1/2-inch allowance is withdrawn. Cabinet pitch and the vent/cleanout envelope also
   need representation. Do not certify the 4 1/4-inch platform from the schematic port.
   Raising the cabinet requires moving both necks, box inlet/outlet ports and drain start
   together; no elevation change has been made in this review.
3. **Supply connector:** the specified Duro Dyne MFN has a nominal 3-inch fabric section.
   The manual's first-six-inches sheet-metal wording needs resolution before fabrication.
   The bottom outlet begins 10 1/2 inches west of the cabinet discharge plane; a solid
   floor strip alone does not establish that the fabric connector is acceptable.
4. **Heat kit:** `FLEXA2LHTR05KWD` is specified and placed inside the cabinet, but its drawn
   envelope is schematic. Obtain its installation envelope and resolve the main manual's
   supply-duct clearance wording against the drop through the wood floor assembly.
5. **ERV backdraft damper:** required in the 6-inch feed but has no selected product or
   independently verified blade/body/service envelope here. The drawn feed invert is only
   1/4 inch above the box bottom, so a flanged collar cannot be assumed to fit there;
   coordinate the damper/collar assembly and final deck-leg height. A shell opening adds none.
6. **Refrigerant pair and controls:** outdoor pairing is declared; the 3/8 + 3/4 lineset,
   insulation, fitting access and actual control route are not modeled. The cabinet's
   markers reserve none of this space.
7. **Filtering and static pressure:** return filter grilles are specified; the cabinet's
   internal filter choice and combined losses still need coordination. Submittal fan
   data are for a dry coil with factory filter. Its 0.96 wet-coil factor makes speed 3
   at 0.5-inch ESP about 730 cfm, below the nominal 750. Do not treat 760 dry-coil cfm
   as confirmation of delivered design airflow.
8. **Service access:** front panels face south onto open deck. The existing 24-inch zone
   remains, but installation of the missing pan/trap/lineset must preserve removal access.

Software/design work is tracked in `plans/TODO.md`; measurements, submittals and
manufacturer confirmations belong in [`construction_holds.md`](construction_holds.md).
