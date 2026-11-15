# Electrical rules the engine grades: Article 680, spas and fountains (2026 NEC)

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

Continues `nec-2026-paraphrase.md` (same conventions). The owner read 680.34-680.54 in print
on 2026-11-14, then 680.1-680.27(A) (Parts I and II) the same day. Still unread: 680.27(B)-680.33,
which no spa rule here reaches. Parts I and II reach a spa because 680.42 and 680.43 send an
outdoor or indoor tub to them, reading "pool" as the tub (680.1 puts spas and hot tubs in the
article's scope). The check is `code.NEC_680_spa` (`checks/mep/electrical_spa.py`, distances in
`electrical_spa_geometry.py`); section strings are in `model/nec.py`.

## Catlin's spa, as authored (read from `plan/` 2026-11-14)

- **A circuit, a disconnect and a receptacle; no tub.** `CKT-SPA` (50 A, 2-pole, GFCI breaker,
  `spa=True`, "Hot tub (sunken garden)", on `ED-B-PANEL-2`) feeds `ED-B-SPA-DISC`, a NEMA 3R
  disconnect 5 ft up on `W-SG-W1`'s court face (the porch wall), through `CD-B-SPA`. Beside it,
  28 in. along the wall at 4 ft, `ED-B-SPA-RC` is a weather-resistant GFCI receptacle on
  `CKT-RC-BSMT` (a GFCI breaker, 20 A general circuit).
- **The tub is not modeled.** No tub is installed at construction; `CKT-SPA` is
  `rough_in_only`. No Equipment, footprint, position, product or listing exists for
  it, so its position, whether it is self-contained or packaged, and what lies within 5 ft or
  10 ft of its walls are all unauthored. The description puts it in the sunken garden, which is
  outdoors. No switch, luminaire or metal item is tied to it in the data.
- **No pool, storable pool, immersion pool or fountain** is authored, and the model has no
  element that could hold one. That is absence of a declaration, not evidence of absence, so
  pool rules (680.34/680.35/680.45) and Part V emit no finding (see Part V below).

## Part IV: spas and hot tubs

**680.40 General.** *(summary kept local)*
- **Engine:** scope only.

**680.41(A) Emergency switch.** Other than one-family dwellings, a clearly marked emergency
shutoff for the recirculation and jet motors must be at least 5 ft from the tub, adjacent to it
and in sight of it.
- **Engine:** `code.NEC_680_spa` returns N/A when the plan has exactly one `dwelling` building
  (the model carries no dwelling-unit count; Catlin is a single family house, see its brief),
  else UNKNOWN. Catlin: N/A.

**680.41(B) Equipment over the low-voltage contact limit.** Except for self-contained spas and
hot tubs, any such equipment stays at least 5 ft horizontally from the tub's inside walls,
unless a solid fence, wall or other permanent barrier separates them.
- **Engine:** needs the modeled tub. For each disconnect, panel, junction box, meter or
  circuit-fed Equipment on the tub's storey within 5 ft in plan: PASS when a wall band crosses
  the line between them, or the type states `spa_self_contained`; else FAIL, or UNKNOWN while
  the listing is unstated. Plan distance is taken from the footprint (the outer edge, which
  under-reports the distance to the inside wall, a conservative error). Receptacles, switches
  and luminaires have their own rules and are not included. N/A when every spa circuit is
  `Circuit.rough_in_only` and no SPA Equipment exists. Catlin: N/A (owner 2026-11-14: rough-in,
  no tub).

**680.42 Outdoor installations.** Parts I and II also apply to an outdoor tub, except as
(A)-(C) allow.
- **(A) Flexible connections.** A listed packaged equipment assembly, or a self-contained unit
  with its control panel built in, may use liquidtight flexible metal or nonmetallic conduit, or
  a cord and plug of at most 15 ft if GFCI protected.
- **(B) Bonding.** Metal-to-metal mounting on a common frame or base counts as bonding; wooden
  stave bands need no bonding. Perimeter-surface equipotential bonding (680.26(B)(2)) is waived
  only when all four hold: the unit is listed, labeled and identified as self-contained for
  aboveground use; it is not identified as indoor-only; it is installed to its instructions on
  or above grade; and its top rim is at least 28 in. above every perimeter surface within 30 in.
  horizontally (nonconductive external steps do not change that measure).
- **(C) Underwater luminaires** are wired to 680.23 or 680.33.
- **Engine:** a tub outside every room is outdoors and gets Part II's receptacle, luminaire,
  switch and outlet rules (below). (A) and (C) are not graded; the (B) waiver's four conditions
  have no fields, so 680.26 stays UNKNOWN (see 680.26). Catlin: the tub is not modeled.

**680.43 Indoor installations.** Parts I and II apply, modified here, and the equipment is
wired by Chapter 3 methods. Ex. 1: a listed packaged unit of 20 A or less may be cord-and-plug
connected for service. Ex. 2: the perimeter-surface bonding does not apply to a listed
self-contained tub on a finished floor.
- **(A) Receptacles.** At least one 125 V, 15/20 A receptacle on a general-purpose branch
  circuit lies between 6 and 10 ft from the inside wall. (1) Every receptacle is at least 6 ft
  away, measured on the shortest path the cord would take without piercing a floor, wall,
  ceiling, hinged or sliding door, window or other permanent barrier (4). (2) Every receptacle
  within 10 ft has GFCI or SPGFCI per 680.5. (3) A receptacle supplying the
  tub is at most 150 V to ground and GFCI protected.
- **(B) Luminaires, lighting outlets and paddle fans.** Over the tub or within 5 ft of its
  walls: at least 12 ft above the maximum water level without GFCI, at least 7 ft 6 in. with
  GFCI; lower than 7 ft 6 in. only for listed recessed (glass or plastic lens, nonmetallic or
  isolated trim) or surface (glass or plastic globe, nonmetallic or isolated body) types, damp
  location rated, on GFCI. Underwater lights go to 680.23 or 680.33.
- **(C) Switches** are at least 5 ft horizontally from the inside walls.
- **(D) Bonding** joins metal fittings on the tub; metal parts of the circulation equipment
  (pump motors, unless part of a listed self-contained tub); metal raceway and piping within 5 ft
  and unbarriered; metal surfaces within 5 ft and unbarriered (small unlikely-to-energize items
  such as jets, drains, towel bars and mirror frames excepted when not tied to metallic piping);
  and non-current-carrying metal of unrelated devices within 5 ft.
- **(E) Methods:** threaded metal piping, metal-to-metal frame mounting, or a solid copper
  jumper of 8 AWG or larger, insulated, covered or bare.
- **(F) Equipment grounding:** all electrical equipment within 5 ft, and all equipment of the
  circulating system, goes to the EGC, except low-voltage equipment on a 680.23(A)(2) supply.
- **Engine:** needs the modeled tub; indoors means its centre lies inside a room of its storey,
  and 680.43(A)/(C) then stand in for 680.22(A)/(C) below. (A)(1): an
  ElectricalDevice receptacle within 6 ft in plan is FAIL, UNKNOWN if a wall lies between (the
  cord path is longer than the straight line and is not computed). (A) "at least one": a general
  circuit receptacle 6-10 ft away with an open path is PASS, none FAIL. (A)(2)/(3): FAIL for a
  receptacle within 10 ft, or on a spa circuit, with neither a GFCI device nor a GFCI breaker.
  (C): a switch within 5 ft is FAIL (UNKNOWN behind a wall). (B) and (D)-(F) are not graded: no
  luminaire listing, water level or bonding data (680.26 below). Catlin: ungraded, the tub is
  outdoors and unmodeled.

**680.44 GFCI and SPGFCI.** (A) The outlet or outlets supplying a self-contained, packaged or
field-assembled tub have GFCI protection per 680.5(B) or SPGFCI per 680.5(C), whichever
applies. (B) A listed unit marked as having integral GFCI for all its electrical parts needs
nothing further. (C) A circuit for a gas-fired tub water heater that runs separately from the
tub and operates above the low-voltage contact limit has GFCI.
- **Engine:** (A) is graded for every circuit with `Circuit.spa` or named by a spa Equipment: a
  GFCI breaker (class A or C) PASS, none FAIL, with the (B) listing named in the fix because the
  model cannot state it. 680.5 then picks the class: a 1- or 2-pole circuit of
  60 A or less is 120 V to ground on this house's 120/240 V service, so Class A is required (a
  Class C SPGFCI there is FAIL, a circuit over 60 A or of 3 poles is UNKNOWN). (C): no gas
  heater is modeled; not graded. **Catlin: `CKT-SPA` (50 A, 2-pole, Class A) PASS.**

## 680.45, 680.34, 680.35: other pools

**680.45 Permanently installed immersion pools.** **680.34 / 680.35 Storable and portable pools.** *(summary kept local)*
- **Engine:** not graded. Catlin authors no such pool; the model has no element to declare one,
  so the check stays silent rather than answer N/A.

## Part V: fountains (680.50-680.54)

**680.50 General.** **680.51 Luminaires, submersible pumps and submerged equipment.** **680.52 Junction boxes.** **680.54 Grounding and bonding.** *(summary kept local)*
- **Engine:** not graded. Catlin's water elements (its two rain gardens) are planted
  infiltration basins with no pump, luminaire or powered equipment; the model has no
  fountain element. The check emits no finding for Part V (no N/A without a positive statement
  that a house has none).

## Part I: general (680.1-680.14)

**680.1, 680.2, 680.4 Scope, listing, inspection.** *(summary kept local)*
- **Engine:** not graded (the model carries no listing for the tub).

**680.5 GFCI and SPGFCI.** These are in addition to 210.8. (B) Receptacles and outlets on
branch circuits of 150 V or less to ground get a Class A GFCI, on single-phase circuits of 60 A
or less and three-phase circuits of 100 A or less; an exception frees listed low-voltage
equipment fed from a 680.23(A)(2) transformer or supply. (C) Above 150 V to ground, up to 480 V
phase to phase, a Class C-style SPGFCI tripping at 20 mA or less.
- **Engine:** `code.NEC_680_spa` reads the class from the circuit (see 680.44). Catlin PASS.

**680.7 Grounding and bonding.** *(summary kept local)*
- **Engine:** not graded: no conductor, EGC or terminal data. One UNKNOWN per spa circuit.
  `CD-B-SPA`'s conductors are not authored; its raceway is the default EMT.

**680.8 Cord-and-plug equipment.** *(summary kept local)*
- **Engine:** not graded. **680.9 Overhead conductors.** Power conductors and open wiring clear
the water, platform or raft in any direction by 22.5 ft (insulated, messenger-supported
service-type cable), 25 ft (other, up to 15 kV) or 27 ft (15-50 kV), measured from the maximum
water level; observation stands and towers 14.5, 17 or 18 ft; the horizontal limit reaches the
outer edge of those structures and is at least 10 ft from the inside wall. Communications and
coaxial cable stays 10 ft over the water; network-powered broadband follows the table.
- **Engine:** not graded; no overhead conductor is modeled near the court.

**680.10 Pool water heaters.** *(summary kept local)*
- **Engine:** not graded (no spa heater data).

**680.11 Underground wiring.** *(summary kept local)*
- **Engine:** not graded: no tub footprint to measure the 5 ft from, and `CD-B-SPA` is EMT
  running inside the basement to sleeves at `W-SG-W1`.

**680.12 Equipment rooms.** *(summary kept local)*
- **Engine:** not graded; no spa equipment room is modeled.

**680.13 Maintenance disconnect.** One or more means open all ungrounded conductors to
non-lighting equipment, readily accessible, within sight of the equipment, and at least 5 ft
horizontally from the inside walls of a pool, spa, fountain or hot tub, unless a permanent
barrier from the open water gives a 5 ft reach path. The distance is measured from the water's
edge along the shortest path needed to reach the disconnect.
- **Engine:** every DISCONNECT on a spa circuit, plan distance from the footprint: 5 ft or more
  PASS (within-sight and accessibility are not graded), under 5 ft FAIL, UNKNOWN behind a wall
  (the barrier must give a 5 ft reach). No tub footprint means UNKNOWN. N/A when every spa
  circuit is `Circuit.rough_in_only` and no SPA Equipment exists. **Catlin: N/A (owner
  2026-11-14: rough-in, no tub).**

**680.14 Corrosive environments.** *(summary kept local)*
- **Engine:** not graded (shares 680.7's UNKNOWN). EMT is not on 680.14's suitable list; the
  owner decides whether the garden counts as corrosive.

## Part II: permanently installed pools, as 680.42/.43 apply it to a tub

**680.20 General.** *(summary kept local)*

**680.21 Motors.** *(summary kept local)*
- **Engine:** not graded; the pump motors are not modeled.

**680.22(A) Receptacles.** (1) At least one 125 V, 15/20 A general-purpose receptacle 6-20 ft
from the inside wall, at most 6 ft 6 in. above the floor, platform or grade serving the pool.
(2) Receptacles for circulation and sanitation loads are at least 6 ft away, GFCI and grounding
type. (3) Other receptacles are at least 6 ft away. (4) Every receptacle within 20 ft has GFCI
or SPGFCI. (5) Distances follow the cord path, not piercing a floor, wall, ceiling, door,
window or other permanent barrier.
- **Engine:** outdoor tub. Under 6 ft: FAIL (UNKNOWN behind a wall). One qualifying receptacle:
  general-circuit, 6-20 ft, open path, mount height at most 6 ft 6 in. (read as AFF), else FAIL.
  GFCI within 20 ft, or on a spa circuit, else FAIL. N/A when every spa circuit is
  `Circuit.rough_in_only` and no SPA Equipment exists. **Catlin: N/A (owner 2026-11-14:
  rough-in, no tub);** `ED-B-SPA-RC` (WR GFCI, 4 ft up) is the candidate receptacle for a
  future tub.

**680.22(B) Luminaires, fans, festoon lighting.** Outdoors, over the pool or within 5 ft
horizontally: at least 12 ft above the maximum water level. Indoor clearances match unless the
circuit is GFCI, then 7 ft 6 in. for totally enclosed luminaires and rated outdoor-style paddle
fans. Existing luminaires within 5 ft of the wall stay if at least 5 ft over the water,
rigidly attached and GFCI protected. In the 5-10 ft band luminaires need GFCI unless 5 ft over the water and
rigidly attached. Cord-and-plug luminaires within 16 ft follow 680.8. Listed low-voltage
luminaires and gas-fired low-voltage decorative equipment may stand closer, with bonding.
- **Engine:** outdoor tub, `LIGHT` devices only: mount height is an upper bound on the clearance,
  so only a low luminaire FAILs (under 12 ft within 5 ft; under 5 ft with no GFCI in the 5-10 ft
  band), a GFCI one in the band PASSes, the rest UNKNOWN (water level, rigid attachment).
  Indoor luminaires are not graded.

**680.22(C)-(F).** (C) Switches stay 5 ft from the inside wall unless a fence, wall or barrier
gives a 5 ft reach, or the switch is listed for use that close. (D) No portable signs within
5 ft. (E) Other outlets (remote control, signaling, alarm, communications) are 10 ft away by
cord path. (F) Other equipment over the low-voltage limit is 5 ft away unless walled off.
- **Engine:** (C) switch under 5 ft FAIL, UNKNOWN behind a wall. (E) `DATA_OUTLET` under 10 ft
  FAIL, UNKNOWN behind a wall. (F) shares 680.41(B)'s test and its self-contained exception.

**680.23 and 680.24 Underwater luminaires, boxes.** *(summary kept local)*
- **Engine:** not graded; no underwater luminaire is modeled.

**680.26 Equipotential bonding.** *(summary kept local)*
- **Engine:** not graded. The model has no bonding grid, reinforcement, perimeter surface or
  fixed-metal-near-the-tub data. One UNKNOWN per tub names what to author. 680.42(B) waives (2)
  only if the tub is listed self-contained for aboveground use, not indoor-only, on or above
  grade, with its rim 28 in. over perimeter surfaces within 30 in. N/A when every spa circuit
  is `Circuit.rough_in_only` and no SPA Equipment exists. Catlin: N/A (owner 2026-11-14:
  rough-in, no tub).

**680.27(A) Underwater audio.** *(summary kept local)*
- **Engine:** not graded.

## What Catlin must author before its tub grades

| To grade | Author |
| --- | --- |
| 680.13, 680.22, 680.41(B), 680.43 | An `Equipment` of kind `SPA` with footprint and position (the sunken garden); its `EquipmentType.spa_self_contained`. |
| 680.26, 680.42(B) waiver | Tub type: in-ground (no waiver) or listed self-contained aboveground; rim height over every perimeter surface within 30 in.; the perimeter paving and its bonding; metal within 5 ft horizontally or 12 ft up: `W-SG-W1` rebar and door frames, railings, `CD-B-SPA` and the disconnect's enclosure. |
| 680.7, 680.14 | `CKT-SPA`'s EGC size and wiring method (today an EMT run, unlisted for corrosion). |
| 680.22(B) | Luminaires near the court: mount height over the water, GFCI and rigid attachment. |
