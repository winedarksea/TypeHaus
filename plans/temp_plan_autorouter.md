# Whole-house MEP routing with actionable design feedback

## Summary

Extend TypeHaus’s existing CPU A* router to propose coordinated plumbing and HVAC networks: connections, trunks, branches, sizes, fittings, and physical paths. Return several independently evaluated alternatives, along with specific explanations when the building or fixture layout prevents a satisfactory route.

The router holds fixtures, equipment, walls, and assemblies fixed. An external agent uses the results to make broader design changes and rerun the search. Electrical services participate as obstacles initially.

Retain sparse A* as the baseline. Classic JPS’s uniform-cost assumptions do not directly fit the proposed semantic costs, and Dubins curves do not replace fitting geometry. GPU acceleration remains a later optimization driven by profiling. ([JPS research](https://ojs.aaai.org/index.php/AAAI/article/view/7994), [Dubins-path research](https://arxiv.org/abs/1211.2365))

## 1. Establish trustworthy geometry and constraints

- Introduce shared, search-independent MEP geometry and constraint primitives. Resolution, checks, and routing consume these primitives; checks never depend on search results or preference weights. Keep candidate orchestration above these packages.
- Represent run envelopes using actual outside dimensions, insulation, rectangular orientation, fitting bodies, and installation clearance. Use spatial indexing for broad collision detection and segment/fitting geometry for final intersection tests. Replace whole-run extrusions that incorrectly block empty space between elevations.
- Add per-vertex conduit elevations while preserving existing endpoint-based resolution. Distinguish schematic profiles from physically specified routes; missing geometry produces an explicit coverage gap.
- Model connection ports with service, position, direction, section, and positional certainty. Existing approximate equipment ports remain usable for preliminary routing but cannot establish an exact connection.
- Check all service pairs and relevant building geometry, including studs, plates, blocking, beams, floor members, concrete, openings, equipment, and access spaces. Permit contact only at explicit connections or compatible penetrations.
- Add dimensioned fitting and penetration records that survive proposal rendering, resolution, takeoff, and IFC export. Catalog entries state permitted connections, angles, dimensions, and hydraulic or airflow data where available.

**Framing policy:** prefer clear cavities; allow verified prescriptive bores with a penalty; do not automatically introduce notches, reinforcement, or structural redesign. Grade existing notches as well as proposed bores.

Implement stud, sawn-member, and plate rules against the house’s jurisdiction profile. Evaluate combined penetrations, remaining edge distances, bearing status, and existing reinforcement. Engineered members require applicable manufacturer data; a generic open-web height is insufficient evidence of a clear passage. Staggered walls use actual member positions rather than treating the entire wall as empty. ([ICC framing guidance](https://www.iccsafe.org/building-safety-journal/bsj-technical/codenotes-cutting-drilling-and-notching/))

## 2. Build fitting-aware paths and coordinated networks

**Single routes**

- Complete duct dispatch and make existing routing options effective: enforced waypoints, storey restrictions, tag exclusions, and loaded preference weights.
- Extend the sparse search with available cavity lanes, penetration locations, riser connections, and fitting-compatible turns. Multiple services may occupy a bay when their actual envelopes fit.
- Carry direction, fitting requirements, and gravity elevation through search. Evaluate sloped segments at their resulting elevations; remove the “search flat, slope afterward” assumption.
- Support catalog-backed rigid fittings and product-specific bend limits for flexible services. Missing fitting data remains visible.
- Revalidate the final rounded, serialized geometry, including terminal approaches and junctions.

**Whole-house coordination**

- Accept fixed equipment and fixture locations, service assignments, demands, boundary connections, allowed products, and any locked routes. Infer only unambiguous information already represented in the model; report missing assignments or design inputs.
- Build connected riser and storey subproblems with a shared occupancy model. Choose branch and trunk topology through repeated connection searches, tracking junction capacity and accumulated demand.
- Derive supported pipe and duct sizes from shared sizing calculations and supplied design criteria. Any size change triggers geometry and performance reevaluation. Never substitute the current generic 2-inch branch default for fixture-specific requirements.
- Route gravity drainage and its vent constraints first, prioritizing scarce headroom and constrained large sections. Coordinate bulky HVAC routes next, then smaller supply services. Treat this as an initial ordering heuristic and try alternative orders when conflicts arise.
- Use bounded removal and rerouting of previously proposed services to resolve congestion. Locked services remain fixed. Preserve separate networks, drainage direction, vent connectivity, and equipment assignments.
- Evaluate flow-dependent performance on complete networks: drainage capacity and slope, vent requirements, water-supply demand and pressure where inputs exist, and HVAC airflow/static pressure. Unsupported cases are reported explicitly.

Produce up to three distinct evaluated alternatives by varying topology, corridor choices, and conflict-resolution order. Search budgets and cost weights belong in configuration; every result records the effective settings and termination reason.

## 3. Expose results that an agent can act on

Extend `haus route` with whole-house selection, alternative count, structured JSON output, and an output directory for review artifacts. Preserve single-run, fixture, and tree entry points.

Introduce three public contracts:

- **Routing request:** scope, terminals and assignments, design inputs, locked elements, preferences, and search budget.
- **Network proposal:** connected runs, fittings, sizes, penetrations, replaced elements, metrics, and model/input revision.
- **Evaluation report:** independent findings, coverage gaps, unserved terminals, blocker locations, and search diagnostics.

Evaluate each proposal against a separate candidate model. Keep source files unchanged; export declarative proposal source and an explicit replacement list for the agent to apply.

Rank complete, validated candidates ahead of incomplete results. Within that group, use configurable preference costs and expose the underlying quantities: length, fittings, bores, clearance margins, pressure losses, affected finishes, and estimated installed cost. Monetary estimates use available house pricing and disclose unpriced work.

For failed connections, report:

- The affected terminal and service.
- Blocking element tags and exact conflict locations.
- Quantified shortages, such as missing fall, insufficient opening width, or inadequate fitting space.
- Alternatives attempted and the limits of the search.

Use bounded diagnostic searches that relax named obstacles to identify changes worth investigating. Label these as counterfactuals, not buildable proposals or proof that an element may legally move. Distinguish “no route found within this search” from a directly established impossibility.

## 4. Export semantic routing-space views

Generate SVG plan/section diagnostics and a tagged GLB review artifact containing candidate routes and relevant surrounding geometry.

Colors describe space for the selected service, dimensions, orientation, and elevation:

- **Green:** verified available clearance.
- **Orange:** conditional passage or an identified change worth investigating, with the required action attached.
- **Red:** prohibited passage under the current design and policy.
- **Gray:** insufficient geometry or constraint information.

Show existing congestion, proposed bores, fitting envelopes, tight clearances, and failed terminal approaches. Include dimensions and element tags so an agent can connect a picture to the structured report. Diagnostic relaxation never turns an unresolved collision green.

Defer interactive editing, automatic fixture movement, and assembly selection.

## 5. Delivery and acceptance

Implement in dependency order: geometry and checks → individual paths → network topology and coordination → alternatives and diagnostics. Whole-house capability remains the completion criterion.

Verification includes:

- Hand-derived geometric cases for sloped crossings, staggered studs, legal and illegal bores, rectangular ducts, insulation, fittings, and intentional junctions.
- Small exhaustive-search oracles for directional costs, gravity constraints, and competing routes; do not claim whole-house optimality.
- Feasible synthetic multi-storey networks covering drainage, vents, supply, and HVAC, plus deliberately impossible layouts.
- Independent validation after proposal source round-tripping and IFC export, including fitting and penetration geometry.
- A fixture-movement scenario where the first attempt identifies the blocker and a caller-authored move allows the next attempt to succeed.
- Catlin regression cases for the NW chase, suite-bath gravity budget, shared floor bays, and equipment connections. Recompute the current baseline rather than pinning stale TODO collision counts.
- Repeatable CPU benchmarks recording graph construction, search, validation, memory, and budget exhaustion. Cache unchanged geometry across alternatives.
- Targeted tests during development and the repository verification gate before completion, following the Catlin fixture discipline.

Success means complete feasible examples route and validate; infeasible or underspecified examples return useful, accurate feedback. Catlin need not be forced into a successful result while its fixed design contains unresolved conflicts.
