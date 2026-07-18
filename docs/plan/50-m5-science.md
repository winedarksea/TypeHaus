# M5 — Building-Science Analysis Tools

**Purpose:** lowest priority by decision (#42) — genuinely last, after the M4 gate. All
schema this depends on landed in M1 (→ 10 §Building-science scalars); nothing here touches
the compiler pipeline, the UI editing surface, or adds authored element kinds — three new
report/check consumers of the already-resolved model. The **assembly section card** (→ 12
§Assembly card) has been shipping since M1; these tools enrich it.

## The three tools

- **Condensation risk (Glaser method).** For each Assembly, walk its layers in order
  computing the steady-state **temperature gradient** (from cumulative R-value between
  `Site.design_temp_heating` and an assumed interior setpoint) and the **vapor-pressure
  gradient** (from each layer's `Material.perm_rating` and thickness, interior/exterior
  humidity assumptions in `preferences.toml`). Where the saturation curve and actual vapor
  pressure cross inside a layer, emit a WARN `Finding` naming the layer ("dew point reached
  at Layer 3: Sheathing") and render a temperature/vapor-pressure plot **onto the assembly
  section card** and on the A-401 sheet beside that assembly's detail Slice (→ 30 §Sheets) —
  the same per-Assembly walk the R-value calc already does, one more consumer of the same
  data. A material missing `perm_rating` → UNKNOWN with the material named (#32), never a
  guess.
- **Window-to-wall ratio.** Per façade (N/E/S/W, from `Site.true_north` + each wall's
  resolved outward normal — already computed), glazing area ÷ gross wall area. A WARN when
  south-facing WWR exceeds a `preferences.toml [envelope]` threshold without adequate
  overhang coverage (reads roof/eave overhang geometry the same way the R305 check reads the
  roof). Advisory, not code: MN residential doesn't hard-cap WWR the way commercial ASHRAE
  90.1 does.
- **Block heating/cooling load ("Manual J lite").** Sum UA (U-factor × resolved area) across
  every envelope element — walls, roof, slab/foundation, windows/doors, the last two also
  SHGC-weighted for solar gain — against `design_temp_heating/cooling`. Not a pass/fail
  check — a **report**: `haus energy` (CLI + `--json`), a UI dashboard panel (below), and an
  EN-1 sheet line item. This is the tool that answers "what does 2x4 → 2x6 actually save me"
  directly, because it's summing Assembly R-values the resolver already computes — no new
  geometry, just a new consumer.

**Tier placement:** condensation risk + WWR live in `checks/building_science/`
(physics-grounded like `checks/structural/` — "advisory, not engineering"; distinct from code
citations and design opinions, → 12 §Checks). The load estimator is a report, not a check, so
it doesn't live in a check tier.

**UI: building-science dashboard** (completes the → 21b intelligence list): per-façade WWR
readout, block heat/cool load summary (BTU/h, rough tonnage) with a live 2x4-vs-2x6
wall-assembly comparison, and a condensation-risk list (assemblies with a dew-point crossing,
linking to their card/A-401 plot). Every number reads the resolved model exactly like the
takeoff dashboard.

## Workpackages

- **WP5.1 Condensation risk (Glaser method).** `checks/building_science/condensation.py` —
  per-Assembly temperature + vapor-pressure gradient walk, WARN `Finding` on a crossing, plot
  renderer wired into the assembly card and the A-401 sheet. *Tests:* fixture assemblies with
  a known condensation point and a known-safe point as golden tests; UNKNOWN on missing perm
  data.
- **WP5.2 Window-to-wall ratio analyzer.** `checks/building_science/wwr.py` — per-façade
  glazing percentage from `true_north` + resolved wall normals, overhang-aware south-glass
  WARN against `preferences.toml [envelope]`; dashboard panel.
- **WP5.3 Block heating/cooling load estimator.** `haus energy` CLI (`--json`), UA-sum +
  SHGC-weighted solar gain against `Site.design_temp_heating/cooling`; dashboard panel; EN-1
  sheet line item.

## M5 acceptance

For the catlin house, `haus check --tier building_science` reports the eave/sauna
assemblies' condensation margins with no unexplained UNKNOWNs; the WWR dashboard matches a
hand count of the south-façade glazing; `haus energy` output brackets a sane MN heating
BTU/h figure and visibly drops when a wall assembly swaps 2x4 → 2x6 on the same run.

## Why M5 and not earlier

All three read the resolved model and nothing else — no new authored elements, no UI editing
surface, no compiler-pipeline change. Scheduling them last costs nothing architecturally;
scheduling the *schema* last would have meant touching Material/WindowType/Site/Room again
after houses already depend on them — which is why the scalars landed in M1 (#41) and only
the tools wait. (The early-Glaser option was considered and declined during the plan review —
→ 01 §Rejected.)
