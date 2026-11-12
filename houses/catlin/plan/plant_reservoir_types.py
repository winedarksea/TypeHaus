"""Coordinated reservoir products and service envelopes; see notes/plant_reservoir.md.

Retail identities are separate from prices. Small hardware envelopes are approximate;
manufacturer facts, selection holds and commissioning limits live in the installation note.
"""

from typehaus import (
    ApplianceType,
    ModelRepresentation,
    Product,
    ProductPart,
    Service,
    ServicePort,
    inch,
)
from typehaus.model.plant_reservoir import RESERVOIR_GEOMETRY as G

from .plant_reservoir_hardware import HARDWARE_PRODUCTS, HARDWARE_QUANTITIES


def _product(tag, brand, model, name, url, source):
    return Product(
        tag=tag,
        brand=brand,
        model=model,
        name=name,
        url=url,
        source="Selection review 2026-11-11. " + source,
    )


TANK = _product(
    "PROD-RUBBERMAID-FG261000GRAY",
    "Rubbermaid Commercial",
    "FG261000GRAY",
    "BRUTE 10 US gal gray reservoir",
    "https://rcp.structpim.com/media/20254/brute-spec-sheet.pdf",
    "Maker sheet: 15.63 in body, 18 in over handles, 17.13 in rim. Current web "
    "catalog says 17.32 in: verify delivered rim before setting suction and low-water support.",
)
LID = _product(
    "PROD-RUBBERMAID-FG260900GRAY",
    "Rubbermaid Commercial",
    "FG260900GRAY",
    "BRUTE 10 gal removable lid, notched for top-entry suction",
    "https://www.rubbermaidcommercial.com/utility-refuse/brute-containers/",
    "Matching 10 gal lid; remove for attended filling and cleaning.",
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
    "itemized separately. Add downstream 200-mesh emitter filtration (RBY075MPTX).",
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
LEAK_CUTOFF = _product(
    "PROD-HYDROCHECK-WATERWATCHER",
    "HydroCheck",
    "WaterWatcher",
    "Packaged wired floor-leak appliance-power cutoff, qualification required",
    "https://www.hydrocheckproducts.com/product-page/waterwatcher-leak-detector",
    "Supplied revision, humidity suitability, dual-PSU inrush/load rating and dry/wet "
    "power recovery are purchasing holds. Product page and instructions disagree on "
    "rating/reset. Do not credit persistent fault memory across power interruption. "
    "One packaged sensor; controller is shown on rack and counted only here.",
)
LOW_WATER = _product(
    "PROD-MADISON-M8000-NO",
    "Madison",
    "M8000-NO",
    "Vertical normally-open low-water float, verify close-on-rise in installed orientation",
    "https://www.madisonsensor.com/std-min-lls-pp-flt-pp-stm-normally-open",
    "1 in float, 1/8 NPT mount. Switch RIBU1C 24 VAC coil only (46 mA maker rating). "
    "Low water or disconnected wire disables both pumps; refilling restores permission.",
)
RELAY = _product(
    "PROD-FUNCTIONAL-RIBU1C",
    "Functional Devices",
    "RIBU1C",
    "Enclosed SPDT automatic low-water pump-permission relay",
    "https://hosted.functionaldevices.com/downloads/datasheets/RIBU1C.pdf",
    "24 VAC coil through M8000-NO, COM/NO switches AC ahead of both timers. "
    "No ARM button or seal-in. Verify combined PSU load/inrush against contact rating; "
    "10 A resistive is not an arbitrary electronic-load rating. Noncondensing enclosure.",
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
RACK = _product(
    "PROD-PLANT-SERVICE-RACK",
    "Fabricated",
    "PLANT-RACK-36X12",
    "36 x 12 x 24 in corrosion-resistant equipment rack with dry enclosure",
    "https://www.functionaldevices.com/",
    "Pumps on lower ventilated shelf, mains controls in segregated dry enclosure. "
    "Equipment is removable without moving tank; rack geometry is design intent.",
)
PLANT_RESERVOIR_PRODUCTS = (
    TANK,
    LID,
    PUMP,
    PSU,
    TIMER,
    EMITTER,
    FILTER,
    EMITTER_FILTER,
    LEAK_CUTOFF,
    LOW_WATER,
    RELAY,
    TRANSFORMER,
    RACK,
    *HARDWARE_PRODUCTS,
)

PLANT_RESERVOIR = ApplianceType(
    tag="APPL-PLANT-RESERVOIR",
    name="Manually filled 10 gal lidded BRUTE reservoir",
    product_ref=TANK.tag,
    footprint=(inch(G.handle_width_in), inch(G.envelope_depth_in)),
    height=inch(G.installed_height_in),
    model_representation=ModelRepresentation(symbol="plant-reservoir"),
    parts=(
        ProductPart(role="cover_panel", product_ref=LID.tag),
        ProductPart(role="fitting", product_ref=LOW_WATER.tag),
    ),
    source="notes/plant_reservoir.md. No permanent domestic supply connection. "
    "Remove lid for attended filling with a removable potable tube secured above rim; "
    "disconnect tube afterward. Water marks and low-water mounting need field qualification.",
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
            (PUMP, 2),
            (PSU, 2),
            (TIMER, 2),
            (EMITTER, 24),
            (FILTER, 2),
            (EMITTER_FILTER, 2),
            (RELAY, 1),
            (TRANSFORMER, 1),
            *HARDWARE_QUANTITIES,
        )
    ),
    ports=(
        ServicePort(
            tag="power",
            service=Service.POWER_120,
            position=(inch(-17), inch(4), inch(16)),
            notes="Cord-only connection at WR GFCI RC6; controls mount in dry enclosure. "
            "Disconnect enclosure before servicing; transformer stays upstream of both cutoffs.",
        ),
    ),
    source="notes/plant_reservoir.md. Two pumps/timers are components, not separately billed "
    "appliances. Small equipment is shown as approximate service envelopes.",
)
LEAK_SENSORS = ApplianceType(
    tag="APPL-PLANT-WIRED-LEAK",
    name="One wired WaterWatcher floor sensor (controller on rack)",
    footprint=(inch(3), inch(3)),
    height=inch(1.3),
    model_representation=ModelRepresentation(symbol="plant-leak-sensors"),
    parts=(ProductPart(role="fitting", product_ref=LEAK_CUTOFF.tag),),
    source="Packaged cutoff counted once here. Floor sensor envelope approximate; qualify "
    "actual location by representative spills stopping BOTH pumps. "
    "AL-S-PLANT-LEAK remains a separate notification-only Zigbee sensor.",
)
PLANT_RESERVOIR_TYPES = (PLANT_RESERVOIR, IRRIGATION_RACK, LEAK_SENSORS)
