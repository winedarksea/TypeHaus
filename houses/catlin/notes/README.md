# `houses/catlin/notes/` — the note set

Two kinds of file live here, and the difference decides what may be edited.

**Calculation notes** are the independent hand passes that verify this engine's engineering
suite. The rule they exist for is in the root `CLAUDE.md`: *every calculation is oracled
against an independently hand-worked note — a calc that only agrees with itself is not
verified.* They are worked by hand, from the authored geometry and the published standard,
**before or apart from** the code they check, and a test named on each one reproduces its
numbers. `haus calcs` prints the note beside every result, so a reviewer holding the
calculation package can reach the hand pass behind it.

**Detail notes** are named by a `Transition.notes=` in `plan/transitions.py`. Those, and
only those, are *drawing content*: their prose renders onto the detail sheets and G-002 and
is byte-pinned by `tests/test_section_goldens.py`. Editing one is a deliverable change, not
a documentation change. `applied_to:` frontmatter is **not** the test — several notes carry
it and render nowhere, which is what this README used to get wrong. They are listed at the
bottom and are outside this document's normalisation.

A detail note's drawing content lives under a `## Sheet notes` heading, split three ways
(`### General` / `### Keyed` / `### Spec <section>`) per `emit/draw/sheet_notes.py`;
everything below `# Notes` is the design record and prints nowhere.

`TEMPLATE.md` is the shape a new calculation note takes. `superseded/` holds notes whose
design is not built; each opens with a `⛔ SUPERSEDED` banner naming what replaced it, and
each is kept because the *rule* it established usually outlives the design that prompted it.

---

## Calculation notes — what each one oracles

| Note | Oracles | Status |
|---|---|---|
| `board_batten_girt_span.md` | `engineering/wall_panel.py` + `engineering/wall_panel_withdrawal.py` (`tests/test_wall_panel_calcs.py`) | live |
| `balcony_moment_columns.md` | `engineering/deck_post.py`; §5 is now the NDS cross-check beside a published-table read, not an oracle (`tests/test_pier_calcs.py`) | live |
| `breezeway_piers.md` | superseded by foundation bridge | retired 2026-09-10 |
| `north_entry_structure.md` | the north entry bearing map and what carries what | live |
| `north_entry_piers.md` | `engineering/roof_beam.py` §5, `engineering/pier_basis.py` / `deck_post.py` / `spread_footing.py` §6 (`tests/test_north_entry_piers.py`) | live |
| `hp3_north_relocation.md` | cabinet/stand, airflow and services | schematic |
| `catlin_truss_engineering.md` | `typehaus/wind.py` (`tests/test_wind_loads.py`); the `rafter/RF-{GARAGE,BW-CANOPY}` deferral — the two TRUSSED roofs only | live |
| `centre_pillar_bearing.md` | `engineering/post_bearing.py` (`tests/test_post_bearing.py`) | live |
| `sunken_garden_court_free_body.md` | `engineering/retaining_system.py`, `retaining_basis.py` (`tests/test_retaining_court.py`) | live |
| `sunken_garden_piers.md` | `engineering/pier_basis.py`, `engineering/spread_footing.py` (`tests/test_pier_calcs.py`) | live |
| `sunken_garden_retaining_screening.md` | `engineering/retaining_wall.py` §4 (`tests/test_retaining_wall_calc.py`) | live |
| `uplift_load_path.md` | `lateral_uplift/RF-*` deferral (`tests/test_uplift_load_path.py`) | live |
| `soffit_rung_deflection.md` | `checks/structural/soffit.py` | live |

### Published-table reads

Not calculation notes and not deferrals: a manufacturer publishes a row, a reviewer opens
the document, and the question is closed. Each is authored on the element as a
`PublishedSpan` and graded by `checks/structural/published.py`, with drift guards so a
retype or a spacing change turns the PASS back into an UNKNOWN.

| Note | Reads | Status |
|---|---|---|
| `garage_door_header.md` | Weyerhaeuser TJ-9000 p.9 → `structural.header_prescriptive` on `D-G-OVERHEAD` | live |
| `roof_rafter_span_read.md` | Weyerhaeuser TJ-4000 p.12 → `structural.rafter_span` on `RF-HOUSE`. §3 is OPEN | live |
| `balcony_moment_columns.md` §5 | Anthony/Canfor Power Preserved Glulam Deck Guide Table 2 → `structural.deck_beam_span` on `BM-SG-BL{W,C,E}` | live |

| `rebar_backout.md` | the rebar back-out in `takeoff/reinforcement.py` | live |
| `ridge_beam_detail.md` | the ridge beam section. Its §hanger reaction (600 lb at 4:12) is SUPERSEDED by `roof_rafter_span_read.md` §4 (~980 lb at 6:12), and it no longer oracles the garage header — that deferral is gone | live, revised in part |
| `mep_drain_routing_basis.md` | `routing/{gravity,corridors,graph,search,tree}.py` (`tests/test_routing_oracle.py`); `mep.fixture_drain_reach` §1 | live, ahead of the code it oracles |
| `mep_duct_routing_basis.md` | `routing/trades/duct.py`, the corridor half of `routing/corridors.py` | live, ahead of the code it oracles |

## Design and decision notes — reasoning, not an oracle

These carry the argument behind a choice. No calculation is pinned to them, and no test
reproduces them; they are here because the reasoning is worth keeping.

| Note | Subject |
|---|---|
| `bath2_over_toilet_cabinet.md` | the over-toilet cabinet and its clearances |
| `beam_water_protection.md` | keeping water out of a built-up exterior beam |
| `east_breast_bearing.md` | RM-M-LIVING's fireplace surround: why the brick bears on `W-B-E1`'s pour and not on the floor, the opening it needs through `FS-M-EAST`, and the list of things nothing in `haus check` looks at |
| `fortified_roof_cert.md` | what the FORTIFIED Roof designation asks for |
| `garage_orientation_lot.md` | the south-lot/east-driveway premise the garage was drawn for, why it never agreed with `plan/site.py`'s own north FRONT setback, what turning the door north moved, the eastward move that followed it, and the revert recipe |
| `heat_pump_ground_pad.md` | why the condensers left the balcony, and why the three of them now stand on three separate pads on three sides of the house |
| `interior_selections.md` | the 2026-09-06 interior pass: what was chosen and why, the category-by-category import verdict, and the five things it found that were wrong rather than merely unspecified |
| `mixed_deck_movement_joint.md` | the movement joint where two deck materials meet |
| `pantry_climbable_shelving.md` | the climbable-shelving rule and what it retired |
| `pocket_door_at_laundry.md` | the pocket door and the wall it is cut into |
| `porch_enclosure.md` | the seasonal curtain track that replaced the glazed enclosure |
| `porch_stair.md` | the porch stair geometry |
| `roof_flash_and_batt.md` | the unvented flash-and-batt roof and its condensation gate |
| `system1_return_path.md` | the one return grille, and the six door undercuts that are the whole return path |

## Detail notes — drawing content, byte-pinned

**Do not edit these as documentation.** Their prose renders onto the detail sheets and
G-002 and is pinned by `tests/test_section_goldens.py`. Exactly six files reach a drawing —
grep `notes=` in `plan/transitions.py` for the list, which is the only authority:

`basement_to_framed_wall_detail.md` · `garage_wall_detail_side.md` ·
`outie_window_truss_detail.md` · `plant_room.md` · `roof_wall_eave_detail.md` ·
`sauna_basement_wall_detail.md`

Five files this section used to name — `backup_power.md`, `balcony_irrigation.md`,
`garage_hydrant.md`, `sauna_shower_basement_detail.md`, `shower_niche.md` — are referenced
from `plan/*.py` **comments only** and render nowhere. They are design notes, and they are
free to be edited as documentation.

## Superseded

| Note | Replaced by | What survives |
|---|---|---|
| `superseded/balcony_lateral_bracing_design.md` | `balcony_moment_columns.md` | the wind derivation, and the record of the braced scheme that was not built |
| `superseded/heat_pump_deck_mounting.md` | `heat_pump_ground_pad.md` | the rule: a fastener through a deck that is a roof lands in a sacrificial member |
