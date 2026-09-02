# Type:Haus

**Infrastructure as code, but the infrastructure is a residential house.** Author a house
plan as typed, declarative Python; compile it to an IFC4 model, DXF, permit-ready PDFs, and
a 2D/3D editing UI.

The vision here is for non-architects to be able to use vibe coding and simple UIs to 'play around' with a house design until they capture most of their vision for their home, then be able to export a practical, usable home design in a format architects can easily load into the software of their choice to polish and refine. This also aims to go beyond many "floor plan" apps by allowing users to get into the assemblies and building science of their home. Although it does not aim for 1:1 parity with leading architectural tools, this library does aim to export permit ready construction drawings for homes completely from the tools here.

Note that we don't intend to make this "visually stunning". The idea here is users can pass an elevation/screenshot to an AI process to get a "photorealistic render" as needed. We do aim for quality, realistic portrayals of surface where feasible without great complexity.

Try it out at: [https://type-haus.com/app/](https://type-haus.com/app/). Note that the browser version allows edits, but they won't be saved and are lost on refresh, so a local server instance is needed for actual use.

## How

You describe walls, rooms, openings, assemblies, and foundations as frozen typed objects.
The engine resolves topology (gap-free mitered corners), stacks walls across storeys, frames
every wall with real studs/plates/headers, derives rooms and takeoffs, and runs integrity /
code / structural checks — all from one source of truth. Two exit ramps, both first-class:
refine in place to a permit-ready set, or hand off an IFC an architect can build on directly.

## Quickstart (source tree)

`typehaus` is installed editable into `.venv` (Python 3.11), so the console script is the
entry point — no `PYTHONPATH`, no `uv`.

```bash
pip install -e packages/engine           # once, into a 3.11+ venv
.venv/bin/haus ls houses/starter --summary          # compact plan digest
.venv/bin/haus build houses/starter                 # -> houses/starter/out/model.json (+ IFC)
.venv/bin/haus check houses/starter                 # integrity/code/advisory/structural findings
.venv/bin/haus doctor                               # environment sanity check
.venv/bin/haus permit-check houses/catlin           # declared MN permit-submittal subset
.venv/bin/haus print houses/catlin --handoff        # gate + permit PDF, DXFs, architect bundle
.venv/bin/haus import furniture chair.glb houses/catlin --room RM-M-LIVING --at-m 7.0,4.0
.venv/bin/haus explain HOUSE_WALL_2X6_WITH_ZIPR houses/starter --card   # assembly section card SVG
.venv/bin/haus explain transitions houses/starter   # derived boundary conditions
```

Tests and the full gate:

```bash
.venv/bin/python -m pytest packages/engine/tests -q   # parallel by default (~4 min)
scripts/verify.sh                                     # the CI gate; --fast skips builds/bench/npm
```

## UI Start
Terminal 1
```bash
.venv/bin/haus serve houses/starter --port 8000
```
Terminal 2
```bash
cd ui && HAUS_ENGINE=http://127.0.0.1:8000 npm run dev
```

`haus serve` watches the house directory only — restart it after editing
`packages/engine/`, or the viewer keeps serving stale geometry.


## Layout

- `packages/engine/` — the `typehaus` Python package (quantities, model, resolve, emit,
  checks, CLI).
- `library/` — shared assemblies/materials/types — the community contribution seam.
- `houses/starter/` — the interim `haus new` template and cold-start delight target.
- `plans/` — the living design documentation (00–50) and the decision log.

## Trust model

`haus build` **imports the plan package** — building a downloaded house executes its Python,
the same trust decision as `pip install`. `# haus: editable` files are a constrained
declarative subset with no executable surface (the linter proves it); `haus build --inspect`
previews a plan without importing `params/`. See `plans/02-architecture.md` §Git topology.

## License

MIT © Colin Catlin. See `LICENSE`.
