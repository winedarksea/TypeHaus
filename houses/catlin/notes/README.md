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
| `board_batten_girt_span.md` | `engineering/wall_panel.py` (`tests/test_wall_panel_calcs.py`) | live |
| `balcony_moment_columns.md` | `engineering/deck_post.py` §5 → `engineering/glulam_beam.py` (`tests/test_pier_section_calcs.py`) | live |
| `breezeway_piers.md` | `engineering/deck_post.py`, `engineering/pier_basis.py` | live |
| `catlin_truss_engineering.md` | `typehaus/wind.py` (`tests/test_wind_loads.py`); `rafter/RF-*` deferral | live |
| `centre_pillar_bearing.md` | `engineering/post_bearing.py` (`tests/test_post_bearing.py`) | live |
| `sunken_garden_court_free_body.md` | `engineering/retaining_system.py`, `retaining_basis.py` (`tests/test_retaining_court.py`) | live |
| `sunken_garden_piers.md` | `engineering/pier_basis.py`, `engineering/spread_footing.py` (`tests/test_pier_calcs.py`) | live |
| `sunken_garden_retaining_screening.md` | `engineering/retaining_wall.py` §4 (`tests/test_retaining_wall_calc.py`) | live |
| `uplift_load_path.md` | `lateral_uplift/RF-*` deferral (`tests/test_uplift_load_path.py`) | live |
| `soffit_rung_deflection.md` | `checks/structural/soffit.py` | live |
| `rebar_backout.md` | the rebar back-out in `takeoff/reinforcement.py` | live |
| `ridge_beam_detail.md` | `header/D-G-OVERHEAD` deferral; the ridge beam section | live, revised in part |

## Design and decision notes — reasoning, not an oracle

These carry the argument behind a choice. No calculation is pinned to them, and no test
reproduces them; they are here because the reasoning is worth keeping.

| Note | Subject |
|---|---|
| `bath2_over_toilet_cabinet.md` | the over-toilet cabinet and its clearances |
| `beam_water_protection.md` | keeping water out of a built-up exterior beam |
| `east_breast_bearing.md` | RM-M-LIVING's fireplace surround: why the brick bears on `W-B-E1`'s pour and not on the floor, the opening it needs through `FS-M-EAST`, and the list of things nothing in `haus check` looks at |
| `fortified_roof_cert.md` | what the FORTIFIED Roof designation asks for |
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
