"""Smart-home device and appliance types: the local-only Home Assistant register.

NOT editable (types are never written back by a UI drag; ``needs`` is a ``frozenset``).
Instances live in ``plan/smart_home.py``. Rules, transports and the open verifications are
in ``notes/smart_home.md``; every product here must run with no vendor cloud after setup.
Facts read 2026-10-30 off the manufacturer pages named in each ``source``.
"""

from typehaus import (
    ApplianceType,
    ElectricalDeviceType,
    Product,
    Service,
    ServicePort,
    ft,
    inch,
    mm,
)
from typehaus.model import ModelRepresentation

_ORIGIN = (ft(0), ft(0), ft(0))
_P120 = (ServicePort(tag="power", service=Service.POWER_120, position=_ORIGIN),)
_P240 = (ServicePort(tag="power", service=Service.POWER_240, position=_ORIGIN),)
_DATA = (ServicePort(tag="data", service=Service.DATA, position=_ORIGIN),)
_NOTE = " Local-only register: notes/smart_home.md."

# --- products ------------------------------------------------------------------------------
REOLINK_DOORBELL = Product(
    tag="PROD-REOLINK-D340P", brand="Reolink", model="D340P",
    name="Video Doorbell PoE, 2K, black",
    url="https://reolink.com/product/reolink-video-doorbell-poe/",
    source="Reolink page, read 2026-10-30: 133 x 48 x 23 mm, 802.3af PoE (watts unpublished), "
           "IP65, black -10..50 C (14 F; owner accepts the cold limit). Core Reolink "
           "integration, local push; two-way talk is app-only. Plug-in Reolink Chime (433 MHz) "
           "or an HA announcement; no mechanical chime." + _NOTE)
REOLINK_OMVI_3I = Product(
    tag="PROD-REOLINK-OMVI-3I-POE", brand="Reolink", model="Omvi 3i PoE",
    name="Triple-lens 180 deg pan-tilt PoE camera",
    url="https://reolink.com/product/omvi-3i-poe/",
    source="Owner, 2026-11-02 (replaces the discontinued RLC-833A). Reolink page and power "
           "table, read 2026-11-02: 202 x 151 x 125 mm, 1.3 kg, 802.3at PoE+ (a 30 W port), "
           "20 W max, IR 30 m, IP66, -10..55 C; 180 x 65 deg panorama over a 55 deg tele lens, "
           "350 deg pan; wall, ceiling or corner bracket included. microSD to 512 GB, RTSP. "
           "Not in the core reolink integration's tested, certified or incompatible "
           "lists (home-assistant.io/integrations/reolink, read 2026-11-07): RTSP to HA "
           "locally is the path; Reolink's page lists RTSP/RTMP/HTTP(S), not ONVIF." + _NOTE)
REOLINK_DUO3 = Product(
    tag="PROD-REOLINK-DUO-3-POE", brand="Reolink", model="Duo 3 PoE",
    name="Dual-lens 180 deg PoE camera",
    url="https://reolink.com/product/reolink-duo-3-poe/",
    source="Reolink page, read 2026-10-30: 195 x 103 x 56 mm, <12 W, 802.3af, 180 x 55 deg "
           "field, IP67, -10..55 C. microSD on board; no NVR." + _NOTE)
LIFTMASTER_87504 = Product(
    tag="PROD-LIFTMASTER-87504-267", brand="LiftMaster", model="87504-267",
    name="Secure View belt-drive opener, Security+ 2.0, battery backup",
    url="https://www.garaga.com/garage-door-openers/residential/belt/87504-267",
    source="Replaces the discontinued 8550W (06-001). Owner's manual (Smart LED 87504-267/84501, "
           "read 2026-11-04): 'ONLY compatible with myQ and Security+ 2.0'; control panel on red/"
           "white terminals; 12 V 485LM battery. Garaga page: belt drive, battery backup, "
           "headroom 2 in. LiftMaster product guide: head 10.5 L x 18.7 W x 8.185 H in "
           "(30 in wide with the decorative doors open), 124 in installed with the 7 ft rail. "
           "ratgdo32 supports "
           "Security+ 2.0 (ratcloud / ratgdo docs); no 87504 report was found, and the manual "
           "never names the learn-button colour: CONFIRM yellow on arrival. Driven by a ratgdo32 "
           "on ESPHome; MyQ and its camera are never set up. Not Security+ 3.0 (white button)."
           + _NOTE)
GRIZZLE_SMART = Product(
    tag="PROD-GRIZZLE-SMART-40", brand="United Chargers", model="Grizzl-E Smart 40A, 14-50P",
    name="Grizzl-E Smart EVSE, 40 A (hardwired: 14-50P removed)",
    url="https://roulezelectrique.com/wp-content/uploads/2021/05/Grizzl-E_Smart_v9.pdf",
    source="Grizzl-E Smart v9 manual, read 2026-10-30: 10.25 x 6.25 x 3.75 in, NEMA 4, "
           "-30..50 C, 40 A default (DIP 16/24/32/40), OCPP 1.6 over Wi-Fi, 'UL Certified'. "
           "Manual documents removing the plug to hardwire (CCID is the ground-fault protection, no receptacle GFCI). Confirm the Smart's own UL file and OCPP 1.6J before buying. Runs against HA's "
           "OCPP integration (HACS lbbrhzn/ocpp) with no internet." + _NOTE)
KIDDE_SM120X = Product(
    tag="PROD-KIDDE-SM120X", brand="Kidde", model="SM120X",
    name="Smoke relay module, hardwired interconnect",
    url="https://kidde.com/home-safety/en/us/products/fire-safety/safety-accessories/"
        "auxiliary-devices/sm120x",
    source="Kidde UG_SM120X, read 2026-10-30: 120 VAC 0.03 A; Form C 10 A/120 VAC; trips on the "
           "SMOKE interconnect only, so CO needs the CO120X. In a listed junction box. Dry "
           "contact to an isolated input in ED-B-BACKUP-ENCL." + _NOTE)
KIDDE_CO120X = Product(
    tag="PROD-KIDDE-CO120X", brand="Kidde", model="CO120X",
    name="CO relay module, hardwired interconnect",
    url="https://www.kidde.com/",
    source="Kidde 810-1809 Rev. B, read 2026-10-30: 120 VAC 0.08 A; Form C 10 A/120 VAC; "
           "trips on the CO interconnect only; counts as one of the line's 24 devices." + _NOTE)
AQARA_W200 = Product(
    tag="PROD-AQARA-W200", brand="Aqara", model="SRT-A06E",
    name="Thermostat Hub W200",
    url="https://www.aqara.com/en/product/thermostat-hub-w200/",
    source="Aqara page, read 2026-10-30: 100 x 100 x 25 mm, 24 VAC 18-30 VA (C-wire), Matter, "
           "Wi-Fi 2.4/5 GHz, terminals Y2/Y3, W2/W3, AUX/E, O/B. Stage counts NOT published: "
           "bench one unit on the Gree AH before buying (plans/TODO.md)." + _NOTE)
WARMUP_7IE = Product(
    tag="PROD-WARMUP-7IE", brand="Warmup", model="7iE-04-CW-LC",
    name="7iE smart floor-heat thermostat, cloud white",
    url="https://www.warmup.com/wp-content/uploads/Warmup-TS-7iE-V1.0-2025-09-02_NAM-EN.pdf",
    source="Warmup NAM submittal, read 2026-10-30: Matter over Wi-Fi, 110-240 VAC, 15 A "
           "resistive, integral Class A GFCI (5 mA), 10 ft NTC10K floor sensor, ~114 x 90 mm "
           "face. Schluter cable warranty with a non-Schluter stat: ask in writing." + _NOTE)
SONOFF_SNZB_05P = Product(
    tag="PROD-SONOFF-SNZB-05P", brand="SONOFF", model="SNZB-05P",
    name="Zigbee 3.0 water leak sensor",
    url="https://sonoff.tech/products/sonoff-snzb-05p-zigbee-water-leak-sensor",
    source="SONOFF page and retailer listings, read 2026-11-08: 48 x 48 x 21.6 mm, 1 x CR2477, "
           "-10..60 C, Zigbee 3.0, probe contacts on the underside plus an optional cable "
           "probe. Pairs to ZHA on the Zigbee ZBT-2 with no SONOFF app or cloud; reports "
           "water_leak and battery. Retail, no quote." + _NOTE)
ARRE_TEMP = Product(
    tag="PROD-ARRE-TEMP-SENSOR", brand="arre", model="Temperature Sensor (Matter over Thread)",
    name="Thread temperature sensor, -40 to 185 F",
    url="https://arrehome.com/pages/arre-temp-sensor",
    source="arre product page, read 2026-11-14: operating range -40 to 85 C (-40 to 185 F), "
           "Matter certified, Thread, 1 x CR2032 (about a year), not waterproof, 'designed "
           "primarily for indoor use'. Matter over Thread to HA through the house's border "
           "router, no cloud. A coin cell sags in the cold: check it each autumn." + _NOTE)

# The hardwired interconnected heads (one Kidde line, 2026-10-30). Retail listings, no quote.
KIDDE_30CUA10_V = Product(
    tag="PROD-KIDDE-30CUA10-V", brand="Kidde", model="30CUA10-V",
    name="Smoke + CO alarm, hardwired, 10-yr sealed backup, voice",
    url="https://www.supplyhouse.com/Kidde-21032783-30CUA10-V-Hard-Wired-Carbon-Monoxide-and-"
        "Photoelectric-Smoke-Alarm-120-V-w-10-Year-Backup-Battery",
    source="Home Depot / SupplyHouse listings, read 2026-11-17: 5 in round x 1.88 in, "
           "120 VAC with a sealed 10-yr backup, photoelectric + electrochemical, interconnect "
           "(draw unpublished in the listings)." + _NOTE)
KIDDE_20SA10 = Product(
    tag="PROD-KIDDE-20SA10", brand="Kidde", model="20SA10",
    name="Smoke alarm, hardwired, 10-yr sealed backup",
    url="https://www.kidde.com/home-safety/en/us/products/fire-safety/detect-products/"
        "detect-smoke-alarm-hardwired-with-10-year-backup-battery-20SA10",
    source="Webstaurant listing (Kidde 21031556), read 2026-11-17: 5 in diameter x 2 in deep, "
           "120 VAC, photoelectric, interconnect." + _NOTE)
KIDDE_HD135F = Product(
    tag="PROD-KIDDE-HD135F", brand="Kidde", model="HD135F",
    name="Heat alarm, 135 F fixed temperature, hardwired, 9 V backup",
    url="https://kidde.com/home-safety/en/us/products/fire-safety/safety-accessories/"
        "auxiliary-devices/hd135",
    source="Kidde HD135F spec sheet, read 2026-11-17: 5 in diameter x 2 in deep, 120 VAC "
           "60 Hz, 9 V backup, 85 dB, up to 24 interconnected Kidde devices." + _NOTE)

SMART_HOME_PRODUCTS = (REOLINK_DOORBELL, REOLINK_OMVI_3I, REOLINK_DUO3, LIFTMASTER_87504,
                       GRIZZLE_SMART, KIDDE_SM120X, KIDDE_CO120X, AQARA_W200, WARMUP_7IE,
                       SONOFF_SNZB_05P, ARRE_TEMP, KIDDE_30CUA10_V, KIDDE_20SA10,
                       KIDDE_HD135F)

# --- low-voltage endpoints (DATA_OUTLET kind; PoE from the switch in ED-B-NET-PATCH) ----------
# 12.95 W is the 802.3af PD ceiling, used where the maker publishes no draw; the Duo 3
# publishes "<12 W" and the Omvi 3i 20 W.
_CAMERA = dict(ports=_DATA, ifc_entity="IfcAudioVisualAppliance", ifc_predefined_type="CAMERA")

DEVICE_TYPES = (
    ElectricalDeviceType(
        tag="ED-T-DOORBELL-POE", name="Video doorbell, PoE (Reolink D340P)",
        footprint=(inch(1.875), inch(0.875)), height=inch(5.25),
        product_ref=REOLINK_DOORBELL.tag, poe_watts=12.95, source=REOLINK_DOORBELL.source,
        **_CAMERA),
    # Product photo orientation: 202 mm high, 151 mm wide, 125 mm deep.
    # PoE+: the only port on ED-B-NET-PATCH's switch that needs 802.3at.
    ElectricalDeviceType(
        tag="ED-T-CAM-PANTILT", name="PoE+ pan-tilt camera, 180 deg (Reolink Omvi 3i)",
        footprint=(mm(151), mm(125)), height=mm(202),
        model_representation=ModelRepresentation(symbol="reolink-omvi-3i-ceiling"),
        product_ref=REOLINK_OMVI_3I.tag, poe_watts=20.0, source=REOLINK_OMVI_3I.source,
        **_CAMERA),
    # Body 195 x 56 mm in plan; the depth carries the mount bracket under a beam soffit.
    ElectricalDeviceType(
        tag="ED-T-CAM-WIDE", name="PoE 180-degree camera (Reolink Duo 3 PoE)",
        footprint=(inch(7.75), inch(3.5)), height=inch(4.25),
        product_ref=REOLINK_DUO3.tag, poe_watts=12.0, source=REOLINK_DUO3.source, **_CAMERA),
    # --- controls --------------------------------------------------------------------------
    # 24 VAC from EQ-S-HP1-AH's control board, Class 2: no branch circuit, no port, no box.
    ElectricalDeviceType(
        tag="ED-T-HP-STAT", name="Heat-pump thermostat, 24 VAC, Matter (Aqara W200)",
        model_representation=ModelRepresentation(symbol="thermostat"),
        footprint=(inch(3.94), inch(0.875)), height=inch(3.94), needs=frozenset(), ports=(),
        device_box=False, product_ref=AQARA_W200.tag, source=AQARA_W200.source),
    # Replaces the library ED-T-FLOOR-STAT on all three zones; line voltage, own GFCI.
    ElectricalDeviceType(
        tag="ED-T-FLOOR-STAT-WARMUP", name="Floor-heat thermostat, 120 V, Matter, GFCI (7iE)",
        model_representation=ModelRepresentation(symbol="thermostat"),
        footprint=(inch(4.5), inch(0.875)), height=inch(3.5), ports=_P120,
        product_ref=WARMUP_7IE.tag, source=WARMUP_7IE.source),
    # The relay rides in its own listed 4" box, so the type is the box: no derived box.
    ElectricalDeviceType(
        tag="ED-T-ALARM-RELAY-SMOKE", name="Smoke interconnect relay, 4\" box (Kidde SM120X)",
        footprint=(inch(4), inch(2.125)), height=inch(4), ports=_P120, load_va=3.6,
        plan_symbol="junction-box", device_box=False, product_ref=KIDDE_SM120X.tag,
        source=KIDDE_SM120X.source),
    ElectricalDeviceType(
        tag="ED-T-ALARM-RELAY-CO", name="CO interconnect relay, 4\" box (Kidde CO120X)",
        footprint=(inch(4), inch(2.125)), height=inch(4), ports=_P120, load_va=9.6,
        plan_symbol="junction-box", device_box=False, product_ref=KIDDE_CO120X.tag,
        source=KIDDE_CO120X.source),
    # Alarm heads: an Alarm's ``type_ref`` (kind stays on the Alarm). Round heads are cylinders.
    ElectricalDeviceType(
        tag="ED-T-ALARM-COMBO-KIDDE", name="Smoke/CO alarm, 120 V interconnect (Kidde 30CUA10-V)",
        footprint=(inch(5), inch(5)), height=inch(1.88), ports=_P120, device_box=False,
        model_representation=ModelRepresentation(primitive="cylinder"),
        product_ref=KIDDE_30CUA10_V.tag, source=KIDDE_30CUA10_V.source),
    ElectricalDeviceType(
        tag="ED-T-ALARM-SMOKE-KIDDE", name="Smoke alarm, 120 V interconnect (Kidde 20SA10)",
        footprint=(inch(5), inch(5)), height=inch(2), ports=_P120, device_box=False,
        model_representation=ModelRepresentation(primitive="cylinder"),
        product_ref=KIDDE_20SA10.tag, source=KIDDE_20SA10.source),
    ElectricalDeviceType(
        tag="ED-T-ALARM-HEAT-KIDDE", name="Heat alarm 135 F, 120 V interconnect (Kidde HD135F)",
        footprint=(inch(5), inch(5)), height=inch(2), ports=_P120, device_box=False,
        model_representation=ModelRepresentation(primitive="cylinder"),
        product_ref=KIDDE_HD135F.tag, source=KIDDE_HD135F.source),
    ElectricalDeviceType(
        tag="ED-T-LEAK-SNZB05P", name="Water leak sensor, Zigbee, battery (SONOFF SNZB-05P)",
        footprint=(inch(48 / 25.4), inch(48 / 25.4)), height=inch(21.6 / 25.4),
        needs=frozenset(), device_box=False,
        product_ref=SONOFF_SNZB_05P.tag, source=SONOFF_SNZB_05P.source),
    ElectricalDeviceType(
        tag="ED-T-FREEZE-ARRE", name="Temperature sensor, Thread, battery (arre)",
        footprint=(inch(40 / 25.4), inch(40 / 25.4)), height=inch(10.2 / 25.4),
        needs=frozenset(), device_box=False,
        product_ref=ARRE_TEMP.tag,
        source=ARRE_TEMP.source + " Body 40 x 40 x 10.2 mm (arre page, read 2026-11-17)."),
)

# --- appliances: equipment the house names but does not wire in --------------
APPLIANCE_TYPES = (
    ApplianceType(
        tag="APPL-LIFTMASTER-87504-267",
        name="Garage door opener, belt trolley (LiftMaster 87504-267)",
        product_ref=LIFTMASTER_87504.tag, footprint=(inch(18.7), inch(10.5)), height=inch(8.185),
        model_representation=ModelRepresentation(symbol="liftmaster-87504-267-7ft"),
        needs=frozenset({Service.POWER_120}), ports=_P120, source=LIFTMASTER_87504.source),
    ApplianceType(
        tag="APPL-GRIZZLE-SMART-40", name="EVSE, 40 A hardwired (Grizzl-E Smart, plug removed)",
        product_ref=GRIZZLE_SMART.tag, footprint=(inch(6.25), inch(3.75)),
        height=inch(10.25), needs=frozenset({Service.POWER_240}), ports=_P240,
        # 625.50: the EasyEvPlug holster ships loose, "any location near the charging
        # station" (manual v9 §7); placed beside the unit at its 42 in. AFF (a default).
        connector_holster_height=inch(42),
        source=GRIZZLE_SMART.source),
)
