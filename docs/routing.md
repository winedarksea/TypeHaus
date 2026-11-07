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
| `--run TAG` | Same authored terminals, a better route; a duct uses the fitted search (take-off C2F·tan(θ/2), a 12" flex `PortKit` lead) |
| `--fixture TAG` | A drain branch from the fixture to its nearest main |
| `--tree MAIN` | All fixtures served by this drain main, coordinated together |
| `--tree MAIN --lift TAG...` | Tree rip-up: the named authored runs are lifted and re-laid after the tree, each laid or refused with a reason |
| `--group ROOM` | A bathroom group in UPC 908.2 order: dry arm and its vent, 3" wet vent, water closet last |
| `--tree COLD-MAIN [--topology trunk\|tree]` | A cold supply main as a z-gated trunk plus farthest-first branches; `trunk` tees only onto the trunk or the branch's own group, `tree` (default) onto any branch laid before it. Cold only; hot is refused |
| `--unconnected` | Branches for fixtures reported by `mep.fixture_drain_reach` |
| `--house --trades drain --storey basement` | Coordinate a scoped campaign with shared occupancy |
| `--manifold EQ-TAG` | Every supply branch leaving that manifold's outlet ports, as one campaign |
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
| A 3-D lattice adds a corridor's plane only where no kept plane lies inside its window | `graph._merged_levels` | duct basis §5 |
| A falling run's start with no lane to any tie (rises, too-shallow windows, prisms spanning tie to ceiling) is refused before the search | `gravity.tie_reach` | drain basis §13 |
| Couplings per stock length are disclosed, not counted (no stock length on record) | `trades/pipe.coupling_disclosure` | — |
| A falling run's arrival holds the 1/16" snap's head; a band that cannot reach any tie by plan distance is dropped | `gravity.grid_allowance`, `gravity.head_floor_fn` | drain basis §13 |
| A falling run crosses rims and joists, never rides them, and never a blocking flange; foundation walls, exterior insulated cavities (at their own height) and the outside of the decks are hard; a tie is pardoned only its own run; the drop into a tie is tested | `gravity_band.rail_prisms`, `obstacles`, `gravity_band.terminal_pardons` | drain basis §13 |
| A trunk's level legs stay inside the floor system's z gate; a riser only in a 24" hole at each end | `routing/supply_tree`, `cli/cmd_route_supply_tree` | `mep_supply_trunk_basis.md` §5 |
| A branch tees only onto a run that can carry its WSFU, up the whole host chain | `cli/route_supply_group` | `mep_supply_trunk_basis.md` §2 |
| A buried outdoor run is left as authored | `cli/cmd_route_supply_tree` | `mep_supply_trunk_basis.md` §3 |
| Tree rip-up: most recent branch first, at most two trials per refused terminal, exact rollback of a failed trial | `routing/tree_ripup` | `mep_tree_ripup_basis.md` §1 |
| A bathroom group lays in role order (dry drain and vent, wet arms in flow order, the closet last), each step re-resolved | `routing/group_order`, `cli/cmd_route_group` | `mep_group_wet_vent_basis.md` §3 to §5 |
| Two duct turns may not sit closer than their take-offs; a turn beside a run end owes only its own | `routing/duct_fittings`, `routing/duct_search` | duct basis §7 |
| A port kit's flex is a straight lead that never bends; the search starts at its far end | `routing/duct_fittings`, `cli/route_ports` | duct basis §8 |
| Rip-up P8: a branch refused on size is re-laid one DWV size up in a world round its own lane, to the tie it had; the rest of the tree stands | `cli/route_tree_upsize`, `routing/tree_ripup` | `mep_tree_ripup_basis.md` §4.3 |
| A falling profile is snapped to 1/16" from the arrival up, each leg's fall rounded up; the search and the proposal read one rule | `routing/gravity_grid` (`on_grid`, `grid_start`) | drain basis §13 |
| A refusal names what stopped the furthest-reaching label (its path), not the tightest miss anywhere in the search | `GravityRefusal.front`, `settle` | drain basis §13 |
| An I-joist hole stays "2 x the larger hole" from every authored hole in the same joist (ESR-1153 Table A fn1); a run the search may occupy is not counted | `routing/members` (`_authored_holes`), `resolve/mep_hole_chart` | `framing_bore_limits.md` §10 |
| Open-web chords are flange prisms along each truss: a run crosses a truss through its web window, never rides inside a chord | `routing/obstacles` | drain basis §13 |
| A turn back along its own axis (a lav arm out to its wall tee and back) stays a vertex through simplification; its take-off is that vertex (UPC 908.2) | `routing/search._reverses`, `RouteProposal.snapped` | group basis §3 to §5 |
| 908.2 is graded strictly: a child rising more than it runs is a 908.1 vertical wet vent, a dry-vented lavatory's drop included; a closet may drop to the drain | `resolve/mep_trap_arm.grade_wet_vent`, `cli/route_fixture_wet` | group basis §4, §5 |
| A duct search is bounded at 1,000,000 labels or 45 s, then refuses with `stopped` set ("a budget, not a proof"); a step that would cross the route's own lane is refused | `routing/duct_search` | duct basis §7.2 |
| A duct proposal carries its `DuctStandard`; an elbow snaps within 10 degrees of the stamped angles, the one snap the catalog and the bill share | `RouteProposal.duct_standard`, `resolve/duct_standard.ELBOW_SNAP_DEG` | duct basis §7.5 |
| Condensate (`sanitary=False`) is laid at 1/4"/ft and goes to 3/16 or the IMC 307.2.1 floor of 1/8 only when that beats the 768 in-per-in/ft penalty (or 1/4 refuses); `mep.drain_slope` FAILs below 1/8 and ADVISES below 1/4; cleanouts only on sanitary runs | `routing/gravity.graded_route`, `resolve/mep_slope`, `cli/route_cleanouts` | `mep_condensate_routing_basis.md` §4, §5, §8 |
| A tree tie is ON its collector (1/8"); the step into it may cross the collector, never ride or leave it; a branch ties into a plumb drop's side at its own height; a refusal is reported per fixture | `cmd_route_tree.TIE_TOLERANCE_M`, `gravity_band.band_obstacles`, `route_tree_branches.Branches` | drain basis §13 |

**A fixture's arm and vent.** `--fixture` on a drain fixture searches the arm and its vent
together: the arm's reachable take-offs (`arm_reach`) seed the gravity search at their arm
cost plus the vent's cost-to-go, and the vent is read back off a 3D lattice in which
finished rooms are hard. The pair is proposed and evaluated together (`A + B`). The arm is
laid at the trap — a tub, shower or floor drain at the floor traps 3" under its datum
(`under_floor_weir_m`) — holds grade to the take-off, and drops plumb there (`route_fall`).
An arm that may end on a dry-vented bathroom-group drain as a UPC 908.2 wet vent is offered
that join as a goal, graded by the check's own walk (`route_fixture_wet`,
`resolve/mep_wet_tie`); the proposal then carries no vent, and its notes say which runs to
upsize and which vent's `serves` to extend. A fixture whose authored arm already meets a vent
(wet vents graded) is noted and its drain proposed alone. A refusal prints a **take-off
table**: every candidate, its wall and arm length, and the first thing a plumb riser from
the arm meets (`route_takeoff_table`); `--counterfactual` lifts those blockers in the vent
lattice too, and `--summary` drops each row's station. **Cleanouts** a proposed drain needs are placed
on it, each with access (wall, floor or ceiling), cap point and concealment; a concealed
one pays `cleanout_concealed_in`.

**Limitations.** `--fixture` offers a wet vent only onto a drain already authored (`--group`
lays the whole group); seeds keep the two cheapest take-offs (`keep=2`); a vertical barrel's
stack pitch is left to the check; a tie's fitting is named but not priced; rack lanes exist
only inside `--house` and `--manifold` campaigns. `--tree` prints each branch graded alone, so
a branch meets the authored drain another branch replaces; the scorecard grades the tree as
one network. Neither catlin bathroom group lays on today's geometry (the supply lanes stop
it). On `tree:main`, P8 re-lays BATH2-TUB one size up onto BATH2-SH; 7 of 8 branches lay in about
83 s and one still refuses (read the scorecard row for which). The stamped Linx elbow has no published centre-to-face (the 1.5 D gored
radius stands in), and the flex bend radius and the GV0772 transition length are unread
(counted 0, and said so).

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

**What a proposal replaces.** `--evaluate` removes from the candidate plan the run of the
proposal's own name and any same-system run whose `serves` it covers, so a route is never graded
against its own ghost. `RouteProposal.replaces`, when set, is the whole answer: a supply trunk
serving what its service lateral serves must not delete the lateral, and a tree stands in for
runs no tag names. Otherwise a run the proposal ties INTO (an ancestor of what it replaces, with
an end of the proposal on it) stays, however much of its `serves` the proposal covers
(`route_eval._replaced_tags`, `_tied_into`).

**A target whose terminals cannot be derived** (no sump pump names its line; the receiver has
no modelled riser; nothing downstream of a drain) is an `EndpointRefusal`: a `Refusal` with no
lattice counts and `cause`, `element` and `fix` in its payload. It renders as the old line.

Blocker mobility comes from geometry kind: fixed, movable service, priced volume, or
unknown. A failed search is not proof of impossibility: inspect `established`, the searched
margin, shortages, and reachable-node counts. A counterfactual prices a world with one
blocker lifted; that blocker still needs a route. A sweep moves the drain point, not the
fixture, and does not establish trap-arm or fixture-clearance compliance.

`--manifold EQ-TAG` targets each supply run whose tie-in resolves to an exact outlet port
of that machine (`resolve/mep_tie_ins`: a first vertex on a port outranks a run passing
over it). Each search ends at its port's stub tip, and the branches share one occupancy, so
`--orders`, `--rip-up`, exit codes and `--json --summary` are the campaign's.
`mep.water_manifold_ports` grades that every outlet carries exactly one run.

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

## Minor systems

- **Condensate** (`sanitary=False`) falls at the engine's drain grade, 1/4"/ft; Rheem's 1/8" is
  second-hand and not encoded. Its parent is where it was authored to land, at the parent's
  invert there (`route_roots._landing`), not the chain's lowest vertex. No cleanouts.
- **Radon** campaigns as a vent (it rises to the same stack); **sump discharge** as supply (a
  pumped line has no grade, and the goal is fixed). Gas has no trade and is named in `skipped`.
- **Sump discharge** roots on the receiver's derived riser (`<receiver>-EXT-RISER`) at the line's
  authored end elevation, and is held through its cast sleeve (`SP-B-N4-SUMP`, `sleeve_hold`) like
  `--hold-upstream`: the tail from the first vertex past the wall is searched, never under the
  footing (UPC 314.1).
- **Cleanouts** (UPC 707.4) are placed on sanitary runs only.

## Limitations

- `--lift` cannot re-lay a supply that has tees: it refuses ("loses N") rather than orphan them.
- Vent-free 908.2 bathroom groups are not proposed; whether 908.2 admits a dry-vented lavatory's
  drop is an AHJ question.
- The duct catalog has no adjustable set-down, so an off-angle turn like `DU-B-ERV-R-GYM`'s 18.2
  degrees stays an ungraded fitting.
- The `PR-B-BATH-VENT` lattice exceeds `MAX_LATTICE_NODES` (600,000).
- The supply trunk's remaining evaluation fails are router and model gaps: open-air risers,
  spacing from existing bores, and a terminal inside a duct.
- A full scorecard run takes about 7 minutes: rows run in forked workers (`HAUS_SCORECARD_JOBS`,
  default min(4, cores/2)) and the longest row (`tree:main`, about 107 s) sets the floor.

## Read only the relevant implementation

| Responsibility | Modules under `packages/engine/src/typehaus/` | Tests |
| --- | --- | --- |
| CLI, reports, artifacts | `cli/cmd_route`, `cli/route_propose` (one proposal pass), `cli/route_options` (parsed options, `not_built`), `cli/route_report` | `test_route_reporting`, `test_cmd_route` |
| Terminals and tie-ins | `cli/route_support`, `cli/route_endpoints_duct` (duct and raceway ends), `cli/route_roots`, `resolve/mep_ports` | `test_cmd_route`, `test_route_metadata` |
| Drain tree, rip-up, lift | `cli/cmd_route_tree`, `cli/route_tree_group`, `cli/route_tree_branches`, `cli/route_tree_lift`, `cli/route_tree_upsize`, `cli/route_tree_ledger`, `routing/tree_ripup` | `test_routing_tree_ripup`, `test_cmd_route` |
| Bathroom group (908.2) | `cli/cmd_route_group`, `routing/group_order` | `test_routing_group` |
| Supply trunk and tree | `cli/cmd_route_supply_tree`, `cli/route_supply_group`, `routing/supply_tree` | `test_routing_supply_tree` |
| Fitted duct search | `cli/route_duct_search` (the one entry), `routing/duct_search`, `routing/duct_fittings`, `cli/route_ports` | `test_routing_duct_fittings` |
| Space and graph | `routing/space`, `routing/obstacles`, `routing/graph` | `test_routing_graph`, `test_routing_perf_guard` |
| Search and gravity | `routing/search`, `routing/gravity*` (incl. `gravity_grid`), `routing/tree` | `test_routing_oracle`, `test_gravity_search`, `test_routing_vent`, `test_routing_hole_spacing` |
| Minor systems | `cli/route_roots` (sump and condensate ends), `routing/campaign` (trades) | `test_routing_minor_systems` |
| Plumber's rules | `routing/members`, `fitting_room`, `compaction`, `trap_vent`, `rack` | `test_routing_members`, `test_routing_compaction`, `test_routing_trap_vent`, `test_routing_supply` |
| Fixture vent, cleanouts | `cli/route_fixture_vent`, `cli/route_cleanouts`, `resolve/cleanout_rules` | `test_drain_cleanouts` |
| Scorecard | `cli/route_scorecard`, `route_scorecard_targets` (rows), `route_scorecard_modes` (how each mode is proposed) | `test_route_scorecard` (`-m autorouter`) |
| Campaign policy | `routing/campaign` | `test_routing_campaign`, `test_routing_campaign_cli` |
| Candidate grading | `cli/route_eval` | `test_route_eval` |
| Shared geometry | `resolve/mep_envelopes`, `resolve/mep_bores`, `resolve/mep_fittings` | Corresponding MEP tests |

Routing imports model/resolve/quantities, never checks. Only CLI adapters coordinate the
router with its grader; `test_package_leaves` enforces the dependency boundary. Independent
numerical notes remain in `houses/catlin/notes/mep_drain_routing_basis.md`,
`mep_duct_routing_basis.md`, `vent_grade_basis.md`, `mep_tree_ripup_basis.md`,
`mep_group_wet_vent_basis.md`, `mep_supply_trunk_basis.md` and `mep_condensate_routing_basis.md`; `routing/oracle.py` maps them to
modules and tests. Keep equations, tolerances, and local algorithm invariants beside code.

`test_routing_campaign_cli` runs a real campaign and is opt-in: after editing
`typehaus/routing/`, run `pytest packages/engine/tests/test_routing_campaign_cli.py --autorouter`.
