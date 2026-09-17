# Type:Haus empty house — agent guide

This directory **is the state**: the house is the editable plan source under `plan/`.
Edit that source; never edit `out/` (generated). Read `brief.md` and `preferences.toml`
before proposing a design.

It starts with one storey (`main`) and nothing on it. `haus check .` is red until walls,
rooms, a floor and life-safety items exist — that is the work, not a defect.

## Project map
- `plan/manifest.py` — plain-Python assembler (NOT editable); wires modules into `PLAN`.
- `plan/storeys/main.py` — `# haus: editable`: door/window types, `NODES`, `WALLS`,
  `OPENINGS`, `ROOMS`. The editor's wall and room tools append here.
- `plan/placeables.py` — `MAIN_PLACEABLES`, the Place tool's target.
- `plan/assemblies.py`, `plan/site.py` — editable library + site.

## Editable-dialect rules
- Only imports from `typehaus.*` / `library.*`, named constants, and constructor calls with
  keyword args. No loops, conditionals, math, f-strings or comprehensions.
- Never write a `uid=` by hand: leave it off and run `haus fmt .` to mint one.
- Dimensions go through quantity constructors (`ft(12, 6)`, `inch(5.5)`).

## The loop
```
haus serve .            # draw walls and rooms in the editor
haus build .            # -> out/model.json
haus check .            # findings
haus render --view plan # LOOK at what you made
```
