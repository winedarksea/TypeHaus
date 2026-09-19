"""Regression: strapping/furring battens and courses split around window/door openings
instead of running straight through them (``resolve/framing/furring.py``).

Builds a minimal wall + FURRING layer + assembly double directly, following the fixture
convention in ``test_solver_units.py`` (a bare ``ResolvedWall``/``SimpleNamespace`` plan,
no full house), so the vertical/horizontal split logic is asserted independent of any
authored house's geometry.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch
from typehaus.resolve.framing.furring import frame_wall_furring
from typehaus.resolve.model import ResolvedLayer, ResolvedOpening, ResolvedWall

_BAND = ((0.0, 0.05), (3.6576, 0.05), (3.6576, -0.05), (0.0, -0.05))


def _opening(center_along_m: float, width_m: float, height_m: float,
            sill_m: float) -> ResolvedOpening:
    return ResolvedOpening(
        uid="O1", tag="WIN-1", host_wall="W-TEST", type_ref=None,
        width_m=width_m, height_m=height_m, sill_m=sill_m, center_along_m=center_along_m,
        kind="window", is_door=False,
    )


def _vertical_wall(spacing_in: float | None):
    layer = Layer(name="strap", material_ref="spf", thickness=inch(0.75),
                 function=LayerFunction.FURRING,
                 framing=FramingSpec(member="1x4", direction="vertical",
                                     spacing=inch(spacing_in) if spacing_in else None))
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    resolved = ResolvedLayer(name="strap", material_ref="spf", function="furring",
                             thickness_m=inch(0.75).meters, polygon=_BAND)
    rw = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
        axis=((0.0, 0.0), (3.6576, 0.0)), layers=(resolved,), z0_m=0.0, z1_m=2.5,
    )
    return plan, rw


def test_vertical_batten_splits_around_a_mid_height_window():
    plan, rw = _vertical_wall(spacing_in=150.0)  # forces exactly two stations: first + last
    # First station sits at face/2 (~0.04445 m); a 0.2 m-wide window centred there overlaps
    # only that station, not the far one at ~3.61315 m.
    opening = _opening(center_along_m=0.04445, width_m=0.2, height_m=0.5, sill_m=1.0)
    members, findings = frame_wall_furring(plan, rw, [opening])
    assert not findings

    at_first = sorted((m for m in members if abs(m.p0[0] - 0.04445) < 1e-6),
                      key=lambda m: m.z0_m)
    assert len(at_first) == 2
    assert abs(at_first[0].z0_m - 0.0) < 1e-6 and abs(at_first[0].z1_m - 1.0) < 1e-6
    assert abs(at_first[1].z0_m - 1.5) < 1e-6 and abs(at_first[1].z1_m - 2.5) < 1e-6

    at_last = [m for m in members if abs(m.p0[0] - 3.61315) < 1e-6]
    assert len(at_last) == 1
    assert abs(at_last[0].z0_m - 0.0) < 1e-6 and abs(at_last[0].z1_m - 2.5) < 1e-6


def test_vertical_batten_unaffected_with_no_openings():
    plan, rw = _vertical_wall(spacing_in=150.0)
    members, _ = frame_wall_furring(plan, rw, [])
    assert len(members) == 2
    assert all(abs(m.z0_m - 0.0) < 1e-6 and abs(m.z1_m - 2.5) < 1e-6 for m in members)


def _horizontal_wall():
    layer = Layer(name="strap", material_ref="spf", thickness=inch(0.75),
                 function=LayerFunction.FURRING,
                 framing=FramingSpec(member="1x4", direction="horizontal",
                                     spacing=inch(60.0)))  # forces exactly two courses
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    band = ((0.0, 0.05), (3.0, 0.05), (3.0, -0.05), (0.0, -0.05))
    resolved = ResolvedLayer(name="strap", material_ref="spf", function="furring",
                             thickness_m=inch(0.75).meters, polygon=band)
    rw = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
        axis=((0.0, 0.0), (3.0, 0.0)), layers=(resolved,), z0_m=0.0, z1_m=1.0,
    )
    return plan, rw


def test_horizontal_course_splits_around_a_window_in_its_band():
    plan, rw = _horizontal_wall()
    # Bottom course covers z in [0, ~0.0889]; a window from z=[0, 0.05] overlaps it and no
    # other course. Centred mid-band so the split leaves a real piece on both sides.
    opening = _opening(center_along_m=1.5, width_m=0.5, height_m=0.05, sill_m=0.0)
    members, findings = frame_wall_furring(plan, rw, [opening])
    assert not findings

    bottom = sorted((m for m in members if abs(m.z0_m - 0.0) < 1e-6), key=lambda m: m.p0[0])
    assert len(bottom) == 2
    assert abs(bottom[0].p1[0] - 1.25) < 1e-6 and abs(bottom[1].p0[0] - 1.75) < 1e-6

    top = [m for m in members if m.z0_m > 0.5]
    assert len(top) == 1
    assert top[0].p0[0] < 0.02 and top[0].p1[0] > 2.98


def test_horizontal_course_unaffected_with_no_openings():
    plan, rw = _horizontal_wall()
    members, _ = frame_wall_furring(plan, rw, [])
    assert len(members) == 2


# --- a banded layer's members live inside its band ---------------------------------------
#
# ``band_tops``/``course_elevations``/``_layout_vertical`` marched members from ``rw.z0_m``
# to ``rw.z1_m`` and never read ``layer.z0_m``/``z1_m``, so even the sauna's ALREADY-banded
# liner framed its 1x4 strapping full height — ~36 lf of it standing in the joist bay above
# a 7'-6" ceiling. Since ``layer_bands.clamp_to_plates`` trims a lifted wall's interior
# layers too, this is the second half of that fix and not an independent nicety.


def test_a_banded_layer_frames_no_member_outside_its_band():
    plan, rw = _vertical_wall(spacing_in=150.0)
    banded = replace(rw.layers[0], z0_m=0.5, z1_m=2.0)
    rw = replace(rw, layers=(banded,))
    members, findings = frame_wall_furring(plan, rw, [])
    assert not findings
    assert members
    assert all(m.z0_m >= 0.5 - 1e-9 and m.z1_m <= 2.0 + 1e-9 for m in members), \
        [(m.z0_m, m.z1_m) for m in members]


def test_a_banded_horizontal_band_runs_its_courses_on_the_walls_own_module():
    """The courses stop at the band; the PHASE does not move with it. ``course_phase`` is an
    unbounded datum, and sliding it to the band's bottom would take a banded liner's courses
    off the module every other band on the wall is registered to."""
    from typehaus.resolve.framing.furring import course_phase

    plan, rw = _horizontal_wall()
    spec = plan.library.resolve_assembly("TEST_ASM").layers[0].framing
    assert course_phase(rw, spec) == 0.0

    banded = replace(rw, layers=(replace(rw.layers[0], z0_m=0.0, z1_m=0.6),))
    members, findings = frame_wall_furring(plan, banded, [])
    assert not findings
    assert members
    assert all(m.z1_m <= 0.6 + 1e-9 for m in members)
    # The starter still sits on the module's own datum, and the band's top edge gets its
    # own nailer — the same two edge rules an unbanded wall gets, one band lower.
    face = 0.0889  # a 1x4 laid flat
    assert min(m.z0_m for m in members) == pytest.approx(0.0)
    assert max(m.z0_m for m in members) == pytest.approx(0.6 - face)


def test_no_catlin_strapping_member_stands_outside_its_layers_band(catlin_model_ro):
    """House-wide, on the real walls: every ``strapping-<layer>`` member is inside the band
    of the layer it is named for."""
    outside = []
    for wall in catlin_model_ro.walls:
        bands = {ly.name: ly.band(wall) for ly in wall.layers}
        for member in wall.members:
            if not member.child_key.startswith("strapping-"):
                continue
            name = member.child_key[len("strapping-"):].rsplit("-", 1)[0]
            band = bands.get(name)
            if band is None:
                continue
            if member.z0_m < band[0] - 1e-9 or member.z1_m > band[1] + 1e-9:
                outside.append(f"{wall.tag}/{member.child_key}")
    assert not outside, outside


def test_the_outer_girt_tier_is_untouched_by_the_trim(catlin_model_ro):
    """The counterweight. A girt tier is OUTBOARD of the studs on an envelope wall, so
    nothing trims it and it still runs the rim band it is there to nail — which is the
    reason ``band_tops`` runs courses to ``rw.z1_m`` rather than to the plate."""
    girts = [(w, m) for w in catlin_model_ro.walls if w.assembly == "EXT_2X6"
             for m in w.members if m.child_key.startswith("strapping-outer-girt-")]
    assert len(girts) > 200, f"only {len(girts)} outer girts; the tier stopped resolving"
    over_plate = [f"{w.tag}/{m.child_key}" for w, m in girts
                  if w.plate_top_z_m is not None and m.z1_m > w.plate_top_z_m + 1e-9]
    assert over_plate, "no girt laps the rim band any more — the trim reached the skin"
