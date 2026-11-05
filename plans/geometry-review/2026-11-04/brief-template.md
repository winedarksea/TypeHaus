# Phase 1 reviewer brief, round 2 — {AREA}

You are a read-only reviewer in round 2 of the Type:Haus geometry & dimensional-accuracy
review. Read `plans/geometry-review/2026-11-04/README.md`, then round 1's
`plans/geometry-review/README.md` (priorities, severity, `kind`, model loading), the repo
`CLAUDE.md` and `houses/catlin/CLAUDE.md`. Skim `houses/catlin/DESIGN-LOG.md` and
`plans/01-decisions.md` for decisions touching your area, so a deliberate choice is not
reported as a defect.

**Area {AREA}: {SCOPE}**

Your row in `plans/geometry-review/2026-11-04/areas.md` lists the start files
(grep outward from them), the **prior ids you own**, the sheets, the TODO lines and the
files **changed since round 1 — look there first**.

{EXTRA}

Snapshot: `houses/catlin/out/geometry-review-2026-11-04/baseline/` — `permit_set.pdf` and
`permit_set_full.pdf` (the sibling `.json` maps sheet → page; `Read` with `pages`, ≤ 20 per
call), `model.json`, `checks.json`, `takeoff.json`, `millwork.md`, `engineering.json`,
`countertops/`. Round-1 artifacts: `plans/geometry-review/findings/<area>.json` and
`adjudicated/C*.md`.

## Method

1. **Reconcile first.** For every prior id: read its round-1 finding and the adjudicator's
   verdict, then **re-probe it on today's model** (the same method, re-run). Set `status`:
   `closed` (measured fixed), `open` (unchanged), `partial`, `regressed` (fixed then broken,
   or worse), `obsolete` (the element or design no longer exists). A round-1 "Resolved" or
   "Rejected" line is a claim, not a verdict: a rejected id stays `closed` only if the
   rejection still holds. Evidence is a number measured now, not a quote.
2. **Inventory** every product and element in the area, with where its dimensions come from
   (catalog `source=`, a `P/products*.py` row, a `N/*.md` note).
3. **Product truth.** Trust a note or catalog row that cites the manufacturer. Where sourcing
   is missing, vague or looks wrong, WebSearch/WebFetch the spec sheet. Check commodity
   sizes: actual vs nominal lumber, sheet thickness, pipe and duct OD.
4. **Interface fit**, measured from the *resolved* model (round-1 README snippet), not
   authored intent.
5. **Engine geometry.** A mismatch that traces into engine code: name the function and line.
6. **Construction set.** Open your sheets; confirm printed dimensions and schedules match the
   model and real-world values.
7. **Check context.** Read a check's body before calling its verdict a defect (a check FAIL
   may be a check bug). A recorded decision that is wrong in the real world is
   `interface-fit` with `size_guess: large`.

## Hard rules

- Edit **nothing** except `plans/geometry-review/2026-11-04/findings/{AREA}.json`. Probe
  scripts, caches and **pickles go only in
  `{SCRATCH}/{AREA}/`, by absolute path** — never a relative path, never the repo root.
- No `haus fmt`, `serve`, `print`, `build`, `render` (they write the shared `out/`),
  **no `pytest`, no `scripts/verify.sh`, no full suite**, no `git` writes. Allowed:
  `.venv/bin/haus check houses/catlin`, `haus explain`, `haus ls`, `haus route ... --out
  {SCRATCH}/{AREA}/...`, Python model loads and probes. A probe may draw its own PNG into
  your scratchpad.
- **No code or product tables from memory.** Cite the published row (URL, page, table) or
  read the engine's own table. An approximate table the coordinator once supplied produced a
  false finding.
- ≤ 40 new findings, ranked by severity. Seams into another area go in `seam_with`.
- Every finding and every prior status needs a measured-vs-expected and a method a second
  person can re-run. Confidence < 0.6 is fine if you say why.
- Record what you verified as correct in `verified_clean`.
- **Coverage is required.** Open every listed sheet (not a sample) and web-check every
  product whose source is missing or vague. Every prior id appears in `prior_findings`.
  Whatever you could not cover goes in `inventory_summary` as "NOT examined: …".
- `review_sha: "539d9a81"`. Validate:
  `.venv/bin/python plans/geometry-review/validate.py --schema plans/geometry-review/2026-11-04/findings.schema.json plans/geometry-review/2026-11-04/findings/{AREA}.json`.

Finish with a 6-line summary: prior ids by status, new findings by severity, the top three.
