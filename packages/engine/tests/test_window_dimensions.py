"""Framing, the modeled frame and escape clearance are separate dimensions."""

from dataclasses import replace

import pytest

from typehaus.checks.code.mn_residential.egress import _meets_r310_2_1
from typehaus.emit.draw.schedules.openings import _frame_size_text
from typehaus.model.types import WindowType
from typehaus.quantities import inch
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model import ResolvedOpening
from typehaus.resolve.model_window_seat import WindowSeat, window_frame_dimensions


def test_escape_formula_tracks_installation_clearances_and_sill_rise():
    opening = ResolvedOpening(
        "window", "WIN", "W", "WT", inch(27).meters, inch(48).meters,
        inch(30).meters, 1, "window", False,
        window_seat=WindowSeat(inch(.645).meters, inch(.55).meters,
                               inch(.645).meters, 0))
    product = WindowType(
        tag="WT", width=inch(27), height=inch(48), operation="casement",
        net_clear_width_deduction=inch(5.81), net_clear_height_deduction=inch(4.85))
    assert not _meets_r310_2_1(opening, grade_floor=False, window_type=product)
    # A different installation that actually clears 20 inches can pass. No cached
    # RO-minus-half-inch clear opening may survive a seat edit.
    wider = replace(opening, window_seat=replace(opening.window_seat,
                                                jamb_inset_m=inch(.59).meters))
    assert _meets_r310_2_1(wider, grade_floor=False, window_type=product)
    assert not _meets_r310_2_1(replace(wider, sill_m=inch(44).meters),
                              grade_floor=False, window_type=product)
    assert not _meets_r310_2_1(replace(wider, window_seat=None),
                              grade_floor=False, window_type=product)


def test_schedule_frame_dimensions_match_the_rendered_frame(catlin_model_ro):
    windows = [o for o in catlin_model_ro.openings if o.kind == "window"]
    assert len(windows) == 41
    unresolved = []
    for opening in windows:
        dimensions = window_frame_dimensions(opening)
        if dimensions is None:
            unresolved.append(opening.tag)
            assert _frame_size_text(dimensions) == "UNRESOLVED"
            continue
        width, height, sill = dimensions
        wall = catlin_model_ro.wall(opening.host_wall)
        _origin, tangent, _normal, _run = wall_frame(wall)
        frame = next(p for p in opening_parts(wall, opening, None) if p.key == "frame")
        stations = [x * tangent[0] + y * tangent[1]
                    for solid in frame.solids for x, y in solid.ring]
        assert max(stations) - min(stations) == pytest.approx(width), opening.tag
        assert max(s.z1_m for s in frame.solids) - min(s.z0_m for s in frame.solids) \
            == pytest.approx(height), opening.tag
        assert min(s.z0_m for s in frame.solids) == pytest.approx(wall.base_ref_z_m + sill)
        assert width < opening.width_m and height < opening.height_m
    assert unresolved == ["WIN-B-SAUNA"]


def test_ifc_window_sizes_follow_frames_and_keep_voids_at_rough_openings(
    catlin_model_ro, catlin_ifc_path,
):
    import ifcopenshell
    import ifcopenshell.util.element

    file = ifcopenshell.open(str(catlin_ifc_path))
    windows = {o.tag: o for o in catlin_model_ro.openings if o.kind == "window"}
    for window in file.by_type("IfcWindow"):
        opening = windows[window.Name]
        dimensions = window_frame_dimensions(opening)
        properties = ifcopenshell.util.element.get_psets(window)["TypeHaus_WindowDimensions"]
        assert properties["RoughOpeningWidth"] == pytest.approx(opening.width_m)
        assert properties["RoughOpeningHeight"] == pytest.approx(opening.height_m)
        if dimensions is None:
            assert window.OverallWidth is None and window.OverallHeight is None
            assert properties["FrameSizeResolved"] is False
            continue
        assert properties["FrameSizeResolved"] is True
        assert window.OverallWidth == pytest.approx(dimensions[0])
        assert window.OverallHeight == pytest.approx(dimensions[1])
        body = window.Representation.Representations[0].Items[0]
        assert body.Depth == pytest.approx(dimensions[1])
        void = window.FillsVoids[0].RelatingOpeningElement
        assert void.Representation.Representations[0].Items[0].Depth \
            == pytest.approx(opening.height_m)


def test_schedule_labels_both_sizes_and_identifies_the_manual_detail(catlin_model_ro, monkeypatch):
    from contextlib import contextmanager

    from typehaus.emit.draw.schedules import openings

    @contextmanager
    def page(*args):
        yield None

    tables = []
    monkeypatch.setattr(openings, "schedule_sheet", page)
    monkeypatch.setattr(openings, "_add_table",
                        lambda fig, rows, headers, **kwargs: tables.append((rows, headers)))
    openings._write_opening_schedule(None, catlin_model_ro, "A-602", "Windows", "window")
    rows, headers = tables[0]
    assert headers[4:6] == ("Rough opening", "Modeled frame")
    assert all(len(row) == len(headers) for row in rows)
    by_tag = {row[1]: row for row in rows}
    assert by_tag["WIN-S-BED1"][4:6] == ('27" × 48"', '25.710″ × 46.805″')
    assert by_tag["WIN-B-SAUNA"][5] == "UNRESOLVED"
