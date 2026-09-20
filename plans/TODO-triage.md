# TODO.md triage (Wave 0) — scratch, delete in Wave 5

Measured against HEAD `9c28975e` on 2026-09-19. Read-only; nothing was edited.
`haus check houses/catlin --only fail,unknown` at the time of this triage: **1 FAIL**
(`structural.lateral_racking` on `RF-BW-CANOPY`/`PT-BW-RNE`, engineered, embedment d/c 2.21),
2 UNKNOWN shown. **Not** the 2 `column_base` embedment FAILs the plan expects.

Verdicts: **DONE** (prune) · **OPEN** (maps to a workstream) · **PREFS** (live record is
`houses/catlin/preferences.toml`) · **DEFERRED** (covered by the plan's *Stays in TODO.md* table).

## Needs your decision

| Lines | Entry | Verdict | Evidence | Destination |
|---|---|---|---|---|
| 6 | NEC 210.52 measures to the carcass, no `FixtureType.basin` | OPEN | no `basin` in `model/types.py` | **E7** |
| 8–14 | `Room.clear_face` is not the finish face | DEFERRED | — | table row 1 |
| 16–20 | 2D-edit sync | DEFERRED | — | table row 3 |

## Remaining Work

| Lines | Entry | Verdict | Evidence | Destination |
|---|---|---|---|---|
| 24–39 | SDPW published spacing read but not graded; joist maker unread | OPEN | `Wall` has **no** `published_span` (`model/elements.py:121` is on **`Door`**); no `checks/structural/partition_fasteners.py`; `takeoff/partition_fasteners.py` exists | **R1 + E6** |
| 41–44 | Blocking an SDPW lands in is billed nowhere | OPEN | `resolve/floor_blocking.py` unchanged | **E6** (second half) |
| 46–50 | ~220 sf gypsum through the joist band | DEFERRED | — | table row 7 |
| 52–56 | `member_interference` can't see a plate in a rafter | DEFERRED | — | table row 5 |
| 58–61 | Member-level short-framing finding | OPEN | `solver.py::short_post_findings` still the only shape | **E3** |
| 63–68 | `PT-BW-W`/`-GW` beam end + `ABU66SS` overlap | DEFERRED | — | table row 9 |
| 71–76 | 1/2" sheathing lap undeclared | DEFERRED | — | table row 8 |
| 78–89 | Deck post / concrete-spec follow-ups (6) | DEFERRED | — | table row 10 |
| 91–95 | Breezeway piers axial INCOMPLETE | DEFERRED | — | table row 11 |

### From the 2026-09-10 notes.md triage

| Lines | Entry | Verdict | Evidence | Destination |
|---|---|---|---|---|
| 99–110 | No low-voltage security/sensing devices | DEFERRED | entry says "-- DEFERRED" | table row 12 |
| 112–130 | Basement equipment plinth | DEFERRED | research not commissioned | table row 13 |
| 132–143 | DWHR has no model presence | OPEN | `grep -i dwhr houses/catlin` → nothing | **R2** |

### MEP / lighting residuals

| Lines | Entry | Verdict | Evidence | Destination |
|---|---|---|---|---|
| 147–152 | `_ATTIC_BAY_Z` may repeat the 1 1/2" error | OPEN | `plan/mep_erv_l3.py:122` = `inch(-9.875)`; l2 `_BAY_Z` = `inch(-8.375)` | **H1** |
| 153–157 | AH/ERV blower interlock | DEFERRED | — | table row 15 |
| 158–159 | No filter/access-panel field | DEFERRED | — | table row 15 |
| 160–162 | ERV condensate on `FX-B-SAUNA-FD` | DEFERRED | — | table row 15 |
| 163–165 | **Duct-against-duct ungraded outside a `Soffit`** | **DONE — superseded** | `checks/mep/run_interference.py` grades duct↔duct house-wide; `preferences.toml:319` class table row `duct <-> duct` = **0** | prune |
| 166–169 | ~~`DU-ERV-RISER-EXH`~~ FIXED | DONE | struck | prune |
| 170–175 | Nothing grades a duct against a conduit | **DONE** | `model/mep.py:443` `ConduitRun.elevations`; `grep -c` in `plan/electrical.py`: 17 `ConduitRun(` / 17 `elevations=`; `preferences.toml` "+29 THE RACEWAYS ARE PLACED IN z (E7)" | prune |
| 176–184 | ~~`haus route --run` refuses every duct~~ | DONE | struck; flags present in `cli/cmd_route.py` | prune |
| 185–205 | ~~Ports/bay sharing/duct sizing~~ (Phase 3) | DONE | `resolve/mep_ports.py`, `mep_packing.py`, `duct_sizing.py` all present | prune |
| 206–218 | ~~No blocker mobility/counterfactuals~~ (Phase 4) | DONE | `cmd_route.py:173,177` `--sweep`/`--counterfactual` | prune |
| 219–234 | ~~Whole-storey duct exceeds MAX_LATTICE_NODES~~ (Phase 7) | DONE | struck | prune |
| 235–248 | ~~No fitting is a part~~ (Phase 5) | DONE | `resolve/mep_fittings.py`, `library/fittings.py` | prune |
| 249–255 | ~~No whole-house coordination~~ (Phase 6) | DONE | `cmd_route.py:127` `--house` | prune |
| 256–262 | ~~Nothing can picture the routing space~~ (Phase 8) | DONE | `cmd_route.py:123` `--space` | prune |
| **263–553** | **The whole MEP-interference narrative** (145/146/147/150/188 counts, D1–D3, P1–P3, Phase 4 campaign, suite stack 0.48", radon pair, `--no-suppress` scores) | **PREFS** | `houses/catlin/preferences.toml:256–360` is the live record: **67**, class table summing to its own headline, dated 2026-09-19 | delete; leave one pointer line (Wave 5) |
| 550–553 | sub-bullet: "catlin authors no `ConduitRun.elevations` yet" | DONE (and factually wrong at HEAD) | 17/17 authored | prune |
| 554–562 | ~~Notching and boring limits not covered~~ | DONE | `checks/code/mn_residential/profile.py:77–79` lists R502.8.1 / R602.6 / R602.6.1 as covered | prune (its tail = the header gap, see next row) |
| 563–582 | **Three things this engine cannot see** (vent grade P3104.1; header over an opening; equipment with no ports) | OPEN ×3 | no `vent_grade` anywhere in engine; `resolve/mep_bores.py:338` category tuple is `("stud","king","jack","cripple","plate","sill")` — no header; `EQ-T-WATER-HEATER` (`plan/mep_hvac.py:185–187`) has cold **and** hot both at `(ft(0),ft(0),ft(4))` | **E1**, **E2**, **H2** |
| 583–587 | `EQ-M-ERV-MAN-SUP`/`-EXH` have no drawn feed | OPEN | no `DuctRun` into either | **H3** |
| 588–595 | FS-S-WEST truss panel layout provisional | DEFERRED | — | table row 16 |
| 596–599 | `FS-M-MECH` chase cluster undrawn | OPEN | only `FO-M-ERV-OA`/`-EA` exist | **H6** |
| 600–602 | `REG-S-HP-PLANT` throw | DEFERRED | — | table row 17 |

### Structural / framing residuals

| Lines | Entry | Verdict | Evidence | Destination |
|---|---|---|---|---|
| 605–608 | `FT-SG-*` frost cover UNKNOWN | DEFERRED | correct by design | table row 18 |
| 609 | French drains / form-a-drain | DEFERRED | — | table row 19 |
| 610–616 | Four stack matchers at three tolerances | OPEN (refactor only) | four helpers still distinct | **E5**; true unification stays (table row 6) |
| 617–619 | `_append_track_jamb_legs` bottoms on a removed plate | OPEN | unchanged | **E3** |
| 620–622 | `IfcBuildingElementPart` bodies carry no voids | OPEN | unchanged | **E15** (scope first) |
| 623–625 | `Slab`/`FloorSystem` rim has no cladding concept | DEFERRED | — | table row 20 |

### Schema gaps found during selections/fireplace passes

| Lines | Entry | Verdict | Evidence | Destination |
|---|---|---|---|---|
| 629–637 | **Resilient channel framed as a 2x6** | **DONE** | `resolve/framing/profiles.py:370` returns `_rect(0.5, 2.5)` for `"25 ga. resilient channel"`, listed in `_PARSED_LITERALS:389`; commit `421a23d4` | prune |
| 639–646 | Fireplace elevation checkable by no drawing | OPEN | no interior-elevation view kind | **H7** (scope first) |
| 647–663 | **No lintel type; a `Beam` standing in costs two things** | **SPLIT — half DONE** | cost 1 closed: `_RE_ANGLE` at `profiles.py:134–136` (commit `49291abf`) and `BM-M-FIRE-LINTEL` now authors `size="L3.5x3.5x0.25"` (`plan/storeys/main.py:2271`). Cost 2 open: still no per-LF/per-EA beam price path, no `Lintel`/`MasonrySpec` | rewrite (see §A); remainder → table row 20 |
| 664–675 | **Nothing grades a placeable against its host wall / stale mantel prose** | **DONE** | all three files read post-fix: `plan/electrical.py:783–794`, `plan/placeables.py:243–256`, `plan/millwork.py:335–341` all state the FINISHED-floor datum and `inch(64)`. **No stale prose remains** | prune (see §B) |
| 676–681 | `light_run_materials` unread price table | OPEN | `takeoff/lighting.py:255` still keyed on `item` | **E12** |
| 682–688 | **A `LightRun`'s load is invisible to the panel schedule** | **DONE** | `takeoff/electrical.py:52–72` `_connected_va` adds `line_voltage_run_va`; `takeoff/lighting.py:325–329` adds runs; commit `41164998` | prune |
| 689–693 | Door hardware has no schema vocabulary | OPEN | no `function` on `DoorType` | **E7** |
| 694–700 | Fixture vs code clearance after a size change (BATH2 vanity) | DONE (specific) / OPEN (general) | `FX-VANITY-48-SHALLOW` at `plan/fixtures.py:355`; `tests/test_catlin_bath2_vanity_heat_and_joists.py` exists | prune the vanity; general sweep → **R3** |
| 701–705 | R502.10.1 single-member header span | DEFERRED | — | table row 20 |
| 706–710 | `W-M-FIRE` is five stacked thin walls, no continuity check | **HALF DONE** | `checks/integrity/wall_stack.py` exists and names `W-M-FIRE` as the panel it was written from. What stays open is the `Wall.voids` schema | prune the continuity half; `Wall.voids` → table row 20. **See §C** |
| 711–731 | Second-floor drain noise solved by layout | DONE (a record) | numbers recorded; `CR-LIVING-CEIL-RC` exists | prune |
| 732–742 | "IRC P2604" in prose at 6 sites | OPEN | still in `checks/mep/plumbing_concrete.py`, `resolve/mep_sleeves.py`, `plan/mep_sleeves.py`, `plan/mep_drainage.py`, `notes/garage_hydrant.md`, `tests/test_hydrant.py`, `tests/test_plumbing_pass.py` | **E9** |
| 743–750 | Pipe support spacing (UPC 313.3) | DEFERRED | — | table row 14 |

## Phase 2 — Complete Catlin junctions (752–764)

All six bullets: **DEFERRED by decision 2026-08-02**. Plan says keep the section verbatim.

## Current Orientation (766–769) — keep.

## Questions

| Lines | Entry | Verdict | Evidence | Destination |
|---|---|---|---|---|
| 773 | Floor drains in laundry | **DONE (decided)** | "deferred 2026-07-30: neither, for now" — a settled decision, not a queue item | prune |
| 774–776 | Showers: one of four classified | DEFERRED | design tier | table row 21 |
| 777–779 | `FX-S-BALC-HYD` sleeve | DEFERRED | design tier | table row 21 |
| 780–781 | Cavity RH canary sensors | DEFERRED | design tier | table row 21 |
| 782–787 | `RM-S-PLANT` clear face / liner | DEFERRED | — | table row 2 |
| 788 | Access panels | DEFERRED | design tier | table row 21 |
| 789 | Garage switched back to concrete footings | OPEN | `FT-GF-*` are R403.5 crushed stone since 2026-09-15 but `PD-BW-GW/-GE/-RNE` still declare `cast_with` on them (`params/north_entry_frame.py:624`; `houses/catlin/CLAUDE.md:2429` calls it stale) | **H5** |
| 790 | `TR-SG-LEADER-SE` leader shoe | DEFERRED | design tier | table row 21 |
| 791 | Plant-room watering | DEFERRED | design tier | table row 21 |
| 792 | Frost-free hydrants render no penetration, sit low | OPEN | unchanged | **E11** |
| 793 | **Fireplace into brick + lintel + lower it** | **DONE** | sill `inch(24)` + `recessed_into_host_surface=True` (`plan/electrical.py:830–835`); `BM-M-FIRE-LINTEL` at `plan/storeys/main.py:2270` | prune |
| 794 | Kitchen lights above cabinets | DEFERRED | design tier | table row 21 |
| 795 | **Bituthene selection** | **DONE (settled)** | `library/materials.py:255–266` carries the selection + the Low-Temperature/Primer B2 LVC note; `prices.toml:3349,3363` | prune |
| 796 | `Material.product_ref` library/house override | DEFERRED | — | table row 22 |
| 797 | `FS-SG-DECK` tilted-beam joists | DEFERRED | — | table row 23 |
| 798–810 | **Disciplines toggles: 3 of 4 closed, 1 real** | **SPLIT** | the three closures stand; the multi-trade one is open — `ui/src/model/tradeVisibility.ts` has `anyTradeVisible:74` and `primaryTrade:265` but **no `primaryTradeVisible`** | prune the 3; the 4th → **E13** |
| 811 | Rain garden | DEFERRED | design tier | table row 19 |
| 812–821 | Soffits: three retired, three stay | DONE (a record) | `Room.exposed_services` in use | prune; `SF-B-BATH` question → table row 21 |
| 822–823 | Rebar inside `[concrete]` $/cy | DEFERRED | design tier | table row 21 |
| 824–827 | Trim/baseboard, orientation glass, room "hop", study alcove | DEFERRED | design tier | table row 21 |
| 828–833 | Pyodide GEOS smoke test in CI | OPEN | no Pyodide job in `.github/workflows/` | **E14** |
| 834–839 | `macros_walls.py` hardcodes `"Wall"` | **OPEN, line refs stale** | `macros_walls.py` now has ONE `"Wall"` literal at `:79` and it is an **add** of a genuinely new plain wall; the split/heal path moved to `item.element_kind` (`:142`). The real residue is `source/macros_split.py:166,245,246` (update/delete ops) and `source/macros_rooms.py:153,229` | **E10** — rewrite the entry against those lines |
| 840–842 | `W-B-CW3`/`W-B-STR2` over-specified | DEFERRED | — | table row 21 |
| 843 | EV charger = Leviton 1450R | OPEN | `ED-T-EV-1450` at `plan/electrical.py:969`; no `Product` for the Leviton | **H4** |
| 844–865 | `_y_in_n` / `house_ext_layers_in` / `D-M-BALC` landing | **SPLIT: landing DONE, constant OPEN, union OPEN** | `code.R311_3_exterior_landing` does **not** appear in the FAIL report at HEAD — `W-B-BRICK.top_elevation` is `inch(-8)` with the porch joists run north over it (`plan/storeys/basement.py:995–1003`, commit `6ad17b91` era). `house_ext_layers_in = 5.0` is **still** stale at `houses/catlin/params/sunken_garden.py:213` against `_WALL_OUTBOARD_IN` 7.25" | prune the landing half; stale constant + landing-union → **E4** |
| 866–871 | Framing member buried in a wall layer | DEFERRED | — | table row 4 |
| 872 | Cat litter box | DEFERRED | design tier | table row 21 |

## Project Management (874–897)

| Lines | Entry | Verdict | Destination |
|---|---|---|---|
| 876–882 | "Built 2026-09-11 … What was on this list and is now done: …" | **DONE — prune the "what is now done" sentence**, keep the section | prune sentence |
| 884–892 | Five deferrals (photos/voice, bids-as-GC, calendar, bid image, local-first sync) | DEFERRED | table row 24 |
| 894–897 | The three-phase product statement | keep | — |

---

## §A — Proposed replacement text: the steel-angle / lintel entry

`plans/TODO.md:647–663`. The whole entry is currently written as two live costs; cost 1
closed on 2026-09-15. **Replace lines 647–663 with:**

```markdown
- **There is no lintel element type, and a `Beam` standing in for one still bills $0.**
  `BM-M-FIRE-LINTEL` is the fireplace's steel angle authored as a `Beam` — free-string
  `size`, two ends, a span. The SECTION half is closed: `cross_section` reads the AISC
  decimal spelling (`_RE_ANGLE`, `resolve/framing/profiles.py:134`) and the element authors
  `size="L3.5x3.5x0.25"`, so the drawn solid is the angle and not a 3 1/2" square of steel.
  The fraction spelling (`"L3-1/2x3-1/2x1/4"`) is deliberately NOT accepted and is reported
  by `integrity.member_profile_parses` rather than guessed at.
  **What is left is the money.** A `Beam` reaches the estimate only through its `assembly`,
  as a `beam · <assembly>` **cubic-yard** row. Leaving `assembly` unset is deliberate — a
  $/cy rate is the wrong shape for a steel angle and inventing a steel assembly would file it
  in the concrete ladder — so the dollars are an `[allowances]` lump instead. Wants a
  per-LF/per-EA beam price path, or a real `Lintel` / `MasonrySpec` opening. **The same trap
  is live for any steel member anywhere in the house**, not just this one.
```

## §B — The mantel stale-prose item: there is nothing to fix

The plan's Wave 0 bullet says to "fix whatever still describes the pre-fix mantel" in
`plan/electrical.py` and `plan/placeables.py`. **Both already read post-fix**, and so does
`plan/millwork.py`:

- `plan/electrical.py:783–794` — "`Mount.elevation` is measured from the ROOM'S FINISHED
  FLOOR, not the subfloor … plan/placeables.py now authors `inch(64)`".
- `plan/placeables.py:243–256` — "`elevation` IS THE BASE, AND ITS DATUM IS THE FINISHED
  FLOOR (corrected 2026-09-11)", quoting the old text explicitly as the old text.
- `plan/millwork.py:335–341` — "It was authored `inch(64.9375)` against the old subfloor
  reading, which applied that 15/16" twice".

The element itself is `mount=Mount(kind=MountKind.WALL, elevation=inch(64))`
(`plan/placeables.py:268`). **No edit is proposed.** TODO.md:673–675's closing sentence
("What survives is prose: the comments at `plan/millwork.py` and `plan/electrical.py` still
describe the pre-fix mantel") is itself the only stale text, and it goes with the entry.

## §C — Where the plan's coverage claims are wrong

1. **Entry count.** The plan says 73 top-level entries. Counting `^- ` / `^ - ` bullets plus
   the section bodies gives **~88** (the MEP-interference narrative alone is 22 nested
   bullets over 291 lines). The mapping below still covers everything; the headline number
   is low.
2. **The mantel prose is already clean** (§B). No Wave-0 edit exists for it.
3. **`Wall.published_span` is not what `model/elements.py:121` shows.** That field is on
   **`Door`**. E6 still has to add it to `Wall` — the plan's decision table implies it may
   already be half there.
4. **E8's premise has partly landed.** `checks/integrity/wall_stack.py` already grades
   stacked-wall elevation continuity and names `W-M-FIRE` as the panel it was written from.
   E8 should be re-scoped to whatever `wall_stack.py` does *not* cover (or dropped), and the
   `Wall.voids` schema gap is the part that remains.
5. **The expected FAIL count is wrong.** Waves 4's verification says "expect the 2 deliberate
   `column_base` embedment FAILs". HEAD shows **1 FAIL**, and it is
   `structural.lateral_racking` on `PT-BW-RNE` (embedment, non-constrained, d/c 2.21), not
   `column_base`.
6. **`macros_walls.py`'s line references are stale** and the file is mostly fixed; E10's real
   targets are `macros_split.py:166,245,246` and `macros_rooms.py:153,229`.
7. **`D-M-BALC` is confirmed fixed** (no `code.R311_3_exterior_landing` finding at HEAD), but
   `house_ext_layers_in = 5.0` is confirmed **still stale** — E4's second half stands.
8. **Duct-against-duct outside a `Soffit` is superseded**, as the plan suspected: the class
   table in `preferences.toml` scores it 0.
