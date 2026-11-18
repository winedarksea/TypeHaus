"""LED construction (decision #137): the section as built, gear access, and the lead drop
against the hand-worked oracle (houses/catlin/notes/led_construction.md)."""

from __future__ import annotations

import dataclasses
from types import SimpleNamespace

import pytest

from typehaus.checks.mep.led_gear_access import led_gear_access
from typehaus.findings import Result
from typehaus.model.led import LedChannel, LedStrip
from typehaus.quantities import inch, mm
from typehaus.resolve.led_leads import lead_drop_pct, wire_drop_pct
from typehaus.resolve.led_sections import channel_parts, fill_modules, section_extent

_IN = 0.0254


def test_channel_section_and_module_fill():
    channel = LedChannel(uid="X", tag="CH", outer_width=inch(0.74), outer_depth=inch(0.57),
                         inner_width=inch(0.65))
    parts = channel_parts(channel, LedStrip(tape_width=mm(8)), "down")
    width, depth = section_extent([p for p in parts if p[0] != "endcap"])
    assert width == pytest.approx(0.74 * _IN)
    assert depth == pytest.approx(0.57 * _IN)
    tape = next(q for k, q in parts if k == "tape")
    assert max(a for a, _ in tape) - min(a for a, _ in tape) == pytest.approx(0.008)
    # "out" turns the channel's back onto the wall: depth now runs across.
    out = channel_parts(channel, LedStrip(tape_width=mm(8)), "out")
    assert section_extent(out)[0] == pytest.approx(0.57 * _IN)
    # MITTLED's schedule (plan/lighting_living.py): 36 = 24 + 12, 15.56 -> 15.
    sizes = tuple(x * _IN for x in (12, 15, 18, 24))
    assert [round(x / _IN) for x in fill_modules(sizes, 36 * _IN, 0.0)] == [24, 12]
    assert [round(x / _IN) for x in fill_modules(sizes, 15.56 * _IN, 0.0)] == [15]
    assert fill_modules(sizes, 10 * _IN, 0.0) == ()


def test_lead_drop_matches_the_hand_worked_note(catlin_model_ro):
    # The note's per-gauge arithmetic, then the engine's derived lead for the same run.
    assert wire_drop_pct(3.05, 29.551 * 0.3048, 16) == pytest.approx(3.748, abs=0.002)
    assert wire_drop_pct(3.05, 29.551 * 0.3048, 14) == pytest.approx(2.358, abs=0.002)
    leads = {lead.tag: lead for lead in catlin_model_ro.led_leads}
    feed, driver = leads["LR-M-LIVING-E-LEAD"], leads["ED-M-LIVING-LT-CTRL-E-LEAD"]
    assert (driver.awg, feed.awg) == (18, 14)
    assert driver.drop_pct == pytest.approx(0.190, abs=0.001)
    assert feed.length_m / _IN == pytest.approx(354.62, abs=0.05)
    assert feed.drop_pct == pytest.approx(2.358, abs=0.002)
    assert lead_drop_pct(catlin_model_ro, "LR-M-LIVING-E") == pytest.approx(2.548, abs=0.003)


def test_concealed_gear_fails_until_an_opening_reaches_it(catlin_model_ro):
    """ED-M-BATH2-PSU hoisted above BATH2's board FAILs; a ceiling access panel beside it
    PASSes. Exposed (as authored, on the laundry ceiling) it PASSes."""
    model = catlin_model_ro
    obj = next(o for o in model.canvas_objects if o.tag == "ED-M-BATH2-PSU")
    hidden = dataclasses.replace(obj, storey="main", room="RM-M-BATH2",
                                 position=(30 * _IN, 200 * _IN),
                                 footprint=((26 * _IN, 199 * _IN), (34 * _IN, 199 * _IN),
                                            (34 * _IN, 201 * _IN), (26 * _IN, 201 * _IN)),
                                 body_z0_m=obj.body_z0_m + 0.2, body_z1_m=obj.body_z1_m + 0.2)
    panel = dataclasses.replace(obj, tag="TEST-PANEL", type_ref="FT-ACCESS-PANEL-CLG-3029",
                                footprint=((36 * _IN, 190 * _IN), (66 * _IN, 190 * _IN),
                                           (66 * _IN, 219 * _IN), (36 * _IN, 219 * _IN)))

    def verdict(objects):
        view = SimpleNamespace(**{f.name: getattr(model, f.name)
                                  for f in dataclasses.fields(model)})
        view.canvas_objects = objects
        found = led_gear_access(SimpleNamespace(plan=model.plan, model=view))
        return next(f.result for f in found if f.element_tags[0] == "ED-M-BATH2-PSU")

    others = [o for o in model.canvas_objects if o.tag != obj.tag]
    assert verdict(model.canvas_objects) is Result.PASS
    assert verdict([*others, hidden]) is Result.FAIL
    assert verdict([*others, hidden, panel]) is Result.PASS
