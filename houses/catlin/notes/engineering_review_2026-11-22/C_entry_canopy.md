# Review C — north entry canopy, landing structure, girt screw

Reviewer: C (entry canopy). Report-only. No `haus`, pytest or verify runs. Hand checks are in
`out/review/scratch/C_entry_canopy/{embed.py,hand.py}` (plain Python, no typehaus import).
One secondary source was fetched: an ASD transcription of IBC 2018 Tables 2306.2(3)/(4)
(SDPWS diaphragm rows ÷ 2.0), published by the City of Santa Clarita. It is cited where used.

Sheets read: `houses/catlin/out/calcs/calcs/{column_base,deck_post,deck_tie,lateral_system,roof_beam,wood_roof_post,girt_screw,rafter}.md`,
the BW/W-A-N1 appendix files, `04-assumptions.md` and `03-open-items.md`. Also read: the oracle notes
`canopy_garage_diaphragm.md`, `canopy_west_band.md`, `north_entry_canopy_lateral.md` and `north_entry_piers.md`
(§§3, 4a, 7, 9), `preferences.toml [structural]`, `plan/storeys/garage.py` (DiaphragmSpec),
`params/north_entry_frame.py`, `library/hardware/ties.py`, `typehaus/wind.py`, `checks/structural/deck.py`
(the pad weight) and `engineering/soil.py`.

---

## Findings, most significant first

### C-1 · GAP (high) · Below the chord bases, the W-BW-SCREEN shear path is not closed, and the pier it implies cannot carry the load
- **Where:** `calcs/lateral_system.md` §4 row "W-BW-SCREEN chord base shear, one base" (1,034.6 lb into one
  CBSTQ66Z-SDS2 base, 0.815) and row "chord hold-down, full height" (2,230.5 lb, 0.729). Compare
  `appendix/deck_post__PT-BW-GW.md` / `__PT-BW-W.md` §6: "no wind or seismic moment in the shaft … k 1.0 on the
  LEANING-COLUMN assumption". No `column_base/` item exists for PT-BW-W or PT-BW-GW. `deck_tie` assumption #3:
  "The wood path from each load to the tied member is assumed to deliver it".
- **The problem:** the lateral record sends the screen's whole in-plane shear and its overturning tension into the
  cast-in base on the PT-BW-W/GW pier tops. No record grades those piers for either force.
  - **Lateral.** If the pier has to deliver 1,034.6 lb ASD to the soil as a non-constrained pole, the load
    acts 17.8" above grade (pier top −16.19" against grade −34"). IBC 1807.3.2.1 then needs 7.16 ft of embedment
    at S1 = 150 psf/ft on the 14" round, or 5.24 ft with §1806.3.4's doubling. PT-BW-GW has 4.50 ft from grade
    to the bottom of its pad, so d/c = 1.59 (1.16 doubled). PT-BW-W has about 7.1 ft, so d/c ≈ 1.0. Run in `embed.py`.
  - **Pull-out.** No record grades the tension chord's pier for uplift.
    - PT-BW-GW at 0.6D: shaft 799 lb + 2'×2'×1' pad 600 + soil prism over the pad 1,128 (110 pcf)
      + wall 157 + post 60 gives 1,647 lb of resistance.
    - Against the record's own overturning tension of 1,804 lb, d/c = 1.10.
    - If the overturning is taken only to the landing sill (arm 7.41 ft), the tension is 1,540 lb and d/c = 0.93.
    - PT-BW-W is deeper and passes at 0.79. Run in `hand.py`.
  - **The landing path.** `deck_tie` grades the second path (screen → landing → HL33 → W-G-W, 0.761 N-S). The
    links from the screen's bottom plate or chord into the landing framing are assumed, not graded. Those links
    are the bottom-plate nailing to BM-BW-SCSILL, and the chord to the seat-beam LUS26-2Z.
- **Confidence:** high that it is ungraded. Medium on the pull-out numbers: soil weight, the prism versus a frustum,
  and how much landing dead load hangs on the chord all move it ±15%.
- **Class:** DECISION, with a small fix inside it.
  1. *(Recommended, cheap)* Make the landing the declared lateral support of the chord base:
     - Grade the screen bottom-plate-to-sill fastening, 190 plf over 5.44 ft. 16d at 6" into the 2x8 KDAT
       sill, or a row of SDWS, is ample.
     - Grade a chord-to-landing tie at each chord foot, e.g. an A35Z pair or an LTP4 per chord to the sill/rim.
       They must be rated for the N-S 1,034.6 lb.
     - Mark the pier tops as laterally propped. That makes IBC 1807.3 inapplicable to W/GW, and the CBSTQ
       base-shear row stays as the anchorage check.
  2. For uplift, grade pier pull-out explicitly (a new `column_base` uplift row for W/GW). The cheapest fixes:
     - Go to a 2'-6" square, 1'-0" pad under PT-BW-GW: +338 lb concrete and +~520 lb soil prism, d/c ≈ 0.75.
     - Or credit the frustum.
     - Or credit the dead load of the landing that hangs on the chord.
  3. Alternative: drop the "one base takes all" envelope and split the shear by the landing's stiffness. That is
     more analysis and less certain, so it is not recommended.

### C-2 · ERROR-unconservative (moderate) · The N-S chord force sent to the truss fabricator uses the deck depth, not the distance between the named chords
- **Where:** `north_entry_canopy_lateral.md` §8b line 35: `1,034.49 x 24.0 / (8 x 6.0) = 517.2 lb`. The
  DiaphragmSpec `chords=` text (`plan/storeys/garage.py:639`) names "the end trusses' 2x4 top chords". The
  `03-open-items.md` A row tells the fabricator to carry `chord_force_*`.
- **Evidence:** the canopy's three trusses sit at y = 37.333 / 39.333 / 41.333 (`canopy_garage_diaphragm.md`
  §3b), so the two end trusses are **4.0 ft apart**, not 6.0.
  - The screen-at-100% envelope is in equilibrium only as a simple span. The span runs from the screen to the
    east end strap (±517 lb couple across the joint), about 23.23 ft.
  - That span gives T = 1,034.6 × 23.23 / (8 × 4.0) = **751 lb**, 45% above the 517 lb on the order.
  - Naming the garage gable truss (`truss-000`, y 43.281) as the north chord instead gives d = 5.95 ft and 505 lb.
    The deck is continuous and nailed 8d at 6" into it, which is plausible.
  - Either reading must be stated, and the truss order must carry the chosen chord and force. Under the second
    reading, the garage gable truss carries it, not a canopy truss.
- **Related GAP:** the ±517 lb end-strap couple is not graded in the N-S case, although the same envelope needs it
  for equilibrium. The sheet grades only 172.4 + 88.0 at the end straps.
  - Hand check: 517/823 = 0.63 at CN-BW-JOINT-1/-7, or 0.73 if the E-W chord force is added linearly.
  - RF-GARAGE then carries a ±12,000 lb-ft torque. That is ~500 lb more into W-G-E and W-G-W, or about 27 plf on
    surplus walls carried at 182.5 plf. It passes.
- **Confidence:** high on geometry and statics.
- **Class:** SMALL-FIX.
  - In `lateral_system`/`lateral_collectors` chord-force arithmetic, take W as the authored chord spacing, not the
    deck dimension, or name `truss-000` as the north chord.
  - Add an "N-S joint couple at end straps" row of V·L/(2·L_strap) to the strap and receiving-wall rows.
  - Update §8b, the DiaphragmSpec `chords` text and the truss-order line.
  - Effect: the chord force goes 517 → ~751 lb (fabricator item). The end straps go 0.316 → ~0.73. No graded
    ratio exceeds 0.8.

### C-3 · ERROR-conservative · `lateral_system` at 0.91 is an artefact of an arbitrary halving of the diaphragm capacity
- **Where:** `plan/storeys/garage.py:630-631`: `unit_shear_asd_plf=190.0`, "a deliberate round-down for this
  19/32in deck". Repeated in `canopy_garage_diaphragm.md` §3a and `roof_sheathing_and_membranes.md:37-40`.
- **Evidence:** the engine's own source string reads SDPWS Table 4.2A blocked, Structural I, 8d at 6/6, 2" framing,
  as 755 nominal × 0.92 / 2.0 = **347 plf**.
  - The independent ASD transcription (IBC 2018 Table 2306.2(4), Santa Clarita) gives wind ASD **372 plf** for
    Structural I 8d 3/8" min (and for 15/32" sheathing 8d) at 6/6 with 2" framing. With fn. b SG 0.42 that is
    0.92 × 372 = **342 plf**.
  - Nothing in the source justifies 190. A thicker panel at the same schedule is not weaker, and the author's own
    comment says so.
  - Demand is 1,034.6 / 6.0 = 172.4 plf, so d/c = **0.50**, not 0.908.
  - The same halving sits on RF-GARAGE: carried at 167.5 against 335 × 0.92 = 308 (Table 2306.2(3) unblocked,
    Case 1, Structural I 8d: 335 ASD wind).
- **On the rest of the question:**
  - The rigid/flexible call does not affect any graded ratio in the built `kdat` variant: both paths are graded
    at 100% (C-8).
  - The capacity row (blocked, Case 1, SPF fn. 2 factor, 2" nominal framing) is right for the authored schedule
    of 8d at 6" boundary and edges with bevelled 2x4 blocking at every edge. All edges are nailed at 6", so the
    Case does not change the column.
  - Chords: see C-2. Collectors: LTP4Z 172.4/450 verified.
  - Overturning at the screen: see C-1.
- **Cheapest real margin, if wanted beyond the corrected 0.50:**
  - 8d at 4" on the boundary in the west bay (the row along BM-BW-RW and its collector blocks), 6" elsewhere.
    That is the 4/6 column, 420 × 0.92 = 386 plf, d/c 0.45. Cost: ~15 extra nails.
  - No new blocking is needed; it is already in.
- **Confidence:** high. The row values come from a secondary transcription. A reviewer should open the primary
  AWC table once and cite its page.
- **Class:** SMALL-FIX.
  - `garage.py` canopy DiaphragmSpec: `unit_shear_asd_plf=190.0` → `342.0`, and rewrite `source=` as
    "…372 plf ASD (744 nominal) × 0.92 SPF = 342 plf".
  - Garage: `167.5` → `308.0`.
  - Effect: lateral_system governs at the band KBS1Z 0.748 or the base shear 0.815, not 0.908. The
    joint-boundary rows drop roughly by half.

### C-4 · ERROR-conservative · `roof_beam` 0.877 overstates truss bearing (uniform-load inflation and C_b = 1.0)
- **Where:** `calcs/roof_beam.md` R6, "truss reaction 2,492 lb (1245.8 plf x 24" o.c.) … C_b 1.0".
- **Evidence:**
  - 1,245.8 plf = 83.7 × 80 sf / 5.375 ft. The deck's 6.0 ft depth is put onto the 5.375 ft bearing run, a
    ×1.116 inflation for a mid-run truss.
  - Per truss, with the drift triangle placed (`hand.py`), the half-span is 13.333 ft:
    - T1 (y 37.333) = 1,463 lb, or 177 psi.
    - T2 = 2,353 lb, or 285 psi.
    - T3 = 2,052 lb, or 249 psi.
  - NDS §3.10.4 gives C_b = (1.5 + 0.375)/1.5 = 1.25 for T2 and T3 (more than 3" from the beam end). T1 sits
    0.75" from the end, so C_b = 1.0 there.
  - Governing: T2, 285 / (344.5 × 1.25) = **0.66**. T1: 177/344.5 = 0.51. The current 0.877 bounds both.
  - Bending (358/2,208, 0.16), shear, post bearing (112/344.5) and deflection reproduce exactly.
  - The truss's own chord bearing (SPF or SYP chord Fc-perp) is the fabricator's. List it in the criteria (C-9).
  - Wet service on a header directly under the roof edge is defensible, but it is inconsistent with C-10's dry
    reading at the deck tie a few feet below.
- **Confidence:** high.
- **Class:** SMALL-FIX in `engineering/truss_on_beam.py`:
  - Take the reaction as `load × half-span × truss tributary width`, not `uniform_load × spacing`.
  - Apply C_b per NDS §3.10.4 where the truss is ≥ 3" from the member end.
  - Effect: 0.877 → ~0.66 (T2), still governing the family.

### C-5 · ERROR-unconservative (small) · The equal post share ignores the N-S drift gradient on the house-side posts, piers and pads
- **Where:** `wood_roof_post` (40 sf × 83.7), `deck_post` PT-BW-PE/W (roof_tributary 40, snow 73.7), and the pad check.
- **Evidence:**
  - The surcharge runs from 47.1 psf at the canopy's south edge to 16.3 psf at its north edge (prefs comment).
  - On each 6-ft header the south support takes L(2p_s + p_n)/6 = 110.5 psf-ft of surcharge, against 95.1 for the
    uniform average.
  - That is **+205 lb (≈ +6%)** on PT-BW-RE, PT-BW-CW, piers PE/W and pads PD-BW-RE/W. North posts are 205 lb lighter.
  - No verdict moves. Post axial goes 0.213 → 0.226, and pad PD-BW-W's D+S gross is 1,546 psf.
- **Confidence:** high.
- **Class:** SMALL-FIX. In `pier_basis.landed_roof_tributaries`, carry the authored balanced and surcharge pair
  (`roof_beam_balanced_snow_psf`, `roof_beam_drift_surcharge_psf`, `roof_beam_drift_width_ft`, all already in
  preferences) and split each header by statics, not by halves. Or state the 6% on the sheets as a known bounded
  approximation.

### C-6 · GAP (minor) · The pad bearing check is gravity-only and uses a deck table for roof piers
- **Where:** `structural.deck_footing_size` (`checks/structural/deck.py`, R507.3.1 currency (10+S)/50).
  `column_base` lists `allowable_bearing` 2,000 psf but grades no bearing row.
- **Evidence, worst pad PD-BW-W (2'-6"×1'-6"×1'-0"), under the screen's compression chord:**
  - D + S + L, with the C-5 gradient: 5,798 lb → **1,546 psf gross / 1,436 net**.
  - D + 0.75(S+L) + 0.75(0.6W), with the 1,804 lb overturning compression: 6,312 lb → **1,683 gross / 1,573 net**.
  - Against 2,000 psf (GM presumptive, IRC Table R401.4.1 / IBC Table 1806.2 class 4) that is 0.79–0.84. It passes.
  - The earlier review's "1,525 psf vs 1,500" is resolved by net bearing at 2,000 psf.
  - The shaft is still charged at full concrete weight with no displaced-soil credit, which is conservative.
- **Prescriptive route (goal 1):** a roof-borne pier is not a deck post. A direct P/A against IRC Table R401.4.1,
  with the wind combination, is simpler and plainly prescriptive.
- **Class:** SMALL-FIX. Add a bearing row to `column_base` (and to the W/GW item C-1 creates) using the ASD
  combinations, including the chord overturning reaction. Expected d/c ≤ 0.84.

### C-7 · ERROR-unconservative (small) and GOAL-1 route · girt_screw demand omits girt continuity, and h is measured from the floor datum
- **Where:** `calcs/girt_screw.md` §4: `tributary_area 5.333`, `mean_roof_height 25.64`. `wind.mean_roof_height_ft`
  reads `roof.eave_z_m` and `ridge_z_m`, which are relative to the main-floor datum, not grade.
- **Evidence (`hand.py`):**
  1. **Continuity.** The 2x4 girt is continuous over blocks at 32", and the panel is continuous over girts at 24".
     An interior screw on a 2-span girt reacts 1.25 wL, and ~1.1 more for panel continuity. Demand goes 97.5 →
     121.8 lb (pull-through 0.61), or →134 lb (0.67).
  2. **Height.** Grade is 2'-10" below datum, so h = 28.5 ft, Kh 0.690 against 0.670: +3%. The canopy calc measures
     h from the lowest ground (the sunken garden, −9.12 ft). On that basis h = 34.8 ft and the demand is +9%.
     The two calcs use two different h rules.
  - **Worst case: 134 × 1.09 ≈ 146 lb against 200, d/c ≈ 0.73.** It passes.
- **Verified:**
  - Zone 5 GCp −1.4 (≤ 10 sf) and GCpi 0.18 give q(1.58) = 30.5 psf strength and 18.27 psf ASD.
  - Tributary 32"×24" = 5.33 sf.
  - Thread bookkeeping: 8 − 2 = 6" shank against a 6" stack, 1.5" into the stud.
  - The 6D minimum penetration.
  - The ESR-1078 table values themselves (170 lb/in at SG 0.42, 200 lb pull-through at a 1-1/2" member, SG 0.55)
    are NOT verified. I did not open ESR-1078.
- **Conservative item:** C_D is taken as 1.0 on the ESR values. Most ICC-ES screw reports state their allowables
  are for normal load duration and may be adjusted per the NDS. If ESR-1078 says so, both capacities rise ×1.6.
  UNVERIFIED; read §4.1 of the report.
- **LSL studs (assumption #6):** closable without the PE. Use NDS 12.2.1 lag-screw withdrawal with the LSL's
  published equivalent SG for withdrawal, from its own evaluation report (LP SolidStart LSL, ESR-2403 — value not
  read here). Or confirm ESR-1078 lists SCL. Either way the 0.382 withdrawal row has room.
- **Goal 1, the prescriptive route.** This item is structurally identical to `structural.cladding_wind`: an
  ASCE 7 C&C demand against a manufacturer's published allowable.
  - The withdrawal and pull-through values are an ICC-ES table read, which the repo already treats as prescriptive
    for connectors (`PublishedCapacity` in `model/refs.py`, used by `checks/structural/published.py`).
  - Proposal: author a `PublishedCapacity` (or a `PublishedFastening` sibling of `Material.published_cladding`) on
    the girt band's `FramingSpec.standoff_fastener_*`. Its fields:
    - source: ESR-1078 (2026-01), Tables 1A/2/3
    - rows: withdrawal 170 lb/in at G 0.42; pull-through 200 lb at a 1-1/2" side member, G 0.55
    - conditions: thread 2", length 8", coating per §4.1.7, C_D basis, service dry
  - Grade it in a `structural.girt_fastening` check. The drift guards are: block module ≤ 32", course ≤ 24",
    stack = shank, stud species/SG, and wind basis ≤ the read. That retires `girt_screw/W-A-N1` from the register
    the way `wall_panel/W-A-N1` was retired.
  - IRC R703.15.2 / Table R703.15.1 (cladding over foam, furring fastening) is NOT a fit. That table assumes
    furring bearing on rigid foam and is indexed by cladding weight; this wall bears on wood blocks and is
    governed by suction. Not recommended (UNVERIFIED that the 2018 table's limits exclude it).
- **Class:** SMALL-FIX for the demand. In `girt_screw_withdrawal.crossing_demand_lb`, apply 1.25 (2-span girt) ×
  1.1 (panel), or justify tributary. Measure h from the house's grade (`Site.grade` or spot elevations), not the
  datum, in `wind.mean_roof_height_ft`; this also changes `cladding_wind`. Expected 0.487 → ~0.67–0.73.
  DECISION for the published-read conversion. Recommended: it is the item's cheapest exit from the register.

### C-8 · REVIEWABILITY / simplification · The 0.03" splice slip and the rigid/flexible call are not load-bearing for the built canopy
- **Where:** `03-open-items.md` A (both truss rows), DiaphragmSpec `chord_splice_slip=inch(0.03)`, and
  `north_entry_canopy_lateral.md` §8b.
- **Evidence:** in the `kdat` variant the east posts are pinned. The only N-S lines are W-BW-SCREEN and the garage
  joint, and **both are graded at 100% of V** (assumption #10, "no relief is credited to either path"). The split
  never enters a ratio. The slip mattered only for the `cast` variant.
- **Class:** SMALL-FIX.
  - Drop the slip from the fabricator's must-confirm list, or mark it "cast variant only".
  - State on `lateral_system` that the rigid/flexible split is not used under the double envelope.
  - One fewer open input for the PE and the fabricator.

### C-9 · GAP · The deferred trusses: what the house can decide now (task item 7)
The package prints no truss design-criteria schedule. `rafter.md` and its appendix carry one sentence about drift.
The cover's DEFERRED SUBMITTALS block (`emit/draw/schedules/cover.py:64`) is generic. Per its docstring,
`engineering/snow_drift.py` puts the drift reach on S-001/S-102; I did not verify the sheets.

The schedule below can be decided now. Recommendation: a `TrussCriteria` block on each Roof (or a printed table off
`preferences.toml` and the model), on S-001 and in `rafter.md` §3.

| Item | Canopy (RF-BW-CANOPY, 3 trusses) | Garage (RF-GARAGE) |
|---|---|---|
| Geometry | 4:12 common, 23'-11 1/8" out to out, 24" o.c., standard heel 3.939", overhang 1'-7 3/16" both ends | same truss, 24" o.c. |
| TCDL | 10 psf (authored) | 10 psf |
| BCDL | 0 (open) | ceiling, R-38 + 5/8" gyp, ~7-10 psf (to author) |
| Snow, balanced | p_g 50, Ce 1.0, Ct 1.2, Is 1.0, Cs 1.0 → p_f 42 psf | same |
| Unbalanced | ASCE 7-16 §7.6.1, W ≤ 20 ft: leeward Is·p_g = 50 psf, windward 0 (confirm in the standard) | same |
| Drift | Leeward roof-step from the house: h_d 2.45 ft, γ 20.5 pcf, p_d 50.3 psf at the house wall face, linear to 0 at w = 9.8 ft from it, on balanced. Covers all three canopy trusses (T1 ≈ 88.5 psf total snow, T2 78.2, T3 68.0) | truss-000 (gable, also carries the joint bay's half, ~82 plf) and truss-001 |
| Sliding / rain-on-snow | N/A: no higher roof slopes onto either; p_g > 20 psf | same |
| Wind | V 115, Exp B, RC II, K_d 0.85; open canopy (ASCE 7 Ch. 27/30 open-building) | enclosed |
| Bearings | Full 5-1/2" glulam (BM-BW-RW/RE), heel at the outside face of bearing; Fc-perp of the glulam 650 × 0.53 wet | 2x6 SPF plates |
| Uplift / ties | H2.5ASS each heel with SSA8D: **specify max net uplift reaction 450 lb/heel** (hand: 289 lb at 0.6W − 0.6D, below) | H2.5A / per schedule |
| Diaphragm chord | End-truss top chords, N-S chord force **751 lb** (C-2) or name truss-000 at 505 lb; plated peak splice to carry it in tension | truss-000 if so named |
| Deflection | IRC Table R301.7: L/240 snow (no ceiling), L/180 TL | L/240 with ceiling |
| Splice slip | not required (C-8) | — |

**Grading the uplift chain now.**
- `structural.truss_reactions` waits for `Roof.published_reactions`. With the engine's own surrogate (16.832 psf
  uplift on plan, 0.6D = 6 psf):
  - T2: 26.7 sf × 10.83 = **289 lb** net per heel.
  - T1: 161 lb.
- Against H2.5ASS 700 lb with SSA8D (or 440 smooth) that is 0.41 (0.66).
- `north_entry_piers.md` §4a is **stale**. It divides by "4 truss stations" per header; there are three. Corrected:
  427 → 569 lb gross per heel and 0.6W 256 → 341 lb, still under 700.
- Recommended: add a `Roof.specified_reactions` (the design criteria the fabricator must not exceed). Grade the
  chain below the heel against it now. Then `truss_reactions` compares the fabricator's published row ≤ specified
  when it arrives. That closes `structural.uplift_capacity` and `truss_reactions` today on a stated, conservative
  number. Only the component design itself stays deferred, which is normal.
- **Class:** DECISION (schema) plus SMALL-FIX (fix §4a's station count).

### C-10 · REVIEWABILITY · The deck_tie sheet: orientation, the service judgement, and confusing labels
- **Orientation.** The HL33HDG is graded "heel vertical", reading the published *uplift* (740 lb) for horizontal
  forces both ways (`calcs/deck_tie.md` R2). The catalog values are tested in the catalog's installation; rotated
  90°, the bolts bear at a different angle to grain in each member. The interaction arithmetic is right: 1,127/1,480
  = 0.761, and 579.7/1,480 + 290.2/740 = 0.784. The catalog row matches `library/hardware/ties.py` (C-C-2024 p. 303:
  740/1,040 at C_D 1.6, fn 6 doubling of uplift for two). The open question is the reading, not the arithmetic.
  Confirm with the catalog figure, or orient the angles as drawn.
- **Service condition.** deck_tie takes C_M 1.0, dry, "under RF-BW-CANOPY". roof_beam and wood_roof_post take the
  members a few feet higher and more sheltered as wet. Pick one judgement for the canopy zone and state it once.
- **Labels.** In the E-W case the larger component is labelled "along the wall" at a tie on W-G-W (a N-S wall),
  while the E-W face wind acts across that wall. Either the label or the direction mapping is wrong. Re-check
  `deck_tie.py`'s axis naming. I did not trace the code.
- **IRC R507.9.2** cannot replace this calc. It is the ledger-deck lateral connection ("where provided"). This
  landing is freestanding, and the governing load is the screen's canopy share plus face wind, not deck lateral.
- **Goal 1:** the HL ties are a manufacturer published-capacity read against an ASCE 7 demand, the same pattern as
  C-7. The item can leave the register as a `PublishedCapacity` check once the orientation is confirmed.
- **Class:** DECISION (orientation) / SMALL-FIX (labels, one service judgement).

### C-11 · DECISION · column_base (PE/PNE) is verified; these are not structural flagpoles, and the item can leave the register
- **Verified independently (`embed.py`):**
  - P = 81.9 lb ASD (post half-drag 23.6 + pier drag 58.3) at h = 1.932 ft above grade.
  - IBC 1807.3.2.1 with S1 = 150 psf/ft × d/3 (Table 1806.2 class 4) needs 2.26 ft (PNE, b_eff 1.451) and 2.39 ft
    (PE, b_eff 1.268) against 4.50 / 7.12 ft. Matches 0.50 / 0.34.
  - Shaft-only b = 14" needs 2.47 ft, so crediting the pad as part of the pole changes nothing.
  - The §1806.3.4 doubling is correctly not claimed.
  - Frost: PNE pad bottom at 54" below grade against 42" (Minn. R. 1303.1600, per `north_entry_piers.md` §7). PE at 85".
- **Flagpole?** No. They carry only their own wind drag (82 lb). The canopy's lateral system does not use them;
  the east posts are pinned. The exposed part is 3.0 ft on a 14" round, h/d = 2.57 ≤ 3. Above grade that is an ACI
  pedestal, below grade a soil-embedded pier (ACI §14.1.2). `deck_post` calls them COLUMNS only because it counts
  the buried 6.1 ft in h/d (assumption text: "every pier graded in this module stands free above grade for part of
  its own").
  - Recommendation: classify by the exposed height, as an ACI pedestal on a soil-embedded pier.
  - The embedment row is then a plain IBC 1807.3.2.1 code equation (82 lb), a code read like any deck footing.
  - Optionally stand the 6x6 post on a lower pier top to shrink it further.
  - No braced or house-tied alternative is needed. Tying to the house would cross the movement joint the design
    keeps at the house end.
- **Open, ungraded (`north_entry_piers.md` §7):** adfreeze jacking and negative skin friction. Close it with a
  drawn polyethylene bond-breaker or slip sleeve over the top 42" of all six shafts. That is a detail, not a calc.
- **Class:** DECISION (reclassify, add the sleeve note).

### C-12 · REVIEWABILITY · roof_beam / wood_roof_post prescriptive routes
- **roof_beam.** IRC R602.7(1)/(2) cannot be read: those tables are for wall headers, tabulated only to 70 psf
  ground snow, and the canopy's governing load is a 73.7 psf design roof snow with drift. The glulam maker's
  allowable-load table (Rosboro X-Beam, treated) can be read as a `PublishedSpan` with `demand_plf` for bending,
  shear and deflection at 4.98 ft. The governing state, truss bearing on the beam (C-4), is not in a span table;
  it stays an NDS §3.10 row. Net: no gain. Keep it engineered and fix C-4.
- **wood_roof_post.** The east pair (RE/RNE) are axial-only, pinned 6x6s with ESR-2604 / ESR-3050 connectors. IRC
  Table R507.4's 6x6 height plus published connector reads (ACE6Z uplift 632→426.5 lb against 1,950, CBSTQ) would
  make them prescriptive, if the house accepts R507.4 for a roof post. The tributary is equivalent to a 67 sf deck
  share; check R507.4's footnotes. The west chords carry the band push (873 lb-ft) and stay engineered.
- **Arithmetic verified:**
  - Fc' = 525 × 1.15 × 0.877 = 529.5 psi; ×30.25 = 16,016 lb.
  - le/d 16.78, FcE 1,284 (E_min 440 k).
  - fb 873.2 × 12 / 27.73 = 377.9 psi.
  - Head uplift 426.5 + 1,034.6 × 0.990/4.979 = 632.2.
  - Axial 3,409 ≈ 40 × 83.7 + post weight.

---

## Load-path reconciliation (task item 1): the earlier review's finding #1

| Link | Snow used | Self-weight | Status |
|---|---|---|---|
| Trusses | none (deferred) | — | Criteria not printed (C-9) |
| BM-BW-RE/RW | 73.7 + 10 D over 80 sf, uniform ×1.116 | glulam | Consistent, conservative (C-4) |
| Posts (wood_roof_post) | 73.7 over 40 sf | post | Consistent; south posts +6% unaccounted (C-5) |
| Piers (deck_post) | 73.7 over 40 sf (`roof_snow` 73.7, L 2,948) | shaft included: PE D 1,907.8 = 400 + 45.4 + 1,462 (14"×9.12 ft×150) — reproduced | Consistent |
| Pads (deck_footing_size) | (10 + 73.7)/50 equivalence | pad + shaft, net of the pad's displaced soil | Consistent for gravity; wind and overturning compression missing (C-6) |
| W/GW piers under the screen chords | gravity consistent | — | Lateral and uplift from the screen ungraded (C-1) |

**Earlier review #1** (`engineering_gap_review_2026-09-18.md`):
- **Closed:** posts, piers and pads now share one snow schedule (73.7 psf) and carry self-weight. The pad allowable
  question is resolved by net bearing.
- **Remaining:**
  - the drift gradient (C-5)
  - the uniform-versus-discrete truss reactions (C-4; conservative)
  - wind and overturning combinations at the pads (C-6)

**Worst pad by hand:** PD-BW-W at D + 0.75(S+L) + 0.75(0.6W) is 1,683 psf gross / 1,573 net against 2,000.
D + S + L is 1,546 gross.

**Snow inputs checked:**
- γ = 20.5, p_f = 42 (Ct 1.2, Ce 1.0), h_d = 2.452 ft, p_d = 50.26 psf, w = 9.81 ft. Reproduced.
- Sliding (§7.9): N/A. The house and garage roofs slope E/W, not onto the canopy.
- Unbalanced (§7.6.1) is not on any sheet. It does not govern the headers (60 psf < 83.7) but belongs in the truss
  criteria (C-9).
- Ce: a reviewer may argue "sheltered" (1.2 → p_f 50.4) for a roof tucked between a 21 ft gable and the garage.
  The drift already models the obstruction, and partially exposed is the usual reading, so no change is recommended.

**Earlier review #2 (fixed bases):**
- Partly closed: `column_base` exists for PE/PNE, `deck_post` searches combinations (closes #4), and dowel hooks
  are graded.
- Open: W/GW (C-1), and the `deck_post` dowel row's ψ-factor "CONFIRM" note.
  - On that note: with six #5 on a ~10" cage, centre spacing is ~4.6" ≥ 6d_b, so ψr = 1.0 holds without
    enclosing ties (ACI 318-19 Table 25.4.3.2, from memory — UNVERIFIED).
  - The note can be resolved on the drawing.

## 04-assumptions.md items that still hand something to the PE, and how to close each

| Kind | # | Item | Close by |
|---|---|---|---|
| column_base | 2 | §1806.3.4 doubling "a judgement about the structure" | Moot. The verdict does not use it; delete the PE wording. |
| column_base | 3 | Base-moment split shaft/pad, rotational stiffness, group effect | Calculation. With 82 lb, a bound shows sway negligible (`base_rotation` exists for the SG piers; add PE/PNE, or state δ from IBC's 1/2" at the allowable). Group effect: piers > 3 diameters apart, N/A earned. |
| column_base | 4, 7 | Presumed soil (GM) | Outside input only: a geotechnical report. Or adopt the most conservative IRC R401.4.1 row (1,500 psf, 100 psf/ft lateral class 5) and show it still passes. PNE embedment at S1 100: ~2.6 ft < 4.5. That removes the "presumed" dependency without a soils report. |
| column_base | 6 | Pad not graded as the mechanism | Moot once the pad is credited only as embedment (already). Delete. |
| deck_tie | 1 | Dry service "the engineer of record confirms" | Decision: one canopy-zone service judgement (C-10). Or grade at C_M 0.7: 1,127/(1,480×0.7) = 1.09 N-S **fails**, so the dry reading is load-bearing. Either upsize to HL35/HL43 (1,310/1,445 F1; uplift 740/1,275) or document dry. |
| deck_tie | 2 | Concrete under anchors and tie-block screws "named with a hand bound" | Calculation: put the hand bound on the sheet as rows (NDS screw lateral; it is small). |
| deck_tie | 3 | Wood path assumed | Calculation (C-1): grade the sill/chord-to-landing link. |
| girt_screw | 3 | C_D 1.0, C_M 1.0 "if a reviewer disagrees" | Published read: quote ESR-1078 §4.1 on load duration and service. At C_M 0.7, withdrawal is 0.55 and still passes. |
| girt_screw | 4 | NOT CHECKED: girt bending between blocks, block compression/bearing, sheathing nailing | Calculation, all trivial. 2x4 flat SP, 32" span at 18.3 psf × 2 ft: M = 0.125×36.5×2.67² = 32 lb-ft, fb ≈ 130 psi. Block bearing is gravity only. Add three rows. |
| girt_screw | 6 | LSL "for the PE to confirm or replace" | Published read: the LSL report's equivalent SG plus NDS 12.2.1 (C-7). |
| lateral_system | 4 | Differential settlement 3/16" tolerance, presumed soil | Calculation: settlement bound on presumptive bearing (1,683 psf on 2.5×1.5 pads). Or a detail: the slotted H2.5ASS / LSTA tolerance stated. Outside input otherwise (geotech). |
| lateral_system | 5 | "What stays with the truss designer is the N-S chord … and the 0.03in splice slip" | C-2 (put the corrected chord force on the order) and C-8 (drop the slip). |
| lateral_system | 7 | "SCREENING, not a stamped design" | Boilerplate. Goal 2 is met when C-1 and C-2 are closed. |
| lateral_system | 8 | Drift limit N/A (SDC A) | Earned; fine. |
| wood_roof_post | 1 | Dry service at connectors, "verify MC before the parts go on" | Specification item (KDAT to ≤ 19% MC, a moisture meter on the inspection checklist). Not a PE item. |
| roof_beam | 1 | Substitute must match 24F-V4 | Specification. Fine. |
| rafter (open items A) | — | Fabricator owns component design, drift, chords, slip, reactions | C-9: print the criteria; grade the chain on specified reactions now; drop the slip. |

## Verified correct (the check done)

- **Canopy wind (`canopy_garage_diaphragm.md` §2):**
  - K_z at 20.764 ft Exp B = 0.6307, q_h 18.149.
  - p = 0.6 × q × 0.85 × 1.80 = 16.661 psf.
  - N-S gable triangle 2.222 × 26.667 = 59.26 sf, V = 987.3 + 2 × 23.585 = 1,034.5 lb.
  - E-W 670.8 lb.
  - Conservative: h measured from the sunken garden, and the house shields the south gable.
- **SDPWS 4.2.5.2 open front:** 6/25 and 0.225. Arithmetic right, for the joint-supported reading.
- **LSTA24 at 12/18 nails:** 823.3. Nailer NDS yield Z = 74.96 lb (mode IIIs) reproduced from the printed terms.
- **Screen panel:**
  - 1,034.6/5.4375 = 190.3 plf, aspect 0.75.
  - The 490 plf capacity rests on the repo's 980 nominal reading of SDPWS Table 4.3A (`canopy_west_band.md` §4a).
    I could not check it against the primary.
  - The garage-wall rows quote the same table at 670 nominal for 6", yet are carried at 182.5 (365 nominal).
    The repo's own readings of that table are inconsistent. A reviewer should open Table 4.3A once.
  - Either way the screen passes. At half the read, d/c ≈ 0.78.
- **Band KBS1Z:**
  - P = V/2/cos θ = 742.8 lb.
  - The 993 lb interpolation between 1,010 @ 45° and 720 @ 30°/60° is in the SPF column.
  - KDAT SP would take the DF/SP 1,175 (0.63). Conservative.
- **Hold-down:** 1,034.6 × 8.6825/4.979 + 426.5 = 2,230.5 (0.729 against 3,060 cracked).
- **Roof beam:** bending, shear, post bearing and deflection, as listed in C-4.
- **deck_post PE:**
  - Load combinations listed: 0.9D + 1.0W governs at 0.03.
  - Hook l_dh = 60,000 × 0.933 /(55 × 70.7) × 0.625^1.5 = 7.11 in, against 8.375.
- **Truss reactions on the header are bounded by the engine's 2,492 lb** (T2 2,353 with drift).

## Not verified

- Primary SDPWS-2015 tables. I used the IBC ASD transcription for 4.2A/4.2C rows, and nothing primary for 4.3A.
- ESR-1078 (TimberLOK) values and its C_D clause.
- ESR-2604 (ACE6Z), ESR-3050 (CBSTQ), ER-280 (KBS1Z) and ESR-2105 (LSTA24) table values. Only their internal
  arithmetic was checked.
- The HL catalog figure orientation.
- Whether S-001/S-102 print the drift reach.
- `deck_tie.py`'s axis labels.
- Adfreeze magnitudes.
- Frost depth beyond the repo note.
- I did not read `wood_roof_post_joints.py`, `post_bearing.py`, `spread_base.py`, `spread_footing.py` or the
  `lateral_band*` code line by line. The findings rest on the sheets, the oracle notes and the authored plan.

Source used: City of Santa Clarita reproduction of IBC 2018 Tables 2306.2(3)/(4)
(https://santaclarita.gov/home/showpublisheddocument/13250/637108086676400000), fetched 2026-11-22.
