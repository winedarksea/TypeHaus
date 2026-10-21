# Window procurement: imported tilt-turn, frame material, install method

2026-10-21. Design reasoning, not a calc oracle. The owner is pricing imported European
windows (Poland or China). 11 operable units are tilt-turn (`WT-*-TT`). The **9 windows
bedrooms rely on for R310 escape stay US outward casements** (§7), and the two 14" kitchen
awnings (`WIN-M-KITCH-N`, `WIN-M-KIT-E`) stay outward awnings, since a Euro sightline leaves
too little glass at 14". Those 11 outward units are a second, US supplier. The catalog presets keep
U 0.25 / SHGC 0.35 / VT 0.5 / 3.25" depth. **No performance is claimed until a label is
in hand.**

The schedule is 41 units: 11 tilt-turn, 9 casement, 2 awning, 19 fixed (4 of them the `-HP`
plant-room units). 11 are tempered.

**The import risk is the code gates, more than the U-value.** Without an NFRC label, IECC
R303.1.3 assigns a default U of about 0.55, and the house fails the energy table. Without a
NAFS label, IRC R609 is not met. An EN 12150 stamp is not a 16 CFR 1201 mark.

## 1. Performance spec

This is the requirement. It names no brand.

| Item | Requirement |
|---|---|
| U, SHGC, VT | NFRC-certified, **listed in the NFRC CPD** (verify the license number, not a PDF). U ≤ 0.25 (`preferences.toml window_u`); target ≤ 0.20 triple. SHGC/VT to the schedule |
| Structural | NAFS (AAMA/WDMA/CSA 101/I.S.2/A440) label, **DP ≥ 20 psf** for every unit (table below). LC-PG30 is the common rating and leaves margin |
| Anchorage | DP is valid only for the **anchorage that was tested**. Get the installation instructions the NAFS report was run with |
| Tempered | 16 CFR 1201 / ANSI Z97.1 permanent mark on all 11 tempered units |
| Hardware | Roto, Winkhaus, Maco or Siegenia, with US parts and service. Hinge rated for the triple-IGU sash weight. Replaceable gaskets |
| IGU | Make-up written on the order (lites, gaps, gas, coatings, spacer) so a US shop can remake a broken unit |
| Aluminium | Thermally broken frame. fRsi or a condensation-resistance figure at the −15 °F design temperature |
| Colour | Dark-colour warranty stated **by orientation**, for uPVC foil and for aluminium powder coat |

**Design pressure.** Computed with `typehaus/wind.py` on catlin's basis: V_ult 115, Exp B,
RC II, K_zt 1, K_d 0.85. The mean roof height is 25.6 ft, so q_h = 19.27 psf. The C&C zone
width is a = 3.6 ft (0.1 × 36').

| Unit area | Zone 4 suction, ASD | Zone 5 suction, ASD | Positive, ASD |
|---|---|---|---|
| ≤ 10 sf (every unit up to 30×48) | 14.8 psf | **18.3 psf** | 13.6 psf |
| 21 sf (`WT-6348-FIX`) | 14.1 psf | 17.1 psf | 13.2 psf |

Zone 5 governs any unit within 3.6 ft of a corner. Order every unit at one rating, DP ≥ 20.

## 2. Sourcing matrix

Every row is **claimed** until it is confirmed in the NFRC CPD and against a NAFS test
report.

| Supplier / line | Material | Flange | NFRC | NAFS / DP | Depth | Sightline | Alu cap | Status |
|---|---|---|---|---|---|---|---|---|
| Oknoplast US PAVA | uPVC | steel-reinforced nailing flange offered | claimed | claimed, DP 30–80 | 3¼" | ~4 5/16"/side | ask | claimed; U 0.14–0.26 |
| Oknoplast US PIXEL | uPVC | ask | ask | ask | ask | narrower than PAVA | ask | unknown |
| Aluplast Ideal 4000 (Debesto) | uPVC | ask (add-on?) | forum post only | ask | ask | ask | ask | unverified |
| Aluplast Energeto 8000 (Debesto) | uPVC, bonded | ask | ask | ask | ask | ask | ask | PHI certificate expired 2025-12-31 |
| Aluplast AluSkin (Debesto) | alu-clad uPVC | ask | ask | ask | ask | ask | **yes** | the preferred material, if it is labelled |
| Aluprof MB-86 / MB-104 | aluminium, TB | ask | reported none | ask | ask | ask | n/a | reported quotes lacked NFRC |
| Aliplast | aluminium, TB | ask | reported none | ask | ask | ask | n/a | reported quotes lacked NFRC |
| Zola ThermoPlus Clad | alu-clad wood | ask | ask | ask | ask | ask | yes | Phius-listed; check the certificate dates |
| Chinese supplier (generic) | any | ask | **CPD listing only** | test report only | ask | ask | ask | the same gates apply |

**RFQ checklist** (ask every supplier):

1. NFRC CPD product line and license number, and U/SHGC/VT for *these sizes* in the quoted
   glazing.
2. NAFS test report: class, PG/DP, the size tested, and **the anchorage tested** (flange or
   strap).
3. Factory nailing flange, or a field add-on? Is the flange in the NAFS test?
4. Frame depth, frame+sash sightline per side, and the sash overlap past the frame rail
   (§6).
5. **Net clear opening in turn mode** for 27×48, 27×54 and 30×48 (§7).
6. Tempered-lite marking: 16 CFR 1201, not only EN 12150.
7. Hardware brand, US parts distributor, and the hinge load rating at the quoted IGU weight.
8. IGU make-up, written down.
9. Colour: RAL, gloss, foil or powder, the IR-reflective foil option, and the warranty by
   orientation.
10. Exterior screen system for an inward sash.
11. Lead time, crating, freight to St Paul, duty/HTS code, and the breakage/replacement
    terms.

## 3. Frame material by orientation

**Preferred: aluminium-clad uPVC on every face**, if a flanged NFRC/NAFS option exists. The
cap carries the dark colour, so the uPVC never sees it.

**Fallback: full aluminium (thermally broken) on the south face only, uPVC on N/E/W and the
garage.** South is the garden side and gets the most sun, which is where dark uPVC risks
heat distortion. Risks:

| Risk | Mitigation |
|---|---|
| Dark uPVC on the **east and west** still takes morning and afternoon sun | IR-reflective foil, and the maker's written exposure warranty for those faces |
| South vs E/W differ in sightline, depth and gloss, which shows at the corners | Each elevation stays one material, so the change falls on a corner and never mid-face |
| Colour mismatch between two products | Match RAL **and** gloss. Approve a physical sample of each side by side |
| The aluminium system's frame depth differs from 3¼" | South stools re-measure to the new depth (§6) |

North is the street face, where any mismatch reads most. Under the fallback it is uPVC,
the same as east and west.

## 4. Operation

- **11 tilt-turn**: `WIN-M-KITCH`, `WIN-M-LIV-E1`/`E2`/`S1`/`S2`, `WIN-M-BED-W1`/`W2`,
  `WIN-S-STUDY1`/`2`/`3`, `WIN-A-N2`.
- **9 egress casements, US supplier** (§7): `WIN-M-BED-S1`/`S2`, `WIN-S-BED1`, `WIN-S-BED2`,
  `WIN-S-HALL-N`, `WIN-S-SUITE1`/`2`, `WIN-A-S-JUL-W`/`E`. Both of each pair go, so a pair
  reads alike. Order the egress (widest-opening) hinge, not wash mode.
- **2 kitchen awnings stay outward**, from the same US supplier, since few Euro lines make an
  outward awning at 14".
- **Two suppliers on one face.** The south, east and west faces each mix the two products
  (e.g. `WIN-M-BED-S1`/`S2` beside `WIN-M-LIV-S1`/`S2`). §3's colour, gloss and sightline
  match applies between suppliers, not only between materials.
- **Fixed units (19).** Fixed-in-sash matches the operable sightlines on the dark facade.
  Fixed-in-frame is cheaper and has more glass. Pick one rule per elevation. Where a fixed
  unit sits beside a tilt-turn on one face (north: `WIN-A-N1`/`N2`), fixed-in-sash.
- **Juliets** (`WIN-A-S-JUL-W`/`E`) are outward casements: the studio's escape opening.
- **R312.2.** The engine grades all 22 operable units: none has a sill under 24" with more
  than 72" below (PASS). **It measures the sill from the storey datum, not the finished
  floor.** The suite's 2'-3½" sill is 26" over its 1½" oak, so it holds. `WIN-A-N2` sits at
  exactly 24" over the attic datum. Confirm against the finished floor; if it lands under
  24", turn mode needs a WOCD (ASTM F2090: a lockable or limiting turn handle).
- **Screens.** An inward sash needs an exterior-mounted screen. It sits in the mount plane,
  so coordinate it with the J-receiver trim at the frame.

## 5. Install: outie flange vs Euro strap

| | Outie nailing flange (current) | Euro strap mount |
|---|---|---|
| **Water** | Flange laps the fluid-applied membrane on the buck (`opening_flashing_spec.md`). Unsealed sill flange; drained pan | RAL three-layer seal: interior airtight tape, the insulating middle, an exterior vapour-open tape. Needs a separate sill pan or extension |
| **Frame vs the 0–4" foam** | Frame at the girt face: **2¾–6" from the sheathing**, outboard of the foam | Frame inside the foam plane (0–4"), which is the thermally ideal position |
| **Weight** | Setting blocks on the buck's sill course | Setting blocks on the sill course. The buck stays, so no load brackets are needed |
| **Tested anchorage** | The NAFS DP is normally tested with the flange | EU tests (EN 12211) are run with straps. A **NAFS** strap test is rare. Ask |
| **Sequencing** | Bucks → foam → girts → windows, after the foam | Windows and tapes go in before the foam, or straps go through the foam to the buck. Foam against a uPVC frame needs the maker's OK (expansion pressure) |
| **Facade** | Frame flush with the cladding plane; hidden sill trim; **no visible drip** (owner, 2026-10-16) | A frame in the foam plane sits ~2–3" behind the cladding. It needs a **visible exterior sill extension** and reveal trim, which contradicts the 2026-10-16 decision |
| **Engine** | Supported: the mount plane is derived from the outermost furring face | Needs new mount-plane support (an inset from the girt face) |

**The decision gate.** Bucks, jamb posts and ROs are common to both methods, so framing
never waits on this. The decision is needed **before the flashing spec is issued and the
trim kit is ordered**.

**Recommendation: outie flange is the baseline.** Strap mounting wins only if:

- the chosen product is NAFS-rated **only** strap-mounted, or
- the supplier's own THERM data shows a large psi-install gain over the outie position.
  Ask for ψ_install at both positions in the 4" ccSPF wall.

## 6. Interior coordination

- **Stool vs inward sweep.** Stools sit on the frame's lower rail at sill + 2.953"
  (`plan/storeys/main.py`, the 2026-10-02 east-wall note). That is a US-casement rail. An
  inward sash overlaps the frame on the room side, and its bottom edge can sweep below the
  rail top. **Replace 2.953" with the chosen product's rail height, minus the sash overlap**,
  and drop the stools to clear it. Where a stool is flush with the counter (`WIN-M-LIV-E1`/
  `E2`, and `WIN-M-KITCH` over the counter), turn mode needs a clear counter. Tilt is the
  daily mode there.
- **Window seats.** In `plan/bed_reading_corner.py`, the cabinet tops are 1.70" under the
  `WIN-M-BED-W1`/`W2` stools: the sash sweeps over the walnut tops, and anything standing on
  them blocks turn. In `plan/study_nook.py`, the seat top is 19½" and the
  `WIN-S-STUDY1`/`2` sills are 32", so it is clear. The suite desk moved ½" east so
  `WIN-S-SUITE1`'s stool (now ~29" AFF, under the 30" desk top) clears it by ⅛".
- **Shades** (the cellular blinds on `WIN-M-LIV-E1`/`E2`/dining, and any others). The tilt
  sash tips its head ~4–6" into the room. Mount the shades on the sash, or outside-mount
  them above the tilt sweep, never inside-mount in the reveal at the head.
- **Turn is limited to 90°.** The outie frame sits 2¾–6" outboard of the sheathing, so the
  interior reveal is deep. The leaf cannot fold back against the wall, and it stands in the
  room at 90°.

## 7. Egress: the hand check the engine does not do

`code.R310_egress` grades the **nominal size** (`_meets_r310_2_1`), not the net clear opening,
so its PASS is not evidence. The 2020 Minnesota Residential Code keeps R310.2.1 unamended:
**20" clear width, 24" clear height, 5.7 sf**, measured "by the normal operation of the
window from the inside" (St Paul DSI handout, MN DLI fact sheet). The house is above a
grade-floor sill everywhere, so the 5.0 sf row never applies.

**Basis.** A type's width/height is the **rough opening** (it is what
`structural.window_framing_module` grades), so the unit is RO − ½" each way.

- **Tilt-turn** (Oknoplast PAVA, published sightline 4 5/16"/side, frame plus sash):
  clear = unit − 8⅝". Oknoplast says its tilt-turns "can meet egress when properly sized"
  and publishes no clear-opening figure.
- **US casement** (Andersen 400 Series, 2025-26 opening specifications, widest-clear-opening
  hinge): clear width = unit − 5.81"; clear height = unit − 4.43" for widths 28⅜"–31½" and
  heights 40 13/16"–48", otherwise unit − 4.85".

| Room | Escape window | RO | Tilt-turn clear | sf | Casement clear | sf |
|---|---|---|---|---|---|---|
| RM-M-BED | `WIN-M-BED-S1`/`S2` | 30×48 | 20⅞ × 38⅞ | 5.64 ✗ | 23.7 × 43.1 | **7.09** |
| RM-S-BED1 | `WIN-S-BED1` | 27×48 | 17⅞ × 38⅞ | 4.83 ✗ | 20.7 × 42.7 | **6.13** |
| RM-S-BED2 | `WIN-S-BED2` | 27×48 | 17⅞ × 38⅞ | 4.83 ✗ | 20.7 × 42.7 | **6.13** |
| RM-S-BED3 | `WIN-S-HALL-N` | 27×48 | 17⅞ × 38⅞ | 4.83 ✗ | 20.7 × 42.7 | **6.13** |
| RM-S-SUITE | `WIN-S-SUITE1`/`2` | 27×36 (was) | — | — | 20.7 × 30.7 | 4.40 ✗ |
| RM-S-SUITE | `WIN-S-SUITE1`/`2` | **27×54** (now) | 17⅞ × 44⅞ | 5.57 ✗ | 20.7 × 48.7 | **6.99** |
| RM-A-STUDIO | `WIN-A-S-JUL-W`/`E` | 27×54 | 17⅞ × 44⅞ | 5.57 ✗ | 20.7 × 48.7 | **6.99** |

**No tilt-turn on this schedule passes**, the 30×48 included (5.64 against 5.7). A narrower
sash would need ≤ 3½"/side at 27" and the maker's published dimension to count; none is on
offer. The engine's credit of `WIN-M-BED-W1` (27×36) for RM-M-BED is also false. The room
passes on its south pair.

**Resolution (owner, 2026-10-21):**

- The 9 escape windows are US outward casements (§4).
- **The suite fails even as a casement at 27×36**, so both suite windows and `WIN-S-PLANT3`
  beside them grew to **27×54 on a 2'-3½" sill**, head 6'-9½". The width stays 27", the
  bearing wall's one-stud-break size.
  - The sill's girt course lands exactly on the 24" module (NEW-OPENING RULE).
  - The centre is ½" over the 14" units' 4'-6" line.
  - The stool sits at desk height.
- `WIN-S-PLANT3` is a fixed `WT-2754-HP`. The plant room's glass must stay U-0.14
  (`building_science.glazing_dew_point`), and it still passes.

Engine follow-up 2 (below) would let the model carry the net clear and grade it.

## Engine follow-ups (not in this pass; the owner decides)

1. **The tilt-turn elevation glyph is drawn upside down.** `emit/draw/elevation_openings.py`
   draws the tilt hinge at the head, like an awning. A tilt sash hinges at the sill, so the
   apex belongs there. The retype makes this visible on every elevation.
2. **R310 credits the nominal size.** Add an optional `WindowType.net_clear_width/height`,
   and have `_meets_r310_2_1` use them when they are authored. Then §7 becomes a graded
   check rather than this table.
3. **R312.2 measures the sill from the storey datum**, not the finished floor
   (`fall_protection.py`), so a sill can pass at 24" while standing 22½" over an oak floor.
