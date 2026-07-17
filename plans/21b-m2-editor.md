# M2 — Editor Features: Macros, Driven Dimensions, Intelligence

**Purpose:** the interactions that make the editor *smart* — room macros, editable
dimensions, the drafting command set with its identity-preserving mutation contract, and the
M2 slice of the editor-intelligence backlog. Common rule inherited from (→ 20 §FastAPI
server): **every number derives from `model.json` — the UI never re-measures geometry.**

## Room macros — rubber-band, split, heal

Server-side ops, same PATCH/undo path as any edit (→ 20 §Write safety):

- **Rubber-band stretch:** drag a wall perpendicular to its axis → its two nodes translate,
  every connected wall stretches/shrinks, dimensions live-update during the drag; openings on
  stretched walls keep their `from_node` anchor (or flag if they no longer fit — a
  framing-bumper/integrity finding, never silent). Implemented as one `move_nodes` op so undo
  is atomic.
- **Split:** draw a partition across a claimed room face → the engine inserts the wall
  (default interior assembly, confirm-badge per the standard flow), splits the face, and
  prompts to claim the two resulting rooms; T-junction nodes heal into the existing walls
  automatically.
- **Heal/merge:** delete a shared wall → the two rooms' faces merge (the surviving Room claim
  wins by prompt), stranded collinear nodes are removed, and the neighbors' wall segments
  fuse back into single edges. "Heal" is the inverse of "split" and round-trips in the op
  journal.

## Driven dimensions (#26) — the missing interaction, without a solver

Every dimension on the canvas is editable: tap `12'-6"`, the ft-in keypad opens, type
`13'-0"`, and the wall moves. The rule system is deliberately tiny:

- **Dimensions reference elements, not coordinates:** a dimension is stored as
  `(element uid, face role)` per end (e.g. `W-101 / face:stud-int`), resolving to node sets
  via the (→ 11 §Wall topology) alignment — so dimensions survive moves, resizes, and
  split/join remaps like any other reference. This same `AnchorRef` scheme is reused by
  overlay anchors (→ 11b) and the drawing IR (→ 20) — one resolver, one failure surface.
- On edit, the engine picks the **less-anchored side** to move: fewer connected walls loses;
  exterior beats interior; a tie moves the side farther from the plan origin. Users are never
  asked to internalize that rule — **the proposed result is ghosted before commit**: "moves
  the east wall 6" → **[Apply] [Move west side instead]**". The heuristic is just the default
  ordering of a two-choice preview. The commit is one ordinary transactional `move_nodes` op
  — journaled, undoable, rubber-banding connected walls exactly like the stretch macro (it
  *is* that macro with a typed delta).
- **Whole node sets move, never one endpoint:** a dimension edit translates the complete node
  set of the moving side rigidly — an op that would rotate or distort a wall (one endpoint
  pinned, the other free) is rejected with a message, not "solved".
- The only persistent "constraint" is a per-node **anchor pin** (📌 toggle; stored as
  `anchored=True` in source): pinned nodes never move as a side effect, so the user controls
  which side gives way by pinning the other. Editing a dimension between two pinned sets is a
  rejected op with a clear message — never a solver deadlock, because there is no solver.
- Openings on affected walls keep their `from_node` anchors; no-longer-fits becomes the
  standard framing-bumper/integrity finding.

## Drafting command set (WP2.4c)

High-frequency actions the room macros don't cover, each an ordinary transactional patch
through the same journal:

- **Clipboard:** copy/paste selection (fresh uids minted on paste, tags auto-suggested);
  duplicate wall parallel at typed offset (new nodes, same assembly).
- **Transforms:** mirror selection about an axis; rotate selection 90°; move selection by
  exact typed distance/direction.
- **Layout:** align selected elements (node coordinates or opening centers); distribute
  evenly along an axis.
- **Topology (junction-solver-backed):** extend/trim wall to intersection with another wall's
  axis (inserts the shared node); split wall at a point (one edge → two edges + midnode,
  openings re-hosted by position); join collinear walls (inverse of split — same op the heal
  macro uses).
- **Selection:** select-same (all elements of the same kind, or all walls with the same
  assembly) — which is also how bulk assembly swaps work.

All of these operate on the node graph and re-run the junction solver — none introduce
geometry math in the client (the "server owns all geometry" rule holds).

## Mutation contract (#33) — identity through surgery

Split, join, trim, and the macros can invalidate far more than geometry: hosted openings,
dimensions, details, notes bindings, footing `under=` refs, roof/joist `bearing_refs`, room
claims, `stacks_on` tiebreakers (#43), and IFC diff continuity all point at uids. So every
topology-changing op returns, alongside its patch ops:

```python
MutationResult(
    ops=[...],
    reference_remap={old_wall_uid: [surviving_uid, new_uid],   # split: 1 → 2
                     old_node_uid: surviving_node_uid},         # merge: 2 → 1
    deleted_uids=[...],
    warnings=[...],   # e.g. "opening D-103 re-hosted to W-101b; note N-4 now ambiguous"
)
```

- **Deterministic survivor rules:** on **split**, the original uid stays with the segment
  attached to the wall's first node (`a`-side); the other segment gets a fresh uid. On
  **join**, the survivor is the wall contributing the joined edge's `a` node. Openings
  re-host to whichever segment their position falls in, keeping their own uids. The rules are
  boring on purpose — predictability beats cleverness here.
- **Remap is processed, not broadcast-and-hoped — registry API resolved:** every element kind
  that can hold a reference registers a remap handler with the element registry (→ 10
  §Schema headroom):

  ```python
  RemapHandler = Callable[[ElementT, ReferenceRemap], ElementT | None]  # None = unchanged

  @registry.remap_handler(Opening, ref_fields=("host",))
  def remap_opening(el: Opening, remap: ReferenceRemap) -> Opening | None: ...
  ```

  The **CI completeness test** introspects every registered element kind's pydantic fields
  for reference types (`Ref[...]`, `tuple[Ref, ...]`) and asserts each such field is named in
  some handler's `ref_fields` — no reference-bearing field can lack one. Dangling refs after
  remap are integrity errors with the mutation named.
- **Undo restores exact uids:** the journal's inverse op carries the full pre-mutation
  payload including original uids — undoing a split brings back *the* wall (same uid, same
  GUID, diff continuity intact), never an equivalent-shaped stranger.

## Editor intelligence — M2 features

(The M3 features — sun indicator, space dashboard, service filters, clearance overlays,
underlays, roof designer — are in → 30; the M5 building-science dashboard is in → 50.)

1. **Extents & dimensions HUD (WP2.4):** persistent readout of overall building
   width/depth/height (X, Y, Z) and current-storey extents, each split **structural**
   (face-of-sheathing envelope) vs. **open space** (clear interior). Clicking a value flashes
   the governing dimension chain on the canvas.
2. **Stair designer (WP2.13) — flagged major value-add:** stairs are the hardest element for
   an inexperienced designer. Floor-to-floor rise is *derived, never typed* — the storey
   elevation delta already includes joist depth + subfloor + finish floor from the floor
   assembly (→ 11 §Floors), which is exactly the part beginners get wrong. The panel
   live-solves riser count/height and tread depth against code (MN/IRC R311.7: riser ≤ 7¾",
   tread ≥ 10", headroom ≥ 6'-8"), shows total run and landing requirements, checks headroom
   against the floor opening above, and writes back a valid `Stair(...)` declaration.
   Out-of-range configurations render red with the violated code ref — never silently
   accepted.
3. **Takeoff dashboard (WP2.8) — the kept catlin feature (#25/#47):** a HUD panel totaling
   framing member counts (studs/plates/headers/joists by size), sheet goods (sheathing,
   drywall, subfloor), insulation panel/batt area by assembly layer, and per-material
   floor-finish areas (carpet, tile — from the → 11 finish tier). Every number derives from
   the resolved framing solve + finish tier; clicking a line highlights the counted members
   on the canvas. Same data ships as the BOM/takeoff sheet in the permit set and
   `haus takeoff --json`. **Costs (#28):** if the house carries a `prices.toml`
   (user-supplied $/unit, each entry optionally a low–high range), the dashboard, sheet, and
   CLI multiply through and show dollar ranges with an "own prices, not estimates" label;
   absent the file, no dollars appear anywhere. The panel labels quantities as **resolved
   design quantities**, shows active waste/cut allowance separately, and lists excluded
   procurement items (for example fasteners and sealants unless a ConstructionRule explicitly
   models/counts them). It never represents a quantity as a purchase order.
4. **Assembly swap preview (WP2.4):** swapping an assembly offers three scopes — this wall,
   this contiguous run (auto-split at the chosen boundary), or select-same (every wall with
   the assembly) — with a ghost preview before commit: thickness delta, which finished faces
   move, which dimension chains change value, and **which new boundary conditions the swap
   creates** (→ 11b — the "did I just make a discontinuity?" answer, shown before it
   happens; storey-stack re-keying included per #43). One journaled op-set; undo restores
   everything.
5. **Variant compare view (WP2.14):** side-by-side canvases with linked pan/zoom over the
   active and a forked variant (→ 11b §Fork), element-level delta list, takeoff/R-value
   deltas ("variant B: +142 sf drywall, kitchen +18 sf"), promote/discard actions.
6. **Slice manager (plans M2; sections/details M3):** the list of all views (→ 11b §Slices)
   — plan slices per storey, sections, details; draw a cut line on the plan to create a
   section/detail; per-slice annotation show/hide/placement; the 3D panel renders slice
   planes as widgets.

Model prerequisites (already in → 10 §Element model): `FurnitureType`/`FixtureType` library
entries (footprint polygon, height, clearance zones, `storage`, `needs`), `Furniture`
placement element (optionally emitted as `IfcFurniture` at core LOD), `Room.conditioned`, the
`Service` enum. Furniture types are prime `library/` contribution-seam content
(→ 02 §Git topology).

## Workpackages

- **WP2.4b Room macros.** Rubber-band stretch (atomic `move_nodes` op, live dimensions,
  opening refit findings), split (partition insert + face split + claim prompts), heal/merge
  (wall delete + node cleanup + edge fusion) — all through the standard PATCH/undo journal.
  Includes the **conflict banner** (stale-source detection + element-level summary + reload,
  #30). *Tests:* Playwright macro round-trips; op→undo→redo file identity.
- **WP2.4c Driven dimensions + drafting commands.** Editable dimensions (uid+face-role
  references, ghost preview with the move-other-side alternative, rigid node-set moves,
  anchor pins); the full drafting command set; split/join/trim implement the
  **`MutationResult` remap contract** with the registry completeness test. *Tests:* assert
  op→undo→redo round-trips the file **and restores exact uids**; rejected-op cases (two
  pinned sets, distorting move) produce messages, not writes.
- **WP2.8 Floor framing + framed IFC emit + takeoffs.** Joist generation from `JoistSpec`
  (bearing spans, trimmers/headers at `FloorOpening`s — completes the → 11 solver begun in
  WP1.4b); framed-LOD IFC emission (members aggregated under parents via `IfcRelAggregates`,
  parent GUIDs stable across LODs); **BOM/takeoff rollup** (member counts, sheet goods,
  insulation + finish areas), `haus takeoff --json` (+ `prices.toml` dollar ranges), takeoff
  dashboard, takeoff sheet in the sheet set; storey-`Soffit` drop framing generation (#40).
  *Done when:* the dashboard's stud count matches the framed IFC's member count exactly.
- **WP2.9 First MN code checks + preferences.toml.** The starter five + PGH envelope warns
  (→ 12 §Checks); **profile rigor scaffolding per #32** (citation/effective-date/coverage
  fields, per-rule fixtures, the constrained "N of M encoded rules" wording); first
  geometry-only advisory checks (windowless habitable rooms, unique door/window size counts,
  door-swing collisions — work triangle waits for M3 fixtures).
- **WP2.13 Stair designer panel** (feature 2 above): derived floor-to-floor rise, live
  riser/tread/headroom solve against R311.7, writeback of a valid `Stair(...)` declaration.
- **WP2.14 In-plan variants + compare view** (→ 11b §Fork): fork an assembly or storey
  (`variant_of` + `active` + `forked_from`), one-active integrity check, side-by-side compare
  canvases with linked pan/zoom + element/takeoff deltas, promote-with-uid-remap (#33
  machinery), `haus compare`.

## M2 acceptance

A user draws a small house entirely in the UI — closed loops enforced, every wall carries an
assembly, **floorplans showing true studs/headers and layer hatching, the 3D panel showing
framed walls under the Nordic preset** — while the plan file stays human-readable with
comments intact after 50 UI edits; a rubber-band stretch and a room split/heal round-trip
through undo; **typing a new value into a canvas dimension moves the correct wall** (ghost
preview shown, anchor pins respected) and undoes cleanly; **a wall split then undone comes
back with its original uid and its openings correctly hosted**; a patch sent against a stale
revision hash is rejected with 409 and the conflict banner appears after an external VSCode
edit; the takeoff dashboard's stud count matches the framed IFC's member count exactly;
**swapping an interior wall's assembly to a wider one visibly widens the wall on the plan and
updates every dimension chain referencing its faces** (with the new-boundary-condition
warning shown before commit); a forked storey is edited, compared side-by-side, and promoted
with original uids restored; the assembly inspector renders the section card for a
just-edited assembly without a manual refresh; Claude edits the same file in VSCode and the
UI hot-reloads; `haus diff` on a Blender-modified copy correctly reports a moved wall and an
added window. **This unblocks designing the catlin floorplans in the UI.**

## Open questions — resolved in this doc

- **`MutationResult` remap-handler registry API** → §Mutation contract (handler signature,
  `ref_fields` declaration, field-introspecting CI completeness test).
