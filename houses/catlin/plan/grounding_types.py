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
# Siemens FirstSurge product overview (supplyhouse.com mirror, read 2026-11-14): "UL 1449
# Listed, Type 2 ... suitable for use downstream of the service disconnect", 140,000 A surge
# capacity, UL 1449 3rd ed. VPR; SCCR 100 kA (Siemens Canada datasheet LP-1408-2). Neither
# sheet publishes In, so 230.67(E) stays ungraded until the label is read.
_FS140_SRC = ("Siemens FirstSurge product overview, s3.amazonaws.com/s3.supplyhouse.com/"
              "product_files/Siemens-FS140-Product-Overview.pdf; Siemens Canada FirstSurge "
              "datasheet LP-1408-2 (SCCR 100 kA)")
SPD_T1 = Product(tag="PROD-SIEMENS-FS140", brand="Siemens", model="FS140",
                 name="Type 2 SPD, 140 kA surge capacity, 120/240 V split phase, UL 1449",
                 source=_FS140_SRC)
# The feeder panels' plug-on SPDs (plan/circuits.py CKT-SPD, CKT-SPD-2). Schneider product data
# sheets: QO2175SB (Sep 18, 2025) "SPD type 1", Nominal Discharge Current 10 kA, SCCR 100 kA,
# UL 1449; HOM2175SB (Jun 28, 2026) "SPD type 1" in its title and "UL 1449 ed. 4 type II" in
# its standards row, "Rated Current 10 kA" (its 2022 sheet's 5 kA there is what retailers print
# as In), SCCR 25 kA.
SPD_QO = Product(tag="PROD-SQUARED-QO2175SB", brand="Square D", model="QO2175SB",
                 name="QO plug-on Surgebreaker SPD, 25 kA, 120/240 V, 2-pole",
                 source="Schneider Electric product data sheet QO2175SB, Sep 18 2025")
SPD_HOM = Product(tag="PROD-SQUARED-HOM2175SB", brand="Square D", model="HOM2175SB",
                  name="Homeline plug-on Surgebreaker SPD, 25 kA, 120/240 V, 2-pole",
                  source="Schneider Electric product data sheet HOM2175SB, Jun 28 2026 "
                         "(do1jvmih5t6vs.cloudfront.net mirror)")
SPD_T2 = Product(tag="PROD-LEVITON-51120-1", brand="Leviton", model="51120-1",
                 name="Type 1/2 panel SPD, 120/240 V split phase, UL 1449", source=_SRC)
SPD_PV = Product(tag="PROD-MIDNITE-MNSPD600", brand="MidNite Solar", model="MNSPD-600-DC",
                 name="PV DC surge protector, 600 VDC, UL 1449 Type 1CA", source=_SRC)

GROUNDING_PRODUCTS = (GND_ROD, GND_ACORN, GND_UFER_CLAMP, GND_IBT, GND_TRANSITION, GND_CLIP,
                      SPD_T1, SPD_T2, SPD_PV, SPD_QO, SPD_HOM)

_BOX = dict(footprint=(inch(6), inch(4)), height=inch(6), needs=frozenset(), ports=())

GROUNDING_DEVICE_TYPES = (
    # The tag keeps its old "T1"; the FS140 is a Type 2 (Siemens), landed on a breaker.
    ElectricalDeviceType(tag="ED-T-SPD-T1", name="Type 2 SPD beside the meter-main (NEC 230.67)",
                         product_ref=SPD_T1.tag, spd_class="2", surge_ka=140, **_BOX,
                         spd_listing="UL 1449 Type 2", source=_FS140_SRC),
    ElectricalDeviceType(tag="ED-T-SPD-T2", name="Type 2 SPD, separate building (garage)",
                         product_ref=SPD_T2.tag, spd_class="2", surge_ka=50, **_BOX,
                         source=_SRC),
    ElectricalDeviceType(tag="ED-T-SPD-PV", name="PV DC SPD, 600 VDC",
                         product_ref=SPD_PV.tag, spd_class="pv_dc", surge_ka=20, **_BOX,
                         source=_SRC),
    # Catalog-only (never placed): the plug-ons a ``Circuit.spd_type_ref`` names.
    ElectricalDeviceType(tag="ED-T-SPD-QO2175SB", name="QO plug-on Type 1 SPD (QO2175SB)",
                         product_ref=SPD_QO.tag, spd_class="1", surge_ka=25,
                         spd_nominal_discharge_ka=10, spd_listing="UL 1449, Type 1",
                         footprint=(inch(1.5), inch(2.6)), height=inch(3.7), needs=frozenset(),
                         ports=(), source=SPD_QO.source),
    ElectricalDeviceType(tag="ED-T-SPD-HOM2175SB", name="Homeline plug-on SPD (HOM2175SB)",
                         product_ref=SPD_HOM.tag, spd_class="1", surge_ka=25,
                         spd_nominal_discharge_ka=10,
                         spd_listing="UL 1449 4th ed. (title: type 1; standards row: type II)",
                         footprint=(inch(2), inch(2.6)), height=inch(3.7), needs=frozenset(),
                         ports=(), source=SPD_HOM.source),
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
