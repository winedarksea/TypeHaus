"""Heat-pump product records: Gree FLEXX Ultra, Multi R32 and Sapphire R32.

Manufacturer facts only — outline, electrical, seasonal ratings and the published heating
table (``HeatPumpRating`` rows, each with its basis and citation). What a zone needs, and
whether a unit covers it, is the house's arithmetic, never a row's.
"""

from __future__ import annotations

from typehaus import EquipmentType, HeatPumpRating, RatingBasis, Service, ServicePort, ft, inch

GREE_FLEXX_ULTRA_24_AH = EquipmentType(
    tag="EQ-T-GREE-FLEXX-ULTRA-24-AH",
    name="Gree FLEXX Ultra R32 concealed ducted air handler, 24k",
    footprint=(inch(43.5), inch(21.25)),
    height=inch(18.125),
    cooling_capacity_btuh=24000,
    hspf2=10.0,
    seer2=18.0,
    source=("Gree FLEXX Ultra R32 air handler FXU24HP230V1R32AH, matched to FXU24HP230V1R32AO. "
            "Cabinet 18 1/8 x 21 1/4 x 43 1/2 in (W x D x H as shipped), 135.6 lb; multi-position,"
            " laid horizontal for ceiling mount. 760 cfm at 0.5 in. w.c. ESP (speed 3). HSPF2 10.0"
            " / SEER2 18.0, ENERGY STAR Cold Climate (AHRI 215213329). 24 VAC thermostat "
            "terminals; field-installed electric heat kit (5 / 6 / 10 kW). Heating is rated on the"
            " outdoor unit."),
    ports=(
        ServicePort(
            tag="power",
            service=Service.POWER_240,
            position=(inch(21.75), inch(10.625), inch(18.125)),
        ),
        ServicePort(
            tag="supply", service=Service.SUPPLY_AIR, position=(inch(-21.75), ft(0), inch(9.0625))
        ),
        ServicePort(
            tag="return", service=Service.RETURN_AIR, position=(inch(21.75), ft(0), inch(9.0625))
        ),
    ),
)

GREE_FLEXX_ULTRA_24_OD = EquipmentType(
    tag="EQ-T-GREE-FLEXX-ULTRA-24-OD",
    name="Gree FLEXX Ultra R32 outdoor unit, 24k (-22F, cold climate)",
    footprint=(inch(39), inch(14.5625)),
    height=inch(37.8125),
    plan_symbol="heat-pump-outdoor",
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
            "F). Operating to -22 F."),
    ports=(ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),),
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
