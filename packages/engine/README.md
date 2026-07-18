# typehaus

The Type:Haus engine — infrastructure-as-code for residential houses. Author a house plan as
typed, declarative Python; resolve topology, stacking, and framing; emit an IFC4 model,
`model.json`, and assembly section cards; and run integrity / code / structural checks.

> **Pre-alpha.** APIs, schema, and outputs change without notice. Not for production use.

This is the Python package behind the `haus` CLI. See the repository root and `docs/plan/`
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
```

IFC emission requires `ifcopenshell` (pin `0.8.x`); when it is absent, `haus build` still
writes `model.json` and reports the skipped IFC step.

## License

MIT © Colin Catlin.
