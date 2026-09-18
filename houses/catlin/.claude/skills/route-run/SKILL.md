---
name: route-run
description: Propose, judge and commit one MEP route on a branch — haus route --alternatives --evaluate (--counterfactual, --sweep), paste, haus fmt, haus trial, look at the drawing. Use when asked to route or re-route a pipe, duct or raceway in this house, or to fix a mep.* finding about where a run goes.
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
is congestion. Every blocker now carries a **mobility class**, and it tells you which move
to make:

* `movable` (another run) — re-route that one first, or run `--counterfactual` to find out
  whether moving it is even enough before you spend the effort:

  ```
  .venv/bin/haus route houses/catlin --run PR-B-KITCH-DRAIN --counterfactual
  ```

  It lifts one movable blocker at a time and prices what opens. **It is a diagnosis, not a
  proposal**: it does not say where the lifted run would go instead, and "a route exists if
  X moved" is not permission for X to move.
* `fixed` (a rough opening, a void, concrete) — nothing to negotiate. If every blocker is
  fixed the refusal says so in those words ("established from the geometry"), and that is
  the sentence to quote rather than re-running the search.
* `unknown` — usually your own `--avoid`. Drop it and see.

Read the refusal's last clause before anything else: **"not within this search"** means try
a wider `--margin` or a different order; **"established from the geometry"** means stop.

## Asking whether the FIXTURE should move

Before concluding a fixture is in the wrong place, ask:

```
.venv/bin/haus route houses/catlin --fixture FX-S-SUITEBATH-WC --sweep 8
```

This walks the derived drain point along the fixture's `wall_ref` in 2" steps — clamped to
the wall, skipping stations that would land in a stud — and prints what each buys. The best
one comes back as a `Fixture(...)` with `drain_position` set.

Two cautions. It moves the **drain point**, not the china: `drain_position` is the override
the model already has for where the waste actually drops. And a station it calls feasible is
feasible *to route* — whether the moved drain still clears its trap arm and its clearance
zone is what `haus trial` tells you after you paste it. "NO station on this wall routes" is
also an answer: the obstruction is not where the fixture stands.

## What this loop cannot see yet

Say it out loud in the commit message when it applies:

* **fittings** are counted from turns and never modelled, so a turn no stock elbow makes
  draws as a mitre and passes (roadmap Phase 5).
* **whole-house coordination** — routing one run at a time cannot find the order that makes
  all of them fit, and there is no rip-up-and-re-route (Phase 6).
* **a duct's size is advised, never applied.** `--explain` prints what the air wants at the
  house's design friction rate; the authored size always wins. DU-B-ERV-SUP-TRUNK is drawn
  4x under it and that is a real, known, deliberate fact about this house.
* **two lanes in one bay** are a capacity statement, not an arrangement: the model gives a
  run one centreline per bay, so `mep.duct_joist_bay_occupancy` can say the bay holds them
  and cannot say they were drawn side by side.

Run-vs-run interference and stud/plate bores used to be on this list. Both are graded now
(`mep.run_interference`, `mep.run_through_stud`, `mep.run_through_plate`) — which is why
`preferences.toml` carries two blanket suppressions with their counts and dates beside them.
Deleting one and re-running `haus check` is how that debt gets measured.
