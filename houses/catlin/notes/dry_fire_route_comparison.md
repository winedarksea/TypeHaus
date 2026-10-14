# Dry-fire ERV route comparison — 2026-10-13

The full-length lane has not passed the routing gates. The implemented design takes
`plans/dry-fire-lane.md` §5's fallback: retain the ERV header and outdoor legs, move the
condensate, and lift the three marginal crossings. The clear lane starts behind the target
face at y=13 in, so its available length to y=352 in is **8.6106 m**; the study's 8.74 m
included the five inches behind that target face.

These searches establish that the tested arrangements are unqualified, not that every
possible ERV relocation is physically impossible. A lattice-size refusal is a search limit;
a collision with an existing movable pipe can instead justify a larger plumbing redesign.
Neither is permission to accept a route or weaken a check.

## Reproduction and scope

The local artifact bundle is `houses/catlin/out/dry-fire-study/` (git-ignored). It contains
complete house-source snapshots without generated output, the preparation scripts, logs,
and successful campaign `report.json` / `proposed.py` files. From the repository root:

```sh
.venv/bin/haus route houses/catlin/out/dry-fire-study/baseline --house --storey basement --trades duct --orders 3 --evaluate --out /tmp/dry-fire-baseline
.venv/bin/haus route houses/catlin/out/dry-fire-study/supply --house --storey basement --trades duct --orders 3 --evaluate --out /tmp/dry-fire-supply
.venv/bin/haus route houses/catlin/out/dry-fire-study/extract --house --storey basement --trades duct --orders 3 --evaluate --out /tmp/dry-fire-extract
.venv/bin/haus route houses/catlin/out/dry-fire-study/supply-v2 --house --storey basement --trades duct --orders 3 --level basement --evaluate --out /tmp/dry-fire-supply-v2
.venv/bin/haus route houses/catlin/out/dry-fire-study/extract-v2 --house --storey basement --trades duct --orders 3 --level basement --evaluate --out /tmp/dry-fire-extract-v2
```

There are eight basement targets: six radials and two machine trunks. The outdoor legs and
room risers are filed elsewhere, so zero basement refusals would not itself prove them.
`--level basement` additionally confines the v2 searches to the basement elevation band;
storey scoping alone allows a proposed detour upstairs or outdoors.

The original campaigns began before the router's insulation/metadata fixes. Their geometric
search refusals are recorded, but their evaluated bare-duct proposals cannot establish a
wrapped outdoor route or a reliable static budget. The v2 campaigns use the corrected
12-in outdoor envelope and preserve design flow, material, and insulation.

## Candidate geometry

All relocated-machine variants rotate `EQ-B-ERV` 90°, centred at (81,328.5) in, still hung
54 in AFF. The initial supply and extract alternatives move the named plenum to (76,264)
in, bottom 86.5 in AFF, retaining its 36-in east–west orientation. Their own collar/run
endpoints move with the box. The kitchen ceiling line is replaced by a drop at (36,418) in
to the existing under-slab main. This is a scratch comparison, not accepted plumbing.

An earlier body-placement probe at (90,282) in found clashes with the hot trunk, washer
hot branch, and sauna vent. A grid scan of unrotated bodies, centres x=60–112 in and
y=264–300 in at two-inch steps, bottoms 82.5/84/85/86/87/88 in AFF, found no station free
of existing nonduct hard solids. This uses the engine's conservative swept-run obstacles;
it does not prove a continuous space has no solution.

The rotated v2 alternatives put the selected plenum at (82,270) in, rotation 90°, bottom
86.5 in AFF: 8 in east–west by 36 in north–south. This clears nonduct bodies in the same
scan. Supply ports become trunk (82,273,86.5), riser (78,258,90.5), sauna (86,255,90.5),
gym (86,279,90.5), and play (82,288,90.5), all inches AFF. Exact source for each alternative
is in its snapshot; endpoint-only exploratory moves are distinguished from the more
complete supply-v2 trunk/radial paths by the preparation scripts.

Both v2 variants retain the facade hood stations. Outdoor trunks take separate north–south
corridors at x=48 and x=61 in, centred 86.5 in AFF (80.5–92.5 in wrapped envelope). OA
turns east at y=367 in and EA at y=354 in. The approximate machine port stations are OA
(77,321), EA (77,335), supply (88.5,321), return (88.5,335), at 75.6 in AFF. The relocated
supply trunk goes south outside the lane before rising into its plenum; the return drops
from the retained extract plenum and reaches the machine over a seven-inch horizontal leg.
Room risers still require a successful coordinated reroute. Their old approach paths are
not treated as accepted parts of the candidate.

## Results and gates

| Run | Best result | Meaning |
|---|---|---|
| Original baseline | 7 laid, 1 refused | Sauna-supply lattice 357,737 nodes exceeds 350,000 cap; not an impossibility proof. |
| Initial supply relocation | All three orders: 6 laid, 2 refused | Evaluation also hit an invalid swept-polygon topology exception; no proposals accepted. |
| Initial extract relocation | All three orders: 6 laid, 2 refused | Sauna-supply lattice 362,080 nodes; supply-trunk departure blocked by hot trunk and heater cold feed. |

The rotated v2 campaigns were interrupted before producing reports; their logs contain
only the eight-target start message. They provide no acceptance evidence. The completed
initial campaigns and the below-gate static diagnostic already require the fallback.

A direct check of the **authored supply-v2 scratch network before accepting any campaign
proposals** reports 0.436 in w.g. governing supply static and about **204 cfm**, below the
205-cfm gate. Its hand static oracle has not been re-derived, and its room riser approaches
still clash, so this is diagnostic evidence, not a qualified final design or an oracle
replacement. It is insufficient to accept the full lane.

Separate outdoor probes also failed qualification. The unbounded initial OA search found
an outdoor/main-level shortcut and introduced clashes. Basement-only segment probes
refused against the lane, existing room riser, and radial/conduit field; those exploratory
terminals also demonstrated why a 12-in wrapped drop needs a centre east of x=74.5 in.
Their logs are retained for diagnosis, not promoted to successful full-run evaluations.

The zero-refusal, ≥205-cfm, zero manifold-port/interference, and headroom gates have not
been established for a complete relocated network. The fallback therefore closes this
implementation without moving the machine, plenums, kitchen tie, or outdoor hoods.

## Final fallback validation

The original fallback overlooked the low `DU-B-ERV-RET-TRUNK` crossing at y342".
It now stays east at x74" until y357", then turns west to the unchanged machine port.
This adds one elbow without adding developed length. Together with the riser lift,
the independent static addendum gives about 0.3736 in. w.g. and 206.53 cfm.

A fresh `haus route --run PR-B-HW-TRUNK --evaluate` proposal introduced two deck-hole
failures and a branch interference, so it was rejected. The authored basement route
keeps its downstream tees and passes the full-house interference checks. No campaign
proposal was pasted. The final `haus check` reports 0 FAIL and an explicit PASS for
the required lane; the trial against the recorded baseline adds no FAIL. The trial's
blanket-suppression warning is stale tool prose: neither run interference nor stud
checks are blanket-suppressed in the current house preferences.

The main-drain lift regrades the retained kitchen branch tail; its plan route and
slab connection remain in place. The new bath-vent arrival has an unresolved fitting
pattern (79.5°), which the trial reports as UNKNOWN. The sink drain's existing
unresolved turn changes from 70.8° to 71.8°. These are retained fabrication details,
not clearance intrusions. Backflow geometry is corrected at the owner-confirmed
entry-riser station; the upstream buried hydrant branch order still needs resolution
before installation.

Updated geometry goldens (pipe/duct intersections at their actual cuts):

- `catlin_elevations.json`
- `section_goldens/catlin/center_section.json`
- `section_goldens/catlin/detail_opening_perimeter-INT_2X6_PLUMBING.json`
- `section_goldens/catlin/detail_stack_width_change-INT_2X4_PARTITION-INT_2X4_STAGGERED_GWB.json`
- `section_goldens/catlin/detail_stack_width_change-INT_2X4_PARTITION-INT_2X6_BRG_EXPOSED_PLY.json`
- `section_goldens/catlin/detail_stack_width_change-INT_2X6_BRG_MUDROOM_UPPER_GWB-STAIRWALL_INT_2X6_BRG_UNDERSTAIR.json`
- `section_goldens/catlin/detail_storey_stack-rim-INT_2X4_PARTITION-INT_2X4_STAGGERED_GWB.json`
- `section_goldens/catlin/detail_storey_stack-rim-INT_2X4_PARTITION-INT_2X6_BRG_EXPOSED_PLY.json`
- `section_goldens/catlin/detail_storey_stack-rim-INT_2X6_BRG_MUDROOM_UPPER_GWB-STAIRWALL_INT_2X6_BRG_UNDERSTAIR.json`
- `section_goldens/catlin/detail_wall_foundation-BASEMENT_8-EXT_2X6.json`
- `section_goldens/catlin/slice_SL-D-FNDN.json`
- `section_goldens/catlin/slice_SL-S-DRYFIRE.json` (new authored lane section).

## Verification outcome — 2026-10-14

- Final house check: **1859 PASS, 0 FAIL**, including `integrity.clear_zone_intrusion`;
  70 UNKNOWN and 61 N/A remain visible. Baseline had 69 UNKNOWN; the added bath-vent
  fitting detail is described above.
- Focused lane, metadata, static-oracle and geometry-golden regressions: **52 passed**.
- Full engine run: 9289 passed, 28 skipped. Its 14 failures included stale shared house
  fixtures loaded before the return detour and test expectations corrected afterward.
  The fresh rerun of those cases gives **11 passed**, with the two failures below.
- `test_connector_geometry_integration::test_paired_heavy_angles_project_away_from_their_tie_block`
  and `test_bid_packages::test_framing_golden` both fail identically on unchanged HEAD
  `d793c691` in a separate worktree. Their missing connector and framing-bid drift
  predate this lane; the unrelated bid golden was not blessed.
- The remaining failure was the 30-target supply CLI campaign, interrupted after the
  full suite had run for about 19 minutes. Its result is incomplete, not an accepted
  campaign or evidence that this lane passes that search. The completed duct studies
  already selected the fallback under the plan's gates.
- The full script's remaining stages were run independently after its engine stage:
  **309 starter and 309 Catlin checks-as-tests passed**, strict Catlin check passed,
  starter/Catlin JSON and Catlin IFC builds passed, rebuild performance guard passed,
  ruff passed, and UI typecheck/tests/production build passed.

Generated reports are retained under `out/dry-fire-study/final-validation/`. The visual
review is `out/render/dry-fire-lane-review.png`, with the authored section at
`out/render/section_SL-S-DRYFIRE.png`. The broad suite is not claimed green.
