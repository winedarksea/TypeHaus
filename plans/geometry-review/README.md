# Geometry & dimensional-accuracy review (2026-10-31)

Answers `plans/TODO.md`'s "do passes to confirm geometry and dimensions … align together
correctly for real world build dimensions". Shape follows the trade audit
(`plans/trade-audit-decisions.md`): Sonnet reviewers → Opus adjudicators → one report.

- Review SHA: `247a13e9`, clean tree.
- Baseline `haus check houses/catlin`: **2 FAIL** — both `code.R311_7_1_stair_width` on
  ST-S2A (33.11" between guard posts vs 36"; 29.66" past the handrail vs 31.5") — plus 202
  UNKNOWN. The gate is "no FAIL beyond these two", diffed by line, not count.
- Snapshot (gitignored): `houses/catlin/out/geometry-review-2026-10-31/baseline/`
  — `model.json`, `checks.json` (`--only all --json`), `takeoff.json`, `millwork.md`,
  `engineering.json`, `countertops/`, `permit_set.pdf` + `.json` (63 sheets) and
  `permit_set_full.pdf` + `.json` (158 sheets). The two sets were written **ungated**
  ("REVIEW SNAPSHOT — NOT GATED") because the ST-S2A FAILs block `haus print`. The `.json`
  manifests map sheet number → PDF page; read pages with `Read(pages=...)`.

## Priorities

1. **The construction set** (`haus print`) — what gets built from. Rank every finding by
   whether it misprints there.
2. **The UI viewer.** Depth bias / polygon offset is deliberate and not a finding.
3. **Emitters** (IFC, GLB, print3d) are out of scope: one line, `kind: drawing`,
   `severity: doc`, title prefixed `[emitter]`. Don't chase.

## Severity

| severity | meaning |
|---|---|
| `build-blocker` | the real product cannot be installed as modelled (doesn't fit, wrong RO, collides) |
| `wrong-build` | it installs, but a trade building from the set builds it wrong (wrong height, reveal, slope) |
| `drawing-error` | the model is right; a sheet prints a wrong dimension, schedule value or label |
| `model-only` | wrong in the model or viewer, invisible on the set and harmless to the build |
| `doc` | note, citation or source string wrong or missing; geometry fine |

`kind`: `product-data` (catalog row ≠ manufacturer) · `interface-fit` (two right parts that
don't meet) · `commodity-size` (nominal vs actual, sheet thickness, pipe OD) ·
`engine-geometry` (a resolver/derivation bug) · `drawing` · `viewer`.

## Loading the resolved model

```python
from pathlib import Path
from typehaus.source import load_plan
from typehaus.resolve import resolve
r = load_plan(Path("houses/catlin"))
model, _ = resolve(r.plan)
```

`ResolvedModel` (`packages/engine/src/typehaus/resolve/model.py:1625`), all metres:
`walls[].members` (framing), `openings`, `solids`, `roofs`, `stairs`, `floors`, `rooms`,
`ceilings`, `window_stools`, `window_returns`, `jamb_fills`, `base_runs`, `door_casings`,
`drywall_trims`, `countertops`, `pipe_runs`, `ducts`, `conduits`, `device_boxes`,
`light_runs`, `rebar`, `soffits`, `fireblocks`. `model.find(tag)`-style lookups: grep
`_tag_index`. Measure from the **resolved** model, not authored intent.

## Fix rubric (Phase 2)

SMALL only if **all** hold: corrects a value to a cited real-world dimension · local to one
catalog/product row, one element's authored offset/size, or one engine function whose
consumers were grepped · moves no wall, opening position, storey/ceiling height, stud module,
or structural member size/grade · swaps no product, changes no owner-visible design · adds no
`haus check` FAIL and keeps the print gate where it was · contradicts no
`plans/01-decisions.md` decision or dated `houses/catlin/CLAUDE.md` entry · follows house
rules (`haus fmt` mints uids, `# haus: editable` dialect, files < 500 lines, tests only for
clear value).

Anything else is **ESCALATED** with: problem + evidence · 2–3 options and a recommendation ·
blast radius (elements, checks, engineered items, sheets, goldens) · rough size.
Fingerprint changes are fine (no `engineering.toml`, no seals) — note them.

## Layout

- `findings.schema.json` — Phase 1 output schema; `findings/<AREA>.json` one per area;
  `validate.py` checks them (stdlib, no jsonschema in `.venv`).
- `brief-template.md` — the Phase 1 reviewer prompt.
- `adjudicated/<cluster>.md` — Phase 2 verdicts (Fixed / Escalated / Rejected / Handed off).
- `REPORT.md` — Phase 3 roll-up.
