# haus: editable
# IRC R602.6.1 top-plate ties — a cut past half a plate's width is permitted WITH a
# galvanized 16 ga x 1 1/2" strap lapping 6" past the cut each way, 8 10d nails a side.
#
# `# haus: editable` is here for `haus fmt` to mint the uids; nothing in the UI moves a tie.
# Each tie `covers` its one run, so a later cut in the same plate is graded, not excused.
# Owner call, 2026-09-23: tie both plates rather than re-route.

from typehaus import PlateTie


# PR-A-STUBATH-DRAIN takes 3.50" of W-S-DC2's 5.50" 2x6 top plate.
SECOND_PLATE_TIES = [
    PlateTie(uid="GDQ6HTC2BX", tag="PTIE-W-S-DC2", wall="W-S-DC2",
             covers=("PR-A-STUBATH-DRAIN",),
             product="Simpson PSPN58"),
]

# DU-M-ERV-R-LAUNDRY takes 4.00" of W-M-CLN2's 5.50" 2x6 top plate.
MAIN_PLATE_TIES = [
    PlateTie(uid="GFR1FS0F4W", tag="PTIE-W-M-CLN2", wall="W-M-CLN2",
             covers=("DU-M-ERV-R-LAUNDRY",),
             product="Simpson PSPN58"),
]
