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
)

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
REOLINK_TURRET = Product(
    tag="PROD-REOLINK-RLC-833A", brand="Reolink", model="RLC-833A",
    name="4K PoE turret camera, IR 30 m",
    url="https://reolink.com/product/rlc-833a/",
    source="Reolink page, read 2026-10-30: 117.4 x 103.8 mm, <12 W, 802.3af, IR 30 m, IP67. "
           "Marked DISCONTINUED: buy the current 4K PoE turret of the same envelope "
           "(RLC-833A class). microSD on board; core Reolink integration." + _NOTE)
REOLINK_DUO3 = Product(
    tag="PROD-REOLINK-DUO-3-POE", brand="Reolink", model="Duo 3 PoE",
    name="Dual-lens 180 deg PoE camera",
    url="https://reolink.com/product/reolink-duo-3-poe/",
    source="Reolink page, read 2026-10-30: 195 x 103 x 56 mm, <12 W, 802.3af, 180 x 55 deg "
           "field, IP67, -10..55 C. microSD on board; no NVR." + _NOTE)
LIFTMASTER_8550W = Product(
    tag="PROD-LIFTMASTER-8550W", brand="LiftMaster", model="8550W",
    name="Elite belt-drive opener, Security+ 2.0 (yellow learn button)",
    url="https://support.chamberlaingroup.com/s/article/LiftMaster-Garage-Door-Opener-Models-"
        "8550W-8550WL-8550WLB-8550WLB-267-8557W-WLED-WLED-267-85503-85503-267-8587W-8587WL-"
        "and-8580WLB-Owner-s-Manual",
    source="Chamberlain support, read 2026-10-30: Security+ 2.0, yellow learn button. Driven by "
           "a ratgdo32 on ESPHome; MyQ is never set up. Not Security+ 3.0 (white button), not "
           "the 8500/RJ020 jackshaft. Head size and headroom NOT read (manual is a viewer "
           "shell): the envelope is an allowance." + _NOTE)
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
ZOOZ_ZAC36 = Product(
    tag="PROD-ZOOZ-ZAC36-LR", brand="Zooz", model="ZAC36 LR",
    name="Titan water valve actuator, Z-Wave Long Range, wired leak probe",
    url="https://apolloautomation.com/products/"
        "zooz-z-wave-long-range-700-series-titan-water-valve-actuator-zac36-lr",
    source="Retailer listing, read 2026-10-30 (Zooz pages did not load): clamps a quarter-turn "
           "lever ball valve; 12 VDC 1 A plug-in adapter; the wired probe closes the valve with "
           "no hub. Optional backup battery pack. Envelope is an allowance until the manual "
           "is read." + _NOTE)

SMART_HOME_PRODUCTS = (REOLINK_DOORBELL, REOLINK_TURRET, REOLINK_DUO3, LIFTMASTER_8550W,
                       GRIZZLE_SMART, KIDDE_SM120X, KIDDE_CO120X, AQARA_W200, WARMUP_7IE,
                       ZOOZ_ZAC36)

# --- low-voltage endpoints (DATA_OUTLET kind; PoE from the switch in ED-B-NET-PATCH) ----------
# 12.95 W is the 802.3af PD ceiling, used where the maker publishes no draw; the two cameras
# publish "<12 W".
_CAMERA = dict(ports=_DATA, ifc_entity="IfcAudioVisualAppliance", ifc_predefined_type="CAMERA")

DEVICE_TYPES = (
    ElectricalDeviceType(
        tag="ED-T-DOORBELL-POE", name="Video doorbell, PoE (Reolink D340P)",
        footprint=(inch(1.875), inch(0.875)), height=inch(5.25),
        product_ref=REOLINK_DOORBELL.tag, poe_watts=12.95, source=REOLINK_DOORBELL.source,
        **_CAMERA),
    ElectricalDeviceType(
        tag="ED-T-CAM-TURRET", name="PoE turret camera, 4K (RLC-833A class)",
        footprint=(inch(4.625), inch(4.625)), height=inch(4.125),
        product_ref=REOLINK_TURRET.tag, poe_watts=12.0, source=REOLINK_TURRET.source,
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
        footprint=(inch(3.94), inch(0.875)), height=inch(3.94), needs=frozenset(), ports=(),
        device_box=False, product_ref=AQARA_W200.tag, source=AQARA_W200.source),
    # Replaces the library ED-T-FLOOR-STAT on all three zones; line voltage, own GFCI.
    ElectricalDeviceType(
        tag="ED-T-FLOOR-STAT-WARMUP", name="Floor-heat thermostat, 120 V, Matter, GFCI (7iE)",
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
)

# --- appliances: equipment the house names but does not wire in --------------
APPLIANCE_TYPES = (
    ApplianceType(
        tag="APPL-LIFTMASTER-8550W", name="Garage door opener, belt trolley (LiftMaster 8550W)",
        product_ref=LIFTMASTER_8550W.tag, footprint=(inch(13), inch(20)), height=inch(8),
        needs=frozenset({Service.POWER_120}), ports=_P120, source=LIFTMASTER_8550W.source),
    ApplianceType(
        tag="APPL-GRIZZLE-SMART-40", name="EVSE, 40 A hardwired (Grizzl-E Smart, plug removed)",
        product_ref=GRIZZLE_SMART.tag, footprint=(inch(6.25), inch(3.75)),
        height=inch(10.25), needs=frozenset({Service.POWER_240}), ports=_P240,
        source=GRIZZLE_SMART.source),
    ApplianceType(
        tag="APPL-ZOOZ-ZAC36", name="Leak shutoff actuator on a lever ball valve (Zooz ZAC36)",
        product_ref=ZOOZ_ZAC36.tag, footprint=(inch(4), inch(3.5)), height=inch(5),
        needs=frozenset({Service.POWER_120}), ports=_P120, source=ZOOZ_ZAC36.source),
)
