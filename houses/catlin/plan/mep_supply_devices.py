# haus: editable
# Catlin MEP — in-line supply devices — valves, stops and arrestors on the supply runs.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1) verbatim; plan/mep.py
# re-exports the storey lists so the manifest is unchanged. Each device names the run it
# sits on; the runs themselves are in plan/mep_supply.py.

from typehaus import (
    PipeAccessory,
    PipeAccessoryKind,
    ft,
    pt,
)

# --- In-line supply devices (2026-08-01) ---------------------------------------------
#
# These fifteen `PipeAccessory` elements replace what used to be prose scattered across
# notes/garage_hydrant.md, mep.hydrant_freeze_depth (an UNKNOWN) and plans/TODO.md.
#
# An accessory with no `elevation` takes its host run's invert at the nearest vertex (a
# valve sitting on its pipe). Only devices off that line — a stub, a breaker at handle
# height — author one.
SUPPLY_DEVICES_BASEMENT = [
    # P2903.9.1. The service (buried -8'-6", PR-G-HYDRANT-CW) tees off at (5', 1') and rises
    # to the basement ceiling; this valve sits on that riser at 4'-0" — head height,
    # reachable with one hand, which is what "accessible" means.
    #
    # The garage hydrant is deliberately upstream, on the service itself: routing the yard
    # line up to an indoor valve and back down would put a high point above frost mid-run —
    # exactly the failure `mep.hydrant_freeze_depth` catches.
    PipeAccessory(uid="N5PK9WQ2TB", tag="PA-B-MAIN-SHUTOFF",
                  kind=PipeAccessoryKind.MAIN_SHUTOFF, pipe_ref="PR-B-CW-TRUNK",
                  position=pt(ft(5), ft(1)), elevation=ft(4), accessible=True,
                  room="RM-B-FURNACE",
                  model='1 1/4" full-port bronze ball valve, lever handle',
                  serves=("PR-B-CW-TRUNK",)),
    # P2902, the owner's request (plans/TODO.md §Plumbing). Two rather than one: the two
    # basement groups tee off different trunks in different rooms, so no single point is
    # upstream of both.
    PipeAccessory(uid="H2VD7MCX4L", tag="PA-B-BFP-BATH",
                  kind=PipeAccessoryKind.BACKFLOW_PREVENTER, pipe_ref="PR-B-CW-BATH",
                  position=pt(ft(7), ft(26)), room="RM-B-FURNACE", accessible=True,
                  model='1/2" dual-check backflow preventer, testable',
                  serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    PipeAccessory(uid="Q8RJ1ZFN6V", tag="PA-B-BFP-SAUNA",
                  kind=PipeAccessoryKind.BACKFLOW_PREVENTER, pipe_ref="PR-B-CW-SAUNA",
                  position=pt(ft(17, 4), ft(16)), room="RM-B-SAUNA", accessible=True,
                  model='1/2" dual-check backflow preventer, testable',
                  serves=("FX-B-SAUNA-SH",)),
    # P2903.5. The washer slams two solenoids shut, so it needs an arrestor on each supply —
    # cold alone would leave the hot line to hammer. Both sit at the machine's own riser,
    # within the manufacturer's 6' of the quick-closing valve.
    PipeAccessory(uid="F3ZC6TWL9N", tag="PA-M-WASH-WHA-CW",
                  kind=PipeAccessoryKind.WATER_HAMMER_ARRESTOR, pipe_ref="PR-B-CW-WASH",
                  position=pt(ft(8), ft(20, 7.2)), room="RM-M-LAUNDRY",
                  model="Sioux Chief MiniRester 660-G class, size A",
                  serves=("FX-M-LAUNDRY",)),
    PipeAccessory(uid="K7XB2VDR5H", tag="PA-M-WASH-WHA-HW",
                  kind=PipeAccessoryKind.WATER_HAMMER_ARRESTOR, pipe_ref="PR-B-HW-WASH",
                  position=pt(ft(8), ft(21, 2.4)), room="RM-M-LAUNDRY",
                  model="Sioux Chief MiniRester 660-G class, size A",
                  serves=("FX-M-LAUNDRY",)),
    # The dishwasher's fill solenoid is the other quick-closing valve in the house. It takes
    # hot water only, so it takes one arrestor, on the kitchen hot branch at the sink base.
    PipeAccessory(uid="W4NL8QSJ0M", tag="PA-M-DW-WHA-HW",
                  kind=PipeAccessoryKind.WATER_HAMMER_ARRESTOR, pipe_ref="PR-B-HW-KITCH",
                  position=pt(ft(29, 6.6), ft(33, 7.2)), room="RM-M-LIVING",
                  model="Sioux Chief MiniRester 660-G class, size A",
                  serves=("APPL-M-DW",)),
    # Branch isolation for both wall hydrants, at the tee off the cold trunk. Not a code
    # item — the hydrants' own seats are their shutoffs — but a hose bib is the thing most
    # likely to need a fast shutoff, and this is the last point one valve reaches both.
    PipeAccessory(uid="Y6MT3HKB1F", tag="PA-B-HYD-ISO", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-HYD", position=pt(ft(6), ft(16)), accessible=True,
                  room="RM-B-GYM", model='3/4" quarter-turn ball valve',
                  serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
]

# The garage yard hydrant's two devices, on the service run (filed on ``main``). The seat
# takes the run's elevation, its own buried valve at -8'-6" (the 72" bury
# `mep.hydrant_freeze_depth` grades, measured from the -2'-6" grade); the vacuum breaker
# screws onto the outlet, 2'-6" above the garage slab, which puts it at 0'-0".
SUPPLY_DEVICES_GARAGE = [
    PipeAccessory(uid="C9GW5PXV2R", tag="PA-G-HYD-SEAT", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-G-HYDRANT-CW", position=pt(ft(5), ft(59, 6)),
                  room="RM-GARAGE", model="hydrant's own compression seat, 6' bury",
                  serves=("FX-G-HYDRANT",)),
    PipeAccessory(uid="J1DS4RQZ8X", tag="PA-G-HYD-VB",
                  kind=PipeAccessoryKind.VACUUM_BREAKER, pipe_ref="PR-G-HYDRANT-CW",
                  position=pt(ft(5), ft(59, 6)), elevation=ft(0), room="RM-GARAGE",
                  model="screw-on hose-bib vacuum breaker, ASSE 1011",
                  serves=("FX-G-HYDRANT",)),
    # The weep, answered (2026-08-15). PA-G-HYD-VB above protects the hose thread (the only
    # opening P2902.3.1 names); a self-draining yard hydrant has a second opening, the weep
    # at the buried shutoff, which empties into DRW-G-HYDRANT's stone at -6'-0". On a Y34 the
    # drain port is open only while seated and closed while open, so weep and supply are
    # never both connected — the hazard needs a worn seat, a submerged weep, and negative
    # pressure simultaneously, which is why the code allows it and the house keeps it
    # (→ notes/garage_hydrant.md).
    #
    # Placed on the branch, not the fixture, because that's where it's reachable: the run is
    # exposed across the heated basement, 3'-0" over the basement floor — head height, beside
    # PA-B-MAIN-SHUTOFF. No elevation authored; a check valve on a pipe sits on the pipe.
    #
    # Dual check, matching PA-B-BFP-BATH/SAUNA, since this is low-hazard (car-wash) use. An
    # AHJ treating the weep as a health hazard would want an RPZ instead — ask, don't build
    # ahead of the answer.
    PipeAccessory(uid="R7QB4XKD2M", tag="PA-G-HYD-BFP",
                  kind=PipeAccessoryKind.BACKFLOW_PREVENTER, pipe_ref="PR-G-HYDRANT-CW",
                  position=pt(ft(5), ft(3)), room="RM-B-FURNACE", accessible=True,
                  model='3/4" dual-check backflow preventer, testable',
                  serves=("FX-G-HYDRANT",)),
]

# The porch hydrant's two, and the RO provision. All on ``main``.
#
# No PA-M-PORCH-HYD-VB: FX-HYDRANT-SD34 (a Woodford Model 19) ships its anti-siphon vacuum
# breaker integral to the faucet body — `mep.backflow_prevention` reads that off the
# fixture type's `integral_vacuum_breaker` flag (library/placeables/fixtures.py). Authoring
# a second, screw-on vacuum breaker as an accessory here would double-bill a part the
# hydrant's own price already includes; contrast the garage yard hydrant (FX-HYDRANT-Y34SS,
# bare thread), whose PA-G-HYD-VB is a real, separately-bought device.
SUPPLY_DEVICES_MAIN = [
    PipeAccessory(uid="A5VK7BND3T", tag="PA-M-PORCH-HYD-SEAT",
                  kind=PipeAccessoryKind.SHUTOFF, pipe_ref="PR-M-CW-PORCH-HYD",
                  position=pt(ft(12), ft(0, 3.25)), room="RM-M-BED",
                  model="hydrant's own compression seat, inboard end of the barrel",
                  serves=("FX-M-PORCH-HYD",)),
    # The penetration itself: says "protected by the envelope, not bury depth", which
    # exempts it from `mep.hydrant_freeze_depth` and hands it to
    # `mep.exterior_hydrant_protection`. `install_parts` are the three loose items nobody
    # stocks as a hydrant — properties of this hole in this wall.
    PipeAccessory(uid="U3FP6ZMG8B", tag="PA-M-PORCH-HYD-SEAL",
                  kind=PipeAccessoryKind.PENETRATION_SEAL, pipe_ref="PR-M-CW-PORCH-HYD-CU",
                  position=pt(ft(12), ft(0)),
                  model="gasketed escutcheon over a foamed barrel penetration",
                  install_parts=("silicone gasket, hydrant escutcheon",
                                 "plastic mounting bracket, non-conductive",
                                 'closed-cell spray foam, 1/4" annulus around the barrel'),
                  serves=("FX-M-PORCH-HYD",)),
    # P2903 has nothing to say about this one: a capped 1/4" tee off the kitchen cold riser,
    # left for a reverse-osmosis unit nobody has bought yet. No fixture/fixture units since
    # a capped stub draws no water; it just saves opening the wall the day one arrives.
    PipeAccessory(uid="L8CY2WRT4K", tag="PA-M-RO-STUB", kind=PipeAccessoryKind.RO_STUB,
                  pipe_ref="PR-B-CW-TRUNK", position=pt(ft(29, 0.6), ft(34, 1.2)),
                  elevation=ft(2, 6), room="RM-M-LIVING", accessible=True,
                  model='1/4" compression stop on a capped tee, in the sink base'),
]

# The balcony hydrant's two, on ``second``. No PA-S-BALC-HYD-VB, same reason as the porch's
# — see the note above SUPPLY_DEVICES_MAIN.
SUPPLY_DEVICES_SECOND = [
    PipeAccessory(uid="S6BN1JXV7Q", tag="PA-S-BALC-HYD-SEAT",
                  kind=PipeAccessoryKind.SHUTOFF, pipe_ref="PR-M-CW-BALC-HYD",
                  position=pt(ft(16, 8), ft(0, 3.25)), room="RM-S-PLANT",
                  model="hydrant's own compression seat, inboard end of the barrel",
                  serves=("FX-S-BALC-HYD",)),
    PipeAccessory(uid="M4TQ8HRC1Z", tag="PA-S-BALC-HYD-SEAL",
                  kind=PipeAccessoryKind.PENETRATION_SEAL, pipe_ref="PR-S-CW-BALC-HYD-CU",
                  position=pt(ft(16, 8), ft(0)),
                  model="gasketed escutcheon over a foamed barrel penetration",
                  install_parts=("silicone gasket, hydrant escutcheon",
                                 "plastic mounting bracket, non-conductive",
                                 'closed-cell spray foam, 1/4" annulus around the barrel'),
                  serves=("FX-S-BALC-HYD",)),
]
