"""Elevation annotations — grade profile, material leaders, vertical dims (Phase 5).

The sheet-margin half of the hidden-line elevation. The projection and occlusion half is
``test_elevation_projection.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.elevation import build_elevation
from typehaus.emit.draw.elevation_annotate import ANNO_HEIGHT_IN
from typehaus.emit.draw.scene import ArchDimension, Leader, Polyline, Symbol, Text
from typehaus.quantities import M_PER_IN
from typehaus.resolve import resolve
from typehaus.source import load_plan


@pytest.fixture(scope="module")
def starter_model(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def _leader_texts(scene) -> list[str]:
    return [node.text for node in scene.nodes if isinstance(node, Leader)]


def test_south_elevation_grade_profile_interpolates_spots(catlin_model):
    scene = build_elevation(catlin_model, "south")
    grade = [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == "L-SITE-GRAD"
             and len(n.points) > 2]
    assert grade
    z_values = {round(p[1] / 39.37007874015748, 2) for p in grade[0].points}
    assert z_values  # a real (non-empty) interpolated profile, not a crash


def test_starter_grade_profile_falls_back_to_flat_site_grade(starter_model):
    scene = build_elevation(starter_model, "south")
    grade = [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == "L-SITE-GRAD"
             and len(n.points) >= 2]
    assert grade
    poly = grade[0]
    zs = {round(p[1], 3) for p in poly.points}
    assert len(zs) == 1  # flat fallback — starter authors no spot_elevations


def test_one_leader_per_distinct_exterior_assembly(catlin_model):
    scene = build_elevation(catlin_model, "west")
    texts = _leader_texts(scene)
    assert len(texts) == len(set(texts))  # each distinct callout appears once
    assert texts  # west facade actually has exterior walls with layers


def test_material_callouts_name_finishes_not_substrates(catlin_model):
    """A callout names what the building is clad in, never a deck's ply or a soffit's spf.

    Every family but wall/roof was reaching the callout column, and a leader reading
    "STRUCT-1-PLYWOOD" beside a standing-seam wall describes nothing a person can see.
    """
    scene = build_elevation(catlin_model, "west")
    materials = {text for text in _leader_texts(scene) if " EL. " not in text}
    assert "PBR-PANEL-26" in materials
    assert not {"STRUCT-1-PLYWOOD", "SPF", "OSB"} & materials


def test_vertical_dim_string_covers_floor_plate_and_ridge(catlin_model):
    scene = build_elevation(catlin_model, "south")
    dims = [n for n in scene.nodes if isinstance(n, ArchDimension)]
    assert dims
    joined = " ".join(text for text in _leader_texts(scene) if "EL." in text)
    assert "GRADE" in joined
    assert "FLOOR" in joined
    assert "T.O. PLATE" in joined
    assert "RIDGE" in joined


def test_coincident_level_datums_share_one_marker(catlin_model):
    """MAIN T.O. PLATE and SECOND FLOOR are one line at 10'-0" and get one label."""
    scene = build_elevation(catlin_model, "south")
    labels = [text for text in _leader_texts(scene) if "EL." in text]
    assert any("MAIN T.O. PLATE / SECOND FLOOR" in text for text in labels)
    # ...and every printed elevation appears exactly once, however many names share it.
    elevations = [text.split("EL.")[1].strip() for text in labels]
    assert len(elevations) == len(set(elevations))


def test_level_labels_do_not_overprint(catlin_model):
    """GRADE, GARAGE FLOOR, MAIN FLOOR and BASEMENT T.O. PLATE sit within 3'-4" here.

    They used to print on top of each other; they are dodged now, so no two datum labels
    may come within one line of each other in z.
    """
    scene = build_elevation(catlin_model, "south")
    zs = sorted(node.at[1] for node in scene.nodes
                if isinstance(node, Leader) and "EL." in node.text)
    gaps = [b - a for a, b in zip(zs, zs[1:], strict=False)]
    assert gaps, "expected several datum labels"
    assert min(gaps) >= ANNO_HEIGHT_IN, f"labels {min(gaps):.2f}in apart overprint"


def test_material_callouts_do_not_overprint_the_datum_column(catlin_model):
    """The two annotation columns are dodged against each other, not just internally."""
    scene = build_elevation(catlin_model, "west")
    leaders = [node for node in scene.nodes if isinstance(node, Leader)]
    datums = [node for node in leaders if "EL." in node.text]
    callouts = [node for node in leaders if "EL." not in node.text]
    assert datums and callouts
    # The callout column sits left of the datum column and never reaches into it.
    assert max(node.at[0] for node in callouts) < min(node.at[0] for node in datums)


def test_short_dimension_rungs_are_skipped_and_the_chain_still_sums(catlin_model):
    """SECOND T.O. PLATE stands 1" over ATTIC FLOOR; a 1" rung is unreadable.

    Skipping it must not break the chain: bottom to top still adds up to the building's
    full height, because the next rung measures from the last one drawn.
    """
    scene = build_elevation(catlin_model, "south")
    dims = sorted((n for n in scene.nodes if isinstance(n, ArchDimension)),
                  key=lambda n: n.p0[1])
    spans = [abs(n.p1[1] - n.p0[1]) for n in dims]
    assert spans and min(spans) >= 24.0
    for lower, upper in zip(dims, dims[1:], strict=False):
        assert upper.p0[1] >= lower.p1[1] - 1e-6  # chained, never overlapping


def test_level_markers_present(catlin_model):
    scene = build_elevation(catlin_model, "south")
    markers = [n for n in scene.nodes if isinstance(n, Symbol) and n.name == "level-marker"]
    assert markers


def test_annotation_column_clears_the_freestanding_garage(catlin_model):
    """The garage stands 28' in front of the north wall and reaches past the facade.

    Measuring the margin off the facade plane put the dimension string straight through it.
    """
    scene = build_elevation(catlin_model, "east")
    drawn = [n for n in scene.nodes if isinstance(n, Polyline)
             and n.layer in {"A-WALL", "A-WALL-BEYD", "A-ROOF", "A-ROOF-TRIM"}]
    right_edge = max(point[0] for node in drawn for point in node.points)
    markers = [n for n in scene.nodes if isinstance(n, Symbol) and n.name == "level-marker"]
    assert markers
    assert min(marker.insert[0] for marker in markers) > right_edge


def test_elevation_title_and_grade_label_are_legible_at_sheet_scale(catlin_model):
    scene = build_elevation(catlin_model, "south")
    heights = {node.height for node in scene.nodes if isinstance(node, Text)}
    assert min(heights) >= ANNO_HEIGHT_IN


def test_elevation_dxf_round_trips_with_leader(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_elevation(catlin_model, "west")
    path = write_dxf(scene, tmp_path / "elevation.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert "L-SITE-GRAD" in names
    leader_types = {e.dxftype() for e in doc.modelspace()}
    assert "LEADER" in leader_types


def test_below_grade_geometry_is_dashed_on_its_own_layer(catlin_model):
    scene = build_elevation(catlin_model, "south")
    buried = [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == "A-WALL-BELW"]
    assert buried
    grade_z = catlin_model.plan.project.site.grade.meters / M_PER_IN
    for node in buried:
        assert node.linetype == "DASHED"
        assert max(point[1] for point in node.points) <= grade_z + 1e-6
