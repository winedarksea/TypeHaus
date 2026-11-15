# Window and door procurement: the chosen lines, frame material, install method

2026-10-21. Design reasoning, not a calc oracle. **The owner's selection (updated 2026-10-25):**

- **Drutex IGLO Energy Alucover** (Polish, aluminium-capped uPVC) for the 11 tilt-turn and
  18 fixed units.
- **Aliplast Max Light Modern** (Polish thermally broken aluminium, tilt-turn) for the three
  operable 14x24s: `WIN-M-KITCH-N`, `WIN-M-KIT-E`, `WIN-M-BATH1-W` (2026-10-31), and the 9 R310
  escape windows (2026-11-13; one fabricator, Słowińscy, STO-M-20). The clear opening is an
  estimate with a supplier gate: [egress_window_review.md](egress_window_review.md).
- **Andersen 400 retired 2026-11-13** (the documented revert for the escape windows).
- **Therma-Tru Smooth-Star full-lite** fiberglass / composite frames / Endura hardware
  for all three French pairs; an opaque **Therma-Tru
  Smooth-Star** for `D-M-ENTRY`; a commodity **Masonite** insulated steel outswing for
  `D-G-SERVICE`; a Clopay Classic Steel sectional for `D-G-OVERHEAD`.

Black outside, white inside throughout ([exterior_darks.md](exterior_darks.md), 2026-11-07;
the Clopay stays Charcoal until a dealer confirms Black at R-12.9). The products are in the model
(`plan/opening_products.py`, `plan/window_types.py`, `plan/door_types.py`), each type
carrying its NFRC CPD row. **Every NFRC number below was read from the CPD itself
(search.nfrc.org), not from a brochure or a Phius page.** What is still claimed rather than
in hand is listed in §2.6.

The schedule is 41 units: 23 tilt-turn (12 Max Light), 0 casements, 18 fixed (4 of them the
`-HP` plant-room units); 23 operable. 11 are tempered. Suppliers: Drutex 29, Max Light 12, both
Polish.

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
RC II, K_zt 1, K_d 0.85. The mean roof height is 25.5 ft, so q_h = 19.25 psf. The C&C zone
width is a = 3.6 ft (0.1 × 36').

| Unit area | Zone 4 suction, ASD | Zone 5 suction, ASD | Positive, ASD |
|---|---|---|---|
| ≤ 10 sf (every unit up to 30×48) | 14.8 psf | **18.2 psf** | 13.6 psf |
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
- **Egress at 27½" (2026-11-13).** The 27" family is the full 27½" jack-to-jack clear (one stud
  broken). The 9 escape units are Max Light tilt-turns: a 26.21" unit, **estimated** 20.15" clear
  (0.15" margin), a supplier gate (§2.6 item 12). See [egress_window_review.md](egress_window_review.md).
- **Dark frames.** On Alucover the black (RAL 9017 matt) is powder-coated aluminium, so no dark uPVC sees the
  sun on any face (§3's preferred material). Max Light is powder-coated aluminium (the
  Andersen vinyl frame retired 2026-11-13). Smooth-Star doors are painted fiberglass.
- **14" units (2026-10-31).** Cascadia's outswing awning starts at 20" wide and its casement
  at 18 3/4". The three operable 14x24s are **Max Light tilt-turns**: at a 12.71" frame a
  Drutex operable lite (125 mm a side) leaves ~0.40 sf of glass, Max Light (70 mm) ~0.86 sf,
  about the Drutex fixed unit's 0.80. Two Polish fabricators hold NFRC rows for it (§2.2).
- **Slim-line survey (2026-10-31, NFRC CPD read directly).** Aluprof MB-Slimline and MB-79N
  CSF: no NFRC listing found (CSF is a UK outward system, 60.5 mm operable sightline).
  Drutex's slim lines buy no glass: IGLO EDGE 114 mm frame + sash (U 0.18), IGLO LIGHT 108 mm
  (U 0.21), SL 38 U 0.27 triple, MB-79N/86N SI U 0.22. The 2026-10-21 gate on Aluprof/Aliplast
  was NFRC, which fabricators (not the system house) hold.

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
| **Tilt-turn egress — selected (2026-11-13)** | Aliplast Max Light Modern (Słowińscy) | STO-M-20 | 0.20 | 0.40 | 0.58 | thermally broken alu, 75 mm; 35 + 35 mm face | clear opening estimated; supplier gate (§2.6) |
| Egress casement — retired 2026-11-13 (revert) | Andersen 400 (triple AND-N-1-04162 0.20/0.40/0.51; HeatLock double AND-N-1-03559 0.24/0.31/0.53) | AND-N-1 | — | — | — | wood/vinyl | revert on BED1/2, SUITE1/2 only |
| Casement (no 27" egress) | Cascadia outswing | CWL-K-21-00079 | 0.17 | 0.29 | 0.37 | fiberglass | fails 20" |
| **Tilt-turn 14" — selected** | Aliplast Max Light Modern (Słowińscy) | STO-M-20 | 0.20 | 0.40 | 0.58 | thermally broken alu, 75 mm; 35 + 35 mm face | CR 69; quote |
| Tilt-turn 14" — alternate fabricator | Aliplast Max Light Modern (Plastixal) | PLX-K-17 | 0.20 | 0.40 | 0.58 | as above | CR 66; not taken: its low-U row is SN63HT solar-control (SHGC 0.22), 2026-11-13 |
| Tilt-only 14" — retired 2026-10-31 | Drutex Alucover | DRU-K-26-00001 | 0.18 | 0.24 | 0.35 | uPVC + alu cap | 125 mm operable sightline |

**High-gain south glass: searched, none taken (2026-11-13, CPD read directly).** Scope was the
summer-shaded main-floor south (`WIN-M-LIV-S1/S2`, `WIN-M-BED-S1/S2`) and the unshaded
second-floor south (`WIN-S-STUDY1/2`, `WIN-S-PLANT1/2/4`). A row had to be in the same line and
frame, U ≤ 0.25, SHGC at least ~0.08 higher, and VT no lower.

- **Drutex tilt-turn, DRU-K-24 (all 10 rows):** the highest SHGC is 0.35 (`-00003`/`-00004`,
  laminated, U 0.20/0.21). The selected `-00001` (0.16/0.33/0.47) is already the high-gain glass;
  the rest are SN63/SKN176 solar-control (0.19-0.21).
- **Drutex fixed, DRU-K-23 (all 10 rows):** the highest is 0.42 at U 0.20 (`-00003`/`-00004`, a
  single CGPrem2). At the plant room's U ≤ 0.14 (`glazing_dew_point`) the only row is the selected
  `-00010` at 0.39.
- **Andersen 400 casement, AND-N-1 (all 4,048 rows):** of the 249 rows at U ≤ 0.25, the highest
  SHGC is 0.48, on the HeatLock **double** LowE(180/i89) (`-03558-00001`: U 0.25 / SHGC 0.48 / VT 0.59;
  the 180 coating is the PassiveSun one). The LowE(180/180) triple is 0.22/0.43/0.52 (+0.03). Only
  the double clears +0.08, and it gives up the triple: ΔU +0.05 on ~20 sf costs about
  0.05 × 7,500 HDD × 24 ≈ 9,000 Btu/sf·yr. Breaking even takes ~1,000 Btu/sf·day on south glass
  (assumed, not oracled) × 212 days × 0.08 ΔSHGC × a **53%** heating-season sunlit fraction.
  `WIN-M-BED-S1/S2` are 51% sunlit at the winter peak and fully shaded by the equinox
  (`plans/pattern_language_review.md` §5), so the swap loses heat.

The current glass is kept, and the TODO item is closed.

NAFS: Drutex holds Florida approvals (FL41835/6/7, AAMA/WDMA/CSA 101/I.S.2/A440-17) for IGLO
5 Classic casement and tilt-turn and IGLO Energy Classic fixed, **nail-fin plus jamb-strap
anchorage** — the fin alone is not the tested anchorage. Cascadia: AW-PG60 casement, awning
and fixed; LC-PG45/CW-PG80 tilt-turn. Every value is over §1's DP 20.

### 2.3 Doors

| Door | Line | CPD | U | SHGC | VT | Notes |
|---|---|---|---|---|---|---|
| `D-M-ENTRY` | Therma-Tru Smooth-Star flush, inswing | THC-M-5-03881 | 0.15 | — | — | opaque; polyurethane core; single-point Sense Pro (was Encode Plus); DS2000; black / white field paint |
| `D-B-SUNKEN`, `D-M-PORCH`, `D-S-BALCONY` | Therma-Tru Smooth-Star full-lite, composite frame / Endura | THC-M-5-04493-00001 | 0.21 | 0.12 | 0.27 | provisional CPD basis; laminated triple and assembled pair NFRC/NAFS label are dealer items |
| `D-G-SERVICE` | MMI Z0364688R stock six-panel insulated steel, 32x80 RH outswing, 6-9/16 composite frame; included fixed composite sill, weatherstrip and NRP hinges; HD Supply 219385, $1,023 listed 2026-10-27 | none | — | — | — | `DT-EXT-SWING32-G`: framed RO 34x81.5; west hinges; black outside/white inside; retain factory sill; see service-door installation note |
| `D-G-OVERHEAD` | Clopay Classic Steel long panel GDU293, R-12.9, Charcoal, 16x7 | none | — | — | — | unconditioned; wind rating for q_h 19.3 psf to confirm |

**French pairs (owner, 2026-10-25).** All three use one glass specification: laminated
low-E triple, special quote, with Therma-Tru impact full-lite as the fallback. No separate
balcony type. The [CPD basis row](https://search.nfrc.org/search/cpd/cpd_search_detail.aspx?cpdnum=THC-M-5-04493-00001),
read 2026-10-25, is full-lite E366/Argon/i89, U 0.21 / SHGC 0.12 / VT 0.27;
it does not certify laminated triple or the assembled pair. U rises from 0.15 and VT drops
from 0.42; the modeled U remains below the MN 0.32 glazed-door limit. Certification requires
the prehung assembly to follow a Therma-Tru product approval and carry its own label.
Alternates to revert to: Cascadia Universal triple fiberglass (U 0.15 / SHGC 0.33 / VT 0.42;
pair label also unresolved), or imported European uPVC such as Drutex DRU-K-20 (~U 0.17,
foil-black), potentially shipped with the windows.

**Hardware.** All three pairs use Endura PanoLock+ with Schlage BE365 keypad deadbolt and
passage lever, double-bored at 5-1/2 inches. The deadbolt drives the tapered top and bottom
bolts; the lever drives only the latch, so the deadbolt-free FE595 cannot engage PanoLock+
and was dropped. Confirm BE365 compatibility and stile width ≥ 4 inches with the prehanger.
The Ultimate Flip-Lever Astragal's single lever drives both passive-leaf flush bolts.
The preferred sill is Endura Z-Series Adjustable Inswing (ZAI); the owner expects
compatibility, and the installed section and assembled-system approval remain pending.
Ask for a complete Therma-Tru Tru-Defense-eligible pair as a priced fallback, identifying
whether the requested glazing and hardware are available and any substitutions required.

**The front door is opaque (owner, 2026-10-21, later).** The first pass hung a Cascadia full
lite at `D-M-ENTRY` because the Cascadia line carries no opaque infill. The owner wants a
sturdy, well-insulated, solid door: a small lite at most. Smooth-Star is the commodity
fiberglass slab with a foam core and a 1 1/4" engineered lock stile, and Twin Cities stock.
The 2026-10-25 owner selection is single-point Encode Plus BE499WB (Sense Pro BE889WB since
2026-10-30, `smart_home.md`) plus Century / Latitude
passage lever, DS2000 viewer, composite frame and strike reinforcement. Field paint is
black exterior (matched to a Metal Sales Matte Black (106) chip) / white interior; factory
black is a quote alternate. All four house
exterior swings get doubled packs, solid hardware backing, composite strike/keep shims
and local ccSPF; see `exterior_door_hardening.md` for installation and open dealer items. Its flush NFRC row matches the Cascadia U 0.15, so heating is
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
| WT-1424-TT(-T) | 2+1 | Max Light tilt-turn | 14x24 → 12.71" frame | STO-M-20 | 0.20/0.40/0.58 | 75 mm |
| WT-1424-FIX(-T) | 7+3 | Drutex fixed | 14x24 → 13½x23½ | DRU-K-23-00001 | 0.15/0.39/0.57 | 93 mm |
| WT-2736-FIX(-T), WT-2748-FIX-T | 1+1+1 | Drutex fixed | — | DRU-K-23-00001 | 0.15/0.39/0.57 | 93 mm |
| WT-6348-FIX | 1 | Drutex fixed | 63x48 → 62½x47½ | DRU-K-23-00001 | 0.15/0.39/0.57 | 93 mm |
| WT-2736-TT, WT-2748-TT(-T), WT-3048-TT(-T) | 4+2+1+1+3 | Drutex tilt-turn | — | DRU-K-24-00001 | 0.16/0.33/0.47 | 93 mm |
| WT-2754-HP, WT-3048-HP | 1+3 | Drutex fixed, laminated | — | DRU-K-23-00010 | 0.14/0.39/0.56 | 93 mm |
| WT-2748(-T), WT-2754, WT-3048 | 2+1+4+2 | Max Light tilt-turn (escape) | 27½x48/54, 30x48 → 26.21/28.71 × 46.805/52.805 | STO-M-20 | 0.20/0.40/0.58 | 75 mm |

Flange: factory nailing fin on all window lines (Max Light: quoted +15%, to confirm).
Colour: black exterior (RAL 9017 Traffic black matt on Drutex and Max Light), white interior.

**Visible faces, modelled (2026-11-07, [section sources](window_profile_measurements.md)).**
Drutex Alucover: **74 mm frame + 50 mm sash** on operable units, 74 mm on fixed units
(70001 / 70013 dealer sections, replacing the 75/125 mm Phius basis). Max Light: 35 + 35 mm.
Andersen 400 (retired 2026-11-13): **1⅝" sash; exposed frame 9/16" jamb, 3/4" head, 13/16" sill**, from its
architectural CAD. The three frame faces are separately authored; the interior stool rail
is independently 1⅛". Confirm the selected triple-pane section before manufacture.

### 2.5 Landed price

**One factory-market signal** (kb.pl, Polish list, net of VAT, undated): IGLO Energy white,
triple, single-sash tilt-turn, 975 x 1090 mm, **713 zł**, about $195. Alucover, black, a nail
fin, export crating, freight, duty and a US dealer all sit on top of that, and none of them
is published, so it bounds the base product rather than re-bases a row. No US price is
published for any of the three lines; every row in `prices.toml` stays a band with a named product.
Drutex sells through dealers (DAKAM, Franklin Park IL, 16 years as a partner; Home One,
Chicago), and the Chicago dealer is the freight point. The Polish landed cost adds ocean
freight, crating, US duty on HTS 3925.20 plus the 2025 EU tariff, and 10–14 weeks. Therma-Tru is a Twin Cities dealer-stocked line; the
composite-frame Endura pair and laminated triple still need a special quote and lead time.
**One quote per supplier
for the actual schedule** is the next step; price for performance cannot be ranked closer
than ±20% without it.

### 2.6 Claimed, not yet in hand

1. Drutex: written confirmation that Alucover ships with a nail fin, and the NAFS report and
   DP for **Alucover** itself (the Florida approvals cover IGLO 5 / Energy Classic).
2. Max Light minimum tilt-turn sash at the **12.71" modeled outie frame** (the Drutex
   tilt-only it replaced had the same open item). Confirm every modeled frame size with
   the supplier.
3. Stool height (§6). [Public Alucover sections](window_profile_measurements.md#1-drutex-iglo-energy-alucover--dakam)
   now dimension the inward sash bottom 38 mm above the bare PVC frame bottom, and
   adaptors 54123/54113 at 30 mm (50114 at 50 mm). A retained 30 mm adaptor puts the sash
   bottom 68 mm above its bottom, before clearance. The model uses a **bare-frame unit**,
   so `inward_sash_bottom_height=38 mm` now limits operable stool tops. (Superseded the same
   day: operable Alucover units carry the 30 mm adaptor, and since 2026-11-15 the Max Light
   units carry a provisional 30 mm one too; see §6.)
   DAKAM still confirms the ordered adaptor, unit-height datum and stool-bearing rail;
   include a retained adaptor in the unit envelope before raising the rail. Fixed stools
   retain the explicit provisional 75 mm rail, independently of the 74 mm exterior face.
4. Closed 2026-11-13: Andersen retired (revert only), so the Northeast-only triple, the unpublished
   face split and the Twin Cities dealer are moot.
5. Therma-Tru pair NFRC/NAFS label under its product approval with the specified Endura
   components; laminated triple CPD row and SHGC (0.12 is only the provisional basis row);
   BE365 on PanoLock+'s compatibility list; stile width ≥ 4 inches; installed threshold
   heights at D-B-SUNKEN and D-S-BALCONY, measured from the installed crest rather than
   floor-to-landing drop. Request the composite frame/hinge section, ZAI sill and
   compatible sweep, corner seals, FLA sill receiver and installation details, bearing
   contacts, and written assembled-system compatibility, approval and warranty. Price a
   complete Therma-Tru Tru-Defense-eligible fallback with any glazing or hardware changes.
   Read current nominal and tolerance-adjusted crest heights from the engine-generated
   [catalog height review](french_door_catalog_installation.md#3-height-and-geometry-review);
   confirm them against the actual installed section and landing.
6. Dark-colour warranty by orientation. Get Drutex, Max Light (powder coat) and Therma-Tru finish terms for the selected black exterior in writing.
7. Clopay: Texas TDI approval GDR150 lists Modern Steel residential models 7208/7209,
   non-impact, at **+38/−42 psf**, about twice §1's worst 18.3 psf. The door is now Classic
   Steel GDU293 (2026-10-29): get its own rating. Confirm it is listed and that the listing reaches 16'-0" wide (drawing 104859/105042-B-TDI).
8. 16 CFR 1201 marks on the 11 tempered units (including the Max Light `WIN-M-BATH1-W`) and
   every glazed door (the three French pairs).
9. **Size standardization, priced, not assumed.** Ask each supplier to quote the schedule
   as drawn and with sizes merged (e.g. the 27" heights 36/48/54 onto fewer). Take a merge only
   where the quote shows a real saving. Limits: 27" egress width, the girt-course sill module,
   R303.1 glazing area per room, and the stool heights.
10. **Main-floor security glazing (owner request, 2026-10-26).** Ask Drutex / DAKAM and
    the Max Light fabricator to price an alternate for every main-floor (`WIN-M-*`) window:
    factory-laminated security glass with a clear PVB (polyvinyl butyral) or manufacturer-
    specified security interlayer bonded between the glass plies, incorporated as a
    laminated lite in the insulating glass unit (IGU). Ask
    Cascadia for the same alternate if quoting that line. Confirm availability for each
    scheduled size and operation, added cost per unit and total, lead time, and warranty.
    Request the proposed glass make-up, interlayer product and thickness, and any tested
    forced-entry rating for the complete window assembly; identify ordinary safety
    lamination separately from a security-rated option. Confirm the quoted configuration's
    NFRC U/SHGC/VT, NAFS rating, required safety-glazing marks, sash/hardware weight limits
    and bedroom egress clear opening. This is a quote alternate pending supplier responses
    and owner selection; availability and security performance are not yet confirmed.

11. **Max Light (2026-10-31).** Fabricator Słowińscy (settled 2026-11-13; STO-M-20); its US import
    route; nail fin (Debesto quotes +15%); NAFS DP ≥ 20; the 16 CFR 1201 mark on the `-T` units;
    RAL and gloss match to the Drutex caps; a dimensioned sill section with the adaptor (or
    under-sill trim) that lifts the stool over a 1 1/2" pan back dam, its height and the
    lowest inward sash edge (the model assumes 30 mm, §6). Item 12 adds the escape-unit gate.
12. **Egress gate (a construction hold).** Ask Słowińscy for a **written** net clear opening,
    W × H, for the turn sash at 26.21×46.805, 26.21×52.805 and 28.71×46.805, and the hinge's
    maximum opening angle (none is published; the model's 154 mm / 100 mm deductions are an
    estimate, 0.15" over R310's 20"). Confirm also the NAFS DP ≥ 20 with a nail fin, the 1201
    mark on WIN-S-BED1 (-T), RAL/gloss, and an **exterior screen that releases from inside
    without tools** on all 9 (R310.4; an inward sash cannot take an interior screen):
    retractable or push-out. Fallback and the Andersen revert: [egress_window_review.md](egress_window_review.md).
13. **Dropped (2026-11-13).** One Max Light order for all 41 units: Max Light fixed is best U 0.17
    (STO-M-19), and the plant room needs U ≤ 0.14 (`glazing_dew_point`; Drutex fixed 0.14-0.15).

**Security-glazing sourcing check (2026-10-26).**
[Drutex's glass options](https://www.drutex.eu/en/products/addons/type/3/) explicitly
include **44.4 anti-burglary** glass. Ask for that option's availability in the scheduled
Alucover triple IGUs and its documented EN 356 class.
[Eurostaklo's make-up table](https://www.eurostaklo.hr/en/staklo-lamistal) lists 44.4 as
4 mm glass + 1.52 mm PVB + 4 mm glass, P4A. Treat this as a useful quote reference,
not proof of Drutex's rating or of whole-window forced-entry resistance.
For the Max Light escape units (main-floor `WIN-M-BED-S1/S2` are among them), ask Słowińscy for the
same laminated option combined with triple glazing, and its effect on U/SHGC and sash weight.
(Andersen's laminated-insulating option is moot since the 2026-11-13 retirement.)
A monolithic laminated option is not an insulating-glass substitute.
Glass impact classifications and acoustic results
do not establish a forced-entry rating for the complete window.

**Cost signal, not a project quote.**
[European-window supplier Debesto](https://debesto.com/en-us/blog/european-custom-windows/)
publishes an indicative **+10% of window price for safe glass**. It does not specify a
44.4/P4A security package or establish a Drutex or Max Light surcharge. For illustration,
10% on a $500–$1,000 base unit is $50–$100 extra; that arithmetic is not a supplier quote.
Obtain separate add prices for ordinary safety lamination and the proposed security
lamination, including any hardware, freight and duty changes. No confirmed security
upgrade allowance is entered in the model or prices.

**Sunken-garden/study catalog coordination, 2026-10-26:** use
[french_door_catalog_installation.md](french_door_catalog_installation.md) for the current
component/evidence matrix, separate nominal/unit/RO sizes, adapter F, installed-height
calculations and public-price comparison. No inquiry or order was made. Complete preferred
and Tru-Defense pair prices are not established; replacement-part prices are not whole-unit
quotes. The Endura assembly's exact unit size, installed frame/sweep/pan interfaces,
performance label and warranty remain unconfirmed, and structural connection design is
still required. The two installation TODOs have not been marked complete.

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

- **23 tilt-turn, all inward (0 casements)**: Drutex `WIN-M-KITCH`, `WIN-M-LIV-E1`/`E2`/`S1`/`S2`, `WIN-M-BED-W1`/`W2`,
  `WIN-S-STUDY1`/`2`/`3`, `WIN-A-N2`; Max Light `WIN-M-KITCH-N`, `WIN-M-KIT-E`,
  `WIN-M-BATH1-W` (the powder room's second ventilation path, still tempered).
- **9 egress tilt-turns, Max Light** ([egress_window_review.md](egress_window_review.md)): `WIN-M-BED-S1`/`S2`, `WIN-S-BED1`, `WIN-S-BED2`,
  `WIN-S-HALL-N`, `WIN-S-SUITE1`/`2`, `WIN-A-S-JUL-W`/`E`. Both of each pair go, so a pair
  reads alike.
- **No awnings.** No line surveyed builds an outward awning at 14" (§2.1); the kitchen pair
  went Drutex tilt-only → Max Light tilt-turn on 2026-10-31. Bedroom 3's two 14s stay fixed.
- **Two suppliers on one face.** The south, east and west faces each mix the two products
  (e.g. `WIN-M-BED-S1`/`S2` beside `WIN-M-LIV-S1`/`S2`). §3's colour, gloss and sightline
  match applies between suppliers, not only between materials.
- **Fixed units (18).** Fixed-in-sash matches the operable sightlines on the dark facade.
  Fixed-in-frame is cheaper and has more glass. Pick one rule per elevation. Where a fixed
  unit sits beside a tilt-turn on one face (north: `WIN-A-N1`/`N2`), fixed-in-sash.
- **Juliets** (`WIN-A-S-JUL-W`/`E`) are inward tilt-turns (2026-11-13): the studio's escape opening
  if it becomes a bedroom; a craft room today, so R310 is not graded.
- **R312.2.** The engine grades all 23 operable units: none has a sill under 24" with more
  than 72" below (PASS). **It measures the sill from the storey datum, not the finished
  floor.** The suite's 2'-3½" sill is 26" over its 1½" oak, so it holds. `WIN-A-N2` sits at
  exactly 24" over the attic datum. Confirm against the finished floor; if it lands under
  24", turn mode needs a WOCD (ASTM F2090: a lockable or limiting turn handle).
- **Screens.** An inward sash needs an exterior-mounted screen. It sits in the mount plane,
  so coordinate it with the J-receiver trim at the frame. On the 9 escape units it must release
  from inside without tools (R310.4): retractable or push-out (§2.6 item 12).

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

- **Stool vs inward sweep (2026-11-07).** Alucover operable stools now sit at the measured
  **38 mm above the bare frame bottom**, a 37 mm drop from the previous 75 mm basis.
  Fixed Alucover stools retain the provisional 75 mm rail, preserving the dining counter
  plane. All 12 Max Light units (the 14s and the 9 escape units) carry a **PROVISIONAL 30 mm sill
  adaptor** (2026-11-15, Drutex's 54123 figure): on the bare 35 mm rail the 1" stool stood in
  the pan's 1 1/2" back dam. The stool now sits 65 mm above the rail bottom, about 6 mm clear
  of the dam, and the sash is drawn above the adaptor. It costs the escape units 30 mm of
  estimated clear height (smallest 6.00 sf vs 5.7). Ask Słowińscy for their sill adaptor
  and inward clearance (§2.6 item 11). DAKAM confirms
  the retained adaptor and rail datum; all elevations start at the resolved seated unit,
  not the RO. Where a stool is coordinated with the counter (`WIN-M-LIV-E1`/
  `E2`, and `WIN-M-KITCH` over the counter), turn mode needs a clear counter. Tilt is the
  daily mode there. The Max Light kitchen pair (`WIN-M-KITCH-N`, `WIN-M-KIT-E`, sill 42" over
  the counter and backsplash) turns its sash over the counter too: keep the sill clear of
  appliances and canisters, and fit an exterior screen (inward sash). **Order the pair hinged
  on the far jambs** (`WIN-M-KITCH-N` west, `WIN-M-KIT-E` south): hinged toward the corner,
  the two turned sashes meet at about (34'-7", 34'-7").
- **Window seats.** In `plan/study_nook.py`, the seat top is 19½" and the
  `WIN-S-STUDY1`/`2` sills are 32", so it is clear. The suite desk moved ½" east so
  `WIN-S-SUITE1`'s stool (now ~29" AFF, under the 30" desk top) clears it by ⅛".
- **Shades** (the cellular blinds on `WIN-M-LIV-E1`/`E2`/dining, and any others). The tilt
  sash tips its head ~4–6" into the room. Mount the shades on the sash, or outside-mount
  them above the tilt sweep, never inside-mount in the reveal at the head.
- **Turn is limited to 90°.** The outie frame sits 2¾–6" outboard of the sheathing, so the
  interior reveal is deep. The leaf cannot fold back against the wall, and it stands in the
  room at 90°.

## 7. Egress review

Moved to [egress_window_review.md](egress_window_review.md): the Max Light escape units
(2026-11-13: estimated clear opening, supplier gate, fallback) and, below it, the superseded
Andersen 400 basis (2026-10-23), the documented revert.

## Engine follow-ups (not in this pass; the owner decides)

1. **The tilt-turn elevation glyph is drawn upside down.** `emit/draw/elevation_openings.py`
   draws the tilt hinge at the head, like an awning. A tilt sash hinges at the sill, so the
   apex belongs there. The retype makes this visible on every elevation.
2. **R310 sizing calculation corrected 2026-10-23.** Clear-opening deductions
   read the resolved, orderable unit, and selected products without clear-opening data
   receive no nominal-RO credit. The Max Light escape units use estimated deductions
   ([egress_window_review.md](egress_window_review.md)).
3. **R312.2 measures the sill from the storey datum**, not the finished floor
   (`fall_protection.py`), so a sill can pass at 24" while standing 22½" over an oak floor.

## Sill, track and floor-transition submittals (2026-10-23)

See [doorway_product_sections.md](doorway_product_sections.md) for the manufacturer
sources, verified installation dimensions and supplier questions for Therma-Tru / Endura,
Masonite and Clopay. Door-type `doorway` selections now retain these unresolved variants
in model JSON and schedules. Their sections remain omitted with UNKNOWN findings until
approved; a product-line name is insufficient. Factory sills/seals are included with the
unit. Obtain the flooring manufacturer's matching trims before selecting a documented
Schluter alternative; separately purchased transitions are counted once per installed cut.
