# Electrical rules the engine grades: Article 440, air-conditioning and refrigeration (2026 NEC)

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

Continues `nec-2026-paraphrase.md` (same conventions; the owner read these pages on 2026-11-14).
All of Article 440 is now read (the owner sent 440.8-440.12(C), the rest of 440.52 and Part VII
later the same day), plus the start of Article 445. **Not read:** 210.63. Table 430.251(C)
is used only with 430.110, 440.12, 440.41 and 455.8(C).

## Catlin, read against these rules

Three outdoor heat-pump units, each on its own 2-pole GFCI breaker with a 3R disconnect beside
it, and one ducted air handler with a factory heat kit. The indoor heads of the multi-split and
the Sapphire carry no circuit; the outdoor unit feeds them.

| Unit | Circuit | Disconnect | Nameplate in the plan |
|---|---|---|---|
| `EQ-M-HP1-OD` FLEXX Ultra 24k (`FXU24HP230V1R32AO`) | `CKT-HP1`, 25 A | `ED-M-HP1-DISC`, 4.3 ft off | MCA 21 A, max OCPD 25 A, in a circuits comment |
| `EQ-S-HP1-AH` air handler + 4.6 kW kit (`FLEXA2LHTR05KWD`) | `CKT-HP1-AH`, 35 A | `ED-A-HP1-AH-DISC`, 3.2 ft off | kit MCA 29.9 A, max OCPD 35 A, in the type's source |
| `EQ-M-HP2-OD` Multi Ultra, 3 heads | `CKT-HP2`, 30 A | `ED-M-HP2-DISC`, 2.0 ft off | MCA 23 A, MOCP 30 A |
| `EQ-M-HP3-OD` Sapphire R32 VFD | `CKT-HP3`, 15 A (backup panel) | `ED-M-HP3-DISC`, 1.7 ft off | MCA 11 A, MOCP 15 A |

- **440.14, within sight.** `electrical.hvac_disconnect` passes the three outdoor units (a
  disconnect on the unit's circuit in plan view with no wall between) and the air handler, whose
  disconnect `ED-A-HP1-AH-DISC` is 3.2 ft off. The distance limit for "within sight" and
  readily accessible are not graded.
- **440.4(B)/440.22 maximum OCPD.** `CKT-HP1` 25 A, `CKT-HP1-AH` 35 A, `CKT-HP2` 30 A and
  `CKT-HP3` 15 A each sit at or under the nameplate MOCP (HP2 MCA 23 / MOCP 30, HP3 MCA 11 /
  MOCP 15, authored on the `EquipmentType`).
- **440.35/440.32 conductor ampacity.** Graded from `Circuit.conductor_awg` (see the Engine
  line). From
  Table 310.16's 60 degC column (equipment of 100 A or less terminates at 60 degC unless listed
  for 75, 110.14(C)(1)(a)): HP1's MCA of 21 A needs 10 AWG Cu (12 AWG is 20 A at 60 degC, 25 A
  at 75 degC); the air handler's 29.9 A needs 10 AWG Cu (30 A), just over. 240.4(D) would cap a
  12 or 10 AWG circuit at 20 or 30 A, but 240.4(G) sends A/C conductors to Article 440.
- **440.8, bath zone (new).** `electrical.bath_hvac_zone` passes: none of the eight heat-pump
  units (three outdoor, four heads, the air handler) comes within 3 ft in plan of any of the six
  tubs and showers. Nearest: the air handler `EQ-S-HP1-AH`, 6.1 ft from the studio-bath shower;
  the sauna-gym head 8.6 ft from the sauna shower; `EQ-M-HP3-STAIR` 13 ft from the main tub.
  The ERV and its mixing box carry no compressor and are not A/C equipment under this rule
  (the box is 8.9 ft from the studio-bath shower anyway).
- **440.11 disconnect enclosure.** The three 3R disconnects are outdoors, on the house or court
  walls at about 6 ft 4 in. above grade, readily accessible to anyone: their enclosures must
  lock or need a tool to open. A standard hooded safety switch needs a tool or a padlock hasp
  only if so specified; not modelled. **Owner question:** specify a lockable or tool-opened
  3R enclosure (or a padlock) for `ED-M-HP1/2/3-DISC`.
- **440.12(A)(1) disconnect rating.** The 3R type (`ED-T-DISCONNECT-3R`) carries no ampere
  rating (a plan comment calls it 60 A). 115% of HP1's 21 A MCA is 24 A, of the air handler's
  29.9 A is 34 A; a 60 A switch covers both. HP2 and HP3 need their nameplate rated-load
  currents (not authored). Field needed: an ampere rating (and horsepower or unfused rating)
  on the disconnect type.
- **440.10 short-circuit rating.** Applies to the motor controllers of multimotor and
  combination-load equipment (the heat pumps and air handler): they are not installed where the
  available fault current exceeds the marked rating, and the calculation and date are kept.
  440.4(B) Ex. 3 relieves one- and two-family dwellings from *marking* a short-circuit current
  rating, so Catlin's units may carry none; 440.10 then has nothing to compare, which makes
  Xcel's available fault current (see 408.6 in `nec-2026-paraphrase-404-408.md`) the open item.
- **Part VII room air conditioners:** none authored. All cooling is the three Gree heat-pump
  systems, which are not cord-and-plug (Part VII applies only to cord-and-plug units of 250 V
  or less, single phase). N/A. A future window unit would be graded there.
- **Article 445 generators:** none authored. The backup is an inverter with a GEN port
  (`backup_power.md` section 8-11): a car's 240 V outlet or a portable generator could be fed
  into it (that makes 445.11's neutral-bonding marking relevant if a generator is plugged in), but no generator
  or inlet is modelled, and V2H is not a generator under 445.

- **440.15** (indoor-unit marking on the outdoor disconnect) applies only outside one- and
  two-family dwellings: N/A. **440.2(A)** listing is the manufacturers' (not modelled);
  **440.2(B)** the factory heat kit is a listed field-installable accessory in the air handler.
  **440.13** cord-and-plug: none of these is cord-connected.

## Part I: general

**440.1 Scope.** **440.2** *(summary kept local)*
- **Engine:** not graded.

**440.4 Marking.** (A) A hermetic motor-compressor is marked with maker, designation, phases,
voltage, frequency; the rated-load current (on its own or the equipment's nameplate); the
locked-rotor current where single-phase above 9 A at 115 V or 4.5 A at 230 V, or polyphase;
"thermally protected" or "thermally protected system" where those protectors are used; and the
nameplate stays accessible after installation. (B) Multimotor and combination-load equipment
is marked with maker, voltage, frequency, phases, **minimum supply circuit conductor
ampacity (MCA)**, **maximum rating of the branch-circuit short-circuit and ground-fault device
(MOCP)** and the controllers' short-circuit current rating. The MCA comes from Part IV counting
everything that runs together; the OCPD may not exceed Part III's value; multi-circuit equipment
is marked per circuit. Ex.: equipment on a single 15 or 20 A 120 V (or 15 A 208/240 V
single-phase) circuit is marked as one load; a room A/C under 440.62(A) needs no MCA/MOCP;
dwelling or cord-and-plug equipment needs no short-circuit current rating. (C) Equipment whose
protection allows continuous current above the percentage in 440.52(B)(2) or (B)(4) also marks
a branch-circuit selection current.
- **Engine:** `NEC.HVAC_NAMEPLATE` names (B). `electrical.bath_hvac_zone`
  (`NEC.HVAC_BATH_ZONE`, advisory) grades the 440.8 zone: plan distance of a heat-pump
  unit's footprint to a tub or shower fixture at most 3 ft with the unit's base under 8 ft above
  the fixture's top (conservatively the rim). FAIL when inside; PASS when none is; N/A when no tub, shower
  or A/C equipment is authored. A wall does not end the zone (unlike 406.9(C)).
  `EquipmentType.min_circuit_ampacity_a`/`max_overcurrent_a` hold the nameplate.

**440.5 Controllers** **440.6 Ampacity and rating.** **440.7** **440.8** **440.9** **440.10** *(summary kept local)*
- **Engine:** not graded.

**440.11 General.** A disconnect is provided for the A/C equipment, motor-compressors and
controllers. If it is readily accessible to unqualified persons, any enclosure door or cover
that exposes live parts when open is locked or needs a tool to open.
**440.12 Rating.** (A) A disconnect for a hermetic motor-compressor is chosen on the nameplate
rated-load or branch-circuit selection current (whichever is greater) and the locked-rotor
current. (1) Ampere rating at least 115% of that current (Ex.: a listed unfused motor-circuit
switch with a horsepower rating not under the equivalent horsepower may have an ampere rating
under 115%). (2) Equivalent horsepower: from Tables 430.248-430.250 for the rated-load or
selection current and 430.251(A)-(C) for the locked-rotor current; use the next higher value
for off-table currents, and the larger horsepower where the two differ. (B) Combination loads on
one disconnect: (1) horsepower from the sum of all currents (resistance included) at rated load
and at locked rotor, treated as one motor; (2) ampere rating at least 115% of the summed rated-load currents (same switch
exception). (C) A small compressor with no marked locked-rotor current, or a small motor
outside the tables, is taken at six times its rated-load current.
**440.12(D)-(E), 440.13, 440.14, 440.15.** (D) Every disconnect in the compressor circuit
between the feeder and the compressor meets 440.12; (E) over 100 hp, 430.109(E).
**440.13** A cord-connected unit may use its plug as the disconnect.
**440.14 Location.** The disconnect is within sight of, and readily accessible from, the
equipment; it may be on or inside the equipment. It meets the 110.26(A) working space, and is
not on a panel designed for access to the equipment or where it hides the nameplate. Ex. 1: an
industrial process unit with a lockable disconnect and written safety procedures, qualified
persons only, needs none in sight. Ex. 2: a plug as disconnect (440.13) must be accessible,
not readily accessible. **440.15** In other than one- and two-family dwellings the outdoor
disconnect of a split system is marked with the location of every indoor unit it supplies.
- **Engine:** `electrical.hvac_disconnect` (advisory, `NEC.HVAC_DISCONNECT`): for each heat
  pump or ducted air handler on a circuit, a DISCONNECT device on that circuit in plan sight
  (no wall between) passes; a wall between or another level is UNKNOWN; none is UNKNOWN.
  440.11/440.12(A)(1) graded from `ElectricalDeviceType.lockable`/`disconnect_rating_a` (115%
  of the MCA as the bound); UNKNOWN while unset.
  Not graded: the within-sight distance limit (Article 100, unread), readily accessible, 110.26(A)
  working space, nameplate obstruction, or the indoor heads.

## Part III: branch-circuit short-circuit and ground-fault protection

**440.21** Part III's devices protect the branch conductors, controls and motors from short
circuits and ground faults, in addition to the rest of the code.
**440.22 (A) One motor-compressor.** The device carries the starting current and is rated or
set no higher than 175% of the rated-load current or branch-circuit selection current, whichever
is larger. Ex. 1: if that is not a standard size, the next standard rating is allowed. Ex. 2: if
that will not start the motor, up to 225%. Ex. 3: no device need be under 15 A.
**(B) Equipment.** The device carries the equipment's starting current. A sole compressor
follows (A). Several loads follow 430.53 and (1)-(2): (1) the compressor is the largest load:
the (A) value for it plus the other compressors' rated-load (or selection) currents plus the
other loads' ratings; (2) it is not the largest: the sum of the compressors' currents plus
430.53(C)(4) for other motors, or 240.4 for non-motor loads. Ex. 1: equipment on a 15 or 20 A
120 V or 15 A 208/240 V single-phase circuit may take that circuit's 15 or 20 A device, but
not above the maximum marked on the equipment. Ex. 2: cord-and-plug equipment of 250 V or less,
single-phase, uses its nameplate. **(C)** The device never exceeds the maximum on the
equipment (a controller's overload-relay table).
- **Engine:** `NEC.HVAC_MAX_OCPD`. `electrical.hvac_disconnect` grades breaker <= marked MOCP
  per circuit (largest-MCA nameplate on the circuit). Catlin: all four PASS.

## Parts IV-VI: conductors, controllers, overload protection

**440.31** Part IV and Article 310 Part III give the conductor ampacities (440.6(A) Ex. 1
excepted), not for integral conductors. **440.32 Single compressor:** at least 125% of the
rated-load current or branch-circuit selection current, whichever is greater; for wye-start,
delta-run, 72% of it between the controller and the compressor. **440.33 Compressors with
other motors:** at least the sum of the compressors' rated-load (or selection) currents, plus
the other motors' full-load currents, plus 25% of the highest motor (Ex. 1: interlocked, the
largest group that runs together; Ex. 2: room A/C under Part VII). **440.34** A compressor plus
other loads: the other loads from the load calculation plus the compressor's 440.32 or 440.33
value. **440.35 Multimotor and combination equipment:** at least the marked minimum circuit
ampacity.
- **Engine:** `NEC.HVAC_CONDUCTORS` (440.32), `NEC.HVAC_COMBINATION_CONDUCTORS` (440.35).
  Graded from `Circuit.conductor_awg` at its 110.14(C)(1) column against the nameplate MCA;
  all four HP circuits PASS.

**440.41 Controllers.** **440.51-440.52** **440.52(A)(3)-(4), (B)** **440.53** **440.54** **440.55** *(summary kept local)*

## Part VII: room air conditioners

**440.60** **440.61** **440.62** **440.63** **440.64** **440.65** *(summary kept local)*
- **Engine:** not graded; N/A at Catlin (no room A/C).

## Article 445: generators (start)

**445.1-445.2** **445.10** **445.11 Marking.** **445.12** *(summary kept local)*
- **Engine:** not graded; no generator is authored.
- **Engine:** not graded.
