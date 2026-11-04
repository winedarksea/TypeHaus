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
| `--scorecard --out DIR` | Search and grade the fixed scorecard targets; diff against `tests/data/route_scorecard.json` |

`--summary` supports all proposal selectors, including campaigns, and rejects `--space`
and fixture sweeps. Space views and sweeps keep their separate diagnostic output.

## Plumber's rules

Weights are inches of equivalent travel in `[mep.routing]`; cheapest first: ride a corridor,
ride a rack, pipe, a PEX bend, a fitting, a stud bore, a plate cut, a joist bore, an
exterior wall. Every rule has a hand-worked note (`routing/oracle.py`).

| Rule | Enforced in | Note |
| --- | --- | --- |
| DWV turns by flow direction (UPC 706): level-to-down a 1/4 bend, else a sweep, never up | `RouteCost.turn_cost`, `search.turn_price` | drain basis §10 |
| Members: a bore, plate cut or joist hole priced per cut; an illegal cut is no edge; a riser through a joist or proud of the stud plane is refused | `routing/members.py` | `framing_bore_limits.md` §10 |
| A fitting's room: nipple at least a hub OD, heel clear for the joining tool | `routing/fitting_room.py` | drain basis §10 |
| Short level jogs as a pair of 1/8 bends, re-checked against obstacles | `routing/compaction.py` | drain basis §10 |
| Trap arm within Table 1002.2, no S-trap, vent taken off inside the arm and plumb to 6" over the rim | `routing/trap_vent.py`, `cli/route_fixture_vent.py` | drain basis §9 |
| Branch ties on a level main keep the catalogued inlet pitch | `cli/route_roots._spaced_goals`, `resolve/mep_inlet_spacing` | drain basis §10 |
| Cleanouts (UPC 707.4) placed with 707.9 clearance on the plug axis | `cli/route_cleanouts.py`, `resolve/cleanout_rules.py` | `mep.drain_cleanouts` |
| PEX bends where its 6 x OD arc clears; copper and CPVC take a fitting | `search.bend_price`, `trades/pipe.bend_radius_m` | drain basis §11 |
| Supply and drain in an exterior insulated cavity pay per foot; vents, ducts, conduit exempt | `graph._finish`, `RouteCost.for_run` | drain basis §11 |
| NEC 110.26(E)(1) dedicated space is hard for pipe and duct | `resolve/panel_space.py`, `routing/obstacles` | drain basis §11 |
| A campaign's laid level legs offer rack lanes to the same trade | `routing/rack.py` | drain basis §12 |
| Couplings per stock length are disclosed, not counted (no stock length on record) | `trades/pipe.coupling_disclosure` | — |
| A falling run's arrival holds the 1/16" snap's head; a band that cannot reach any tie by plan distance is dropped | `gravity.grid_allowance`, `gravity.head_floor_fn` | drain basis §13 |
| A falling run crosses rims and joists, never rides them, and never a blocking flange; foundation walls, exterior insulated cavities (at their own height) and the outside of the decks are hard; a tie is pardoned only its own run; the drop into a tie is tested | `gravity_band.rail_prisms`, `obstacles`, `gravity_band.terminal_pardons` | drain basis §13 |
| A tree tie is ON its collector (1/8"); the step into it may cross the collector, never ride or leave it; a branch ties into a plumb drop's side at its own height; a refusal is reported per fixture | `cmd_route_tree.TIE_TOLERANCE_M`, `gravity_band.band_obstacles`, `route_tree_branches.Branches` | drain basis §13 |

**A fixture's arm and vent.** `--fixture` on a drain fixture searches the arm and its vent
together: the arm's reachable take-offs (`arm_reach`) seed the gravity search at their arm
cost plus the vent's cost-to-go, and the vent is read back off a 3D lattice in which
finished rooms are hard. The pair is proposed and evaluated together (`A + B`). A refusal
names the cheapest take-off's first blocker. **Cleanouts** a proposed drain needs are placed
on it, each with access (wall, floor or ceiling), cap point and concealment; a concealed
one pays `cleanout_concealed_in`.

**Limitations.** Wet vents are ungraded in `arm_is_vented`; seeds keep the two cheapest
take-offs (`keep=2`); a vertical barrel's stack pitch is left to the check; a tie's fitting
is named but not priced; `--manifold` and trunk topologies are not implemented (no water
manifold is modelled); rack lanes exist only inside `--house` campaigns. `--tree` prints each
branch graded alone, so a branch meets the authored drain another branch replaces; the
scorecard grades the tree as one network.

## Interpret and accept

Read refusals, evaluation changes, and coverage gaps before comparing route costs. An
UNKNOWN or ungraded area is not a pass. Missing fitting patterns and laying lengths
remain disclosed; a route's centreline does not establish a fitting's physical clearance.
Authored duct sizes win over equal-friction advice. Approximate equipment ports remain
preliminary; exact ports constrain the termination.

An exact port with a `ServicePort.direction` is also left along that axis: the search starts
(or ends) at the tip of a straight stub, one outside diameter plus a 2" fitting allowance
(`cli/route_ports.py`), and the stub is put back on the found path, so a water heater's
upward port yields a vertical first leg. A stub that runs into anything but its own machine
is a refusal naming the obstruction. Oblique directions, approximate ports, tee lines and
gravity runs are not constrained.

Blocker mobility comes from geometry kind: fixed, movable service, priced volume, or
unknown. A failed search is not proof of impossibility: inspect `established`, the searched
margin, shortages, and reachable-node counts. A counterfactual prices a world with one
blocker lifted; that blocker still needs a route. A sweep moves the drain point, not the
fixture, and does not establish trap-arm or fixture-clearance compliance.

Campaigns normally lay drains deepest first, then vents, ducts largest first, supply, and
conduit. Accepted proposals occupy space for later searches. Rip-up only lifts proposals
accepted by that campaign; authored geometry remains an obstacle.

A conduit proposal keeps its raceway's pull boxes (`ConduitRun.pull_points`). Authored boxes
the new path still passes within 6" are kept (a vertex is inserted beside a straight stretch);
the rest are dropped and counted. Then a pull point goes at any vertex that would take a
section past 360 degrees of bends (the `conduit_pulls` measure). The proposal prints
`pull_points=(...)`, notes `pull points: kept N authored, added N, N no longer on the path`,
and carries `pull_point_assignment` in the JSON. `material` and `circuits` are echoed too.

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
| Plumber's rules | `routing/members`, `fitting_room`, `compaction`, `trap_vent`, `rack` | `test_routing_members`, `test_routing_compaction`, `test_routing_trap_vent`, `test_routing_supply` |
| Fixture vent, cleanouts | `cli/route_fixture_vent`, `cli/route_cleanouts`, `resolve/cleanout_rules` | `test_drain_cleanouts` |
| Scorecard | `cli/route_scorecard` | `test_route_scorecard` (`-m autorouter`) |
| Campaign policy | `routing/campaign` | `test_routing_campaign`, `test_routing_campaign_cli` |
| Candidate grading | `cli/route_eval` | `test_route_eval` |
| Shared geometry | `resolve/mep_envelopes`, `resolve/mep_bores`, `resolve/mep_fittings` | Corresponding MEP tests |

Routing imports model/resolve/quantities, never checks. Only CLI adapters coordinate the
router with its grader; `test_package_leaves` enforces the dependency boundary. Independent
numerical notes remain in `houses/catlin/notes/mep_drain_routing_basis.md`,
`mep_duct_routing_basis.md`, and `vent_grade_basis.md`; `routing/oracle.py` maps them to
modules and tests. Keep equations, tolerances, and local algorithm invariants beside code.

`test_routing_campaign_cli` runs a real campaign and is opt-in: after editing
`typehaus/routing/`, run `pytest packages/engine/tests/test_routing_campaign_cli.py --autorouter`.
