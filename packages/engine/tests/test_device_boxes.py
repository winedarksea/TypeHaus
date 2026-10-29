"""Device boxes, derived NM sleeves and raceway parts (decision #93).

Box mounting off the host face, the NEC 314.16(B) fill oracle
(``houses/catlin/notes/basement_surface_wiring.md`` §Box fill), the drop's geometry and
its skip rule, and the strap/coupling/conductor counts on known runs.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.electrical_boxes import required_volume_in3
from typehaus.quantities import M_PER_IN
from typehaus.resolve.conduit_fittings import conduit_parts, couplings_for, straps_for
from typehaus.resolve.pipe_sections import raceway_outside_diameter_m
from typehaus.takeoff.raceways import _named_rows, conductor_takeoff


def _box(model, tag):
    return next(box for box in model.device_boxes if box.device_tag == tag)


def test_mounting_follows_the_host_face(catlin_model_ro):
    gym = _box(catlin_model_ro, "ED-B-GYM-RC5")  # bare basement concrete
    assert (gym.mounting, gym.box_product) == ("surface", "PROD-RACO-232")
    assert gym.projection_m == pytest.approx((2.125 + 0.5) * M_PER_IN)
    stat = _box(catlin_model_ro, "ED-M-BATH2-FH-STAT")  # stud wall a floor-heat lead reaches
    assert stat.mounting == "flush_raceway" and stat.depth_m <= stat.cavity_m
    quad = _box(catlin_model_ro, "ED-B-WORKSHOP-RC2")
    assert (quad.mounting, quad.gangs, quad.cover_product) == ("surface", 2, "PROD-RACO-809C")
    # The device stands on the cover face, and its footprint carries the box to the wall.
    device = next(o for o in catlin_model_ro.canvas_objects if o.tag == "ED-B-GYM-RC5")
    reach = [(x - gym.face_point[0]) * gym.normal[0] + (y - gym.face_point[1]) * gym.normal[1]
             for x, y in device.footprint]
    assert min(reach) == pytest.approx(0.0, abs=1e-6)


def test_box_fill_oracle():
    # RC2 quad, surface 2-gang, through-fed 12 AWG: 2x2 + 2x2 + 1 = 9 x 2.25 = 20.25 in3.
    assert required_volume_in3(12, 1, False, 2) == pytest.approx(20.25)
    # A 15 A switch in a flush 1-gang, through-fed 14 AWG: 2x2 + 2 + 1 = 7 x 2.0 = 14.0 in3.
    assert required_volume_in3(14, 1, False, 1) == pytest.approx(14.0)
    # RC1, 2-pole with neutral, end-fed: 3 + 2x2 + 1 = 8 x 2.25 = 18.0 in3.
    assert required_volume_in3(12, 2, True, 2, cables=1) == pytest.approx(18.0)


def test_drop_rises_on_the_face_and_skips_authored_feeds(catlin_model_ro):
    runs = {run.tag: run for run in catlin_model_ro.conduits}
    box = _box(catlin_model_ro, "ED-B-GYM-RC5")
    drop = runs["ED-B-GYM-RC5-DROP"]
    half_od = raceway_outside_diameter_m(drop.trade_size_m, "emt") / 2
    (x0, y0), (x1, y1) = drop.path
    assert (x0, y0) == pytest.approx((x1, y1))
    assert (x0 - box.face_point[0]) * box.normal[0] + (y0 - box.face_point[1]) * box.normal[1] \
        == pytest.approx(half_od)
    assert drop.z_m[0] == pytest.approx(box.z1_m) and drop.z_m[1] > drop.z_m[0]
    assert drop.derived == "nm_sleeve" and drop.material == "emt"
    # An authored ConduitRun reaches these, so no sleeve is derived.
    assert "ED-B-WORKSHOP-RC1-DROP" not in runs and "ED-B-PLAY-N-RC1-DROP" not in runs


def test_strap_and_coupling_counts():
    # One strap reaches both ends of a run up to 6 ft (358.30(A)).
    assert [straps_for(ft, "emt") for ft in (2, 6, 7, 16, 17)] == [1, 1, 2, 2, 3]
    assert straps_for(10, "ent") == 3  # 3 ft spacing
    assert [couplings_for(ft, "emt") for ft in (9, 10, 25)] == [0, 0, 2]
    assert couplings_for(40, "ent") == 0  # a coil


def test_parts_and_conductors_on_known_runs(catlin_model_ro):
    parts = {(p.run_tag, p.kind): p.count for p in conduit_parts(catlin_model_ro)}
    assert parts[("ED-B-GYM-RC5-DROP", "offset_connector")] == 1
    assert parts[("ED-B-GYM-RC5-DROP", "bushing")] == 1
    assert parts[("CD-B-WORKSHOP", "connector")] == 2
    assert parts[("CD-B-PLAY-SPARE", "pull_box")] == 2
    assert parts[("FH-M-BATH2-SENSOR", "end_cap")] == 1
    # Two runs meeting in a named box are two raceways, not one chained through a coupling.
    assert parts[("CD-B-PLAY-SPARE", "connector")] == 6  # 3 sections, 2 ends each
    # Trunk -> bench box -> RC1 is one pull of CKT-WORKSHOP-240: one 10 ft make-up, not two.
    runs = {r.tag: r for r in catlin_model_ro.conduits}
    pull_ft = (runs["CD-B-WORKSHOP"].length_m + runs["CD-B-WORKSHOP-RC1"].length_m) / 0.3048
    named = _named_rows(catlin_model_ro, [runs["CD-B-WORKSHOP"], runs["CD-B-WORKSHOP-RC1"]])
    assert named[0]["length_ft"] == pytest.approx((pull_ft + 10.0) * 4, abs=0.1)
    two_pole = next(row for row in conductor_takeoff(catlin_model_ro) if row["poles"] == 2)
    assert "CD-B-WORKSHOP:CKT-WORKSHOP-240" in two_pole["tags"]
