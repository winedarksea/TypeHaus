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


def _dev(tag: str, name: str, prod: Product, *, ports=_P120, symbol="receptacle-duplex",
         footprint=(inch(4), inch(2)), height=inch(2), **facts) -> ElectricalDeviceType:
    rep = ModelRepresentation(symbol=symbol) if symbol else None
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
GFRBF = _prod("GFRBF-W", "SmartlockPro Slim blank-face GFCI, 20 A feed-through, white")
T5836 = _prod("T5836-W", "Decora duplex with 60 W USB-C PD, 20 A TR, white")
T5380 = _prod("T5380-W", "Decora surge duplex, 20 A TR, white",
              _LEV + "t5380")
T6525 = _prod("T6525-W", "Decora guide-light duplex, 15 A TR, white")
T5020 = _prod("T5020-W", "Decora single receptacle 5-20R, TR, white", "https://leviton.com/")
T5461 = _prod("T5461-W", "Decora 6-20R receptacle, 20 A 250 V, TR, white")
R278 = _prod("278", "30 A dryer receptacle 14-30R", _LEV + "278")
IN_USE = _prod("5980-UCL", "Extra-duty clear in-use cover")

# The in-use cover rides with the WR GFCI: its own product so the schedule prints both.
_DEEP = dict(footprint=(inch(4), inch(2)), height=inch(3))

# Boxes and covers are not on the types: the house's BoxStandard derives them from the face a
# device lands on (plan/device_boxes.py, decision #93), so one type serves drywall and concrete.

RECEPTACLE_TYPES = (
    _dev("ED-T-LEV-DUPLEX-20", "Lever Edge duplex 20 A TR (E5825-W)", E5825, nema="5-20R"),
    _dev("ED-T-LEV-DUPLEX-15", "Lever Edge duplex 15 A TR (E5325-W)", E5325, nema="5-15R"),
    _dev("ED-T-LEV-GFCI-20", "GFCI 20 A TR at the device (GFTR2-W)", GFTR2, nema="5-20R"),
    _dev("ED-T-LEV-GFCI-15", "GFCI 15 A TR at the device (GFTR1-W)", GFTR1, nema="5-15R"),
    _dev("ED-T-LEV-GFCI-ALARM", "GFCI 20 A TR, audible alarm (GFTA2-W)", GFTA2, nema="5-20R"),
    _dev("ED-T-LEV-GFCI-WR",
         "WR GFCI 20 A TR (GFWT2-W), 5980-UCL in-use cover, non-metallic gasketed box",
         GFWT2, footprint=(inch(4.5), inch(3)), height=inch(3), nema="5-20R",
         device_box=False),
    _dev("ED-T-LEV-GFCI-DF", "Blank-face GFCI 20 A, feed-through (GFRBF-W)", GFRBF,
         symbol=None, deadfront=True),
    _dev("ED-T-LEV-USBC", "Duplex with 60 W USB-C PD (T5836-W), deep box", T5836,
         nema="5-20R", **_DEEP),
    _dev("ED-T-LEV-SURGE", "Surge duplex 20 A TR (T5380-W)", T5380, nema="5-20R"),
    _dev("ED-T-LEV-GUIDE", "Guide-light duplex 15 A TR (T6525-W)", T6525, nema="5-15R"),
    _dev("ED-T-LEV-SINGLE-520", "Single 5-20R TR (T5020-W)", T5020, nema="5-20R",
         symbol="receptacle-single-120"),
    _dev("ED-T-LEV-620-DUPLEX",
         "2-gang: 6-20R (T5461-W) beside a 5-20R duplex (E5825-W)",
         T5461, ports=_PBOTH, footprint=(inch(4.5), inch(1)), height=inch(4.5),
         nema="5-20R/6-20R", symbol="receptacle-combined", gangs=2),
    _dev("ED-T-LEV-620-FLUSH",
         "2-gang: 6-20R (T5461-W) beside a 5-20R duplex (E5825-W), flush in drywall",
         T5461, ports=_PBOTH, footprint=(inch(4.5), inch(1)), height=inch(4.5),
         nema="5-20R/6-20R", symbol="receptacle-combined", gangs=2),
    _dev("ED-T-LEV-QUAD-520", "2-gang: two TR 5-20R duplexes (E5825-W)",
         E5825, footprint=(inch(4.5), inch(1)), height=inch(4.5), nema="5-20R",
         symbol="receptacle-quad", gangs=2),
    _dev("ED-T-LEV-620", "Single 6-20R, 240 V only (T5461-W)", T5461, ports=_P240,
         footprint=(inch(2.75), inch(1)), height=inch(4.5), nema="6-20R", load_va=3840,
         symbol="receptacle-240"),
    _dev("ED-T-LEV-RANGE-1450", "Range receptacle 14-50R (1450R)", None, ports=_P240,
         footprint=(inch(4), inch(4)), height=inch(4), nema="14-50R",
         symbol="receptacle-240-four-wire"),
    _dev("ED-T-LEV-DRYER-1430", "Dryer receptacle 14-30R (278)", R278, ports=_P240,
         footprint=(inch(4), inch(4)), height=inch(4), nema="14-30R", load_va=5000,
         symbol="receptacle-240-four-wire"),
)

# --- switches and controls ---------------------------------------------------------------
E5601 = _prod("E5601-W", "Lever Edge single-pole switch, white")
E5603 = _prod("E5603-W", "Lever Edge 3-way switch, white")
DIVA = _prod("DVCL-153P", "Diva LED+ dimmer, 150 W LED, single-pole/3-way", brand="Lutron",
             url="https://www.lutron.com/")
D215S = _prod("D215S-1BW", "Decora Smart 2nd Gen Matter switch, 15 A, 600 W LED",
              "https://www.leviton.com/en/products/d215s-1bw")
D2ELV = _prod("D2ELV-1BW", "Decora Smart 2nd Gen Matter ELV dimmer",
              "https://www.leviton.com/en/products/D2ELV-1BW")
DD0SR = _prod("DD0SR-DLZ", "Decora Smart wired companion for a 3-way (CONFIRM model)",
              "https://www.leviton.com/")
DOS02 = _prod("DOS02-LW", "Decora PIR occupancy sensor, 150 W LED, neutral optional")
ODS10 = _prod("ODS10-IDW", "PIR occupancy sensor, 10 A, LED-rated, no neutral",
              "https://leviton.com/products/ODS10-IDW")
MAT51 = _prod("MA-T51", "Maestro countdown timer, 5-60 min", brand="Lutron",
              url="https://www.lutron.com/")

SWITCH_TYPES = (
    _dev("ED-T-LEV-SW1", "Lever Edge single-pole switch (E5601-W)", E5601, symbol=None),
    _dev("ED-T-LEV-SW3", "Lever Edge 3-way switch (E5603-W)", E5603, symbol=None),
    _dev("ED-T-LUT-DIVA", "Lutron Diva dimmer (DVCL-153P), Claro plate", DIVA, symbol=None,
         control="dimmer"),
    _dev("ED-T-LEV-MATTER", "Matter switch, 15 A relay (D215S-1BW)", D215S, symbol=None,
         control="smart"),
    _dev("ED-T-LEV-MATTER-COMPANION", "Wired companion to a Matter switch (DD0SR-DLZ class)",
         DD0SR, symbol=None),
    _dev("ED-T-LEV-MATTER-ELV", "Matter ELV dimmer, reverse phase (D2ELV-1BW)", D2ELV,
         symbol=None, control="dimmer"),
    _dev("ED-T-LEV-OCC-PIR", "PIR occupancy sensor, same gang as a switch (DOS02-LW)", DOS02,
         symbol=None, control="occupancy"),
    _dev("ED-T-LEV-OCC-PANTRY",
         "PIR-only occupancy sensor, no neutral (ODS10-IDW); lens masked on its south half",
         ODS10,
         symbol=None, control="occupancy"),
    _dev("ED-T-LUT-COUNTDOWN", "Lutron Maestro countdown timer (MA-T51)", MAT51, symbol=None,
         control="timer"),
)

DEVICE_TYPES = (*RECEPTACLE_TYPES, *SWITCH_TYPES)
DEVICE_PRODUCTS = (
    E5825, E5325, GFTR2, GFTR1, GFTA2, GFWT2, GFRBF, T5836, T5380, T6525, T5020, T5461,
    R278, IN_USE, E5601, E5603, DIVA, D215S, D2ELV, DD0SR, DOS02, ODS10, MAT51,
)
