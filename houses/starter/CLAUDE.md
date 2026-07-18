# Type:Haus starter house — agent guide

This directory **is the state**: the house is defined by the editable plan source under
`plan/`. Edit that source; never edit `out/` (generated). Read `brief.md` (intent) **and**
`preferences.toml` (targets) before proposing any design.

## Project map
- `plan/manifest.py` — plain-Python assembler (NOT editable); wires the modules into `PLAN`.
- `plan/storeys/*.py` — `# haus: editable` element files (Nodes, Walls, Openings, Rooms, Floor).
- `plan/assemblies.py`, `plan/site.py` — editable library + site.
- `brief.md` / `preferences.toml` — intent / machine-read thresholds.
- `out/` — generated (model.json, IFC, sheets, render snapshots). **Never hand-edit.**

## Editable-dialect rules (the grammar the linter enforces)
- Only imports from `typehaus.*` / `library.*`, named constants, and **constructor calls
  with keyword args**. No loops, conditionals, math, f-strings, or comprehensions — move
  parametric logic into `params/*.py`.
- Every element carries a `uid=` (immutable identity) and a `tag=` (human name). If you add
  an element without a uid, run `haus fmt` to mint one. Never change an existing `uid`.
- All dimensions go through quantity constructors (`ft(12, 6)`, `inch(5.5)`) — never bare
  floats.

## The loop: edit → build → check → *look* → fix
```
haus build .            # -> out/model.json (+ IFC when ifcopenshell present)
haus check .            # integrity / code / structural findings
haus render --view plan # -> out/render/plan_*.png  — LOOK at what you made
haus ls --summary       # compact whole-plan digest to re-orient a fresh session
```
After any spatial edit, **render and look** — spatial judgment ("the hallway is awkward")
joins the text findings. After assembly edits, `haus explain <ASM> --card`.

## Command crib
`haus new <dir>` · `haus serve` (UI + PATCH/undo) · `haus build` · `haus check` ·
`haus render` · `haus print` (DXF/PDF) · `haus diff <ext.ifc>` · `haus fmt` · `haus ls`.

## Skills
- `/add-room` — add nodes + walls + a room claim, then build + check + render.
- `/import-review` — walk an architect's IFC diff, accept/reject changes into plan source.
