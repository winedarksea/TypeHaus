"""Itemized small hardware; supplier quotes and qualification live in the house CSV.

Commodity models remain blank until qualified; a design specification is not a retail SKU.
Each row is separately counted, including fabricated rack materials and electrical parts.
"""

from typehaus import Product


def _hardware(tag, name, model):
    return Product(
        tag="PROD-PLANT-" + tag,
        brand="Commodity / field assembly",
        model=model,
        name=name,
        source="2026-11-11 design specification; quote/SKU qualification required. "
        "See notes/plant_reservoir_procurement.csv; no undocumented substitutions.",
    )


HARDWARE_QUANTITIES = (
    (
        _hardware(
            "NPSM-ADAPTER",
            "3/8 male NPT to 1/2 male NPSM strainer adapter with face seal; qualify seat",
            "",
        ),
        2,
    ),
    (_hardware("PUMP-OUTLET-BARB", "3/8 male NPT x 1/2 hose barb, pressure-rated nylon", ""), 2),
    (_hardware("SUCTION-HOSE", "4 ft reinforced 1/2 ID suction hose; vacuum rated", ""), 2),
    (_hardware("HOSE-CLAMP", "Stainless smooth-band clamp for delivered 1/2 ID hose", ""), 12),
    (_hardware("FILTER-INLET", "3/4 female NPT x 1/2 hose barb, pressure-rated nylon", ""), 2),
    (_hardware("FILTER-OUTLET", "3/4 female NPT to 0.700 OD distribution tube; >=50 psi", ""), 2),
    (_hardware("DISCHARGE-HOSE", "2 ft reinforced 1/2 ID discharge hose; >=50 psi", ""), 2),
    (
        _hardware(
            "HEADER-TUBE", "50 ft blank distribution tubing 0.700 OD / 0.600 ID; >=50 psi", ""
        ),
        2,
    ),
    (_hardware("OUTLET-TUBE", "100 ft outlet tubing 0.250 OD / 0.170 ID; >=50 psi", ""), 1),
    (
        _hardware(
            "OUTLET-STAKE",
            "Pot outlet stake supporting 1/4 tube above tank maximum water level",
            "",
        ),
        24,
    ),
    (_hardware("HEADER-TEE", "Tee for 0.700 OD header; >=50 psi", ""), 4),
    (_hardware("HEADER-END", "End closure for 0.700 OD header; >=50 psi", ""), 4),
    (_hardware("TUBE-CLIP", "Removable 1/4 tube clip", ""), 24),
    (_hardware("TUBE-PLUG", "Ten-pack of compatible emitter-hole plugs for unused outlets", ""), 1),
    (
        _hardware(
            "PRESSURE-TEST", "0-60 psi gauge with tee, isolation and 1/2 barb connections", ""
        ),
        2,
    ),
    (
        _hardware("THREAD-SEAL", "PTFE seal tape for NPT only; no seal tape on NPSM face seal", ""),
        1,
    ),
    (
        _hardware(
            "POTABLE-FILL-TUBE",
            "4 ft potable 1/4 OD removable fill tube; compatible compression insert/ferrule",
            "",
        ),
        1,
    ),
    (
        _hardware(
            "FILL-TUBE-CLIP",
            "Removable rim clip securing potable discharge above rim during attended fill",
            "",
        ),
        1,
    ),
    (
        _hardware(
            "FLOAT-MOUNT",
            "Over-rim low-water support with 1/8 female NPT mount; no below-rim penetration",
            "",
        ),
        1,
    ),
    (
        _hardware(
            "KYCON-CONNECTOR",
            "Locking 4-pin mating plug; parallel pin pairs per MEAN WELL drawing",
            "KPPX-4P",
        ),
        2,
    ),
    (
        _hardware(
            "MOTOR-HARNESS",
            "4 ft 16 AWG two-conductor motor harness; verify ampacity and pin termination",
            "",
        ),
        2,
    ),
    (_hardware("FUSE-HOLDER", "Inline enclosed DC fuse holder rated for selected OEM fuse", ""), 2),
    (
        _hardware(
            "MOTOR-FUSE",
            "OEM-required motor fuse; amperage/time characteristic hold for start test",
            "",
        ),
        2,
    ),
    (_hardware("C13-CORD", "Grounded NEMA 5-15P to IEC C13 supply cord, 3 ft", ""), 2),
    (_hardware("RACK-CORD", "Grounded 14/3 rack supply cord, single NEMA 5-15P at RC6", ""), 1),
    (
        _hardware(
            "PERMIT-OUTLET",
            "Enclosed two-outlet 120 V distribution after relay, for two timer inputs",
            "",
        ),
        1,
    ),
    (
        _hardware(
            "UNSWITCHED-OUTLET",
            "Enclosed 120 V distribution for transformer and WaterWatcher input",
            "",
        ),
        1,
    ),
    (_hardware("CONTROL-WIRE", "25 ft 18/2 low-voltage control wire, float extension", ""), 1),
    (
        _hardware(
            "TERMINALS", "Ten-pack protected terminal connectors and grounding terminals", ""
        ),
        1,
    ),
    (_hardware("CABLE-GLAND", "Strain relief matched to delivered cord diameters", ""), 6),
    (
        _hardware(
            "DRY-ENCLOSURE",
            "Dry protected electrical compartment with mains/control barrier; fit and heat review",
            "",
        ),
        1,
    ),
    (_hardware("RACK-FRAME", "36 x 12 x 24 corrosion-resistant frame stock; free-standing", ""), 1),
    (_hardware("RACK-SHELF", "36 x 12 removable corrosion-resistant shelf panel", ""), 2),
    (
        _hardware(
            "MOUNT-HARDWARE",
            "Stainless fasteners, pump vibration pads, ties and shelf brackets",
            "",
        ),
        1,
    ),
    (
        _hardware(
            "CONTROL-PROTECTION",
            "Transformer manufacturer-required primary/secondary protection and covered holder",
            "",
        ),
        1,
    ),
)

HARDWARE_PRODUCTS = tuple(product for product, _ in HARDWARE_QUANTITIES)
