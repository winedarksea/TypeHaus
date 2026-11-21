"""Grounding, bonding and surge parts (decision #123, ``notes/grounding_bonding.md``).

NOT editable: types are never written back by a UI drag. Products marked "selection
pending" name the listing a part must carry, not a SKU; the electrician picks the part.
"""

from typehaus import ElectricalDeviceType, Product, inch
from typehaus.model import ModelRepresentation

_SRC = "notes/grounding_bonding.md (2026-11-10)"
_PENDING = _SRC + "; selection pending, any part carrying the stated listing"

GND_ROD = Product(tag="GND-ROD-58X8", brand="nVent ERICO", model="615880",
                  name="5/8 in x 8 ft copper-bonded ground rod, UL 467", source=_SRC)
GND_ACORN = Product(tag="GND-ACORN-58", brand="nVent ERICO", model="CP58",
                    name="5/8 in acorn ground rod clamp, direct burial, UL 467", source=_SRC)
GND_UFER_CLAMP = Product(tag="GND-UFER-CLAMP", brand="TBD",
                         name="Rebar-to-conductor clamp, #4 bar to #2 Cu, listed for concrete "
                              "encasement (UL 467)", source=_PENDING)
# nVent ERICO IBTB spec sheet (2024): five connectors #14 solid-#6 str, one lay-in #6-#2 GEC.
GND_IBT = Product(tag="GND-IBT", brand="nVent ERICO", model="IBTB",
                  name="Intersystem bonding termination bar, 5 bonding terminations + #6-#2 "
                       "GEC lay-in", source="nVent ERICO IBTB specification sheet (2024)")
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
              "datasheet LP-1408-2 (SCCR 100 kA); envelope 8 x 4 x 3 in from the Siemens FS100P "
              "product data sheet (one FirstSurge enclosure)")
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
# MidNite MNSPD datasheet (mrsolar.com/content/pdf/MidNite/MNSPD.pdf, read 2026-11-17): the
# MNSPD-600 row is 0-600 VDC, 57 kA per phase, SCCR 115 kA; a 3.527 in dome, 4.425 in over
# its 1/2 in knockout nipple, 24 in #12 leads, polycarbonate Type 4X.
_MNSPD_SRC = "MidNite Solar MNSPD datasheet, mrsolar.com/content/pdf/MidNite/MNSPD.pdf"
SPD_PV = Product(tag="PROD-MIDNITE-MNSPD600", brand="MidNite Solar", model="MNSPD-600-DC",
                 name="PV DC surge protector, 600 VDC, UL 1449 Type 1CA", source=_MNSPD_SRC)

GROUNDING_PRODUCTS = (GND_ROD, GND_ACORN, GND_UFER_CLAMP, GND_IBT, GND_TRANSITION, GND_CLIP,
                      SPD_T1, SPD_PV, SPD_QO, SPD_HOM)

GROUNDING_DEVICE_TYPES = (
    # The tag keeps its old "T1"; the FS140 is a Type 2 (Siemens), landed on a breaker.
    ElectricalDeviceType(tag="ED-T-SPD-T1", name="Type 2 SPD beside the meter-main (NEC 230.67)",
                         product_ref=SPD_T1.tag, spd_class="2", surge_ka=140,
                         spd_listing="UL 1449 Type 2", source=_FS140_SRC,
                         # Laid on its side, nipple into the meter-main (Siemens' figure).
                         footprint=(inch(8), inch(3)), height=inch(4), needs=frozenset(),
                         ports=(),
                         model_representation=ModelRepresentation(symbol="siemens-fs140"),
                         # Close-nippled to the meter-main: rides its strut (#142).
                         exterior_mount="strut"),
    ElectricalDeviceType(tag="ED-T-SPD-PV", name="PV DC SPD, 600 VDC",
                         product_ref=SPD_PV.tag, spd_class="pv_dc", surge_ka=57,
                         source=_MNSPD_SRC, footprint=(inch(3.527), inch(3.527)),
                         height=inch(4.425), needs=frozenset(), ports=(),
                         model_representation=ModelRepresentation(symbol="midnite-mnspd")),
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
                         product_ref=GND_IBT.tag, ibt=True, bonding_terminals=5,
                         # IBTB spec sheet: 4 L x 2.01 W x 1.41 in overall, wall-mounted flat.
                         footprint=(inch(4), inch(1.41)),
                         height=inch(2.01), needs=frozenset(), ports=(), source=_SRC,
                         model_representation=ModelRepresentation(symbol="nvent-erico-ibtb")),
    ElectricalDeviceType(tag="ED-T-DATA-ENTRY", name="NEMA 3R comms entrance box, blank cover",
                         footprint=(inch(8), inch(4)), height=inch(8), needs=frozenset(),
                         ports=(), source=_SRC,
                         model_representation=ModelRepresentation(symbol="comms-entrance-box")),
)
