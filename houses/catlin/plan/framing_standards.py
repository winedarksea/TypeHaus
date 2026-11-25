# haus: editable
# Wall headers (decision #116): R602.7 sizes every bearing header from its derived load
# (resolve/header_loads.py); the house never frames one smaller than 2-2x8. Nonbearing heads
# up to 8' are the R602.7.4 flat 2x at the wall's depth.
# Sheathing (decision #146): CDX laid vertically from the corner its sheathing runs through;
# a joint needs 7/16" of member face under each edge = APA E30's 3/8" nail edge distance +
# half an 8d common's 0.131" shank, so the shank lands inside the face (notes/
# sheet_layout_oracle.md). 12" is the narrowest rip the crew hangs (house preference).

from typehaus import HeaderStandard, SheathingNailing, SheetLayoutStandard, inch

# Wall sheathing nailing (decision #147): bright 8d common at 6"/12" on dry SPF, the
# 1/2" CDX at 16" and the 7/16" ZIP at 24" alike; every edge on studs, plates or rim
# (bracing panels). Code-standard: one S-001 note line.
WALL_SHEATHING_NAILING = SheathingNailing(
    part="8d common 0.131x2.5 bright", edge_oc_in=6.0, field_oc_in=12.0, blocked=True,
    code_row="IRC 2018 Table R602.3(3)",
    source="IRC 2018 Table R602.3(3) (UpCodes): 8d common, 7/16 in. 24/16 panel, 6 in. edges / 12 in. field, Vult 170 Exp. B at 16 in. studs; R602.10.4 WSP/CS-WSP fasten per R602.3(3) at 6/12. ZIP: Huber HUB 9216, code-recognized fasteners as for OSB")

# Subfloor (decision #147): glued and screwed, the WSV in place of the 8d of R602.3(1)
# item 31 at its spacing. Special (a screw, not the row's nail): S-001 lists it.
SUBFLOOR_FASTENING = SheathingNailing(
    part="WSV212S", edge_oc_in=6.0, field_oc_in=12.0,
    source="ICC-ES ESR-1472 (reissued Sept. 2026) 4.1.2.1: WSV screws >= 2 in. may substitute for the 8d/10d common nails of IRC 2018 Table R602.3(1) items 30-32 (subflooring to framing), >= 1-3/8 in. penetration; item 31 spacing (19/32-1 in., 6 in. edges / 12 in. intermediate)")

HEADER_STANDARD = [
    HeaderStandard(uid="FPEZ7QS5W4", tag="HEADER-STANDARD", min_bearing_header="2-2x8"),
    # centre_cladding: the court's LP panel is laid from its centre, for the look (owner,
    # 2026-11-25); sheathing still walks from its through end.
    SheetLayoutStandard(uid="D0FSC9880R", tag="SHEET-LAYOUT-STANDARD", orientation="vertical",
                        min_rip_width=inch(12), min_edge_bearing=inch(0.4375),
                        stagger_min=inch(16), kerf=inch(0.125), start_at_through_end=True,
                        max_course_shortfall=inch(0.75), centre_cladding=True,
                        source="APA E30 (3/8 in. nail edge distance) + 1/2 of an 8d common shank"),
]
