"""Grounding, bonding and surge parts (decision #123, ``notes/grounding_bonding.md``).

NOT editable: types are never written back by a UI drag. Products marked "selection
pending" name the listing a part must carry, not a SKU; the electrician picks the part.
"""

from typehaus import ElectricalDeviceType, Product, inch

_SRC = "notes/grounding_bonding.md (2026-11-10)"
_PENDING = _SRC + "; selection pending, any part carrying the stated listing"

GND_ROD = Product(tag="GND-ROD-58X8", brand="nVent ERICO", model="615880",
                  name="5/8 in x 8 ft copper-bonded ground rod, UL 467", source=_SRC)
GND_ACORN = Product(tag="GND-ACORN-58", brand="nVent ERICO", model="CP58",
                    name="5/8 in acorn ground rod clamp, direct burial, UL 467", source=_SRC)
GND_UFER_CLAMP = Product(tag="GND-UFER-CLAMP", brand="TBD",
                         name="Rebar-to-conductor clamp, #4 bar to #4 Cu, listed for concrete "
                              "encasement (UL 467)", source=_PENDING)
GND_IBT = Product(tag="GND-IBT", brand="nVent ERICO", model="IBTB",
                  name="Intersystem bonding termination bar, 3 terminations, UL 467",
                  source=_SRC)
GND_TRANSITION = Product(tag="GND-AL-CU-TRANS", brand="TBD",
                         name="Bimetallic Al-Cu parallel connector, 1/0 Al to #2 Cu, UL 96 / "
                              "UL 486A-B", source=_PENDING)
GND_CLIP = Product(tag="GND-CLIP-S5", brand="TBD",
                   name="Conductor clip on a standing-seam / trim clamp, aluminium, no "
                        "penetration of the panel", source=_PENDING)
SPD_T1 = Product(tag="PROD-SIEMENS-FS140", brand="Siemens", model="FS140",
                 name="Type 1 SPD, 140 kA, 120/240 V split phase, UL 1449", source=_SRC)
SPD_T2 = Product(tag="PROD-LEVITON-51120-1", brand="Leviton", model="51120-1",
                 name="Type 1/2 panel SPD, 120/240 V split phase, UL 1449", source=_SRC)
SPD_PV = Product(tag="PROD-MIDNITE-MNSPD600", brand="MidNite Solar", model="MNSPD-600-DC",
                 name="PV DC surge protector, 600 VDC, UL 1449 Type 1CA", source=_SRC)

GROUNDING_PRODUCTS = (GND_ROD, GND_ACORN, GND_UFER_CLAMP, GND_IBT, GND_TRANSITION, GND_CLIP,
                      SPD_T1, SPD_T2, SPD_PV)

_BOX = dict(footprint=(inch(6), inch(4)), height=inch(6), needs=frozenset(), ports=())

GROUNDING_DEVICE_TYPES = (
    ElectricalDeviceType(tag="ED-T-SPD-T1", name="Type 1 SPD at the meter-main (NEC 230.67)",
                         product_ref=SPD_T1.tag, spd_class="1", surge_ka=140, **_BOX,
                         source=_SRC),
    ElectricalDeviceType(tag="ED-T-SPD-T2", name="Type 2 SPD, separate building (garage)",
                         product_ref=SPD_T2.tag, spd_class="2", surge_ka=50, **_BOX,
                         source=_SRC),
    ElectricalDeviceType(tag="ED-T-SPD-PV", name="PV DC SPD, 600 VDC",
                         product_ref=SPD_PV.tag, spd_class="pv_dc", surge_ka=20, **_BOX,
                         source=_SRC),
    ElectricalDeviceType(tag="ED-T-IBT", name="Intersystem bonding termination (NEC 250.94)",
                         product_ref=GND_IBT.tag, ibt=True, footprint=(inch(6), inch(2)),
                         height=inch(3), needs=frozenset(), ports=(), source=_SRC),
    ElectricalDeviceType(tag="ED-T-DATA-ENTRY", name="NEMA 3R comms entrance box, blank cover",
                         footprint=(inch(8), inch(4)), height=inch(8), needs=frozenset(),
                         ports=(), source=_SRC),
    ElectricalDeviceType(tag="ED-T-GND-JB", name="Grounding junction: EGC bar bonded to the "
                         "building's electrodes (NEC 250.32)", footprint=(inch(6), inch(4)),
                         height=inch(4), needs=frozenset(), ports=(), source=_SRC),
)
