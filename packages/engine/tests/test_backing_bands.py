"""Authored ``WallBacking`` bands, at the solver seam.

Same minimal wall double ``test_solver_units`` uses, for the same reason: a band's geometry
is a property of the emitter, not of any authored house.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch
from typehaus.resolve.framing.backing_panels import BackingBand, band_face_height_m
from typehaus.resolve.framing.openings import WallOpening
from typehaus.resolve.framing.solver import frame_wall
from typehaus.resolve.model import ResolvedWall

WALL_LEN_M = 4.0


def _wall_and_plan() -> tuple[SimpleNamespace, ResolvedWall]:
    layer = Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                  function=LayerFunction.STRUCTURE,
                  framing=FramingSpec(member="2x6"))
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    rw = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
        axis=((0.0, 0.0), (WALL_LEN_M, 0.0)), layers=(), z0_m=0.0, z1_m=2.5,
    )
    return plan, rw


def _band(**overrides) -> BackingBand:
    base = dict(tag="BK-TEST", wall_ref="W-TEST", face="left", start_m=None, length_m=None,
                elevation_m=inch(32).meters, height_m=inch(12).meters,
                profile="0.75x12.0", material_ref="struct-1-plywood", purpose="grab bar")
    base.update(overrides)
    return BackingBand(**base)


def _backing(members):
    return sorted((m for m in members if m.child_key.startswith("backing-")),
                  key=lambda m: m.p0[0])


def _covers(pieces, station_m: float) -> bool:
    return any(min(m.p0[0], m.p1[0]) < station_m < max(m.p0[0], m.p1[0]) for m in pieces)


def test_a_full_run_band_is_fitted_between_the_studs():
    """Between, not across: a flush board run through the studs is a dado in each."""
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=[], backing=(_band(),))
    bands = _backing(members)
    studs = [m for m in members if m.category == "stud"]
    assert len(bands) == len(studs) - 1, "one block per bay"
    half = inch(0.75).meters
    for band in bands:
        assert band.category == "blocking"
        assert band.profile == "0.75x12.0"
        assert band.material == "struct-1-plywood"
        # Elevation is off the FRAMING base, not the stud bearing line a plate above it.
        assert abs(band.z0_m - inch(32).meters) < 1e-9
        assert abs(band.z1_m - inch(44).meters) < 1e-9
        assert not any(_covers([band], stud.p0[0] + d) for stud in studs for d in (-half, 0, half))
    assert 0.85 * WALL_LEN_M < sum(b.length_m for b in bands) < WALL_LEN_M


def test_a_furred_band_runs_over_the_studs_proud_of_their_face():
    plan, rw = _wall_and_plan()
    nailer = _band(profile="2x4", height_m=inch(3.5).meters, furred=True)
    bands = _backing(frame_wall(plan, rw, openings=[], backing=(nailer,)))
    assert len(bands) == 1 and abs(bands[0].length_m - WALL_LEN_M) < 1e-9


def test_no_backing_is_emitted_by_default():
    plan, rw = _wall_and_plan()
    assert not _backing(frame_wall(plan, rw, openings=[]))


def test_a_partial_run_emits_only_over_that_run():
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=[],
                         backing=(_band(start_m=1.0, length_m=1.5),))
    bands = _backing(members)
    assert abs(bands[0].p0[0] - 1.0) < 1e-9 and abs(bands[-1].p1[0] - 2.5) < 1e-9


def test_a_run_authored_past_the_wall_end_is_trimmed_not_extended():
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=[],
                         backing=(_band(start_m=3.0, length_m=9.0),))
    bands = _backing(members)
    assert abs(bands[0].p0[0] - 3.0) < 1e-9
    assert WALL_LEN_M - inch(1.5).meters - 1e-9 <= bands[-1].p1[0] <= WALL_LEN_M


def test_an_opening_the_band_runs_through_splits_it():
    """A board across a window is one the framer cannot install."""
    plan, rw = _wall_and_plan()
    # Sill 24", head 84": the 32"-44" band runs straight through it.
    opening = WallOpening(center_m=2.0, width_m=1.0, height_m=inch(60).meters,
                          sill_m=inch(24).meters, is_door=False)
    members = frame_wall(plan, rw, openings=[opening], backing=(_band(),))
    bands = _backing(members)
    assert not any(_covers(bands, x) for x in (1.51, 2.0, 2.49))
    assert _covers(bands, 1.0) and _covers(bands, 3.0)


def test_an_opening_the_band_passes_under_does_not_split_it():
    """Backing keeps running under a high window; that is where a framer wants it."""
    plan, rw = _wall_and_plan()
    opening = WallOpening(center_m=2.0, width_m=1.0, height_m=inch(36).meters,
                          sill_m=inch(60).meters, is_door=False)
    members = frame_wall(plan, rw, openings=[opening], backing=(_band(),))
    bands = _backing(members)
    assert any(1.5 < m.p0[0] < 2.5 for m in bands), "blocks continue under the window"


def test_a_band_above_the_stud_top_is_dropped_not_flown_through_the_roof():
    plan, rw = _wall_and_plan()
    # The wall is 2.5 m tall; a band at 9'-0" has no studs left to fasten to.
    members = frame_wall(plan, rw, openings=[],
                         backing=(_band(elevation_m=inch(108).meters),))
    assert not _backing(members)


def test_the_profile_string_needs_its_decimal():
    """``cross_section`` falls back SILENTLY, so the fallback is pinned here on purpose."""
    assert abs(band_face_height_m("0.75x12.0") - inch(12).meters) < 1e-9
    assert abs(band_face_height_m("2x8") - inch(7.25).meters) < 1e-9
    # "3/4x12" does not parse and reads as a 2x6 — the trap the model docstring warns about.
    assert abs(band_face_height_m("3/4x12") - inch(5.5).meters) < 1e-9


def test_a_band_over_a_door_head_still_breaks_at_its_header():
    """The rough head is not the top of the framing, and the header fills the wall depth.

    A band that clears a 7'-0" door's head by ten inches lands square in the header above
    it. Reported by ``structural.member_interference`` the first time this ran at catlin.
    """
    plan, rw = _wall_and_plan()
    door = WallOpening(center_m=2.0, width_m=0.9, height_m=inch(84).meters,
                       sill_m=0.0, is_door=True)
    high = _band(elevation_m=inch(86).meters, height_m=inch(7.25).meters, profile="2x8")
    members = frame_wall(plan, rw, openings=[door], backing=(high,))
    headers = [m for m in members if m.category == "header"]
    assert headers, "the fixture must actually frame a header for this to mean anything"
    bands = _backing(members)
    assert not _covers(bands, 2.0), "the band must stop each side of the header"
    assert _covers(bands, 1.0) and _covers(bands, 3.0)


def test_a_band_clear_of_the_framing_is_not_broken_by_it():
    """Under a high window's rough sill there is nothing solid, so the band runs on."""
    plan, rw = _wall_and_plan()
    window = WallOpening(center_m=2.0, width_m=0.9, height_m=inch(24).meters,
                         sill_m=inch(72).meters, is_door=False)
    members = frame_wall(plan, rw, openings=[window], backing=(_band(),))
    assert any(1.55 < m.p0[0] < 2.45 for m in _backing(members))
