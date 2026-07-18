# Catlin house — agent guide

This directory **is the state**: the house is defined by the editable plan source under
`plan/` plus the parametric modules under `params/`. Edit those; never edit `out/`
(generated). Read `brief.md` (intent) **and** `preferences.toml` (targets) before
proposing any design change.

## Project map
- `plan/manifest.py` — plain-Python assembler (NOT editable); wires modules + params.
- `plan/storeys/{basement,main,second,attic,garage}.py` — `# haus: editable` elements.
- `plan/assemblies.py`, `plan/site.py` — editable assemblies + site.
- `params/sunken_garden.py` — the freestanding arched porch/garden structure (math OK here).
- `params/foundations.py` — footings, garage ICF stem, breezeway posts.
- `notes/*.md` — construction detail notes migrated from the original repo.

## House facts that must stay true
- Four structures: house, freestanding garage (12' north), freestanding sunken-garden/
  porch/balcony concrete structure (5" south gap), breezeway on freestanding 6x6 posts.
- 36'x36' at sheathing; everything on the 16" o.c. module; exterior walls carry
  `alignment=face("sheathing-ext")` so the sheathing plane is the vertical datum (#43).
- The side-wall stack is 2x6 (main) → 2x4 (second) → 2x4 (attic) — sheathing plane
  continuous, stud depth jogs inward.
- Bearing lines: west wall, center N-S wall (x=18'), east wall; 18' I-joist spans E-W.
- Attic is a habitable hot-roofed cathedral space: 5' knee walls E/W, gables N/S,
  ridge N-S, 4:12, **zero overhang**.
- Window rules: 14" RO fits a stud bay; 30" RO max non-bearing (one stud broken);
  27" RO max bearing (jacks added). Resize windows to fit the grid, not vice versa.

## The loop: edit → build → check → *look* → fix
```
haus build .            # -> out/model.json (+ IFC when ifcopenshell present)
haus check .            # integrity / code / structural findings
haus render --view plan # -> out/render/plan_*.png  — LOOK at what you made
haus ls --summary       # compact whole-plan digest
```
After any spatial edit, **render and look**. After assembly edits,
`haus explain <ASM> --card`.
