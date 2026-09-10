"""North entry foundation bridge and broad east tiers; roof belongs to the garage.

Schematic members and fixed/slip seats require the structural package described in
notes/north_entry_structure.md. No passage pads, piers or roof posts remain.
"""

from typehaus import (
    Annotation, Beam, Connector, ConnectorKind, DeckLayer, FloorSystem, JoistSpec,
    Node, Railing, RailingKind, SlatScreen, Stair, ft, inch, pt,
)

from params.foundations import SITE_GRADE
from plan.storeys.garage import GARAGE_Y_SOUTH

HOUSE_CLADDING_Y_FT = 36 + 7.25 / 12
GARAGE_CLADDING_Y_FT = GARAGE_Y_SOUTH.feet - 0.875 / 12
GARAGE_INSIDE_Y_FT = GARAGE_Y_SOUTH.feet + 11 / 12
LANDING_WEST_FT = 6.0  # extra west margin keeps screen/guard outside both 36in door patches
LANDING_EAST_FT = 11.5
GARAGE_LANDING_WEST_FT = 8.5
GARAGE_LANDING_END_Y_FT = GARAGE_INSIDE_Y_FT + 3
DECK_FINISH_FT = 0.0
DECK_JOIST_TOP_FT = -1 / 12
JOIST_DEPTH_IN = 7.25
MOVEMENT_GAP_IN = 0.25
DETAIL_CUT_Y_FT = (HOUSE_CLADDING_Y_FT + GARAGE_CLADDING_Y_FT) / 2

# The two members within the service opening continue to the interior stair. The west
# member stops outside: the two-foot door offset cannot be bridged through a solid jamb.
BEAM_WIDTH_IN = 3.0
BEAM_X_FT = (LANDING_WEST_FT + BEAM_WIDTH_IN / 24,
             GARAGE_LANDING_WEST_FT + BEAM_WIDTH_IN / 24,
             LANDING_EAST_FT - BEAM_WIDTH_IN / 24)
HOUSE_SEAT_Y_FT = HOUSE_CLADDING_Y_FT + 2 / 12
GARAGE_SEAT_Y_FT = GARAGE_CLADDING_Y_FT - 2 / 12
FRAME_Y0_FT = HOUSE_SEAT_Y_FT + 1.5 / 12
FRAME_Y1_FT = GARAGE_SEAT_Y_FT - 1.5 / 12


def rectangle(x0, y0, x1, y1):
    return (pt(ft(x0), ft(y0)), pt(ft(x1), ft(y0)),
            pt(ft(x1), ft(y1)), pt(ft(x0), ft(y1)))


NODES = []
BEAMS = []


def beam(number, tag, x0, y0, x1, y1, bearings, top=DECK_JOIST_TOP_FT):
    for end, x, y in (("S", x0, y0), ("N", x1, y1)):
        NODES.append(Node(uid=f"BWNB{number:02d}{end}AAA", tag=f"N-{tag}-{end}",
                          position=pt(ft(x), ft(y))))
    result = Beam(uid=f"BWB{number:03d}AAAA", tag=tag,
                  start_node=f"N-{tag}-S", end_node=f"N-{tag}-N", size="2-2x8",
                  top_elevation=ft(top), bearing_refs=bearings, assembly="BEAM_KDAT",
                  engineering_note="Foundation bridge with custom fixed/slip seats and garage landing cantilever; north_entry_structure.md; sizes provisional",
                  top_protection="butyl-tape-beam")
    BEAMS.append(result)
    return result


# Dropped ledgers on custom stand-off concrete seats, never fastened into EPS or veneer.
beam(1, "BM-BW-HOUSE-SEAT", LANDING_WEST_FT, HOUSE_SEAT_Y_FT,
     LANDING_EAST_FT, HOUSE_SEAT_Y_FT, ("W-B-N3", "W-B-N2"), DECK_JOIST_TOP_FT - JOIST_DEPTH_IN / 12)
beam(2, "BM-BW-GARAGE-SEAT", LANDING_WEST_FT, GARAGE_SEAT_Y_FT,
     LANDING_EAST_FT, GARAGE_SEAT_Y_FT, ("W-GF-S1", "W-GF-S-DR"), DECK_JOIST_TOP_FT - JOIST_DEPTH_IN / 12)
for index, (suffix, x) in enumerate(zip(("FW", "FC", "FE"), BEAM_X_FT, strict=True), 3):
    beam(index, f"BM-BW-{suffix}", x, HOUSE_SEAT_Y_FT, x,
         GARAGE_SEAT_Y_FT if suffix == "FW" else GARAGE_LANDING_END_Y_FT,
         ("BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT"))

FLOOR = FloorSystem(
    uid="BWFS01AAAA", tag="FS-BW-FLOOR",
    top_elevation=ft(DECK_JOIST_TOP_FT),
    joists=JoistSpec(member="2x8", spacing=inch(12), direction="x",
                     bearing_refs=("BM-BW-FW", "BM-BW-FC", "BM-BW-FE")),
    outline=rectangle(BEAM_X_FT[0], FRAME_Y0_FT, BEAM_X_FT[-1], FRAME_Y1_FT),
    subfloor_outline=rectangle(LANDING_WEST_FT, HOUSE_CLADDING_Y_FT,
                               LANDING_EAST_FT, GARAGE_Y_SOUTH.feet),
    subfloor=DeckLayer(material_ref="composite-deck", thickness=inch(1)),
    service="deck", top_protection="butyl-tape",
    source="shared upper landing; fixed house / sliding garage seats; north_entry_structure.md",
)

# A narrower framing zone preserves the main landing identity while keeping the garage
# wall out of the rectangular joist field. Boards share the finish datum and direction.
GARAGE_FLOOR = FloorSystem(
    uid="BWFS02AAAA", tag="FS-BW-GARAGE",
    top_elevation=ft(DECK_JOIST_TOP_FT),
    joists=JoistSpec(member="2x8", spacing=inch(12), direction="x",
                     bearing_refs=("BM-BW-FC", "BM-BW-FE")),
    outline=rectangle(BEAM_X_FT[1], GARAGE_Y_SOUTH.feet + MOVEMENT_GAP_IN / 12,
                      BEAM_X_FT[2], GARAGE_LANDING_END_Y_FT),
    subfloor_outline=rectangle(GARAGE_LANDING_WEST_FT,
                               GARAGE_Y_SOUTH.feet + MOVEMENT_GAP_IN / 12,
                               LANDING_EAST_FT, GARAGE_LANDING_END_Y_FT),
    subfloor=DeckLayer(material_ref="composite-deck", thickness=inch(1)),
    service="deck", top_protection="butyl-tape",
    source="FS-BW-FLOOR continuation; 1/4in threshold joint; replaces SL-G-STEP-0",
)

SEATS = [
    Connector(uid=f"BWCS{i}{end}AAAA", tag=f"CN-BW-{end}-{i}",
              kind=ConnectorKind.HOLD_DOWN, position=pt(ft(x), ft(y)),
              elevation=ft(DECK_JOIST_TOP_FT - JOIST_DEPTH_IN / 12), size=f"BW-ENGINEERED-{condition}-SEAT",
              connects=(ledger, substrate), source="houses/catlin/notes/north_entry_structure.md — custom seat specification pending engineering")
    for i, x in enumerate(BEAM_X_FT, 1)
    for end, y, ledger, substrate, condition in (
        ("HOUSE", HOUSE_SEAT_Y_FT, "BM-BW-HOUSE-SEAT",
         "W-B-N3" if x < 10 else "W-B-N2", "FIXED"),
        ("GARAGE", GARAGE_SEAT_Y_FT, "BM-BW-GARAGE-SEAT",
         "W-GF-S1" if x < 8.25 else "W-GF-S-DR", "SLIDING"),
    )
]

STAIR_Y0_FT = HOUSE_CLADDING_Y_FT + 3 / 12
STAIR_Y1_FT = GARAGE_CLADDING_Y_FT - 3 / 12
STAIR_WIDTH_FT = STAIR_Y1_FT - STAIR_Y0_FT
TREAD_DEPTH_FT = 2.0
TREAD_COUNT = 4
STAIR_FOOT_X_FT = LANDING_EAST_FT + TREAD_COUNT * TREAD_DEPTH_FT
LOWER_LANDING_END_X_FT = STAIR_FOOT_X_FT + 3

TIERS = Stair(
    uid="BWST01AAAA", tag="ST-BW-ENTRY", from_storey="main", to_storey="main",
    base_elevation=SITE_GRADE, top_elevation=ft(DECK_FINISH_FT),
    width=ft(STAIR_WIDTH_FT), start=pt(ft(STAIR_FOOT_X_FT), ft(STAIR_Y0_FT)),
    run_direction="x", run_reversed=True, tread_depth=ft(TREAD_DEPTH_FT),
    nosing_depth=inch(0), material="kdat", stringer_spacing=inch(12),
    tread_material="composite-deck", tread_thickness=inch(1),
)


def guard(uid, tag, path):
    return Railing(uid=uid, tag=tag, path=tuple(pt(ft(x), ft(y)) for x, y in path),
                   height=inch(36), base_elevation=ft(DECK_FINISH_FT),
                   post_spacing=inch(36), post_size="2x2", rail_count=2,
                   kind=RailingKind.METAL_SURFACE_MOUNT, mount="surface",
                   assembly="RAILING_DARK_METAL", infill="balusters", baluster_spacing=inch(3.5))


RAILINGS = [
    guard("BWRGW1AAAA", "RL-BW-WEST", ((6.4, HOUSE_CLADDING_Y_FT),
                                      (6.4, GARAGE_CLADDING_Y_FT))),
    guard("BWRGGWAAAA", "RL-BW-GARAGE-W", ((8.5, GARAGE_INSIDE_Y_FT),
                                          (8.5, GARAGE_LANDING_END_Y_FT))),
    guard("BWRGGEAAAA", "RL-BW-GARAGE-E", ((11.5, GARAGE_INSIDE_Y_FT),
                                          (11.5, GARAGE_LANDING_END_Y_FT))),
    Railing(uid="BWRHE1AAAA", tag="RL-BW-ENTRY",
            path=(pt(ft(STAIR_FOOT_X_FT), ft(STAIR_Y1_FT)),
                  pt(ft(LANDING_EAST_FT), ft(STAIR_Y1_FT))),
            kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
            base_elevation=SITE_GRADE, post_spacing=inch(36), post_size="2x2",
            rail_count=1, mount="surface", assembly="RAILING_DARK_METAL",
            role="guard_and_handrail", serves_stair="ST-BW-ENTRY", top_height=inch(36),
            graspable_profile="1.5in round — Type I", infill="balusters",
            baluster_spacing=inch(3.5)),
]

NOTES = [
    Annotation(uid="BWAN03AAAA", tag="AN-BW-ROOF", position=pt(ft(22), ft(40)),
               text="OFF-MODEL TRUSS PACKAGE: 6ft cantilever/backspan, house snow drift, uplift to E/W garage walls; old gable fire/draft closure; 4–6in flexible house joint"),
    Annotation(uid="BWAN01AAAA", tag="AN-BW-STRUCTURE", position=pt(ft(7), ft(39)),
               text="ENGINEERED BRIDGE: fixed house / sliding garage concrete seats; shim access; see north_entry_structure.md"),
    Annotation(uid="BWAN02AAAA", tag="AN-BW-TIERS", position=pt(ft(16), ft(39)),
               text="5 equal 6.8in rises; four 24in composite tiers; 12in max stringers; drained paver landing and seasonal movement detail"),
]

# On-edge 2x4s: 3.5in projection in x, 1.5in faces and gaps along y. They stand on
# the west floor beam and carry only themselves; a separate guard takes guard loads.
SCREEN_PITCH_IN = 3.0
SCREEN_START_Y_FT = FRAME_Y0_FT + 1.5 / 12
SCREEN_END_Y_FT = FRAME_Y1_FT - 1.5 / 12
SCREEN_SLAT_COUNT = int((SCREEN_END_Y_FT - SCREEN_START_Y_FT) * 12 / SCREEN_PITCH_IN) + 1
SCREEN = SlatScreen(
    uid="BWSC001AAA", tag="SC-BW-WEST", start=pt(ft(BEAM_X_FT[0]), ft(SCREEN_START_Y_FT)),
    end=pt(ft(BEAM_X_FT[0]), ft(SCREEN_END_Y_FT)), base_elevation=ft(DECK_JOIST_TOP_FT),
    height=ft(8), slat_face=inch(1.5), slat_depth=inch(3.5), clear_gap=inch(1.5),
    assembly="POST_KDAT", supported_by="BM-BW-FW",
    engineering_note="Non-guard screen, 50% open; design wind bracing and fixings with bridge frame",
)

# Procurement allowance at the two eaves over the entry zone. Supplier must size rail
# lengths, row spacing and clamp demand for the actual drift load and roof profile.
SNOW_RETENTION = [
    Connector(uid=f"BWNS{side}{i}AAAA", tag=f"CN-BW-SNOW-{side}-{i}",
              kind=ConnectorKind.SNOW_GUARD, position=pt(ft(x), ft(y)),
              elevation=ft(8, 2), size="S-5! ColorGard", connects=("RF-GARAGE",),
              source="north_entry_structure.md — provisional entry-zone snow-rail layout")
    for side, x in (("W", 5.5), ("E", 30.5))
    for i, y in enumerate((38.5, 42.5), 1)
]

MAIN_ELEMENTS = [*NODES, *BEAMS, FLOOR, GARAGE_FLOOR, *SEATS, TIERS, SCREEN,
                 *RAILINGS, *SNOW_RETENTION, *NOTES]
