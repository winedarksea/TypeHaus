# The analytical IFC, and a centreline DXF — designed, not built

**Status: DESIGNED, NOT IMPLEMENTED (2026-09-11).** The physical enrichment shipped —
`haus handoff`'s IFC carries section profiles, engineering records and a bar schedule
(`docs/handoff-bundle-format.md`). This is the next step and it is written down rather than
written, deliberately: an IFC4 structural analysis view has no oracle in this repo and no
consumer any test here can open, so building it untested would produce a file that looks
authoritative and has been checked by nobody. That is the failure mode the whole engineering
lane exists to avoid.

What follows is the design, in enough detail to implement against.

## Why an analytical model at all

The physical IFC says *this beam is a 3-1/2" x 11-7/8" glulam here*. It does not say *this
member spans between these two nodes, pinned at one end and fixed at the other, under these
load cases*. An engineer wanting to re-run the calculation in their own software currently
re-models the building by hand from the drawings — which is most of the cost of a review,
and every hand re-model is a chance to re-model it differently from what was built.

Consumers, checked before designing anything against them: **Bonsai** reads
`IfcStructuralAnalysisModel` (this is the gate — decision #48 makes Bonsai the reference
viewer). **ETABS** and **SAP2000** import the IFC4 structural analysis view. **RISA reads
no IFC at all**, which is why the DXF in §3 is part of the same design rather than an
afterthought.

## 1. `emit/ifc/analytical.py` (~320 lines)

- One `IfcStructuralAnalysisModel` with `PredefinedType = LOADING_3D`, aggregated to the
  project.
- One `IfcStructuralCurveMember` per beam, column, post, joist and rafter, with an `IfcEdge`
  centreline and **the same `IfcMaterialProfileSet` the physical member carries**. Sharing
  the profile set is the point: two section definitions for one member is how the analytical
  and physical models drift apart.
- `IfcRelAssignsToProduct` back to the physical element, so a reviewer can select a member in
  either model and find it in the other.
- `IfcStructuralSurfaceMember(SHELL)` for foundation walls, retaining walls and slabs.
- `IfcStructuralPointConnection` per bearing, with an `IfcBoundaryNodeCondition` that is
  **fixed or pinned from `pier.lateral_system`** — authored, never inferred. A base fixity
  this engine guessed would be a structural claim, and the balcony's four fixed-base cast
  columns are the whole lateral system: getting that wrong reverses the answer.
- Units: FORCE, PRESSURE and MASS plus the derived linear- and planar-force units, in a new
  `emit/ifc/lowlevel_units.py`. `lowlevel.py` is 562 lines and is not grown.

## 2. `emit/ifc/analytical_loads.py` (~220 lines)

- One `IfcStructuralLoadCase` per source: dead, snow, wind, earth, live.
- The actions come off `EngineeringRecord.inputs` — `uniform_load`, `suction_asd`,
  `active_efp`, `retained_height` — plus `typehaus/wind.py` and `engineering/soil.py`. **The
  loads a calculation actually consumed**, not a second derivation of them; a load case that
  disagreed with the sheet beside it would be worse than none.
- The import direction is settled and must stay so: `emit/ifc` **may** import `engineering`;
  `engineering` **never** imports `checks`. `tests/test_routing_leaf.py`'s AST walk is the
  pattern for a lint if one is wanted.
- Each action's property set names the item id and the load combination, so an action traces
  back to the sheet that produced it.

## 3. `emit/draw/dxf_structure.py` — the centreline DXF

RISA reads no IFC. A 3-D centreline DXF is what it and most older analysis packages do read:
one `LINE` per member, a layer per kind, and a text entity carrying the profile and the item
id. `ezdxf` is already a dependency and `emit/draw` already writes plan DXFs, so this is the
smallest of the three pieces and probably the first one worth doing.

## What has to be true before any of this is built

1. **An oracle.** Every calculation in this engine is checked against an independent hand
   pass; an analytical model is not a calculation, but the boundary conditions and the load
   cases it publishes *are* claims, and a note has to state them.
2. **A consumer that was actually opened.** "Bonsai reads the SAM" is a statement about
   Bonsai that somebody has to verify by opening the file, the way
   `scripts/verify_bonsai_import.py` already verifies the physical one.
3. **Byte-determinism preserved.** Every entity added here is machine-minted and must be
   pinned by `emit/ifc/lowlevel_guids.py`, or `haus handoff`'s manifest stops meaning
   anything. Add the new relationship types to `_MACHINE_MINTED` in the same commit.
