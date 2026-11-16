"""Receptacle, switch and control types: the owner's device schedule (2026-10-27).

Selection and reasons: ``notes/workshop_receptacles.md``. NOT editable (types are never
written back by a UI drag). Each type names its Leviton/Lutron ``Product``; the shared
``ED-T-*`` catalog cannot, so a house retypes its instances to these tags.
"""

from typehaus import (
    ElectricalDeviceType,
    Product,
    Service,
    ServicePort,
    ft,
    inch,
)
from typehaus.model import ModelRepresentation

_P120 = (ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),)
_P240 = (ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),)
_PBOTH = (
    ServicePort(tag="power-120", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),
    ServicePort(tag="power-240", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),
)
_DECISION = "Owner decision 2026-10-27, notes/workshop_receptacles.md."
_LEV = "https://leviton.com/products/"


def _prod(model: str, name: str, url: str | None = None, brand: str = "Leviton") -> Product:
    return Product(tag=f"PROD-{brand.upper()}-{model}", brand=brand, model=model, name=name,
                   url=url or _LEV + model.lower(), source=_DECISION)


# Geometry (notes/wiring_device_geometry.md): ``footprint`` is (face width, projection past
# the plate), ``height`` the face height; the plate and box are derived (BoxStandard).
# ``rear_projection`` is behind the strap, graded against box depth (NEC 314.24(B)).
_FACE = (inch(1.29), inch(0.05))  # Lever Edge Decora face, 0.30" past strap less a 1/4" plate
_FACE_H = inch(2.61)
_WHITE = {"device-face": "device-white"}


def _dev(tag: str, name: str, prod: Product, *, ports=_P120, symbol="receptacle-duplex",
         footprint=_FACE, height=_FACE_H, colour=_WHITE, **facts) -> ElectricalDeviceType:
    rep = ModelRepresentation(symbol=symbol, material_refs=colour) if symbol else None
    return ElectricalDeviceType(
        tag=tag, name=name, footprint=footprint, height=height, ports=ports,
        product_ref=prod.tag if prod else "PROD-LEVITON-1450R", model_representation=rep, source=_DECISION, **facts)


# --- receptacles -----------------------------------------------------------------------
E5825 = _prod("E5825-W", "Lever Edge duplex, 20 A, tamper-resistant, white")
E5325 = _prod("E5325-W", "Lever Edge duplex, 15 A, tamper-resistant, white")
GFTR2 = _prod("GFTR2-W", "Lever Edge SmartlockPro GFCI, 20 A, TR, white")
GFTR1 = _prod("GFTR1-W", "Lever Edge SmartlockPro GFCI, 15 A, TR, white")
GFTA2 = _prod("GFTA2-W", "SmartlockPro GFCI with audible alarm, 20 A, TR, white")
GFWT2 = _prod("GFWT2-W", "SmartlockPro GFCI, weather-resistant, 20 A, TR, white")
GFWT1 = _prod("GFWT1-W", "SmartlockPro GFCI, weather-resistant, 15 A, TR, white")
GFRBF = _prod("GFRBF-W", "SmartlockPro Slim blank-face GFCI, 20 A feed-through, white")
T5836 = _prod("T5836-W", "Decora duplex with 60 W USB-C PD, 20 A TR, white")
T5380 = _prod("T5380-W", "Decora surge duplex, 20 A TR, white",
              _LEV + "t5380")
T6525 = _prod("T6525-W", "Decora guide-light duplex, 15 A TR, white")
GFNL2 = _prod("GFNL2-W", "SmartlockPro GFCI with dusk-sensing LED guide light, 20 A TR, white")
T5020 = _prod("T5020-W", "Decora single receptacle 5-20R, TR, white", "https://leviton.com/")
T5461 = _prod("T5461-W", "Decora 6-20R receptacle, 20 A 250 V, TR, white")
R278 = _prod("278", "30 A dryer receptacle 14-30R", _LEV + "278")
IN_USE = _prod("5980-UCL", "Extra-duty clear in-use cover")

# The in-use cover rides with the WR GFCI: its own product so the schedule prints both.
_GFCI20 = dict(symbol="receptacle-gfci", footprint=(inch(1.29), inch(0.10)), height=inch(2.70),
               rear_projection=inch(1.03))  # SLIM GFCI drawing: 0.35" front, 1.03" rear
_SINGLE = dict(footprint=(inch(1.4), inch(0.07)), height=inch(1.4), plate="standard",
               plate_openings=("single",))  # round smooth-face body (not Decora), 80704-W

# Boxes and covers are not on the types: the house's BoxStandard derives them from the face a
# device lands on (plan/device_boxes.py, decision #93), so one type serves drywall and concrete.

RECEPTACLE_TYPES = (
    # E5825 has no drawing of its own: the E5325's 0.88" rear stands in (verify).
    _dev("ED-T-LEV-DUPLEX-20", "Lever Edge duplex 20 A TR (E5825-W)", E5825, nema="5-20R",
         rear_projection=inch(0.88)),
    # Behind the fridge and freezer: the plug sits inside the wall (box row use="recessed").
    # The body is the trim plate; its 1/4" proud of the gypsum is not published.
    _dev("ED-T-LEV-DUPLEX-20-REC", "Lever Edge duplex 20 A TR (E5825-W), recessed IN BOX",
         E5825, footprint=(inch(4.2), inch(0.25)), height=inch(6.698), nema="5-20R",
         box_use="recessed"),
    _dev("ED-T-LEV-DUPLEX-15", "Lever Edge duplex 15 A TR (E5325-W)", E5325, nema="5-15R",
         rear_projection=inch(0.88)),
    _dev("ED-T-LEV-GFCI-20", "GFCI 20 A TR at the device (GFTR2-W)", GFTR2, nema="5-20R",
         **_GFCI20),
    _dev("ED-T-LEV-GFCI-15", "GFCI 15 A TR at the device (GFTR1-W)", GFTR1, nema="5-15R",
         **{**_GFCI20, "footprint": (inch(1.29), inch(0.04))}),
    _dev("ED-T-LEV-GFCI-ALARM", "GFCI 20 A TR, audible alarm (GFTA2-W)", GFTA2, nema="5-20R",
         **{**_GFCI20, "footprint": (inch(1.29), inch(0.11)), "height": inch(2.71),
            "rear_projection": inch(1.07)}),
    # NEC 406.9: leviton.com GFWT2-W / GFWT1-W "Weather Resistant" (read 2026-11-14); 5980-UCL
    # "Extra Duty Weatherproof While-In-Use Cover", NEMA 3R. No 'controlled' marking on either.
    _dev("ED-T-LEV-GFCI-WR",
         "WR GFCI 20 A TR (GFWT2-W), 5980-UCL in-use cover, non-metallic gasketed box",
         GFWT2, footprint=(inch(4.5), inch(3)), height=inch(3), nema="5-20R",
         device_box=True, weather_resistant=True, in_use_cover=True),
    # On a 15 A branch (NEC 210.21(B)(3)): the radon fan's outlet on CKT-RC-ATTIC.
    _dev("ED-T-LEV-GFCI-WR-15",
         "WR GFCI 15 A TR (GFWT1-W), 5980-UCL in-use cover, non-metallic gasketed box",
         GFWT1, footprint=(inch(4.5), inch(3)), height=inch(3), nema="5-15R",
         device_box=False, weather_resistant=True, in_use_cover=True),
    _dev("ED-T-LEV-GFCI-DF", "Blank-face GFCI 20 A, feed-through (GFRBF-W)", GFRBF,
         deadfront=True, **{**_GFCI20, "symbol": "receptacle-blank-gfci"}),
    _dev("ED-T-LEV-USBC", "Duplex with 60 W USB-C PD (T5836-W), deep box", T5836,
         nema="5-20R", footprint=(inch(1.29), inch(0.07)), rear_projection=inch(1.50)),
    _dev("ED-T-LEV-SURGE", "Surge duplex 20 A TR (T5380-W)", T5380, nema="5-20R",
         footprint=(inch(1.29), inch(0.12)), height=inch(2.72), rear_projection=inch(1.19)),
    # T6525: no Leviton drawing; face assumed Lever Edge, rear not stated.
    _dev("ED-T-LEV-GUIDE", "Guide-light duplex 15 A TR (T6525-W)", T6525, nema="5-15R"),
    # A bath's night light (owner, 2026-11-03): the vanity GFCI's own ~1 W dusk guide light.
    _dev("ED-T-LEV-GFCI-GUIDE", "GFCI 20 A TR, dusk guide light (GFNL2-W)", GFNL2, nema="5-20R",
         **_GFCI20),
    # Rear scaled off the drawing (0.82"), so not authored.
    _dev("ED-T-LEV-SINGLE-520", "Single 5-20R TR, smooth face (T5020-W)", T5020, nema="5-20R",
         symbol="receptacle-single-120", **_SINGLE),
    # OPEN: a round T5461 beside a Decora E5825 takes a single + Decora plate, and the
    # BoxStandard has none, so integrity.device_plate is UNKNOWN until one is chosen.
    _dev("ED-T-LEV-620-DUPLEX",
         "2-gang: 6-20R (T5461-W) beside a 5-20R duplex (E5825-W)",
         T5461, ports=_PBOTH, footprint=(inch(3.10), inch(0.07)), height=_FACE_H,
         nema="5-20R/6-20R", symbol="receptacle-combined", gangs=2,
         plate_openings=("single", "decora"), rear_projection=inch(0.88)),
    _dev("ED-T-LEV-620-FLUSH",
         "2-gang: 6-20R (T5461-W) beside a 5-20R duplex (E5825-W), flush in drywall",
         T5461, ports=_PBOTH, footprint=(inch(3.10), inch(0.07)), height=_FACE_H,
         nema="5-20R/6-20R", symbol="receptacle-combined", gangs=2,
         plate_openings=("single", "decora"), rear_projection=inch(0.88)),
    _dev("ED-T-LEV-QUAD-520", "2-gang: two TR 5-20R duplexes (E5825-W)",
         E5825, footprint=(inch(3.10), inch(0.05)), nema="5-20R",
         symbol="receptacle-quad", gangs=2, rear_projection=inch(0.88)),
    _dev("ED-T-LEV-620", "Single 6-20R, 240 V only (T5461-W)", T5461, ports=_P240,
         nema="6-20R", load_va=3840, symbol="receptacle-240", rear_projection=inch(0.79),
         **_SINGLE),
    # Black round faces; the strap is the plate. Rears scaled off the drawings (1.80", ~1.9").
    _dev("ED-T-LEV-RANGE-1450", "Range receptacle 14-50R (1450R)", None, ports=_P240,
         footprint=(inch(2.43), inch(0.45)), height=inch(2.43), nema="14-50R",
         symbol="receptacle-round-50", colour={"device-face": "device-black"},
         plate="integral", rear_projection=inch(1.80)),
    _dev("ED-T-LEV-DRYER-1430", "Dryer receptacle 14-30R (278)", R278, ports=_P240,
         footprint=(inch(2.10), inch(0.42)), height=inch(2.10), nema="14-30R", load_va=5000,
         symbol="receptacle-round-30", colour={"device-face": "device-black"},
         plate="integral", rear_projection=inch(1.90)),
)

# --- switches and controls ---------------------------------------------------------------
E5601 = _prod("E5601-W", "Lever Edge single-pole switch, white")
E5603 = _prod("E5603-W", "Lever Edge 3-way switch, white")
DIVA = _prod("DVCL-153P", "Diva LED+ dimmer, 150 W LED, single-pole/3-way", brand="Lutron",
             url="https://www.lutron.com/")
# Reverse-phase, for the sauna's OMNIDRIVE X: on Diode LED's recommended-dimmer list.
DIVA_ELV = _prod("DVELV-300P", "Diva ELV dimmer, 300 W, reverse phase, single-pole",
                 brand="Lutron", url="https://www.lutron.com/")
# The D215S's successor (D215S discontinued): Matter out of the box.
D315S = _prod("D315S-1BW", "Decora Smart Wi-Fi switch, Matter, 15 A / 3 A LED",
              "https://www.leviton.com/products/d315s-1bw")
# Wire-free (battery, RF) companion: no hub, no wiring, no branch circuit. Leviton's page
# (read 2026-11-09, owner) lists the D315S as compatible; published range 50 ft.
DAWSC = Product(tag="PROD-LEVITON-DAWSC-1BW", brand="Leviton", model="DAWSC-1BW",
                name="Decora Smart wire-free companion switch, RF, battery",
                url="https://leviton.com/products/dawsc-1bw",
                source="Leviton page via owner, 2026-11-09: wire-free RF companion to the D315S "
                       "(listed compatible), no hub, 50 ft published range; surface or box "
                       "mount, battery.")
DOS02 = _prod("DOS02-LW", "Decora PIR occupancy sensor, 150 W LED, neutral optional")
ODS10 = _prod("ODS10-IDW", "PIR occupancy sensor, 10 A, LED-rated, no neutral",
              "https://leviton.com/products/ODS10-IDW")
MAT51 = _prod("MA-T51", "Maestro countdown timer, 5-60 min", brand="Lutron",
              url="https://www.lutron.com/")
# The lounge's scene keypad (2026-10-31): five buttons on the house's Z-Wave 800 LR stick,
# local in Z-Wave JS; its relay is unused (the loads are on their own D315S switches).
ZEN32 = _prod("ZEN32", "ZEN32 800LR scene controller, 5 buttons, Z-Wave", brand="Zooz",
              url="https://www.getzooz.com/zooz-zen32-scene-controller/")

# PV rapid-shutdown initiator (NEC 690.12(C)(1)(b): outdoors on a dwelling). The 12kPV keeps
# PV on its backup output when the grid drops, so the CL320 main does not initiate it; a switch
# on the inverter's RSD terminals does. EG4 Hybrid RSD Wiring Guide v1.0.3: normally closed,
# opening shuts down (the 12kPV QSG v1.3.2 still says NO; the factory RSD jumper says NC).
# ON = closed: one pole in the RSD loop, OFF initiates. 98 x 180 x 107 mm, -40 C.
RSD_INIT = Product(tag="PROD-IMO-ESS-RSD01", brand="IMO", model="ESS-RSD01",
                   name="Rapid shutdown initiator, 2-pole rotary, 48 VDC 10 A, NEMA 4X, "
                        "lockable, cULus",
                   url="https://www.solar-electric.com/lib/wind-sun/ESS-RSD01_Datasheet.pdf",
                   source="IMO datasheet ESS-RSD01 0426; also Fronius 42,0440,0338 ($93.40, "
                          "solar-electric.com, read 2026-11-13).")

# HVAC / spa disconnect (owner 2026-11-14: 60 A non-fused, NEMA 3R, lockable). Square D
# DU222RB data sheet (Jun 28 2026): general duty, non-fusible, 2 pole, 240 V AC, 60 A, NEMA 3R,
# 10 hp 1-phase, 7.75 W x 3.75 D x 9.63 H in, UL E2875. Lock OFF: Schneider FAQ FA95934,
# "Provision to padlock the operating handle in the OFF position is standard on all general
# duty safety switches." Check the date code against PRB-207512 (codes 1401-1803).
DU222RB = Product(tag="PROD-SQUARED-DU222RB", brand="Square D", model="DU222RB",
                  name="General duty safety switch, non-fusible, 2-pole, 60 A 240 V AC, NEMA 3R",
                  url="https://www.se.com/us/en/product/DU222RB/",
                  source="Schneider Electric product data sheet DU222RB, Jun 28 2026; "
                         "se.com FAQ FA95934 (padlock OFF)")

DISCONNECT_TYPES = (
    _dev("ED-T-SQD-DU222RB", "60 A non-fused NEMA 3R disconnect, lockable (DU222RB)", DU222RB,
         ports=_P240, symbol=None, footprint=(inch(7.75), inch(3.75)), height=inch(9.63),
         plan_symbol="disconnect", disconnect_rating_a=60, lockable=True),
)

SWITCH_TYPES = (
    # No power port and no box: a companion draws nothing from a circuit (device_box=False).
    ElectricalDeviceType(
        tag="ED-T-LEV-RF-COMPANION", name="Wire-free RF companion (DAWSC-1BW)",
        footprint=(inch(1.75), inch(0.6)), height=inch(2.9), needs=frozenset(), ports=(),
        device_box=False, control="smart", product_ref=DAWSC.tag, source=DAWSC.source),
    # Surface NEMA 4X enclosure: its own box (device_box=False), no power port (Class 2 loop).
    ElectricalDeviceType(
        tag="ED-T-RSD-INIT", name="PV rapid-shutdown initiator, NEMA 4X rotary (IMO ESS-RSD01)",
        footprint=(inch(3.875), inch(4.25)), height=inch(7.125), needs=frozenset(), ports=(),
        device_box=False, rsd_initiator=True, product_ref=RSD_INIT.tag, source=RSD_INIT.source),
    _dev("ED-T-LEV-SW1", "Lever Edge single-pole switch (E5601-W)", E5601,
         symbol="wall-switch-rocker", rear_projection=inch(1.01)),
    _dev("ED-T-LEV-SW3", "Lever Edge 3-way switch (E5603-W)", E5603,
         symbol="wall-switch-rocker", rear_projection=inch(1.01)),
    # Diva paddle projection is not published (0.10" assumed); Claro plate is 0.30".
    _dev("ED-T-LUT-DIVA", "Lutron Diva dimmer (DVCL-153P), Claro plate", DIVA,
         symbol="wall-switch-dimmer", footprint=(inch(1.29), inch(0.10)), control="dimmer",
         plate="claro", rear_projection=inch(1.31)),
    _dev("ED-T-LUT-DIVA-ELV", "Lutron Diva ELV dimmer, reverse phase (DVELV-300P)", DIVA_ELV,
         symbol="wall-switch-dimmer", footprint=(inch(1.29), inch(0.10)), control="dimmer"),
    _dev("ED-T-LEV-MATTER", "Matter switch, 15 A relay (D315S-1BW)", D315S,
         symbol="wall-switch-rocker", footprint=(inch(1.29), inch(0.04)), control="smart",
         rear_projection=inch(1.09)),
    _dev("ED-T-LEV-OCC-PIR", "PIR occupancy sensor, same gang as a switch (DOS02-LW)", DOS02,
         symbol="wall-switch-occupancy", footprint=(inch(1.29), inch(0.18)),
         control="occupancy", rear_projection=inch(0.95)),
    _dev("ED-T-LEV-OCC-PANTRY",
         "PIR-only occupancy sensor, no neutral (ODS10-IDW); lens masked on its south half",
         ODS10, symbol="wall-switch-occupancy", footprint=(inch(1.30), inch(0.23)),
         control="occupancy", rear_projection=inch(1.35)),
    # The MA-T51MNB sheet's 1 1/8" rear is not authored until the wired part is confirmed.
    _dev("ED-T-LUT-COUNTDOWN", "Lutron Maestro countdown timer (MA-T51)", MAT51,
         symbol="wall-switch-timer", footprint=(inch(1.29), inch(0.06)), control="timer"),
    # ZEN32 face and projection unpublished (1.16" total depth only).
    _dev("ED-T-ZOOZ-ZEN32", "Scene keypad, 5 buttons (Zooz ZEN32)", ZEN32,
         symbol="wall-switch-keypad", footprint=(inch(1.29), inch(0.10)), control="smart"),
)

DEVICE_TYPES = (*RECEPTACLE_TYPES, *SWITCH_TYPES, *DISCONNECT_TYPES)
DEVICE_PRODUCTS = (
    E5825, E5325, GFTR2, GFTR1, GFTA2, GFWT2, GFWT1, GFRBF, T5836, T5380, T6525, GFNL2, T5020,
    T5461, R278, IN_USE, E5601, E5603, DIVA, DIVA_ELV, D315S, DAWSC, DOS02, ODS10, MAT51, ZEN32,
    RSD_INIT, DU222RB,
)
