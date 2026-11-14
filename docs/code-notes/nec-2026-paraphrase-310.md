# Electrical rules the engine grades: Article 310, conductors (2026 NEC)

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

The owner read 310.1-310.6, 310.10, 310.12, 310.14 and all of 310.15, with the 310.16-310.21
conditions, and Tables 310.16 and 310.17, on 2026-11-14. Table 310.16 is transcribed in
`model/ampacity.py` (copper 16 AWG-600 kcmil, aluminum 14 AWG-600 kcmil); 310.17 is not coded.

**310.1-310.6 General.** **310.5(A)** **310.6** *(summary kept local)*
- **Engine:** not graded. Table 310.4(1) matters here only for the types the take-off names:
  THHN (counted, not typed) and NM-B (334).

**310.10 Uses.** (A)-(B) Dry and damp locations take the listed types (THHN, THW, THWN, XHHW,
RHW and so on). **(C) Wet locations** take moisture-impervious metal-sheathed cable, MTW, RHW,
RHW-2, TW, THW, THW-2, THHW, THWN, THWN-2, XHHW, XHHW-2, XHWN, XHWN-2 or ZW, or a type listed
for wet use; plain THHN is not on that list, so conductors in an underground or outdoor
raceway are the THWN/THWN-2 dual-rated kind. **(D) Sunlight:** conductors exposed to it are
listed sunlight-resistant, covered with listed sunlight-resistant tape or sleeving, or are
bare or otherwise not needing it. **(E)** Direct burial uses a type identified for it.
(F) Corrosive exposure calls for a suitable type.
- **(G) Parallel conductors.** Allowed in 1/0 AWG and larger (Ex. 1: smaller than 1/0 for
  control power to indicating or relay devices, or 360 Hz and up, inside one raceway or cable,
  each able to carry the whole load and protected so a lost leg can't overload the others;
  Ex. 2: 2 and 1 AWG neutrals in existing installations under engineering supervision).
  Each set is the same length, material, circular-mil area and insulation, and is terminated
  the same way, in cables or raceways with the same number of conductors and electrical
  characteristics. Ampacity corrections follow 310.15(B)/(C). Parallel EGCs follow 250.122
  (sectioned ones under 1/0 allowed in multiconductor cables) and parallel bonding jumpers
  250.102.
- **Engine:** graded for underground runs via `Circuit.conductor_insulation` (`CKT-EV-1450` is
  THHN/THWN-2, PASS). The PV runs (sunlight) fall under (C)/(D)/(E) and are not graded.

**310.12 Single-phase dwelling services and feeders.** Applies to one-family dwellings and
each unit of a two- or multifamily dwelling on a 120/240 V single-phase system (and 208Y/120
two-phase-plus-neutral feeders). Where 310.15(B)/(C) factors are needed they are applied to
the ampacity at the conductor's own temperature rating.
- **(A) Services.** Service conductors carrying the entire load of the dwelling, on a service
  rated 100-400 A, may have an ampacity of at least 83% of the service rating. With no
  correction or adjustment factors, Table 310.12(A) may be used for conductors rated 75 degC
  or more. **(B) Feeders.** The same 83% and table, only for feeders carrying the entire load
  of the dwelling or of an individual dwelling unit. **(C)** A feeder to an individual dwelling
  unit never needs more ampacity than (A) or (B) gives. **(D)** The grounded conductor may be
  smaller than the ungrounded one if 120.61 and 230.42 (services) or 215.4 and 120.61
  (feeders) are met.
- **Table 310.12(A), checked cell by cell against the printed table 2026-11-14** (service or
  feeder rating, A: copper / aluminum or copper-clad aluminum conductor, AWG or kcmil):

  | Rating | Cu | Al | Rating | Cu | Al |
  |---|---|---|---|---|---|
  | 100 | 4 | 2 | 225 | 3/0 | 250 |
  | 110 | 3 | 1 | 250 | 4/0 | 300 |
  | 125 | 2 | 1/0 | 300 | 250 | 350 |
  | 150 | 1 | 2/0 | 350 | 350 | 500 |
  | 175 | 1/0 | 3/0 | 400 | 400 | 600 |
  | 200 | 2/0 | 4/0 | | | |

- **A rating between rows** has no row of its own, but the rule is a percentage: the
  conductor needs an ampacity of at least 83% of the service rating. Table 310.12(A) is that
  rule read at the 75 degC column of Table 310.16, and agrees with it at every printed row (a
  test pins this: the table's conductor is the smallest whose 75 degC ampacity is at least 83%
  of the rating). A rating between rows takes the 83% figure directly, with no correction
  factors. `dwelling_service_conductor()` does it.
- **Catlin's arrangement.** One Class 320 combination meter-main outdoors holds two 200 A mains
  (a 320 A continuous socket; there is no 225 A or 400 A class). Each main feeds a basement
  panel (`ED-B-PANEL`, `ED-B-PANEL-2`) through a short 4/0 Al SER feeder, priced as an
  allowance and not modelled as an element. The service-entrance conductors are the utility
  lateral and the enclosure's busing; their size is not authored.
  - **(A), service conductors.** 83% of 320 A is 265.6 A: **300 kcmil Cu (285 A) or 400 kcmil
    Al (270 A)** at 75 degC. If the 400 A the mains add up to (230.80) were the rating, 332 A:
    400 Cu (335 A) or 600 Al (340 A).
  - **(B) does not apply to the feeders**: each carries only part of the load (estimated 136 A
    and 121 A). They are sized by Table 310.16: 4/0 Al is 180 A at 75 degC (205 A at 90 degC).
    Equipment over 100 A takes conductors at 75 degC (110.14(C)(1)(b)), so 180 A is the
    ampacity. It covers the estimated panel demand. **A 200 A main ahead of 180 A conductors
    is allowed by 240.4(B)** on three conditions: a feeder is not a multi-receptacle branch
    circuit (met); the ampacity is not itself a standard rating; and the next standard rating
    up is 800 A or less. Table 240.6(A) (read) lists no 180 A and gives 200 A next, so all
    three hold. **Verdict: permitted.**
- **Sizes this fixes.** Table 250.66 (GEC) and Table 250.102(C)(1) (bonding) read the same
  rows. On a 320 A service (300 Cu / 400 Al): **#2 Cu**. On a 400 A rating (400 Cu / 600 Al):
  **#1/0 Cu**. The two feeders' summed area (2 x 4/0 Al, 423 kcmil, 250.64(D)(1) if the mains
  count as separate enclosures): **#2 Cu**. The installed GECs (#6 to rods, #4 to the Ufer) are
  each a sole connection to one electrode type, so the 250.66(A)/(B) caps govern and they pass
  on every basis. **The water bond `BC-B-WATER` (#4 Cu) is under Table 250.102(C)(1) on every
  basis**: #2 Cu is wanted at 320 A, #1/0 at 400 A (the earlier 1/0 figure is the 400 A
  reading), and a larger utility lateral raises it. The Al conductor column of the printed
  Table 250.102(C)(1) does track Table 250.66 row for row, so these rows are confirmed.
- **Engine:** read by `electrical_grounding_service.service_basis` when no service conductor is
  authored.

**310.14 Ampacities.** *(summary kept local)*
- **Engine:** not graded; there is no ampacity table in the engine.

**310.15 Ampacity tables and corrections.**
- **(A) General.** Ampacities come from Tables 310.16-310.21 as modified by 310.15(A)-(F) and
  310.12; engineering supervision may calculate them. A size missing from a table is
  interpolated from the adjacent sizes' circular-mil areas. Correction and adjustment factors
  apply to the ampacity at the conductor's own temperature rating, provided the result does not
  exceed the ampacity at the termination's rating (110.14(C)).
- **(B)(1) Ambient.** Outside 30 degC (Tables 310.16, 310.17) or 40 degC (310.18-310.21), multiply
  by Table 310.15(B)(1)(1) or (2) (printed per ambient band and 60/75/90 degC, plus higher
  ratings in the 40 degC table), or use the square-root equation on conductor, new and table
  temperatures. **(B)(2) Rooftop:** a raceway or cable in sun on or above a roof, less than
  3/4 in. above it, adds 33 degC to the outdoor ambient (Ex.: XHHW-2).
- **(C)(1) Adjustment for more than three current-carrying conductors** in a raceway or
  cable, or in single or multiconductor cables not in a raceway, without spacing for a
  continuous length over 24 in.; each paralleled conductor counts. Different systems in
  one raceway (300.5) count only their power and lighting conductors. Table 310.15(C)(1),
  percent of the 310.16/310.18/310.20 value, by the total conductors in the raceway or cable,
  spares included and counted per (E)/(F), and excluding conductors tied to loads that
  can't be energised together:

  | Conductors | 4-6 | 7-9 | 10-20 | 21-30 | 31-40 | 41+ |
  |---|---|---|---|---|---|---|
  | Percent | 80 | 70 | 50 | 45 | 40 | 35 |

  No adjustment: (a) cable trays, where 392.80 governs; (b) a raceway 24 in. or shorter; (c)
  underground conductors entering or leaving an outdoor trench in RMC, IMC, PVC or RTRC up to
  10 ft long with no more than four conductors; (d) Type AC or MC cable without an overall
  jacket, three or fewer current-carrying conductors per cable, 12 AWG copper, and no more than
  20 conductors unspaced, stacked or on bridle rings (past 20, 60%). **(2)** Keep raceways
  spaced. **(D)** Bare or covered conductors with insulated ones take the lowest insulation
  rating. **(E) Neutrals:** counted as current-carrying in a 2-wire circuit (one hot, one
  neutral), in a 3-wire circuit of two hots and the neutral of a 4-wire three-phase wye, and
  where nonlinear loads dominate a 4-wire wye; otherwise a neutral carrying only the
  unbalance is not counted. **(F)** Grounding and bonding conductors are never counted.
- **310.16-310.21 scope.** 310.16: 0-2000 V, 60/75/90 degC, 30 degC ambient, no more than three
  current-carrying conductors, in raceway, cable or earth. 310.17: single conductors in free
  air, 30 degC. 310.18: 150/200/250 degC, 40 degC ambient, in raceway or cable. 310.19:
  single conductors in free air to 250 degC, 40 degC. 310.20: on a messenger, 75/90 degC, 40 degC,
  three or fewer. 310.21: bare or covered conductors in free air, 80 degC conductor, 2 ft/s
  wind, 40 degC. **The value tables themselves are unread.**
- **Table 310.16 (printed), the rows the engine holds** (60/75/90 degC, amperes). Copper: 16 AWG
  10/15/20 (the 75 and 90 degC values for adjustment or correction only), 14 15/20/25, 12
  20/25/30, 10 30/35/40, 8 40/50/55, 6 55/65/75, 4 70/85/95, 4/0 195/230/260, 300 kcmil
  240/285/320, 600 kcmil 350/420/475. Aluminum or copper-clad: 14 AWG 10/15/20 (copper-clad
  only, 75/90 for adjustment only), 12 15/20/25, 6 40/50/55, 4/0 150/180/205, 400 kcmil
  225/270/305, 600 kcmil 285/340/385. Footnote 1 sends 16-10 AWG to 240.4(D). Table 310.17
  (free air, 30 degC) is not coded.
- **Engine:** `model/ampacity.py` holds Table 310.16, the 310.12(A) rule, Table 310.15(C)(1)
  and the 334.80(A) NM cap; `electrical.nm_sleeve_ampacity` (below) reads it, and
  `electrical.conductor_protection` and `continuous_load_circuit` also read it (110.14(C)(1)
  column via `ampacity.termination_column`). There is
  no ambient logic. `box_fill`'s breaker-to-gauge map
  (`GAUGE_BY_BREAKER_A`: 15/20/30/40/50 A to 14/12/10/8/6 AWG Cu) agrees with the 60 degC
  column of the printed table (15, 20, 30, 40, 55 A).
- **Catlin, NM in the derived EMT sleeves (decision #93).** 12 of 251 device boxes take a
  3/4 in. sleeve (the rest are flush). A through-fed box has two NM cables, an end-fed
  receptacle one. Per (E)/(F) each 2-wire 120 V cable carries two current-carrying conductors
  (the neutral counts, the EGC does not): **four in the worst sleeves, so 80%** (4-6
  conductors). Lengths: 77.2 in. (`ED-B-GYM-RC5`/`RC6`/`RC7`, `ED-B-PLAY-N-RC4`/`RC5`, all
  `CKT-RC-BSMT`, 20 A, 12 AWG), 45.9 in. (`ED-B-UTIL-RC1`, `CKT-HA`, 15 A, 14 AWG;
  `ED-B-SUMP-RC`, one cable, two conductors, no adjustment), 24.6 and 17.2 in.
  (`ED-B-STAIR-RC1`/`RC2`), 9.7 in. (three `ED-B-PLAY-N-SCONCE`s). Exemption (b) frees the
  three at 9.7 in. and the 17.2 in. one; the other eight are adjusted if the cables run
  unspaced for over 24 in. (the bundle's length counts, not only the sleeve's).
  - **334.80(A) settles it.** NM ampacity never exceeds the 60 degC value, but the 90 degC
    value may be the base for adjustment and correction if the result stays within the 60
    degC one. 12 AWG: 30 A x 0.80 = 24 A, capped at 20 A, **covers the 20 A breaker exactly**;
    14 AWG: 25 A x 0.80 = 20 A, capped at 15 A, covers the 15 A breaker. (334.80(B)/(C) add
    adjustment, with no 10 ft exception, for more than two NM cables through one sealed
    opening in wood framing or in contact with thermal insulation; a sleeve holds two.)
  - **Engine:** `electrical.nm_sleeve_ampacity` (advisory) applies this to each derived sleeve
    and passes all 12 at Catlin. It counts only the sleeve; its cables-per-sleeve and
    current-carrying counts are `box_fill`'s (two through-fed, one end-fed; two conductors per
    cable). A 20 A circuit on 12 AWG has no margin: the cap holds at 20 A through nine
    conductors, and ten or more (50%) would give 15 A and fail.
  - Overhead NM bundles through joist bays are not modelled; only the sleeves can be counted.
- **Catlin, rooftop adder.** No raceway is modelled on the roof. `CD-A-PV-EAST` ends in
  `ED-A-PV-JB` on the north gable wall, not on a roof, and the array's own wiring is on the
  racking, outside the model; (B)(2) is not graded and would not apply to XHHW-2 anyway.

## Companion rules read with Article 310

**110.14 Connections.** Terminations are identified for the conductor material, and aluminum
terminals say so. (A) Connections are mechanically secure, by pressure connectors, solder or
flexible-lead splices; wire-binding screws and studs with upturned lugs for 10 AWG or smaller.
(B) Splices use identified devices (or brazing, welding, soldering), and are insulated like
the conductors; connectors for direct burial are listed for it. **(C) Temperature:** no
conductor is used where its operating temperature exceeds the lowest rating of any connected
termination, conductor or device; a higher-rated conductor may be used only for adjustment and
correction. **(1)(a)** Equipment for circuits of 100 A or less, or marked for 14-1 AWG,
terminates at 60 degC conductors, or higher-rated ones sized on the 60 degC ampacity, or any if
the equipment is listed and identified for it. **(1)(b)** Over 100 A, or larger than 1 AWG,
75 degC conductors, or higher-rated ones not exceeding the 75 degC ampacity (more if listed).
Ampacities come from Table 310.16 as modified by 310.12. (2) Separate connectors follow their
listed rating. **(D)** Terminal torque is the marked or instructed value, by an approved
means. Catlin's branch circuits therefore read the 60 degC column (as `GAUGE_BY_BREAKER_A`
does), and the 4/0 Al feeders the 75 degC one.
- **Engine:** `NEC.TERMINATION_TEMP`; graded through `termination_column`;
  `Circuit.termination_temp_c` authors a 75 °C listing.

**110.15** **110.16** *(summary kept local)*
- **Engine:** not graded; neither applies to Catlin.

**240.2-240.3** OCPDs, GFPE relays and breakers, GFCI devices and fuse reducers are listed;
reconditioned low-voltage power circuit breakers and electromechanical relays are allowed, but
not GFPE, GFCIs, molded-case breakers or electronic trip units.

**240.4 Conductor protection.** Conductors are protected at their 310.14 ampacity unless
(A)-(H) say otherwise. (A) No overload protection where opening would create a hazard.
**(B) Up to 800 A:** the next standard OCPD above the conductor ampacity may be used if the
conductors do not serve a branch circuit with more than one cord-and-plug receptacle, the
ampacity is not itself a standard rating (without trip adjustment below it), and the next
rating is 800 A or less. (C) Over 800 A, the ampacity equals or exceeds the OCPD rating.
**(D) Small conductors**, after correction factors: 18 Cu 7 A and 16 Cu 10 A (each with limits
on continuous load, 5.6 A or 8 A, and marked OCPD or Class CC/CF/J/T fuses), 14 CCA 10 A
(same conditions, 8 A), 14 Cu 15 A, 12 Al or CCA 15 A, 12 Cu 20 A, 10 Al or CCA 25 A, 10 Cu 30 A.
(E) Taps, (F) transformer secondaries and the rest are out of scope here.
- **Engine:** `GAUGE_BY_BREAKER_A` (15/20/30 A to 14/12/10 AWG Cu) matches (D); the 40 and 50 A
  rows are not (D) rows. `NEC.SMALL_CONDUCTOR_OCPD` is confirmed as 240.4(D). 240.6(A)'s
  standard ratings are in `nec-2026-paraphrase-110-240-625.md`. `electrical.conductor_protection`
  grades 240.4, (B) (no-receptacle circuits only) and (D) (`SMALL_CONDUCTOR_MAX_OCPD`); (G) A/C
  circuits short of plain 240.4 are UNKNOWN.

**334 Nonmetallic-sheathed cable.** **334.40** Nonmetallic boxes follow 314.5; self-contained
devices of insulating material may go without a box if they close around the sheath. **334.80**
(see above). **334.100-334.116** The sheath is nonmetallic; conductors are 16-2 AWG Cu, 14-2
CCA or 12-2 Al for 600 V power; the cable has an insulated, covered or bare EGC; insulation is
a Table 310.4(1) branch-circuit type rated 90 degC (NM-B and NMC-B meet it); the sheath is
flame and moisture resistant (NMC adds fungus and corrosion resistance).
- **Engine:** `NEC.NM_AMPACITY` (334.80(A)) is read by `electrical.nm_sleeve_ampacity`; the
  rest is not graded.
