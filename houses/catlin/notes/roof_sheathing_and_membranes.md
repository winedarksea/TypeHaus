# Roof deck and underlayment decision — 2026-10-28

Plywood throughout: house `ROOF` uses ordinary CDX **APA Rated Sheathing 40/20,
19/32 inch**; `GARAGE_ROOF` and `CANOPY_ROOF` use **Structural I 40/20, 19/32 inch**.
Order grade-stamped panels; CDX alone is not a span rating. Structural I remains on the
connected garage/canopy because the lateral design and NDS panel specific gravity use it.
Structural I is a structural grade, not a decay treatment. Wall sheathing is unchanged.

## Gravity, installation and lateral assessment

[APA E30 roof construction, Table 33](https://www.buildgp.com/wp-content/uploads/2022/06/APA-Engineered-Wood-Construction-Guide-Roofs-E30-2020.pdf)
lists **120 psf live load at 24 inch support spacing** for 19/32 40/20 sheathing,
assuming 10 psf dead load, strength axis across supports, panels at least 24 inches wide,
and continuity over two or more spans. Its maximum unsupported-edge span is 32 inches;
H-clips are not required by that span row at 24 inches. Clips do not supply diaphragm blocking.

The authored roofs have 24 inch framing. The house's 35 psf snow and garage's 42 psf
balanced snow are below that table load. The roof-step drift has a 50 psf peak surcharge:
42 + 50 = **92 psf**, screened conservatively as uniform over the affected panels rather
than crediting the tapered drift. The canopy header's 73.7 psf tributary average must NOT
be used as the peak deck demand. These comparisons are a screening of ordinary full-width,
multi-span panels, not a design of every strip or edge. Correct for dead load exceeding
10 psf rather than claiming the table covers an arbitrary assembly weight.

**Open engineering conditions:** RF-BW-CANOPY's last truss to the garage gable is about
24-1/8 inches, so the 24 inch row is not an exact lookup there. Do not interpolate: obtain
a panel design or revise support, retaining continuous plywood across the garage gable.
House sheathing oversails the rafter ends to the wall girts; the cantilever, actual support
and fastening require design. Narrow strips, single-span pieces, ridge cuts and exposed
rakes likewise require layout and appropriate support; do not extend Table 33 to them.
Lay strength axis across framing, provide approximately 1/8 inch panel gaps per APA and
follow the panel maker's instructions. Keep the canopy's existing solid panel-edge blocking,
collectors and joint nailing; the garage diaphragm remains unblocked.

The garage diaphragm retains the conservative SDPWS-2015 Table 4.2A 15/32 inch
Structural I unblocked row: **167.5 plf ASD, G_a 7 kip/in**. The blocked canopy retains
**190 plf ASD, G_a 12 kip/in** and its existing chord/collector assumptions. Both decks
remain thicker than the credited minimum; no increased table capacity is claimed.

NDS 2018 single-shear nail yield with D=0.131, L=2.5, F_yb=100,000 psi, deck G=0.50,
SPF G=0.42, l_s=0.59375 and l_m=1.90625 inches gives **Z=74.957994 lb (IIIs)**.
At wind C_D=1.6 this is **119.932791 lb/nail**, versus 135.002177 for the old 3/4 inch
panel. Crediting one row gives canopy 9 nails = **1,079.395 lb**, garage 8 nails =
**959.462 lb**. Current joint-2 demand 262.670 lb gives ratios 0.243 and 0.274.
The older cast-column variant demand 303.37 lb remains below 959.462 lb (0.316).
See [the full lateral calculation](canopy_garage_diaphragm.md).

**Open roofing approval:** [Image II installation guide, panel information](https://www.metalsales.us.com/wp-content/uploads/2020/01/install-guide-25.pdf)
recommends 5/8 inch plywood. Obtain confirmation that the specified 19/32 performance
category is acceptable, together with screw attachment/uplift and underlayment compatibility.
The model records a selected candidate, not manufacturer acceptance or a sealed panel design.

## Membranes and dry-in

- House: `roof-adhered-butyl-ht`, **0.030 inch installed**, GRACE ULTRA dimensional basis,
  0.05 perm maximum, 300 F. Retain the existing unvented flash-and-batt assembly.
  [GRACE ULTRA](https://ca.gcpat.com/en/solutions/products/grace-ice-water-shield-roofing-underlayment/grace-ultra)
  requires ventilation for full coverage: **written confirmation for this unvented assembly
  remains open**. Code compliance of the insulation does not waive product instructions.
- Garage/canopy: `roof-adhered-asphalt-ht`, **0.040 inch installed**, GRACE Ice & Water
  Shield HT basis, full deck, 260 F, 0.05 perm maximum. Both roof stacks stay identical,
  with the garage's existing soffit intake and vented ridge. The open canopy has no insulation.
  [GRACE HT product data](https://ca.gcpat.com/en/solutions/products/grace-ice-water-shield-roofing-underlayment/grace-ice-water-shield-ht)
  identifies rubberized asphalt and fastener sealing. It is underlayment beneath Image II,
  not an exposed EPDM roof.
- Henry PE200HT is an **SBS rubberized-asphalt** alternative, not butyl. Both chemistries
  have ASTM D1970 nail-sealing products; earlier claims that only butyl seals were incorrect.
  [Henry data](https://dam.carlisle.com/asset/d6ba5d60-3df8-4e58-a6f6-94382ac475f2/Blueskin-PE200HT-High-Temperature-Roof-Underlayment-TDS.pdf).

Install on clean, flat, dry plywood. Preserve the house eave detail's **<16% moisture-content
hold point** before sealing, and verify moisture again before underside foam encapsulation.
Follow manufacturer substrate, temperature, primer, lap and rolling instructions. Full-field
coverage replaces the garage ice-barrier allowance; do not bill an additional eave membrane
beyond the house strip-in below.
The model uses one field thickness, without release liner or doubled lap solids. Its existing
closed roof bands carry physical thickness into viewer, GLB and IFC. Near-black appearance
and the Flashing control are presentation decisions, independent of construction trade ownership.

## House eave: two-stage membrane

Order, bottom to top at the east and west eaves: plywood; field membrane to the deck edge;
box-gutter roof flange; Extended Eave pitched leg (7/8 in hem folded flat under); **strip-in**
of the same membrane over both flanges, lapped onto the field membrane; Image II pan.
This follows GCP [TL-15](https://ca.gcpat.com/sites/ca.gcpat.com/files/2018-02/RE0042_U-245-0316_Tech-Letter-15_1.pdf)
("metal drip edge ... should be placed over the membrane") and
[IWSDET-102](https://ca.gcpat.com/sites/ca.gcpat.com/files/2017-07/IWSDET-102.pdf) option 2
(drip edge stripped in). It **replaces** the earlier "flange on bare deck, membrane over"
rule: without the strip, water on the membrane runs under the flanges and off the deck edge
onto the wall head.

The strip is `roof-adhered-butyl-ht`, a **provisional 9 in width**, about 4 in past the flange
hem, scope `roof eave strip-in`: **55.9 SF** added to the membrane takeoff. Open: GCP
confirmation of strip width and of this unvented full-coverage assembly, and Metal Sales
acceptance of Image II over this deck-and-membrane stack. Cover the strip from UV (the pan does).

## Cost and AdvanTech upgrade

Comparison prices observed during planning (not delivered Minnesota quotations):
[Hamshaw CDX](https://store.hamshawlumber.com/departments/construction-plywood--amp--sheathing-%7C11%7C018.html)
5/8 nominal pine $32.98, fir $37.78; [square-edge 5/8 AdvanTech](https://store.hamshawlumber.com/products/4x8-5-8-advantech-sheathing-361.html)
$46.37. Versus fir, premium $8.59/sheet: about $650 over 75.85 net sheets for all roofs,
or $240 over 27.59 for garage/canopy, before waste/tax/delivery. The house pricing uses
thickness-qualified envelope rates for 0.594 inch (the takeoff's three-decimal rounding);
Structural I and membrane ranges remain budgets pending local quotes. Procurement sheets
and envelope areas overlap intentionally; the existing estimate must not bill both.

**Consider AdvanTech further as an upgrade**, especially if extended construction weather
exposure is expected. [Huber](https://www.huberwood.com/advantech/sheathing) offers full
5/8 inch Structural I 40/20 roof/wall sheathing with moisture-resistant resin throughout.
Its [residential warranty](https://www.huberwood.com/uploads/warranties/downloads/AdvanTechWarrantyResidential201305.pdf)
covers specified installation moisture/delamination issues but excludes wood-destroying
organisms; it does not demonstrate superior long-term rot resistance in this roof.
[ESR-1785](https://www.huberwood.com/uploads/documents/technical/Code-Recognition-for-AdvanTech-Subflooring-ESR-1785.pdf)
identifies Exposure 1 OSB and product-specific nail properties. Do not copy plywood G=0.50
into a 5/8 AdvanTech connection: its equivalent lateral G is 0.44. Recheck connections,
diaphragm properties, weight, actual thickness, underlayment adhesion and Image II acceptance,
and obtain local quotes before switching. Neither panel replaces sound water control and dry-in.
