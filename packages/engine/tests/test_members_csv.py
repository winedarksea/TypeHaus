"""The per-member CSV: the table a PE retypes into ForteWEB or Enercalc."""

from __future__ import annotations

import csv
import dataclasses

import pytest
from analytical_fixtures import DEAD_N_M, WIND_N, portal_frame

from typehaus.analytical.graph import Fixity, Support
from typehaus.emit.analytical.members_csv import BASE_COLUMNS, write_members_csv

#: 2,000 N/m is 137.04 plf. Written out rather than converted, so a broken conversion
#: constant cannot make the test agree with itself.
DEAD_PLF = 137.04


@pytest.fixture(scope="module")
def rows(tmp_path_factory):
    path = write_members_csv(portal_frame(), tmp_path_factory.mktemp("csv") / "members.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle)), path


def test_one_row_per_member_in_id_order(rows):
    table, _ = rows
    assert [row["member_id"] for row in table] == ["BM-1", "PT-E", "PT-W"]


def test_columns_are_the_base_set_plus_two_per_case(rows):
    table, path = rows
    header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert tuple(header[: len(BASE_COLUMNS)]) == BASE_COLUMNS
    assert header[len(BASE_COLUMNS):] == ["dead_plf", "dead_point_lb",
                                          "wind_plf", "wind_point_lb"]
    assert set(table[0]) == set(header)


def test_beam_carries_the_dead_line_load_in_plf(rows):
    table, _ = rows
    beam = next(row for row in table if row["member_id"] == "BM-1")
    assert float(beam["dead_plf"]) == pytest.approx(-DEAD_PLF, abs=0.1)
    assert DEAD_N_M == 2000.0            # the fixture is the one this number came from
    assert float(beam["wind_plf"]) == 0.0
    # Both column tops carry the wind push and the beam lands on both of them.
    assert float(beam["wind_point_lb"]) == pytest.approx(2 * WIND_N * 0.2248, abs=0.5)


def test_releases_and_supports_are_marked(rows):
    table, _ = rows
    beam = next(row for row in table if row["member_id"] == "BM-1")
    assert beam["release_i"] == "moment released"
    assert beam["release_j"] == "moment released"
    assert beam["support_i"] == "" and beam["support_j"] == ""

    column = next(row for row in table if row["member_id"] == "PT-W")
    assert column["release_i"] == "continuous"
    assert column["support_i"] == "fixed"     # the base
    assert column["support_j"] == ""          # the top bears nothing


def test_section_and_geometry_columns(rows):
    table, _ = rows
    beam = next(row for row in table if row["member_id"] == "BM-1")
    assert beam["section"] == "3.5X11.875_GLULAM"
    assert beam["shape"] == "rect"
    assert float(beam["width_in"]) == pytest.approx(3.5)
    assert float(beam["depth_in"]) == pytest.approx(11.875)
    assert float(beam["length_ft"]) == pytest.approx(4.0 / 0.3048, rel=1e-4)
    assert float(beam["n1_z_ft"]) == pytest.approx(3.0 / 0.3048, rel=1e-4)
    assert beam["e_basis"].startswith("assumed:")

    column = next(row for row in table if row["member_id"] == "PT-E")
    assert column["section"] == "12_RD_CONCRETE"
    assert column["item_ids"] == "deck_post/PT-E"


def test_two_writes_are_byte_identical(tmp_path):
    model = portal_frame()
    first = write_members_csv(model, tmp_path / "a.csv").read_bytes()
    second = write_members_csv(model, tmp_path / "b.csv").read_bytes()
    assert first == second
    assert b"\r" not in first            # \n only, and no BOM
    assert not first.startswith(b"\xef\xbb\xbf")


def _rolled_pin(model):
    """The fixture with its two bases re-authored as beam-on-wall pins that cannot roll."""
    return dataclasses.replace(model, supports=tuple(
        Support(s.node, Fixity.PINNED, "bears on a wall", item_id=s.item_id,
                element_tag=s.element_tag, rotations=(True, False, False))
        for s in model.supports))


def test_support_cells_name_a_pinned_support_that_also_restrains_a_rotation(tmp_path):
    path = write_members_csv(_rolled_pin(portal_frame()), tmp_path / "m.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        table = list(csv.DictReader(handle))
    column = next(row for row in table if row["member_id"] == "PT-W")
    assert column["support_i"] == "pinned+RX"
    assert column["support_j"] == ""
