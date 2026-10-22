"""Selected mirror glass, serviceable vanity lighting, and their product identities.

Bulb lumens are source output; delivered lumens through the opal shades are unpublished.
Prices, including the fitted bulbs, live in prices.toml rather than product identities.
"""

from typehaus import (
    FurnitureType, LuminaireForm, LuminaireType, Mount, MountKind, Product,
    Service, ServicePort, inch,
)

_KOHLER_SPEC = "https://resources.kohler.com/webassets/kpna/catalog/pdf/en/K-{}_spec_US-CA_Kohler_en.pdf"
_FLEURCO_SPEC = "https://fleurco.com/media/website_furnishing.specification/GENERALSPECS_HALOPLUS-MHAP_07_2023.pdf"
_FLEURCO_MANUAL = "https://fleurco.com/media/website_furnishing.manual/MHAP_Halo_PLUS_03-23.pdf"
_READ_DATE = "Read 2026-10-22. "
_PLAIN_MIRROR_INSTALLATION = (
    " Use factory hanging hardware into solid backing; removable without disturbing finishes. "
    "No lighting, driver, defogger, or electrical connection. One-year limited Kohler warranty. "
    "Apply cleaner to the cloth, keep edges dry."
)


def _kohler_mirror(model, width, height, shape, finish):
    product_tag = "PROD-KOHLER-" + model
    product = Product(
        tag=product_tag, brand="Kohler", model="K-" + model,
        name=f"Essential {shape} mirror, {finish}",
        url=_KOHLER_SPEC.format(model.split("-")[0]),
        source=_READ_DATE + f"Overall {width} x {height} x 1.375 in., {finish}."
               + _PLAIN_MIRROR_INSTALLATION,
    )
    mirror_type = FurnitureType(
        tag="FT-MIRROR-KOHLER-" + model, name=product.name,
        footprint=(inch(width), inch(1.375)), height=inch(height),
        mount=Mount(kind=MountKind.WALL), product_ref=product_tag,
        plan_symbol=f"plain-{shape}-mirror-{'chrome' if finish == 'polished chrome' else 'nickel'}",
        source=product.source,
    )
    return product, mirror_type


_KOHLER_SELECTIONS = (
    _kohler_mirror("26052-BNL", 22.1875, 34.1875, "soft-rectangle", "brushed nickel"),
    _kohler_mirror("30638-CPL", 20, 32, "arch", "polished chrome"),
    _kohler_mirror("30638-BNL", 20, 32, "arch", "brushed nickel"),
    _kohler_mirror("26050-BNL", 28.0625, 28.0625, "round", "brushed nickel"),
    _kohler_mirror("31367-BNL", 22, 22, "round", "brushed nickel"),
)
_UMBRA_PRODUCT = Product(
    tag="PROD-UMBRA-1023469-624", brand="Umbra", model="1023469-624",
    name="Hubba Pill full-length mirror, metallic titanium",
    url="https://www.umbra.com/products/hubba-pill-mirror-62x18",
    source=_READ_DATE + "17.88 W x 62 H x 2 D in.; metallic titanium, wall-mounted capsule. "
           "Use factory mounting hardware into solid backing. Plain glass, no power connection. "
           "Finish is titanium, not a claim of a nickel-plated frame.",
)
_UMBRA_MIRROR = FurnitureType(
    tag="FT-MIRROR-UMBRA-HUBBA-PILL", name=_UMBRA_PRODUCT.name,
    footprint=(inch(17.88), inch(2)), height=inch(62),
    mount=Mount(kind=MountKind.WALL), plan_symbol="plain-capsule-mirror-nickel",
    product_ref=_UMBRA_PRODUCT.tag, source=_UMBRA_PRODUCT.source,
)
_FLEURCO_PRODUCT = Product(
    tag="PROD-FLEURCO-MHAP2436", brand="Fleurco", model="MHAP2436",
    name='Halo Plus 24 x 36 illuminated border and rear glow mirror', url=_FLEURCO_SPEC,
    source=_READ_DATE + "24 W x 36 H x 1.75 D in. Factory plug installation, 120 V, "
           "70 W TOTAL including defogger, maximum published output 1711 lm (not a "
           "2700 K photometric measurement). CRI unpublished. ETL/CEC certified. "
           "Own touch ON/OFF and brightness, 2700/4500/6500 K selection, work at 2700 K. "
           "Light and defogger share the power button; no separate defogger wall leg. "
           "Supply full, unswitched line voltage; no wall dimmer. Five-year limited warranty. "
           "Field replacement of electronic parts is not documented; do not promise it. "
           "Lift off for plug and hardware access; retain removal clearance. Manual: "
           + _FLEURCO_MANUAL,
)
_BULB_3000 = Product(
    tag="PROD-SUNLITE-80793-SU", brand="Sunlite", model="80793-SU",
    name="9 W E26 A19 LED bulb, fixed 3000 K, CRI 94",
    url="https://sunlite.com/ecomutils/downloadproductfileexternal?id=2063",
    source=_READ_DATE + "9 W, 800 source lumens, CRI 94, R9 69, dimmable. "
           "2.34 in. diameter x 4.5 in. long; three-year warranty. "
           "Not rated for enclosed fixtures; Karlie's downward open shades permit cooling.",
)
_BULB_5000 = Product(
    tag="PROD-SUNLITE-80795-SU", brand="Sunlite", model="80795-SU",
    name="9 W E26 A19 LED bulb, fixed 5000 K, CRI 95, R9 82",
    url="https://sunlite.com/ecomutils/downloadproductfileexternal?id=2066",
    source=_READ_DATE + "9 W, 800 source lumens, CRI 95, R9 82. "
           "2.34 in. diameter x 4.5 in. long; dimmable bulb used on the bath2 plain toggle. "
           "Three-year warranty; replace independently of fixture and mirror.",
)


def _karlie(model, count, finish, type_tag, mark, *, daylight=False):
    bulb = _BULB_5000 if daylight else _BULB_3000
    product = Product(
        tag="PROD-HINKLEY-" + model, brand="Hinkley", model=model,
        name=f"Karlie {count}-light vanity fixture, {finish}",
        url=f"https://www.hinkley.com/{model.lower()}.html",
        source=_READ_DATE + f"{13.25 if count == 2 else 22.5} W x 7.5 H x 6 D in. "
               "Etched opal glass, downward open shades, 120 V, damp listed. "
               "Medium E26 sockets, maximum 14 W LED each; no integral driver. "
               f"Fit {count} Sunlite {bulb.model} bulbs. "
               "Replace bulbs and remove glass for cleaning. Junction-box centre is "
               "5.5 in. above body bottom in the selected shades-down orientation. "
               "Delivered fixture lumens are unpublished; do not substitute bulb lumens.",
    )
    luminaire = LuminaireType(
        tag=type_tag, name=product.name + (", 5000 K" if daylight else ", 3000 K"),
        form=LuminaireForm.MIRROR_LIGHT, type_mark=mark,
        footprint=(inch(13.25 if count == 2 else 22.5), inch(6)), height=inch(7.5),
        plan_symbol=f"socketed-vanity-{count}-{'chrome' if finish == 'chrome' else 'nickel'}",
        lamp=f"{count} x E26 A19 Sunlite {bulb.model}, replaceable",
        watts=count * 9, load_va=count * 9, lumens=None,
        cct_k=5000 if daylight else 3000, cri=95 if daylight else 94,
        dimmable=not daylight, damp_rated=True, product_ref=product.tag,
        ports=(ServicePort(tag="power", service=Service.POWER_120,
                           position=(inch(0), inch(3), inch(5.5))),),
        source=product.source + f" Total bulb source output {count * 800} lm; "
               + ("published bulb R9 82." if daylight else "published bulb R9 69."),
    )
    return product, luminaire


_KARLIE_SELECTIONS = (
    _karlie("54622BN", 2, "brushed nickel", "ED-T-LT-KARLIE-2-BN", "P1"),
    _karlie("54622CM", 2, "chrome", "ED-T-LT-KARLIE-2-CM", "P2"),
    _karlie("54623CM", 3, "chrome", "ED-T-LT-MIRROR-DAY", "P3", daylight=True),
    _karlie("54623BN", 3, "brushed nickel", "ED-T-LT-KARLIE-3-BN", "P5"),
)
_HALO_TYPE = LuminaireType(
    tag="ED-T-LT-MIRROR-HALO-2700", name=_FLEURCO_PRODUCT.name,
    form=LuminaireForm.MIRROR_LIGHT, type_mark="P4",
    footprint=(inch(24), inch(1.75)), height=inch(36), plan_symbol="halo-mirror-light",
    lamp="Factory LED border and rear glow, integral touch dimmer",
    watts=70, load_va=70, lumens=1711, cct_k=2700, cri=None,
    dimmable=True, integral_switch=True, damp_rated=True,
    ports=(ServicePort(tag="power", service=Service.POWER_120,
                       position=(inch(0), inch(0.875), inch(22))),),
    product_ref=_FLEURCO_PRODUCT.tag, source=_FLEURCO_PRODUCT.source,
)

# Under the attic rake a 4-in. octagon box attaches directly to the east stud. Offset
# its centre 5/8 in. east within Karlie's 7-1/4-in. backplate; local +x faces west.
_ATTIC_KARLIE = _KARLIE_SELECTIONS[0][1].model_copy(update={
    "tag": "ED-T-LT-KARLIE-2-BN-ATTIC", "type_mark": "P1A",
    "ports": (ServicePort(tag="power", service=Service.POWER_120,
                          position=(inch(-0.625), inch(3), inch(5.5))),),
    "source": _KARLIE_SELECTIONS[0][1].source +
              " Attic mounting: 4-in. octagon fixture box centred x=165.25 in., 77.5 in. AFF, "
              "side-fixed to the x=168-in. stud; manufacturer-approved adjustable crossbar "
              "keeps the fixture centred x=164.625 in. No high horizontal backing strip "
              "under the rake. Verify supplied crossbar before rough-in.",
})

MIRROR_PRODUCTS = (
    *(product for product, _ in _KOHLER_SELECTIONS), _UMBRA_PRODUCT,
    _FLEURCO_PRODUCT, _BULB_3000, _BULB_5000,
    *(product for product, _ in _KARLIE_SELECTIONS),
)
MIRROR_FURNITURE_TYPES = (*(kind for _, kind in _KOHLER_SELECTIONS), _UMBRA_MIRROR)
MIRROR_LIGHT_TYPES = (*(kind for _, kind in _KARLIE_SELECTIONS), _ATTIC_KARLIE, _HALO_TYPE)
