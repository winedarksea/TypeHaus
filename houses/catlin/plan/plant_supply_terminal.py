"""Plant supply fabrication dimensions; coordinates are relative to its ceiling face.

The actuator goes west: an east actuator would intersect the rising feed. Motor and blade
travel are checked as envelopes; the actuator is included in the damper purchase.
"""

from typehaus import TerminalNeck, TerminalNeckComponent, TerminalNeckInlet, inch

PLANT_SUPPLY_NECK = TerminalNeck(
    # Legacy dimensions describe the boot; every component is placed and checked separately.
    width=inch(12), height=inch(10), depth=inch(10.5),
    part="TH-HP-PLANT-BOOT-01 / ZD12X6TZ / 12x6 collar assembly",
    inlet=TerminalNeckInlet(position=(inch(6), inch(0), inch(7.5)),
                            width=inch(10), height=inch(6), normal=(1, 0), straight_length=inch(6)),
    components=(
        TerminalNeckComponent(tag="COLLAR", width=inch(12), height=inch(6), depth=inch(.5),
            offset=(inch(0), inch(0), inch(0)), part="12x6 removable galvanized collar",
            product_ref="PROD-AIR-PLANT-COLLAR"),
        TerminalNeckComponent(tag="DAMPER", width=inch(12), height=inch(6), depth=inch(4),
            offset=(inch(0), inch(0), inch(.5)), part="Honeywell Home ZD12X6TZ",
            product_ref="PROD-AIR-PLANT-DAMPER-12X6"),
        TerminalNeckComponent(tag="ACTUATOR", width=inch(4.0625), height=inch(4.96875),
            depth=inch(4.640625), offset=(inch(-8.03125), inch(0), inch(.5)),
            part="M847D actuator envelope, included with ZD12X6TZ",
            product_ref="PROD-AIR-PLANT-DAMPER-12X6"),
        TerminalNeckComponent(tag="BOOT", width=inch(12), height=inch(10), depth=inch(6),
            offset=(inch(0), inch(0), inch(4.5)), part="TH-HP-PLANT-BOOT-01 26ga end boot",
            product_ref="PROD-AIR-PLANT-END-BOOT", receives_duct=True),
        TerminalNeckComponent(tag="SERVICE-HATCH", width=inch(12), height=inch(8),
            depth=inch(.5), offset=(inch(-16), inch(0), inch(-.5)),
            part="TH-HP-PLANT-HATCH-01 gasketed PVC service cover",
            product_ref="PROD-AIR-PLANT-SERVICE-HATCH"),
        TerminalNeckComponent(tag="ACTUATOR-WITHDRAWAL", width=inch(10.0625),
            height=inch(4.96875), depth=inch(4.640625),
            offset=(inch(-11.03125), inch(0), inch(.5)),
            part="actuator westward withdrawal, 6in travel", clearance_only=True),
        TerminalNeckComponent(tag="ACTUATOR-REMOVAL", width=inch(4.0625),
            height=inch(4.96875), depth=inch(11.140625),
            offset=(inch(-14.03125), inch(0), inch(-6)),
            part="actuator lowering through 10x6 service opening", clearance_only=True),
        TerminalNeckComponent(tag="DAMPER-REMOVAL", width=inch(12), height=inch(6),
            depth=inch(12.5), offset=(inch(0), inch(0), inch(-8)),
            part="damper lowering after actuator removal", clearance_only=True),
        # A full passage envelope conservatively contains the parallel blades' sweep.
        TerminalNeckComponent(tag="BLADE-SWEEP", width=inch(12), height=inch(6), depth=inch(4),
            offset=(inch(0), inch(0), inch(.5)), part="ZD12X6TZ blade movement",
            clearance_only=True),
    ),
)
