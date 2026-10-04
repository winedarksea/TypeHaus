# Simpson hanger geometry

The shapes in `resolve/connector_geometry/hangers.py` use thin folded plates instead
of a solid block around the carried member. Catalog dimensions are inches, converted
to metres by the shared mesh helpers. The caller supplies the black material.

## Sources and dimensions

Dimensions were read on 2026-10-04 from Simpson's current
[Wood Construction Connectors catalog C-C-2026](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog),
[downloadable PDF](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf).
Printed and PDF page numbers match. The table below lists the principal authored parts;
the Python dimension records include the additional published sizes.

| Part | Clear W | H | B or A | Gauge | Pages |
| --- | ---: | ---: | ---: | ---: | --- |
| LUS28 | 1-9/16 | 6-5/8 | B 1-3/4 | 18 | 114, 219–220 |
| LUS210, Z, SS | 1-9/16 | 7-13/16 | B 1-3/4 | 18 | 115, 220 |
| HHUS410 | 3-5/8 | 9 | B 3 | 14 | 160, 221 |
| HU28-2, Z | 3-1/8 | 6-5/16 | B 2-1/2 | 14 | 114 |
| HU212-3 / HUC212-3 | 4-11/16 | 9-13/16 | B 2-1/2 | 14 | 115 |
| HUCQ410-SDS | 3-9/16 | 9 | B 3 | 14 | 117, 160 |
| IUS2.56/11.88 | 2-5/8 | 11-7/8 | B 2 | 18 | 154, 159 |
| LSSR1.81Z | 1-13/16 | 8-15/16 | A 4-1/8 | 18 | 176–178 |
| LSSR2.37Z | 2-3/8 | 8-15/16 | A 4-1/8 | 18 | 176–178 |
| THA422 | 3-5/8 | 22 stock | C 7-7/8 | 16 | 212–214 |
| LSCZ | 1-1/2 strip | 11-1/16 developed | 6-3/4 stringer leaf | 18 | 320 |

The catalog's p. 24 nominal uncoated sheet thicknesses are used: 14 ga 0.075 in,
16 ga 0.060 in, 18 ga 0.048 in. Coating buildup is omitted.

Simpson's
[LSSR CAD download library](https://strongtie.com.au/products/lssr-slopeable-skewable-rafter-hanger)
was inspected for the tapered wings, relief at the front edge and separate swivel seat.
Its downloadable installation drawings were used for shape reference; US dimensions
come from the US catalog. The
[IUS installation guide](https://www.strongtie.com/resources/product-installers-guide/ius-installation)
also documents the locator tabs and snap-in seat.

## Placement and simplification

Local x crosses the clear opening; +y runs from the supporting face into the carried
member; z=0 is the carried bottom at that face. Level seats have steel below z=0.
H is the overall steel height from the seat underside to the top, so a level cheek
ends at H minus sheet thickness. W is the free space between the cheeks.

HU and LUS have outward face wings. HUC and HUCQ turn those wings into the opening,
behind the carried member. IUS has waisted cheeks and short tabs over the header.
LSSR mounting wings remain upright; its separate seat follows the signed outward
pitch, with seat-top points on z=y tan(pitch). LSC has one side flange and a support
leaf that stays upright when its stringer leaf slopes.

THA422's H=22 in describes developed strap stock. When the caller supplies a carried
depth, straps bend over the support at that depth. `support_width_in` determines the
horizontal wrap; remaining stock returns down the far face. Without support width,
the catalog's 2 in minimum wrap is used. Without a usable depth, the stock is drawn
straight. Thin overlapping corner plates approximate bend radii.

Nail holes, embossed ribs, nail domes, stamping, the LSSR pivot hole and hinge curvature
are omitted. Cheek reliefs, the LSSR seat's small cheeks, IUS tabs and LSC side ears use
simple outlines traced from illustrations. Their undimensioned proportions are
explicit configuration, rather than claims of manufacturing accuracy. Catalog W/H/B
and sheet gauge remain fixed as carried-member dimensions change.

## Family-only annotations

Authored product numbers always select that stamping, even if a carried member does
not fit. Generic LUS/LUSZ/HU/HUC/IUS/LSSR annotations select published sizes from the
supplied member dimensions; they do not scale steel to match the wood. Unknown
product numbers or unsupported dimension combinations return no catalog mesh.

Two current family-only cases have documented visual representatives: a 1-1/4 in
rim at 7-1/4 in depth uses LUS28's 1-9/16 in opening; a 2 or 2-1/2 in I-joist flange
at 11-7/8 in depth uses LUS210-2's 3-1/8 in opening. The current four generic Catlin
I-joist connections have 2-1/2 in flanges. This representative is oversized and does not establish a
correct installed product for that I-joist. The catalog has no LUS2.06/11.88 row.
These choices preserve family annotations and billing, which this visual pass does
not modify. An exact fitting product requires a separate authored specification.

## Catalog discrepancies

The current p. 115 HU212-3 / HUC212-3 row gives H=9-13/16 in; historical C-C-2017
citations in the hardware library give 10-5/16 in. Geometry uses the current row.
The current catalog also differs between its HU412 sawn and engineered tables:
p. 117 gives 10-3/8 in, while p. 160 gives 10-5/16 in. Geometry uses the sawn table's
10-3/8 in. These discrepancies remain documented; allowable-load records are separate.
