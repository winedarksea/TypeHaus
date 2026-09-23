# haus: editable
# Catlin MEP — RM-S-PLANT's water: the interior watering stub, and the balcony hydrant's
# envelope sleeve. Split from plan/mep_supply.py (already past AGENTS.md's 500 lines);
# plan/mep.py files each list on its storey.

from typehaus import (
    PipeAccessory,
    PipeAccessoryKind,
    PipeRun,
    PipeSystem,
    Service,
    SleevePenetration,
    ft,
    inch,
    pt,
)

# --- the automatic-watering stub (2026-09-23) --------------------------------------------
# The owner wants the room hookable to automatic watering from INSIDE; FX-S-BALC-HYD's thread
# is outdoors and does not count. So a capped 1/2" PEX tee off PR-M-CW-BALC-HYD's riser, which
# already stands in W-S-S1's x 81 1/2"..94 3/4" bay: 3" east of the riser at 14" AFF,
# under BK-S-S1-HYD (21") and the hydrant seat (24"). Nothing crosses the floor, so no new
# penetration; the only hole is the recessed box, gasketed to the humid membrane like the
# room's electrical boxes (notes/plant_room.md). Filed on `main`: project elevations.
#
# ** WHERE THE WATER GOES: NO FLOOR DRAIN, AND THAT IS STILL THE ANSWER. ** Drip watering
# drains into the benches' own trays; nothing is washed down. A drain here means a trap in a
# room nobody uses in February and a DWV branch through FS-S-WEST's trusses from a storey
# down (notes/plant_room.md, item 2). The floor is vinyl sheet with a 6" integral flash cove,
# which holds a spill in the room. The residual — a failed-open line with nobody home — is
# answered at the box: the future controller is a valve that shuts on a floor leak sensor.
# Hard-piping irrigation off this stub makes it P2902.5.3's case: a PVB or RPZ is owed then.
PLANT_STUB_MAIN = [
    PipeRun(uid="9R0AYJMJZ4", tag="PR-M-CW-PLANT-STUB", system=PipeSystem.WATER_COLD,
            path=(pt(ft(7, 4), ft(0, 3.25)), pt(ft(7, 7), ft(0, 3.25))),
            diameter=inch(0.5), material="pex",
            elevations=(inch(134.829), inch(134.829)),
            wall_refs=("W-S-S1",)),
]

# Filed on `second`: an accessory reads its own storey's datum, so 14.829" is 14" AFF plus 0.829"
# of RM-S-PLANT's build-up over the deck.
PLANT_STUB_DEVICES_SECOND = [
    PipeAccessory(uid="KX282R48FS", tag="PA-S-PLANT-WATER-STUB", kind=PipeAccessoryKind.RO_STUB,
                  pipe_ref="PR-M-CW-PLANT-STUB", position=pt(ft(7, 7), ft(0, 3.25)),
                  elevation=inch(14.829), room="RM-S-PLANT", accessible=True,
                  model='1/2" quarter-turn stop, capped hose-thread outlet, in a recessed box gasketed to the humid membrane'),
]

# --- FX-S-BALC-HYD's sleeve (2026-09-23) ------------------------------------------------
# The barrel crosses W-S-S1 from its seat in the stud cavity to the escutcheon, and the bore
# (AO-S-BALC-HYD, blind 12" from outside) stops 1 1/4" short of the humid membrane, so the
# plant room's liner is NOT pierced. What the barrel does cross is the air/water/vapour
# plane — the 4" ccSPF on the sheathing — into a -15 F wall. This sleeve is that crossing:
# 2 1/2" PVC set in the sheathing at rough-in, pitched out, lining AO-S-BALC-HYD's hole,
# concentric with it and the barrel (144.829" = 24" AFF over the 0.829" build-up).
# `position` is the barrel's escutcheon vertex, so mep.sleeve_alignment reads it on the run.
HYDRANT_SLEEVE_SECOND = [
    SleevePenetration(uid="X4W3WBMX9T", tag="SP-S-BALC-HYD", host_ref="W-S-S1",
                      position=pt(ft(7, 4), inch(-5)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(2.5), serves_fixture="FX-S-BALC-HYD",
                      purpose=Service.WATER_COLD, axis="horizontal",
                      center_elevation=inch(144.829),
                      seal="flanged sleeve taped to the sheathing (butyl), ccSPF sprayed tight to it; escutcheon gasket at the cladding (PA-S-BALC-HYD-SEAL)",
                      insulation="closed-cell foam annulus over the barrel's half-inch elastomeric sleeve"),
]
