# haus: editable
from typehaus import ClearZone, Slice, SliceKind, inch, pt

# A thin paper target sits 1/16" proud of the south concrete face. The north limit
# is the inverter's actual front: 403 9/16" = 10.2504875 m of usable dry-fire length.
# Keep the inverter's working space free of fixed furniture. D-B-FURN is held open
# while the lane is used; only that named door is excepted. All MEP clears 80" AFF.
DRY_FIRE_LANE = [
    ClearZone(uid="EN85FVSX1Q", tag="CZ-B-DRYFIRE",
              outline=(pt(inch(40.5), inch(8.0625)), pt(inch(68), inch(8.0625)),
                       pt(inch(68), inch(411.625)), pt(inch(40.5), inch(411.625))),
              bottom=inch(0), top=inch(80),
              purpose="10.25 m dry-fire lane through D-B-FURN; hold the door open during use",
              # recommended until the basement ERV is re-laid (plans/dry-fire-lane.md Phase 4)
              policy="recommended", except_tags=("D-B-FURN",)),
    Slice(uid="18XSSZCHEA", tag="SL-S-DRYFIRE", kind=SliceKind.SECTION,
          title="Dry-fire lane — 10.25 m usable",
          cut_origin=pt(inch(54), inch(0)), cut_direction="y",
          crop=(pt(inch(0), inch(-112)), pt(inch(420), inch(-10)))),
]
