# The analytical model — one graph, four readers

**Status: IN PROGRESS (2026-09-12).** The physical enrichment shipped first — `haus handoff`'s
IFC carries section profiles, engineering records and a bar schedule
(`docs/handoff-bundle-format.md`). This plan is the next step: what an engineer needs to
**load the engineered work into their own software in one click** and re-run it, instead
of re-modelling the building from the drawings.

The 2026-09-11 version of this document was a design and said so, gated on two things: an
oracle, and a consumer somebody had actually opened. Both gates are now in the plan itself
(§5), and the owner made the three decisions the design was waiting on (§1).

## 1. Owner decisions, 2026-09-12

1. **Scope is the engineered items plus their load path.** Every member a record names,
   everything it bears on down to the footing, and everything that bears on it. A few
   hundred elements a PE can read, and the same things the calc sheets cover. Not the
   whole 15,000-member frame: a review scope buried in studs and blocking is not a review.
2. **Fixity and releases are derived and claimed.** The earlier draft said "authored, never
   inferred". The owner's goal is a *full PE output, just without the stamp* — every
   structural claim the review needs is modelled and stated — so the engine derives a
   column's base fixity from the same fact `deck_post` already grades on (`_Pier.lateral_
   system`: no brace, no wall, therefore the columns are the lateral system and are fixed)
   and says so in a `basis` string beside the claim. What cannot be derived is listed in
   `gaps`, in words. Nothing is silently defaulted.
3. **An open FE solver is the oracle, and later a calculation engine.** PyNite (3-D frame
   FE, textbook-tested CI) is a `dev` and `fea` extra. A test reads the exported model
   back, solves it, and checks reactions against the hand-worked notes. The owner wants a
   Python FEA in the main calculations as a follow-on; the graph below is the input it
   will consume, which is why it is format-neutral.

## 2. Consumers, verified before designing against them

| Tool | Reads | Verified how |
|---|---|---|
| SAP2000 / ETABS | IFC4 structural analysis view: `IfcStructuralAnalysisModel`, curve/surface members, point connections with `IfcBoundaryNodeCondition`, load cases/groups, linear/point/planar actions **when connected to a structural item**, `IfcMaterialProfileSet`, parametric rectangle/circle profiles. Not `IfcRelAssignsToProduct`, not `IfcTopologyRepresentation`. | CSI Technical Note *IFC4 Import and Export* (S-TN-IFC-001), entity tables pp. 2–12 |
| Bonsai 0.8.3 (Blender 4.2, installed on this machine) | `bim/module/structural`: analysis models, curve/surface members, point connections, boundary conditions, load cases, linear/point actions | module source, `tool/structural.py` |
| RISA-3D | **No IFC.** DXF: `LINE` → member, `POINT` → node, layer name → section set (import option), units chosen on import, rotate-to-Y-up option | RISA help, *DXF Files* |
| ForteWEB / WoodWorks Sizer / Enercalc | Nothing. Single-member tools a PE types into | vendor pages |
| PyNite | Its own Python API | installed, 3.1.0 |

## 3. The design

```
typehaus/analytical/            LEAF — imports model/resolve/quantities/engineering/wind,
  graph.py                      never checks/takeoff/emit (tests/test_package_leaves.py)
  build.py  scope.py  members.py  supports.py  loads.py  materials.py
  pynite_map.py  solve.py       SI graph -> lb/in PyNite inputs; in-process solve
emit/ifc/analytical.py          IfcStructuralAnalysisModel + members + connections
emit/ifc/analytical_loads.py    load cases, actions, combinations
emit/ifc/lowlevel_units.py      FORCE / PRESSURE / MASS + linear/planar force units
emit/draw/dxf_structure.py      3-D centreline DXF for RISA
emit/analytical/pynite_script.py  self-contained .py that rebuilds and solves the model
emit/analytical/members_csv.py    one row per member, loads by case, for single-member tools
cli/cmd_analysis.py             `haus analysis` — the four files, and --solve
```

- **One graph, four readers.** `graph.py` is a format-neutral `AnalyticalModel` — nodes,
  members (with the same `CrossSection` the geometry was built from), supports, load cases,
  member/node loads, combinations, `assumptions`, `gaps`. The IFC, the DXF, the CSV and the
  PyNite script all read it and nothing else, so they cannot disagree about which node a
  beam lands on. Same reason the physical IFC shares one `IfcMaterialProfileSet` between the
  geometry and the analytical member.
- **Loads are what the records consumed**, never a second derivation where a record has the
  number: `roof_beam`'s `uniform_load`, `deck_post`'s dead/live and wind base moment (applied
  as the storey shear at the column top so the solve reproduces the moment), the guard's
  200 lb as its own case. Each load's `source` names the item and the quantity.
- **Every analytical entity is machine-minted and pinned** through
  `emit/ifc/lowlevel_guids.py`, or `haus handoff`'s manifest stops meaning anything.
- **Rigid-link convention.** A post's top node sits on the beam centreline it bears on; the
  beam end there is moment-released. Stated in `assumptions`, printed in every export.
- **Not in v1:** retaining walls and slabs as `IfcStructuralSurfaceMember`. They are listed
  in `gaps` by item id. The retaining items' oracle is a free-body note, which a surface
  model would not check better than the hand pass does.

## 4. Where it lands

`haus handoff` adds `analysis/` — `model.pynite.py`, `members.csv`, `centreline.dxf` —
and the structural analysis view rides inside `model.ifc` (SAP2000's import form picks the
view; Bonsai shows both; the `IfcRelAssignsToProduct` links need one file). The README
gains "Open it in your software", one paragraph per tool. `haus analysis houses/<name>`
writes the same four files standalone and `--solve` prints reactions beside the records'
demands.

## 5. The two gates, now inside the work

1. **Oracle.** `houses/catlin/notes/analytical_model_basis.md` states the boundary
   conditions and load cases as claims and hand-solves the balcony bent: 614 lb E-W storey
   shear over four fixed columns, 153.4 lb each at the deck plane, 9.03' lever, **1,385
   lb-ft** per base — the number `balcony_moment_columns.md` §2b already carries.
   `tests/test_analytical_oracle.py` solves the exported graph in PyNite and reproduces it,
   plus each pier's gravity reaction against its record's `dead_load + live_load`.
2. **A consumer that was opened.** `scripts/verify_bonsai_import.py` now counts the
   analysis model's members and connections, and is run headless against
   `out/handoff/model.ifc` with the Blender 4.2 + Bonsai 0.8.3 on this machine.
3. **Byte-determinism** for the IFC, the DXF, the CSV and the script: two-run equality
   tests on each.
