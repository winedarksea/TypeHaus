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


def test_eave_overlay_defers_to_the_authored_gutter(catlin_model):
    """The house eave carries an authored Gutter + drip (params/roof_trim.py) riding the
    roofing plane, so the overlay must NOT add its schematic pair a storey of roof stack
    lower — one eave, one gutter. The apron and vent screen have no authored counterpart
    and still come from the overlay."""
    scene, findings = build_detail(catlin_model, _eave(catlin_model))
    assert not findings
    tags = _tags(scene)
    assert any(t.startswith("TR-RF-GUTTER") for t in tags), \
        "the authored box gutter should be cut into the eave detail"
    assert any(t.startswith("TR-RF-DRIP") for t in tags)
    assert "detail-component:box-gutter" not in tags, \
        "overlay must defer to the authored gutter, not double it"
    assert "detail-component:drip-edge" not in tags
    assert "detail-component:apron-flashing" in tags
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
    assert scene.notes and scene.notes[0] == "NOTES:", \
        "notes loaded from Transition.notes ride Scene.notes, outside the drawing space"
    assert not any(t.startswith("NOTES") for t in texts), \
        "notes must not be Text nodes — they would couple the drawing scale to prose length"
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


def _leaders(scene):
    from typehaus.emit.draw.scene import Leader

    return [n for n in scene.nodes if isinstance(n, Leader)]


@pytest.mark.parametrize("pick", [_eave, _foundation])
def test_layer_label_ladder_is_deduped_and_non_overlapping(catlin_model, pick):
    """The ladder bug: per-interval labels duplicated ("5.5 stud" twice) and rungs from
    different layers interleaved into a smear. Labels are now deduped per (wall, layer)
    and every label box — ladder rungs and seed callouts alike — is dodged clear."""
    from typehaus.emit.draw.annotate import leader_box

    scene, _ = build_detail(catlin_model, pick(catlin_model))
    leaders = _leaders(scene)
    assert leaders, "detail should carry layer labels"
    # deduplicated: no two leaders repeat the same note at the same target
    keys = [(n.text, n.to) for n in leaders]
    assert len(keys) == len(set(keys)), "duplicate layer labels"
    # Non-overlapping: estimated text boxes are pairwise disjoint. Measured **in the
    # drawing's own frame** — a label carries a printed size, so how much of the model it
    # covers is a fact about the sheet, and asking at the wrong scale reports collisions
    # that do not happen on paper.
    scale = scene.frame.scale if scene.frame is not None else None
    boxes = [leader_box(n, scale) for n in leaders]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert not (a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]), \
                f"label boxes overlap: {leaders[i].text!r} / {b!r}"


def test_seed_callouts_wrap_at_leader_wrap_columns(catlin_model):
    from typehaus.emit.draw.annotate import LEADER_WRAP_COLUMNS

    scene, _ = build_detail(catlin_model, _eave(catlin_model))
    continuity = [n for n in _leaders(scene) if "continuity" in n.text]
    assert continuity, "eave detail should seed continuity callouts"
    assert any("\n" in n.text for n in continuity), \
        "the 45+ char air-continuity claim must wrap"
    for n in continuity:
        assert all(len(line) <= LEADER_WRAP_COLUMNS for line in n.text.split("\n"))


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
    """The eave rafter is a notched member seated on the plate — six points, not five.

    Six because the notch has a real corner: eave-top, ridge-top, ridge-bottom, the plumb
    heel's head, the heel's foot, and the seat's outboard end. The 2D version was five
    because it dropped the ``(u_heel, plate_top)`` corner and ran a slanted line instead —
    one of the *three* birdsmouths that used to exist (the rafter's own elevation, an
    additive ``seat_cut`` block, and this drawing).
    """
    scene, _ = build_detail(catlin_model, _eave(catlin_model))
    rafters = [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == "S-FRAM"
               and (n.tag or "").startswith("rafter") and "/flange" not in (n.tag or "")]
    assert rafters, "the eave detail should carry a representative rafter"
    notched = [r for r in rafters if len(r.points) == 6]
    assert notched, "rafter should be a notched profile"

    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    plate_top = roof.bearing_z_m / 0.0254
    for rafter in notched:
        # Its bottom sits *on* the plate over the seat run, rather than a notch-depth clear
        # of it or a notch-depth into it.
        seat = sorted(u for (u, z) in rafter.points if abs(z - plate_top) < 1e-6)
        assert len(seat) == 2, rafter.points
        member = next(m for m in roof.members if m.child_key == rafter.tag)
        assert seat[1] - seat[0] == pytest.approx(member.seat.seat_run_m / 0.0254, abs=1e-3)

    # I-joist rafters carry flange delineation lines.
    flanges = [n for n in scene.nodes if isinstance(n, Polyline)
               and (n.tag or "").endswith("/flange")]
    assert flanges, "I-joist rafter should carry flange lines"


def _sauna_slice(model):
    detail = next((s for s in model.plan.elements_of_kind("Slice")
                   if s.tag == "SL-D-SAUNA"), None)
    assert detail is not None, "catlin should author a sauna room-section detail slice"
    return detail


def test_authored_sauna_detail_draws_room_scale_vocabulary(catlin_model):
    # The authored sauna floor-section routes through build_authored_detail_scene, which
    # layers the sauna liner base + room-scale vocabulary over the plain cut.
    from typehaus.emit.draw.details import build_authored_detail_scene

    scene = build_authored_detail_scene(catlin_model, _sauna_slice(catlin_model))
    tags = _tags(scene)
    # Liner base + slab thermal break (previously dormant components).
    assert "detail-component:sauna-baseboard" in tags
    assert "detail-component:thermal-break" in tags
    # New room-scale vocabulary.
    assert "detail-component:sauna-bench" in tags, "two-tier benches expected"
    assert "detail-component:sauna-heater" in tags, "heater clearance box expected"
    assert "detail-component:sauna-floor-slope" in tags, "floor slope to drain expected"
    assert "detail-component:sauna-drop-ceiling" in tags, "hung drop ceiling expected"
    # Everything stays polyline/hatch geometry, never a bare Symbol.
    assert not any(getattr(n, "node", None) == "symbol" for n in scene.nodes)


def test_authored_non_sauna_detail_is_unchanged(catlin_model):
    # A non-sauna authored detail must be byte-identical to the plain section cut — the sauna
    # overlay self-gates on sauna walls being in the cut, so it never touches other details.
    from typehaus.emit.draw.details import build_authored_detail_scene
    from typehaus.emit.draw.section import build_section

    fndn = next(s for s in catlin_model.plan.elements_of_kind("Slice")
                if s.tag == "SL-D-FNDN")
    assert (build_authored_detail_scene(catlin_model, fndn).to_json()
            == build_section(catlin_model, fndn).to_json())


def test_sauna_bench_geometry_matches_reference(catlin_model):
    # Bench tops at 18"/36" above the floor slab, 1.5" boards — the reference numbers.
    from typehaus.emit.draw.detail_components import (
        SAUNA_BENCH_LOWER_TOP_IN,
        SAUNA_BENCH_UPPER_TOP_IN,
        sauna_benches,
    )
    from typehaus.quantities import M_PER_IN

    floor = next(s for s in catlin_model.solids if s.tag == "SL-B-FLOOR")
    floor_z = floor.z1_m / M_PER_IN
    nodes = sauna_benches(120.0, 210.0, floor_z)
    seats = [n for n in nodes if getattr(n, "tag", None) == "detail-component:sauna-bench"]
    assert len(seats) == 2, "a lower and an upper bench"
    tops = sorted(max(z for _u, z in seat.points) for seat in seats)
    assert abs(tops[0] - (floor_z + SAUNA_BENCH_LOWER_TOP_IN)) < 1e-6
    assert abs(tops[1] - (floor_z + SAUNA_BENCH_UPPER_TOP_IN)) < 1e-6


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
