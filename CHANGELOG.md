# Changelog

All notable changes to `typehaus`. This project follows [semantic versioning](https://semver.org).

## Unreleased

- **Manual-J-shaped cooling: the glass is walked hour by hour, and the peak is ONE hour.**
  The sequel the block-load pass promised. New `checks/building_science/solar.py`, oracled by
  the new `houses/catlin/notes/solar_gain_basis.md` and reproduced by
  `tests/test_energy_solar.py`. What the term was:
  `area × shgc × ORIENTATION_WEIGHT[facade] × 164.0`, weights `{N 0.25, E 0.70, S 1.00,
  W 0.85}` — and it was wrong twice over.
  - **The weights put south at the peak.** At 45 °N in July the clear-sky total on a vertical
    surface at each orientation's own peak is N 54 / **E 230** / S 161 / **W 230** Btu/h·ft²:
    south is 0.70 of the peak and east and west *are* it. (The noon sun is 66° up, so a south
    window sees it 66° off normal and most of the beam slides past the glass.)
  - **But the weights were not the expensive error.** Summed, they came within 4% of the
    sum-of-own-peaks — they were wrong in a way that cancelled across four facades. The
    expensive error was charging the east glass its 8 a.m. peak and the west glass its 4 p.m.
    peak **in the same hour**, an hour that does not exist. catlin's real house-wide peak is
    **12,271 Btu/h at solar 10:30** against the 17,435 reported: a **1.42× overstatement**,
    essentially all of it hour-coincidence. This is why the block-load pass declined to fix
    the weights alone: it would have changed almost nothing while looking like a fix.
  - **Shading, from whatever is actually overhead.** `RF-HOUSE` projects *nothing* past
    catlin's main-floor south wall, so an eave-only model finds no shading on `D-M-BALC` —
    33 sf of glazed door and the largest piece of south glass in the house. What shades it is
    a **floor**: the sunken-garden balcony deck, 2 3/4" clear of the wall face, reaching 9.9 ft
    out, a metre above the door head. So any horizontal plane overhead counts (a roof
    footprint, a slab outline, a floor deck) and a plane shades a **band** — its near edge
    sets the top of the shadow and its far edge the bottom, of which an eave is the
    degenerate `near = 0` case. Bands union rather than sum (two decks over one door), only
    the DIRECT beam is shaded (45.6 of the 144.2 Btu/h·ft² on a fully shaded door still
    reaches it), and the test is lateral too: the window 10 ft east of that door is *not*
    shaded, because the balcony stops short of it.
  - **The AED excursion** (ACCA TRB 2003-001a): `peak − 1.3 × average`, added when positive.
    catlin pays **894 Btu/h, 7%** — it has good exposure diversity, and the term is written
    down precisely because it is small here and would be 30% on a glass wall facing one way.
  - **Internal gains, cooling only.** Manual J credits none against heating and neither does
    this — a design heating hour is 4 a.m. in January with the house asleep. Occupants =
    bedrooms + 1 (Manual J's own rule, and a fact the model already carries), 230 Btu/h
    sensible + 200 latent each, plus the low end of the published 1,200–2,400 kitchen
    appliance allowance. A model with **no conditioned room at all** gets no occupants,
    which is a different answer from "no bedroom".
  - **A latent load and an SHR**, and both honestly incomplete. Occupant latent only: an
    air-side latent load needs the cooling design outdoor **humidity ratio** and nothing on
    `Site` carries one (`monthly_normals`' RH is a monthly mean, not a design coincident wet
    bulb), and the ERV's **latent** recovery is unstated. So SHR 0.94 is an upper bound and
    the sizing checks say so. **`cooling_tons` is now a TOTAL** (sensible + latent over
    12,000) — a ton of refrigeration is a total, not a sensible.
  - **`EnergyReport.cooling_caveats`, a second list beside `unknown_inputs`.** An *unknown*
    is an input the model does not have; a *caveat* is a term the method knowingly does not
    carry. A reader who cannot tell them apart cannot tell a gap they could close from one
    they cannot — and an omitted term must not take an equipment-sizing verdict to UNKNOWN.
    `mep.cooling_capacity` prints them and calls its ratio an upper bound.
  - **The roof's sol-air term is built and OPEN.** A roof is solar-dominated and nearly
    ΔT-independent: at catlin's peak hour a black roof behaves as though it faced 144 °F, a
    69 °F CTD against the wall's 15. New `Material.solar_absorptance` (a published optical
    property — `color` is an sRGB triple and says nothing about the near-infrared). Nobody has
    stated one for this roof's cladding, so the roof carries the plain air ΔT and the omission
    is a **caveat, not an `unknown_input`**; the note's §6 prices the three candidate colours
    at +329 / +881 / +1,572 Btu/h and asks for one number.
  - `Preferences.cooling_solar_gain_btu_per_hour_ft2` is **deleted**: one peak irradiance for
    all four orientations at once has nothing left to say. No house authored it.

- **The block load's total was right and every one of its parts was wrong.** A review found
  `checks/building_science/energy_load.py` arithmetically correct and physically wrong in six
  places, in both directions, by 0.5–2.0 kBtu/h each — and catlin's heating figure moved 17
  Btu/h when all six were fixed, because they cancelled. **Nothing pinned any of it**:
  `houses/catlin/out/` is gitignored and every energy assertion in the suite was relational,
  so the scope could have drifted 20% either way and stayed green. New
  `tests/test_energy_envelope_scope.py` and `tests/test_energy_ground.py` are the coverage
  that would have caught it, hand-worked in the new `houses/catlin/notes/block_load_basis.md`.
  What moved:
  - **Envelope scope is derived, not read off one house's tag prefixes.** Both the block load
    and the MN prescriptive table carried their own tuple of catlin names (`"W-SG-"`,
    `"W-B-BRICK"`, `"SL-G-"`, …), so renaming a wall changed the answer and any other house's
    porch was graded against R-21. New `checks/building_science/envelope_geometry.py` derives
    it as three composed tests — bounds a conditioned room's face (measured from the wall
    BODY, not `axis ± thickness/2`), carries a weather skin or is cast as foundation, and is
    not interior on both faces — plus a prism table that answers the vertical half. The naive
    single test ("conditioned on exactly one side") was measured and rejected: it moved 25
    catlin walls, 12 right and 13 wrong. The derived rule moves exactly the audit's 12 and
    **zero walls in `houses/starter`**. It also finally drops `SL-M-DECK` and `SL-M-TUBDK`
    (interior floors, conditioned above AND below) and the two 7-sf equipment pads from the
    load, and reads a garage floor as a **buffer** — a third answer, so the next house with an
    attached garage gets a named gap instead of a silent ~40% overstatement.
  - **Below grade: Latta depth-resistance and a derived ground design temperature.** Two
    errors were fighting and the ΔT one won. New `checks/building_science/ground.py`:
    `U(z) = 1/(R + πz/2k)` integrated over the buried depth (catlin's R-21.8 wall buried
    6.12 ft is R_eff **27.4**), the ASHRAE below-grade floor relation (R-11.1 of assembly is
    R-**50.9** in the ground — the soil is four fifths of it, and `A/R` overstated that floor
    2×), and the two published ASHRAE 90.1 slab F-factors, because a slab on grade loses heat
    around its **perimeter** against outdoor **air** and reading it as an area against soil is
    ~10× low. **The ground design temperature is now derived**: `Site.soil_temp_f` is the
    ANNUAL MEAN and the design hour sits at the bottom of the surface's annual swing, so it is
    `annual_mean − amplitude` — the mean off `Site.monthly_normals` (46.86 °F, which
    reproduces this house's hand-computed 47.0 as a free self-check) and the amplitude one new
    authored field, `Site.ground_surface_amplitude_f`, off one published map. **ΔT 45 °F, not
    23.**
  - **Walls split at their LOCAL grade, not the `Site.grade` plane.** The global plane buried
    1.73 m of catlin's open-air walkout wall in soil ΔT, a 3.7× understatement on the very
    walls the scope fix had just added. `resolve/site_earth.py` gains
    `strip_grade_elevation_m`, which sweeps an 18" strip off the wall's own exterior face:
    the existing `local_grade_elevation_m` measures RADIALLY, which is right for frost and
    cannot separate a wall collinear with the excavation from one facing it (0.148 m against
    0.100 m). The strip separates them ~25×. The split emits **three** wall components —
    `walls`, `foundation_walls`, and a new `foundation_walls_above_grade` (253 sf of catlin's
    walkout, cast concrete in open air at the full air ΔT).
  - **A raked gable wall is a trapezoid, not a prism.** `length × (z1_m − z0_m)` ignored
    `top_z0_m`/`top_z1_m`, and `z1_m` on a `ToRoof` wall is the RIDGE: 657.6 sf billed against
    414.0 sf real over catlin's attic gables, ≈470 Btu/h of invented heating.
  - **A cooling setpoint of its own.** One `interior_setpoint_f` served both seasons, so the
    cooling ΔT was 20 °F where Manual J's is 15. New `Preferences.cooling_setpoint_f = 75.0`.
  - **The air side: three missing multipliers.** `N` is the LBL table `base × height ×
    shielding`, not the flat 18.0 that was its two-storey/normal cell (catlin derives 17.76,
    with shielding read off the `Site.wind_exposure` the house already authors for wind).
    Sherman's N yields an ANNUAL AVERAGE, so a heating design hour takes 1.5× it and a cooling
    one 0.84×. And 1.08 Btu/h·cfm·°F is a SEA-LEVEL figure — 0.97 at catlin's 830 ft.
  - **Solar was deliberately left wrong** in this pass and is corrected in the next. The
    weights `{N 0.25, E 0.70, S 1.00, W 0.85}` put south at the peak where at 45 °N in July
    it is 0.70 of it, but the term is four fifths of the cooling load and a partial fix moves
    the number the WRONG way.
  - `Preferences.wall_r` / `.roof_r` are **deleted**: read by nothing, in three houses'
    `[envelope]` tables. `preferences.toml` still has no schema and no unknown-key rejection —
    the gap that let those two sit there unread, and that has bitten three times now.

- **The plan stair symbol is a stair symbol now, and A-1xx draws its floor openings.** Two
  reported defects with one root cause each. (1) *"Part of the attic is open to the stairs
  below; it should say that in the printed plan."* The architectural plan never read
  `FloorSystem.openings` at all — the framing plan was the only sheet that drew a floor
  opening — so a hole in a deck and a deck looked identical from above, and `views.py`
  answered the question with a whole SECTION because the plan could not. New
  `emit/draw/plan_voids.py` draws every opening's true authored ring on the new
  `A-FLOR-OPEN` layer and captions it: `OPEN TO STAIR BELOW` where a flight is visible
  through it (derived from the stairs' own footprints, nothing authored), `OPEN TO BELOW`,
  `CHASE — OPEN TO BELOW` or `ACCESS HATCH` otherwise. (2) *"The printed plans draw the
  stair lines wrong."* The treads were always right — they are the same resolved members
  glTF and IFC extrude. Everything around them was not: **both flights of a U-stair were
  drawn in full, superimposed, in the same well**, which is the whole of "two tread widths",
  "an extra one on the right" and "two stairs north of the landing". New
  `emit/draw/stair_symbol.py` + `stair_travel.py` (moved out of a 542-line `floorplan.py`)
  cut a departing flight at a **4'-0" plan cut plane** — one predicate, no storey branch —
  **break** it there with two skewed diagonals placed where the walk line crosses the cut,
  and **occlude** the arriving flight surface by surface on the point its line marks rather
  than on a fraction of its area. The floor-opening bounding-box centreline that served as a
  direction line, and which on a U landed exactly on the well partition *between* the lanes,
  is replaced by a **travel line that follows the walk** — station midpoints in climb order,
  clipped at the break, with an arrowhead and a start tick as plain IR geometry. A **segment
  ledger** enforces one line per riser face with exactly one owner, so a landing edge or a
  well ring is never drawn twice; a stair with no floor opening draws its own footprint ring
  instead. `A-FLOR-OPEN` is styled in both writers and grouped under the shell in the review
  stack.
- **`resolve/stairs/u_split.py`: each flight is anchored to the storey edge it MEETS.** Found
  while measuring the above, and the more serious of the two. The upper flight was laid out
  backwards from the *lower* flight's line, which is the same line only while the two carry
  the same number of treads. On an odd tread split it stopped one going short: ST-M2S's head
  stood 10" out into `FO-S-STAIR` — **a 10" x 3'-6 3/8" strip of open floor opening at the
  top of the stair**. `code.R311_7_5_1_stair_end_risers` passed it, because it compares
  elevations and never plan position. The slack now falls in the landing zone, where the
  upper half-landing takes one going of extra depth (the two stay flush at the far end of the
  well, so the opening budget is unchanged); the well partition stops at the shorter flight,
  or its studs run through the upper landing's deck. Hand-worked in
  `houses/catlin/notes/u_stair_split_landing.md`, which is the oracle this arithmetic never
  had — part of why it went unseen. New `stair_walk_stations` in `resolve/stairs/walkline.py`
  chains the per-flight stations into one route, orienting each flat landing toward where the
  previous line left off; `flight_walklines` is untouched, so the R311.7 checks and the
  railing rake are unaffected.
- **New check `code.R311_7_6_stair_arrival_floor`** — is there a floor, or the hole it is cut
  in, where the top nosing puts a foot down? Both R311.7.5.1 rules read the arrival deck
  through the well itself, so a flight ending over the opening arrives at exactly the right
  *elevation* and passes; this one steps half a going off the top nosing and asks what is
  there. It reports UNKNOWN where nothing is modelled at all and NOT_APPLICABLE for a stair
  that perforates no deck. **It immediately found the same defect authored in the reference
  house**: `FO-A-STAIR` ran 15 3/8" west of anywhere ST-S2A reaches, so catlin's attic well
  had a 15 3/8" x 3'-0" hole at the head of the stair. Both that and the resolver defect are
  fixed.

## 0.1.1 — 2026-09-13

**The first working publish.** 0.1.0 was tagged but never reached PyPI: its CI could not go
green, because `mypy --strict` was a gate on the engine job and reports 2781 errors. The tag
stands as history; 0.1.1 is the version that ships. Everything below under 0.1.0 is part of
this release.

The four days between the tag and the upload were not spent waiting on CI, so this release
also carries the work below — a build surface (`haus schedule` / `inspections` / `site`), the
PE handover (`haus handoff`), the analytical export (`haus analysis`), per-trade bid packages,
nineteen new checks and one renamed one. **Two changes need action from a 0.1.0 user**: the
trade vocabulary rename, and the retired `code.R406_1_dampproofing` id.

- **`haus schedule`, `haus inspections` and `haus site` make the build a first-class
  surface.** The engine already knew what the house was made of and nothing knew what order
  it gets built in. `typehaus/schedule/` is a leaf like `engineering/` and `routing/`: it
  derives *readiness* — what is ready to start and exactly what is in the way — while every
  date comes from an authored input (`[calendar]`, `duration_days`, `cure_days`,
  `lead_days`) and anything absent reads **"needs confirmation"** rather than taking a
  default. The schedulable unit is a **visit** (one sub, one arrival), authored in
  `tasks.toml`; **checkpoints** are ordered pauses inside one arrival, so a footing visit is
  forms / pour / strip rather than three mobilisations. A booking is never moved — a
  predecessor that slips past one marks it *threatened* with the slack. The AHJ's own record
  lives in `houses/<name>/inspections.toml` (`docs/site-state-format.md`), an inspection
  result is an appended `attempt` rather than an overwritten slot, a `partial` releases only
  the scope it approved, and a waiver is a table naming who granted it because it outranks
  the model's own evidence. `haus site validate` exits 1 on any error; `haus schedule
  --propose` prints a visit split to paste and writes nothing. `schedule/site_ops.py` is the
  one write path both `PUT`s and the CLI fold through: temp-file plus `os.replace`, and a
  stale `if_revision` is a 409 carrying the fresh payload, never a merge. In the UI the site
  pages are a second top-level surface at `#/site/board` — no canvas, no 3D.
- **One trade vocabulary replaces the 13-name visibility list, and it is a breaking
  rename.** 21 trades in 11 groups are now shared by the viewer toggles, the BOM and the
  schedule, so a beam cap cannot be roofing in one place and siding in another. `walls`,
  `floors` and `roof` are **retired**: `roof` becomes `roofing`, and the old `walls` /
  `floors` buckets split across `framing`, `siding`, `drywall`, `insulation` and the rest.
  An element now carries a *set* of trades (`ElementGeometry.trades`, glTF extras,
  `model.json`) and draws if any of them is visible. A house with authored site files must
  run **`haus site migrate --write`**, which folds the textual renames in place and lists
  the one-to-many cases it cannot decide; a saved viewer visibility recipe is migrated in
  the UI. A visit naming rows outside its own package is now a validation error rather than
  a silent miss.
- **`haus bids` writes unpriced per-trade bid packages.** A sub is asked to quote scope, not
  to read someone's cost model, so the packages carry quantities and no dollars
  (`docs/bid-package-format.md`). Alongside it `takeoff/labels.py` gives every estimate row
  a readable label with the id kept beside it — id-shaped descriptions went from 354 to 8,
  ratcheted by a test — and `takeoff/bom_walk.py` is now the single BOM walk the estimate,
  the tasks and the bid packages all read.
- **`haus handoff` assembles the whole engineering handover in one command.** Handing the
  engineering to a PE meant running `haus calcs`, running `haus build`, working out which
  notes were cited, pulling forty fingerprints one at a time and writing the covering page
  by hand, which nobody did twice the same way. `out/handoff/` now carries the calc package
  and its PDF, only the notes those records are actually checked against, the models, a
  README that routes a reviewer through it in five minutes, a `MANIFEST.json` of sha256s,
  and `engineering.toml.draft` — the seal register as a **form**, fingerprints filled in and
  every human field a visible `<<placeholder>>`. The rule is kept by the loader rather than
  by restraint: `register.py` now **refuses** a register still holding a placeholder, naming
  the field, so the engine can scaffold the tedious half without ever writing a seal. A
  manifest is only worth having if the bundle is byte-deterministic and it was not, so four
  emitter fixes land with it: the calc PDF's `CreationDate` / `ModDate` and the IFC's STEP
  timestamp are pinned, every GUID ifcopenshell mints for us is rewritten as a uuid5 of what
  it identifies, and the member lists it collects through `set()` are sorted. Two runs now
  produce identical bytes, so a changed hash is a changed model. The IFC inside that bundle
  is enriched where `haus build`'s deliberately is not — section profiles shared per
  section, `Pset_TH_Engineering_<kind>` on every element a record names, and a bar schedule
  under the pours it belongs to — and `docs/handoff-bundle-format.md` describes it.
- **`haus analysis` exports the analytical model, and `--solve` checks it.** The engineered
  items and their load path are now one graph of nodes, members, supports and load cases,
  read by four consumers: the IFC4 structural analysis view for SAP2000/ETABS/Bonsai, a
  centreline DXF for RISA, `members.csv`, and a runnable PyNite script. Fixity and releases
  are **derived and claimed**, each with a `basis` string, and what cannot be derived goes
  in an explicit `gaps` list rather than being guessed; the loads are the ones the
  engineering records actually consumed. PyNite is the oracle rather than a feature —
  `tests/test_analytical_oracle.py` solves the exported graph against a hand-worked note —
  and it ships as a new **`fea` extra** (`pip install 'typehaus[fea]'`) for an install that
  wants `--solve` without the whole dev toolchain.
- **A published manufacturer table is now a prescriptive read, not engineering.** Three
  requirements sat in the engineering register on one shared piece of reasoning — the IRC's
  table stops, so an engineer owns it — and the hole in that is that the IRC is not the only
  body that publishes a table. `PublishedSpan` puts the read in the model: source, the row
  in the table's own words, the member, the span, and the conditions the row assumes that
  this engine does not check. Four of its fields are drift guards, and
  `checks/structural/published.py` returns UNKNOWN naming the mismatch — rather than a PASS
  off a quotation that has stopped describing the building — as soon as the member is
  retyped, the spacing changes, the carried span grows or the demand passes the row's load
  basis. **`deck_beam` is deregistered from the engineering register and `glulam_beam` is
  demoted to a pure `nds_states` module**; the arithmetic stays, printed beside the
  published row as an advisory, because every deck guide is dry-use and a balcony beam
  stands in weather. The `header` deferral is gone and `rafter` is narrowed to roofs that
  resolve no member at all. A house that authors no `PublishedSpan` gets the UNKNOWN with a
  hint, which is what `engineered()`'s old NO_CALC branch supplied. The register goes from
  41 items to 36 and unsealed from 9 to 7.
- **Nineteen new checks, and one renamed.** `code.R406_1_dampproofing` is **gone**, replaced
  by `code.MN_1309_0406_waterproofing` — a suppression or an allow-list naming the old id no
  longer matches anything. The additions are `code.R311_7_5_1_stair_end_risers`,
  `structural.slab_published_span`, `structural.rake_overhang_backspan`,
  `structural.deck_beam_cantilever`, `structural.column_on_wall_support`,
  `mep.run_member_crossing`, `mep.drain_tie_in`, `mep.drain_slope_margin`,
  `mep.room_heat_source`, `mep.erv_static_budget`, `mep.erv_manifold_ports`,
  `electrical.panel_feeder_load`, `integrity.member_profile_parses`,
  `integrity.drip_flashing_back_side`, `advisory.assembly_variety`,
  `advisory.countertop_overhang`, `advisory.floor_finish_depth` and
  `advisory.wall_backing_bearing`. A house that was clean under 0.1.0 may pick up findings
  from any of them; several found real defects in the reference house.
- **Minnesota is not an IRC plumbing state, and the drain-slope rule now says so.** The
  profile cited IRC P3005.3 for slope while citing ch. 4714 (UPC) for the sizing and
  trap-arm tables two lines below, and Minn. R. 1309.0010 subp. 3.D deletes IRC chapters
  25–33. UPC 708.0 is 1/4"/ft at **every** size, so the `>3" -> 1/8"/ft` row that both
  `mep.drain_slope` and `routing/gravity` carried is gone — it had been reading a 4" line as
  holding twice its grade when it was 0.017"/ft over the minimum. `resolve/mep_slope.py` is
  the one owner, returning the grade and the sentence to cite, and the reduced-slope
  exception is authored per run as `PipeRun.reduced_slope_approval` rather than as a
  preferences flag, because an approval is of one pipe on one set of drawings. On pipe under
  4" it is a FAIL. Beside it, `mep.drain_slope_margin` reports how much pitch is in hand **on
  a PASS as well**, since the field method steps a standoff about an inch every four feet and
  "at the minimum" and "half an inch over" are not the same building.
- **A pipe's nominal size and the diameter it measures are now two different numbers.**
  `resolve/pipe_sections.py` is the sibling of `LUMBER_ACTUAL`: the author writes the
  nominal the code tables are keyed on, the geometry gets the real OD, and `run_radii` reads
  it so all five consumers share one notion of a run's surface. Three tables, because the
  material decides and that is load-bearing — a material-blind IPS table reads 1 1/4" copper
  at 1.660" instead of 1.375" and invents clearance findings. Authored `diameter` is
  untouched and `mep.pipe_sizing` still keys its table on the nominal. The emitters and the
  takeoff still sweep the nominal tube this pass, recorded as debt in the module docstring,
  because widening the solid re-blesses every IFC golden.
- **One owner for the window a service may cross a floor's members in.** Three readings of
  that band existed and no two agreed. `resolve/mep_crossings.py` owns all three now — an
  open-web truss gives its web, an I-joist its depth less both flanges, solid-sawn IRC
  R502.8.1's 2" from each edge — and each carries the `basis` sentence a finding quotes,
  because "1.194" of crown" means nothing without "inside the 8 7/8" web" beside it. Those
  three are **not** the same permission: a truss's web is a hole that is already there,
  while the other two are zones a *bored* hole may sit in, and reading them alike had
  silently permitted an 8" round duct through an 11 7/8" I-joist. `mep.run_member_crossing`
  then grades pipe, duct and raceway alike per crossing rather than per leg; it found
  fifteen real defects in the reference house.
- **Clear height is measured from the finished floor, not the joist tops.** A storey's
  elevation is the structural datum and the finished floor stands above it by the whole
  build-up, which on the reference house runs from 0" on a bare slab to a full 1 1/2" over a
  3/4" wood floor — the code comments' flat 3/4" was wrong in both directions.
  `resolve/rooms.py::_clear_head` now takes an explicit datum and is handed
  `room_finished_floor_elevation`. It is the only place the datum could be chosen, so every
  consumer downstream moves with it, and headroom verdicts near a limit can change.
- **A room may say its ceiling is open on purpose.** A `Soffit` was the only authored answer
  to `mep.run_in_finished_volume`, which made a soffit the engine's idea of a ceiling rather
  than the owner's. `Room.exposed_services` is the other answer: a sentence saying why,
  refused at load time if it is a flag wearing a string. The check quotes it back in a PASS,
  so the report carries the decision rather than a silence and the house stays clean rather
  than suppressed — a suppression folds to UNKNOWN and does not open the permit gate. It
  retires exactly one question: every run in a declared room is still measured against
  `MepPreferences.exposed_service_headroom_ft`.
- **A nominal profile `cross_section` cannot parse is reported instead of swallowed.** An
  unreadable nominal came back as the 1 1/2" x 5 1/2" fallback and the solid, the plan cut,
  the interference check and the BOM row all quietly became a 2x6. The silence in `resolve()`
  stays, because 31 modules call `cross_section` where a raise aborts the build rather than
  reporting a defect; `parses()` asks the question without raising and
  `integrity.member_profile_parses` asks it of every authored and resolved nominal —
  elements, `JoistSpec`, `FramingSpec` and every stick the solver mints. UNKNOWN, not FAIL:
  the engine cannot say the member is wrong, only that it does not know what the string
  names.
- **New authorable elements and fields.** `Countertop` hosts on the placeables it covers and
  derives its slab polygon, area, run length and cantilever off the run, so a peninsula's
  knee is a gradeable fact rather than prose — it deliberately draws nothing, because the
  base-cabinet symbol already draws the slab. `SlatScreen` and `resolve/screens.py` model an
  open screen as structure. `Roof.bearing_refs` may now name a `Beam` and not only a wall
  (`resolve/roof_bearing.py`), which is what a canopy on two headers needs. `DoorType`
  carries `shgc` / `vt` with the same semantics `WindowType` has. `Site.parcel_basis` gains
  `"plat"` — dimensions stated off a plat, county record or deed, with nobody's seal on them
  and no corner located — which grades UNKNOWN rather than borrowing either the drawn or the
  surveyed verdict; `"placeholder"` still FAILs unchanged.
- **A glazed door is fenestration.** R202 says so and the engine treated one as glazing in
  some places and not others. `energy_load` now accumulates a door solar term with the
  orientation lookup hoisted out of the window branch, so a glazed exterior leaf stating no
  SHGC earns the same UNKNOWN a window does and an opaque leaf earns neither gain nor gap;
  the cooling sum is taken off the components rather than off `window_solar` by name, which
  was why the doors' gain sat in the report and outside the load. `mn_energy` grades exterior
  door types against the same N1102.1.2 fenestration column as `window_u_max` — the
  2009-era separate door column is gone — and skips interior leaves. A house with glazed
  exterior doors will see its cooling load move.
- **The panel schedule sees a line-voltage light run.** `_connected_va` summed
  `ElectricalDevice`s only and `connected_lighting_va` admitted luminaire types and PSU tags,
  so a `LightRun` with a circuit and no `psu_ref` was counted nowhere. It has no `load_va` to
  bill — it is watts per foot over a length, and only the resolved run knows the length — so
  the VA is indexed by tag off `model.light_runs`. Runs report under their own `runs` key and
  the fixture count is unchanged. A 24V run stays out: its load belongs to its PSU, which is
  a device counted already. `electrical.panel_feeder_load` grades the service the same way.
- **`model.json` tells the UI a wall's true kind, so a `FoundationWall` can be edited.** A
  writeback op matches the constructor name literally, which is what keeps a source rewrite
  honest about which constructor it edits, but the UI addressed every wall as `"Wall"` — so
  an op aimed at a `FoundationWall` routed to no file and came back 422, while the loader's
  consistency check counted that same element as UI-movable and reported the house clean on
  a capability it did not have. The disagreement, not the 422, was the bug. The wall payload
  now carries the authored element's own class name and the UI sends it back for delete and
  for the assembly picker; `writeback_py._call_kind` is deliberately **not** broadened.
- **`TrimKind.BEAM_CAP` gets its own solid category and trade.** It collapsed onto
  `flashing`, and flashing rides roofing, so aluminium beam caps showed under the roof toggle
  while the BOM had been billing them to siding all along. Minting a category touches five
  more consumers keyed on the category string — the glTF palette, the IFC kind map (unknown
  kinds fall back to `IfcFooting`, so seven caps would have exported as footings), the
  elevation projector, and the rest — which is why the split is eight files rather than
  three. Separately, the twelve HGAM10 masonry gussets are one BOM row of hurricane ties
  rather than two rows split ten post caps to two ties: landing on a cast column top is what
  the part is published for and does not turn it into a post cap.
- **The dead `PEDESTAL_CONCRETE` assembly is retired.** Zero elements carried it and the tag
  its comment named no longer exists. The BOM is byte-identical, because a `[concrete]` price
  key is only emitted for an assembly some element actually carries; the one real consequence
  is `model.json`'s `building_science.condensation` array, which analyses every library
  assembly and goes from 75 rows to 74, re-indexed at 28.
- **The reference house.** `houses/catlin` absorbed several hundred commits' worth of design
  work this cycle — the north entry engineered as real structure, the sunken garden court
  simplified to one footing, column and bell, an extruded garage replacing the poly
  breezeway, the truss girts, the board-and-batten product named and its screw withdrawal
  computed per NDS 2018 §12.2, the ERV static budget re-struck against the HVI-certified
  curve, the parcel corrected to its real 50' x 133', the electrical circuits reworked, and
  three soffits retired in favour of rooms that declare their ceilings open. It is a
  reference model rather than shipped API surface, so the detail lives in
  `houses/catlin/DESIGN-LOG.md`; what matters here is that it reports **0 FAIL** against
  1,450 encoded rules and remains the house the engine is exercised on.
- **mypy is no longer a gate**, in `ci.yml` or in `scripts/verify.sh`. There was no setting
  under which it passed — a heavily relaxed run still reports 1119 errors in 158 files — so
  it was removed rather than pinned green by a config that hides it. `[tool.mypy]
  strict = true` stays in the root `pyproject.toml` for local use.
- **`scripts/verify.sh` runs to completion again.** It is `set -e` with mypy at stage 4, so
  the builds, `haus check houses/catlin`, the full IFC build and the UI stages were never
  being reached by the script documented as the full gate. All ten stages now run.
- **`pytest-xdist` is now a declared dependency.** The root `pyproject.toml` carries
  `-n 6 --dist loadfile` in `addopts` unconditionally, so a pytest without xdist does not
  fall back to serial — it exits 4 at argument parsing, before collecting a test. It went
  undeclared because every local `.venv` happened to have it.
- **`scripts/ci_local.sh`** reproduces the CI engine job in a throwaway venv built from the
  declared extras alone. `verify.sh` runs in `.venv` and structurally cannot see a missing
  dependency; this can.
- **Float goldens are compared with a tolerance, not byte for byte.** CI runs linux x86_64
  and development happens on arm64; IEEE-754 arithmetic agrees exactly across the two but
  libm's transcendentals do not, so any coordinate that went through a sine or an `atan2`
  can differ in its last bits. The sweep parity fixture is graded at 1e-9, the tolerance its
  TypeScript reader already used. The section goldens are graded at **1/8 inch** on
  model-space coordinates — the finest tolerance anyone builds to — with drawing parameters
  (`scale`, `lineweight`, rotations, paper coordinates) held at 1e-9, because 1/8" of slack
  on `scale` would make 1/4" = 1'-0" compare equal to 3/8". Structure, layers and text stay
  exact. The trade is explicit: a change moving drawn geometry less than 1/8" no longer
  registers.
- **The catlin check stage matches the test it names.** It gated on zero FAILs while
  `test_catlin_carries_no_failures` accepts one — the parcel-ring advisory, owner state
  rather than a defect, already `blocking=False` in the Minnesota profile. The stage now
  gates on `haus check --json --exit-on none` with the identical one-entry allow-list, so a
  real regression still stops the build.
- **The PyPI project links point at the repository that exists.** `Repository` and `Issues`
  named `github.com/colincatlin/TypeHaus`; the remote is `github.com/winedarksea/TypeHaus`.
  Nothing in the build reads those fields, so the only place the mistake could surface was
  the published project page — as a dead "Source" link, after upload, permanently for that
  version.

## 0.1.0 — 2026-09-09 (tagged, never published)

`0.1.0a0` is on PyPI and is unusable: that wheel contained
only `typehaus/`, with no shared catalog, no `haus new` template, and no license text. Every
house plan does `from library import ...`, so `pip install typehaus==0.1.0a0` installed an
engine that could not load or scaffold a single house. Nothing in the source tree could see
the break, because from a checkout every one of those paths resolves anyway. Do not install
`0.1.0a0`.

### Packaging

- The shared catalog now lives inside the package as `typehaus/library/` and ships in the
  wheel. It is deliberately not a top-level `library` in site-packages: that name belongs to
  an unrelated project on PyPI, and installing both would break one of them. Plan source is
  unchanged — `from library import ...` still works, aliased by the loader.
- The `haus new` starter template ships in the wheel, so a pip-installed engine can scaffold
  a house without a checkout to copy one from.
- The pre-built editor ships in the wheel. `pip install 'typehaus[server]' && haus serve`
  now delivers the browser app instead of answering the "UI not built" 404. A checkout's own
  `ui/dist` still wins, so a local rebuild is never shadowed by the packaged copy.
- The license text ships in the wheel, declared with PEP 639 `license = "MIT"`.
- The sdist repeats the wheel's force-includes, so it can rebuild an equivalent wheel.
- `haus doctor` reports the packaged UI alongside the checkout's `ui/dist`.
- CI asserts wheel contents (`scripts/check_wheel.py`), prints the catlin permit set, and
  publishes to PyPI through Trusted Publishing on a published release.

### Engine

- An empty or absent `uid` is now a load-time ERROR, alongside the existing collision error.
  `haus fmt` mints a uid only where the keyword is absent entirely and never visits
  `params/*.py` at all, so an element authored there with `uid=""` used to load clean and
  then collide every derived IFC GlobalId onto the value derived from the empty string —
  erasing that element's geometry three layers downstream.
- `ruff check packages/engine/src` is clean.

### Known limitations

- **mypy is not a gate**, in CI or in `scripts/verify.sh`. `mypy --strict packages/engine/src`
  reports 2781 errors in 333 files, and a heavily relaxed run still reports 1119 in 158, so
  there was no setting under which the step could pass. It blocked the whole engine job, and
  because `verify.sh` is `set -e` it also meant every build, `haus check houses/catlin`, the
  full IFC build and the UI stages were never reached by the script documented as the full
  gate. `[tool.mypy] strict = true` stays in the root `pyproject.toml` for local use.
- `Room.clear_face` is inset from the wall axis rather than the finish face, which skews room
  polygons and areas on thick walls. Fixing it moves every golden; it is the first item after
  this release.
- `resolve/framing/profiles.cross_section` falls back to a 1.5x5.5 rectangle for any profile
  string it cannot parse, silently, rather than raising.
- `PipeRun` elevations are storey-relative while `ConduitRun` elevations are absolute.
