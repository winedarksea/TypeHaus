# haus: editable
# Catlin MEP — the hot-water header (owner, 2026-11-03; notes/water_service.md §6).
#
# PR-B-HW-TRUNK (1" copper) runs heater -> header. Eight hot room branches are 1/2" PEX-A
# lines, each off its own ProPEX outlet, so a tap waits on the trunk plus ONE 1/2" line.
# PR-B-HW-SBATH (5.25 WSFU) and PR-B-HW-SUITE (6.75, the studio rides on it) need 3/4" by
# `mep.pipe_sizing` and the outlets are 1/2", so those two tee off the trunk just upstream.
# `haus route houses/catlin --manifold EQ-B-HW-HEADER` proposes the eight together.
#
# Product: Uponor LF2821050, 1" copper branch manifold, eight 1/2" ProPEX LF brass outlets,
# 1" sweat supply (Uponor submittal "ProPEX (type L) copper branch manifolds", read
# 2026-11-04). Sold by SupplyHouse; Uponor's sheet says made to order.
#
# Product frame: body along x, closed end -x, sweat inlet +x, outlets hung DOWN so the
# branches leave at 83 1/2".
# A = 14.675" long, body H = 1.256" OD, G = 2.479" over the outlet tips, D = 1.5" pitch. The
# first outlet sits B + C = 1.626" in from the inlet end (the sheet's letters, off its drawing).

from typehaus import (
    Equipment,
    EquipmentKind,
    EquipmentType,
    Mount,
    MountKind,
    PortCertainty,
    Service,
    ServicePort,
    deg,
    inch,
    pt,
)

EQUIPMENT_TYPES_HEADER = (
    EquipmentType(tag="EQ-T-HW-HEADER-8",
                  name="Hot-water header, Uponor LF2821050 1in copper branch manifold, 8 x 1/2in ProPEX outlets",
                  footprint=(inch(14.675), inch(1.5)), height=inch(2.479),
                  source="Uponor submittal 'ProPEX (type L) copper branch manifolds' (read 2026-11-04): LF2821050, 1in copper, 1in sweat supply, eight 1/2in ProPEX LF brass outlets, A 14.675in, D 1.5in pitch, G 2.479in, H 1.256in, 1.4 lb; 80 psi at 200 F (ASTM F2023 DHW limit 140 F at 80 psi). SupplyHouse lists it as stock.",
                  ports=(ServicePort(tag="inlet", service=Service.WATER_HOT,
                                     position=(inch(7.3375), inch(0), inch(1.851)),
                                     connection_size=inch(1), direction=(1.0, 0.0, 0.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="1in sweat supply, the +x end."),
                         ServicePort(tag="out-1", service=Service.WATER_HOT,
                                     position=(inch(5.7115), inch(0), inch(0)),
                                     connection_size=inch(0.5), direction=(0.0, 0.0, -1.0),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="out-2", service=Service.WATER_HOT,
                                     position=(inch(4.2115), inch(0), inch(0)),
                                     connection_size=inch(0.5), direction=(0.0, 0.0, -1.0),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="out-3", service=Service.WATER_HOT,
                                     position=(inch(2.7115), inch(0), inch(0)),
                                     connection_size=inch(0.5), direction=(0.0, 0.0, -1.0),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="out-4", service=Service.WATER_HOT,
                                     position=(inch(1.2115), inch(0), inch(0)),
                                     connection_size=inch(0.5), direction=(0.0, 0.0, -1.0),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="out-5", service=Service.WATER_HOT,
                                     position=(inch(-0.2885), inch(0), inch(0)),
                                     connection_size=inch(0.5), direction=(0.0, 0.0, -1.0),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="out-6", service=Service.WATER_HOT,
                                     position=(inch(-1.7885), inch(0), inch(0)),
                                     connection_size=inch(0.5), direction=(0.0, 0.0, -1.0),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="out-7", service=Service.WATER_HOT,
                                     position=(inch(-3.2885), inch(0), inch(0)),
                                     connection_size=inch(0.5), direction=(0.0, 0.0, -1.0),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="out-8", service=Service.WATER_HOT,
                                     position=(inch(-4.7885), inch(0), inch(0)),
                                     connection_size=inch(0.5), direction=(0.0, 0.0, -1.0),
                                     certainty=PortCertainty.EXACT))),
)

# ** IN THE WORKSHOP'S NE CORNER BESIDE EQ-B-WH SINCE 2026-11-09 ** (was x=7'-6" in
# RM-B-FURNACE), so the 1" trunk is 7.2 ft: a foot of it holds what 4.7 ft of 1/2" PEX does.
# Body on x=13'-4" between the tank and W-B-HALL-W, inlet south, closed end 3/8" off
# W-B-CW2; tips at 86 1/8". Copper and 7.2 ft of trunk from the tap: UPC 604.13's 18" holds.
# Each branch drops 2 5/8" to 83 1/2" and turns west (a bend support at each), then:
#   out-1 SAUNA, out-2 KITCH: 6-7" west, up to 103 3/16" in the joist web, south and east.
#   out-3..8 FILLER, WASH, BATH2, BATH, BATH1, BATH2-SH: up at x=12'-7" to 95 7/16" and
#     west over the tank's elbow on their own outlet's line (BATH2 at 97 7/16"), each
#     dropping or climbing where it turns. Lines south of out-3 would meet
#     PR-M-S-SUITE-DRAIN's drop at x=10'-2".
# Lanes drawn by hand and graded by `haus check` (0 FAIL); `haus route --manifold` proposed
# exposed runs at fixture height.
EQUIPMENT_HEADER = [
    Equipment(uid="GVKJA0755W", tag="EQ-B-HW-HEADER", kind=EquipmentKind.WATER_MANIFOLD,
              position=pt(inch(160), inch(206)), rotation=deg(-90),
              footprint=(inch(14.675), inch(1.5)), room="RM-B-WORKSHOP",
              type_ref="EQ-T-HW-HEADER-8",
              mount=Mount(kind=MountKind.CEILING, elevation=inch(86.149)),
              install_parts=("Uponor A5110500 1/2in metal bend support",
                             "Uponor A5110500 1/2in metal bend support",
                             "Uponor A5110500 1/2in metal bend support",
                             "Uponor A5110500 1/2in metal bend support",
                             "Uponor A5110500 1/2in metal bend support",
                             "Uponor A5110500 1/2in metal bend support",
                             "Uponor A5110500 1/2in metal bend support",
                             "Uponor A5110500 1/2in metal bend support")),
]
