# typehaus

The Type:Haus engine — infrastructure-as-code for residential houses. Author a house plan as
typed, declarative Python; resolve topology, stacking, and framing; emit an IFC4 model,
`model.json`, and assembly section cards; and run integrity / code / structural checks.

> **Pre-alpha.** APIs, schema, and outputs change without notice. Not for production use.

This is the Python package behind the `haus` CLI. See the repository root and `plans/`
for the full design documentation and monorepo layout.

## Install

```bash
pip install -e packages/engine        # from the repo root
```

## CLI

```bash
haus ls houses/starter --summary                 # compact plan digest
haus build houses/starter                        # -> out/model.json (+ IFC when ifcopenshell present)
haus check houses/starter                         # integrity/code/advisory/structural findings
haus explain HOUSE_WALL_2X6_WITH_ZIPR houses/starter --card
haus explain transitions houses/starter           # derived boundary conditions

# M2 — the loop closes
haus new my-house --name "My House"               # scaffold a self-contained house
haus serve houses/starter                          # FastAPI: model.json, PATCH /plan, undo/redo, live reload
haus render houses/starter --view plan             # -> out/render/plan_*.png  (agent eyes, #52)
haus print houses/starter                          # -> out/sheets/plan_*.dxf + .pdf (AIA layers)
haus fmt houses/starter                            # assign missing uids (merge-friendly canonical)
haus diff architect.ifc houses/starter             # semantic diff -> out/diff.json + table
```

IFC emission (and `haus diff`'s external-IFC read) requires `ifcopenshell` (pin `0.8.x`);
when it is absent, `haus build` still writes `model.json` and reports the skipped IFC step.
The server is an optional extra: `pip install -e 'packages/engine[server]'`.

### The `model.json` contract + write safety (M2)

`haus serve` exposes the resolved `model.json` (revision hash, per-element provenance, live
findings). Every `PATCH /plan` carries the project revision as a precondition (stale → 409),
applies element-level ops through the libcst writeback (comments/formatting preserved),
stages + validates the whole project, then writes each file atomically. Undo/redo is
server-owned (the file is the state); an external VSCode/Claude edit seals the journal.

## License

MIT © Colin Catlin.
