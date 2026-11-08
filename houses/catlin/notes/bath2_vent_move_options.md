# BATH2: moves that open the vent, the group and the hot riser (proposal only)

**2026-11-07, wave 2 / H.** Proposal for the owner; nothing here is applied. Every number was measured in a
throwaway sandbox (branches at the end) with `haus route`, `haus check --only all` and the engine's own geometry
(`model.json`). Inches, project frame, main datum 0, basement-relative elevations marked "bsmt". Baseline:
`haus check houses/catlin` = 3553 pass, **0 fail**, 200 not evaluable, 23 advisory.

BATH2 (`RM-M-BATH2`): x 0..98, y 156..268. WC against W-M-HS1 (x 30, flange y 252.74), 48" vanity on W-M-W3
(y 158..206), shower SE, Bask tub E (fixed), door D-M-BATH2 in W-M-BDN1 (x 25..58).

## The three problems, as measured

**P2, `PR-M-BATH2-WC-VENT` (the one the move is for).** The WC flange sits at the seam of two floor systems.
FS-M-WEST joist 016 is at y 256, its stub 017 at 259.06, FS-M-MECH joist 000 at 261.37 (all 11 7/8" TJI 230,
flanges 2 5/16" wide x 1 1/4" thick). The three flange footprints run y 254.84 to 262.53, **7.69"**. A 1 1/2" vent
(OD 1.9") may pass them only in the web zone, centreline z -9.68 to -2.20, a **7.475"** travel. A 45 degree
climb (MN 905.3, `mep.vent_connection`) needs 7.69". **It is 0.21" short, for any start height and any x
along HS1.** Measured: a 45 degree vent from the closet drop north to the wall (z -10.1 to +2.7) takes the top
flange of joist 017 and of MECH-000 (1.9" each), crosses MECH-000 with its crown 0.76" into the member, and
stands 0.7" proud of HS1's cavity (4 new FAIL; the 905.3 advisory closes). So today's level leg at -13.5" is
what is left, and moving the WC along HS1, or its drain point (sweep: -4" and -6" are cheapest at 9" of travel,
`--sweep 8`), changes nothing. A headered chase must open the web zone itself (an engineered detail, not
measurable here).

**P1, `--group BATH2` lays nothing.** It is no longer the 5.39"-over-7.50" hole spacing the TODO records.
Today the SH step refuses on head, "FS-M-MECH joist y 309/325, short 4.33" to 4.48"" (three passes: SH dry, TUB
held, SINK dry). `cmd_route_group._tie_stations` offers only the three highest in-band stations on
PR-B-MAIN-DRAIN, which is the collector's head and the stretch just under it, y ~255..271: **north of the same
seam**. Probe (engine edit in the sandbox only: pick the stations nearest a given y): ties near y 212 or 230 lay
SH -> WC as a 3" wet vent (5 DFU, tied to the main), a tie near y 250 refuses exactly as baseline. Even then the
group stops: the TUB has no take-off ("12 take-offs, all rise into the x 97" partition-block flange, 0.9" above
the arm" or into PR-B-CW-WASH), so the WC is left unlaid, and the SH wet vent it draws (x 8'-2" to 9'-8.5", back
west at y 19'-6") bores the sister-1 block flange 2.1" (FAIL). SINK dry refuses on its own arm
("W-M-W3, short 1.52"") and a sink `drain_position` +2" (the sweep's best) does not change it. With the WC on W-M-W3
(option 2) and ties near y 225 the result is the same, and the router's own WC step refuses ("no wall cavity holds
the vent"), so option 2 exists only as a hand-authored lay. **No fixture move clears P1**; it is an engine tie-offer fix plus a design that keeps the tub and shower on their own vents
(today's authored design), or an AHJ-accepted vent-free group.

**P3, hot riser in `PR-B-SH2-DRAIN`.** The model today elbows the hot riser 6 3/4" north of its hub (hub y 178.25,
riser y 185), which is not the cold's uniform 1 1/2". Measured: hot riser at hub + 1 1/2" (y 179.75) gives
`mep.run_interference` FAIL against `PR-B-SH2-DRAIN` (0.87" in plan, 1.50" in elevation); straight in at the hub
(y 178.25) passes, 2.15" off the arm's centre.

## Ranked options

| # | Move | P2 | P1 | P3 | Check delta (baseline 0 fail) |
|---|------|----|----|----|-------------------------------|
| 1 | SH2 arm tee 2" north (180.5 to 182.5), vent and cleanout with it | - | - | **clears** | 0 fail; 3 riser_through_deck UNKNOWN swap |
| 2 | WC to W-M-W3, bay 13-14 (flange 18.49, 221.0) | **clears** | no change | no change | 1 fail (floor-heat keepout); vent_connection advisory and 4 UNKNOWN closed, 3 UNKNOWN new |
| 3 | WC drain point -4" or -6" (sweep) | no change | no change | no change | none run; 9" travel against 43" |
| 4 | Group ties lowered (engine, probe only) | no change | partial (SH to WC lays; TUB, WC not) | no change | proposal bores a block flange 2.1" (FAIL), WC left unlaid |
| 5 | Stay, 45 degree vent through the seam | fails by 0.21" | - | - | 4 new FAIL |
| 6 | Swap WC and vanity | not measured | - | - | WC lands in D-M-BATH2's swing; not pursued |

**1. SH2 tee north (cheapest, no fixture moves).** Authored as: `PR-B-SH2-DRAIN` arm to (96, 182.36) and (98, 182.5),
`PR-M-BATH2-SH-VENT` from (98, 182.5), `CO-M-SH2-HEAD` fitting (96, 182.36) and cap (96, 184.4); the hot riser at hub
+ 1 1/2". Result: 0 FAIL, and the three `riser_through_deck` UNKNOWNs only change station (all at y 182.5, in the
177..191 bay). Quantities: arm 2" longer, nothing added. Lets the hot take the cold's uniform detail, and
BATH1's stays as is.

**2. WC to W-M-W3 (the only P2 closer, and it closes it for real).** Flange (18.49, 221.0) on W-M-W3, bowl centre
(21.4, 221.25) rotation 90, vent plumb in W-M-W3's cavity at x 2.5 up to the existing `PR-M-BATH2-LAV-VENT` header
(88"), drain 3" to the x 28.5" crossing and the collector corner (36, 198). Measured result: `mep.vent_connection`
**PASS** ("leaves above its centreline, rises plumb to 6" over the rim"), `trap_arm_length` PASS (12" against 72"),
drain slope flattest 0.60"/ft, 0 run interference, vent bores one king stud 1.9" (40% limit 2.2"). No new CODE FAIL
and no front-clearance finding (by hand the bowl front, x 35.6, is about 20.7" from the deck's west face at ~56.2:
check it against the finished deck). What it costs, in the order they appeared:
- **The joist.** The drop must stand in bay 13-14 (joist flanges y 222.84 and 209.16): flange y <= 221.09 for a
  3.5" OD drop. At y 221.5 it takes joist 014's top flange 0.41" (FAIL) and `riser_through_deck` FAILs.
- **The vanity.** The 15" side clearance to the 48" vanity (ends y 206.25) needs y >= 221.25. At 221.0 the engine
  FAILs `placeable_required_clearance_conflict` and `fixture_overlap`. The two meet with a **1/4" offset closet
  flange** (stock part): margin 0.0" against the vanity and 0.09" against the flange. Zero slack.
- **The sauna duct.** `DU-B-ERV-R-SAUNA-SUP` runs N-S at x 19 (z 86.5, top 88.5): the drain must stay above it
  (z centre >= 90.3 there); at 88.4 it is a FAIL (1.83" inside). Authored at 90.5.
- **Floor heat.** `FH-M-BATH2`'s zone is sized to one cable SKU (16.0 ft2); it needs a new bite west and the old
  HS1 bite refilled, net roughly +1.5 to 2 ft2 (estimate, not drawn). The one FAIL.
- **Washlet outlet** `ED-M-BATH2-WC-RC` (HS1 bay x 8..15) must move to W-M-W3 and the 6"-12" AFF rear-left
  rule; the HS1 bay it shared with BATH1's box is freed. Not graded, so not measured.
- **Supply.** `PR-B-BATH2-WC-CW` becomes a 5 3/8" tee off `PR-B-CW-BATH2` (x 13) to a stop at x 7.63 (was 11" at
  y 263.6 through FS-M-MECH); `PR-B-CW-BATH2`'s HS1 leg is unchanged.
- **The window.** The bowl is 5" south of `WIN-M-BATH2`'s centre (y 240), not under it. Router: at y 232 "no
  wall cavity holds the vent" (the window); only bay 13-14 works.
- Quantities: drain 41" (was 63"), vent 16" in-bay climb + 82" plumb (was 17" level + 103" riser), one cleanout
  moved, one stop. The level vent under the seam and its MECH crossing go.

**3. Sweeps.** FX-M-BATH2-WC: 5 of 9 stations ok (-8..-2, +4, +6), best -4" at 9" equivalent, 0 bends; FX-M-BATH2-SINK
best +2" (351 vs 397"); TUB best -8" (40"); SH has no legal station. They move drain points, not vents, and none
reaches P1, P2 or P3. The router also proposes WC vents (PROPOSED-A/B) that rise inside the room: ignore them.

**4. Ties.** See P1: an engine change with a design question behind it, not a house move; the sandbox edit is a hack.

## Recommendation

1. Take **#1** (SH2 tee 2" north). It closes P3 with one 2" arm change.
2. For P2 the choice is the owner's. **#2 is the only measured closer**, at the cost of the floor-heat bite, the
   washlet outlet and a window that no longer lines up with the bowl; it also drops 20" of drain and the level
   vent under the seam. **If the owner would rather keep the WC beside the tub wall, P2 stays an ADVISORY** until an
   engineered chase opens the seam's web zone (0.21"). Do not move the WC along HS1.
3. **Leave P1 on the authored three-vent design** (the TODO's own position). No fixture move helps; a better
   `_tie_stations` plus a TUB take-off that clears the x 97" block flange is a router item.

Open: the TODO line on "straight in at the finished face" and the file comment ("elbows once along the wall") disagree;
this note read the file.

## Sandbox branches (delete)

`scratch/h-bath2-wc-west` (#2, plus the tie probe), `scratch/h-bath2-hot-straight` (#1 and P3), `scratch/h-bath2-tie-probe`
(engine hack), `scratch/h-bath2-45deg` and `scratch/h-bath2-sink-dp` (no commits).
