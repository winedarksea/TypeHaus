---
name: route-run
description: Propose, judge and commit one MEP route on a branch — haus route --alternatives --evaluate, paste, haus fmt, haus trial, look at the drawing. Use when asked to route or re-route a pipe, duct or raceway in this house, or to fix a mep.* finding about where a run goes.
---

# Routing one run: the engine proposes, you commit

**There is no `--write`, and there never will be.** The prose in a plan file *is* the
design record, and accepting a route is a judgement. Everything below is a loop that ends
with a person — or an agent acting as one — pasting a block and saying why.

## The loop

```bash
git switch -c route/<what>                       # never on main; never `git stash`
.venv/bin/haus trial houses/catlin --record      # out/trials/baseline.json, every tier

.venv/bin/haus route houses/catlin --fixture FX-S-SUITEBATH-WC \
    --alternatives 3 --evaluate --explain
```

`--json` gives the same thing as data — the proposal (points, diameter, corridor refs,
cost terms, and the source to paste) beside its evaluation — which is what to read when an
agent is choosing rather than a person.

Read three things before choosing, in this order:

1. **the refusals**, which are printed first and in yellow. A refusal names a number —
   inches of head short, which lane is blocked by which tag, how much of the lattice was
   reachable. It is not a failure of the command; it is the answer.
2. **the evaluation**, which is the MEP checks run against a model *holding* each
   alternative, diffed against the house's own report. `NEW FAIL` is this route's fault.
   `not graded:` lines are holes, and a hole reads as a pass — take them seriously.
3. **the cost breakdown** under `--explain`, in inches of equivalent travel, against the
   weights printed at the top (this house authors them in `preferences.toml`'s
   `[mep.routing]`).

Then paste **exactly one** alternative into the house's own `# haus: editable` file — for
drainage that is `plan/mep_drainage.py`, for air `plan/mep_erv.py`, for raceway
`plan/electrical.py`. Three rules and each is silent when broken:

* **the list you paste into decides the storey**, and the printed elevations are relative
  to it. A `ConduitRun`'s are project-frame absolute and the printout says so.
* **no `uid=`.** `haus fmt` mints one. A hand-written uid is a load-time ERROR.
* **write the reason above it.** A proposal pasted with no sentence is a route nobody can
  argue with later, which is the thing the plan files exist to prevent.

```bash
.venv/bin/haus fmt houses/catlin                 # mints uids, formats the block
.venv/bin/haus trial houses/catlin               # exit 1 on a NEW FAIL
```

Iterate on `NEW FAIL` only. A `NEW UNKNOWN` may be a real gap or may be the check saying
it cannot see this run — read the message.

```bash
.venv/bin/haus render houses/catlin --view plan --fmt png    # and LOOK at it
git add houses/catlin/plan/<the one file> && git commit       # explicit paths only
# or, if it did not work out:
git switch main && git branch -D route/<what>
```

## What order to route in

Gravity first and the tightest first — the terminal with the least head slack has the most
nearly forced route, and RSPH gives the direct lane to whoever goes first
(`notes/mep_drain_routing_basis.md` §5). Then vents, then bulky rigid ducts largest first,
then supply, then conduit. `--tree` already does this inside one main; across mains it is
yours.

## When to conclude the fixture must move

A refusal that names **head** — "short 1.54" of head over 3.15 ft" — is arithmetic, and
only three things change it: raise the start, lower the tie, or shorten the run. When none
of the three is available the honest conclusion is that the *fixture* is in the wrong
place, and that is a design decision to put to the owner, not a weight to tune. Say so in
those words rather than re-running the search with a steeper `--slope` than the code
allows.

A refusal that names **tags** — "the lanes off the origin are inside DU-M-ERV-R-BATH2" —
is congestion. Either `--avoid` something and see what it costs, or re-route the other run
first. The catlin ERV manifold is genuinely full (ten ports at 4" centres); a route out of
it is not a search problem.

## What this loop cannot see yet

Say it out loud in the commit message when it applies:

* **run-vs-run interference** outside a shared soffit or duct bay is not graded at all.
  The NW basement column holds 37 known interpenetrations that nothing reports.
* **stud bores and notches** — R502.8, R602.6 — are on the jurisdiction profile's
  not-covered list.
* **fittings** are counted from turns and never modelled, so a turn no stock elbow makes
  draws as a mitre and passes.
