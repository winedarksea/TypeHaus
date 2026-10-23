# Window and door procurement: the chosen lines, frame material, install method

2026-10-21. Design reasoning, not a calc oracle. **The owner's selection (2026-10-21):**

- **Drutex IGLO Energy Alucover** (Polish, aluminium-capped uPVC) for the 11 tilt-turn, 19
  fixed and 2 tilt-only units.
- **Andersen 400 casement** (Bayport, MN) for the 9 R310 escape windows.
- **Cascadia Universal** fiberglass for the three French pairs; an opaque **Therma-Tru
  Smooth-Star** for `D-M-ENTRY`; a commodity **Masonite** insulated steel outswing for
  `D-G-SERVICE`; a Clopay Modern Steel sectional for `D-G-OVERHEAD`.

Black outside, white inside throughout. The products are in the model
(`plan/opening_products.py`, `plan/window_types.py`, `plan/door_types.py`), each type
carrying its NFRC CPD row. **Every NFRC number below was read from the CPD itself
(search.nfrc.org), not from a brochure or a Phius page.** What is still claimed rather than
in hand is listed in §2.6.

The schedule is 41 units: 11 tilt-turn, 9 casement, 2 tilt-only, 19 fixed (4 of them the
`-HP` plant-room units). 11 are tempered.

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

## 2. The lines compared, and the selection

### 2.1 What decided it

- **NFRC CPD listing** is the gate (§1). Of the Polish makers, only **Drutex** lists every
  operation the house needs (tilt-turn, fixed, tilt-only, an outswing line and doors), and it
  is the only one with an **aluminium-capped** uPVC line in the CPD. Oknoplast lists PAVA
  tilt-turn and fixed only (OKN-K-5/-6), with no casement or awning. Eko-Okna's Ideal 4000
  (the Debesto/Aluplast candidate) rates U 0.27–0.28, over the 0.25 target. DAKO lists
  tilt-turn/fixed/awning at U 0.15–0.18, with no aluminium-capped line. Doorwin (Shandong) lists tilt-turn and fixed at
  U 0.17–0.18, but its casement is U 0.37.
- **Egress at 27½" (2026-10-23).** A 27" RO nets a 25⅝" Andersen 400 unit and 19.8"
  clear. The 27" family widened to the full 27½" jack-to-jack clear, which seats a 26⅛"
  unit at **20.3" clear**; still one stud broken. Calculated; supplier confirmation
  outstanding. See §7.
- **Dark frames.** On Alucover the black is powder-coated aluminium, so no dark uPVC sees the
  sun on any face (§3's preferred material). Andersen 400 is black Perma-Shield vinyl over
  wood. Cascadia is painted fiberglass.
- **14" units.** Cascadia's outswing awning starts at 20" wide and its casement at 18 3/4".
  The two kitchen units go Drutex tilt-only (inward, bottom-hinged), modelled as `awning`.

### 2.2 Windows, by role (whole-window NFRC, triple low-e unless noted)

| Role | Line | CPD | U | SHGC | VT | Frame | Status |
|---|---|---|---|---|---|---|---|
| **Tilt-turn — selected** | Drutex IGLO Energy Alucover | DRU-K-24-00001 | 0.16 | 0.33 | 0.47 | uPVC + alu cap, 93 mm | quote |
| Tilt-turn — alternate | Cascadia Universal inswing | CWL-K-23-00068 | 0.15 | 0.37 | 0.47 | fiberglass | quote |
| Tilt-turn | Alpen Tyrol | ALP-M-17-00509 | 0.15 | 0.39 | 0.48 | uPVC/foam | black ext unconfirmed |
| Tilt-turn | Oknoplast PAVA | OKN-K-5 | 0.16 best | 0.25 | 0.43 | uPVC, 82 mm | no casement/awning in CPD |
| Tilt-turn | Doorwin 86 | DRN-M-1 | 0.18 best | 0.19 | 0.36 | uPVC | casement U 0.37 |
| **Fixed — selected** | Drutex Alucover | DRU-K-23-00001 | 0.15 | 0.39 | 0.57 | as above | quote |
| **Fixed `-HP` — selected** | Drutex Alucover, laminated inner | DRU-K-23-00010 | 0.14 | 0.39 | 0.56 | as above | quote |
| Fixed — alternate | Cascadia exterior-glazed | CWL-K-25-00118 | 0.14 | 0.43 | 0.55 | fiberglass | quote |
| **Egress casement — selected** | Andersen 400 | AND-N-1-04162 | 0.20 | 0.40 | 0.51 | wood/vinyl | triple is Northeast-only; dealer to confirm |
| Egress casement — fallback | Andersen 400 HeatLock double | AND-N-1-03559 | 0.24 | 0.31 | 0.53 | wood/vinyl | stocked |
| Casement (no 27" egress) | Cascadia outswing | CWL-K-21-00079 | 0.17 | 0.29 | 0.37 | fiberglass | fails 20" |
| **Tilt-only 14" — selected** | Drutex Alucover | DRU-K-26-00001 | 0.18 | 0.24 | 0.35 | as above | minimum sash to confirm |

NAFS: Drutex holds Florida approvals (FL41835/6/7, AAMA/WDMA/CSA 101/I.S.2/A440-17) for IGLO
5 Classic casement and tilt-turn and IGLO Energy Classic fixed, **nail-fin plus jamb-strap
anchorage** — the fin alone is not the tested anchorage. Cascadia: AW-PG60 casement, awning
and fixed; LC-PG45/CW-PG80 tilt-turn. Every value is over §1's DP 20.

### 2.3 Doors

| Door | Line | CPD | U | SHGC | VT | Notes |
|---|---|---|---|---|---|---|
| `D-M-ENTRY` | Therma-Tru Smooth-Star flush, inswing | THC-M-5-03881 | 0.15 | — | — | opaque; polyurethane core; multipoint lock |
| `D-B-PATIO`, `D-M-BALC`, `D-S-DECK-E` | Cascadia Universal, double | -00344 in / -00415 out | 0.15 | 0.33 | 0.42 | inswing double R-PG35; **CPD lists the single leaf**, the pair's label is a quote item |
| `D-G-SERVICE` | Masonite Premium Flush steel, outswing (HD 74213) | none | — | — | — | own type `DT-EXT-SWING36-G`; insulated core, unconditioned garage |
| `D-G-OVERHEAD` | Clopay Modern Steel, Intellicore R-18.4, Black, 16x7 | none | — | — | — | unconditioned; wind rating for q_h 19.3 psf to confirm |

Therma-Tru's best full-lite (THC-M-5-04493) is U 0.21 at VT 0.27; Drutex's uPVC balcony door
(DRU-K-20) is ~0.17 but foil-black and not fiberglass. Both are the alternates for the pairs.

**The front door is opaque (owner, 2026-10-21, later).** The first pass hung a Cascadia full
lite at `D-M-ENTRY` because the Cascadia line carries no opaque infill. The owner wants a
sturdy, well-insulated, solid door: a small lite at most. Smooth-Star is the commodity
fiberglass slab with a foam core and a 1 1/4" engineered lock stile, a multipoint lock
option, and Twin Cities stock. Its flush NFRC row matches the Cascadia U 0.15, so heating is
unchanged, and it drops 6.6 ft² of north A·SHGC (`solar_gain_basis.md`). A small lite is a
catalog option; if one is taken, it is tempered (R308.4.1) and needs its own CPD row.
Drutex's MB-86N SI aluminium entry door (Ud 0.83 W/m²K, about U 0.15) would ship with the
windows. It is the alternate, but has no NFRC row and no US price, and an aluminium leaf in
Climate Zone 6 is a quote item.

**The garage service door is a commodity steel door.** The garage is unconditioned and only
rarely heated, so it needs an insulated core and nothing more: no NFRC row is needed or
claimed.

### 2.4 Per-type spec (in the model)

| Type | n | Line | RO → unit | CPD | U/SHGC/VT | Depth |
|---|---|---|---|---|---|---|
| WT-1424 | 2 | Drutex tilt-only | 14x24 → 13½x23½ | DRU-K-26-00001 | 0.18/0.24/0.35 | 93 mm |
| WT-1424-FIX(-T) | 7+4 | Drutex fixed | 14x24 → 13½x23½ | DRU-K-23-00001 | 0.15/0.39/0.57 | 93 mm |
| WT-2736-FIX(-T), WT-2748-FIX-T | 1+1+1 | Drutex fixed | — | DRU-K-23-00001 | 0.15/0.39/0.57 | 93 mm |
| WT-6348-FIX | 1 | Drutex fixed | 63x48 → 62½x47½ | DRU-K-23-00001 | 0.15/0.39/0.57 | 93 mm |
| WT-2736-TT, WT-2748-TT(-T), WT-3048-TT(-T) | 4+2+1+1+3 | Drutex tilt-turn | — | DRU-K-24-00001 | 0.16/0.33/0.47 | 93 mm |
| WT-2754-HP, WT-3048-HP | 1+3 | Drutex fixed, laminated | — | DRU-K-23-00010 | 0.14/0.39/0.56 | 93 mm |
| WT-2748(-T), WT-2754, WT-3048 | 2+1+4+2 | Andersen 400 casement | — | AND-N-1-04162 | 0.20/0.40/0.51 | 3¼" (preset; confirm) |

Flange: factory nailing fin on all three window lines. Colour: black exterior, white interior.

### 2.5 Landed price

**One factory-market signal** (kb.pl, Polish list, net of VAT, undated): IGLO Energy white,
triple, single-sash tilt-turn, 975 x 1090 mm, **713 zł**, about $195. Alucover, black, a nail
fin, export crating, freight, duty and a US dealer all sit on top of that, and none of them
is published, so it bounds the base product rather than re-bases a row. No US price is
published for any of the three lines; every row in `prices.toml` stays a band with a named product.
Drutex sells through dealers (DAKAM, Franklin Park IL, 16 years as a partner; Home One,
Chicago), and the Chicago dealer is the freight point. The Polish landed cost adds ocean
freight, crating, US duty on HTS 3925.20 plus the 2025 EU tariff, and 10–14 weeks. Cascadia
trucks from Langley BC with no duty under USMCA. Andersen is local. **One quote per supplier
for the actual schedule** is the next step; price for performance cannot be ranked closer
than ±20% without it.

### 2.6 Claimed, not yet in hand

1. Drutex: written confirmation that Alucover ships with a nail fin, and the NAFS report and
   DP for **Alucover** itself (the Florida approvals cover IGLO 5 / Energy Classic).
2. Drutex tilt-only minimum sash at the **12.71" modeled outie frame**; if not buildable,
   WT-1424 needs a different product or operation. The previous 13.5" assumption omitted
   the buck and membrane allowances. Confirm every modeled frame size with the supplier.
3. Stool height (§6). **The frame half is confirmed**: Drutex's frame face is 75 mm = 2.95"
   (Phius W-102033, IGLO Energy Classic, fixed-section frame height), which is the 2.953" the
   stools already assume, so no fixed unit moves. Two terms are unpublished: the 5-chamber
   PVC sill adaptor Drutex ships under the frame as standard (Alucover data; IGLO Energy
   brochure, "5-Kammer-Fensterbankleiste"), which RAISES the rail, and the inward sash's
   overlap past the frame, which the turn sweep needs the stool to clear. Ask for both
   on the section drawing; re-strike `plan/window_stools.py` and the main.py east-wall note
   to rail = 75 mm + adaptor, less the overlap on the tilt-turns.
4. Andersen 400 triple-pane availability through a Twin Cities dealer; basic-unit frame depth.
5. Cascadia: NFRC label for the double door — **confirmed absent from the CPD** (none of the
   1,355 CWL-K-27 rows is a pair), so it is a certification question for Cascadia, not a
   lookup; threshold height at D-B-PATIO's 7¼" step and D-S-DECK-E's 0.58".
6. Dark-colour warranty by orientation. Andersen 400 publishes 20 years glass / 10 years
   non-glass, transferable, not prorated (400 Series product guide), with no black-specific
   term. Drutex and Cascadia publish no finish term (a Cascadia user reports a factory paint
   that touches up, less hard than PVDF). Ask all three in writing.
7. Clopay: Texas TDI approval GDR150 lists Modern Steel residential models 7208/7209,
   non-impact, at **+38/−42 psf**, about twice §1's worst 18.3 psf. Confirm GDU011 is one of
   them and that the listing reaches 16'-0" wide (drawing 104859/105042-B-TDI).
8. 16 CFR 1201 marks on the 11 tempered units and every glazed door (the three French pairs).
9. **Size standardization, priced, not assumed.** Ask each supplier to quote the schedule
   as drawn and with sizes merged (e.g. the 27" heights 36/48/54 onto fewer). Take a merge only
   where the quote shows a real saving. Limits: 27" egress width, the girt-course sill module,
   R303.1 glazing area per room, and the stool heights.

## 3. Frame material by orientation

**Resolved (2026-10-21): Drutex Alucover is aluminium-clad uPVC on every face**, flanged
and NFRC-listed (§2). The cap carries the dark colour, so the uPVC never sees it. The
fallback below stays as the record of why.

**Preferred: aluminium-clad uPVC on every face**, if a flanged NFRC/NAFS option exists.

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
- **9 egress casements, Andersen 400** (§7): `WIN-M-BED-S1`/`S2`, `WIN-S-BED1`, `WIN-S-BED2`,
  `WIN-S-HALL-N`, `WIN-S-SUITE1`/`2`, `WIN-A-S-JUL-W`/`E`. Both of each pair go, so a pair
  reads alike. Order the egress (widest-opening) hinge, not wash mode.
- **2 kitchen units are Drutex tilt-only** (inward, bottom-hinged). No line surveyed builds an
  outward awning at 14" (§2.1).
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
- **Window seats.** In `plan/study_nook.py`, the seat top is 19½" and the
  `WIN-S-STUDY1`/`2` sills are 32", so it is clear. The suite desk moved ½" east so
  `WIN-S-SUITE1`'s stool (now ~29" AFF, under the 30" desk top) clears it by ⅛".
- **Shades** (the cellular blinds on `WIN-M-LIV-E1`/`E2`/dining, and any others). The tilt
  sash tips its head ~4–6" into the room. Mount the shades on the sash, or outside-mount
  them above the tilt sweep, never inside-mount in the reveal at the head.
- **Turn is limited to 90°.** The outie frame sits 2¾–6" outboard of the sheathing, so the
  interior reveal is deep. The leaf cannot fold back against the wall, and it stands in the
  room at 90°.

## 7. Frame sizing and egress review (2026-10-23)

**Every 27" RO is now 27½", the full jack-to-jack clear of a one-stud break** (30½" bay
less two 1½" jacks, `preferences.toml`). The owner asked for one buck pattern across the
family, so all eighteen former 27" openings widened, not only the seven escape casements.
Centres, studs broken, headers, sills and heads are unchanged; each `from_node` jamb offset
dropped ¼" to hold its centre, and each adjoining braced panel gave up ¼". The perimeter
detail is unchanged: ⅜" buck, 0.020" membrane and ¼" shim gap at each jamb and the head;
the sill consumes about 0.550" (buck + pan fall + 0.060" membrane). Only the unit grows.

The resolved seat now sizes an orderable unit where the type states one
(`WindowType.frame_size_increment` and `minimum_rough_opening_allowance`). The four
Andersen types carry ⅛" and ½": the unit must clear both the shim gaps and Andersen's
RO = unit + ½" inside the **flashed** opening, rounds **down** to ⅛", stays centred between
the jambs and bears on the pan; the head takes the remaining slack. Schedule, IFC, renders
and R310 all read that one seat. Drutex types state no step (made to the mm) and keep the
continuous envelope.

| RO | Modeled unit / frame |
|---|---|
| 14×24 | 12.710×22.805 (Drutex) |
| 27½×36 | 26.210×34.805 (Drutex) |
| 27½×48 | 26.210×46.805 (Drutex) · **26⅛×46½ (Andersen)** |
| 27½×54 | 26.210×52.805 (Drutex) · **26⅛×52½ (Andersen)** |
| 30×48 | 28.710×46.805 (Drutex) · **28⅝×46½ (Andersen)** |
| 63×48 | 61.710×46.805 |

The two garage frames are about 13.460×23.509". **WIN-B-SAUNA is unresolved:** its
manual court-opening detail supplies no modeled seat. Its schematic placeholder is not a
frame dimension; A-602 prints UNRESOLVED and IFC leaves overall frame dimensions unset.
Add a dimensioned buck/pan/seat detail before ordering it. Stool heights still require the
supplier's sill adaptor and sash-overlap section (§2.6).

For the selected Andersen 400 widest-opening hinge, the engine applies the published
**unit-width deduction of 5.81"** to the resolved unit. The height deduction is 4.43" for
WT-3048's unit (inside 28⅜"–31½" × 40 13/16"–48") and 4.85" for the narrower types. Exact
published clear openings remain supported for other catalog products. A selected product
without clear-opening data (including the Drutex tilt-turns) receives no nominal-RO credit.

| Escape windows | RO | Unit | Calculated clear | Area |
|---|---|---|---|---|
| WIN-M-BED-S1/S2 | 30×48 | 28⅝×46½ | 22.815×42.070 | 6.67 sf |
| WIN-S-BED1, BED2, HALL-N | 27½×48 | 26⅛×46½ | 20.315×41.650 | 5.88 sf |
| WIN-S-SUITE1/2, WIN-A-S-JUL-W/E | 27½×54 | 26⅛×52½ | 20.315×47.650 | 6.72 sf |

All six sleeping rooms pass `code.R310_egress` (20" × 24", 5.7 sf). This is **calculated
compliance with procurement confirmation outstanding.** Before ordering, obtain written
confirmation of the exact units, widest-opening hinges, glazing, operator and any opening-
control device, the actual net clear openings, and the installation requirements; the
installer must confirm the finished flashed openings and attachment detail accept those
units. If confirmation fails, the thinner-buck path below is the fallback to revisit.
The 63" dining picture window stays an owner-approved exception with its own LVL header
(`preferences.toml`, `notes/dining_window_header.md`).

Sources checked 2026-10-23:
[Andersen 400 opening specifications](https://www.andersenwindows.com/-/media/Project/AndersenCorporation/AndersenWindows/AndersenWindows/files/technical-docs/area-and-opening-specifications/area-openingspecifications-windows--400series-casement.pdf),
[Minnesota R310](https://www.revisor.mn.gov/rules/1309.0310/).

### Fallback, not taken: a thinner buck at the 27" RO (investigated 2026-10-23)

Superseded by the 27½" RO above; kept in case supplier confirmation fails.

The narrowest product path found is the already-selected Andersen 400 casement with its
widest-clear-opening hinge, paired with a thinner buck detail. Andersen's 2025–26 guide
allows custom widths in ⅛" increments, gives clear width as unit width minus 5.81", and
specifies minimum RO as unit width plus ½". At the current 25.710" modeled frame envelope,
the largest size that rounds down is 25⅝", for 19.815" clear. The next size, 25⅞", gives
20.065" clear and fits a 27" RO only if the combined buck and membrane thickness is at most
⅝", preserving Andersen's ½" installation allowance. With the 0.020" membrane each side,
that means buck thickness no greater than about 9/32" per jamb; the current buck is ⅜".

This is a concrete supplier/installer question, not an approved detail. Confirm that a
25⅞" unit is available with the specified hinge and glass, that its actual egress opening
meets R310 with the selected operator and any opening-control device, and that a 9/32" buck
can be securely fastened and flashed in the outie wall. The 27×48 units would then have
about 20.065" × 41.955" clear (5.84 sf); the 27×54 units about 20.065" × 47.955" (6.68 sf).
The existing 30×48 pair remains ample. The check must use the supplier's confirmed ordered
dimensions, not these screening calculations.

No second catalog product was verified to fit the present 27" RO/frame envelope and
provide the required clear width. Andersen 100 Series' published widest-opening formula
loses 7.790" from unit width; it does not help at this size. Do not treat fixed jamb width
as opening width: the sash swings outside, but the jambs stay in the passage. Andersen's
published 400-series clear-opening formula already captures that distinction. The adopted
2020 Minnesota Residential Code (2018 IRC base) requires a 20" net clear width, 24" height,
the applicable minimum area, and dimensions achieved by normal operation from inside; the
Minnesota amendments do not change R310.2.1.

Sources checked 2026-10-23:
[Andersen 400 opening specifications](https://www.andersenwindows.com/-/media/Project/AndersenCorporation/AndersenWindows/AndersenWindows/files/technical-docs/area-and-opening-specifications/area-openingspecifications-windows--400series-casement.pdf),
[Andersen 100 opening specifications](https://www.andersenwindows.com/-/media/Project/AndersenCorporation/AndersenWindows/AndersenWindows/files/technical-docs/area-and-opening-specifications/area-openingspecifications-windows--100series-casement.pdf),
[Minnesota R310](https://www.revisor.mn.gov/rules/1309.0310/).

## Engine follow-ups (not in this pass; the owner decides)

1. **The tilt-turn elevation glyph is drawn upside down.** `emit/draw/elevation_openings.py`
   draws the tilt hinge at the head, like an awning. A tilt sash hinges at the sill, so the
   apex belongs there. The retype makes this visible on every elevation.
2. **R310 sizing calculation corrected 2026-10-23.** Andersen clear-opening deductions
   read the resolved, orderable unit, and selected products without clear-opening data
   receive no nominal-RO credit. The seven narrow escape windows clear at 27½" ROs (§7).
3. **R312.2 measures the sill from the storey datum**, not the finished floor
   (`fall_protection.py`), so a sill can pass at 24" while standing 22½" over an oak floor.

## Sill, track and floor-transition submittals (2026-10-23)

See [doorway_product_sections.md](doorway_product_sections.md) for the manufacturer
sources, verified installation dimensions and supplier questions for Therma-Tru, Cascadia,
Masonite and Clopay. Door-type `doorway` selections now retain these unresolved variants
in model JSON and schedules. Their sections remain omitted with UNKNOWN findings until
approved; a product-line name is insufficient. Factory sills/seals are included with the
unit. Obtain the flooring manufacturer's matching trims before selecting a documented
Schluter alternative; separately purchased transitions are counted once per installed cut.
