# M2 — Engine Side: Server, Writeback, Drawing IR, Diff, Agent Scaffolding

**Purpose:** M2 closes the loop — a user draws in the UI while Claude edits the same files in
VSCode, and both see one truth. This doc covers the engine half: the server, the write-safety
and undo machinery, the libcst writeback that makes plan files editable state, the 2D drawing
IR with its DXF/PDF writers, the semantic diff, and the agent scaffolding. The UI half is
(→ 21, → 21b).

## FastAPI server (`haus serve`)

- `GET /model` → resolved `model.json` (contract below)
- `GET /model.ifc` → latest core-LOD build
- `GET /checks` → current findings
- `PATCH /plan` → ops `{op: add|update|delete, type, tag, fields}` — fields carry
  authored-unit strings (`"12'-6\""`) which serialize to `ft(12, 6)` in source. `type` spans
  storey elements **and** library objects: `assembly | layer | material` targets (the UI
  assembly editor, → 21b §Assembly editor) ride the same op shape — a `layer` reorder is an
  ordered-list field update on the parent `assembly`; no new grammar, since the dialect printer
  only ever emits keyword-arg constructor calls (§libcst writeback).
- `POST /build`, `POST /undo`, `POST /redo`
- `WS /events` (build done / findings changed / file changed)
- `watchfiles` watches plan source, so edits by VSCode/Claude hot-reload the UI — the
  two-screen workflow is symmetric by design.

### `model.json` contract — resolved

The UI seam, typed on both sides (pydantic model on the server, generated TS types in
`ui/src/engine/types.ts` — generation checked in CI so they cannot drift):

```ts
interface ModelJson {
  revision: string;              // project revision hash — the PATCH /plan precondition (#30)
  units: "imperial" | "metric";
  projectNorth: number;          // true_north angle, radians — sun indicator/north arrow only
  storeys: StoreyJson[];
  libraries: {
    assemblies: AssemblyJson[];  // incl. resolved R-values + card geometry (→ 12 §Assembly card)
    doorTypes: TypeJson[]; windowTypes: TypeJson[];
    transitions: TransitionJson[];
  };
  conditions: ConditionJson[];   // derived boundary conditions + coverage status (→ 11b)
  findings: FindingJson[];       // current check findings
}
interface ElementJson {
  uid: string; tag: string; kind: ElementKind;
  editable: boolean;             // false for params/-generated elements
  provenance: { file: string; line: number } | null;   // jump-to-VSCode affordance
  geometry: GeometryJson;        // resolved, SI meters, project-north frame
  fields: Record<string, FieldJson>;  // authored fields; FieldJson carries the
}                                     //   authored-unit string for display + writeback
// Walls additionally carry: layerPolygons (per layer, for the framed floorplan cut),
// framingMembers (instanced primitive refs, → 21 §Nordic preset), stackEdges (#43).
```

Every number the UI shows derives from this payload — **the UI never re-measures geometry**
(the rule all → 21b intelligence features inherit).

## Write safety (#30) — because the files are the state, writes get database manners

A patch is not a file operation: one op set can touch a storey file, `assemblies.py`, and an
annotation at once. So the transaction unit is the **project**, coordinated by one
server-side mutation path:

1. Every `PATCH /plan` carries the **project revision hash** — a hash over all source inputs,
   served with `model.json`. Mismatch → `409`, no write, client re-syncs.
2. The coordinator takes the project mutation lock, applies all ops to a **staged in-memory
   CST tree**, and parses + validates the entire staged project before anything touches disk.
3. Affected files are then replaced one by one — each an **atomic temp + fsync + rename**,
   with the on-disk hash **rechecked immediately before each replace** (VSCode and Claude
   don't honor advisory locks); any mismatch aborts and restores from the pre-commit
   snapshots, which are retained until the commit completes.
4. The **journal entry (one per patch, with inverse ops) is recorded only after every file
   lands**, and watcher-triggered rebuilds are suppressed until the single project-commit
   event fires. Room macros and driven dimensions (→ 21b) get multi-file atomicity for free.

**Conflict UI:** when the source changed under the editor (external-edit hash mismatch — the
same event that seals the undo journal), the canvas shows a banner: what changed on disk
(element-level summary via the provenance map), with **reload** as the only mutation path.
In-flight local edits are rejected by the precondition, never silently merged over.

## Undo/redo — server-owned, because the file is the state

Ctrl+Z in the browser cannot be a client-side state pop when the truth lives in `main.py`.
The server keeps a per-session **op journal**: every applied `PATCH /plan` op is recorded
with its computed **inverse op** (add↔delete with the full element payload; update stores
prior field values — cheap because ops are element-level). Undo/redo = `POST /undo|/redo` →
apply the inverse/original through the *same* libcst writeback path as any edit, rebuild,
push. Consequences that fall out correctly: undo works identically from any client; the file
on disk always matches what the UI shows; and an **external edit** (VSCode/Claude, detected
by watchfiles content hash ≠ hash after our last write) **truncates the redo branch and seals
the journal up to that point** — you can't undo "through" someone else's edit, which is the
honest behavior. Journal is in-memory per serve session; durable history is git's job.

**Performance note:** updates apply at the **element level** — rebuild the one changed frozen
element and re-resolve, never deep `model_copy(update=…)` through nested frozen Pydantic
trees, which is a known v2 hot-loop bottleneck. The flat PATCH-ops design already enforces
this; keep it that way.

## libcst writeback + `haus fmt`

- Op application assigns uids on element creation (→ 10 §Stable IDs); comments and formatting
  in untouched statements are preserved by construction (libcst round-trips them).
- **`haus fmt` canonical style is merge-friendly by construction** (→ 02 §Git topology):
  exactly one element declaration per statement, one statement per line-block, stable
  ordering (grouped by kind, then tag); assigns missing uids as an auto-fix.
- The dialect grammar (→ 10 §Plan-source dialect) is what keeps this tractable: no operators,
  no control flow — the printer only ever emits constructor calls with keyword arguments.

## Drawing IR — one 2D scenegraph, two writers

A small 2D **drawing IR** generated from `ResolvedModel`, with two writers: **ezdxf** and
**matplotlib-PDF**. Guarantees DXF and PDF agree; the team already knows matplotlib deeply.
(Fallback if we change our minds: ezdxf's `drawing` add-on can render DXF→matplotlib
directly.)

### IR node vocabulary — resolved

```
IRNode = Polyline(points, layer, lineweight, linetype, closed)
       | Hatch(boundary, pattern, scale, angle, layer)          # material hatches, insulation
       | Text(anchor, content, height, rotation, style, layer)
       | ArchDimension(kind=linear|aligned, ends=(AnchorRef, AnchorRef), offset, layer)
       | Leader(anchor: AnchorRef, text, layer)
       | Symbol(name, insert, rotation, scale, layer)           # door swings, fixtures,
       | Viewport(sheet, window, scale, target_slice)           #   north arrow (M3 sheets)

AnchorRef = (uid, face_role) | NamedPoint                       # the → 21b dimension scheme;
                                                                #   overlay anchors reuse it
```

- The IR is **pure data** (frozen pydantic records — no matplotlib objects, no ezdxf
  handles), so golden tests snapshot it as JSON before any writer runs.
- **Writer obligations:** the DXF writer maps `layer` → AIA names, `ArchDimension` → real
  DXF DIMENSION entities with the architectural DIMSTYLE, and stamps uid/tag XDATA; the PDF
  writer draws to sheet scale with the title block. Neither writer computes geometry — all
  placement math happens IR-side, once.
- **Every 2D view is a `Slice` (→ 11b, #36):** floorplans are the auto-scaffolded plan slices
  (cut 4' above each storey floor); wall polygons/openings projected from the IR, **stairs
  drawn as the standard plan symbol** (tread lines + break/direction line + `UP N R` label,
  from the resolved stair geometry — → 10 §Element model) — never redrawn from scalar specs
  (the old failure mode). **The cut slices real framing
  (→ 11 §Framing solver):** stud sections, insulation hatch, sheathing and drywall linework
  per assembly layer — the signature framed-floorplan look is the default everywhere, with
  the per-sheet `simplified_poche` toggle for jurisdictions that prefer gray poché.
- **Dimensions:** auto-generated chains from the node graph + grid (overall → grid line →
  opening centers), plus explicit `Dimension` annotations in plan source for anything the
  auto-dimensioner shouldn't guess.
- **DXF conventions:** AIA CAD Layer Guidelines (`A-WALL`, `A-WALL-PATT`, `A-DOOR`,
  `A-GLAZ`, `A-ANNO-DIMS`, `A-ANNO-TEXT`, `A-AREA-IDEN`, `S-FRAM`, `C-TOPO`/`C-PROP` site).
  Model space in **inches**, `INSUNITS=1` (configurable to mm). Paperspace layout per sheet,
  viewports at standard scales, architectural DIMSTYLE (tick marks, ft-in text). uid/tag in
  XDATA per (→ 10 §Stable IDs).
- Sheet composition, schedules, and the full permit set are M3 (→ 30 §Sheets); M2 ships one
  floor-plan sheet to prove the writer pair.

## Diff / architect round-trip

`haus diff <external.ifc>` compares against the deterministic baseline (rebuilt from
source):

1. **Match by GlobalId** (uid-derived GUIDs survive tools that preserve GUIDs — most do; and
   because identity is the immutable uid, retags and storey moves on our side never break
   matching).
2. **Fallback matcher** for unkeyed/new elements: cost matrix over (IFC class, storey,
   centroid distance, oriented-bounding-box dims, axis direction), solved with
   `scipy.optimize.linear_sum_assignment` (Hungarian).
3. **Replace detection (same pass, no new machinery):** after keyed matching, the leftover
   "deleted" and "added" sets go through the *same* Hungarian cost matrix — a delete+add pair
   of the same IFC class in near-identical bounding boxes reports as **replaced (was W-101)**
   with the attribute delta, instead of two unrelated changes. Matters because some architect
   tools regenerate elements with fresh GUIDs; below a confidence threshold it stays
   delete+add, with the near-miss candidate noted in `diff.json`.
4. Classify: added / deleted / **replaced** / moved / resized / attribute-changed, deltas in
   **authoring units** (`W-101 moved 3 1/2" north`; `WIN-204 widened to 3'-0"`).

Output: human table + `out/diff.json` (structured per-change deltas + match confidence).

**Agentic merge — `/import-review` skill:** Claude reads `diff.json` + plan source, walks
through accept/reject per change, applies accepted changes as plan-source edits (same libcst
writeback path the UI uses), rebuilds, re-diffs until the report is empty or intentionally
deferred. Rejections are logged to a decision file for the reply to the architect.

## Agent scaffolding

- **CLAUDE.md:** project map; invariants (never edit `out/`; always `haus build && house
  check` after edits; all dimensions via quantity constructors, never bare floats; tag
  conventions; editable-dialect rules; read `brief.md` **and** `preferences.toml` before
  proposing designs; **look at what you made** — `haus render` after spatial edits); command
  crib sheet. Keep this concise, hints rather than full descriptions.
- **Agent eyes (#52) — the loop is edit → build → check → *look* → fix:** `haus render
  --view plan|section|3d` emits headless PNG/SVG snapshots (plan/section straight from the
  drawing IR, 3D offscreen from the #51 glTF artifact) that Claude reads natively — spatial
  judgment ("the hallway is awkward", "the massing works") joins the text-only findings loop.
  `haus ls --summary` emits a compact whole-plan digest (storeys, rooms + areas, wall runs +
  assemblies, open findings) sized for a context window, so a fresh session re-orients from
  one command instead of re-reading plan files.
- **Skills** (`.claude/skills/`):
  - `/add-room` — nodes + walls + room claim + run checks
  - `/add-assembly` — Assembly (or variant) + **render the section card** (→ 12) + detail
    Slice/Transition stubs + notes + R-value check vs preferences. Shares one writeback path
    and artifact set with the UI assembly editor (→ 21b §Assembly editor), so UI- and
    agent-authored assemblies are indistinguishable in source and diff.
  - `/import-review` — the diff flow above
  - `/permit-check` — full check suite + sheet-completeness audit, summarize gaps
  - `/port-detail` — migrate an old matplotlib detail to the drawing IR (M3 helper)
- **preferences.toml schema:** `[project]` (display_units="imperial", jurisdiction="mn"),
  `[envelope]` PGH targets (→ 12 §Checks), `[structure]` (preferred members, spacing,
  species/grade), `[style]` (e.g. "simple gable massing"), `[gc_notes]` free text. Read by
  checks **and** by Claude.
- **`brief.md` — the design brief (#18)** (scaffolded by `haus new`, lives beside
  `preferences.toml`): YAML frontmatter for the machine-readable fields + prose sections for
  humans and Claude. Template sections: **spatial program** (rooms, target areas,
  adjacencies), **budget level** (tier + optional hard cap), **climate** (zone, e.g. MN 6A/7
  — sets envelope expectations), **style** (massing, references), **accessibility** (e.g.
  aging-in-place / ADA-ish clearances → feeds door-width and turning-radius checks),
  **phasing** (build now vs. rough-in for later), **must-haves**, **dislikes**, **priorities**
  (ranked tradeoffs, e.g. "envelope > sqft > finishes"). Division of labor: **brief = intent**
  (what/why — read by Claude before proposing anything; included in the `--handoff` bundle so
  the architect gets the why, not just the geometry), **preferences.toml = targets**
  (machine-read thresholds consumed by checks). Structured brief fields that map to checks
  (climate zone, accessibility standard) are copied into preferences by `haus new` so checks
  read exactly one file.

## Workpackages

- **WP2.1 FastAPI server.** Endpoints above, watchfiles, WebSocket events. *Done when:* an
  external file edit round-trips to a UI reload event in < 2 s.
- **WP2.2 libcst writeback.** `PATCH /plan` op application (uids on creation); **write
  safety per #30** (the four-step coordinator above); op journal with computed inverse ops +
  `POST /undo|/redo` + external-edit journal sealing; `haus fmt` incl. missing-uid auto-fix
  and the merge-friendly canonical style. *Tests:* property-based — random op sequences →
  parse/emit/parse fixpoint; comments preserved; op→inverse→op is an identity on the file.
  *Done when:* 50 scripted UI edits leave a human-readable file with comments intact.
- **WP2.6 DXF floorplan export.** Drawing IR core + ezdxf writer, AIA layers, auto dimension
  chains, architectural dimstyle, XDATA tags. *Tests:* IR JSON goldens; DXF opens in a second
  CAD tool with correct layers/units (→ 02 §Verification).
- **WP2.7 Minimal PDF sheet.** Title block + one floor-plan sheet via the matplotlib writer.
  *Done when:* PDF and DXF of the same slice visibly agree.
- **WP2.10 `haus diff` v1.** GlobalId matcher + Hungarian fallback + replace detection +
  diff.json + human table. *Tests:* fixture pairs per change class; a Blender-modified copy
  reports the known edit set.
- **WP2.11 Agent scaffolding v1.** CLAUDE.md complete, `/add-room`, `/import-review` skills;
  `haus render` + `haus ls --summary` (#52) wired into the skills so mutating edits end with
  a rendered snapshot. *Done when:* Claude adds a room to the demo plan via the skill, checks
  pass, and the skill's final output includes the rendered plan snapshot.
- **WP2.12 CLI complete.** `new | serve | print | diff | fmt | render` join the M1 set
  (→ 02 §CLI).

## Risks owned

- **Risk 1 — libcst writeback complexity** (the novel part). Mitigation pattern: the dialect
  grammar (→ 10) keeps the CST surface tiny; WP2.2's property-based round-trip suite;
  `haus fmt` normalizer; worst-case degradation = regenerate one element's statement
  (losing only that statement's comments).

## Open questions — resolved in this doc

- **`model.json` contract** → §FastAPI server (typed payload; CI-checked TS generation;
  "UI never re-measures" rule).
- **Drawing-IR node vocabulary** → §Drawing IR (seven node kinds, pure-data records,
  writer obligations).
