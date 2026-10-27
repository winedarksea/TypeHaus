# haus: editable
# Flat SPF 2x6, cut to clear stud faces; the mounting post may also land on a stud itself.
# Band bottoms = finished floor above framing base + 26 in. - half the 5.5 in. block.

from typehaus import WallBacking, inch


BASEMENT_TP_BACKING = [
    # Floor is 0.12 in. above frame; studs y=264/280. The south post lands on the 264 stud.
    WallBacking(uid="TPBBLOCK01", tag="BK-B-BATH-TP", wall_ref="W-B-STR3B", face="left",
                start=inch(26.75), length=inch(14.5), elevation=inch(23.37),
                height=inch(5.5), profile="2x6", material_ref="spf",
                purpose="FURN-B-BATH-TP north mounting post; south post fixes to stud"),
]

MAIN_TP_BACKING = [
    # BATH1 floor build-up is 0.94685 in.; the north post lands on the y=304 stud.
    WallBacking(uid="TPMBLOCK01", tag="BK-M-BATH1-TP", wall_ref="W-M-W2", face="left",
                start=inch(16.25), length=inch(14.5), elevation=inch(24.2362),
                height=inch(5.5), profile="2x6", material_ref="spf",
                purpose="FURN-M-BATH1-TP south mounting post; north post fixes to stud"),
    # BATH2 floor is 1.5 in.; window king/jack divide the two fixing bays, below the sill.
    WallBacking(uid="TPMBLOCK02", tag="BK-M-BATH2-TP-S", wall_ref="W-M-W3", face="left",
                start=inch(44.5), length=inch(14.75), elevation=inch(24.75),
                height=inch(5.5), profile="2x6", material_ref="spf",
                purpose="FURN-M-BATH2-TP south mounting post, stud to window king"),
    WallBacking(uid="TPMBLOCK03", tag="BK-M-BATH2-TP-N", wall_ref="W-M-W3", face="left",
                start=inch(31.25), length=inch(10.25), elevation=inch(24.75),
                height=inch(5.5), profile="2x6", material_ref="spf",
                purpose="FURN-M-BATH2-TP north mounting post, window jack to sill cripple"),
]

SECOND_TP_BACKING = [
    WallBacking(uid="TPSBLOCK01", tag="BK-S-BATH1-TP", wall_ref="W-S-CH-S", face="left",
                start=inch(1.25), length=inch(14), elevation=inch(24.75),
                height=inch(5.5), profile="2x6", material_ref="spf",
                purpose="FURN-S-BATH1-TP both posts below raised shaft access panel"),
]
