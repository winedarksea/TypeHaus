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
    assert by_tag["WIN-S-BED1"][4:6] == ('27.5" × 48"', '26.125″ × 46.500″')
    assert by_tag["WIN-S-PLANT3"][4:6] == ('27.5" × 54"', '26.210″ × 52.805″')
    assert by_tag["WIN-B-SAUNA"][5] == "UNRESOLVED"


def test_orderable_size_rounds_down_and_never_past_the_envelope():
    from typehaus.resolve.model_window_seat import orderable_size

    step = inch(0.125)
    assert orderable_size(inch(26.125).meters, step) == pytest.approx(inch(26.125).meters)
    assert orderable_size(inch(26.125).meters - 1e-6, step) == pytest.approx(inch(26).meters)
    assert orderable_size(inch(26.21).meters, step) <= inch(26.21).meters
    assert orderable_size(inch(26.21).meters, None) == inch(26.21).meters


def _seat(width_in, height_in, product=None):
    from typehaus.resolve.flashing_config import FLASHING
    from typehaus.resolve.opening_flashing import OpeningFlashingFrame, window_seat

    # Mount at the back dam: a level pan, so the sill rise is buck + membrane alone.
    frame = OpeningFlashingFrame((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), 0.0, 0.1,
                                 FLASHING.back_dam_strip_m, 0.2, True, inch(0.375).meters)
    opening = ResolvedOpening("window", "WIN", "W", "WT", inch(width_in).meters,
                              inch(height_in).meters, inch(30).meters, 1, "window", False)
    return replace(opening, window_seat=window_seat(opening, frame, FLASHING, product))


def test_seat_sizes_an_orderable_unit_inside_the_flashed_opening():
    product = WindowType(tag="WT", width=inch(27.5), height=inch(48), operation="casement",
                         frame_size_increment=inch(0.125),
                         minimum_rough_opening_allowance=inch(0.5))
    sized = _seat(27.5, 48, product)
    width, height, bottom = window_frame_dimensions(sized)
    # 48 - (3/8 buck + 0.060 pan membrane) - (3/8 + 0.020 head) - 1/2 = 46.67 -> 46 5/8.
    assert (width / .0254, height / .0254) == pytest.approx((26.125, 46.625))
    # Centred between the jambs; it still bears on the pan, so the head takes the slack.
    seat = sized.window_seat
    unsized = _seat(27.5, 48).window_seat
    assert seat.sill_rise_m == unsized.sill_rise_m
    assert 2 * seat.jamb_inset_m + width == pytest.approx(sized.width_m)
    assert seat.head_drop_m > unsized.head_drop_m
    assert bottom == pytest.approx(sized.sill_m + seat.sill_rise_m)


def test_the_larger_of_the_gaps_and_the_maker_allowance_governs_each_axis():
    def unit(allowance_in):
        product = WindowType(tag="WT", width=inch(27.5), height=inch(48),
                             minimum_rough_opening_allowance=inch(allowance_in))
        return window_frame_dimensions(_seat(27.5, 48, product))[:2]

    plain = window_frame_dimensions(_seat(27.5, 48))[:2]
    # 1/4" shims at both jambs already make 1/2" across; the head has only one 1/4" shim.
    assert unit(0.5)[0] == pytest.approx(plain[0])
    assert unit(0.5)[1] == pytest.approx(plain[1] - inch(0.25).meters)
    assert unit(1.0)[0] == pytest.approx(plain[0] - inch(0.5).meters)
    assert unit(0)[0] == pytest.approx(plain[0])


@pytest.mark.parametrize("update", [
    {"frame_size_increment": inch(0)},
    {"minimum_rough_opening_allowance": inch(-0.5)},
])
def test_orderable_size_fields_reject_nonsense(update):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        WindowType(tag="WT", width=inch(27), height=inch(48), **update)


def test_profiled_metal_windows_have_four_terminated_sides(catlin_model_ro):
    from typehaus.resolve.cladding_trim.openings import cladding_finish

    windows = [opening for opening in catlin_model_ro.openings
               if opening.kind == "window" and opening.window_seat
               and opening.window_seat.outer_m is not None]
    assert len(windows) == 40
    for opening in windows:
        pieces = [solid for solid in catlin_model_ro.solids
                  if solid.category == "cladding_trim" and solid.host_ref == opening.tag]
        # PBR ribs take the catalog jamb; BBD75 and corrugated keep the site-brake one.
        wall = catlin_model_ro.wall(opening.host_wall)
        jamb = ("PBR_WINDOW_JAMB" if cladding_finish(catlin_model_ro, wall) == "ribbed-panel"
                else "WINDOW_JAMB_CUSTOM")
        # A rainscreen cavity over the head takes the K6 cap (the garage has none).
        from typehaus.resolve.rainscreen_closures import rainscreen_band

        cap = ["OPENING_HEAD_CAP"] if rainscreen_band(wall.layers) is not None else []
        assert sorted(solid.product for solid in pieces) == sorted([
            "OPENING_HEAD", *cap, jamb, jamb, "WINDOW_SILL_CUSTOM"])
        assert all(solid.body_mesh and solid.body_mesh.positions for solid in pieces)
