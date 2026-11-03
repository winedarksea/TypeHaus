# Selected mirrors and vanity lighting

**Decision record · 2026-10-22; lighting amended 2026-10-31** (vanity sconces, suite 3-light bar, 95-CRI lamps, bath2 at 42 × 36). Sources of model identity and geometry are
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
| Main bath2 | Fleurco **MHAP4236** Halo Plus | 42 × 36 × 1 3/4 | 42 / 78 | Illuminated border **and** rear glow; owner accepted both; centred on the vanity |
| Upstairs hall bath | Kohler K-26050-BNL | 28 1/16 diameter × 1 3/8 | 44 / 72 1/16 | Plain round keeps the softened silhouette over the 36-inch vanity |
| Suite bath | Kate and Laurel Estero 221484 | Existing 20 1/8 × 28 × 5 1/2 model | 46 / 74 | Preserve the owner's gold arch and shelf, including its existing placement |
| Upstairs double vanity | Two Kohler K-30638-BLL (matte black, 2026-11-02) | Each 20 × 32 × 1 3/8 | Each 42 / 74 | Repeated arches, centered at x=22 3/8 and 52 3/8, with a 10-inch gap; three side sconces |
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

Every separate light takes replaceable E26 lamps; no fixture has a driver to fail. The
3000 K lamp in every Karlie is the **Waveform CentricHOME A19 3000K** (800 lm, 95 CRI, R9 90+,
`PROD-WAVEFORM-CENTRICHOME-A19-30K`), which replaced the Sunlite 80793-SU (CRI 94, R9 69) on
2026-10-31; it bills as its own lamp line. Bath2's 5000 K day bar keeps the Sunlite 80795-SU.

Hinkley Karlie bars have etched opal glass and **open shades facing down**: the 54622
two-light is 13 1/4 W × 7 1/2 H × 6 D, the 54623 three-light 22 1/2 W × 7 1/2 H × 6 D,
sockets to 14 W each.

| Location | Fixture / schedule mark | Lamps | Body bottom / top AFF |
|---|---|---|---|
| Basement | 54623BN / P5 | 3 × CentricHOME | 76 3/16 / 83 11/16 |
| Powder room | 54622CM / P2 | 2 × CentricHOME | 76 / 83 1/2 |
| Bath2 daytime | 54623CM / P3 | 3 × 80795-SU | 80 / 87 1/2 |
| Hall bath | 54623BN / P5 | 3 × CentricHOME | 74 1/16 / 81 9/16 |
| Suite | 54623BN / P5 (was P1 until 2026-10-31) | 3 × CentricHOME | 76 / 83 1/2 |
| Double vanity | three P6 Hinkley Soren 50910BK, 1 × E26 | 1 × Waveform ModernVintage A19 each | 56 7/8 / 71 1/8 (centres 64) |
| Attic | 54622BN / P1A | 2 × CentricHOME | 72 / 79 1/2 |

Each Karlie body starts **2 inches above its mirror head**, and its mounting elevation is the
body bottom: rough-in the box 5 1/2 inches above it, and check the supplied plate.
The attic's lowest roof height over the light's footprint is about 80 1/2 inches; the
basement soffit is about 86 7/16 inches above finished floor. Neither needs a ceiling move.

**Double vanity (2026-10-31).** Makeup light comes from the side, at the face, rather than
from over the mirror. The two Karlies over the arches became three P6 sconces at x = 9 7/16,
37 3/8 and 65 5/16 inches (`ED-S-VANITY-SCONCE-W/-C/-E`). Each 5-inch body clears the side
wall and the mirror edge by **7/16 inch**. Shifting the mirrors east does not help, because
both outer gaps are already equal. The boxes land in `BK-S-BD-N-MIRROR-HANG` (60 to 71 1/4
inches); the old Karlie band `BK-S-BD-N-MIRROR-LIGHT` is gone.

**Soren, black (owner, 2026-11-02).** `PROD-HINKLEY-50910BK`: 14 1/4 × 5 in., 4 3/4 in.
extension, a 5 in. round backplate, clear fluted glass, one E26 with a **6 W cap**. The mirrors
went black with it (K-30638-BLL, same 20 × 32 × 1 3/8). The lamp is the Waveform ModernVintage
A19 filament (5 W, 450 lm, 95 CRI, R9 80+): 1,350 source lm for the three against the old
2 × E26 allowance's 4,800, a deliberate trade for the look. Confirm before rough-in: the UL
damp label (dealers disagree) and the box offset (2 1/2 in. top to outlet).

**Suite (2026-10-31).** The three-light bar sits on the existing 22 1/2-inch
`BK-S-SN3-MIRROR-LIGHT`. Flanking sconces would stand in the tub's spray zone.

- [Hinkley 54622CM](https://www.hinkley.com/54622cm.html) /
  [54623BN](https://www.hinkley.com/54623bn.html); BN is brushed nickel, CM is chrome.
- [Sunlite 80795-SU](https://sunlite.com/ecomutils/downloadproductfileexternal?id=2066):
  fixed 5000 K, 9 W, 800 source lumens, CRI 95, R9 82; bath2 uses its plain daytime toggle.
- Waveform CentricHOME A19: confirm R9 ≥ 90 and the damp/enclosed rating on its sheet before ordering.

The schedule leaves **delivered fixture lumens unknown**. The listed lumens are lamp source
output, not what comes through the opal glass.

## Bath2 factory controls and power

The selected mirror is **Halo Plus MHAP4236**, 42 × 36, centred on the vanity. The owner
accepted the glowing glass border as well as the wall halo. The manufacturer publishes 120 V
plug installation, **116 W total including defogger**, up to 2243 lumens and a five-year limited
warranty. **CRI is UNCONFIRMED.** Neither the spec sheet nor the manual publishes it (searched
2026-10-31). The mirror stays as the house's one integrated mirror light; ask Fleurco, and if
the answer is below 90, swap to a front-lit 42 × 36 with a published CRI of 93 or more. Field-replaceable
LEDs and drivers are not documented either.

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
main-storey receptacles stay on their original non-GFCI-breaker branch. The mirror's 116 VA
is counted once, on the same branch as its plug; the circuit's explicit `load_va=116`
overrides device-load summation. Leave access to lift the mirror off its
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
found, installation labour, and the fitted bulbs in each light price (except the 3000 K CentricHOME
lamps, which bill as their own line since 2026-10-31). The suite mirror is billed
once, unchanged; the retired Robern and closet LED allowance rows are removed. Ordinary
plain mirrors remain in the agreed $150–400 range; the 42 × 36 Halo Plus is the deliberate
premium exception. These are estimates before tax/freight, not supplier quotes.
