"""NEC 110.26(A) working space and 110.26(E)(1) dedicated space in front of / over a panel."""

from __future__ import annotations

import copy

from typehaus.checks import run_from_model
from typehaus.resolve.model import ResolvedDuct

_WORK, _DEDICATED = "electrical.panel_working_space", "electrical.panel_dedicated_space"


def _results(model, cid) -> dict[str, str]:
    return {f.element_tags[0]: f.result.value
            for f in run_from_model(model, [], only=[cid]).findings if f.check_id == cid}


def _duct(tag, path, z):
    return ResolvedDuct(uid=tag, tag=tag, storey="basement", system="supply", path=path,
                        width_m=0.2, depth_m=0.2, diameter_m=0.2, routing="exposed",
                        floor_ref=None, crossings=(), conflicts=(), depth_ok=True,
                        z_m=(z, z))


def test_catlin_panels_clear_and_a_duct_blocks_both_spaces(catlin_model_ro):
    for cid in (_WORK, _DEDICATED):
        assert set(_results(catlin_model_ro, cid).values()) == {"pass"}
    model = copy.copy(catlin_model_ro)
    # ED-B-PANEL faces +x off W-B-W1 at x=0.30 m, y 8.59-9.09 m, floor at -2.78 m.
    model.ducts = [*catlin_model_ro.ducts,
                   _duct("DU-FRONT", [(0.6, 7.0), (0.6, 11.0)], -2.0),
                   _duct("DU-OVER", [(0.25, 8.0), (0.25, 9.5)], -0.4)]
    assert _results(model, _WORK)["ED-B-PANEL"] == "fail"
    assert _results(model, _DEDICATED)["ED-B-PANEL"] == "fail"


def test_open_doors_90_degree_and_24_inch_access():
    """110.26 intro / (A)(2) on one 14" enclosure, with all its windows or only one clear."""
    from types import SimpleNamespace

    from typehaus.checks.mep import electrical_panel_space as space
    from typehaus.checks.mep.electrical_panel_doors import access_findings, door_findings

    inch = 0.0254
    body = SimpleNamespace(tag="ED-P", rotation_degrees=0.0, storey="main",
                           footprint=[(0, 0), (14 * inch, 0), (14 * inch, 0.1), (0, 0.1)],
                           body_z0_m=1.2, body_z1_m=2.0)
    windows = list(space._windows(body))
    panel = SimpleNamespace(tag="ED-P", type_ref="ED-T-P")

    def verdict(hinge, clear):
        types = {"ED-T-P": SimpleNamespace(door_hinge=hinge)}
        [f] = access_findings([panel], {"ED-P": body}, types, {"ED-P": clear}, {"ED-P": 0.0})
        return f.result.value

    [door] = door_findings([panel], {"ED-P": body}, {"ED-P": windows})
    assert door.result.value == "pass"  # a 14" leaf inside the 36" depth
    assert verdict(None, windows) == "pass"  # some window puts the leaf on its edge
    first = [windows[0]]  # ends at the panel's right edge, 16" of it left of the panel
    assert (verdict("left", first), verdict("right", first), verdict(None, first)) == (
        "fail", "pass", "unknown")
