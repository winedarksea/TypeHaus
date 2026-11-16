# haus: editable
# Catlin MEP — air terminals on the attic. plan/mep.py re-exports the lists below
# (AGENTS.md §1.1); the ERV terminals' flows are named in plan/erv_balance.py.

from typehaus import (
    DuctSystem,
    Mount,
    MountKind,
    Register,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, WallAttachment

from .erv_balance import (
    REG_A_RET1,
    REG_A_STUBATH_EXH,
)

REGISTERS_HVAC_ATTIC = [
    # Keep the floor boot in FS-ATTIC's y=3'-4" bay, under the desk's open top near the
    # centreline wall. Rotate the 12x6 grille along the desk: x=18'-7"..19'-1" clears the
    # desk chair's west edge (~19'-3") and stays inside the desk footprint. Its 6" rise
    # (DU-S-HP-STUDY-BOOT) stands straight up off DU-S-HP-SOUTH's top in SF-S-DUCT.
    Register(uid="CARH01AAAA", tag="REG-A-HP-STUDY", kind=DuctSystem.SUPPLY,
             room="RM-A-STUDY", position=pt(ft(18, 10), ft(3, 4)), rotation=deg(90),
             duct_ref="DU-S-HP-STUDY-BOOT",
             type_ref="REG-T-HP-FLOOR-0612", design_cfm=100,
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # Directly above the hall soffit: a 6" rise (DU-S-HP-EAST-BOOT) stands off the trunk's
    # crown through FS-ATTIC's bay. y=11'-4" is the next FS-ATTIC bay centre north of
    # W-A-SN's north face (9'-10 3/8", thickened to 12 3/4" for the study's bookcase wall)
    # and is still over DU-S-HP-SUP; the grille stays inside RM-A-EAST-UNFIN and clear of
    # FO-A-STAIR's walkway.
    Register(uid="CARH02AAAA", tag="REG-A-HP-EAST", kind=DuctSystem.SUPPLY,
             room="RM-A-EAST-UNFIN", position=pt(ft(19, 4), ft(11, 4)), duct_ref="DU-S-HP-EAST-BOOT",
             type_ref="REG-T-HP-FLOOR-0612", design_cfm=35,
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # RM-A-EAST-UNFIN's return (owner, 2026-11-12): the 35 cfm its supply pushes in goes back
    # to the air handler through the stock 12x12x1 on the SOUTH face of EQ-S-ERV-MIX (x 298-325.5",
    # y 328-368"), centred 14" AFF (base at 6"), reached from the room. ** THE DAMPER IS THE DESIGN. ** The plenum's
    # returns are in PARALLEL and an open 12x12 pulls its share of the 750 cfm from the nearest
    # grille, not the 35 it was given; the locked balancing damper in the stub, set to 35 cfm
    # through the hinged face, is what stops the short-circuit. Re-check at filter changes.
    Register(uid="S81SMAW96C", tag="REG-A-HP-EAST-RET", kind=DuctSystem.RETURN,
             room="RM-A-EAST-UNFIN", position=pt(inch(311.75), inch(322.5)),
             duct_ref="DU-A-HP1-EAST-RET", type_ref="REG-T-HP-RET-FILTER-1212-WALL",
             design_cfm=35, mount=Mount(kind=MountKind.WALL, elevation=inch(6))),
    # The west loft's supply: a floor boot fed by DU-S-HP-WEST-BOOT, a side take-off off
    # DU-S-HP-SUITE (which lies under the y=14'-8" joist) that turns south into the bay and
    # stands up. At (17'-0", 14'-0") since 2026-10-14, rotated 90 degrees; its 6" x-face
    # clears W-A-C2's gypsum by 5 5/8".
    # The room gets conditioned air off System 1 like RM-A-STUDY/RM-A-EAST-UNFIN, returning
    # stale air at REG-A-RET1, so the ERV's attic side is extract-only.
    #
    # `room=RM-A-STUDIO` is LOAD-BEARING TWICE OVER: the room is habitable (the craft room),
    # and this one register answers two checks for it — `mep.ventilation_distribution` wants a
    # fresh-air supply in it, and R303.1 Exception 1 (which is how this
    # room gets out of its 8% glazing shortfall — see plan/lighting_attic.py) requires a
    # mechanical fresh-air SUPPLY Register in the room as one of its four conditions. NO
    # MINI-SPLIT IS WANTED: reusing this boot is the whole reason the studio costs what it
    # costs.
    Register(uid="CARH03AAAA", tag="REG-A-HP-WEST", kind=DuctSystem.SUPPLY,
             room="RM-A-STUDIO", position=pt(ft(17), ft(14)), rotation=deg(90),
             duct_ref="DU-S-HP-WEST-BOOT", type_ref="REG-T-HP-FLOOR-0612", design_cfm=75,
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

# The attic ERV terminals: extract only. Fresh air is off System 1 (REG-A-HP-WEST, the
# floor boot in REGISTERS_HVAC_ATTIC above); this is the stale pickup — the same pattern as
# every other storey. The attic is not one cathedral volume: it is a craft room, a closed
# bathroom and a walled storage pocket with three doors between them, so REG-A-RET1 sits in
# the studio and the bath gets its own terminal, because R303.3 requires local exhaust from
# a bathroom and a grille in the next room is not it.
REGISTERS_ATTIC = [
    # x=1'-0": the 6:12 roof underside there is 7 1/2" above the deck — a wedge nothing else
    # can use, no furniture can stand in and nobody walks through — which is exactly what
    # makes it the right home for a boxed-in 3" surface duct and a floor grille at its end.
    # Moving it inboard would put a duct across a finished room to buy headroom a floor
    # boot has no use for.
    # (1'-0", 20'-8") is a floor boot in the studio's NW corner, on the existing x=1'-0" chase,
    # at a bay centre (248" = 8 + 15 x 16), diagonally opposite REG-A-HP-WEST's supply at
    # (17'-0", 14'-0"). Fresh in at one corner, stale out at the other, which is the
    # arrangement every other storey already has.
    Register(uid="CARV04AAAA", tag="REG-A-RET1", kind=DuctSystem.RETURN, room="RM-A-STUDIO",
            position=pt(ft(1), ft(20, 8)), duct_ref="DU-A-ERV-R-ATTIC",
            type_ref="REG-T-ERV-EXH-FLOOR", design_cfm=REG_A_RET1,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # ** THE BATH'S EXHAUST, AND ITS design_cfm IS NOT OPTIONAL. ** R303.3 accepts an operable
    # window OR a local exhaust; this room has no exterior wall, so it is the exhaust — and
    # `checks/.../ventilation.py` reads the AUTHORED number on the GRILLE (the run's is only a
    # fallback for a single-terminal branch, and None on both is UNKNOWN, never a pass).
    #
    # 20 cfm lands in R303.3's CONTINUOUS band, which is what every other bath terminal in this
    # house runs at — 50 cfm intermittent would pass the same check and would be the odd one
    # out on a balanced machine whose whole attic side is continuous extract.
    #
    # A WALL MOUNT, AND AT 3'-0" RATHER THAN THE 4'-4" THE WALL WOULD ALLOW (2026-09-26).
    # There is no ceiling plenum under a cathedral: the room follows the roof, and
    # W-A-STU-W's 5 1/2" 2x6 cavity is the only place a duct can drop into the
    # FS-ATTIC bay. PR-A-STUBATH-VENT runs that same cavity at 3'-5"..3'-9", so a riser to a
    # higher grille crosses it; at 3'-0" the 4" boot tops out at 3'-2" and the vent passes
    # over it. A lower pickup gives up some stratified moist air, which the 20 cfm
    # continuous rate absorbs.
    Register(uid="N989VQP3T8", tag="REG-A-STUBATH-EXH", kind=DuctSystem.EXHAUST, room="RM-A-STUBATH",
            # y=21'-8 1/2" is where DU-A-ERV-R-STUBATH can actually stand: the wet wall's
            # axis carries the suite's two drains south of 21'-4 5/8", and this is the first
            # stud bay north of them (see plan/mep_erv_l3.py). The grille follows the riser,
            # not the other way round — on this wall there is one station and the plumbing
            # picked it. x=9'-11 7/16" is W-A-STU-W's bath-side paint face plus the ~1"
            # inboard offset every wall device here carries, NOT the wall AXIS — on the axis
            # the footprint centre sits inside the wall and outside the room, and
            # `integrity.placeable_room_mismatch` says so. The riser stays on the axis in the
            # staggered cavity; the offset is the boot crossing the finish.
            duct_ref="DU-A-ERV-R-STUBATH",
            # REG-T-ERV-EXH-WALL, not the ceiling REG-T-ERV-EXH: this is the house's only
            # WALL-mounted extract, and on the ceiling type the resolver read its 7" face as
            # 7" of projection into the room. See plan/mep_hvac.py.
            type_ref="REG-T-ERV-VALVE-EXH-WALL", design_cfm=REG_A_STUBATH_EXH,
            mount=Mount(kind=MountKind.WALL, elevation=inch(35)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-A-STU-W", face="right", distance_from_start=inch(52.5),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
]
