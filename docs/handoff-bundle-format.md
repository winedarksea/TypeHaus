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
  calcs.pdf                 the same, flattened and page-anchored — what a seal binds to
  notes/                    ONLY the hand-worked notes these records are checked against
  model.ifc                 IFC4, framed LOD, with sections, records and a bar schedule
  model.glb                 the same building, for a viewer that does not read IFC
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
  Lengths come from the same two helpers `takeoff/reinforcement.py` uses, and a test sums
  them back up against the bill of materials. **No Body representation**: drawing a cage
  would invent hook geometry, laps and cover the model does not carry, and a drawn cage read
  as a placement drawing is worse than none because it looks like one.

## Pruning

Anything the previous manifest listed and this run did not produce is deleted. The bundle is
a statement about the current model; a sheet for an item the house no longer has reads as a
calculation somebody did. Same helper, and the same rule, as `haus calcs`
(`takeoff/handoff.py`).
