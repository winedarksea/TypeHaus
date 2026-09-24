"""Air, vapour and water control membranes and foundation protection."""

from __future__ import annotations

from typehaus.model import Material

MATERIALS: tuple[Material, ...] = (
    Material(
        tag="air-barrier",
        name="Air/weather-resistive barrier",
        r_per_inch=0.0,
        vapor_permeance_perms=54.0,
        hatch="membrane",
        color="#4a4a4a",
        source="DuPont Tyvek HomeWrap physical-properties data sheet: 54 perm by "
        "ASTM E96-05 Method B (56 perm Method A) — a sheet rating, not perm-in",
    ),
    # BELOW-GRADE WATERPROOFING, and it is a different product from `air-barrier` above in
    # every way that matters: 0.05 perm against 54, adhered against hung, and required
    # rather than optional. Minnesota deleted IRC R406.1 outright (Minn. R. 1309.0406
    # subp. 1) and subp. 2 puts WATERPROOFING on every exterior foundation wall that
    # retains earth and encloses below-grade space — no high-water-table precondition, and
    # crawl spaces named. Authoring the layer as housewrap was how a 54-perm sheet came to
    # stand in for the one product the state does not let you omit.
    #
    # 60-mil rubberised-asphalt peel-and-stick sheet: item 5 of subp. 2's eight acceptable
    # materials ("40 mil polymer modified asphalt"), and the strongest published numbers of
    # the eight. Bituthene 3000 is the reference; Polyguard 650 and Carlisle MiraDRI 860
    # are equals. Specify `Bituthene Low Temperature` with `Primer B2 LVC` for a pour that
    # lands below 40 F — the standard grade gates the whole foundation on a warm week.
    Material(
        tag="waterproofing",
        name="Below-grade waterproofing (60 mil self-adhered rubberised asphalt)",
        r_per_inch=0.0,
        density=1100.0,
        vapor_permeance_perms=0.05,
        hatch="membrane",
        color="#2f2b2a",
        source="GCP Bituthene 3000 data sheet: 0.05 perm (ASTM E96 B), 300% "
        "elongation (D412), 200 ft hydrostatic head (D5385), 50 lb puncture "
        "(E154), crack-cycled 100x at -25 F unaffected (C836), 60 mil",
    ),
    # The drained plane on a retained face: a dimpled HDPE core with a bonded non-woven
    # filter fabric on the soil side. It is not a membrane and does not try to be — it
    # protects the membrane behind it and gives water a vertical path to the collector at
    # the footing, which is the thing a retaining-wall calculation assumes when it declines
    # to run a hydrostatic case. `vapor_permeance_perms` is deliberately high: a drainage
    # composite must not trap water against the waterproofing it protects.
    Material(
        tag="drainage-composite",
        name="Dimpled drainage composite with bonded filter fabric (0.4 in core)",
        r_per_inch=0.0,
        density=45.0,
        vapor_permeance_perms=10.0,
        hatch="membrane",
        color="#3f5a6b",
        source="generic HDPE dimple-sheet class (e.g. Cosella-Dorken Delta-Drain / "
        "Mar-flex ShoreDri): 0.4 in core, >=15 gal/min/ft in-plane flow at 1 ft "
        "head (ASTM D4716), 3,000+ psf compressive (D1621), AASHTO M288 class 2 "
        "non-woven bonded to the soil face. A PRODUCT CLASS, not a selection — "
        "the submittal is the engineer's",
    ),
    # Plain dimpled foundation membrane — the standard "dimpleboard": an HDPE sheet hung dimples
    # to the wall, no bonded fabric. The air gap behind it carries water down to the footing
    # drain. The sheet itself is vapour-tight; the permeance is the sheet's, not the gap's.
    Material(
        tag="dimple-board",
        name="Dimpled HDPE foundation membrane (5/16 in dimple)",
        r_per_inch=0.0,
        density=45.0,
        vapor_permeance_perms=0.1,
        hatch="membrane",
        color="#2f3a33",
        source="generic HDPE dimple-sheet class (e.g. Dorken DELTA-MS): 8 mm (5/16 in) "
        "dimple, ~5,200 psf compressive (ASTM D6364), 0.13 gal/SF air-gap "
        "volume, water- and vapour-impermeable sheet. A PRODUCT CLASS, not a "
        "selection",
    ),
    # The wet/humid-room air+vapour barrier: the layer a room run at 55-70% RH depends on,
    # and the one `building_science.humid_room_liner` keys on. Authored as a
    # **specification**, not a datasheet reading — 0.05 perm is the loosest a submitted
    # product may test at and still be IRC R702.7.1 Class I (<= 0.1 perm) with margin. That
    # is a different kind of number from the rest of this file and the `source` says so;
    # replace it with the selected product's own ASTM E96 result when one is chosen.
    #
    # It exists as a separate material from `air-barrier` (54 perm) precisely because those
    # two are opposites: one is a vapour-open weather barrier for the cold side, this is a
    # vapour-closed barrier for the warm side, and confusing them is the classic way to
    # build a wall that cannot dry in either direction.
    # Under-slab vapour retarder. There was no polyethylene in this catalog at all — the only
    # hit for the word was the radon sump basin — which is why the layer below every slab in
    # every house was simply absent, and why ``sheet.foundation.vapour_retarder`` fired
    # UNKNOWN on the permit sheet and nowhere else.
    #
    # 10 mil, Class A per ASTM E1745. The class is the specification that matters: E1745
    # grades a sheet on water-vapour transmission (0.01 perms or less after conditioning),
    # tensile strength and puncture resistance together, and Class A is the tier that
    # survives being walked on and having rebar chairs set on it. A 6-mil builder's poly is
    # the same polymer and none of the same product.
    Material(
        tag="polyethylene",
        name="Under-slab vapour retarder (10 mil, ASTM E1745 Class A)",
        r_per_inch=0.0,
        density=940.0,
        vapor_permeance_perms=0.01,
        hatch="membrane",
        color="#2e3d34",
        source="ASTM E1745 Class A: <=0.01 perms by ASTM E96 after the standard's "
        "conditioning, >=45 lbf/in tensile (E154), >=2,200 g puncture (D1709). "
        "IRC R506.2.3 requires a vapour retarder in contact with a slab's base "
        "course; ACI 302.2R and E1745 are what specify which one",
    ),
    Material(
        tag="humid-room-membrane",
        name="Self-adhered air/vapour barrier membrane (Class I)",
        r_per_inch=0.0,
        density=1000.0,
        vapor_permeance_perms=0.05,
        hatch="membrane",
        color="#3f4a52",
        source="specification, not a product datasheet: a fully-adhered sheet "
        "air/vapour barrier tested to ASTM E96 desiccant method at 0.05 perm "
        "or tighter, i.e. Class I per IRC R702.7.1 with margin",
    ),
    Material(
        tag="tile-uncoupling-membrane",
        name='Uncoupling membrane, 1/8"',
        hatch="membrane",
        color="#d9662a",
        source='companion layer under `tile` — Schluter DITRA or equivalent 1/8" '
        "polyethylene dimpled sheet, bedded in thinset. Carried so a takeoff "
        "orders it with the tile: it is what lets porcelain go over a wood "
        "deck without a crack-isolation gamble, and it is not in the tile "
        "row's own rate",
    ),
    Material(
        tag="roof-deck-vapor-barrier",
        name="Self-adhered roof deck vapour barrier",
        r_per_inch=0.0,
        vapor_permeance_perms=0.04,
        hatch="membrane",
        color="#4a4a4a",
        source="Published SBS self-adhered deck vapour barriers, ASTM E96 0.03-0.05 perm.",
    ),
    Material(
        tag="roof-vent-mat",
        name="Ventilated underlayment mat (nylon matrix)",
        r_per_inch=0.0,
        perm_rating=120.0,
        hatch="membrane",
        color="#8a8f94",
        source=(
            "Open nylon-matrix ventilation mat; air permeance per ASHRAE/UAF still-air reference."
        ),
    ),
    Material(
        tag="roof-adhered-butyl-ht",
        name="High-temp self-adhered butyl roof membrane",
        r_per_inch=0.0,
        vapor_permeance_perms=0.05,
        hatch="membrane",
        color="#2f3134",
        source=(
            "High-temperature self-adhered butyl underlayment technical data, ASTM E96 "
            "and ASTM D1970."
        ),
    ),
    Material(
        tag="roof-underlayment-synthetic",
        name="Vapour-permeable synthetic roof underlayment",
        r_per_inch=0.0,
        vapor_permeance_perms=20.0,
        hatch="membrane",
        color="#3b3b3b",
        source="Vapour-permeable synthetic roof-underlayment technical data, ASTM E96.",
    ),
    Material(
        tag="foundation-coating-acrylic",
        name='Trowel-applied acrylic foundation coating over mesh (1/8")',
        r_per_inch=0.0,
        density=1400.0,
        vapor_permeance_perms=5.0,
        coating=True,
        hatch="concrete",
        color="#8e8f8c",
        source=(
            "Acrylic foundation-coating product data and exterior acrylic/stucco vapour references."
        ),
    ),
    Material(
        tag="foundation-protection-panel",
        name='Aluminium-faced foundation protection panel (1/2")',
        r_per_inch=0.0,
        density=1100.0,
        hatch="metal",
        color="#1c1f24",
        source=(
            "Aluminium-faced foundation-protection panel product class; no installed "
            "ASTM E96 value published."
        ),
    ),
)
