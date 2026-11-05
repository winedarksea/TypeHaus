# Geometry review, round 2 (2026-11-04)

Re-verifies round 1 (`../REPORT.md`, SHA `247a13e9`, 244 findings), cleans out what closed,
finds what is new. Same three phases; severity, `kind`, priorities, model loading and the
**fix rubric** are round 1's, unchanged: read `../README.md`.

- Review SHA: `539d9a81`, tree clean but for the owner's `plans/TODO.md` (never revert it).
- Baseline `haus check houses/catlin --only all`: **0 FAIL**, 208 UNKNOWN. The gate is
  **no FAIL beyond the Phase 0 list** (that is, none), diffed by line:
  `baseline/fail.txt` and `baseline/unknown.txt`.
- Snapshot (gitignored): `houses/catlin/out/geometry-review-2026-11-04/baseline/` —
  `model.json`, `checks.json`, `takeoff.json`, `millwork.md`, `engineering.json`,
  `countertops/`, `permit_set.pdf`/`.json` and `permit_set_full.pdf`/`.json`, printed
  **gated** (`haus print` passes). The `.json` maps sheet → page.

## What changed from round 1

- Every findings file carries `prior_findings`: each round-1 id the area owns
  (`areas.md`), re-probed, with `closed | open | partial | regressed | obsolete`. A
  "Resolved" line in `../adjudicated/C*.md` or `../REPORT.md` is a claim to verify.
- New finding ids start at `-101` (`M4-101`).
- S1 + S2 → **S1**. M1 → **M1** (air side of the equipment) + **M4** (branches and
  fittings). M2 → **M2** (supply) + **M5** (DWV and vents).
- `findings.schema.json` here; validate with
  `.venv/bin/python plans/geometry-review/validate.py --schema plans/geometry-review/2026-11-04/findings.schema.json <file>`.

## Layout

- `areas.md` / `areas.json` — scope, start files, prior ids, sheets, TODO lines and the
  `git diff 247a13e9..HEAD` per area.
- `brief-template.md`, `adjudicator-brief.md` — the Phase 1 and Phase 2 prompts.
- `findings/<AREA>.json`, `adjudicated/C1..C5.md`.
