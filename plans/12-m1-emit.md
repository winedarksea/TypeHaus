# M1 — Emit & Checks: IFC, Assembly Card, Checks Framework

**Purpose:** M1's output half — the IFC emitter that proves the schema/resolve stack works,
the assembly section card that gives the assembly workflow a visual from day one, and the
checks framework every later tier plugs into.

## IFC emission

- **Schema: IFC4 (Add2 TC1)**, not 4.3 — materially better Revit/Bonsai/web-ifc support; IFC4
  has everything residential needs including georeferencing. Emitters behind an interface so
  4.3 is a future flag.
- **IfcOpenShell:** pin **0.8.x**; use module-style API
  (`ifcopenshell.api.root.create_entity`). Port from `ifcplot/ifc_utils.py` nearly verbatim
  into `emit/ifc/lowlevel.py` (typed): `placement_matrix`, `translation_matrix`,
  `add_prism_from_profile[_with_voids]`, `add_rect_member_between_points`, surface styles,
  trade groups, `ensure_pset`. **Rewrite** the wall builder: consumes junction-solved
  polygons; cuts real `IfcOpeningElement`s. Beware the mm-units scaling gotcha documented at
  `ifc_utils.py:395-406` (raw profile entities need `calculate_unit_scale` division) — or
  standardize project length unit and centralize scaling in lowlevel.py.
- **Georeferencing (M1):** `Site(lat, lon, elevation, crs, true_north)` →
  `IfcSite.RefLatitude/RefLongitude/RefElevation` + `IfcProjectedCRS`/`IfcMapConversion`
  (eastings/northings/rotation). `pyproj` for transforms. Basemap import is M3 (→ 30).
  Project-north-vs-true-north rule: (→ 02 §Pipeline).
- **LOD mechanics (#20, → 02 §Pipeline):** `--lod core` = one `IfcWall` per wall with
  `IfcMaterialLayerSetUsage` + shared `IfcWallType` per assembly; `--lod framed` adds
  generated members (`IfcMember`/`IfcCovering`) aggregated under the wall via
  `IfcRelAggregates`. Parent GUIDs identical across LODs so diff stays stable.
- **Psets:** `Pset_HF_Source = {uid, tag, plan_content_hash, assembly}` on every element,
  plus standard `Pset_WallCommon`/`Pset_DoorCommon`/`Pset_SpaceCommon`/`Qto_*`
  (→ 10 §Element model).
- **Determinism:** uuid5 GUIDs, sorted iteration, pinned OwnerHistory — CI asserts two
  consecutive builds are byte-identical (→ 02 §Pipeline).

## Assembly section card

The assemblies' visual feedback surface, shipped **early** because assemblies are half the
product and their authors (mostly Claude, sometimes the user) need to *see* a stack the
moment they touch it — not after the M3 detail slices land.

- **What it is:** a per-Assembly vertical stack rendering — every layer to scale (thin layers
  clamped via `ExaggerationSpec` with true thicknesses labeled), material hatch/color from
  the shared palette (→ 21 §Nordic preset), layer names + thicknesses, the **R-value rollup**
  (core + `default_lining`, per #34), **control-layer tags** (AIR/WATER/VAPOR/THERMAL badges
  on the layers that carry them), and the core/lining boundary. An **STC badge** renders beside
  the R-value rollup when `Assembly.stc` is set (#50) — always with its `source` note, the
  value being a lab-test lookup, never computed. A freeform `source` note renders
  when a library value carries one (#46, revised — no structured evidence); a calc missing an
  input renders visibly as UNKNOWN with the material named (#32).
  Variants render grouped under their base with the substituted span highlighted.
- **Where it appears:**
  - **M1 (WP1.9):** `haus explain <assembly> --card [--out card.svg]` — SVG (PNG via
    matplotlib for terminals that want it). Built on the drawing-IR primitives ported from
    `detail_utils.py` (`_batt_insulation`, `_lumber`, hatches) — the same port WP2.6 needs,
    pulled forward; the card is deliberately model-free (it renders an Assembly definition,
    not resolved geometry), so it needs nothing from the resolve pipeline.
  - **M2:** the UI **assembly inspector panel** (→ 21 §Assembly picker) renders the same card
    live — and because the card is model-free, it doubles as the **live canvas of the assembly
    editor** (→ 21b §Assembly editor, WP2.4d/e), re-rendering on every layer edit, not only a
    read view.
  - **M3:** the A-401 sheet's per-assembly header block reuses it (→ 30).
  - **M5:** the Glaser condensation plot lands *on* the card (→ 50) — temperature/vapor
    curves drawn beside the same stack. One artifact, progressively enriched.
- **Agent loop:** `/add-assembly` (→ 20 §Agent scaffolding) renders the card after every
  edit; the card plus `haus check`'s R-value-vs-preferences warn is the fast feedback pair
  that makes "agentic AI organizes the envelope layers" concrete.

## Checks framework

- **Shape:** a check is a pure function
  `(ResolvedModel, Preferences, JurisdictionProfile) -> list[Finding]` registered via
  decorator. `Finding(severity: ERROR|WARN, check_id, message, element_tags, code_ref,
  source_loc, fix_hint)`. Rule *results* are **tri-state** (#32): `PASS | FAIL |
  UNKNOWN(reason)` — a rule that cannot evaluate (data not modeled, unsupported geometry,
  e.g. R305 before the roof exists) reports UNKNOWN with the reason, is counted in its own
  column in every output surface, and is never folded into the pass count.
- **Tiers** (integrity/code/advisory/structural all scaffolded early — integrity is the deep
  one; `building_science` is the exception, scaffolded last per #42 → 50):
  - `checks/integrity/` — **main focus**: wall-loop closure / dangling nodes; every wall has
    an assembly and its alignment resolves to a real layer; openings fit host with min edge
    distances; room seeds resolve to closed faces; storey/height consistency; tag uniqueness;
    assembly layer sanity (thicknesses > 0, functions ordered sensibly);
    **boundary-condition coverage** — every derived condition (→ 11b) bound to a Transition
    or warn-flagged, transition/overlay anchors resolve; assembly-change nodes audited with
    per-layer face jogs quantified; **stack derivation sanity (#43)** — ambiguous stacks
    flagged with the `stacks_on` hint, storey-stack conditions enumerated; lining stacks
    resolve on every claimed face; variant sets have exactly one active member and no
    cross-variant refs.
  - `checks/code/mn_residential/` — profiles **versioned by edition**: `mn-2024` first (the
    current MN Residential Code — 2021 IRC base with MN Rules 1309 amendments — what a 2026+
    catlin submittal is reviewed against); other editions are additional profiles. Start with
    ~5 high-value rules: egress window area/dimensions/sill height (R310), door clear widths,
    minimum ceiling heights (**including Soffit drops** and the R305 sloped-ceiling average
    for roof-defined attic ceilings), stair riser/tread/headroom (R311.7), hallway width;
    smoke/CO alarm placement (R314/R315) joins in M3. **Profile rigor (#32):** every rule
    carries its code citation; the profile module declares its edition, effective date, and
    amendment history vs. its IRC base; each rule ships with pass/fail fixture plans; and the
    profile exposes a **coverage statement** (which code chapters it encodes, which it
    doesn't). All rendered output — CLI table, A-000 code summary, UI panel — says "N pass,
    F fail, U not evaluable, of M encoded rules; this profile covers a declared subset of the
    code" and **never** the words "code compliant".
  - `checks/advisory/` — **design intelligence, warn-only, reasoning shown** (opinions with
    arithmetic behind them, never authority): habitable rooms without an exterior window;
    count of unique door and window sizes (fewer sizes = cheaper ordering — reported as a
    fact, with the size histogram); kitchen work-triangle perimeter outside the 12'–26' rule
    of thumb (activates in M3 with fixtures); door-swing collisions (two swing arcs
    intersecting, or a swing hitting a fixture clearance box — shares geometry with the → 30
    clearance overlays so UI and CLI always agree); **control-layer continuity** (→ 11b):
    walk each tagged air/water/vapor/thermal layer across junctions *and stack edges* and
    warn where one dead-ends at a boundary whose transition doesn't declare continuity;
    `FloorHeat` zones under fixed fixtures; **wet-wall depth** (M3, → 30): a drain-needing
    fixture on a wall too thin for its stack; **acoustic adjacency (#50, M3)**: a quiet-class
    room (bedroom) sharing a partition with a noisy-class room (bathroom, mechanical, media)
    where the partition's `stc` is unset or below a `preferences.toml` threshold — reported as
    the adjacency fact plus the assembly's STC status, one rule, warn-only, off by default
    until the STC library presets exist. Every advisory finding states *why* in the
    message and is individually suppressible in `preferences.toml`.
  - `checks/structural/` — table-driven, clearly labeled "advisory, not engineering":
    I-joist span lookup (covers catlin's 18-ft spans), header sizing over openings — one
    table module shared with the framing solver (→ 11 §Framing solver).
  - `checks/building_science/` — scaffolded (empty registry + tier wiring) in M1, populated
    in M5 (→ 50).
- **Dual invocation:** a small pytest plugin parametrizes the registry so plain `pytest` runs
  every check as a test (the agent-native feedback loop); `haus check --profile mn-2024
  --json` runs the same registry with human table + machine JSON output.
- **Preferences feed targets:** `preferences.toml` `[envelope]` (PGH: `wall_r=40, roof_r=60,
  window_u=0.25, ach50=1.0`) consumed by warn-tier envelope checks against computed Assembly
  R-values.
- **IDS/ifctester:** `haus check --ifc` generates an `.ids` from the active profile
  (required psets/attributes/classifications) and runs `ifctester` against the built IFC —
  validating the **emitter**, not just the model. Integrity-tier post-build gate.
- **Feedback loop contract:** every failure surface is structured and points at source —
  build errors carry element tag + file:line; `haus check --json` likewise; `mypy --strict`
  + pytest complete the loop. The agent loop is: edit → build → check → fix, entirely from
  CLI output.

## Workpackages

- **WP1.7 IFC emitter (core LOD).** Port `ifc_utils.py` → `emit/ifc/lowlevel.py` (typed);
  walls with `IfcMaterialLayerSetUsage`/`IfcWallType`; real `IfcOpeningElement`/`IfcDoor`/
  `IfcWindow`/`IfcRelFillsElement`; `IfcSpace`; georeferencing (`IfcMapConversion`/
  `IfcProjectedCRS` via pyproj); deterministic GUIDs; pinned OwnerHistory. *Tests:* golden
  IFC snapshot of the demo plan; ifctester baseline IDS; byte-determinism (two builds).
  *Done when:* the demo IFC opens in Bonsai with correct walls/corners/openings/spaces/
  georef.
- **WP1.8 Integrity checks + pytest plugin.** Registry, `Finding` model, the integrity set
  above (including stack-derivation sanity and condition coverage), pytest parametrization;
  deliberately-broken fixture plans (gap node, orphan opening, missing assembly, ambiguous
  stack) each producing exactly one precise finding. *Done when:* `pytest` and `haus check`
  report identical findings on every fixture.
- **WP1.9 CLI v1.** `haus build | check | ls | explain` — including
  `explain <assembly> --card` (§Assembly card) and `explain --transitions` (condition
  enumeration). *Done when:* the M1 acceptance script below runs end-to-end from the CLI.

## M1 acceptance

A hand-written 2-storey demo plan (in `houses/starter/`) builds to valid IFC4 — passes an
ifctester baseline IDS and opens in Bonsai with correct walls/openings/spaces/georef; two
consecutive builds are **byte-identical** (CI-enforced); broken fixtures fail precisely;
every Room's `IfcSpace` polygon touches its bounding walls' interior faces with zero gap
(#41); the demo plan's two storeys derive a wall-line stack whose **storey-stack condition
appears in `haus explain --transitions` (#43)**; `haus explain <assembly> --card` renders a
correct card for every `library/` assembly; `mypy --strict` and ruff clean.

## Risks owned

- **Risk 5 — IfcOpenShell API instability.** Mitigation pattern: pin 0.8.x; all calls
  confined to `emit/ifc/lowlevel.py` (~600-line adapter, exactly what `ifc_utils.py` proved
  out); golden IFC snapshots detect drift on any bump.

## Open questions — resolved in this doc

- **Assembly-card format & placements** → §Assembly section card (SVG/PNG via drawing-IR
  primitives; CLI M1, UI panel M2, A-401 header M3, Glaser plot M5).
- **Where the checks registry lives relative to pytest** → §Checks framework (one registry,
  two invokers — pytest plugin and `haus check` — identical findings guaranteed by test).
