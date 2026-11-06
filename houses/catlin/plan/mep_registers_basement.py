# haus: editable
# Catlin MEP — air terminals on the basement. plan/mep.py re-exports the lists below
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
    REG_B_EXH1,
    REG_B_EXH2,
    REG_B_RET1,
    REG_B_SUP1,
    REG_B_SUP2,
    REG_B_SUP3,
)

# Basement terminals are ceiling valves under the FS-M-* floors, fed from the CHASE trunks in
# the joist/truss cavity above — except the sauna's stale pickup, which is the one
# wall-mounted terminal in the house (see below).
REGISTERS_BASEMENT = [
    Register(uid="CBRV01AAAA", tag="REG-B-SUP1", kind=DuctSystem.SUPPLY, room="RM-B-GYM",
            # Dragged north-east on 2026-09-05 and kept, rounded onto (19'-0", 13'-0") —
            # 1 11/16" and 1/2" off the drag, both genuinely round stations, and near the
            # centre of the gym's 18' x 18' ceiling instead of tucked into its south-west
            # corner. DU-B-ERV-R-GYM's last leg follows it: a register and the duct that
            # feeds it have to end at the same point. 13'-4" since 2026-10-31: on 13'-0" the
            # valve's collar stood on an FS-M-EAST joist (`mep.terminal_neck_fit`).
            # 10 cfm since 2026-11-03: 8 went to the sauna's supply (REG-B-SUP3).
            position=pt(ft(19), ft(13, 4)), duct_ref="DU-B-ERV-R-GYM",
            type_ref="REG-T-ERV-VALVE-SUP", design_cfm=REG_B_SUP1,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # RM-B-PLAY-N is 324 sf of windowless habitable MEDIA space, legal only under R303.1
    # Exception 1, whose second half requires outdoor air supplied to *the room* — an
    # adjacent room's grille doesn't satisfy it. **Deleting this terminal is a hard
    # code.R303_1_light_and_ventilation FAIL.**
    #
    # (19', 20'-6"): entering at the room's west edge and stopping just inside cuts about eight
    # feet of duct off the old (27', 27') position; it still throws away from FURN-B-PLAY-TV on
    # the east wall. Moved 5'-0" south on 2026-09-23 (was y=25'), where the duct arrives from
    # the south up the hall: over the walk between the south bookcases (fronts y=19'-3 3/8",
    # tops 7'-6") and the sectional, not over either.
    # ** 20'-6" SINCE 2026-11-01 (decision #112). ** The ceiling is FS-M-NE's trusses over a
    # resilient channel, so the valve's 125 mm collar and increaser (2.94" tall) stand in the
    # cavity: at y=20'-0" they stood on a 12" o.c. truss (`mep.terminal_neck_fit`, 3.50"); at 20'-6"
    # they are mid-bay of the 16" o.c. lines (236, 252: 237 3/4".. 250 1/4"), fed by the cavity duct.
    Register(uid="CBRV02AAAA", tag="REG-B-SUP2", kind=DuctSystem.SUPPLY, room="RM-B-PLAY-N",
            position=pt(ft(19), ft(20, 6)), duct_ref="DU-B-ERV-R-PLAY",
            type_ref="REG-T-ERV-VALVE-SUP-125", design_cfm=REG_B_SUP2,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # THE WORKSHOP TERMINAL IS A BENCH HOOD, NOT A CEILING DIFFUSER: a diffuser eight feet
    # up does not capture solder fume, it dilutes it into the room and then extracts the
    # dilution. REG-T-ERV-BENCH-HOOD is a 30" x 12" capture face hung at 5'-6", i.e. 24"
    # above FURN-B-WORKSHOP-BENCH-N/S's 34" tops, and it captures at the source.
    #
    # It stays `kind=RETURN` rather than becoming a dedicated EXHAUST: the fumes are light,
    # the heat is worth recovering, and this is not a spray booth.
    #
    # HONEST LIMIT: the two benches run ten feet along the west wall (y 3'-6"..13'-6") and
    # one 30" hood captures a fraction of that. It is a bench hood, not bench-run
    # coverage. It is a bench hood, not bench-run coverage.
    Register(uid="CBRV03AAAA", tag="REG-B-RET1", kind=DuctSystem.RETURN, room="RM-B-WORKSHOP",
            position=pt(ft(2), ft(8, 6)), duct_ref="DU-B-ERV-R-BENCH",
            type_ref="REG-T-ERV-BENCH-HOOD", design_cfm=REG_B_RET1,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(5, 6))),
    # The sauna's stale pickup is on the wall, 4" above the floor on the WEST liner below
    # FURN-B-SAUNA-UPPER; its inset posts keep the register face clear. The former south
    # face rotated on 2026-09-05 and
    # EQ-B-SAUNA-HTR took that wall: a sauna stratifies hard, so the low pickup pulls
    # the cold spent
    # layer off the floor rather than the löyly at bench height. Paired with REG-B-SUP3 over
    # the heater, both ends closeable wood vents (REG-T-SAUNA-VENT-*), it drives the room's convection
    # loop — down the far wall, across the floor, out under the bench. EXHAUST at 20 cfm:
    # the room is Occupancy.BATHROOM and its window's openable area (1.2 sf) falls short of
    # R303.3's 1.5 sf, so mechanical exhaust governs.
    Register(uid="CBRV04AAAA", tag="REG-B-EXH2", kind=DuctSystem.EXHAUST, room="RM-B-SAUNA",
            duct_ref="DU-B-ERV-R-SAUNA-EXH",
            type_ref="REG-T-SAUNA-VENT-EXH", design_cfm=REG_B_EXH2,
            mount=Mount(kind=MountKind.WALL, elevation=inch(4), recessed_into_host_surface=True),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-B-SA-W", face="right", distance_from_start=inch(38),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # Fresh air in high, over the stones, directly above EQ-B-SAUNA-HTR (the EAST liner
    # since 2026-09-05 round three, plan/electrical.py) at 7'-0" — below the 8' ceiling so
    # the boot doesn't fight the drop ceiling the condensate line already runs above. It
    # moved 1'-5" east with the heater, and DU-B-ERV-R-SAUNA-SUP's east leg moved with both:
    # the register sits on the heater's own centre, which is what "over the stones" means.
    # 20 cfm since 2026-11-03, balancing REG-B-EXH2 behind the sealed sauna door; the 8 cfm
    # came off REG-B-SUP1 on the same plenum (notes/erv_static_budget.md §10.8).
    Register(uid="CBRV06AAAA", tag="REG-B-SUP3", kind=DuctSystem.SUPPLY, room="RM-B-SAUNA",
            position=pt(inch(199.75), inch(20.5)), duct_ref="DU-B-ERV-R-SAUNA-SUP",
            type_ref="REG-T-SAUNA-VENT-SUP", design_cfm=REG_B_SUP3,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(7))),
    # RM-B-BATH. Filed as EXHAUST rather than RETURN, like RM-S-BATH1's terminal and unlike
    # the basement's other two stale pickups: a bathroom's air is pulled and not
    # recirculated. It is a SIDEWALL grille high on W-B-STR3B, the west wall, far from the
    # door, so the room's makeup air crosses it. Since 2026-09-22: the ceiling grille at
    # (12', 24'-1 5/8") was fed through ST-B2M's stringer. x is the bath-side paint face plus
    # 1"; the base at 7'-1 1/4" centres the 7" face on the duct.
    Register(uid="CBRV05AAAA", tag="REG-B-EXH1", kind=DuctSystem.EXHAUST, room="RM-B-BATH",
            duct_ref="DU-B-ERV-R-BATH",
            type_ref="REG-T-ERV-VALVE-EXH-WALL", design_cfm=REG_B_EXH1,
            mount=Mount(kind=MountKind.WALL, elevation=inch(85.25)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-B-STR3B", face="left", distance_from_start=inch(18),
                 normal_gap=inch(0), rotation_offset=deg(-180)))),
]
