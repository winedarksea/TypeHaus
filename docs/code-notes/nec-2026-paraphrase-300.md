# Electrical rules the engine grades: Article 300, wiring methods (2026 NEC)

> Independent engineering notes for Type:Haus. Not published, endorsed or reviewed by the
> National Fire Protection Association. NFPA 70®, National Electrical Code® and NEC® are
> registered trademarks of NFPA, named here only to identify the code a rule comes from.
> This file contains no code text. Each entry is a summary in our own words, limited to
> what a check needs. It does not substitute for the code: read the edition your
> jurisdiction has adopted before relying on anything here.
>
> Summaries of rules the engine does not grade, and whole code tables, are kept out of
> the public repo; such an entry keeps its citation and Engine note, marked
> *(summary kept local)*.

Continues `nec-2026-paraphrase.md` (same conventions). Tests: `test_nec_printed_rules.py`.

The owner read 300.1, 300.4-300.9(A)(1), the tail of 300.21, and 300.22-300.25(B) with the
start of (C) on 2026-11-14. **Not yet read:** 300.2-300.3; 300.9(A)(2) through 300.21 (support,
boxes at splices, free conductor length at boxes, securing, raceway fill); 300.25(C) onward.
The Chapter 9 Notes to Tables and Tables 1, 2, 4, 5, 5A and 8 were read the same day (section below).

**Renumbered in 2026.** Old 300.4 (physical damage) is now **300.6**; old 300.5
(underground) is now **300.7**, with Table 300.7(A) (was Table 300.5); old 300.21
(firestopping) is now **300.23**; bends between pull points are the new **300.24**.
New 300.4 is Limitations and new 300.5 is Conductors (one circuit, one raceway). Citations
re-numbered in this change: `plans/TODO.md` "300.4 / 300.5" is now 300.6 / 300.7. The
per-raceway bend sections (342.24, 344.24, 352.24, 358.24, 362.24) stay beside 300.24; their
pages are unread, so they are not removed. `nec-2026-paraphrase-230-314.md` (225.27 refers
to 300.7(G)) and `-250.md` (300.7) already used the new numbers.

## Catlin findings

Grade is `Site.grade` -2'-10" (a design elevation, not a survey); the local grade beside the
house wall can read down to -3'-4" (nearest grade station). All runs are raceways, so none
is "direct burial". Checks are ADVISORY tier: shortfalls report as `Result.ADVISORY` with
numbers, never FAIL, and never a permit gate.

| Run | Depth found (top of run to top of cover) | Required | Table row, column | Verdict |
|---|---|---|---|---|
| `CD-B-GAP-EV` (now 1 1/4" Sch 80 PVC) and `CD-B-V2H-GAP`, at -5'-0" | 19.2 / 18.8 in. at the gravel strip; 26.2 / 25.8 in. under `SL-WK-C` | 18 in. | "all locations", Col. 3 | PASS (both) |
| both, last 1.5 ft under the garage slab | under a building, in a raceway | 0 | "under a building", Col. 3 | PASS |
| `CD-B-SPA` 1" EMT | inside concrete wall `W-SG-W1` (1/8 in. in from the court face), -4'-0" | n/a | cast into a retaining wall, not buried | UNKNOWN: reviewer's call whether the table reaches it |
| `CD-B-SPARE-CHASE` 2" EMT | indoors and in basement walls | n/a | not underground | not graded |

**Why the walk row is not used.** The "under a 4 in. concrete exterior slab" row (4 in. for
Columns 2 and 3) needs three things: slab at least 4 in. thick (`SL-WK-C` is 4 in.), no
vehicles (the model has no field; assumed for a sidewalk), and the slab extending 6 in. past
the run on each side. `SL-WK-C`'s west edge is at x=15'-7 1/2"; the EV run (x=16'-0") clears
it by 3.7 in. and the V2H run (x=16'-2 7/16") by 5.8 in. Both miss 6 in., so the row falls
to "all locations" and 18 in. Widening the slab 2-3 in. west (or sliding both runs east
3 in.) buys the row, and both would pass at 4 in. The EV run's circuit is 240 V, so Column 4
(120 V, 20 A, GFCI) does not apply.

**Other 2026 Article 300 hooks (UNKNOWN or exempt, never invented):**
- 300.7(B) / 310.10(C): wet insulation PASS (`CKT-EV-1450` is THHN/THWN-2); the spares carry no
  conductors (N/A).
- 300.7(D)(1) concerns direct-buried conductors; Catlin's are in raceways, so (D)(4) is what
  applies where a run rises through the garage floor. (D)(4)/352.10(K) PASS: `CD-B-GAP-EV` and
  the V2H legs are PVC Sch 80.
- 300.7(G) PASS: `CD-B-GAP-EV`, `CD-B-V2H-GAP` and `CD-B-SPA` are sealed at the house end with
  Polywater FST.
- 300.8(A)(3): `CD-B-SPA` (EMT cast in `W-SG-W1`) stays UNKNOWN under 300.7(A)(3)/burial (AHJ,
  owner question 4); Note 6 sends buried EMT to 358.10(B)(1) (read, `nec-2026-paraphrase-followup.md`).
- 300.9(A) PASS: the power raceways crossing house to garage or court (`CD-B-GAP-EV`,
  `CD-B-V2H-GAP`, `CD-B-SPA`) are sealed at the house end. Data conduits are outside Article 300
  (300.1(B)).
- 300.6(A)/(D)/(F): all 43 EMT and PVC raceways are excepted from the plate and setback
  rules; the four ENT floor-heat leads are not and their framing is unknown: UNKNOWN. NM
  cable is not drawn; its derived sleeves are 3/4 in. EMT (decision #93), exempt.
- 300.6(E): nearest approach to any roof plane is 15.7 in. (`CD-A-PV-EAST`): PASS.
- 300.23: no fire-resistance-rated assembly is modelled (the ESS closet is an owner
  standard, sealed per plan comments; the garage is detached). Not graded.
- 300.24: graded since before the renumbering (`mep.conduit_bend_total`); every finding
  now cites 300.24 first. Catlin holds 360 degrees between pulls everywhere.
- 300.25: no wiring in ducts is modelled; `mep.run_interference` would read a conduit drawn
  through a duct as a clash. Not graded.
- Chapter 9 fill (`mep.raceway_fill`, advisory; the section at the end): 31 runs graded. 12
  derived EMT sleeves: N/A (Note 2); conductor-free spares N/A. UNKNOWN: `CD-B-INV-BACKUP`,
  `CR-M-LAUNDRY-24V`, `CD-M-DATA-ENTRY` and the 4 floor-heat leads.

## Scope and limits

**300.1 Scope.** (A) Covers wiring methods and materials for installations of 1000 V ac or
1500 V dc nominal and under, except where Chapter 3 or another article modifies it. (B) Not
covered: Class 2/3/4, fibre, communications, antenna and broadband systems, power-limited fire
alarm; and conductors forming an integral part of equipment (motors, controllers, listed
utilisation equipment).
**Engine:** the 300.6(E), 300.7 and 300.9 checks skip Class 2 and data
raceways (`_power` in `checks/mep/conduit_burial.py`).

**300.4 Limitations.** *(summary kept local)*
**Engine:** not graded (a field condition).

## 300.5 Conductors

**(A)** *(summary kept local)*
**Engine:** not graded; the model draws trunks and `ConduitRun.service` is one service per run.

## 300.6 Protection against physical damage

Conductors, raceways and cables subject to damage are protected.

**(A)(1) Bored holes.** Cable or raceway through bored holes in joists, rafters or other wood
keeps the hole at least 1 1/4 in. from the member's edges; where it cannot, a steel plate or
bushing at least 1/16 in. thick covers the area. Ex. 1: no plate for rigid metal conduit, IMC,
rigid PVC, RTRC or EMT. Ex. 2: a listed, marked thinner plate with equal protection.
**(A)(2) Notches.** Where weakening is acceptable, cable or raceway may lie in notches, with a
1/16 in. plate installed before the finish; same two exceptions.
**(B)** NM cable through slots or holes in metal framing is protected by listed bushings or
grommets over all metal edges, fastened in place before the cable goes in; where nails or screws
may reach NM or electrical nonmetallic tubing, a steel sleeve, plate or clip at least 1/16 in.
(or a listed marked thinner one) protects it. **(C)** Cable or raceway behind access panels is
supported per its article. **(D) Parallel to framing or furring:** the nearest outside surface of
the cable or raceway is at least 1 1/4 in. from the nearest framing or furring edge where nails
or screws may penetrate; otherwise a steel plate, sleeve or equivalent of 1/16 in. Ex. 1: RMC,
IMC, rigid nonmetallic conduit, EMT. Ex. 2: concealed work in finished buildings or prefabricated
panels may be fished between access points. Ex. 3: the listed marked thinner plate.
**(E) Under roof decking:** keep at least 1 1/2 in. from the lowest surface of the decking; no
wiring in concealed locations of metal-corrugated sheet-deck roofs. Ex. 1: RMC and IMC with listed
steel or malleable-iron fittings and boxes. Ex. 2: no spacing where corrugated metal deck is covered by
2 in. of concrete. Ex. 3: concealed wiring encased in 2 in. of concrete (boxes per 314.29).
**(F) Shallow grooves:** under wallboard, siding, paneling or carpet finish, the cable or
raceway has a 1/16 in. plate or sleeve, or at least 1 1/4 in. of free space for the groove's whole
length; Ex. 1 and 2 as (A). **(G) Fittings:** where a raceway holds 4 AWG or larger insulated
conductors entering a cabinet, box, enclosure or raceway, they are protected by an identified
smooth-rounded insulating fitting, a listed metal fitting with rounded edges, insulating
separation held in place, or threaded hubs; an all-insulating bushing may not hold the
fitting or raceway; insulating material is rated at least the conductors' temperature.
**(H) Structural joints:** a listed expansion/deflection fitting or approved means where a
raceway crosses a joint made for expansion, contraction or deflection.
**Engine:** `mep.raceway_physical_damage` grades (A)(1)/(A)(2)/(D)/(F) by material (EMT and PVC
exempt, ENT UNKNOWN) and (E) by distance from each roof plane; (B), (C), (G) and (H) are not
graded (no cable or fitting data). `mep_bores.py` already grades stud and joist bores under IRC
R602.6 and R502.8, a different rule.

## 300.7 Underground installations

**(A) Minimum cover.** Direct-buried cable, conduit or other raceway meets Table 300.7(A)
(next section). **(B) Wet location.** The inside of an underground enclosure or raceway is a wet
location; insulated conductors in it meet 310.10(C). **(C) Under buildings.** Underground
cable and conductors under a building go in a raceway. Ex. 1: Type MI embedded in concrete,
fill or masonry, or suitably protected underground, per 332.10(6)/(10). Ex. 2: Type MC listed
for direct burial or concrete encasement per 330.10(A)(5) and (A)(11). **(D) Protection from
damage.** (1) Direct-buried conductors and cables emerging from grade (Columns 1 and 4 of the
table) are protected by an enclosure or raceway from the minimum cover depth to at least 8 ft
above finished grade, and never needed deeper than 18 in. below it. (2) Conductors entering a
building are protected to the point of entrance. (3) Direct-buried service conductors not encased
in concrete and buried 18 in. or more get a warning ribbon in the trench at least 12 in. above.
(4) Where an enclosure or raceway may be damaged, conductors go in EMT, RMC, IMC, RTRC-XW,
Schedule 80 PVC or equivalent. **(E) Splices and taps.** Direct-buried conductors may be
spliced without a splice box, made per 110.14(B). **(F) Backfill** with large rocks, paving,
cinders, sharp substances or corrosive material does not go where it could damage the run,
hinder compaction or promote corrosion; where needed, running boards, sleeves or granular
cover protect it. **(G) Raceway seals.** A raceway through which moisture might reach live
parts is sealed or plugged at one or both ends; **spare or unused raceways are sealed too**;
sealants are identified for the insulation and metals. **(H) Bushing.** A bushing or terminal
fitting with an integral bushed opening ends a raceway underground where direct-buried wiring
emerges; a seal that also protects like a bushing may replace it.
**Engine:** `mep.conduit_burial` (A), (C). `electrical.underground_raceway` grades (B) from
`Circuit.conductor_insulation` / `ConduitRun.cables`, (G) from `sealed_ends` + `sealant`, and
(D)(4) from `pvc_schedule`. Only buried EMT still reads (A)(3) UNKNOWN (`CD-B-SPA`). (D)(2)-(3),
(E), (F), (H) not graded (no direct-buried conductor, ribbon or backfill data).

**(I) Same circuit in a trench.** *(summary kept local)*
**Engine:** not graded (no trench grouping, loops or boring modelled).

### Table 300.7(A) (coded in `model/burial.py`; pinned in the tests)

**Table 300.7(A)** *(full table kept local; the values the engine uses are in its source)*

**Notes.** 1: cover is the shortest distance from the top of any buried conductor, cable or
raceway to the top of finished grade, concrete or similar cover (`burial.cover_in`). 2: a
raceway approved for burial only when concrete-encased needs a concrete envelope at least
2 in. thick. 3: lesser depths where cables or conductors rise for terminations, splices or
other access. 4: where a Column 1-3 method serves a Column 4 or 5 circuit, the shallowest
depth is permitted (`burial.shallowest_in`). 5: where solid rock prevents the depths, use a
metal raceway or a direct-burial nonmetallic raceway under 2 in. of concrete down to the
rock. 6: directly buried EMT meets 358.10.

## 300.8 Corrosion and deterioration

Raceways, trays, cablebus, gutters, cable armour, boxes, cable sheathing, cabinets,
enclosures, elbows, couplings, fittings, supports and hardware suit their environment; fences
and walls around equipment are not "enclosures" here. **(A) Ferrous metal** is protected inside
and outside by an approved corrosion-resistant coating; where protection is needed and threads
are cut away from the factory, they are coated with an approved conductive corrosion-resistant
compound. Stainless steel needs no coating. (1) Enamel alone: not outdoors or in 300.8(D) wet
places. (2) Organic coatings on boxes or cabinets: outdoors only where marked "Raintight",
"Rainproof" or "Outdoor Type". **(3) In concrete or direct contact with the earth** (or severe
corrosive influence): permitted where the material is approved for the condition or has
approved corrosion protection. **(B) Aluminium** embedded in concrete or in earth has
supplementary corrosion protection. **(C) Nonmetallic** equipment suits the condition: (1) in
sunlight, listed or identified sunlight resistant; (2) with chemical solvents, vapours,
splashing or immersion, resistant by listing or identified for the reagent. **(D) Indoor wet
locations** (dairy, laundries, canneries, frequently washed walls, absorbent surfaces): exposed
wiring system, boxes and fittings sit at least 1/4 in. off the wall or surface; nonmetallic
raceways, boxes and fittings may sit directly on concrete, masonry, tile or similar.
**Engine:** `electrical.underground_raceway` reads (A)(3) for EMT in earth or in a foundation wall
(UNKNOWN: protection not modelled); (A)(1)-(2), (B), (C), (D) not graded (no finish or
standoff data; no aluminium raceway is drawn).

## 300.9 Raceways exposed to different temperatures

**(A) Condensation.** Where parts of a raceway or sleeve see different temperatures and
condensation is a known problem (cold storage, or passing from a building's interior to its
exterior), it follows (A)(1) or (A)(2). **(1) Sealants:** seal the raceway or sleeve so warm air
cannot circulate to the colder section. (A)(2) onward is unread.
**Engine:** `mep.raceway_condensation` passes a run sealed at an end inside a building. It is
ADVISORY when sealed only outdoors and UNKNOWN when unsealed. Catlin's three runs PASS.

## 300.21 (tail), 300.22, 300.23, 300.24, 300.25

**300.21 tail (vertical support, unread above it).** *(summary kept local)*
**Engine:** not graded.

**300.22 Induced currents in ferrous enclosures.** *(summary kept local)*
**Engine:** not graded (conductors are not drawn singly; all Catlin trunks are one raceway per
circuit group).

**300.23 Spread of fire or products of combustion** *(summary kept local)*
**Engine:** not graded: no rated assembly is modelled (see Catlin findings).

**300.24 Bends.** The total of all bends in any combination of conduit or tubing for one run
does not exceed 360 degrees between pull points.
**Engine:** `mep.conduit_bend_total`
(`resolve/conduit_pulls.py` measures; `NEC.RACEWAY_BENDS`, with the per-raceway 342.24, 344.24,
352.24, 358.24, 362.24 beside it; the check cites 300.24 first).

**300.25 Wiring in ducts not used for air handling, ducts fabricated for environmental air, and
plenums.** *(summary kept local)*
**Engine:** not graded: the model draws no
wiring inside a duct; the ERV runs are ducts and `mep.run_interference` flags overlap.

## Chapter 9 Tables: conduit fill, bend radius, conductor dimensions

The owner read the Notes to Tables, Tables 1, 2, 4, 5, 5A and 8 on 2026-11-14. Data lives in
`model/raceway_fill.py` (Tables 1 and 2, Notes), `model/raceway_areas.py` (Table 4) and
`model/conductor_areas.py` (Table 5); each cell is pinned by self-consistency in
`tests/test_nec_ch9_fill.py` (the 60/53/31/40% cells against the 100% cell, the 100% cell
against the internal diameter, a Table 5 area against its diameter) plus spot cells.

**Notes to Tables, in our words.**
- (1) Annex C lists the maximum same-size conductor count per trade size (unread).
- (2) Table 1 is for a complete conduit or tubing system; it is not meant for a section that
  only shields exposed wiring from damage.
**Engine:** the derived NM sleeves are N/A.
- (3) The equipment grounding or bonding conductor, insulated or bare, counts in fill at its
  actual dimensions. **Engine:** one insulated EGC per circuit at its Table 250.122 size.
- (4) A nipple of 24 in. or less (connectors excluded) between boxes, cabinets or similar
  enclosures may fill to 60% and needs no 310.15(C)(1) adjustment. **Engine:**
  `fill_percent_for(nipple_length_in=...)`; no nipple is modelled.
- (5) A conductor Chapter 9 does not list (multiconductor or optical-fibre cable) uses its
  actual dimensions. (6) Mixed sizes use actual dimensions or Tables 5/5A, with Table 4 for
  the raceway. (8) Bare conductors take Table 8.
- (7) Where the count of same-size conductors comes out with a decimal of 0.8 or more, round
  up (the same for the size of conduit for a single conductor). `permitted_count`.
- (9) A multiconductor cable, optical-fibre cable or flexible cord of two or more conductors
  counts as ONE conductor, a circle on the major diameter if the section is elliptical (NM).
  An assembly of single conductors with no overall covering is not a cable: count each.
  `cable_area_in2`.
- (10) Table 5 values are worst-case round concentric-lay-stranded; compact stranding is
  Table 5A; a known actual diameter and area may be used instead.
- Informational Note 1: Table 1 assumes proper cabling and alignment and a pull with a
  reasonable length and few bends; a larger raceway may be wise. Note 2: with three
  conductors, jamming can occur where raceway ID over conductor OD is 2.8 to 3.2 (low
  probability with four or more).

**Table 1.** One conductor 53%, two 31%, over two 40% of the cross-section.

**Table 2, radius of bends (in.), one-shot and full-shoe / other bends.** 1/2: 4 / 4;
3/4: 4 1/2 / 5; 1: 5 3/4 / 6; 1 1/4: 7 1/4 / 8; 1 1/2: 8 1/4 / 10; 2: 9 1/2 / 12;
2 1/2: 10 1/2 / 15; 3: 13 / 18; 3 1/2: 15 / 21; 4: 16 / 24; 5: 24 / 30; 6: 30 / 36.
**Engine:** recorded (`min_bend_radius_in`), not graded: field bends carry no radius in the
model (`resolve/mep_fittings.py` `RACEWAY_BEND_GAP`), and the derived sleeves are straight.

**Table 4, 40% area (in.2) at 1/2, 3/4, 1, 1 1/4, 1 1/2, 2** for the materials Catlin uses
(all rows and the 60/53/31/100% cells are in the module): EMT 0.122, 0.213, 0.346, 0.598,
0.814, 1.342; ENT 0.114, 0.203, 0.333, 0.581, 0.794, 1.316; PVC Schedule 80 0.087, 0.164,
0.275, 0.495, 0.684, 1.150; PVC Schedule 40 and HDPE equal ENT through 2 in. FMC, IMC, RMC
are coded too. **Read, not coded** (Catlin has none): LFMC, LFNC-A/-B/-C, PVC Type A and
Type EB. ENT has no row above 2 in. Note the model's ENT outside diameter
(`resolve/pipe_sections.py`, IPS series) pairs with Table 4's 0.602 in. ID at 1/2 in. as a
0.12 in. wall; the print gives no ENT OD to confirm it.

**Table 5** (areas and diameters, in.2 and in.) is coded for THHN/THWN/THWN-2 (e.g. #12
0.0133 and 0.130, #4/0 0.3237), XHHW/XHHW-2/XHH (#12 0.0181) and TW/THW/THHW/THW-2 (#12
0.0181). Other families (RH*, SF, TF, XF, fluoropolymer, Z, KF) are read, not coded. A
footnote: the RHH/RHW/RHW-2 rows marked * are without outer covering.
**Table 5A** (compact copper and aluminium: bare, RHH*, THW/THHW, THHN and XHHW diameter
and area, 8 AWG to 1000 kcmil; dimensions "from industry sources") and **Table 8** (area,
stranding, overall diameter and area, dc resistance at 75 degC for uncoated copper, coated
copper and aluminium; R2 = R1[1 + alpha(T2 - 75)], alpha_Cu 0.00323, alpha_Al 0.00330;
IACS 100% and 61%; compact conductors are smaller than the table, see 5A; Class B stranding
is also listed as solid at some sizes) are read, not coded: nothing in the engine sizes a
conductor by area or computes voltage drop.

**Engine:** `mep.raceway_fill` (ADVISORY): fill grades `ConduitRun.cables` at datasheet OD
(Notes 5 and 9) or Table 5. PVC grades at the authored schedule. 31 runs are graded. Still
UNKNOWN: `CD-B-INV-BACKUP`, `CR-M-LAUNDRY-24V`, `CD-M-DATA-ENTRY` and the 4 floor-heat leads.
N/A only for protection sleeves and conductor-free spares. No derating (310.15(C)(1)) is
applied.

## Open questions for the owner

1. Is `SL-WK-C` vehicle-free (no pickup parked on the entry walk)? That plus 6 in. of slab edge
   buys the 4 in. row for the EV and V2H runs, which are at 14.2 and 13.8 in. otherwise short
   of 18.
2. (Closed: the runs are buried to -5'-0", so the 18 in. row is met.)
3. (Closed: the conductor type is authored (THHN/THWN-2) and the V2H pipe is Sch 80; buried-EMT
   corrosion protection is question 4.)
4. Is a retaining-wall-embedded EMT (`CD-B-SPA`) acceptable to the inspector, or should it
   go in a PVC sleeve across the wall?
5. Fill: do you want conductor sizes authored on the 11 unnamed power runs (feeders, PV,
   riser) so `mep.raceway_fill` can grade them? And is the model's ENT outside diameter right
   (IPS 0.840 at 1/2 in. against a 0.602 in. ID)? Say which ENT product Catlin buys.
