# Selected mirrors and vanity lighting

**Decision record · 2026-10-22.** Sources of model identity and geometry are
`plan/mirror_types.py` and `plan/mirrors.py`; the suite's existing Estero remains in its
original furniture catalog and placement. This closes the hall-bath replacement-risk review
and supplies the missing mirror glass in the other bathrooms. No purchases have been made.

![Dimensioned mirror elevations](assets/mirror_selections.png)

[Vector elevations](assets/mirror_selections.svg), generated from the resolved model by
`scripts/render_mirror_selections.py`. Heights are above each room's finished floor.
Colours and the fixture shades are schematic, not finish samples or photometric predictions.
Basin locations follow authored countertop cutouts; bath2's generic toe-kick symbol is not
a fabrication drawing of its floating SEKTION frames.

## Glass and proportions

| Room | Selected product | Actual modeled W × H × D, inches | Bottom / head AFF | Design intent |
|---|---|---|---|---|
| Basement bath | Kohler K-26052-BNL | 22 3/16 × 34 3/16 × 1 3/8 | 40 / 74 3/16 | Soft rectangle gives the narrow room height without filling its wall |
| Main powder room | Kohler K-30638-CPL | 20 × 32 × 1 3/8 | 42 / 74 | Slim chrome arch over the D-Code basin and chrome B.2 mixer |
| Main bath2 | Fleurco **MHAP2436** Halo Plus | 24 × 36 × 1 3/4 | 42 / 78 | Illuminated border **and** rear glow; owner accepted both |
| Upstairs hall bath | Kohler K-26050-BNL | 28 1/16 diameter × 1 3/8 | 44 / 72 1/16 | Plain round keeps the softened silhouette over the 36-inch vanity |
| Suite bath | Kate and Laurel Estero 221484 | Existing 20 1/8 × 28 × 5 1/2 model | 46 / 74 | Preserve the owner's gold arch and shelf, including its existing placement |
| Upstairs double vanity | Two Kohler K-30638-BNL | Each 20 × 32 × 1 3/8 | Each 42 / 74 | Repeated arches, centered at x=22 3/8 and 52 3/8, with a 10-inch gap |
| Attic guest bath | Kohler K-31367-BNL | 22 diameter × 1 3/8 | 48 / 70 | Compact round permits a socketed light below the sloping roof |
| Main closet | Umbra Hubba Pill **1023469-624** | 17.88 × 62 × 2 | 12 / 74 | Plain full-length capsule, metallic titanium; no electrical load |

[Kate and Laurel Estero manufacturer page](https://www.kateandlaurel.com/products/estero-metal-framed-arch-wall-mirror-with-shelf).

The Estero's retailer/name dimensions have historically differed from its modeled overall
frame and shelf. This pass preserves that model rather than silently narrowing its shelf.
Kohler's K-26052 drawing has a truncated height label (“4-3/16”, alongside 868 mm); the
modeled 34 3/16 inches follows the overall 34-inch product and that drawing. Confirm the
factory hardware template at installation, rather than scaling the PDF.

Manufacturer sources, read 2026-10-22:

- [K-26052 soft rectangle](https://resources.kohler.com/webassets/kpna/catalog/pdf/en/K-26052_spec_US-CA_Kohler_en.pdf)
- [K-30638 arch](https://resources.kohler.com/webassets/kpna/catalog/pdf/en/K-30638_spec_US-CA_Kohler_en.pdf)
- [K-26050 round](https://resources.kohler.com/webassets/kpna/catalog/pdf/en/K-26050_spec_US-CA_Kohler_en.pdf)
- [K-31367 round](https://resources.kohler.com/webassets/kpna/catalog/pdf/en/K-31367_spec_US-CA_Kohler_en.pdf)
- [Kohler Essential finish/size collection](https://www.kohler.ca/en/products/mirrors-and-medicine-cabinets/shop-essential-collection-mirrors)
- [Umbra Hubba Pill](https://www.umbra.com/products/hubba-pill-mirror-62x18): order metallic
  titanium **-624**, not the brass **-104** variant shown by default.

## Replaceable lighting

All new separate lights are Hinkley Karlie, with etched opal glass and **open shades facing
down**. Two-light 54622 fixtures measure 13 1/4 W × 7 1/2 H × 6 D inches; three-light
54623 fixtures measure 22 1/2 W × 7 1/2 H × 6 D. Their E26 sockets accept LED bulbs up to
14 W each; the selected bulbs draw 9 W. Glass removes for cleaning and bulbs replace
independently of both the fixture and mirror. No fixture driver needs replacing.

| Location | Fixture / schedule mark | Bulbs | Body bottom / top AFF |
|---|---|---|---|
| Basement | 54623BN / P5 | 3 × 80793-SU | 76 3/16 / 83 11/16 |
| Powder room | 54622CM / P2 | 2 × 80793-SU | 76 / 83 1/2 |
| Bath2 daytime | 54623CM / P3 | 3 × 80795-SU | 80 / 87 1/2 |
| Hall bath | 54623BN / P5 | 3 × 80793-SU | 74 1/16 / 81 9/16 |
| Suite and each double-vanity basin | 54622BN / P1 | 2 × 80793-SU each | 76 / 83 1/2 |
| Attic | 54622BN / P1A | 2 × 80793-SU | 72 / 79 1/2 |

Each new fixture body starts **2 inches above its mirror head**. Its mounting elevation
is the body bottom, not the box centre. For the selected shades-down orientation, rough-in
the junction box 5 1/2 inches above the body bottom, checking the supplied mounting plate.
Confirm the factory plate's small projection above the catalog body before drilling, especially in the attic.
The attic's lowest roof height over the light's footprint is about 80 1/2 inches; the
basement soffit is about 86 7/16 inches above finished floor. Neither needs a ceiling move.

- [Hinkley 54622CM](https://www.hinkley.com/54622cm.html) /
  [54623BN](https://www.hinkley.com/54623bn.html); BN is brushed nickel, CM is chrome.
- [Sunlite 80793-SU](https://sunlite.com/ecomutils/downloadproductfileexternal?id=2063):
  fixed 3000 K, 9 W, 800 source lumens, CRI 94, R9 69, dimmable.
- [Sunlite 80795-SU](https://sunlite.com/ecomutils/downloadproductfileexternal?id=2066):
  fixed 5000 K, 9 W, 800 source lumens, CRI 95, R9 82; bath2 uses its plain daytime toggle.

The schedule leaves **delivered fixture lumens unknown**. Three 800-lumen bulbs are 2400
source lumens, not 2400 delivered through opal glass. Retain the exact bulb SKU and its
photometric sheet; a similarly named V2 lamp is not an automatic substitute. The researched
80795-SU six-pack listing was sold out on 2026-10-22, so availability remains a procurement
check. The studio wet-bar task light retains its existing generic linear type and price row.

## Bath2 factory controls and power

The selected mirror is **Halo Plus MHAP2436**, not the old MHA2436. The owner's final choice
allows a glowing glass border as well as the wall halo. The manufacturer publishes 24 × 36,
120 V plug installation, **70 W total including defogger**, up to 1711 lumens, and a five-year
limited warranty. CRI is unpublished; neither 1711 lumens at 2700 K nor field-replaceable
LEDs/drivers is established by those documents.

Use its **own touch dimmer**, normally at 2700 K, with 4500/6500 K available to the user.
The power button switches light and defogger together. There is no independent defogger
wall switch and no connection through the evening wall dimmer. The evening wall dimmer
continues to control the warm shower can and three low-voltage runs.

`ED-M-BATH2-MIRROR-PLUG` is an unswitched recessed grounded duplex behind the glass on
the mirror's y=173 3/8-inch centreline, 64 inches AFF, within the manufacturer's central
recommended outlet zone. Recess the plug behind the wall plane and route the cord
clear of direct contact with the heater pad, as the manual requires. It shares the existing protected 20 A bathroom-receptacle branch,
`CKT-BATH-ATTIC`, whose description now includes bath2. This avoids another panel space and
an inaccessible GFCI reset behind the mirror. Reset/test is at the GFCI breaker; general
main-storey receptacles stay on their original non-GFCI-breaker branch. The mirror's 70 VA
is counted once, on the same branch as its plug; the circuit's explicit allowance is
updated from 0 to 70 VA because that field overrides device-load summation. Leave access to lift the mirror off its
mounting screws and keep the spare cord clear of the heater.

[Fleurco specification](https://fleurco.com/media/website_furnishing.specification/GENERALSPECS_HALOPLUS-MHAP_07_2023.pdf)
and [installation / controls manual](https://fleurco.com/media/website_furnishing.manual/MHAP_Halo_PLUS_03-23.pdf).
The defogger is included because this manufactured model supplies it; no custom mirror or
lighting fabrication is required.

## Backing, clearances and cost

The new plain mirrors are furnishings rather than light devices. The old hall-bath light's
UID follows its replacement Karlie light; the closet mirror's UID follows the same physical
mirror location into its furnishing. Existing powered-mirror and separate-light UIDs are
retained when moving source modules.

Backing at each body's bottom supports the placement check; separate bands support the
**actual hanging rails**. The arch rail is 9 3/16 inches below its peak, around 64.8 inches
AFF, and would miss a generic 72-inch backing course. New bands span complete stud bays;
wet-wall blocks use the mirror-side face and avoid the lower basin/carrier services. The
attic uses a 4-inch octagon fixture box centred x=165 1/4 inches, 77 1/2 inches AFF,
side-fixed to the west face of the existing x=168-inch stud. Its centre is offset
5/8 inch east within Karlie's 7 1/4-inch backplate; the fixture stays on its basin centre
using the manufacturer-approved adjustable crossbar. Verify that crossbar before rough-in.
A proposed high horizontal backing strip was omitted because the roof resolver skips
it at the low stud end; the emitted lower mirror bands remain. Factory template and screw
selection remain installation responsibilities; backing coverage alone is not a fastener-capacity
calculation.

The double-vanity switch moves between the mirrors to x=37 3/8 inches at 48 inches AFF.
Its receptacle shifts one inch east to x=65 1/2 inches at 44 inches AFF, clear of the east
mirror. The existing hall-bath GFCI stays exposed south of its new plain round glass.

`prices.toml` carries dated retail evidence, an explicit allowance where no firm price was
found, installation labour, and fitted bulbs in each light price. The suite mirror is billed
once, unchanged; the retired Robern and closet LED allowance rows are removed. Ordinary
plain mirrors remain in the agreed $150–400 range; the $968 Halo Plus is the deliberate
premium exception. These are estimates before tax/freight, not supplier quotes.
