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


def _garage_foundation(model):
    detail = next((d for d in derive_detail_slices(model)
                   if d.key.startswith("wall_foundation") and "GARAGE" in d.key), None)
    assert detail is not None, "catlin should scaffold a garage wall_foundation detail"
    return detail


def test_eave_overlay_emits_apron_flashing(catlin_model):
    scene, _ = build_detail(catlin_model, _eave(catlin_model))
    assert "detail-component:apron-flashing" in _tags(scene), (
        "apron flashing is a named component distinct from the drip/Z/L flashings")


def test_garage_foundation_draws_slab_thermal_break(catlin_model):
    # The 1" thermal break is its own labelled component (xps + sealant cap), drawn where a
    # slab-on-grade edge meets the foundation wall — the garage ICF stem.
    scene, _ = build_detail(catlin_model, _garage_foundation(catlin_model))
    tags = _tags(scene)
    assert "detail-component:thermal-break" in tags
    assert "detail-component:thermal-break-sealant" in tags
    # It stays polyline+hatch, never a bare Symbol.
    assert not any(getattr(n, "node", None) == "symbol" for n in scene.nodes)


def test_birdsmouth_rafter_reads_as_a_notched_member(catlin_model):
    # The eave detail's representative rafter is drawn as a raked, notched profile (a 5-point
    # polygon: eave-top, ridge-top, ridge-bottom, seat toe, heel), not a straight bar.
    scene, _ = build_detail(catlin_model, _eave(catlin_model))
    rafters = [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == "S-FRAM"
               and (n.tag or "").startswith("rafter") and "/flange" not in (n.tag or "")]
    assert rafters, "the eave detail should carry a representative rafter"
    assert any(len(r.points) == 5 for r in rafters), "rafter should be a notched profile"
    # I-joist rafters carry flange delineation lines.
    flanges = [n for n in scene.nodes if isinstance(n, Polyline)
               and (n.tag or "").endswith("/flange")]
    assert flanges, "I-joist rafter should carry flange lines"


def test_birdsmouth_depth_parsed_from_connection():
    from typehaus.emit.draw.section import _birdsmouth_depth_in

    assert _birdsmouth_depth_in("ridge:adjustable-slope-hanger;eave:birdsmouth-1.17in") == 1.17
    assert _birdsmouth_depth_in("eave:beveled-web-stiffener") is None
    assert _birdsmouth_depth_in(None) is None


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
