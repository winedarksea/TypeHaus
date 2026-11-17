"""The two outside-room components of the mandatory Xenio controller kit."""

from typehaus import ElectricalDeviceType, Service, ServicePort, inch

XENIO_MANUAL = (
    "Harvia CX170 US manual 02112021/Y05-0653, sections 1.2, 3.1, 3.2, figure 6b: "
    "https://harviaheater.ca/wp-content/uploads/2024/02/"
    "Harvia-Xenio-Controller-Manual-for-Canada-and-the-USA-North-America-3.pdf"
)

SAUNA_CONTROL_TYPES = (
    ElectricalDeviceType(
        tag="ED-T-SAUNA-CONTROL", name="Harvia Xenio CX170 touch control panel",
        footprint=(inch(3.4), inch(1)), height=inch(4.4),
        plan_symbol="switch", needs=frozenset(),
        source=XENIO_MANUAL + "; low-voltage data cable to ED-B-SAUNA-POWER, no branch feed. "
        "Included in PROD-HARVIA-CX170 and the EQ-T-SAUNA-HEATER package price.",
    ),
    ElectricalDeviceType(
        tag="ED-T-SAUNA-POWER", name="Harvia Xenio CX170-U1-15 power unit",
        footprint=(inch(10.6), inch(3)), height=inch(10.6),
        plan_symbol="junction-box", needs=frozenset({Service.POWER_240}),
        product_ref="PROD-HARVIA-CX170",
        ports=(ServicePort(tag="power", service=Service.POWER_240,
                           position=(inch(0), inch(0), inch(0))),),
        source=XENIO_MANUAL + "; 240 V single-phase, 10.5 kW single-feed configuration. "
        "Surface mount in dry gym; switches EQ-B-SAUNA-HTR through ED-B-SAUNA-JB. "
        "No additional connected load; heater and controller kit priced at EQ-T-SAUNA-HEATER.",
    ),
)
