# haus: editable
# Catlin MEP — water supply — the house entry, hot/cold distribution, hydrant branches.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# The in-line valves, hammer arrestors and stops on these runs are authored separately in
# plan/mep_supply_devices.py.

from typehaus import (
    PipeRun,
    PipeSystem,
    ft,
    inch,
    pt,
)
from typehaus.model import m

# --- Water supply: the house entry out to the garage hydrant ------------------------
#
# The project's first WATER_COLD run: from the water entry (5', 0') to the garage hydrant,
# staying at the service's own 6' bury the whole way — a supply line that rises above frost
# anywhere along its length freezes there. Filed on ``main`` (datum 0'-0") so the authored
# elevations read straight off the drawing set; on ``basement`` (-9' datum) they would
# resolve nine feet lower.
#
# **The bury is 6' below *grade*, and grade is -2'-6" (2026-08-18), so the run sits at
# -8'-6".** It dropped with the soil it is buried in, exactly as the garage foundation it
# passes under did: FT-GF-S-DR's bearing plane went from -4'-2" to -6'-8", and this run from
# -6'-0" to -8'-6", so the 22" of cover between them is unchanged. The terminal rise ends
# 4 4/5" above the garage slab, which is also 2'-6" lower than it was.
#
# Straightened 2026-07-29 through 2026-08-15 into a straight line from entry to hydrant at
# x=5', touching only FT-GF-S-DR — earlier routes jogged around the garage footing and
# clipped its 45° influence line. `mep.hydrant_freeze_depth` checks every buried vertex holds
# the full 72" bury; the terminal rise is the hydrant's own self-draining barrel and exempt.
WATER_SUPPLY = [
    PipeRun(uid="CMP920AAAA", tag="PR-G-HYDRANT-CW", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(0)), pt(ft(5), ft(59, 6)), pt(ft(5), ft(59, 6))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(-8, -6), ft(-8, -6), ft(-2, -1.2)),
            serves=("FX-G-HYDRANT",)),
]

# --- Domestic hot/cold distribution (2026-07-29 plumbing pass) -----------------------
#
# PEX home-run-lite: 1" cold trunk tees off the water service at (5', 1'), 1" hot trunk
# leaves EQ-B-WH; both run the ceiling band south of the y=18' wall, cross the concrete
# through their own WALL_SLEEVES, and rise to each wet-wall group through SUPPLY_SLEEVES.
# `serves` on a trunk is the union of everything downstream, so `mep.pipe_sizing` sums the
# real WSFU. Filed on ``basement`` (datum -9') so ceiling runs read as 8'-ish heights.
#
# Cold trunk went 1" -> 1 1/4" on 2026-07-30: the stair-foot bath and sauna shower added 4
# WSFU, taking it from 30 to 34 against the 32 a 1" branch carries (Table 610.4, 46-60 psi /
# <100'). Hot trunk stays 1" at 21.5 WSFU; SP-B-CS2-CW (the trunk's cast crossing) grew with it.
SUPPLY = [
    PipeRun(uid="CBPW30AAAA", tag="PR-B-CW-TRUNK", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(1)), pt(ft(5), ft(1)), pt(ft(5), ft(16)),
                  pt(ft(8), ft(16)), pt(ft(29, 0.6), ft(16)),
                  pt(ft(29, 0.6), ft(34, 1.2)), pt(ft(29, 0.6), ft(34, 1.2))),
            diameter=inch(1.25), material="copper", finish="lacquered",
            elevations=(ft(3), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2),
                        ft(8, 1.2), ft(12, 6)),
            serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV", "FX-M-BATH2-WC",
                    "FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-SINK",
                    "FX-M-LAUNDRY", "FX-M-KITCH-SINK",
                    "FX-B-BATH-WC", "FX-B-BATH-LAV", "FX-B-SAUNA-SH",
                    "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2",
                    "FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH",
                    # The two south-face wall hydrants (2026-08-01), 2.5 WSFU cold each.
                    # 34 -> 39 on a 1 1/4" trunk that carries 64 in Table 610.4's 46-60 psi
                    # column, so the tee costs nothing in size.
                    "FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    PipeRun(uid="CBPW31AAAA", tag="PR-B-HW-TRUNK", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(m(1.88684), m(10.0015)),
                  pt(ft(6, 6), ft(19, 2.4)), pt(ft(6, 6), ft(15, 6))),
            diameter=inch(1), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(4), ft(8), ft(8), ft(8)),
            serves=("FX-M-BATH1-LAV", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK", "FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK",
                    "FX-M-KITCH-SINK",
                    "FX-B-BATH-LAV", "FX-B-SAUNA-SH",
                    "FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                    "FX-S-VANITY-LAV2", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH",
                    # The dishwasher was taking hot water from a branch that never declared
                    # it (2026-08-01). Undeclared, its 1.5 WSFU was missing from the trunk's
                    # load *and* `mep.water_hammer_arrestor` had no supply to ask about, so
                    # the quick-closing valve on it went ungraded rather than failing.
                    "APPL-M-DW")),
    # Cold feed to the water heater itself (equipment, not a fixture — no fixture units).
    PipeRun(uid="CBPW32AAAA", tag="PR-B-CW-WH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(5, 6), ft(16, 9.6)), pt(ft(5, 6), ft(19, 2.4)),
                  pt(m(1.88684), m(10.0015)), pt(m(1.88684), m(10.0015))),
            diameter=inch(1), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(4))),
    # Main-storey groups.
    PipeRun(uid="CBPW33AAAA", tag="PR-B-CW-BATH1", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(7, 4.8), ft(16, 9.6)),
                  pt(ft(7, 4.8), ft(19, 2.4)), pt(ft(6), ft(23, 7.2)),
                  pt(ft(6), ft(23, 7.2)), pt(ft(6), ft(23, 7.2))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(9), ft(12, 6)),
            wall_refs=(None, None, None, None, "W-M-BAE"),
            serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV")),
    PipeRun(uid="CBPW34AAAA", tag="PR-B-HW-BATH1", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(6), ft(24)), pt(ft(6), ft(24)),
                  pt(ft(6), ft(24))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(9), ft(12, 6)),
            wall_refs=(None, None, "W-M-BAE"),
            serves=("FX-M-BATH1-LAV",)),
    PipeRun(uid="CBPW35AAAA", tag="PR-B-CW-BATH2", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(2, 3), ft(16)),
                  pt(ft(2, 3), ft(17, 2.4)), pt(ft(2, 3), ft(17, 2.4))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(12)),
            serves=("FX-M-BATH2-WC", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK")),
    PipeRun(uid="CBPW36AAAA", tag="PR-B-HW-BATH2", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(2, 3), ft(15, 6)),
                  pt(ft(2, 3), ft(16, 9.6)), pt(ft(2, 3), ft(16, 9.6))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(8), ft(12)),
            serves=("FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-SINK")),
    # The laundry pair riser splits at the deck top (ft(9) basement-relative = 0'-0"
    # project), like the BATH1 pair above: sleeved concrete crossing below, stud cavity
    # above, each leg naming its own host so `mep.wet_wall_occupancy` doesn't read a single
    # riser as escaping the wall it's actually inside.
    PipeRun(uid="CBPW37AAAA", tag="PR-B-CW-WASH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(8), ft(16)), pt(ft(8), ft(20, 7.2)),
                  pt(ft(8), ft(20, 7.2)), pt(ft(8), ft(20, 7.2))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(9), ft(12)),
            wall_refs=(None, None, "W-M-BA2E"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeRun(uid="CBPW38AAAA", tag="PR-B-HW-WASH", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(8), ft(21, 2.4)),
                  pt(ft(8), ft(21, 2.4)), pt(ft(8), ft(21, 2.4))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(9), ft(12)),
            wall_refs=(None, None, "W-M-BA2E"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeRun(uid="CBPW39AAAA", tag="PR-B-HW-KITCH", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(29, 6.6), ft(15, 6)),
                  pt(ft(29, 6.6), ft(33, 7.2)), pt(ft(29, 6.6), ft(33, 7.2))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(8), ft(12, 6)),
            serves=("FX-M-KITCH-SINK", "APPL-M-DW")),
    # Second-storey groups: risers climb two storeys to the hall bath, split at both deck
    # top (ft(9) basement-rel = 0'-0" project) and second floor (ft(19) = 10'-0" project),
    # naming the host wall on each leg. Main-storey leg is in a 2x4 partition (3.5" cavity,
    # ample for 3/4" PEX); only the second-storey leg is in a staggered wet wall.
    PipeRun(uid="CBPW40AAAA", tag="PR-B-CW-SBATH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(4), ft(16, 9.6)), pt(ft(4), ft(26, 4)),
                  pt(ft(5, 7.2), ft(26, 4)), pt(ft(5, 7.2), ft(26, 4)),
                  pt(ft(5, 7.2), ft(26, 4)), pt(ft(5, 7.2), ft(26, 4))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(9), ft(19),
                        ft(21, 6)),
            wall_refs=(None, None, None, None, "W-M-STOS", "W-S-BD-N"),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # Riser moved 2.4" -> 4" east of N-M-BA1 (2026-08-02, RM-M-MUD-CLOSET): the old x=6'-2.4"
    # left half the pipe in W-M-STOS2's corner pack after W-M-MUDC-E tee'd in. 6'-4" is the
    # first clean bay past the tee (6 1/2" west of D-M-MUD's jamb pack, 8" west of D-S-BATH1's
    # above). SP-M-HW-SBATH moved with it.
    PipeRun(uid="CBPW41AAAA", tag="PR-B-HW-SBATH", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(6, 4), ft(26, 4)),
                  pt(ft(6, 4), ft(26, 4)), pt(ft(6, 4), ft(26, 4)),
                  pt(ft(6, 4), ft(26, 4))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(9), ft(19), ft(21, 6)),
            wall_refs=(None, None, "W-M-STOS2", "W-S-BD-N1B"),
            serves=("FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                    "FX-S-VANITY-LAV2")),
    PipeRun(uid="CBPW42AAAA", tag="PR-B-CW-SUITE", system=PipeSystem.WATER_COLD,
            path=(pt(ft(8), ft(16)), pt(ft(13, 7.2), ft(16, 10.8)),
                  pt(ft(13, 7.2), ft(16, 10.8))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(21, 6)),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
    PipeRun(uid="CBPW43AAAA", tag="PR-B-HW-SUITE", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(14, 2.4), ft(16, 10.8)),
                  pt(ft(14, 2.4), ft(16, 10.8))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(21, 6)),
            serves=("FX-S-SUITEBATH-LAV", "FX-S-SUITEBATH-TUBSH")),
    # Stair-foot bathroom, fed off the same pair of runs (same uids) that fed FX-1 until
    # 2026-07-30, now turned east through W-B-STR's two sleeves at their own y (cold 20'-3",
    # hot 19'-9") to x=16', then north into W-B-BA-N's cavity. Cold carries the WC and
    # lavatory (3.25 WSFU), hot the lavatory alone.
    PipeRun(uid="CBPW44AAAA", tag="PR-B-CW-BATH", system=PipeSystem.WATER_COLD,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(7), ft(26)), pt(ft(7), ft(20, 3)),
                  pt(ft(16), ft(20, 3)), pt(ft(16), ft(21, 9.375)),
                  pt(ft(16), ft(21, 9.375))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2),
                        ft(2, 6)),
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    PipeRun(uid="CBPW45AAAA", tag="PR-B-HW-BATH", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(7, 3.6), ft(26)),
                  pt(ft(7, 3.6), ft(19, 9)), pt(ft(16), ft(19, 9)),
                  pt(ft(16), ft(21, 9.375)), pt(ft(16), ft(21, 9.375))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8), ft(8), ft(8), ft(8), ft(8), ft(2, 6)),
            serves=("FX-B-BATH-LAV",)),
    # Sauna shower mixer, the first supply this room ever had. Both legs tee off the existing
    # trunks and run down the aisle at x=17'-4" (2" clear of W-B-CS2's face at 17'-6"), through
    # W-B-SA-N's framed stud bay (no cast sleeve needed) to the valve inside W-B-CS's liner.
    # No supply to FX-B-SAUNA-FD: a floor drain has none.
    PipeRun(uid="CBPW46AAAA", tag="PR-B-CW-SAUNA", system=PipeSystem.WATER_COLD,
            path=(pt(ft(17, 4), ft(16)), pt(ft(17, 4), ft(12, 2)),
                  pt(ft(17, 4), ft(12, 2))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(4, 6)),
            serves=("FX-B-SAUNA-SH",)),
    PipeRun(uid="CBPW47AAAA", tag="PR-B-HW-SAUNA", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(17, 4), ft(15, 6)),
                  pt(ft(17, 4), ft(11, 10)), pt(ft(17, 4), ft(11, 10))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8), ft(8), ft(8), ft(4, 6)),
            serves=("FX-B-SAUNA-SH",)),
]

# --- The two south-face wall hydrants (2026-08-01) -----------------------------------
#
# Both fed from above, out of the second floor's joist space (FS-SECOND, 11 7/8" I-joists),
# rather than from below: the main-storey exterior wall's stud cavity sits directly over
# W-B-S1 (12" cast concrete, and W-M-C1/W-B-CS on the centre line), so a riser through
# SL-M-DECK would surface through the top of a bearing wall. One riser leaves the basement
# and splits upstairs — one leg into W-M-S1 to the porch hydrant, one into W-S-S1 to the
# balcony hydrant — always inboard of the wall's 4" continuous exterior insulation so the
# pipe stays warm.
#
# The riser stands in W-M-BDN1, a 2x4 partition (3.5" cavity, ample for 3/4" PEX) whose
# deck crossing (SP-M-CW-HYD) lands in open slab at x=6', not on a wall below.
HYDRANT_BRANCH_BASEMENT = [
    # Two runs, one branch: material changes at the deck. Ceiling leg is exposed lacquered
    # copper like everything else down here; slab-up it's inside wall/joist bays, hidden, so
    # PEX's freeze tolerance matters more than finish.
    PipeRun(uid="X4M2QP7B0K", tag="PR-B-CW-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(16)), pt(ft(6), ft(13))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2)),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    PipeRun(uid="Z5NB8QMK2H", tag="PR-B-CW-HYD-RISER", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(13)), pt(ft(6), ft(13)), pt(ft(6), ft(13)),
                  pt(ft(6), ft(13))),
            diameter=inch(0.75), material="pex",
            # Basement-relative -> project: 8'-1.2" ceiling trunk, 9'-0" deck top (0'-0"),
            # 18'-0" W-M-BDN1's top plate (9'-0", the partition's ceiling height), 18'-3"
            # (9'-3") inside the joist space (11 7/8" joists hang 9'-0 1/8" to 10'-0"). Split
            # at the plate because `mep.wet_wall_occupancy` grades an in-wall segment against
            # the wall's own z-extent; a straight riser would escape it by 3".
            elevations=(ft(8, 1.2), ft(9), ft(18), ft(18, 3)),
            wall_refs=(None, "W-M-BDN1", None),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
]

# Joist-space distribution, filed on ``main`` (datum 0'-0") so 9'-3" reads as the ceiling
# height it is. The E-W leg runs *along* a joist bay at y=0'-9"; the riser crosses joists at
# x=6' drilled through their webs — 3/4" PEX in an 11 7/8" I-joist web is within every
# manufacturer's hole chart, which is why this branch stays PEX rather than becoming copper.
HYDRANT_BRANCH_MAIN = [
    PipeRun(uid="R9TC5VZ1WQ", tag="PR-M-CW-HYD-DIST", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(13)), pt(ft(6), ft(0, 9)), pt(ft(16, 8), ft(0, 9))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(9, 3)),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    # Porch leg: south into the wall's own plane (y=3 1/4", the 2x6 cavity's centre line),
    # then straight down inside W-M-S1 to the hydrant's seat at 2'-0".
    PipeRun(uid="B6HD0NKX3M", tag="PR-M-CW-PORCH-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12), ft(0, 9)), pt(ft(12), ft(0, 3.25)), pt(ft(12), ft(0, 3.25))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(2)),
            wall_refs=(None, "W-M-S1"),
            serves=("FX-M-PORCH-HYD",)),
    # Balcony leg: the same jog into the wall plane, then up. Split at 10'-0" because the
    # second floor is between: below that line the pipe is crossing the deck and hosted by
    # nothing, above it it is inside W-S-S1's cavity (which starts at 10'-0"), and
    # `mep.wet_wall_occupancy` grades a declared segment against the wall's own z-extent.
    PipeRun(uid="V2FJ8LRY6P", tag="PR-M-CW-BALC-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(16, 8), ft(0, 9)), pt(ft(16, 8), ft(0, 3.25)),
                  pt(ft(16, 8), ft(0, 3.25)), pt(ft(16, 8), ft(0, 3.25))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(10), ft(12)),
            wall_refs=(None, None, "W-S-S1"),
            serves=("FX-S-BALC-HYD",)),
    # The barrel: the hydrant's own metal tube + sleeve, modelled as a run so the insulation
    # can be billed and `mep.exterior_hydrant_protection` has something to grade. The one
    # place in the house where a supply pipe is *in* the envelope rather than behind it — 10"
    # of metal from the seat out through sheathing/polyiso/EPS/rainscreen to the escutcheon
    # at y=-5". PEX stops at the seat so the thermal bridge doesn't extend into the room.
    PipeRun(uid="T8WQ3E5AZC", tag="PR-M-CW-PORCH-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12), ft(0, 3.25)), pt(ft(12), inch(-5))),
            diameter=inch(0.75), material="copper",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(ft(2), ft(2)),
            serves=("FX-M-PORCH-HYD",)),
]

# The balcony hydrant's barrel, filed on ``second`` (datum 10'-0") with the wall it pierces.
HYDRANT_BRANCH_SECOND = [
    PipeRun(uid="G7YB4XN2SD", tag="PR-S-CW-BALC-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(16, 8), ft(0, 3.25)), pt(ft(16, 8), inch(-5))),
            diameter=inch(0.75), material="copper",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(ft(2), ft(2)),
            serves=("FX-S-BALC-HYD",)),
]
