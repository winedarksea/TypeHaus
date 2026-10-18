# MEP routing

`haus route` proposes geometry; independent checks grade it. Accept a proposal by editing
the house's authored plan and updating its design explanation. `--out` saves review
artifacts outside `plan/`; it never applies a route.

## Start with a decision report

```bash
.venv/bin/haus route houses/catlin --run PR-B-KITCH-DRAIN \
    --alternatives 3 --json --summary --out out/route/kitchen
```

`--json` implies evaluation. `--summary` requires `--json --out DIR` and retains candidate
tags, storeys, lengths, bends, costs, evaluation changes, blocker diagnostics, coverage
gaps, fitting gaps, and follow-up work. Coordinates, constructor source, and detailed cost
terms remain in `DIR/report.json`. `DIR/proposed.py` groups source by storey and labels
alternatives: paste exactly one per target.

For example, read one candidate's full details without searching again:

```bash
jq '.proposals[] | select(.tag == "PR-B-KITCH-DRAIN-PROPOSED-A")' \
    out/route/kitchen/report.json
```

Full JSON goes to stdout as one document, including refusals and partial/empty results.
Warnings, timing, and counterfactual text are report data rather than extra console lines.
Individual reports use `proposals`; campaigns use `accepted`. Both include `evaluations`.
Campaign evaluations grade the accepted network together. An empty network is explicitly
ungraded. Without evaluation, the evaluation list is empty, which does not imply a pass.

Exit codes retain the existing contract: single/tree proposals exit 1 when none can be
made, while a partial proposal set exits 0; campaigns exit 1 if any target was refused.
An empty scope exits 0. Invalid options exit 2. Evaluation findings do not change these
routing exit codes.

## Choose the question

| Selector / option | Question |
| --- | --- |
| `--run TAG` | Same authored terminals, a better route |
| `--fixture TAG` | A drain branch from the fixture to its nearest main |
| `--tree MAIN` | All fixtures served by this drain main, coordinated together |
| `--unconnected` | Branches for fixtures reported by `mep.fixture_drain_reach` |
| `--house --trades drain --storey basement` | Coordinate a scoped campaign with shared occupancy |
| `--alternatives N` | Distinct lanes for a target; incompatible with trees |
| `--orders N` | Try up to three campaign conflict orders; fewest refusals ranks first |
| `--locked TAG` / `--rip-up N` | Preserve an authored run / bound campaign rip-up |
| `--level STOREY` | Restrict the search's elevation band; distinct from target `--storey` |
| `--hold-upstream N` | Preserve the first N authored legs of a `--run` |
| `--counterfactual` | Diagnose whether lifting one movable blocker opens a route |
| `--fixture TAG --sweep 8` | Try drain-point stations within eight inches along its wall |
| `--space TAG --out DIR` | Classify routing space and save one SVG per elevation |
| `--explain` / `--timing` | Cost weights and terms / build and search measurements |

`--summary` supports all proposal selectors, including campaigns, and rejects `--space`
and fixture sweeps. Space views and sweeps keep their separate diagnostic output.

## Interpret and accept

Read refusals, evaluation changes, and coverage gaps before comparing route costs. An
UNKNOWN or ungraded area is not a pass. Missing fitting patterns and laying lengths
remain disclosed; a route's centreline does not establish a fitting's physical clearance.
Authored duct sizes win over equal-friction advice. Approximate equipment ports remain
preliminary; exact ports constrain the termination.

Blocker mobility comes from geometry kind: fixed, movable service, priced volume, or
unknown. A failed search is not proof of impossibility: inspect `established`, the searched
margin, shortages, and reachable-node counts. A counterfactual prices a world with one
blocker lifted; that blocker still needs a route. A sweep moves the drain point, not the
fixture, and does not establish trap-arm or fixture-clearance compliance.

Campaigns normally lay drains deepest first, then vents, ducts largest first, supply, and
conduit. Accepted proposals occupy space for later searches. Rip-up only lifts proposals
accepted by that campaign; authored geometry remains an obstacle.

Paste into the correct storey's `# haus: editable` source and explain why it changed.
Pipe/duct elevations are relative to that storey; conduit elevations are project-frame
absolute. Let `haus fmt` mint uids. Record a `haus trial --record` baseline before editing,
then run `haus fmt`, `haus trial`, inspect the drawing, and run repository verification.

## Read only the relevant implementation

| Responsibility | Modules under `packages/engine/src/typehaus/` | Tests |
| --- | --- | --- |
| CLI, reports, artifacts | `cli/cmd_route*`, `cli/route_report` | `test_route_reporting`, `test_cmd_route` |
| Terminals and tie-ins | `cli/route_support`, `cli/route_roots`, `resolve/mep_ports` | `test_cmd_route`, `test_route_metadata` |
| Space and graph | `routing/space`, `routing/obstacles`, `routing/graph` | `test_routing_graph`, `test_routing_perf_guard` |
| Search and gravity | `routing/search`, `routing/gravity*`, `routing/tree` | `test_routing_oracle`, `test_gravity_search`, `test_routing_vent` |
| Campaign policy | `routing/campaign` | `test_routing_campaign`, `test_routing_campaign_cli` |
| Candidate grading | `cli/route_eval` | `test_route_eval` |
| Shared geometry | `resolve/mep_envelopes`, `resolve/mep_bores`, `resolve/mep_fittings` | Corresponding MEP tests |

Routing imports model/resolve/quantities, never checks. Only CLI adapters coordinate the
router with its grader; `test_package_leaves` enforces the dependency boundary. Independent
numerical notes remain in `houses/catlin/notes/mep_drain_routing_basis.md`,
`mep_duct_routing_basis.md`, and `vent_grade_basis.md`; `routing/oracle.py` maps them to
modules and tests. Keep equations, tolerances, and local algorithm invariants beside code.
