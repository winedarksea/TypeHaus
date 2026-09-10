# typehaus

Infrastructure-as-code for residential houses. Author a house plan as typed, declarative
Python; resolve topology, stacking, and framing; emit an IFC4 model, `model.json`, drawings,
and assembly section cards; and run integrity, code, structural, and building-science checks
against it.

Quantities are the product. The engine ships no price, wage, or productivity data — a house
owns its own numbers.

## Install

```bash
pip install typehaus                # engine + CLI
pip install 'typehaus[server]'      # adds `haus serve` (FastAPI + the bundled editor)
```

Python 3.11 or newer.

## Scaffold a house

```bash
haus new my-house --name "My House"
haus build my-house                 # -> my-house/out/model.json (+ IFC)
haus check my-house                 # integrity / code / structural / advisory findings
haus serve my-house                 # the browser editor and 3D viewer, no node required
```

`haus new` writes a complete, buildable starter house: `plan/` (the declarative source),
`brief.md`, and `preferences.toml`. Plans import shared assemblies, materials, and door,
window, fixture and furniture types from the reviewed catalog that ships with the engine:

```python
from library import HOUSE_WALL_2X6_WITH_ZIPR, STARTER_MATERIALS
```

## The rest of the CLI

```bash
haus doctor                                 # environment sanity
haus ls my-house --summary                  # compact plan digest
haus fmt my-house                           # mint uids, canonicalize plan source
haus explain HOUSE_WALL_2X6_WITH_ZIPR my-house --card
haus render my-house --view plan            # -> out/render/plan_*.png
haus print my-house                         # -> out/sheets/*.dxf + .pdf (AIA layers)
haus takeoff my-house --csv out/estimate.csv
haus tasks my-house --csv out/tasks.csv
haus millwork my-house                      # hardwood cut list
haus engineering my-house                   # what needs a professional seal, and what governs
haus calcs my-house                         # the calculation package a PE marks up
haus diff architect.ifc my-house            # semantic diff -> out/diff.json + table
```

IFC emission (and `haus diff`'s external-IFC read) requires `ifcopenshell`, pinned to
`0.8.x` and installed by default; when it is absent, `haus build` still writes `model.json`
and reports the skipped step.

## `model.json` and write safety

`haus serve` exposes the resolved `model.json` (revision hash, per-element provenance, live
findings). Every `PATCH /plan` carries the project revision as a precondition (stale → 409),
applies element-level ops through a libcst writeback that preserves comments and formatting,
stages and validates the whole project, then writes each file atomically. Undo/redo is
server-owned — the file is the state — and an external editor edit seals the journal.

## Status

Beta. The schema and the emitted artifacts are stable enough to build against; check the
changelog before upgrading. Permit sets print at `draft` authority; a sealed set requires a
licensed professional, which the engine gates on and never fakes.

## Links

- Homepage: <https://type-haus.com>
- Source and issues: <https://github.com/colincatlin/TypeHaus>

## License

MIT © Colin Catlin.
