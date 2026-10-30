"""Large standard single bowl: the Kraus KHU100-32 (owner selection 2026-10-22)."""

from typehaus.model import CountertopHole, FixtureType, Footprint2D, Mount, MountKind, Product, Service, inch, pt

COUNTER_HEIGHT_IN = 36.0
QUARTZ_THICKNESS_IN = 1.181
BOWL_DEPTH_IN = 10.0

KRAUS_BOLDEN = Product(
    tag="PROD-KRAUS-KPF-1610SFS", brand="Kraus", model="KPF-1610SFS",
    name="Bolden single-handle pull-down faucet, spot-free stainless",
    url="https://www.kraususa.com/media/catalog/product/documentation/KPF-1610-IM.pdf",
    source="Owner selection 2026-10-24. Single 1 3/8 in. hole through 3 cm quartz, no "
           "escutcheon; right-hand lever moves forward. June 2024 manual/spec: 18 3/4 in. "
           "overall, 8 5/8 in. reach, 2 1/8 in. base, 3 3/8 in. maximum deck, "
           "3/8 in. compression supplies. See notes/kitchen_sink_installation.md.",
)
DEARBORN_KITCHEN_TRAP = Product(
    tag="PROD-DEARBORN-P9703WBG", brand="Dearborn by Oatey", model="P9703WBG",
    name="1 1/2-inch white polypropylene tubular P-trap with threaded PVC adapter",
    url="https://www.oatey.com/products/P_041193009241/"
        "dearborn-112-in-plastic-tubular-ptraps-with-threaded-adapter?upc=041193009241",
    source="Selected 2026-10-24; Oatey LCS1353 submittal: reversible J-bend, "
           "3 1/2 in. inlet/outlet spacing, 4 5/8 in. inlet-top to outside bottom, "
           "approximately 2 1/2 in. seal. Includes PVC adapter, nuts and washers. "
           "Connect to Badger discharge, not the unused Kraus basket strainer; "
           "see notes/kitchen_sink_installation.md for set-out and dry-fit hold points.",
)

KRAUS_KHU100_32 = Product(
    tag="PROD-KRAUS-KHU100-32", brand="Kraus", model="KHU100-32",
    name='Standart PRO 32" undermount single-bowl kitchen sink, 16 gauge stainless',
    url="https://www.kraususa.com/media/catalog/product/documentation/KHU100-32-Spec-Sheet.pdf",
    source="Owner selection 2026-10-22: the dimensional reference is the order.",
)

KITCHEN_SINK_32_SINGLE = FixtureType(
    tag="FX-KITCHEN-SINK-32-SINGLE",
    name='32" single-bowl undermount kitchen sink (30" x 17" bowl)',
    # Includes three inches behind the 19-inch steel flange for a quartz-mounted faucet.
    footprint=(inch(32), inch(22)),
    height=inch(20),
    mount=Mount(kind=MountKind.WALL,
                elevation=inch(COUNTER_HEIGHT_IN - QUARTZ_THICKNESS_IN - BOWL_DEPTH_IN)),
    plan_symbol="kitchen-sink-undermount-single",
    countertop_cutout=Footprint2D(points=(
        pt(inch(-15), inch(-10)), pt(inch(15), inch(-10)),
        pt(inch(15), inch(7)), pt(inch(-15), inch(7)),
    )),
    # Centred across the bowl, rear edge + 1" flange + 2": (352, 423.49) as placed
    # (notes/kitchen_sink_installation.md §2).
    countertop_holes=(CountertopHole(center=pt(inch(0), inch(10)), diameter=inch(1.375),
                                     purpose="faucet, Kraus KPF-1610SFS"),),
    basin=False,
    product_ref=KRAUS_KHU100_32.tag,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    source='Kraus KHU100-32 specification sheet (rev. April 30, 2019), read 2026-10-03: '
           '32 x 19 in. exterior, 30 x 17 in. single bowl, 10 in. bowl depth, '
           '36 x 24 in. minimum cabinet, rear-centre drain 4 1/2 in. from exterior rear. '
           'https://www.kraususa.com/media/catalog/product/documentation/'
           'KHU100-32-Spec-Sheet.pdf. Selected 2026-10-22. '
           '32 x 22 in. placement envelope includes a 3 in. rear faucet zone; '
           '30 x 17 in. schematic flush-reveal opening. Fabricator templates from the delivered '
           'sink and its template: corner radii, mounting clips and support. '
           'Faucet PROD-KRAUS-KPF-1610SFS: single 1 3/8 in. hole, centred across bowl, '
           '2 in. behind rear flange. Trap PROD-DEARBORN-P9703WBG on APPL-M-DISP; '
           'InSinkErator flange replaces the BST-1 basket strainer. Installation and '
           'fabrication hold points: notes/kitchen_sink_installation.md.',
)
