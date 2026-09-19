"""Fitted bookcase geometry stays board-accurate in every consumer contract."""

from __future__ import annotations

import pytest

from typehaus.model import (
    Building,
    BuiltInBookcaseBay,
    BuiltInBookcaseSpec,
    FurnitureType,
    Project,
    Site,
    ft,
    inch,
    m,
)
from typehaus.model.built_in_bookcase import built_in_bookcase_dimensions, built_in_bookcase_parts
from typehaus.model.canvas import canvas_object_types
from typehaus.model.plan import Library, PlanModel


@pytest.fixture
def stepped_spec() -> BuiltInBookcaseSpec:
    return BuiltInBookcaseSpec(
        bays=(
            BuiltInBookcaseBay(clear_width=inch(31.25), height=ft(5), horizontal_board_count=5),
            BuiltInBookcaseBay(clear_width=inch(31.25), height=ft(3.5), horizontal_board_count=4),
            BuiltInBookcaseBay(clear_width=inch(31.25), height=ft(2.5), horizontal_board_count=3),
        ),
        shelf_depth=inch(9.875), horizontal_board_thickness=inch(1.5),
        divider_thickness=inch(.75), back_thickness=inch(.75),
    )


def test_stepped_bookcase_generates_exact_back_divider_and_board_counts(stepped_spec) -> None:
    parts = built_in_bookcase_parts(stepped_spec)
    backs = [part for part in parts if part.role == "back"]
    dividers = [part for part in parts if part.role == "divider"]
    boards = [part for part in parts if part.role == "horizontal_board"]

    assert len(backs) == 3
    assert len(dividers) == 4
    assert len(boards) == 12
    assert [part.size[2] * 12 / .3048 for part in backs] == pytest.approx([60, 42, 30])
    assert [part.size[2] * 12 / .3048 for part in dividers] == pytest.approx([60, 60, 42, 30])
    assert [part.z0_m * 12 / .3048 for part in boards if part.bay_index == 0][0] == pytest.approx(0)
    top_board = [part for part in boards if part.bay_index == 0][-1]
    assert top_board.z1_m * 12 / .3048 == pytest.approx(60)


def test_bookcase_dimensions_and_browser_parts_share_one_geometry_source(stepped_spec) -> None:
    width, depth, height = built_in_bookcase_dimensions(stepped_spec)
    assert tuple(value * 12 / .3048 for value in (width, depth, height)) == pytest.approx(
        (96.75, 10.625, 60))
    furniture = FurnitureType(tag="F-BUILT-IN", name="Stepped built-in bookcase",
                              footprint=(inch(96.75), inch(10.625)), height=ft(5),
                              built_in_bookcase=stepped_spec)
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        library=Library(furniture_types=(furniture,)),
    )
    record = canvas_object_types(plan)[0]
    assert len(record["model_parts"]) == 19
    assert len(record["plan_strokes"]) == 7
    assert {part["role"] for part in record["model_parts"]} == {
        "back", "divider", "horizontal_board"}
