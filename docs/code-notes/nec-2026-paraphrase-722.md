# Limited-energy cables: 721.50-723.22 (2026 NEC)

> Independent engineering notes for Type:Haus. Not published, endorsed or reviewed by NFPA.
> NFPA 70®, National Electrical Code® and NEC® are registered trademarks of NFPA. No code text
> here: each entry restates a rule in our own words. Read your adopted edition before relying
> on it. See `nec-2026-paraphrase.md` for the conventions.
>
> Summaries of rules the engine does not grade, and whole code tables, are kept out of
> the public repo; such an entry keeps its citation and Engine note, marked
> *(summary kept local)*.

Read in print by the owner 2026-11-14: 721.50, 721.60, all of Article 722, and 723.1, 723.2,
723.20 and 723.22. Constants in `typehaus.model.nec.NEC`; the one check is
`electrical.limited_energy_wiring` (`checks/mep/limited_energy.py`, ADVISORY); numbering and the
check are pinned in `tests/test_nec_722.py`. **Not read:** 721.30 (Class 2/3 power-source
limits and listing), 723.20's Table 723.20 body, 724.x (Class 1 wiring, 724.46).

## What it means for Catlin

| Rule | Catlin | Verdict |
|---|---|---|
| 722.15(A) no limited-energy cable in a raceway or box with power | 14 data / Class 2 raceways (12 data runs, `CD-M-RSD-INIT`, `CR-M-LAUNDRY-24V`) each carry one `service` and name no circuit | PASS (structural) |
| 722.2(B) wet location: wet-listed or metal sheath | 4 raceways run outdoors; cables authored | PASS (datasheet wet listings: GenSPEED 10, Belden 5200F2) |
| 722.2(B), unplaced | `CD-M-DATA-ENTRY` authors only two end elevations (outdoor entry device through the rim) | gap |
| 722.140(A)(3) Class 2 cable 150 V / 60 degC | no cable authored | not graded |
| Table 722.140(B)(2) PoE bundle ampacity | no bundle or PoE class authored; arithmetic below passes | not graded |
| 722.131(L) dwelling cable types | Cat 6A is general-purpose (CMG/CM) | permitted; limited-use cable of 1/4 in. or more is graded ADVISORY |
| 722.133(C), 722.135(B) no strapping to a raceway | no support is modelled | not graded |
| 722.135(B) / 680.11 pool zone (5 ft) | the spa shell is not an `Equipment`; Catlin has a rough-in only (conditions in `notes/grounding_bonding.md` §10) | gap |
| 722.135(A) broadband cover | no network-powered broadband | N/A |
| Class 4, optical fiber, PLFA, CI | none modelled | read only |

**722.15, the run tags.** `ConduitRun.service` is a single value, so one raceway cannot be both
data and power. `electrical.limited_energy_wiring` grades ADVISORY (a FAIL candidate, never a
permit gate) any data or `power_24` run that names a power circuit; Catlin has none. The check
does not see boxes: a data jack and a receptacle in one box, or power in a patch enclosure,
needs (B) a barrier, (D) power solely to supply the equipment with 1/4 in. between, or (G).

**722.2(B), the wet runs.** Read from `resolve/conduit_reaches.py` (a stretch "open", outdoors
above grade): `CD-M-RSD-INIT` (about 6 in. of stub at the exterior wall), `CD-M-DATA-PORCH` (20
samples = 5 ft), `CD-M-DATA-CAM-PORCH` (26 = 6.5 ft), `CD-M-DATA-CAM-CANOPY` (20 = 5 ft). None runs
in earth, so Table 300.7(A) never reaches data. The cable inside must be marked "wet location"
(722.100(C)) or have a moisture-impervious metal sheath; a raceway does not make it dry.

**PoE arithmetic (Table 722.140(B)(2)).** The informational label example for an 802.3 Class 8
source is 0.433 A per conductor. At 60 degC, 24 AWG carries 0.46 A or more in any bundle up to 91
cables and 23 AWG 0.58 A or more, so a PoE load cannot be limited by the table at Catlin's scale
(about a dozen data runs at the patch panel). Only a bundle of 92 or more 24 AWG cables
(0.40 A) would bind. Two cautions: the table is for 30 degC, so attic and canopy runs above that
take the 310.15(B) correction; and the connector's per-contact limit (informational, 1.0 A for
8P8C at 60 degC) can bind first. The Reolink devices are 802.3af/at (`smart_home_types.py`);
their per-conductor currents are not authored.

**Dwelling cable types (722.131(L), 722.120).** Plenum, riser and general-purpose cable
(CMP, CMR, CMG, CM and the CL2/CL3 equivalents) are permitted in a one- or two-family dwelling
outside the special spaces. Limited-use cable (CMX, CL2X, CL3X) is permitted only under 1/4 in.
diameter (printed 6 mm in (G) and (L), 6.35 mm in Table 722.120's footnote; read 1/4 in.). Cat 6A
is usually 0.30-0.35 in., so it is CMG/CM, not CMX. Comms wire (as opposed to cable) and BMU/BLU
are not permitted. Non-concealed spaces: limited-use is capped at 10 ft exposed.

## Part I General

- **721.50 Class 4 sources.** At most 450 V peak or dc; a transmitter must interrupt on a
  short, line-to-line or ground fault, overcurrent or a control malfunction (listed to UL 1400-1).
  Not used in a house. **721.60** premise-powered broadband sources are limited by Chapter 9
  Table 11(B) up to 60 V dc and listed (a power source listed to 721.30(A), or listed as
  communications equipment for power-limited circuits). Not modelled.
- **722.1** scope; informational: Class 4 is fault-managed (not power-limited).
- **722.2 listing.** (A) Cables in buildings are listed as resistant to the spread of fire and
  suitable for the application (Parts III-IX). (B) In wet locations: listed and marked "wet
  location", or a moisture-impervious metal sheath. Exceptions: optical fiber and cable
  installed to 800.48 need no listing. Engine: graded above; 4 runs PASS on datasheet wet
  listings (GenSPEED 10, Belden 5200F2). 722.131(L) limited-use cable of 1/4 in. or more is
  graded ADVISORY. 722.140(A)(3) and 721.30 are still not graded.
- **722.13 mixing.** Plenum, riser, general-purpose and limited-use limited-energy cables of
  Table 722.13(A) share a raceway, tray, box or enclosure, with the sub-rules below. (B) Two or
  more circuits of one class in one cable. (C) Class 2 may use listed Class 3 cable, or
  dual-listed 3/4. (D) Class 2/3 and communications conductors in one cable, if the cable is
  listed as communications; composite cable is judged by its combustion characteristics.
  (E) Plenum, riser, general-purpose and limited-use cable share an enclosure or raceway;
  trays and cable routing assemblies take all but limited-use. (F) PLFA circuits mix with each
  other, with Class 2 (its insulation at least the PLFA's), Class 3 and comms, not with 640.9(C)
  audio circuits. (G) Outside-plant cable shares manholes. (H) Limited-use and under-carpet cable
  stay out of trays. Table 722.13(A) lists the types by
  grade (P plenum, R riser, general-purpose, X limited-use); engine: not graded, no cable type.
- **722.15 separation** (the full page was read earlier; see `nec-2026-paraphrase.md`). (A) 2 in.
  from power, light, Class 1, non-power-limited fire alarm and medium-power broadband
  conductors and not in their raceway, box or enclosure. Exception: low-power broadband with
  medium-power. Relaxed by (B) a permanent barrier or listed divider; (C) a raceway inside the
  enclosure; (D) power introduced solely to supply the equipment, kept 1/4 in. away, or at 150
  V or less to ground with the limited-energy side Class 1 or CL3/CL3R/CL3P (jacket ends
  separated 1/4 in. or by a nonconductive barrier); (E) a single-opening enclosure entered
  through one fitting with the conductors in flexible tubing; (F) elevator travelling cables
  (620.36) and hoistway raceways; (G) either side in a raceway or in MC, NM, UF cable (AC on the
  power side, TC on the limited-energy side); (H) a firmly fixed nonconductor such as porcelain
  tube or flexible tubing; (I) manholes; (J) cable trays with a solid fixed barrier, or in MC;
  (K) functionally associated circuits installed with Class 1 methods (724.46, unread).
  **Reading:** (G) lifts the 2 in., so NM power and a Cat 6A in one stud bay need no spacing;
  the engine keeps the same-raceway ban (a data and a power circuit in one conduit stays a
  finding) because the model never needs it, and the text on its face is ambiguous there.
- **722.27** no cable operates above its temperature rating. Not graded (attic data runs
  `CD-A-DATA-NE`; the rating is not authored).

## Part II Marking and Part III Wiring methods

- **722.100 marking.** Surface-marked: AWG every 24 in., other markings every 40 in., the type
  letters per Table 722.100(A) (CL2, CL3, CL4, FPL, OFN/OFC, CMUC; with P plenum, R riser, X
  limited-use, Z Class 4 outdoor-only), maker, a temperature rating above 60 degC (60 degC is
  assumed otherwise). Voltage is not marked (exception: multiple listings). Optional marks
  (sunlight resistant, low smoke) allowed; (C) wet-location cable carries the 722.2(B) marking.
  Table 722.100(A): plenum CL2P/CL3P/CL4P/FPLP/OFNP/OFCP; riser CL2R/CL3R/CL4R/FPLR/OFNR/OFCR;
  general-purpose CL2/CL3/CL4/FPL/OFN/OFC (and OFNG/OFCG); limited-use CL2X/CL3X; under-carpet CMUC.
- **722.120 / Table 722.120** applications by cable type: ducts and plenum spaces need plenum
  cable or a metal raceway; vertical runs need riser or plenum cable; one- and two-family
  dwellings and the "other locations" rows take every type except under-carpet (limited-use
  only under 1/4 in. and, in non-concealed spaces, 10 ft exposed); under carpet only CMUC; PLTC
  in trays and industrial only. Engine: not graded.
- **722.121** industrial PLTC; **722.122** and Table 722.122 substitutions: a higher grade
  replaces a lower (CMP anywhere, CMR for CL3R, CL2 may be CMG/CM, CL2X may be CL2/CL3/CMX).

## Part IV Communications and CATV (722.130-722.136)

- **722.130 / Table 722.130** communications, CATV and network-powered broadband applications
  mirror Table 722.120 with comms-specific rows; comms wire is allowed only in metal raceways,
  frames and general-purpose raceways. Hybrid power-and-comms cable shows Y in dwelling risers
  and dwelling "within buildings" rows. Informational: Table 723.20 covers the raceways.
- **722.131** (A) cable types per Table 722.131(A): plenum CMP, CATVP, BLP, OFNP, OFCP; riser
  CMR, CATVR, BMR, BLR, OFNR, OFCR; general-purpose CMG, CM, CATV, BM, BL, OFNG, OFN, OFCG, OFC;
  limited-use CMX, CATVX, BLX; under-carpet CMUC; underground BMU, BLU. (B)-(K) fabricated ducts,
  plenums, risers (D)-(G), trays (H), frames (I), other locations (J: limited-use 10 ft exposed;
  multifamily (K)). **(G) one- and two-family risers** and **(L) dwelling "other" locations**:
  plenum, riser and general-purpose cable, limited-use under 1/4 in., in the listed raceways
  or recognized Chapter 3 raceways. (G)(2) bars CMUC, BMU/BLU, comms wire and hybrid cable in
  dwelling risers (Table 722.130 shows hybrid Y there: the print disagrees with itself; Catlin
  has no hybrid cable); (L)(2) bars BMU/BLU and comms wire; (L)(1) allows hybrid per 722.100.
  Engine: (L) limited-use cable of 1/4 in. or more is graded ADVISORY; the rest not graded.
- **722.132** and Table 722.132: CMR may be CMP; CMG/CM may be CMP or CMR; CMX may be CMP,
  CMR, CMG or CM.
- **722.133(A)** comms and CATV share a raceway or enclosure with Class 2/3 (per Art. 725 Parts I and
  II, 645.6(E)(2)), PLFA, optical fiber, CATV and low-power broadband, but (A)(3) never with
  power, light, Class 1 or non-power-limited fire alarm; Exception 1 is a permanent barrier or
  listed divider, Exception 2 is power solely for the equipment with 1/4 in., Exception 3 is
  elevator travelling cables. **(B)** elsewhere, 2 in. from power; exceptions: a raceway or
  MC/NM/UF/AC on the power side, or the comms in a raceway, or a firmly fixed nonconductor.
  **(C)** raceways are for their purpose: no comms or CATV cable strapped, taped or attached to
  the outside of any raceway as support (exception: overhead drop spans on a mast made for
  it). Engine: not graded, nothing models support. **(D)** Table 722.133(D) coaxial CATV
  substitutions (CATVP for CMP/BLP, and so on).
- **722.134** (low- and medium-power network-powered broadband): same separation as above, 6 mm
  inside outlet boxes; bends not under 10 times the cable diameter; no strapping to a raceway.
- **722.135 underground network-powered broadband** entering a building. (A) Table 722.135(A)
  cover: 18 in. direct burial, 6 in. in RMC/IMC, 12 in. in listed nonmetallic raceways;
  12/6/6 in. below a 2 in. concrete trench; 0 under a building (raceway only); 12/4/4 in.
  under a 4 in. slab extending 6 in. beyond; 12 in. in a dwelling driveway; lesser depth to rise
  at terminations. Cable emerging from the ground is protected from the minimum cover to 8 ft
  above grade, no deeper than 18 in. Exception: a listed fault-protection device on the
  network side. Engine: **N/A**, no network-powered broadband (Catlin's `ED-M-DATA-ENTRY` is
  ordinary comms; Table 300.7(A) does not govern it, 300.1(B)). **(B)** pools: cable under a pool
  or within 5 ft of its inside wall meets the 680.11 limits (see `nec-2026-paraphrase-680.md`).
  Engine: not graded; the spa shell is not modelled. Catlin has a rough-in only; conditions in
  `notes/grounding_bonding.md` §10.
- **722.136** Table 722.136 substitutions for broadband cable (BLP, BLR, BL, BLX).

## Part V Class 2 and Class 3 (722.140)

- **(A)(1)** Class 1 wiring methods may be used for Class 2/3; the 310.15(C)(1) adjustment need
  not apply. **(A)(2)** load-side conductors follow 722.15, 722.140(B) and 723.20; exceptions:
  elevators (620.21), 720.4(A)/720.21/720.22/750.5 methods to extend or replace, bare Class 2
  conductors in a listed intrusion system. **(A)(3)** Class 2 cable: at least 150 V and 60 degC;
  Class 3: 300 V. **(A)(4)** a Class 3 single conductor is listed CL3 and no smaller than 18 AWG.
  Engine: 722.140(A)(3) and 721.30 are still not graded; the `CD-M-RSD-INIT` pair (16 AWG) and the 24 V LED
  runs rest on listed CL2/CL3 cable or Class 1 methods; Class 2 listing of the sources is
  721.30, unread.
- **(B) Power and data.** (1) Power-and-data Class 2/3 over listed cable: the current per
  conductor is limited by the connector (8P8C is 1.0 A at 60 degC, informational), power
  conductors are copper, and 720.30 and Article 725 govern bundling. (2) For 4-pair CL2P/CL2R/
  CL2/CL3-type cable, the source's rated current per conductor is within the table at 30 degC
  (above that, 310.15(B)(1)(1) or Equation 310.15(B)). **Exception:** conductors 24 AWG or
  larger carrying a rated 0.3 A or less need no table. (3) A cable marked "-LP" with a current
  limit is rated to that limit in bundles of up to 192, with the ambient correction, and
  follows its un-suffixed type's substitution hierarchy.

**Table 722.140(B)(2)** *(full table kept local; the values the engine uses are in its source)*

## Parts VI-IX and Article 723 (read only)

- **722.150-722.152 Class 4.** **722.160-722.165 optical fiber.** **722.170-722.172 PLFA.** **722.180-722.182 CI cable.** **723.1-723.2.** **723.20** *(summary kept local)*

## Open

Owner questions and unread items are in `plans/TODO-nec-2026.md`. Article 722
still cites Articles 725 (Parts I-III) and 760, 720.30, 724.46 and 800.44-800.53 by number:
those sections exist in the print and are unread, so `nec.py`'s "725 is gone" means 725.136 only.
