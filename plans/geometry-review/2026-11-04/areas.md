# Round-2 areas (2026-11-04)

Generated from round-1 `findings/*.json`, `git diff 247a13e9..HEAD` and the round-2 `permit_set_full.json`. Sheets are a sheet-number match: a starting list, not a limit.

## S1: Stairs, interior and exterior: straight, U-split, winders, concrete tiers, porch stair, ST-G-SERVICE; stringers, nosing, skirt, landings, headroom, thresholds

- **Start:** `packages/engine/src/typehaus/resolve/stairs/*`, `packages/engine/src/typehaus/resolve/stair_headroom.py`, `houses/catlin/notes/stair_*_basis.md`, `houses/catlin/notes/floor_heights.md`, `houses/catlin/notes/porch_stair.md`, `houses/catlin/notes/u_stair_split_landing.md`, `houses/catlin/notes/winder_stair_basis.md`, `houses/catlin/notes/garage_service_door_outswing.md` (24 files)
- **Prior ids (10):** S1-001, S1-002, S1-003, S1-004, S1-005, S2-001, S2-002, S2-003, S2-004, S2-005
- **Sheets:** S-501.1 (p21), A-101 (p29), A-102 (p30), A-103 (p31), A-104 (p32), A-301 (p38), A-301.1 (p39), A-301.2 (p40), A-508 (p55), A-509 (p56), A-510 (p57)
- **Changed since round 1, look here first** (8 files): `houses/catlin/notes/porch_stair.md` ±177, `houses/catlin/notes/floor_heights.md` ±132, `houses/catlin/notes/garage_service_door_outswing.md` ±33, `houses/catlin/notes/stair_riser_basis.md` ±18, `packages/engine/src/typehaus/resolve/stairs/walkline.py` ±10, `packages/engine/src/typehaus/resolve/stairs/bearing.py` ±7, `houses/catlin/notes/stair_skirt_basis.md` ±6, `packages/engine/src/typehaus/resolve/stairs/dispatch.py` ±3
- **TODO lines (keyword match):**
  - L48: `mep.riser_through_deck` (undrawn holes) and the itemised web crossings, each with its count
  - L70: front-left, under the ERV case's 54" bottom), the HydroBoost riser's projection (r ~15", 2 1/4"
  - L88: gate. The binding gate is 2.7" between the EXH riser crown (y 409.8") and `DU-ERV-EA`'s wrap
  - L89: (y 412.5"), with the radon moved 2 1/2" or not; also 5.5" between the SUP and EXH risers (three
  - L180: post-resolve documentation.
  - L222: - A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairw
  - L224: - Around bathrooms and bedrooms we want higher STC. Around major hallways and stairs we want abuse resistance (but only need it on the lower 4' above 
  - L257: - [ ] Window stools pass through the buck jambs (`framing|window_stool`, 34 pairs): notch in `geometry_millwork.window_stool_ring`. ST-G-SERVICE riser
  - L263: - DAKAM: Alucover operable sill rail height and sash overlap (author `WindowType.sill_rail_height` / `sash_overlap`). Andersen dealer: the 400 casemen
  - L269: - Product/cost review holds (2026-11-04, `plans/catlin-product-cost-review/REPORT.md`):
  - L298: - Owner: trimless for RM-M-LIVING / RM-M-BED / the stair hall (note §12), and whether "the heat pump over the stairway" includes the 28x12 return.
  - L325: - **`RL-A-FLIGHT-GUARD` newel junction (not graded).** Near the 25'-5 1/8" newel its post (top 20'-2 1/4") and top rail run into `FO-A-STAIR`'s trimme

## S3: Guards, handrails, railings, bracket products, incl. the fascia-mount balcony railings

- **Start:** `packages/engine/src/typehaus/resolve/railings/*`, `packages/engine/src/typehaus/library/railings.py`, `houses/catlin/plan/handrail_types.py`, `houses/catlin/plan/titanium_types.py`, `houses/catlin/notes/balcony_fascia_mounts.md`, `houses/catlin/notes/titanium_handrail_backsplash.md` (19 files)
- **Prior ids (8):** S3-001, S3-002, S3-003, S3-004, S3-005, S3-006, S3-007, S3-008
- **Sheets:** S-501.1 (p21), S-602 (p24), S-602.1 (p25), S-602.2 (p26), A-102 (p30), A-103 (p31), A-104 (p32), A-201 (p34), A-202 (p35), A-203 (p36), A-204 (p37), A-508 (p55), A-510 (p57)
- **Changed since round 1, look here first** (14 files): `packages/engine/src/typehaus/resolve/railings/fascia_assembly.py` ±158, `packages/engine/src/typehaus/resolve/railings/fascia_mesh.py` ±117, `packages/engine/src/typehaus/resolve/railings/fascia_layout.py` ±82, `packages/engine/src/typehaus/resolve/railings/__init__.py` ±68, `packages/engine/src/typehaus/resolve/railings/column_ends.py` ±64, `houses/catlin/notes/balcony_fascia_mounts.md` ±64, `packages/engine/src/typehaus/resolve/railings/surface_assembly.py` ±62, `packages/engine/src/typehaus/library/railings.py` ±51, `packages/engine/src/typehaus/resolve/railings/frame.py` ±44, `packages/engine/src/typehaus/resolve/railings/spans.py` ±41, `packages/engine/src/typehaus/resolve/railings/infill.py` ±21, `packages/engine/src/typehaus/resolve/railings/guard_line.py` ±17, `packages/engine/src/typehaus/resolve/railings/mounting_solids.py` ±16, `houses/catlin/plan/handrail_types.py` ±4
- **TODO lines (keyword match):**
  - L228: - Make sure all handrail brackets are stock, avoid custom needs. Remaining: titanium railing brackets (aim to use standard as much as possible). Also 
  - L233: - [ ] Before fabricating RM-M-STUDY-CLOSET: complete the 60-minute seating mock-up, verify occupied cushion height, lumbar fit and bracket/blocking co
  - L263: - DAKAM: Alucover operable sill rail height and sash overlap (author `WindowType.sill_rail_height` / `sash_overlap`). Andersen dealer: the 400 casemen
  - L271: - 07-001 Breezeway: the 5.9 LF guard package (product, posts, price).
  - L281: - Kitchen sink fabrication hold: dry-fit KHU100-32 / Bolden KPF-1610SFS / Badger 5 / Dearborn P9703WBG in the 36-inch SEKTION. Verify delivered Badger
  - L290: - Autorouter open items (plumber's-rules pass, 2026-11-03; drain basis §13, `docs/routing.md`; perf guard and `--manifold` done 2026-11-04):
  - L306: - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the
  - L325: - **`RL-A-FLIGHT-GUARD` newel junction (not graded).** Near the 25'-5 1/8" newel its post (top 20'-2 1/4") and top rail run into `FO-A-STAIR`'s trimme
  - L345: - Properly model the fascia mount railing
  - L346: - Items that seem too expensive: 12" concrete basement (thought we were down to narrower), FX-SHOWER-36-THERMO-COMBO, FX-TUBSHOWER-60-DIVERTED, RAILIN

## O1: Interior doors: leaves, ROs, jambs, door_sizing, pocket (Eclisse), bookcase door, hardware

- **Start:** `packages/engine/src/typehaus/resolve/door_sizing.py`, `packages/engine/src/typehaus/resolve/doorway*.py`, `packages/engine/src/typehaus/resolve/jamb_fill.py`, `packages/engine/src/typehaus/library/doors.py`, `houses/catlin/plan/door_types.py`, `houses/catlin/plan/interior_door_types.py`, `plans/door-sizing.md`, `houses/catlin/notes/interior_door_schedule.md`, `houses/catlin/notes/pocket_frame_eclisse.md` (13 files)
- **Prior ids (8):** O1-001, O1-002, O1-003, O1-004, O1-005, O1-006, O1-007, O1-008
- **Sheets:** A-101 (p29), A-102 (p30), A-103 (p31), A-104 (p32), A-516 (p67), A-517 (p68), A-518 (p69), A-519 (p70), A-520 (p71), A-521 (p72), A-522 (p73), A-523 (p74), A-524 (p75), A-527 (p78), A-528 (p79), A-530 (p81), A-601 (p149), A-601.1 (p150)
- **Changed since round 1, look here first** (8 files): `houses/catlin/plan/interior_door_types.py` ±88, `packages/engine/src/typehaus/resolve/door_sizing.py` ±78, `packages/engine/src/typehaus/resolve/doorway_framing.py` ±66, `houses/catlin/notes/interior_door_schedule.md` ±63, `packages/engine/src/typehaus/resolve/doorway.py` ±31, `plans/door-sizing.md` ±16, `houses/catlin/plan/door_types.py` ±8, `packages/engine/src/typehaus/resolve/jamb_fill.py` ±4
- **TODO lines (keyword match):**
  - L19: - **D-G-SERVICE swing limited by W-BW-SCREEN after the canopy-beam move — owner to revisit (slide door, rebuild screen face).** Stopped at 81° for now
  - L40: - **Low-voltage devices still unmodelled:** the doorbell, both cameras, the leak probe and
  - L41: the lock exist (`plan/smart_home.py`); an outdoor weather station and any access reader
  - L71: off `D-B-CLOSET`'s 75-degree sweep) and the cord's length (`notes/water_service.md` §1); and the
  - L76: the Broan ERV's exposed service door, published clearances, and high outdoor screen's ladder
  - L209: widening the gap back to a nominal 5" pushes the court 2.25" south and FAILs D-B-SUNKEN.
  - L210: - Figure out a space for a cat litter box. Options: either a cat door on the current vanity planned (no change) or a wall mounted sink leaving space f
  - L211: - **A library catalog type cannot name a house-owned `Product`.** `ED-T-EV-1450` lives in
  - L222: - A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairw
  - L224: - Around bathrooms and bedrooms we want higher STC. Around major hallways and stairs we want abuse resistance (but only need it on the lower 4' above 
  - L226: - Open (drywall overhaul): mudroom wainscot could be LP SmartSide 38 Series 7/16" (sidings used indoors) instead of the shiplap; the shiplap stays unt
  - L238: - [ ] `D-B-SUNKEN` band header (structural project): load takedown for the stacked D-S-BALCONY/D-M-PORCH jamb packs, their bearing interfaces, LVL ply

## O2: Interior trim: casing and base from TrimStandard; intersections, reveals

- **Start:** `packages/engine/src/typehaus/resolve/interior_trim*.py`, `packages/engine/src/typehaus/resolve/geometry_millwork.py`, `houses/catlin/plan/products_trim_stock.py` (7 files)
- **Prior ids (11):** O2-001, O2-002, O2-003, O2-004, O2-005, O2-006, O2-007, O2-008, O2-009, O2-010, O2-011
- **Sheets:** A-002 (p28), A-516 (p67), A-517 (p68), A-518 (p69), A-519 (p70), A-520 (p71), A-521 (p72), A-522 (p73), A-523 (p74), A-524 (p75), A-525 (p76), A-526 (p77), A-527 (p78), A-528 (p79), A-529 (p80), A-530 (p81), A-601 (p149), A-601.1 (p150), A-603 (p152)
- **Changed since round 1, look here first** (5 files): `packages/engine/src/typehaus/resolve/interior_trim_casing.py` ±13, `houses/catlin/plan/products_trim_stock.py` ±13, `packages/engine/src/typehaus/resolve/interior_trim_base.py` ±8, `packages/engine/src/typehaus/resolve/interior_trim_scope.py` ±6, `packages/engine/src/typehaus/resolve/geometry_millwork.py` ±5
- **TODO lines (keyword match):**
  - L7: Note that many of the pinned decisions in the code base here aren't as fixed as they sometimes claim, the "fixed" decisions were usually fixed in a na
  - L136: model (±5%) of W2/S/E2 with W1's braced top reads base moments 0.50–0.51× the cantilever
  - L243: - [ ] C3-E3 follow-up: the three exterior doors (D-M-ENTRY, D-M-PORCH, D-S-BALCONY) keep their RO base on the joist top, 3/4" under the subfloor the w
  - L262: - Metal Sales / SFS: Profile Vent NFA under the 1" Image II clip, and per foot or per strip (R806 passes 562 vs 553 in2); a lower BBD75 panel stopped 
  - L264: - Murphy Door: the custom 32 x 82 RO flush-mount (FF datum, body 28 3/4 x 78 1/2 x 8 1/4, casing 36 1/2, passage 24 1/4, price/lead time).
  - L267: - Frigidaire TWINSPAIRKIT 1/8" seam; LG LDTS5552S side-mount with no sub-top. Carpet backing thickness (Z-bar answer holds to 0.10"); Mohawk on the 3/
  - L287: - D-S-BALCONY: catalog coordination replaces the schematic plate/wrapped trim with a digitized ZAI outline, composite returns and short AridDek boards
  - L288: - House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and inst
  - L298: - Owner: trimless for RM-M-LIVING / RM-M-BED / the stair hall (note §12), and whether "the heat pump over the stairway" includes the 28x12 return.
  - L324: - Rainscreen closures (2026-10-29): close the supplier questions in `houses/catlin/notes/metal_trim_kit.md` "Open with suppliers" (Metal Sales x4, the
  - L325: - **`RL-A-FLIGHT-GUARD` newel junction (not graded).** Near the 25'-5 1/8" newel its post (top 20'-2 1/4") and top rail run into `FO-A-STAIR`'s trimme
  - L326: - Upgrade fasteners still uncounted (decision #105 covers panel screws, connector schedules, treated framing, roof/screen sheathing): wall sheathing a

## O3: Exterior doors: catalog units, sills, pans, thresholds vs finished floor, French and garage doors

- **Start:** `packages/engine/src/typehaus/resolve/exterior_door*.py`, `houses/catlin/plan/french_door_installations.py`, `houses/catlin/notes/french_door_catalog_installation.md`, `houses/catlin/notes/exterior_door_*.md`, `houses/catlin/notes/garage_door_header.md` (16 files)
- **Prior ids (11):** O3-001, O3-002, O3-003, O3-004, O3-005, O3-006, O3-007, O3-008, O3-009, O3-010, O3-011
- **Sheets:** A-101 (p29), A-102 (p30), A-103 (p31), A-201 (p34), A-202 (p35), A-203 (p36), A-204 (p37), A-508 (p55), A-512 (p59), A-512.1 (p60), A-512.2 (p61), A-513 (p62), A-513.1 (p63), A-513.2 (p64), A-514 (p65), A-515 (p66), A-601 (p149), A-601.1 (p150)
- **Changed since round 1, look here first** (9 files): `packages/engine/src/typehaus/resolve/exterior_door_catalog_fit.py` ±142, `houses/catlin/notes/french_door_catalog_installation.md` ±91, `houses/catlin/plan/french_door_installations.py` ±62, `packages/engine/src/typehaus/resolve/exterior_door_catalog_parts.py` ±41, `packages/engine/src/typehaus/resolve/exterior_door_catalog.py` ±22, `packages/engine/src/typehaus/resolve/exterior_door.py` ±18, `houses/catlin/notes/exterior_door_structural_mount.md` ±18, `packages/engine/src/typehaus/resolve/exterior_door_catalog_layout.py` ±16, `houses/catlin/notes/exterior_door_hardening.md` ±4
- **TODO lines (keyword match):**
  - L19: - **D-G-SERVICE swing limited by W-BW-SCREEN after the canopy-beam move — owner to revisit (slide door, rebuild screen face).** Stopped at 81° for now
  - L209: widening the gap back to a nominal 5" pushes the court 2.25" south and FAILs D-B-SUNKEN.
  - L238: - [ ] `D-B-SUNKEN` band header (structural project): load takedown for the stacked D-S-BALCONY/D-M-PORCH jamb packs, their bearing interfaces, LVL ply
  - L239: - [ ] Garage sill 3 5/8" of 5 1/2" on the ICF core (C3-E8).
  - L243: - [ ] C3-E3 follow-up: the three exterior doors (D-M-ENTRY, D-M-PORCH, D-S-BALCONY) keep their RO base on the joist top, 3/4" under the subfloor the w
  - L257: - [ ] Window stools pass through the buck jambs (`framing|window_stool`, 34 pairs): notch in `geometry_millwork.window_stool_ring`. ST-G-SERVICE riser
  - L263: - DAKAM: Alucover operable sill rail height and sash overlap (author `WindowType.sill_rail_height` / `sash_overlap`). Andersen dealer: the 400 casemen
  - L286: - D-B-SUNKEN: separate brick reveal, widened RO, 5-1/2 inch concrete seat and a foam-bed Trex tread with fascia box sides (2026-11-04, §6 of the note)
  - L287: - D-S-BALCONY: catalog coordination replaces the schematic plate/wrapped trim with a digitized ZAI outline, composite returns and short AridDek boards
  - L288: - House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and inst
  - L313: - D-B-SUNKEN has some weird top flashing that isn't needed here it seems (the threshold now reaches over the foam gap: the foam-bed tread, 2026-11-04)
  - L314: - D-B-SUNKEN has an STHD14 connector sprouting up in the middle.

## O4: Windows (incl. aluminum units): unit vs RO, heights vs girts and stud module, returns, stools, seats

- **Start:** `packages/engine/src/typehaus/library/windows.py`, `packages/engine/src/typehaus/resolve/opening_product_dimensions.py`, `packages/engine/src/typehaus/resolve/window_returns.py`, `packages/engine/src/typehaus/resolve/model_window_*.py`, `houses/catlin/plan/window_types.py`, `houses/catlin/plan/opening_products.py`, `houses/catlin/plan/window_stools.py`, `houses/catlin/notes/window_*.md` (11 files)
- **Prior ids (10):** O4-001, O4-002, O4-003, O4-004, O4-005, O4-006, O4-007, O4-008, O4-009, O4-010
- **Sheets:** A-201 (p34), A-202 (p35), A-203 (p36), A-204 (p37), A-512 (p59), A-512.1 (p60), A-512.2 (p61), A-513 (p62), A-513.1 (p63), A-513.2 (p64), A-514 (p65), A-515 (p66), A-525 (p76), A-526 (p77), A-529 (p80), A-602 (p151)
- **Changed since round 1, look here first** (6 files): `packages/engine/src/typehaus/resolve/window_returns.py` ±119, `houses/catlin/notes/window_and_door_procurement.md` ±88, `houses/catlin/plan/window_types.py` ±41, `houses/catlin/plan/opening_products.py` ±29, `houses/catlin/notes/window_coverings.md` ±6, `packages/engine/src/typehaus/resolve/model_window_seat.py` ±2
- **TODO lines (keyword match):**
  - L200: - Orientation-tuned glass, particularly second-story south-facing windows.
  - L236: - Window bottoms in 3D: the cause (stool top coplanar with a frame drawn 5.44" deep) is fixed in engine and viewer (geometry review O4-001); confirm b
  - L257: - [ ] Window stools pass through the buck jambs (`framing|window_stool`, 34 pairs): notch in `geometry_millwork.window_stool_ring`. ST-G-SERVICE riser
  - L263: - DAKAM: Alucover operable sill rail height and sash overlap (author `WindowType.sill_rail_height` / `sash_overlap`). Andersen dealer: the 400 casemen
  - L281: - Kitchen sink fabrication hold: dry-fit KHU100-32 / Bolden KPF-1610SFS / Badger 5 / Dearborn P9703WBG in the 36-inch SEKTION. Verify delivered Badger
  - L326: - Upgrade fasteners still uncounted (decision #105 covers panel screws, connector schedules, treated framing, roof/screen sheathing): wall sheathing a
  - L330: - Let's make sure all the charcoal gray and black details of the house exterior (various metal trim, window frames, foundation insulation cover) show 
  - L337: - **Tile medallions: not this pass (review 2026-11-01).** Any tile forces an underlay under all the LVP (~0.47" more finish: re-derive ST-M2S/ST-B2M r

## O5: Opening flashing, head caps, drips vs rainscreen and cladding depth

- **Start:** `packages/engine/src/typehaus/resolve/opening_flashing.py`, `packages/engine/src/typehaus/resolve/opening_head_*.py`, `houses/catlin/notes/opening_flashing_spec.md`, `houses/catlin/notes/flashing_model.md` (5 files)
- **Prior ids (5):** O5-001, O5-002, O5-003, O5-004, O5-005
- **Sheets:** A-002 (p28), A-201 (p34), A-202 (p35), A-203 (p36), A-204 (p37), A-512 (p59), A-512.1 (p60), A-512.2 (p61), A-513 (p62), A-513.1 (p63), A-513.2 (p64), A-514 (p65), A-515 (p66), A-525 (p76), A-526 (p77)
- **Changed since round 1, look here first** (4 files): `houses/catlin/notes/opening_flashing_spec.md` ±15, `packages/engine/src/typehaus/resolve/opening_head_cap.py` ±14, `houses/catlin/notes/flashing_model.md` ±8, `packages/engine/src/typehaus/resolve/opening_flashing.py` ±4
- **TODO lines (keyword match):**
  - L287: - D-S-BALCONY: catalog coordination replaces the schematic plate/wrapped trim with a digitized ZAI outline, composite returns and short AridDek boards
  - L288: - House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and inst
  - L304: - [x] Roof membranes at installed thickness, near-black under Flashing: house butyl 30 mil, garage/canopy HT rubberized asphalt 40 mil. House unvented
  - L312: - Pg 288 of the book has a roof eave detail where the roof and drip flashing alone extend out about an inch (no metal or sheathing).
  - L313: - D-B-SUNKEN has some weird top flashing that isn't needed here it seems (the threshold now reaches over the foam gap: the foam-bed tread, 2026-11-04)

## F1: Wall framing: studs, plates, heights vs storey stack, headers, kings/jacks, corners, jamb packs, stock

- **Start:** `packages/engine/src/typehaus/resolve/framing/*.py`, `packages/engine/src/typehaus/resolve/plate_seat.py`, `houses/catlin/plan/assemblies/envelope_walls.py` (34 files)
- **Prior ids (11):** F1-001, F1-002, F1-003, F1-004, F1-005, F1-006, F1-007, F1-008, F1-009, F1-010, F1-011
- **Sheets:** S-101.1 (p11), S-101.2 (p12), S-101.3 (p13), S-103.1 (p17), S-103.2 (p18), S-103.3 (p19), S-103.4 (p20), S-601 (p22), S-601.1 (p23), A-301 (p38), A-301.1 (p39), A-301.2 (p40), A-512 (p59), A-512.1 (p60), A-512.2 (p61), A-513 (p62), A-513.1 (p63), A-513.2 (p64), A-514 (p65), A-515 (p66), A-516 (p67), A-517 (p68), A-518 (p69), A-519 (p70), A-520 (p71), A-521 (p72), A-522 (p73), A-523 (p74), A-524 (p75), A-525 (p76), A-526 (p77), A-527 (p78), A-528 (p79), A-529 (p80)
- **Changed since round 1, look here first** (16 files): `packages/engine/src/typehaus/resolve/plate_seat.py` ±183, `packages/engine/src/typehaus/resolve/framing/openings.py` ±109, `packages/engine/src/typehaus/resolve/framing/roof.py` ±86, `packages/engine/src/typehaus/resolve/framing/backing_panels.py` ±80, `packages/engine/src/typehaus/resolve/framing/solver.py` ±42, `packages/engine/src/typehaus/resolve/framing/roof_stiffeners.py` ±38, `packages/engine/src/typehaus/resolve/framing/truss_heel.py` ±36, `packages/engine/src/typehaus/resolve/framing/girt_support_spacing.py` ±34, `packages/engine/src/typehaus/resolve/framing/sill_plate.py` ±33, `packages/engine/src/typehaus/resolve/framing/profiles.py` ±33, `packages/engine/src/typehaus/resolve/framing/roof_gable.py` ±22, `houses/catlin/plan/assemblies/envelope_walls.py` ±22, `packages/engine/src/typehaus/resolve/framing/truss_girts.py` ±16, `packages/engine/src/typehaus/resolve/framing/furring.py` ±14, `packages/engine/src/typehaus/resolve/framing/frame_end_supports.py` ±6
- **TODO lines (keyword match):**
  - L34: - **No sheet-layout engine**, so nothing checks a sheathing break landing on a stud. L corners
  - L116: - **Make the PV layout comply with roof access, then study a second row.** `params/solar.py`
  - L121: below 33% coverage or 36 inches above it. Study five modules along the ridge and a second
  - L133: ### Structural/framing residuals
  - L135: - **Court stems as a two-way plate (owner option, 2026-11-02).** A screening PyNite MITC4 plate
  - L159: - **R502.10.1's single-member header allowance is sawn-lumber only, deliberately** — an
  - L160: I-joist/floor-truss deck would need a manufacturer's hung-header table this engine doesn't
  - L162: nothing grades a single-member header against a span table at all —
  - L163: `structural.floor_opening_header` only reports past the prescriptive 8' ceiling.
  - L194: - **Cavity "canary" RH sensors** wanted in a south and west stud bay (no liner redundancy
  - L218: touch a tag (PANTRY/D8, STUDY/D13, MECH's "CHASE TYP. OF 2"), and on the 11x17 reduced check
  - L223: - Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam

## F2: Backing, blocking, fireblocking, bore limits

- **Start:** `packages/engine/src/typehaus/resolve/framing/backing*.py`, `packages/engine/src/typehaus/resolve/backing_datum.py`, `houses/catlin/plan/backing*.py`, `houses/catlin/notes/wall_backing.md`, `houses/catlin/notes/framing_bore_limits.md`, `packages/engine/src/typehaus/resolve/mep_bore*.py` (12 files)
- **Prior ids (12):** F2-001, F2-002, F2-003, F2-004, F2-005, F2-006, F2-007, F2-008, F2-009, F2-010, F2-011, F2-012
- **Sheets:** S-001 (p8), S-001.1 (p9), S-101.1 (p11), S-101.2 (p12), S-101.3 (p13), S-601 (p22), S-601.1 (p23), A-002 (p28), A-401.1 (p41), A-401.2 (p42), A-401.3 (p43), A-401.4 (p44), A-401.5 (p45), A-401.6 (p46)
- **Changed since round 1, look here first** (9 files): `packages/engine/src/typehaus/resolve/backing_datum.py` ±81, `packages/engine/src/typehaus/resolve/framing/backing_panels.py` ±80, `houses/catlin/plan/backing_wet.py` ±67, `houses/catlin/plan/backing.py` ±51, `packages/engine/src/typehaus/resolve/mep_bore_scope.py` ±38, `houses/catlin/notes/framing_bore_limits.md` ±29, `packages/engine/src/typehaus/resolve/mep_bore_geometry.py` ±9, `houses/catlin/plan/backing_bath_accessories.py` ±4, `houses/catlin/notes/wall_backing.md` ±3
- **TODO lines (keyword match):**
  - L24: the hydrant bores): the elevation honours `depth_from` via `geometry_walls.cuts_layer`, the
  - L30: checklist's non-blocking "Concrete materials for the exposure class" line, not on an
  - L233: - [ ] Before fabricating RM-M-STUDY-CLOSET: complete the 60-minute seating mock-up, verify occupied cushion height, lumbar fit and bracket/blocking co
  - L247: - FX-M-BATH2-TUB: `haus route --fixture` refuses: no 1 1/4" vent cavity within its 42" arm, the arm held by the FS-M-WEST joist lines at y=208"/224" (
  - L256: - [ ] No check grades a run passing through a room's `ceiling_lining` layers (found at the sauna; design: `mep.run_in_ceiling_lining`, runs below the 
  - L267: - Frigidaire TWINSPAIRKIT 1/8" seam; LG LDTS5552S side-mount with no sub-top. Carpet backing thickness (Z-bar answer holds to 0.10"); Mohawk on the 3/
  - L281: - Kitchen sink fabrication hold: dry-fit KHU100-32 / Bolden KPF-1610SFS / Badger 5 / Dearborn P9703WBG in the 36-inch SEKTION. Verify delivered Badger
  - L325: - **`RL-A-FLIGHT-GUARD` newel junction (not graded).** Near the 25'-5 1/8" newel its post (top 20'-2 1/4") and top rail run into `FO-A-STAIR`'s trimme
  - L334: - **FS-M-NE truss order (decision #112).** 16" o.c. is a published TRIFORCE OJ418S read (p. 5, 40/25 psf L/480, 18'-0"), so this is a stock order plus
  - L336: - **W-B-N2 wall-top restraint (Minn. R. 1309.0404).** `FO-M-STAIR` fills the first three joist spaces against W-B-N2 for x 10'-3"..17'-6", so no footn

## F3: Floor framing, rim, subfloor, floor openings, the finished-floor datum chain

- **Start:** `packages/engine/src/typehaus/resolve/floor*.py`, `packages/engine/src/typehaus/resolve/construction_rim.py`, `packages/engine/src/typehaus/resolve/construction_sills.py`, `houses/catlin/notes/floor_heights.md`, `houses/catlin/notes/main_floor_truss_basis.md` (15 files)
- **Prior ids (11):** F3-001, F3-002, F3-003, F3-004, F3-005, F3-006, F3-007, F3-008, F3-009, F3-010, F3-011
- **Sheets:** S-101.1 (p11), S-101.2 (p12), S-101.3 (p13), S-601 (p22), S-601.1 (p23), A-301 (p38), A-301.1 (p39), A-301.2 (p40), A-502 (p49), A-550 (p101), A-551 (p102), A-552 (p103), A-553 (p104), A-554 (p105), A-555 (p106), A-556 (p107), A-557 (p108), A-558 (p109), A-559 (p110), A-560 (p111), A-561 (p112), A-562 (p113), A-563 (p114), A-564 (p115), A-565 (p116), A-566 (p117), A-567 (p118), A-568 (p119), A-569 (p120), A-570 (p121), A-571 (p122), A-572 (p123), A-573 (p124), A-574 (p125), A-575 (p126), A-576 (p127), A-577 (p128), A-578 (p129), A-579 (p130), A-580 (p131), A-581 (p132), A-582 (p133), A-583 (p134), A-584 (p135)
- **Changed since round 1, look here first** (7 files): `houses/catlin/notes/main_floor_truss_basis.md` ±293, `houses/catlin/notes/floor_heights.md` ±132, `packages/engine/src/typehaus/resolve/floor_strongbacks.py` ±77, `packages/engine/src/typehaus/resolve/floor_openings.py` ±42, `packages/engine/src/typehaus/resolve/floors.py` ±36, `packages/engine/src/typehaus/resolve/floor_ends.py` ±25, `packages/engine/src/typehaus/resolve/construction_sills.py` ±9
- **TODO lines (keyword match):**
  - L160: I-joist/floor-truss deck would need a manufacturer's hung-header table this engine doesn't
  - L161: have, so catlin (all I-joist/floor-truss decks) sees no saving from it. **Still open:**
  - L223: - Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam
  - L238: - [ ] `D-B-SUNKEN` band header (structural project): load takedown for the stacked D-S-BALCONY/D-M-PORCH jamb packs, their bearing interfaces, LVL ply
  - L240: - [ ] RF-HOUSE birdsmouth notches the TJI 230 flange (C3-E5).
  - L243: - [ ] C3-E3 follow-up: the three exterior doors (D-M-ENTRY, D-M-PORCH, D-S-BALCONY) keep their RO base on the joist top, 3/4" under the subfloor the w
  - L247: - FX-M-BATH2-TUB: `haus route --fixture` refuses: no 1 1/4" vent cavity within its 42" arm, the arm held by the FS-M-WEST joist lines at y=208"/224" (
  - L248: - FX-S-SUITEBATH-LAV: refused, the take-off at (165.5", 268") rises into PR-S-SUITE-LAV-HW 25.75" over the arm; move that leg to y <= 266.36" (§9). -T
  - L252: - [ ] Doorway transitions: D-A-STUDY / D-A-POCKET open onto unfinished subfloor (`compatible_finish_pairs` can't name it); D-M-MECH's floor varies acr
  - L262: - Metal Sales / SFS: Profile Vent NFA under the 1" Image II clip, and per foot or per strip (R806 passes 562 vs 553 in2); a lower BBD75 panel stopped 
  - L266: - Broan: the derived 9 3/4" port 3-4 spacing; 8" flex on those centres. Weyerhaeuser: TJI 230 row assumes a glue-nailed subfloor. BuildBlock: BB600 co
  - L267: - Frigidaire TWINSPAIRKIT 1/8" seam; LG LDTS5552S side-mount with no sub-top. Carpet backing thickness (Z-bar answer holds to 0.10"); Mohawk on the 3/

## F4: Trusses and roof framing: shapes, heel, bearing, ridge, overhangs, girts

- **Start:** `packages/engine/src/typehaus/resolve/framing/truss_*.py`, `packages/engine/src/typehaus/resolve/roof_*.py`, `packages/engine/src/typehaus/resolve/rafter_seat.py`, `houses/catlin/notes/catlin_truss_engineering.md`, `houses/catlin/params/roof_*.py`, `houses/catlin/notes/ridge_beam_detail.md` (28 files)
- **Prior ids (10):** F4-001, F4-002, F4-003, F4-004, F4-005, F4-006, F4-007, F4-008, F4-009, F4-010
- **Sheets:** S-101.3 (p13), S-102.1 (p14), S-102.2 (p15), S-102.3 (p16), S-602 (p24), S-602.1 (p25), S-602.2 (p26), A-105 (p33), A-301 (p38), A-301.1 (p39), A-301.2 (p40), A-504 (p51), A-531 (p82), A-591 (p142), A-592 (p143), A-593 (p144), A-594 (p145), A-595 (p146), A-596 (p147), A-597 (p148)
- **Changed since round 1, look here first** (22 files): `packages/engine/src/typehaus/resolve/roof_soffit.py` ±171, `packages/engine/src/typehaus/resolve/roof_ridge_trim.py` ±108, `packages/engine/src/typehaus/resolve/roof_geometry.py` ±77, `packages/engine/src/typehaus/resolve/roof_trim.py` ±73, `packages/engine/src/typehaus/resolve/rafter_seat.py` ±68, `packages/engine/src/typehaus/resolve/roof_panel_skin.py` ±49, `packages/engine/src/typehaus/resolve/roof_layer_setbacks.py` ±47, `packages/engine/src/typehaus/resolve/roof_bearing.py` ±39, `packages/engine/src/typehaus/resolve/framing/truss_heel.py` ±36, `houses/catlin/params/roof_trim.py` ±36, `houses/catlin/notes/catlin_truss_engineering.md` ±33, `packages/engine/src/typehaus/resolve/roof_edge_geometry.py` ±29, `houses/catlin/notes/ridge_beam_detail.md` ±24, `packages/engine/src/typehaus/resolve/framing/truss_girts.py` ±16, `houses/catlin/params/roof_panel.py` ±12
- **TODO lines (keyword match):**
  - L118: current 1 ft ridge clearance, access pathways and array coverage against MN R324 and final
  - L119: roof geometry; pathways run eave-to-ridge across the slope, not along the ridge. DLI
  - L120: guidance calls for 36-inch pathways and, under the ordinary rule, an 18-inch ridge setback
  - L121: below 33% coverage or 36 inches above it. Study five modules along the ridge and a second
  - L160: I-joist/floor-truss deck would need a manufacturer's hung-header table this engine doesn't
  - L161: have, so catlin (all I-joist/floor-truss decks) sees no saving from it. **Still open:**
  - L227: - Check whether `RF-BW-CANOPY`'s 190 plf and `RF-GARAGE`'s 167.5 plf diaphragm rows already carry SDPWS-2015 Table 4.2A's specific-gravity factor (0.9
  - L232: - Plan limited mobility bathroom use on the main floor. Looks like full wheelchair clearance won't work, but look what we can add to make limited mobi
  - L240: - [ ] RF-HOUSE birdsmouth notches the TJI 230 flange (C3-E5).
  - L242: - [ ] Canopy truss bearing 2 3/4", heel lift, north-entry seat-beam hangers and shim pack (C3-E6/E7/E12-E14).
  - L327: - Backup battery, still open (`houses/catlin/notes/backup_power.md` §11-§12): EG4's UL 9540 certificate naming 12kPV + WallMount Indoor; how the 12kPV
  - L334: - **FS-M-NE truss order (decision #112).** 16" o.c. is a published TRIFORCE OJ418S read (p. 5, 40/25 psf L/480, 18'-0"), so this is a stock order plus

## F5: Foundation and concrete (incl. the concrete deck swap): footings, stems, slabs, ICF/CMU, rebar, cover, laps

- **Start:** `packages/engine/src/typehaus/resolve/concrete.py`, `packages/engine/src/typehaus/resolve/slab_*.py`, `packages/engine/src/typehaus/resolve/rebar/*`, `houses/catlin/plan/assemblies/foundation*.py`, `houses/catlin/plan/assemblies/footings*.py`, `houses/catlin/notes/rebar_layout_basis.md`, `houses/catlin/notes/sunken_garden_*.md` (21 files)
- **Prior ids (14):** F5-001, F5-002, F5-003, F5-004, F5-005, F5-006, F5-007, F5-008, F5-009, F5-010, F5-011, F5-012, F5-013, F5-014
- **Sheets:** C-101 (p7), S-001 (p8), S-001.1 (p9), S-100 (p10), A-501 (p48), A-509 (p56), A-585 (p136), A-586 (p137), A-587 (p138), A-588 (p139), A-589 (p140), A-590 (p141)
- **Changed since round 1, look here first** (9 files): `houses/catlin/notes/sunken_garden_court_free_body.md` ±185, `houses/catlin/notes/sunken_garden_veneer_beam.md` ±123, `houses/catlin/notes/rebar_layout_basis.md` ±58, `houses/catlin/plan/assemblies/footings.py` ±22, `houses/catlin/plan/assemblies/foundation.py` ±19, `packages/engine/src/typehaus/resolve/rebar/stock.py` ±18, `packages/engine/src/typehaus/resolve/rebar/mats.py` ±15, `houses/catlin/notes/sunken_garden_piers.md` ±6, `packages/engine/src/typehaus/resolve/rebar/beams.py` ±3
- **TODO lines (keyword match):**
  - L32: cold-weather placement and slab joint layout exist only in prose.
  - L61: - **Determine basement backwater protection before under-slab rough-in.** Add the next
  - L139: horizontals going borderline (0.148 vs 0.15 in²/ft) with a rotating footing. Free body §6c.
  - L239: - [ ] Garage sill 3 5/8" of 5 1/2" on the ICF core (C3-E8).
  - L243: - [ ] C3-E3 follow-up: the three exterior doors (D-M-ENTRY, D-M-PORCH, D-S-BALCONY) keep their RO base on the joist top, 3/4" under the subfloor the w
  - L251: - [ ] TB-SG-W1/E1 closure boards are 8" while FT-B-S2/S3 are now 10": 2" x 32" of strip faces the court footing with no board. Extend to 10" (moves §1
  - L257: - [ ] Window stools pass through the buck jambs (`framing|window_stool`, 34 pairs): notch in `geometry_millwork.window_stool_ring`. ST-G-SERVICE riser
  - L258: - [ ] FB-B-CS bedding's drain-tile ring (CFB011AAAA-DT-00/02) runs under FT-B-S2/S3 to y=0: 1" clear before, 1" into them since S2/S3 went to 10" (`dr
  - L263: - DAKAM: Alucover operable sill rail height and sash overlap (author `WindowType.sill_rail_height` / `sash_overlap`). Andersen dealer: the 400 casemen
  - L265: - **Engineer hold, 14" north-entry pier cage (C3-E21):** PT-BW-W/-GW and PT-BW-PE/-PNE (`PIER_CONCRETE_14`, (4) #5) are 0.806% of gross, under ACI 318
  - L268: - Plumber: the attic WC's 1 1/2" vent (UPC 904.1); basement WC re-route under the slab to W-B-BA-E; moving BATH2's supplies and PR-B-HW-TRUNK for a ve
  - L283: - Oksana wants an elm slab sofa table

## F6: Exterior structures (incl. the concrete deck): decks, porch, canopy, north entry, balcony, posts, Simpson fit

- **Start:** `packages/engine/src/typehaus/library/hardware/*`, `packages/engine/src/typehaus/resolve/connector_geometry/*`, `houses/catlin/params/*deck*.py`, `houses/catlin/params/north_entry*.py`, `houses/catlin/notes/north_entry_*.md`, `houses/catlin/notes/balcony_*.md`, `docs/simpson-*-geometry.md` (40 files)
- **Prior ids (8):** F6-001, F6-002, F6-003, F6-004, F6-005, F6-006, F6-007, F6-008
- **Sheets:** S-001 (p8), S-001.1 (p9), S-100 (p10), S-102.1 (p14), S-602 (p24), S-602.1 (p25), S-602.2 (p26), S-603 (p27), A-508 (p55), A-509 (p56)
- **Changed since round 1, look here first** (19 files): `houses/catlin/params/main_deck.py` ±537, `houses/catlin/notes/north_entry_piers.md` ±210, `houses/catlin/notes/balcony_moment_columns.md` ±86, `packages/engine/src/typehaus/library/hardware/simpson_hangers_lus.py` ±74, `houses/catlin/params/north_entry_frame.py` ±68, `packages/engine/src/typehaus/resolve/connector_geometry/hangers.py` ±66, `houses/catlin/notes/balcony_fascia_mounts.md` ±64, `packages/engine/src/typehaus/resolve/connector_geometry/placement.py` ±51, `houses/catlin/params/second_deck.py` ±47, `packages/engine/src/typehaus/library/hardware/roof_ties.py` ±23, `houses/catlin/notes/balcony_irrigation.md` ±23, `houses/catlin/notes/north_entry_structure.md` ±15, `packages/engine/src/typehaus/resolve/connector_geometry/ties.py` ±12, `packages/engine/src/typehaus/library/hardware/simpson_hangers.py` ±12, `houses/catlin/notes/balcony_differential_movement.md` ±12
- **TODO lines (keyword match):**
  - L19: - **D-G-SERVICE swing limited by W-BW-SCREEN after the canopy-beam move — owner to revisit (slide door, rebuild screen face).** Stopped at 81° for now
  - L28: (ASTM C1218), ASR x2 (the aggregate's C1293/C1260 result plus a C1778 structure class), SCM
  - L48: `mep.riser_through_deck` (undrawn holes) and the itemised web crossings, each with its count
  - L57: garage; power-on state of the D315S relays and the six-plus controllers; the Zigbee
  - L160: I-joist/floor-truss deck would need a manufacturer's hung-header table this engine doesn't
  - L161: have, so catlin (all I-joist/floor-truss decks) sees no saving from it. **Still open:**
  - L165: carries no support, hanger or guide field, so there is no spacing to measure. The governing
  - L168: Schedule 40 PVC with mid-story guides plus a 30 ft expansion interval against the new
  - L170: `PipeRun` plus a `mep.pipe_support` reading the material off the run — and is not needed to
  - L202: deck's own elevation faces cladding.** Below z=0 the house's south face is `W-B-BRICK`,
  - L204: the porch deck now stops on the brick's face). The two halves
  - L227: - Check whether `RF-BW-CANOPY`'s 190 plf and `RF-GARAGE`'s 167.5 plf diaphragm rows already carry SDPWS-2015 Table 4.2A's specific-gravity factor (0.9

## E1: Roof cladding and trim: panel coverage, drip edge, ridge, Image II, gutters, soffits

- **Start:** `packages/engine/src/typehaus/resolve/roof_panel_*.py`, `packages/engine/src/typehaus/resolve/roof_image_ii*.py`, `packages/engine/src/typehaus/resolve/roof_ridge_trim.py`, `packages/engine/src/typehaus/resolve/gutter_*.py`, `packages/engine/src/typehaus/library/trim/*`, `houses/catlin/notes/roof_*.md`, `houses/catlin/notes/box_gutter_sizing.md` (21 files)
- **Prior ids (10):** E1-001, E1-002, E1-003, E1-004, E1-005, E1-006, E1-007, E1-008, E1-009, E1-010
- **Sheets:** A-002 (p28), A-105 (p33), A-201 (p34), A-202 (p35), A-203 (p36), A-204 (p37), A-511 (p58), A-591 (p142), A-592 (p143), A-593 (p144), A-594 (p145), A-595 (p146), A-596 (p147), A-597 (p148)
- **Changed since round 1, look here first** (11 files): `packages/engine/src/typehaus/resolve/roof_ridge_trim.py` ±108, `houses/catlin/notes/roof_wall_eave_detail.md` ±75, `houses/catlin/notes/roof_wall_rake_detail.md` ±56, `packages/engine/src/typehaus/resolve/roof_panel_skin.py` ±49, `packages/engine/src/typehaus/library/trim/metal_sales.py` ±42, `packages/engine/src/typehaus/library/trim/_image_ii.py` ±28, `houses/catlin/notes/box_gutter_sizing.md` ±23, `packages/engine/src/typehaus/resolve/roof_image_ii.py` ±10, `packages/engine/src/typehaus/resolve/roof_panel_trim.py` ±7, `packages/engine/src/typehaus/resolve/roof_panel_hem.py` ±4, `packages/engine/src/typehaus/resolve/roof_image_ii_pan_end.py` ±4
- **TODO lines (keyword match):**
  - L118: current 1 ft ridge clearance, access pathways and array coverage against MN R324 and final
  - L119: roof geometry; pathways run eave-to-ridge across the slope, not along the ridge. DLI
  - L120: guidance calls for 36-inch pathways and, under the ordinary rule, an 18-inch ridge setback
  - L121: below 33% coverage or 36 inches above it. Study five modules along the ridge and a second
  - L253: - [ ] Leader straps bill twice: `CN-A-LEADER-*` (SS316 standoff strap #13, sized for the old 4" round) and the leader's 58110XX. Pick one product for 
  - L262: - Metal Sales / SFS: Profile Vent NFA under the 1" Image II clip, and per foot or per strip (R806 passes 562 vs 553 in2); a lower BBD75 panel stopped 
  - L274: - 05-001 Metal Sales: PBR jamb sticks, gutter end caps and straps (unpriced joins).
  - L303: - [x] Roof sheathing: 19/32" 40/20 plywood, CDX house and Structural I garage/canopy. [Assessment](../houses/catlin/notes/roof_sheathing_and_membranes
  - L305: - [ ] House eave/gutter, remaining after the geometry pass ([plan](roof-wall-eave-detail.md), [note](../houses/catlin/notes/roof_wall_eave_detail.md))
  - L306: - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the
  - L307: - Joints: eave and gutter splices, thermal movement, sealant/fastener schedule.
  - L309: - Snow protection: gutter front is about 2" above the snow-slide line.

## E2: Wall cladding (incl. entry-screen MDO): board-batten, PBR, brick, rainscreen, closures, corner trim

- **Start:** `packages/engine/src/typehaus/resolve/board_batten.py`, `packages/engine/src/typehaus/resolve/rainscreen_*.py`, `packages/engine/src/typehaus/resolve/cladding_trim/*`, `houses/catlin/params/cladding.py`, `houses/catlin/plan/masonry_joints.py`, `houses/catlin/plan/entry_screen_*.py`, `houses/catlin/plan/products_entry_screen.py`, `houses/catlin/notes/entry_screen_*.md`, `houses/catlin/notes/board_batten_girt_span.md` (24 files)
- **Prior ids (9):** E2-001, E2-002, E2-003, E2-004, E2-005, E2-006, E2-007, E2-008, E2-009
- **Sheets:** A-002 (p28), A-201 (p34), A-202 (p35), A-203 (p36), A-204 (p37), A-503 (p50), A-513 (p62), A-513.1 (p63), A-513.2 (p64), A-535 (p86), A-536 (p87), A-537 (p88), A-554 (p105), A-555 (p106), A-556 (p107), A-557 (p108), A-558 (p109), A-559 (p110), A-560 (p111), A-561 (p112), A-588 (p139), A-589 (p140)
- **Changed since round 1, look here first** (10 files): `houses/catlin/plan/entry_screen_finish_spec.py` ±169, `houses/catlin/notes/entry_screen_mdo.md` ±138, `houses/catlin/plan/entry_screen_finish_checks.py` ±113, `houses/catlin/notes/board_batten_girt_span.md` ±66, `packages/engine/src/typehaus/resolve/rainscreen_strips.py` ±48, `houses/catlin/plan/masonry_joints.py` ±43, `packages/engine/src/typehaus/resolve/cladding_trim/wall_tops.py` ±23, `houses/catlin/plan/products_entry_screen.py` ±22, `packages/engine/src/typehaus/resolve/cladding_trim/openings.py` ±15, `houses/catlin/notes/entry_screen_metal_cassettes.md` ±15
- **TODO lines (keyword match):**
  - L23: - **Blind ROs export as full-depth IFC voids** (`AO-BW-MDO-TIE-RELIEF`, `AO-M-FIRE-NICHE`,
  - L35: now carry `ResolvedJunction.sheathing_through`, which a layout pass would read. Cladding, WRB,
  - L201: - **OPEN: `_y_in_n` is datumed off the ABOVE-GRADE cladding face, and nothing at the porch
  - L202: deck's own elevation faces cladding.** Below z=0 the house's south face is `W-B-BRICK`,
  - L203: which stands **2.375" south of that line** (cladding -7.25", brick -9.625" since 2026-11-04;
  - L222: - A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairw
  - L251: - [ ] TB-SG-W1/E1 closure boards are 8" while FT-B-S2/S3 are now 10": 2" x 32" of strip faces the court footing with no board. Extend to 10" (moves §1
  - L262: - Metal Sales / SFS: Profile Vent NFA under the 1" Image II clip, and per foot or per strip (R806 passes 562 vs 553 in2); a lower BBD75 panel stopped 
  - L274: - 05-001 Metal Sales: PBR jamb sticks, gutter end caps and straps (unpriced joins).
  - L288: - House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and inst
  - L306: - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the
  - L324: - Rainscreen closures (2026-10-29): close the supplier questions in `houses/catlin/notes/metal_trim_kit.md` "Open with suppliers" (Metal Sales x4, the

## I1: Kitchen: SEKTION carcasses, fronts, fillers, countertops, appliance cutouts, sink

- **Start:** `packages/engine/src/typehaus/library/placeables/sektion*.py`, `houses/catlin/plan/kitchen_*.py`, `houses/catlin/plan/products_ikea.py`, `houses/catlin/plan/countertops.py`, `houses/catlin/notes/ikea_sektion_*.md`, `houses/catlin/notes/kitchen_*.md` (13 files)
- **Prior ids (8):** I1-001, I1-002, I1-003, I1-004, I1-005, I1-006, I1-007, I1-008
- **Sheets:** A-002 (p28), A-102 (p30), A-603 (p152)
- **Changed since round 1, look here first** (11 files): `houses/catlin/plan/kitchen_casework.py` ±75, `houses/catlin/notes/kitchen_stock_cabinet_details.md` ±57, `houses/catlin/plan/countertops.py` ±38, `houses/catlin/plan/products_ikea.py` ±29, `houses/catlin/plan/kitchen_front_types.py` ±23, `packages/engine/src/typehaus/library/placeables/sektion.py` ±14, `packages/engine/src/typehaus/library/placeables/sektion_parts.py` ±9, `houses/catlin/notes/kitchen_sink_installation.md` ±8, `houses/catlin/notes/ikea_sektion_ladder.md` ±7, `houses/catlin/plan/kitchen_deep_cabinets.py` ±4, `houses/catlin/notes/ikea_sektion_order.md` ±1
- **TODO lines (keyword match):**
  - L109: kitchen sink and dishwasher (49.5 ft). Price ½-inch alternatives and check fixture demand,
  - L112: the kitchen. Shorter waits and less cooled water may save energy; quantify with actual use
  - L281: - Kitchen sink fabrication hold: dry-fit KHU100-32 / Bolden KPF-1610SFS / Badger 5 / Dearborn P9703WBG in the 36-inch SEKTION. Verify delivered Badger
  - L334: - **FS-M-NE truss order (decision #112).** 16" o.c. is a published TRIFORCE OJ418S read (p. 5, 40/25 psf L/480, 18'-0"), so this is a stock order plus
  - L337: - **Tile medallions: not this pass (review 2026-11-01).** Any tile forces an underlay under all the LVP (~0.47" more finish: re-derive ST-M2S/ST-B2M r

## I2: Baths: fixtures, vanities, tub and shower, tile, accessories, mirrors

- **Start:** `packages/engine/src/typehaus/library/placeables/fixtures.py`, `packages/engine/src/typehaus/resolve/tub_enclosures.py`, `houses/catlin/plan/fixture_types*.py`, `houses/catlin/plan/products_bath_lavs.py`, `houses/catlin/plan/products_showering.py`, `houses/catlin/notes/bath*.md` (14 files)
- **Prior ids (10):** I2-001, I2-002, I2-003, I2-004, I2-005, I2-006, I2-007, I2-008, I2-009, I2-010
- **Sheets:** A-002 (p28), A-401.1 (p41), A-401.2 (p42), A-401.3 (p43), A-401.4 (p44), A-401.5 (p45), A-401.6 (p46), A-507 (p54), A-603 (p152)
- **Changed since round 1, look here first** (4 files): `houses/catlin/notes/bath2_lighting.md` ±84, `houses/catlin/plan/products_showering.py` ±18, `houses/catlin/plan/fixture_types_wc.py` ±17, `houses/catlin/notes/bath2_shower.md` ±16
- **TODO lines (keyword match):**
  - L56: enclosed/damp rating; Waveform tubes are Type B double-ended; GL-C-001P cold rating in the
  - L78: are front-access; three high heads require a ladder. The bath-2 stall-dryer intake now
  - L95: - **Router port stub is unpriced** (decision #95): its length and bend are not in a proposal's
  - L107: - **Pressure-check smaller hot-water branches before rough-in.** `PR-B-HW-BATH1` is a
  - L113: and HPWH performance. Do not resize shared bath/tub trunks without a separate demand
  - L197: - **`SF-B-BATH` stays, and not for want of numbers** — its three runs clear the 6'-8"
  - L198: headroom line by ~7 1/2" and a declaration on `RM-B-BATH` would pass. Nobody has decided a
  - L199: bathroom ceiling should be open. That is a design question, not a cleanup.
  - L210: - Figure out a space for a cat litter box. Options: either a cat door on the current vanity planned (no change) or a wall mounted sink leaving space f
  - L223: - Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam
  - L224: - Around bathrooms and bedrooms we want higher STC. Around major hallways and stairs we want abuse resistance (but only need it on the lower 4' above 
  - L230: - Perhaps mount the espalier posts on sonotubes to increase the lifespan of the posts.

## I3: Built-in millwork and furniture: bookcases, benches, wardrobes, closets, study booth, sauna

- **Start:** `packages/engine/src/typehaus/model/millwork*.py`, `packages/engine/src/typehaus/resolve/millwork.py`, `houses/catlin/plan/millwork*.py`, `houses/catlin/plan/study_*.py`, `houses/catlin/plan/sauna*.py`, `houses/catlin/notes/study_*.md`, `houses/catlin/notes/sauna_*.md` (16 files)
- **Prior ids (8):** I3-001, I3-002, I3-003, I3-004, I3-005, I3-006, I3-007, I3-008
- **Sheets:** A-103 (p31), A-104 (p32), A-401.2 (p42), A-505 (p52), A-506 (p53), A-603 (p152)
- **Changed since round 1, look here first** (13 files): `packages/engine/src/typehaus/model/millwork.py` ±49, `houses/catlin/notes/study_bookcase_bridge.md` ±37, `houses/catlin/plan/millwork.py` ±15, `houses/catlin/plan/study_bridge.py` ±13, `houses/catlin/plan/sauna_types.py` ±9, `houses/catlin/notes/sauna_basement_wall_detail.md` ±8, `packages/engine/src/typehaus/resolve/millwork.py` ±7, `houses/catlin/notes/sauna_seating.md` ±7, `houses/catlin/plan/study_nook_types.py` ±2, `houses/catlin/plan/study_nook.py` ±2, `houses/catlin/plan/study_booth_types.py` ±2, `houses/catlin/notes/study_booth.md` ±2, `houses/catlin/notes/sauna_shower_basement_detail.md` ±2
- **TODO lines (keyword match):**
  - L72: ProSaunas vent hatch's cutout and free area (unpublished; (844) 565-1113).
  - L116: - **Make the PV layout comply with roof access, then study a second row.** `params/solar.py`
  - L121: below 33% coverage or 36 inches above it. Study five modules along the ridge and a second
  - L218: touch a tag (PANTRY/D8, STUDY/D13, MECH's "CHASE TYP. OF 2"), and on the 11x17 reduced check
  - L229: - Wall W-A-GC-S and it's matching south pair should have bookshelves against them, likely custom to fix the short triangle present there. In between t
  - L233: - [ ] Before fabricating RM-M-STUDY-CLOSET: complete the 60-minute seating mock-up, verify occupied cushion height, lumbar fit and bracket/blocking co
  - L252: - [ ] Doorway transitions: D-A-STUDY / D-A-POCKET open onto unfinished subfloor (`compatible_finish_pairs` can't name it); D-M-MECH's floor varies acr
  - L256: - [ ] No check grades a run passing through a room's `ceiling_lining` layers (found at the sauna; design: `mep.run_in_ceiling_lining`, runs below the 
  - L257: - [ ] Window stools pass through the buck jambs (`framing|window_stool`, 34 pairs): notch in `geometry_millwork.window_stool_ring`. ST-G-SERVICE riser
  - L273: - 15-001 Sauna: tile-on-shiplap substrate and membrane detail.
  - L333: - O-S-VANITY and D-S-STUDY2, both openings (not true doors) seem to get ignored, improperly showing baseboard, sill plates, and non-continuous floorin

## I4: Drywall, finishes, the PaintStandard (#113), vinyl/LVP and carpet stacks, ceilings, drywall trims, transitions

- **Start:** `packages/engine/src/typehaus/resolve/drywall_*.py`, `packages/engine/src/typehaus/resolve/ceilings.py`, `packages/engine/src/typehaus/resolve/room_floor.py`, `packages/engine/src/typehaus/resolve/room_paint.py`, `packages/engine/src/typehaus/model/paint.py`, `packages/engine/src/typehaus/resolve/layer_bands.py`, `packages/engine/src/typehaus/resolve/doorway_floors.py`, `houses/catlin/plan/drywall.py`, `houses/catlin/plan/transitions.py`, `houses/catlin/plan/paint.py`, `houses/catlin/plan/doorway_transitions.py`, `houses/catlin/notes/lvp_flooring.md`, `houses/catlin/notes/paint_selection.md` (15 files)
- **Prior ids (10):** I4-001, I4-002, I4-003, I4-004, I4-005, I4-006, I4-007, I4-008, I4-009, I4-010
- **Sheets:** A-002 (p28), A-101 (p29), A-102 (p30), A-103 (p31), A-104 (p32), A-541 (p92), A-542 (p93), A-543 (p94), A-544 (p95), A-545 (p96), A-546 (p97), A-550 (p101), A-603 (p152), A-604 (p153)
- **Changed since round 1, look here first** (13 files): `houses/catlin/notes/lvp_flooring.md` ±218, `houses/catlin/plan/transitions.py` ±182, `houses/catlin/plan/doorway_transitions.py` ±156, `houses/catlin/notes/paint_selection.md` ±110, `packages/engine/src/typehaus/resolve/room_paint.py` ±88, `packages/engine/src/typehaus/model/paint.py` ±77, `packages/engine/src/typehaus/resolve/drywall_trims.py` ±33, `packages/engine/src/typehaus/resolve/ceilings.py` ±26, `packages/engine/src/typehaus/resolve/drywall_led.py` ±19, `houses/catlin/plan/paint.py` ±19, `packages/engine/src/typehaus/resolve/drywall_trim_edges.py` ±15, `houses/catlin/plan/drywall.py` ±12, `packages/engine/src/typehaus/resolve/layer_bands.py` ±2
- **TODO lines (keyword match):**
  - L16: - **Cotton Oak LVP (Karndean AKP-RL38):** get a local quote (the `lvp` row in `prices.toml` is
  - L18: `#d6cebb` (`houses/catlin/notes/lvp_flooring.md`).
  - L42: do not, if wanted. Place them before drywall, on the AP rollout's pattern (type,
  - L156: - **A `floor:ceiling_channel` rule adds no ceiling depth.** `RM-B-PLAY-N`'s resilient channel
  - L157: (`CR-PLAY-CEIL-RC`) bills LF only; the finished ceiling is ~1/2" lower than R305 and the
  - L158: register/ceiling-plane checks read (`houses/catlin/notes/theater_ceiling_acoustics.md`).
  - L163: `structural.floor_opening_header` only reports past the prescriptive 8' ceiling.
  - L179: - Render transition/detail overlays from the resolved junctions. `Transition` stays
  - L199: bathroom ceiling should be open. That is a design question, not a cleanup.
  - L220: - The theater, RM-B-PLAY-N is specified as carpet, and should have a heating strip under the carpet near the sofa where feet are, likely just plugged 
  - L222: - A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairw
  - L223: - Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam

## M1: Ducts, air side of the equipment: ERV B210E75RT port grid, plenums, manifolds, trunks, risers, OA/EA wraps and hoods

- **Start:** `packages/engine/src/typehaus/library/hvac*.py`, `packages/engine/src/typehaus/resolve/duct_*.py`, `packages/engine/src/typehaus/resolve/mep_ducts.py`, `houses/catlin/plan/mep_erv_*.py`, `houses/catlin/plan/mep_hvac*.py`, `houses/catlin/plan/products_air.py`, `houses/catlin/notes/erv_*.md`, `houses/catlin/notes/mep_duct_routing_basis.md`, `houses/catlin/notes/air_distribution_products.md` (18 files)
- **Prior ids (5):** M1-001, M1-004, M1-006, M1-007, M1-009
- **Sheets:** G-005 (p6), A-402 (p47), M-101 (p162), M-102 (p163), M-103 (p164), M-104 (p165)
- **Changed since round 1, look here first** (12 files): `houses/catlin/plan/mep_erv_l1.py` ±131, `houses/catlin/plan/mep_hvac.py` ±112, `houses/catlin/plan/products_air.py` ±68, `houses/catlin/plan/mep_erv_l2.py` ±40, `houses/catlin/plan/mep_erv_types.py` ±33, `houses/catlin/notes/erv_static_budget.md` ±31, `packages/engine/src/typehaus/resolve/mep_ducts.py` ±28, `houses/catlin/notes/mep_duct_routing_basis.md` ±27, `houses/catlin/notes/air_distribution_products.md` ±27, `houses/catlin/plan/mep_erv_risers.py` ±26, `houses/catlin/plan/mep_hvac_branches.py` ±7, `houses/catlin/notes/erv_service_access.md` ±1
- **TODO lines (keyword match):**
  - L5: We generally want exact products specified (or standard/commodity sizes) so we can verify everything works together correctly.
  - L19: - **D-G-SERVICE swing limited by W-BW-SCREEN after the canopy-beam move — owner to revisit (slide door, rebuild screen face).** Stopped at 81° for now
  - L68: since 2026-10-29, so the meter set is the only possible check. `notes/water_service.md` §4.
  - L70: front-left, under the ERV case's 54" bottom), the HydroBoost riser's projection (r ~15", 2 1/4"
  - L71: off `D-B-CLOSET`'s 75-degree sweep) and the cord's length (`notes/water_service.md` §1); and the
  - L74: - **Filter and service access is only partly resolved; no reachability rule grades it.**
  - L75: System 1's 28x12x1 MERV 13 return filter is typed and reachable from the hall floor;
  - L76: the Broan ERV's exposed service door, published clearances, and high outdoor screen's ladder
  - L77: access are recorded in `houses/catlin/notes/erv_service_access.md`. Gree wall-head screens
  - L83: General open item: grade filter-change/service envelopes and decide
  - L86: - **The ERV SUPPLY manifold still has no drawn feed, and the radon pipe is not the blocker.**
  - L88: gate. The binding gate is 2.7" between the EXH riser crown (y 409.8") and `DU-ERV-EA`'s wrap

## M4: Ducts, branches and fittings: every round and rectangular leg from trunk to terminal

- **Start:** `packages/engine/src/typehaus/resolve/duct_*.py`, `packages/engine/src/typehaus/resolve/terminal_*.py`, `packages/engine/src/typehaus/resolve/mep_fitting*.py`, `packages/engine/src/typehaus/resolve/mep_soffit.py`, `houses/catlin/plan/mep_erv_l*.py`, `houses/catlin/plan/mep_registers.py`, `houses/catlin/plan/air_terminal_types.py`, `houses/catlin/notes/mep_duct_routing_basis.md` (13 files)
- **Prior ids (4):** M1-002, M1-003, M1-005, M1-008
- **Sheets:** A-402 (p47), M-101 (p162), M-102 (p163), M-103 (p164), M-104 (p165)
- **Changed since round 1, look here first** (9 files): `houses/catlin/plan/mep_registers.py` ±133, `houses/catlin/plan/mep_erv_l1.py` ±131, `packages/engine/src/typehaus/resolve/mep_fitting_direction.py` ±117, `packages/engine/src/typehaus/resolve/terminal_necks.py` ±92, `houses/catlin/plan/air_terminal_types.py` ±69, `packages/engine/src/typehaus/resolve/mep_fittings.py` ±55, `packages/engine/src/typehaus/resolve/terminal_connections.py` ±41, `houses/catlin/plan/mep_erv_l2.py` ±40, `houses/catlin/notes/mep_duct_routing_basis.md` ±27
- **TODO lines (keyword match):**
  - L5: We generally want exact products specified (or standard/commodity sizes) so we can verify everything works together correctly.
  - L80: against the selected grille holder. A ladder below the high intake screen temporarily
  - L90: conduits in it), 1.4" south of EXH, 0.9" north of EA. A 6" stock duct needs 6". Levers:
  - L124: as feasible. Request incremental installed pricing and site-specific production estimates.
  - L158: register/ceiling-plane checks read (`houses/catlin/notes/theater_ceiling_acoustics.md`).
  - L196: - **`Material.product_ref` was NOT set, and it is not an oversight.** The plan called for a `Product` record naming the GCP datasheet so the BOM row r
  - L211: - **A library catalog type cannot name a house-owned `Product`.** `ED-T-EV-1450` lives in
  - L212: `library/electrical.py` and the Leviton 1450R is authored in `houses/catlin/plan/products.py`,
  - L213: so the `product_ref` cannot be made: `houses/starter` would resolve it to nothing and take an
  - L214: `integrity.unknown_product_ref` ERROR. Same seam as the Bituthene selection. Needs a
  - L223: - Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam
  - L244: - Left open by the 2026-11-01 fit and product-data pass (REPORT items 14-24; plan `make-a-plan-to-warm-otter`):

## M2: Plumbing supply: PEX and copper, the HW header (Uponor LF2821050) and branches, sleeves, insulation, bores

- **Start:** `packages/engine/src/typehaus/library/fittings.py`, `packages/engine/src/typehaus/resolve/pipe_sections.py`, `packages/engine/src/typehaus/resolve/mep_sleeves.py`, `houses/catlin/plan/mep_supply*.py`, `houses/catlin/plan/mep_sleeves.py`, `houses/catlin/plan/wet_ports.py`, `houses/catlin/plan/lav_ports.py`, `houses/catlin/notes/water_service.md`, `houses/catlin/notes/plant_supply_connection.md` (13 files)
- **Prior ids (4):** M2-001, M2-005, M2-008, M2-009
- **Sheets:** A-401.1 (p41), A-401.2 (p42), A-401.3 (p43), A-401.4 (p44), A-401.5 (p45), A-401.6 (p46), A-402 (p47), P-101 (p154), P-102 (p155), P-103 (p156), P-104 (p157)
- **Changed since round 1, look here first** (9 files): `houses/catlin/plan/mep_supply.py` ±388, `houses/catlin/notes/water_service.md` ±183, `houses/catlin/plan/mep_sleeves.py` ±112, `houses/catlin/plan/mep_supply_header.py` ±86, `houses/catlin/notes/plant_supply_connection.md` ±83, `houses/catlin/plan/mep_supply_devices.py` ±44, `houses/catlin/plan/mep_supply_branches.py` ±32, `houses/catlin/plan/mep_supply_plant.py` ±30, `packages/engine/src/typehaus/resolve/pipe_sections.py` ±17
- **TODO lines (keyword match):**
  - L86: - **The ERV SUPPLY manifold still has no drawn feed, and the radon pipe is not the blocker.**
  - L103: ventilation-only watts and annual runtime, then price a balanced dedicated supply
  - L107: - **Pressure-check smaller hot-water branches before rough-in.** `PR-B-HW-BATH1` is a
  - L108: ¾-inch copper branch serving one basin (8.8 ft); `PR-B-HW-KITCH` is ¾-inch copper for the
  - L109: kitchen sink and dishwasher (49.5 ft). Price ½-inch alternatives and check fixture demand,
  - L114: calculation. [EPA hot-water distribution guidance](https://www.epa.gov/watersense/watersense-labeled-homes-hot-water).
  - L118: current 1 ft ridge clearance, access pathways and array coverage against MN R324 and final
  - L119: roof geometry; pathways run eave-to-ridge across the slope, not along the ridge. DLI
  - L120: guidance calls for 36-inch pathways and, under the ordinary rule, an 18-inch ridge setback
  - L159: - **R502.10.1's single-member header allowance is sawn-lumber only, deliberately** — an
  - L160: I-joist/floor-truss deck would need a manufacturer's hung-header table this engine doesn't
  - L162: nothing grades a single-member header against a span table at all —

## M5: Plumbing DWV and vents: slope, 3D vents, trap arms, cleanouts, wet vents, the 3 unvented fixtures

- **Start:** `packages/engine/src/typehaus/resolve/mep_slope.py`, `packages/engine/src/typehaus/resolve/mep_trap_arm.py`, `packages/engine/src/typehaus/resolve/drainage*.py`, `packages/engine/src/typehaus/resolve/cleanout*.py`, `packages/engine/src/typehaus/resolve/vent_termination.py`, `houses/catlin/plan/mep_drainage.py`, `houses/catlin/plan/mep_venting.py`, `houses/catlin/plan/mep_vent_tees.py`, `houses/catlin/plan/mep_cleanouts.py`, `houses/catlin/notes/mep_drain_routing_basis.md`, `houses/catlin/notes/wet_vent_basis.md`, `houses/catlin/notes/vent_grade_basis.md` (14 files)
- **Prior ids (5):** M2-002, M2-003, M2-004, M2-006, M2-007
- **Sheets:** A-401.1 (p41), A-401.2 (p42), A-401.3 (p43), A-401.4 (p44), A-401.5 (p45), A-401.6 (p46), P-101 (p154), P-102 (p155), P-103 (p156), P-104 (p157), P-201 (p158), P-202 (p159), P-203 (p160), P-204 (p161)
- **Changed since round 1, look here first** (9 files): `houses/catlin/notes/mep_drain_routing_basis.md` ±323, `packages/engine/src/typehaus/resolve/mep_trap_arm.py` ±260, `packages/engine/src/typehaus/resolve/cleanout_rules.py` ±208, `houses/catlin/plan/mep_drainage.py` ±196, `houses/catlin/plan/mep_vent_tees.py` ±143, `houses/catlin/plan/mep_venting.py` ±64, `houses/catlin/notes/wet_vent_basis.md` ±50, `houses/catlin/notes/vent_grade_basis.md` ±9, `houses/catlin/plan/mep_cleanouts.py` ±6
- **TODO lines (keyword match):**
  - L72: ProSaunas vent hatch's cutout and free area (unpublished; (844) 565-1113).
  - L87: Measured 2026-10-29: the radon is the NORTH pipe of `VR-M-STACK`'s pair and sits west of every
  - L101: `EQ-B-ERV.blower_interlock_ref` calls `EQ-S-HP1-AH` so ventilation reaches remote rooms
  - L103: ventilation-only watts and annual runtime, then price a balanced dedicated supply
  - L142: `platform._collinear_overlap`, `stacking._axis_match`, `construction_geometry._stack_overlap`
  - L146: they differ by 43.8mm (basement) / 57.0mm (garage) — 13 stack pairs stack in one pass and
  - L223: - Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam
  - L234: - Plant-room sink (replaces `PA-S-PLANT-WATER-STUB`): feasibility test reported 2026-11-03, awaiting the owner; `haus route --fixture` crashes on an e
  - L238: - [ ] `D-B-SUNKEN` band header (structural project): load takedown for the stacked D-S-BALCONY/D-M-PORCH jamb packs, their bearing interfaces, LVL ply
  - L246: - [ ] 3 drain fixtures have no 3D vent (`mep.trap_arm_developed` ADVISORY; C6-E7, wet-vent grading done):
  - L247: - FX-M-BATH2-TUB: `haus route --fixture` refuses: no 1 1/4" vent cavity within its 42" arm, the arm held by the FS-M-WEST joist lines at y=208"/224" (
  - L248: - FX-S-SUITEBATH-LAV: refused, the take-off at (165.5", 268") rises into PR-S-SUITE-LAV-HW 25.75" over the arm; move that leg to y <= 266.36" (§9). -T

## M3: Electrical and lighting: boxes, device heights vs trim, housings vs joist/ceiling depth, panels, conduit

- **Start:** `packages/engine/src/typehaus/resolve/device_boxes.py`, `packages/engine/src/typehaus/resolve/conduit_*.py`, `packages/engine/src/typehaus/library/electrical.py`, `packages/engine/src/typehaus/library/lighting.py`, `houses/catlin/plan/electrical*.py`, `houses/catlin/plan/products_lighting*.py`, `houses/catlin/plan/lighting_*.py`, `houses/catlin/plan/device_*.py`, `houses/catlin/plan/panel_*.py` (26 files)
- **Prior ids (11):** M3-001, M3-002, M3-003, M3-004, M3-005, M3-006, M3-007, M3-008, M3-009, M3-010, M3-011
- **Sheets:** E-101 (p166), E-102 (p167), E-103 (p168), E-104 (p169), E-201 (p170), E-202 (p171), E-203 (p172), E-204 (p173), E-601 (p174), E-602 (p175), E-603 (p176)
- **Changed since round 1, look here first** (21 files): `houses/catlin/plan/lighting_basement.py` ±496, `houses/catlin/plan/electrical.py` ±411, `houses/catlin/plan/lighting_second.py` ±366, `houses/catlin/plan/lighting_living.py` ±341, `houses/catlin/plan/lighting_garage.py` ±341, `houses/catlin/plan/lighting_main.py` ±336, `houses/catlin/plan/lighting_entry.py` ±208, `houses/catlin/plan/lighting_types.py` ±189, `houses/catlin/plan/lighting_types_decor.py` ±100, `houses/catlin/plan/lighting_attic.py` ±93, `houses/catlin/plan/products_lighting_selected.py` ±87, `houses/catlin/plan/electrical_branches.py` ±84, `houses/catlin/plan/panel_working_space.py` ±58, `houses/catlin/plan/products_lighting.py` ±51, `houses/catlin/plan/device_types.py` ±38
- **TODO lines (keyword match):**
  - L14: - **Sconce J/J1 (WAC Sprig BL-23210-BK):** confirm it can be hardwired. Output drops from
  - L19: - **D-G-SERVICE swing limited by W-BW-SCREEN after the canopy-beam move — owner to revisit (slide door, rebuild screen face).** Stopped at 81° for now
  - L54: the Fleurco MHAP4236's CRI (swap if under 90); the Soren 50910BK's UL damp label and box
  - L84: whether a reachability rule is worth a swing envelope; `Equipment.behind_access_panel` /
  - L85: `access_panel_ref` remain unused in catlin.
  - L90: conduits in it), 1.4" south of EXH, 0.9" north of EA. A 6" stock duct needs 6". Levers:
  - L91: relocate `EQ-M-ERV-MAN-SUP`, or re-pack the EA/EXH/conduit column.
  - L210: - Figure out a space for a cat litter box. Options: either a cat door on the current vanity planned (no change) or a wall mounted sink leaving space f
  - L222: - A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairw
  - L223: - Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam
  - L227: - Check whether `RF-BW-CANOPY`'s 190 plf and `RF-GARAGE`'s 167.5 plf diaphragm rows already carry SDPWS-2015 Table 4.2A's specific-gravity factor (0.9
  - L231: - W-BW-SCREEN's shear role is already redundant with the garage path (graded 100%). Relaxing its 4″ edge nailing needs the reviewer to accept `canopy_

## D1: Construction set, plans and schedules: dimension strings; door, window, hardware, framing schedules vs model

- **Start:** `packages/engine/src/typehaus/emit/draw/plan_dimensions.py`, `packages/engine/src/typehaus/emit/draw/dimension_rows.py`, `packages/engine/src/typehaus/emit/draw/framing_schedule.py`, `packages/engine/src/typehaus/emit/draw/schedules/*`, `packages/engine/src/typehaus/emit/draw/schedule_*.py` (20 files)
- **Prior ids (12):** D1-001, D1-002, D1-003, D1-004, D1-005, D1-006, D1-007, D1-008, D1-009, D1-010, D1-011, D1-012
- **Sheets:** G-001 (p1), G-001.1 (p2), G-002 (p3), G-003 (p4), G-004 (p5), G-005 (p6), S-100 (p10), S-101.1 (p11), S-101.2 (p12), S-101.3 (p13), S-102.1 (p14), S-102.2 (p15), S-102.3 (p16), S-103.1 (p17), S-103.2 (p18), S-103.3 (p19), S-103.4 (p20), S-601 (p22), S-601.1 (p23), S-602 (p24), S-602.1 (p25), S-602.2 (p26), S-603 (p27), A-101 (p29), A-102 (p30), A-103 (p31), A-104 (p32), A-105 (p33), A-601 (p149), A-601.1 (p150), A-602 (p151), A-603 (p152), A-604 (p153)
- **Changed since round 1, look here first** (18 files): `packages/engine/src/typehaus/emit/draw/schedules/openings.py` ±335, `packages/engine/src/typehaus/emit/draw/schedules/cover.py` ±242, `packages/engine/src/typehaus/emit/draw/schedules/structural_notes.py` ±207, `packages/engine/src/typehaus/emit/draw/schedules/paged_tables.py` ±157, `packages/engine/src/typehaus/emit/draw/schedules/cover_index.py` ±154, `packages/engine/src/typehaus/emit/draw/schedules/architectural.py` ±147, `packages/engine/src/typehaus/emit/draw/schedules/structural.py` ±135, `packages/engine/src/typehaus/emit/draw/plan_dimensions.py` ±123, `packages/engine/src/typehaus/emit/draw/schedule_plan_sheet.py` ±111, `packages/engine/src/typehaus/emit/draw/schedules/blocks.py` ±97, `packages/engine/src/typehaus/emit/draw/schedules/electrical.py` ±91, `packages/engine/src/typehaus/emit/draw/dimension_rows.py` ±72, `packages/engine/src/typehaus/emit/draw/schedules/paint.py` ±63, `packages/engine/src/typehaus/emit/draw/schedules/door_hardware.py` ±43, `packages/engine/src/typehaus/emit/draw/schedule_block.py` ±24
- **TODO lines (keyword match):**
  - L34: - **No sheet-layout engine**, so nothing checks a sheathing break landing on a stud. L corners
  - L55: offset (P6, 2026-11-02); CentricHOME R9 (the 2026-11-02 sheet says > 80, not 90+) and
  - L79: specifies an AAF PerfectPleat HC M8, nominal 10x10x1 filter; verify its actual dimensions
  - L96: cost terms, and the 2" fitting allowance is a stated value, not a datasheet one.
  - L128: datasheet idle (<55 W standby) and 94% maximum efficiency; both flatter a ~250 W outage
  - L154: - **R304.2's 7'-0" minimum room dimension is ungraded.** `code.R304_1_floor_area` and
  - L168: Schedule 40 PVC with mid-story guides plus a 30 ft expansion interval against the new
  - L196: - **`Material.product_ref` was NOT set, and it is not an oversight.** The plan called for a `Product` record naming the GCP datasheet so the BOM row r
  - L222: - A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairw
  - L233: - [ ] Before fabricating RM-M-STUDY-CLOSET: complete the 60-minute seating mock-up, verify occupied cushion height, lumbar fit and bracket/blocking co
  - L237: - Geometry & dimensional-accuracy review 2026-10-31 done: [report](geometry-review/REPORT.md) (244 findings; ~84 fixed). Open escalations, ranked (det
  - L286: - D-B-SUNKEN: separate brick reveal, widened RO, 5-1/2 inch concrete seat and a foam-bed Trex tread with fascia box sides (2026-11-04, §6 of the note)

## D2: Construction set, sections, elevations, details: datums, ground line, detail dimensions vs model

- **Start:** `packages/engine/src/typehaus/emit/draw/section*.py`, `packages/engine/src/typehaus/emit/draw/elevation*.py`, `packages/engine/src/typehaus/emit/draw/detail*.py`, `packages/engine/src/typehaus/emit/draw/datum.py`, `packages/engine/src/typehaus/emit/draw/winder_detail.py`, `packages/engine/src/typehaus/emit/draw/sheet_notes.py` (24 files)
- **Prior ids (15):** D2-001, D2-002, D2-003, D2-004, D2-005, D2-006, D2-007, D2-008, D2-009, D2-010, D2-011, D2-012, D2-013, D2-014, D2-015
- **Sheets:** S-501.1 (p21), A-201 (p34), A-202 (p35), A-203 (p36), A-204 (p37), A-301 (p38), A-301.1 (p39), A-301.2 (p40), A-501 (p48), A-502 (p49), A-503 (p50), A-504 (p51), A-505 (p52), A-506 (p53), A-507 (p54), A-508 (p55), A-509 (p56), A-510 (p57), A-511 (p58), A-512 (p59), A-512.1 (p60), A-512.2 (p61), A-513 (p62), A-513.1 (p63), A-513.2 (p64), A-514 (p65), A-515 (p66), A-531 (p82), A-532 (p83), A-533 (p84), A-534 (p85), A-535 (p86), A-536 (p87), A-537 (p88), A-538 (p89), A-539 (p90), A-550 (p101), A-551 (p102), A-552 (p103), A-553 (p104), A-554 (p105), A-555 (p106), A-556 (p107), A-557 (p108), A-558 (p109), A-559 (p110), A-585 (p136), A-586 (p137), A-587 (p138), A-588 (p139), A-589 (p140), A-590 (p141), A-591 (p142), A-592 (p143), A-593 (p144), A-594 (p145), A-595 (p146), A-596 (p147), A-597 (p148)
- **Changed since round 1, look here first** (14 files): `packages/engine/src/typehaus/emit/draw/details.py` ±406, `packages/engine/src/typehaus/emit/draw/detail_annotations.py` ±392, `packages/engine/src/typehaus/emit/draw/elevation_annotate.py` ±143, `packages/engine/src/typehaus/emit/draw/detail_anchors.py` ±141, `packages/engine/src/typehaus/emit/draw/section.py` ±121, `packages/engine/src/typehaus/emit/draw/elevation.py` ±116, `packages/engine/src/typehaus/emit/draw/section_callouts.py` ±109, `packages/engine/src/typehaus/emit/draw/detail_dimensions.py` ±109, `packages/engine/src/typehaus/emit/draw/section_labels.py` ±76, `packages/engine/src/typehaus/emit/draw/detail_enlarged.py` ±69, `packages/engine/src/typehaus/emit/draw/sheet_notes.py` ±56, `packages/engine/src/typehaus/emit/draw/detail_derive.py` ±33, `packages/engine/src/typehaus/emit/draw/section_truss.py` ±14, `packages/engine/src/typehaus/emit/draw/section_annotate.py` ±12
- **TODO lines (keyword match):**
  - L179: - Render transition/detail overlays from the resolved junctions. `Transition` stays
  - L237: - Geometry & dimensional-accuracy review 2026-10-31 done: [report](geometry-review/REPORT.md) (244 findings; ~84 fixed). Open escalations, ranked (det
  - L250: - Fitting detail: PR-M-LSINK-VENT and PR-M-BATH2-WC-VENT tee into the drain where CO-B-LSINK / CO-B-WC2-HEAD sit (solids overlap 32 / 86 cm^3, blessed
  - L273: - 15-001 Sauna: tile-on-shiplap substrate and membrane detail.
  - L275: - 01-001 DSI: does Saint Paul's 6" concrete / 4" aggregate driveway guidance apply to the modeled 4/8 section?
  - L286: - D-B-SUNKEN: separate brick reveal, widened RO, 5-1/2 inch concrete seat and a foam-bed Trex tread with fascia box sides (2026-11-04, §6 of the note)
  - L287: - D-S-BALCONY: catalog coordination replaces the schematic plate/wrapped trim with a digitized ZAI outline, composite returns and short AridDek boards
  - L288: - House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and inst
  - L305: - [ ] House eave/gutter, remaining after the geometry pass ([plan](roof-wall-eave-detail.md), [note](../houses/catlin/notes/roof_wall_eave_detail.md))
  - L306: - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the
  - L312: - Pg 288 of the book has a roof eave detail where the roof and drip flashing alone extend out about an inch (no metal or sheathing).
  - L325: - **`RL-A-FLIGHT-GUARD` newel junction (not graded).** Near the 25'-5 1/8" newel its post (top 20'-2 1/4") and top rail run into `FO-A-STAIR`'s trimme

## U1: UI viewer geometry: builders that rebuild geometry vs model.json. Ignore deliberate depth bias

- **Start:** `ui/src/three/builders/*`, `ui/src/three/roofGeometry.ts`, `ui/src/three/floorTruss.ts`, `ui/src/three/members.ts`, `ui/src/three/memberBox.ts` (44 files)
- **Prior ids (4):** U1-001, U1-002, U1-003, U1-004
- **Sheets:** —
- **Changed since round 1, look here first** (12 files): `ui/src/three/builders/openings.ts` ±526, `ui/src/three/builders/sceneStages.ts` ±312, `ui/src/three/builders/scene.ts` ±296, `ui/src/three/builders/openings.test.ts` ±111, `ui/src/three/memberBox.ts` ±37, `ui/src/three/builders/alarms.ts` ±34, `ui/src/three/builders/structure.ts` ±25, `ui/src/three/builders/site.ts` ±8, `ui/src/three/builders/stairFinish.ts` ±4, `ui/src/three/members.ts` ±3, `ui/src/three/builders/roomFloor.test.ts` ±2, `ui/src/three/builders/doorway.test.ts` ±2
- **TODO lines (keyword match):**
  - L12: owner-GC build (cash items alone look like $15–30k), and `[contingency]` 10% also applies on
  - L17: still Quincy's placeholder) and check a sample in the house light against the model's
  - L19: - **D-G-SERVICE swing limited by W-BW-SCREEN after the canopy-beam move — owner to revisit (slide door, rebuild screen face).** Stopped at 81° for now
  - L63: floors under UPC 710.1, and protect only affected low branches if required. The existing
  - L64: sewer-permit task records invert, not cover elevation. [UPC 710.1 guidance](https://forms.iapmo.org/email_marketing/codespotlight/2019/Oct17.htm)
  - L78: are front-access; three high heads require a ladder. The bath-2 stall-dryer intake now
  - L84: whether a reachability rule is worth a swing envelope; `Equipment.behind_access_panel` /
  - L90: conduits in it), 1.4" south of EXH, 0.9" north of EA. A 6" stock duct needs 6". Levers:
  - L91: relocate `EQ-M-ERV-MAN-SUP`, or re-pack the EA/EXH/conduit column.
  - L114: calculation. [EPA hot-water distribution guidance](https://www.epa.gov/watersense/watersense-labeled-homes-hot-water).
  - L120: guidance calls for 36-inch pathways and, under the ordinary rule, an 18-inch ridge setback
  - L125: [MN DLI solar guidance](https://www.dli.mn.gov/sites/default/files/pdf/fs_res_solar.pdf).

