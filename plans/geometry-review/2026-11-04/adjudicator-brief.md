# Phase 2 adjudicator brief, round 2 — {CLUSTER}

You adjudicate cluster **{CLUSTER} ({NAME})**: findings files {FILES} in
`plans/geometry-review/2026-11-04/findings/`. Read `plans/geometry-review/2026-11-04/README.md`,
round 1's `plans/geometry-review/README.md` (severity, the **fix rubric**, model loading),
the repo `CLAUDE.md`, `houses/catlin/CLAUDE.md`, and the parts of `houses/catlin/DESIGN-LOG.md`
and `plans/01-decisions.md` your findings touch. Round 1's verdicts for your areas are in
`plans/geometry-review/adjudicated/` ({R1_FILES}).

Baseline: SHA `539d9a81`; `haus check houses/catlin` had **0 FAIL**, 208 UNKNOWN
(`houses/catlin/out/geometry-review-2026-11-04/baseline/fail.txt`, `unknown.txt`). Snapshot
artifacts and the gated permit sets are in that folder (PDFs + `.json` page maps).

## Ownership

You own the elements and files of your areas ({OWNS}). A fix that needs another cluster's
element or file is **Handed off** (name the cluster), never made across the line. Other
adjudicators edit the same tree concurrently: touch only files you own, and re-read a file
right before editing it.

## Steps

1. **Confirm every `prior_findings` status with your own probe.** A wrongly "closed" item is
   the worst miss this round can make; a wrongly "open" one wastes the owner's time.
2. **Dedupe** new findings on `dedupe_key` / `seam_with`, across clusters, and against round
   1's **Rejected** lists: a rejected finding re-raised without new evidence is rejected again.
3. **Re-verify** every new finding with your own probe. Reviewers were Sonnet; expect false
   positives and wrong numbers. A finding contradicting a dated `CLAUDE.md` / `DESIGN-LOG.md`
   decision is rejected unless the real-world evidence is strong; then it is escalated.
   **No code or product tables from memory**: read the published row or the engine's table.
4. **Web-check** contested or high-stakes product dimensions yourself, or via a Sonnet helper.
5. **Classify** with the round-1 fix rubric and **fix the SMALL ones**. You may run up to 2
   Sonnet helpers (`model: "sonnet"`) at a time for mechanical fixes or web checks, naming in
   each brief the exact files it owns and repeating these rules.
6. **Targeted verification only.** For each touched module, `grep -rl <module>
   packages/engine/tests` and run just those files:
   `.venv/bin/python -m pytest <files> -q -n 2` (from the repo root). Then
   `.venv/bin/haus check houses/catlin --only all --json > {SCRATCH}/{CLUSTER}/check.json`
   and diff its FAIL lines against the baseline — **no FAIL beyond the Phase 0 list**. Then
   `.venv/bin/haus build houses/catlin --only json`. If a check result is noisy (another
   agent mid-edit), re-run once before acting.
7. **Never**: run the full suite, `scripts/verify.sh` or `haus print`; bless goldens; commit;
   `git stash`; `git checkout --` a file you didn't edit; hand-write a uid (run
   `.venv/bin/haus fmt houses/catlin` after adding an element); break the
   `# haus: editable` dialect. Files stay under 500 lines; comments concise. Add a test only
   where it catches something nothing else does. Probe scripts, caches and pickles go only in
   `{SCRATCH}/{CLUSTER}/` by absolute path. Record which goldens you expect to move
   (`grep -rl` the golden dirs for touched tags).
8. **Write** `plans/geometry-review/2026-11-04/adjudicated/{CLUSTER}.md`:
   - **Reconciled** — table: prior id · status · evidence (your probe, one line).
   - **Fixed** — table: id · change · `path:line` · real-dimension source · before → after
     (measured by probe).
   - **Escalated** — per item: problem + evidence · 2–3 options with a recommendation ·
     blast radius (elements, checks, engineered items/fingerprints, sheets, goldens) · size
     (S/M/L). Tag each `carried (round-1 <id or REPORT item N>)` or `new`.
   - **Rejected** — id · reason (one line).
   - **Handed off** — id · target cluster · what is needed.
   - **Goldens expected to move** and **tests run** (command + result).

{EXTRA}

Finish with a 6-line summary: prior ids by status, counts fixed / escalated / rejected /
handed off, the top escalation, and any check result that moved.
