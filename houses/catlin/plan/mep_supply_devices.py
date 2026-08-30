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
    # P2903.9.1. The service (buried -8'-10", PR-G-HYDRANT-CW) tees off at (5', 35'-6") —
    # SP-B-N3-HYD, the north wall crossing — and rises to the basement ceiling; this valve
    # sits on that riser at 4'-0", head height, reachable with one hand, which is what
    # "accessible" means. It moved with the tee on 2026-08-30, when the water service entry
    # went from the rear of the lot to the front: the shutoff belongs where the water comes
    # in, and the water now comes in on the north.
    #
    # The garage hydrant is deliberately upstream, on the service itself: routing the yard
    # line up to an indoor valve and back down would put a high point above frost mid-run —
    # exactly the failure `mep.hydrant_freeze_depth` catches.
    PipeAccessory(uid="N5PK9WQ2TB", tag="PA-B-MAIN-SHUTOFF",
                  kind=PipeAccessoryKind.MAIN_SHUTOFF, pipe_ref="PR-B-CW-TRUNK",
                  position=pt(ft(5), ft(35, 6)), elevation=ft(4), accessible=True,
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
    # Held at the sink base's WEST face (2026-08-26) rather than sliding +9" with the rest
    # of the kitchen hot branch: the dishwasher moved to the sink base's west side in the
    # same re-composition, and +9" would have put this 41" east of it — across the whole
    # carcass — instead of at the point the branch actually reaches the machine.
    PipeAccessory(uid="W4NL8QSJ0M", tag="PA-M-DW-WHA-HW",
                  kind=PipeAccessoryKind.WATER_HAMMER_ARRESTOR, pipe_ref="PR-B-HW-KITCH",
                  position=pt(ft(27, 10), ft(33, 7.2)), room="RM-M-LIVING",
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

# --- Branch and fixture stops (2026-08-23) --------------------------------------------
#
# Until now the house had exactly ONE valve you could close: PA-B-MAIN-SHUTOFF, plus the
# hydrant isolation above. Change a lavatory tap and the whole dwelling goes dry, including
# the WCs. `mep.main_shutoff` never noticed because it only asks for the one; nothing in the
# engine grades a branch stop, so the deliverable here is not a green check but a model that
# stops implying the plumbing has stops it does not have.
#
# **Why these sit at the fixture end of each branch and not at the tee.** The natural place
# for a branch stop is where the branch leaves its trunk, and in this house every one of
# those tees is at the basement ceiling plane (~8'-1" on the cold trunk, ~8'-0" on the hot).
# That plane is 5/8" gypsum end to end — `ceiling_below` on FS-M-WEST and FS-M-EAST
# (params/main_deck.py) — so a valve at a tee is a valve behind a finished ceiling, which
# `PipeAccessory.accessible` would have to be False about. The four access panels this house
# owns (plan/placeables.py) serve a WC carrier, two tub wastes and the NW shaft; none is over
# a supply tee, and two more were deliberately declined there. **Authoring stops at the tees
# would mean inventing panels, so the stops go where the pipe already comes out into the
# room it serves** — at the riser head, under the lavatory, behind the WC, at the machine
# box. Every one is reachable standing or kneeling in a finished room with no panel and no
# ladder, which is what P2903.9.1 means by accessible and what makes a stop worth having.
#
# The consequence, stated rather than hidden: these isolate a FIXTURE GROUP at its point of
# use, not a whole branch at its origin. Working on the pipe *between* the tee and the room
# still means closing the main. Putting a real stop at each tee is an access-panel decision
# and it is on plans/TODO.md as one.
#
# No `elevation` on any of them: an accessory without one takes its host run's invert at the
# nearest vertex, and each position below IS that run's last vertex — the height the riser
# already arrives at (2'-6" to 3'-6" above the room's own floor). Authoring a number here
# would only be a second, drift-prone copy of one the run already carries.
SUPPLY_STOPS = [
    # RM-M-BATH1 — the wall-hung WC and its lavatory. Cold carries both, hot the lav alone.
    #
    # ** BOTH MOVED OUT OF W-M-BAE AND ONTO W-M-HS1 ON 2026-08-30, 8" APART. ** They had sat
    # 4.8" apart at (6'-0", 23'-7.2") and (6'-0", 24'-0"), which is inside D-M-BATH1's rough
    # opening — the risers under them were standing in the doorway, and the stops came along
    # for the ride. The argument for the new wall is on the BATH1 pair in plan/mep_supply.py
    # and is not repeated here; what matters at this end is that the two stops are still AT
    # THEIR OWN RISER HEADS, which is this file's rule, and that the heads are now on the
    # wall the lavatory backs onto rather than the one its door is in. Both land behind
    # FX-M-BATH1-LAV's carcass (x 41.5"..65.5"), reachable kneeling at the cabinet.
    PipeAccessory(uid="0RA7PE7K5N", tag="PA-M-BATH1-STOP-CW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-BATH1", position=pt(ft(5), ft(22, 4)),
                  accessible=True, room="RM-M-BATH1",
                  model='3/4" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV")),
    PipeAccessory(uid="1YCTZR50YR", tag="PA-M-BATH1-STOP-HW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-HW-BATH1", position=pt(ft(4, 4), ft(22, 4)),
                  accessible=True, room="RM-M-BATH1",
                  model='3/4" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-M-BATH1-LAV",)),
    # RM-M-BATH2 — WC, shower, tub and sink; the busiest group in the house and the one
    # most worth being able to isolate on its own.
    PipeAccessory(uid="3VR28WJF1E", tag="PA-M-BATH2-STOP-CW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-BATH2", position=pt(ft(2, 3), ft(17, 2.4)),
                  accessible=True, room="RM-M-BATH2",
                  model='3/4" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-M-BATH2-WC", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                          "FX-M-BATH2-SINK")),
    PipeAccessory(uid="4ZC2WZVFWB", tag="PA-M-BATH2-STOP-HW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-HW-BATH2", position=pt(ft(2, 3), ft(16, 9.6)),
                  accessible=True, room="RM-M-BATH2",
                  model='3/4" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-SINK")),
    # RM-S-BATH1 — the second floor's hall bath plus the two vanity lavatories it feeds.
    PipeAccessory(uid="B20MFS2ZH2", tag="PA-S-BATH1-STOP-CW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-SBATH", position=pt(ft(5, 7.2), ft(26, 6)),
                  accessible=True, room="RM-S-BATH1",
                  model='3/4" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                          "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    PipeAccessory(uid="P6WSEM39FM", tag="PA-S-BATH1-STOP-HW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-HW-SBATH", position=pt(ft(6, 4), ft(26, 6)),
                  accessible=True, room="RM-S-BATH1",
                  model='3/4" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                          "FX-S-VANITY-LAV2")),
    # RM-S-SUITEBATH.
    PipeAccessory(uid="SSSW9XQZZ4", tag="PA-S-SUITEBATH-STOP-CW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-SUITE", position=pt(ft(13, 7.2), ft(16, 10.8)),
                  accessible=True, room="RM-S-SUITEBATH",
                  model='3/4" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                          "FX-S-SUITEBATH-TUBSH")),
    PipeAccessory(uid="R24SV93Y39", tag="PA-S-SUITEBATH-STOP-HW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-HW-SUITE", position=pt(ft(14, 2.4), ft(16, 10.8)),
                  accessible=True, room="RM-S-SUITEBATH",
                  model='3/4" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-S-SUITEBATH-LAV", "FX-S-SUITEBATH-TUBSH")),
    # RM-B-BATH, the stair-foot bathroom. 1/2" branches, so 1/2" valves — the only pair
    # here that is not 3/4". Both arrive in W-B-BA-N's cavity at the same point.
    PipeAccessory(uid="F1M7RSZV67", tag="PA-B-BATH-STOP-CW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-BATH", position=pt(ft(16), ft(21, 9.375)),
                  accessible=True, room="RM-B-BATH",
                  model='1/2" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    PipeAccessory(uid="2DD9DEYNAS", tag="PA-B-BATH-STOP-HW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-HW-BATH", position=pt(ft(16), ft(21, 9.375)),
                  accessible=True, room="RM-B-BATH",
                  model='1/2" quarter-turn ball valve, chrome, at the riser head',
                  serves=("FX-B-BATH-LAV",)),
    # The kitchen. Its hot has its own branch; its COLD comes straight off the end of
    # PR-B-CW-TRUNK, so the cold stop sits on the trunk's own terminus at the sink base.
    # That is a stop for the kitchen, not a second main: PA-B-MAIN-SHUTOFF is upstream of
    # everything and this is the last 3'-6" of the run.
    PipeAccessory(uid="09MWB7MH7K", tag="PA-M-KITCH-STOP-CW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-TRUNK", position=pt(ft(29, 9.6), ft(34, 1.2)),
                  accessible=True, room="RM-M-LIVING",
                  model='1 1/4" quarter-turn ball valve, in the sink base cabinet',
                  serves=("FX-M-KITCH-SINK",)),
    PipeAccessory(uid="JPFD6JQM44", tag="PA-M-KITCH-STOP-HW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-HW-KITCH", position=pt(ft(30, 3.6), ft(33, 7.2)),
                  accessible=True, room="RM-M-LIVING",
                  model='3/4" quarter-turn ball valve, in the sink base cabinet',
                  serves=("FX-M-KITCH-SINK", "APPL-M-DW")),
    # The laundry. These land on the same two vertices as PA-M-WASH-WHA-CW/HW above — the
    # machine box is where the arrestors already are, and a washer box with stops in it is
    # the ordinary product.
    PipeAccessory(uid="VCF71D18GJ", tag="PA-M-WASH-STOP-CW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-WASH", position=pt(ft(8), ft(20, 7.2)),
                  accessible=True, room="RM-M-LAUNDRY",
                  model='3/4" quarter-turn ball valve, in the recessed washer box',
                  serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeAccessory(uid="D0DS71PB2J", tag="PA-M-WASH-STOP-HW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-HW-WASH", position=pt(ft(8), ft(21, 2.4)),
                  accessible=True, room="RM-M-LAUNDRY",
                  model='3/4" quarter-turn ball valve, in the recessed washer box',
                  serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    # The water heater's cold inlet — the one stop in this list that IS at its branch's own
    # end rather than at a fixture, and the one the house most obviously lacked. P2903.9.2
    # wants a valve on the cold supply to a water heater; without it, changing an anode rod
    # or a T&P valve means closing the main. It stands at the tank in the mechanical room at
    # the run's own 4'-0" invert, with nothing over it — the most accessible valve in the
    # house after the main itself.
    PipeAccessory(uid="XTPXNZ8PRZ", tag="PA-B-WH-STOP-CW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-WH", position=pt(ft(5, 6), ft(24)),
                  accessible=True, room="RM-B-FURNACE",
                  model='1" full-port bronze ball valve, lever handle, at the tank inlet',
                  serves=("EQ-B-WH",)),
]

# The garage yard hydrant's two devices, on the service run (filed on ``main``). The hydrant
# stands on the service ENTRY itself now (plan/site.py, 2026-08-30) — it is the first thing
# the lateral reaches, not the last. The seat takes the run's elevation, its own buried valve
# at -8'-10" (the 72" bury `mep.hydrant_freeze_depth` grades, measured from the -2'-10"
# grade); the vacuum breaker screws onto the outlet, 2'-6" above the garage slab, which puts
# it at 0'-0".
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
                  pipe_ref="PR-B-CW-TRUNK", position=pt(ft(29, 9.6), ft(34, 1.2)),
                  elevation=ft(2, 6), room="RM-M-LIVING", accessible=True,
                  model='1/4" compression stop on a capped tee, in the sink base'),
    # The cold-storage bay's twin of the row above, at the far end of
    # PR-M-CW-COLDSTORE-STUB (plan/mep_supply.py). Same reasoning, same nothing-drawn: the
    # chosen all-refrigerator has no ice maker, so this caps a line that serves nobody yet.
    # `accessible` is True on the reading that a stop behind a refrigerator is reached the
    # way every ice-maker stop in every house is — by rolling the appliance out — not by
    # opening a wall. No fixture, no fixture units, and no arrestor: an arrestor answers to
    # a quick-closing valve (P2903.5), and a cap is the opposite of one.
    PipeAccessory(uid="2KBAMK6NTE", tag="PA-M-COLDSTORE-STUB", kind=PipeAccessoryKind.RO_STUB,
                  pipe_ref="PR-M-CW-COLDSTORE-STUB", position=pt(ft(18, 9), ft(31)),
                  elevation=ft(2, 6), room="RM-M-LIVING", accessible=True,
                  model='1/4" compression stop on a capped tee, behind the cold-storage bay'),
]

# The balcony hydrant's two, on ``second``. No PA-S-BALC-HYD-VB, same reason as the porch's
# — see the note above SUPPLY_DEVICES_MAIN.
#
# ** BOTH MOVED 16'-8" -> 7'-4" ON 2026-08-30. ** Neither is an independent position: the
# seat is the inboard end of the barrel and the seal is its escutcheon, so both are the
# hydrant's own station. They had been left behind twice over — FX-S-BALC-HYD went west on
# 2026-08-24 when D-S-DECK-W's rough opening (x 12'-2"..17'-2") swallowed 16'-8", and the
# riser, the barrel and these two accessories all stayed put. `mep.run_through_opening`
# caught the pipe; nothing was ever going to catch the accessories but the pipe they name.
SUPPLY_DEVICES_SECOND = [
    PipeAccessory(uid="S6BN1JXV7Q", tag="PA-S-BALC-HYD-SEAT",
                  kind=PipeAccessoryKind.SHUTOFF, pipe_ref="PR-M-CW-BALC-HYD",
                  position=pt(ft(7, 4), ft(0, 3.25)), room="RM-S-PLANT",
                  model="hydrant's own compression seat, inboard end of the barrel",
                  serves=("FX-S-BALC-HYD",)),
    PipeAccessory(uid="M4TQ8HRC1Z", tag="PA-S-BALC-HYD-SEAL",
                  kind=PipeAccessoryKind.PENETRATION_SEAL, pipe_ref="PR-S-CW-BALC-HYD-CU",
                  position=pt(ft(7, 4), ft(0)),
                  model="gasketed escutcheon over a foamed barrel penetration",
                  install_parts=("silicone gasket, hydrant escutcheon",
                                 "plastic mounting bracket, non-conductive",
                                 'closed-cell spray foam, 1/4" annulus around the barrel'),
                  serves=("FX-S-BALC-HYD",)),
]


# --- the attic guest studio, 2026-08-29 -------------------------------------------------
# One accessible stop per riser at its head inside W-A-STU-W, following this file's own
# per-group pattern. `accessible=True` is the whole point of authoring them: an attic bath fed
# from a riser two storeys down has no other isolation short of the basement trunk, and the
# access is the wall cavity behind D-A-STUBATH's jamb.
# ** BOTH MOVED NORTH ON 2026-08-30 (19'-0"/19'-6" -> 20'-6"/21'-0") WITH THEIR RISERS. **
# FX-A-STUBATH-WC went back onto this wall and stands against y 18'-6"..20'-2"; a stop behind
# a toilet tank is not an accessible stop, and `accessible=True` is an authored claim that no
# check can contradict. See plan/mep_supply.py, which carries the same note on the runs.
# Filed on ``attic`` — an accessory takes ITS OWN storey's datum, not its pipe_ref's, so these
# read ft(2, 6) against the attic deck while the runs they sit on are filed on ``main``. Both
# stops stand in RM-A-STUBATH at 2'-6" AFF, which is the project 22'-6" the risers arrive at.
STUDIO_SUPPLY_DEVICES = [
    PipeAccessory(uid="5KSHNN2HVJ", tag="PA-A-STUBATH-STOP-CW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-A-CW-STUBATH", position=pt(ft(9, 7.5), ft(20, 6)),
                  elevation=ft(2, 6), accessible=True, room="RM-A-STUBATH",
                  model='3/4" quarter-turn ball valve',
                  serves=("FX-A-STUBATH-WC", "FX-A-STUBATH-LAV", "FX-A-STUBATH-SH",
                          "FX-A-STUDIO-BAR-SINK")),
    PipeAccessory(uid="MA4EXBFW5G", tag="PA-A-STUBATH-STOP-HW", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-A-HW-STUBATH", position=pt(ft(9, 7.5), ft(21)),
                  elevation=ft(2, 6), accessible=True, room="RM-A-STUBATH",
                  model='3/4" quarter-turn ball valve',
                  serves=("FX-A-STUBATH-LAV", "FX-A-STUBATH-SH", "FX-A-STUDIO-BAR-SINK")),
]
