# Canopy beam tails — ventilated metal hoods

Implemented 2026-10-26 in `params/canopy_beam_hoods.py`,
`params/north_entry_frame.py` and `params/east_posts.py`.
**Modeled design; fabrication release remains open** for actual movement, shop
securement, treatment compatibility and the roofing lap described below.

[Model-derived coordination sections](assets/canopy_beam_tail_hoods.svg) show the
ventilated crown, separate roof apron and open house slot.

## Framing and symmetry

Both `BM-BW-RW` and `BM-BW-RE` now have equal **8⅞″ tails from post centres**,
77½″ overall. The east header grew 6⅛″ south, matching the west amendment of
2026-10-14. Both retain the original roof-bearing run through their south
`roof_bearing_insets`; roof footprint, truss stations, roof area, gutters and
leaders stay at their existing stations.

The active east system is `EAST_POST_SYSTEM = "kdat"`, with 6x6 wood posts.
`CN-BW-CAP-E` retains uid `X0QPPRBG1X` and changes from ACE6Z to the paired
AC6Z through-beam assembly. Both east heads now use AC6Z, MAX nailing: 14 beam
and 14 post 16d common HDG nails per complete paired assembly. A35Z angles
and the drained PVC-wrap termination remain. Steel/cast alternatives retain
their own head hardware; no AC cap is applied to concrete.

The existing rated AC6Z library row cites ESR-2604 §3.1.3/Table 3 for a continuous
5½″ beam on a 6x6, both pieces, MAX nailing, no splice. The revised east head
is graded by `wood_roof_post` at **0.164** combined uplift/along-beam lateral;
all four post records remain OK. Keep its stated moisture and fastener conditions.

The east extension adds `6.125/12 × 11.875/12 × 16.7232 = 8.447 lb` of exposed
header wind force. The recalculated canopy joint couple is **2,132.02 lb-ft**,
delivered E-W shear **707.06 lb**, chord force **88.834 lb**, combined end-strap
demand **261.893 lb**. West collector plate **217.475 lb**, east **88.834 lb**,
each against 450 lb. Joint boundary nailing is 29.719 plf against 190; the
garage south wall receives 40.579 plf against 182.5 and a 288.594 lb hold-down
increment against 3,065 lb. Roof-header uniform loading stays 1,125.77 plf and the
existing roof-load bending/bearing ratios remain 0.146/0.355. This is the
engine's distributed roof-load calculation, not a discrete truss-reaction or
hood-fastener design. Roof dead load remains the authored 10 psf allowance;
individual hood/apron weight and wind securement are not separately engineered.

## Cover and north termination

`TR-BW-HOOD-W/E` are matching crowned covers; `-APRON` identifies each separate
roof-supported apron. All four are thin sheet meshes in the shared IR, visible
as **Flashing · 3D**, and exported through the existing beam-cap IFC/GLB path.
They attach exclusively to the canopy, leaving the house-side slot open.

| Dimension | Modeled value |
|---|---|
| Coated metal sheet | 0.032″, `metal-dark-exterior`; confirm with treatment supplier |
| Hood cover width | 6½″ over 5½″ glulam |
| Clear top, side and south-end air space | ½″ minimum, excluding discrete supports |
| Crown slope, both directions | ¼″/ft, approximately ¹⁄₁₆″ centre rise |
| Side downstand / outward hem | ¾″ / ¼″ |
| South end return / outward hem | 1¼″ / ⅛″; bottom remains open |
| North upstand | 1″ |
| Clearance to south truss face | 1″, including upstand sheet thickness |
| Separate apron to hood upstand | ½″ horizontal separation, ⅞″ vertical overlap |
| Apron drip above hood | ⅛″ |
| Apron roof leg | 1″ past deck edge beneath water-control/roofing layers |

The first truss bears directly on the glulam. Its south face is actually ⅛″
south of the deck edge. A shallow cover cannot simply run north beneath that
bearing with ½″ air space. Instead, the hood stops clear of the truss; a
separate apron extends from the roof-deck surface, outside the rake fascia and
drips over the hood's raised north edge. The apron top follows the actual
4:12 roof plane, including the deck thickness. It shelters the remaining top
strip without passing metal through a truss bearing or changing the roof.

Use discontinuous, nonabsorptive spacers and sheltered side tabs fixed to the
glulam. Size their spacing and fasteners for local wind uplift and wood movement;
keep top sheets unpierced. These supports, fasteners, bend radii, seams and any
insect screening are shop/installation requirements, not individually modeled
parts. The bottom and vent paths must remain open and accessible for cleaning.
Preserve the specified treatment and field-cut treatment. Removability is required
for inspection. Do not copy the fitted sill cap's tape-bedded detail to these hoods.

## House clearance and fabrication release

The modeled wood end is **1⅞″** from the finished house cladding. The south air
space consumes ½″ and the outward end hem ⅛″. The resulting **minimum modeled
metal-to-house gap is 1¼″**, measured to the outermost sheet geometry. Nominal
geometry does not establish an adequate movement allowance.

Before fabrication, verify the actual house finish at both ends; include bends,
shop tolerances, installation tolerances and thermal movement. Establish the
required house/canopy movement envelope independently, and show the residual gap
on the shop section. The roof's existing 3/16″ settlement criterion is not a
horizontal house/canopy allowance. No hood, apron, tab, screw, spacer or sealant
may bridge to or contact the house throughout the design movement.

Also release the side-tab/spacer fastening and wind design, the actual glulam
preservative/metal/fastener compatibility (including nearby ZMAX), and the
roof-apron lap with the roofer. The 1″ roof leg is a modeled coordination
allowance, not a tested waterproof lap: extend it beneath the roofing as required
by the roof system without moving the roof edge. Coordinate its local interruption
of the existing rake trim before fabrication. Verify cap nail end/edge distances,
A35Z clearance, and wrap venting against actual hardware before erection.

Takeoff bills **two hood-and-apron assemblies**, 0.8 LF total of hood run, under
`edge_trim/beam_tail_hood`. Derived cover/apron meshes are excluded from volume
billing. Spacers, side tabs and fastening belong in that shop assembly quote.
The fitted sill-cap rate is not applied: this category is intentionally unpriced
until a fabricator quotes the two small assemblies and minimum shop charge.

## Source basis

[APA, Glulam Connection Details, p. 20, Figures 20A–B](https://www.dukepacific.com/cms_files/original/APA_EWS_Tech_Note___Glulam_Connections.pdf#page=20)
illustrates spaced top/end protection, ½″ minimum air space and preservative
treatment. The crown, apron and side-tab fastening are project detailing, not an
APA engineered or tested connection.

[FPInnovations, Optimizing the Design of Mass Timber in Exterior Applications,
pp. 10–13](https://cwc.ca/wp-content/uploads/2015/06/Durability-Exterior-Timber-Frame.pdf#page=10)
warns that flashing has limited efficacy and poorly detailed end caps trap water.
Gaps, drip edges, drainage, drying and treatment remain essential.
