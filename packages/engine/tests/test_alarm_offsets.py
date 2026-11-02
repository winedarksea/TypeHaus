"""R314.3.3 / R314.3.4 / NFPA 72: smoke head offsets from bath doors, fans, registers, ranges."""

from __future__ import annotations

import copy

from typehaus.checks import run_from_model
from typehaus.model import m, pt

_CID = "code.R314_alarm_offsets"


def _results(model, tag) -> set[str]:
    return {f.result.value for f in run_from_model(model, [], only=[_CID]).findings
            if f.check_id == _CID and f.element_tags[0] == tag}


def _moved(model, tag, xy):
    plan = model.plan
    storey = next(s.tag for s in plan.storeys if any(e.tag == tag
                                                     for e in plan.storey_elements(s.tag)))
    elements = [e.model_copy(update={"position": pt(m(xy[0]), m(xy[1]))}) if e.tag == tag
                else e for e in plan.storey_elements(storey)]
    out = copy.copy(model)
    out.plan = plan.with_elements(storey, elements)
    return out


def test_hall_alarm_passes_until_moved_toward_the_range(catlin_model_ro):
    assert _results(catlin_model_ro, "AL-M-HALL") == {"pass"}
    x, y = next(o.position for o in catlin_model_ro.canvas_objects if o.tag == "APPL-M-RANGE")
    assert _results(_moved(catlin_model_ro, "AL-M-HALL", (x, y + 1.2)), "AL-M-HALL") == {"fail"}
    assert _results(_moved(catlin_model_ro, "AL-M-HALL", (x, y + 3.5)),
                    "AL-M-HALL") == {"unknown"}
