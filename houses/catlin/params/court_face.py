"""The sunken court's house face when it is brick: W-B-BRICK and everything that exists for it.

Built only under ``sunken_garden.cladding`` = brick / fiber-cement (variant ``court-face-brick``;
the fiber-cement variants swap the wythe's assembly and keep its geometry). The default face
is LP SmartSide panel on W-B-S2-FR/S3-FR (notes/court_face_lp_panel.md), which needs none of
this, only its sealant joints at the court walls (``_LP_JOINTS``, below). The beam-side half
(W-SG-BRKBM, its bed, board and slab void) is gated in place in params/sunken_garden.py.
Not ``# haus: editable``: the switch is the point, and the elements keep the uids and tags
they had in plan/storeys/basement.py, masonry_joints.py and transitions.py. The oracles stay
live: notes/sunken_garden_veneer_beam.md, notes/veneer_opening_detail.md.
"""

from __future__ import annotations

from params.sunken_garden_options import OPTION
from typehaus import (Beam, Flashing, FormedFlashingSection, FoundationWall, MovementJoint, Node,
                      RoughOpening, Slice, SliceKind, Transition, TrimKind, face, from_node, ft,
                      inch, pt)

IS_BRICK = OPTION.has_brick_face

# A freestanding wythe off the backup's FOAM face (-4.06"), both ends `open_end`: the 1.94"
# `air-gap` puts its back on W-SG-BRKBM's concrete north face (-6.0", veneer note §6k). Its x
# runs 1/2" off W-SG-W1/E1's clear faces (9'-6" / 26'-6"): the two soft joints, graded by
# `structural.masonry_movement_joint` off these nodes. The lintel nodes give 4" of bearing past
# each reveal's jambs on the brick's centre line (-7 13/16").
_NODES = [
    Node(uid="CBN019AAAA", tag="N-B-BRICK-W", position=pt(ft(9, 6.5), inch(-4.06)),
         open_end=True),
    Node(uid="CBN020AAAA", tag="N-B-BRICK-E", position=pt(ft(26, 5.5), inch(-4.06)),
         open_end=True),
    Node(uid="AJQZFAJA54", tag="N-B-LINTEL-WIN-W", position=pt(inch(157), inch(-7.8125)), open_end=True),
    Node(uid="B1V1GP5A21", tag="N-B-LINTEL-WIN-E", position=pt(inch(179), inch(-7.8125)), open_end=True),
    Node(uid="FMVJN56WM2", tag="N-B-LINTEL-DOOR-W", position=pt(inch(220.34375), inch(-7.8125)), open_end=True),
    Node(uid="ZV7YRY3Z02", tag="N-B-LINTEL-DOOR-E", position=pt(inch(291.65625), inch(-7.8125)), open_end=True),
]

# Stands on W-SG-BRKBM, not the house footing: the wythe runs at outdoor temperature, and the
# beam's 2" board breaks that path. Authored EAST->WEST on purpose: its own open wall-graph
# component takes outward sign +1, so its layers build south into the court. Top -13 1/3",
# 2 1/12" under the porch joists (nothing grades that gap); bottom = the beam's top.
_WALLS = [
    FoundationWall(uid="CBW126AAAA", tag="W-B-BRICK", start_node="N-B-BRICK-E",
                   end_node="N-B-BRICK-W",
                   assembly="BASEMENT_BRICK_VENEER",
                   alignment=face("air-gap-int"),
                   unbalanced_fill=ft(0),
                   top_elevation=inch(-13.333), bottom_elevation=inch(-102.4375)),
]

# The wythe's reveals in front of WIN-B-SAUNA and D-B-SUNKEN (not duplicate Window/Door),
# flat-headed on a lintel each. `integrity.reveal_concentric` keeps each on its opening;
# test_catlin_contract_m3 pins both pairs. Edit the reveal with its opening.
_OPENINGS = [
    RoughOpening(uid="CBO601AAAA", tag="AO-B-BRICK-WIN", host="W-B-BRICK",
                 position=from_node("N-B-BRICK-W", inch(46.5)),
                 width=inch(14), height=inch(20), sill_height=inch(37)),
    RoughOpening(uid="CBO602AAAA", tag="AO-B-BRICK-DOOR", host="W-B-BRICK",
                 position=from_node("N-B-BRICK-W", inch(109.84375)),
                 width=inch(63.3125), height=inch(80), sill_height=ft(0)),
]

# IRC R703.8.3 / Table R703.8.3.1: L3x3x1/4 HDG (ASTM A123), 4" bearing, no story above, 6 ft.
_BEAMS = [
    Beam(uid="310GJ6VFEJ", tag="BM-B-BRICK-LINTEL-WIN", start_node="N-B-LINTEL-WIN-W", end_node="N-B-LINTEL-WIN-E",
         size="L3x3x0.25", bearing_refs=("W-B-BRICK",), top_elevation=inch(-42.4375),
         engineering_note="L3x3x1/4 hot-dip galvanized (ASTM A123) steel angle lintel over AO-B-BRICK-WIN, 4 in bearing each side: IRC Table R703.8.3.1, 3x3x1/4, no story above, 6 ft"),
    Beam(uid="GA9XME0R7M", tag="BM-B-BRICK-LINTEL-DOOR", start_node="N-B-LINTEL-DOOR-W",
         end_node="N-B-LINTEL-DOOR-E", size="L3x3x0.25", bearing_refs=("W-B-BRICK",),
         top_elevation=inch(-19.4375),
         engineering_note="L3x3x1/4 hot-dip galvanized (ASTM A123) steel angle lintel over AO-B-BRICK-DOOR, 4 in bearing each side: IRC Table R703.8.3.1, 3x3x1/4, no story above, 6 ft"),
]

# R703.8.5 base sheet (dry: the bond break, BIA TN 28D) and head sheets, Type 316 stainless; each
# head sheet stands on 1/16" EPDM over the HDG angle. Weeps (R703.8.6) are not modelled.
_SECTION = FormedFlashingSection(profile="counter", upstand=inch(2), drip=inch(0.375))
_FLASHINGS = [
    Flashing(uid="0WA1308RE7", tag="FL-B-BRICK-BASE-W", kind=TrimKind.DRIP_FLASHING, host_ref="W-B-BRICK",
             path=(pt(inch(114.5), inch(-6.0)), pt(inch(224.34375), inch(-6.0))),
             top_elevation=inch(-102.4375), depth=inch(0.375), thickness=inch(4.0),
             material="stainless-steel-flashing", back_side="right", section=_SECTION),
    Flashing(uid="8E5HFJYK0Q", tag="FL-B-BRICK-BASE-E", kind=TrimKind.DRIP_FLASHING, host_ref="W-B-BRICK",
             path=(pt(inch(287.65625), inch(-6.0)), pt(inch(317.5), inch(-6.0))),
             top_elevation=inch(-102.4375), depth=inch(0.375), thickness=inch(4.0),
             material="stainless-steel-flashing", back_side="right", section=_SECTION),
    Flashing(uid="X5DHN3YANZ", tag="FL-B-BRICK-WIN-HEAD", kind=TrimKind.DRIP_FLASHING, host_ref="W-B-BRICK",
             path=(pt(inch(157), inch(-6.0)), pt(inch(179), inch(-6.0))),
             top_elevation=inch(-42.375), depth=inch(0.375), thickness=inch(4.0),
             material="stainless-steel-flashing", back_side="right", section=_SECTION),
    Flashing(uid="D9RT7NGEG8", tag="FL-B-BRICK-DOOR-HEAD", kind=TrimKind.DRIP_FLASHING, host_ref="W-B-BRICK",
             path=(pt(inch(220.34375), inch(-6.0)), pt(inch(291.65625), inch(-6.0))),
             top_elevation=inch(-19.375), depth=inch(0.375), thickness=inch(4.0),
             material="stainless-steel-flashing", back_side="right", section=_SECTION),
    Flashing(uid="XJS864FKEX", tag="FL-B-BRICK-WIN-ISOL", kind=TrimKind.WRB_COUNTERFLASHING, host_ref="W-B-BRICK",
             path=(pt(inch(157), inch(-6.0)), pt(inch(179), inch(-6.0))),
             top_elevation=inch(-42.375), depth=inch(0.0625), thickness=inch(4.0),
             material="epdm", back_side="right"),
    Flashing(uid="4P47AE0VFN", tag="FL-B-BRICK-DOOR-ISOL", kind=TrimKind.WRB_COUNTERFLASHING, host_ref="W-B-BRICK",
             path=(pt(inch(220.34375), inch(-6.0)), pt(inch(291.65625), inch(-6.0))),
             top_elevation=inch(-19.375), depth=inch(0.0625), thickness=inch(4.0),
             material="epdm", back_side="right"),
]

# The wythe's two soft ends (BIA TN 18A Eq. 1, veneer note §6g/§6k): 1/2" Class 50 neutral-cure
# silicone over 5/8" closed-cell rod, half the seal depth in from the brick's south face.
_SEAL = ("neutral-cure low-modulus silicone, ASTM C920 Type S Grade NS Class 50 or better, "
         "brick-matched")
_SEAL_SOURCE = ("ASTM C920 Type S Grade NS Class 50+ (e.g. DOWSIL 790/795, GE SilPruf SCS2000, "
                "Pecora 890NST, as equals); backer ASTM C1330 Type C")
_BACKER = "5/8\" closed-cell backer rod (ASTM C1330 Type C)"
_JOINTS = [
    MovementJoint(uid="8C4QVJG0H7", tag="MJ-B-BRICK-E",
                  path=(pt(inch(317.5), inch(-9.5)), pt(inch(318), inch(-9.5))),
                  top_elevation=inch(-13.333), depth=inch(89.104), thickness=inch(0.25),
                  material=_SEAL, host_ref="W-B-BRICK", abuts="W-SG-E1", compression_pct=50.0,
                  backer=_BACKER, source=_SEAL_SOURCE),
    MovementJoint(uid="H1GWTPAS9B", tag="MJ-B-BRICK-W",
                  path=(pt(inch(114), inch(-9.5)), pt(inch(114.5), inch(-9.5))),
                  top_elevation=inch(-13.333), depth=inch(89.104), thickness=inch(0.25),
                  material=_SEAL, host_ref="W-B-BRICK", abuts="W-SG-W1", compression_pct=50.0,
                  backer=_BACKER, source=_SEAL_SOURCE),
]

# The veneer's two detail cuts (A-5xx): the lintel and head sheet at D-B-SUNKEN's reveal, and
# the base bond break on the beam west of it.
_SLICES = [
    Slice(uid="H1459MWCKF", tag="SL-D-VENEER-HEAD", kind=SliceKind.DETAIL,
          title="Veneer lintel and head flashing at the door reveal",
          cut_origin=pt(ft(21, 4), ft(0)), cut_direction="y",
          crop=(pt(inch(-15), inch(-30)), pt(inch(6), inch(-10)))),
    Slice(uid="XQWZ2CJ90N", tag="SL-D-VENEER-BASE", kind=SliceKind.DETAIL,
          title="Veneer base bond break and flashing on the court beam",
          cut_origin=pt(ft(12, 6), ft(0)), cut_direction="y",
          crop=(pt(inch(-18), inch(-112)), pt(inch(6), inch(-94)))),
]

# Their opening-perimeter sheets. Imported here, not from plan/transitions.py, so that the
# `AIR_WATER_THERMAL` tuple stays defined once.
from plan.transitions import AIR_WATER_THERMAL  # noqa: E402

_TRANSITIONS = (
    Transition(uid="109WBK5F0T", tag="TR-CATLIN-SUNKEN-TREAD-BED", title="Sunken-garden tread bed in the veneer beam's board",
               condition_pattern="opening_perimeter:SG_VENEER_BEAM_14",
               notes="notes/court_opening_detail.md", star=False,
               suppress=True,
               suppress_reason="the beam's XPS board cut down under the sunken-garden tread, not a framed opening; coordinated in the sunken-garden door installation review"),
    # Flat heads on a lintel, flashed heads and base, weeps: their own sheet.
    Transition(uid="CATR015AAAA", tag="TR-CATLIN-VENEER-OPENING", title="Veneer opening",
               condition_pattern="opening_perimeter:BASEMENT_BRICK_VENEER",
               notes="notes/veneer_opening_detail.md"),
    # The framed walkout behind the brick: an innie opening on the 7 1/4" curb, the water plane
    # the waterproofing over the sheathing. Starred: the hand spec (opening_flashing_spec.md §8).
    Transition(uid="6997Z5EY26", tag="TR-CATLIN-GARDEN-FRAMED-OPENING", title="Garden framed opening",
               condition_pattern="opening_perimeter:GARDEN_FRAMED_2X6",
               notes="notes/court_opening_detail.md",
               overlay="window-head-jamb-sill", continuity=AIR_WATER_THERMAL,
               star=True),
)

# The LP face's sealant joints (notes/court_face_lp_panel.md, "Court-wall ends"). Each stem
# board's court edge (2 1/2" of XPS between W-SG-W1/E1's end and the house foam) is capped
# 1/4" deep, flush with the court face, slab to the panel top (above it, W-M-S1/S2's skin
# covers the edge), and is the panel's butt joint:
# the panel overruns to 1/4" off it (W-B-S2-FR/S3-FR `skin_overrun`). The rim slab's 0.69" joint
# to the curbs' coated foam takes a traffic-grade seal between the caps. Both are movement
# joints: the court slides on the house (court_sliding_levers_study.md).
_LP_BACKER = "closed-cell backer rod (ASTM C1330 Type C), 25% over the joint width"
_LP_SEAL_SOURCE = ("LP AI 2024 p.11 (3/16 in gap and sealant where the panel meets another "
                   "material); backer ASTM C1330 Type C")
_LP_JOINTS = [
    MovementJoint(uid="2QYJH3CTKV", tag="MJ-SG-W1-STEM",
                  path=(pt(inch(114.125), inch(-6.68)), pt(inch(114.125), inch(-4.06))),
                  top_elevation=inch(-13.4375), depth=inch(96.0), thickness=inch(0.25),
                  material="lp-joint-sealant", host_ref="TB-SG-W1-STEM", abuts="W-B-S2-FR",
                  compression_pct=50.0, backer=_LP_BACKER, source=_LP_SEAL_SOURCE),
    MovementJoint(uid="XX7AHGSA0V", tag="MJ-SG-E1-STEM",
                  path=(pt(inch(317.875), inch(-6.68)), pt(inch(317.875), inch(-4.06))),
                  top_elevation=inch(-13.4375), depth=inch(96.0), thickness=inch(0.25),
                  material="lp-joint-sealant", host_ref="TB-SG-E1-STEM", abuts="W-B-S3-FR",
                  compression_pct=50.0, backer=_LP_BACKER, source=_LP_SEAL_SOURCE),
    MovementJoint(uid="422VHQBG5R", tag="MJ-SG-CURB", vertical=False,
                  path=(pt(inch(114.25), inch(-4.40625)), pt(inch(317.75), inch(-4.40625))),
                  top_elevation=inch(-109.4375), depth=inch(0.5), thickness=inch(0.6875),
                  material="slab-joint-sealant", host_ref="SL-SG-FLOOR", abuts="W-B-S2",
                  compression_pct=25.0, backer=_LP_BACKER, source=_LP_SEAL_SOURCE),
]

BASEMENT_ELEMENTS = ([*_NODES, *_WALLS, *_OPENINGS, *_BEAMS, *_FLASHINGS, *_JOINTS] if IS_BRICK
                     else [*_LP_JOINTS])
MAIN_ELEMENTS = [*_SLICES] if IS_BRICK else []
TRANSITIONS = _TRANSITIONS if IS_BRICK else ()
