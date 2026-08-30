"""A-301's sheet annotation — datums, ground line, room names, envelope callouts.

The building section drew a beautiful cut and said nothing about it: no level datum, no
floor-to-floor dimension, no grade, no room names. These pin the annotation that closed
that, and — as much — the two rules it must not break: **no geometry may move** (the cut is
identical, annotation is added beside it), and an authored ``Slice`` detail stays
un-annotated (a junction detail has no storey ladder to hang off).
"""

from __future__ import annotations

import pytest

from typehaus.emit.draw.elevation_annotate import feet_inches_signed, merged_levels
from typehaus.emit.draw.plan_labels import room_display_name
from typehaus.emit.draw.scene import ArchDimension, Leader, Polyline, Symbol, Text
from typehaus.emit.draw.section import build_center_section, build_section
from typehaus.emit.draw.section_annotate import (
    SECTION_RESERVATION_SCALE,
    annotate_building_section,
)
from typehaus.model.enums import SliceKind
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals


@pytest.fixture(scope="module")
def section(catlin_model_ro):
    return build_center_section(catlin_model_ro)


@pytest.fixture(scope="module")
def plane(catlin_model_ro):
    walls = [w for w in catlin_model_ro.walls if w.tag.startswith("W-")
             and w.storey in {"basement", "main", "second", "attic"}]
    stations = [c for w in walls for c in (w.axis[0][1], w.axis[1][1])]
    return CutPlane(axis="x", station_m=(min(stations) + max(stations)) / 2.0)


def _leaders(scene) -> list[Leader]:
    return [node for node in scene.nodes if isinstance(node, Leader)]


# --- the two invariants ------------------------------------------------------------------
def test_annotation_moves_no_geometry(catlin_model_ro, section, plane):
    """Every polyline/hatch of the bare cut survives the annotation unchanged.

    The annotation adds nodes; it must never edit one. Comparing the drawn nodes as a
    multiset catches a moved point, a re-layered band or a dropped hatch — the whole class
    of "the section changed while I was labelling it".
    """
    from typehaus.model.views import Slice
    from typehaus.quantities import m, pt

    view = Slice(uid="RNDSEC00001", tag="SECTION-HOUSE-CENTER", kind=SliceKind.SECTION,
                 cut_origin=pt(m(0), m(plane.station_m)), cut_direction="x")
    bare = build_section(catlin_model_ro, view)
    drawn = [n.model_dump_json() for n in section.nodes
             if getattr(n, "points", None) or getattr(n, "boundary", None)]
    assert drawn[:len(bare.nodes)] == [n.model_dump_json() for n in bare.nodes]


def test_authored_detail_slices_are_not_annotated(catlin_model_ro):
    """A detail is a fragment, not a sheet: no datum ladder, no ground line."""
    details = [v for v in catlin_model_ro.plan.elements_of_kind("Slice")
               if v.kind is SliceKind.DETAIL]
    assert details  # catlin authors detail slices — the guard would be vacuous otherwise
    for view in details:
        scene = build_section(catlin_model_ro, view)
        assert not [n for n in scene.nodes
                    if isinstance(n, Symbol) and n.name == "level-marker"]
        assert not [n for n in scene.nodes if getattr(n, "layer", "") == "L-SITE-GRAD"]


# --- 1. the level datum ladder -----------------------------------------------------------
def test_every_merged_level_gets_a_marker_and_a_caption(catlin_model_ro, section):
    levels = merged_levels(catlin_model_ro)
    markers = [n for n in section.nodes
               if isinstance(n, Symbol) and n.name == "level-marker"]
    assert len(markers) == len(levels)
    captions = {n.text for n in _leaders(section)}
    for level in levels:
        assert any(feet_inches_signed(level.z_m) in text and level.labels[0] in text
                   for text in captions), level


def test_datum_captions_name_floors_plates_grade_and_ridge(section):
    captions = " | ".join(n.text for n in _leaders(section))
    for expected in ("MAIN FLOOR  EL. 0'-0\"", "BASEMENT FLOOR  EL. -9'-1\"",
                     "GRADE  EL. -2'-10\"", "RIDGE"):
        assert expected in captions


def test_dimension_chain_sums_from_lowest_datum_to_highest(catlin_model_ro, section):
    """Rungs under 2'-0" are skipped, so the chain must still add up end to end."""
    dims = [n for n in section.nodes if isinstance(n, ArchDimension)]
    assert dims
    levels = merged_levels(catlin_model_ro)
    total = sum(abs(d.p1[1] - d.p0[1]) for d in dims)
    span = (levels[-1].z_m - levels[0].z_m) / M_PER_IN
    assert total == pytest.approx(span, abs=1e-6)


def test_datum_labels_do_not_overprint_each_other(section):
    """``SECOND T.O. PLATE`` stands 1" over ``ATTIC FLOOR``; the dodge is what saves them."""
    from typehaus.emit.draw.annotate import leader_box

    boxes = [leader_box(node, SECTION_RESERVATION_SCALE) for node in _leaders(section)]
    for index, (u0, z0, u1, z1) in enumerate(boxes):
        for (fu0, fz0, fu1, fz1) in boxes[index + 1:]:
            assert not (u0 < fu1 and fu0 < u1 and z0 < fz1 and fz0 < z1)


# --- 2. the ground line ------------------------------------------------------------------
def test_grade_line_is_drawn_outboard_of_the_building_only(section):
    """A section's ground stops at the foundation — it must not cross the basement."""
    ground = [n for n in section.nodes
              if isinstance(n, Polyline) and n.layer == "L-SITE-GRAD"
              and len(n.points) > 1 and n.points[0][1] == n.points[-1][1]]
    assert len(ground) == 2  # one run each side of the house
    left, right = sorted(ground, key=lambda n: n.points[0][0])
    walls = [n for n in section.nodes if getattr(n, "layer", "") in {"A-WALL", "S-FNDN"}]
    inner_lo = min(p[0] for n in walls for p in n.points)
    inner_hi = max(p[0] for n in walls for p in n.points)
    assert max(p[0] for p in left.points) <= inner_hi
    assert min(p[0] for p in right.points) >= inner_lo


def test_grade_carries_its_hatch_and_its_caption(section):
    ticks = [n for n in section.nodes
             if isinstance(n, Polyline) and n.layer == "L-SITE-GRAD" and len(n.points) == 2
             and n.points[0][0] != n.points[1][0] and n.points[0][1] != n.points[1][1]]
    assert len(ticks) >= 4  # the 45° grade-hatch convention, not one token tick
    assert [n for n in section.nodes
            if isinstance(n, Text) and n.content == "GRADE" and n.layer == "L-SITE-GRAD"]


# --- 3. room names -----------------------------------------------------------------------
def test_only_rooms_the_cut_crosses_are_named(catlin_model_ro, section, plane):
    labels = [n for n in section.nodes
              if isinstance(n, Text) and n.layer == "A-AREA-IDEN"]
    assert labels
    crossed = {room_display_name(room.tag) for room in catlin_model_ro.rooms
               if ring_intervals(room.clear_face, plane)}
    assert {n.content for n in labels} <= crossed
    assert "LIVING" in {n.content for n in labels}


def test_a_room_name_sits_inside_its_own_crossed_span(catlin_model_ro, section, plane):
    """One name per crossed volume, centred in the span the cut opens in *that* room.

    Keyed by display name and not by room: catlin has a CLOSET on two storeys, and the
    section legitimately names both — the storey letter the plans drop is what made them
    one name (``room_display_name``).
    """
    by_name: dict[str, list] = {}
    for room in catlin_model_ro.rooms:
        by_name.setdefault(room_display_name(room.tag), []).append(room)
    for node in section.nodes:
        if not (isinstance(node, Text) and node.layer == "A-AREA-IDEN"):
            continue
        u = node.anchor[0] * M_PER_IN
        assert any(u0 <= u <= u1
                   for room in by_name[node.content]
                   for (u0, u1) in ring_intervals(room.clear_face, plane)), node.content


# --- 4. envelope callouts ----------------------------------------------------------------
def test_envelope_callouts_are_three_at_most_and_land_on_drawn_geometry(section):
    """Restrained on purpose — this cut crosses eight wall assemblies (see the module doc)."""
    datum_texts = {n.text for n in _leaders(section) if " EL. " in n.text}
    callouts = [n for n in _leaders(section) if n.text not in datum_texts]
    assert 0 < len(callouts) <= 3
    assert len({n.text for n in callouts}) == len(callouts)  # no assembly named twice
    for node in callouts:
        assert node.at[0] < node.to[0]  # left column: the note runs away from the drawing
        # The arrowhead has to sit *on* an element's near face, not in the air beside it —
        # the gable is the case that breaks a bbox-corner anchor, thirteen feet up.
        on_face = [n for n in section.nodes if getattr(n, "points", None)
                   and abs(min(p[0] for p in n.points) - node.to[0]) < 0.5
                   and min(p[1] for p in n.points) - 0.5 <= node.to[1]
                   <= max(p[1] for p in n.points) + 0.5]
        assert on_face, node.text


# --- legibility --------------------------------------------------------------------------
def test_every_annotation_label_carries_a_printed_size(section):
    """Paper-space rule: a section's lettering is points, never model-space ``height``."""
    annotation = [n for n in section.nodes
                  if isinstance(n, (Text, Leader))
                  and getattr(n, "layer", "") in {"A-ANNO-TEXT", "A-AREA-IDEN",
                                                  "L-SITE-GRAD"}]
    assert annotation
    assert all(n.height_pt is not None for n in annotation)


def test_annotating_an_empty_scene_is_a_no_op(catlin_model_ro, plane):
    from typehaus.emit.draw.scene import Scene

    empty = Scene(name="section-empty", units="in")
    assert annotate_building_section(empty, catlin_model_ro, plane) is empty
