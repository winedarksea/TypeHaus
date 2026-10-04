"""Large standard single bowl; Kraus KHU100-32 is a dimensional reference, not an order."""

from typehaus.model import FixtureType, Footprint2D, Mount, MountKind, Service, inch, pt

COUNTER_HEIGHT_IN = 36.0
QUARTZ_THICKNESS_IN = 1.181
BOWL_DEPTH_IN = 10.0

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
    basin=False,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    source='Kraus KHU100-32 specification sheet (rev. April 30, 2019), read 2026-10-03: '
           '32 x 19 in. exterior, 30 x 17 in. single bowl, 10 in. bowl depth, '
           '36 x 24 in. minimum cabinet, rear-centre drain 4 1/2 in. from exterior rear. '
           'https://www.kraususa.com/media/catalog/product/documentation/'
           'KHU100-32-Spec-Sheet.pdf. Dimensional reference only; brand remains unselected. '
           '32 x 22 in. placement envelope includes a 3 in. rear faucet zone; '
           '30 x 17 in. schematic flush-reveal opening. Fabricator must check the actual '
           'sink/template, corner radii, mounting clips and support before cutting quartz.',
)
