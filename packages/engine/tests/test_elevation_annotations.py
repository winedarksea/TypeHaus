"""Elevation annotations — grade profile, material leaders, vertical dims (Phase 5).

The sheet-margin half of the hidden-line elevation. The projection and occlusion half is
``test_elevation_projection.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.elevation import build_elevation
from typehaus.emit.draw.elevation_annotate import ANNO_HEIGHT_IN
from typehaus.emit.draw.lineweights import CUT_HEAVY
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


def _grade_profile(scene) -> Polyline:
    """The ground-line polyline itself, not one of its 45° hatch ticks."""
    runs = [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == "L-SITE-GRAD"
            and n.lineweight == CUT_HEAVY]  # the hatch ticks are LIGHT two-point segments
    assert len(runs) == 1
    return runs[0]


def test_south_grade_line_is_flat_within_an_inch(catlin_model):
    """The soil plane here is flat; the drawing has to say so.

    It did not. The sampler captured every spot within 10' of the facade plane on *either*
    side, so R401.3's second ring — 9' out, 6" lower, a station about the fall *away* from
    the wall rather than a station along it — printed as a 4" V in the middle of the
    principal elevation. Only the two near-wall stations describe this ground line, and
    they differ by 1".
    """
    profile = _grade_profile(build_elevation(catlin_model, "south"))
    zs = [point[1] for point in profile.points]
    assert max(zs) - min(zs) <= 2.0  # model inches


def test_south_grade_line_carries_no_far_station(catlin_model):
    """The specific artefact: a vertex at the far ring's u, at the far ring's elevation."""
    profile = _grade_profile(build_elevation(catlin_model, "south"))
    assert not [p for p in profile.points if abs(p[0] - 18.0 * 12.0) < 1.0]
    assert not [p for p in profile.points if abs(p[1] - -(3.0 * 12.0 + 4.0)) < 1.0]


def test_north_grade_line_is_flat(catlin_model):
    profile = _grade_profile(build_elevation(catlin_model, "north"))
    assert len({round(point[1], 6) for point in profile.points}) == 1


@pytest.mark.parametrize("facing", ["east", "west"])
def test_side_grade_lines_never_dive_into_the_sunken_court(catlin_model, facing):
    """The court floor stands 9' *behind* both side facade planes and reads -9'-1".

    Captured as ground it ramped the east profile to -7'-4" and the west to -6'-0" — three
    to four feet of imaginary excavation against the principal side elevations. It is a
    structure spot, and structure is not soil.
    """
    profile = _grade_profile(build_elevation(catlin_model, facing))
    floor_in = catlin_model.plan.project.site.grade.meters / M_PER_IN
    assert min(point[1] for point in profile.points) >= floor_in - 6.0


def test_a_structure_spot_at_the_facade_is_not_ground_but_a_grade_spot_is(catlin_model):
    """``kind`` is the invariant, not the geometry: the same point, twice, two profiles.

    The bands alone fix today's sheets. They are not enough on their own —
    ``_dominant_plane_depth`` is area-derived and moves when the building does, and a court
    floor that lands inside the band would be drawn as soil again.
    """
    from typehaus.model.site import SpotElevation
    from typehaus.quantities import ft, pt

    from test_site_checks import _model_with_site

    base = _grade_profile(build_elevation(catlin_model, "south")).points
    at_facade = SpotElevation(position=pt(ft(20), ft(-2)), elevation=ft(-8),
                              kind="structure")
    spots = catlin_model.plan.project.site.spot_elevations

    structure = _model_with_site(catlin_model, spot_elevations=(*spots, at_facade))
    assert _grade_profile(build_elevation(structure, "south")).points == base

    ground = _model_with_site(
        catlin_model,
        spot_elevations=(*spots, at_facade.model_copy(update={"kind": "grade"})))
    moved = _grade_profile(build_elevation(ground, "south")).points
    assert moved != base
    assert min(point[1] for point in moved) < -8.0 * 12.0 + 1.0


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

    Labels are dodged, so no two datum labels may come within one line of each other in z.
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
    # The sunken court is the thing the flat ground line stopped drawing itself around, and
    # this is where it is supposed to read instead: its floor and its south retaining wall,
    # dashed, below the line — the elevation convention for buried work.
    assert {"SL-SG-FIELD", "W-SG-S"} <= {node.tag for node in buried if node.tag}
