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
# branches leave at 83 1/2", under the basement-ceiling drains, where the old trunk ran.
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

# Hung under the basement ceiling in RM-B-FURNACE on the old trunk's x=7'-6" lane, inlet
# north at (7'-6", 25'-6"), body centre 88" (the trunk's height there). Copper and 13 ft of
# developed trunk from the tap, so every PEX branch clears UPC 604.13's 18".
EQUIPMENT_HEADER = [
    Equipment(uid="GVKJA0755W", tag="EQ-B-HW-HEADER", kind=EquipmentKind.WATER_MANIFOLD,
              position=pt(inch(90), inch(298.6625)), rotation=deg(90),
              footprint=(inch(14.675), inch(1.5)), room="RM-B-FURNACE",
              type_ref="EQ-T-HW-HEADER-8",
              mount=Mount(kind=MountKind.CEILING, elevation=inch(86.149))),
]
