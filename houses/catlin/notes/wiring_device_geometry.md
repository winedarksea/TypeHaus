# Wiring device, plate and box geometry

Read 2026-11-15 from manufacturer sheets and drawings. This is the source for
`plan/device_types.py` (face size, projection, `rear_projection`) and the plate and gang-bank
rows in `plan/device_boxes.py` (`resolve/device_banks.py`).

## Adopted in the model

- **Type geometry.** `footprint` is (face width, projection past the plate) and `height` is the face height.
  - Projection past the plate = front past the strap, less the 1/4" midway plate.
  - The body behind the plate is not drawn. It is graded as `rear_projection` against box depth.
  - Scaled or unpublished rears are left unauthored: T5020, T6525, DVELV-300P, MA-T51 and ZEN32.
- **Plates.**
  - Default family `midway`, because the Lever Edge strap is 1.78" wide (Leviton).
  - `standard` is the tight-space alternative; it needs the strap's breakaway tab removed.
  - The Diva takes `claro`; the 1450R/278 are `integral`, because the strap is the plate.
  - The single-receptacle devices (T5020, T5461) take `standard` 80704-W.
- **Banks.**
  - 10 banks snap to 1 13/16" pitch: a 4-gang (BH464A) on W-M-C1, 3-gangs (BH353A) on W-M-C3, W-M-MUDC-E and W-G-S, and six 2-gangs.
  - Box fill is graded on the bank box. The 4-gang carries 60.75 of 64 in³.
- **Open.**
  - ED-M-LIVING-KET1 (`ED-T-LEV-620-FLUSH`): a round T5461 beside a Decora E5825 needs a single + Decora combination plate. `integrity.device_plate` stays UNKNOWN until one is chosen.
  - ED-M-FIRE-RC: no Decora plate fits the 2 3/8" strip beside the insert (`advisory.wall_plate_clearance`).

## 1. Device types (device_types.py)

No `rear_projection` is authored on any type in `device_types.py` today
(`model/electrical_facts.py:89` is the field; `checks/mep/electrical_boxes.py` grades it:
box depth = rear + 1/4" past 1-7/8", or past **1" on 12/10 AWG**). `construction_holds.md`
lists GFCI and smart-switch `rear_projection` as unpublished; the drawings below publish them.

L = https://www.leviton.com/content/dam/leviton ; LE = Lever Edge spec sheet NM-110723A =
`frpublish.leviton.com/content/dam/leviton/residential/product_documents/product_specification/Lever-Edge-Product-Specifications.pdf`

| Tag(s) | Product | Face W x H | Front (past strap) / past plate | Rear | Colour | Source |
| --- | --- | --- | --- | --- | --- | --- |
| ED-T-LEV-DUPLEX-20, -REC, QUAD-520, 620-DUPLEX/-FLUSH (duplex half) | E5825-W | 1.29 x 2.61 [32.8 x 66.3]; strap 1.78 x 4.12 (4.56 with ears) | 0.30 [7.6] / ~+0.04 | **not drawn for the 20 A**; E5325 drawing 0.88 [22.3] (total 1.18) is the nearest; E5825 takes 10 AWG so verify | white | LE (drawing is labelled E5325/E5601 only) |
| ED-T-LEV-DUPLEX-15 | E5325-W | 1.29 x 2.61 | 0.30 / ~+0.04 | 0.88 [22.3] | white | LE |
| ED-T-LEV-SW1 | E5601-W | 1.29 x 2.61 | 0.30 / ~+0.04 | 1.01 [25.6] (total 1.31) | white | LE |
| ED-T-LEV-SW3 | E5603-W | as E5601 (3-way listed on the same sheet and spec text; no own drawing) | 0.30 | 1.01 | white | LE |
| ED-T-LEV-GFCI-20, -GFCI-WR, -GFCI-DF, -GFCI-GUIDE | GFTR2-W, GFWT2-W, GFRBF-W, GFNL2-W | face height 2.70 [68.6]; width not dimensioned (fills the 1.31 opening); body behind plate 1.68 wide; strap 4.19 x 1.31 ears | 0.35 (total 1.38) / ~+0.10 | 1.03 [26] | white | `L/residential/product_documents/dimensional_drawing/gftr2-dimensional%20drawing.jpg`. GFWT2, GFRBF and GFNL2 pages link this same drawing (all "SLIM"). |
| ED-T-LEV-GFCI-15, -GFCI-WR-15 | GFTR1-W, GFWT1-W | as above, 2.70 tall | 0.28 (total 1.31) / ~+0.03 | 1.03 [26] | white | `L/residential/product_documents/dimensional_drawing/gftr1-dimensional-drawing.jpg` |
| ED-T-LEV-GFCI-ALARM | GFTA2-W | 2.71 [68.9] tall | 0.36 (total 1.43) / ~+0.10 | 1.07 [27.2]; "in box from strap back" 4.34 in3 | white | `L/residential/product_documents/dimensional_drawing/GFTA2_dimensional_drawing.pdf` |
| ED-T-LEV-USBC | T5836-W | 1.29 x 2.61 [32.6 x 66.2]; body 1.73 x 2.77 | 0.32 [8] (strap 0.05 separate) / ~+0.07 | 1.50 [38.1] to body (total 1.86); pigtail leads run past that | white | `L/residential/product_documents/dimensional_drawing/t5836-dimensional-drawing.jpg` |
| ED-T-LEV-SURGE | T5380-W | height 2.72 [69.1]; width not dimensioned; body 1.77 | 0.37 (total 1.56) / ~+0.11 | 1.19 [30.2] | white | `L/commercial-industrial/product_documents/dimensional_drawing/T5380-W.jpg` |
| ED-T-LEV-GUIDE | T6525-W | not published by Leviton; dist. 1.31 W x 4.18 H (strap) | not published; assume ~0.30 | not published; dist. total depth 1.08 (Stoneway, Home Depot CA) so rear ~0.8 | white | none on leviton.com (page has no drawing). `stoneway.com/LEVITON-WIRING-DEVICES-T6525-W-...-White-Self-Grounding/p2338136` |
| ED-T-LEV-SINGLE-520 | T5020-W | **not a Decora**: smooth-face round-body single, face ~Ø1.4 (**scaled**); strap ears 1.31, 4.06 tall | total 1.14 [29]; front ~0.32 (**scaled**) | ~0.82 (**scaled**) | white | `L/commercial-industrial/product_documents/dimensional_drawing/CATSTD-T5020-00W-D01.PDF` |
| ED-T-LEV-620, 620-DUPLEX/-FLUSH (6-20R half) | T5461-W | **not a Decora**: round body ~Ø1.4 (**scaled**), 1.53 [38.9] wide with clamps; strap 4.06 tall | total 1.11 [28.1]; front 0.32 | 0.79 [20.1] | white | `L/commercial-industrial/product_documents/none/250VTR-Marketing%20PDF.PDF` (drawing ORB6345-D02) |
| ED-T-LEV-RANGE-1450 | 1450R | round face Ø2.43 [61.7]; strap IS the plate: 2.75 [69.9] x 3.75 [95.3], ~0.08 thick | ~0.45 (**scaled**, 200 dpi) | ~1.80 (**scaled**; total 2.33 [59.1] callout) | **black** | `L/commercial-industrial/product_documents/dimensional_drawing/CATSTD-1450R-XXX-D01.pdf` |
| ED-T-LEV-DRYER-1430 | 278 | body width 2.10 [53.3] (round face ~2.1, not called out); strap 2.50 [63.5] x 3.75 [95.3], 0.04 thick | 0.42 [10.7] | ~1.9 (**scaled**, not called out) | **black** | `L/residential/product_documents/none/LC_DOC_DDG_PNG_FLUSH30GROUND.png` |
| (cover on GFCI-WR / -WR-15) | 5980-UCL | 3.63 W [92.3] x 6.69 H [169.9]; opening 2.66 [67.6] | 3.08 [78.2] off the wall | n/a | clear | `L/commercial-industrial/product_documents/dimensional_drawing/5980-dimensional-drawing.jpg` |
| ED-T-LEV-MATTER | D315S-1BW | paddle body 2.76 [70.2] tall; strap 1.80 [45.7] x 4.12 [104.6] (own plate-width strap) | 0.26 [6.5] / ~0 | 1.09 [27.7] | white (DDKIT-S colours) | `L/residential/product_documents/dimensional_drawing/d315s-dimensional-drawing.jpg` |
| ED-T-LEV-RF-COMPANION | DAWSC-1BW | **not published** (spec sheet has no dimensions) | not published | not published (battery, wall or box mount) | white | `L/residential/product_documents/product_specification/DAWSC-1BW-Decora-Smart-Wi-Fi-Anywhere-Switch-Companion-Product-Specification.pdf` |
| ED-T-LEV-OCC-PIR | DOS02-LW | face not dimensioned; strap 1.73 x 4.13 | 0.43 / ~+0.18 | 0.95 | white (DOSKT faces) | `L/residential/product_documents/product_bulletin/Leviton-Decora-Motion-Sensor-Product-Bulletin.pdf` p.3 |
| ED-T-LEV-OCC-PANTRY | ODS10-IDW | lens width 1.30 [33.0], face height 2.61 [66.3]; strap 1.75 [44.4] x 4.06 [103.2] | 0.48 [12.6] / ~+0.23 | 1.35 [34.4] "install depth"; overall 1.83 [47] on leviton.com | white | `L/lighting-controls/controls/product_documents/product_specification/Passive-Infrared-Wall-Switch-Occupancy-Sensor-ODS10-ID-English-Data-Sheet.pdf` |
| ED-T-LUT-DIVA | DVCL-153P | body 2.75 [70] tall; opening is the Decora designer opening; Claro plate 2.94 x 4.69 | plate 0.30 [7.6]; paddle projection not published | 1.31 [33] (wallbox 2 1/2" [64] min) | WH, IV, LA, etc. gloss | `https://assets.lutron.com/a/documents/369682.pdf` (369682h, 04.08.24) |
| ED-T-LUT-DIVA-ELV | DVELV-300P | not published in a Lutron sheet I could open; dist. plate size 4.69 x 2.94 | not published | not published; a Lutron catalog snippet (unread, no URL) says <= 1.44 [37] and backbox 2.5 min; Diva LED+ is 1.31 | white (WH) gloss | `elliottelectric.com/Media/DVELV300PWH-LUT` (dist.) |
| ED-T-LUT-COUNTDOWN | MA-T51 | body 2 5/8 [66] tall; plate 4 11/16 x 2 15/16 [119 x 75] | plate 5/16 [8]; face projection not published | 1 1/8 [29] (wallbox 2 1/4 [57] min) | white gloss | `https://assets.lutron.com/a/documents/3691316_eng.pdf` is the **MA-T51MNB-WH** (neutral required); no sheet found for plain MA-T51 |
| ED-T-ZOOZ-ZEN32 | ZEN32 | 4.1 H x 1.75 W (strap); face not published | not published | 1.16 total depth, not split | white (not stated) | `https://www.support.getzooz.com/kb/article/705-zen32-scene-controller-specs/` |

## 2. Wall plates

Leviton size guide Q-1289 (2021): `frpublish.leviton.com/content/dam/leviton/commercial-industrial/product_documents/solution_sheets/Wallplate%20Size%20Guide%20Q-1289.pdf`.
Decora screw spacing 3.81 [96.8]; **add 1.81 [46.0] per gang** (3-gang drawing: 1.812 = 1 13/16).
Thickness: Q-1289 says 0.22 plastic standard, 0.26 midway/oversize; the 80401 drawing says
**0.255 [6.4]** and the midway drawing 0.25 [6.4]. Use the product drawings.

| Plate | Gang | Part (white nylon) | W x H | Source |
| --- | --- | --- | --- | --- |
| Leviton Decora standard | 1 | 80401-NW | 2.75 x 4.50 [69.8 x 114.3] | `L/residential/product_documents/none/LC_DOC_DDG_PNG_80401.png` |
| | 2 | 80409-NW | 4.56 x 4.50 [115.9 x 114.3] | `L/residential/product_documents/none/80409.png` |
| | 3 | 80411-NW | 6.375 x 4.50 | `L/residential/product_documents/none/Document-145705-Dimensional%20Data.gif` |
| | 4 | 80412-NW | 8.19 [208.0] x 4.50 | `L/residential/product_documents/none/Document-29687-Dimensional%20Data.gif` |
| Leviton Decora midway (+0.375 each way) | 1 | PJ26-W | 3.13 x 4.88 [79.4 x 123.8] | `L/residential/product_documents/none/Document-31144-Dimensional%20Data.JPG` |
| | 2 | PJ262-W | 4.94 (derived 3.13 + 1.81) x 4.88 | `.../Document-31171-Dimensional%20Data.JPG` (1-gang drawing + "add 1.81") |
| | 3 | PJ263-W | 6.75 (derived) x 4.88 | `.../Document-31176-Dimensional%20Data.JPG` |
| | 4 | PJ264-W | 8.56 (derived) x 4.88 | `.../Document-31181-Dimensional%20Data.JPG` |
| Leviton Decora oversize ("jumbo") | 1 | 88601-W (thermoset, not nylon) | 3.50 x 5.25 [88.9 x 133.4] per Q-1289 | `leviton.com/products/88601`; multi-gang not looked up |
| Leviton single receptacle (T5020, T5461) | 1 | 80704-W (1.406" hole, nylon) | 2.75 x 4.50, ~0.22 thick (dist.) | `leviton.com/products/80704-w` |
| Lutron Claro (gloss white; `-XX1` = gloss, SC- satin) | 1 | CW-1-WH | 2.94 [75] x 4.69 [119] x 0.30 | Lutron Specification Guide Vol.1 P/N 367-1746 REV H (Claro page), copy at `cdn.shopify.com/s/files/1/0011/5517/0351/files/Updated_Spec_-_Lutron_Claro_Multi-Gang_Wallplate_CW-1-WH_CW-2-WH_CW-3-WH.pdf`; height and 0.30 from Diva sheet 369682h and dist. |
| | 2 | CW-2-WH | 4.75 [121] | same |
| | 3 | CW-3-WH | 6.56 [167] | same |
| | 4 | CW-4-WH | 8.37 [213] | same (pitch 1.81) |

Lever Edge strap is 1.78 wide: Leviton says it takes midway plates, and standard plates only
with the breakaway tab removed (leviton.com/products/e5825-w). Plate choice affects the
visible margin round every Lever Edge, GFCI and Decora Smart device.

## 3. Boxes

| Box | W (gang dir) x H x D | Volume | Clamps | Source |
| --- | --- | --- | --- | --- |
| Carlon BH353A 3-gang SuperBlue nail-on | catalog **5 7/8 x 3 3/4 x 3 1/2**; ABB data 5.66 x 3.53 x 3.50 | 53.0 in3 | "integral clamps" | Carlon SuperBlue catalog pages, hosted at `pdf.lowes.com/productdocuments/8d9ea1e1-e68b-48ad-aca9-7601185d9c77/62279009.pdf`; ABB data sheet `media.distributordatasolutions.com/ThomasAndBetts/2018q3/9f657711d84b006ded2f0208da4b800665853082.pdf`. **Verify on ABB catalog** (empower.abb.com timed out). |
| Carlon BH464A 4-gang SuperBlue nail-on + bracket | catalog **7 3/4 x 3 7/8 x 3 1/2**; ABB-derived dist. data 7.46 x 3.53 x **3.18** deep | 64.0 in3 | "integral clamps" | same catalog; depth conflict 3.50 vs 3.18 (Crescent Electric listing of ABB data). **Verify on ABB catalog.** |
| Carlon BH235A 2-gang (existing row, 4.0 x 3.75 x 3.5) | catalog 4 1/8 x 3 7/8 x 3 1/2 | 35.0 | integral clamps | same catalog. Row is 1/8" under in both W and H. Distributors list BH235A as 3.55 x 2.11, which is the 1-gang's size: ignore. |
| Carlon B122A-UPC 1-gang (existing row, 2.25 x 3.75 x 3.5) | dist. 3 3/4 x 2 1/4 x 3 1/2 (matches the row) | 22.0 | none stated | Steiner, Standard Electric (dist.). |
| Carlon **BH122A-UPC** 1-gang SuperBlue (same family as the 2-4 gang) | catalog 2 3/8 x 3 7/8 x **3 3/4** | 22.0 | none stated | same catalog |
| Arlington DVFR1W IN BOX recessed | 4.200 x 6.698 x 3.875 | 21.0 | n/a | `https://www.aifittings.com/media/catalog-pages/Q-3.pdf` |
| DVFR2W / 3W / 4W (multi-gang, same sheet) | 6.012 x 6.698 / 7.930 x 6.818 / 9.742 x 6.818, all 3.875 | 34.0 / 49.3 / 64.5 | n/a | same |

**DVFR1W includes its own plate.** Q-3: "INDOOR IN BOX INCLUDES recessed box, trim plate,
(1) standard duplex and (1) standard GFCI face plate, NM94 connector, mounting screws".
`plate_included=True` is right; the duplex plate is the trim, so no separate Decora plate.

## 4. Open / verify

- **T5020-W and T5461-W are not Decora devices.** Leviton lists them as "Single Receptacle
  Outlet ... Smooth Face" and the drawings show a round body (~1.4"). `device_types.py` calls
  T5020 "Decora single". They take a single-receptacle plate (80704-W, 1.406" hole), and
  `ED-T-LEV-620-DUPLEX/-FLUSH` pairs a round T5461 with a Decora E5825 in two gangs: no
  standard two-gang plate does that. Needs a design decision.
- **E5825 rear projection** is not drawn (only E5325/E5601). 0.88 is provisional.
- **T6525 (guide light) and DVELV-300P**: no manufacturer dimensions found.
- **MA-T51**: Lutron's current sheet is the MA-T51MNB (neutral required); no sheet
  was found for the plain MA-T51. Confirm which part is wired (no-neutral vs neutral) before using 1 1/8".
- **DAWSC, ZEN32**: face size and projection unpublished; the types' 1.75 x 0.6 x 2.9 (DAWSC)
  is unsourced. Zooz also sells its own engraved plate for the ZEN32.
- **278 rear (~1.9)** and **1450R front/rear** are scaled from drawings; 278 would trip the
  1-7/8" depth rule, 1450R (1.80) would not. 278 and 1450R are **black**, 5980-UCL clear.
- GFCI face widths and the 2-gang+ Decora opening spacing assume the 1.310 x 2.630 opening on
  1.8125" pitch (80411 drawing); the 3-gang plate is the only multi-gang drawing read in full.
- Box rows: re-read BH353A/BH464A/BH235A on ABB's catalog; the repo's 1- and 2-gang rows look
  like the "B" family body size, not the SuperBlue catalog size, and BH464A depth is 3.18
  vs 3.50.
- Midway 2-4 gang widths are derived (1-gang drawing + 1.81/gang); the 2-4 gang JPGs show the
  1-gang outline.
