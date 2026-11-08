# haus: editable
# RM-S-PLANT's drip reservoir (owner, 2026-11-07: the reservoir, not a sink). Replaces the
# capped stub as the room's water. Design, UPC 603.3.1 / 603.5.5 reading and the spill
# arithmetic: notes/plant_reservoir.md. Type and parts: plan/plant_reservoir_types.py.
#
# ** NO DRAIN, AND THE ROOM HOLDS A WHOLE TANK. ** 10 gal is 0.12" over the 137.8 sf of vinyl;
# the water stop at D-S-PLANT (plan/doorway_transitions.py, 0.38") holds ~32 gal and 1/4" is
# ~21 gal. The fill is a float valve whose spout stands 2" over the rim (an air gap, UPC
# 603.3.1); the pump is a 12 V diaphragm unit beside the tank, drawing from it.
#
# Placed 1/2" off W-S-S1's finished face (y 7.79"), x 166" so it stands in the bay east of the
# hydrant's (x 145"-158") and 10" short of ED-S-PLANT-RC6; rotation 180 puts the float valve on
# the wall side, west rim, 11" from PA-S-PLANT-RESERVOIR-STOP. Clear of D-S-PLANT's swing
# (x >= 186" at y 17"-47") and under WIN-S-PLANT4's 32" sill.

from typehaus import Appliance, deg, inch, pt

PLANT_RESERVOIR_PLACED = [
    Appliance(uid="YRDYECWWYV", tag="APPL-S-PLANT-RESERVOIR", type_ref="APPL-PLANT-RESERVOIR",
              room="RM-S-PLANT",
              position=pt(inch(166), inch(16.1)), rotation=deg(180),
              install_parts=("Dial 4154 1/4-inch brass float valve, spout 2 inches over the rim",
                             "Dial 94045 1/4-inch needle valve, set to about 0.1 gpm",
                             "SEAFLO SFDP1-012-035-21 12 V diaphragm pump, 1.2 GPM, 35 psi",
                             "12 V DC 5 A UL-listed plug-in supply for the pump",
                             "BrassCraft G2PS04X-C1 1/2-inch push x 1/4-inch compression stop",
                             "1/4-inch polyethylene line, 4 ft, stop to float valve",
                             "Rain Bird DRIPKITBAG drip tubing and drippers, with 25 psi regulator",
                             "Woods 50015WD 7-day outdoor plug-in timer")),
]
