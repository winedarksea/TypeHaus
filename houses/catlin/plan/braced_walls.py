# haus: editable
# IRC R602.10 braced wall panels — the house and the garage, Method CS-WSP throughout.
#
# ** `# haus: editable` IS HERE FOR `haus fmt`, NOT FOR THE EDITOR. ** A panel is a
# designation, like a Circuit: nothing in the UI moves one. The marker is what lets
# `haus fmt` mint the ~70 uids below, and that is the whole reason for it.
#
# ** CS-WSP EVERYWHERE, AND WSP WAS REJECTED ON ONE MEASUREMENT. ** Every exterior wall of
# this house is sheathed in 1/2" struct-1 plywood over its whole face, above and below every
# opening (the garage in 5/8" CDX), which is Method CS-WSP's own requirement (R602.10.4.2)
# and is what the house builds anyway. Method WSP would ask 48" of every panel at these wall
# heights (Table R602.10.5) — main E1's first qualifying run is 34 1/2" and its second is
# 37", so the line's first 48" panel would not start until 19'-10", past R602.10.2.2's 10 ft.
# CS-WSP reads its minimum off the ADJACENT CLEAR OPENING HEIGHT instead (27"-35" here), and
# the same sheathing then counts.
#
# ** THE PANELS ARE THE FULL-HEIGHT RUNS BETWEEN OPENINGS, AND NOTHING IS INVENTED. ** Every
# station below is measured off the resolved model: the wall's own start node, the openings
# on it, and Table R602.10.5's minimum at that opening height. A run under the minimum is
# NOT authored — it contributes nothing and authoring it would only put a zero-length
# contributor on the drawing (main E1's two 25 1/2" slivers beside the fire niche, the 17"
# ends beside the two kitchen windows, second S1's 19" beside the deck door, the garage's 7"
# beside the service door). A run that crosses a wall butt is authored once per wall and
# merged by `resolve/braced_walls.py`.
#
# ** THE NE CORNER CARRIES FOUR 800-LB DEVICES (owner, 2026-09-22). ** Both lines at that
# corner end in a 17" sliver — WIN-M-KIT-E and WIN-M-KITCH-N sit 2'-7" off the corner on the
# main floor, WIN-S-BED3 and WIN-S-BED3-N on the second — so neither line has a 24" return to
# turn (Figure R602.10.7 end conditions 1 and 4) and the panel nearest the corner takes an
# 800 lb hold-down instead (end condition 5). THE STANDING ALTERNATIVE, deliberately not
# taken: move those four windows 16" inboard, which buys the returns and deletes all four
# devices. **Never move them TOWARD the corner** — that is the one direction with no answer.
#
# ** THE GARAGE SW CORNER TAKES A FIFTH. ** D-G-SERVICE sits 7" off that corner, so W-G-S has
# no 24" return to give W-G-W's end panel. The alternative is to move the service door 17"
# east, which `plan/storeys/garage.py` warns drags the landing, the carriers, two backing
# bands, three lighting stations and a section cut with it; one cast-in strap is cheaper.
#
# ** THE 16' OVERHEAD DOOR NEEDS NO PORTAL FRAME. ** Its two 4'-0" piers are 48" against
# Table R602.10.5's 35" (CS-WSP, 84" adjacent opening, read at the more onerous of the 8'
# and 9' columns for an 8'-4" wall), so `OVERHEAD_DOOR_OFFSET` is now a GRADED fact: at
# 3'-0" the piers would still clear, and below that Method CS-PF (R602.10.6.4) is the
# fallback the garage would have to adopt.
from typehaus import BracedWallPanel, Connector, ConnectorKind, ft, inch, pt

# The hold-down stations: 3 1/4" inboard of the wall axis, the `CN-M-HD-ENTRY-*` convention
# (plan/storeys/main.py) — the king stud's face at the end of the panel nearest the corner.
_NE_INBOARD = ft(35, 8.75)          # 36'-0" less 3 1/4"
_NE_PANEL_END = ft(33, 5)           # where both NE panels stop, on both floors
_MAIN_HD_Z = inch(1)                # sill-plate mid-height, project-frame absolute
_SECOND_HD_Z = inch(121)            # the same, one floor up (second datum +10'-0")

# ---------------------------------------------------------------------------------------
# MAIN — first story of two. Table R602.10.3(1) at <=115 mph / 40' spacing / CS-WSP reads
# 11.5 ft, x1.15 (eave-to-ridge) x0.95 (9'-0" story) = 12.56 ft per line.
MAIN_BRACED_WALLS = [
    # BWL-W-A-E1 — 19'-7" provided. The 163 1/2" run ends 2'-7" short of the NE corner and
    # takes the hold-down.
    BracedWallPanel(uid="0BK3XPH9EX", tag="BWP-M-E1-0000", wall_ref="W-M-E1", start=inch(0.0),
                    width=inch(34.5), note="SE corner; return for BWL-W-A-S1's east end"),
    BracedWallPanel(uid="0TRH4SAQSS", tag="BWP-M-E1-0174", wall_ref="W-M-E1", start=inch(173.5),
                    width=inch(37.0)),
    BracedWallPanel(uid="KZ7TYRTJKY", tag="BWP-M-E1-0238", wall_ref="W-M-E1", start=inch(237.5),
                    width=inch(163.5), hold_down_ref="CN-M-BWHD-NE-E",
                    note="R602.10.7 end condition 5 at the NE corner"),
    # BWL-W-A-N1 — 28'-2" provided. The 78" run crosses the W-M-N3/W-M-N3B butt.
    BracedWallPanel(uid="58ACV3YPDF", tag="BWP-M-N3-0042", wall_ref="W-M-N3", start=inch(42.0),
                    width=inch(6.0)),
    BracedWallPanel(uid="65VXYA3ZEF", tag="BWP-M-N3B-0000", wall_ref="W-M-N3B", start=inch(0.0),
                    width=inch(72.0),
                    note="AO-M-ERV-OA's 9\" port is a service penetration, not an opening"),
    BracedWallPanel(uid="BWHFQEKHB2", tag="BWP-M-N1-0094", wall_ref="W-M-N1", start=inch(93.5),
                    width=inch(46.5)),
    BracedWallPanel(uid="KKYT2C33M8", tag="BWP-M-N1B-0000", wall_ref="W-M-N1B", start=inch(0.0),
                    width=inch(76.0)),
    BracedWallPanel(uid="EDBNWQY768", tag="BWP-M-N2-0000", wall_ref="W-M-N2", start=inch(0.0),
                    width=inch(96.0)),
    BracedWallPanel(uid="NET8VQTWP7", tag="BWP-M-N3-0000", wall_ref="W-M-N3", start=inch(0.0),
                    width=inch(6.0)),
    BracedWallPanel(uid="F90FQFJGXV", tag="BWP-M-N1-0031", wall_ref="W-M-N1", start=inch(31.0),
                    width=inch(35.5), hold_down_ref="CN-M-BWHD-NE-N",
                    note="R602.10.7 end condition 5 at the NE corner"),
    # BWL-W-A-S1 — 23'-6" provided.
    BracedWallPanel(uid="E93FHN22AB", tag="BWP-M-S1-0000", wall_ref="W-M-S1", start=inch(0.0),
                    width=inch(33.0), note="SW corner; return for BWL-W-A-W1's south end"),
    BracedWallPanel(uid="G47B3JDPK5", tag="BWP-M-S1-0063", wall_ref="W-M-S1", start=inch(63.0),
                    width=inch(98.0),
                    note="AO-M-PORCH-HYD's 2 1/2\" hose bibb is a service penetration"),
    BracedWallPanel(uid="2ENAKWR6JH", tag="BWP-M-S1-0191", wall_ref="W-M-S1", start=inch(191.0),
                    width=inch(25.0)),
    BracedWallPanel(uid="ZH2V7AW8PA", tag="BWP-M-S2-0000", wall_ref="W-M-S2", start=inch(0.0),
                    width=inch(10.0)),
    BracedWallPanel(uid="YSEYF7GF0J", tag="BWP-M-S2-0070", wall_ref="W-M-S2", start=inch(70.0),
                    width=inch(83.0)),
    BracedWallPanel(uid="VX1VGVJS1D", tag="BWP-M-S2-0183", wall_ref="W-M-S2", start=inch(183.0),
                    width=inch(33.0), note="SE corner return"),
    # BWL-W-A-W1 — 26'-11" provided.
    BracedWallPanel(uid="Q0B7D5A81N", tag="BWP-M-W4-0106", wall_ref="W-M-W4", start=inch(105.5),
                    width=inch(50.5), note="SW corner; 50 1/2\" is end condition 3"),
    BracedWallPanel(uid="1BV2KCN83W", tag="BWP-M-W4-0042", wall_ref="W-M-W4", start=inch(41.5),
                    width=inch(37.0)),
    BracedWallPanel(uid="3JGJ937175", tag="BWP-M-W3-0042", wall_ref="W-M-W3", start=inch(41.5),
                    width=inch(70.5)),
    BracedWallPanel(uid="KQKSNR8NDC", tag="BWP-M-W4-0000", wall_ref="W-M-W4", start=inch(0.0),
                    width=inch(14.5)),
    BracedWallPanel(uid="C2TCD1J5KN", tag="BWP-M-W2-0029", wall_ref="W-M-W2", start=inch(29.0),
                    width=inch(21.0)),
    BracedWallPanel(uid="2XPV7AX7JJ", tag="BWP-M-W3-0000", wall_ref="W-M-W3", start=inch(0.0),
                    width=inch(14.5)),
    BracedWallPanel(uid="509W4PNV0M", tag="BWP-M-W1-0031", wall_ref="W-M-W1", start=inch(31.0),
                    width=inch(13.5)),
    BracedWallPanel(uid="QBJM5Z9MK6", tag="BWP-M-W1C-0000", wall_ref="W-M-W1C", start=inch(0.0),
                    width=inch(37.5)),
    BracedWallPanel(uid="8HCYR1BY53", tag="BWP-M-W2-0000", wall_ref="W-M-W2", start=inch(0.0),
                    width=inch(15.0)),
    BracedWallPanel(uid="5CVH7SFX70", tag="BWP-M-W1-0000", wall_ref="W-M-W1", start=inch(0.0),
                    width=inch(17.0)),
    BracedWallPanel(uid="P43WX6T0PK", tag="BWP-M-W1B-0000", wall_ref="W-M-W1B", start=inch(0.0),
                    width=inch(32.0), note="NW corner; 49\" merged is end condition 3"),
]

# The two cast-in straps at the NE corner. STHD14RJ and not the plain STHD14: the main floor
# deck sits between the basement wall top and these panels, and the RJ strap is the one long
# enough to cross it (ESR-2920 Table 1; 17" maximum unnailed clear span, and this band is
# 13 1/2").
MAIN_BRACED_CONNECTORS = [
    Connector(uid="338EJC5QA2", tag="CN-M-BWHD-NE-E", kind=ConnectorKind.HOLD_DOWN,
              position=pt(_NE_INBOARD, _NE_PANEL_END), elevation=_MAIN_HD_Z,
              size="STHD14RJ", connects=("W-M-E1", "W-B-E2")),
    Connector(uid="0RQCYBMJ89", tag="CN-M-BWHD-NE-N", kind=ConnectorKind.HOLD_DOWN,
              position=pt(_NE_PANEL_END, _NE_INBOARD), elevation=_MAIN_HD_Z,
              size="STHD14RJ", connects=("W-M-N1", "W-B-N1")),
]

# ---------------------------------------------------------------------------------------
# SECOND — the top story. 6.0 ft x1.30 (eave-to-ridge, measured from this storey's top
# plate to the ridge: the habitable attic is not a story and its gable walls ride this
# factor) x0.95 = 7.41 ft per line, and 10.37 ft on the two lines the plant room stands on,
# where Table R602.10.3(2) item 6 charges x1.40 for a panel with no gypsum inside it.
SECOND_BRACED_WALLS = [
    # BWL-W-A-E1 — 26'-8" provided.
    BracedWallPanel(uid="J1DJCJK12V", tag="BWP-S-E1-0000", wall_ref="W-S-E1", start=inch(0.0),
                    width=inch(34.5), note="SE corner return"),
    BracedWallPanel(uid="HD9VHPM55N", tag="BWP-S-E1-0062", wall_ref="W-S-E1", start=inch(61.5),
                    width=inch(46.5)),
    BracedWallPanel(uid="X0BJTGKPWB", tag="BWP-S-E2-0000", wall_ref="W-S-E2", start=inch(0.0),
                    width=inch(38.5)),
    BracedWallPanel(uid="QH49XH0ZDQ", tag="BWP-S-E2-0066", wall_ref="W-S-E2", start=inch(65.5),
                    width=inch(38.5)),
    BracedWallPanel(uid="S1C5H53WFS", tag="BWP-S-E3-0000", wall_ref="W-S-E3", start=inch(0.0),
                    width=inch(46.5)),
    BracedWallPanel(uid="DYES49FCSP", tag="BWP-S-E3-0074", wall_ref="W-S-E3", start=inch(73.5),
                    width=inch(34.5)),
    BracedWallPanel(uid="PY14ZH198H", tag="BWP-S-E4-0000", wall_ref="W-S-E4", start=inch(0.0),
                    width=inch(81.0), hold_down_ref="CN-S-BWHD-NE-E",
                    note="R602.10.7 end condition 5 at the NE corner"),
    # BWL-W-A-N1 — 28'-11" provided.
    BracedWallPanel(uid="0BKQ0Y5079", tag="BWP-S-N2-0086", wall_ref="W-S-N2", start=inch(85.5),
                    width=inch(10.5)),
    BracedWallPanel(uid="2Q5HXNJ6MD", tag="BWP-S-N3-0000", wall_ref="W-S-N3", start=inch(0.0),
                    width=inch(87.0)),
    BracedWallPanel(uid="SAP7Y0TCGZ", tag="BWP-S-N3B-0000", wall_ref="W-S-N3B", start=inch(0.0),
                    width=inch(33.0),
                    note="AO-S-ERV-EA's 9\" port is a service penetration, not an opening"),
    BracedWallPanel(uid="HPXGXK35XZ", tag="BWP-S-N1-0158", wall_ref="W-S-N1", start=inch(157.5),
                    width=inch(11.5)),
    BracedWallPanel(uid="1Q9FM8AC6Q", tag="BWP-S-N1B-0000", wall_ref="W-S-N1B", start=inch(0.0),
                    width=inch(47.0)),
    BracedWallPanel(uid="GEQAX9CJAC", tag="BWP-S-N2-0000", wall_ref="W-S-N2", start=inch(0.0),
                    width=inch(58.5)),
    BracedWallPanel(uid="PYYCZERABX", tag="BWP-S-N1-0031", wall_ref="W-S-N1", start=inch(31.0),
                    width=inch(99.5), hold_down_ref="CN-S-BWHD-NE-N",
                    note="R602.10.7 end condition 5 at the NE corner"),
    # BWL-W-A-S1 — 16'-11" provided against 10.37 ft: W-S-S1 is the plant room, whose PVC
    # liner is not gypsum, so this line pays item 6's x1.40.
    BracedWallPanel(uid="Y9S7CV3A49", tag="BWP-S-S1-0000", wall_ref="W-S-S1", start=inch(0.0),
                    width=inch(33.0), note="SW corner return"),
    BracedWallPanel(uid="EJCZVV971W", tag="BWP-S-S1-0063", wall_ref="W-S-S1", start=inch(63.0),
                    width=inch(34.0)),
    BracedWallPanel(uid="GHW2DD98NE", tag="BWP-S-S1-0127", wall_ref="W-S-S1", start=inch(127.0),
                    width=inch(34.0)),
    BracedWallPanel(uid="D8D3P9T2E3", tag="BWP-S-S1-0191", wall_ref="W-S-S1", start=inch(191.0),
                    width=inch(25.0)),
    BracedWallPanel(uid="0WQ9ZYZ3XH", tag="BWP-S-S2-0000", wall_ref="W-S-S2", start=inch(0.0),
                    width=inch(10.0)),
    BracedWallPanel(uid="CWYKFJ7J49", tag="BWP-S-S2-0119", wall_ref="W-S-S2", start=inch(119.0),
                    width=inch(34.0)),
    BracedWallPanel(uid="THTV68V314", tag="BWP-S-S2-0183", wall_ref="W-S-S2", start=inch(183.0),
                    width=inch(33.0), note="SE corner return"),
    # BWL-W-A-W1 — 26'-11" provided, also against 10.37 ft (W-S-W4 is the plant room's
    # west wall).
    BracedWallPanel(uid="1MADAHH0B7", tag="BWP-S-W4-0058", wall_ref="W-S-W4", start=inch(57.5),
                    width=inch(50.5), note="SW corner; 50 1/2\" is end condition 3"),
    BracedWallPanel(uid="BYFCA49K6E", tag="BWP-S-W3-0154", wall_ref="W-S-W3", start=inch(153.5),
                    width=inch(6.5)),
    BracedWallPanel(uid="JVMC4ADCMQ", tag="BWP-S-W4-0000", wall_ref="W-S-W4", start=inch(0.0),
                    width=inch(30.5)),
    BracedWallPanel(uid="14W4PDZB3D", tag="BWP-S-W3-0042", wall_ref="W-S-W3", start=inch(41.5),
                    width=inch(85.0)),
    BracedWallPanel(uid="1DKX1FP4X5", tag="BWP-S-W2-0029", wall_ref="W-S-W2", start=inch(29.0),
                    width=inch(21.0)),
    BracedWallPanel(uid="HX10BS9THX", tag="BWP-S-W3-0000", wall_ref="W-S-W3", start=inch(0.0),
                    width=inch(14.5)),
    BracedWallPanel(uid="2YFGZKHZW9", tag="BWP-S-W1-0028", wall_ref="W-S-W1", start=inch(27.875),
                    width=inch(51.0)),
    BracedWallPanel(uid="VNDMZBR8ER", tag="BWP-S-W2-0000", wall_ref="W-S-W2", start=inch(0.0),
                    width=inch(15.0)),
    BracedWallPanel(uid="48468JKMDQ", tag="BWP-S-W1-0000", wall_ref="W-S-W1", start=inch(0.0),
                    width=inch(13.875)),
    BracedWallPanel(uid="EH38YXY3JD", tag="BWP-S-W1B-0000", wall_ref="W-S-W1B", start=inch(0.0),
                    width=inch(35.125), note="NW corner; 49\" merged is end condition 3"),
]

# The second-floor pair. A DTT2Z each side of the floor on one 1/2" rod, tying the panel end
# above to the corner post below (R602.10.9) — there is no concrete up here to cast a strap
# into. ESR-2330 Table 4 publishes 1,825 lb at a 1 1/2" member against the 800 lb asked for,
# and it publishes it for SG 0.50 lumber, which is why these two posts are specified DF-L.
SECOND_BRACED_CONNECTORS = [
    Connector(uid="YE8NE66A0N", tag="CN-S-BWHD-NE-E", kind=ConnectorKind.HOLD_DOWN,
              position=pt(_NE_INBOARD, _NE_PANEL_END), elevation=_SECOND_HD_Z,
              size="DTT2Z", connects=("W-S-E1", "W-M-E1")),
    Connector(uid="00909G1F6F", tag="CN-S-BWHD-NE-N", kind=ConnectorKind.HOLD_DOWN,
              position=pt(_NE_PANEL_END, _NE_INBOARD), elevation=_SECOND_HD_Z,
              size="DTT2Z", connects=("W-S-N1", "W-M-N1")),
]

# ---------------------------------------------------------------------------------------
# GARAGE — one story. 4.5 ft x1.00 x0.95 = 4.28 ft per line, and every line clears it twice
# over. The E and S walls are split into two panels each because R602.10.2.3 asks a line
# over 16 ft for not less than two: the sheathing is continuous either way, the designation
# is not.
GARAGE_BRACED_WALLS = [
    BracedWallPanel(uid="FAX16APCA2", tag="BWP-G-E-0000", wall_ref="W-G-E", start=inch(0.0),
                    width=inch(144.0), note="blind wall, split for R602.10.2.3"),
    BracedWallPanel(uid="Z0XPRY0WCA", tag="BWP-G-E-0144", wall_ref="W-G-E", start=inch(144.0),
                    width=inch(144.0)),
    BracedWallPanel(uid="ZQBZQNBQ1T", tag="BWP-G-W-0259", wall_ref="W-G-W", start=inch(259.0),
                    width=inch(29.0), hold_down_ref="CN-G-BWHD-SW",
                    note="SW corner: only 7in of return beside D-G-SERVICE, so end condition 2"),
    BracedWallPanel(uid="APCR31K2YY", tag="BWP-G-W-0043", wall_ref="W-G-W", start=inch(43.0),
                    width=inch(202.0)),
    BracedWallPanel(uid="0SABZSFPT6", tag="BWP-G-W-0000", wall_ref="W-G-W", start=inch(0.0),
                    width=inch(29.0), note="NW corner return for BWL-W-G-N"),
    BracedWallPanel(uid="9ZKS274K27", tag="BWP-G-N-0240", wall_ref="W-G-N", start=inch(240.0),
                    width=inch(48.0),
                    note="west pier of D-G-OVERHEAD: 48\" against Table R602.10.5's 35\""),
    BracedWallPanel(uid="0ETF57CKSX", tag="BWP-G-N-0000", wall_ref="W-G-N", start=inch(0.0),
                    width=inch(48.0), note="east pier of D-G-OVERHEAD"),
    BracedWallPanel(uid="22CSZHTSKN", tag="BWP-G-S-0043", wall_ref="W-G-S", start=inch(43.0),
                    width=inch(121.0), note="split for R602.10.2.3"),
    BracedWallPanel(uid="XWQW640JC9", tag="BWP-G-S-0164", wall_ref="W-G-S", start=inch(164.0),
                    width=inch(124.0), note="SE corner return for BWL-W-G-E"),
]

# Cast into the ICF stem's 6" core at the SW corner (ESR-2920 Table 1's 6" stem rows). The
# plain STHD14, not the RJ: the wood wall bears directly on the stem top, so there is no
# floor band for the long strap to cross.
GARAGE_BRACED_CONNECTORS = [
    Connector(uid="EXWYG5FPB1", tag="CN-G-BWHD-SW", kind=ConnectorKind.HOLD_DOWN,
              position=pt(ft(6, 3.25), ft(43, 5.5)), elevation=inch(-11.25),
              size="STHD14", connects=("W-G-W", "W-GF-W")),
]
