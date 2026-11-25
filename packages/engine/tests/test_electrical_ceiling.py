"""A recessed can's housing must sit in a clear joist bay."""

from dataclasses import replace

from shapely.affinity import translate
from shapely.geometry import Polygon

from typehaus.checks import run_from_model
from typehaus.model import inch

CHECK = "electrical.ceiling_can_framing"
CAN = "ED-B-GYM-CAN1"  # mid-bay under FS-M-EAST


def _result(model, offset_m: float) -> tuple[str, str]:
    can = next(item for item in model.canvas_objects if item.tag == CAN)
    moved = replace(can, position=(can.position[0], can.position[1] + offset_m),
                    body_z1_m=can.body_z0_m + inch(6).meters,
                    footprint=tuple(translate(Polygon(can.footprint), yoff=offset_m)
                                    .exterior.coords)[:-1])
    copy = replace(model, canvas_objects=[moved if item.tag == CAN else item
                                         for item in model.canvas_objects])
    finding = next(f for f in run_from_model(copy, [], only=CHECK).findings
                   if CAN in f.element_tags)
    return finding.result.value, finding.message


def test_ceiling_can_in_a_bay_passes_and_on_a_joist_fails(catlin_model_ro):
    assert _result(catlin_model_ro, 0.0)[0] == "pass"
    result, message = _result(catlin_model_ro, inch(8).meters)
    assert result == "fail" and "joist" in message


def test_can_over_a_well_hangs_from_the_stair_above_and_clears_its_landing(catlin_model_ro):
    """ED-B-STAIR-LAND-CAN1 serves ST-B2M: past that stair's own landing lid it recesses into
    ST-M2S's landing underside, and is graded against that landing's joists."""
    stair = next(s for s in catlin_model_ro.stairs if s.tag == "ST-M2S")
    board = next(b for b in stair.undersides if b.role == "landing")
    can = next(o for o in catlin_model_ro.canvas_objects if o.tag == "ED-B-STAIR-LAND-CAN1")
    assert abs(can.z_m - board.z_start_m) < 1e-6
    finding = next(f for f in run_from_model(catlin_model_ro, [], only=CHECK).findings
                   if can.tag in f.element_tags)
    assert finding.result.value == "pass" and "ST-M2S" in finding.message
