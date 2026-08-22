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

## The four `advisory.control_continuity` FAILs are ACCEPTED — do not "fix" them

`haus check .` reports four of them, one per exterior wall, all reading *"control-layer
continuity not declared across `storey_stack:rim:HOUSE_WALL_2X6_WITH_ZIPR`"* on
`W-101/W-201`, `W-102/W-202`, `W-103/W-203`, `W-104/W-204B`. They are the rim band where the
main-storey wall meets the second-storey wall, and the check is asking a real question: does
the air/water control layer carry across that joint, and *has somebody said so*.

**Accepted, deliberately, and recorded here because `scripts/verify.sh` runs the check
plugin against this house** — so anyone who touches the transition catalog will see these
four and be tempted to make them go away.

- The answer is a `Transition`, and a transition is a **detail decision about a specific
  building**. The starter is a template: four walls, two storeys, one assembly, no site
  data. Authoring a rim-band detail here would ship an opinion about flashing and air
  sealing to every house `haus new` creates, which is the opposite of a template's job.
- It is an ADVISORY finding, not a code one. `haus check` exits 1 on any FAIL, so the
  starter's check run is red by design; the reference house `houses/catlin` is the one held
  to a clean gate.
- **The right time to close them is in a real house**, by authoring the transition the
  builder actually details. Catlin does exactly that — see its `plan/transitions.py`.
- Same reasoning covers the starter's other reds (`integrity.condition_coverage`,
  `structural.window_framing_module`, `structural.ijoist_span`,
  `mep.ventilation_distribution`, `electrical.*`): a template with 36" windows on an
  unstated stud grid and a 20' I-joist span is a *shape*, not a buildable design. Do not
  tune the starter to a clean report; tune it to be the smallest thing that loads.

## Command crib
`haus new <dir>` · `haus serve` (UI + PATCH/undo) · `haus build` · `haus check` ·
`haus render` · `haus print` (DXF/PDF) · `haus diff <ext.ifc>` · `haus fmt` · `haus ls`.

## Skills
- `/add-room` — add nodes + walls + a room claim, then build + check + render.
- `/import-review` — walk an architect's IFC diff, accept/reject changes into plan source.
