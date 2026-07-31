# Catlin house — agent guide

This directory **is the state**: the house is defined by the editable plan source under
`plan/` plus the parametric modules under `params/`. Edit those; never edit `out/`
(generated). Read `brief.md` (intent) **and** `preferences.toml` (targets) before
proposing any design change.

## Project map
- `plan/manifest.py` — plain-Python assembler (NOT editable); wires modules + params.
- `plan/storeys/{basement,main,second,attic,garage}.py` — `# haus: editable` elements.
- `plan/assemblies.py`, `plan/site.py`, `plan/placeables.py` — editable assemblies/site/placeables.
- `plan/mep.py`, `plan/fixtures.py` — `# haus: editable` MEP + plumbing-fixture *instances*
  (so UI drags round-trip). Only explicit constructors here — no functions/generators.
- `plan/electrical.py` — `# haus: editable` electrical service upgrade: meter, backup
  enclosure, 240V/EV/spa devices, conduit trunks, NEC 210.52 fill receptacles.
- `plan/circuits.py` — the panel schedule (NOT editable: Circuits are schedule data, not
  geometry). Devices point at circuits via `circuit=`; `electrical.circuit_refs` reconciles.
- `plan/lighting.py` — `# haus: editable` luminaire/LED-run/control *instances*, room by
  room. Every light names its switch(es) in `controlled_by`; 24V runs name a `psu_ref`
  instead of a circuit. The `ED-*-LT` fixtures still live in `plan/mep.py` — they were
  re-typed in place from the old generic `ED-T-LIGHT` so their uids (and IFC GlobalIds)
  survived — and each is one corner of a grid completed here.
- `plan/lighting_types.py` — the `LuminaireType` catalog, schedule marks A–P (NOT
  editable: `frozenset` again). Marks must stay unique; the E-602 schedule is keyed on
  them. Also holds the two 24V supply types and the dimmer/timer switch types.
- `params/solar.py` — rooftop PV array (12 × 440 W on the gable ridge, computed max fit).
- `params/roof_trim.py` — the eave water chain on RF-HOUSE's west/east eaves: drip edge →
  box gutter → downspout, each piece's position derived from the one above it so the laps
  hold. RF-HOUSE has **no fascia** (continuous standing-seam skin ⇒ the resolver's corner
  trim), so every offset is measured off the corner trim's face, never a fascia's. The lap
  order is enforced by `packages/engine/tests/test_catlin_eave_water.py` — read it before
  moving any of these numbers.
- `library/placeables/*.py` (repo root, not this directory) — the shared FixtureType/
  ApplianceType/FurnitureType *catalog*, wired in by `plan/manifest.py`. NOT editable: it
  uses `frozenset(...)`, which the dialect forbids. Type libraries stay non-editable;
  movable instances that reference them live in the editable modules above. The house-local
  `plan/fixture_types.py` this line used to name was deleted in the `3d3973a` library
  dedupe; only `plan/furniture_types.py` (the two mudroom closets) is still house-local.
- `params/sunken_garden.py` — the freestanding arched porch/garden structure (math OK here).
- `params/foundations.py` — house footings, garage ICF stem + slab.
- `params/breezeway.py` — the enclosed breezeway: pads, piers, posts, deck, roof, glazing.
- `notes/*.md` — construction detail notes migrated from the original repo.

**Editability rule (enforced):** any UI-movable element (Furniture/Fixture/Appliance/
Equipment/Register/ElectricalDevice/Door/Window/Wall/Room/Node/Stair) must be authored in a
`# haus: editable` file, or its canvas edits can't be written back. The loader raises
`loader.uneditable_movable_element` (a hard build error) if one is authored in a non-editable
module. Params-generated geometry (no constructor to write back to) is exempt.

## House facts that must stay true
- Four structures: house, freestanding garage (4' north), freestanding sunken-garden/
  porch/balcony concrete structure (5" south gap), enclosed breezeway on freestanding 6x6
  posts spanning that 4' gap door-to-door (`params/breezeway.py`).
- **The garage storey datum is not the garage floor.** Its wood walls bear on the ICF stem
  at `GARAGE_STEM_REVEAL` (1'-10"), which is the `garage` storey elevation; the slab they
  enclose is poured at grade, 1'-10" lower, and filed on `main`. Anything that has to sit
  on the garage floor must say so explicitly — D-G-OVERHEAD carries the plan's only
  negative `sill_height` to reach it, and the stem becomes a grade beam flush with the slab
  under that door so there is no curb across it. Emitters read
  `emit/room_floor.py::room_floor_elevation` rather than the storey elevation for the same
  reason. Raising the stem means re-dropping the door: the tie is enforced by
  `test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade`.
- 36'x36' at sheathing; everything on the 16" o.c. module; exterior walls carry
  `alignment=face("sheathing-ext")` so the sheathing plane is the vertical datum (#43).
- The side-wall stack is 2x6 throughout — one `CATLIN_EXT_2X6` on main, second and
  attic, sheathing plane continuous, no stud-depth jog. Main-storey studs are LSL,
  the upper storeys standard dimensional 2x6 (a purchasing note recorded in the
  assembly's `source`, not a separate assembly).
- Bearing lines: west wall, center N-S wall (x=18'), east wall; 18' I-joist spans E-W.
- Attic is a habitable hot-roofed cathedral space: 5' knee walls E/W, gables N/S,
  ridge N-S, 4:12, **zero overhang**.
- **Structural ridge, not a rafter-tie roof.** `RB-HOUSE` bears continuously on the
  `W-A-C1/C2` bearing wall, which stacks unbroken to the footings. That is what makes the
  rafters simple spans and keeps thrust off the 5' knee walls. Opening that center line up
  without a beam under it dumps ~1.5 klf of thrust into knee walls that can take ~0.1.
- Window rules: 14" RO fits a stud bay (centre on a bay centre); 27" RO max bearing
  (centre on a stud line, jacks added); 42" RO max non-bearing (centre on a BAY CENTRE
  — it breaks two studs, so a stud-line centre breaks three and fails the module
  check). Resize windows to fit the grid, not vice versa. One type per width family —
  WT-1424, WT-1864 (the attic gable's juliet pair, head at 8'-0"), WT-2736,
  WT-3036 (north gables/hall), WT-4248 (the south-glazing size, head at 6'-8") —
  each family sharing the one height that fits its most constrained wall. Five sizes
  carry the whole house; the 18" family breaks one stud and so centres on a stud line,
  which is also what lets the juliet pair sit 32" apart instead of 48".
- Facade rules (2026-07-30 pass). Windows line up or they are not there:
  - **Columns.** The south face stacks four columns clean through main, second and
    attic (x 3'-4", 8'-8", 28'-0", 33'-4" — the attic's east pair sits 4" off because
    W-A-S4's grid starts at N-A-V1, not at x=18'). The north face stacks one three-storey
    column at x=28'-0" (WIN-M-KITCH / WIN-S-HALL-N / WIN-A-N2).
  - **Rows.** Where a column is impossible, the storey's own rhythm wins instead: the
    east face runs an exact 9'-0" beat on the second storey (WIN-S-STUDY3 leaves its
    survey station for this) and 8'-0"/7'-4" on the main, and stacking between them is
    deliberately abandoned. The kitchen stretch north of WIN-M-DIN-E2 stays blank.
  - **Head lines.** The west face puts every main and second head on one 6'-0" line —
    27" units at a 3'-0" sill, 14" units at 4'-0". The south face shares a 2'-8" sill.
  - **Gables** read symmetric about the ridge before they answer to anything below:
    that is why WIN-A-N1 stays at 7'-4" rather than stacking on WIN-S-STAIR-N.
  - WT-1424 does the work wherever a bigger unit will not fit — under the 4:12 rake and
    in the 5' knee walls, where its 2'-0" height is the only one that clears the plate.
- Exterior opening finish: every window in a clad wall ships a charcoal picture-frame
  casing (resolve/geometry_openings.py `exterior_trim`), and every opening in a clad
  wall — doors included — draws its frame/mullion/stile boxes in the same charcoal.
  Recolor = emit/gltf/palette.py `window_trim` + ui/src/three/members.ts
  `CATEGORY_COLOR.window_trim`, nothing else.

## The loop: edit → build → check → *look* → fix
```
haus build .            # -> out/model.json (+ IFC when ifcopenshell present)
haus check .            # integrity / code / structural findings
haus render --view plan # -> out/render/plan_*.png  — LOOK at what you made
haus ls --summary       # compact whole-plan digest
```
After any spatial edit, **render and look**. After assembly edits,
`haus explain <ASM> --card`.
