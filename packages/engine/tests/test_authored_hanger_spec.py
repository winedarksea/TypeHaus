"""An authored JOIST_HANGER naming (beam, FloorSystem) names the part; the count stays derived."""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import hardware_by_model
from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG
from typehaus.joints import derived_joints
from typehaus.joints.authored import authored_hanger_item
from typehaus.joints.hung import hung_connections
from typehaus.model.structure import Connector
from typehaus.takeoff.hardware import hardware_takeoff

_SPECS = {("BM-M-HALL", "FS-S-EAST"): "IUS2.56/11.88",
          ("BM-M-HALL", "FS-S-WEST"): "THA422",
          ("BM-S-HALL", "FS-ATTIC"): "IUS2.56/11.88",
          ("BM-S-BATH-E", "FS-ATTIC"): "IUS2.56/11.88",
          ("BM-SG-LDGW", "FS-SG-PORCH"): "LUS210SS",
          ("BM-SG-LDGE", "FS-SG-PORCH"): "LUS210SS"}


def _takes_the_spec(connection) -> bool:
    spec = _SPECS.get((connection.carrier_tag, connection.member_floor))
    return spec is None or (authored_hanger_item(spec, connection.member_profile)
                            is hardware_by_model(spec))


def test_every_hung_end_of_a_spec_joint_takes_the_authored_part(catlin_model_ro) -> None:
    """Every end the part fits; a line built up past it (the daybed's 3-ply porch lines)
    takes the part catalogued for its ply count, and is counted in the next test."""
    hung = Counter((c.carrier_tag, c.member_floor)
                   for c in hung_connections(catlin_model_ro, CONFIG.hanger_detection)
                   if _takes_the_spec(c))
    for pair, part in _SPECS.items():
        expected = hung[pair]
        assert expected > 0, pair
        rows = [row for row in hardware_takeoff(catlin_model_ro, CONFIG)
                if row["part_number"] == part and pair[0] in str(row.get("basis", ""))]
        assert all(row["scope"] == "hung framing" for row in rows), "the spec billed itself"
        assert sum(row["count"] for row in rows) == expected, pair
        joints = [j for j in derived_joints(catlin_model_ro, CONFIG)
                  if j.part == part and pair[0] in j.members]
        assert len(joints) == expected, pair


def test_a_built_up_line_takes_the_part_for_its_ply_count(catlin_model_ro) -> None:
    ends = [c for c in hung_connections(catlin_model_ro, CONFIG.hanger_detection)
            if c.member_floor == "FS-SG-PORCH" and c.member_profile.startswith("3-")]
    assert len(ends) == 4
    assert {authored_hanger_item("LUS210SS", c.member_profile).model for c in ends} == {
        "LUS210-3Z"}
    assert authored_hanger_item("LUS210SS", "2x12:kdat").model == "LUS210SS"


def test_spec_connectors_draw_no_marker(catlin_model_ro) -> None:
    specs = [e for e in catlin_model_ro.plan.all_elements()
             if isinstance(e, Connector) and e.hanger_spec_pair(catlin_model_ro.plan)]
    assert {e.hanger_spec_pair(catlin_model_ro.plan) for e in specs} == set(_SPECS)
    tags = {e.tag for e in specs}
    assert not [s for s in catlin_model_ro.solids if s.tag in tags]
