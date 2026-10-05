"""Living-room coffee-table power, recessed into the wood floor's joist bay."""

from typehaus import (
    ElectricalDeviceType,
    Product,
    Service,
    ServicePort,
    ft,
    inch,
)

FLOOR_BOX_PRODUCT = Product(
    tag="PROD-ARLINGTON-FLBR5420", brand="Arlington", model="FLBR5420",
    name="IN BOX recessed floor-box kit; finish suffix to be selected",
    source="https://www.aifittings.com/media/catalog-pages/P-19.pdf (2026-10-05)",
)

DEVICE_TYPES = (
    ElectricalDeviceType(
        tag="ED-T-FLOOR-RECEPTACLE-FLBR5420",
        name="Arlington FLBR5420 recessed floor box, 20A TR duplex",
        # Overall envelope: A is the flange diameter, B the below-floor depth;
        # C (3.775") is the body width, not its depth, on Arlington's side view.
        footprint=(inch(6.625), inch(6.625)), height=inch(6.55),
        nema="5-20R", product_ref=FLOOR_BOX_PRODUCT.tag,
        floor_box_listing="cULus E170558, listed floor-box kit",
        ports=(ServicePort(tag="power", service=Service.POWER_120,
                           position=(ft(0), ft(0), ft(0))),),
        source=(
            "Arlington P-19: 24.5 cu in box, 20A tamper-resistant duplex, 5-inch "
            "hole through LVP and subfloor; 6.625-inch flange, 6.550-inch depth. "
            "https://www.aifittings.com/media/catalog-pages/P-19.pdf. "
            "Thin flange over finished LVP, recessed plugs and slotted in-use cover; "
            "use gasketed blank cover when unused. Secure to structural subfloor, "
            "seal under flange per instructions and coordinate floating-LVP movement "
            "with flooring installer. Keep framing intact; verify bay and services "
            "before drilling. Pull 12/2 NM-B with ground from CKT-RC-MAIN through "
            "supplied NM connector; AFCI at breaker. Blank both unused LV ports. "
            "Second choice: Leviton listed TR pop-up floor box, "
            "https://leviton.com/products/residential/pop-up-floor-box-receptacles; "
            "recheck cutout, depth and clearances for the selected model."
        ),
    ),
)

