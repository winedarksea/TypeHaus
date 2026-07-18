# M1 — Resolve: Topology, Stacking, Floors, Framing, Foundations

**Purpose:** the resolve pipeline stage — everything between the validated `PlanModel` and the
emitters. This is where the product's harmony contract lives: one authored change → junction
solver → wall polygons → room faces → dimension chains → framing solve → every Slice, the 3D
view, checks, and takeoffs. Nothing is drawn twice, so plans, details, and the 3D model cannot
disagree.

**Exit criteria (resolve half of M1 acceptance, → 12 §M1 acceptance):** the demo plan's walls
resolve gap-free with mitered corners; rooms derive and claim; framing solves under budget;
broken fixtures (gap node, orphan opening, missing assembly) each fail with exactly one
precise finding.

## Wall topology — node graph + junction solver (the "no gaps" fix)

The single most important structural decision. Walls are **edges between shared nodes**, not
independent segments:

- **`Node`** — a 2D point per storey (auto-tagged `N-1…`, user-nameable).
- **`Wall`** — connects exactly two nodes. Required fields: `assembly` (a wall cannot exist
  without one), a **top constraint** — `top: Length | ToRoof(ref)` from **day one in the
  schema**, because real walls terminate against sloped roof planes (gable-end walls, walls
  under sheds): a scalar-height-only wall model produces flat tops jutting through or gapping
  under roofs and cannot be retrofitted without rewriting the wall core. M1 implements only
  the `Length` arm; `ToRoof` resolves in M3 (the resolver clips the wall's layer polygons
  against the referenced roof's plane — a shapely/boolean step in the junction-solved
  pipeline, and the IFC emitter already receives arbitrary polygons so it needs no change).
  An unresolved `ToRoof` (missing/non-adjacent roof) is an integrity error. When `top` is
  omitted, it defaults to the underside of the storey's `FloorSystem` above (derived from the
  storey elevation delta, §Floors below) — one source of truth for wall height. And
  **alignment**: which assembly face lies on the node-to-node axis (`"center"` |
  `"face:sheathing-ext"` | `"face:stud-int"` | center+offset). Residential dimensions
  reference face-of-stud / face-of-sheathing, so alignment is first-class.
- The **junction solver** (in `resolve/`) builds the planar graph per storey and resolves
  every node:
  - **L-corner:** mitered layer geometry.
  - **T-junction:** butt per layer priority — structure runs through, sheathing/membrane
    continuity per the layer's `function`, finishes wrap.
  - **X-junction:** split into four resolved corners.
  - Output per wall: a **polygonal body per layer** (replacing the old
    rectangle-between-points), so corners are geometrically complete *by construction*.
- **Gaps cannot be silent:** any node with exactly one wall edge not flagged `open_end=True`
  (wing walls) is an integrity **error** with coordinates and tag.

### Junction policy — resolved

How layers meet at a junction is a property of the *assemblies* meeting there, expressed as a
small closed enum rather than free-form rules:

```python
class JunctionPolicy(Enum):
    STRUCTURE_BUTTS_FINISH_WRAPS = auto()   # default: structure runs through at T, finishes wrap
    FINISH_BUTTS = auto()                   # utility spaces: finishes butt square, no wrap
```

- `Assembly.junction_policy: JunctionPolicy = STRUCTURE_BUTTS_FINISH_WRAPS`. Per layer
  `function`, the solver applies a fixed behavior table (STRUCTURE: through/butt by priority;
  SHEATHING/MEMBRANE: continuous past the joint per `control` role; INSULATION/AIRGAP: butt;
  FURRING/CLADDING/FINISH: wrap or butt per policy).
- **No per-node overrides in M1** — a per-node override needs a schema slot and UI
  affordances, and no catlin condition requires one. If a real case appears, the addition is
  a `Node.junction_override` field — additive, not a redesign.
- Priority between two STRUCTURE layers at a T: the wall whose axis runs *through* wins;
  at an L both miter. Ties (X-junctions) resolve by wall tag order — deterministic, boring.

## Vertical stacking (#43) — walls across storeys

The catlin house is the motivating case: one wall line runs poured concrete (basement) →
2x6 LSL (first floor) → 2x4 LSL (second floor) → 2x4 dimensional (attic), with the exterior
sheathing plane constant ("36'×36' measured at the sheathing"). Assemblies changing across
floor levels is the *normal* condition, not an edge case — so it is modeled, derived, and
checked like every other boundary.

- **Vertical datum.** `Storey.vertical_datum: FaceRef = face("sheathing-ext")` with per-wall
  override `Wall.vertical_datum: FaceRef | None`. The datum names the assembly face that
  stays plumb across storeys. Default is exterior-sheathing continuity (the catlin
  convention); an interior-face datum suits party-wall-style alignment; `center` is allowed
  but discouraged (a width change then jogs both faces).
- **Stack derivation — derived, never authored.** After each storey's junction solve, the
  **vertical stacking pass** runs per pair of adjacent storeys: for wall `W` below, project
  its datum-face line into the storey above; candidate walls above are those whose datum-face
  line lies within tolerance (default `inch(0.5)`) with overlapping extent ≥ `ft(2)`.
  - Exactly one candidate → a **stack edge** (W below ↔ W′ above).
  - Multiple or partial-overlap candidates → the stack edges are still recorded per
    overlapping span (a long wall below may carry two walls above), but a genuinely ambiguous
    alignment (two candidates over the same span) is an integrity finding suggesting the
    authored tiebreaker `Wall.stacks_on = "<tag-below>"`, which always wins.
  - No candidate → simply no stack edge (a setback storey); nothing to check.
- **Wall-line stacks** (chains bottom → top, including `FoundationWall` at the bottom) are a
  first-class `ResolvedModel` product with three consumers:
  1. **Boundary conditions** — each stack edge through a `FloorSystem` emits a
     **storey-stack condition** (the rim/band condition, anchored to the generated rim joist,
     §Floors), and each stack edge where assembly
     widths differ additionally emits a **stack-width-change condition** with per-layer face
     jogs quantified (same computation as assembly-change nodes, §Wall variation below).
     Both feed the transition system (→ 11b §Transitions).
  2. **Stud stacking** — the framing solver's in-line framing option (§Framing solver below)
     aligns stud layout grids along stack edges.
  3. **Load path** — `haus explain --bearing` walks stack edges as vertical load-path
     segments (§Foundations below).
- **Control-layer continuity is vertical too:** the continuity check (→ 12 §Checks) walks
  each control layer across stack edges exactly as it walks plan junctions — the air barrier
  must get from sheathing below, across the rim band, to sheathing above, and a storey-stack
  condition whose transition doesn't declare that continuity is a warn finding. This is the
  answer to "do the assemblies come together coherently across floor levels": the moment they
  don't, a finding names the exact edge.

## Two-tier floor model (#21) — FloorSystem + finish tier

The tension: joists span between bearing walls and ignore interior partitions, while floor
finishes vary per room (or within one). These are **two different tiers with two natural
owners** — model them separately and the tension disappears:

- **`FloorSystem` (owner: Storey) — the structural deck.** One per framed level (a storey may
  have zero for slab-on-grade — that's what `Slab` remains for). Carries:
  - `JoistSpec(member, spacing, direction, bearing_refs)` — bearing refs are wall/beam tags;
    the framing solver generates joists between them, running straight over partitions, **plus
    the rim/band joist** closing the joist ends around the deck perimeter (and rim blocking at
    intermediate bearing lines) — a real generated member of joist depth following the
    FloorSystem's outer edge, with deterministic child uids like every other framed member.
    This is the member the storey-stack (rim/band) condition and its air-sealing transition
    anchor to (#43, §Vertical stacking): the detail now flashes over a member that actually
    exists in 3D, in section slices, and in the BOM — not a described-but-unbuilt board.
  - `subfloor` layer (material + thickness) and `ceiling_below` layer (the drywall on the
    underside), so the deck is a real assembly-like stack: its total depth **feeds the storey
    elevation delta**, which is exactly what the stair designer's derived floor-to-floor rise
    (→ 21b §Stair designer) reads — one source of truth for the number beginners get wrong.
  - **`FloorOpening(polygon, purpose=stair|chase|hatch)`** — first-class, owned by the
    FloorSystem, **referenced by tag from the `Stair`** (and from anything else that passes
    through). This is what makes stair openings *consistent between levels by construction*:
    there is exactly one opening object, the stair points at it, and integrity checks verify
    (a) the stair's referenced opening exists in the FloorSystem above it, (b) headroom clears
    per R311.7, (c) the solver generated trimmer/header joists around it (doubled members at
    opening edges fall out of the framing solver, not hand modeling).
- **Finish tier (owner: Room) — `FloorFinish`.** Each Room's finish polygon is **derived from
  its claimed face** (no re-drawing, no drift when walls move): `Room.floor_finish="carpet-x"`
  covers the face; optional `FinishZone(polygon, material)` children handle in-room variation
  (tile inlay at an entry, hearth pad). Ceiling finish is likewise Room-level and composes
  with overlapping storey `Soffit`s. **All area takeoffs (#25) — carpet, tile, underlayment
  sq ft — read this tier;** structural BOM (joist count/length, subfloor sheets) reads the
  FloorSystem.
- **Emission:** FloorSystem → `IfcSlab` (deck) + aggregated `IfcMember` joists **and rim/band
  joists** at framed LOD + `IfcOpeningElement` per FloorOpening; FloorFinish →
  `IfcCovering(FLOORING)` per room — which
  is also exactly how Revit expects to receive floor finishes.
- **`Soffit` — storey-level dropped ceiling (#40).** `Soffit(polygon, drop |
  underside_elevation, framing: FramingSpec | None = None)` owned by the Storey — the polygon
  may cross room boundaries (the catlin case: a duct chase running down the hallway and into
  part of one room). With a `FramingSpec`, the framing solver generates the drop framing
  (2x4 ladder below primary structure) — visible in 3D at framed LOD, cut by slices, counted
  in the BOM. Floorplans render it with the dashed above-cut-plane convention plus a
  ceiling-height annotation; ceiling-height checks evaluate residual clear height **per
  overlapped room** (hallway vs. habitable-room minimums separately — the "fits the duct
  without blocking the hallway" question is answered by a finding, not by eyeballing). Rooms
  don't own soffits; a room's ceiling derivation subtracts overlapping soffits geometrically.
- **`FloorHeat` — zone-level radiant heat (#39).** `FloorHeat(zone=polygon | room_ref,
  system=electric | hydronic, spacing, embed=in_slab(depth) | under_subfloor, stat=pt(...),
  sensors=[...])`, owned by the Slab or FloorSystem it heats. Resolves to: a schematic
  serpentine clipped to zone-minus-keep-outs on floorplans (symbol layer; also the E/M sheet),
  wire/tube dots at spacing + embed depth in any slice cutting the slab, wire-length /
  mat-area + stat/sensor counts in takeoffs (#25), and warn findings where the zone runs under
  fixed fixtures or cabinet footprints (shares clearance-overlay geometry, → 30). Deliberately
  no routing solver — the serpentine is schematic.

## Framing solver & FramingSpec (#20 — the signature)

Platform framing is a small closed rule system — that's the "inherent mathematical beauty" —
so it lives as a **library of framing rules in `resolve/framing/`, running on every build** as
a core pipeline stage. It is a pure, deterministic function
`(resolved wall/floor polygons, FramingSpec) -> list[FramedMember]`; members carry
deterministic child uids under their parent (→ 10 §Stable IDs) so GUIDs are stable
build-to-build.

`FramingSpec` (per Assembly layer — the STRUCTURE layer always, plus any `FURRING` layer that
carries one):

- **Layout:** stud spacing (16"/24" o.c., configurable), member size (2x4/2x6…), layout origin
  rule (from which node the grid counts), bottom plate + double top plate (single-top /
  advanced-framing option). **Partition layouts (#50):** `staggered` (e.g. 2x4 studs
  alternating on a 2x6 plate) and `double` (two independent stud rows with a declared gap,
  each row with its own plates) are first-class layout options — the STC-rated library
  partitions must frame truthfully under #20, not render as ordinary single-row walls.
- **Openings:** king + jack (trimmer) studs per opening-width table, header sizing pulled from
  the same tables `checks/structural/` uses (one table module, two consumers), cripple studs
  above headers and below sills, sill plates — driven by the `DoorType`/`WindowType`
  rough-opening size. This is also what powers the "framing bumpers" overlay (→ 30). Applies
  to **rectangular ROs in framed walls only**: openings in masonry/concrete walls (the
  `MasonrySpec` path below) — including **arched openings** (catlin's poured-concrete arches,
  → 10 §Element model) — are cut and shown but grow no wood members; a non-rectangular opening
  in a framed wall is a finding, never silently approximated with a rectangular header.
- **Corners & intersections:** junction-solver output tells the framer the condition; default
  three-stud California corner (four-stud and ladder-blocking T options per spec) — corners
  are framed correctly *because* walls are edges in a solved graph, not independent boxes.
- **Stacking:** an opt-in advanced-framing flag aligns stud layout grids **along the derived
  wall-line stacks (#43)** and with joist layout (in-line framing), giving visibly aligned
  load paths in section views — the stacking pass supplies which walls stack; the framer only
  aligns grids.
- **Raked tops & rafters (M3 — closing the gable-end gap):** a wall whose `top: ToRoof(ref)`
  resolves (§Wall topology) hands the framer its *clipped* polygon: studs generate on the
  same layout grid but are cut individually to the rake line, top plates follow the rake as
  sloped plates, and opening framing (king/jack/header/cripple) composes with the raked top
  exactly as with a level one. Rake overhangs > 0 get ladder/lookout framing via the roof
  `ConstructionRule` family (#45); zero-overhang rakes (catlin) need none. Roof planes
  themselves frame from the roof assembly's STRUCTURE-layer `FramingSpec` — rafters at
  spacing between ridge and bearing refs, with birdsmouth/bearing-plate geometry supplied by
  `ConstructionRule`s (§Interfaces below) — so gable ends and roof planes are framed, cut by
  slices, rendered in 3D, and counted in takeoffs like every other member. M1's solver
  handles level tops only; this arm activates with the M3 roofs (→ 30 WP3.11), where the
  golden matrix grows gable-end fixtures.
- **Furring & strapping (the rainscreen / standing-seam path):** a `FURRING` layer may carry
  its own `FramingSpec`, and the solver generates its strapping as **real members on the
  layer's own grid** — *independent of the stud layout* (24" o.c. strapping over 16" o.c.
  studs is the normal case, and the grids need not divide evenly). The spec's **`direction`**
  chooses how the members run: vertical furring for horizontal cladding, horizontal girts for
  vertical standing-seam panels — so the strapping runs the right way for the cladding it
  carries. Members get deterministic child uids like studs and sit inside the resolved furring
  layer's envelope (which still wraps/butts at junctions per `JunctionPolicy`, §Junction
  policy), so they feed all four sinks: shown between sheathing and cladding in 3D and every
  section slice, drawn on S-sheets, and counted in the takeoff as **strapping lineal feet**.
  This is the visible **panel → furring → stud/sheathing** fastening path. Fasteners
  themselves stay a schedule note, not modeled members (the standard procurement-item
  exclusion, → 21b §Takeoff dashboard). **The same layer path frames roof battens/counter-battens** over
  a roof plane (vented over-batten metal roofs); catlin's hot roof lands the panel directly on
  the deck and grows none.
- **Masonry (#23):** CMU/ICF STRUCTURE layers carry `MasonrySpec(unit_size, coursing,
  core_fill, rebar_spacing)` instead — the walls render as accurate layered solids (insulation
  and air-barrier layers hatched exactly like wood assemblies), and the takeoff computes
  block / form counts and rebar length arithmetically. No per-block geometry.

**Where the output goes (one solve, four sinks):** (a) 3D members (`IfcMember` aggregated
under the parent wall at framed LOD), (b) **2D plan cuts — the signature look:** the
floor-plan cut plane slices real stud rectangles, insulation hatch between them,
sheathing/drywall linework from the assembly, replacing gray-box wall poché (a per-sheet
`simplified_poche` toggle exists for jurisdictions that want conventional plans), (c) S-101
framing plan sheets, (d) BOM/takeoff counts (#25).

**Performance budget:** framing a whole house is thousands of rectangles from closed-form
rules — target **< 200 ms** for the full solve; members stay lightweight records (no geometry
kernel) until emit; the UI receives them as instanced primitives (→ 21 §Nordic preset).

## Foundations & bearing (#27 — schema in M1, sheets in M3)

Promoted from headroom because the flagship house needs them (basement + ICF garage) and a
permit set without a foundation plan isn't a permit set:

- **`FoundationWall`** — a `Wall` in every structural sense (edges between nodes,
  assembly-driven, junction-solved; `GARAGE_ICF` already models one), distinguished by kind so
  checks (frost depth, anchor-bolt notes), sheets (foundation plan, not floor plan), and IFC
  class selection (`IfcWall` with foundation pset) treat it correctly. Reuses everything — no
  second wall system. Participates in wall-line stacks (#43) as the bottom link.
- **`Footing(under=<wall-or-post tag>, width, depth)`** — strip footings under foundation
  walls, spread footings under posts; auto-follows its parent's geometry so moving a wall
  moves its footing. → `IfcFooting`. **`Pad(polygon, thickness)`** for isolated pads/thickened
  slabs.
- **`Post` / `Beam`** — point/axis structural members reusing
  `add_rect_member_between_points`; beams are valid `bearing_refs` for `JoistSpec`, which is
  how a mid-span beam line enters the floor solve. → `IfcColumn`, `IfcBeam`.
- **Load path: authored facts, derived graph.** Geometry alone cannot tell bearing from
  spatial adjacency — a wall under a joist isn't necessarily carrying it. So the elements
  carry **minimal authored structural intent**:
  `Wall(structural_role="bearing"|"nonbearing"|"unknown")` (default `unknown`), and explicit
  `bearing_refs`/`supported_by` tags where load transfers — `Beam(bearing_refs=("POST-1",
  "FW-2"))`, `Post(supported_by="PAD-3")`, plus the `JoistSpec`/`Roof` bearing refs already in
  the schema. The load-path **graph stays derived** (never authored as a graph — it would
  drift): `haus explain --bearing` and the UI overlay follow these references plus geometry
  plus the #43 stack edges, and **`unknown` breaks the chain visibly** — rendered as a gap
  with a warn finding, never silently treated as nonbearing. Advisory structural checks
  (→ 12 §Checks) walk the same derivation, and a bearing wall whose joists land on nothing
  below is exactly the kind of finding this exists for.
- **Foundation scope, stated honestly:** `FoundationWall` carries top and bottom elevations
  (the catlin walkout/sunken-garden condition needs them). **Stepped footings and engineered
  retaining-wall conditions are out of scope through M3** — a foundation wall whose retained
  height exceeds the prescriptive table limit, or a footing that would need to step, produces
  an explicit "requires engineering / not modeled" finding rather than plausible-looking
  geometry.

M1 ships the schema + resolve + core-LOD IFC emission; the S-100 foundation-plan sheet and
frost-depth check land with the M3 permit set.

## Interfaces, vertical stacks, and construction rules (#43–#45)

The resolver must describe the *connection* between assemblies as rigorously as each wall. A
layer stack alone is insufficient: the eave and basement examples rely on semantic surfaces
(sheathing/air barrier/drainage plane), bearing faces, and offsets that remain meaningful as
layers vary.

- **Assembly interfaces (#44):** after variants and room linings resolve, expose stable face
  roles: `bearing`, `structure_ext`, `structure_int`, `envelope_datum` (default exterior
  sheathing), `drainage`, and one named surface per control layer. A role either resolves to
  one face or is absent with a precise finding; no recipe may fall back to “layer number 4.”
  A variant declares whether it preserves, replaces, or removes an interface.
- **Vertical interfaces:** match projected wall-run overlap using #43's datum and tolerance,
  then create `VerticalInterface(lower_run, support, upper_run, overlap, offsets,
  condition_kind)`. The relationship is derived whenever geometry yields one unambiguous
  candidate. `stacks_on` is required for ambiguous candidates and allowed for intentional
  setbacks; it references the lower wall/run and is validated against real overlap. This
  record, rather than tag matching downstream, is the sole input to stud stacking, load-path
  explanation, continuity walking, slices, and takeoffs.
- **Construction rules (#45):** `ConstructionRule` is a typed pre-resolve input selected by
  compact family/role predicates. It can require blocking, plate geometry, web stiffener,
  bearing gap, or framing offset, with dimensions and takeoff category. The resolver applies
  it once before final framing. Rules cannot draw notes/overlays; a later `Transition` only
  documents and validates the rule it names. This keeps resolution acyclic and makes the 3D
  model, plan cut, section, and BOM agree.

## Wall variation — lining tier + assembly variants (#34, #35)

The sauna exposed the general shape of the problem: walls vary **by face** (what a room does
to its side) and **by segment** (what the exterior does along a run). Two mechanisms, both
keeping the base assembly single-source:

- **Lining tier — per room-face (#34).** Mirrors the two-tier floor model. The assembly
  proper is the **core** — the structural layer and everything outboard of it — plus a
  **`default_lining`** (the interior-of-structure stack, e.g. `[5/8" drywall]`). Every wall
  face bounding a Room resolves a lining: the assembly default unless the Room overrides —
  `Room(wall_lining=[Layer(polyiso, inch(2)), Layer(furring, inch(0.5)),
  Layer(t_and_g, inch(1))])`, with per-wall exceptions allowed. The sauna authors its liner
  **once**; it lands on the exterior wall face *and* both partition faces, while each
  partition's other side keeps the neighboring room's drywall — per-side asymmetry by
  construction, no `INT-2X4-SAUNA-SIDE-A` assembly zoo. Consequences that fall out:
  - **Floorplans update automatically:** room clear faces derive from core + resolved lining
    thickness, so a lining change moves the finished face and every dimension chain
    referencing `face:finish-int` — and a drywall spec change (1/2" → 5/8") visibly moves the
    plan.
  - **R-value & takeoffs:** the wall's thermal path is core + per-face lining; lining areas
    roll into the finish takeoff tier exactly like `FloorFinish` (#25).
  - **Junctions:** the junction solver wraps linings under the finish-wraps default, so
    lining meets lining at inside corners (the sauna's taped polyiso continuity in the
    existing detail).
  - Bottom/base conditions (the sauna's 6" fiber-cement base course with membrane up-turn)
    are transition content (→ 11b), not schema.
- **Assembly variants — per segment (#35).**

  ```python
  Assembly(tag="EXT-1-BRICK", variant_of="EXT-1",
           substitute={outside_of("membrane"): [Layer(air_gap, inch(1)),
                                                Layer(brick_veneer, inch(3.625))]})
  ```

  Layer-span selectors (`outside_of(name)`, `inside_of(name)`, `layers(a, b)`) substitute one
  contiguous span; **everything else resolves live against the base** — bump the base's CI
  from 2 to 3 layers of 2" polyiso once, and the brick-clad and standing-seam sections both
  follow. Guardrails: a variant must keep the base's STRUCTURE layer (different structure = an
  honestly different assembly, authored as one), and alignment faces resolve through shared
  layers so segments stay structurally aligned even where finished faces jog.
  - **Segment application:** assigning a variant to part of a run auto-splits the wall at the
    boundary (the split op under the #33 remap contract). The node where base and variant (or
    any two assemblies) meet becomes a derived **assembly-change condition** (→ 11b): face
    jogs are computed per layer and surfaced, and a Transition binding is expected where the
    change is intentional — a swap can never *silently* create a discontinuity.
  - Variants are also the fork target for assembly experiments (→ 11b §Fork) — same
    mechanism; the `active` flag decides what builds.

Whole-assembly swaps (2x4 partition → staggered-stud) are neither of these — walls are simply
re-pointed (this wall, this contiguous run, or select-same bulk swap — → 21b) and the graph
re-resolves. **The cascade is the harmony contract** stated at the top of this doc — which is
also the working loop the product assumes: tune assemblies, tune floorplans, confirm in 3D,
then layer in fixtures/electrical/HRV.

## Workpackages

- **WP1.4 Topology + junction solver + vertical stacking.** Node graph, L/T/X junction
  resolution per layer under `JunctionPolicy`, alignment offsets, polygonal wall bodies; the
  **vertical stacking pass** (#43: datum projection, stack-edge derivation, `stacks_on`
  tiebreaker); emits derived boundary conditions keyed for Transition matching
  (assembly-change nodes, wall↔foundation, wall↔slab, **storey-stack, stack-width-change**;
  wall↔roof activates with M3 roofs); resolves per-face linings into the layer polygons;
  produces Assembly/VerticalInterface records and applies selected pre-resolve
  ConstructionRules (#44/#45). *Tests:* retain the WP0.1 eave, basement, and width-change
  fixtures as golden slices/interface reports, including CI and lining parameter sweeps.
  *Tests:* golden-image matrix enumerating junction cases (L/T/X × alignments × lining
  overrides) as snapshot tests, **plus a stacking matrix** (aligned / width-change / setback /
  ambiguous-needs-tiebreaker × datum choices) asserting derived stack edges and emitted
  condition keys. *Done when:* the demo plan resolves with zero silent gaps and
  `haus explain --transitions` lists its conditions.
- **WP1.4b Wall framing solver.** Stud layout, plates, king/jack/cripple + header generation
  at openings, corner conditions from junction output; deterministic child uids; masonry
  walls take the `MasonrySpec` quantity path (no members). Level wall tops only — the
  raked-top/rafter arm (§Framing solver above) lands with M3 roofs (→ 30 WP3.11). *Tests:* golden matrix (spacing ×
  opening widths × corner types); **< 200 ms whole-house budget asserted in CI** from this WP
  onward. *Done when:* the demo plan's framed member list feeds both the IFC emit and a stud
  count that matches a hand count.
- **WP1.5 Room derivation + finish tier.** Shapely polygonize face extraction, seed claiming,
  storey-soffit overlap subtraction; `FloorFinish` polygons derived from claimed faces with
  `FinishZone` overrides; wall-lining tier resolution (room clear faces offset by per-face
  lining; lining areas join the rollup — feeds WP2.8 takeoffs); per-material area rollup; the
  **zero-gap assertion** that every Room's clear-face polygon touches the interior faces of
  its bounding walls (#41 — the space-boundary-closure requirement future energy-modeling
  exporters need). *Tests:* fixture plans per failure mode (unclosed loop seed, overlapping
  claims, lining on a non-bounding wall), zero-gap property test across the demo plan.
  *Done when:* rooms render tinted in the (M2) UI from `model.json` data produced here.

## Risks owned

- **Risk 2 — junction/topology solver math.** Mitigation pattern: shapely for all boolean
  work; the WP1.4 golden matrix *is* the spec — every supported junction case is a pinned
  image; `JunctionPolicy` keeps the rule surface a closed enum rather than per-node
  configuration.
- **Risk 6 — framing solver in the hot path.** Mitigation pattern: members are plain records
  (`FramedMember(profile, placement, length, parent_uid, child_key)`) until emit; no geometry
  kernel in the solve; CI-asserted latency budget; single solver feeding IFC, 2D cuts, UI,
  and BOM so there is exactly one implementation to optimize.

## Open questions — resolved in this doc

- **Junction per-assembly override policy** → §Junction policy (`JunctionPolicy` enum,
  default `STRUCTURE_BUTTS_FINISH_WRAPS`, no per-node overrides in M1).
- **Vertical datum default + stack derivation rules** → §Vertical stacking (sheathing-ext
  default, tolerance `inch(0.5)`, min overlap `ft(2)`, derived edges, `stacks_on`
  tiebreaker).
- **Wall height default** → §Wall topology (`top` defaults to underside of the FloorSystem
  above; explicit `Length` or `ToRoof` otherwise).
