# haus: editable
# Catlin MEP — in-line supply devices — valves, stops and arrestors on the supply runs.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# Each device names the run it sits on; the runs themselves are in plan/mep_supply.py.

from typehaus import (
    PipeAccessory,
    PipeAccessoryKind,
    ft,
    inch,
    pt,
)

# --- In-line supply devices (2026-08-01) ---------------------------------------------
#
# Everything below used to be prose. `notes/garage_hydrant.md` recorded the hydrant's
# shutoff and vacuum breaker in a sentence, `mep.hydrant_freeze_depth` emitted an UNKNOWN
# saying the model had no element for either, and the backflow preventer, the arrestors,
# the main shutoff and the RO provision lived only in `plans/TODO.md`. `PipeAccessory` is
# the element that makes them real; these are the fifteen the house actually has.
#
# An accessory with no `elevation` takes its host run's invert at the nearest vertex, which
# is what a valve on a pipe is at. Only the ones that sit somewhere other than on the pipe's
# own line — a stub rising to a cabinet, a breaker at a handle height — author one.
SUPPLY_DEVICES_BASEMENT = [
    # P2903.9.1. The service enters buried at -6'-0" and stays there all the way to the
    # garage (PR-G-HYDRANT-CW *is* the service); the house tees off it at (5', 1') and rises
    # to the basement ceiling, and this valve is on that riser at 4'-0" above the basement
    # floor — head height in the mechanical room, reachable with one hand and no ladder,
    # which is what "accessible" means and is not true of anything buried.
    #
    # The garage hydrant is upstream of it, on the service itself. That is deliberate rather
    # than an oversight: the hydrant's own seat is 6' down and is its shutoff, and bringing
    # the yard line up to a valve inside the house and back down would put a high point
    # above frost in the middle of it — the exact failure `mep.hydrant_freeze_depth` exists
    # to catch.
    PipeAccessory(uid="N5PK9WQ2TB", tag="PA-B-MAIN-SHUTOFF",
                  kind=PipeAccessoryKind.MAIN_SHUTOFF, pipe_ref="PR-B-CW-TRUNK",
                  position=pt(ft(5), ft(1)), elevation=ft(4), accessible=True,
                  room="RM-B-FURNACE",
                  model='1 1/4" full-port bronze ball valve, lever handle',
                  serves=("PR-B-CW-TRUNK",)),
    # P2902, the owner's request (plans/TODO.md §Plumbing): backflow protection on the
    # basement fixture connections. Two rather than one, because the two basement groups tee
    # off different trunks in different rooms and no single point is upstream of both. These
    # fixtures sit 9' below grade with the building drain leaving under the slab, which is
    # the condition that makes a siphon back into the supply worth a device rather than
    # trusting each fixture's own air gap.
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
    # P2903.5. The washer slams two solenoids shut, so it takes two arrestors — one on each
    # supply. An arrestor on the cold alone leaves the hot line to hammer, which is the
    # failure this pair exists to prevent and the reason the check grades per system rather
    # than per appliance. Both sit at the machine's own riser, within the 6' of the quick-
    # closing valve the manufacturers specify.
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
    # The branch isolation for both wall hydrants, at the tee where their shared riser
    # leaves the cold trunk. Not a code item — the hydrants' own seats are their shutoffs
    # and neither is winterised — but a hose bib is the thing most likely to need a valve
    # turned off in a hurry, and this is the last point where one valve reaches both.
    PipeAccessory(uid="Y6MT3HKB1F", tag="PA-B-HYD-ISO", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-HYD", position=pt(ft(6), ft(16)), accessible=True,
                  room="RM-B-GYM", model='3/4" quarter-turn ball valve',
                  serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
]

# The garage yard hydrant's two devices, on the service run they belong to (which is filed
# on ``main``, → WATER_SUPPLY above). The seat is the hydrant's own buried valve at -6'-0" —
# it takes the run's elevation, which is exactly the 72" bury `mep.hydrant_freeze_depth`
# grades — and the vacuum breaker screws onto the outlet at the handle, 2'-6" up.
SUPPLY_DEVICES_GARAGE = [
    PipeAccessory(uid="C9GW5PXV2R", tag="PA-G-HYD-SEAT", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-G-HYDRANT-CW", position=pt(ft(5), ft(59, 6)),
                  room="RM-GARAGE", model="hydrant's own compression seat, 6' bury",
                  serves=("FX-G-HYDRANT",)),
    PipeAccessory(uid="J1DS4RQZ8X", tag="PA-G-HYD-VB",
                  kind=PipeAccessoryKind.VACUUM_BREAKER, pipe_ref="PR-G-HYDRANT-CW",
                  position=pt(ft(5), ft(59, 6)), elevation=ft(2, 6), room="RM-GARAGE",
                  model="screw-on hose-bib vacuum breaker, ASSE 1011",
                  serves=("FX-G-HYDRANT",)),
    # The weep, answered (2026-08-15). PA-G-HYD-VB above protects the *hose thread*, which
    # is what P2902.3.1 asks about and the only opening the code names. A self-draining yard
    # hydrant has a second one: the weep at the buried shutoff, which empties the barrel into
    # DRW-G-HYDRANT's stone every time the handle closes and sits in wet stone at -6'-0".
    #
    # On a Y34 the drain port is open only while the valve is seated and closed while the
    # valve is open, so the weep and the supply are never both connected in normal operation.
    # The hazard needs a worn seat *and* a submerged weep *and* negative pressure at once,
    # which is why nothing in the IRC or the MN plumbing code prohibits this fixture and why
    # the house keeps it — → notes/garage_hydrant.md for the reasoning and the owner's call.
    #
    # This is the cheap insurance against that three-way coincidence, and it is on the branch
    # rather than at the fixture because the branch is where a device can be reached: the
    # hydrant's own seat is 6' down in the yard and the tee to the house is at (5', 1'). The
    # run is exposed across the heated basement between its three wall sleeves at the -6'
    # bury, which is 3'-0" over the basement floor — head height in the mechanical room,
    # beside PA-B-MAIN-SHUTOFF, with no elevation authored because a check valve on a pipe
    # sits on the pipe.
    #
    # A dual check, matching PA-B-BFP-BATH/SAUNA, because this is a low-hazard residential
    # connection — a car gets washed with it. An AHJ that reads a buried weep as a *health*
    # hazard would want an RPZ instead, which needs a drain and an annual test; that is a
    # question to ask, not a thing to build in ahead of the answer.
    PipeAccessory(uid="R7QB4XKD2M", tag="PA-G-HYD-BFP",
                  kind=PipeAccessoryKind.BACKFLOW_PREVENTER, pipe_ref="PR-G-HYDRANT-CW",
                  position=pt(ft(5), ft(3)), room="RM-B-FURNACE", accessible=True,
                  model='3/4" dual-check backflow preventer, testable',
                  serves=("FX-G-HYDRANT",)),
]

# The porch hydrant's three, and the RO provision. All on ``main``.
SUPPLY_DEVICES_MAIN = [
    PipeAccessory(uid="A5VK7BND3T", tag="PA-M-PORCH-HYD-SEAT",
                  kind=PipeAccessoryKind.SHUTOFF, pipe_ref="PR-M-CW-PORCH-HYD",
                  position=pt(ft(12), ft(0, 3.25)), room="RM-M-BED",
                  model="hydrant's own compression seat, inboard end of the barrel",
                  serves=("FX-M-PORCH-HYD",)),
    PipeAccessory(uid="E2QH9LCW6Y", tag="PA-M-PORCH-HYD-VB",
                  kind=PipeAccessoryKind.VACUUM_BREAKER, pipe_ref="PR-M-CW-PORCH-HYD-CU",
                  position=pt(ft(12), inch(-5)),
                  model="integral anti-siphon vacuum breaker, ASSE 1052",
                  serves=("FX-M-PORCH-HYD",)),
    # The penetration itself. This is the element that says "this hydrant is protected by
    # the envelope rather than by bury depth", which is what exempts it from
    # `mep.hydrant_freeze_depth` and hands it to `mep.exterior_hydrant_protection`. Its
    # `install_parts` are the three loose items the TODO asked for by name: nobody stocks
    # them as a hydrant, and they are properties of this hole in this wall.
    PipeAccessory(uid="U3FP6ZMG8B", tag="PA-M-PORCH-HYD-SEAL",
                  kind=PipeAccessoryKind.PENETRATION_SEAL, pipe_ref="PR-M-CW-PORCH-HYD-CU",
                  position=pt(ft(12), ft(0)),
                  model="gasketed escutcheon over a foamed barrel penetration",
                  install_parts=("silicone gasket, hydrant escutcheon",
                                 "plastic mounting bracket, non-conductive",
                                 'closed-cell spray foam, 1/4" annulus around the barrel'),
                  serves=("FX-M-PORCH-HYD",)),
    # P2903 has nothing to say about this one: it is a capped 1/4" tee off the kitchen cold
    # riser, left for a reverse-osmosis unit nobody has bought yet. No fixture and no
    # fixture units, because a capped stub draws no water — what it buys is that the wall
    # does not have to be opened the day one is.
    PipeAccessory(uid="L8CY2WRT4K", tag="PA-M-RO-STUB", kind=PipeAccessoryKind.RO_STUB,
                  pipe_ref="PR-B-CW-TRUNK", position=pt(ft(29, 0.6), ft(34, 1.2)),
                  elevation=ft(2, 6), room="RM-M-LIVING", accessible=True,
                  model='1/4" compression stop on a capped tee, in the sink base'),
]

# The balcony hydrant's three, on ``second``.
SUPPLY_DEVICES_SECOND = [
    PipeAccessory(uid="S6BN1JXV7Q", tag="PA-S-BALC-HYD-SEAT",
                  kind=PipeAccessoryKind.SHUTOFF, pipe_ref="PR-M-CW-BALC-HYD",
                  position=pt(ft(16, 8), ft(0, 3.25)), room="RM-S-PLANT",
                  model="hydrant's own compression seat, inboard end of the barrel",
                  serves=("FX-S-BALC-HYD",)),
    PipeAccessory(uid="P0GZ5DKF9W", tag="PA-S-BALC-HYD-VB",
                  kind=PipeAccessoryKind.VACUUM_BREAKER, pipe_ref="PR-S-CW-BALC-HYD-CU",
                  position=pt(ft(16, 8), inch(-5)),
                  model="integral anti-siphon vacuum breaker, ASSE 1052",
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
