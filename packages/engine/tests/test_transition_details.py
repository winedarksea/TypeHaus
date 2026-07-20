"""Transition details — live-cut joints, per-layer roof bands, wedge, anchors (WP2/WP3)."""

from __future__ import annotations

import pytest

from typehaus.emit.draw.details import (
    build_detail,
    derive_detail_slices,
    resolve_anchor,
)
from typehaus.emit.draw.scene import Hatch, Polyline


def _eave(model):
    detail = next((d for d in derive_detail_slices(model)
                   if d.key.startswith("wall_roof")), None)
    assert detail is not None, "catlin should scaffold a wall_roof (eave) detail"
    return detail


def test_derive_scaffolds_bound_conditions_only(catlin_model):
    details = derive_detail_slices(catlin_model)
    assert details
    # keys are unique and sorted deterministically
    keys = [d.key for d in details]
    assert keys == sorted(set(keys))


def test_eave_has_per_layer_roof_bands_and_wedge(catlin_model):
    scene, findings = build_detail(catlin_model, _eave(catlin_model))
    assert not findings
    # per-layer sloped roof bands: multiple A-ROOF polylines tagged per layer
    roof_bands = [n for n in scene.nodes
                  if isinstance(n, Polyline) and n.layer == "A-ROOF" and "/" in (n.tag or "")]
    assert len(roof_bands) >= 2, "roof should be drawn as per-layer bands in detail mode"
    # spray-foam wedge treatment present
    wedges = [n for n in scene.nodes if isinstance(n, Hatch) and n.pattern == "spray-foam"]
    assert wedges, "spray-foam wedge hatch expected at the roof/wall foam interface"


def test_detail_scene_is_deterministic(catlin_model):
    detail = _eave(catlin_model)
    a, _ = build_detail(catlin_model, detail)
    b, _ = build_detail(catlin_model, detail)
    assert a.to_json() == b.to_json()


def test_unresolvable_anchor_yields_finding_no_crash(catlin_model):
    wall = catlin_model.walls[0]
    frame = lambda x, y, z: (x, z)  # noqa: E731 - trivial test frame
    point, err = resolve_anchor(catlin_model, frame, wall.uid, "layer:does-not-exist:out")
    assert err is not None
    assert err.check_id == "detail.anchor_unresolved"
    # a valid face still resolves cleanly
    _, ok = resolve_anchor(catlin_model, frame, wall.uid, "top")
    assert ok is None
    # a missing uid degrades to a finding rather than raising
    _, missing = resolve_anchor(catlin_model, frame, "NOPEUID0000", "top")
    assert missing is not None
