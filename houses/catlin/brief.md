# Catlin House — Design Brief

The real house this tool exists for: a 36'x36' family house in Minnesota (climate zone 6)
with a basement, two full storeys and a habitable cathedral attic. Three more structures
stand apart from it, each across a gap:

- **Garage**, 4' north: freestanding, wood-framed on an ICF stem.
- **North entry**, between house and garage: a landing on piers under a canopy roof that is
  one plane with the garage roof.
- **Court**, 5" south: a freestanding concrete structure of three levels (sunken garden,
  porch, balcony) inside arched concrete garden walls. The balcony sits on two treated
  glulams carried by four 12" round cast corner columns, fixed at their bases.

- **Spatial program:** walkout basement (sauna opening onto the sunken garden, gym,
  playroom/theater, workshop, bath, furnace room, battery closet); open living, dining and
  kitchen on the main floor with a main-floor bedroom suite, powder room, laundry, mudroom
  and pantry; four bedrooms (one a suite), a study and the plant room upstairs; hot-roofed
  cathedral attic, partially finished (guest studio with its own bath, a small study,
  unfinished space and storage).
- **Structure discipline:** every outer dimension derives from clear 16" o.c. framing, one
  grid per facade struck from the outside sheathing corner. Three bearing lines (west wall,
  the x=18' centre wall, east wall) give 18' floor spans on every storey. The centre wall
  stacks from its footings to a structural ridge beam, so rafters are simple spans with no
  ties. Floors are 11 7/8" TJI 230, with 11 7/8" open-web trusses where services cross.
  House corners are four-stud, strength-first (the exterior foam carries the corner
  insulation); garage corners three-stud. Bracing is prescriptive IRC CS-WSP on every line.
- **Window rule of thumb (small windows align to stud bays; resize to fit):**
  - 14" RO fits between studs without breaking a stud line (tight but doable).
  - 30" RO max on non-load-bearing walls (one stud broken).
  - 27½" RO max on load-bearing walls (one stud broken, a jack each side).
- **Envelope:** 2x6 walls throughout on 15/32" CDX, plus **4" of exterior high-lift HFO
  closed-cell spray foam, one visit** (`notes/ccspf_spec.md`). The foam is the air, water
  and thermal plane, so there is no sheet WRB. One tier of flat KDAT girts on block
  standoffs carries the cladding over a vented, drained cavity
  (`notes/catlin_truss_engineering.md`); windows are outies. Every metal face is 24 ga PVDF
  Linen White: concealed-fastener board & batten on the north and south (gable) faces,
  exposed-fastener PBR on east and west, corrugated on the garage.
- **Roof:** 6:12 gable, ridge north-south, zero overhang, unvented hot roof:
  11 7/8" TJI rafters, 5" ccSPF under a 5/8" CDX deck plus a batt (flash-and-batt, no
  above-deck foam), self-adhered butyl membrane, standing seam. Garage and canopy roofs are
  4:12 standing seam with overhangs. Target: FORTIFIED Roof + Hail.
- **Basement:** poured walls, 8" except 10" on the east (under the 2x6 wall and the
  fireplace brick), with 4" exterior XPS and 2" XPS under the slab. PGH-class targets in
  `preferences.toml`.
- **Climate:** MN zone 6; design temps -15°F / 88°F; 50 psf ground snow; 115 mph wind,
  Exposure B.
- **Style:** simple gable forms, white metal skin, arched concrete garden walls.
- **Must-haves:** sauna with walkout to the sunken garden; south porch and balcony off the
  main and second floors; attic R305-compliant habitable space; 18' floor spans between
  bearing lines.
- **Dislikes:** gray-box walls (we show real framing); attached garage.
