# Patio and study French pairs — catalog coordination

Owner scope, 2026-10-26: standard rainproofing, catalog parts and ordinary field
fitting; no inquiries, custom metal fabrication or purchases. Keep the nominal
60 × 80 pairs and their centerlines. Exterior finish is composite/PVC/aluminum,
with no exposed wood. Main-floor door installations and WIN-B-SAUNA are unchanged.

**Status: design coordination, NOT construction-ready.** The exterior boundaries,
formed patio seat, catalog sill outline, approach boards, support envelopes and
flashing-end envelopes are modeled. Member feasibility and installed-height checks
are calculated. Root connections, concrete bar development, cross-bearer bearing and
several installed product interfaces remain UNKNOWN. Do not close these as purchase-only
questions: the two installation TODOs remain open until these design issues close.

## 1. Catalog assembly and evidence

| Part / interface | Selection and published evidence | What is not established |
| --- | --- | --- |
| Leaves | Therma-Tru Smooth-Star full-lite, nominal pair 60 × 80 | Laminated triple, exact assembled pair NFRC/NAFS and performance label remain unconfirmed; the existing U/SHGC/VT row is provisional |
| Frame | Therma-Tru composite 4-9/16 inch jamb; 2026 Comp 6.4 | Factory machining, hinge axis and hinge locations of an assembled Endura pair |
| Returns / casing | Composite exterior returns, 3/4 inch coordination thickness; Therma-Tru 3-1/2 inch flat composite casing | The deep returns are board envelopes, not proof that a single stock jamb extension reaches their full depth; exact extension SKU and permissible dark finish still need documentation |
| Sill | Endura ZAI4565FN, dimensioned 4-9/16 inch width and 1-3/8 inch rear-fin height; digitized exterior outline | Adjustment limits, actual installed cap setting and bearing contacts; the drawing does not dimension the highest cap outline |
| Sweep / pads | Endura DBK-R double-bulb kerfed bottom and compatible corner-pad family are catalog candidates | Therma-Tru leaf kerf fit, installed compression and selected pad variant; no substitute sweep geometry is invented |
| Passive leaf | Ultimate Flip Lever Astragal; field instructions include the lower receiver | Receiver is drilled 5/8 inch diameter, at least 1-3/8 inch deep; delivered assembly setting and cap/screw clearances remain unconfirmed |
| Active leaf | PanoLock+ and Schlage BE365 | Endura explicitly lists BE365 CAM/PLY with **adapter F**; selected passage-handle adapter and exact assembly prep still need documentation |
| Fasteners | Factory hinges and installation kit, structural screws into framing at hinge/strike locations | Actual screw gauge, length, count, hinge machining and substrate-specific anchorage; the inherited generic three-inch kit is not an approved shop schedule |
| Pan | SureSill 4-9/16 inch sloped pan, 80 inch complete pack | Manufacturer FAQ gives 1/4–3/8 inch rise depending on pan; **3/8 inch is the conservative coordination allowance**, not a traced installed pan section |
| Apron | Impermeable self-adhered membrane under the approach, with raised jamb ends | Exact sheet/primer/sealant combination, PVC-pan bond and water-plane tie; no implicit approval of an unidentified waterproofing material or ccSPF |
| Approach | AridDek standard boards, nominal 6 inch module and modeled 1-1/2 inch depth, stock profile trim | Board/rib section, minimum cut length, end support, isolation and fastener details for this short approach |
| Head | SureSill HeadFlash 1-3/8 × 84 complete pack, stock end caps | Upstand, thickness and end-dam geometry are labeled coordination envelopes; they are not traced product sections |
| Balcony ends | Proglaze ETA System 1, standard 6 inch extrusion, molded corners, aluminum adaptors and Spectrem 1 | A candidate application: its published instructions assume engineering review and require substrate adhesion/compatibility verification. No such review or approval has been obtained |

Primary documents:

- [Therma-Tru 2026 dimensional data](https://outdoorsandsecurity.widen.net/content/lpxemo2dti/original/2026-Arch-Comp-BOOK---ARCH-1-Dimensional-Data.pdf), Arch 1.4, French inswing with 7/8 inch astragal.
- [Therma-Tru 2026 frame parts](https://outdoorsandsecurity.widen.net/content/ixw8lz4q8x/original/2026-Arch-Comp-BOOK---COMP-6-Frame-Parts--Packages.pdf), Comp 6.4 composite jamb profiles and composite trim pages.
- [Endura ZAI4565FN drawing](https://resources.enduraproducts.com/hubfs/OMRSv3%20-%20Line%20Drawings/Inswing%20Sill%20Systems/ZAI4565FN.pdf).
- [Endura DBK-R and other bottom profiles](https://marketing.poweredbyendura.com/hubfs/Weathersealing_TechnicalDocuments/Door%20Bottom%20Product%20Profiles_v2.pdf).
- [FLA inswing field instructions](https://www.enduraproducts.com/wp-content/uploads/2023/06/211159-FL-I-FP-Flip-Lever-Inswing-Field-Install-Inst-6_20_23.pdf).
- [PanoLock+ / Schlage compatibility](https://www.enduraproducts.com/wp-content/uploads/2024/01/2026-PanoLock-Compatibility-List-Schlage-Locks.pdf).
- [SureSill installation documents](https://www.suresill.com/install-guide), [height allowance](https://www.suresill.com/faq), [HeadFlash sizes and kit](https://www.suresill.com/product/headflash).
- [AridDek installation](https://wahoobuildingproducts.com/ariddek-installation-guide/).
- [Proglaze ETA System 1 instructions](https://www.tremcosealants.com/resource/download/Proglaze_ETA_System_1_AI.pdf), §§3.1, 4.1 and 5; the review and adhesion requirements are not waived by buying standard components.

### Outline provenance

`notes/assets/endura-zai4565fn-outline.json` records the simplified digitized outer
coordination outline and source. The PDF's horizontal and vertical scales are
normalized independently to the dimension lines. Internal cavities and extrusion
thicknesses are omitted. The traced cap crest is approximately **1.522 inches** above
its base, rather than the 1.375 inch fin callout. This is a clearance estimate, not an
additional manufacturer dimension or an approved installed cap setting. The raw PDF
and reference image are in `out/exterior-door-review/sources/`.

The ordered nominal leaves, assembled unit and framed void are separate model fields.
The working catalog envelope is **62-9/16 × 82 inches**, with a **63-5/16 × 82-1/2 inch
RO**, from Therma-Tru's 7/8-astragal table. The modeled framed height is
**82-7/8 inches**, adding the 3/8 inch pan allowance above that published RO. That table does **not** establish the Endura
FLA assembly's exact unit dimensions. The delivered Endura assembly still requires dimensional confirmation. `assembly_confirmed=False`.
The new `DT-EXT-FRENCH60-CATALOG` applies only to D-B-PATIO and D-S-DECK-E; it does not
resize D-M-BALC.

## 2. Placement, support and water paths

### Patio

D-B-PATIO stays on W-B-S3-FR. AO-B-BRICK-DOOR supplies its separate exterior boundary;
it supplies no door anchorage. The openings stay concentric. Their wider ROs preserve
the original centerline; the brick arch keeps its 8 inch rise and has a coordinated
86-1/4 inch overall opening height measured from the brick wall's own base.

AO-B-PATIO-SEAT is a real formed recess in W-B-S3, across the door RO, **1-3/4 inches
down** from the adjacent 7-1/4 inch curb. Its concrete seat is **5-1/2 inches above the
court datum**. Jamb/adjacent curb tops and the footing stay in place. The flood-step
check reads this actual lower edge, not the unrecessed wall top. W-B-S3 declares the
new 5-1/2 inch minimum; the sauna curb retains 7-1/4 inches. The door is not credited
as a flood barrier. Overflow drainage and the sump remain the backup provisions.

The pan's level bearing envelope is over the concrete seat. The pan drops outward
into a lower sloped apron below the thick AridDek approach and its cross bearers.
A concrete cantilever envelope supports the approach without relying on the veneer,
foam or plywood buck. It is a **candidate six-inch reinforced section**, not an
approved pour: root reinforcement, hooked-bar development, the curb/footing interface,
concrete cover, existing reinforcement and construction-joint details remain unresolved.
Keep the cavity, weeps and the isolation from the separately supported brick open.

### Study

The composite factory jamb anchors at the structural wall. The outer return/casing is
composite; no steel-wrap fabrication is included. The supported factory sill is level.
The short AridDek boards run outward and are supported by two cross bearers over the
concealed 2×6 outrigger envelopes. Their root connection to FS-S-EAST must be designed
against actual joist/rim geometry; a 24 inch drawn backspan is not proof of anchorage.
The cross-bearer-to-outrigger bearing/isolation detail also remains unresolved.

The approach reaches to the actual balcony edge minus the specified drainage gap.
The two structures are not fastened together. Flashing-end envelopes show separate
house/deck aluminum adaptors and a flexible corner, adjacent to both interrupted rear
flashing runs. Their actual positions follow the deck edge. These are not verified
Tremco application sections. Nominal movement checks reserve 1/4 inch horizontal and
1/4 inch vertical displacement, a 1/2 inch approach gap and 2 inch flashing overlap.
The whole balcony movement basis remains `balcony_differential_movement.md`; local
clearance arithmetic does not establish a flexible product's movement rating or bonds.

### Calculations and limits

The report assigns a **300 lb point load entirely to one support**, combined
conservatively with **60 psf live + 10 psf dead load**. Timber checks use declared
conservative adjusted stresses (Fb 575 psi, Fv 135 psi, E 1.2 million psi), with no
short-duration increase. The 2×4 cross bearers are checked on edge. These declared
material properties require the purchased species/grade/treatment to meet them.
The concrete strip feasibility uses 4,000 psi concrete, Grade 60 #4 top steel and
2 inch top cover. Root connection capacity is **not supplied** for either system;
member PASS therefore leaves installation fit **UNKNOWN**. Full-path capacity,
including concrete development and cross-bearer bearing, is still a design deliverable.

## 3. Height and geometry review

The report measures both finished floors against the cap outline and separately
checks its **+1/4 inch installation allowance**. Its nominal values are approximately:

| Door | Crest above interior finish | Crest above exterior landing | Conservative exterior value |
| --- | ---: | ---: | ---: |
| D-B-PATIO | 7.085 in | 7.397 in | 7.647 in |
| D-S-DECK-E | 0.397 in | 0.988 in | 1.238 in |

These are coordination calculations, not product certification or final site dimensions.
The selected pan maximum-rise allowance and digitized cap setting are explicit assumptions.
The prior study values 0.720/1.311 inches came from a different schematic seat/cap.

[Minnesota R311.3.2](https://www.revisor.mn.gov/rules/1309.0311/) measures from the top
of the threshold. The landing check now reads an installed/schematic crest when known;
a selected product without a section gets UNKNOWN rather than a rough-sill PASS.
The patio arch is checked at the clear jamb width against a 78 inch project headroom
criterion. Source/fit/supplier statuses stay independent in JSON and IFC.

Reproduce the actual resolved sections, height table, takeoff, flashing-end plots,
IFC/glTF and production-builder screenshots:

```sh
.venv/bin/python scripts/review-exterior-doors.py --export
node ui/scripts/door-review.mjs --exterior
```

Artifacts: `out/exterior-door-review/catalog-installation-report.json`,
`catalog-height-review.csv`, `catalog-installation-takeoff.json`,
`catalog-flashing-ends.pdf`, `door-sections.pdf`, and `after-exterior-*.png`.
The JSON takeoff lists the separate short AridDek cuts and the last board's rip width;
factory-included sill components are excluded from separate purchasing.

## 4. Public-price comparison and compatibility

| Configuration / item | Public price checked 2026-10-26 | Interpretation |
| --- | --- | --- |
| Preferred complete Smooth-Star/composite/ZAI/FLA/PanoLock+ pair with requested glass | **Not published for this configuration** | No complete price or assembly approval claimed |
| [FLA replacement system](https://www.betterdoor.com/shop/french-door-astragals-locks-replacement-parts/double-door-astragal-french-door-locks/endura-ultimate-flip-lever-astragal-system/) | **$190–$359**, options vary | Replacement component only; do not add it again to a prehung-unit allowance |
| Complete Tru-Defense-eligible fallback | **Not established from public pricing** | Requires Therma-Tru sill, dual-bulb bottom, seven-shape pads, qualifying frame/hinges/weatherstrip/glass and its 7/8 inch astragal; PanoLock+/FLA and laminated triple are not assumed retained |
| [Therma-Tru composite adjustable sill store page](https://store.thermatru.com/products/composite-adjustable-sill) | **No usable price: $0 placeholder / sold out** | Not a zero-cost component and not a complete-system price |
| Stock pan, head kit, approach, composite returns and transition parts | **Exact selected variants not fully priced** | Missing prices remain gaps; the model receives no invented catalog rates; its existing French-pair allowance is carried to the new type without presenting it as a quote |

Therma-Tru's [component requirements](https://www.thermatru.com/project-center/faqs/)
and [current warranty resources](https://www.thermatru.com/technical/warranties/) establish
that Tru-Defense is a specific system. Component geometric fit, the F adapter listing,
ordinary component warranties and a complete assembled-system performance label are
separate evidence. No prehanger/manufacturer was contacted, and no compatibility letter,
unit label, order confirmation or warranty extension was obtained.

## 5. Construction sequence after the evidence holds close

1. Confirm the exact catalog unit/hinge/sweep/pan sections and adjust the RO/head allowance.
2. Detail the support root connections, concrete development and actual cross-bearer bearing;
   coordinate reinforcement and independently moving structures before forming/framing.
3. Form the patio recess and support; frame both enlarged openings and the study approach
   supports. Check the resulting clear openings, concrete edge and landing elevations.
4. Install the supported sloping apron and catalog pan, with their prescribed end caps,
   corners, bonds and sealant. Join the jamb/head bands to the actual water plane.
5. Set and anchor the composite frame on continuous level bearing. Install/adjust the
   matched sweep, corner seals and FLA receiver without drilling through the pan.
6. Install the supported approach boards and stock trim with metal isolation and the
   required movement gaps. Keep outlets, cavity drainage and veneer weeps open.
7. Complete and inspect the two flexible flashing ends, install composite returns/casing
   and the stock head kit, and verify both leaf swings, bolt operation and weather seals.
8. Measure finished crest/landing heights and clear headroom; water-test drainage and
   adhesion in the completed detail before concealing inaccessible joints.
