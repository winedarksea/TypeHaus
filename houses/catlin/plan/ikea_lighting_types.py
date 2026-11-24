"""IKEA luminaire swaps of 2026-11-21: the laundry bar, the basement vanity light and the
exterior wall lights. Owner's call on cost; every one keeps a replaceable lamp.

IKEA publishes no UL/ETL file, CCT, CRI or delivered lumens for these; each is a CONFIRM
before ordering. One GU10 lamp serves NYMÅNE and GRÖNSPRÖT, so the house stocks one spare.
Pages and assembly sheets read 2026-11-21.
"""

from __future__ import annotations

from typehaus import LuminaireForm, Service, ServicePort, ft, inch
from typehaus.model import LuminaireType, Product, ProductPart

_READ = "Read 2026-11-21. "
_POWER_120 = (ServicePort(tag="power", service=Service.POWER_120,
                          position=(ft(0), ft(0), ft(0))),)

GU10_90_30K = Product(
    tag="PROD-LAMP-GU10-90-30K", brand="generic", model="GU10 LED, 3000 K, CRI 90",
    name="GU10 LED lamp, ~6 W, ~500 lm, 3000 K, CRI 90+, dimmable",
    source=_READ + "Allowance, not a SKU: any 90-CRI 3000 K GU10 at or under NYMÅNE's 8 W cap "
           "and short enough for its shade (reviews: some 6 W bodies foul the baffle). Rated "
           "for enclosed use where it goes in GRÖNSPRÖT. IKEA's SOLHETTA states no CRI.",
)
NYMANE_4SPOT = Product(
    tag="PROD-IKEA-NYMANE-4SPOT-WH", brand="IKEA", model="603.377.06", sku="603.377.06",
    name="NYMÅNE ceiling light with 4 spotlights, white",
    url="https://www.ikea.com/us/en/p/nymane-ceiling-light-with-4-spotlights-white-60337706/",
    source=_READ + "$79.99. Hardwired, contract grade; 29 L x 3 W x 5 H in.; 4 x GU10 LED, "
           "max 8 W. Assembly sheet AA-1961877-8: centre canopy on the box's crossbar, end "
           "spots at the bar ends, each spot swivels and tilts. Spot pitch, canopy and shade "
           "sizes are not dimensioned. Reviews: the plate does not sit quite flush.",
)
VALLMORA_3 = Product(
    tag="PROD-IKEA-VALLMORA-3-NI", brand="IKEA", model="803.069.40", sku="803.069.40",
    name="VALLMORA wall lamp, 3 spots, nickel plated",
    url="https://www.ikea.com/us/en/p/vallmora-wall-lamp-3-spots-nickel-plated-80306940/",
    source=_READ + "$89.99. 23 W x 11 H x 6 D in.; brushed nickel-plated steel, frosted "
           "glass; 3 x E26 LED. Approved for damp locations, tested for bathroom use. "
           "Assembly sheet AA-1405541-2: crossbar on a junction box, oval back plate, shades "
           "DOWN only. Back plate and shade pitch not dimensioned. Reviews: rust after ~2 "
           "years in a shower room (this one has no shower).",
)
GRONSPROT = Product(
    tag="PROD-IKEA-GRONSPROT-BK", brand="IKEA", model="205.559.99", sku="205.559.99",
    name="GRÖNSPRÖT wall lamp, hardwire installation, outdoor, black",
    url="https://www.ikea.com/us/en/p/groensproet-wall-lamp-hardwire-installation-outdoor-"
        "black-20555999/",
    source=_READ + "$19.99. 2 dia x 5 H x 4 D in.; powder-coated aluminium and stainless; "
           "1 x GU10 LED; hardwired, electrician installed. Rating stated only as IP44.",
)

# R: exterior wall light. The tag stays the role so the five placements did not move; the
# WAC Tube it replaced is ED-T-LT-SCONCE-EXT-WAC (R1), catalog-only, the named revert.
GRONSPROT_EXT = LuminaireType(
    tag="ED-T-LT-SCONCE-EXT", replaceable_lamp=True, lamp_base="GU10",
    name="Exterior cylinder wall light, GU10, black",
    form=LuminaireForm.SCONCE, type_mark="R",
    footprint=(inch(2), inch(4)), height=inch(5), plan_symbol="sconce-tube",
    lamp="1 x GU10 LED, 3000 K, CRI 90+, replaceable", watts=6.0, lumens=None,
    cct_k=3000, cri=90, dimmable=False, damp_rated=True, wet_rated=True, full_cutoff=True,
    load_va=6.0, ports=_POWER_120, product_ref=GRONSPROT.tag,
    parts=(ProductPart(role="lamp", product_ref=GU10_90_30K.tag),),
    source=GRONSPROT.source + " CONFIRM before ordering: (1) a UL/ETL WET-location label "
           "(IP44 is not one; the garage face and balcony edge are wet; damp-only sends "
           "those three back to R1); (2) down-only (IKEA's photo lights the lower wall), "
           "which full_cutoff claims; (3) its base covers the box, or add a round "
           "weatherproof cover. Delivered lm unpublished (~500 lm lamp).",
)

# P7: RM-B-BATH's vanity light (was the Karlie 54623BN, P5), centred over the 22 3/16" mirror.
VALLMORA_VANITY = LuminaireType(
    tag="ED-T-LT-VALLMORA-3-NI", replaceable_lamp=True, lamp_base="E26",
    name="VALLMORA 3-light vanity fixture, nickel, 3000 K",
    form=LuminaireForm.MIRROR_LIGHT, type_mark="P7",
    footprint=(inch(23), inch(6)), height=inch(11), plan_symbol="socketed-vanity-3-nickel",
    lamp="3 x E26 A19 Waveform CentricHOME A19 3000K, replaceable",
    watts=30, load_va=30, lumens=None, cct_k=3000, cri=95, dimmable=False, damp_rated=True,
    product_ref=VALLMORA_3.tag,
    parts=(ProductPart(role="lamp", product_ref="PROD-WAVEFORM-CENTRICHOME-A19-30K",
                       quantity=3),),
    # Box centre ~9" over the body bottom, scaled off the assembly sheet's drawing.
    ports=(ServicePort(tag="power", service=Service.POWER_120,
                       position=(inch(0), inch(3), inch(9))),),
    source=VALLMORA_3.source + " Lamps as the Karlie's (2,400 source lm). CONFIRM the UL/ETL "
           "mark and the back plate against the box.",
)

# R2: the basement stair night light (owner, 2026-11-24). The exterior GRÖNSPRÖT indoors,
# down-only, with IKEA's 2 W GU10: on CKT-LT-BACKUP, the one basement light an outage keeps.
SOLHETTA_GU10_253 = Product(
    tag="PROD-IKEA-SOLHETTA-GU10-253-27K", brand="IKEA", model="SOLHETTA GU10 253 lm",
    sku="405.849.48", name="SOLHETTA LED bulb GU10 253 lumen, 2700 K",
    url="https://www.ikea.com/us/en/p/solhetta-led-bulb-gu10-253-lumen-40584948/",
    source="IKEA US listing, read 2026-11-24. $5.99 / 3 pack; 2.0 W; 2700 K; not dimmable.",
)
GRONSPROT_NIGHT = GRONSPROT_EXT.model_copy(update={
    "tag": "ED-T-LT-NIGHT-STAIR", "type_mark": "R2",
    "name": "Stair night light, GU10 2 W 2700 K, black",
    "lamp": "1 x GU10 LED, 2 W, 253 lm, 2700 K, replaceable", "watts": 2.0, "lumens": 253.0,
    "cct_k": 2700, "cri": None, "wet_rated": False, "load_va": 2.0,
    "parts": (ProductPart(role="lamp", product_ref=SOLHETTA_GU10_253.tag),),
    "source": GRONSPROT.source + " Indoors over ST-B2M's landings, down-only; a 2 W lamp "
              "to see the treads by in an outage, not to light them to R303.7. Indoors on a flush box "
              "its 2\" base covers nothing: a 4\" round box and a blank round cover, CONFIRM.",
})

IKEA_LIGHTING_PRODUCTS = (GU10_90_30K, NYMANE_4SPOT, VALLMORA_3, GRONSPROT, SOLHETTA_GU10_253)
