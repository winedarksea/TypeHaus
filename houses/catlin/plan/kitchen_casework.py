# haus: editable
# The kitchen runs and their installation pieces. Dimensions are nominal finish datums.
# 
# The 32-inch single bowl and faucet centre on the window, 5/8 inch east within
# the fixed 36-inch base. Stock modules close the corner without a filler. Installation
# and actual rail/front allowances: notes/kitchen_stock_cabinet_details.md.

from typehaus import Appliance, Furniture, Location, Mount, MountKind, WallAttachment
from typehaus.model import deg, ft, inch, pt

MAIN_KITCHEN_CASEWORK = [
    # West run — cold storage and pantry against the centre bearing wall, opening east.
    # North to south: RM-M-PANTRY's south partition, freezer, refrigerator, closet pantry.
    # Cabinets 24" deep (centre x=19'-3 3/8"); cold boxes 27" deep (centre 19'-4 7/8").
    #
    # ** THE RUN'S NORTH END IS A WALL, NOT A CABINET. ** RM-M-PANTRY's south partition
    # W-M-PAN-S puts its face at y=32'-6 5/8"; the shared catalog's CASE-TALL-PANTRY-12/-18
    # accordingly have no instance in this house — scattered tall storage became one framed
    # room.
    #
    # The pair shifts SOUTH to meet that face and FURN-M-KIT-COLDSTORE-FILL is deleted with
    # them: the partition takes 4 3/4" off the north end, the filler gives 6 1/4" back, so
    # PANTRYC nets 1 1/2" north — the whole budget, and a bigger move means a shallower
    # pantry. The bay is 65 3/4", EXACTLY two appliance widths, so the appliances divide it
    # with no filler at either end. The two over-cabinets DO need filler and cannot avoid
    # it: 65 3/4" is not two SEKTION widths. See their note below.
    #
    # Fridge/freezer door zones: fronts at x=20'-6 3/8", so a 3'-0" zone reaches 23'-6 3/8"
    # — clear of W-M-PAN-E by 7 1/4" and south of the north counter run. ** DESIGN NOTE, and
    # no check catches it: ** that zone stands in front of D-M-PANTRY. An open fridge door
    # blocks the pantry. It is the price of putting both on one aisle, and it is the price
    # the owner is paying knowingly.
    # Product: the Frigidaire Professional single-door pair (plan/appliance_types.py). The
    # bay is 26'-11 3/8" to 32'-11 3/8", 72" — the appliances do not divide it in half,
    # because a column is 32 7/8" and not 36". The 6 1/4" remainder goes to
    # FURN-M-KIT-COLDSTORE-FILL at the SOUTH end, which is what lets both these boxes shift
    # south as a contiguous pair and still keep their own receptacles behind them
    # (ED-M-LIVING-KFZ1 at y=29'-10" lands behind the freezer, KRF1 at y=31'-5 3/8" behind
    # the refrigerator). Splitting the remainder into two 3 1/8" scribes would have put KFZ1
    # on the joint between them.
    #
    # x moved OUT, from 19'-8 3/8" to 19'-4 7/8", and the run got roomier for it: these
    # columns are 27" deep against the allowance's 34", and both are back-aligned to the
    # centre bearing wall's face at x=18'-3 3/8" the way the whole run is. They stand 3"
    # proud of the 24" tall cabinets beside them instead of 10". Frigidaire does not publish
    # the handle projection, so the *real* proudness is 3" plus a handle nobody has measured
    # — a tape on a floor sample before the cabinet order, not a number to invent here.
    Appliance(uid="A1Y5Q0RDXV", tag="APPL-M-FRIDGE", type_ref="APPL-FRIG-PRO-ALLFRIDGE",
              room="RM-M-LIVING",
              position=pt(ft(19, 4.875), ft(31, 6.1875)), rotation=deg(90),
              # TWINSPAIRKIT rides on the refrigerator rather than the freezer arbitrarily —
              # it is one kit for the pair, and billing it twice would be wrong. It is what
              # makes two cabinets legal to stand against each other: the shared side walls
              # would otherwise sweat.
              install_parts=("Frigidaire TWINSPAIRKIT twin pairing kit (anti-condensation heater, power supply, cord, clips)",)),
    Appliance(uid="ZH6G4SNPWT", tag="APPL-M-FREEZER", type_ref="APPL-FRIG-PRO-ALLFREEZER",
              room="RM-M-LIVING",
              position=pt(ft(19, 4.875), ft(28, 9.3125)), rotation=deg(90)),
    # PANTRYC closes straight up against the freezer now that the filler is gone.
    # ** 18" WIDE, NOT 24" (owner, 2026-09-25). ** The 24" box oversailed W-M-C5's south end
    # at y=25'-10" by 5 1/8" into the passage. At 18" its south end is y=25'-10 7/8", 7/8"
    # inside the wall's end and flush with the PANTRYC-ST stacker over it.
    Furniture(uid="XTD1N9A693", tag="FURN-M-KIT-PANTRYC", type_ref="SEKT-HIGH18-80",
              room="RM-M-LIVING",
              position=pt(ft(19, 3.375), ft(26, 7.875)), rotation=deg(90)),
    # ** THE TALL UNITS ALIGN BELOW THE FINISHED CEILING. ** The stacker is a 24"-DEEP
    # box: a tall cabinet's carcass is base depth, so the 15"-deep wall family would float
    # a shallow box over it and put the step back in a different place. The 3 1/2" support
    # and 80" frame top at 83 1/2", followed by a custom 20" course.
    #
    # 18" wide to match PANTRYC: south end on y=25'-10 7/8", 7/8" clear of W-M-C5's end.
    Furniture(uid="ZMBSYYRCX5", tag="FURN-M-KIT-PANTRYC-ST", type_ref="FT-KIT-DEEP18-20",
              room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(83.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-C5", face="right", distance_from_start=inch(9.875),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    # Over the two cold boxes: 24" deep like the talls, so all four fronts land on
    # x=20'-3 3/8" and the appliances stand 3" proud — clearing the fridge/freezer door
    # swing.
    #
    # ** TWO CUSTOM 30"-HIGH FRAMES AT 73 1/2", REPLACING FOUR BOXES. ** This was a
    # 32 7/8"-wide house-local FT-KIT-OVER-COLD-3278 at 75" with a CASE-TS3278-12 stacker
    # over it, per appliance. 32 7/8" is an appliance width, not a cabinet width, and
    # nobody sells it. A 30" custom frame at 73 1/2" aligns
    # with the 103 1/2" cabinet top without a stacker.
    #
    # ** THE HINGE CONTROLS THE MOUNT. ** The Frigidaire columns top at 72 1/2" at the
    # hinge and want 1" above (plan/appliance_types.py). A 73 1/2" cabinet starts exactly
    # there; confirm the hinge and rail clearance on the appliance/shop drawings.
    #
    # ** THE 5 3/4" OF FILLER, AND WHERE IT GOES. ** Bay 26'-11 3/8"..32'-11 3/8" is
    # 65 3/4"; two 30" boxes are 60". The pair is GANGED, with its joint on the appliance
    # joint at 30'-1 3/4", so each end of the bay takes a 2 7/8" scribe against a tall
    # cabinet — instead of one 2 7/8" gap floating between the two boxes where every eye
    # in the room lands. Box centres are 28'-10 3/4" and 31'-4 3/4", NOT the appliance
    # centres below them.
    Furniture(uid="8T3D1P2QRV", tag="FURN-M-KIT-OVER-FRIDGE", type_ref="FT-KIT-DEEP30-30",
              room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(73.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-C5", face="right", distance_from_start=inch(66.75),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="Y4KJ6WB0ZC", tag="FURN-M-KIT-OVER-FREEZER", type_ref="FT-KIT-DEEP30-30",
              room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(73.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-C5", face="right", distance_from_start=inch(36.75),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    # ** THE COLD RUN'S STACKER COURSE IS GONE, AND THAT IS THE POINT (2026-09-11). **
    # FURN-M-KIT-OVER-FRIDGE-ST/-FREEZER-ST were two CASE-TS3278-12 at 96" closing a 21"
    # box toward the ceiling. A 30" custom wall frame hung at 73 1/2" tops at 103 1/2", so
    # four boxes became two and there is no joint at 8'-0" on this wall at all.

    # Pantry face x=297 3/8; 12 + 24 DW + 36 sink + 18 = 90 inches to the carousel.
    Furniture(uid="49B0RDP4NW", tag="FURN-M-KIT-E1", type_ref="SEKT-B12", room="RM-M-LIVING",
              position=pt(inch(303.375), inch(413.375))),
    Furniture(uid="F8A30SK31X", tag="FURN-M-KIT-SINKBASE", type_ref="SEKT-SINK-B36",
              room="RM-M-LIVING",
              position=pt(inch(351.375), inch(413.375))),
    # The disposer follows the smaller undermount bowl's rear-centre drain and lower rim.
    Appliance(uid="ADCW7VPPC1", tag="APPL-M-DISP", type_ref="APPL-DISPOSAL", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(12.319)),
              install_parts=("24V Class-2 control transformer, 40 VA",
                             "double-pole contactor, 30 A, 24V coil",
                             "NEMA 1 enclosure, 6x6x4, hinged",
                             "guarded illuminated toggle switch, 24V",
                             "momentary pushbutton, stainless, counter-top",
                             "2-gang low-voltage mounting ring and plate",
                             "18/6 CL2 control cable, 50 ft"),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-N1", face="left", distance_from_start=inch(80),
                  normal_gap=inch(5), rotation_offset=deg(-180)))),
    Appliance(uid="XPA5ZCQM5Q", tag="APPL-M-DW", type_ref="APPL-LG-DISHWASHER", room="RM-M-LIVING",
              position=pt(inch(321.375), inch(413.375))),
    Furniture(uid="3QTQ2NFWYD", tag="FURN-M-KIT-E2", type_ref="SEKT-B18", room="RM-M-LIVING",
              position=pt(inch(378.375), inch(413.375))),

    # A single W36 over B12/DW avoids inventing a 12x20 stacker IKEA does not list.
    Furniture(uid="AQTQJBTXRR", tag="FURN-M-KIT-WE1", type_ref="SEKT-W36-30", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(53.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-N1", face="left", distance_from_start=inch(116.625),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="H3N6SVBPQY", tag="FURN-M-KIT-WE1-ST", type_ref="SEKT-W36-20", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(83.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-N1", face="left", distance_from_start=inch(116.625),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Bridge above the sink window; its head is 78 inches.
    Furniture(uid="RSP5MTPXPM", tag="FURN-M-KIT-WE4-ST", type_ref="SEKT-W36-20", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(83.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-N1", face="left", distance_from_start=inch(80.625),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="2V68CXXCNR", tag="FURN-M-KIT-WE5", type_ref="SEKT-W30-30", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(53.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-N1", face="left", distance_from_start=inch(47.625),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="T0QD4C4KHD", tag="FURN-M-KIT-WE5-ST", type_ref="SEKT-W30-20", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(83.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-N1", face="left", distance_from_start=inch(47.625),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),

    # Existing cooking wall: reversible carousel doors fold away from the range.
    Furniture(uid="KB9K9RXY2W", tag="FURN-M-KIT-CORNER-NE", type_ref="SEKT-CORNER-B38",
              room="RM-M-LIVING",
              position=pt(ft(33, 10.375), ft(33, 10.375)), rotation=deg(0)),
    Appliance(uid="417H1EH5C3", tag="APPL-M-RANGE", type_ref="APPL-LG-INDUCTION-RANGE",
              room="RM-M-LIVING",
              position=pt(ft(34, 2.375), ft(31, 0.375)), rotation=deg(-90)),
    Furniture(uid="5PZ7SPZYDT", tag="FURN-M-KIT-CORNER-PEN", type_ref="SEKT-CORNER-B38",
              room="RM-M-LIVING",
              position=pt(ft(33, 10.375), ft(28, 2.375)), rotation=deg(-90)),

    # S1 meets the garage. Rev-A-Shelf 5374-24FL remains in each 24-inch frameless box:
    # 22 1/4 W x 18 3/4 D x 75 H minimum opening; 22 1/2 W x ~22 1/2 D x 78 1/2 H provided.
    # Their west-opening doors and racks need the clear area reserved at the bar's end.
    Furniture(uid="77DB93R0QZ", tag="FURN-M-KIT-PANTRY-S1", type_ref="SEKT-HIGH24-80",
              room="RM-M-LIVING",
              position=pt(inch(413.375), inch(307.375)), rotation=deg(-90)),
    Furniture(uid="K09MANH37J", tag="FURN-M-KIT-PANTRY-S2", type_ref="SEKT-HIGH24-80",
              room="RM-M-LIVING",
              position=pt(inch(413.375), inch(283.375)), rotation=deg(-90)),
    # Stock 15-high deep tops finish at 98 1/2; 30-high frames would cross the ceiling.
    Furniture(uid="4WFET9VXWK", tag="FURN-M-KIT-PANTRY-S1-ST", type_ref="SEKT-TS24-15",
              room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(83.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(307.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="785R3FDGRK", tag="FURN-M-KIT-PANTRY-S2-ST", type_ref="SEKT-TS24-15",
              room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(83.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(283.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),

    # Diagonal corner backs are +x/+y, so this glyph stays at rotation 0, unlike straight uppers.
    Furniture(uid="2BF9VM3SFA", tag="FURN-M-KIT-WN1", type_ref="SEKT-CORNER-W26-30",
              room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(73.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(412.375),
                  normal_gap=inch(0), rotation_offset=deg(-90)))),
    Furniture(uid="6V2R6KBT2A", tag="FURN-M-KIT-WN2", type_ref="SEKT-W12-30", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(73.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(393.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Appliance(uid="Q0W3FYXJGX", tag="APPL-M-HOOD", type_ref="APPL-HOOD-RECIRC", room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(372.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),

    # Peninsula carcasses stay put; north aisle 58 inches, west aisle 56 1/2 inches.
    Furniture(uid="PSB290H9BR", tag="FURN-M-KIT-PEN-END", type_ref="FT-KIT-PEN-END-PANEL",
              room="RM-M-LIVING",
              position=pt(ft(25, 3.125), ft(27, 7.375)), rotation=deg(180)),
    Furniture(uid="J79MCTXA1Q", tag="FURN-M-KIT-PEN-B36", type_ref="SEKT-B36", room="RM-M-LIVING",
              position=pt(ft(26, 9.375), ft(27, 7.375)), rotation=deg(180)),
    Furniture(uid="WXDDD2CFGW", tag="FURN-M-KIT-PEN-B24-W", type_ref="SEKT-B24", room="RM-M-LIVING",
              position=pt(ft(29, 3.375), ft(27, 7.375)), rotation=deg(180)),
    Furniture(uid="WZ8XSHVH2G", tag="FURN-M-KIT-PEN-B24-E", type_ref="SEKT-B24", room="RM-M-LIVING",
              position=pt(ft(31, 3.375), ft(27, 7.375)), rotation=deg(180)),
    # Projecting finish stops with the bar. Paint/edge-band the remaining backs in place.
    Furniture(uid="JS6D4MHJPQ", tag="FURN-M-KIT-PEN-BACK", type_ref="FT-KIT-PEN-BACK-PANEL",
              room="RM-M-LIVING",
              position=pt(inch(339.625), inch(319.125)), rotation=deg(180)),
    Furniture(uid="MZNJ9TAN56", tag="FURN-M-KIT-STOOL1", type_ref="FURN-BAR-STOOL",
              room="RM-M-LIVING",
              position=pt(inch(315.125), ft(25, 5.375)), rotation=deg(180)),
    Furniture(uid="TMR4RNV2E3", tag="FURN-M-KIT-STOOL2", type_ref="FURN-BAR-STOOL",
              room="RM-M-LIVING",
              position=pt(inch(339.625), ft(25, 5.375)), rotation=deg(180)),
    Furniture(uid="1RME2HHSQT", tag="FURN-M-KIT-STOOL3", type_ref="FURN-BAR-STOOL",
              room="RM-M-LIVING",
              position=pt(inch(364.125), ft(25, 5.375)), rotation=deg(180)),

    # Both fronts face WEST: east-wall tangent 90 degrees + offset -180 = -90.
    # Heavy-duty full-extension mixer shelf at counter level; two outlets wired before assembly.
    Furniture(uid="5T1VTCY3EV", tag="FURN-M-KIT-MIXER-GARAGE", type_ref="FT-KIT-DEEP24-40",
              room="RM-M-LIVING", mount=Mount(kind=MountKind.WALL, elevation=inch(36)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(331.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Stock base FRAME only: no legs or counter. Supported by the lower carcass and restrained to wall.
    Furniture(uid="34W6S0G5EX", tag="FURN-M-KIT-MIXER-GARAGE-UP", type_ref="FT-KIT-STOCK24-30-HUNG",
              room="RM-M-LIVING", mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-E1", face="left", distance_from_start=inch(331.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),

    # Reach-in shelves remain 18 inches deep, leaving 8 inches of standing floor.
    # 73 1/4-inch width with a structural centre gable gives two 36 1/4-inch clear spans.
    Furniture(uid="J49EW9WWTQ", tag="FURN-M-PANTRY-SHELVES", type_ref="FT-KIT-PANTRY-SHELVES-70",
              room="RM-M-PANTRY", position=pt(inch(256), ft(34, 8.375))),
]
