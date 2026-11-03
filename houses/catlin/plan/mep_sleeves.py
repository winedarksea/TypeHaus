# haus: editable
# Catlin MEP — concrete penetrations — the sleeves and stubs cast into slabs and walls.
#
# plan/mep.py re-exports the storey lists below (AGENTS.md §1.1), so the manifest is
# unchanged.
#
# Positions are the exact pre-pour centers the concrete crew works from, validated against
# the fixture drain point (`mep.sleeve_alignment`); nothing here is derived. Framed-floor
# drops (e.g. the second-floor hall bath into wet wall W-S-BD-N) need no sleeve at all.
#
# The main floor is wood end to end since 2026-11-01 (decision #112: FS-M-NE replaced the
# concrete band SL-M-DECK), so nothing on it casts a sleeve. A pipe crossing a joist bay or
# truss web is bored or dropped between the members on site — nothing to cast, nothing to get
# wrong before the pour, which is the only reason a SleevePenetration exists.

from typehaus import (
    PipeRun,
    Service,
    SleevePenetration,
    ft,
    inch,
    pt,
)
from typehaus.model import m

SLEEVES = []

# Supply risers through a deck: none. The kitchen pair rises through FS-M-NE's truss bay.
SUPPLY_SLEEVES = []

# Second-storey waste stacks. The upstairs bathrooms drain down through framed walls and
# floors — joists everywhere they land, not concrete. Empty, and kept rather than deleted
# so plan/mep.py's re-export and the manifest stay as they are, and so the next stack that
# does cross a pour has an obvious home.
STACK_SLEEVES = []

# Slab-on-grade stub-ups. A fixture on grade has no wall drain stack — its trap arm runs
# *under* the slab — so the penetration is set pre-pour, at the
# fixture's own `drain_position` for an exact alignment match: a bathroom at the stair foot,
# and the sauna's shower end (curbed pan + floor drain). All four moved with the rooms on
# 2026-09-05 when the sauna rotated onto the garden wall and the bathroom onto the stair
# wall; `mep.sleeve_alignment` is what holds each of them on its fixture.
SLAB_STUBS = [
    # Upsized to 3" for a WC (needing a closet bend) in place of the old utility sink.
    SleevePenetration(uid="CBP901AAAA", tag="SP-B-BATH-WC", host_ref="SL-B-FLOOR",
                      position=pt(ft(12), inch(291.8125)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-B-BATH-WC"),
    SleevePenetration(uid="CBP904AAAA", tag="SP-B-BATH-LAV", host_ref="SL-B-FLOOR",
                      position=pt(ft(12), inch(224.375)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-B-BATH-LAV"),
    # FX-B-UTIL-SINK's drop, inside W-B-STR2 under the vent tee (mep_lavatories.py).
    SleevePenetration(uid="RF0AQ0KDPT", tag="SP-B-SLAB-USINK", host_ref="SL-B-FLOOR",
                      position=pt(inch(120), inch(229.5)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-B-UTIL-SINK",
                      seal="continuous radon-rated elastomeric seal to pipe and slab membrane"),
    # FX-B-BATH-WC's vent riser (mep_vent_tees.py PR-B-BATH-WC-VENT), up W-B-STR2's cavity.
    SleevePenetration(uid="PXGXETEFWC", tag="SP-B-SLAB-WC-VENT", host_ref="SL-B-FLOOR",
                      position=pt(inch(121.6), inch(231.3)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), purpose=Service.VENT,
                      seal="continuous radon-rated elastomeric seal to pipe and slab membrane"),
    # The sauna vents' risers (mep_venting.py PR-B-SAUNA-VENT, PR-B-SAUNA-FD-VENT), up W-B-SA-N2/-N.
    SleevePenetration(uid="1RDFAM8VSF", tag="SP-B-SLAB-SA-VENT", host_ref="SL-B-FLOOR",
                      position=pt(inch(204), inch(121.375)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), purpose=Service.VENT,
                      seal="continuous radon-rated elastomeric seal to pipe and slab membrane"),
    SleevePenetration(uid="KY9JRBHRRZ", tag="SP-B-SLAB-SA-FDV", host_ref="SL-B-FLOOR",
                      position=pt(inch(152), inch(121.375)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), purpose=Service.VENT,
                      seal="continuous radon-rated elastomeric seal to pipe and slab membrane"),
    # The sauna's two. The pan's is under the centre of the 36" x 36" curbed shower; the floor
    # drain's is the drain body itself, which is why its position and the fixture's are the
    # same point with no `drain_position` override on either.
    SleevePenetration(uid="CBP905AAAA", tag="SP-B-SAUNA-SH", host_ref="SL-B-FLOOR",
                      position=pt(inch(191.75), inch(98.1875)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-B-SAUNA-SH"),
    SleevePenetration(uid="CBP906AAAA", tag="SP-B-SAUNA-FD", host_ref="SL-B-FLOOR",
                      position=pt(ft(13, 6), inch(98.1875)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-B-SAUNA-FD"),
    # Kitchen stack west of the dry-fire lane and south of FT-B-N4. Seal both
    # the sleeve-to-pipe annulus and sleeve-to-slab joint to the radon membrane.
    SleevePenetration(uid="CKSLAB0001", tag="SP-B-SLAB-KITCH", host_ref="SL-B-FLOOR",
                      position=pt(inch(32.5), inch(406.5)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3),
                      seal="continuous radon-rated elastomeric seal to pipe and slab membrane"),
    # Where the ceiling collector turns down to become the under-slab building drain; 4",
    # matching the building drain. `mep.sleeve_coverage` holds the crossing.
    SleevePenetration(uid="CBP902AAAA", tag="SP-B-SLAB-MAIN", host_ref="SL-B-FLOOR",
                      position=pt(ft(3), ft(16, 6)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6)),
]

# Horizontal sleeves through the basement's cast concrete walls: every run crossing the
# perimeter is a cast-in hole (`mep.sleeve_coverage`).
# center_elevation is project-frame absolute (the walls span -9'-1 7/16"..-13 7/16");
# neighbours keep >= 5" apart so the 4"-tolerance matcher stays unambiguous.
#
# SP-B-SEWER-EXIT — the drain's own crossing — carries a re-stated absolute elevation,
# since every ``PipeRun.elevations`` in this house is basement-storey-relative
# and this sleeve is the only absolute number in the drainage path.
# ``mep.sewer_exit_invert`` is what would catch a mismatch.
#
# What is left crosses concrete that is still concrete: the perimeter and the footings.
# Every crossing of a framed wall (W-B-CW, W-B-CW2, W-B-CW3, W-B-CE, W-B-STR2, W-B-CS, and
# since 2026-11-01 W-B-CS2/-CN2/-CN on the x=18' line) takes a bored hole on the day, or
# passes over the plate, not a sleeve set before a pour.
WALL_SLEEVES = [
    # The x=18' line casts no sleeves: W-B-CS2/-CN2/-CN are framed 2x6 bearing walls, and
    # the supply, drain and ERV runs cross over their plate in FS-M-NE's truss space.
    # PR-B-COND crosses W-B-CS (2x6 stud, not concrete) with a bored hole, not a sleeve —
    # same reasoning as the framed-wall crossings above.
    # Perimeter exits.
    # Building drain leaves NORTH, *under* FT-B-N4, toward the street (2026-10-01; it left
    # south under FT-B-S1 until then). The walls stop at the slab top, above the sewer
    # connection, so this is an under-footing protection sleeve (UPC 314.1,
    # `mep.footing_clearance`) on the wall line, the pipe 3 3/4" clear of SM-B-RADON.
    # center_elevation = invert (-129.3125" project, the main's 1/4"/ft line at y=36')
    # + half the 4" pipe = -127.3125", matched to within 1/2" by `mep.sewer_exit_invert`.
    SleevePenetration(uid="CBPW18AAAA", tag="SP-B-SEWER-EXIT", host_ref="FT-B-N4",
                      position=pt(ft(3), ft(36)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6), axis="horizontal",
                      center_elevation=inch(-127.3125)),
    # The water's two wall crossings, side by side under ST-B2M's upper landing in W-B-N2, at
    # the 6' bury (-8'-10"): a sleeve at -6'-0" would be a bore the pipe misses by 2'-10".
    # Both sit 6" above the wall's own bottom, as low as a crossing goes before the footing.
    # SP-B-N3-HYD (x=11'-0", tag kept) carries the hydrant branch back out; SP-B-N2-SVC
    # (x=11'-4") brings the service lateral in, where PR-B-CW-TRUNK rises (2026-10-29).
    SleevePenetration(uid="CBPW20AAAA", tag="SP-B-N3-HYD", host_ref="W-B-N2",
                      position=pt(ft(11), ft(35, 6)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-8, -10)),
    SleevePenetration(uid="3N11XJK7M8", tag="SP-B-N2-SVC", host_ref="W-B-N2",
                      position=pt(ft(11, 4), ft(35, 6)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-8, -10)),
]

# The hydrant line's garage-foundation protection (UPC 314.1 — Minn. R. 1309.0010 subp. 3.D
# strikes the IRC chapter P2604 lived in): the buried run passes 22" below FT-GF-S-DR's
# 6'-8" bearing plane, on its centerline, inside a protection sleeve —
# being *under* a footing is the worst case in its 45° influence cone, not clearance from it.
#
# `mep.footing_clearance` requires the run to actually thread the sleeve, not merely pass
# near the footing (checks/mep/plumbing_concrete.py) — see params/foundations.py for the
# hydrant's station at (11'-0", 48'-1 5/16"), chosen to clear the west and south footings.
GARAGE_SLEEVES = [
    # It crosses the garage's south foundation line at x=11'-0", at -8'-10", inside a 2"
    # protection sleeve. `host_ref=FT-GF-S-DR`: the garage moved 6'-0" east on 2026-09-07 and
    # the hydrant with it, so the crossing landed under the grade beam beneath D-G-SERVICE.
    # The door moved again on 2026-09-11 (into the SW corner) and the footing did NOT follow:
    # W-GF-S-DR is a full stem now, its nodes pinned at x 8'-3"..11'-9" as a fossil split
    # precisely so this host stays over the crossing, 9" inside its east end.
    # `integrity.sleeve_in_opening` catches a sleeve naming a host it no longer sits in.
    SleevePenetration(uid="CGPW01AAAA", tag="SP-GF-S-HYD", host_ref="FT-GF-S-DR",
                      position=pt(ft(11), ft(43, 6.875)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-8, -10)),
    # The service lateral's own, 4" east (2026-10-29): 1 1/4" PEX in a 3" sleeve, 1" inside
    # the pour's east end at FT-GF-S2, which `mep.footing_clearance` reads as one pour.
    SleevePenetration(uid="C4VDRMBJ5W", tag="SP-GF-S-SVC", host_ref="FT-GF-S-DR",
                      position=pt(ft(11, 4), ft(43, 6.875)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(3), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-8, -10)),
]
