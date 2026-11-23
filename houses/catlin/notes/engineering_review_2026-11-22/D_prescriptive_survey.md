# D — Prescriptive survey: what can leave the engineering register (houses/catlin)

Reviewer D, 2026-11-22. Report only: no repo file edited, no `haus`/pytest run. Sources read: the
18 calc sheets under `houses/catlin/out/calcs/calcs/`, `out/review/engineering.json`,
`out/review/check.txt` / `check_all.txt`, the routing checks under
`packages/engine/src/typehaus/checks/` (`engineered_rows.py`, `structural/foundation.py`,
`deck.py`, `snow.py`, `published.py`, `stacked_ladder.py`, `sheathing_edge_support.py`,
`concrete_materials.py`, `bracing_eval.py`), the plan (`plan/assemblies/mixes.py`,
`plan/storeys/{main,second}.py`, `params/{main,second}_deck.py`) and the oracle notes named
below. Web reads were done by a helper agent on up.codes and maker sites. Where it saw a page
only through a summariser, I say so, and anything nobody opened is marked **UNVERIFIED**.

## 0. Headline

- **About 20 of the 51 items can leave the register with no structural redesign.** Two routes
  do it. One is reclassifying a computed demand against a published maker/code row as a
  prescriptive read; the repo already does this for roof uplift and the cladding screw. The
  other is a small authored change.
  - Kinds: `rafter` 2, `veneer_anchor` 1, `tiered_retaining` 5, `girt_screw` 1,
    `band_header` 1, `glulam_beam` 2, `deck_tie` 1.
  - `deck_post` (6 north-entry piers) and `column_base` 2 also go, if the piers are re-declared
    pinned and the entry's lateral load is sent through the deck tie and the garage diaphragm.
- **About 30 items exist because of three architectural choices.** None of them is a code
  necessity:
  - the court balcony's **cast cantilever columns**: `base_rotation`, `column_head_joint`,
    `column_support`, `deck_post/PT-SG-*`, 14 items;
  - the **9 ft cantilever court**: `retaining_wall`, `retaining_system`, 4 items;
  - the **court pours abutting the house through load-bearing XPS**: `thermal_break_transfer`,
    5 items.
  - Plus the north-entry canopy's **screen shear wall used as a second lateral path**
    (`lateral_system`, `wood_roof_post`, `roof_beam`, 7 items).
  - The plain prescriptive alternative for each is in §1.2. Most cost the owner something
    visible.
- **Reverse risk (Part 3). Four PRESCRIPTIVE passes rest on conditions nobody grades:**
  - **(R1)** the story count for wall bracing assumes the habitable attic is "not a story" under
    IRC R325.6, but **R325.6's area condition is never checked**;
  - **(R2)** ~240 plf from `W-S-SN3`/`FO-A-HALL`'s trimmer rides one J12 floor truss, outside
    the uniform-load table that passes `FS-S-WEST`;
  - **(R3)** the court walls `W-SG-W1/E1` pass Table R404.1.2(8), which has no surcharge, while
    carrying the fixed-column base moments, and no check grades the wall stem for them;
  - **(R4)** the retaining records take bearing and friction off the 42" stone bed (IBC class 3),
    and nobody checks the stone/GM interface underneath.
- **Part 2: the concrete-mix UNKNOWNs are spec fields and can be completed now**, except ASR,
  which needs the plant's aggregate data (exact edits in §2.1).
- **The `stacked_line_ladder` UNKNOWN is a real load path, not paperwork** (R2), and the plan
  contradicts itself about whether `W-S-SN3` bears.

---

## 1. Part 1 — the register

### 1.1 Table: kind by kind

The "why engineered" column is the routing check's own reason, with the number.

| Kind (n) | Why it is engineered | Prescriptive / maker route that could replace it | Design change | Cost / complexity | Verdict |
|---|---|---|---|---|---|
| `rafter` (2: RF-GARAGE, RF-BW-CANOPY) | `snow.py:220` — the roof "resolves no rafters (trussed)", so `engineered(... "IRC R802.4")` NO_CALC | A metal-plate truss is a **deferred submittal under IRC R802.10.1/R802.10.2** (truss design drawings to TPI 1). It is the fabricator's sealed component, not a house PE item. Off-the-shelf trusses come with a stock design drawing. | None. Reclassify the item as a deferred submittal. Order the canopy truss against the drift case (`north_entry_piers.md` §3). | Nil. A procurement document. | CONVERT-AS-IS (deferred submittal; out of the PE seal set) |
| `veneer_anchor` (1: W-B-BRICK) | `veneer_cavity.py:77`: 6.500" back of brick to stud, past the 2018 Table R703.8.4(1) maximum of 4½" (W1.7) | **2021 IRC Table R703.8.4(1)** adds a W2.8 (0.187") adjustable-wire row, ">4⅝ in." to "max 6⅝ in." (up.codes, Texas 2021 copy), as an **R104.11 alternate**. Maker data: **Hohmann & Barnard 2-Seal Tie (wood stud)** tech note, tested at "CAVITY 6½"" (4½" insulation + 2" air); working loads at 0 / 1¼" offset are tension 573/206 lb and compression 402/166 lb. It has **no ICC-ES report**. | (a) None: an AHJ alternate request on the 2021 row. Meet the 2021 footnotes: pintle offset ≤ 1¼", two pintle legs, pintle end ≤ 2" from the brick face. (b) **Plain 2018 route: cut the cavity XPS from 4" to 2"**. That gives 6.5 − 2 = **4.5"**, exactly W1.7's limit, so 1½" XPS for tolerance. It costs ~R-10 on W-B-S1..S4 behind the brick (energy compliance UNVERIFIED). | (a) One letter. (b) Cheap material, but an energy trade. | CONVERT-AS-IS via R104.11 (no seal). CONVERT-WITH-SMALL-CHANGE if the AHJ refuses. |
| `tiered_retaining` (5: W-RG-*) | Not a code trigger. It is in `engineered_rows.py` as a kind: "a footingless gravity wall retaining fill above a taller cut". The sheet says IRC R404.4 SF 1.5. | **IRC R404.4 does not reach these walls.** Its trigger (up.codes MN 2018) is "retain in excess of 48 inches of unbalanced fill, or ... exceeding 24 inches in height that resist lateral loads in addition to soil". These retain 40"/36"/37" of soil only (CLAUDE.md "Sunken garden court"). Maker read: **Allan Block "AB Gravity Walls, 12°" chart** (commercial manual, charts-and-tables page), level backfill, clay 27°: **3'-6" exposed** ≥ 3'-4" here. With a solid surcharge the chart drops to 1'-8". Seen through a summariser only, no page number: **UNVERIFIED** until someone opens the PDF. | None, provided no surcharge (paving, a structure) is ever placed on the terrace within the wall's zone. Keep the tier interaction where it already is: the apron's bearing on the court walls is inside `retaining_wall/system` (`tier_surcharge.py`). | Nil | CONVERT-AS-IS (code not triggered + AB chart) |
| `girt_screw` (1) | No prescriptive table for an 8" screw through a 6" stack. Capacity is ICC-ES ESR-1078 Tables 2/3, demand is ASCE 7 wind. | Same pattern as `published.graded_against_published_capacity`: a demand the engine computes against a **published evaluation-report allowable**. The cladding fastener's NDS arithmetic is already only an ADVISORY (`structural.cladding_fastener`); this one is more table-based than that, yet it is a seal item. | None. Engine: grade it through a `PublishedCapacity` (ESR-1078 T2/T3 row, SG, side-member thickness, coating guard) instead of `engineered()`. | Small code change | CONVERT-AS-IS (reclassify). A reviewer may still want to see the 0.6W tributary. |
| `band_header` (1: D-B-SUNKEN) | Floor-band header, not a wall header, so no R602.7 row. NDS on Microllam design stresses (TJ-9000 p.5). | A **maker header/beam table**: the Boise VERSA-LAM Header Guide p.4/p.9 the house already reads for `D-M-LAUN` and `WIN-M-DINING-E`, or Weyerhaeuser's LVL floor-beam load table (page **UNVERIFIED**). Every jamb load lands on the seats (`loads_inside_span 0`), so the span carries only a 0.71 ft floor strip: bending 0.011, shear 0.018. Any floor-beam row covers it many times over. The TJ-8000 rim reads that govern (0.43) are already published reads. | Author a `PublishedSpan` (Boise p.9 "Floor Beams" 2-ply 1¾ x 11⅞, ≥ 6' clear) and let `band_header` accept it, like `header_prescriptive`. | Small data + code | CONVERT-WITH-SMALL-CHANGE |
| `glulam_beam` (2: BM-SG-BLW/BLE) | `deck.py:1266`: "a glulam in WEATHER, which no IRC table publishes a row for". The supplier rows are dry-use (refused on `service_condition`). | **IRC 2018 Table R507.5, Southern Pine 3-2x12: 8'-10" at an 18' joist span** (up.codes; one source shows 8'-9"/8'-10" overlaid, so read **8'-9"**), against a **7.33'** beam span. Cantilevers 0.67'/1.67' are ≤ ¼ of the allowable span (2.19'). R507 tables are wet-service by construction. No wet-use glulam table was found: Anthony Power Preserved and Rosboro PR-L251 are both explicitly **dry-use** (helper agent, PDFs parsed). | Retype both beams to **3-ply 2x12 No.2 KDAT/treated SYP**, 4½" wide, which suits the 12" column tops. **Engine:** `deck_tables.DECK_BEAM_SPAN_FT` carries only one "most restrictive" column (3-2x12 at 18' = 6.83'), so it would FAIL this. Add the SP beam rows (the joist table already has species). Check the HETA20Z seat strap and H10ASS spacing against the 4½" face. | Lumber is cheaper than glulam; one table edit | CONVERT-WITH-SMALL-CHANGE |
| `deck_tie` (1: FS-BW-FLOOR) | A deck braced by HL angles to the garage's concrete. Simpson HL row, demand from wind/torsion. | Code: IRC 2018 **R507.9.2** wants hold-downs at 2 locations ≥ 1,500 lb or 4 at ≥ 750 lb (up.codes), but into the house's **floor framing** through a ledger, not into a concrete stem. Literal compliance would need a ledger + R507.9.2 devices on `W-G-S`'s framing. Maker read: HL33/HL43 rows (Simpson C-C-2024 p.303) are already the capacity. | (a) Reclassify as demand vs published capacity (as with `girt_screw`). (b) A literal R507.9 ledger to the garage framing with two 1,500 lb hold-downs. | (a) code change; (b) moderate | CONVERT-AS-IS by reclassification. The demand includes a torsion model a reviewer may still call design. |
| `deck_post` PT-BW-E/GE/W/GW/PE/PNE (6) + `column_base` PT-BW-PE/PNE (2) | `deck.py:588`: "no IRC Table R507.4 row for a {round concrete} post". The piers are **declared fixed** (moment piers), and `column_base` grades the fixed base's embedment. | **R507.3.1 pad + R507.4 6x6 PT post** on a short pier. The deck's lateral load is already carried by `deck_tie` to the garage, and the canopy's by its diaphragm into `RF-GARAGE`. So the piers do not need to cantilever: they carry 1.1–7.3 kip of gravity at d/c ≤ 0.02. | Declare the piers pinned (drop `_MOMENT_PIERS`). Grade the pads under R507.3.1 (they already pass it). The pier becomes a footing extension under a post base. The dowel-anchorage states (0.85) disappear. Depends on `deck_tie` carrying both directions (it grades N-S and E-W, torsion included). | Lighter cages; one modelling change | CONVERT-WITH-SMALL-CHANGE (conditional on `deck_tie`) |
| `wood_roof_post` (4) | No IRC table for a roof post; NDS. **Governing is lateral**: SB-BW-BAND pushes 517 lb into the post (combined 0.538) and the ACE6Z head takes uplift + drag (0.55). | Pure gravity: 6x6 at 7.7' against the R507.4 14' cross-check (by analogy only; R507.4 is a deck table). Heads and bases are published ESR reads (ESR-2604 T3, ESR-3096 T5, ESR-3050 T2). | Take `W-BW-SCREEN` + band braces **out of the lateral system** (the canopy already carries 100% N-S through the garage joint, "double envelope", owner 2026-11-14). The posts become gravity + connector reads. | Removes eight KBS1Z, the chord hold-down demand and the band design | CONVERT-WITH-SMALL-CHANGE (partial: connectors as published reads; the post stays NDS by analogy) |
| `lateral_system` (1: RF-BW-CANOPY) | An open-front diaphragm + shear panel, SDPWS §4.2/4.3. Governs 0.908 at the screen. | None. R602.10 does not cover an open canopy diaphragm. Dropping the screen as a lateral element shrinks it to the canopy-to-garage delivery. | As above | — | STAYS-ENGINEERED (smaller if the screen is dropped) |
| `roof_beam` (2: BM-BW-RW/RE) | Treated glulam in weather; truss chord bearing 0.877 governs. | No wet-use glulam roof-beam table found (see `glulam_beam`). R602.7 is a wall-header table. | Could become a sawn treated 3-ply member if a span read existed. None found. | — | STAYS-ENGINEERED (small calc) |
| `retaining_wall` (3: W-SG-E2/S/W2) | `foundation.py:233`: `lateral_support="base"`, so the wall is "restrained at its base and free at its top", R404.4. | **Table R404.1.2(8)** if the tops are braced. CLAUDE.md "Sunken garden court" records that #5@10 would pass the table against #6@38 required. **Or keep the retained height ≤ 48"** (R404.4 not triggered). | (a) Top struts/beams across the 17' court (a pergola or deck over the garden): loses the open sky. (b) A terraced court of ≤ 4' steps: loses the 9' sunken garden. | High: architectural | STAYS-ENGINEERED (unless the owner gives up the open 9' court) |
| `retaining_system` (1: W-SG-ARCH) | Court sliding as a closed loop, FS 1.735 | Same as above | Same | High | STAYS-ENGINEERED |
| `thermal_break_transfer` (5) | Isolation boards passing court thrust into the house slab edge (22.5 kip; FOAMULAR NGX sustained-load rule 0.676) | No table. The plain alternative is a **true separation**: a compressible, non-load-bearing joint (or a clear gap) at every court/house contact, with the court self-stable on its own loop. Its sliding check already shows "court sliding under break thrust 0", so the loop does not need the house. The item would then be N/A. | Change the 15/100 psi XPS boards to a compressible filler. Check that the court loop FS still holds without the house's restraint (it is computed without it). Check the veneer beam's bearing on FT-SG-W1/E1 toes. | Moderate | CONVERT-WITH-REDESIGN (to N/A), or STAYS |
| `base_rotation` (4), `column_head_joint` (4), `column_support` (2), `deck_post` PT-SG-BF1/BF3/BR1/BR3 (4) | One choice: **four 12" cast columns fixed at the wall tops are the balcony's entire lateral system** (CLAUDE.md "Exterior colour, balcony and veneer"). No IRC table covers a cantilever concrete column or its joints. | Plain alternative: **wood 6x6 posts (R507.4) on the wall tops, beams per R507.5** (as `glulam_beam` above), lateral by **R507.9 attachment to the house**. The owner refuses that: separate structure, movement joint, brick. Or by **diagonal knee bracing of a freestanding deck**: AWC FAQ says DCA6 braces at corner posts. The DCA6 post-height threshold is **UNVERIFIED** (DCA6 PDF not opened). | Knee braces at the four corners in both directions. Posts on post bases on the wall tops. Guards would need posts again: today the columns are the porch guard posts. | Moderate. Visible braces change the look. | CONVERT-WITH-REDESIGN (owner's call); else STAYS-ENGINEERED |

Count: CONVERT-AS-IS 10 items (rafter 2, veneer 1, tiered 5, girt 1, deck_tie 1).
CONVERT-WITH-SMALL-CHANGE 15 (band 1, glulam 2, PT-BW deck_post 6 + column_base 2, wood_roof_post 4).
CONVERT-WITH-REDESIGN 19 (court columns 14, thermal break 5). STAYS 7 (lateral 1, roof_beam 2,
retaining 4). Total 51.

### 1.2 Engineered only because of an architectural choice: the plain alternative, honestly

| ID | Severity | What | Plain prescriptive alternative | Cost to owner | Class |
|---|---|---|---|---|---|
| D1 | GAP (goal 1) | Balcony on four fixed cast columns (14 items: `base_rotation`, `column_head_joint`, `column_support`, `deck_post/PT-SG-*`) | 6x6 KDAT posts on post bases on the W1/E1 tops; 3-ply 2x12 SP beams (R507.5 8'-9" ≥ 7.33'); knee-braced freestanding deck per DCA6 (UNVERIFIED threshold), or R507.9 ledger + two 1,500 lb hold-downs to the house | Knee braces in view. Guard posts return. Ledger/hold-downs cross the house movement gap (the owner rejected that). | DECISION. Recommend at least the beam change (D3), which is independent. |
| D2 | GAP | 9'-1" cantilever court (4 items) | Brace the wall tops so Table R404.1.2(8) governs (top struts or a deck across 17'), or ≤ 48" terraces | Loses the open 9' sunken garden. Owner unlikely to take it. | DECISION; keep engineered |
| D3 | GAP | Balcony glulams engineered because the maker's rows are dry-use | 3-ply 2x12 No.2 SYP, R507.5 | Cheaper | SMALL-FIX. Edit `params/sunken_garden.py` beam `size`/assembly to `3-2x12` SYP treated. Add the Southern Pine column to `deck_tables.DECK_BEAM_SPAN_FT` (3-2x12 row read off 2018 R507.5). Effect: `glulam_beam` 2 items leave; `deck_beam_span` PASS at 7.33/8.75 = 0.84. |
| D4 | GAP | North-entry piers declared as moment piers | Pinned piers, lateral via `deck_tie` + canopy diaphragm | Simpler cages | SMALL-FIX (modelling): drop `_MOMENT_PIERS` / fixed-base declaration in `params/north_entry_frame.py`. Expected: 8 items leave; `deck_footing_size` stays a PASS. Confirm `deck_tie` then covers the deck alone. |
| D5 | GAP | 6½" veneer cavity | 2" (or 1½") XPS in the cavity, giving ≤ 4½" | ~R-10 to R-12.5 lost behind the brick | DECISION. Recommend the R104.11 letter on the 2021 row (no design change). |
| D6 | GAP | XPS boards transmit court thrust into the house | Compressible joint, no transfer | Detailing only | DECISION |

### 1.3 Maker tables that could close an item as a published read (Part 1, second ask)

| Item | Maker document | Row / page | Status |
|---|---|---|---|
| `tiered_retaining/*` | Allan Block commercial manual, "Charts and Tables", AB Gravity Walls 12° | Level, clay 27°: 3'-6"; surcharge 1'-8"; slope 2'-8"; silty sand 32°: 5'-4" | **UNVERIFIED**: seen via summariser only, no page number |
| `veneer_anchor/W-B-BRICK` | H&B 2-Seal Tie Technical Notes (buildsite.com PDF) | Tested at cavity 6½": tension 573 / compression 402 lb working at 0 offset | Read (PDF parsed by helper). No ICC-ES. 2X-Hook values UNVERIFIED (snippet). |
| `veneer_anchor` (code) | 2021 IRC Table R703.8.4(1) | W2.8 adjustable, > 4⅝" to 6⅝" | Read on up.codes (2021 TX copy) |
| `girt_screw` | ICC-ES ESR-1078 (FastenMaster TimberLOK) | Tables 1A, 2, 3 (already cited) | Already in repo |
| `deck_tie` | Simpson C-C-2024 p.303 HL table | HL33/HL43 rows (already cited) | Already in repo |
| `wood_roof_post` joints | ESR-2604 T3 (ACE6Z), ESR-3096 T5 (A35Z), ESR-3050 T2 (CBSTQ66Z-SDS2) | already cited | Already in repo |
| `band_header` | Boise VERSA-LAM 1.7 2650 Header Guide 06/2009 r07/2011, p.9 Floor Beams | (repo already read it for D-M-LAUN) | Repo-read; the exact row for 5.78' seat-to-seat is not read here |
| `glulam_beam`, `roof_beam` | Anthony Power Preserved Glulam brochure; Rosboro APA PR-L251 | **Both dry-use**; wet factors left to the user | Read (helper). **No wet-service table exists** among those checked; Rosboro X-Beam Treated span table not found. |
| `column_head_joint` | Simpson HETA (FL11473 Table 3) | F1/F2 lateral values | **UNVERIFIED** (did not load) |
| `rafter/*`, `truss_reactions` | The stock truss's own design drawing (fabricator, TPI 1) | — | Outside input. Not a maker table. |
| `stacked_line_ladder` | SBCA/BCSI, TrimJoist, UFP/Triforce | — | **No published parallel-bearing-wall detail found** (UNVERIFIED negative) |

---

## 2. Part 2 — structural UNKNOWNs outside the register

### 2.1 Concrete mix spec fields: complete the spec

The values come from the check source (`checks/structural/concrete_materials.py`):
`CHLORIDE_LIMIT_PCT = {"C0": 1.00, "C1": 0.30, "C2": 0.15}` (Table 19.3.2.1, nonprestressed,
ASTM C1218), the F3 SCM caps (Table 26.4.2.2(b): fly ash 25, slag 50, silica fume 10, fly ash + SF
35, total 50), and the sulfate logic (S1 needs an MS cement: C150 Type II/V, or C595 "(MS)").

| ID | Sev | Finding | Edit (file `houses/catlin/plan/assemblies/mixes.py`) | Effect |
|---|---|---|---|---|
| P2-1 | GAP | `concrete_chloride_limit` ×3: no mix states its limit | `BURIED_MIX`: add `chloride_ion_max_pct=0.30,`. `EXPOSED_MIX`: `chloride_ion_max_pct=0.15,`. `INTERIOR_SLAB_MIX` and `DECK_CAP_MIX`: `chloride_ion_max_pct=1.00,`. Say in each `source=` that it is the **specified ceiling, confirmed by the C1218 result on the mix submittal**. | 3 UNKNOWN to PASS. The plant certifies; standard spec practice. |
| P2-2 | GAP | `concrete_scm_caps`: the cement is unnamed | `EXPOSED_MIX` (and `BURIED_MIX` for consistency): `cement=CementSpec(standard="ASTM C150", designation="I/II", source="spec: Type I/II portland, no blended cement"),`. `CementSpec` is exported through `typehaus.model`, so add it to the `from typehaus import (...)` list. If the plant ships **C595 IL** (now common in MN), `_blended` treats IL as non-blended and the cap check still PASSes, but see P2-3. | PASS (25% fly ash is at the cap exactly; the sheet already says so) |
| P2-3 | GAP / DECISION | `concrete_sulfate_cement`: no S class | Nobody has run a soil sulfate test. Two options. (a) **Design to S1** (covers S0 and S1 without a test): add `exposure_s="S1"` to all three live mixes, with cement `C150 "I/II"` (MS by `_resists`). S1's w/cm ≤ 0.50 and f'c ≥ 4,000 are met by all three (0.40/5,000; 0.45/4,000). (b) Take the S class from the sulfate test in the geotechnical investigation the soil gap already owes. **Do NOT author S1 with an IL cement**: `_resists` FAILs plain IL for MS. | (a) PASS now, conservative unless the soil is S2+. (b) Waits on the geotech. The mixes.py comment refuses "S0 as an assumption"; S1 is a bound, not a measurement, so state it as a design choice. Recommend (a) + confirm in the geotech. |
| P2-4 | GAP (outside input) | `concrete_asr` ×2 (W1) | Needs the plant's aggregate reactivity class (ASTM C1260/C1293, C1778 Table 1) and a structure class (S2 is plausible for a residence: **UNVERIFIED** C1778 reading). Then `asr=AsrSpec(aggregate_class="R?", structure_class="S2", prevention_level="?")` on BURIED_MIX and EXPOSED_MIX. **Cannot be authored now honestly.** Specify "prevention per ASTM C1778 for the aggregate's class, structure class S2" on the order and author the class from the submittal. | Stays UNKNOWN until the submittal |

### 2.2 `structural.sheathing_edge_support` ×2

| ID | Sev | Finding | Fix |
|---|---|---|---|
| P2-5 | GAP (real detail) | **North:** joints on W-M-N2/N3/N3B at run stations 256–400" are bare for **11.9"**, the whole second-floor band. The north run starts at `N-M-NE` (x=36'), so these stations are **x = 14'-8" to 2'-8"**, over **`FS-S-WEST`**. `params/second_deck.py:198` gives it `edge_rims=("lo",)` only, with the comment "the north one is opening trimmer packs". So between the openings, nothing stands at the face behind the main wall's 4x10 sheet, which laps that band (`wall_bracing_layout.md` §4). `sheet_layout_backing.py` credits a floor member only within ⅛" of the sheathing's back. | SMALL-FIX: `params/second_deck.py` `WEST_FLOOR.joists`, `edge_rims=("lo",)` → `edge_rims=("lo", "hi"),` (an LSL rim at y=36', the house rule "every gable-end edge line is an LSL rim board"). First check that no north-face opening (`FO-S-ERV-CHASE`, VR-M-STACK at y≈35'-1.3", the ERV risers) needs the last 1¼" at y=430.75–432". Expected: UNKNOWN to PASS for the N run. Medium confidence: no model run. |
| P2-6 | GAP (small) | **South:** W-M-S1/S2 joints at x≈13'-3", 16'-1", 20'-0", 22'-8", 25'-3" are bare **1.6"** only. Both FS-S-WEST and FS-S-EAST have a `lo` edge rim, so this is a partial strip, most likely a deck-edge inset or a z gap between the rim and the plate/subfloor. | Needs one look at the resolved geometry (z of the rim against the plate top and the subfloor edge). Not resolvable by reading. If it is a deck inset at D-S-BALCONY, a backer/ply strip closes it. |

### 2.3 `structural.stacked_line_ladder`: a real line load, and a plan contradiction

- **P2-7 (GAP, high consequence; links to R2).** `header_spans_r602_7.md` §4a–4b works the load
  that comes down `W-S-SN3` onto `W-M-HS3`/`HS4`. It is `FO-A-HALL`'s 2-ply LVL south trimmer +
  `W-A-HALL-S` + the wall + a floor strip, **≈ 240 plf**, plus `BM-S-BATH-E`'s 570 lb point.
  - The point has a squash block (`P-S-SN3-SQUASH`). The **uniform part reaches J12 truss y=272
    through the subfloor**, and nothing blocks it.
  - No published blocking detail between open-web trusses was found (helper search, UNVERIFIED
    negative).
- **Plan contradiction (REVIEWABILITY).**
  - `plan/storeys/second.py:417–447` says W-S-SN3 is **"NOT BEARING (reverted 2026-08-30)"**,
    because the trimmer is "hung" on a doubled trimmer joist.
  - `plan/storeys/main.py:697,702` makes `W-M-HS3`/`HS4` **BEARING**, with the comment "FO-A-HALL
    lands on W-S-SN3 above".
  - The header note says the trimmer **"lies on W-S-SN3's plate"**.
  - Pick one. The engine follows the second reading: HS3/HS4 BEARING means they take no
    deflection gap (`resolve/stacked_ladder.py` `takes_a_deflection_gap`), so the ladder line
    exists.
- **Fix options:**
  - (a) A **continuous 1¼" LSL rim strip on edge between trusses 256 and 272, on HS3/HS4's top
    plate under SN3** (y≈268.5–269.75" fits between chords 257¾/270¼"). Its vertical capacity
    is a **TJ-8000 published read**: the house already uses the 1¼" 1.3E rim's vertical row,
    5,400 plf in `band_header`, against 240 plf. It must go on TrimJoist's layout so the
    fabricator knows. An authored floor reinforcement would need the ladder resolver to accept
    it for an open-web deck (it lays nothing for trusses today).
  - (b) **A truss line directly over the wall** (`JoistSpec.extra_lines` at ≈268.5"),
    TrimJoist's call.
  - (c) If the trimmer really is hung (no load on SN3), set HS3/HS4 NONBEARING. They then stop
    ¾" under the deck, the ladder disappears, and the header rows for D-M-LAUN change.
  - Recommendation: (a). It is the cheapest and a published capacity. Fix the stale comment
    either way.

### 2.4 Trussed roofs: `truss_reactions` ×2, `uplift_capacity` ×2, `rafter_span` ×2

| ID | Sev | Finding | Route |
|---|---|---|---|
| P2-8 | GAP (engine limitation) | `uplift_capacity` says Table R802.11 "is indexed by a truss span and spacing" and the roof "resolves no truss member". The span and spacing **are known**: 23'-11⅛" out to out, 24" o.c., pitch (139.79 − 86.46)/143.6 ≈ **4.5:12**. | **2018 IRC Table R802.11** (up.codes): 24' span, 24" o.c., 115 mph, Exposure B, pitch < 5:12 gives **178 lb per connection**. R802.11.1 also lets ≤ 200 lb at ≤ 24" o.c. be toe-nailed per Table R602.3(1). The authored H2.5ASS (stainless) compares with the H2.5A's 615 lb SPF (`library/hardware/roof_ties.py`); **the H2.5ASS's own value is UNVERIFIED**. Edit: let the roof author its truss span/spacing (or a `PublishedCapacity` per joint) so `uplift_path` reads R802.11. **The garage closes this way.** The **canopy is an open structure**, and I did not confirm that Table R802.11 covers open buildings (**UNVERIFIED**). It already carries an engineered uplift through `wood_roof_post` (426.5 lb net), so keep the canopy on that. |
| P2-9 | GAP | `truss_reactions` ×2: no published reaction authored | Outside input: the stock truss's design drawing (R802.10.1) prints gravity and uplift reactions. Author them as the truss reaction once the order is placed. `roof_beam`'s chord bearing (0.877) uses an engine reaction of 2,492 lb, which the drawing should confirm. |
| P2-10 | — | `rafter_span` ×2 | Same as `rafter` in §1.1: a deferred submittal |

### 2.5 `structural.veneer_anchor` / `veneer_cavity_width`

See §1.1 and D5. The cavity check's margin to the 2021 W2.8 row is 6⅝ − 6½ = **⅛"**
(CLAUDE.md), so any shift in the strip face, the board, the beam or the stud line breaks the
alternate too. The R104.11 request should also carry H&B's 6½" tested data and the 2021
footnote conditions.

### 2.6 `code.MN_1309_0404_wall_top`: W-B-N2 at FO-M-STAIR

- **P2-11 (GAP, DECISION).** `FO-M-STAIR` (y 26'..35'-4⅞") fills W-B-N2's first three joist
  spaces for x 10'-3"..17'-6", so footnote f blocking cannot stand there. The wall top needs
  400 plf (Table R404.1(1), 8'/7'-6", 45 pcf; `main_floor_truss_basis.md` §4).
  - There is no prescriptive equivalent: footnote f's blocking spacing is ≤ 72" and the two
    opening headers are ~87" apart.
- **Options:**
  - (a) A one-page calc of the well's north trimmer/rim pack as a **horizontal beam** spanning
    between the two header ends (which then need A35Z/station ties as "trimmers ending on a tied
    sill"). The arithmetic is small: w = 400 plf, L ≈ 7.25', **M ≈ 2,630 lb-ft, R ≈ 1,450 lb**
    each end. A 2–3-ply LVL pack bending flatwise is the likely member. The LVL flatwise Fb is
    UNVERIFIED and must be read from TJ-9000.
  - (b) Move the well ≥ 3 joist spaces off the wall: a large redesign.
  - (c) A short steel angle/strut set. Also engineered.
- **Recommendation:** (a), put in the register as a small item, or added to `band_header`-style
  computed kinds. It is the least change.

---

## 3. Part 3 — reverse risk: PRESCRIPTIVE passes outside their table's conditions

| ID | Sev | What and where | Evidence | Confidence | Class |
|---|---|---|---|---|---|
| R1 | GAP (potentially unconservative) | **Wall bracing story count.** `checks/structural/bracing_eval.py:108-119` drops the attic because it has no braced line and cites IRC R325.6 ("shall not be considered a story"). **It never tests R325.6's conditions.** | I could not open R325.6 text (up.codes truncated). My recollection is that condition 1 limits the habitable attic's aggregate area to ≤ ⅓ of the story below (½ if sprinklered); **that is UNVERIFIED**. Here: the second floor is ~1,296 sf, so ⅓ ≈ 432 sf. The attic has studio + study + stub bath + hall; the "head-limited" area is 496 of 1,171 sf (CLAUDE.md). If the attic is a story, the main storey reads "first of three" in Table R602.10.3(1), and main E1 (14.75 vs 12.56 ft, 0.85) and S1 would probably fail. | Medium (rule text not read) | DECISION/GAP: read R325.6. Compute the attic's habitable aggregate area. If it is over the limit, re-run bracing at three stories or sprinkler. Engine: make `story_location` grade R325.6 instead of assuming it. |
| R2 | GAP (unconservative) | **FS-S-WEST J12 read** (`structural.ijoist_span` PASS: 17.92' ≤ 23'-2", "uniform load") covers truss y=272 while it carries ~240 plf extra from SN3 (§2.3). | `header_spans_r602_7.md` §4a–4b | High | See P2-7 |
| R3 | GAP | **W-SG-W1/E1 pass Table R404.1.2(8)'s 10' row** (CLAUDE.md "Sunken garden court"). That table has no surcharge column, and these walls carry the four fixed columns' base moments: factored M_u up to 4,612 lb-ft at the wall top (`column_support` R7). `column_support` grades only the joint (bearing, dowels, shear friction, development). `foundation.py:347` docstring: "The wall itself is prescriptive (IRC Table R404.1.2(8), no surcharge column)". **No check grades the stem's out-of-plane bending for that moment.** | The north part of W1/E1 is **#6 @ 38"** (CLAUDE.md). Rough φM_n ≈ 0.9 × 0.139 in²/ft × 60 ksi × ~8.9" ≈ 5.6 k-ft/ft. A 4.6 k-ft point moment spread over ~4–6 ft adds ~0.8–1.2 k-ft/ft to the soil moment at the top. Probably OK, but ungraded, and the column sits where the soil moment is near zero (braced top). | Medium | SMALL-FIX (compute): add the stem-flexure state under the column moment to `column_support`, or show the strip calc in `balcony_moment_columns.md`. |
| R4 | GAP | **Retaining base on stone.** `engineering/soil.aggregate_bed()` gives the retaining footings IBC Table 1806.2 **class 3** (3,000 psf, μ 0.35) because they bear on 42" of washed stone. The column bases and the SRW use class 4 (2,000 psf, μ 0.25; GM site). Nobody checks the **stone/GM interface below the bed**, for bearing (spread through 42") or for sliding of footing + stone on GM at μ 0.25. | Per-foot rough: N ≈ stem 1.37k + footing 1.05k + heel soil 3.0k ≈ 5.4 k/ft. Sliding on GM at 0.25 matches 0.35 on stone only if the stone carried with it weighs ≥ 0.4N ≈ 2.2 k/ft, i.e. a bed ≥ ~6' wide at 3.5' × 100 pcf. Bed widths are not read here. Bearing through 42" at 2:1 is ≈ 1.24 ksf against 2.0, OK. | Medium | SMALL-FIX (compute the second plane), or DECISION via the geotech that is already owed. Flag to the retaining reviewer. |
| R5 | REVIEWABILITY | **Cladding read.** BBD75-1212 is graded on the older p.13 row, 58 out / 43 in psf. The 07/2026 CTR republishes **42/75**, and the house records it as "not adopted". If the newer sheet's inward 42 governs, d/c moves 0.317 to ~0.325, still fine. | CLAUDE.md "Shell" | High that it passes either way | SMALL-FIX: cite both and grade on the lower inward (42). |
| R6 | GAP (minor) | **FS-M-NE OJ418S read**: the uniform-load table covers fields with doubled lines (316/332) under the peninsula, i.e. concentrated cabinet + quartz loads. A doubled truss under a point/line load is not a table row. Margin on span is 1" (17.92' vs 18.00'). | `main_floor_truss_basis.md` | Medium | DECISION: put the peninsula loads on TRIFORCE's order, as is already done for the J12 tile dead load. |
| R7 | — | **RF-HOUSE rafters**: TJ-4000 p.13 row 18'-4" ≥ 17'-11½". The high-end condition is now a bearing wall (R14W plate on W-A-C*), which p.13 asks for ("A support beam or wall at the high end is required. Ridge board applications do not provide adequate support"). | `roof_rafter_span_read.md` §2–3 | High | Verified; the 2026-09-18 finding is **closed** |
| R8 | — | **Headers**: R602.7 reads with note f's 0.70 for cripples, and Boise reads for the x=18' stack and D-M-LAUN (32' column + load comparison: an owner item, not a literal cell). | `header_spans_r602_7.md` §1–4 | Medium-high | Verified at read level. The 32'-for-36' substitution stays a disclosed DECISION. |
| R9 | — | **Foundation walls / wall-top restraint**: the 8'/7'-6" GM row at 400 plf, A35Z capacities with C_D 0.9, ×0.86/×0.90 species factors, and station spacing ≤ 72". Only W-B-N2 is open (P2-11). | `main_floor_truss_basis.md` §4 | High | Verified at read level |

I did not re-derive the footing widths (R403.1(1) 25") or the basement wall bar tables; only
their stated conditions were read.

---

## 4. The 2026-09-18 gap review, my area

| Finding | Status |
|---|---|
| 5: glulam dry-use row used for a wet beam | **Partly closed**: the row is now refused and an NDS record carries it. The prescriptive alternative (R507.5 SP 3-2x12, D3) is not taken. |
| 5: RF-HOUSE high-end support unconfirmed | **Closed** (R7) |
| 5: published-span helper ignoring `demand_psf` | **Closed** (`published.py` "a guard the caller passes nothing for is a mismatch") |
| 6: tiered SRW deferred | **Partly closed**: computed now (FS 1.54/2.02). **Open in a different sense:** it should not be a register item at all (§1.1). |
| 6: garage/canopy trusses and uplift chain | **Open.** Garage uplift closable by R802.11 (P2-8). Reactions wait on the truss drawing. |
| 6: house/garage/entry bracing UNKNOWNs | **Closed** (all lines PASS). New risk R1. |
| 6: veneer beam NO_CALC | **Closed**: veneer beam retired (bedded on stone). Veneer anchor remains, as an alternate. |
| 6: thermal-break transfers | **Computed** (0.676). Still engineered (D6). |
| 2: fixed-base columns lack foundation/connection design | **Mostly closed** (`column_base`, `column_support`, `base_rotation`, `column_head_joint` all computed). R3 is the residue. |

## 5. Verified correct (and how)

- Each kind's routing reason, read in the check source (the table in §1.1 quotes them).
- Repo R507.5 beam table = most-restrictive column; 3-2x12 at 18' = 6.83'
  (`deck_tables.py:97-110`), against up.codes SP 8'-10"/8'-9".
- Chloride, SCM and sulfate limits read from `concrete_materials.py`; the authorable fields
  exist on `ConcreteSpec` (`model/assembly.py:300-335`, `model/concrete_materials.py`).
- The sheathing-backing rule credits a floor member only within ⅛" (`sheet_layout_backing.py`).
  FS-S-WEST has no north edge rim (`second_deck.py:198`). The north run's stations map to x < 18'.
- The stacked-ladder resolver skips a lower wall that takes a deflection gap (nonbearing),
  `stacked_ladder.py:150-160`.
- R802.11 index and value (178 lb) from up.codes via the helper. Pitch computed from CLAUDE.md
  ridge/eave numbers.

## 6. Not verified

- R325.6 conditions (R1). DCA6 knee-brace threshold. The Allan Block chart page (summariser only).
- HETA lateral values. The H2.5ASS uplift value. Whether Table R802.11 applies to an open canopy.
- Any wet-use glulam table (none found; absence is not proof).
- C1778 structure class for a residence. LVL flatwise Fb for P2-11.
- Geometry behind P2-6. Bed widths for R4.
- No arithmetic of the register families was re-checked; other reviewers own that.
