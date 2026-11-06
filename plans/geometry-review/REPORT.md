# Geometry & dimensional-accuracy review — open items (round 2, 2026-11-05)

Current state of the review. Round 1 reviewed `247a13e9` (2026-10-31, 244 findings). Round 2
reviewed `539d9a81` (2026-11-04). It re-probed every round-1 id, found 246 new findings and
fixed the small ones. Fully resolved round-1 prose has been removed; the record is in
`findings/`, `adjudicated/C1..C7.md` (round 1) and `2026-11-04/` (round 2: kit, findings,
`adjudicated/C1..C5.md`).

- **Phase 1:** 27 Sonnet reviewers. S1 merged round 1's S1+S2. M1 split into M1 (ERV air side)
  + M4 (branches and fittings), M2 into M2 (supply) + M5 (DWV). Every reviewer reconciled
  its round-1 ids first. No re-brief was needed.
- **Phase 2:** 5 Opus adjudicators (C1–C3, then C4–C5) confirmed each prior status by their
  own probe, fixed the SMALL items under the round-1 rubric (`README.md`) and escalated the
  rest.
- **Phase 3:** coordinator integration, gate and this report.

**Gate result.**

| | baseline `539d9a81` | after round 2 |
|---|---|---|
| `haus check --only all` FAIL | 0 | **0** |
| UNKNOWN | 208 | **205** (3 court-wall `electrical.wall_device_opening` now PASS; no new UNKNOWN by check + element) |
| `haus print` (gated) | 83 / 176 sheets | 83 / **177** (+E-602.1), both printed through the gate |
| `scripts/verify.sh` | — | **green**: 10,553 passed, starter 358, catlin strict, ruff, UI typecheck and tests |

The first `verify.sh` run failed 3 tests: the two golden sets and the overlap ratchet. The
ratchet had caught a real regression. C4's TOTO supply stations put the Aquia IV stop 4 3/4"
AFF, into the 3 1/2" base (`baseboard|shutoff`, 100 cm³). It is now set at 7" AFF
(`fixture_types_wc.py`, `mep_supply_branches.py`). The goldens (`catlin_elevations.json`,
19 section scenes) were blessed after reading every diff, and the second run was green.

| | round-1 ids | closed | partial | open | obsolete / superseded |
|---|---|---|---|---|---|
| confirmed by adjudicator probe | 244 | 177 | 50 | 14 | 3 |

| new findings | wrong-build | drawing-error | model-only | doc | build-blocker |
|---|---|---|---|---|---|
| 246 | 57 | 68 | 53 | 68 | 0 |

| cluster | fixed | escalated (items) | rejected | handed off |
|---|---|---|---|---|
| C1 stairs & openings | 9 + 3 late | 11 + 1 late | 2 | 7 |
| C2 structure | 14 | 13 | 2 groups | 30 (21 to C5) |
| C3 envelope & interiors | 14 + 1 late | 13 | 8 | 22 |
| C4 MEP | 13 | 17 | 1 | 10 |
| C5 set & viewer | 18 rows (~30 ids) | 8 groups | 4 | 3 |

## 1. Open escalations

Ranked by construction-set impact, then build risk. "→" is the adjudicator's
recommendation. Evidence, options and blast radius are in the cited `2026-11-04/adjudicated/`
entry (`C2 E1` = C2.md, escalation E1). `carried` names the round-1 item.

### Structure, code minimums and wrong-build prints

1. **Centreline strip footings undersized** (C2 E1, F5-101) · new. FT-B-CS/CS2/CN/CN2 are
   20"×8". IRC 2018 Table R403.1(1) (read on up.codes), with footnote b scaled to the 36'
   depth, gives 29×9 (2-story + bsmt) or 32×11 (3-story + bsmt) at 1,500 psf. S-001 prints
   1,500 psf while the engine maps GM to 2,000. A hand bearing check from the house's own
   3,205 plf comes to about 2,023 psf. No check grades strip width.
   → Widen the four strips (and thicken them for P ≤ T) and add a typed R403.1(1) check. M.
2. **Duct system not specified** (C4 E1, the owner's concern, M1/M4 checklist) · carried
   (item 17) + new. The set prints no duct spec. The model and BOM have no round-duct gauge,
   no hangers (about 120 points), no named collar or balancing dampers, no tees, take-offs,
   reducers or boots (M4-102), no Broan port kit (6-to-8 transition + 12" flex, M1-103) and
   no duct schedule. 15 legs are too short for even a mitre pair (M4-101). 8 terminals sit on
   a different section with no boot (M4-103). The checklist table is in C4.md "Duct
   specification".
   → One `DuctStandard` (like Trim/Box/Drywall) that derives, bills and schedules the parts. L.
3. **ERV port wiring and the OA/EA/RET hold** (C4 E2 + E9, C3 I4-101, C2 E13) · carried
   (item 17).
   - DU-ERV-EA starts on Broan port 1 and RET-TRUNK on port 3: the two exhaust streams are
     cross-wired. Whoever releases the hold must not keep these starts.
   - The `DU-ERV-OA` riser stands in the FO-M-ERV-OA chase under D-M-MECH's doorway, where
     the floor is a ¾" fireblock sheet. That sheet cannot be walking deck as modelled.
   → One re-route of OA/EA/RET with a ledgered deck lid. M.
4. **Balcony fascia guard mounts** (C1 E9 + C2 E2, S3-101/103/106/108/110, F6-101/103,
   F3-108) · new.
   - The 5/16"×4" bolts cannot reach a block: fascia + rim + block is 3.75".
   - The rim is a non-stock 1.25×11.25.
   - The drip passes through every front bracket.
   - The posts are 49 7/8" where Ultralox stocks 48".
   - C2 fixed the metres-vs-feet blocking bug (F6-104).
   → One package: 2x12 KDAT rim, double blocks tight to the rim, and Ultralox's
   SD04964 5/16×6" screws (2025 guide p.37). M.
5. **DWV vent rules and the three unvented fixtures** (C4 E11–E13, M5-101..105/109) ·
   **closed 2026-11-05** but for one vent.
   - Every vent now leaves its drain at a tee within one arm diameter of the weir, rising at
     45 degrees or steeper; `mep.vent_connection` grades the four rules (ADVISORY).
   - BATH2's tub and the suite's lav and tub have 3D vents; the suite takes individual dry
     vents (a 908.2 wet vent had no legal lane). The two cleanout tees are separated.
   - The 3D walk is `mep.trap_arm_length` (CODE) since then, and the plan-`hypot` check is
     deleted; it counts a drop before the vent as an S-trap.
   - Open: `PR-M-BATH2-WC-VENT` offsets under the bowl's rim (framing; TODO).
6. **Exterior doors on the joist-top datum** (C1 E1, O3-103 = F1-102 = F3-107) · **closed
   2026-11-06** (owner: the standard way). All three ROs start on the subfloor (head +3/4",
   83 5/8" over the datum) and the skin under each sill stays cut to the datum, which also
   cleared D-S-BALCONY's three W-M-S2 coordination UNKNOWNs. ENTRY/PORCH seat the schematic
   sill 3/8" over the subfloor (the sloped pan's rise). Open residue: ENTRY's crest stands
   1.60" over the mudroom LVP against R311.3.1's 1.5" (TODO; not yet graded).
7. **Holes through floor framing** (C2 E3/E4, C4 E6/E7, F3-101..103) · **I-joists closed
   2026-11-06** (decision #117); ERV level 2 open on an owner call.
   - **TJI holes are graded:** ESR-1153 Table A's TJI 230 ladder (`plan/framing_charts.py`)
     grades every TJI crossing in `mep.run_member_crossing` and the router. The fix was a lane
     set, not one move: x=100.7" would have overlapped `PR-M-WC-VENT`'s hole. Suite vent
     108 -> 90, `PR-S-BATH1-VENT` squared onto x=40, and fn 1 spacing also moved the trunk,
     sauna and four basement cold lanes (`notes/framing_bore_limits.md` §11).
   - **FS-S-WEST is TrimJoist J12** (`PublishedWebOpenings`, a derived `OpenWebShape` per truss,
     `notes/open_web_truss_geometry.md`); ~19 runs moved into its pockets. Open: the 8" trunk fits
     no published opening, and the owner's R1-corridor re-route does not fit the north trusses'
     staggered chases (14.75" common). The trunk, five radials, D4, `PR-M-S-SUITE-WC-DRAIN`'s
     south leg and two interference pairs are suppressed as the open-campaign score pending the owner
     (`plans/TODO.md`).
8. **S-102 snow note** (C5 #3, F4-101) · new, prints wrong. `_snow_load_note` prints
   Pf 35 psf at Ct 1.0 for the unheated garage and canopy. The house basis and the truss order
   are 42 psf (Ct 1.2) plus drift.
   → Read Ct per roof. S.
9. **14" north-entry pier cage at 0.806%** (C2 E6, F5-106) · **fixed 2026-11-05**: (6) #5
   (1.21% of gross) on PT-BW-W/-GW/-PE/-PNE, dowels lapped beside the verticals
   (`ENTRY_PIER_CAGE_14`, `notes/north_entry_piers.md` §13b). The 12" rounds keep (4) #5.
10. **Header sizing** (C2 E5, F1-104) · **fixed 2026-11-06** (decision #116): headers are
    read off 2018 R602.7(1)/(2) at a load derived from the bearing refs (`structural.header_span`,
    `structural.wall_role_load`); nonbearing heads up to 8' are flat. 11 header UNKNOWNs left for triage
    (`plans/TODO.md`).
11. **Interior stair guards drawn off the joist-top datum** (C1 E2, S1-105, S3-102/104) · new
    + carried.
    - Four surface guards sit 1.5" below the finished oak, and the interior guard type has no
      mount spec.
    - Correcting the datum pushes RL-A-STAIR's east post 1.0" into the roof underside.
    - The bases need blocking (C2).
    → Datum, mount spec and blocking together; the roof clash is an owner call.

### Construction set (misprints and missing content)

Items 12–19 were closed on 2026-11-06 (commits 667dfdbe7, e64444332, 0dfba2680 and the
goldens commit). Gated `haus print`: 83 → **95** permit sheets. Only the residue is listed.

12. **Overprints** · closed (C5 #1). Detail dims, leaders, caption and K-bubbles go through one
    obstacle set (`annotation_layout_detail.py`), and captions dodge the linework. Floating
    CI/stud tags that repeat the ladder are gone, and an unbubbled K-note prints as a bullet.
    Across the A-5xx sheets, label/label overlaps went 16 → 0 and label/caption 11 → 0. Room
    labels dodge each other. Residue:
    - D1-109: MUD CLOSET, MECH/CHASE and BATH1/W4 still overprint at 3/32" (owner: a scale
      step or abbreviations).
    - I2-107: on A-401.6 the STUBATH label still crosses the WC.
    - D2-109 (`section_callouts`) and F1-106 (framing-plan labels) were not touched.
    - Found in review: E-101's northwest device-tag cluster overprints; on A-514 the K5
      leader crosses the K2 bubble; on A-531 the continuity tags overlap the detail head.
13. **Structural schedule rows** · closed (C5 #4). S-101.1 adds H4 (D-B-SUNKEN LVL) and
    sister/strongback rows. S-100 adds cast column/pier reinforcement. S-602.2 adds 76 I-joist
    bearing stiffeners; LSSR/LSTA24 were already on S-602. S-601 adds a Material column and
    the backing bands grouped by stock, material and use (128 bands, 426 LF). Residue:
    - the LSSR2.37Z part name is a `library/hardware/simpson_hangers.py` change;
    - the backing "use" classes are keyword reads of the purpose text (owner to confirm);
    - D1-110's note listing what the takeoff leaves out.
14. **Opening details per kind** · closed (C5 #2; O4-103, O5-103, O3-104). A key that holds
    windows and doors derives one detail per kind (`resolve/detail_keys.py`). D-M-ENTRY is
    A-531 (+.1/.2): it sits on the subfloor and has its own notes. The garage window section
    is A-532. A-533 onward are renumbered +2. Residue: K1/K3 point at a layer's face rather
    than the part. The A-531 head ladder lists the canopy roof layers above the door.
15. **Plan chains** · closed (D1-104/105/108). Bearing walls stay on every interior chain.
    The S-101.x LOCATING chains tie to the overall's faces. Veneer leaves the overall: S-101.1
    N-S went 36'-9 5/8" → 36'-0". Brick is a STRUCTURE layer, so the "no STRUCTURE layer"
    rule would not have dropped it. Residue: the west N-S chains have no tier names (needs a
    rotated-label reserve in the frame fit).
16. **MEP sheet content** · closed (C5 #6):
    - labels read system/material/insulation;
    - new P-401 (enlarged furnace-room plumbing) and P-601 (77 stub heights), both full set;
    - E-101/E-102 at 3/16";
    - ERV ports and wrapped-duct OD tagged; ducts print on the storey where they meet the ERV.

    Residue: P-101/P-102 wet-wall labels sit in side columns; E-102 has 10 of ~160 tags
    touching.
17. **Rim bands** · closed (F3-105, F3-112). `floor_band_at` counts a floor only where one of
    its members is cut. The garage and five bay cuts no longer print the house TJI. The porch
    sheets were right (FS-M TJIs bear there). Residue: the bay-cut rim conditions draw no
    floor at all (A-570 pairs a basement wall with an attic wall). Move the stations onto a
    joist line, or drop the conditions.
18. **C1 E8 drawing gaps** · closed:
    - A-605: stair and guard schedule, with headroom from the check's probes;
    - A-606: typical guard and handrail sections;
    - S-602: guard hardware;
    - A-601: Function, KD/flat jamb, RO sill above the storey datum, clear footnotes;
    - A-602: Product, Frame depth and Hinge (`Window.hinge`), plus a separate no-unit RO
      table; A-603 base by kind;
    - window/door marks and an RO height key on A-201..A-204;
    - A-520 draws a door;
    - the plant details reference their exterior head/sill sheets;
    - A-515 crest strings and a casing cut on cased doors;
    - O4-105: a 12 mm Corian Glacier White frame on WIN-S-PLANT1–4 (`WindowStool.return_*`),
      cut and billed with the countertops. O4-104 (1/4" rounding) was already fixed.

    Residue:
    - C1 E2: `RAILING-INT-STAIR-GUARD` has no fascia mount spec (6 posts print "NOT
      MODELLED"), and RL-BW-ENTRY / RL-A-FLIGHT-SKIRT have no type;
    - the surface-mount screw has no product row;
    - the plant membrane return is unbilled;
    - A-527 reads the B&B plant key's notes;
    - the KD 6 7/8" throat is not in the catalog.
19. **Smaller sheet items** · closed:
    - cover index wraps (no truncation, and the ledger permit index adds G-001.1);
    - G-004/G-005 headers; RO at 1/16";
    - S-103 notes in a wrapped panel; S-501.1 in 1/16" rounded down;
    - E-602.1 paged with whole cells (+E-602.2 on ledger);
    - A-501 cut at y=17'; RIDGE EL at the finished peak with T.O. RAFTER under it;
    - A-301 FIN. FLR tier; A-502/A-504 strings named; truss label without a depth;
    - a partition-to-roof transition (no eave caption; K2 scoped);
    - plain-language S-001.1 fastener basis;
    - A-607 casework and countertop schedule (full set); bath setout on A-401.x;
    - A-301.3 typical east wall section; A-503 retitled; A-508 prints the MDO screen notes;
    - HVAC equipment labelled by type.

    Residue:
    - A-301/A-204 level labels clip at the notes panel on ledger;
    - E1-107 ridge-cover/Z-closure callouts;
    - the MDO layer is not drawn on A-508, and its RO prints 2 3/4";
    - the portrait title block's county overprints CRS;
    - D2-112's rotated W1 text;
    - **the A-5xx block is full at A-599**, so the next derived detail would number A-600
      (owner call: renumber, or a second detail series).

### Fit and product data

20. **Exterior door head gaps and sill seats** (C1 E3, O3-101/102/004/008, S2-002) ·
    carried. D-M-PORCH and D-G-SERVICE have 0" head gap. The MMI sill crest is a supplier hold. S.
21. **Interior door RO height and undercut** (C1 E5, O1-101/102/107/108) · new. ROs are
    81.51" over the finished floor, against JELD-WEN's 82 7/16" and Masonite's 82". There is
    no undercut, and A-601 has no column for it. Leaves are modelled 45 mm, not 1 3/8". S–M.
22. **Hot-water header connections** (C4 E10, M2-101/102) · new. The trunk's last leg is
    perpendicular to the inlet socket. No bend supports within 6" of the outlets
    (Uponor submittal). S.
23. **BD8 backdraft damper on the ERV exhaust hood** (C4 E3, M1-102) · new. Broan forbids it
    (it freezes). Removing it reverses a recorded reason in `erv_static_budget.md` and gains
    about 8 Pa. Owner call. S.
24. **ERV static margin and airflow split** (C4 E4, M1-104/M4-112) · new. The 0.9 cfm R403.5
    margin uses a smooth-elbow coefficient for stamped elbows. Eight legs' duct and register
    cfm disagree. S–M.
25. **EQ-M-ERV-MAN-SUP has no feed** (C4 E5, M1-111) · carried (TODO). M.
26. **Kitchen fridge hinge** (C3 I1-101) · new, owner-visible. The fridge sits 5/16" off
    W-M-PAN-S, while the door at 90° needs 35.82".
    → Hinge at the pair seam (kit TTDRRVFRKIT). S.
27. **BATH2 shower backer** (C3 I2-105) · carried (TODO). Swan allows gwb-mr, but §6 asks for
    glass-mat under the membrane.
    → Glass-mat on the two closed walls, about 48 sf. S.
28. **Other interiors** (C3), each S unless noted:
    - Hall-bath insert nailers at 81–84.5" vs a 71–76.5" flange (I2-101).
    - TOTO tanks ¾" off the wall (I2-102).
    - The 1/2" "gwb-x" should be Firecode C (I4-103).
    - The sauna step abuts the shower pan (I3-108).
    - Tile mortar and SurePly allowances (I4-004/005, carried).
    - D-A-STUDY / D-A-POCKET onto unfinished subfloor (I4-107, carried).
    - The Murphy door datum is ¾" low, read off the subfloor (C1 late, I3-103).
    - The 4" rubber cove base needs a per-kind height (C1 E6, O2-101).
29. **Envelope** (C3):
    - The entry-screen wall end runs into the garage's corrugated layer (E2-101).
    - MDO panel 4 edge screws skip 11.2" (E2-104).
    - Partition/roof sheets titled "Eave" (E1-107).
30. **Other structure** (C2 E7–E12):
    - Backing bands vs runs and band overlaps.
    - The backing face test and the R602.6 edge offset.
    - Seat-beam ends 0.13" inside the CBSQ66 strap (F6-102).
    - CBSQ66-SDS2 → CBSTQ66Z-SDS2 part number.
    - Unsized derived IUS.
    - Smaller items.
31. **Other openings and stairs** (C1):
    - ST-M2S stringers and skirts bear on the floating LVP (E4).
    - Trim residue (E6).
    - Window stools through the buck jambs (E7, 34 pairs).
    - Handrail products (E10, bracket 7 is a custom 26.5" L).
    - Owner-scope opening items (E11).
32. **Other MEP** (C4 E8, E14–E17):
    - Runs through backing bands.
    - Supply open items.
    - Electrical: sconce footprint, 26 flush boxes on studs, DVFR1W.
    - `drain_tie_in` message.
    - `mep_registers.py` at 693 lines.

## 2. Fixes applied this round

Every fix carries a cited dimension and a before → after probe in its `adjudicated/` row.

| cluster | fix | effect |
|---|---|---|
| C1 | Pocket split studs seat on a cut neighbouring plate (`resolve/doorway_framing.py`) | 4 of 9 floating 1.5" → all seated |
| C1 | Porch stair pad outline matches SL-SG-STAIRPAD (`plan/site.py`); C2 the quantity | C-101 stair area +7 sf |
| C1 | MDF casing 11/16", pine base 23/32" descriptions; A-601 net clear to 1/16" | D-M-ENTRY reads Therma-Tru's 2'-9 5/16" |
| C1 | Sauna door head casing 2 1/2" (`plan/millwork.py`) | casing top 84.95" → 83.95", under the 84 1/16" ceiling |
| C1 | Stair notes at decision #112 rises; 81° service-door stop; stool height; window handing and supplier asks; 58114XX on B&B as accepted deviation | doc |
| C2 | Flank rollover blocking metres-vs-feet (`params/sunken_garden.py:2542`) | x=103: 6 → 3 blocks, x=329: 0 → 3 |
| C2 | Girts, straps and rims bought spliced like plates (`takeoff/framing.py`) | no stick over 20' on S-601 |
| C2 | `mep_bores.py` 507 → 439 lines (`mep_bore_verdict.py`, `mep_bore_flat.py`, re-exported) | — |
| C2 | A-502 cut onto a truss line (`plan/views.py`) | the truss bearing detail draws a truss |
| C2 | Four backing bands moved to their bodies' face | BK-M-HS1-HIGH, BK-M-C5-MID… |
| C2 | Diaphragm cites to SDPWS Table 4.2C; S-001.1 cast-in CBSQ66 note; stale deck/rim/ABU prose; catlin CLAUDE.md attic roof line | doc; ratios unchanged (about 1.8× conservative) |
| C3 | Wind clamps on seam stations; south trio re-hosted on RF-BW-CANOPY (`plan/wind_clamps.py`) | 7.56" off seam → on seam |
| C3 | Paint `_rooms_facing` drops a one-station sliver (`resolve/room_paint.py`) | W-A-STU-N studio face PT-3 → wall paint (only face changed) |
| C3 | RM-A-STUBATH ceiling gwb-mr | +34 sf gwb-mr |
| C3 | Peninsula/living end panels to the stone underside; study leaf cut 19 7/8" | gaps 13/16–15/16" → 0; 5/16" → 1/16" scribe |
| C3 | Leader straps bill once: 58110XX ×6 (`takeoff/anchors.py`, `takeoff/cladding_trim.py`) | SS316 #13 ×6 no longer billed |
| C3 | Roof-vent margin 873 vs 553 in²; K7 1 15/16" air; counter build-up stated once; Frigidaire 35.82"; LVP gap premise | doc |
| C4 | Supply-plenum trunk port on the trunk; EWC 4RSD attached to the plant register | port 7.7" → 0"; damper reaches the BOM |
| C4 | Code cites IRC M1601 → IMC 603.4 / Minn. R. 1346; vent termination (MN deletes P3103); sealing UL 181B-M / 181B-FX | doc |
| C4 | Per-type TOTO WC supply stations (`wet_ports.py`, `fixture_types_wc.py`); suite lav legs off the vent line | Aquia/Drake/Carlyle stations from SS-02072/02049/01809 |
| C4 | `electrical.wall_device_opening` finds foundation walls | 3 UNKNOWN → PASS |
| C4 | ED-A-STUBATH-CAN1 onto its ceiling; RACO 192 depth 1.563"; leader strap points on the leader centreline | 2.3" gap → 0 |
| C5 | A-301 levels and detail strings at 1/16" | MAIN T.O. PLATE 9'-0" → 9'-0 1/8"; A-505 7'-0 1/16" |
| C5 | `bearing_stations()`: BRG LINES at the structure centre (`structural_dimensions.py`) | garage 24'-0" → 23'-5 1/4" |
| C5 | S-603 one full-width table; E-602 split into E-602 + **E-602.1** (control schedule) | no clipped ids, no title-block overlap; **+1 sheet** |
| C5 | Elevation roof label names the top layer | A-203/204 "CDX-PLYWOOD" → standing seam |
| C5 | A-603 Walls lists paneling; A-402 draws rotated equipment; plumbing runs print on the storey they serve | P-103/P-104 now carry their supply |
| C5 | A-514 notes (20"×8" stone, 5,000 psi, Str. I ply); A-515 K7; B&B opening detail cut at a window | — |
| C5 | Viewer: seated I-joist rafters notched, thin solids at true thickness, rough-opening doorway parts drawn | `members.ts`, `structure.ts`, `openings.ts` |
| coord. | Aquia IV stop 7" AFF clears the base (above); catlin CLAUDE.md sauna headroom 42 1/16", living run 36 3/4" | ratchet back to 0 new pairs |

## 3. Closed since round 1

Each line points to the round-2 Reconciled tables (`2026-11-04/adjudicated/C*.md`).

- **Round-1 REPORT items 1–16 and 19–24** are closed in the model. Residues are listed in §1
  (items 2, 4 → §1.12; item 17 → §1.2/1.3; item 18 → §1.5).
- **S1/S2 (C1):** ST-S2A is 36.00" / 32.55" and `stair_head_landing` reads the posts. ST-G-SERVICE
  arrives at the +1.5" crest. S2-005 is closed (pad outline).
- **O1–O5 (C1):** window frame depths and returns, pocket kit RO (Eclisse sheet), trim stock,
  casing heads, K6 lap (1.000" on all 38). O1-001 and O5-005 were closed this pass.
- **F1–F6 (C2):** all 67 headers clear their plates. The stack closes. Birdsmouth (TJ-4000 p.28),
  canopy bearing 5.5", LUS26-2Z/LUS28Z seats and the shim packs are in. The garage sill is a
  2x8 at 74% on the core, with stone beds for frost. All Simpson seats fit (C-C-2026).
- **E1–E2 (C3):** seam register 16.0" on all roofs, rake counts, BBD75 band girt and lap.
- **I1–I4 (C3):** fridge 1" rear, stone 1 5/8", peninsula 40 5/8", Swanstone 96" + TK-105,
  sauna base at the benches and 84 1/16" ceiling, paint on every used face, LVP stacks.
- **M1–M5 (C4):** panel handles 78" AFF, sconce boxes, TV stand-off, 82 cans clear, the Uponor
  header body matches its submittal, pipe size labels, insulated bores. Every drain is at
  ≥ 1/4"/ft and the vent network is connected.
- **D1, D2, U1 (C5):** every A-101..A-104 chain closes, the A-601/602/603 rows match, the
  plant rim details derive, the paper-space pile-ups are gone, and the viewer draws the
  served opening parts.

## 4. Rejected (round 2)

14 new findings rejected.

| reason | count | ids |
|---|---|---|
| Within the published range or normal site tolerance | 4 | O2-105, E2-106, I1-103 (LG cutout 33 5/8–36), I2-106 (Swan 5 1/2") |
| The reviewer misread the code, the engine or a figure | 4 | M5-107 (MN 4714.0905 deletes the sentence), F3-103 "TRIFORCE governs", E1-109, F2-101 (3 bands) |
| A recorded owner choice or decision | 2 | E1-104, I3-107 |
| Not a defect: coordination, or matches the engine | 4 | O2-107, I3-106, I4-102, U1-105 |

Round-1 rejections re-raised without new evidence (D2-005, D2-010, U1-004) stay rejected.
Two round-1 rejections were overturned by new evidence: M2-008 and I2-009 (TOTO publishes the
inlet stations) and M3-009 (Carlon's BH235A catalog row).

## 5. Open handoffs

- **C1, from C5:**
  - U1-103 engine side: the GLB omits the D-B-GYM and O-S-VANITY doorway parts that the viewer
    now draws (emitter, deferred).
  - D1-106: WIN-B-SAUNA has no resolved seat, so A-602 prints "UNRESOLVED" and the viewer's
    one stool/frame overlap remains.
- **Owner:** the TODO corrections from C4 (BATH2 tub vent blockers, "12 types / 29 lights")
  are applied in `plans/TODO.md`. E2-105 is left for you: the "W-BW-SCREEN metal cassette
  engineering" TODO line tracks a design the MDO screen replaced.
- **Supplier holds** are unchanged except where listed in §1: MMI sill crest, DAKAM/Aliplast
  sill rail and sash lap, Metal Sales vented gable peak, Broan port spacing, the Murphy datum,
  and the fabricator truss hole chart.
