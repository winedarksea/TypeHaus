# MEP routing

`haus route` proposes geometry; independent checks grade it. Accept a proposal by editing
the house's authored plan and updating its design explanation. `--out` saves review
artifacts outside `plan/`; it never applies a route.

## Start with a decision report

```bash
.venv/bin/haus route houses/catlin --run PR-B-KITCH-DRAIN \
    --alternatives 3 --json --summary --out out/route/kitchen
```

`--json` implies evaluation. `--summary` requires `--json --out DIR` and prints one line of
bounded **decision view** `{house, storey, decision, artifacts}` (`cli/route_decision.py`),
built from the report dict alone so `proposals` and `accepted` runs read the same:

- `decision.completion`: termination, refused/skipped targets, refusals with blockers grouped
  by tag and mobility, problems.
- `decision.candidates.items[]`: each proposal's developed ft, bends, cost, fittings
  (count/gaps), bores by member kind, cleanouts placed/required, `after_paste`, and a `grade`.
- `grade`: evaluated / refused (reason) / ungraded, FAIL and UNKNOWN counts per check group
  (`route_check_groups.GROUPS`), clash tags with mobility, coverage gaps, and at most three
  representative findings, each with a JSON pointer into `report.json`
  (`/evaluations/<i>/introduced/<j>`). A campaign's network grade is `decision.network`.

Lists are capped (3 to 20 items) and each `{count, items}` reports the true count. Full
messages, coordinates, source and cost terms stay in `DIR/report.json`; open it by pointer.
`DIR/proposed.py` groups source by storey and labels alternatives: paste exactly one per
target. `proposed.py`, `report.json`'s `source` and the console all print
`RouteProposal.full_source` — the run followed by its `DrainCleanout`s, exactly the elements
`--evaluate` grades; paste the whole block.

Alternatives are the found route repriced on the original graph: cost, terms, bends and
corridor tags are replaced, and gravity metadata (start elevation, take-off, wet/vent, grade)
is kept. A gravity search's alternatives price turns with the drain table, like route A. Each
duct search counts its own labels against its budget; `reached` is a cumulative diagnostic.

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
| `--hold-upstream N` | Keep N authored legs at the search origin: the first N of a drain or vent `--run`, the last N (fixture end) of a supply |
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
| Cleanouts (UPC 707.4) placed with 707.9 clearance on the plug axis; priced `cleanout_in` each, + `cleanout_concealed_in` behind a panel, + `cleanout_floor_finished_in` for a floor cap in a priced room; a buried station may rise in a partition cavity instead; cheapest station wins. `--tree`/`--lift` place them once the whole tree is laid (`place_tree_cleanouts`): requirements read off the network as the check reads it, one on an authored run only noted; a floor cap hidden only by the served fixture's own cabinet is a `cabinet` cleanout (cap 12" up, priced concealed) | `cli/route_cleanouts.py`, `resolve/cleanout_rules.py` | `mep.drain_cleanouts` |
| PEX bends where its 6 x OD arc clears; copper and CPVC take a fitting | `search.bend_price`, `trades/pipe.bend_radius_m` | drain basis §11 |
| Supply and drain in an exterior insulated bay pay by the side they run on: the cold side (where `mep.supply_freeze_exposure` puts the pipe face under 42 F, or any bay with no continuous insulation outboard) `exterior_wall_per_ft` per foot plus `exterior_cold_edge_in` per edge, the warm side `exterior_warm_per_ft`; vents, ducts, conduit exempt | `routing/freeze_bay`, `graph_batch.room_lengths`, `RouteCost.for_run` | `supply_freeze_basis.md` §4-§5 |
| A room charges by the length of an edge inside it (a riser by its z overlap), summed over overlapping rooms | `graph_batch.room_lengths`, `RouteCost.segment_cost(rooms=)` | — |
| NEC 110.26(E)(1) dedicated space is hard for pipe and duct | `resolve/panel_space.py`, `routing/obstacles` | drain basis §11 |
| A campaign's laid level legs offer rack lanes to the same trade | `routing/rack.py` | drain basis §12 |
| A 3-D lattice adds a corridor's plane only where no kept plane lies inside its window | `graph._merged_levels` | duct basis §5 |
| A falling run's start with no lane to any tie (rises, too-shallow windows, prisms spanning tie to ceiling) is refused before the search | `gravity.tie_reach` | drain basis §13 |
| Couplings per stock length are disclosed, not counted (no stock length on record) | `trades/pipe.coupling_disclosure` | — |
| A falling run's arrival holds the 1/16" snap's head; a band that cannot reach any tie by plan distance is dropped | `gravity.grid_allowance`, `gravity.head_floor_fn` | drain basis §13 |
| A falling run crosses rims and joists, never rides them, and never a blocking flange; foundation walls, exterior insulated cavities (at their own height) and the outside of the decks are hard; a tie is pardoned only its own run; the drop into a tie is tested | `gravity_band.rail_prisms`, `obstacles`, `gravity_band.terminal_pardons` | drain basis §13 |
| A trunk's level legs stay inside the floor system's z gate; a riser only in a 24" hole at each end | `routing/supply_tree`, `cli/cmd_route_supply_tree` | `mep_supply_trunk_basis.md` §5 |
| A branch tees only onto a run that can carry its WSFU, up the whole host chain | `cli/route_supply_group` | `mep_supply_trunk_basis.md` §2 |
| A pipe riser stands in wall cover or a soffit, never a finished flat-ceiling room's open air, except at the route's own ends, or inside a served fixture's body holding one and under its top (the check's `fixture_trim`), in the room they stand in, or behind floor-standing casework a countertop sits on, under its top (`casework_cover`, #130); a supply branch with no such lane is laid last with cover off and noted | `resolve/riser_cover`, `routing/members.cuts` | `mep.run_in_finished_volume`, `mep_supply_trunk_basis.md` §5a |
| A fixture end inside a door swing or a duct moves to the nearest legal point on its own wall, or (its riser column crossing one) is refused with a typed `TerminalBlock`; a swing or duct is pardoned at the terminal's own level only | `routing/terminal_block`, `graph.build_graph` | — |
| `--lift` keeps a supply's tees: only branches derived to tee on it count, their legs are held as authored, and a lifted branch tees onto its feeder's re-laid line | `cli/route_tree_lift`, `cli/route_supply_roots` | `mep_tree_ripup_basis.md` §3 L6-L9 |
| A buried outdoor run is left as authored | `cli/cmd_route_supply_tree` | `mep_supply_trunk_basis.md` §3 |
| Tree rip-up: most recent branch first, at most two trials per refused terminal, exact rollback of a failed trial | `routing/tree_ripup` | `mep_tree_ripup_basis.md` §1 |
| A bathroom group lays in role order (dry drain and vent, wet arms in flow order, the closet last), each step re-resolved | `routing/group_order`, `cli/cmd_route_group` | `mep_group_wet_vent_basis.md` §3 to §5 |
| Two duct turns may not sit closer than their take-offs; a turn beside a run end owes only its own | `routing/duct_fittings`, `routing/duct_search` | duct basis §7 |
| A port kit's flex is a straight lead that never bends; the search starts at its far end | `routing/duct_fittings`, `cli/route_ports` | duct basis §8 |
| Rip-up P8: a branch refused on size is re-laid one DWV size up in a world round its own lane, to the tie it had; the rest of the tree stands | `cli/route_tree_upsize`, `routing/tree_ripup` | `mep_tree_ripup_basis.md` §4.3 |
| A falling profile is snapped to 1/16" from the arrival up, each leg's fall rounded up; the search and the proposal read one rule | `routing/gravity_grid` (`on_grid`, `grid_start`) | drain basis §13 |
| A refusal names what stopped the furthest-reaching label (its path), not the tightest miss anywhere in the search | `GravityRefusal.front`, `settle` | drain basis §13 |
| A floor crossing keeps clear of the holes already there, authored or laid earlier in the campaign: I-joist "2 x the larger hole" (ESR-1153 Table A fn1); an open-web crossing lands in an opening it fits, one run per D pocket | `routing/holes`, `resolve/mep_hole_chart`, `resolve/open_web` | `framing_bore_limits.md` §10-11, §14 |
| A floor's solid cross members (strongback, blocking, ledger, a solid-sawn sister) are bored only within D/3 (IRC R502.8.1, `joist_bore`, the check's own call): a legal crossing is priced as a joist bore, an illegal one is refused, and a falling run gets banded prisms to pass over or under | `routing/floor_bars`, `resolve/mep_crossings.is_solid_floor_member` | `framing_bore_limits.md` §15 |
| A tree's stack takes a wye anywhere down its plumb leg inside the tie band: its tie heights are rungs, tried highest first, each fixture tying at the first rung that routes; a fixture on the stack's own column keeps the head's verdict | `cli/cmd_route_tree` (`_stack_rungs`), `Branches.drop_top` | `mep_tree_ripup_basis.md` §6 |
| A level edge through a blocked bearing-line bay stays inside its 2x6 box (crown under the top rail, sides in the bay); risers pass | `routing/bearing_bays`, `resolve/floor_blocking.bearing_bays` | `mep.run_through_blocking` |
| A falling run crosses a truss only at a height a free opening leaves it there: the complement of each station's bands is forbidden, a station with none is an all-z block naming the pocket's holder | `routing/gravity_webs`, `resolve/open_web.station_bands` | `framing_bore_limits.md` §13 |
| Open-web chords are flange prisms along each truss: a run crosses a truss through its web window, never rides inside a chord | `routing/obstacles` | drain basis §13 |
| A turn back along its own axis (a lav arm out to its wall tee and back) stays a vertex through simplification; its take-off is that vertex (UPC 908.2) | `routing/search._reverses`, `RouteProposal.snapped` | group basis §3 to §5 |
| 908.2 is graded strictly: a child rising more than it runs is a 908.1 vertical wet vent, a dry-vented lavatory's drop included; a closet may drop to the drain | `resolve/mep_trap_arm.grade_wet_vent`, `cli/route_fixture_wet` | group basis §4, §5 |
| A duct search is bounded at 1,000,000 labels or 45 s, then refuses with `stopped` set ("a budget, not a proof"); a step that would cross the route's own lane is refused | `routing/duct_search` | duct basis §7.2 |
| A duct proposal carries its `DuctStandard`; an elbow snaps within 10 degrees of the stamped angles, the one snap the catalog and the bill share | `RouteProposal.duct_standard`, `resolve/duct_standard.ELBOW_SNAP_DEG` | duct basis §7.5 |
| Condensate (`sanitary=False`) is laid at 1/4"/ft and goes to 3/16 or the IMC 307.2.1 floor of 1/8 only when that beats the 768 in-per-in/ft penalty (or 1/4 refuses); `mep.drain_slope` FAILs below 1/8 and ADVISES below 1/4; cleanouts only on sanitary runs | `routing/gravity.graded_route`, `resolve/mep_slope`, `cli/route_cleanouts` | `mep_condensate_routing_basis.md` §4, §5, §8 |
| A tree tie is ON its collector (1/8"); the step into it may cross the collector, never ride or leave it; a branch ties into a plumb drop's side at its own height; a refusal is reported per fixture | `cmd_route_tree.TIE_TOLERANCE_M`, `gravity_band.band_obstacles`, `route_tree_branches.Branches` | drain basis §13 |
| A flat rectangular duct reads its half-height in z, not its plan radius: corridor windows and tiers, floor-member and bar windows, bearing-bay boxes, rails | `RoutingSpace.z_r`, `Penetrations.z_r`, `floor_bars.crossed` | duct basis §5 |
| A recessed can's housing is a hard prism (kind `can`) over its body; it nominates no lattice line and its edges are tested exactly, as a round prism's are | `resolve/can_housings`, `routing/obstacles`, `graph._NO_TURN` | `mep.ceiling_can_framing` |
| A trunk's gate offers its middle plane and both extremes, so a run on the middle plane (catlin's PR-B-HW-BATH2) is passed on a tier | `supply_tree.gate_for` | `mep_supply_trunk_basis.md` §5 |

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
one pays `cleanout_concealed_in`, and every one `cleanout_in`, so a route needing fewer cleanouts
ranks higher.

**Limitations.** `--fixture` offers a wet vent only onto a drain already authored (`--group`
lays the whole group); seeds keep the two cheapest take-offs (`keep=2`); a vertical barrel's
stack pitch is left to the check; a tie's fitting is named but not priced; rack lanes exist
only inside `--house` and `--manifold` campaigns. `--tree` prints each branch graded alone, so
a branch meets the authored drain another branch replaces; the scorecard grades the tree as
one network. Neither catlin bathroom group lays whole: BATH2 lays its SH arm, 3" wet vent and
dry vent and refuses TUB and WC; SUITEBATH stays the authored three-vent design. On `tree:main`, P8 re-lays BATH2-TUB one size up onto BATH2-SH. Its 2" group is a 339 x 416
plan lattice (`MAX_CANDIDATE_LINES` 450; its 1.5" form was 315 x 393 before UPC 2018's 2" drains):
all three size groups build and 8 of 8 fixtures lay (395 s wall measured with other runs on the
machine: search 69 s for the 2" group, 1.18 GB peak). The stamped Linx elbow has no published
centre-to-face (its catalog gives only rC ≈ 1.5 d1; the 1.5 D radius stands in), and the flex bend radius and the GV0772 transition length are unread
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
gravity runs are not constrained. The stub's travel and one bend where the route turns at its
tip are priced into the proposal's cost (`port_stub_stated_in`, `port_stub_bend_in`) after the
search, so they change a reported cost, never a route. `PortKit` leads and duct tip turns are
not added (`duct_search` already charges the start heading). The search has no heading at a
terminal, so `forbid_port_reversal` cuts the tip's lattice step back along the stub toward the
port, both ways, right after each `build_graph` (`_propose`, `space_for`): a route may not
leave or reach the tip over its own stub (drain basis §11). A reversal that still reaches
`attach_priced` is noted and never priced as a bend.

**What a proposal replaces.** `--evaluate` removes from the candidate plan the run of the
proposal's own name and any same-system run whose `serves` it covers, so a route is never graded
against its own ghost. `RouteProposal.replaces`, when set, is the whole answer: a supply trunk
serving what its service lateral serves must not delete the lateral, and a tree stands in for
runs no tag names. Otherwise a run the proposal ties INTO (an ancestor of what it replaces, with
an end of the proposal on it) stays, however much of its `serves` the proposal covers
(`route_eval._replaced_tags`, `_tied_into`).

**A target whose terminals cannot be derived** (no sump pump names its line; the receiver has
no modelled riser; nothing downstream of a drain) is an `EndpointRefusal`: a `Refusal` with no
lattice counts and `cause`, `element` and `fix` in its payload. The finders log a `Miss` through
`cli/route_miss.miss()` and `route_propose.endpoint_refusal` takes the first one; a fixture end
standing in a door or duct carries `TerminalBlock.payload()` as `terminal`. Nothing parses
sentences, and the rendered line is unchanged.

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

**Choosing among orders.** `--orders N` lays the campaign in up to N conflict orders, ranked
by refusals, then skips. When the network is evaluated (`--evaluate`, or `--json`), the orders
tied with the best on refusals and skips form a shortlist of at most `min(N, 3)` (only when
there are two or more), each graded against one shared baseline and classed **constructible**
— the evaluation resolved, no introduced FAIL in `route_check_groups.CONSTRUCTION_CHECKS`
(bores, run interference, finished volume, freeze exposure) and no fitting `forbidden_turns`
refuses — or **provisional**. The shortlist ranks constructible first, then introduced FAILs,
UNKNOWNs, then cost. Fittings, penetrations and supports are in cost; an unplaced required
cleanout is not, but its `mep.drain_cleanouts` FAIL counts in the FAIL tiebreak. A grade never
outranks a refusal. `orders_tried` rows carry `grade` (`class`, `refused`, `fail`, `unknown`,
`construction_fail`, `forbidden_fittings`), null when ungraded; the scorecard's campaign rows
use the same selection.

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

Evaluation follows replaced runs: a valve or stop on a replaced run moves to the proposal piece
within 3" of its station (else `<run>-PROPOSED`); a bond end, `Register.duct_ref` or any
`from_ref`/`to_ref` naming a replaced run is re-pointed at its `<run>-PROPOSED`. A drain proposal
ties in only at its arrival end. A branch never tees within r1+r2+clearance of a bend of its host,
and a supply end on a shower-assembly inlet leaves on a straight stub along the valve axis
(`cli/route_fixture_inlet.py`, applied in `_endpoints`).

## Limitations

- Flex transfers that need a free-angle bend (DU-B-WH-OUT/IN) are refused: the duct lattice is
  axis-aligned. DU-B-ERV-R-BATH is refused 0.4" short of its clearance to PR-M-COND-HP3. Both
  stay authored by owner decision.
- The supply trunk search carries the house's outside as space prisms
  (`gravity_band.outside_prisms`, 12" holes at run ends) and retries free of the outline, with a
  notice, only when no interior lane crosses the floor system. The main-floor seam was never
  missing a crossing: PR-B-HW-BATH2 (z -7.7 to -4.7") sat across the gate's one middle plane at
  y 187-191", so every column stopped there. The gate now offers both tiers and the trunk lays
  inside the house (`trunk:CW` freeze FAIL 3 to 1, hydrant 1 to 0). What is left: the trunk's
  `-END` riser runs 0.9 ft in W-M-E1's bay. Branches do not get the outside prisms (row budget).
  PR-B-FILLER-CW and PR-S-SUITE-LAV-CW were lost to two older flaws the new trunk exposed, not to
  the tiers: a lane's two 1" pins (an end and its own riser station, 2.2" apart) left a 0.24"
  sliver of gate between them, which a midpoint test had passed only by luck of a trunk-seeded line
  (`supply_tree.wall_lanes` now joins them with a 1" slot); and a supply end plumb under its host
  (a lav 5" below a branch) was dropped as "origin already on the goal" (`route_proposal`: a
  supply tie keeps a plumb stub).
- Supply branches teeing beside a sibling or the trunk can still overlap by 0.3-1"; there is no
  no-collinear-approach rule in the search.
- A tree branch starts at its fixture's drain port (`mep.fixture_port_connection`), its profile at
  the storey datum with a plumb drop between, and lands on its collector's final snapped invert
  when within 1/4". A wall-hung fixture's port sits on the wall axis, so its drop stands in the
  stud plane (`mep.run_through_stud`, as with `--fixture`); the cavity stub is open.
- A 3" WC arm the authored route makes with a 1/8 bend can exceed 72" on the Manhattan
  lattice (basement WC: 73.8"); trees have no diagonal jogs and no vent-aware arm.
- DU-B-ERV-RET-TRUNK and DU-B-ERV-SUP-TRUNK stay refused for what is authored, not for a prism's
  shape: SUP's 12" kit lead ends at z -35.4", 1.5" into DU-ERV-EA's underside (its first turn needs
  a tip at -36.9" or lower), and RET's tip stands 0.37" inside DU-ERV-OA's riser prism (0.13" gap
  authored, 0.5" clearance routed). Squaring a run prism's ends (the body stops at its vertex) is
  right but adds a second offset per bend and takes `tree:main`'s 2" lattice past
  `MAX_CANDIDATE_LINES` (492 y-lines), so it is not applied.
- A riser at a bearing line: `crossing_runs` skips risers (they pass the plate), so a riser near a
  blocked bay's block stood on a 5 1/2" box rail nothing was framed round, and the check read the
  flat 2x6 as a 1.5" ribbon. `blocking_parts.riser_cuts` now opens the box's rails (and
  `pass_through_box` adds a cheek at each cut; pieces under 2" are dropped) where a plumb leg
  stands in the rail footprint, and `mep.riser_through_deck` reads a member's plan section
  (`plan_cross_section_m`). A riser in a solid block (no run crossing) still FAILs. The router
  lets risers pass bearing bays on purpose (`bearing_bays`).
- `--lift` still refuses a supply whose unlifted branch tees on its first leg ("loses N"), and
  grades each re-laid line on its own, against the authored runs.
- `--group` offers at most four tie stations (`cli/group_ties`): two authored, then the main's
  in-band stations dealt per floor system, nearest the room first; each refused station costs a
  full search. A station refused before one that lays is dropped from the refusals. A partial
  group (the dry fixture laid, a later one refused) is proposed and replaces only the laid
  fixtures' runs.
- Vent-free 908.2 bathroom groups are not proposed; whether 908.2 admits a dry-vented lavatory's
  drop is an AHJ question.
- An off-catalog round duct turn (outside the 30/45/90 +/-10 deg windows) is made by the house's
  adjustable `DuctElbowRow`, graded as the bought 90 with loss C x K read from the row's authored
  `angle_k`. A turn no adjustable row at that size can make (a reversal, or no row) stays ungraded.
- A vent with no `--level` is banded to the storeys its terminals span (`routing/terminal_band`),
  not the whole house: `PR-B-BATH-VENT` was 674,698 nodes (19 levels, eight of them corridor planes
  on main, second and attic) and is 268,128 (13 levels, all basement). A vent that must leave its
  terminals' storeys needs an explicit wider band, which does not exist yet; ducts and risers are
  not banded.
- A `RoughOpening` that names a run in `penetration_for` is no obstacle to that run (nor to a run it
  is joined to): the origin standing in `AO-M-ERV-OA` had no lattice step off it when no other
  level was nominated. The fit is still graded by `mep.duct_penetrations`.
- The riser-cover rule covers flat-ceiling rooms only; sloped (FollowRoof) rooms, mechanical
  rooms and rooms with `exposed_services` are not zones. `SUPPLY-GATE` holes confine supply
  risers regardless of cover (the lattice never reads a prism's `applies`): a group's holes are
  its fixture ends, laid branch ends, and the riser stations of each member's authored run and
  its feeders (each also a lattice line, `supply_tree.riser_stations`, trunk basis §5a). Each
  member also gets a storey-banded **lane** (`supply_tree.wall_lanes`): the layers of the walls
  standing at its end's height on its own storey, within a bay of the end and its riser stations,
  are opened from the nearest gate edge to the end's height (below the gate for a basement end),
  and inside that band a tight hole shrinks to its own 1" riser column (`PIN_M`), so a branch
  climbs in walls rather than through a hole's square of air (`trunk:CW` finished-volume FAILs
  7 to 1). The one left is `PR-A-STUBATH-SH-CW` in RM-A-STUBATH, a FollowRoof room the router
  does not zone.
- A bendable tube (`bend_radius_m` > 0) is searched over labels (`search._bent_route`): signed
  heading, straight laid since the last turn, and what began the leg (start, fitting, bend). Each
  turn branches into a fitting or a field bend admitted by `mep_fittings._bend`'s tangent rule
  (R fits all of an end leg and half of a leg between turns; conservative beside a fitting);
  `price_route` applies the same rule and prices a foreign reversal as two fittings. Reversals are
  refused. Fitted services (copper, vents) keep the `(node, axis)` search, where reversing along
  one axis is still free; drain basis §4 pins its expansions.
- The router excuses a riser in a served fixture's body when the body holds one of the route's
  ends, in the body's own room; the check excuses only the legs walked in from a run's end, so
  a mid-run riser through that body would still be graded.
- Exterior insulated bays are priced by depth, not refused. `routing/freeze_bay` restates the
  check's steady-state walk (routing may not import checks), so the two must change together;
  continuous exterior insulation is in the outboard R (catlin's R-26 leaves only the outer ~1.5"
  of a 5.5" bay cold at -15 F). An edge is graded at the deepest point it reaches.
- Laid-run holes reach supply and drain campaigns: a
  house campaign and a `--lift` re-lay pass what is laid so far (`holes.laid_lines`), a tree its
  `Branches.laid_lines()` (the main it ties into included, hidden from the space by `touch`), and a
  drain keeps its tie target's own holes (`holes.kept_lines`). A sibling laid later in the same
  group is not in the space built for it, so it is read per search: a falling run's
  `gravity_webs.spacing_obstacles` (D pockets likewise, `web_obstacles`) and a supply lattice's
  `holes.drop_close_edges` (framing_bore_limits.md §14); the P8 re-lay searches through the same.
- A stack rung is a goal at ONE height (a lattice node holds one invert), so a still-refused group
  is searched once per rung: `--tree PR-M-S-SUITE-DRAIN` takes ~3x longer to refuse its tub and WC.
  Both refusals are real holds (framing_bore_limits.md §13: D13/D14 held by PR-B-CW-SUITE, D12 by
  PR-A-HW-STUBATH); the authored tub lane stands.
- The scorecard records `eval_refused` and `eval_coverage_gaps` per row; a row with proposals
  whose evaluation refused is always a regression, never 0 FAIL.
- A full scorecard run takes about 7 minutes: rows run in forked workers (`HAUS_SCORECARD_JOBS`,
  default min(4, cores/2)) and the longest row (`tree:main`, minutes now its 2" group lays) sets the floor.

## Read only the relevant implementation

| Responsibility | Modules under `packages/engine/src/typehaus/` | Tests |
| --- | --- | --- |
| CLI, reports, artifacts | `cli/cmd_route`, `cli/route_propose` (one proposal pass), `cli/route_options` (parsed options, `not_built`), `cli/route_report` | `test_route_reporting`, `test_cmd_route` |
| Terminals and tie-ins | `cli/route_support`, `cli/route_endpoints_duct` (duct and raceway ends), `cli/route_roots`, `cli/route_miss` (structured misses), `resolve/mep_ports` | `test_cmd_route`, `test_route_metadata` |
| Drain tree, rip-up, lift | `cli/cmd_route_tree`, `cli/route_tree_group`, `cli/route_tree_branches`, `cli/route_tree_lift`, `cli/route_supply_roots`, `cli/route_tree_upsize`, `cli/route_tree_ledger`, `routing/tree_ripup` | `test_routing_tree_ripup`, `test_cmd_route` |
| Bathroom group (908.2) | `cli/cmd_route_group`, `routing/group_order` | `test_routing_group` |
| Supply trunk and tree | `cli/cmd_route_supply_tree`, `cli/route_supply_group`, `routing/supply_tree`, `resolve/riser_cover`, `routing/terminal_block` | `test_routing_supply_tree`, `test_routing_riser_terminal` |
| Fitted duct search | `cli/route_duct_search` (the one entry), `routing/duct_search`, `routing/duct_fittings`, `cli/route_ports` | `test_routing_duct_fittings` |
| Space and graph | `routing/space`, `routing/obstacles`, `routing/graph` | `test_routing_graph`, `test_routing_perf_guard` |
| Search and gravity | `routing/search`, `routing/gravity*` (incl. `gravity_grid`), `routing/tree` | `test_routing_oracle`, `test_gravity_search`, `test_routing_vent`, `test_routing_hole_spacing` |
| Minor systems | `cli/route_roots` (sump and condensate ends), `routing/campaign` (trades) | `test_routing_minor_systems` |
| Plumber's rules | `routing/members`, `holes`, `bearing_bays`, `rails`, `fitting_room`, `compaction`, `trap_vent`, `rack` | `test_routing_members`, `test_routing_hole_spacing`, `test_routing_compaction`, `test_routing_trap_vent`, `test_routing_supply` |
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
