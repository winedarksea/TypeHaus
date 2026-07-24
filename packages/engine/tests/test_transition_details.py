"""Transition details — live-cut joints, per-layer roof bands, wedge, anchors (WP2/WP3)."""

from __future__ import annotations

import pytest

from typehaus.emit.draw.details import (
    build_detail,
    derive_detail_slices,
    resolve_anchor,
)
from typehaus.emit.draw.scene import ArchDimension, Hatch, Polyline, Text


def _eave(model):
    detail = next((d for d in derive_detail_slices(model)
                   if d.key.startswith("wall_roof")), None)
    assert detail is not None, "catlin should scaffold a wall_roof (eave) detail"
    return detail


def _foundation(model):
    detail = next((d for d in derive_detail_slices(model)
                   if d.key.startswith("wall_foundation")), None)
    assert detail is not None, "catlin should scaffold a wall_foundation detail"
    return detail


def _tags(scene):
    return {n.tag for n in scene.nodes if isinstance(n, Polyline) and n.tag}


def test_eave_overlay_emits_box_gutter_and_drip(catlin_model):
    scene, findings = build_detail(catlin_model, _eave(catlin_model))
    assert not findings
    tags = _tags(scene)
    assert "detail-component:box-gutter" in tags, "zero-overhang-eave needs a box gutter"
    assert "detail-component:drip-edge" in tags
    # Flashings are polyline+hatch geometry, never a bare Symbol.
    assert not any(getattr(n, "node", None) == "symbol" for n in scene.nodes)


def test_foundation_overlay_emits_flashings_and_gasket(catlin_model):
    scene, _ = build_detail(catlin_model, _foundation(catlin_model))
    tags = _tags(scene)
    assert "detail-component:z-flashing" in tags
    assert "detail-component:l-flashing" in tags
    assert "detail-component:sill-gasket" in tags


def test_detail_has_legend_dims_and_notes(catlin_model):
    scene, _ = build_detail(catlin_model, _foundation(catlin_model))
    texts = [n.content for n in scene.nodes if isinstance(n, Text)]
    assert "MATERIALS" in texts, "a material legend band is expected"
    assert any(t.startswith("NOTES") for t in texts), "notes column loaded from Transition.notes"
    assert catlin_model.plan.project.name in texts, "title block carries the project name"
    dims = [n for n in scene.nodes if isinstance(n, ArchDimension)]
    assert dims, "derived dimension strings expected from resolved layer thicknesses"
    assert any('CI' in (n.text or '') for n in dims)


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
