# `out/handoff/` — the engineering handoff bundle

What `haus handoff` writes: everything a licensed professional needs to confirm this
house's engineered requirements and stamp what they agree with, in one folder, with a
manifest.

```
out/handoff/
  README.md                 the route through the bundle — five minutes, in order
  MANIFEST.json             every file, with its sha256
  engineering.toml.draft    the seal register as a FORM (see docs/engineering-toml-format.md)
  calcs/                    the calculation package, verbatim from `haus calcs`
  calcs.pdf                 the same, flattened and page-anchored — what a seal binds to.
                            The calculations; the per-member appendix tables are in
                            calcs/appendix/ and print into the PDF with `--full`
  notes/                    ONLY the hand-worked notes these records are checked against
  model.ifc                 IFC4, framed LOD, with sections, records, a bar schedule AND the
                            structural analysis view (see below)
  model.glb                 the same building, for a viewer that does not read IFC
  analysis/
    model.pynite.py         the analytical model as a self-contained PyNite script: run it
    members.csv             one row per analytical member, loads by case, for ForteWEB/Sizer
    centreline.dxf          3-D centrelines, layer = section, for RISA-3D
    README.md               which file opens in which tool, and the claims every file makes
out/handoff.zip             --zip: the file you actually send
```

`out/handoff-architect/` is a different bundle for a different reader — drawings, DXFs and
the decision log, written by `haus print --handoff`. Two bundles, two folders, deliberately:
one folder holding whichever ran last is how somebody sends the wrong thing.

## Byte-determinism, and why the manifest depends on it

Two runs over an unchanged model produce identical files. That is the only thing that makes
the manifest worth shipping: a changed sha256 is then a *changed model*, not a re-run, and a
reviewer can tell a regenerated bundle from an edited one.

Getting there took four fixes, all of them in the emitters rather than here. The calc PDF's
`CreationDate`/`ModDate` are pinned. The IFC's STEP header timestamp is pinned, every GUID
ifcopenshell mints for us — relationships, property sets, the site, the building, the
storeys, the systems — is rewritten as a `uuid5` of what it identifies
(`emit/ifc/lowlevel_guids.py`), and the member lists ifcopenshell collects through `set()`
are sorted. Set `SOURCE_DATE_EPOCH` to pin the generation date printed on the cover.

## Only the notes that verify these calculations

`notes/` holds exactly the notes the records' `Oracle`s name, and no others. Every
calculation in this engine is checked against an independent hand pass — that is the root
`CLAUDE.md` rule, *a calc that only agrees with itself is not verified* — and section 8 of
each sheet names its own. Copying the whole house's design log would bury the four that
matter under forty that do not.

## What the IFC carries beyond geometry

`haus build`'s IFC goes to a plan reviewer who wants geometry. This one goes to an engineer,
and carries three things more:

- **Section profiles.** `IfcMaterialProfileSet` on every beam, column and framed member,
  built from the same `cross_section` parse the geometry came from, so the two cannot
  disagree. Shared per section rather than per member: catlin has ~15,000 members over a few
  dozen sections. Species and grade are **not** written for sawn lumber, because this engine
  authors neither and a grade nobody typed is a grade nobody checked.
- **The engineering records.** `Pset_TH_Engineering_<kind>` on every element a record names:
  item id, status, basis, governing limit state, demand, capacity, ratio, citation, the
  oracle notes, the fingerprint and whether any seal still matches it. Plus
  `Pset_BeamCommon`/`Pset_ColumnCommon` with Span and LoadBearing, which is what a structural
  importer reads.
- **The reinforcing steel.** One `IfcReinforcingBar` per `(host, role)` — a pier cage is
  "(4) #5 vertical", which is the unit the model authors, the BOM bills and ACI 318 grades.
  Lengths are summed off the same laid-out pieces `takeoff/reinforcement.py` bills — cut
  length, with `Pset_TH_Reinforcement` splitting it into placed, lap and hook and counting
  pieces — and a test sums them back up against the bill of materials. **No Body
  representation** (decision #75 keeps the IFC non-geometric): the bars' 3D paths are in the
  glTF and behind `GET /model/rebar`, where the viewer draws and picks them.

## The analytical model — one graph, four files

`typehaus/analytical/` builds the **engineered items and their load path** — every member a
record names, what it bears on down to the footing, what bears on it — as nodes, members,
supports and load cases (decision #73, `plans/31-ifc-analytical.md`). Four files are written
from that one graph, so they cannot disagree with each other:

| File | Opens in | What it carries |
|---|---|---|
| `model.ifc` (structural analysis view) | SAP2000, ETABS (*File > Import > IFC*, choose the structural view), Bonsai | `IfcStructuralAnalysisModel`; one `IfcStructuralCurveMember` per member sharing the physical member's `IfcMaterialProfileSet`; `IfcStructuralPointConnection` per node with an `IfcBoundaryNodeCondition` where a support exists; load cases and actions; `IfcRelAssignsToProduct` back to the physical element |
| `analysis/centreline.dxf` | RISA-3D (*File > Import > DXF*, inches, layer = section set, rotate to Y-up) | `LINE` per member, `POINT` per node, layer named for the section, labels with member id, section and item ids, supports and the assumption lines as text |
| `analysis/members.csv` | a spreadsheet; ForteWEB / WoodWorks Sizer / Enercalc by hand | one row per member: section, material, E and where it came from, length, ends, releases, supports, item ids, line and point loads per case |
| `analysis/model.pynite.py` | `python model.pynite.py` with PyNite installed (`pip install PyNiteFEA`) | rebuilds and solves the model, prints reactions per case and member extremes |

**Every fixity, release and load is a claim this engine makes and states.** A support's
`basis` says why it is fixed or pinned (the balcony's cast columns are the deck's lateral
system — no brace, no wall — so they are fixed; a post on a base connector is pinned). A
load's `source` names the engineering item and the quantity it came from. What could not
be derived is in `gaps`, printed in every file, never defaulted. Retaining walls and slabs
are not surface members in this version and the gaps say so by item id.

The model is verified the way every calculation here is: `tests/test_analytical_oracle.py`
solves the exported graph in PyNite and reproduces `notes/analytical_model_basis.md`.

## Pruning

Anything the previous manifest listed and this run did not produce is deleted. The bundle is
a statement about the current model; a sheet for an item the house no longer has reads as a
calculation somebody did. Same helper, and the same rule, as `haus calcs`
(`takeoff/handoff.py`).
