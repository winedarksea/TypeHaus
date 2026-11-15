"""Lane E of the 2026 NEC residue: device listing facts (230.67(E), 215.18(E), 406.9, 406.11(D),
408.6) and 110.26(D)/(E)(2). Paraphrase: docs/code-notes/nec-2026-paraphrase-404-408.md, -110-240-625.md."""

from __future__ import annotations

import dataclasses

from shapely.affinity import translate
from shapely.geometry import Polygon

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier


def _by_tag(model, check_id, tier=Tier.CODE):
    report = run_from_model(model, [], tier=tier, only=check_id)
    return {f.element_tags[0] if f.element_tags else "": f.result.value
            for f in report.findings if f.check_id == check_id}


def test_catlins_device_facts(catlin_model_ro):
    assert _by_tag(catlin_model_ro, "electrical.spd_nominal_discharge") == {
        "ED-M-SPD": "unknown", "CKT-SPD": "pass", "CKT-SPD-2": "pass",
        "CKT-SPD-BACKUP": "unknown",   # FS140 and the backup plug-on publish no In
        "CKT-SPD-GAR": "pass"}         # the garage subpanel's HOM2175SB, In 10 kA
    assert set(_by_tag(catlin_model_ro, "electrical.outdoor_receptacle_wr").values()) == {"pass"}
    # The plant heater's control moved to its plug (2026-11-14): no relay-fed receptacle.
    assert _by_tag(catlin_model_ro, "electrical.controlled_receptacle", Tier.ADVISORY) == {
        "": "not_applicable"}
    assert set(_by_tag(catlin_model_ro, "electrical.panel_sccr").values()) == {"unknown"}


def test_catlins_working_space_lighting_and_outdoor_zone(catlin_model_ro):
    assert set(_by_tag(catlin_model_ro, "electrical.working_space_lighting").values()) == {"pass"}
    assert _by_tag(catlin_model_ro, "electrical.outdoor_working_space") == {"ED-M-METER": "pass"}


def test_track_in_the_tubs_room_fails_honestly(catlin_model):
    """The laundry track shifted 3'-6" west, into RM-M-BATH2: a FAIL, never a held UNKNOWN."""
    shift = -3.5 * 0.3048
    objects = catlin_model.canvas_objects
    i = next(k for k, o in enumerate(objects) if o.tag == "ED-M-LAUNDRY-TRACK")
    old = objects[i]
    ring = translate(Polygon(old.footprint), xoff=shift)
    objects[i] = dataclasses.replace(old, footprint=tuple(ring.exterior.coords)[:-1],
                                     position=(old.position[0] + shift, old.position[1]))
    try:
        assert _by_tag(catlin_model, "electrical.bath_luminaire_zone", Tier.ADVISORY) == {
            "ED-M-LAUNDRY-TRACK": "fail"}
    finally:
        objects[i] = old
