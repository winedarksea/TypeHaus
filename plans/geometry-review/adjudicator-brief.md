# Phase 2 adjudicator brief — {CLUSTER}

You adjudicate cluster **{CLUSTER} ({NAME})**: findings files {FILES} in
`plans/geometry-review/findings/`. Read `plans/geometry-review/README.md` (severity, the
**fix rubric**, model loading), the repo `CLAUDE.md`, `houses/catlin/CLAUDE.md`, and the
parts of `houses/catlin/DESIGN-LOG.md` and `plans/01-decisions.md` your findings touch.

Baseline: SHA `247a13e9`; `haus check houses/catlin` had exactly 2 FAIL, both
`code.R311_7_1_stair_width` on ST-S2A. Snapshot artifacts are in
`houses/catlin/out/geometry-review-2026-10-31/baseline/` (PDFs + `.json` page maps).

## Ownership

You own the elements and files of your areas ({OWNS}). A fix that needs another cluster's
element or file is **Handed off** (name the cluster), never made across the line. Other
adjudicators edit the same tree concurrently: touch only files you own, and re-read a file
right before editing it.

## Steps

1. **Dedupe** on `dedupe_key` / `seam_with`, including against other clusters' files.
2. **Re-verify** every finding with your own probe (the README snippet; a scratchpad
   script). Reviewers were Sonnet and some ran thin — expect false positives and wrong
   numbers. Reject with a reason. A finding that contradicts a dated `CLAUDE.md` /
   `DESIGN-LOG.md` decision is rejected unless the real-world evidence is strong; then it is
   escalated, not fixed.
3. **Web-check** contested or high-stakes product dimensions yourself (or via a Sonnet
   helper — `model: "sonnet"`).
4. **Classify** with the README fix rubric and **fix the SMALL ones**. You may hand a batch
   of mechanical fixes to up to 2 Sonnet helpers at a time, naming in each brief the exact
   files it owns and repeating these rules.
5. **Targeted verification only.** For each touched module, `grep -rl <module>
   packages/engine/tests` and run just those files: `.venv/bin/python -m pytest <files> -q -n 2`
   (overrides the root `-n 6` to stay light). Then
   `.venv/bin/haus check houses/catlin --plain > <scratch>/check.txt` and diff its FAIL
   lines against the baseline two — **no new FAIL**. Then `.venv/bin/haus build
   houses/catlin --only json`. If a check result is noisy (another agent mid-edit), re-run
   once before acting.
6. **Never**: run the full suite or `scripts/verify.sh`, bless goldens, commit, `git stash`,
   `git checkout --` a file you didn't edit, hand-write a uid (run `.venv/bin/haus fmt
   houses/catlin` after adding an element), or break the `# haus: editable` dialect. Files
   stay under 500 lines. Add a test only where it catches something nothing else does.
   Record which goldens you expect to move (`grep -rl` the golden dirs for touched tags).
7. **Write** `plans/geometry-review/adjudicated/{CLUSTER}.md`:
   - **Fixed** — table: id · change · `path:line` · real-dimension source · before → after
     (measured by probe).
   - **Escalated** — per item: problem + evidence · 2–3 options with a recommendation ·
     blast radius (elements, checks, engineered items/fingerprints, sheets, goldens) ·
     rough size (S/M/L).
   - **Rejected** — id · reason (one line).
   - **Handed off** — id · target cluster · what is needed.
   - **Goldens expected to move** and **tests run** (command + result).

{EXTRA}

Finish with a 6-line summary: counts fixed / escalated / rejected / handed off, the top
escalation, and any check result that moved.
