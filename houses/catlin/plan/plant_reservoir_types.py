"""Coordinated reservoir products and service envelopes; see notes/plant_reservoir.md.

Retail identities are separate from prices. Small hardware envelopes are approximate;
manufacturer facts, selection holds and commissioning limits live in the installation note.
"""

from typehaus import (
    ApplianceType,
    ModelRepresentation,
    PortCertainty,
    Product,
    ProductPart,
    Service,
    ServicePort,
    inch,
)
from typehaus.model.plant_reservoir import RESERVOIR_GEOMETRY as G


def _product(tag, brand, model, name, url, source):
    return Product(
        tag=tag,
        brand=brand,
        model=model,
        name=name,
        url=url,
        source="Selection review 2026-11-10. " + source,
    )


TANK = _product(
    "PROD-RUBBERMAID-FG261000GRAY",
    "Rubbermaid Commercial",
    "FG261000GRAY",
    "BRUTE 10 US gal gray reservoir",
    "https://rcp.structpim.com/media/20254/brute-spec-sheet.pdf",
    "Maker sheet: 15.63 in body, 18 in over handles, 17.13 in rim. Current web "
    "catalog says 17.32 in: verify delivered rim before fixing the bracket.",
)
LID = _product(
    "PROD-RUBBERMAID-FG260900GRAY",
    "Rubbermaid Commercial",
    "FG260900GRAY",
    "BRUTE 10 gal snap-on lid, notched for independent fill bracket and suction",
    "https://www.rubbermaidcommercial.com/utility-refuse/brute-containers/",
    "Matching 10 gal lid; field notches do not support the float bracket.",
)
FLOAT_VALVE = _product(
    "PROD-KERICK-MA252",
    "Control Devices / Kerick",
    "MA252",
    "1/4 in OD tubing mini float valve with adjustable arm",
    "https://www.cdivalve.com/products/detail/kerick-m-series-float-valves",
    "PVC, adjustable arm, tubing compression inlet. Material suitability "
    "does not establish a potable-water assembly listing: AHJ hold. "
    "Open-position plunger drips must land inside the reservoir.",
)
FILL_SHUTOFF = _product(
    "PROD-FLOODSTOP-FS14C",
    "IPS / FloodStop",
    "20020 / FS14C",
    "1/4 in compression electric fill shutoff, wired sensor and controller",
    "https://ipsplumbingproducts.com/brands/floodstop/floodstop-installation-instructions/",
    "Kit includes motorized valve, controller, sensor, adapter. Four AA "
    "backup batteries; valve stays closed after a leak until manually opened. "
    "Auxiliary interface is NOT assumed to be a latched pump safety output.",
)
NEEDLE = _product(
    "PROD-JOHNGUEST-PPSV040808W",
    "John Guest",
    "PPSV040808W",
    "1/4 in OD push-fit straight shutoff, fill throttling service",
    "https://www.johnguest.com/us/en/",
    "Potable-system fitting; commissioning throttle to <=0.1 gpm across supply "
    "pressure range. A ball valve is not a pressure-independent flow limiter.",
)
PUMP = _product(
    "PROD-SHURFLO-8000-543-210",
    "Pentair SHURflo",
    "8000-543-210",
    "12 V DC 35 psi internal-bypass irrigation pump",
    "https://www.pentair.com/en-us/flow/commercial-products/water-supply-pumps/spray-pumps/8000_series_diaphgram_pumps.html",
    "Current maker row: 1.35 GPM open flow, 7 A max, 35 psi bypass, 3/8 in NPT. "
    "Older catalog: 1.3 GPM, 5.5 A. Size power for current 7 A; no pressure switch "
    "cycling at the 6 GPH zone demand. 9 x 4.5 x 4.5 in service envelope, "
    "not a mounting template; verify I-18 drawing before drilling.",
)
PSU = _product(
    "PROD-MEANWELL-GST120A12-R7B",
    "MEAN WELL",
    "GST120A12-R7B",
    "12 V DC 8.5 A desktop pump supply, 4-pin locking connector",
    "https://www.meanwell.com/Upload/PDF/gst120a/gst120a-spec.pdf",
    "Maker: 167 x 67 x 35 mm; 102 W at 12 V. One per pump. Use mating Kycon "
    "KPPX-4P harness, correct parallel pin pairs, OEM-sized fuse and grounded C13 lead. "
    "Verify motor starting against current-limit protection in commissioning.",
)
TIMER = _product(
    "PROD-HYDROFARM-TM01715D",
    "Hydrofarm",
    "TM01715D",
    "Local digital seven-day seconds-resolution timer; one per zone",
    "https://s3.amazonaws.com/hydrofarmpubdocs/tm01715d_instructions.pdf",
    "Separate units give independent schedules; both outlets on one unit share "
    "the same program. Wall-mount inside dry equipment enclosure, not at RC6.",
)
EMITTER = _product(
    "PROD-RAINBIRD-XB05PC",
    "Rain Bird",
    "XB05PC",
    "Xeri-Bug pressure-compensating emitter, 0.5 GPH",
    "https://www.rainbird.com/professionals/specifier/emission-devices-bubblers",
    "Maker range 15-50 psi. Two zones of 12. Verify >=15 psi at the highest "
    "emitter with all twelve running; bypass pump bounds pressure below 50 psi.",
)
FILTER = _product(
    "PROD-SHURFLO-255-323",
    "Pentair SHURflo",
    "255-323",
    "Twist-on pump inlet strainer, 1/2 in barb inlet x NPSM outlet",
    "https://www.pentair.com/en-us/products/business-industry/accessories/recreational-vehicle-plumbing-accessories/strainers/sku/255-323.html",
    "One per pump; adapters to pump 3/8 NPT and reinforced suction hose are "
    "in the fitting package. Add downstream 200-mesh emitter filtration (RBY075MPTX).",
)
EMITTER_FILTER = _product(
    "PROD-RAINBIRD-RBY075MPTX",
    "Rain Bird",
    "RBY075MPTX",
    "3/4 in MPT inline filter with 200-mesh screen",
    "https://www.rainbird.com/professionals/specifier/zone-filters-pressure-regulators",
    "Maker specifies 200-mesh screen; no pressure-regulator function is assumed. "
    "Adapt male pipe threads to distribution tube; one filter per zone. "
    "Service envelope is approximate pending delivered housing.",
)
WET_SWITCH = _product(
    "PROD-DIVERSITECH-WS1",
    "DiversiTech",
    "WS-1",
    "24 VAC manual-reset wired floor wet switch",
    "https://media.diversitech.com/doc/doc00036.pdf",
    "Wet event opens healthy control circuit and latches until dry/reset. "
    "Co-locate with FloodStop sensor; test water travel to BOTH sensors. "
    "Manual power interruption can reset this detector: inspect before rearming.",
)
LOW_WATER = _product(
    "PROD-MADISON-M8000",
    "Madison",
    "M8000",
    "Reversible vertical float switch, closed only above low-water mark",
    "https://www.madisonsensor.com/m8000-single-point-level-switch",
    "1 in float, 1/8 NPT mount; reverse float for close-on-rise. Control "
    "relay coil only. Open wire or low water disables pumps, not refill.",
)
RELAY = _product(
    "PROD-FUNCTIONAL-RIB2401D",
    "Functional Devices",
    "RIB2401D",
    "Enclosed 10 A DPDT manual-arm pump-permit relay, 24 VAC coil",
    "https://hosted.functionaldevices.com/downloads/datasheets/RIB2401D.pdf",
    "One NO pole seals in through momentary ARM button; second NO pole switches AC. "
    "WS-1 healthy output "
    "and M8000 series contact interrupt seal-in coil; power loss requires manual ARM. Switch AC, "
    "not motor current through the float. Segregate mains/control wiring.",
)
TRANSFORMER = _product(
    "PROD-FUNCTIONAL-TR40VA001",
    "Functional Devices",
    "TR40VA001",
    "120-to-24 VAC 40 VA control transformer",
    "https://hosted.functionaldevices.com/downloads/datasheets/TR40VA001.pdf",
    "Permanently powered control supply inside enclosed electrical assembly; "
    "manufacturer fuse/protection and Class 2 wiring requirements apply.",
)
BRACKET = _product(
    "PROD-PLANT-FLOAT-BRACKET",
    "Fabricated",
    "PLANT-FILL-BRACKET-304",
    "304 stainless rim saddle and slotted independent float bracket",
    "https://www.cdivalve.com/products/detail/kerick-m-series-float-valves",
    "Field-fitted saddle, no penetrations below rim. Hold discharge 2 in above "
    "delivered rim while float closes at calibrated 9 gal mark. Check full arm "
    "travel on delivered MA252 before fabrication; shown setout is approximate.",
)
RACK = _product(
    "PROD-PLANT-SERVICE-RACK",
    "Fabricated",
    "PLANT-RACK-36X12",
    "36 x 12 x 24 in corrosion-resistant equipment rack with dry enclosure",
    "https://www.functionaldevices.com/",
    "Pumps on lower ventilated shelf, mains controls in segregated dry enclosure. "
    "Equipment is removable without moving tank; rack geometry is design intent.",
)
FITTINGS = _product(
    "PROD-PLANT-IRRIGATION-FITTINGS",
    "Commodity",
    "PLANT-TWO-ZONE-FITTINGS",
    "Two-zone tubing, filter adapters, wiring and mounting package",
    "https://www.rainbird.com/professionals/specifier/emission-devices-bubblers",
    "Schedule in notes/plant_reservoir.md: pressure-rated tubing, filter "
    "filters, suction adapters, strain relief, fused harnesses and cord leads. "
    "Commodity package is an allowance, not an exact purchased kit.",
)

PLANT_RESERVOIR_PRODUCTS = (
    TANK,
    LID,
    FLOAT_VALVE,
    FILL_SHUTOFF,
    NEEDLE,
    PUMP,
    PSU,
    TIMER,
    EMITTER,
    FILTER,
    EMITTER_FILTER,
    WET_SWITCH,
    LOW_WATER,
    RELAY,
    TRANSFORMER,
    BRACKET,
    RACK,
    FITTINGS,
)

PLANT_RESERVOIR = ApplianceType(
    tag="APPL-PLANT-RESERVOIR",
    name="10 gal lidded BRUTE reservoir; independent float-fill bracket",
    product_ref=TANK.tag,
    footprint=(inch(G.handle_width_in), inch(G.envelope_depth_in)),
    height=inch(G.installed_height_in),
    model_representation=ModelRepresentation(symbol="plant-reservoir"),
    # Keep the visual symbol separate from the domestic fixture-unit vocabulary.
    needs=frozenset({Service.WATER_COLD}),
    parts=(
        ProductPart(role="cover_panel", product_ref=LID.tag),
        ProductPart(role="fitting", product_ref=FLOAT_VALVE.tag),
        ProductPart(role="fitting", product_ref=BRACKET.tag),
        ProductPart(role="fitting", product_ref=LOW_WATER.tag),
    ),
    ports=(
        ServicePort(
            tag="supply",
            service=Service.WATER_COLD,
            position=(inch(0), inch(6.5), inch(G.inlet_height_in)),
            connection_size=inch(0.25),
            certainty=PortCertainty.APPROXIMATE,
            hose_length=inch(48),
            notes="Valve INLET, not discharge or air gap. "
            "Discharge coordinates and delivered-rim verification in the reservoir note.",
        ),
    ),
    source="notes/plant_reservoir.md. Published body plus handle envelope; bracket setout and "
    "water marks require field qualification. Lid lifts separately from float bracket.",
)
IRRIGATION_RACK = ApplianceType(
    tag="APPL-PLANT-IRRIGATION-RACK",
    name="Two local irrigation zones with wired pump safety cutoff",
    product_ref=RACK.tag,
    footprint=(inch(G.rack_width_in), inch(G.rack_depth_in)),
    height=inch(G.rack_height_in),
    model_representation=ModelRepresentation(symbol="plant-irrigation-rack"),
    needs=frozenset({Service.POWER_120}),
    parts=tuple(
        ProductPart(role="fitting", product_ref=product.tag, quantity=count)
        for product, count in (
            (FILL_SHUTOFF, 1),
            (NEEDLE, 1),
            (PUMP, 2),
            (PSU, 2),
            (TIMER, 2),
            (EMITTER, 24),
            (FILTER, 2),
            (EMITTER_FILTER, 2),
            (RELAY, 1),
            (TRANSFORMER, 1),
            (FITTINGS, 1),
        )
    ),
    ports=(
        ServicePort(
            tag="power",
            service=Service.POWER_120,
            position=(inch(-17), inch(4), inch(16)),
            notes="Cord-only connection at WR GFCI RC6; controls mount in dry enclosure. "
            "Disconnect enclosure before servicing; safety supplies stay unswitched.",
        ),
    ),
    source="notes/plant_reservoir.md. Two pumps/timers are components, not separately billed "
    "appliances. Small equipment is shown as approximate service envelopes.",
)
LEAK_SENSORS = ApplianceType(
    tag="APPL-PLANT-WIRED-LEAK",
    name="Co-located wired fill and pump floor leak detectors",
    footprint=(inch(6), inch(3)),
    height=inch(1.3),
    model_representation=ModelRepresentation(symbol="plant-leak-sensors"),
    parts=(ProductPart(role="fitting", product_ref=WET_SWITCH.tag),),
    source="FloodStop sensor is included in its kit on the rack; WS-1 is counted here. "
    "These are distinct from AL-S-PLANT-LEAK's notification-only Zigbee sensor.",
)
FILL_VALVE_COMPONENT = ApplianceType(
    tag="APPL-PLANT-FILL-VALVE",
    name="FloodStop valve at manual stop (included in rack's kit)",
    footprint=(inch(3), inch(2)),
    height=inch(3),
    model_representation=ModelRepresentation(symbol="plant-fill-shutoff"),
    source="Visual component only: FS14C kit is counted once on the rack. Fit directly on "
    "the manual stop, before every flexible fill hose. Envelope approximate.",
)
PLANT_RESERVOIR_TYPES = (PLANT_RESERVOIR, IRRIGATION_RACK, LEAK_SENSORS, FILL_VALVE_COMPONENT)
