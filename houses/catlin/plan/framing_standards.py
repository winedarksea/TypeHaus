# haus: editable
# Wall headers (decision #116): R602.7 sizes every bearing header from its derived load
# (resolve/header_loads.py); the house never frames one smaller than 2-2x8. Nonbearing heads
# up to 8' are the R602.7.4 flat 2x at the wall's depth.
# Sheathing (decision #146): CDX laid vertically from the corner its sheathing runs through;
# a joint needs 7/16" of member face under each edge = APA E30's 3/8" nail edge distance +
# half an 8d common's 0.131" shank, so the shank lands inside the face (notes/
# sheet_layout_oracle.md). 12" is the narrowest rip the crew hangs (house preference).

from typehaus import HeaderStandard, SheetLayoutStandard, inch

HEADER_STANDARD = [
    HeaderStandard(uid="FPEZ7QS5W4", tag="HEADER-STANDARD", min_bearing_header="2-2x8"),
    SheetLayoutStandard(uid="D0FSC9880R", tag="SHEET-LAYOUT-STANDARD", orientation="vertical",
                        min_rip_width=inch(12), min_edge_bearing=inch(0.4375),
                        stagger_min=inch(16), kerf=inch(0.125), start_at_through_end=True,
                        max_course_shortfall=inch(0.75),
                        source="APA E30 (3/8 in. nail edge distance) + 1/2 of an 8d common shank"),
]
