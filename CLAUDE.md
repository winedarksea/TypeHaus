# Type:Haus — repo guide

```
.venv/bin/haus build houses/catlin        # the CLI. No PYTHONPATH, no uv.
.venv/bin/python -m pytest packages/engine/tests -q
scripts/verify.sh                         # standard gate, targets five minutes
scripts/verify.sh --full                  # exhaustive local/release gate
```

`scripts/verify.sh` runs in `.venv`, which has accumulated packages nobody declared, so it
is blind to a missing dependency. `scripts/ci_local.sh` is the one that catches those: it
builds a throwaway venv from the declared extras alone and runs the CI engine job's steps.
Run it before touching `pyproject.toml` dependencies or a CI step.

`.venv/bin/python` is 3.11.16 and `typehaus` is installed **editable** into it, so the
console script `.venv/bin/haus` is the real entry point. `uv` is **not** installed; ignore
any `uv sync` / `PYTHONPATH=packages/engine/src python -m typehaus.cli.app` incantation you
find in older docs. Pytest defaults are configured in the **root** `pyproject.toml`, the only
pytest config in the repo (`-n 6 --dist loadfile`) — bare `pytest` runs every test, including
the `slow` modules. `scripts/verify.sh` deselects those modules by default; use `--full` before
a release or for exhaustive local verification.

## Non-negotiables

- **Never hand-write a uid.** `.venv/bin/haus fmt houses/<name>` mints them. A colliding
  uid is now a load-time ERROR, but the cheap fix is to never author one.
- **`# haus: editable`.** A UI-movable element (walls, openings, placeables, fixtures,
  MEP, lighting) must live in a file whose first lines carry the `# haus: editable`
  marker, or UI edits are silently dropped on write-back. The editable dialect is a
  constrained declarative subset: no `frozenset`, no multi-line string concatenation, and
  a 1-tuple needs its trailing comma. `haus build --inspect` lints without importing.
- **Quantities are the product; dollars are opt-in** (`plans/01-decisions.md` #28). No
  price, wage, or productivity data ships in the engine — a house owns its own numbers in
  `houses/<name>/prices.toml`.
- **Files under 500 lines**, per `AGENTS.md`. And aim to keep comments concise and token-efficient. There is no need for long essays to explain a single point that a few quick words can summarize effectively.

## Layout

- `packages/engine/` — the `typehaus` package: `quantities` → `model` → `source` (load +
  dialect) → `resolve` → `checks` / `takeoff` / `emit` / `server` / `cli`.
- `packages/engine/src/typehaus/library/` — the shared, reviewed catalog of assemblies,
  materials, and types. Plans still spell it `from library import ...`; the loader aliases
  the name. Promoting a house-local item into it follows `CONTRIBUTING.md`.
- `houses/catlin/` — the reference house (see its own `CLAUDE.md`); `houses/starter/` — the
  `haus new` template.
- `ui/` — the React/three.js editor; `plans/` — the living design docs and decision log.

## Registries and geometry semantics

- **A solid category is a registry row** (`resolve/solid_category_table.py`, decision #80):
  trade, IFC class, elevation family, `is_pour`, `slab_family`, `supports_on_top` and
  `collision` all derive from it, and an unknown name raises. Add a row, not a table entry.
- **`LayerFunction` metadata is one table** (`model/layer_functions.py`): trade, billing,
  weather, fill/hatch fallback and glTF colour. A test requires a row for every enum member.
- **A material's look is authored on the `Material`** (`hatch`, `color`, `finish`). No engine
  or UI table may name a house-only tag, and a lint enforces it (decision #57).
- **Base and door casing are derived from one `TrimStandard`** (decision #85): records on
  `ResolvedModel.base_runs` / `door_casings`, drawn by `geometry_millwork`, billed by the LF in
  `interior_trim`. The base kind is the floor's `Material.base_detail`; the stock's
  `requires_custom_milling` decides whether it is milled or bought.
- **Device boxes are derived from one `BoxStandard`** (decision #93): `resolve/device_boxes.py`
  reads the host face (bare concrete/masonry → surface, framed cavity → flush, a box a raceway
  reaches → `flush_raceway`) into `ResolvedModel.device_boxes`; a surface box gets a derived
  3/4" EMT NM sleeve to the ceiling, and a `FloorHeat.thermostat_ref` its two ENT leads — both
  `derived` `ResolvedConduitRun`s. Graded by `electrical.box_fill`, billed in `[electrical_boxes]`.
  A `recessed_into_host_surface` device inside a blind `RoughOpening` takes a surface box on the
  recess plane (finish face + `normal_gap`), fed from the framing beside it, so no sleeve.
  Neighbouring flush devices on one face form a **gang bank** (`resolve/device_banks.py`): one
  N-gang box, snapped to `gang_pitch`, and a derived `wall_plate` from `BoxStandard.plates`; every
  box record is a bank (`device_tags`, `boxes_by_device`). A device symbol draws only its face
  proud of the plate (`footprint` = face width x projection); the body is `rear_projection`.
  A box solid carries a `body_mesh` (`resolve/device_box_mesh.py`: round, raised cover, mud ring)
  and its colour from `BoxRow.material_ref`.
  A ceiling fixture or hardwired alarm head that mounts to a box (not a housing/wafer, not
  PSU-fed) takes a `host="ceiling"` record (`resolve/ceiling_boxes.py`, decision #140; under a
  bare deck, a surface box on the member over its point): never banked or sleeved, graded by
  `electrical.ceiling_box_framing` (a clash moves the fixture) and `ceiling_box_support` (a
  fan's row is `fan_rated`). A `remote_box` type (a knuckle flood on
  its own plate) takes no box over its point: a surface junction box derives on the nearest
  framing member beside it, within a 6 ft whip and inside the deck outline
  (`resolve/remote_feed_box.py`).
- **Drywall accessories are derived from one `DrywallStandard`** (decision #103):
  `resolve/drywall_trims.py` finds outside corners, J-bead terminations, tile-stop reveals,
  trimless-door L-bead and window-return beads off the host faces into
  `ResolvedModel.drywall_trims`, billed by the LF in `[drywall_trims]`. Its `led_profile`
  (a `ShadowGapProfile`) puts a light run in a gypsum ceiling or soffit in a `shadow_gap`
  (`resolve/drywall_led.py`): each leg moved onto the reveal's centre off the washed gypsum
  face (`integrity.light_run_host`), the reveal cut from the board, `z_m` on the board face,
  the Z bead's depth graded by `mep.plaster_in_depth`. The run's swept section is served to
  the viewer, never copied there.
  A free wall end with gypsum on both faces takes a board, its coat and two corner beads
  (`resolve/wall_ends.py`, `ResolvedModel.wall_ends`), over the height nothing else occupies.
- **Paint is derived from one `PaintStandard`** (decision #113, `model/paint.py`): rooms take its
  `walls`/`ceilings`/`wet` system through `resolve/room_paint.py`, swapping default coats only;
  trim and doors bill in `takeoff/trim_paint.py`; `Material.paint` + `Product.equals` feed A-604.
- **Duct construction is derived from one `DuctStandard`** (decision #114, `model/ducts.py`):
  round gauge by pressure class, sealing, the bought elbow (its centre-to-face and C feed
  `mep.fitting_pattern` and `mep.erv_static_budget`), parts by (kind, size, branch), hangers and
  equipment `PortKit`s. The `duct_parts` stage (`resolve/duct_parts.py`) derives take-offs, tees,
  reducers, collar dampers, boots, port kits and hangers into `ResolvedModel.duct_parts` /
  `duct_supports`; elbows stay `mep_fittings` records keyed off the standard's angles (rect W×D).
  Billed in `[duct_parts]`/`[duct_supports]`/`[duct_sealing]`, printed on M-601.
  A deck `saddle` row's `sleeper` lets a duct standing ~that far off the deck bear on a block
  (`ResolvedDuctSupport.sleeper_m`, its own `[duct_supports]` row).
  An elbow's R is `DuctElbowRow.radius_m()` (centre-to-face, else `radius_diameters` × D); a
  rectangular turn is the standard's shop-made `rect_elbow` (r/W × the side in the turn's plane,
  `resolve/rect_elbows.py`), else a coverage gap (#124). An in-line damper is a station on its
  run (`DuctRun.inline_dampers`), charged its row's fully-open `loss_c` (#128).
- **A register's joint to its run is derived in 3D; a manifold needs a feed** (decisions #126,
  #136): `resolve/terminal_joints.py` (inlet/drop/through/end/side/unreached; boots and caps read
  it), `checks/mep/register_reach.py` FAILs a run passing THROUGH its grille or not reaching it, and
  `manifold_feed.py`. A run draws as stretches and elbows split at its parts
  (`resolve/duct_fabrication.py`); a boot's row matches its derived `entry`. A plain ceiling neck, round or rectangular, takes a drop from above and must match the arriving
  section (`resolve/terminal_drops.py`, #129). A passive shop box is `EquipmentKind.PLENUM`, one
  where an ERV feed joins a return `MIXING_BOX` (#125); a blocking `RunBand` is boxed by half-width and half-height.
- **NEC labels are derived, never authored** (decision #134): `resolve/electrical_labels.py` reads each
  label's trigger (PV, a source circuit, the service, an ESS, a heating cable, a remote EVSE breaker) into
  `ResolvedModel.electrical_labels`, wording from the paraphrase docs only. House inputs go on the one
  `LabelStandard`; an unauthored one is UNKNOWN in `electrical.label_inputs`. Billed in
  `[electrical_labels]`, printed on E-605.
- **LED construction is derived from one `LedStandard`** (decision #137, `model/led.py`): a
  strip type's `LedStrip` names its tape (width, feed limit, reel, rigid `modules`) and its
  `LedChannel`; `resolve/led_sections.py` builds every run's section (body, tape, lens, end caps;
  modules swept per piece) and emitters sweep it through `geometry.light_run_shells`.
  `resolve/led_leads.py` derives driver→controller and controller→feed leads
  (`ResolvedModel.led_leads`, functional route, gauge by drop, NEC Ch. 9 Table 8). Graded by
  `electrical.light_run_fit`, `led_gear_access` (concealed gear needs an opening in reach),
  `led_wiring` and `led_voltage_drop`; billed in `[light_run_materials]`. A driver is
  `DeviceKind.LED_DRIVER`, sized on `rated_output_w`, loading its branch at `input_va`.
- **Linesets are derived from one `LinesetStandard`** (decision #139): a lineset is a
  `PipeRun(system=REFRIGERANT)` (`diameter` vapour, `liquid_diameter` liquid, `serves` the head,
  `outdoor_port`), its envelope the lagged bundle; `resolve/linesets.py` reads it against the
  outdoor type's `RefrigerantLimits` into `ResolvedModel.linesets` (length, rise, cover LF, kit,
  field charge, port offsets). Graded by `mep.lineset_limits` / `mep.lineset_reach`, billed in
  `[linesets]` (drive allowances off `kit_length_ft`; no `[pipe_runs]` refrigerant price).
- **A cast-in STHD is graded as placed against ESR-2920 Table 1** (decision #141):
  `ResolvedModel.embedded_straps` records each one (`resolve/connector_geometry/embedded_straps.py`).
  Where the spoon cannot reach from the framing face, the strap is cast at the core face and jogged
  over the pour to the leaf; that jog is UNKNOWN (no published row; §4.2's cycle bends back plumb). `resolve/strap_holdowns.py` reads its concrete, and `resolve/rebar/strap_bars.py`
  lays the Figure 1 #4 bar. `structural.strap_hold_down_embedment` grades it; the table is
  `hardware/esr2920.py`. `Footing.cast_with_wall` lets l_e run into the footing.
- **Condensate overflow is authored on the unit** (decision #127): `Equipment.secondary_drain_pan`
  / `overflow_drain_ref` / `float_switch_ref`, graded by `mep.condensate_overflow` (IMC 307.2.3).
- **A hung machine's trapeze is derived from `Equipment.hangers`** (decision #131):
  `resolve/equipment_hangers.py` (struts under the short sides; each rod's bridge is cut between two
  joists' webs and bears on their bottom-flange tops, clear of the ceiling; host by
  `_MemberIndex.member_over`, drop derived), graded by `structural.equipment_hangers`
  against `Product.rated_load_lb` and `Library.joist_flange_allowances`, billed in `[equipment_hangers]`.
- **A pitched duct names its drains** (decision #132): `DuctRun.drains` derives a `drain_tee`
  (`resolve/duct_drains.py`, `[duct_parts]`); `mep.duct_drainage` grades only runs declaring
  `slope_in_per_ft` or `drains`. Don't pitch the leg off a port kit's lead: past 90° the straight
  lead becomes a bent flex (C 2.85).
- **A lidded chase is floor** (decision #130): `FloorOpening.lid` (needs a fireblock sheet) takes
  ledgers on its trimmer/header faces, cut round the runs (`resolve/opening_lid.py`, `ledger` in
  `[framing]`). The hole stays in `deck_voids`; walkable and finish readers use
  `ResolvedFloor.open_voids`.
- **A wall header is chosen from its host's role and derived load** (decision #116):
  `resolve/header_loads.py` walks `bearing_refs` and the walls above; a BEARING host takes the
  smallest IRC 2018 R602.7(1)/(2) row (`resolve/framing/header_tables.py`, note f's 0.70 where
  cripples bear) at or above `HeaderStandard.min_bearing_header`, with its NJ; a NONBEARING one
  up to 8' takes the R602.7.4 flat 2x within 24" of the plates. No row → the old ladder as a
  placeholder, `structural.header_span` UNKNOWN; `structural.wall_role_load` grades the roles.
- **A stair underside is derived from `Stair.underside_material`** (`resolve/stair_undersides.py`):
  `stair_soffit` boards under each flight's rake and landing, plumb returns and free-side faces,
  clipped at a ceiling over them, coated with the room's ceiling coat; `ResolvedStair.undersides`
  bills in `[sheet_goods]` "stair soffit", beads in `[drywall_trims]`, and is overhead for R311.7.2.
- **A pour slab stops at what it is cast against; a rim band has one wall** (decision #107):
  `resolve/slab_clip.py` cuts flush footings and through-walls out of the slab; read the slab
  as a floor through `floor_plan`. A wall dropping to a foundation owns its band outright.
- **A wall stands on the subfloor; its sills stay on the datum** (decision #110):
  `ResolvedWall.frame_base_z_m` (plates, studs, `resolve/plate_seat.py`) vs `base_ref_z_m`
  (every `sill_m`, backing band and girt course). Never measure framing off `base_ref_z_m`.
- **A tee branch frames to the through wall's framing** (`resolve/tee_interrupt.py`): its core
  passes the through wall's room-face layers, which a late stage cuts over its stud band
  into `<layer>-tee-<i>` pieces sharing one slot. Walk a stack by slot, not by entry.
- **A pour slab may fall** (`Slab.fall`, decision #138): `top_elevation` is its low edge; read a
  point with `ResolvedSolid.top_at`, never `z1_m`. `Stair.foot_on` seats a flight's foot on it.
  A wall finish whose foot lies in a falling pour rides its plane (`ResolvedLayer.bottom_plane`,
  `resolve/layer_seat.py`): `layer_solids` makes those pieces `GBox`es, the viewer reads the
  served plane, the takeoff bills the trapezoid. `mep_concrete.concrete_hosts` carries the plane.
- **`Slab.kind`** is `pour | deck | platform | band` (decision #81). Code that means concrete
  reads `is_pour_slab`, never `category == "slab"`.
- **A pour slab may fall; `top_elevation` is its low edge** (decision #138): `Slab.fall`
  (`SlabFall`) lifts top and bottom on one plane, so `z0_m`/`z1_m` are the low edge's.
  Anything that stands on the floor reads `ResolvedSolid.top_at(x, y)`; a falling pour draws
  from `resolve/slab_fall.sloped_slab_mesh`. `Stair.foot_on` seats a flight's foot on it.
- **`clear_face` is the finish face; `axis_face` owns points** (decision #82). Measure
  furniture and areas off `clear_face`. For "which room is this in", use
  `resolve/room_lookup.room_owning`.
- **A pitched cross-section is `FramedMember.section_ring`**: a ring in the run's
  (left-normal, up) frame that `member_solid` sweeps (the formed drip edge). The box fields
  only bound it; every emitter and the viewer read the sweep.
- **Wall mounts are hosted** (decision #83): a `WallAttachment` and no `position`. Read a
  placeable's plan point through `resolve/placeables.placed_xy`, never `.position`.
- **Equipment collides** (decision #84): only an authored relation pardons a contact.
- Ownership is by uid or geometry, never by tag prefix: `resolve/ownership.children_of`.
  Every `unary_union` goes through `resolve/overlay.py`.

## Commands worth knowing

```
.venv/bin/haus doctor                     # environment sanity: venv, install, ui/dist, gitignore
.venv/bin/haus check houses/catlin        # failures only; --only all restores every finding
.venv/bin/haus check houses/catlin --no-suppress   # lift [checks] suppress: the open-campaign score
.venv/bin/haus fmt houses/catlin          # mints uids, formats plan source
.venv/bin/haus serve houses/catlin        # editor; does NOT reload engine code — restart it
.venv/bin/haus takeoff houses/catlin      # BOM (+ costs when prices.toml exists)
.venv/bin/haus render houses/catlin --view plan --fmt png|svg|psd   # docs/review-exports.md
.venv/bin/haus render houses/catlin --view section --slice SL-S-FIRE  # a house-AUTHORED cut
.venv/bin/haus takeoff houses/catlin --csv out/estimate.csv   # estimating-software intake
.venv/bin/haus tasks houses/catlin --csv out/tasks.csv        # work packages for a PM tool
.venv/bin/haus millwork houses/catlin                         # hardwood cut list for the mill
.venv/bin/haus millwork houses/catlin --md out/milling.md --csv out/milling.csv
.venv/bin/haus countertops houses/catlin                      # slab-yard package: DXF per piece, PDF, piece list
.venv/bin/haus print3d houses/catlin --timing             # A1-ready 3MF: storeys on a plate + furniture (docs/print3d.md)
.venv/bin/haus bids houses/catlin --all --out out/bids       # unpriced per-crew RFQs + summary schedules (docs/bid-package-format.md)
.venv/bin/haus order houses/catlin --brand IKEA --md out/ikea.md   # one retailer's shopping list, in packs (docs/order-list-format.md)
.venv/bin/haus costs import out/estimate.csv --house houses/catlin   # actuals back in
scripts/verify.sh                        # standard tests, house checks, ruff, UI typecheck/tests
scripts/verify.sh --full                 # all tests, checks, builds, benchmark, Pyodide smoke, UI build
scripts/ci_local.sh                       # the CI engine job in a THROWAWAY venv, declared deps only
```

`--view section` draws the derived house-centre cut; **`--slice <TAG>` (or `--slice all`)
reaches a section the HOUSE authored**, and both come out annotated through the one
`build_annotated_section` that `haus print`'s A-301 series uses — datums, ground line, room
names, with the room names and detail callouts clipped to the slice's own crop. A DETAIL is
not reachable that way: it is its own view, cut with a joint plan and its own paper.

All three `haus render` formats share one **review-layer stack** (`emit/draw/review_layers.py`,
`docs/review-exports.md`): the SVG groups by it, the PSD is one raster layer per entry (for
markup in Procreate — open it from the **Gallery**, inserting flattens it), and the PNG is the
same picture flattened. Rasters size by `--long-edge` (default 4096) **or** `--dpi`, never both.
`haus print` is deliberately outside all of this — the review stack re-orders, and the submittal
deliverable does not get restacked as a side effect.

`haus check` exits 1 on any FAIL, not only on an ERROR — `--exit-on error` is the older,
looser gate, and `scripts/verify.sh` does **not** use it on catlin: the reference house is
held to a clean report, 0 FAIL. See `houses/starter/CLAUDE.md` for the one house that
*does* carry deliberate reds, and why a template is the right place for them.

## Engineering, and the two gates

Some requirements fall outside the prescriptive tables — a 10' cantilever retaining wall, a
round column with no IRC R507.4 row, a trussed roof. Those are not UNKNOWNs. A finding
carries an `Authority` (PRESCRIPTIVE or ENGINEERED) *orthogonal to* its `Result`, and names
an item id `<kind>/<element-tag>` that a professional seal can cover (decision #65).

```
.venv/bin/haus engineering houses/catlin                  # what needs a seal, and what governs
.venv/bin/haus engineering houses/catlin --item retaining_wall/W-SG-E2   # term by term
.venv/bin/haus engineering houses/catlin --fingerprint retaining_wall/W-SG-E2
.venv/bin/haus calcs houses/catlin                        # the calc package a PE marks up
.venv/bin/haus handoff houses/catlin --zip                # the whole bundle a PE gets
.venv/bin/haus print houses/catlin --sealed               # the submittal gate
.venv/bin/haus analysis houses/catlin                     # the engineered frame: IFC SAM, RISA DXF, CSV, PyNite script
.venv/bin/haus analysis houses/catlin --solve             # solve it in PyNite; reactions beside the records' demands
```

- `typehaus/engineering/` is a **leaf package**: it imports `model`/`resolve`/`quantities`/
  `wind` and **never `checks`**. Its output is an `EngineeringRecord` (demand, capacity,
  ratio, governing limit state, citation), not a `Finding` — `Finding` has nowhere to hold
  numbers. `checks/_authoring.engineered()` is the one bridge between them.
- **A published manufacturer table is a prescriptive read, not engineering.** A reviewer
  opens the document, finds the row, and the question is closed — nothing a seal adds to.
  Author a `PublishedSpan` on the element (source, the row in its own words, the member, the
  span, and the conditions the row assumes) and grade it with
  `checks/structural/published.py`, which refuses the row when the model drifts away from
  what it was read at. PBR cladding is the precedent: it stays out of the register on the
  strength of three published wall span tables. `engineered()` is for what no table
  publishes.
- **Every calculation is oracled against an independently hand-worked note** in
  `houses/<name>/notes/`, the way `typehaus/wind.py` is oracled against
  `catlin_truss_engineering.md`. A calc that only agrees with itself is not verified.
- **The analytical model is one graph, four readers** (decision #73). `typehaus/analytical/` is a leaf
  like `engineering/`; it builds the engineered items *and their load path* as nodes, members,
  supports and load cases, and the IFC4 structural analysis view (SAP2000/ETABS/Bonsai), the
  centreline DXF (RISA), `members.csv` and the PyNite script all read it. Fixity and releases are
  **derived and claimed**, each with a `basis`; the underivable goes in `gaps`. Loads are the ones
  the records consumed. PyNite (`dev`/`fea` extra) is the oracle: `tests/test_analytical_oracle.py`
  solves the exported graph against `notes/analytical_model_basis.md`.
- **draft** = this engine computed it and it checks out; `haus print` gates here, because
  draft approval is exactly what a permit-ready printoff is for. **sealed** = a licensed PE
  stamped it *and* the pinned fingerprint still matches the model. `haus print --sealed` is
  the second gate and it really does refuse.
- `haus calcs` writes `out/calcs/` — cover, derived design criteria, item register, gap
  register, collapsed assumptions, one calculation per design FAMILY, and an appendix:
  `appendix/<kind>.md` (the per-member data as a table) over one nine-section sheet per
  item. **The PDF prints the calculations, not the appendix** — `--appendix` (or
  `haus handoff --full`) prints it, and the divider page always says where it is.
  Byte-deterministic and regenerated rather than maintained
  (`docs/calc-package-format.md`). Each kind declares its oracle note with
  `oracled_by(KIND, Oracle(...))`, and a test lints that every kind names one that exists.
- **`haus handoff` is the whole handover in one command**: `out/handoff/` carries the calc
  package, its PDF, only the notes those records cite, the models, a manifest of sha256s and
  `engineering.toml.draft` — the seal register as a FORM, fingerprints filled in and every
  human field a visible `<<blank>>`. The loader **refuses** a register still holding one, so
  the engine can scaffold without ever writing a seal. The bundle is byte-deterministic, or
  the manifest would prove nothing (`docs/handoff-bundle-format.md`).
- The seal lives in `houses/<name>/engineering.toml` (`docs/engineering-toml-format.md`),
  never on the elements: those are `# haus: editable` and undoable, and a stamp in plan
  source would be read back by the very records it is a statement about. **The engine reads
  that file and never writes it.** (It is *not* true that `_content_hash` pins a seal — a
  seal pins `engineering/fingerprint.fingerprint(record)`, which hashes the record's inputs
  and ratio and never the model's bytes. `_content_hash` reaches printed prose and the UI's
  concurrency revision only. What stales a seal is moving geometry or elevations.)
- `Result.NOT_APPLICABLE` is a fourth verdict — "the condition this rule governs does not
  exist in this building" — and must be **earned** from positive evidence of absence. "No
  masonry guard anywhere in the plan" is N/A. "No dryer modeled" in a house with a laundry
  is a real gap, and stays UNKNOWN.

## Costs and schedule

Dollars are opt-in and live in the house: `houses/<name>/prices.toml` (unit prices, plus
`[basis]` / `[waste]` / `[contingency]` / `[markup]` / `[tax]`), `costs.toml` (what was
actually paid), `tasks.toml` (work-package status). The engine ships no price data, ever.

- `cli/price_file.py` owns the file format; `cli/prices.py` owns the join to the BOM.
- `takeoff/cost_model.py` is the `net -> waste -> ordered -> contingency -> markup -> tax`
  ladder. A `merged` (installed, split unknown) subtotal is never divided.
- **A trade is the smallest scope some house bids alone; a crew is the house's grouping**
  (decision #115): `[crews]` in `tasks.toml` joins trades for one sub or marks them
  `self_performed`, and `haus bids` writes one package per crew. Trades file by fact in
  `takeoff/cost_facts.py`; never add a trade to fit one house — add a crew.
- `takeoff/tasks.py` derives work packages at (trade x storey), ordered by
  `emit/trades.CONSTRUCTION_SEQUENCE`. Task ids are stable GlobalIds, so re-exporting
  updates rather than duplicates. No durations, crew sizes or dates — the model cannot know
  them.
- **The room owns its paint** (`resolve/room_paint.py`, decision #104): `Room.paint` swaps an
  authored coat and is the coat added to bare gypsum facing a used room; `Room.unpainted`
  strips coatings from its faces and ceiling. An envelope wall's room-face paint (its Class III
  retarder) always stays. Paint is resolved, so model and bill agree: walls bill off their
  layers, ceilings off `model.ceilings` (`takeoff/coating_areas.py`).
- **A coating takes no depth** (`resolve/coatings.py`): `ResolvedLayer.thickness_m` is 0 and
  its ring is zero-width on its host face; emitters draw it as a skin or a stroke, never a solid.

## Building it: visits and inspections

```
haus schedule houses/catlin                       # the build board: what is ready, what blocks it
haus schedule houses/catlin --milestone weathertight
haus schedule houses/catlin --propose task/concrete/building   # a visit split to paste
haus inspections houses/catlin                    # every inspection, and what stands before each
haus site validate houses/catlin                  # load + graph + rules; exits 1 on any error
haus site migrate houses/catlin --write           # fold the old spellings, in place
```

- **Readiness is derived; dates come only from authored inputs** (decision #69, loosened).
  `typehaus/schedule/` is a leaf like `routing/` and `engineering/`. It derives a suggested
  date from the house's own `[calendar]`, `duration_days`, `cure_days` and `lead_days`, and
  says **"needs confirmation"** where any of those is absent — never a default. **A booking
  is never moved**: a predecessor that slips past one marks it *threatened* with the slack.
- A **visit** (one sub, one arrival) is the schedulable unit, authored in `tasks.toml`'s
  `[visits]`; a package nobody splits is one implicit visit. `--propose` prints, never writes.
- **`gates` is a default for implicit visits only.** A gate names a trade and a trade is not
  schedulable: applied to every arrival it made excavation wait on the backfill inspection,
  which waits on the walls, which wait on the footings, which wait on excavation. Two gates
  on one trade, one after the other, and the later is dropped — `haus site validate` prints
  every drop. **Cycles are found and named**, never silently dropped.
- **Checkpoints** are ordered pauses inside one arrival (forms / pour / strip). A visit's
  status derives from them, so `status =` on a checkpointed visit is a validation error.
  A dependency may target `visit#checkpoint`. `blocks_successors = false` takes a late
  arrival (flatwork, final grading, the punch list) out of package-level expansion.
- **An inspection has attempts and instances.** A result is an appended `attempt`, never an
  overwritten slot; a `partial` releases only the scope it `approved`;
  `[entries."footing/court"]` is a second instance with its own scope and booking. A waiver
  is a table naming who granted it, because it outranks the model's own evidence.
- **One write path**: `schedule/site_ops.py`. Both `PUT`s, the CLI and a future in-UI agent
  fold through the same ops and the same rules; writes are temp-file + `os.replace`; a stale
  `if_revision` is a 409 with the fresh payload, never a merge.
- The AHJ's own record lives in `houses/<name>/inspections.toml`
  (`docs/site-state-format.md`), outside the undo journal like `costs.toml` — and the engine
  ships no phone numbers: `[authorities]` is house-owned.
- **FAIL blocks a visit, UNKNOWN is attention only.** An inspection is stricter and matches
  the permit gate: its checks must fold to PASS/N/A. `verified` is the owner's own walk and
  needs every hold cleared, every handoff item ticked or **skipped with a reason**, and every
  inspection the visit depends on resolved — and one request may not both clear the last hold
  and verify. `done` under an open hold records an **exception**; the hold stays open.
- In the UI the site pages are a **second top-level surface** (`#/site/board`), not a reader:
  no canvas, no 3D, nothing of the design workbench is mounted.

## Routing: proposals and independent checks

Read [docs/routing.md](docs/routing.md) for commands, diagnostic interpretation,
acceptance, module responsibilities, tests, and oracle notes. Start with:

```bash
.venv/bin/haus route houses/catlin --run PR-B-KITCH-DRAIN \
    --json --summary --out out/route/kitchen
```

The compact report preserves actionable diagnostics; full geometry/source is saved for
selective reading. Routing stays separate from checks. Accepting a route requires an
explicit edit to its authored plan and design explanation. Pipe/duct elevations are
storey-relative; conduit elevations are absolute. `--out` never applies a route.
After editing `typehaus/routing/`, run
`pytest packages/engine/tests/test_routing_campaign_cli.py --autorouter` (opt-in, skipped otherwise).

`haus serve` watches `houses/<name>/` only. After editing anything under
`packages/engine/`, **restart the server** or the viewer shows stale geometry.

see also AGENTS.md
