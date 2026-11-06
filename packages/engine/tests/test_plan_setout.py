"""Bath setout strings (I2-005/006) and the A-607 casework rows (I1-106), off the model."""

from __future__ import annotations

import math


def test_a_floor_wc_gets_its_rough_in_and_side_clearances(catlin_model_ro):
    from typehaus.emit.draw.datum import model_at_level
    from typehaus.emit.draw.plan_setout import setout_nodes

    nodes = setout_nodes(model_at_level(catlin_model_ro, "basement"), ("RM-B-BATH",))
    length = {n.ends[0].name[:-2]: math.dist(n.p0, n.p1) for n in nodes}
    # TOTO Drake: 12" rough-in to the finish wall, and UPC 402.5's 15" each side.
    assert abs(length["FX-B-BATH-WC-back"] - 12.0) < 0.25
    assert min(length["FX-B-BATH-WC-side1"], length["FX-B-BATH-WC-side-1"]) >= 15.0
    assert any(n.text.endswith("CLR") for n in nodes if n.ends[0].name.startswith(
        "FX-B-BATH-WC-front"))


def test_casework_schedule_has_every_top_and_its_hosts(catlin_model_ro):
    from typehaus.emit.draw.schedules.casework import casework_rows, countertop_rows

    tops = {row[0]: row for row in countertop_rows(catlin_model_ro)}
    assert set(tops) == {top.tag for top in catlin_model_ro.countertops}
    # K1/K6: 3 cm quartz, top 36" and underside 34 13/16" above the finished floor.
    assert tops["CT-M-KIT-N"][5:7] == ('36"', '34 13/16"')
    hosted = {row[0] for row in casework_rows(catlin_model_ro) if row[6] != "-"}
    assert hosted == {host for top in catlin_model_ro.countertops for host in top.hosts}
