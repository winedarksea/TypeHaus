"""An authored JOIST_HANGER naming (beam, FloorSystem) names the part; the count stays derived."""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG
from typehaus.joints import derived_joints
from typehaus.joints.hung import hung_connections
from typehaus.model.structure import Connector
from typehaus.takeoff.hardware import hardware_takeoff

_SPECS = {("BM-M-HALL", "FS-S-EAST"): "IUS2.56/11.88",
          ("BM-M-HALL", "FS-S-WEST"): "THA422",
          ("BM-S-HALL", "FS-ATTIC"): "IUS2.56/11.88",
          ("BM-S-BATH-E", "FS-ATTIC"): "IUS2.56/11.88",
          ("BM-SG-LDGW", "FS-SG-PORCH"): "LUS210SS",
          ("BM-SG-LDGE", "FS-SG-PORCH"): "LUS210SS"}


def test_every_hung_end_of_a_spec_joint_takes_the_authored_part(catlin_model_ro) -> None:
    hung = Counter((c.carrier_tag, c.member_floor)
                   for c in hung_connections(catlin_model_ro, CONFIG.hanger_detection))
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


def test_spec_connectors_draw_no_marker(catlin_model_ro) -> None:
    specs = [e for e in catlin_model_ro.plan.all_elements()
             if isinstance(e, Connector) and e.hanger_spec_pair(catlin_model_ro.plan)]
    assert {e.hanger_spec_pair(catlin_model_ro.plan) for e in specs} == set(_SPECS)
    tags = {e.tag for e in specs}
    assert not [s for s in catlin_model_ro.solids if s.tag in tags]
