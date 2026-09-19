> Current north entry, 2026-09-10 (engineered pass, then an owner revision the same day):
> the canopy is FREESTANDING — `RF-BW-CANOPY`, three 24' trusses between two 3-ply 2x12 KDAT
> headers, the WEST one on two 6x6 KDAT columns over cast piers and the EAST one on
> full-height cast columns, bearing on the garage for nothing but the shared sheathing
> diaphragm. SIX piers on TWO depths: house-side −9'-9 7/16" (cast with the open basement
> excavation), garage-side −7'-0" (cast with the garage footings). The landing touches
> nothing on the house; the tiers are four CAST pours on a compacted base, no wood and no
> piers. The canopy BRACES ITSELF: `PT-BW-RE`/`-RNE` are full-height cast columns fixed at
> the base (east) and `W-BW-SCREEN` is a sheathed shear panel (west); the garage joint is a
> tied diaphragm, not the lateral system. `W-BW-SCREEN` is also the guard, with `SC-BW-WEST`
> a slat clerestory over it; `RL-BW-SCREEN` is retired.
> **2026-09-11: `D-G-SERVICE` is hard in the garage's SW corner** (RO 6'-7"..9'-7", centre
> x=8'-1", an inch off `D-M-ENTRY`), the landing narrowed to its east jamb (3'-7" wide, piers
> at x=6'-0"/9'-7"), the interior landing and `ST-G-SERVICE` stand against `W-G-W` with a
> wall-mounted handrail, `RL-BW-GARAGE-W` is gone, the two carrier-tip posts are 4x4 KDAT on
> `ABU44` standoffs reaching the beams, the stem gap under the door is closed, and
> `ED-M-ENTRY-LT` lights the entry landing. Garage +30in north; bridge composite finish 0; SL-G-STEP-0,
> pads, glazing and the six invented seat connectors retired; HP3 west in open yard. See
> notes/north_entry_structure.md (the bearing map), notes/north_entry_piers.md (the
> arithmetic) and notes/hp3_north_relocation.md.

# Catlin house — agent guide

This directory **is the state**: the house is defined by the editable plan source under
`plan/` plus the parametric modules under `params/`. Edit those; never edit `out/`
(generated). Read `brief.md` (intent) **and** `preferences.toml` (targets) before
proposing any design change. `DESIGN-LOG.md` holds the reasoning behind the numbers here
— derivations, rejected alternatives, engine bugs a rule exists to dodge. It is history,
not instruction: when it disagrees with this file or the model, it is the one that is wrong.

## Project map
- `plan/manifest.py` — plain-Python assembler (NOT editable); wires modules + params.
- `plan/storeys/{basement,main,second,attic,garage}.py` — `# haus: editable` elements.
- `plan/storeys/attic_studio.py` — `# haus: editable`, holds the west attic's
  guest studio: every new node, wall and door, `FO-A-HALL`, the three Rooms (including
  `RM-A-STUDIO`, which is `RM-A-WEST-UNFIN` moved here whole — **a uid follows the element,
  not the file**), `AL-A-STUDIO`, and the second-storey beam `BM-S-BATH-E` with its tee node.
  It feeds **two** storeys from one file, exporting `ATTIC_ELEMENTS` and `SECOND_ELEMENTS` —
  the `plan/mep_erv.py` precedent — because `attic.py` was already 565 lines against
  `AGENTS.md`'s 500. **What deliberately stayed in `attic.py`:** every WALL SPLIT the change
  forced — `W-A-C2`/`W-A-C2M`/`W-A-C2B`, `W-A-N2`/`W-A-N2B`, `W-A-W1`/`W-A-W1B` — so nobody
  reading a line has to look in two files for a segment of it, and `RB-HOUSE.bearing_refs`
  sits beside the walls it names.
- `plan/lighting_attic.py`, `plan/electrical_attic.py` — `# haus: editable`, split off for the
  same reason (`lighting.py` was 1,158 lines, `electrical.py` 1,700). Split
  by STOREY, which is how `plan/manifest.py` already consumes both. An editable file cannot
  `from plan import ...`, so the manifest composes; nothing imports across.
- `plan/assemblies.py`, `plan/site.py`, `plan/placeables.py` — editable assemblies/site/placeables.
- ⚠ **`params/sunken_garden.py` is ~4,480 lines against `AGENTS.md`'s 500, and it is the
  largest single violation in this house.** Logged 2026-09-14 rather than fixed: the file is
  under concurrent edit by more than one session, and a 4,000-line move is the one change
  where a merge silently keeps both halves of a constant. It is a real debt and the split is
  a pass of its own, on a quiet tree. The seams are already visible and the file's own
  section banners name them — the court's structure, its drainage, the thermal-break dowels,
  the porch enclosure, the leader and gutter run. Take the DRAINAGE half first: it is the
  most self-contained (`GARDEN_DRYWELL`, the four `FrenchDrain`s, the sleeve and the beam
  pipe) and the only one with no derived-elevation constants shared across the seam.
- `plan/mep*.py` — MEP *instances*, split by system so no file runs past ~400 lines:
  `mep_sleeves` (cast penetrations), `mep_drainage`, `mep_venting`, `mep_supply` +
  `mep_supply_devices`, `mep_hvac` (System 1's conditioned-air chase, equipment, terminal
  types), `mep_erv` + `mep_erv_types` (the ventilator, its manifolds, its outdoor side, its
  risers and radials), `mep_registers`, `mep_electrical` (symbols). All ten are
  `# haus: editable`. `plan/mep.py` itself is now only the four storey element lists the
  manifest consumes — NOT editable, because an aggregator needs `from plan import ...` and
  the dialect forbids it. **`mep_erv.py` cannot import `mep_erv_types.py`** for that same
  reason; the aggregator imports both and hands both to `Library(...)`.
- `plan/fixtures.py` — `# haus: editable` plumbing-fixture *instances* (so UI drags
  round-trip). Only explicit constructors in any of these — no functions/generators.
- `plan/electrical.py` — `# haus: editable` electrical service upgrade: meter, backup
  enclosure, 240V/EV/spa devices, conduit trunks, NEC 210.52 fill receptacles.
- `plan/equipment_types.py` — the equipment *catalog* (sauna heater, the three Gree
  heat-pump systems and their ratings tables, the garage heater). **NOT editable**, in the
  `plan/fixture_types.py` idiom: a type definition is never written back by a UI drag, and
  the heat-pump ratings tables need nesting and a wrapped `source=` that the editable
  dialect forbids. Split out of `electrical.py` (2,412 lines) 2026-09-18; the split moved
  `_content_hash` and nothing else in `model.json`. `electrical.py` is ~2,090 lines and
  still four times the 500-line guideline — recorded, not fixed.
- `plan/circuits.py` — the panel schedule (NOT editable: Circuits are schedule data, not
  geometry). Devices point at circuits via `circuit=`; `electrical.circuit_refs` reconciles.
  **BOTH MAIN-FLOOR WATER CLOSETS ARE BIDET TOILETS, AND THE ELECTRICAL FOR THEM IS TWO
  CIRCUITS THAT MUST NEVER BE GANGED.** `FX-M-BATH1-WC` is a TOTO SP wall-hung on a DuoFit
  carrier — **the carrier brand IS the bidet decision**, because only TOTO's frame carries
  the concealed WASHLET+ supply — and `FX-M-BATH2-WC` is a Carlyle II whose `AT40` suffix is
  that same readiness. Two WASHLET S5 seats ride on them (`plumbing-bidet-seats`, the seats
  only). `CKT-WASHLET-BATH1`/`-BATH2` at slots 25 and 28 feed `ED-M-BATH1-WC-RC` /
  `ED-M-BATH2-WC-RC`, one outlet each, GFCI at the DEVICE (a washlet trips a Class A GFCI
  now and then and a reset in the basement for a toilet seat is the failure mode the
  convention avoids), no AFCI (210.12 exempts bathrooms), `load_va=0`.
  - **Both boxes are in ONE stud bay and there is no second candidate.** `W-M-HS1` is the
    wet wall between the two baths and carries both bowls; the resolved framing leaves
    exactly one clear 2x6 cavity beside them, x 8 1/8"..15" between `stud-000` and the
    carrier's west king. Everything east is the 19 3/4" carrier bay, then the vanity at
    x=41 1/2" on the north face and the tub deck on the south. The two boxes are back to
    back on opposite faces of that one bay — a 4" device cannot be offset inside 6 7/8" —
    with ~1 1/2" of air between them. **Confirm the bay is still free of MEP before putting
    anything else in it**: today no pipe, conduit, duct, sleeve or accessory has a vertex in
    x 4"..22", y 258"..278", and the west end of a wet wall is exactly where a plumber
    reaches for a spare bay.
  - **`load_va=0` IS A COINCIDENCE JUDGEMENT, NOT AN OMISSION** (owner's call). Each seat is
    ~1,400 VA and only while its instantaneous heater runs — seconds per use. At the other
    reading of 220.82 (nameplate under (B)(3)) `electrical.service_load` goes 267.4 A ->
    272.1 A against the 320 A service and still passes, so this is not load-hiding to make a
    check green. **Revisit it if anything with a real duty cycle joins these circuits.**
  - **THE WARM WATER IS THE ELECTRICITY.** An S5 heats from the COLD supply instantaneously.
    No WC in this house takes a hot run and none should — `needs` is `WATER_COLD` on all six
    and every `PR-*-HW-*` deliberately omits the WC. The heated SEAT is switched off by
    owner's choice (heated floors); it is a setting on the same appliance, so it is worth no
    line in the order either way.
- `plan/lighting.py` — `# haus: editable` luminaire/LED-run/control *instances*, room by
  room. Every light names its switch(es) in `controlled_by`; 24V runs name a `psu_ref`
  instead of a circuit. The `ED-*-LT` fixtures still live in `plan/mep_electrical.py` — they were
  re-typed in place from the old generic `ED-T-LIGHT` so their uids (and IFC GlobalIds)
  survived — and each is one corner of a grid completed here.
- `plan/lighting_types.py` — the `LuminaireType` catalog, schedule marks A–X (NOT
  editable: `frozenset` again). It said A–P until 2026-09-15 and had been wrong for a
  while: the run is A…X with `I` and `O` never used (they read as digits on a drawing),
  plus numbered variants of an existing family (`A1`, `E1`, `J1`, `P1`…), 31 marks in all.
  Only `Y` and `Z` are free — `V` is held by a retained revert. Prefer reusing a mark's
  family over minting a letter. Marks must stay unique; the E-602 schedule is keyed on
  them. Also holds the two 24V supply types and the dimmer/timer switch types.
- `params/solar.py` — rooftop PV array (12 × 440 W on the gable ridge, computed max fit).
- `params/roof_trim.py` — the eave water chain on RF-HOUSE's west/east eaves: drip edge →
  box gutter → downspout, each piece's position derived from the one above it so the laps
  hold. RF-HOUSE has **no fascia** (continuous metal skin ⇒ the resolver's corner trim), so
  every offset is measured off the corner trim's face, never a fascia's. "Continuous" is
  `Material.skin_family`, not tag equality — the walls are exposed-fastener PBR and the roof
  is mechanically seamed, and they read as one skin because both declare
  `skin_family="standing-seam"`. Drop that on either and the flush edge silently reverts to
  a fascia-and-drip-edge detail nobody has drawn. The lap
  order is enforced by `packages/engine/tests/test_catlin_eave_water.py` — read it before
  moving any of these numbers. All three pieces are ordered in `_CHAIN_MATERIAL`, the
  house's one exterior dark, so the eave line matches the rake's corner trim.
- `typehaus/library/placeables/*.py` (inside the engine, not this directory) — the shared FixtureType/
  ApplianceType/FurnitureType *catalog*, wired in by `plan/manifest.py`. NOT editable: it
  uses `frozenset(...)`, which the dialect forbids. Type libraries stay non-editable;
  movable instances that reference them live in the editable modules above. **`plan/
  fixture_types.py` holds SEVEN selections** — `FX-KOHLER-UNDERSCORE-6036`
  (the drop-in bath) and `FX-VANITY-51-SINGLE` (RM-M-BATH2's vanity), plus
  the six vanities that replaced this house's remaining bare lavatories:
  `FX-VANITY-24-SHALLOW` (RM-M-BATH1 and, since 2026-09-09, RM-A-STUBATH — 24" is the whole
  width that bath's north wall has between ED-A-STUBATH-GFCI's plate and the neo-angle shower
  it got in the same pass), `FX-VANITY-30-SHALLOW` (RM-S-VANITY, TWICE — a 60"
  double alcove is two 30" bases under one 61" top, which is how one is actually built and
  which keeps two drains and two lavatories in the schedule instead of collapsing them),
  `FX-VANITY-30-SINGLE` (RM-S-SUITEBATH), `FX-VANITY-36-SHALLOW` (RM-B-BATH — 18" deep
  on the pallet-depth argument alone since 2026-09-05; the door-swing argument that forced
  it went with the room's rotation) and
  `FX-VANITY-48-SINGLE` (RM-S-BATH1).
  **`-SHALLOW` is 18" deep and `-SINGLE` is 21"**, and shallow is not the premium it sounds
  like: the cheap big-box combos that arrive boxed with their top and bowl already on them
  are 18.6"-18.75" deep, so 18" is the pallet depth. Widths are the stock ladder
  (24/30/36/48/60) — 18/42/54 are one-SKU-or-special-order, which is why RM-S-BATH1 got 48"
  rather than the 42" that a bounding-box reading of its door swing would have forced.
  **`FX-LAV-24` prices ZERO instances and the row is kept anyway** (the
  `glazed-green-brick` convention). **`RM-A-STUBATH` deliberately keeps its
  `FX-LAV-COMPACT`**: its water closet is on the west wall, and the 24"
  front envelope that creates crosses the only wall a vanity could have used.
  **The 21" front zone on every vanity type is a design convention, NOT a Minnesota code
  minimum** — Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33, ch. 4714 adopts the
  2018 UPC, and UPC 402.5 names only water closets and bidets, so a lavatory has no MN
  plumbing front clearance at all. (An earlier comment cited a UPC "Exception 1" giving
  lavatories 21" in dwelling units; that text is a *Washington* amendment.) The guest
  studio's wet bar uses `FX-LAV-COMPACT` (18" x 14"), dimensionally exact for a bar bowl
  and costing no catalog entry. **Borrowing a catalog type from the other direction** is
  free only while the borrowed type's footprint, symbol and schedule line are all still true
  of the thing in the room — `FX-M-BATH2-SINK` no longer borrows `FX-KITCHEN-SINK-33` (a
  double-bowl kitchen sink) for exactly that reason; it modelled no cabinet.
  **RM-M-BATH2 has storage above the toilet**:
  `FURN-M-BATH2-CAB` / `FT-BATH2-CAB-4506`, a 45" x 6" x 60" flush-fronted box on the room's
  only free wall (W-M-HS1's bath face), bottom at 4'-0" AFF — which is a **code line, not a
  comfort choice**: below `FX-TOILET-STD`'s own 30" top the wall face would move 6" south and
  take the bowl's front clearance 2.8" into the vanity. It is also why
  `resolve/placeables.py::_mounted_over_the_fixture` exists (→ `plans/01-decisions.md` #67,
  `notes/bath2_over_toilet_cabinet.md`): the engine was calling a 6"-deep cabinet 4' up an
  ERROR against UPC 402.5, whose 15" is elbow room for a *seated* person and not a column of
  air.
- `params/sunken_garden.py` — the freestanding arched porch/garden structure (math OK here).
- `params/foundations.py` — house footings, garage ICF stem + slab.
- `params/north_entry_frame.py` — the north entry STRUCTURE: geometry constants, the beam
  factory, the seven beams, six piers and their footings, the four KDAT roof columns and the
  two interior posts. Publishes every constant `breezeway.py` and `plan/views.py` read, so
  the two cannot drift.
- `params/breezeway.py` — what sits on that: the landing, the four cast tier pours, the
  guards, the slat screen, the seat/cap/truss-tie connectors and the annotations. The canopy `Roof` itself is authored in
  `plan/storeys/garage.py`, because a roof belongs to a storey.
- `notes/*.md` — construction detail notes migrated from the original repo.

**Editability rule (enforced):** any UI-movable element (Furniture/Fixture/Appliance/
Equipment/Register/ElectricalDevice/Door/Window/Wall/Room/Node/Stair) must be authored in a
`# haus: editable` file, or its canvas edits can't be written back. The loader raises
`loader.uneditable_movable_element` (a hard build error) if one is authored in a non-editable
## House facts that must stay true

Each section below is the building as it stands. The reasoning behind a number, the
alternatives that were rejected, and the engine bugs these rules dodge live in
`DESIGN-LOG.md` under the same section title.

### Site and the four structures

- Four structures: house, garage (4' north gap), sunken-garden/porch/balcony concrete structure (5" south gap), and the north-entry bridge (4' gap).
- **The north entry is engineered, not schematic** (2026-09-10). `RF-BW-CANOPY` spans 24' between `BM-BW-RW`/`-RE`, which top out at +7'-4" — the garage plate — so the two roof planes are ONE plane; change either and they step apart. **The canopy is freestanding and braces itself.** The WEST header lands on two 6x6 KDAT columns (`PT-BW-CW`/`-CNW`) on `ABU66SS` stainless bases; the EAST header lands on `PT-BW-RE`/`-RNE`, which are **12" cast concrete columns running unbroken from footing to header soffit, fixed at the base** — the east lateral system, and the reason that joint is a shim pack plus an `HGAM10` gusset and never a post cap. The west side is braced by `W-BW-SCREEN`, a sheathed KDAT 2x4 panel deck-to-+4'-0" that is ALSO the guard and the closure over the deck framing. **Its two faces are not the same** (2026-09-11): WEST is 5/8" CDX under 7/8" `corrugated-panel-24` and carries the shear ALONE; EAST is one 5/8" APA Rated Siding 303 MDO panel doing shear and finish together, uncounted, because that face stands under the canopy roof and is a finish problem rather than a weather one. It carries `alignment=face("stud-ext", offset=inch(-1.75))` so the 2x4s stay centred on the `PT-BW-CW`/`-CNW` line at x=6'-0" — without it the stack re-centres and the west corrugated face leaves the plane it shares with the garage panel, **which since 2026-09-12 is the whole of the reason**. The six `structural.member_interference` FAILs recorded here were the offset's stated purpose and were a misreading: 7/16" was just the first value clearing `interference_tolerance_in`, and the real clash was all three plate courses running THROUGH both 6x6s, hidden by `_butt_joint`'s centroid-point reading of a column. Both columns now carry `within_wall="W-BW-SCREEN"` and the solver cuts the plates flush at their faces (3 plates become 9; 7 1/2" / 54 1/4" / 6 1/8"), so no plate/column pair is left to report. **`W-BW-SCREEN-SKIRT`** carries that west sheet 13 1/2" further down over the sill, the seat beams and the two `ABU66SS` bases, stopping 1" ABOVE the pier tops — the bottom edge is OPEN and must stay open, it is how the flutes drain and the column bases dry. It is a second element with its own node pair, not a lower base on the panel, because a wall's layers cannot run below its base and its sole plate would land on the piers in the seat beams. `SC-BW-WEST` is a 2'-4 3/4" slat clerestory above it and `RL-BW-SCREEN` is retired. **The garage joint is a TIE, not the lateral system** — seven `LSTA24` straps at 4'-0" o.c. (`CN-BW-JOINT-*`) make the shared sheathing a drawn connection, and the two roofs move together; the only movement joint is at the HOUSE end. The record said the opposite until this revision, in the same file that required that plane to move. Every truss ties to its header with a stainless `H2.5ASS` at both ends (`CN-BW-TRTIE-*`), authored rather than derived. Both canopy eaves carry the garage's fascia and a CONTINUOUS trough falling north to `TR-G-LEADER-E`/`-W` — no leader at the south end (it would discharge onto the tiers) and no soffit (no wall to die into, and no vented attic to feed). **SIX cast piers on TWO bearing planes and the split matters**: `PT-BW-W`/`-E`/`-RE` bottom at −9'-9 7/16" with the house footing ten inches away, so **cast them in the open basement excavation or they undermine it**; `PT-BW-GW`/`-GE`/`-RNE` bottom at −7'-0", coplanar with the garage strip footings, and are cast with the garage foundation. Nothing here names a `W-B-*` or a `W-G-*` tag. **The landing has ONE tier of beams**: two east-west seat beams on the piers with 2x8 joists running north-south straight on them; `BM-BW-FW` is deleted and `BM-BW-FC`/`-FE` sit in the joist plane, reaching the interior landing under `D-G-SERVICE`'s sill, 3 3/4" over the continuous ICF stem (the west one sistered to the deck's second joist, the east one's face on the RO jamb). `W-BW-SCREEN` is filed on the **garage** storey, with the canopy roof it braces — on `main` it joined the house's braced wall lines and its dimension chain. See notes/north_entry_structure.md and notes/north_entry_piers.md. (→ DESIGN-LOG.md, "Site and the four structures")
- **The north entry's three HOUSE-side piers are `Pad`s, the three GARAGE-side ones are not** (2026-09-14). `PD-BW-W`/`-E`/`-RE` are 2'-6" x 1'-6" x 1'-0" rectangles at -9'-9 7/16", graded prescriptively against IRC Table R507.3.1 — their `spread_footing/` items have left the register. **The rectangle is not a preference**: `FT-B-N1`..`-N4` sit on the same plane and a 24" square reached 2 1/8" into them, a lap that was invisible while these were Footings because `structural.concrete_interference` scopes every `Pad` and only a wall-less `Footing`. **One size for all three** — three pad sizes are three rows in S-100's FOUNDATION SCHEDULE, and that sheet is one row from its schedule governing its height. `PT-BW-GW`/`-GE`/`-RNE` stay `Footing`: they lap `FT-GF-S1`/`-S3` by ~7 1/2" on one plane and the pier line is only 4 1/2" from that face, so the 12" shaft overhangs any pad that clears it — one pour, which only `Footing.under` can say, and three `spread_footing/` items are the price. (→ notes/north_entry_piers.md §6)
- **A post that carries only a ROOF is now reached by `structural.deck_footing_size`** (2026-09-14). `_roof_borne_posts` converts a post's roof-footprint share into R507.3.1's deck currency — `(10 + design snow) / 50`, **1.674** here — and hands it down the post chain, so `PT-BW-CW`/`-CNW`'s canopy share lands on the piers under them. **`PT-BW-RE`/`-RNE` were invisible before this, not light**: they carry `BM-BW-RE` and no deck, so no deck's post list held them. It is **not** a restatement any more (2026-09-18): the rule is `engineering/pier_basis.landed_roof_tributaries`'s and the check reads it through `checks/structural/_engineering.py`. Checks may import engineering; the copy was unnecessary, not forced, and it had drifted twice over — it knew nothing of `_rafter_fields`, and it scaled at the 50 psf **ground** snow while `BM-BW-RE` overhead was designed at the authored 73.7 psf drift.
- **A pad carries its own weight and the shaft on it, net of displaced soil** (2026-09-18). `deck_footing_size` adds both as equivalent R507.3.1 tributary; `engineering/soil.displaced_soil_credit_lb` credits back the soil the pad replaced at the low end of the 110–130 pcf band, because a presumptive allowable is a **net** pressure. Gross was what put `PD-BW-RE` 1.5% over an allowable it is not over. Every house-side pad passes at one size, so S-100's FOUNDATION SCHEDULE stays one row.
- **`BM-BW-RW`/`-RE` stay 3-ply 2x12 KDAT; the exterior glulam is REFUSED** (owner, 2026-09-12), and the engine is the reason rather than capacity. These are the only two `roof_beam` items in the house, and `engineering/roof_beam.py`'s `_SECTION` matches a sawn `N-2xM` and nothing else — a `"3.5x11.875"` makes both records INCOMPLETE, and nothing picks them up (`engineering/glulam_beam.py` left the registered-kind tuple on 2026-09-11 and is deck-only besides, 40 psf live at `C_D` 1.0, which cannot carry this 73.7 psf drift case). Retyping trades a d/c of **0.71** for a gap in the register. **The ply seam does not reach these two**: both headers ARE the eave bearing lines, the trusses land on their TOPS, so both seams sit inside the roof assembly under the deck, 1'-4" inboard of the drip line — which is the FPInnovations carve-out for appressed treated plies, and **not** the porch's 2026-09-06 refusal, which rested on tape plus a formed cap. No cap here, and its absence is not a gap. Cost confirms rather than drives: ~$325-450 over 11.4 LF. (→ DESIGN-LOG.md, "Site and the four structures")
- **Every wood-on-concrete beam seat is a drained STANDOFF, never a sill gasket** (owner, 2026-09-12) — twelve of them, six at the north entry (`CN-BW-STDF-*`) and six in the garden (`CN-SG-STDF-*`), all `SS316-SHIM-35` packs holding a 1/2"-1" gap, and **not one grout island** (`PIER_CONCRETE_12` carried one until 2026-09-12; retyping `PT-SG-COL` on 2026-09-10 rode it over to `PT-BW-RE`/`-RNE` rather than closing it). The `HGAM10` beside the pack is the **TIE**, never the bearing — two parts, two jobs. `BM-BW-RW` never touches concrete at all: 6x6 KDAT posts through `CCQ46SDS2.5` caps on `ABU66SS` bases. **No IRC provision requires a barrier or a standoff at this joint** — R317.1 item (2) needs a foundation wall AND under 8" to grade, R317.1.2 is embedment, and R317.1.4 governs wood COLUMNS with 1"/6"/8" projections that *relieve* the treatment requirement rather than impose a clearance; a treated beam on a concrete column top satisfies R317 with nothing added. A closed-cell gasket would be the wrong part: it is a capillary break for a plate bolted tight to a slab, and at an exposed joint it becomes the water-holding layer. Wicking is not the mechanism that governs either — capillary rise is bounded by evaporation at 100-480 mm, and nothing here is within reach of it: the north entry's pier tops stand 18 1/2" above grade, its canopy columns 9'-2 3/4", and the garden's porch columns rise 10'-0 15/16" out of the court floor. What wets a seat is rain standing on the pour and end-grain uptake where a beam END lands there, which is `BM-BW-RE`'s south end; the wash, the drip lip and the gap are aimed at that. (→ DESIGN-LOG.md, "Site and the four structures")
- **Grade is 2'-10" below the main floor.** **Datum is the TOP OF JOISTS, not the finished floor** — main-floor FFE is +3/4", so a slab landing there needs an explicit `top_elevation` (`params/main_deck.py`).
- Basement storey is at -9'-1 7/16", independent of grade. Pour is exactly 8'-0"; clear height 8'-0 15/16" under joists / 7'-10 7/8" under the EPS band. `code.R305_ceiling_height` DERIVES this, not `Storey.default_ceiling_height` (still a fictional 9'-0") (→ DESIGN-LOG.md, "Site and the four structures").
- Grade-dependent: garage + foundation, bridge's frost pads/piers, hydrant bury, sunken garden floor, nine perimeter spot elevations, both impervious surfaces. `SITE_GRADE` lives in `params/foundations.py`, repeated as a literal in `plan/site.py`; `plan/manifest.py` asserts the two agree.
- **Garage storey datum is not the garage floor.** Walls bear on the ICF stem at `GARAGE_STEM_REVEAL` (1'-10") above grade → `garage` storey at -1'-0"; the slab pours at grade (1'-10" lower), absolute `Slab.top_elevation`.
- Sitting on the garage floor must be explicit: `D-G-OVERHEAD` carries the plan's only negative `sill_height`; the ICF stem becomes a curb-free grade beam there.
- `D-G-SERVICE` threshold stays 0'-0" with the bridge deck (`+1'-0"` sill); the 2'-10" drop is five 6.8" risers inside (`ST-G-SERVICE` KDAT, flush to the stem's finished face at x=6'-11 5/8"; `RL-G-SERVICE` wall-mounted on `W-G-W`, one bracket on stud-010 and one on `BK-G-W-RAIL-FOOT`). `SL-G-STEP-0` is retired — `FS-BW-GARAGE` replaces it — though stray comments in `plan/assemblies.py` still name it. **The stem does NOT gap under this door** (since 2026-09-11): `W-GF-S-DR` is full stem with its nodes pinned at x 8'-3"/11'-9" as a fossil, so `SP-GF-S-HYD` keeps its host.
- `Stair.floor_opening` is optional (a rise states directly via `base_elevation`/`top_elevation`) — but `structural.stair_riser_uniformity` and `code.R311_7_8_handrail` iterate `model.stairs`, so slabs instead of a `Stair` draw NO riser/handrail finding.
- Garage plates are 8'-4", not 8'-0" — the door climbed 4" when the storey dropped; a shorter plate would push the 3-ply LVL header into the truss heels.
- Emitters/placeable resolver read `resolve/room_floor.py::room_floor_elevation` for garage heights, not storey elevation — enforced by `test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade`.
- **ICF stem and wood wall are coplanar outside.** `GARAGE_Y_SOUTH`/`NORTH` (`plan/storeys/garage.py`) is both the sheathing plane and the stem's EPS face (walls `cdx-ext`, stem `concrete-ext`+`GARAGE_ICF_EPS` offset) — layer NAME is the alignment key, so a sheathing swap is also an alignment edit or the wall silently misplaces. Only 7/8" of the corrugated panel projects past.
- Do not fix alignment by moving stem nodes — `resolve/stacking.py::_axis_match`'s 1/2" tolerance would silently drop the whole foundation-to-framed stack.
- `FT-GF-*` follow the stem via `Footing.center_on="wall"`, not the node line.

### Shell: framing module and envelope

- 36'x36' at sheathing; everything on the 16" o.c. module; exterior walls carry
  `alignment=face("sheathing-ext")` as the vertical datum (#43). Side-wall stack is 2x6
  throughout — one `EXT_2X6` on main, second and attic. Main-storey studs are LSL, upper
  storeys dimensional 2x6 (a purchasing note in the assembly's `source`).
- It is a CATLIN TRUSS WALL outboard of the sheathing, ONE girt tier: 4" ccSPF crossed only
  by the blocks, then the block's proud 1/2" as a continuous vent gap, then one tier of flat
  horizontal KDAT 2x4 girts at 24" o.c. in free air, then the panel. Each crossing: three
  loose 3-1/2"x3-1/2"x1-1/2" KDAT offcuts stacked to 4-1/2" over every OTHER stud, clamped
  by one 8" FASTENMASTER TIMBERLOK (TLOK08) through girt + block + sheathing, 1-1/2" into
  the stud. There is only ONE tier — do not add a second inner one; the foam needs no
  backing (ESR-4073 §4.4.2) (→ DESIGN-LOG.md, "Shell: framing module and envelope").
- **AN INTERIOR PARTITION'S FRAMING STOPS 3/4" CLEAR OF WHATEVER IS OVER IT** (2026-09-19) —
  the rafter soffit in the attic, the joist or SIP soffit everywhere else — and a Simpson
  **SDPW19600 DEFLECTOR** screw spans that gap: braced laterally, RELEASED VERTICALLY, so the
  deck deflects onto nothing and no partition becomes a prop. 58 walls, 188 screws, one per
  crossing (24" o.c. under a parallel member; one blocked bay per module between them — and
  **that blocking is billed nowhere**). The part is the 6"/0.195" one and NOT because 6"
  reaches: Simpson publish the 5" SDPW14500 for a single 2x or a built-up plate to 2-1/4"
  and the SDPW19600 for the DOUBLE 2x this house frames. T-40, not T-25; 3/8" predrill
  through the plate only.
- **TWO TOPS, AND ONLY THE FRAMING ONE MOVED.** `plate_top_z_m`/`top_z*_m` are the framing
  and belong to `resolve/partition_top.py`; `z1_m` is the BODY — the gypsum bill, the stair
  enclosure, the wet wall a riser climbs — and stays with `resolve/platform.py`. Cutting the
  body at the joist soffit too costs four FAILs (`code.R312_1_1_stair_open_side` on `ST-S2A`,
  `mep.wet_wall_occupancy` x3). Do not re-collapse them; `tests/test_partition_top.py` says
  so out loud.
- THE SCREW IS CHOSEN ON THREAD, NOT LENGTH (2026-09-12). The CLAMPED STACK is 6.0" — girt
  1-1/2" + block 4-1/2"; the 1/2" ply is nailed to the stud and is NOT a member being drawn
  together — and plain shank has to span it. TimberLOK threads 2" (ESR-1078 Table 1A) and
  clears it exactly. The SDWS22800DB this wall carried until 2026-09-12 does NOT: every
  SDWS22 threads 3" whatever its length (IAPMO UES ER-192 Table 7), so 1" of thread stood
  inside the stack and jacked the girt off its blocks. **Never substitute a screw here
  without reading its thread length.** The part is authored on the girt band's `FramingSpec`
  (`standoff_fastener_*`), and the takeoff bills exactly it.
- THE SCREW IS THE ONLY LOAD PATH per crossing, no second tier, no nail. Graded as
  `girt_screw/W-A-N1` beside `wall_panel/W-A-N1` — three states, head pull-through governing
  at d/c 0.487 (Exposure B, the site's basis; 0.712 at Exposure C). Mark the stud line across
  the girt face as it's laid: the screw is blind through 6" of wood into a 1-1/2" target,
  invisible once the foam is on — inspect the pattern before the sprayer arrives. Head seats
  FLUSH; a head that will not pull down means the wrong screw.
- There is no WRB — the foam is air/water/vapour/thermal; `plan/transitions.py` names
  `spray-foam-ext` as the water/thermal plane. **THE FOAM IS A PERFORMANCE SPEC, NOT A
  BRAND** (owner, 2026-09-16): `notes/ccspf_spec.md` §1 is the requirement and §2 the
  qualifying list — Enverge OnePass HFO, Heatlok HFO High Lift, SealTite PRO HFO,
  InsulStar OPTIMAXX (report unread). The one that cannot slip: **≥ 4" per pass by the
  evaluation report**, or the wall needs a cooling wait or a second visit — Heatlok HFO
  *Pro* (2"/pass) and Corbond IV (ER-146 lapsed 2026-07) do not qualify. Spray only at
  60-80 F on dry (< 16% MC) sheathing, as two back-to-back passes in one visit (1" picture-
  frame pass, then 3"); one 4" pass is acceptable. **Never a sub-1" flash coat** — Huntsman
  and JM both say it under-cures and loses adhesion. **WRB listing is the tiebreaker**:
  only OnePass carries it in its report (ER-859); on any other product the water plane is
  an open Minn. R. 1300.0110 alternate-approval item (notes/catlin_truss_engineering.md §9).
  Wood and the screw pass happen on the FLAT wall before tilt; fillet the foam against the
  block sides (BSI-048), never butt square.
- Everything outboard of sheathing is KDAT — one BOM row, plus `3-2x4:kdat` for the block.
  Blocks are on the STUD module, every OTHER stud, at 32" from the wall's LAYOUT LINE (girts
  run their own 24" module) — 32"x24"=5.33 ft2 is the crossing tributary in
  `notes/catlin_truss_engineering.md`. Block phase is solved for 32", not 16" — reusing the
  stud phase puts half a facade's segments on the wrong parity.
- Girt course module counts from the SILLS' datum, phase ZERO
  (`course_datum="framing-base"` + `course_offset=inch(0)`), not the wall base. One module
  runs unbroken from wall base through the gable rake, breaking only at a starter (band
  bottom), a top course (level wall), and a rake nailer (gable's raked top, field one board
  clear).
- NEW-OPENING RULE: head on a 24" multiple above the sole plate (24/48/72/96"), or sill
  3-1/2" above one — this phase is the only one keeping every bay ≤24.00"
  (`structural.girt_course_spacing` FAILs otherwise) (→ DESIGN-LOG.md, "Shell: framing
  module and envelope").
- Windows are OUTIE, mount plane 6" out from sheathing on the outermost furring layer's
  outer face (derived, never authored, so unaffected by cladding-depth changes).
  `structural.truss_wall_opening_support` keeps every RO jamb within a flange's bearing of
  wood.
- Cladding face stands 7.25" proud of sheathing (`_WALL_OUTBOARD_IN` in
  `params/roof_trim.py`). Consumers that hand-transcribe this and must move together:
  `params/north_entry_frame.py::HOUSE_CLADDING_Y_FT`, `params/sunken_garden.py`'s `gap_to_house_in`,
  exterior devices in `plan/electrical.py`.
- The Swinburne truss (vertical `laid="edge"` framing) is one swap away:
  `resolve/framing/truss_frame.py` sits behind its own predicate, the girt frame is a
  sibling on `standoff="block"`, and the old layer tuple survives verbatim as
  `EXT_2X6_SWINBURNE` (referenced by nothing) — revert steps in
  `notes/outie_window_truss_detail.md`.
- R-value card reads R-43.5; honest is ≈R-39.8 wood-only / ≈R-37.9 with girt screws counted
  (blocks are framed, not a `CavityFill`; girt credited its own R though outboard of the
  vent gap). `wall_r=40` is met wood-only (39.85) and 2.1 short with fasteners in — don't
  read either number as the other. See engineering note §7, §7.1.
- Stud bay is FIBREGLASS, not mineral wool, EXCEPT tub deck, saunas, plant rooms, and
  `_GARDEN_FRAMED_STUD` — do not sweep those next time (list in `plan/assemblies.py` above
  `EXT_2X6_SWINBURNE`).
- `INT_2X4_PARTITION` has NO insulation. Exception: `W-S-SS2` uses `INT_2X4_RC` (resilient
  channel, STC 48) instead of a batt.
  - Rated STC 34 (USG SA924/UL U305/U314) at 16" o.c. — do not difference against the old
    insulated 36; different test series. Card over-reports it too: no `CavityFill` means
    `analysis._layer_rsi` bills the stud layer as solid SPF (R-6.4 vs honest ~R-2.5-3),
    harmless only because `INT` excludes it from `mn_energy` — never quote the card here.
  - Knowingly left uninsulated (fix, if wanted, is a retype to `INT_2X4_RC`, not a batt):
    `W-A-BATH-S`, `W-M-HS3`. `W-M-HS3` (laundry ↔ living) is a decision, not an oversight
    — see DESIGN-LOG.md, "The laundry is not acoustically treated".
  - **`W-S-SBS` and `W-M-BDN1` left this list on 2026-09-15**, both retyped to `INT_2X4_RC`:
    each is a wall between a bed and a bathroom, which is the case the STC 34 preset is
    worst at. On `W-M-BDN1` the channel faces the BEDROOM (RM-M-BATH2's face carries the
    shower, the vanity, the floor-heat stat and the bath switch, all flush; the bedroom's
    face carries nothing), leaving a 1/2" step at x=8'-2" behind the king's headboard where
    `W-M-BDN2` stays plain. On `W-S-SBS` the channel faces the BATH and `interior_room` does
    not select it — the alignment does, and both spellings resolve identically.
- `INT_2X6_BRG` also has an EMPTY cavity and no channel, and two segments of it stand
  between a sleeping room and something noisy: **`W-S-C2C`** (RM-S-SUITE ↔ the second
  storey's east rooms) and **`W-M-C2`** (RM-M-BED's line continued north past N-M-C1).
  Both are known, accepted gaps as of 2026-09-15 — the fix is the same retype `W-S-C2B`
  took that day, to `INT_2X6_BRG_RC` with `alignment=face("stud-ext", offset=inch(-2.75))`.
  Neither was done, because unlike `W-S-C2B` neither has tees at both ends to absorb the
  channel's 1/2", so each would step a face in the open.
  - On `W-S-SS2` the channel must stay on the NORTH face: the south face carries ST-S2A's
    stringer ledger/handrail and a void boundary `attic.py` defines off it; moving it south
    leaves 35-1/2" against R311.7.1's 36".
- Cladding split by orientation: `board-batten-24` (1,678.3 SF, Metal Sales **BBD75-1212**,
  24 ga concealed DIRECT-fastened PVDF, **12" net coverage**) on the 20 east-west-facing
  walls; **`pbr-panel-24`** (1,416.6 SF) on the rest — a per-wall `Wall.layer_materials`
  override, not a sibling assembly (→ DESIGN-LOG.md, "Shell: framing module and envelope").
  - **Every metal face on the property is 24 ga PVDF Linen White (81) since 2026-09-14**, and
    the gauge is not a preference: at Metal Sales PVDF *is* a 24 ga product (the 24 ga colour
    guide is the PVDF palette; the 26 ga guides are MS Colorfast45, which is SMP), so the
    authored "26 ga PVDF" on the E/W walls and the garage was probably not a purchasable
    combination. Secondary reasons: hail (Twin Cities corridor, insurers exclude cosmetic
    denting, 24 ga dents and oil-cans less — gauge has ZERO corrosion effect) and one colour
    on every face, which also neutralises St Paul §63.110's advisory on street-facing
    materials. Linen White is the highest SRI in the Metal Sales line — SR 0.73 / TE 0.86 /
    **SRI 89** — which is the point: bounce daylight into the tree-shaded rear gardens.
    Caveat: SRI is NIR-weighted, no visible LRV is published, and it is NOT a low-gloss
    colour. **Two new house-local tags, `pbr-panel-24` and `corrugated-panel-24`**; the 26 ga
    rows stay at 0 SF as documented reverts. Tags read the GAUGE, which is why they had to
    move and `board-batten-24` did not.
  - Thickness stays 1-1/4" — LOAD BEARING for the same four consumers listed above
    (`_WALL_OUTBOARD_IN`, `HOUSE_CLADDING_Y_FT`, `gap_to_house_in`, `plan/electrical.py`).
    `skin_family="standing-seam"` must stay on BOTH panels or the flush zero-overhang edge
    reverts to fascia-and-drip-edge on all four edges. `exposed_fastener` is deliberately
    ABSENT (`T09150HWAM` is 1,804: 640 garage + 1,164 E/W PBR; `attic` storey has none).
  - Ten separate registrations render the appearance across `ui/src/three/materials.ts`,
    `ui/src/nordic/palette.ts`, `emit/gltf/palette.py`, `emit/draw/palette.py`,
    `ui/src/components/DetailCanvas.tsx`, and `emit/draw/elevation_finish.py`'s
    `_BATTEN_PITCH_M` — each silent if missed; full list (→ DESIGN-LOG.md, "Shell: framing
    module and envelope"). The `elevation_finish.py` one is the trap: without its
    finish-first branch it draws 16" seam pitch, not 12" battens. Both `_BATTEN_PITCH_M`
    and `ui`'s `BATTEN_PITCH_M` carried **20"** until 2026-09-14 — authored against no named
    panel and never re-struck when one was named — and `_CORRUGATED_LAP_M` carried 32", which
    is the ROOF coverage where the wall is 34-2/3". Both drew a line where no joint is. The
    ui's `ribHalfWidth` is a FRACTION of the module, so it had to be re-struck with the pitch
    (0.05 -> 0.0833) to keep the drawn cap at 2".
  - Four wall corners now bill: `TrimKind.WALL_CORNER` + `Flashing.vertical`, 89.5 LF,
    derived off `_WALL_OUTBOARD_IN`. Without `vertical`, a 22'-4" corner bills as 1-1/4" of
    metal (`_EdgeRun.path` is a plan polyline).
  - The panel is **Metal Sales BBD75-1212**, 12" coverage, 24 ga (re-named 2026-09-14; the
    tag `board-batten-24` reads as the GAUGE and does not change). **BB75-1111, named
    2026-09-11, is the CLIP-fastened sibling** — its wall-base detail wants a clip and two
    screws where BBD75's wants one screw at the nail strip, which is the model §6 of the note
    has always used. Structurally identical (both guides publish 43/58 psf at 2'-0"); BBD75
    is cheaper to install (~9% fewer panels, ~840 screws and no clips against ~2,000 and
    ~1,000). 12" is 3.0x PBR's panel count, which is why `prices.toml` labour sits near the
    top of its band. **Panel length maxes at 20'**, so the 31.4' gables joint at the storey
    lines with Transition Trim 55536XX; PBR and corrugated run to 45'.
  - ENGINEERED, not prescriptive (decision #65), and **one group item covering all twenty
    walls**: `wall_panel/W-A-N1`, keyed by the lowest member tag. **Three limit states since
    2026-09-14, because IRC R703.1.2 names three** ("bending rupture of siding, fastener
    withdrawal and fastener head pull-through"): bending d/c **0.315** (58 psf published at
    24" girts); screw withdrawal d/c **0.334**, COMPUTED per NDS 2018 §12.2 because the
    maker's table excludes fasteners by name; head pull-through d/c **0.118**, COMPUTED per
    AISI S100. **WITHDRAWAL GOVERNS** — it was bending until 2026-09-14, flipped by the
    coverage going 11" -> 12" and the screw 2" -> 1". Both pass wide, the two are 6% apart,
    and a later coverage or wind change can flip them back with no physical meaning: read the
    governing state as a label. Status OK. Oracled by `notes/board_batten_girt_span.md`.
    `--item wall_panel/W-M-S1` resolves to the group. PBR stays prescriptive, now on Metal
    Sales' own PBR CTR (1/2026): **318 psf** at 2'-0" in 24 ga, 236 in 26, superseding the
    ASC PS230 / Metal Panels Inc. / Homewood citations.
  - **The substrate question is closed by the CODE, not by a letter.** IRC R703.1.2 asks for
    a wind-load path by ASTM E330 test or by design analysis and says nothing about a solid
    substrate; BBD75-1212 lists an ASTM E 330 Load Test; and the allowable table is indexed
    on FASTENER SPACING from 2'-0" (narrowest) to 6'-0", so a 24" girt is at its strong end.
    The 07/2026 CTR's sheathing-only summary badge is a copy artifact — the same row says
    `10" & 12" COVERAGE` on a sheet showing ONE panel at 11". No Tech Services letter needed.
  - **58 psf is kept although a newer sheet publishes 75.** The 07/2026 CTR re-publishes this
    panel at 42/75 off a LOWER section, which is not reconcilable in either limit state
    (scaling 58 by the section ratio gives ~25-29, not 75). Recorded, not adopted; a question
    for the Rogers branch when quoting, not a gate. **BBD75-1212 also carries no product
    approval at all** — the CTR scopes FL47647.1 to "BBD75-1010 only", and BB75's is "over
    Sheathing". Florida approval is not a Minnesota requirement.
  - ESR-4729 DOES NOT COVER THIS WALL — Western States' ROOF-panel report, 24 ga min over
    16 ga steel. Do not reintroduce it. Of eight surveyed, only Western States and Metal
    Sales permit open girts, and Western States publishes no load data at all (doc 4209-22,
    read in full) — substituting another forces a second girt course or a continuous deck.
  - Cladding screw is the guide's own stocked **1"**, wood-point (Type 17), 316 stainless or
    ASTM A153 Class D HDG — **REVERSED from the 2" specified 2026-09-11 to 2026-09-14.** That
    2" rested on one clause, "fasteners should extend 1/2" or more past the inside face of
    the support", and the clause does not carry it: the GIRT is the support and the tip
    emerges into a vent gap and then ccSPF, buying nothing; the same rule yields 0.034" of
    thread on the guide's own 7/16" OSB row against 0.596" here; and the load table footnotes
    fasteners out by name, so NDS §12.2 governs the fastener and every length passes it.
    **2" is affirmatively rejected** — its tip stands 0.476" into a 0.500" vent gap, 0.024"
    off the ccSPF, so ~840 tips are one thin girt or one overdrive from the foam. 1-1/2" is
    the recorded no-cost margin; nothing longer than that, ever. A drill point would ream its
    own thread out of the nailer. PBR's face screw stays 1-1/2".
  - **The EPDM washer is the 100-year limiter, not the screw** — 15-40 yr against 300-series
    stainless in painted Galvalume "matching the expected life" of the cladding (MCA 09/2025)
    and painted AZ50 at 50-375 yr. Annual look, washer campaign ~yr 30-40, painted heads on
    the order. Ranked after it: base-of-wall salt zone (ungraded here), treated-wood contact
    (KEEP THE GIRTS — `notes/board_batten_girt_span.md` §7.10; read the end tag before
    ordering and upgrade the BACKER coat), sealants, then paint.
  - Revert = delete the twenty `layer_materials=` overrides; `pbr-panel-24` and its
    `prices.toml` row stay live on the other elevations. The `pbr-panel-26` /
    `corrugated-panel-26` rows sit at 0 SF as the gauge revert.
- Every exterior corner is construction-correct, 4-stud. Layout grid is struck from the
  building's outside sheathing corner: all four facade lines origin `+0.0000"`; 217 of 241
  exterior module studs land on exact 16" multiples (24 exceptions are the corner posts);
  all 31 exterior windows centre on that grid.
  - `EXT_2X6` and `PLANT_EXT_2X6_HUMID` carry `corner_style="4-stud"` (`preferences.toml`'s
    `[framing] corner` states it once) — valid because the continuous exterior foam, not the
    post cavity, is the primary insulation. `resolve/framing/solver.py::frame_model`
    resolves a corner's style from BOTH incident walls (→ DESIGN-LOG.md, "Shell: framing
    module and envelope"). `GARAGE_WALL_2X6` stays 3-stud (no continuous exterior foam);
    `structural.corner_style_matches_preference` is scoped accordingly.
  - The corner box is RETIRED for the girt band (courses butt at the corner, nothing
    full-height to cap); `FramingSpec.corner_cap`/`TrussFrame.corner_box` still fire for any
    band that asks (`EXT_2X6_SWINBURNE` still does).
  - The 1/2" sheathing lap at the corner is still undeclared (all layers mitre 45° today) —
    logged in `plans/TODO.md`, not built.

### Bearing lines and floor decks

- Bearing lines: west wall, center N-S wall (x=18'), east wall; 18' spans E-W, on every
  storey and in both materials.
- **Second storey has a fourth bearing line, x=10'-0".** `W-S-BA-E`, `W-S-BA-E1B`,
  `W-S-BD-N1B` carry `FO-A-HALL`'s attic joist cut ends: `structural_role=BEARING` and
  `INT_2X6_BRG_PLUMBING` (continuous studs, not staggered — `structural.wet_wall_bearing`
  FAILs a staggered BEARING wall). Thickness unchanged (6.77"): no face/area moved,
  `FX-S-BATH1-LAV.wall_ref` untouched.
  - `stacks_on` is MANDATORY: `W-M-STRW` has two collinear upper candidates (`W-S-BA-E`,
    `W-S-BA-E1B`) and `integrity.stack_ambiguous` is a hard ERROR without one. Only
    `W-S-BA-E1B` names `W-M-STRW` — do not also point `W-S-BA-E` at it, only one upper wall
    may claim a lower wall.
  - y=22'-4" to 26'-6" on this line has no wall and never can (the hall stub mouth to
    `D-S-BATH1`); `BM-S-BATH-E` spans it, `3-1.75x11.875 LVL` flush (`top_elevation=ft(20)`).
    Ply count (3, matching `BM-S-HALL`) is set by bearing WIDTH so the 4.77" attic partition
    doesn't overhang, not by bending demand (→ DESIGN-LOG.md, "Bearing lines and floor decks").
- **Basement ceiling: ONE FLAT BEARING SEAT at -13 7/16", not one depth.** `FS-M-WEST`,
  `FS-M-MECH`, `FS-M-STAIR` (x 0'-18') and `FS-M-EAST` (x 18'-36', y 0'-13') are 11 7/8"
  I-joists at 16" o.c.; `SL-M-DECK` (414 SF) is a 10" **BuildDeck** EPS SIP beam (8" base + 2"
  top hat) under 4 3/8" cast cover — BuildDeck is the basis of design since 2026-09-12
  (LiteDeck/Insul-Deck are named alternates), and its published 10"/4"/2-#5 row (20'-0" at
  62 psf) is quoted onto `SL-M-DECK.published_span`, where
  `structural.slab_published_span` grades the 18'-0" span as a PRESCRIPTIVE read. One plate serves studs and joists, no step in the forms.
  Seat/depth constants live in `params/main_deck.py` — moving the boundary is a one-line
  edit there. `structural.mixed_deck_bearing_seat` (FAIL) and `integrity.floor_bearing_grid`
  hold this.
  - Ceiling is 5/8" gypsum end to end (IRC R316.4, `ceiling_below` on the joist fields), but
    the two faces step 2 1/16" at the boundary. `RM-B-GYM` (only room crossing it) resolves
    TWO ceilings — 234 SF at -11 7/8", 90 SF at -13 7/16" — since ceilings derive per *deck
    region* (`resolve/ceilings.py`, `ceiling_over.ceiling_regions`), not per room. A seam
    alone isn't a step: `RM-M-LIVING` (2nd-floor truss/I-joist split, same depth) is ONE.
  - Floor finish follows the deck via `_BAND_Y`: `SL-M-DECK.floor_finish=coated-concrete`
    (`polished-concrete` until 2026-09-12),
    `RM-M-LIVING.floor_finish=lvp` over the wood bays; this band is the room's only zone,
    and nothing is currently authored on it. Prefer a derived zone over authoring one here —
    an authored zone's drawn ring must be clipped to the room, same as its area (fixed
    2026-09-05).
  - `RM-M-MUDROOM` + its closets (`RM-M-MECH`, `RM-M-MUD-CLOSET`) are porcelain over an
    uncoupling membrane (`integrity.concrete_finish_needs_concrete_deck` keeps them off
    concrete since `FS-M-MECH` is I-joist/plywood) — tiled because their doors open INTO the
    mudroom, not because they're wet; don't put either back on plank, it islands the tile.
  - Two walking planes meet flush (plank +0.986" vs the coated cap's +15/16") on both legs of
    the L; only the mudroom breaks it (~+1 5/16", ~5/16" strip at `D-M-MUD`, the one
    threshold on the storey). Oak (+1 1/2") is the two studies' floor only — never extend it
    to a cap edge (→ DESIGN-LOG.md, "Bearing lines and floor decks"). Junction detail is in
    `notes/mixed_deck_movement_joint.md`; mix is `DECK_CAP_MIX` (micro-monofilament PP, no
    macro fibre or steel — macro would be re-exposed by the coating's CSP 2-3 grind).
    The finish is a **coating**, not a cream polish, since 2026-09-12: light steel trowel,
    grind to ICRI CSP 2-3, ASTM F2170 RH gate, moisture-mitigating primer, matte 2K PU.
    The polish stays as a costed fallback in `prices.toml`.
- **Second floor's deck is mixed for services, not material.** `FS-S-WEST` (x 0'-18') is
  11 7/8" open-web trimmable floor trusses at 16" o.c.; `FS-S-EAST` (x 18'-36') is 11 7/8"
  I-joists. West carries nearly every 2nd-floor service crossing (both drain stacks, 4
  supply risers, radon/plumbing chase, hydrant distribution, data conduits) through the
  webs (8 7/8" clear opening, `resolve/framing/profiles.py::open_web_opening_m`) rather than
  boring/soffiting/chasing. Both fields stay 11 7/8" deliberately, so the split needs no
  movement joint or finish break.
  - Trimmable stock is 18'/20', up to 6" trim per end. Bearing grid is 18'-0" but the truss
    is 17'-11" (`resolve/floor_ends.py`), clear span 17'-3¼"; an 18' blank trimmed 1" covers
    it (`takeoff/framing.py::_order_length_ft`). The shared x=18' plate splits 3½" to the
    truss / 2" to the I-joist (`params/second_deck.py`, also holds the shared depth constant
    `params/main_deck.py` imports) — don't centreline-split it, it shorts the truss's seat
    (`integrity.floor_end_bearing` grades this). `FO-S-STAIR` clips 8 joist lines in the
    west half to 10'-1⅝", outside the trimmable range, fabricated to length.
  - Truss price row in `prices.toml` is a placeholder pending a fabricator quote; the
    borrowed I-joist span-table row (`checks/structural/checks.py::_IJOIST_SPAN_FT`) is
    advisory only at 18'-0" — the fabricator's table governs.

### Attic and roof

- Attic is a hot-roofed cathedral space: rafter plates E/W (not knee walls), gables N/S,
  ridge N-S, 6:12, zero overhang.
- **Eave blocking is a 2x6 on edge on the plate, tight to the sheathing** (`eave_blocking="2x6"`
  on RF-HOUSE; 36 blocks, one per bay). Lower bay only, so ccSPF fills over it; the air
  barrier is the sheathing band plus that foam, not the block. It is also what the gutter
  girt screws into. See `notes/roof_wall_eave_detail.md` K3.
- **The line every attic station answers to**: roof underside is `1 1/2" + x/2` above the
  attic finished floor, mirrored past x=18'-0" — 9'-1 1/2" at the ridge, 7'-0" at
  x=13'-9", 5'-0" at x=9'-9", 3'-0" at x=5'-9". Every height quoted in `plan/` (window
  head, can light, receptacle, door, duct, furniture, vent riser) is measured from this
  line — **and since 2026-09-19 the seven attic partitions answer to it too**: their raked
  top plates stop 3/4" under it, where they used to rake to the roof DECK plane and run
  11-7/8" of plate through the rafter above (`notes/partition_top_deflection.md`). Corollary for an opening: a head at `h` needs `h + 2"` of rake: `x_outer_jamb >= 2
  x (head + 2")`. (→ log4.md, "Attic and roof" — the 6:12/knee-wall history and cost
  delta)
- `FS-ATTIC` is also the 2nd storey's ceiling: authors `ceiling_below` (5/8" gypsum)
  inline, since `plan/storeys/attic.py` is `# haus: editable` and can't import `params/`.
  Exception: `RM-S-PLANT` uses `Room.ceiling_lining` instead.

- `RM-A-WEST-UNFIN` is now four rooms (was 598 sf unused loft):
  - `FO-A-HALL` (x 10'-0"..18'-0", y 22'-6 3/8"..35'-5 3/8"): stair well + hall run open
    to the roof underside. `purpose=STAIR` must be explicit — `code.R312_1_guard` filters
    on it and `code.R312_1_guard_height` never walks a void, so `CHASE` would drop
    fall-protection checking entirely. Never add x=10' to `FS-ATTIC.joists.bearing_refs`
    for this void — the field is global to the deck and would cut all ~34 joist lines
    including the 17 over the suite.
  - `RM-A-STUDIO`: `Occupancy.BEDROOM`, `floor_finish="vinyl-sheet"` over
    `plywood-subfloor`, uid `CAR401AAAA` (retagged in place). `RM-A-STUDY` next door is
    oak. BEDROOM occupancy is load-bearing for R310, the ventilation bedroom count,
    R314/R315, and whether `electrical.receptacle_spacing` evaluates the room at all. (→
    log4.md, floor-finish history)
    - 13.6 sf glazing, none addable (south gable mirror about x=18' is fixed; dormer/roof
      penetration excluded). R303.1 has passed on daylight since 2026-09-10 via
      `ResolvedRoom.head_limited_area_m2` (146 sf, area under the roof UNDERSIDE per
      R304.3) rather than the whole 356 sf — needs 11.7 sf glazing (has 13.6).
      `code.R305_ceiling_height` still reads 190 sf off the rafter TOP; the two are not
      reconciled. Revert lives in `_r303_floor_area`
      (`checks/code/mn_residential/ventilation.py`). (→ log4.md, literal-reading risk)
    - Exception 1's lumen floor no longer binds this room while it passes on daylight —
      `plan/lighting_attic.py` claims of R303.1-required fittings are stale (room carries
      5,400 lm over 146 sf). `REG-A-HP-WEST` stays regardless (graded on BEDROOM
      occupancy, not Exception 1).
  - `RM-A-STUBATH` (x 9'-10 7/8"..17'-8 5/8", y 17'-6 3/8"..22'-1 5/8", vinyl-sheet). Tag
    must stay `RM-A-STUBATH`, never `RM-A-STUDIO-BATH` — `electrical.room_lighting`
    matches `ED-{room.tag[3:]}-*` and the longer tag would prefix-match the studio,
    merging luminaire sets. x=9'-7 1/2" is `W-S-DC2`'s axis (no stud to bore); y=17'-4" is
    a joist line under `W-A-BATH-S`'s sole plate. Vent starts over the shower (6'-7" trap
    arm vs Table 1002.2's 5'-0"). No `humidity_class` set (NORMAL like every other bath) —
    WET would pull ROOF into the humid-room condensation walk for nothing.
  - `RM-A-POCKET` (x 0..9'-7 1/2", y 22'-4"..36', STORAGE). Door `D-A-POCKET` is in the
    SOUTH wall of `W-A-STU-N`, not the x=10' wall (far side is the void/shaft). Wall raked
    at 5'-0"+x/3; a 6'-8" head needs x ≥ 5'-9" (`structural.member_interference` catches a
    shallower station). Door not scuttle: ERV manifold, OA hood, `VR-M-RADON-VENT` head
    sit inside, so IRC M1305.1.3 wants the passageway plus its light and receptacle
    (`ED-A-POCKET-LT1`, `ED-A-POCKET-RC1`). `ResolvedRoom.head_limited_area_m2` is what the plan label
    and `haus build` report beside `area_m2` (whole attic: 496 of 1,171 sf built); every
    takeoff still reads `area_m2`.
  - Walls split for this void: `W-A-C2` (×2), `W-A-N2`, `W-A-W1` — a mid-span tee leaves
    `resolve/topology.py`'s junction solver without a shared endpoint; TAG/UID stay on the
    piece keeping a hosted opening. Exception: `W-A-STU-W`'s north end dies short into
    `W-A-STU-N`'s face, so `N-A-WW-N` carries `open_end=True`. `RB-HOUSE.bearing_refs`
    names all five segments; `test_ridge_beam_depth.py` pins the tuple.
  - ERV hoods: NORTH face, intake +5'-0" at x=3'-4" (main), discharge +17'-0" at x=2'-0"
    (second) — off the attic GABLE (where the leg crossed both gable windows' ROs) and, since
    2026-09-15, off the WEST facade too (`plan/mep_erv.py`). The gable objection is about
    W-A-N* at +23'-0" and never applied to W-M-N3B/W-S-N3B. (→ log4.md, why the gable failed)
  - `DU-A-ERV-R-BED3` and `CD-A-DATA-NE` both route SOUTH — the only option, since
    `FO-A-HALL`'s maxy is `W-A-N2`'s gwb face, severing every west→east route north of the
    studio. BED3 (5 cfm) runs ~53'-6"; `DU-S-ERV-HP-FEED` (100 cfm) sets the x=1'-0" chase
    section, turning east at y=22'-0" to `SF-S-HP1`'s drop up `RM-A-EAST-UNFIN`.
  - `DU-M-ERV-R-PLANT` (was `-A-`): LEVEL-2 manifold, south through `FS-S-WEST`'s open-web
    trusses at x=2'-10", east along y=4'-8", up inside `W-S-C1` to a high sidewall grille
    at 8'-6" (humid air stratifies). `W-S-C1` is `PLANT_INT_2X6_BRG_HUMID` (5 1/2" cavity
    for riser + vapour-tight boot) — `W-S-PS1` is plain 2x4, not sized for this. It is the
    longer, pressure-critical run at 55'-8", affordable because the ERV's rating point is
    0.4" w.g. — HVI certifies the B210E75RT at 206 cfm net supply at 0.4" (HVI ID
    2004940). (→ log4.md, 0.2" misconception)
  - `EQ-M-ERV-MAN-EXH` is full, 10 of 10; the x=2'-10" lane crosses only one sibling
    radial vs eight at the manifold's east end.
  - `AL-A-COMBO` is in `RM-A-STUDY`, `AL-A-STUDIO` in the studio — reversed is a hard
    FAIL: `code.R315_co_every_sleeping_area` fails if every CO alarm on a storey is inside
    a bedroom.
  - `code.N1103_6_whole_house_ventilation` sits at 210 cfm provided against 205 required
    (MN 1322 R403.5) — a seventh bedroom or ~250 sf more conditioned floor fails it.

- **`FO-A-STAIR`'s WEST edge is the stair head, `x=22'-5 3/8"`, not the source's 21'-2"**
  (moved 2026-09-15). ST-S2A spends 3'-0" on its winder box and 12 goings at 10" on the
  straight run, so it tops out there; 21'-2" left a **15 3/8" x 3'-0" hole at the head of the
  stair**, which `code.R311_7_5_1_stair_end_risers` passed because it reads the arrival deck
  through the well and never asks where in it the flight ends.
  `code.R311_7_6_stair_arrival_floor` is the rule that asks in plan and the one that found
  it. The north, east and south edges did not move.
- **`P-M-STRWELL-SS` is ST-M2S's third well post** (`y=31'-0 3/8"`, 2026-09-15). The two
  half-landings are no longer the same rectangle: ST-M2S carries 13 treads over two flights,
  7 and 6, so the upper half-landing starts one going further south — at its own flight's
  springing — and that corner is a rim end no host wall reaches. Over `FO-M-STAIR`'s hole, so
  full-height to `SL-B-FLOOR` like the two beside it, not a squash block like
  `P-M-STRLAND-SE`. See `notes/u_stair_split_landing.md`; move ST-M2S and all three move.
- `W-A-SN` is a 12 3/4" bookcase wall (`INT_2X4_BOOKCASE_12`); its south face is the only
  cover for `FO-A-STAIR`'s north edge — moving it north FAILs `code.R312_1_guard` (~14'-3"
  unguarded well). It was thickened, not moved (face held at 8'-9 5/8"), why
  `N-A-C2`/`N-A-E1` sit at y=9'-4". Do not split the wall to thin its west 1'-6" — a 4
  3/4" wall there puts the south face 4" north of the well edge, re-opening the FAIL.
  `interior_room="RM-A-STUDY"` is load-bearing on this `Wall` (asymmetric stack-up) —
  without it `orientation.wall_outward_sign` may put the gwb face on the well edge.
- `RM-A-STUDY` reads 165 sf (was 159) because `resolve/rooms.py` builds the room face from
  wall centrelines and the axis moved 4" north though the south face didn't —
  `code.R312_1_guard` (wall footprint union) still passes. `RM-A-EAST-UNFIN` loses the
  same 6 sf (STORAGE, no glazing rule binds).
- Study casework must NOT become a placeable — catalog bookcases are 1'-0" deep against a
  9 7/8" pocket (2 1/8" proud into the well). Priced via `prices.toml [allowances]` lump
  `cabinet-study-bookcase-wall`. `D-A-STUDY` is `DT-INT-BOOKCASE30` (retyped in place);
  `trimless=True` means a millwork case here, NOT the drywall return jamb it means
  elsewhere — never price off `DT-INT-SWING36-TRIMLESS` (which replaced
  `DT-INT-SWING30-TRIMLESS` on 2026-09-15 when `D-M-BED2`, its only door, widened).

- **Roof is flash-and-batt in the joist bay**: 11-7/8" TJI 230 @ 24" o.c., 5" ccSPF
  against the deck underside + R-30C batt in the remaining 6-7/8", 5/8" CDX plywood,
  self-adhered butyl membrane, standing seam. R-53.2 at 13.1" deep; interior is paint on
  gypsum only. Oracle: `notes/roof_flash_and_batt.md`. (→ log4.md, prior nailbase stack +
  cost delta)
  - Legal with ZERO above-deck foam under IRC/MSRC R806.5 item 5.1.3 (air-impermeable
    insulation at the sheathing meets Table R806.5, air-permeable insulation directly
    under it): 5" ccSPF = R-32.5 against R-25 (zone 6)/R-30 (zone 7). Graded by
    `code.R806_5_unvented_roof`. NO interior Class I vapour retarder, ever — item 2 makes
    a ceiling poly or vapour-barrier primer a code-FAIL, not just a preference.
  - Condensation check reports NOT_APPLICABLE on this roof by design — a steady-state
    Glaser walk can't grade a stack sealed cold-side by a 0-perm metal panel.
    `condensation._r806_5_deferral` defers ONLY where `code.R806_5_unvented_roof` passes.
  - Do not restore a permeable underlayment/vent mat — the impermeable panel above now
    leaves no gap to dry into. The butyl membrane replacing both self-seals ~1,160
    standing-seam clip screws, this roof's real water risk.
  - 24" o.c. spacing is NOT FINAL: `structural.rafter_span` is UNKNOWN/engineered at both
    16" and 24" o.c., and the printed TJ-4000 table assumes bearing at the high end where
    these joists instead HANG off the ridge on 38 LSSR hangers — confirm in ForteWEB
    (fallback TJI 210 @ 19.2" o.c.). Budget for
    upsized eave uplift ties (H10A+); don't bank the H2.5A count falling 378→360 — catlin
    frames SPF at SG 0.42 against H2.5A's SG 0.50 rating, with 1.5x the tributary.
  - The roof deck oversails the last rafter and spans the wall girts, clipping at the
    cladding's back face — that cantilever is graded by nothing in the engine. Stack depth
    is hand-transcribed into `params/roof_trim.py` (`_DRIP_CEILING_IN`,
    `_CLADDING_HEAD_IN`) and into `test_catlin_eave_water.py` — moving a layer must move
    both.

- **Structural ridge, not a rafter-tie roof**: `RB-HOUSE` bears continuously on the
  `W-A-C1/C1B/C2` bearing wall (unbroken to footings), keeping rafters simple spans and
  thrust off the eave line — a beamless center line dumps ~1.5 klf of thrust into a 1 1/2"
  rafter plate that can't take it.
  - Section is `2-1.75x16 LVL`; depth is a HANGER dimension, not span-driven — the beam
    must reach 14.15" below the ridge at the rafter's plumb cut (14" misses by 0.15", 16"
    clears). LVL comes in 9.5/11.875/14/16/18", no 14 1/4". Beam hangs 16" into the room.
    3 1/2" width only works because demand is small, and the 1-1/2" LSSR header nail that
    keeps mirrored patterns on 28 opposing rafter pairs from overlapping is a **published
    row**, not an ER-280 §3.2.2 derivation (C-C-2026 p. 178 sloped-only, DF/SP: 1,175 lbf).
    The connection is capped by the TJI's end bearing at **1,090 lbf** (TJ-4000 Jul 2025
    p. 15, sloped-only — 1,565 is hanger-side-only and 1,060 is the *skewed* row), against
    ~980 lb/rafter: d/c 0.90.
  - Peak hardware: 38 beveled web stiffeners both sides (23/32" ply ripped 4" wide — NOT a
    2x4, cavity is 15/16" a side), 19 LSTA24 over the top per pair (mandatory above 3:12
    per Weyerhaeuser H5S), 10 H2.5A tying beam to plate at 4' o.c. (`uplift_path.py` skips
    a `Beam.bearing_ref` that resolves to a wall, so this joint had none before).
  - Ordered as three 12' pieces, not one 36' stick — `FramedMember.continuously_supported`
    sends a beam supported everywhere to the stock ladder. Cap is handling
    (`_MAX_SPLICE_PIECE_FT` in `takeoff/framing.py`), not stock — plies stagger 6+12+12+6.
    `structural.ridge_beam_depth` grades the depth.

### Windows and facade

- **Window RO ladder.** Three caps, arithmetic on the 16" module and 1.5" stud, enforced by
  `structural.window_framing_module` (`preferences.toml [framing]`):

  | RO | studs broken | clear-width math | head framing |
  |----|--------------|-------------------|--------------|
  | **14"** | 0 | one bay: `16 - 1.5 = 14.5"` clear | none — the bay's own two studs carry sill/head nailer |
  | **30"** | 1 | `32 - 1.5 = 30.5"` clear | R602.7.4 NONBEARING: single flat 2x4 header, no jack |
  | **27"** | 1 | 30.5" less a jack each side | R602.7.5 BEARING: header on a jack each end, packed against kings |

  - The 3" between the 30" and 27" caps IS the pair of jacks — the cap is purely a function
    of the wall's bearing status, same module/stud/broken line both ways. R602.7.5's
    approved-framing-anchor alternative would buy the 3" back but is declined deliberately
    (per-opening hardware/detail costs more than it saves); raise `max_window_ro_bearing_in`
    deliberately if ever needed.
  - **Modelling gap:** `needs_jamb_pack` keys off whether the RO breaks a stud, not
    `structural_role`, so it frames a full king/jack/header pack on nonbearing 30" windows
    too — the 30" cap is correct about what's buildable, conservative about what the model
    draws; widening the gap is not fixing it.
  - RO position is a property of the RO **width**, not the wall — resize windows to the grid,
    never move the grid to fit a window
    (`test_catlin_contract_m3.py::test_catlin_window_openings_follow_their_walls_framing_module`).

- **Width/height families.** Five widths carry the house: WT-1424, WT-2736, WT-3036 (north
  gables/hall), WT-3048 (south glazing, head 6'-8"). The 27" family carries FOUR heights
  (36/48/54/64"); the 14" family THREE (24/36/48"). **WT-2764 and WT-1448 are
  CATALOG-ONLY** (superseded by WT-2754, WT-1436 under the 6:12 rake); WT-2464 is also
  catalog-only. Retired sizes stay priced (same convention as `glazed-green-brick`,
  `EXT_2X6_SWINBURNE`). The bearing cap bounds width, so when an opening needs more
  area/head-line/composition, **height** is the only dimension left to spend — hence the
  exceptions below, not drift from "one type per width family."
  - **Every window is on its ideal station; the exception list is empty**
    (`test_catlin_contract_m3.py::test_catlin_window_openings_follow_their_walls_framing_module`).
    Keep it empty — see **ONE GRID PER FACADE** before concluding a window can't reach its
    station.
  - **Six height exceptions** (an extra height on an existing family, cheaper than a new one):
    - **WT-1448** (south flankers, catalog-only): 14" takes no header, so only the glass
      answers to the rake; any wider unit's header is what the rake won't take.
    - **WT-1436** (south flankers): third height on the 14" family — 5'-8" head fits the
      6:12 rake's clearance (`2 x (head+2")`) at 12'-8"/23'-4" with 4" to spare, where
      WT-1448's 6'-8" head does not fit anywhere a mirrored pair could use. Also keeps
      `RM-A-STUDY` on R303.1 daylight (165 sf needs 13.2 sf; gives 13.625) without
      Exception 1's electric-light substitute.
    - **WT-3048** (south glazing): the 30" family's committed 36" height would drop the
      south head off the house's 6'-8" door-head line.
    - **WT-2748** (`WIN-M-EAST-MID`): bearing cap forced 30"→27"; 48" is a pure retype
      (same 2'-8" sill, same 6'-8" head) — the cheapest of the six.
    - **WT-2754** (`WIN-S-BED1`/`BED2`): 27" cap, single-window bedrooms — 27x48 (9.00 sf)
      fails BED2's 9.945 sf R303.1 requirement; 27x54 (10.125 sf) passes. Code necessity.
    - **WT-2764→WT-2754** (`WIN-A-S-JUL-W`/`-E`, catalog-only, NONBEARING walls W-A-S2/S3):
      the only composition-choice exception and the only nonbearing one. Growing the pair
      closes the gap between the units to a 21" clear bearing pier (14" required) without
      moving either centre off its stud line.

- **Facade alignment — ONE GRID PER FACADE.** `EXT_2X6`/`PLANT_EXT_2X6_HUMID` set
  `layout_origin="line"`, so a wall segment lays out from its **layout line** (the derived
  chain of collinear, stacked walls, `resolve/layout_lines.py`), not its own start node.
  Every facade segment, every storey, sits on one 16" grid off the house origin: a stud line
  at `x ≡ 0 mod 16"`, a bay centre at `x ≡ 8" mod 16"`. A window's legal stations are a
  property of the facade, not any one node — moving a node no longer re-phases anything.
  `test_catlin_contract_m3.py::test_catlin_window_openings_follow_their_walls_framing_module`
  asserts an EMPTY exception list. Keep it empty.
  - **The 8" rule is the only phase rule left.** A 14" RO sits on a bay centre, a 27"/30" RO
    on a stud line — 8" apart — so a 14" unit can never column with a 27"/30" unit anywhere
    in the house (e.g. `WIN-M-BATH2`); retyping the narrow unit is the only fix.
  - **A node move is cheap; a window move is global.** A node may move freely, but a window
    off the grid stays off it, and a facade whose windows disagree with the grid can't be
    blamed on authoring order.
  - **A tee is not a wall end.** Where two collinear segments provably share one grid,
    `framing/solver.py::continuation_roles` drops both segments' end studs so the module
    runs through, one `"owner"` claiming the seam. The **stand-off band**
    (`framing/furring.py`, where cladding lands) reads the same way — a HORIZONTAL band
    (the catlin truss girt courses) also continues through a seam via
    `_furring_module_signature`'s `direction`, or every tee would notch every course. The
    girts' **blocks**, one under every course on every OTHER stud, phase-lock to the layout
    line on a 32" grid instead. Pinned per facade by
    `test_catlin_contract_m3.py::test_each_facade_block_grid_is_one_grid_on_every_storey` and
    `::test_no_facade_stud_stands_off_the_module_except_at_a_corner`. Only corner packs and
    jamb packs (which sit where their ROs put them) are off this grid.
  - **Interior bearing walls opt in too**, STRUCTURE layer only (no liner-band phase-lock,
    unlike the exterior pair): `INT_2X6_BRG`/`PLANT_INT_2X6_BRG_HUMID` (the x=18'-0"
    **centreline**, `W-M-C1..C5B`/`W-S-C1..C4B`/`W-A-C1..C2`) and
    `INT_2X6_BRG_EXPOSED_PLY` and its two variants `STAIRWALL_INT_2X6_BRG_TYPEX`/
    `_UNDERSTAIR` (the **stair line**, `W-B-STR/STR2/STR3` under `W-M-STRW/STRW2`). **No code compels this**
    (R602.3.3 is the bearing-stud rule; R602.3.2's single-top-plate exception is about
    rafters/joists centred over studs within 1"; in-line framing is an APA technique) — done
    because the centreline carries `RB-HOUSE` continuously to the footings. Pinned by
    `test_catlin_contract_m3.py::test_the_centreline_bearing_wall_is_one_stud_grid_on_every_storey`
    and `::test_upper_storey_studs_stand_over_studs` — 94 of 237 stacked upper-storey studs
    still stand over nothing (down from 113), a **ceiling, not a target** (correct framing
    never reaches zero). Caveat: a line's grid phase is set by `layout_lines._orient` off its
    own extreme member end, not the house origin — the centreline matches the house's 16"
    grid by luck (it ends at y=0); `LL-W-B-STR` starts at y=216" and sits 8" off.
    **Not opted in, deliberately:** `INT_2X4_PARTITION`/~46 other non-bearing partitions, and
    the *staggered* assemblies — never widen into the latter without reading `plans/TODO.md`
    first (`framing/solver.py`'s face-parity rounding at a 4"/12" phase would collapse runs
    onto one face and destroy the acoustic decoupling; it can't fire at the staggered walls'
    universal phase 0.0, and a non-zero phase is exactly what opting in would hand it).

- **Minting a wall tag** (decision #72). A tag is ONE geometry stack: same detail drawing,
  same IFC wall type, same takeoff row, same condition keys. Before adding one, check
  whether the difference is already sayable. A **material** is `Wall.layer_materials` (the
  mudroom's DF studs on `INT_2X6_BRG_EXPOSED_PLY`). What the wall **lands on, or its
  height**, is `Wall.base_elevation`/`top`/`FoundationWall.top_elevation`. A **room-side
  finish** over a base with a `default_lining` is `Room.wall_lining`. A stack that **shares
  most of a base** is `variant_of` + `substitute` — the card prints "variant of X" and the
  shared layers track the base forever. A tag **nothing references** is deleted unless it is
  a named revert with a note (`EXT_2X6_SWINBURNE` is one). Stars curate the *permit* set and
  are not a reason to keep a tag. `advisory.assembly_variety` FAILs a material-only twin and
  prints the inventory; catlin must stay clean.
  - The UI's assembly inspector **refuses to edit a variant's layers**
    (`source/assembly_ops.py`): duplicate first, and the duplicate is flat.
  - `PLANT_EXT_2X6_HUMID` is deliberately NOT a variant — see its own note in
    `plan/assemblies.py`.

- **Columns.** South face stacks columns at x 4'-0"/32'-0" (main+second); second adds
  9'-4"/26'-8" (none on main); both mirror about x=18'-0" (main: 4'-0"/14'-8"/21'-4"(door)/
  32'-0"; second: 4'-0"/9'-4"/14'-8"(door)/21'-4"(door)/26'-8"/32'-0" — every pair sums to
  36'-0"). Attic gables do not join these (see **Gables**).
  West face stacks FIVE (y 5'-4", 10'-8", 20'-0", 24'-8", 31'-4"): first three 27" family on
  a 3'-0" sill; fourth pairs tempered 14" awnings (`RM-M-BATH1`/`RM-S-VANITY`) on a 3'-6"
  sill; fifth pairs `WIN-M-MUD`/`WIN-S-BATH-W`, also 3'-6". The 27" units share one 6'-0"
  head line; the two 14" pairs share the 4'-6" centre line instead (see **Head lines**).
  `WIN-M-BATH2` is WT-2736-T (retyped from WT-1424-T) at a 3'-0" sill to reach the third
  column (the 8" rule, also satisfying R303.3's window alternative). West attic pair:
  4'-8"/31'-4", symmetric about y=18'-0" (→ DESIGN-LOG.md for the chase/backing history).
  **The north face has no column, a deliberate trade** (→ DESIGN-LOG.md): the upper facade
  reads as one rectangle instead — `WIN-A-N1`/`WIN-S-STAIR-N` at **12'-0"**,
  `WIN-A-N2`/`WIN-S-HALL-N` at **24'-0"**, each attic unit over its second-storey partner,
  mirrored about the ridge. Since 2026-09-10 **all four are 27" wide** (attic WT-2736,
  second WT-2748), so the two stacks are columns of one width and one rough opening rather
  than four squarish 30x36s. `from_node` resolves to the near JAMB, so every one of those
  four offsets grew 1 1/2" to hold its centre — do the same on any future retype here. `WIN-M-KITCH` stands alone below, dead-centred on the sink run.
  `WIN-S-BED3-N` (WT-1424, x 34'-0", sill 4'-0") sits over `WIN-M-KITCH-N`, completing a
  **corner pair** with `WIN-S-BED3` (east wall y=34'-0", each 2'-0" off the corner) — a
  two-storey column — and satisfies R303.1 Exception 1 for `RM-S-BED3` (12.2 sf glazed/6.1
  sf openable against 10.32 required). The kitchen counter run (5/8" scribe + B15 + DW +
  SINK-36 + B30) has no slack; the window column follows the sink, never the reverse
  (`plan/placeables.py` kitchen header).

- **Rows.** Where a column is impossible, the storey's rhythm must be centred, not merely
  even. East second storey: 4'-0"/13'-4"/22'-8"/32'-0", mirrored about y=18'-0" in station,
  width (27/30/30/27), and head (6'-0"/7'-0"/7'-0"/6'-0") over one 3'-0" sill — a 9'-4" beat
  three times over (→ DESIGN-LOG.md).
  East main row: 4'-0"/13'-4"/18'-8"/34'-0" — the last gap deliberately ends a blank kitchen
  stretch. First three: 27" units on one 2'-8" sill, 6'-8" head. `WIN-M-KIT-E` is a 14" unit
  at a 3'-6" sill (bay centre, 408" off `N-M-SE`) — joins neither beat nor head line, closes
  the row's north end as a service window (can never column with the 27"/30" family beside
  it — the 8" rule). `WIN-S-STUDY3` at 4'-0" columns with `WIN-M-LIV-E1`. **Check
  `out/render/elev_east.png` before touching this row.**
  The fireplace pier sits between `WIN-M-LIV-E1`/`E2`: a 45 1/2" facebrick surround
  centred y=8'-8", walnut mantel at 5'-4". No window moved for it — the pier centre is a bay
  centre on `W-M-E1`'s grid. **The firebox sill NO LONGER shares the east row's 2'-8" line**
  (2026-09-11): the owner reversed that morning's decision to raise it and it is back at
  **24" AFF**, so the one-datum-four-openings argument is retired and the fire does not
  column with `WIN-M-LIV-E1`/`-E2`. That is a preference call overruling a design argument,
  not a correction of one — the record and the cost are in `plan/electrical.py`'s
  `EQ-M-FIREPLACE` block and `plan/storeys/main.py`'s `W-M-FIRE-*` block; do not restore 32"
  without asking. `notes/east_breast_bearing.md` carries the bearing and the joist pockets —
  **`haus check` grades ONE thing about this panel and only one**,
  `structural.through_deck_clearance` (the pier/joist gaps and the bearing under the piers).
  Nothing grades the ties, the lintel, the mantel hold-down or the heights
  (`mn_residential/profile.py` disclaims R1001-R1004).
  - The firebox is **seven walls, not one**: `W-M-FIRE-STUB-S`/`-M`/`-N`/`-PLINTH`/`-JAMB-S`/
    `-JAMB-N`/`-HEAD`, all `FIREPLACE_BRICK_WYTHE`, NONBEARING, stacked on x=35'-1 11/16" with
    **its own `open_end` node pair each** (a shared node collapses every junction polygon it
    touches). Masonry opening **29 1/2" x 20 5/8"** (sill 24" AFF, head 44 5/8" AFF) is the
    gap between elements, not a subtraction from one; elevations off the +15/16" finished
    floor: STUB -13 7/16"→+15/16", PLINTH →24 15/16", jamb piers →45 9/16", HEAD →64 15/16".
    - **The buried stub is THREE PIERS since 2026-09-19 and the joist pockets are the gaps
      between them** — the same idiom one level down. `FO-M-FIRE` is RETIRED: the premise it
      was framed on ("the brick cuts the joists short of their bearing") was never true, the
      brick is 3 5/8" thick and stands 2 1/2" clear of a 5 1/2" mudsill, and `FS-M-EAST`'s
      joists run CONTINUOUS through the panel. Piers at y 81 7/8"–94" / 98"–110" /
      114"–126 1/8", two 4" pockets on joists 006 (y=96") and 007 (y=112"). Clearances
      5/8" / 3/4" / 3/4" / 5/8", graded by `structural.through_deck_clearance` against a 1/2"
      threshold; the 5/8" pair is residue of a 44 1/4" panel on a 16" module, not a chosen
      margin. Gone with the opening: a 2-ply LVL header, four full-span 17'-11" trimmer plies,
      two LUS, two HHUS410 and the I-joist web stiffeners — and with them the joist maker's
      header table, the one outstanding document in the detail. **The subfloor cut round the
      piers is DERIVED** (`resolve/through_deck.py`, decision #78); nobody authors it. The
      pockets stay **open and un-mortared** and the plinth wants a **bond break** over each.
      **Do not widen them past ~4 1/2"**: TMS 402's pier/column line is 3t = 10 7/8" and the
      12" middle pier has 1 1/8" of room.
    **The 8" the plinth lost went into the HEAD, not into the panel** — `W-M-FIRE-HEAD` is
    19 3/8" tall, not 11 3/8", so the panel top holds at 64 15/16" absolute, the mantel stays
    on the brick, the hand-measured 0" BESTA gaps stay true and brick stays 20.4 SF (19.6 SF
    since the pier split, which takes 8" of width out of the buried course). Sill is
    9 modular courses exactly; zero cut closers on the visible 45 1/2" opening; head is a
    deliberate CUT COURSE at 16.7 courses (a course line gives 18 2/3", ~1" of daylight) —
    steel angle lintel, not a rowlock. The $/SF rate deliberately does not drop — a mason
    bills the panel on a job this small; re-rating down would deduct twice.
  - **The surround is laid in the court's BROWN blend and WASHED WHITE, since 2026-09-13.** It
    ordered `white-brick` until then, which was never a designed choice — the Material was
    sourced to the retired porch parapet and `brief.md` says only "white metal skin". One blend
    house-wide removes a third cube of special-order brick against ~21 SF of need (~53 SF never
    laid), its 1.5-2x premium and lead time, and a second colour for the mason to lay to a line.
    **The estimate moves $0 on brick** — both rows price $/SF of face laid, so the cube arithmetic
    is off-model; do NOT re-rate the material half down to "book the saving".
    - **The wash is the LAST layer, and this is the trap.** These five walls are their own
      `open_end` node pairs, find no closed walk, take outward sign +1, and are authored S->N — so
      layer 0 lands EAST, against `W-M-E1`'s studs. `layers=(brick, wash)`. Nothing grades it:
      `advisory.cladding_side_mismatch` inspects CLADDING layers and this assembly deliberately
      has none. `test_masonry_finish.py::test_fireplace_wash_faces_the_room` is the only guard.
    - `LayerFunction.FINISH`, **not** CLADDING — CLADDING would drag a brick panel standing inside
      a conditioned room into the Glaser scope. Both are in `_BILLABLE`, so billing is identical.
      **No `ControlLayer.VAPOR`**: a silicate wash is ~80 perms, the opposite of a retarder.
    - Accepted render loss: the washed face reads as a flat near-white plane, not coursed brick
      (the wash is not in the masonry family). Coursing still shows on the 3 5/8" reveal returns.
      Do **not** reach for `Wall.layer_materials` to fix it — `resolve/topology.py` substitutes on
      the *resolved* layer, so the BOM row would follow it back to `white-brick`.
    - Sequencing, and it is real: the Amantii BI-30-XTRASLIM is **trimless** (the brick runs to
      the glass edge), so the wash stops at the reveal returns and goes on **before the appliance
      is set**, or is masked. The walnut mantel goes on **after the wash cures**; its hold-down
      blocking is still pre-brick. Mineral silicate on brick is non-combustible, so no clearance
      number moves.
    - Geometry: the stack totals 3 3/4" rather than 3 5/8", so the centred panel drifts 1/16"
      west and the overhang past `W-B-E1`'s pour goes 1/8" -> 3/16". Below every tolerance in
      `notes/east_breast_bearing.md`, whose numbers all stand (both bricks are 1,920 kg/m3).
  - **The lintel is `BM-M-FIRE-LINTEL`, a `Beam`, since 2026-09-11** — it was prose in three
    files and an element in none. There is no lintel type in the engine and
    `FIREPLACE_BRICK_WYTHE` carries no `MasonrySpec`, so a `Beam` (free-string `size`, two
    ends, a span) is the closest honest schema. It runs `N-M-FIRE-JS-S`→`N-M-FIRE-JN-N`, the
    whole 45 1/2" panel, so 8" of bearing lands on each jamb pier and no node had to be
    invented; `top_elevation=inch(49.0625)` puts the horizontal leg on the jamb tops at
    45 9/16" with the vertical leg in `W-M-FIRE-HEAD`'s bed joints. Piece is an
    **L3-1/2 x 3-1/2 x 1/4 A36 HDG angle**, named in `engineering_note` (a `Beam` has no
    `source` field). **`size="3.5x3.5"` is the angle's BOUNDING BOX and it is the trap here**:
    `cross_section` parses that and only that — `"L3-1/2x3-1/2x1/4"` or a trailing `" STEEL"`
    both fall silently to the 1.5x5.5 rectangle. The drawn solid is ~2.7x the steel. It bills
    at **$0**: a `Beam` reaches the estimate through its `assembly` as a `beam · <assembly>`
    cubic-yard row, this one has none, and a volume rate is the wrong shape for an angle
    anyway — the dollars want an `[allowances]` lump.
  - `FO-M-FIRE` is **RETIRED (2026-09-19)** — see the pier split above. Its two live engine
    traps are salvaged onto `FO-M-ERV-OA`'s note, which already cross-referenced them: the
    **first trimmer ply's AXIS sits on the opening edge** (draw an outline at the size of the
    thing passing through and the ply stands inside the hole), and **`header_size` branches
    on `w_ft <= 4.0`**, so 48.0" arriving as `4.0000000000000009` after a metre round trip
    takes the wrong branch silently. (`haus check` grades floor-opening headers at EIGHT feet,
    gated on a sawn-joist profile, so an I-joist opening draws the same header at any span.)
  - The mantel is `FURN-M-FIRE-MANTEL`/`FT-MANTEL-WALNUT-46`, a wall-mounted placeable
    (`FURN-B-PLAY-TV` idiom), 45 1/2"x11 1/2"x2 1/4", meant to sit 64"–66 1/4" AFF on
    `W-M-FIRE-HEAD`'s top (`depth` DELETED so `_carcass_depth_m` inherits from the type).
    **`Mount.elevation` IS OFF THE ROOM'S FINISHED FLOOR, and the guide said the opposite
    until 2026-09-11.** `resolve/placeables.py::_floor_elevation` returns
    `room_finished_floor_elevation(...)` and `resolved_mount_elevation` adds the mount to it;
    the subfloor plane it also resolves is only what a CEILING mount hangs from. So the
    authored `inch(64.9375)`, written for the old subfloor reading, resolves to **65 7/8"
    absolute — the mantel would float 15/16" OFF the brick, at 0 FAIL**. **Fixed the same day:
    `plan/placeables.py` now authors `elevation=inch(64)`**, and the comment block there that
    argued for the subfloor reading is rewritten rather than deleted. `EQ-M-FIREPLACE`
    was always authored on the correct reading (`inch(24)` = 24" AFF, landing exactly on the
    plinth top), which is how the two were told apart. `work_surface` is UNSET, not False, to stay out of NEC 210.52(A)'s
    wall-space rule. `[allowances] finish-fireplace-mantel-walnut` is **deleted** (not
    zeroed) and `[placeables] "FT-MANTEL-WALNUT-46"` carries the scope instead — an unpriced
    type is silently dropped from the bill.

- **Knee band — GONE.** East/west knee walls are 1 1/2" rafter plates now with no glazing,
  so `WIN-A-W-S`/`-N` and `WIN-A-E-S`/`-N` are deleted; those facades stop at the second
  storey (two storeys there, three on the gables, per
  `test_each_facade_block_grid_is_one_grid_on_every_storey`). The stair well's east edge
  lost its guard with the wall, so `RL-A-STAIR` gained a 3'-0" east leg (`code.R312_1_guard`).

- **Head lines.** West face: the 27" units head on one 6'-0" line off a 3'-0" sill.
  **The 14" family does NOT — it holds the 4'-6" CENTRE line instead (owner, 2026-09-12).**
  Four leaves (`WIN-M-BATH1-W`, `WIN-M-MUD`, `WIN-S-VANITY-W`, `WIN-S-BATH-W`) came off a
  4'-0" sill onto **3'-6"**, so they head at 5'-6". The arithmetic is exact and is the whole
  reason: a 27" unit spans 36"..72" and is centred at 54"; a 24"-tall unit at a 3'-6" sill
  spans 42"..66" and is centred at 54" too. At 4'-0" they shared the head and stood 6" high
  of that centre, leaving a deep blank sill under each small unit. **A 14" unit on this face
  is dimensioned from the centre line, never from the head line** — and the 27" units did not
  move. Pinned by `test_the_west_facade_stacks_five_two_storey_window_columns`.
  South face shares a 2'-8" sill. `WIN-S-BED3-N` is a
  WT-1424 at a 4'-0" sill (as is `WIN-S-BED3` around the corner), so it heads at 6'-0" —
  leaving the east face's 3'-0" datum (`WIN-S-BED1`/`WIN-S-BED2` still hold it) when it was
  retyped down to a 14" unit, the rule working, not an exception.
  **The north second storey is a ROW, not a head line**, and this entry claimed otherwise
  until 2026-09-10. `WIN-S-HALL-N`/`WIN-S-STAIR-N` are **WT-2748 at a 3'-4" sill**, heading
  at 7'-4" — the highest heads on the storey, 4" over the east row and 16" over
  `WIN-S-BED3-N`. (They were never on the 6'-0" line: commit `5487fd79` had put them at a
  3'-6" sill and a 6'-6" head with no note.) **A 48" unit cannot satisfy either half of the
  NEW-OPENING RULE on a 24" module** — the head half wants a 24" or 48" sill, the sill half
  wants 27 1/2" or 51 1/2", and they never meet, so every exact hit on offer drags a sliver
  with it for no net board saving. The rule's real intent is no redundant board, so this
  pair sits CLEAR of the courses instead, in the 2'-10 1/2"..3'-5" band; 3'-4" is its top
  even inch and it took `test_truss_girt_courses.py` from 33 slivers to 31.

- **Gables** read symmetric about the ridge before answering to anything below. The north
  gable is symmetric at **12'-0" / 24'-0"** (144"/288", both stud lines, mirrored about the
  18'-0" ridge — see **Columns** for why those stations also stack the second storey).
  **The rake is binding here and holds by 6 1/2"**: outer jambs land 130 1/2" from their
  eaves against the 124" a 5'-0" head needs; `structural.truss_wall_opening_support`
  confirms both jamb pairs bear on an outrigger within 1", and there is no third bay
  outboard — **this pair cannot move out again without a shorter unit.** The pair is
  **WT-2736** since 2026-09-10 (30x36 read too square), matching the second storey's new
  27" width so the stack is a column of one width, the attic unit simply 12" shorter under
  the rake. It could not grow taller with the pair below: a 48" unit here needs 148" of run,
  and buying the height off the sill instead lands under R312.2's 24".
  Recheck before any further move: the radon riser is 11 1/8" clear of `WIN-A-N1`'s west
  jamb (`mep_venting.py`), the PV junction box 6 1/2" clear of its framing bumper
  (`electrical.py`) — both widened by the narrowing, and a rewidening spends them back.
  `WIN-A-N1` (hosted on `W-A-N2B`) has RO 10'-10 1/2"..13'-1 1/2", clearing the x=10'-0"
  split by 10 1/2";
  at x=12'-0" it fronts `FO-A-HALL`, daylighting the stair void rather than a room — an
  amenity, not a code problem.
  **The south gable carries FOUR openings**, mirrored about x=18', reading west→east S2,
  JUL-W, JUL-E, S3. Tags gap at S1/S4 rather than renumber (would break the surviving units'
  GlobalIds):

  | station | tag | type | head | outer jamb | allowed | margin |
  |---|---|---|---|---|---|---|
  | 12'-8" / 23'-4" | `WIN-A-S2` / `WIN-A-S3` | **WT-1436** (14x36) | 5'-8" | 145" / 144" | 140" | ✓ 4" |
  | 16'-0" / 20'-0" | `WIN-A-S-JUL-W` / `-E` | **WT-2754** (27x54) | 7'-2" | 178 1/2" | 176" | ✓ 2 1/2" |

  One 2'-8" sill under all four, heads stepping with the rake. Juliets hold a 21" clear
  bearing pier under `RB-HOUSE`'s south bearing point (14" required).
  **The corner pair (`WIN-A-S1`/`S4` at 3'-4"/32'-8") is deleted, and its 8" column miss**
  (against the 4'-0"/32'-0" column below) **is permanent** — at 6:12 there's 21 1/2" of roof
  over the floor there, a 14" RO must sit on a bay centre, and every south column below is
  on a stud line. **Do not "fix" that 8" by moving these two** — it trades a clean framing
  module for a header the rake will not take.
  The mirror about x=18' is the rule that actually governs a gable, and the one thing that
  has survived every position tried here.

- WT-1424 is still used wherever a bigger unit won't fit — chiefly the mudroom. Under the
  south rake it handed off to WT-1448, then WT-1436 (→ DESIGN-LOG.md).

- **Tempered twins.** `WT-1424-T`, `WT-2736-T`, `WT-3036-T`, `WT-3048-T` match their parents
  in every dimension, differing only in glass, for the ten R308.4 units (wet room, within
  24" of a door, within 60" of a stair). Not width families — no facade/framing rule sees
  them; adding a tempered unit is a retype, never a move. All three glazed *door* types are
  tempered outright (R308.4.1 has no location test).

- The east bearing wall (`WIN-S-BED1`/`BED2`) takes the standard bearing cap — 27"
  (`WT-2754`/`WT-2754-T`), same rule as every other bearing wall. An earlier 30" exception
  here was tried and reversed (→ DESIGN-LOG.md). Lesson: when a width cap looks like it
  forces an R303.1 area failure, check height before moving the cap — area is width x
  height.

### Ventilation, ducts and soffits

- **ERV: Broan B210E75RT, home-run distribution in STANDARD PARTS** (`plan/mep_erv.py`).
  Redesigned 2026-09-12 (BLD-08): the topology did not change, what it is built from did.
  - **No proprietary tube anywhere.** The 160 mm/75 mm radial manifold and its semi-rigid
    tube had three US sellers and no Minnesota dealer, and the owner's decision is not to
    buy one. Every radial is **4" galvanized snap-lock** (`material="galvanized"`), every
    trunk, riser and outdoor leg **6" galvanized**, every terminal a **4"-collar** commodity
    diffuser or bath grille, and every manifold a **fabricated galvanized plenum** — 8" inlet
    collar, N x 4" start collars each with a butterfly damper, mastic-sealed — from any
    sheet-metal shop, exactly as `EQ-T-ERV-MIXING-BOX` already is. Tags did not change
    (`EQ-T-ERV-MANIFOLD-6/-6-EXH/-10`); five `type_ref`s, the price rows and the goldens key
    on them. **4" and not 3" is a CATALOGUE decision, not a pressure one**: 3" pipe and
    collars are stocked but 3" dampers and grilles are a thin Amazon-grade catalogue.
  - **The fan curve is typed data now, and it closes `plans/buildability.md` open question
    3.** `EQ-T-BROAN-B210E75RT.fan_curve` carries all ten published points (214 cfm @ 0.1"
    w.g. down to 176 @ 1.2") plus `fan_curve_max_static_in_wg=1.3` — a HARD CEILING above
    which the core deforms, a different statement from the curve's last point. The old
    "0.2" vs 0.4"" argument was never a disagreement: they are two stations on one curve.
    **`ventilation_cfm` stays 210** and it is a design INTENT, not a promise the curve can
    keep — no real duct system lands under 0.2" w.g. The number that governs is MN 1322
    R403.5's **205**.
  - **Three new checks.** `mep.erv_static_budget` (ADVISORY) computes Darcy-Weisbach/Colebrook
    over the whole system and reads the curve at it: **0.350" w.g. worst path, 207 cfm
    delivered**, on the EXTRACT side. It reports the 3 cfm against the 210 design rate as
    UNKNOWN, never a FAIL — whether 207 is ENOUGH is
    `code.N1103_6_whole_house_ventilation`'s question, asked against MN's 205 and not against
    a designer's hope. **The extract side was authored at 265 cfm against a 210 cfm machine
    until 2026-09-15** — summed per plenum and never per side, which is why nothing caught it.
    The governing side swapped three times that day: rebalancing took the worst path off
    DU-M-ERV-R-PLANT and the static 0.459 -> 0.417; `DU-ERV-EA` at 8" took extract to 0.355
    and handed the lead to supply at 0.406; moving both hoods to the NORTH face let
    `DU-ERV-OA` go to 8" as well (0.132 -> 0.032) and handed it back to extract at 0.350.
    `mep.erv_manifold_ports` (INTEGRITY, **blocks**) grades the "10 of 10" prose.
    `mep.room_heat_source` (ADVISORY) is the radiant arithmetic. Oracles:
    `notes/erv_static_budget.md`, `notes/room_heat_loss_baths.md`.
  - **`DuctProductType` is keyed exactly like `prices.toml`'s `[ducts]`** — the
    (material, nominal diameter) pair — so a run that prices as 4" galvanized cannot resist
    as something else. The engine owns the physics; the house owns the ASHRAE roughness and
    bend coefficients, on the row. A run whose pair names no row is UNKNOWN by that pair,
    never given a default epsilon.
  - **Broan's manual asks for an 8" trunk above 200 cfm with long runs, and this house now
    obeys it in full.** Both outdoor legs went to 8" on 2026-09-15. `DU-ERV-EA` first
    (0.167 -> 0.044), which bought almost nothing because supply took over as the governing
    side within a hundredth of an inch; then `DU-ERV-OA` (0.132 -> 0.032), which had been
    blocked on GEOMETRY rather than money — at its old chase station an 8" envelope overran
    the shaft's east face by an inch — until its hood moved to the north wall and its riser
    left the chase. **`notes/erv_static_budget.md` §7 is now spent.** The only large term
    left anywhere is `DU-ERV-RISER-EXH` at 0.203, 58% of the governing column on its own;
    with extract in front by 0.043 the extract elbow audit and riser segmentation are worth
    something again, up to that gap.
    §8 is the commissioning spec, and its real point is that an ordinary flow hood reads
    25-30% low below 150 cfm: a **TSI Alnor LoFlo-class** instrument is required equipment.
  - **Three manifolds map to CAVITIES, not storeys.** Level 1 = basement ceiling, machine in
    RM-B-FURNACE. Level 2 = RM-M-MECH, feeding both main-storey CEILING grilles and
    second-storey FLOOR boots because both open into the one FS-S-WEST/EAST cavity. Level 3 =
    FS-ATTIC deck at the chase head. Moving a terminal between storeys is free; moving it
    between cavities is a new radial off a different manifold.
  - **Machine stays at (3'-11 1/2", 30'-6") — do not move it north.** `EQ-B-ESS-BATT`'s 36"
    REQUIRED clearance zone (x 49 1/4"..145 1/4", y 378"..460") is graded as a RECTANGLE by
    `advisory.ess_clearance`; this station leaves 1 1/2" clear and also clears
    `ED-B-BACKUP-ENCL`'s 36" NEC 110.26 working space. Nothing downstream is anchored to the
    machine, so moving it back would cost a FAIL for no savings.
  - **The radon/plumbing chase at (1', 34'-6") is the only riser and is full**: THREE ERV
    risers (`DU-ERV-RISER-SUP` 9 5/8", `DU-S-ERV-HP-FEED` 12", `DU-ERV-RISER-EXH` 18 5/8",
    all at y=33'-7 1/2"; `DU-ERV-EA` 8" at (2'-0", 35'-0")), six plumbing vents,
    `VR-M-RADON-VENT` and nine conduits. The clear is **24" x 26 1/8"** measured off the wall
    LAYERS — a room-polygon reading counts 6" of exterior stud as shaft on each
    `face("sheathing-ext")` face, which is where the old "~25% fill of 30 1/8" x 32 3/8""
    came from. Nothing else goes in that chase. `DU-ERV-OA` came OUT of it on 2026-09-15 and
    now stands at (3'-4", 33'-11") in the open closet, which is what let it go to 8".
  - **`FS-M-MECH` carries the risers through TWO drawn floor openings** (`FO-M-ERV-OA`,
    `FO-M-ERV-EA`, both `purpose=CHASE`), added 2026-09-15. It declared NONE before that and
    four risers passed through its joist field undrawn — nothing grades a duct against a floor
    member, so it sat at 0 FAIL. Each cuts one 11 7/8" I-joist and gets a 2-ply LVL header and
    doubled trimmers; the joist maker's header table governs, not R502.10.1, which is a
    sawn-lumber rule. The remaining vents and conduits through that deck are still undrawn.
  - **The two outdoor hoods are STACKED on the NORTH face** (moved off the west facade
    2026-09-15): `EQ-M-ERV-HOOD-OA` intake (3'-4", 37'-1 1/4") +5'-0" on `W-M-N3B`;
    `EQ-S-ERV-HOOD-EA` discharge (2'-0", 37'-1 1/4") +17'-0" on `W-S-N3B`, 12'-0" apart,
    exhaust over intake. The y is the CLADDING face (36'-7 1/4") plus half a 12" box — both
    hoods hang ON the panel and are entirely outdoors, which is why both carry `room=None`.
    - **They left the west face because each run had to sweep the chase to reach its hood**,
      and the two sweeps carried twelve measured interpenetrations between them — including
      `DU-ERV-EA`'s basement leg running INSIDE `PR-B-KITCH-DRAIN` for 4'-3". Both runs are
      now clear of every duct and pipe in the house and of each other.
    - **The intake is at +5'-0" and the extra foot is NEC 110.26, not snow.** `ED-M-HP3-DISC`
      is on this wall at (4'-4", +3'-6"); its working space is x 3'-1"..5'-7" and runs to the
      greater of 6'-6" above grade or the top of the equipment — the can is 9 1/2" tall, so
      +4'-3 1/2" governs and a 12" box centred on +4'-0" sat inside it.
    - The north face is crowded and the intake's station is what is LEFT: `EQ-M-HP3-OD`'s
      cabinet holds x 0'-0"..2'-10 3/8" with a 12" rear coil clearance, and `D-M-ENTRY`'s RO
      holds x 6'-6"..9'-6". x=3'-4" is also the only one of `W-M-N3B`'s four legal stud-module
      stations the duct can stand on — the other three are each inside a pipe.
    - Exhaust must stay the UPPER hood: `mep.erv_outdoor_terminals` measures 3-D distance and
      13' of rise alone clears its 10' rule (→ DESIGN-LOG.md, "Ventilation, ducts and
      soffits"). Neither hood may turn and travel inside the wall: an R-8 wrapped 6" duct is
      ~8" OD against a 5 1/2" stud cavity, so each must be a straight through-wall
      penetration. `test_catlin_erv.py` pins this stack order.
    - **BOTH HOLES ARE MODELLED, AND THE DISCHARGE MOVED 8" TO GET ONE (2026-09-11).**
      `AO-M-ERV-OA` and `AO-S-ERV-EA` are 7" `RoughOpening`s — 6 5/8" of flashed curb plus
      3/16" a side — each naming its duct in `penetration_for`, which is what keeps
      `mep.run_through_opening` from reporting the hole it exists for. Before them an
      `Equipment` placeable resolved NO solid and the wall carried no void, so the hoods
      drew in no elevation, section or GLB and the cladding read unbroken across both ducts.
      A 7" RO lands wholly inside a bay, so it takes no header, jack or king; it does pack
      girt blocks at its jambs (+9 house-wide, `test_hardware_takeoff.py`).
    - **The discharge is at y=34'-0" because 34'-8" was `stud-001`.** W-S-W1B frames studs at
      400"/416"/430 3/4" and the duct sat dead on the middle one, boring a bearing 2x6 that
      R602.6 allows 2 1/5" of. y=34'-0" is the bay centre, 3 15/16" to each stud. **Only the
      HEAD moved**: carrying the whole leg south would have stood its riser 4 1/2" from
      `DU-ERV-OA`'s, two 6" ducts overlapping, so the run turns south 8" at +17'-0" inside
      the shaft and leaves the wall square.
    - **The intake cuts girt course 003 and that is accepted.** `AO-M-ERV-OA` clears both
      studs but z 44 11/16"..51 5/16" crosses the course at z 48"..51 1/2". A girt is a KDAT
      2x4 laid flat in free air carrying the panel's wind load into the blocks either side,
      not gravity — broken in one 14 1/2" bay with the curb screwed to the cut ends. The
      discharge cuts nothing, clearing every course by 5 3/16".
    - Still NOT modelled: the seal PRODUCT. `PipeAccessory(PENETRATION_SEAL)` hard-requires a
      resolved `PipeRun` host and there is no duct-side spelling, so the take-off still
      under-bills two escutcheon-and-foam kits. The hole is no longer the missing part.
- **A duct or machine inside a `Soffit` NAMES IT via `soffit_ref`, and the clear section is
  DERIVED — never author a clear width.** `mep.duct_soffit_occupancy` derives the cavity from
  the soffit's own drop, `FramingSpec` member, 5/8" lining, and a 2" hanger gap; an authored
  width is a second source of truth that drifts the first time framing changes. Current
  derived boxes: `SF-S-DUCT` 30 3/4" x 11 1/4"; `SF-S-HP1`
  40 3/4" x 7'-9 3/8" (in `RM-S-NCLOSET`'s ceiling), drop 23", underside at 7'-1".
  **Three soffits were retired on 2026-09-13** — `SF-B-HALL`, `SF-B-GYM` and `SF-S-SUITE` —
  each one built only to satisfy `mep.run_in_finished_volume`, each replaced by a
  `Room.exposed_services` sentence on `RM-B-STAIR`, `RM-B-GYM` and `RM-S-SUITE`. Two soffits
  and `SF-B-BATH` remain. **`SF-B-BATH` would survive the same treatment on the numbers and
  has NOT been retired**: measured with the box deleted, its three runs (`PR-B-BATH-VENT`
  8.4", `PR-B-HW-BATH` 3.8", `PR-B-LSINK-DRAIN` 6.0" under the ceiling) all clear the 6'-8"
  headroom line with ~7 1/2" to spare, so a declaration on `RM-B-BATH` would pass. The
  reason not to is not arithmetic — it is that a 92 SF lined bathroom is not a gym or a
  service hall, and no owner has said its ceiling should be open. That is a design decision,
  not a takeoff one.
  `DU-S-HP-SUITE` lost its `soffit_ref` with `SF-S-SUITE` and is `DuctRouting.EXPOSED` with
  an AUTHORED centreline (100 1/8" storey-relative): without it `_derived_base_z` falls back
  to the storey datum and lays a supply duct on the floor.
  - **A box's LONG plan dimension is its axis; every occupant is measured ACROSS the other
    one.** Near-square soffits (e.g. `SF-S-HP1`) need this ordering chosen deliberately, or
    the check grades the trunk's travel as "width" and never compares lane to machine.
  - **A hatch through a soffit must be AUTHORED as `Soffit.openings` (`SoffitOpening`,
    `model/floors.py`)**, or `resolve/framing/soffit.py` never cuts the rungs it crosses —
    an unauthored `Furniture` access panel is invisible to `structural.member_interference`
    (placeables vs. members is untested), and the model asserts an unopenable panel at 0 FAIL.
    - A cut rung becomes **stubs** carrying the header, keyed `-004a`/`-004b`; an edge landing
      on a rail takes no header. `structural.soffit_opening` grades the header on deflection,
      oracled by `notes/soffit_rung_deflection.md`. Not a duct penetration — a duct leaves
      through a soffit's END (`along` clip); a hatch through a ladder rail is a different
      check.
  - **`CHASE` routing (a framed shaft not modeled as a `Soffit`) is a declared unchecked
    case** — do not rely on it for clearance.
  - **EVERY HEAT PUMP NOW CARRIES ITS PUBLISHED RATINGS TABLE, NOT TWO SCALARS** —
    `EquipmentType.heating_ratings` in `plan/equipment_types.py`, one `HeatPumpRating` row
    per outdoor temperature with a `basis` and a required `citation`, read at the site's
    design temperature by `takeoff/hvac.capacity_at` (decision #76). Rows are NEEP's ccASHP
    listing except the two at −15 °F, where this site designs and NEEP publishes nothing.
    **NEEP is the only public source with a MINIMUM column**, and the minimum is what
    `mep.heat_pump_turndown` grades: **System 1 modulates down to its load only below
    −5.9 °F and cycles above it**, which `mep.heating_capacity`'s +6,743 Btu/h margin cannot
    see. All of it is ADVISORY, not FAIL (decision #77). The whole case, the three tables and
    the owner's 2026-09-18 decisions are in `notes/heat_pump_turndown.md`.
  - **`EQ-T-GREE-FLEXX-ULTRA-24-AH`/`-OD` is the live heat-pump type for
    `EQ-S-HP1-AH`/`EQ-M-HP1-OD`, and its provenance is CLOSED (2026-09-12, BLD-08).** The
    `# TODO verify datasheet` that stood here is gone because the figure was verified, not
    because it was waived: **21,000 Btu/h at -15 F, COP 1.57**, read verbatim from Gree's
    `GREE_FLEXX_ULTRA_EXTENDED RATINGS_08272024`, model FXU24, 70 F return, **"MAX OUTPUT"
    band** (136% of the zone's 15,410 Btu/h block load, unaided — **the load figure was
    15,164 until the block-load correction of 2026-09-18 and the percentage 137; neither the
    unit nor the argument moved, and `notes/block_load_basis.md` says what did**). NEEP ccASHP **id 504980**
    lists the unit as ENERGY STAR Cold Climate with a -22 F maximum of 18,000 Btu/h at
    **COP 1.36** — same capacity as Gree's own -22 F row, lower COP; quote NEEP's when a
    figure must be conservative.
    **AHRI 215213329 certifies SEER2/EER2/HSPF2 and the 47 F and 17 F points ONLY**, so the
    -15 F number is a manufacturer rating with no certificate behind it. Say so at plan
    review rather than pointing at the AHRI number.
    **Two misreads corrected in the same pass, neither changing the decision:** airflow is
    **760 cfm at 0.5" ESP (speed 3)** — 850 cfm is the only speed that reaches 1.0", and the
    "760 at 1.0"" this file carried was the wrong column; and the heat kit is a
    **field-installed accessory** (5/6/10 kW) the cabinet accepts, not factory-fitted — the
    interlock argument that drove the retype is untouched, because what the DUC24 lacked was
    the aux-heat TERMINAL and this cabinet has it.
    HSPF2 10.0. Depth is 18 1/8" (→ DESIGN-LOG.md, "Ventilation, ducts and soffits" for the
    two retypes this replaced).
    **Warranty stays an owner call**: 5 parts / 7 compressor standard, 10/10 only through a
    Gree Select Dealer with 60-day registration. Owner-supplied is NOT void, just not Select.
  - **A `# TODO verify datasheet` marker on any equipment type is not documentation debt —
    every clearance, lane, and velocity downstream of it is provisional** until the type is
    replaced with a verified one; re-check all of them when it is.
  - **`SF-S-HP1`'s box is 40 3/4" x 7'-9 3/8", flush on all four finished faces**, in
    `RM-S-NCLOSET`'s ceiling; the air handler is `rotation=deg(90)` so only its 21 1/4" case
    depth competes for the graded width. Consequences that must stay true:
    - **A SECONDARY DRAIN PAN IS REQUIRED UNDER IT, IT DID NOT FIT, AND THE BOX IS 2"
      DEEPER BECAUSE OF IT (2026-09-18).** The FLEXX Ultra AH is a MULTI-POSITION air
      handler (18 1/8 x 43 1/2 x 21 1/4 upflow cabinet, laid on a side for horizontal
      ceiling mount — a factory configuration, "Horizontal Left: No Modification Needed",
      against submittal `GREE_FXU24_230V_R32_SUB_01272026`), **not** a slim ducted cassette.
      The same page requires an emergency pan where the unit sits over a finished ceiling,
      and so does IRC M1411.3 / IMC 307.2.3 — sized by M1411.3.1 at 1 1/2" deep minimum and
      3" larger than the unit each way. **A DROP IS NOT A CAVITY**: the 21" drop this
      carried gave 18.25" of clear cavity (5/8" of lining top and bottom, 1 1/2" of bottom
      rung), so the slack under an 18 1/8" cabinet was **1/8"** and the pan did not fit at
      all — while `mep.duct_soffit_occupancy` PASSed, because nothing in the model knew the
      pan was coming. The drop is **23"** now: 20.25" of cavity, sized so both things on the
      cavity floor can ride 2" up on the pan — cabinet 2 + 18 1/8 = 20 1/8, `DU-S-HP-RET`
      2 + 18 = 20. **The clear under the box is 7'-0 1/8" and that is the whole margin** —
      the section's CLG tag, off the finished floor, where it read 7'-2 1/8" at the 21" drop
      (the "7'-3"" this guide and the plan source both used to quote was the face struck
      from the storey datum, ~2" optimistic). IRC R305.1 is cleared by 1/8". **The pan
      itself is still unmodelled and the 2" is NOT reserved by any
      check** — no element kind holds one, and authoring it as `Equipment` would clash with
      the machine it catches, since the hanger-gap test ignores z. Do not spend that 2" on a
      new occupant. It reaches the installer through `tasks.toml`'s `site/long-lead-orders`,
      which also carries the other half: horizontal RIGHT requires relocating the factory
      drain pan, so which hand `rotation=deg(90)` lands on goes on the ORDER.
    - **`W-S-BW4` must stay retyped `INT_2X4_RC`.** A plain partition jogs 1/2" at
      y=30'-10" and `_rectangle` returns `None` on a non-rectangle, sending every occupant to
      UNKNOWN.
    - **`DU-S-ERV-HP-FEED` must name NO soffit.** It shares the box's y-band with the attic
      chase legs twenty feet west; naming the soffit would grade those as occupants of a
      cavity they never enter — a false FAIL.
    - **`EQ-S-ERV-MIX` is a full return plenum** (12" x 29 1/2" x 18", x
      20'-5 1/2"..21'-5 1/2", y 27'-10 1/2"..30'-4") — `REG-S-HP-RET`'s whole 336 in² face
      must sit inside it, or part of the return face draws from the bare soffit cavity
      (IMC 601.5's building-cavity-as-plenum, which no check here catches — see
      DESIGN-LOG.md).
    - **A wall grille on `W-S-C4B` is NOT buildable — do not re-propose it.** It is the
      x=18' bearing line (`RB-HOUSE`'s load path); the one bay overlapping the plenum band
      leaves 7 1/4" clear, and cutting the stud puts the plate at f≈1,940 psi against
      Fb≈1,310. `RM-S-NCLOSET` and ~7'-9" of north hall are at a 7'-1" face / 7'-0 1/8"
      clear in trade;
      `RM-S-HALL`'s graded `clear_height` is unchanged at 8'-11 1/2".
    - **`Mount.elevation` on a `Register` is a number NO CHECK READS** (a Register resolves
      no solid) — author every ceiling terminal off its own room's ceiling, never a borrowed
      comment.
    - `REG-S-HP-STAIR` is a SIDEWALL grille (`REG-T-HP-SUP-SIDE`) in `SF-S-DUCT`'s west
      lining at 97 1/8" — do not revert it to a ceiling grille above the room's own return.
      `REG-A-HP-STUDY` floor boot sits at (25'-0", 3'-4") — every station on that bay line
      from x 21'-0" to 27'-3" is under furniture, so this is the best fit, not a clean one.
      **Nothing grades a placeable against a register** — check by hand when moving one.
      `DU-S-HP-SOUTH`'s west terminal is at x=9'-4" (centroid of all three south windows, not
      the middle two).
    - **The riser cannot cut through `FS-ATTIC`'s joists** (they run in x); near x=19'-6"
      every hole lands inside `W-S-C1`'s no-hole zone, and no duct small enough to dodge it
      still moves 250 cfm.
    - **The return path is door undercuts, and `Opening` cannot hold one** — there is no
      undercut column in the A-601 schedule, so an unspecified door defaults to 3/4". Required:
      `D-S-BED1/2/3` 1 1/2", `D-S-SUITE`/`D-A-STUDY` 1 3/4", `D-A-HALVES` 1 1/4"; `D-S-PLANT`
      deliberately none (interlocked damper). Full arithmetic: `notes/system1_return_path.md`.
    - **`AO-S-HP1-AP` (30" x 29" clear) must stay gasketed.** Leaving the soffit's bottom
      open in the closet makes the closet itself the return plenum, which IMC 601.5(7)
      forbids.
    - Where the box passes under `ST-S2A`'s flight, `ledger-W-S-SS2-stringer-1` (the 2x10 on
      `W-S-SS2` at y 104 1/8"..105 5/8") may NOT be lapped — `structural.member_interference`
      excuses treads/stringers over a soffit but not that ledger.
- **`W-M-HS4` is a pocket wall and nothing may ever go in it again** — no outlet, switch,
  pipe, register, blocking, or towel bar between 12'-4" and 16'-5" on y=22'-4" (no stud to
  fasten to, no depth to recess into). `D-M-LAUN`'s 4'-0" pocket leaf parks there, crossing
  node `N-M-E3`. Enforced by `mep.pocket_occupancy`.
  - **A split stud that ever reaches the top plate destroys the `W-M-LS` plate tie** — a
    pocket occupies floor to 6'-8" only, so the tie's plates run continuous over/under it and
    only its vertical edge floats.
  - 4'-0" is the widest leaf that fits: the closing pack must clear `N-M-C2`, where bearing
    `W-M-C3` corners in and `BM-M-HALL` starts. Full detail, including the 1" fastener limit:
    `notes/pocket_door_at_laundry.md`.

### Basement

- **Slabs.** Basement slab: 2" XPS at **>=25 psi** (R-11.1 whole-assembly against an owner
  target of R-10; PASSes `code.energy_prescriptive`'s R-10 slab row). Detached garage slab:
  1" at **40 psi** — a loaded wheel is a contact patch, not a distributed floor load.
  `RM-GARAGE` is `conditioned=False`, so nothing grades the garage number.
  - Do not assume a psi change is priced: `library/materials.py`'s `xps` tag has no
    compressive field and `prices.toml` keys XPS on **thickness only**, so 25 psi and 40 psi
    board bill identically here though 40 psi runs ~20-35% over in the yard. XPS price rows
    ARE qualified by `thickness_in` (`cli/prices.py`'s `envelope_layers`), or any
    foam-thickness change would price at $0. `test_catlin_reference_parity.py` carries no
    `DECLARED_DIVERGENCES` entry for the basement slab; catlin matches the reference detail.

- **Foundation wall assemblies** compose `library/FOUNDATION_WALL_{8,12}_XPS4_CORE` plus a
  house-local skin — the core must not drift between the variants.
  - **Minnesota requires WATERPROOFING, not dampproofing, and there is no rung below it.**
    Minn. R. 1309.0406 subp. 1 deletes IRC R406.1 in its entirety; subp. 2 names eight
    acceptable materials, with no high-water-table precondition. The `waterproofing` layer
    is a **60-mil self-adhered rubberised-asphalt sheet at 0.05 perm** (Bituthene 3000;
    Polyguard 650 / MiraDRI 860 as equals) — subp. 2's item 5.
    `code.MN_1309_0406_waterproofing` grades the layer's MATERIAL against that list, so
    repointing it at anything
    else is a FAIL, not a silent downgrade; it was `air-barrier` (Tyvek, 54 perm) until
    2026-09-12 and PASSed on presence alone. Insulation goes OVER the membrane.
  - **The wall dries INWARD only, so the interior face must stay vapour-open.** No poly, no
    vinyl wallpaper in the basement. Both walls PASS the cold-snap screen only since the
    membrane tightened (→ DESIGN-LOG.md, "Basement").
  - **No dimple mat and no below-grade protection course, by decision.** Nothing outboard of
    4" of mastic-bonded XPS can take a mechanical fastener. Free-draining stone against the
    lower wall does the drainage — `[allowances] foundation-free-draining-backfill`, priced
    off the waterproofed face — and **backfill in controlled lifts** is what protects the
    foam, which is why it is an `insp/foundation_backfill` item. Do **not** author a
    perimeter `FrenchDrain` for it: it would bill the footing bedding's stone twice.
  - **No membrane on the sunken-garden court walls (`W-SG-*`), and that is deliberate** —
    subp. 2 reaches only walls that also enclose below-grade interior space, and none of
    them does. They get drained backfill instead, which relieves the thrust that a coat
    would not. It does not change their R404.4 case either way — sliding is graded on the
    closed court loop at FS 1.63 (`retaining_system/W-SG-ARCH`), not on these walls
    individually (→ "Sunken garden court").
  - Skin: `BASEMENT_12`/`_8` cover the XPS with a 1/8" `foundation-coating-acrylic` (troweled
    over mesh) banded from 6" below grade to the wall top, `Layer.extent` off the `GRADE`
    datum so a grade lift grows it with no edit. Do not revert to the old
    `foundation-protection-panel` alternate (kept, priced, as a named alternate only) — its
    joint permeance is unpublished and makes `building_science.condensation` report UNKNOWN,
    where the coating PASSes (→ DESIGN-LOG.md, "Basement"). **That coating is the
    above-grade exposed-XPS band only**, ~276 SF of a ~1,016 SF face: a UV and impact skin,
    not a below-grade protection board. There is no below-grade protection course.
  - `W-B-S1`/`W-B-S4` use `BASEMENT_8` (no stucco) for ~37 SF of coating. Court segments
    carry **no skin at all** (XPS sits inside `W-B-BRICK`'s ventilated cavity).
    `BASEMENT_8_GARDEN`/`_GARDEN_PARGE` were **deleted 2026-09-12** (#72: a tag nothing
    references is deleted); the revert is in git, pointed at from `plan/assemblies.py`.
  - Pour thickness: only `W-B-E1`/`E2` are `BASEMENT_12` — they bear `SL-M-DECK`, the one
    remaining cast deck. The other nine segments are 8" with `#5 @ 41" o.c.` vertical steel
    per IRC Table R404.1.2(8). `W-B-STR`/`W-B-STR3` and `W-B-CS` are 2x6 bearing **stud**
    walls, not concrete — `unbalanced_fill` is `ft(0)` on all of them; `W-B-CS2`/`W-B-CN`/
    `W-B-CN2` are the only interior pours left. Do not retype any of the nine to 12" without
    cause — `structural.foundation_unbalanced_fill` FAILs correctly otherwise.
  - Cladding: `N-B-BRICK-W`/`-E` stand off `inch(-4.05)` on bare XPS; veneer clear cavity is
    **1-1/2"** (IRC R703.8.4 min 1"). Never re-strike this node off a parge finish face — it
    must sit on the foam itself (→ DESIGN-LOG.md, "Basement"). Walls align on
    `face("concrete-ext")`: the furnace room and workshop have 4" more clear on the inside
    face than the model reports — `clear_face` is inset from the wall axis and did not move
    with the thinner wall; read the layer polygons instead (`notes/basement_to_framed_wall_detail.md`).

- **Sauna (`RM-B-SAUNA`).** Against the south (garden) wall, long axis east-west; west wall
  at x=8'-10" on `N-B-S1`; south face is one plane on `W-B-S2`'s garden curb, no jog. Clear
  box **8'-3 15/16" x 8'-10 11/16"**, 555 cf against `EQ-T-SAUNA-HEATER`'s 600 cf rating
  (45 cf margin — a deeper room needs a bigger heater and circuit). Entered from the gym
  through framed `W-B-CS`; keeps `WIN-B-SAUNA`.
  - Its north wall (`W-B-SA-N`, split at `N-B-HALL-S`; `W-B-SA-N2` is the east segment) lands
    on `W-B-CS3`'s 4'-5" framed run beside `D-B-GYM`'s rough opening (starts y=10'-11 7/16").
    Do not move `D-B-GYM` south or this wall north of 10'-0" — past 10'-6" the wall and the
    opening overlap outright and no `haus check` rule tests a tee wall beside an opening.
  - Heater `EQ-T-SAUNA-HEATER` (9 kW) is on the **east liner**: `rotation=deg(270)`, 18" face
    to wall, 16" deep, 2" off both liners.
  - Benches: `FURN-SAUNA-BENCH-2T-60` (two-tier), `FURN-B-SAUNA-BENCH-E`, and the south-liner
    bench `FURN-SAUNA-BENCH-48` (**4'-0", do not grow it**) — `ED-B-SAUNA-JB`'s box base sits
    at 18" AFF, the bench-top height, so a longer carcass would reach under a live 9 kW
    junction box. Do not push the heater north to `D-B-SAUNA`'s jamb either —
    `EquipmentType` carries no clearances field and nothing would stop a 30" hot stove at the
    doorway. `FURN-SAUNA-BENCH-48` must stay priced in `prices.toml` — an unpriced type
    silently drops from the takeoff. `REG-B-SUP3`, `DU-B-ERV-R-SAUNA-SUP`'s east leg and
    `ED-B-SAUNA-JB` all sit with the heater on the east liner.
  - **Lighting is two 24V under-bench runs and NOTHING ELECTRICAL IS IN THE HOT ROOM
    (2026-09-13).** `LR-B-SAUNA-BENCH-L` (an L along the west + south foot benches, 7'-1/2",
    1 corner connector) and `LR-B-SAUNA-BENCH-N` (5'-0" along the two-tier bench), both
    `ED-T-LT-STRIP24-SAUNA` mark **X** — 24V IP68 silicone tape rated to 90 C, 2700K, at
    **16" AFF** under the 18" bench lips, which is the coolest air in a stratified room. One
    `Mount.elevation` serves a whole `LightRun`, so this works only while all three seat tops
    stay 18". Driver `ED-B-SAUNA-LT-PSU` (`ED-T-LT-PSU-60`) is a surface box on W-B-SA-N's
    **workshop** face at (10'-0", 10'-6 13/16"), 48" AFF; `ED-B-SAUNA-SW` is on W-B-CS's
    **gym** face and retyped `ED-T-SWITCH-DIM`. 36.1 W x1.25 = 45.2 W, **75% of the PSU-60's
    nameplate** — `ED-T-LT-PSU-200` is not available here, a PSU sums at its RATING and 200 VA
    on the ALWAYS_ON tier flips `cycle_48h.sustains_always_on` (surplus is +0.44 kWh).
    The tape bills through `[allowances] electrical-sauna-under-bench-strip`, not
    `[placeables]`. **`ED-T-LT-SAUNA-VT` (mark V, the fibre-optic kit) is retained
    CATALOG-ONLY as the named revert and its letter is NOT freed** — the replacement took X.

- **Bathroom.** Rotated north-south along the framed stair wall (`W-B-STR3B`/`W-B-STR2`);
  clear **3'-3 15/16" x 7'-1 1/4"**. Wet wall is `W-B-BA-E`, an `INT_2X6_STAGGERED_PLUMBING`
  partition at `inch(166.6875)` on the stair well's centreline, carrying the shared vent
  riser at (13'-10 11/16", 19'-3"); `W-B-BA-N` is a dry `INT_2X4_PARTITION`. `D-B-BATH`
  swings out into the hall with `flip_swing=True` on this wall. No `haus check` rule grades
  a wall device's depth — `test_wall_mounted_devices_resolve_against_a_wall_face` is the only
  guard, so verify `ED-B-BATH-SW` sits flush with the studs by eye.

- **Hall and circulation.** The hall runs from the stair foot south, west of `W-B-CN2`, the
  full way to the sauna's north wall, on the x=13'-10 11/16" well-partition centreline shared
  with `W-B-BA-E`/`W-B-WELL`; part of `RM-B-STAIR`'s loop (114.8 -> 147.7 sf, one seed, no
  separate `Room`). Circulation is stair -> hall -> gym (`D-B-GYM`) -> `D-B-PLAY`, and
  stair -> hall -> `D-B-SHOP` -> workshop -> `D-B-FURN`. There are now **no doors through a
  concrete pour** — `prices.toml`'s `concrete-window-bucks-and-blockouts` row drives to zero
  and is kept there under the `glazed-green-brick` convention.
  - `D-B-GYM` is on the hall (not the workshop): same uid/position, 32" leaf, type
    `DT-INT-SWING32-GLAZED` (glazed because the hall has no window of its own and borrows the
    gym's south daylight). Keep it at **32"** — `W-B-CS3` offers 42 3/16" of framed run and a
    36" RO would leave only 3/16" for two jamb packs.
  - The workshop is a room (not a corridor) with `D-B-SHOP` (3'-0", in `W-B-HALL-W`,
    `flip_swing=True`, hinged north, leaf swings west), RO centred on `D-B-GYM`'s at
    y=12'-3 7/16". `D-B-FURN` (3'-0", widened) is pinned west by `PR-B-ERV-COND`. `W-B-CW2B`
    and its cased opening `O-B-HALL` no longer exist.
  - `W-M-CLN2` (upper storey) stacks on nothing: `W-B-CW2` below it overlaps by only
    6 11/16", short of the 2'-0" stacking minimum, so `integrity.stack_ambiguous` does not
    arm. The load routes into the deck instead via two `JoistReinforcement` blocking entries
    in `params/main_deck.py` at x=14'-6"/16'-9", `at` y=**217"** (not 216" — equidistant
    between the 208"/224" joist lines). These two entries must stay **LAST** in
    `_WEST_FLOOR_REINFORCEMENT`.
  - `RM-B-STAIR` (not a `EXPOSED_SERVICE_OCCUPANCIES` room, unlike the workshop) covers the
    hall's ceiling, so `mep.run_in_finished_volume` (3" tolerance) grades pipes there.
    `DU-B-ERV-R-GYM` and `PR-B-SAUNA-VENT` cannot be rerouted around it — any route between
    the sauna and the ERV crosses this space. **They were boxed out by `SF-B-HALL` until
    2026-09-13; that bulkhead is RETIRED and `RM-B-STAIR.exposed_services` carries the room
    instead** — the owner accepts exposed services down here, the same call `RM-B-GYM` makes.
    Both runs are still held to the 6'-8" headroom line (duct bottom 87 1/8", vent 85 1/4"),
    and the declaration also takes `DU-B-ERV-R-BATH` and `PR-B-HW-SUITE` — two shallow
    crossings the 3" allowance had been tolerating silently — out of the ceiling comparison.
    Do not re-box either run without re-reading the declaration. `PR-B-HW-SAUNA` and
    `PR-B-CW-SAUNA` run side by side, not stacked, at x=17'-4"/17'-3" — do not restack them;
    two 1/2" lines need 5/8" separation in a band only 3" deep.
  - Lighting/outlets: three `ED-T-LT-CAN3` on `CKT-LT-BACKUP` at x=190",
    y=19'-6"/15'-0"/11'-6" (27 VA; `cycle_48h.sustains_always_on` holds,
    `test_backup_calc.py`). Keep the middle one at **15'-0"**, not 15'-6" — `PR-B-HW-SAUNA`
    crosses 2 9/16" below the ceiling there. `ED-B-WORKSHOP-SW` sits 5" north of
    `D-B-SHOP`'s hinge jamb — the only side with room for the box. `ED-B-HALL-RC1` is on
    `CKT-RC-BSMT` at y=16' (NEC 210.52(H)); note `electrical.receptacle_spacing` only walks
    {BEDROOM, LIVING, KITCHEN, DINING, OFFICE}, so nothing enforces it if it moves.
    `ED-B-GYM-RC1`/`RC2`/`RC8` are on the gym face of `W-B-CS`/`W-B-CS3` — verify a device's
    side by eye: `electrical.receptacle_spacing` accepts one within 0.5 m of a room's clear
    face regardless of which side it's drawn on. `EQ-B-HP2-GYM` mounts at **6'-6" AFF** on
    `W-B-S3-FR` (not 7'-6" — its cabinet would top out above `code.R305_ceiling_height`'s
    95 3/8").

- **Under-stair space.** No `RM-B-UNDERSTAIR` room exists; the storage under the arriving
  stair flight (and on under the landing deck) is part of `RM-B-STAIR`'s single polygon.
  `D-B-CLOSET` opens it to the furnace room; `ED-B-CLOSET-LT` (`room=RM-B-STAIR`) lights it.
  `LR-B-STAIR-RAIL` lies under the flight rather than along it — one `Mount` elevation for
  the whole `LightRun`, measured off the slab, so it cannot rake.
  - `W-B-WELL` gives the well partition its faces only — `resolve/stairs/u_split.py`
    generates the 2x4 plates and studs between the two flights. Never add a `FramingSpec` to
    `STAIRWELL_PARTITION_4H`'s structure layer or `structural.member_interference` FAILs
    (it did, twelve times). Its thickness must stay locked to
    `resolve/stairs/common._WELL_PARTITION_THICKNESS_M` (4 1/2"). Its north end is open
    (`open_end=True` on `N-B-CL-NE`) — the only honest way to model a partition dying
    mid-well; `integrity.wall_loop_open` reads it.
  - `W-B-STR3` is `STAIRWALL_INT_2X6_BRG_UNDERSTAIR` (5/8" Type X in place of 3/4" stair
    plywood, per R302.7) — costs the exposed-plywood stair face on this segment. **Do not
    retype it back**: `code.R302_7_under_stair_protection` now passes on "no enclosed usable
    space" (`STAIR` is not in `_UNDER_STAIR_OCCUPANCIES`), but the Type X's reason didn't go
    away with the room label. `FO-M-STAIR`'s west edge is at `ft(10, 3.25)`.
  - Do not author `Room.ceiling` or a `Soffit` under the arriving flight — the real head
    rakes 96.7" -> 54.8" and no field represents that; `_clear_head` reads only decks/soffits
    (a stringer is neither), so `clear_height_m` resolves to the main-floor deck and passes
    R305.1.1 honestly. An authored ~53" ceiling would be taken verbatim and FAIL.
  - `DT-INT-CLOSET24` is **2'-0" x 6'-0"**: at y=28'-4" there is 76.5" of head, a 6'-8" leaf
    plus header wants 82", a 6'-0" leaf wants 74".
  - `D-B-FURN` is at `ft(3, 3)`, pinned by the condensate line — `CD-B-SPA`,
    `CD-B-DATA-SHOP` and `PR-B-ERV-COND` all pass nearby and none can move (a `ConduitRun`
    has one flat elevation). Moving this door east re-opens the clash (king stud is 0.475"
    off the pipe).

- **Engine behaviour to rely on.** `illumination._gypsum_finishes` matches `gwb*`/`gwb`/
  `gwb-x` (every gypsum layer in this catalog), not the literal string `"gyp"`.
  `topology._through_pair` prefers a continuous bearing pair at a four-way node, tag order as
  tie-break. `test_upper_storey_studs_stand_over_studs` sits at 112/247; `W-M-C1`'s studs are
  invisible to it because `W-B-CS3` shares the x=18' layout line but `stacks_on` names a
  different basement segment. S-100's ARCH D scale is **3/16"**, with only **0.18"** of
  vertical margin left in the FOUNDATION WALL SCHEDULE column (already carrying all three
  schedules, no width for a fourth) — the next new `FoundationWall` assembly tag anywhere in
  this house steps it down to 1/8" again.

### Decks and the garage

- **Every exterior deck's plank is the floor system's own sheet, no exception.**
  `FS-SG-PORCH` (composite, 3bf2f48) and `FS-SG-DECK` (aluminium) carry their boards as
  `subfloor=DeckLayer(...)`; the old `SL-SG-PORCH`/`SL-SG-DECK` slabs beside the framing are
  gone, and both planks bill by the square foot in `[sheet_goods]`, not by the cubic yard out
  of `[concrete]`.
  - **`FloorSystem.subfloor_outline`** is an authored sheet polygon that can replace a floor
    system's derived joist-field corners (for a plank that oversails its rim). Bound it
    against `[framing] bearing_plan_tolerance_in` (8") with `structural.subfloor_oversail` —
    past that the uplift pass FAILs members under the deck, reported nowhere near it.
    `sheet_goods_takeoff` reads `deck_outline` for sheet area; `ceiling_below` keeps the
    framed extent. (→ DESIGN-LOG.md, "Decks and the garage")
- **`PT-BW-1..4`, `SL-BW-DECK`, `GL-BW-ROOF`, the polycarbonate canopy glazing, `RL-BW-WEST`, `RL-BW-SCREEN`, `BM-BW-FW`, `PT-BW-CE`/`-CNE`
  and `_EW_FT`/`_GLAZING_CENTER_X` no longer exist.** `BM-BW-RW`/`-RE` DO — the tags are
  deliberately reused for the canopy's two roof headers, on the same bearing lines. The
  landing is `FS-BW-FLOOR`/`FS-BW-GARAGE` on six piers. **`PT-BW-T1W..T4E` and their
  footings are gone too** (2026-09-10): eight 42" piers laid out running EAST from the stair
  foot while the flight runs WEST, so every one stood under open ground. The tiers are
  `carriage="cast"` — four `Slab` pours, `SL-BW-TIER1..4`, wedding-caked on a compacted base
  — so **no member of `ST-BW-ENTRY` is a stringer or a rim**; only its treads resolve, and
  they exist because every code rule grading a flight measures them, not because anything
  bills them. See `notes/north_entry_structure.md`.
- **The garage wall was rebuilt; both the garage wall and its roof are current.**
  `GARAGE_WALL_2X6` is **2x6 @24" o.c. / 2" ccSPF in the bays / 5/8" CDX / 7/8" corrugated
  exposed-fastener panel**, trusses at 24" o.c. to match (`GARAGE_ROOF`, framing factor
  0.0625 = 1.5/24 — the two must move together or the R-38 blow is under-credited).
  `RM-GARAGE` is `conditioned=False`, exempt from `code.energy_prescriptive`,
  `building_science.condensation`, and the MN prescriptive table.
  - Whole-wall value is **R-13.2** with `CavityFill` present — a bare SPF-over-cavity read
    of R-14.3 is a modelling bug, not the real wall. (→ DESIGN-LOG.md, "Decks and the garage")
  - **No WRB by design** (IRC R703.2 exception, unconditioned detached accessory). ccSPF is
    the air/water/vapour plane; `TR-CATLIN-GARAGE-OPENING` names `stud-cavity` for all four
    controls, not the house's `sheathing-ext`/`spray-foam-ext`, so bucks go in before foam.
    CDX carries no `control` set — bare sheathing claiming those layers would be a WRB
    nobody is buying.
  - **No furring; the 7/8" corrugation is the rainscreen itself**, drained by ~192 LF of
    closures (`[allowances] envelope-garage-corrugated-closure-strips`), vented at the base,
    solid at the head, priced there and not through `bug_screen:GARAGE_WALL_2X6` (reads 0 SF
    for a corrugated wall). Do not author a 7/8" airgap layer to "activate" that row — it
    would add 7/8" on top of the existing cladding and move both wall faces.
  - `GARAGE_GAP_FT` is **4.71875** (was 4.6875) — do not recess the sheathing to hold the
    cladding face still, since the wall's `alignment` always puts whichever sheathing it
    carries on the node line.
  - **No 16" stud zone at the overhead door.** `W-G-E` is NONBEARING; the 16'-0" opening is
    carried by its own 2-ply 14" LVL on solver-sized jamb packs — `FramingSpec.spacing` lives
    on the assembly, so a closer-spaced zone would need a whole second assembly.
  - Openings re-stationed onto the 24" grid: `WIN-G-N1` 1'-5" -> 2'-5", `WIN-G-S1`
    21'-5" -> 20'-5", `SERVICE_DOOR_OFFSET` 5'-10" -> 6'-6" (leaf centre x=8'-0"). `D-G-OVERHEAD`
    stays at 4'-0" — every legal station makes the two brick piers 5'-0" and 3'-0", so its
    `structural.door_framing_module` suppression stays in `preferences.toml`.
  - The 16 garage-wall `S-5-N` seam clamps are gone — a corrugated panel has no nail-strip
    seam; corner uplift is the panel's own 640 face screws. The garage ROOF keeps its 12
    `S-5-N` clamps (still nail strip). `GARAGE_WALL_WIND_CLAMPS` survives as an empty list,
    and `standing-seam-nailstrip-26`/`zip-r` keep $0 price rows (the `glazed-green-brick`
    convention).
- **The overhead door faces north; the garage sits at x 6'-0"..30'-0" (centre x=18'-0"),
  2026-09-07.** `GARAGE_X_WEST`/`GARAGE_X_EAST` are published beside the two y lines; stem,
  slab, and landing derive from them. Footprint did not rotate — windows stay on `W-G-W`,
  `D-G-SERVICE` on `W-G-S`. (→ DESIGN-LOG.md, "Decks and the garage")
  - `D-G-SERVICE`'s centre is **x=8'-1"** since 2026-09-11 (`SERVICE_DOOR_OFFSET` 0'-7", RO
    6'-7"..9'-7"), an inch off `D-M-ENTRY`'s 8'-0"; it was 10'-0" from 2026-09-07. **The
    "24-inch steps" rule that held it there was the house's own invention** — the engine
    grades how many studs an opening interrupts, and the only hard bound is the corner pack
    (x 6'-0"..6'-3 5/8"); the king at 6'-4" clears it by 3/8" and the RO interrupts the one
    stud at 8'-0". `D-M-ENTRY` still cannot move (its east jamb is 6" west of `N-M-N2`, the
    bearing tee). `code.R311_3_exterior_landing` passes both on a 3'-7" deck (x 6'-0"..9'-7").
    **Do not answer anything here by moving the garage back.**
  - **The interior landing (`FS-BW-GARAGE`) sits in the SW corner**: sheet x 6'-7"..9'-11 5/8"
    (the RO's west jamb to the stem's finished face + 3'-0"), 1/4" off `W-G-W`'s gyp face, so
    the wall closes the west edge and `RL-BW-GARAGE-W` is deleted (uid `BWRGGWAAAA` retired).
    Carriers `BM-BW-FC`/`-FE` at x=7'-1 1/2"/9'-5 1/2": the west one is SISTERED to
    `FS-BW-FLOOR`'s joist at 7'-3 3/4" (3 3/8" between the stem's board and that joist for a
    3" beam — forced), the east one's face is on the jamb. `PT-BW-IC`/`-IE` are **4x4 KDAT,
    25 3/4"**, slab to carrier soffit, on authored `ABU44` standoffs (`CN-BW-IBASE-*`) that
    take **NO cast-in bolt and sit on no thickening** (`anchored=False`, 2026-09-11): a
    5/8"x10" `AB-058-10-SS` wants ~8" of embedment and `SL-G-FLOOR` is 3 1/2" on 1" of XPS,
    so the bolt would have dragged a 10" thickening along to house itself. The bases bear
    only — no uplift, no lateral claimed — and the slab never needed help: 8.1 ft² at 50 psf
    is a lighter, lower-pressure load than one tire of the car that parks on it. The anchor
    order is **4, not 6**. They were 6x6s stopping 7 1/4" SHORT of the beams, sized off the
    pier top, at 0 FAIL.
  - **The stem's finished inside face is x=6'-11 5/8", not 6'-11"** — GARAGE_ICF_6's 5/8"
    `gwb-stem` board is on the ICF from grade up. `GARAGE_STEM_INSIDE_X_FT` carries it; the
    flight, the landing's east edge and both carriers derive from it. The ledge on the stem
    top under the framed wall's gyp face (6'-6 3/4") is 4 7/8", accepted (owner).
  - **`LANDING_EAST_FT = SERVICE_RO_EAST_FT` (9'-7") had to move in the SAME commit as the
    door**, not the separate one the plan asked for: `FS-BW-FLOOR`'s 12" o.c. joist grid puts
    a joist at 9'-3 3/4", inside the new east carrier, until the field's east edge follows the
    deck edge in. Seat beams span 3'-7"; `STAIR_FOOT_X_FT` is 15'-7" and `plan/site.py`'s two
    paver literals followed it by hand.
  - **`ED-M-ENTRY-LT`/`-SW` exist because the narrowing exposed a false PASS**:
    `code.R303_8_exterior_stairway_illumination` had been satisfied for `ST-BW-ENTRY` by
    `ED-M-PANTRY-LT` — a wall light INSIDE the pantry, 3'-10" from the tiers in plan through a
    wall. The sconce is on `W-M-N2`'s bay centre at x=11'-4", 6'-4" up; its switch is on
    `W-M-STRW`'s mudroom face (R303.8.1 wants it inside the dwelling, not in the garage).
  - `EQ-M-HP3-OD` sits at x 12'-4"..15'-2 3/8", `SL-M-HP3PAD` at x 12'-1"..15'-5", clearing
    12 11/16" to the nearest glass (Gree's 12" lesser-side minimum); the front walk's west
    edge is x=15'-9". Nothing grades an Equipment against a deck or clearance envelope, so
    check any future move by hand. **HP3's y-axis clearances are short and it's a deferred
    owner decision** — Gree wants 12"/6'-6", this position has only 8"/25 11/16", and the
    48 1/2" slot can never give more. `params/hp3_pad.py::_BACK_CLEAR_IN` is the only record;
    no check flags it. (→ DESIGN-LOG.md, "Decks and the garage")
  - `EQ-M-HP1-OD` moved 6'-6" east; it oversails the house's NE corner by 3" to keep its 14"
    clearance to the garage's east gutter. Its disconnect `ED-M-HP1-DISC` is a 6 1/2" can in
    a 14" slot, **NEC 110.26 working space ungraded**. Neither can move further on this face.
  - Aligning `ST-G-SERVICE` under its own landing fixed a standing `code.R312_1_guard_height`
    FAIL on `SL-G-STEP-0`. `ED-G-SW`/`ED-G-EXT-SW` sat inside `D-G-SERVICE`'s rough opening
    AND 12" above the landing (a garage device's `Mount.elevation` is off the SLAB); since
    2026-09-11 they are at x=10'-8"/10'-2", east of the king, at 80" over the slab = 46" over
    the landing. `ED-G-LT3` is at the landing's centre, x=8'-3".
  - `notes/garage_orientation_lot.md` is the revert recipe; a south-lot revert must also flip
    `SetbackSpec` edges 0 and 2 (deliberately untouched here).
- **The garage has no wainscot; its base skin is a uniform 24" band on the ICF stem, all
  four walls (2026-09-03 deletion).** `GARAGE_BRICK_WAINSCOT`, `GARAGE_ICF_6_BRICKLEDGE`,
  `off-white-brick`, and both `_BRICKLEDGE` dicts in `params/foundations.py` are deleted
  outright (not kept unreferenced) — revert via git history, not a one-line `assembly=` swap.
  - `GARAGE_ICF_6`'s `coil-gap`+`coil-ext` band always ran behind the former wainscot, so the
    deletion cost nothing structural: **156.2 SF unchanged** that day (162.7 SF since
    2026-09-11 — the service door's stem gap closed, which is added band, not restored
    wainscot). (→ DESIGN-LOG.md, "Decks and
    the garage")
  - Stock sheet stays **48"x120" at 0.040-0.050" gauge** — a 48" sheet rips into two 24"
    bands with no waste, so the heavier sheet costs nothing extra per SF over 24" trim coil.
    Second best on supply failure: 0.024" heavy-gauge 24" trim coil. **Never 0.019"** — takes
    a permanent shovel dent. (→ DESIGN-LOG.md, "Decks and the garage")
  - `STEM_TOP_Z_FLASHING` (`plan/storeys/garage.py`) is five `DRIP_FLASHING` runs, 80 LF,
    broken only at the overhead door's stem gap (the service door's gap closed 2026-09-11;
    `TR-G-STEMZ-S2`/uid `8JZR6X0A4X` retired). One counter-clockwise loop, every run
    `back_side="left"` so each wall's inboard normal puts the turn-down outboard. **Nothing grades
    `back_side`** — get one wall wrong and the drip points at the wall at 0 FAIL.
    `test_garage_base_skin_is_the_stem_band_alone_and_its_top_is_flashed` pins it; confirm in
    the viewer too.
  - **Aluminium over aluminium; no check grades it.** `corrugated-panel-24` above the band is
    26 ga PVDF-coated steel; the band and the Z are aluminium — never lap metal-to-metal
    (sealant/EPDM between) or let aluminium touch concrete/mortar. `aluminum-flat-pvdf` on
    the Z, not `metal-dark-exterior`, is the whole enforcement.
  - `OVERHEAD_DOOR_OFFSET`'s 4'-0" has lost its defence (the asymmetric-pier argument died
    with the wainscot) and is now an open question — moving it drags stem/grade-beam gap,
    footings, Z break stations, and a water-service sleeve. Left suppressed while undecided;
    **do not quietly re-decide it either way**. (→ DESIGN-LOG.md, "Decks and the garage")
  - `W-GF-S3` / `W-GF-N2` are a kept fossil (plain `GARAGE_ICF_6`, nothing stands on them) —
    the wall/room census tests pin the count so a cleanup can't un-split them by accident.
    `W-GF-S-DR` joined them on 2026-09-11: the service door's grade beam is full stem now, its
    two nodes PINNED at x 8'-3"/11'-9" (`_FOSSIL_SERVICE_OFFSET`) so `FT-GF-S-DR` stays over
    the hydrant crossing `SP-GF-S-HYD` names. Nine stem segments, one grade beam.
- **The garage is white again** (all four walls `GARAGE_WALL_2X6`, `corrugated-panel-24` —
  24 ga PVDF Linen White since 2026-09-14, the same colour and gauge as the house; 412 psf at
  2'-0", and the wall coverage is **34-2/3"**, not the 32" roof figure the drawings used).
  `standing-seam-nailstrip-26-green` stays in the catalog, referenced by nothing — going
  green again is a one-line `layer_materials=` change. (→ DESIGN-LOG.md, "Decks and the
  garage")
  - **`Wall.layer_materials`** (`model/refs.py::LayerMaterial`) swaps ONE named layer's
    material on ONE wall, appearance only — thickness/function/framing/banding stay the
    assembly's. A typo in either half is otherwise silent; `integrity.wall_layer_material`
    FAILs on an unknown layer name or material tag.
  - Both renderers key metal-skin colour off the material's declared **`finish`**
    (`FINISH_BASE` in `ui/src/nordic/palette.ts`, `_FINISH_BASE` in `emit/gltf/palette.py`,
    kept in step BY HAND) — a bare `color=` attribute is the drawing-hatch tone, not the
    paint, and is invisible to either renderer.
  - The gable triangle above a wall comes for free: `resolve/roof_edge.py` builds the
    wall→roof closure from the host wall's own layers.
- **The garage roof edge — fascia and ridge cap — is `metal-dark-exterior` (`#1c1f24`), the
  house's exterior dark, across seven members: six fascia pieces plus the vented ridge cap.
  The two are named through DIFFERENT fields, kept in step only by this line and one
  assertion (`test_model_json.py`).**
  - Fascia (6 pieces: 2 eaves + 4 rakes) is named on `FasciaBoard` inside `_GARAGE_EAVE_TRIM`
    (`plan/storeys/garage.py`). Ridge cap is `Roof.edge_trim_material` on `RF-GARAGE`, which
    also drives corner trim (`resolve/roof_trim.py::_edge_trim_material`) — this roof's 16"
    overhang frames fascia+soffit and no corner trim, the only reason naming it recolours
    exactly one member. A zero-overhang roof would spread the colour to corner trim too.
  - **Changing the accent colour is a two-place edit** — miss one and the cap and fascia
    drift apart, reading as a mistake.
  - Fascia substrate is formed metal over a wood nailer, not 5/4 cellular PVC — dark colour on
    PVC forces a solar-reflective coating that caps the LRV below `#1c1f24`. **The soffit
    stays cellular PVC and stays white** so the overhang doesn't read as a shadow.
  - Tag-keyed in both renderer palettes (`_FINISH_BASE` / `FINISH_BASE`, kept in step by
    hand), not by declared `finish` — a fascia/ridge cap is a framed MEMBER and `memberColor`
    has no catalog access. Neither tag contains "seam" and trim carries no `skin_family`.
- **The garage ICF stem is covered on both faces above grade.**
  - Inside: 5/8" gypsum banded from `GRADE` up (`code.R316_4`), continuing the board
    `GARAGE_WALL_2X6` already lines with.
  - Outside: `coil-gap`+`coil-ext`, PVDF-painted aluminium (`aluminum-flat-pvdf`) from 2"
    below grade to stem top on a **1/4" vented standoff**, 316 stainless gasketed screws into
    the ICF webs. 162.7 SF, $813-1,627 (156.2 SF until 2026-09-11, when the service door's
    stem gap closed and 3'-6" of bare wall gained the band), the garage's entire base skin, flashed at the top by
    `STEM_TOP_Z_FLASHING`.
  - **The standoff is not optional and is not about drainage.** A painted sheet laid flat is
    0 perms — a Class I retarder on the cold side of the stem — and produces a real
    `building_science.condensation` FAIL. The 1/4" gap restores outward drying; delete it and
    the FAIL returns. (→ DESIGN-LOG.md, "Decks and the garage")
  - Both bands are banded, not full height; the band pushes the stem's exterior face 0.30"
    east (inside `_axis_match`'s 1/2" tolerance). **Do not recess the EPS to hold the face
    still** — that re-opens the old rain shelf.

### Exterior colour, balcony and veneer

- One exterior dark, `#1c1f24`, on every dark metal element on the envelope:
  opening casings, roof rake/eave/ridge trim coil, eave water chain (drip edge,
  box gutter, downspouts), and guards.
- Windows/doors in a clad wall draw casing (resolve/geometry_openings.py
  `exterior_trim`) in this tone. Recolor only via `window_trim` in
  emit/gltf/palette.py + ui/src/three/members.ts `CATEGORY_COLOR.window_trim`.
- Roof edge/water chain/guards get the colour by *material*
  (`metal-dark-exterior`), named by `RF-HOUSE.edge_trim_material`,
  `params/roof_trim.py::_CHAIN_MATERIAL`, and `RAILING_DARK_METAL`. Both
  renderers resolve via `_FINISH_BASE`/`FINISH_BASE` (emit/gltf/palette.py,
  ui/src/nordic/palette.ts) — keep in step.
- A gutter/downspout is a solid: `ResolvedSolid.material` wins over category
  palette only when it *states* a colour; a generic ref like `"aluminum"` still
  falls to category.
- Author colours under the tone wanted on screen, not the tone typed: the
  viewer's lighting (0.8 hemisphere + 0.9 key + 0.6 IBL) lifts a dark albedo
  well above itself (→ DESIGN-LOG.md, "Exterior colour, balcony and veneer").
- Guards are `RAILING_DARK_METAL`, split off `POST_WHITE_PAINT`. The balcony's
  two remaining 6x6 centre pillars and the stairwell posts still use
  `POST_WHITE_PAINT` and must stay white.
- Balcony structure (2026-09-03, `notes/balcony_moment_columns.md`, supersedes
  `superseded/balcony_lateral_bracing_design.md`): four cast concrete corners,
  two wood centre posts, three glulam beams. No knee braces exist any more.
- Four CORNER pillars: 12" round reinforced concrete, FIXED at the base,
  doweled into the 12" wall tops of `W-SG-W1`/`E1` — the balcony's entire
  lateral system in both plan directions.
- **Durability intent (2026-09-12, BLD-02).** The goal is long-term durability of
  exposed concrete in ACI 318-19 exposure **F3 + C2**, not any one coating. The
  code baseline meets it on its own: w/cm <= 0.40, f'c >= 5,000 psi, 6% ±1.5 air,
  2" cover. Galvanized bar is the owner's margin on top of that, not a code
  requirement — which is what lets the spec flex without losing the goal.
- **Bar ladder.** Galvanized, **either** ASTM **A767** (galvanize AFTER
  fabrication — A767's classes are COATING WEIGHTS, not a bend-order distinction,
  so naming cl. 1 never settled the sequence; A780 repair at any field cut or
  bend; a WELDED cage leaves A767 for ASTM **A123**) **or** ASTM **A1094**
  (coated stock, bends and fabricates after coating without repair). ACI 318-19
  §20.2.1.7.2 lists both and ψ_e = 1.0 either way. **Fabricator's choice, named
  on the order.** Black bar at the stated cover and mix is accepted only as a
  **written exception**, when neither route can be supplied on schedule. Epoxy
  (ψ_e 1.2–1.5 lengthens every lap ~50%; delaminates) and stainless (4–6×,
  austenitic thermal mismatch) stay **refused**. Sources: AZZ Galvanizing,
  Winsted MN and NE Minneapolis (the A767 after-fab route); CMC GalvaBar,
  Catoosa OK (A1094, stocked). (→ `plans/buildability.md` BLD-02.)
- **The cage is a part, not a field-bent detail.** 8" out-to-out of ties — a
  6-5/8" bar circle + 0.625" (one #5 dia.) + 2 × 0.375" (a #3 ring each side) =
  8.0", which is also 12" less 2 × 2" cover — (4) #5 verticals, #3 rings @ 10"
  o.c., 2" cover, in a 12" round. **TWELVE identical sections house-wide**: six
  court columns and the six north-entry pours (`params/north_entry_frame.py`
  `ENTRY_PIER_CAGE`), lengths per pour, **tied not welded**. It is NOT the
  catalog stock 8" cage (4 #4, #3 @ 12"): 0.80 in² is under §10.6.1.1's 1.131 in²
  floor, and 12" ties exceed §25.7.2.1's 16d_b = 8" for #4. The authored #3 @ 10"
  is exactly 16d_b for #5. Quote it by name, twelve off — Rebarfab (720 First St
  SW, New Brighton MN, 651-633-3337) or a Bolsinger custom against their PASC
  stock format.
- 12", not 10": 2" cover on a #5 cage inside #3 ties needs a 6-5/8" bar circle,
  flush with both wall faces. `SUNKEN_GARDEN_COLUMN_12` serves all SIX cast
  columns in the court (`PT-SG-COL` joined them on 2026-09-10); `_COLUMN_20` is
  retired.
- Beam seat is CAST TO LINE, no grout island: screed the wash/drip lip, take
  tolerance in the `SS316-SHIM-35` shim pack (`CN-SG-STDF-*`), HGAM10 gusset +
  Titen Turbo at >=3" edge distance. `PIER_CONCRETE_12` says NO GROUT ISLAND too
  since 2026-09-12; retyping `PT-SG-COL` did not close that follow-up, it rode
  the island over to the north entry's own seats.
- Two CENTRE pillars are wood 6x6 and **bear on the two cast columns** since
  2026-09-14 — `PT-SG-BF2` on `PT-SG-FCOL`, `PT-SG-BR2` on `PT-SG-COL`, both on
  `ABU66SS` standoff bases (`anchored=True`, cast-in 5/8"). **All six pillars are
  on concrete**; the 3-ply pack, its squash blocks and the five-part
  `MSTA12Z`+`L50Z` tie are retired, kept as `_DECK_BORNE_*` revert records in
  `params/sunken_garden.py`. `CCQ46SDS2.5` cap still closes uplift at each.
- **The four porch beams HANG off the centre pillars** — `BM-SG-FRW`/`-FRE` and
  `BM-SG-BKW`/`-BKE` end at the pillar faces (`N-SGM-FCOLW/E`, `N-SGM-COLW/E`)
  on `HU212-3` face-mount hangers, not `HUC212-3` (that is the concrete part,
  and a 5-1/2" post cannot host a concealed flange). That is what lets both
  columns stay 12" round rather than growing to span beam face to pillar face.
  `PT-SG-BR2` moved 3" north onto the column axis with it.
- Each centre pillar passes through a framed 9" chase in `FS-SG-PORCH`
  (`FO-SG-BF2`/`-BR2`), 1 3/4" clear on all four sides; the joist at x=17'-10"
  (the module's nearest line, wholly inside the pillar) is cut and headed. **The
  trimmers stand on the OPENING's own edges and bear on the beam** — each of the
  four takes its beam's full 4 1/2" — not on the joist lines 16" either side,
  which is what this line claimed until 2026-09-15; widening the opening to make
  that true would cut two sound joists for a longer header off the beam.
  **No hanger on the post's N/S faces** — four will not fit on a 5-1/2" face.
- Porch joists CROSS both beams (`JoistSpec.cantilever_start = 4-1/4"`, was
  2-3/4" — the extra 1-1/2" is what takes the front rim band clear of
  `PT-SG-BF2`). The composite sheet ends 4-1/4" outboard of `RL-SG-PORCH`'s
  guard line by design.
- **A post is the WOOD, not the clear span between its bearings** (2026-09-14).
  `resolve/envelope.py::_post_connector_insets` takes the `ABU66SS`'s 1-3/16"
  standoff (Simpson's 1" over the stirrup's own 7 ga plate) off the bottom and
  the `CCQ46SDS2.5`'s 7 ga seat off the top, from the catalog record. Without it
  `PT-SG-BR2` reads 121-3/8" against IRC Table R507.4's 120".
- **`SPEC.balcony_fall_in_per_ft` = 1/4 in/ft** — authored; the rise is derived.
- **`BM-SG-BLC` is flush-framed** (2026-09-16): the joists hang in it on LUS28Z and bear
  on top of BLW/BLE, keeping the 9" drip cantilever and the corner columns unchanged. BR2/BF2
  stand 10.59'/10.44' against 2018 IRC Table R507.4's flat 14' for a 6x6 (the engine's old
  area-stepped 10' row was a table bug).
- `structural.deck_post_bearing` is now NOT_APPLICABLE house-wide and
  `post_bearing/*` has left the engineering register — no post in catlin stands
  on a floor system. `notes/centre_pillar_bearing.md` is KEPT (registered kinds
  must name a live note) and carries a dated section saying so.
- Centre pillars are DF-L, not SPF — connector requirement
  (ESR-2604/2330/2105/3096, all SG >= 0.50 at MC <= 19%); see
  `POST_WHITE_PAINT_DF`. C_M 0.70 wet-service is already in the 658/375 lbf in
  `library/hardware.py` — do not derate again.
- Three beams: treated SYP glulam, `"3.5x11.875"` (24F-V5M1/SP),
  clear-finished. Author DECIMALLY — `_RE_NOMINAL` silently resolves a
  nominal-looking string 1-1/4" short. Engineered items `deck_beam/BM-SG-BL*`.
- Front-row beam/column line did NOT move with the corner change; its 12"
  column top runs 3-1/4" past the beam end. Re-solving it moves the deck edge,
  fascia, drip, gutter and `BALCONY_FRONT_AXIS_Y_FT` together.
- Fallback: New Castle Steel HDG 6x6x3/16" post w/ welded base plate
  (~$458/10'), still needs a fabricated saddle with no shop drawing made.
- Both guards: Williams Architectural Products, ICC-ES ESR-3485, 42" black
  (Menards; Eagan MN); alternate Fortress Al13 Home.
- `RL-SG-PORCH` is surface-mounted (`RAILING-EXT-ALUMINUM-SURFACE`): west/east
  legs on 12" concrete wall tops take ESR-3485's baseplate anchors directly.
  The south leg bolts through the plank into joist-bay blocking north of the
  beam — never through `TR-SG-CAP-FRW/FRE`, its butyl is the dielectric between
  aluminium cap and copper-treated framing.
- `RL-SG-BALCONY` stays fascia-mounted (through-bolted PVC fascia + 2x8 rim)
  because `FS-SG-DECK`'s aluminium plank is the porch roof and carries no other
  penetrations — do not switch to surface mounting. Needs rim blocking in
  `FS-SG-DECK.reinforcements`.
- Veneer `W-B-BRICK` (112.5 SF, both faces exposed; top at -8" so `FS-SG-PORCH`'s joists
  pass over it with 3/4" of air — nothing grades that gap) stands on `W-SG-BRKBM`, a 12"
  x 17-3/4" grade beam spanning 19'-0" between `W-SG-W1`/`W-SG-E1` — not on the
  house footing (`FT-B-BRICK`, retired). Basis:
  `notes/sunken_garden_veneer_beam.md` (2026-09-05).
- Nothing in the engine grades a thermal break for continuity — a `Footing`
  resolves to one blob with no polygon, so verify an adjacent gap directly (→
  DESIGN-LOG.md, "Exterior colour, balcony and veneer").
- `SG_VENEER_BEAM_14` = 12" pour + 2" of 40 psi XPS `Layer`. The beam is its
  own open wall-graph chain and takes the FALLBACK outward sign — do not trust
  it; verify against
  `test_catlin_contract_m3.test_the_veneer_beam_isolates_the_house_footing`.
- `FT-B-S2`/`FT-B-S3` south face is now at **-8"** (via `offset`, not width,
  keeping all 20" of bearing) — anything re-centring these footings must keep
  that face.
- Brick's y is fixed at -10.05"..-13.675" by the beam; `N-B-BRICK-W`/`-E` sit
  at -8.05". `N-B-BRICK-E` is at 27'-6", not 28'-0" (`W-SG-E1`'s axis), so the
  east wythe does not walk inside the retaining wall.
- 2" EPS (ASTM C578 **Type II**, 15 psi — not Type I) is in the BACKUP wall's
  `_GARDEN_CURB_CORE`/`_GARDEN_FRAMED_OUTBOARD` layers, not in
  `BASEMENT_BRICK_VENEER` — blast radius is `W-B-S2`/`S3`/`S2-FR`/`S3-FR` only.
  `code.energy_prescriptive` grades one assembly at a time, so foam in the
  veneer's own stack would earn no R.
- `eps:2.0` is a distinct price key for labour, not thickness —
  `envelope_layers` qualifies on `thickness_in` only, so any other 2" EPS
  elsewhere would silently inherit this rate. None exists today.
- Do not anchor the wythe to `W-SG-W1`/`W-SG-E1` to cut anchor count:
  unreinforced brick can't span 18'-8" horizontally, and both ends want a soft
  joint the model does not carry and the engine does not grade (→
  DESIGN-LOG.md, "Exterior colour, balcony and veneer").
- Do not describe this beam as reinforcing `W-SG-W1`/`E1` — those walls already
  PASS `structural.foundation_unbalanced_fill` independently; the beam's only
  job is the thermal break.
- Two engine bugs fixed here: `local_grade_elevation_m` now uses whole-polygon
  containment, not centroid, for footing shelter; `_exterior_shells_by_storey`
  now keeps holes over an open excavation floor rather than filling every
  interior ring once the court connects to the house.


### Sunken garden court

- **Every interior face of the court is washed white, and that is a daylighting device.** An
  untinted white mineral silicate wash (`silicate-wash-white` in `library/materials.py`, LRV 90)
  on: the five court walls' **court face**, full height (`SUNKEN_GARDEN_WALL` layer 0); all six
  12" cast columns, full round; and — as `silicate-wash-white-block` — the **outboard (yard)
  face** of the three raised-garden perimeter legs, banded to the exposed 3'-4". Bare grey
  concrete reflects ~23-35%, so the court absorbed most of the daylight it was supposed to
  deliver to the basement's south glazing. **Nothing in the engine grades any of this** — no check
  reads reflectance, albedo, LRV or SRI — so a 0-FAIL report says nothing about whether it works
  (→ DESIGN-LOG.md, "Sunken garden court").
- **Deliberately NOT washed**, and each for a reason: `W-B-BRICK` (a colour accent wall, see
  below), `SL-SG-FLOOR` and the porch stair treads (a mineral coating on a walked surface wears,
  and it is a slip question), the court wall **tops** (`W-SG-E1`'s is a walked threshold, same
  reason), and the two raised-garden **balcony returns** (they face no lawn — layer 0 on them
  lands in the terrace fill).
- **The silane is GONE on every washed surface and must not come back.** `SUNKEN_GARDEN_COLUMN_12`
  used to specify "silane/siloxane repellent at 28 days, re-applied ~10-yearly". A silane makes
  concrete hydrophobic and non-absorbent — the one condition a potassium silicate cannot bond to.
  They are alternatives, never a stack; the wash is itself vapour-open weather protection, and the
  10-year recoat obligation went with the silane.
- **The wash layer's side is held by ONE thing: the closed walk through `W-SG-ARCH`.** The
  `N-SG-*` component resolves to outward sign **-1.0** only because `W-SG-ARCH` supplies the
  N-SG-MW/N-SG-ME leg. It is a concrete `Beam`, not a wall, since 2026-09-16:
  `resolve/orientation` counts a cast beam between two wall nodes as a loop edge
  (`assembly_material.is_cast_beam`). Delete it, retype it to wood, or rename either node, and the
  sign falls to +1 and the wash moves to the outboard, buried face of all five walls — **silently,
  at 0 FAIL**. `test_masonry_finish.py::test_court_wash_faces_the_court` is the guard.
- **The POUR DOES NOT MOVE, and `alignment` is what holds it.** Every washed wall carries an
  offset: `±_WASH_FILM/2` on the RG legs (`+`) and the fireplace (`−`), and on the five court
  walls `_COURT_AXIS_SHIFT`, derived from the wash inboard AND the 5/16" dimpleboard outboard. Without it the resolver centres the
  whole 12 1/8" stack on the node line and the concrete slides 1/16" off the grid, which is not
  what gets built. That 1/16" broke three things and only one was caught by a check:
  `SP-SG-W1-CD-SPA` fell out of its own host (a FAIL), while the corner columns stopped being
  flush with the walls they stand on and the raised garden stopped closing on the court walls —
  both at 0 FAIL, by test only. **If `_WASH_FILM` or the board thickness changes, every
  alignment offset changes with it**; nothing derives one from the other across the params/plan
  boundary.
- **The court walls' outboard face is DIMPLEBOARD, not membrane + composite (2026-09-16).** A
  plain 5/16" DELTA-MS-class sheet (`dimple-board`, library material): full height on
  W-SG-W2/E2/S (`SUNKEN_GARDEN_WALL_DRAINED`), below grade only on W-SG-W1/E1
  (`SUNKEN_GARDEN_WALL`, `extent` top at GRADE in `slot="retained-face"`, so the exposed face
  above the yard is bare concrete and ED-M-HP2-DISC / ED-M-STAIR-LT stay on it). Both walls are
  exterior on both faces, the steel is galvanized, and `engineering/retaining_wall` reads only
  the DRAINAGE layer, so the 60-mil membrane was dropped. Keep the slot: an unslotted band still
  occupies its row full height.
- **`W-SG-ARCH` is a concrete `Beam` (`GRADE_BEAMS`), not a `FoundationWall`, so plans and the UI
  draw it as a hidden grade beam instead of a cut wall.** Uid, tag and the item id
  `retaining_system/W-SG-ARCH` are unchanged; `retaining_system` reads its section from `size` and
  its axis from the resolved solid. It keeps `SUNKEN_GARDEN_GRADE_BEAM_12` (no wash: nothing of it
  shows) and bills in `prices.toml` `[concrete] "beam:SUNKEN_GARDEN_GRADE_BEAM_12"` at the court
  walls' rate. `size` keeps a decimal point (`12.0x17.5`) so `cross_section` reads actual
  dimensions. `W-SG-BRKBM` stays a wall because a `Beam` has no layers for its XPS break.
- **W-SG-W1/W2 and E1/E2 are one pour each but stay two elements.** The halves differ in
  `lateral_support`, `unbalanced_fill`, reinforcement, `base_restraint_ref` and how far the
  dimpleboard runs, and nothing in the schema varies those along one wall. Merging would
  mis-state the engineering (a false fill on the braced half, an inflated court FS). The layout
  lines already chain each side as one run on the drawings. **Nor can the court go prescriptive
  by treating it as a basement:** with W2/E2/S relabelled `top_and_bottom`, Table R404.1.2(8)
  passes them easily (#5 @ 7" vs #6 @ 38" required), but nothing braces their TOPS — the porch
  beams brace W1/E1 only, and ARCH, BRKBM and the corners act at the base and ends — so R404.4
  governs. Prescriptive would need new top struts across the open court.
- **A wall's faces are NOT `axis ± thickness_m/2` any more.** That shorthand is only right while
  every layer bears and the stack straddles the node line. On a washed wall `thickness_m` is
  12 1/8" while the pour is 12" exactly where it always was. Read the STRUCTURE layer's polygon
  (`_pour_faces` in `test_catlin_outdoor_structures.py`). For the same reason a `FootingBedding`'s
  band is now centred on STRUCTURE layers only (`resolve/envelope.py`): a levelling pad is placed
  by what bears on it, and the wash had been dragging it 1/16" off the block.
- **Band the raised-garden wash off `LayerDatum.WALL_BASE`, NEVER `GRADE`.** `GRADE` resolves to
  `plan.project.site.grade` — the single global site grade at **-2'-10"** — and the yard this wall
  actually stands in is **-3'-4"**, so a GRADE band sits 6" too high. `WALL_BASE + 8"` is exact.
  This is the "grade cannot see a terrace" problem; a later reader will want to "simplify" it.
- **The SRW block is the weakest substrate in the scope and wants a test panel before 245 SF.**
  Dry-cast integrally-coloured units are far less absorbent than cast-in-place and frequently
  carry an **integral water repellent**. Beecko-SOL (silica-sol modified) is the answer, the open
  dry-stacked joints will take it unevenly, and efflorescence out of the backfill can lift or
  stain it. The manufacturers' own instructions require the trial.
- **The wash is 1/8" thick and `polygonOffset` is what stops it z-fighting — not the thickness.**
  `Material.coating=True` does NOT stop a wall layer drawing (`_is_coating` is scoped to room
  floor finishes), so the wash gets a real plane, and Panel3D's 24-bit depth buffer on
  `PerspectiveCamera(50, 1, 0.05, 500)` resolves only `z² × 1.19e-6` m — 0.48 mm at 20 m, 3.2 mm
  at 52 m. Thickening the layer was a losing race (0.01", 1/16" and 1/8" all shimmered);
  `WASH_POLYGON_OFFSET` in `ui/src/three/materials.ts` wins the depth test deterministically at
  any distance. **Do not "fix" a future shimmer by inflating `_WASH_FILM`** — the offset is the
  mechanism, and every washed wall's `alignment` is half of `_WASH_FILM`, so inflating it moves
  three files. glTF has no `polygonOffset`, so an exported `.glb` in a third-party viewer can
  still shimmer; that is a format limitation, not a reason to re-inflate.
- **The wash has a procedural texture, like the metal skins and the masonry do.**
  `createMineralWashMaterial` builds one shared 4-ft-module tile of low-frequency mottle with a
  matching roughness map, world-scaled by `applyMineralWashUv` so a 10' court wall and a 20 SF
  fireplace panel show the same cloud at the same size. It is declared by `Material.finish ==
  "silicate-wash"`, checked BEFORE the masonry branch (the fireplace's wash sits on a brick wall
  and is not masonry). The SRW legs take the other path: `silicate-wash-block` →
  `SILICATE_WASH_BLOCK_STYLE`, a `CMU_STYLE` clone on the 18"×6" SRW module, because there the
  dry-stacked unit really does telegraph. Both carry the depth offset; no other masonry style
  does, and none should — pushing a real wythe toward the camera would let it win against things
  legitimately in front of it.
- **No new `notes/` entry, deliberately.** `notes/` holds hand-worked **oracles** for
  calculations, and there is no calculation here — no check reads reflectance — so a note would
  name no oracle and the lint would have nothing to bind. Do not add one.
- **The court is one surface, one riser.** `SPEC.court_step_down_in = 0`; `SL-SG-FLOOR` is
  flush with the basement floor plane and the 494 sf court reads as one floor. The only step
  is the 7 1/4" riser at `D-B-PATIO`. `SL-SG-STOOP` is retired — never reuse uid `SGS503AAAA`.
  `code.R311_3_exterior_landing` reads "D-B-PATIO lands on SL-SG-FLOOR, 7.3" below threshold".
- **Do not lower the court below the flush plane** — 7 1/4" is the legal ceiling, not a
  preference: R311.3.2 caps a non-required, inward-swinging door's riser at 7 3/4"
  (`_MAX_NONREQUIRED_STEP_DOWN`), and any lower step needs its own landing (→ DESIGN-LOG.md,
  "Sunken garden court").
- Ponding over the court is ~298 cf against ~177 cf of 100-yr/24-hr rain (~1.7x); the
  two cubic-foot figures scale with the court's area and moved when it shortened to 26'-0"
  — **the 1.7x ratio does not**, because both terms scale by the same 494/532. Cite the
  ratio, not the volumes, unless the volumes are what is being asked for. The
  governing case is snowmelt over a frozen grate, where `DRW-SG-MAIN` contributes nothing.
- **`W-SG-ARCH` must not move, and since 2026-09-10 the reason is no longer the ratio.**
  Dropping its top to the rim underside gives a 10 1/4" section at phi-Pn 60,712 lb, which
  FAILED at Pu 62,051 (d/c 1.02) and **passes at today's Pu 40,145 (d/c 0.66)**; the 8 1/2"
  section passes too, at d/c 0.80. (Pu was 49,157 until 2026-09-14, when the strut force
  became a derived reaction rather than half the largest member's thrust — the south wall's,
  which cannot compress an E-W strut. `notes/..._court_free_body.md` §8.) What holds 12" x 17 1/2" is the SEQUENCING argument — the loop
  must close before backfill, and a strut whose bottom is tied to a surface that moves is a
  residue, not a chosen depth — plus no redundancy and a saving of **0.45 CY**, not the
  ~1.1 CY this line claimed until 2026-09-14 (1.1 CY is the WHOLE beam; the shallower
  section keeps most of it, and the delta is the 87 in² difference). Read
  `notes/sunken_garden_court_free_body.md` §8's three-reason block before shrinking it. Its
  top and `_rim_underside_in` are the same expression. `FO-SG-ARCH` is retired with the stoop.
  `W-SG-BRKBM` carries no structural load — it is the veneer's thermal foundation only.
- `_pier_bell_bottom_ft` is **derived**, not pinned: `(_court_top_in - frost_depth_in) / 12`
  — do not pin it again, a pinned literal silently drifts the next time the court moves (→
  DESIGN-LOG.md, "Sunken garden court"). Both bells carry 42" cover; shafts are 128.1875".
- **Both pier bells are 36" (2026-09-10).** The 36" was a fossil sized for a 20" column
  that shrank to 12"; PT-SG-COL's 30" was set by nothing. One diameter, one under-reamer
  setting, one schedule row, ~$27-43, and the tightest pier in the house goes d/c 0.83 →
  0.60. **What the extra 3" per side spends is the gap to FT-B-S2/S3: 8" → 5" in plan.**
  They still never meet — the bell's top is 22" below the house strip's bottom — so the
  live constraint is SEQUENCING, not clearance: auger both shafts with the open basement
  excavation or they undermine the house footing. `AN-SG-PLACEMENTS` says so on the drawing.
- **`W-SG-W1`+`W2` are ONE pour, and so are `E1`+`E2`** — one 12" section, one form height,
  placement 2. They are two elements because the restraint condition changes at `N-SG-MW` /
  `N-SG-ME`: braced top-and-bottom north, R404.4 base-restrained south. So does the steel —
  **#6 @ 38" north of y = -11'-0" and #5 @ 7" (retained face) south of it, in one form.**
- **One footing type in the court, `COURT_FOOTING_12`** (was `RETAINING_FOOTING_96` +
  `PORCH_FOOTING_84`). Identical stacks — 12" of EXPOSED_MIX — split on a width an Assembly
  does not carry, and the porch card declared **13"** where every strip is built at 12". The
  merge removed the lie and a row off the S-100 FOUNDATION SCHEDULE.
- **All six of the court's 12" cast rounds are `SUNKEN_GARDEN_COLUMN_12`** (PT-SG-COL moved
  off `PIER_CONCRETE_12`, which is now the north-entry piers and nothing else), and that
  assembly finally names `concrete=EXPOSED_MIX`. It stated 5,000 psi in prose only, so the
  register printed **the front column as the weaker of the two identical columns** holding
  the ends of one frame. Consequences: corner φM_n 20,900 → 24,700 lb-ft (re-derived by
  hand in notes/balcony_moment_columns.md §4 — β1 steps to 0.80 and φ reaches 0.900, which
  is half the gain), class B dowel lap 35.6" → 27.6", PT-SG-COL's axial capacity 187k →
  286k. No demand moved. The retype also drops the grout island PIER_CONCRETE_12 carries.
- **One excavation plane again**: `FB-SG-ARCH`'s undercut derives to 33", not the footings'
  42", so all six beds bottom on `_SG_WALL_BED_BOTTOM` with the drywell's top. The 42" was
  copied and is not required — the beam has no `Footing`, so it is not in the frost
  population at all. The BEAM still hangs 9" lower; only its bed came up.
- **Three placements, not four**, and the order is on the drawing (`AN-SG-PLACEMENTS`):
  footings + both belled piers monolithic; then all five walls + the grade beam at one form
  height (house basement wall poured, cured and surveyed FIRST, for the epoxied break
  dowels); then the rim slab with all six columns. `AN-SG-MIX` permits EXPOSED_MIX for the
  whole court so it comes off one ticket — **do not retype PIER_BASE_12**, it is shared with
  the north entry. `AN-SG-COLDWEATHER` puts a hard 1 November milestone on placement 3.
- **`_veneer_beam_bottom` stays held** at -120 3/16", not flush with the slab underside — a
  flush beam is only 10 1/2" deep against ACI 318-19 Table 9.3.1.1's L/16 = 14 1/4" minimum
  for a 19'-0" span. Held, the beam is buried but its 17 3/4" section survives.
- `FT-B-S2`/`S3` cover below `SL-SG-FLOOR` is 8".
- `plan/site.py`'s two garden spot elevations are -9'-1 7/16"; they are a structural input,
  not drafting annotation — `engineering/balcony_wind.ground_below_ft` takes the site's
  lowest spot and these two set it (h 22.7', q_h 18.6 psf, wind base moment 1,385 lb-ft; the
  2,502 lb-ft guard case still governs). Move them only alongside
  `notes/balcony_moment_columns.md` and `test_pier_calcs`'s schedule.
- `space_summary`'s interior-hole filter is an area-overlap test, not a single
  representative-point containment check — a floor spanning two bays (as `W-SG-ARCH` splits
  this court) needs both bays counted.
- **All five court walls top out on the porch datum. One form height.** `SPEC.
  retaining_top_ft` is `porch_top_ft` since 2026-09-10, not `(site_grade_in + 36)/12` — the
  36" was recorded as a MAXIMUM when the owner's call was a band (around 36" out of the
  yard, up to about 48", because the wall may be read as a guard). The exposure is a RESULT
  now: `RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN` is 40" against the -3'-4" yard
  `plan/site.py` authors, pinned by `test_retaining_court`. Keep the terrace name separate
  from the porch-floor name so a future divergence is a one-line change.
  - It doubles as `params/raised_garden.py`'s `RETAINING_WALL_TOP_FT` apron TOP, with
    BASE = TOP - drop_ft — moving one moves both. **`drop_ft` is 4'-0" now, eight whole 6"
    courses**, which buries the apron's base course 8" in the authored yard; at 3'-0" off
    the new top it would have stood 4" in the air, the same negative embedment as before
    arrived at the other way. Nothing grades a freestanding wall's base against the ground
    plane, so a wrong constant here goes to 0 FAIL (→ DESIGN-LOG.md, "Sunken garden court").
  - **The apron's `unbalanced_fill` is the DIFFERENTIAL (3'-4"), never `drop_ft`.** It
    tracks `RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN`: the terrace stands that far above the
    yard and below the yard both faces are in the same ground. Writing the 4'-0" run there
    hits IRC R404.1.1's 48" threshold exactly and sends five segmental landscape walls into
    an R404.4 cantilever analysis they have no footing for — five UNKNOWNs, and the wrong
    model of the wall.
- `W-SG-W1`/`E1` bottom on `_wall_bottom` like every other wall; `_PORCH_FOOTING_THICKNESS_IN`
  no longer exists. IRC Table R404.1.2(8)'s 10'-0" row still passes at 9'-1 7/16".
- `FO-SG-TOE-N-W`/`-N-E` void the rim over them, as `W`/`E`/`S` do over the other three toes.
  `FO-SG-TOE-W`/`-E` are cut to `_y_ax_mid`. **The invariant to hold**: the net rim polygon's
  intersection with every `FT-SG-*` footprint must be 0.000 sf — `structural.concrete_
  interference` only grades ISOLATED pours and will not catch a re-lap.
- `DRW-SG-MAIN` sits on the wall beds: `_SG_DRYWELL_TOP = _SG_WALL_BED_BOTTOM`.
  `FD-SG-LEAD-W`/`-E` are the only two leads — the five wall beds form one connected stone
  body (W1↔W2 at y=-11.0', W2↔S via the corner lap, mirrored east). `FB-SG-ARCH` gets no
  lead: its bed bottoms 9" below the well and stops 2" from the shaft, feeding the column
  through its side. Note: `drainage.discharge_consistency` resolves the tag but never checks
  where the pipe actually terminates — verify inverts by hand.
- **The well is pinned off `_y_ax_mid`, NOT off the court's midpoint.** `_WELL_SOUTH_OF_ARCH_FT`
  = 3'-10" holds it at y = -14.8333. It was `(_y_in_s + _y_in_n) / 2`, written out twice, and
  the 2'-0" shortening would have walked it 1'-0" north — putting the shaft's north edge
  inside `FB-SG-ARCH`'s bed band, which nothing grades. The leads are 6'-6" each now, not
  5'-6": they run from `_field_x_*` to the well centre and the toe reach fell 12".
- `Dowel` z is derived off the shared 8" footing-to-footing joint face (mid-way through it);
  the foam block matches that 8". **Nothing in the engine grades a `Dowel` against the two
  footings it names** — check both footing tops/bottoms by hand after any elevation change.
- **The court is 26'-0" x 19'-0" clear and there is a structural floor at 23'-11".**
  Shortening it removes base friction from the capacity and **nothing** from the demand: the
  E-W thrusts cancel identically, so the resultant is the south wall's alone and the south
  wall is the court's WIDTH. Court length is not the cheap lever it looks like — about $700
  to $1,300 a foot, against 0.09 of system FS per foot, and only **2'-1"** of it is left.
  **Re-derive that floor, never quote it**: it is `run = 61,446 x 1.50 / F` with
  `run = 2(L - 9.6667) + 20`, so it moves with the strip width. It was 23'-3" at 8'-0".
- Current stem/toe state: system FS **1.63** (d/c 0.921), stem flexure **0.61**, toe
  flexure **0.70**, heel flexure **0.70**, stem length **9.1198'**. Every schedule in the
  stem bar table clears, `#6 @ 16"` included at 0.97; the 0.53 in²/ft is held on that 3%
  margin and on §5's stone-bed dependence. **It is `#5 @ 7"`, not `#6 @ 10"` (2026-09-17)**:
  the vertical runs continuous on a 90° foot on the footing mat, 7.875" is available, and
  ACI 318-19 §25.4.3.1(a) ldh is 9.35" for a #6, 7.11" for a #5 (free body §6b).
- **ALL FIVE court strips are 7'-0" x 1'-0" CENTRED on the wall axis, zero offset, with a
  `#5 @ 12"` mat (2026-09-10).** They were 96" with a 6" court-side offset for one revision
  and the 96" was a fossil: §3 widened the strip because the resultant fell outside the
  kern, which was true at `H` 11.3698' and is not at 10.1198' (e 0.800' against a kern of
  1.167', a 31% margin). **The outboard edge does not move either way** — 96/24 − 6/12 and
  84/24 are both 3.5' — which is what `params/raised_garden.py`'s 3'-0" apron clear needs.
  The whole 12" comes off the TOE, so the planted field GREW 147 → 160 sf as the court got
  shorter. **Never cut the heel**: a foot of toe costs 0.05 of system FS, a foot of heel
  0.21, for the same yard of concrete.
- **The mat and the width are one decision.** Narrowing removed 22% of the toe moment, which
  is what lets `#5 @ 12"` read 0.70 where it read 0.90 at 8'-0". `#4 @ 12"` is NOT the next
  step down: it fails flexure and falls under ACI 318-19 §7.6.1.1's `0.0018 Ag = 0.259`.
  FT-SG-W1/E1 keep the mat they gained — their 3'-0" plain HEEL is Mu 8,303 against a plain
  12" strip's 3,536, **d/c 2.35**, and nothing in the engine grades a footing's own flexure
  except on the retaining set. Rebar 4,828 → 3,515 lb; the ratio 31.6 → 23.8 lb/cy, and
  **that sag is a bar-size cut, not a hidden row** (a bar size removes steel and no
  concrete). `SPEC.footing_width_in` is the one width and `_RETAINING_FOOTING_WIDTH_IN`
  reads it — there is no second 84 meaning something else.
- **THE CLOSURE BOARD IS THE JOINT, AND THE JOINT IS THE FOOTING.** `foam_length` reads
  `_RETAINING_FOOTING_WIDTH_IN` and the block is centred on the FOOTING, not the wall axis.
  The two coincide at a zero offset; they did not while the strips carried a 6" inboard
  offset, when a board on the axis hung 6" past one end and left 6" of bare
  footing-to-footing concrete at the other. Keep the expression, not the coincidence.
- **One thermal-break product: `THERMAL_BREAK_IN` / `THERMAL_BREAK_PSI`.** The thickness
  was stated three times in two files and the rating twice, once in prose because `Layer`
  has no compressive field. **The break cannot go on one purchase order today** — the two
  closure blocks bill by VOLUME into concrete, the beam's board by AREA into insulation,
  and nothing reconciles them — so `test_catlin_contract_m3` pins every site against the
  constants. A comment is not a guard; the retaining top's spot elevations proved that.
- **One bar arrangement on the whole plane**: #5 GFRP at 8" o.c., count derived from board
  width (10 across the 84" footing joint, 2 across the 12" wall end — 84/8 is an exact 10.5
  and `round` takes it DOWN). Neither count was
  required by any computed limit state. **The bars are why the board exists** — a `Dowel`'s
  foam block is the only way the engine resolves an XPS solid at a joint, so `count=0`
  deletes the board from the model, the bill and the drawings (and `_resolve_dowel` lays
  `range(max(count, 1))`, so a zero is silently a one).
- **Do not merge the two closure blocks.** Per end it is already one continuous board on
  one plane; two objects only because the joint is T-shaped in elevation. Widening the
  upper one buys foam standing in backfill, and destroys the property that makes it work —
  the narrow block lands flush with both faces of the 12" pour, so the board is a form face.
- **`SG_VENEER_BEAM_14`'s layer order is load-bearing for a fire check.** `code.R316_4`
  reads the innermost layer as facing a room; reversed, a bare 2" of XPS fails it. The
  tuple order is now pinned as well as the faces, so a sign flip and a tuple flip cannot
  cancel into a drawing that looks right.
- **Every wall-to-house joint here needs one continuous 2" XPS board, house-footing-underside
  to porch-wall-top, and nothing checks that continuity** — verify by hand after any footing
  or wall-top move. Four sequencing traps are written into `params/sunken_garden.py` above
  the dowels: the butt joint lands on the court floor plane (lap the upper board); the
  garden pour cannot lead the house (the stem dowels are epoxied into cured wall with ~1"
  of tolerance); the beam's board depends on the FT-B-S2/S3 toe trim, which is a HOLD POINT
  before the house footing pour; and the beam's 20'-0" board is the one with no positive
  tie at all.
- **The brick stays, and it is load-bearing for five other things.** If `W-B-BRICK` ever
  goes it takes `W-SG-BRKBM`, that beam's isolation board, an engineered masonry-anchor
  item no prescriptive table reaches, the weeps, two soft joints and a slab void with it.
  Retiring it is a design pass, not a deletion.
  - Stem blocks and footing blocks are sized by different rules and must stay that way: a
    stem block derives as `max(row_span + 8*dia, 12")` off the bar row (right for a 12" wall
    end); a footing block is `Dowel.foam_length` (default derives the old way) because it
    must span the full width of the footing-to-footing joint, not the bar row.
  - All four south strips (S1-S4) sit on one face at -4"; `_TOE_TRIMMED` is empty and
    `_SOUTH_TOE_TRIM` is superseded.
  - The beam's own isolation board (2" XPS across 4" bedding stone, at `W-SG-BRKBM`'s north
    face, -10") is a separate detail from the wall-joint boards above and is unaffected by
    them — it isolates the veneer pour from the house pour, not the wall.
  - All four footings read "8" below SL-SG-FLOOR" on the R403.3 frost branch (not the ~86"
    `sheltered_by` answer) — re-check this after any footing move, since moving a footing
    north is exactly how a frost check buys a false pass.
  - `test_the_veneer_beam_isolates_the_house_footing` pins the 84" board, full 8" depth, and
    zero plan lap against every house strip.
  - `prices.toml`'s `thermal_break` row bills the four closure boards by SF of 2" 40 psi
    XPS — the four boards are not the same size, so check totals against SF, never against
    count. (The two footing boards went 84" → 96" → 84" on 2026-09-10, with the strips.)
  - **FLAGGED FOR THE ENGINEER, NOT TAKEN: trimming the wall beddings' surplus stone.**
    Worth $835-1,250 and the only four-figure item in the simplification pass, and the one
    that touches a load-bearing claim. It collides with the drywell top, with a 5"
    clearance the model already flags as the one to watch, and with the μ = 0.35 friction
    argument that carries the ENTIRE sliding margin (`notes/sunken_garden_court_free_body.md`
    §5 — at μ = 0.25 the court is at FS 1.16 against 1.50). Do not take it on a takeoff
    reading.
- **`W-B-BRICK` is one flat field of unglazed `brown-brick` (`#a07c5c`)**, ASTM C216 Grade SW,
  full height (plinth to top), **112.5 SF** (18'-8" x 94 7/16" = 146.9 SF gross, less
  `AO-B-BRICK-WIN` 1.94 and `AO-B-BRICK-DOOR` 32.5), one BOM row
  `BASEMENT_BRICK_VENEER:brown-brick`. The 129.2 SF this line and `prices.toml` used to claim was
  stale and is reconciled (2026-09-13); no dollar moved.
  - **It stays BARE brown ON PURPOSE, and it is the one court surface that does.** Every other
    interior face of this court is washed white; this wall is the deliberate colour accent
    against them. Do not "finish the job" by washing it.
  - **`brown-brick` is the only brick blend in the house since 2026-09-13** and carries a live
    per-material row under **two** assembly keys — this one and
    `FIREPLACE_BRICK_WYTHE:brown-brick`. The fireplace surround was `white-brick` and is now this
    blend, washed white. `[basis_notes] wall_structure`'s old "one live per-material row"
    phrasing is amended accordingly.
  Glazed brick is unsuitable here: [BIA Tech Note 13](https://www.gobrick.com/media/file/13-ceramic-glazed-brick-exterior-walls.pdf)
  says not to use it where it can saturate, and this court is a rain sump with walls.
  - **Do not delete** `glazed-green-brick`, `glazed-lapis-brick`, `glazed-gold-brick` from the
    catalog, their `MasonryStyle`s in `ui/src/three/materials.ts`, or their `_FINISH_BASE`
    entries in `emit/gltf/palette.py` — none is referenced now, but a scheme revert is a
    three-place change and needs all three intact. Their `prices.toml` rows are commented
    out, not removed, for the same reason.
  - `BROWN_BRICK_STYLE.jitterHSL = [0.008, 0.035, 0.09]` — deliberately between a glaze's
    near-zero and `BRICK_STYLE`'s `[0.02, 0.08, 0.16]`; either extreme misreads on a 129 SF
    unglazed field (→ DESIGN-LOG.md, "Sunken garden court"). Mortar is `#cfc8ba` (tan).
  - **`haus render` cannot judge this material** — its CLI emitters carry only the flat
    de-jittered `_FINISH_BASE` hex, and `--view elevation` emits east/west while this wall
    faces south. Judge jitter/albedo in the headless viewer, or compute the extremes directly:
    `new THREE.Color(base).offsetHSL(±j[0]/2, ±j[1]/2, ±j[2]/2)`.
  - The wythe is one plain full-height STRUCTURE layer — no `slot`, no `extent`. It must stay
    a STRUCTURE layer, not CLADDING, or `integrity.assembly_layers` finds none (same
    precedent as `RETAINING_BLOCK_12`). `Layer.slot` itself is still live and is exercised by
    the synthetic fixture in `packages/engine/tests/test_emitter_band_parity.py`, not by
    catlin.
  - Rate is `$19-30/SF` (scaffold-inclusive, for the full 8'-5" field) — do not reuse the old
    `$15-28/SF` no-scaffold rate.
  - `AO-B-BRICK-DOOR` reveal height is 78" (84" is also available if more coverage is
    wanted); `AO-B-BRICK-WIN` reveal height is 20". Neither opening is a daylight or egress
    subject; reveal overlap onto the opening is deliberate.
  - **A reveal must stay concentric with the opening it reveals** — width and position are
    not free, only height is. Edit a reveal and its opening together.
    `integrity.reveal_concentric` grades every rough opening with a wall behind it against the
    nearest door/window in that wall, at 1" tolerance; `test_catlin_contract_m3` pins both
    pairs.
  - Both arched reveals are a voussoir ring (`ui/src/three/builders/archRing.ts`), one header
    deep (3 5/8"), 3/16" proud each face. Door extrados crowns at 81 5/8", window's at
    52 5/8". **Viewer-only** — an exported `.glb` still shows a plain spandrel.


### Electrical service

- **Class 320 service, decided 2026-09-12.** One Class 320 HDLB (heavy-duty lever-bypass)
  combination meter-main at `ED-M-METER` on the west wall, 320 A continuous, carrying **two
  200 A mains outdoors** — which is also how the house meets 2026 NEC 230.70(A). The trade
  calls the same enclosure "400 A" because 320 / 0.8 = 400; there is no separate 400 A
  service class, and **there is no 225 A service class either** — 225 A is `ED-T-PANEL`'s
  BUS. (→ DESIGN-LOG.md, "Electrical service")
- **Two feeder panels.** `ED-B-PANEL` (225 A bus, 200 A main, 54 spaces) is feeder 1;
  `ED-B-PANEL-2` (200 A bus, 200 A main, 20 spaces) is feeder 2, on the same W-B-W1/W2 face
  at y=25'-0" — **south** of `ED-B-BACKUP-PANEL`, because the bays north of `ED-B-PANEL` are
  full (`ED-B-NET-PATCH`, the ERV duct crossing at 31'-4", `ED-B-BACKUP-ENCL`) and the one
  gap between them is 6 1/2" wide. **Nothing grades a device-on-device overlap or NEC 110.26
  working space**; both are held by the measurements in `plan/mep_electrical.py`. Feeder 2 carries `CKT-SPA`, `CKT-SAUNA`, `CKT-EV-1450`, `CKT-EV-620` and nothing
  else. `electrical.panel_feeder_load` grades each panel's own 220.82 demand against its own
  main (157.5 A and 117.7 A of 200 A); `electrical.service_load` grades the house against the
  meter (267.4 A of 320 A, **52.6 A of margin**).
- **Both panels state `service_amps=200` on their types, and must keep doing so.**
  `code.NEC_705_12_interconnection` reads the panel's own main first and falls back to the
  service size — drop the field and the ESS backfeed gets graded against 320 A on a 225 A
  bus, which silently loosens the 120% allowance at 0 FAIL.
- **No `LoadManagement` anywhere in this house, and none may be re-added without a
  listing.** The four retired groups (`LM-EV`, `LM-WELLNESS`, `LM-WH`, `LM-HP1-AUX`) were
  the only reason the demand ever fit 200 A. Under the 2026 NEC a controller that limits
  load in a service calculation must be a **power control system** — 130.2 requires the
  listing (UL 3141), 120.7 sets the setpoint at <= 80% of the monitored OCPD, 625.42(A)
  points EV supply equipment at the same Part II — and the engine now refuses a credit whose
  basis does not hold. The one basis that needs no listed device is `hvac_interlock`
  (220.82(C)(2)/(4), a compressor against its own supplemental heat).
- **Backup shedding is NOT load management** and was never touched: it lives on
  `Circuit.backup_tier` plus the Shelly Pro 4PM relay and its contactors
  (`backup_component_rows`). So does the water heater's ESPHome/EcoNet Heat-Pump-Only
  automation, now authored as **`CKT-WH-240.backup_va = 500`** — a backup reserve worth
  nothing in 220.82, and **load-bearing**: at the 4,500 VA nameplate the SHED tier's peak
  does not fit the 12kPV's 8 kW continuous.
- **The Emporia charger stays.** It is a listed EVSE (UL 2594 3rd ed.); what it lacks is a
  PCS listing for PowerSmart throttling, which a 320 A service no longer needs. If dynamic
  EV charging is ever to be credited again the path is a UL 3141 PCS, not a different
  charger.
- The aux-heat **outdoor-thermostat lockout is still set** (elements enabled only below the
  -22 F compressor cut-out, so defrost runs unheated) — it is an HVAC control setting
  recorded on `CKT-HP1-AH`, no longer a credit.

### Kitchen: the IKEA SEKTION ladder

- **Every kitchen box is a SEKTION frame** (`library/placeables/sektion.py`, `SEKT-*`), since
  2026-09-11. The generic `CASE-*` catalog is still the shared catalog and other rooms still
  use it; the kitchen does not. `notes/ikea_sektion_ladder.md` carries the ladder, its
  sources and the arithmetic.
- **A width not on the ladder gets a FILLER, not a type.** Bases 12/15/18/21/24/30/36/38/47;
  wall frames 15/20/30/40 high in 15" and 24" depths; high frames 80 and 90. Do not invent a
  size — two house-local types (`FT-KIT-OVER-COLD-3278`, `FT-KIT-MIXER-GARAGE-24`) existed
  only because the old catalog could not reach a number, and both are retired.
- **The toe kick is 3", not IKEA's 4 1/2", and ONE height serves both runs.** Every SEKTION
  frame height is a multiple of five, so nothing closes a 108" ceiling off a 4 1/2" leg. At
  3": `3 + 90 + 15 = 108` tall, and `40 + 15` hung at 53 = 108 upper. Change the leg and
  every course in the room moves.
- **The counter still lands on 36", by build-up.** `3" leg + 30" frame = 33"`, and the
  Silestone is 3 cm (1.181"), so **1 13/16" of sub-top** goes between them. The base types
  stay 36" tall because 36" is what the object occupies.
- **Uppers are 15" deep and hang at 53"; the stacker course is 93".** Not 13"/54"/96". The
  backsplash is 17", inside NKBA's range. Backing rails moved with them
  (`plan/backing.py`), as did the under-cabinet tape (`plan/lighting.py`).
- **Two odd hangs and two fillers, all deliberate.** `FURN-M-KIT-WN1` hangs at 68" above
  `WIN-M-KIT-E`'s 66" head; the over-cold pair hangs at 78" to clear the Frigidaire hinge.
  The mixer garage scribes 2" at the ceiling (72" is unreachable) and the cold bay carries
  2 7/8" at each end (65 3/4" is not two SEKTION widths). Do not try to close either.
- **The north sink run did not move.** `5/8" scribe + B15 + DW + SINK-36 + B30 = 105 5/8"`
  was already all SEKTION widths.
- **MAXIMERA is a product, not a geometry** (`PROD-IKEA-MAXIMERA`). The model has no drawer
  vocabulary; which boxes are drawer stacks is prose in `prices.toml` and `plan/placeables.py`.

## The engineering workflow

Catlin carries ~36 engineered items across nine kinds — the requirements outside the
prescriptive tables. The workflow lives in the root `CLAUDE.md`; what belongs here is where
this house keeps its half of it.

```
haus engineering .                          # the register: what governs, and who sealed it
haus engineering . --item retaining_wall/W-SG-E2       # one item, term by term
haus engineering . --fingerprint retaining_wall/W-SG-E2  # paste into engineering.toml
haus calcs .                                # -> out/calcs/, the package a PE marks up
haus handoff . --zip                        # -> out/handoff/ + .zip, the whole PE bundle
haus print . --sealed                       # the submittal gate — exits 1 today, correctly
haus analysis . --solve                     # the engineered frame, solved in PyNite beside the records
```

- **`notes/` is the oracle set** and `notes/README.md` is its index: which note checks which
  calculation, which are design reasoning, and which **six** are *drawing content* pinned by
  `test_section_goldens.py` and must not be edited as documentation. `notes/TEMPLATE.md` is
  the shape a new calculation note takes; `notes/superseded/` holds designs that are not
  built, each with a `⛔ SUPERSEDED` banner naming what replaced it.
- **No `engineering.toml` exists yet**, so every item reads `unsealed` and the sealed gate
  is shut. That is the true state, not a gap in the setup — the engine reads that file and
  never writes it, and pinning a seal stays a human act.
- **`haus handoff` is how it gets sent.** One command writes `out/handoff/`: the calc
  package and its PDF, only the notes those records cite (9 of the ~50 in `notes/`), the
  IFC and GLB, a `MANIFEST.json` of sha256s, and `engineering.toml.draft` — the register as
  a form with every fingerprint filled in and every human field a `<<blank>>`. The loader
  refuses a register still holding one, so the draft cannot become a seal by being copied.
  The bundle is **byte-deterministic**; regenerate it and diff the manifest to prove it.
  `out/handoff-architect/` is the OTHER bundle (`haus print --handoff`, drawings for an
  architect) and was renamed out of the way on 2026-09-11.
- **The bundle carries the analytical model four ways** (2026-09-12, decision #73): the IFC4
  structural analysis view inside `model.ifc` (SAP2000/ETABS/Bonsai), `analysis/centreline.dxf`
  (RISA), `analysis/members.csv` (ForteWEB/Sizer/Enercalc by hand) and `analysis/model.pynite.py`.
  Scope is the 36 items and their load path: 54 members, 56 nodes, 22 supports. **The ten
  lateral-system columns are FIXED and every other base is PINNED, a claim the engine makes
  and states** (`notes/analytical_model_basis.md`); the retaining set, the wall panel, the
  trussed roofs and the uplift path are named GAPS, not members. `tests/test_analytical_oracle.py`
  solves it in PyNite: the balcony pair carries what the records say to 0.03 %, but the frame
  hands the REAR column ~10 % more than the sheet's equal split, and the record's wind lever is
  the authored post height, 1 % longer than the built column. Both are findings, not errors.
- **The IFC in that bundle is enriched** and the one from `haus build` is not: section
  profiles on every member, `Pset_TH_Engineering_<kind>` carrying each record and its
  fingerprint, and a 102-row bar schedule under the pours, summing to the same 8,137 LF of
  cut length the BOM bills (laid out and counted as pieces since decision #75). See `docs/handoff-bundle-format.md`.
- **A published manufacturer table is a PRESCRIPTIVE read and stays out of the register**
  (2026-09-11). Three requirements left the engineered lane that way; **one of them came
  back on 2026-09-18.** Still prescriptive: `D-G-OVERHEAD`'s header (Weyerhaeuser TJ-9000,
  `notes/garage_door_header.md`) and `RF-HOUSE`'s I-joist rafters (TJ-4000,
  `notes/roof_rafter_span_read.md` — **§3 is settled now**, and the settlement is that the
  design does not turn on the disputed sentence). Each authors a `PublishedSpan` on the
  element; `checks/structural/published.py` turns the PASS back into UNKNOWN if the member,
  the spacing, the carried span, the load basis **or any of the conditions that used to be
  prose** drifts off the row — and, since 2026-09-18, if the row states a guard the check
  passes nothing for. That last one is not hypothetical: the header call omitted
  `demand_psf` entirely, so the load-basis guard never ran on it.
- **The three balcony glulams are an engineered item again** (2026-09-18) — `glulam_beam/
  BM-SG-BL{W,C,E}`, oracle `notes/balcony_moment_columns.md` §5. The Anthony/Canfor deck
  guide row that retired them is published **DRY-USE** and these beams stand in weather,
  which the row's own `condition` string said all along: the verdict was coming from a row
  that does not describe the member while the NDS wet-service pass — the only arithmetic
  modelling the real service condition — ran beside it as an advisory. `service_condition`
  is a typed guard now, the row is refused on it, and the record carries the verdict at d/c
  **0.59**, bearing (compression perpendicular) governing. One finding, not two: the
  refusal is said out loud inside the engineered finding rather than emitted as a second
  UNKNOWN, which would claim nobody knows about a question the engine has answered. **The 19'-3" rafter
  allowable this house quoted in five places was WRONG** — an interpolation to 35 psf that
  `snow.py`'s own rule forbids. The published row is **18'-4"**.
- **⚠ THE NORTH ENTRY CANOPY'S TWO CAST COLUMNS DO NOT HAVE THE BASE THEY ARE DESIGNED ON**
  (2026-09-18, and this is catlin's only open FAIL). `engineering/column_base.py` grades the
  IBC 1807.3.2.1 embedment a column free to translate at grade needs to turn its own shear
  around — the assumption every `deck_post` record had been NAMING and none grading since
  2026-09-11. `PT-BW-RE` wants 8.08' and has 6.12'; `PT-BW-RNE` wants the same and has
  3.50'. Both fail at BOTH ends of §1806.3.4's isolated-pole doubling, so it is not a
  judgement call. `notes/entry_column_base_fixity.md` works it by hand; §6 lists the three
  closures — deepen the shafts, constrain the base at grade with a grade beam or apron, or
  brace the frame and let the columns revert to leaning columns (the owner has already
  accepted knee braces as a fallback here). The two garage-side LANDING columns straddle
  §1806.3.4 and report INCOMPLETE naming the judgement, which is the band convention
  working. **`haus check` exits 1 and `haus print` refuses until this closes**; both the
  test allow-list and `scripts/verify.sh`'s carry the citation and go with the fix.
  - Two deferrals came with it and are scope rather than arithmetic: `base_rotation/*` (the
    base is graded for STRENGTH, not STIFFNESS — `deck_post`'s sway magnifier assumes a base
    that does not rotate) and `column_head_joint/*` (the `HGAM10` + `SS316-SHIM-35` head,
    whose moment transfer nobody has computed; column shear and torsion ride with it).
- **A fixed-base column's P-M check is a §2.3.1 ENVELOPE** (2026-09-18), each combination at
  its own axial load. A larger axial is not automatically conservative on an interaction
  curve — below the balance point compression RAISES moment capacity — so grading the wind
  moment at `1.2D + 1.6L`'s axial credited compression the governing case does not have. On
  `PT-BW-RE` combination 4 governs at 0.69 with combination 5 (`0.9D + 1.0W`) one point
  behind at 0.68 on barely half the axial. And the dowels' ANCHORAGE into the pad is graded
  beside the lap that already was: the lap alone was half the joint, and the half it left
  out is the one the fixed base depends on.
- **Seven items are deferred to a designer of record** — the TWO trussed roofs' rafters, all
  three roofs' uplift path, and the two wall tops under the balcony's fixed-base columns.
  `out/calcs/03-open-items.md` names who owns each.
  `RF-BW-CANOPY` joined on 2026-09-10 and its deferral carries a condition the others do not:
  **quote its trusses against the DRIFT case, not the ground snow.** A fabricator reading
  "50 psf ground snow" prices ordinary trusses, and the surcharge off the house gable also
  reaches 3'-10" into the garage roof, so ITS two southernmost trusses are drift trusses too.
  S-001 prints the number; `preferences.toml [structural] roof_beam_snow_psf` is where it lives.
- **The wall-panel question is closed too, as of 2026-09-11.** It was the one open
  engineering question: the concealed-fastener panel's withdrawal allowable over 24" open
  girts, which no manufacturer publishes. Naming the product settled the substrate on the
  maker's own words, and the allowable is now **computed** from NDS 2018 §12.2 — the
  rational design IAPMO UES ER-309 expressly authorises — rather than waited for. Twenty
  INCOMPLETE items became one OK group item (`notes/board_batten_girt_span.md` §6).
  **The other closed one:** the breezeway piers had no modelled plan area to shoelace, and
  `engineering/pier_basis.py::_roof_fields` now gives a roof-on-beams one. Their successors
  publish a real axial ratio against a real tributary (`notes/north_entry_piers.md` §6).

## The loop: edit → build → check → *look* → fix
```
haus build .            # -> out/model.json (+ IFC when ifcopenshell present)
haus check .            # integrity / code / structural findings
haus render --view plan # -> out/render/plan_*.png  — LOOK at what you made
haus render --view elevation   # -> out/render/elev_{n,s,e,w}.png — the facade rules' own eye
haus ls --summary       # compact whole-plan digest
```
After any spatial edit, **render and look**. After assembly edits,
`haus explain <ASM> --card`.
