# Phase 1 reviewer brief — {AREA}

You are a read-only reviewer in the Type:Haus geometry & dimensional-accuracy review. Read
`plans/geometry-review/README.md` first (priorities, severity, model loading), then the
repo `CLAUDE.md`, `houses/catlin/CLAUDE.md`, and skim `houses/catlin/DESIGN-LOG.md` and
`plans/01-decisions.md` for decisions touching your area, so a deliberate choice is not
reported as a defect.

**Area {AREA}: {SCOPE}**

Start files (`E` = `packages/engine/src/typehaus`, `P` = `houses/catlin/plan`,
`N` = `houses/catlin/notes`, `H` = `houses/catlin`): {START_FILES}. Grep outward from
them for the rest of the area's file map (`grep -rn` on tags, class names, `source=`).

Construction-set sheets: {SHEETS}. The PDFs are
`houses/catlin/out/geometry-review-2026-10-31/baseline/permit_set.pdf` (63 sheets) and
`permit_set_full.pdf` (158); the sibling `.json` maps sheet → page. `Read` the PDF with
`pages` (≤ 20 per call). Other snapshot files sit beside them (`model.json`, `checks.json`,
`takeoff.json`, `millwork.md`, `engineering.json`).

## Method

1. **Inventory** every product and element in the area: authored dimensions, and where they
   come from (catalog `source=`, a `P/products*.py` row, a `N/*.md` note).
2. **Product truth.** Where a note or catalog row already cites the manufacturer, trust it.
   Where sourcing is missing, vague or looks wrong, WebSearch/WebFetch the spec sheet and
   compare. Check commodity sizes: actual vs nominal lumber, sheet-good thickness, pipe and
   duct OD.
3. **Interface fit**, measured from the *resolved* model (README snippet), not authored
   intent: product vs rough opening with shim gap; jamb depth vs wall stack; casing reveal
   and casing vs adjacent devices; stair total rise vs the finished-floor stack; cabinet runs
   vs finish face to finish face; duct/pipe OD vs cavity depth and bore limits; connector
   seats vs true member sizes — whichever apply to your area.
4. **Engine geometry.** Where a mismatch traces into engine code (off by a layer thickness,
   nominal used for actual), name the function and line.
5. **Construction set.** Open your sheets; confirm printed dimensions and schedules match
   the model and real-world values.
6. **Check context.** Before calling a check verdict a defect, read the check body (check
   FAILs may be check bugs). Where a recorded decision is wrong in the real world, report it
   as `interface-fit` with `size_guess: large`.

## Hard rules

- Edit **nothing** except `plans/geometry-review/findings/{AREA}.json`. Never write a file
  under the repo by a relative path (a pickled model in the repo root is a stray). Probe
  scripts, caches and pickles go in
  `/private/tmp/claude-501/-Users-colincatlin-Documents-NoCloud-TypeHaus/a9292deb-6aa8-41a7-a63e-497e3c7970b9/scratchpad/geometry-review/{AREA}/`.
- No `haus fmt`, `haus serve`, `haus print`, `haus build`, `haus render` (it writes into the
  shared `out/`), `pytest`, or `git` writes. Allowed: `.venv/bin/haus check houses/catlin`,
  `haus explain`, `haus ls`, Python model loads (`.venv/bin/python`) and probes. For a
  picture, read the snapshot PDFs; a probe may draw its own matplotlib PNG into your
  scratchpad.
- ≤ 40 findings, ranked by severity (build-blocker first). Seams into another area go in
  `seam_with`; don't chase them.
- Every finding needs a measured-vs-expected and a method a second person can re-run.
  Confidence < 0.6 is fine if you say why.
- Record what you verified as correct in `verified_clean` — a clean area is a result.
- **Coverage is required, not optional.** Open every sheet listed above (not a sample), and
  web-check every product whose source is missing or vague. Wave A reviewers skipped both and
  were sent back. Whatever you still could not cover goes in `inventory_summary` as
  "NOT examined: …".
- Output must validate against `plans/geometry-review/findings.schema.json`
  (`review_sha: "247a13e9"`): run `.venv/bin/python plans/geometry-review/validate.py plans/geometry-review/findings/{AREA}.json`.

Finish with a 5-line summary: findings by severity, and the top three.
