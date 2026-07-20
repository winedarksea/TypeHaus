# Type:Haus

**Infrastructure as code, but the infrastructure is a residential house.** Author a house
plan as typed, declarative Python; compile it to an IFC4 model, DXF, permit-ready PDFs, and
a 2D/3D editing UI.

The vision here is for non-architects to be able to use vibe coding and simple UIs to 'play around' with a house design until they capture most of their vision for their home, then be able to export a practical, usable home design in a format architects can easily load into the software of their choice to polish and refine. This also aims to go beyond many "floor plan" apps by allowing users to get into the assemblies and building science of their home. Although it does not aim for 1:1 parity with leading architectural tools, this library does aim to export permit ready construction drawings for homes completely from the tools here.

## How

You describe walls, rooms, openings, assemblies, and foundations as frozen typed objects.
The engine resolves topology (gap-free mitered corners), stacks walls across storeys, frames
every wall with real studs/plates/headers, derives rooms and takeoffs, and runs integrity /
code / structural checks — all from one source of truth. Two exit ramps, both first-class:
refine in place to a permit-ready set, or hand off an IFC an architect can build on directly.

## Quickstart (source tree)

```bash
uv sync                                   # or: pip install -e packages/engine
haus ls houses/starter --summary          # compact plan digest
haus build houses/starter                 # -> houses/starter/out/model.json (+ IFC)
haus check houses/starter                 # integrity/code/advisory/structural findings
haus permit-check houses/catlin           # declared MN permit-submittal subset
haus print houses/catlin --handoff        # gate + permit PDF, DXFs, architect bundle
haus import furniture chair.glb houses/catlin --room RM-M-LIVING --at-m 7.0,4.0
haus explain HOUSE_WALL_2X6_WITH_ZIPR houses/starter --card   # assembly section card SVG
haus explain transitions houses/starter   # derived boundary conditions
```

## UI Start
Terminal 1
```bash
PYTHONPATH=packages/engine/src /Users/colincatlin/mambaforge/bin/python3.10 -m typehaus.cli.app serve houses/starter --port 8000
```
Terminal 2
```bash
cd ui && HAUS_ENGINE=http://127.0.0.1:8000 npm run dev
```


## Layout

- `packages/engine/` — the `typehaus` Python package (quantities, model, resolve, emit,
  checks, CLI).
- `library/` — shared assemblies/materials/types — the community contribution seam.
- `houses/starter/` — the interim `haus new` template and cold-start delight target.
- `docs/plan/` — the living design documentation (00–50).

## Trust model

`haus build` **imports the plan package** — building a downloaded house executes its Python,
the same trust decision as `pip install`. `# haus: editable` files are a constrained
declarative subset with no executable surface (the linter proves it); `haus build --inspect`
previews a plan without importing `params/`. See `docs/plan/02-architecture.md` §Git topology.

## License

MIT © Colin Catlin. See `LICENSE`.
