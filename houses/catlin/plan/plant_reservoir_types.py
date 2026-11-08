"""RM-S-PLANT's drip reservoir: the chosen retail parts and the one appliance type.

NOT ``# haus: editable`` (``needs`` is a frozenset, which the dialect forbids); the placed
instance is ``plan/plant_reservoir.py``. Design, code reading and sizing:
``notes/plant_reservoir.md``. Every number below was read from a retailer or maker page on
2026-11-07 and is marked where a sheet was not seen. Identity only, never a price (#28).
"""

from __future__ import annotations

from typehaus import ApplianceType, PortCertainty, Product, Service, ServicePort, inch

TANK = Product(
    tag="PROD-RUBBERMAID-FG261000GRAY", brand="Rubbermaid Commercial", model="FG261000GRAY",
    name="BRUTE 10 gal round container, gray",
    source="Retailer listings, read 2026-11-07: 10 gal, 15 5/8 in. dia x 17 1/8 in. high "
           "(Hillyard says 17.32 in.). Rim = flood level; the 10 gal rating is the "
           "reservoir's whole volume (UPC 603.5.5 tank).")
FLOAT_VALVE = Product(
    tag="PROD-DIAL-4154", brand="Dial", model="4154",
    name='1/4 in. brass compression float valve (evaporative-cooler type)',
    url="https://www.homedepot.com/p/p/100560907",
    source="Home Depot #100560907, read 2026-11-07: brass body/arm/stem, 1/4 in. compression "
           "inlet, polypropylene float; open-orifice outlet, so the air gap is the valve's own "
           "spout above the rim. Orifice ~0.2 in. (assumed): effective opening < 1/2 in.")
PUMP = Product(
    tag="PROD-SEAFLO-SFDP1-012-035-21", brand="SEAFLO", model="SFDP1-012-035-21",
    name="21 Series 12 V diaphragm pump, 1.2 GPM, 35 psi",
    source="Retailer listings, read 2026-11-07: 12 V DC, 1.2 GPM open flow, 35 psi pressure "
           "switch, self-priming to 4 ft, tolerates dry running, 4 A max. A submersible "
           "(Active Aqua AAPW250 5.9 ft / AAPW550 7.9 ft static head) cannot reach the 75 in. "
           "shelf plus an emitter's pressure. Maker sheet not seen.")
PSU = Product(
    tag="PROD-PUMP-PSU-12V", brand="Generic", name="12 V DC 5 A UL-listed plug-in supply",
    source="Pump supply; any listed 12 V >= 5 A unit with a 2.1 mm barrel or bare leads. "
           "Model to the shelf.")
NEEDLE = Product(
    tag="PROD-DIAL-94045", brand="Dial", model="94045",
    name="1/4 in. x 1/4 in. compression needle valve (evaporative-cooler type)",
    url="https://homedepot.com/p/DIAL-1-4-in-x-1-4-in-Evaporative-Cooler-Compression-Needle-Valve-94045/100175352",
    source="Home Depot #100175352, read 2026-11-07. Set once to ~0.1 gpm (6 gph): a stuck "
           "float then needs ~3.6 h to fill the room to 1/4 in., not minutes (note section 4).")
STOP = Product(
    tag="PROD-BRASSCRAFT-G2PS04X-C1", brand="BrassCraft", model="G2PS04X-C1",
    name="1/2 in. push-connect x 1/4 in. compression quarter-turn straight stop",
    url="https://www.homedepot.com/p/306206261",
    source="Home Depot #306206261, read 2026-11-07 (search result; page not opened). "
           "Replaces the capped hose-thread stop: the 1/4 in. line is the fill feed.")
DRIP_KIT = Product(
    tag="PROD-RAINBIRD-DRIPKITBAG", brand="Rain Bird", model="DRIPKITBAG",
    name="Drip system expansion and repair kit in a bag",
    url="https://www.homedepot.com/p/326977353",
    source="Home Depot #326977353, read 2026-11-07: 1/4 in. tubing, drippers. Pump holds 35 psi: "
           "fit a 15-25 psi drip regulator at the pump; confirm the kit's emitters.")
TIMER = Product(
    tag="PROD-WOODS-50015WD", brand="Woods", model="50015WD",
    name="15 A 7-day outdoor plug-in dual-outlet digital timer",
    url="https://www.homedepot.com/p/Woods-15-Amp-7-Day-Outdoor-Plug-In-Dual-Outlet-Digital-Timer-Black-50014WD/301133241",
    source="Home Depot, read 2026-11-07 (50015WD $15.85 / 50014WD): the pump supply plugs "
           "into it, it plugs into ED-S-PLANT-RC6. No cloud, no hub.")

PLANT_RESERVOIR_PRODUCTS = (TANK, FLOAT_VALVE, NEEDLE, PUMP, PSU, STOP, DRIP_KIT, TIMER)

# Port frame: the tank is placed rotation 180 (back to W-S-S1), so local +y is toward that wall
# and local +x toward -x plan. The valve rides the wall-side rim; z is its spout, 2 in. over
# the 17 1/8 in. rim: the air gap, 2x the 1 in. Table 603.3.1 asks (1 1/2 in. near a wall).
PLANT_RESERVOIR = ApplianceType(
    tag="APPL-PLANT-RESERVOIR",
    name="Plant-room drip reservoir: 10 gal BRUTE, float fill over a 2 in. air gap, 12 V pump",
    product_ref=TANK.tag,
    footprint=(inch(15.625), inch(15.625)), height=inch(17.125),
    needs=frozenset({Service.WATER_COLD, Service.POWER_120}),
    ports=(ServicePort(tag="supply", service=Service.WATER_COLD,
                       position=(inch(6), inch(5), inch(19.125)), connection_size=inch(0.25),
                       certainty=PortCertainty.EXACT, hose_length=inch(48),
                       notes="Dial 4154 inlet; the 1/4 in. poly line from the stop. Spout "
                             "2 in. over the rim; nothing downstream of it but air."),
           ServicePort(tag="power", service=Service.POWER_120,
                       position=(inch(-9), inch(0), inch(0)),
                       notes="Pump supply's cord, via the plug-in timer, to RC6.")),
    source="notes/plant_reservoir.md. The eight PROD-* above are the tank, valves, pump, "
           "supply, stop, drip kit and timer; the pump and its supply stand on the floor "
           "beside the tank and are not modelled separately.")

PLANT_RESERVOIR_TYPES = (PLANT_RESERVOIR,)
