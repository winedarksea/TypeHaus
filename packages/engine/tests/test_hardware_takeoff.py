"""Hardware quantities in the BOM — screws, hangers, anchors, ties, braces, straps.

Every count must be *derived*: the unit tests pin the rules on synthetic geometry, and the
catlin cases assert the rule fired on the real model rather than a memorised number.
"""

from __future__ import annotations

import pytest

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
    exterior_insulation_fastening,
    fastener_grid_count,
)
from typehaus.takeoff.hangers import hung_connections
from typehaus.takeoff.hardware_catalog import (
    ROLE_EXTERIOR_INSULATION_SCREW,
    ROLE_KNEE_BRACE,
    ROLE_MUDSILL_ANCHOR,
    ROLE_SLOPED_JOIST_HANGER,
    screw_for_required_length,
    structural_hardware_catalog,
)
from typehaus.takeoff.hardware_config import (
    DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG,
)
from typehaus.takeoff.hardware_config import FT_TO_M, IN_TO_M

FASTENERS = CONFIG.exterior_insulation_fasteners
STRIP_SPACING_M = FASTENERS.strip_spacing_in * IN_TO_M
FASTENER_PITCH_M = FASTENERS.fastener_pitch_along_strip_in * IN_TO_M

# The catlin exterior wall stack, interior→exterior (function, thickness_m, name).
_CATLIN_EXT_STACK = [
    ("finish", 0.625 * IN_TO_M, "gwb-int"),
    ("structure", 5.5 * IN_TO_M, "stud"),
    ("sheathing", 0.5 * IN_TO_M, "sheathing"),
    ("membrane", 0.02 * IN_TO_M, "wrb"),
    ("insulation", 2.0 * IN_TO_M, "polyiso"),
    ("insulation", 2.0 * IN_TO_M, "eps"),
    ("furring", 0.5 * IN_TO_M, "furring"),
    ("cladding", 0.5 * IN_TO_M, "cladding"),
]
# A rainscreen batten straight over sheathing: nailed, not screwed through insulation.
_RAINSCREEN_OVER_SHEATHING_STACK = [
    ("structure", 5.5 * IN_TO_M, "stud"),
    ("sheathing", 1.5 * IN_TO_M, "zip-r"),
    ("furring", 0.375 * IN_TO_M, "rainscreen"),
    ("cladding", 0.5 * IN_TO_M, "cladding"),
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


def test_catlin_bills_wall_and_roof_screws_as_separate_longer_line(catlin_model) -> None:
    rows = [row for row in hardware_takeoff(catlin_model)
            if row["role"] == ROLE_EXTERIOR_INSULATION_SCREW]
    wall = next(row for row in rows if row["scope"] == "exterior wall furring")
    roof = next(row for row in rows if row["scope"] == "roof battens")

    # Same grid, longer screw: the roof carries 6 in of foam to the wall's 4 in.
    assert wall["size"] == "8 in" and roof["size"] == "10 in"
    assert wall["part_number"] != roof["part_number"]
    assert "16 in o.c." in wall["basis"] and "24 in o.c." in wall["basis"]
    assert "16 in o.c." in roof["basis"] and "24 in o.c." in roof["basis"]

    # Counted across every floor that has a furred-and-foamed wall, not just the first.
    assert set(wall["by_storey"]) == {"main", "second", "attic"}
    assert wall["count"] == sum(wall["by_storey"].values())
    assert wall["count"] > roof["count"] > 0


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

    # Catlin's floor joists all *bear* — on a plate, or on top of the porch/balcony beams —
    # so none of them may be billed a hanger.
    floor_member_keys = {f"{member.parent_uid}:{member.child_key}"
                         for floor in catlin_model.floors for member in floor.members}
    assert floor_member_keys
    assert not (floor_member_keys & {item.member_key for item in connections})


# --- sill anchorage ------------------------------------------------------------------


def _sill_return(tag: str, length_m: float) -> ResolvedConstructionReturn:
    return ResolvedConstructionReturn(
        uid=tag, tag="CR-CONC-TO-FRAMED-SILL", storey="main", kind="bearing_plate",
        applies_to="stacking", takeoff_category=CONFIG.sill_plate_takeoff_category,
        material_ref="spf", element_tags=(), z0_m=0.0, z1_m=0.04, thickness_m=0.14,
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


# --- knee braces, ties, straps, catalog ----------------------------------------------


def test_knee_braces_come_in_pairs_per_modeled_location(catlin_model) -> None:
    from typehaus.model.enums import ConnectorKind
    from typehaus.model.structure import Connector

    locations = [element for storey in catlin_model.plan.storeys
                 for element in catlin_model.plan.storey_elements(storey.tag)
                 if isinstance(element, Connector)
                 and element.kind is ConnectorKind.KNEEBRACE]
    row = knee_brace_rows(catlin_model, CONFIG.knee_braces)[0]
    assert row["part_number"] == "APVKB45-6"
    assert CONFIG.knee_braces.braces_per_location == 2
    assert row["count"] == 2 * len(locations)
    assert row["role"] == ROLE_KNEE_BRACE


def test_stud_plate_ties_are_sized_to_the_stud_they_tie(catlin_model) -> None:
    rows = [row for row in hardware_takeoff(catlin_model)
            if row["role"] == "stud_plate_tie"]
    assert {row["part_number"] for row in rows} == {"SP4", "SP6"}
    assert {row["size"] for row in rows} == {"2x4", "2x6"}
    assert all(row["count"] > 0 for row in rows)


def test_coil_strap_is_ordered_by_the_coil(catlin_model) -> None:
    row = next(row for row in hardware_takeoff(catlin_model) if row["role"] == "coil_strap")
    assert row["unit"] == "coil" and row["count"] == row["coils"] >= 1
    assert row["length_ft"] > 0
    assert "straps" in row["basis"]


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
