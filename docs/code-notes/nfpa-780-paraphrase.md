# Lightning protection rules the engine reads: interpretation notes (NFPA 780)

> Independent engineering notes for Type:Haus. Not published, endorsed or reviewed by the
> National Fire Protection Association. NFPA 780® is a registered trademark of NFPA, named
> here only to identify the standard a rule comes from. This file contains no text from the
> standard. Each entry is a summary in our own words, limited to what a check needs. It does
> not substitute for the standard: read it before designing a lightning protection system.
>
> Summaries of rules the engine does not grade, and whole code tables, are kept out of
> the public repo; such an entry keeps its citation and Engine note, marked
> *(summary kept local)*.

The engine treats NFPA 780 as guidance, not as an adopted code. Catlin has no lightning
protection system (LPS), only the *hooks* for one: two terminals on a counterpoise bonded to
the service electrode system, and aluminum down-leads (decision #123). The checks citing it
are ADVISORY and never carry ERROR severity. NEC 250.106, which *is* law, is in
`nec-2026-paraphrase.md`.

The owner read pages 780-11, -12, -24, -25, -28 and -29 on 2026-11-14 (§4.1–4.5.3,
4.12.8–4.15.2.5, 4.19–5.3). The cross-references to NFPA 660 place this as the 2026
edition. Section strings live in `typehaus.model.nfpa780.NFPA780`. Sections cited only by
cross-reference (such as 4.12.4) were not read.

## 4.1 Material class

- **4.1.1.1** **Table 4.1.1.1.1 (Class I minimums)** *(summary kept local)*

  | Conductor | Copper | Aluminum |
  |---|---|---|
  | Main conductor, cable | 57,400 cmil (strands ≥ 17 AWG) | 98,600 cmil (strands ≥ 14 AWG) |
  | Bonding conductor, cable | 26,240 cmil | 41,100 cmil |
  | Air terminal, solid | 3/8 in. dia. | 1/2 in. dia. |

- **Engine:** not graded. Catlin is Class I. Its `GroundingStandard` carries a #2 Cu
  counterpoise (66,360 cmil) and 1/0 Al down-leads (105,600 cmil), both above the main-size
  minimums. No check compares a size against the table.

## 4.2–4.3 Materials and corrosion

- **4.2.1** No metal pairings that corrode galvanically when wet.
- **4.2.2.3.1** Aluminum stays out of the bottom 18 in. above where the system meets earth
  (or soil on vegetated roofs or planters), and away from places where it would deteriorate
  quickly.
- **4.2.3** Copper doesn't go on or touch aluminum roofing, siding or other aluminum
  surfaces. **4.2.4** Aluminum doesn't go on copper surfaces or where copper runoff reaches
  it.
- **4.3.3** Aluminum conductors stay off alkaline-painted surfaces and out of concrete,
  masonry and very wet spots.
- **4.3.4.2–4.3.4.3** Joints between different metals use bimetallic fittings. That
  includes an aluminum down conductor meeting copper or copper-clad grounding.
- **Engine:** `grounding.lightning_ready`. An aluminum down-lead must stop at least
  `transition_min_height` (Catlin: 18 in.) above grade, with the Cu transition below it.
  A copper lead running above that height on the metal skin fails. The check measures from
  site grade rather than from the point where the system meets earth. The bimetallic
  connector is authored (`transition_product_ref`) and not graded.

## 4.4 Mechanical damage

- **4.4.1** **4.4.2** *(summary kept local)*
- **Engine:** not graded.

## 4.5 Strike termination

- **4.5.1** **4.5.2** *(summary kept local)*
- **Engine:** not graded. Catlin authors no air terminals.

## 4.12.8 Electrode selection

- **4.12.8.1** **4.12.8.2** **4.12.8.3** *(summary kept local)*
- **Engine:** not graded. Catlin's counterpoise is buried 24 in. deep (`counterpoise_depth`).
  The ring rule (4.12.4) was not read.

## 4.13–4.14 Common bonding and potential equalization

- **4.13.1** All grounded media and buried metal, underground piping included, that could
  carry lightning current are tied to the LPS within 12 ft vertically of the base of the
  structure. Over 60 ft tall, the tie is a ground loop conductor (4.13.2).
- **4.13.3** That tie includes every grounding electrode system: lightning, power service,
  communications and antenna.
- **4.13.4.1** Underground metal piping to interconnect: water service, well casings within
  25 ft, gas piping, underground conduits and LP gas piping. **4.13.4.2** Jumper around
  nonconductive sections with main-size conductor, or bond where continuity is assured.
- **4.13.5** Where those systems already meet at one accessible point, the LPS connects
  there with one main-size conductor. That point may be a ground bar, a section of water
  pipe, or structural metal per NFPA 70.
- **4.13.6.1** Otherwise, bond the metal to the LPS grounding below 12 ft above the base,
  using main-size conductors. Metal that is already bonded by its construction needs no
  more. Continuous structural metal and a continuous metal water system are connected. Gas
  is bonded on the customer's side of the meter. **4.13.6.2** An isolating spark gap is
  allowed where galvanic corrosion is a concern or local code forbids a direct bond.
- **4.14.1** Ground-level equalization is done by 4.13. Roof-level (4.14.2) and
  intermediate (4.14.3) equalization apply over 60 ft. Loop conductors are main-size
  (4.14.4).
- **Engine:** `grounding.lightning_ready` needs at least two `lps_terminal` electrodes at
  diagonally opposite corners, in the same bonded system as the service electrodes
  (graph connectivity, `resolve/grounding.py`). That system goes beyond 4.13's requirement.
  Water bonding is graded under NEC 250.104 (`code.NEC_250_104_water_bond`). Gas bonding,
  4.13.4.2 jumpers and conductor sizes are not graded.

## 4.15 Bonding metal bodies

- **4.15** **4.15.1** **4.15.2** **4.15.2.5** *(summary kept local)*
- **Engine:** not graded. Catlin is under 40 ft. The low-rise formula (4.15.2.6) was not
  read.

## 4.19 Surge protection

- **4.19.1** Surge protection covers listed Type 1 or 2 SPDs on systems up to 1,000 V,
  arresters above that, and listed protectors on signal, data and communications lines.
- **4.19.2.1** Every power service to the structure has an SPD, either part of the service
  equipment or right next to it.
- **4.19.2.2** SPDs are also needed where power conductors leave one building to feed
  another *and* the run is over 100 ft.
- **4.19.2.3** More SPDs downstream are allowed, in addition to those.
- **4.19.2.6** A service-entrance SPD has a nominal discharge current (In) of at least
  20 kA (8/20 µs) per phase.
- **4.19.2.7** VPR caps per mode. For 120/240 V 3-wire + ground: 700 V line–neutral,
  line–ground and neutral–ground, and 1,200 V line–line.
- **4.19.2.8–4.19.2.9** The SPD is marked with an SCCR (receptacles exempt) that the
  available fault current doesn't exceed. Its MCOV is above the utility's upper tolerance.
- **4.19.2.11** On a circuit, every ungrounded conductor gets one. Leads are as short as
  practical, with no unnecessary bends.
- **4.19.2.14–4.19.2.15** Accessible, with a visible indication that it works.
- **4.19.4** Signal, data and communications lines entering or leaving the structure get
  surge protectors, unless the provider already protects them. They also need them between
  buildings where the run is over 100 ft. Imax is at least 10 kA (8/20 µs). Each is grounded
  (unless it works by isolation), never through a down conductor (4.19.4.7). A supplementary
  ground reference is needed if the ground point is more than 20 ft away (4.19.4.6). Leads
  are short and accessible.
- **Engine:** `grounding.spd_coordination` checks that an SPD is at the service
  (4.19.2.1), a `pv_dc` SPD beside each box on the PV DC run, and an SPD in any outbuilding
  fed by more than one circuit. The outbuilding test is the owner's goal and does not apply
  4.19.2.2's 100 ft. In, VPR, SCCR, MCOV, lead length and the 4.19.4 data protectors are not
  graded.

## 5.2 Masts and flagpoles

*(summary kept local)*
- **Engine:** not graded.
