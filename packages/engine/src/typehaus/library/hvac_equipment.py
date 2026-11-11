"""Heat-pump product records: Gree FLEXX Ultra, Multi R32 and Sapphire R32.

Manufacturer facts only — outline, electrical, seasonal ratings and the published heating
table (``HeatPumpRating`` rows, each with its basis and citation). What a zone needs, and
whether a unit covers it, is the house's arithmetic, never a row's.
"""

from __future__ import annotations

from typehaus import EquipmentType, HeatPumpRating, RatingBasis, Service, ServicePort, ft, inch
from typehaus.model.placeable_symbols._gree_flexx import (
    CABINET_IN,
    CONTROL_CENTER_IN,
    FRONT_CONNECTIONS_IN,
    POWER_CENTER_IN,
    RETURN_CENTER_IN,
    SERVICE_CLEARANCE_IN,
    SUPPLY_CENTER_IN,
    SUPPLY_OPENING_IN,
)
from typehaus.model.placeable_symbols._gree_flexx_outdoor import (
    OUTDOOR_BASELINE_CLEARANCE_IN,
    OUTDOOR_CABINET_IN,
    OUTDOOR_CONNECTIONS_IN,
    OUTDOOR_CONTROL_CENTER_IN,
    OUTDOOR_POWER_CENTER_IN,
)
from typehaus.model.placeables import (
    ClearancePolicy,
    ClearanceZone,
    Footprint2D,
    ModelRepresentation,
)
from typehaus.quantities import pt


def _flexx_front_ports():
    services = {"liquid": Service.REFRIGERANT_LIQUID, "vapor": Service.REFRIGERANT_VAPOR}
    return tuple(ServicePort(
        tag=tag, service=services.get(tag, Service.DRAIN),
        position=(inch(x), inch(-CABINET_IN[1] / 2), inch(z)),
        connection_size=inch(diameter), direction=(0, -1, 0),
        notes=("Nominal connection size verified; front-face station is schematic. "
               "Confirm on delivered unit before routing or drilling. "
               + ("3/4 inch PVC drain; trapped primary and independent secondary protection."
                  if tag.startswith("condensate") else "Flared refrigerant connection.")),
    ) for tag, (x, z, diameter) in FRONT_CONNECTIONS_IN.items())


def _flexx_outdoor_clearances():
    half_width, half_depth = (value / 2 for value in OUTDOOR_CABINET_IN[:2])
    gaps = OUTDOOR_BASELINE_CLEARANCE_IN
    rectangles = {
        "service": (half_width, -half_depth, half_width + gaps["service"], half_depth),
        "rear": (-half_width, half_depth, half_width, half_depth + gaps["rear"]),
        "left": (-half_width - gaps["left"], -half_depth, -half_width, half_depth),
        "front": (-half_width, -half_depth - gaps["front"], half_width, -half_depth),
    }
    # Gree varies these by obstruction configuration. These baseline planning zones
    # cannot establish compliance with Catlin's owner-accepted canopy installation.
    return tuple(ClearanceZone(
        footprint=Footprint2D(points=tuple(pt(inch(x), inch(y)) for x, y in (
            (x0, y0), (x1, y0), (x1, y1), (x0, y1)))),
        purpose=f"FLEXX outdoor {face} baseline coordination space; obstruction table governs",
        policy=ClearancePolicy.RECOMMENDED,
        source="FXU24 submittal p.6: A/B/C rows and D row; canopy acceptance unverified",
    ) for face, (x0, y0, x1, y1) in rectangles.items())


GREE_FLEXX_ULTRA_24_AH = EquipmentType(
    tag="EQ-T-GREE-FLEXX-ULTRA-24-AH",
    name="Gree FLEXX Ultra R32 concealed ducted air handler, 24k",
    footprint=(inch(CABINET_IN[0]), inch(CABINET_IN[1])),
    height=inch(CABINET_IN[2]),
    model_representation=ModelRepresentation(symbol="gree-flexx-ultra-24-horizontal"),
    clearances=(ClearanceZone(
        footprint=Footprint2D(points=tuple(pt(inch(x), inch(y)) for x, y in (
            (-21.75, -10.625), (21.75, -10.625),
            (21.75, -10.625 - SERVICE_CLEARANCE_IN),
            (-21.75, -10.625 - SERVICE_CLEARANCE_IN)))),
        purpose="24 inch access in front of horizontal-left removable service panels",
        policy=ClearancePolicy.REQUIRED,
        source="Gree FXU24 submittal 2026-01-27 p.6; indoor installation manual section 4.2",
    ),),
    cooling_capacity_btuh=24000,
    hspf2=10.0,
    seer2=18.0,
    source=("Gree FLEXX Ultra R32 air handler FXU24HP230V1R32AH, matched to FXU24HP230V1R32AO. "
            "Cabinet 18 1/8 x 21 1/4 x 43 1/2 in (W x D x H as shipped), 135.6 lb; multi-position,"
            " laid horizontal for ceiling mount. 760 cfm at 0.5 in. w.c. ESP (speed 3). HSPF2 10.0"
            " / SEER2 18.0, ENERGY STAR Cold Climate (AHRI 215213329). 24 VAC thermostat "
            "terminals; field-installed electric heat kit (5 / 6 / 10 kW). Heating is rated on the"
            " outdoor unit. Geometry basis: GREE_FXU24_230V_R32_SUB_01272026 pp.4,6. "
            "Local -x discharge, +x return, -y service front (east at rotation 90). "
            "Supply aperture 11 5/8 deep x 16 3/4 wide as shipped; horizontal section "
            "11 5/8 across x 16 3/4 high. Return clear aperture and all connection "
            "setbacks are not dimensioned. Current generic indoor manual section 2.3 "
            "assigns a conflicting 48 3/16 high cabinet to FXU24; verify delivered revision. "
            "https://www.greecomfort.com/assets/our-products/flexx-ultra-r32/documents/"
            "flexx-ultra-r32-submittal-24mbh-a.pdf"),
    ports=(
        ServicePort(
            tag="power",
            service=Service.POWER_240,
            position=tuple(inch(value) for value in POWER_CENTER_IN),
            direction=(0, -1, 0), notes="Front entry allowance; knockout station unverified.",
        ),
        ServicePort(
            tag="control", service=Service.POWER_24,
            position=tuple(inch(value) for value in CONTROL_CENTER_IN),
            direction=(0, -1, 0),
            notes="24 VAC thermostat/RS485 control entry; knockout station unverified.",
        ),
        ServicePort(
            tag="supply", service=Service.SUPPLY_AIR,
            position=tuple(inch(value) for value in SUPPLY_CENTER_IN),
            width=inch(SUPPLY_OPENING_IN[0]), depth=inch(SUPPLY_OPENING_IN[1]),
            direction=(-1, 0, 0),
            notes="Opening size from submittal p.4 A/B; rear-aligned station inferred "
                  "from perspective view, setback unverified. Needs an offset transition.",
        ),
        ServicePort(
            tag="return", service=Service.RETURN_AIR,
            position=tuple(inch(value) for value in RETURN_CENTER_IN), direction=(1, 0, 0),
            notes="Return end face known; clear aperture and centre not dimensioned. "
                  "Do not reuse the supply A/B dimensions for the return.",
        ),
    ) + _flexx_front_ports(),
)

GREE_FLEXX_ULTRA_24_OD = EquipmentType(
    tag="EQ-T-GREE-FLEXX-ULTRA-24-OD",
    name="Gree FLEXX Ultra R32 outdoor unit, 24k (-22F, cold climate)",
    footprint=(inch(OUTDOOR_CABINET_IN[0]), inch(OUTDOOR_CABINET_IN[1])),
    height=inch(OUTDOOR_CABINET_IN[2]),
    plan_symbol="gree-flexx-ultra-24-outdoor",
    model_representation=ModelRepresentation(symbol="gree-flexx-ultra-24-outdoor"),
    clearances=_flexx_outdoor_clearances(),
    heating_ratings=(
        HeatPumpRating(
            outdoor_db_f=-22.0,
            minimum_btuh=13400,
            maximum_btuh=18000,
            cop_at_minimum=1.37,
            cop_at_maximum=1.36,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation=("NEEP ccASHP id 504980 (ashp.neep.org/api/products/504980/), AHRI 215213329,"
                      " 70 F return, read 2026-09-18."),
        ),
        HeatPumpRating(
            outdoor_db_f=-15.0,
            rated_btuh=21000,
            cop_at_rated=1.57,
            return_db_f=70.0,
            basis=RatingBasis.MANUFACTURER,
            citation=("Gree Extended Ratings GREE_FLEXX_ULTRA_EXTENDED RATINGS_08272024, model "
                      "FXU24, 70 F return, the 'MAX OUTPUT' band, read verbatim."),
        ),
        HeatPumpRating(
            outdoor_db_f=5.0,
            minimum_btuh=14000,
            rated_btuh=25000,
            maximum_btuh=25000,
            cop_at_minimum=2.55,
            cop_at_rated=2.0,
            cop_at_maximum=2.0,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation="NEEP ccASHP id 504980, AHRI 215213329, 70 F return, read 2026-09-18.",
        ),
        HeatPumpRating(
            outdoor_db_f=17.0,
            minimum_btuh=7100,
            rated_btuh=20600,
            maximum_btuh=21600,
            cop_at_minimum=2.77,
            cop_at_rated=2.7,
            cop_at_maximum=2.67,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation="NEEP ccASHP id 504980, AHRI 215213329, 70 F return, read 2026-09-18.",
        ),
        HeatPumpRating(
            outdoor_db_f=47.0,
            minimum_btuh=10800,
            rated_btuh=25000,
            maximum_btuh=25400,
            cop_at_minimum=5.11,
            cop_at_rated=3.59,
            cop_at_maximum=3.56,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation="NEEP ccASHP id 504980, AHRI 215213329, 70 F return, read 2026-09-18.",
        ),
    ),
    cooling_capacity_btuh=24000,
    min_operating_temp_f=-22.0,
    hspf2=10.0,
    seer2=18.0,
    source=("Gree FXU24HP230V1R32AO (FLEXX Ultra, R32). 39 x 37 13/16 x 14 9/16 in (W x H x D), "
            "foot pattern 29 3/4 x 15 9/16 in, 187.4 lb. MCA 21 A / MOCP 25 A at 208-230 V, 1 ph. "
            "HSPF2 10.0 / SEER2 18.0, ENERGY STAR Cold Climate; AHRI 215213329 certifies the "
            "seasonal ratings and the 47 F / 17 F points only. Low-ambient rows per "
            "heating_ratings (NEEP id 504980; Gree Extended Ratings 08272024 'MAX OUTPUT' at -15 "
            "F). Operating to -22 F. Geometry: GREE_FXU24_230V_R32_SUB_01272026 p.4 "
            "A/F/C cabinet; B overall foot depth 16 13/16 in; D/E fixing pitch "
            "29 3/4 x 15 9/16 in. Cabinet footprint excludes the projecting feet. "
            "Local -y front discharge, +y rear intake, +x service/valve side. "
            "Connection stations and projections, fan size and foot slot dimensions "
            "are not dimensioned; rendered details are schematic. "
            "https://www.greecomfort.com/assets/our-products/flexx-ultra-r32/documents/"
            "flexx-ultra-r32-submittal-24mbh-a.pdf"),
    ports=(
        ServicePort(tag="power", service=Service.POWER_240,
                    position=tuple(inch(value) for value in OUTDOOR_POWER_CENTER_IN),
                    direction=(1, 0, 0),
                    notes="208-230 V electrical compartment on local +x; knockout unverified."),
        ServicePort(tag="control", service=Service.POWER_24,
                    position=tuple(inch(value) for value in OUTDOOR_CONTROL_CENTER_IN),
                    direction=(1, 0, 0),
                    notes="24 VAC/RS485 control entry; knockout unverified."),
    ) + tuple(ServicePort(
        tag=tag,
        service=Service.REFRIGERANT_LIQUID if tag == "liquid" else Service.REFRIGERANT_VAPOR,
        position=tuple(inch(value) for value in station), connection_size=inch(diameter),
        direction=(1, 0, 0),
        notes="Nominal flared tube size from FXU24 submittal p.2. Valve position, "
              "outlet axis and cover projection are schematic; verify before routing.",
    ) for tag, (station, diameter) in OUTDOOR_CONNECTIONS_IN.items()),
)

GREE_MULTI_U30 = EquipmentType(
    tag="EQ-T-GREE-MULTI-U30",
    name="Gree Multi R32 3-port outdoor unit, 30k (-22F)",
    footprint=(inch(40.16), inch(16.81)),
    height=inch(32.52),
    plan_symbol="heat-pump-outdoor",
    heating_ratings=(
        HeatPumpRating(
            outdoor_db_f=-22.0,
            minimum_btuh=7000,
            maximum_btuh=21000,
            cop_at_minimum=1.49,
            cop_at_maximum=1.45,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation=("NEEP ccASHP id 392050 (ashp.neep.org/api/products/392050/), outdoor "
                      "MUL30HP230V1R32AO, AHRI 215218915, 70 F return, read 2026-09-18."),
        ),
        HeatPumpRating(
            outdoor_db_f=-15.0,
            rated_btuh=23687,
            return_db_f=70.0,
            basis=RatingBasis.MANUFACTURER,
            citation="Gree Multi Ultra R32 Extended Ratings, 70 F return, read at -15 F.",
        ),
        HeatPumpRating(
            outdoor_db_f=5.0,
            minimum_btuh=8800,
            rated_btuh=27000,
            maximum_btuh=27000,
            cop_at_minimum=2.2,
            cop_at_rated=2.07,
            cop_at_maximum=2.07,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation="NEEP ccASHP id 392050, AHRI 215218915, 70 F return, read 2026-09-18.",
        ),
        HeatPumpRating(
            outdoor_db_f=17.0,
            minimum_btuh=8800,
            rated_btuh=28000,
            maximum_btuh=31860,
            cop_at_minimum=2.96,
            cop_at_rated=2.45,
            cop_at_maximum=2.4,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation="NEEP ccASHP id 392050, AHRI 215218915, 70 F return, read 2026-09-18.",
        ),
        HeatPumpRating(
            outdoor_db_f=47.0,
            minimum_btuh=8200,
            rated_btuh=30000,
            maximum_btuh=30400,
            cop_at_minimum=4.22,
            cop_at_rated=4.19,
            cop_at_maximum=3.32,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation="NEEP ccASHP id 392050, AHRI 215218915, 70 F return, read 2026-09-18.",
        ),
    ),
    cooling_capacity_btuh=28400,
    min_operating_temp_f=-22.0,
    hspf2=10.0,
    seer2=21.0,
    source=("Gree MUL30HP230V1R32AO (Multi R32, 3-port). 40 5/32 x 32 33/64 x 16 13/16 in, foot "
            "holes 25 x 15 19/32 in, 145.5 lb (Multi R32 IOM S3 outline p.31). AHRI 215218915 non-"
            "ducted: SEER2 21, EER2 13.6, HSPF2 10.0; MCA 23 A / MOCP 30 A; heating range -22 F to"
            " 75 F. Cooling 28,400 Btu/h. A multi's minimum capacity is the whole outdoor unit's, "
            "shared by every head."),
    ports=(ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),),
)

GREE_HEAD_9 = EquipmentType(
    tag="EQ-T-GREE-HEAD-9",
    name="Gree Multi R32 wall-mount head, 9k",
    footprint=(inch(32.875), inch(7.875)),
    height=inch(10.828125),
    model_representation=ModelRepresentation(symbol="heat-pump-indoor"),
    cooling_capacity_btuh=9000,
    source=("Gree GWH09ATCXB-D6DNA3C/I, Multi R32 9k wall-mounted indoor unit (submittal 'Wall "
            "Mounted Indoor Unit 09KBTU R32'): 32 7/8 x 10 53/64 x 7 7/8 in (W x H x D), 19.8 lb —"
            " the same cabinet as the 12k. Heating is rated on the outdoor unit."),
    ports=(),
)

GREE_HEAD_12 = EquipmentType(
    tag="EQ-T-GREE-HEAD-12",
    name="Gree Multi R32 wall-mount head, 12k",
    footprint=(inch(32.875), inch(7.875)),
    height=inch(10.828125),
    model_representation=ModelRepresentation(symbol="heat-pump-indoor"),
    cooling_capacity_btuh=12000,
    source=("Gree GWH12ATCXB-D6DNA3A/I, Multi R32 12k wall-mounted indoor unit (submittal 'Wall "
            "Mounted Indoor Unit 12KBTU R32'): 32 7/8 x 10 53/64 x 7 7/8 in (W x H x D), 19.8 lb —"
            " the same cabinet as the 9k."),
    ports=(),
)

GREE_SAPPHIRE_9 = EquipmentType(
    tag="EQ-T-GREE-SAPPHIRE-9",
    name="Gree Sapphire R32 wall-mount head, 9.1k (VFD soft start)",
    footprint=(inch(38.1875), inch(10.125)),
    height=inch(13.65625),
    model_representation=ModelRepresentation(symbol="heat-pump-indoor"),
    cooling_capacity_btuh=9100,
    hspf2=11.2,
    seer2=30.0,
    source=("Gree SAP09HP230V1R32AH, Sapphire R32 9k wall-mounted indoor unit (Sapphire R32 9 MBH "
            "230 V submittal, AHRI 214802444): 38 3/16 x 13 21/32 x 10 1/8 in (W x H x D), 33.1 "
            "lb. VFD inverter (soft start). Heating is rated on the outdoor unit."),
    ports=(),
)

GREE_SAPPHIRE_9_OD = EquipmentType(
    tag="EQ-T-GREE-SAPPHIRE-9-OD",
    name="Gree Sapphire R32 outdoor unit, 9.1k (-22F)",
    footprint=(inch(34.375), inch(14.796875)),
    height=inch(21.859375),
    plan_symbol="heat-pump-outdoor",
    heating_ratings=(
        HeatPumpRating(
            outdoor_db_f=-22.0,
            minimum_btuh=2600,
            maximum_btuh=7400,
            cop_at_minimum=4.23,
            cop_at_maximum=1.64,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation=("NEEP ccASHP id 393164 (ashp.neep.org/api/products/393164/), AHRI 214802444,"
                      " 70 F return, read 2026-09-18."),
        ),
        HeatPumpRating(
            outdoor_db_f=5.0,
            minimum_btuh=2600,
            rated_btuh=11500,
            maximum_btuh=11500,
            cop_at_minimum=4.23,
            cop_at_rated=2.11,
            cop_at_maximum=2.11,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation="NEEP ccASHP id 393164, AHRI 214802444, 70 F return, read 2026-09-18.",
        ),
        HeatPumpRating(
            outdoor_db_f=17.0,
            minimum_btuh=2800,
            rated_btuh=12000,
            maximum_btuh=13000,
            cop_at_minimum=4.32,
            cop_at_rated=2.3,
            cop_at_maximum=2.06,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation="NEEP ccASHP id 393164, AHRI 214802444, 70 F return, read 2026-09-18.",
        ),
        HeatPumpRating(
            outdoor_db_f=47.0,
            minimum_btuh=2700,
            rated_btuh=10600,
            maximum_btuh=16000,
            cop_at_minimum=5.28,
            cop_at_rated=4.38,
            cop_at_maximum=3.75,
            return_db_f=70.0,
            basis=RatingBasis.NEEP,
            citation="NEEP ccASHP id 393164, AHRI 214802444, 70 F return, read 2026-09-18.",
        ),
    ),
    cooling_capacity_btuh=9100,
    min_operating_temp_f=-22.0,
    hspf2=11.2,
    seer2=30.0,
    source=("Gree SAP09HP230V1R32AO (Sapphire R32 9 MBH 230 V submittal, AHRI 214802444): 34 3/8 x"
            " 21 27/32 x 14 51/64 in (W x H x D), 78.3 lb, MCA 11 A / MOCP 15 A, SEER2 30.0, HSPF2"
            " 11.2, heating range -22 F to 86 F. The submittal states 8,900 Btu/h at 17 F where "
            "NEEP (id 393164) states 12,000; the rows are NEEP's. Gree's low-ambient table implies"
            " a COP of 2.62 at -22 F, which is not physically plausible; NEEP's 7,400 Btu/h at COP"
            " 1.64 is used."),
    ports=(ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),),
)

HEAT_PUMP_TYPES = (
    GREE_FLEXX_ULTRA_24_AH,
    GREE_FLEXX_ULTRA_24_OD,
    GREE_MULTI_U30,
    GREE_HEAD_9,
    GREE_HEAD_12,
    GREE_SAPPHIRE_9,
    GREE_SAPPHIRE_9_OD,
)
