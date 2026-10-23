# haus: editable
# Flat SPF 2x6, fitted to actual stud faces on the selected wall face.
# Bottom = finished floor above framing base + fixing AFF - 2.75 in.
# Main powder bar already lands on BK-M-HS1-MID / a stud; cabinet bars have internal pads.

from typehaus import WallBacking, inch

BASEMENT_TOWEL_BACKING = [
    # Bath floor +0.12 in.; gym floor +0.3125 in. above wall framing datum.
    WallBacking(
        uid="TWBBLOCK01",
        tag="BK-B-BATH-HAND-TOWEL",
        wall_ref="W-B-STR2",
        face="left",
        start=inch(14.125),
        length=inch(14.5),
        elevation=inch(45.37),
        height=inch(5.5),
        profile="2x6",
        material_ref="spf",
        purpose="FURN-B-BATH-HAND-TOWEL both posts",
    ),
    WallBacking(
        uid="TWBBLOCK02",
        tag="BK-B-SAUNA-BATH-TOWEL-N",
        wall_ref="W-B-CS",
        face="left",
        start=inch(8.75),
        length=inch(14.5),
        elevation=inch(51.5625),
        height=inch(5.5),
        profile="2x6",
        material_ref="spf",
        purpose="FURN-B-SAUNA-BATH-TOWEL north post, gym side",
    ),
    WallBacking(
        uid="TWBBLOCK03",
        tag="BK-B-SAUNA-BATH-TOWEL-S",
        wall_ref="W-B-CS",
        face="left",
        start=inch(40.75),
        length=inch(14.5625),
        elevation=inch(51.5625),
        height=inch(5.5),
        profile="2x6",
        material_ref="spf",
        purpose="FURN-B-SAUNA-BATH-TOWEL south post to door king",
    ),
]

MAIN_TOWEL_BACKING = [
    # Main full-bath floor +1.5 in. above framing.
    WallBacking(
        uid="TWMBLOCK01",
        tag="BK-M-BATH2-BATH-TOWEL",
        wall_ref="W-M-W3",
        face="left",
        start=inch(44.75),
        length=inch(14.5),
        elevation=inch(62.75),
        height=inch(5.5),
        profile="2x6",
        material_ref="spf",
        purpose="FURN-M-BATH2-BATH-TOWEL hook, south of window king",
    ),
    # Three bathroom-face bays support four posts; the middle block serves both bars.
    WallBacking(
        uid="QZP8HSX7B7", tag="BK-M-BATH2-TUB-TOWEL-N", wall_ref="W-M-BA2E", face="right",
        start=inch(8.75), length=inch(14.5), elevation=inch(52.75), height=inch(5.5),
        profile="2x6", material_ref="spf", purpose="FURN-M-BATH2-TUB-TOWEL-N north post",
    ),
    WallBacking(
        uid="EB35BZZ39C", tag="BK-M-BATH2-TUB-TOWEL-MID", wall_ref="W-M-BA2E", face="right",
        start=inch(24.75), length=inch(14.5), elevation=inch(52.75), height=inch(5.5),
        profile="2x6", material_ref="spf",
        purpose="FURN-M-BATH2-TUB-TOWEL-S north post; FURN-M-BATH2-TUB-TOWEL-N south post",
    ),
    WallBacking(
        uid="PP7AAAM7TJ", tag="BK-M-BATH2-TUB-TOWEL-S", wall_ref="W-M-BA2E2", face="right",
        start=inch(8.75), length=inch(14.5), elevation=inch(52.75), height=inch(5.5),
        profile="2x6", material_ref="spf", purpose="FURN-M-BATH2-TUB-TOWEL-S south post",
    ),
]

SECOND_TOWEL_BACKING = [
    # All second-floor bathroom finishes +1.5 in. above framing; keep the staggered row.
    WallBacking(
        uid="TWSBLOCK01",
        tag="BK-S-VANITY-HAND-TOWEL1",
        wall_ref="W-S-SN1",
        face="left",
        start=inch(16.75),
        length=inch(14.5),
        elevation=inch(46.75),
        height=inch(5.5),
        profile="2x6",
        material_ref="spf",
        purpose="FURN-S-VANITY-HAND-TOWEL1 both posts",
    ),
    WallBacking(
        uid="TWSBLOCK02",
        tag="BK-S-VANITY-HAND-TOWEL2",
        wall_ref="W-S-SN1",
        face="left",
        start=inch(48.75),
        length=inch(14.5),
        elevation=inch(46.75),
        height=inch(5.5),
        profile="2x6",
        material_ref="spf",
        purpose="FURN-S-VANITY-HAND-TOWEL2 east post; west post on stud",
    ),
    WallBacking(
        uid="TWSBLOCK03",
        tag="BK-S-BATH1-BATH-TOWEL",
        wall_ref="W-S-W1",
        face="left",
        start=inch(29.625),
        length=inch(14.5),
        elevation=inch(62.75),
        height=inch(5.5),
        profile="2x6",
        material_ref="spf",
        purpose="FURN-S-BATH1-BATH-TOWEL hook between linen and window",
    ),
    WallBacking(
        uid="TWSBLOCK04",
        tag="BK-S-SUITEBATH-BATH-TOWEL",
        wall_ref="W-S-DC2",
        face="right",
        start=inch(56.75),
        length=inch(15.365),
        elevation=inch(52.75),
        height=inch(5.5),
        profile="2x6",
        material_ref="spf",
        purpose="FURN-S-SUITEBATH-BATH-TOWEL north post; south on stud",
    ),
]

ATTIC_TOWEL_BACKING = [
    # Studio bath floor +0.87 in. above framing. Its 51 in. AFF bath bar reuses
    # BK-A-BATH-S (46..53.25 in. framing datum) at both mounting posts.
    WallBacking(
        uid="TWABLOCK01",
        tag="BK-A-STUBATH-HAND-TOWEL",
        wall_ref="W-A-HALL-S",
        face="right",
        start=inch(16.75),
        length=inch(14.5),
        elevation=inch(46.12),
        height=inch(5.5),
        profile="2x6",
        material_ref="spf",
        purpose="FURN-A-STUBATH-HAND-TOWEL both posts",
    ),
]
