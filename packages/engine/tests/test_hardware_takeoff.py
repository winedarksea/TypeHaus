"""Hardware quantities in the BOM — screws, hangers, anchors, ties, braces, straps.

Every count must be *derived*: the unit tests pin the rules on synthetic geometry, and the
catlin cases assert the rule fired on the real model rather than a memorised number.
"""

from __future__ import annotations

import pytest

from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Connector
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import (
    FramedMember,
    ResolvedConstructionReturn,
    ResolvedFloor,
    ResolvedModel,
    ResolvedSolid,
)
from typehaus.takeoff import hardware_takeoff
from typehaus.takeoff.anchors import knee_brace_rows, mudsill_anchor_rows
from typehaus.takeoff.fasteners import (
    exposed_fastener_cladding_screw_rows,
    exterior_insulation_fastening,
    fastener_grid_count,
)
from typehaus.takeoff.hangers import hung_connections
from typehaus.takeoff.hardware_catalog import (
    ROLE_EXPOSED_FASTENER_PANEL_SCREW,
    ROLE_EXTERIOR_INSULATION_SCREW,
    ROLE_KNEE_BRACE,
    ROLE_MUDSILL_ANCHOR,
    ROLE_PIPE_CLAMP,
    ROLE_SLOPED_JOIST_HANGER,
    ROLE_THROUGH_PANEL_PIPE_STRAP,
    hardware_for_role,
    screw_for_required_length,
    structural_hardware_catalog,
)
from typehaus.takeoff.hardware_config import (
    DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG,
)
from typehaus.takeoff.hardware_config import FT_TO_M

FASTENERS = CONFIG.exterior_insulation_fasteners
STRIP_SPACING_M = FASTENERS.strip_spacing_in * M_PER_IN
FASTENER_PITCH_M = FASTENERS.fastener_pitch_along_strip_in * M_PER_IN

# The catlin exterior wall stack, interior→exterior (function, thickness_m, name).
_CATLIN_EXT_STACK = [
    ("finish", 0.625 * M_PER_IN, "gwb-int"),
    ("structure", 5.5 * M_PER_IN, "stud"),
    ("sheathing", 0.5 * M_PER_IN, "sheathing"),
    ("membrane", 0.02 * M_PER_IN, "wrb"),
    ("insulation", 2.0 * M_PER_IN, "polyiso"),
    ("insulation", 2.0 * M_PER_IN, "eps"),
    ("furring", 0.5 * M_PER_IN, "furring"),
    ("cladding", 0.5 * M_PER_IN, "cladding"),
]
# A rainscreen batten straight over sheathing: nailed, not screwed through insulation.
_RAINSCREEN_OVER_SHEATHING_STACK = [
    ("structure", 5.5 * M_PER_IN, "stud"),
    ("sheathing", 1.5 * M_PER_IN, "zip-r"),
    ("furring", 0.375 * M_PER_IN, "rainscreen"),
    ("cladding", 0.5 * M_PER_IN, "cladding"),
]


def _floor_of(members) -> ResolvedFloor:
    return ResolvedFloor(uid="F1", tag="FS-T", storey="main", direction="x",
                         members=tuple(members))


def _member(child_key: str, category: str, p0, p1, z0_m: float, z1_m: float,
            profile: str = "2x8", **kwargs) -> FramedMember:
    return FramedMember(parent_uid="T", child_key=child_key, category=category,
                        profile=profile, p0=p0, p1=p1, z0_m=z0_m, z1_m=z1_m,
                        length_m=1.0, **kwargs)


# --- exterior-insulation screws ------------------------------------------------------


def test_screw_grid_over_a_known_wall_area() -> None:
    """An 18 ft x 10 ft wall: strips at 16 in o.c. (13 bays + 1), screws at 24 in (5 + 1)."""
    run_m, rise_m = 18.0 * FT_TO_M, 10.0 * FT_TO_M
    assert fastener_grid_count(run_m, rise_m, STRIP_SPACING_M, FASTENER_PITCH_M) == 14 * 6
    # Half a bay more of wall adds a strip, not a fraction of one.
    assert fastener_grid_count(run_m + STRIP_SPACING_M / 2, rise_m,
                               STRIP_SPACING_M, FASTENER_PITCH_M) == 15 * 6


def test_screw_length_follows_the_assembly_stack() -> None:
    wall = exterior_insulation_fastening(_CATLIN_EXT_STACK, FASTENERS)
    assert wall is not None and wall.fastened_layer == "furring"
    # sheathing 0.5 + wrb 0.02 + polyiso 2 + eps 2 + furring 0.5 = 5.02 in of penetration.
    assert wall.required_screw_length_in(FASTENERS) == pytest.approx(5.02 + 1.5, abs=1e-6)
    _, length_in, part_number = screw_for_required_length(
        ROLE_EXTERIOR_INSULATION_SCREW, wall.required_screw_length_in(FASTENERS))
    assert (length_in, part_number) == (8.0, "SDWS22800DB")


def test_batten_over_sheathing_is_not_a_structural_screw_condition() -> None:
    assert exterior_insulation_fastening(_RAINSCREEN_OVER_SHEATHING_STACK, FASTENERS) is None


def test_a_vented_mat_over_a_nailbase_deck_does_not_steal_the_screw() -> None:
    """The screws stop at the deck they fasten; the mat above it rides the cladding clips.

    A nailbase roof puts a SHEATHING layer where a vented roof puts its battens, and then
    rolls a ventilated mat on top of that. Both qualify as fastened layers by function, so
    the outermost-match rule alone would pick the mat and over-size the screw by the
    underlayment and the mat. The deck is the last layer whose path back to the foam crosses
    nothing but membranes, and that is what makes it the screwed one.
    """
    stack = [
        ("structure", 11.875 * M_PER_IN, "rafter"),
        ("sheathing", 0.5 * M_PER_IN, "zip"),
        ("membrane", 0.04 * M_PER_IN, "deck-vb"),
        ("insulation", 3.0 * M_PER_IN, "polyiso-1"),
        ("insulation", 3.0 * M_PER_IN, "polyiso-2"),
        ("sheathing", 0.625 * M_PER_IN, "top-deck"),
        ("membrane", 0.06 * M_PER_IN, "underlayment"),
        ("airgap", 0.25 * M_PER_IN, "vent-mat"),
        ("cladding", 0.5 * M_PER_IN, "roofing"),
    ]
    roof = exterior_insulation_fastening(stack, FASTENERS)
    assert roof is not None and roof.fastened_layer == "top-deck"
    assert roof.required_screw_length_in(FASTENERS) == pytest.approx(7.165 + 1.5, abs=1e-6)
    _, length_in, part_number = screw_for_required_length(
        ROLE_EXTERIOR_INSULATION_SCREW, roof.required_screw_length_in(FASTENERS))
    assert (length_in, part_number) == (10.0, "SDWH191000DB")


def test_catlin_bills_wall_and_roof_screws_as_separate_longer_line(catlin_model) -> None:
    """The roof still takes the 10" screw through 6" of foam. The WALL no longer takes one.

    Until 2026-08-23 catlin's walls were the textbook screwed-strip condition: 1/2" furring
    held off the studs through 4" of rigid board, 537 eight-inch SDWS on a 16 x 24 grid. The
    truss wall has no such screw anywhere in it. The outrigger is lap-screwed to a plywood
    tab, the tab to a block, and only the BLOCK is fastened back to the framing — through
    1-1/2" of wood and the sheathing, with no foam in the path, because the foam is sprayed
    around the truss afterwards.

    So the wall line is billed off the resolved BLOCKS rather than off a grid, and this is
    what stops the grid walk from silently re-finding a screwed strip in the stack and
    ordering 537 eight-inch screws for a wall that needs none.
    """
    from typehaus.resolve.framing.truss_wall import girt_block_tier

    rows = [row for row in hardware_takeoff(catlin_model)
            if row["role"] == ROLE_EXTERIOR_INSULATION_SCREW]
    assert not [row for row in rows if row["scope"] == "exterior wall furring"], \
        "a truss wall has no screwed furring strip — see takeoff/fasteners.py"
    roof = next(row for row in rows if row["scope"] == "roof top deck")

    # The roof: 0.625 + 6 + 0.54 = 7.165 in of penetration + 1.5 in of embedment = 8.665 in,
    # so the 8 in SDWS is short and only the 10 in SDWH reaches. An under-length structural
    # screw here is the whole roof hanging on 1 in less thread than it was designed for.
    assert roof["size"] == "10 in" and roof["part_number"] == "SDWH191000DB"
    assert "16 in o.c." in roof["basis"] and "24 in o.c." in roof["basis"]

    # The wall is TWO rows since the catlin truss (2026-08-26), because the two girt tiers
    # land in different things and each is billed at what it actually passes through:
    #   block-1: 1.5 girt + 1.5 block + 0.5 sheathing + 1.5 into the stud       = 5.00 in
    #   block-2: 1.5 girt + 1.5 block           + 1.5 into the inner girt       = 4.50 in
    # Both round up to the same 5 in part, and neither is the 4 in screw the Swinburne pack
    # took — that wall drove through one block, this one drives through a girt as well.
    tiers = {"1": next(r for r in rows if r["scope"] == "girt wall block-1"),
             "2": next(r for r in rows if r["scope"] == "girt wall block-2")}
    for tier, row in tiers.items():
        assert row["size"] == "5 in" and row["part_number"] == "SDWS22500DB"
        assert row["part_number"] != roof["part_number"]
        # ONE screw per block, not two: the girt lying across the block is continuous and
        # screwed at every block along its run, so there is no rotation for a second to
        # resist. And the two tiers are OFFSET half a bay, never through-screwed.
        assert "1 per block" in row["basis"], (tier, row["basis"])
        assert "16 in o.c." in row["basis"]
        assert set(row["by_storey"]) == {"main", "second", "attic"}
        assert row["count"] == sum(row["by_storey"].values())
    assert "into the stud" in tiers["1"]["basis"]
    assert "into the inner girt" in tiers["2"]["basis"]
    assert "8 in off the block-1 line" in tiers["2"]["basis"]

    # Counted off the resolved blocks, not off a grid — exactly one screw per block, per
    # tier, and the two counts differ because the two modules are half a bay apart and so
    # land differently against course ends and rough openings.
    for tier, row in tiers.items():
        blocks = sum(1 for w in catlin_model.walls for m in w.members
                     if m.category == "truss_block"
                     and girt_block_tier(m.child_key) == tier)
        assert row["count"] == blocks > 0, tier
    assert sum(row["count"] for row in tiers.values()) > roof["count"] > 0


# --- hangers -------------------------------------------------------------------------


def test_member_hung_in_a_beams_depth_needs_a_hanger() -> None:
    beam = _member("beam", "beam", (0.0, 0.0), (4.0, 0.0), z0_m=3.0, z1_m=3.3,
                   profile="2-2x10")
    hung = _member("j0", "joist", (2.0, 0.0), (2.0, 3.0), z0_m=3.02, z1_m=3.28)
    model = ResolvedModel(plan=None, floors=[_floor_of([beam, hung])])
    found = hung_connections(model, CONFIG.hanger_detection)
    assert [(item.member_key, item.sloped) for item in found] == [("T:j0", False)]


def test_member_bearing_on_top_of_a_beam_needs_no_hanger() -> None:
    beam = _member("beam", "beam", (0.0, 0.0), (4.0, 0.0), z0_m=3.0, z1_m=3.3,
                   profile="2-2x10")
    bearing = _member("j0", "joist", (2.0, 0.0), (2.0, 3.0), z0_m=3.3, z1_m=3.6)
    model = ResolvedModel(plan=None, floors=[_floor_of([beam, bearing])])
    assert hung_connections(model, CONFIG.hanger_detection) == []


def test_standalone_beam_solid_is_also_a_carrier() -> None:
    solid = ResolvedSolid(uid="B", tag="BM-1", storey="main", category="beam",
                          outline=[(0.0, 0.0), (4.0, 0.0), (4.0, 0.14), (0.0, 0.14)],
                          z0_m=3.0, z1_m=3.3)
    hung = _member("j0", "joist", (2.0, 0.07), (2.0, 3.0), z0_m=3.02, z1_m=3.28)
    model = ResolvedModel(plan=None, floors=[_floor_of([hung])], solids=[solid])
    assert [item.carrier_tag for item in hung_connections(model, CONFIG.hanger_detection)] \
        == ["BM-1"]


def test_catlin_hangs_every_rafter_off_the_ridge_beam(catlin_model) -> None:
    connections = hung_connections(catlin_model, CONFIG.hanger_detection)
    rafters = [item for item in connections if item.carrier_tag.endswith("ridge-beam")]
    ridge_rafters = [member for member in catlin_model.all_members()
                     if member.category == "rafter"]
    # Every resolved rafter frames into the ridge beam's depth — one sloped hanger each.
    assert len(rafters) == len(ridge_rafters) > 0
    assert all(item.sloped for item in rafters)

    row = next(row for row in hardware_takeoff(catlin_model)
               if row["role"] == ROLE_SLOPED_JOIST_HANGER)
    assert row["part_number"] == "LSSR" and row["count"] == len(ridge_rafters)

    # Every catlin floor joist *bears* — on a plate, or on top of a beam — with four
    # exceptions, all flush-framed on purpose and all of which must be billed a hanger each:
    #
    #  - the breezeway deck's joists, so the deck can be 7 1/4" deep instead of 14 1/2" at a
    #    walking surface that has to meet the house threshold;
    #  - the joists over each of the two hall LVLs — BM-S-HALL, which replaced 8'-6" of the
    #    second-storey centre wall, and BM-M-HALL, which replaced 4'-2" of the main-storey
    #    one under it. Both are flush so their storey keeps its 9' ceiling, which is exactly
    #    what makes the joists hang rather than bear;
    #  - the porch deck's joists at their *south* end (2026-08-18), where BM-SG-FRW/FRE
    #    replaced the 16" arched cross-wall. Those two are flush so PT-SG-FCOL can top out at
    #    their soffit and stay clear of the 16"-o.c. joist band — a column reaching the deck
    #    datum cannot miss it. The same joists still bear on BM-SG-BKW/BKE at their north end;
    #  - the four FS-ATTIC joists over BM-S-BATH-E (2026-08-29), which is the same case as
    #    BM-S-HALL one line up. It carries FO-A-HALL's west edge across the 4'-0" hall stub
    #    by the vanity, where the x=10'-0" bearing line has no wall under it and can never
    #    have one — a partition there would seal the hall bath off from the landing. Flush
    #    (`top_elevation=ft(20)`) so the stub keeps its unbroken 9'-0" ceiling, which is
    #    again exactly what makes the joists hang rather than bear.
    #
    # Nothing else may hang.
    breezeway = next(f for f in catlin_model.floors if f.tag == "FS-BW-FLOOR")
    hung_keys = {item.member_key for item in connections}
    breezeway_joists = {f"{m.parent_uid}:{m.child_key}" for m in breezeway.members
                        if m.category == "joist"}
    assert breezeway_joists <= hung_keys, "flush-framed deck joists must be billed hangers"
    # BM-SG-FRW/FRE left this list on 2026-08-29. The porch's front beams were flush-framed
    # — their ``top_elevation`` pinned at the 0' datum with the joists hung into their north
    # face — until dropping them was what put PT-SG-FCOL's top, and PT-SG-BF2 with it, on
    # concrete. Those 18 hangers are 32 derived uplift ties now; the joists bear on top.
    flush_beams = ("BM-S-HALL", "BM-M-HALL", "BM-S-BATH-E")
    flush_beam_keys = {item.member_key for item in connections
                       if item.carrier_tag in flush_beams}
    for beam in flush_beams:
        assert any(item.carrier_tag == beam for item in connections), \
            f"the joists flush-framed into {beam} must hang in it"
    bearing_keys = {f"{member.parent_uid}:{member.child_key}"
                    for floor in catlin_model.floors for member in floor.members
                    if floor.tag != "FS-BW-FLOOR"}
    assert bearing_keys
    assert not (bearing_keys & hung_keys - flush_beam_keys)


# --- sill anchorage ------------------------------------------------------------------


def _sill_return(tag: str, length_m: float) -> ResolvedConstructionReturn:
    return ResolvedConstructionReturn(
        uid=tag, tag="CR-CONC-TO-FRAMED-SILL", storey="main", kind="bearing_plate",
        applies_to="stacking", takeoff_category=CONFIG.sill_plate_takeoff_category,
        material_ref="kdat", element_tags=(), z0_m=0.0, z1_m=0.04, thickness_m=0.14,
        length_m=length_m, lap_m=0.0,
        outline=[(0.0, 0.0), (length_m, 0.0), (length_m, 0.14), (0.0, 0.14)])


def test_mudsill_anchor_pitch_and_minimum_per_run() -> None:
    rules = CONFIG.sill_plate_anchors
    long_run = mudsill_anchor_rows(
        ResolvedModel(plan=None, construction_returns=[_sill_return("A", 40.0 * FT_TO_M)]),
        rules, CONFIG.sill_plate_takeoff_category)
    # 40 ft at 4 ft o.c. = 10 bays, anchored at both ends of every bay line.
    assert long_run[0]["count"] == 11
    assert long_run[0]["part_number"] == "MASA"

    short_run = mudsill_anchor_rows(
        ResolvedModel(plan=None, construction_returns=[_sill_return("B", 3.0 * FT_TO_M)]),
        rules, CONFIG.sill_plate_takeoff_category)
    # Shorter than one pitch, but no plate piece is anchored by fewer than two anchors.
    assert short_run[0]["count"] == rules.minimum_anchors_per_run == 2


def test_catlin_anchors_every_sill_plate_on_concrete(catlin_model) -> None:
    rows = hardware_takeoff(catlin_model)
    sill_runs = [ret for ret in catlin_model.construction_returns
                 if ret.takeoff_category == CONFIG.sill_plate_takeoff_category]
    anchors = next(row for row in rows if row["role"] == ROLE_MUDSILL_ANCHOR)
    holdowns = next(row for row in rows if row["role"] == "embedded_strap_holdown")

    assert sill_runs, "catlin frames walls on concrete, so it must resolve sill plates"
    assert anchors["count"] >= len(sill_runs) * CONFIG.sill_plate_anchors.minimum_anchors_per_run
    # Runs that butt at a corner share one holdown location, so holdowns < 2 per run.
    assert 0 < holdowns["count"] < len(sill_runs) * 2


def test_exterior_door_jambs_are_strapped_to_the_foundation(catlin_model) -> None:
    """The jambs of a main-storey exterior door take their own STHDs.

    ``strap_holdown_rows`` derives holdowns at the *ends* of each sill-plate run, which
    leaves the jamb studs beside a door punched through the middle of a run with no path
    to the concrete. The four authored connectors are that path, and they bill on their
    own ``modeled connector`` row rather than being folded into the derived count — same
    part number, different rule, and the split is what keeps "why 40?" answerable.
    """
    jamb_holdowns = [element
                     for storey in catlin_model.plan.storeys
                     for element in catlin_model.plan.storey_elements(storey.tag)
                     if isinstance(element, Connector)
                     and element.kind is ConnectorKind.HOLD_DOWN
                     and element.size == "STHD"]
    assert {element.tag for element in jamb_holdowns} == {
        "CN-M-HD-ENTRY-E", "CN-M-HD-ENTRY-W", "CN-M-HD-BALC-W", "CN-M-HD-BALC-E"}
    # Each one names the framed wall it straps and the foundation wall it is cast into.
    for element in jamb_holdowns:
        assert len(element.connects) == 2, element.tag
        framed, foundation = element.connects
        assert catlin_model.plan.by_tag(framed) is not None, framed
        assert catlin_model.plan.by_tag(foundation) is not None, foundation

    rows = [row for row in hardware_takeoff(catlin_model)
            if row["role"] == "embedded_strap_holdown"]
    modeled = next(row for row in rows if row["scope"] == "modeled connector")
    derived = next(row for row in rows if row["scope"] == "sill plate on concrete")
    assert modeled["count"] == len(jamb_holdowns)
    assert modeled["part_number"] == derived["part_number"] == "STHD"


# --- knee braces, ties, straps, catalog ----------------------------------------------


def test_each_modeled_knee_brace_takes_two_connectors_one_per_end(catlin_model) -> None:
    """Two KBS1Z per brace the plan models — no per-JOINT multiplier the plan cannot see.

    The rule used to bill a matched pair per braced *joint*, which only holds where a beam
    runs past its post. Every balcony pillar is a beam end, so the pair rule billed twice
    the braces that fit. The multiplier is now a property of the HARDWARE instead: Simpson's
    KBS1Z installation is one connector at each end of the brace, and the F1 the code report
    publishes is measured through that pair, so billing one would order half the connection
    the capacity assumes.

    The part changed on 2026-08-30. It was `APVKB45-6`, Simpson's Outdoor Accents Avant
    decorative knee brace, which has no published allowable load in any code report — IAPMO
    UES ER-102's AP-series index does not list it and ER-280 has no table for it. On catlin
    those braces are the entire lateral system of a freestanding deck at storey height."""
    from typehaus.model.structure import KneeBrace

    braces = [element for storey in catlin_model.plan.storeys
              for element in catlin_model.plan.storey_elements(storey.tag)
              if isinstance(element, KneeBrace)]
    row = knee_brace_rows(catlin_model, CONFIG.knee_braces)[0]
    assert row["part_number"] == "KBS1Z"
    assert CONFIG.knee_braces.braces_per_location == 2
    assert row["count"] == 2 * len(braces)
    assert row["role"] == ROLE_KNEE_BRACE


def test_the_knee_brace_role_serves_a_part_with_a_published_capacity() -> None:
    """The substitution, pinned at the role rather than at the house.

    Any house authoring a knee brace gets whatever this role resolves to. Putting an unrated
    part back on it would silently un-brace every deck in the world that uses it."""
    from typehaus.takeoff.hardware_catalog import hardware_for_role

    item = hardware_for_role(ROLE_KNEE_BRACE)
    assert item.allowable is not None
    assert item.allowable.lateral_f1_lb == 540.0   # ER-280 Table 7, type 2, 45 deg, SPF/HF


def test_the_balcony_is_braced_at_its_four_corners_in_both_directions(catlin_model) -> None:
    """The freestanding balcony's whole lateral system, and the take-off that follows it.

    Four corner pillars x two directions = eight braces. The two centre pillars are
    deliberately unbraced leaning columns — bracing them would push thrust into PT-SG-BR2,
    the one pillar bearing on the porch decking rather than on grouted masonry."""
    from typehaus.model.structure import KneeBrace

    braces = {element.tag: element for storey in catlin_model.plan.storeys
              for element in catlin_model.plan.storey_elements(storey.tag)
              if isinstance(element, KneeBrace)}
    assert set(braces) == {
        "KB-SG-R1-NS", "KB-SG-R1-EW", "KB-SG-R3-NS", "KB-SG-R3-EW",
        "KB-SG-F1-NS", "KB-SG-F1-EW", "KB-SG-F3-NS", "KB-SG-F3-EW",
    }
    assert {b.axis for b in braces.values() if b.tag.endswith("-NS")} == {"y"}
    assert {b.axis for b in braces.values() if b.tag.endswith("-EW")} == {"x"}
    # Every brace names the post it stiffens *and* the member it reaches, so the connector
    # schedule can key the joint. The old records named only the post.
    assert all(len(b.connects) == 2 for b in braces.values())
    # Two KBS1Z per brace, one at each end — see the test above.
    assert knee_brace_rows(catlin_model, CONFIG.knee_braces)[0]["count"] == 16


def test_stud_plate_ties_are_sized_to_the_stud_they_tie(catlin_model) -> None:
    rows = [row for row in hardware_takeoff(catlin_model)
            if row["role"] == "stud_plate_tie"]
    # Every exterior storey frames 2x6 now (CATLIN_EXT_2X4 is deleted), so the tie
    # schedule collapses to the one part sized for the stud it actually ties.
    assert {row["part_number"] for row in rows} == {"SP6"}
    assert {row["size"] for row in rows} == {"2x6"}
    assert all(row["count"] > 0 for row in rows)


def test_coil_strap_is_ordered_by_the_coil(catlin_model) -> None:
    row = next(row for row in hardware_takeoff(catlin_model) if row["role"] == "coil_strap")
    assert row["unit"] == "coil" and row["count"] == row["coils"] >= 1
    assert row["length_ft"] > 0
    assert "straps" in row["basis"]


def test_pipe_fixings_bill_by_size_not_as_a_bare_family(catlin_model) -> None:
    """Every fixing holding a round pipe bills the sized part, on its own line.

    The bug this pins is a silent one. ``hardware_by_model`` falls back to a family-prefix
    match, so an authored size suffix used to collapse into the bare family and print as it
    — a BOM that looked complete, priced fine, and would have arrived on site as brackets
    with nothing to hold the leaders in.

    The part changed on 2026-08-26 and the rule did not. The house walls are an
    exposed-fastener panel now, so the leaders and the vent riser ride through-panel straps
    rather than CanDuit rings on seam clamps; the ring is still catalogued and still serves
    ROLE_PIPE_CLAMP for a seam-clad house (see the role test below), which is why this asks
    the model what it contains rather than asserting a part number the cladding decides.
    """
    rows = [row for row in hardware_takeoff(catlin_model)
            if row["role"] == "through_panel_pipe_strap"]
    assert rows, "the roof leaders and the vent riser are held by pipe straps"
    assert all(row["description"].startswith("316 stainless two-hole pipe strap")
               for row in rows)
    # Selected on the pipe's OD, so the size suffix is the part number and must reach the BOM.
    by_part = {row["part_number"]: row["count"] for row in rows}
    # Six #13, not eight, since 2026-08-29: the roof leaders lost their top strap at each
    # end (CN-A-LEADER-W4/E4 at 23'-0") when the eave came down to 20'-11 3/8" and the knee
    # walls they were fixed to became rafter plates. Three per leader at 5'/11'/17' still
    # holds the ~6' spacing on a leader that is 4'-11" shorter.
    assert by_part == {"SS316-STANDOFF-STRAP #11": 3, "SS316-STANDOFF-STRAP #13": 6}
    # And the strap reaches the wall by itself: nothing is carried under it.
    assert not [row for row in hardware_takeoff(catlin_model)
                if row["scope"] == "carried-mount" and "strap" in row["basis"]]


def test_a_part_that_mounts_on_another_also_bills_that_carrier(catlin_model) -> None:
    """ColorGard is a RAIL: the seam clamps under it are what reach the roof.

    Same part number, its own row: the carrier line's ``scope`` marks it as implied by a
    modeled rail rather than authored directly, so the count stays auditable back to the
    plan instead of being folded into the directly-modeled clamps' total. In the 3D view a
    rail and the clamps it mounts on stay one modeled ``Connector`` — this split only
    affects how the BOM itemizes the same hardware, not the geometry.

    The CanDuit ring exercised this rule too, until the 2026-08-26 cladding swap took the
    house's pipe fixings off the seam. ColorGard is now the only ``requires_role`` part the
    model contains, and it pins the rule the same way.

    That swap also emptied the *modeled* side of the split: an S-5! closes on a seam, and the
    only seam left in the house is the roof's, where nothing is authored as a bare clamp. So
    the carried row is now the whole S-5! story, and this test asserts that rather than
    comparing two rows — see test_solar.py for the same fact from the count's side.
    """
    rows = hardware_takeoff(catlin_model)
    rails = sum(row["count"] for row in rows if row["role"] == "snow_retention")
    seam = [row for row in rows if row["role"] == "standing_seam_clamp"]
    assert not [row for row in seam if row["scope"] == "modeled connector"], \
        "no bare seam clamp is authored any more; every S-5! is implied by the rail"
    # One carried-mount row per *requiring* part, so two parts riding the same clamp never
    # collapse into one row with a right count and a wrong reason. Pick by basis text.
    mounts = next(row for row in seam
                  if row["scope"] == "carried-mount" and "ColorGard" in row["basis"])
    assert mounts["part_number"] == "S-5!"
    assert mounts["count"] == rails > 0
    assert "required to mount a modeled S-5! ColorGard snow-retention rail" in mounts["basis"]


def test_every_hardware_row_is_a_purchasable_catalogued_line(catlin_model) -> None:
    for row in hardware_takeoff(catlin_model):
        assert row["count"] > 0
        assert row["part_number"], row
        assert row["source"], f"{row['part_number']} must cite a manufacturer source"
        assert row["basis"], f"{row['part_number']} must state the rule behind its count"


def test_library_hardware_tags_are_stable_and_sourced() -> None:
    catalog = structural_hardware_catalog()
    tags = [item.tag for item in catalog]
    assert len(tags) == len(set(tags))
    assert all(item.source and item.manufacturer and item.model for item in catalog)


# --- exposed-fastener panel screws (2026-08-26) --------------------------------------


PANEL = CONFIG.exposed_fastener_cladding


class _FakeMaterial:
    def __init__(self, exposed_fastener: bool) -> None:
        self.exposed_fastener = exposed_fastener


class _FakeLibrary:
    def __init__(self, exposed: dict) -> None:
        self._exposed = exposed

    def material(self, ref):
        if ref not in self._exposed:
            return None
        return _FakeMaterial(self._exposed[ref])


class _FakePlan:
    def __init__(self, exposed: dict) -> None:
        self.library = _FakeLibrary(exposed)


class _FakeLayer:
    def __init__(self, function: str, material_ref: str) -> None:
        self.function, self.material_ref = function, material_ref


class _FakeWall:
    """The three things the screw rule reads off a wall: its run, its rise, its cladding."""

    def __init__(self, run_ft: float, rise_ft: float, cladding_ref: str,
                 storey: str = "main") -> None:
        self.storey = storey
        self.axis = ((0.0, 0.0), (run_ft * FT_TO_M, 0.0))
        self.z0_m, self.z1_m = 0.0, rise_ft * FT_TO_M
        self.top_z0_m = self.top_z1_m = None
        self._layers = (_FakeLayer("sheathing", "zip"),
                        _FakeLayer("cladding", cladding_ref))

    def depth_layers(self):
        return self._layers


def _panel_rows(walls, exposed: dict) -> list:
    model = ResolvedModel(plan=_FakePlan(exposed))
    model.walls.extend(walls)
    return exposed_fastener_cladding_screw_rows(model, PANEL)


def test_panel_screws_are_a_rib_by_support_grid_plus_a_sidelap_line() -> None:
    """A 36 ft x 24 ft wall, worked by hand so the row can be re-derived without the model.

    FIELD — screws land in the flats between 12 in major ribs, at every 24 in girt course.
    36 ft = 36 flats + 1 = 37 across; 24 ft = 12 courses + 1 = 13 up; 37 x 13 = 481.

    SIDELAP — one stitch line per 36 in of panel coverage. 36 ft of run is 12 panels, which
    lap at ELEVEN joints, not twelve — the end of the last panel is a corner, not a lap —
    each stitched at 24 in o.c. up 24 ft = 13 screws. 11 x 13 = 143.
    """
    rows = _panel_rows([_FakeWall(36.0, 24.0, "pbr")], {"pbr": True})
    by_scope = {row["scope"]: row for row in rows}
    assert by_scope["exposed-fastener panel field"]["count"] == 37 * 13 == 481
    assert by_scope["exposed-fastener panel sidelap"]["count"] == 11 * 13 == 143


def test_a_partial_last_panel_still_makes_a_joint() -> None:
    """4.5 panels of run is 5 panels and 4 laps: the rip is lapped like any other."""
    rows = _panel_rows([_FakeWall(13.5, 8.0, "pbr")], {"pbr": True})
    sidelap = next(r for r in rows if r["scope"].endswith("sidelap"))
    assert sidelap["count"] == 4 * 5


def test_a_run_one_panel_wide_has_a_field_but_no_sidelap() -> None:
    """The joint count floors. A single 36 in panel laps nothing, and billing it a stitch
    line would put screws down a seam that does not exist."""
    rows = _panel_rows([_FakeWall(3.0, 8.0, "pbr")], {"pbr": True})
    assert {row["scope"] for row in rows} == {"exposed-fastener panel field"}


def test_a_clipped_or_seamed_panel_bills_no_screws_at_all() -> None:
    """**The double-billing guard.** A concealed-fastener panel's fixings are already inside
    its $/SF cladding rate, so a wall whose material does not declare ``exposed_fastener``
    must emit NOTHING here — not a zero row, no row. An unknown material is the same case:
    absence of the declaration is the answer, never a default to True."""
    assert _panel_rows([_FakeWall(36.0, 24.0, "snaplock")], {"snaplock": False}) == []
    assert _panel_rows([_FakeWall(36.0, 24.0, "mystery")], {}) == []


def test_only_the_outermost_cladding_layer_decides() -> None:
    """A wall carrying an inboard cladding layer under the face panel is graded on the face.

    The gate reads the OUTERMOST cladding layer, because that is the one a screw is driven
    through. Reading any cladding layer would let a buried one opt a wall in.
    """
    wall = _FakeWall(36.0, 24.0, "snaplock")
    wall._layers = (_FakeLayer("cladding", "pbr"), _FakeLayer("cladding", "snaplock"))
    assert _panel_rows([wall], {"pbr": True, "snaplock": False}) == []


def test_panel_screw_length_takes_the_full_nailer_and_no_more() -> None:
    """1-1/2 in through a 0.02 in panel into the flat 1.5 in girt = ~1.4 in of embedment.

    Longer is not better: a screw that reached the WRB would put a second penetration in a
    plane meant to stay unbroken, which is why the rule asks for panel + nailer and nothing
    beyond it.
    """
    required_in = PANEL.panel_thickness_in + PANEL.support_embedment_in
    item, length_in, part_number = screw_for_required_length(
        ROLE_EXPOSED_FASTENER_PANEL_SCREW, required_in)
    assert (length_in, part_number) == (1.5, "T09150HWAM")
    assert item.manufacturer == "Simpson Strong-Tie"
    assert "316" in item.source and "EPDM" in item.source


def test_the_canduit_ring_is_still_the_one_part_serving_the_pipe_clamp_role() -> None:
    """The new strap role must not orphan or shadow the part kept for the swap back.

    ``hardware_for_role`` raises unless a role holds exactly one product, so adding the
    strap as a second ROLE_PIPE_CLAMP item would have broken the ring for every house — and
    the ring is what a reverted (or seam-clad) house orders. Two roles, two parts, keyed on
    how each one reaches the building.
    """
    ring = hardware_for_role(ROLE_PIPE_CLAMP)
    strap = hardware_for_role(ROLE_THROUGH_PANEL_PIPE_STRAP)
    assert ring.model == "S-5! CanDuit" and ring.requires_role is not None
    # The strap penetrates the panel itself, so unlike the ring it carries nothing under it.
    assert strap.requires_role is None
    assert ring.tag != strap.tag


def test_catlin_bills_panel_screws_on_the_house_walls_only(catlin_model) -> None:
    """The house is PBR; the garage stays nail strip, and nail strip's fixings are in its rate.

    This is the same guard as the unit test above, asserted against the real model: if the
    garage's ``standing-seam-nailstrip-26`` ever leaked into this rule it would bill ~600
    screws that the garage's $/SF row has already paid for.
    """
    rows = [row for row in hardware_takeoff(catlin_model)
            if row["role"] == ROLE_EXPOSED_FASTENER_PANEL_SCREW]
    assert {row["scope"] for row in rows} == {
        "exposed-fastener panel field", "exposed-fastener panel sidelap"}
    for row in rows:
        assert row["part_number"] == "T09150HWAM" and row["size"] == "1.5 in"
        assert row["count"] == sum(row["by_storey"].values()) > 0
        # The garage is one storey and is not PBR, so it must not appear on either row.
        assert "garage" not in row["by_storey"], row["by_storey"]
    field = next(r for r in rows if r["scope"].endswith("field"))
    sidelap = next(r for r in rows if r["scope"].endswith("sidelap"))
    assert "12 in o.c." in field["basis"] and "24 in o.c." in field["basis"]
    assert "openings not deducted" in field["basis"]
    assert "36 in panel coverage" in sidelap["basis"]
    assert field["count"] > sidelap["count"] > 0
