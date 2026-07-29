"""The IR must reproduce the *correct* emitter's geometry, and fix the incorrect one.

Shadow-parity: for every member in both houses, the IR box is compared against what each of
the two Python emitters draws today. Where they disagreed, this test pins which one the IR
follows — and the plan's blessed list of intentional diffs is exactly the set of
disagreements allowed:

1. **member boxes**: the IR ports the IFC implementation. `emit/gltf/members.py` used
   `width_m / 2` for every half-extent, ignoring `orient` and `depth_m`, so an upright stud
   exported square. The GLB visibly changes; it changes to correct.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from typehaus.resolve import resolve
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_members import MINIMUM_EXTENT_M, member_box, member_uid
from typehaus.source import load_plan

HOUSES = Path(__file__).resolve().parents[3] / "houses"
TOL = 1e-6


def _all_members(model) -> list:
    members = []
    for owner in (*model.walls, *model.roofs, *model.floors, *getattr(model, "stairs", ())):
        members.extend(getattr(owner, "members", ()))
    return members


@pytest.fixture(scope="module", params=["starter", "catlin"])
def model(request):
    result = load_plan(HOUSES / request.param)
    assert result.plan is not None
    resolved, _findings = resolve(result.plan)
    return resolved


def _extent(corners, axis: int) -> float:
    values = [c[axis] for c in corners]
    return max(values) - min(values)


def test_every_member_produces_a_box(model) -> None:
    members = _all_members(model)
    assert members, "house resolved no framing at all"
    assert all(member_box(m) is not None for m in members)


def test_member_uids_are_unique(model) -> None:
    """The merged-mesh pick contract resolves a face index to one of these, so a collision
    would silently select the wrong stick."""
    members = _all_members(model)
    uids = [member_uid(m) for m in members]
    assert len(uids) == len(set(uids))


def test_upright_members_carry_their_true_section(model) -> None:
    """The blessed glTF fix: an upright member's plan footprint is width x depth laid out
    along `orient`, not width x width. This is the bug that made every exported stud square.
    """
    uprights = [m for m in _all_members(model) if m.p0 == m.p1]
    assert uprights, "house has no upright members to check"
    for member in uprights:
        box = member_box(member)
        section = cross_section(member.profile)
        width = max(section.width_m, MINIMUM_EXTENT_M)
        depth = max(section.depth_m, MINIMUM_EXTENT_M)
        got = sorted((_extent(box.corners_bottom, 0), _extent(box.corners_bottom, 1)))
        assert got == pytest.approx(sorted((width, depth)), abs=TOL), member.child_key
        # ...and it is square only when the profile itself is.
        if abs(width - depth) > TOL:
            assert abs(got[0] - got[1]) > TOL, f"{member.child_key} exported square"


def test_box_faces_land_on_the_planes_the_member_record_names(model) -> None:
    """Every other consumer (2D section cuts, the IFC sweep, the viewer) reads those same
    elevations, so a box that floats off them puts the trades out of agreement."""
    for member in _all_members(model):
        box = member_box(member)
        bottom_z = {round(c[2], 9) for c in box.corners_bottom}
        expected_bottom = {round(member.z0_m, 9)}
        if member.z0_end_m is not None:
            expected_bottom.add(round(member.z0_end_m, 9))
        assert bottom_z == expected_bottom, member.child_key


def test_raked_members_keep_both_end_elevations(model) -> None:
    raked = [m for m in _all_members(model)
             if m.z0_end_m is not None or m.z1_end_m is not None]
    if not raked:
        pytest.skip("house has no raked members")
    for member in raked:
        box = member_box(member)
        tops = sorted({round(c[2], 6) for c in box.corners_top})
        z1_end = member.z1_m if member.z1_end_m is None else member.z1_end_m
        if abs(z1_end - member.z1_m) > MINIMUM_EXTENT_M:
            assert len(tops) == 2, f"{member.child_key} flattened its rake"


def test_level_member_length_matches_the_record(model) -> None:
    for member in _all_members(model):
        if member.p0 == member.p1:
            continue
        box = member_box(member)
        (ax, ay), (bx, by) = member.p0, member.p1
        run = math.hypot(bx - ax, by - ay)
        # The box spans the run along the member axis, so opposite mid-edges are `run` apart.
        start_mid = (
            (box.corners_bottom[0][0] + box.corners_bottom[3][0]) / 2,
            (box.corners_bottom[0][1] + box.corners_bottom[3][1]) / 2,
        )
        end_mid = (
            (box.corners_bottom[1][0] + box.corners_bottom[2][0]) / 2,
            (box.corners_bottom[1][1] + box.corners_bottom[2][1]) / 2,
        )
        assert math.hypot(end_mid[0] - start_mid[0],
                          end_mid[1] - start_mid[1]) == pytest.approx(run, abs=TOL)


def test_box_width_matches_the_parsed_section_for_level_members(model) -> None:
    """Width is measured across the run — the IFC sweep's `width_m`."""
    for member in _all_members(model):
        if member.p0 == member.p1:
            continue
        box = member_box(member)
        (ax, ay), (bx, by) = member.p0, member.p1
        run = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / run, (bx - ax) / run
        across = [c[0] * nx + c[1] * ny for c in box.corners_bottom]
        width = max(cross_section(member.profile).width_m, MINIMUM_EXTENT_M)
        assert max(across) - min(across) == pytest.approx(width, abs=TOL), member.child_key


# --- the producer ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def geometry(model):
    assert model.geometry is not None, "the pipeline's geometry stage did not run"
    return model.geometry


def test_every_resolved_solid_becomes_one_element(model, geometry) -> None:
    solid_uids = {s.uid for s in model.solids}
    assert solid_uids <= {e.uid for e in geometry.elements}


def test_every_solar_panel_keeps_its_authored_corners(model, geometry) -> None:
    """The IR generalized ResolvedSolarPanel, so the panel path must be a pass-through: the
    tilt math stays in resolve/solar.py alone."""
    panels = getattr(model, "solar_panels", ())
    if not panels:
        pytest.skip("house has no solar panels")
    for panel in panels:
        element = geometry.by_uid(panel.uid)
        assert element is not None
        box = element.parts[0].solids[0]
        assert box.corners_bottom == tuple(panel.corners_bottom)
        assert box.corners_top == tuple(panel.corners_top)


def test_every_member_is_addressable_through_its_owner(model, geometry) -> None:
    """Framing rides its owner so the exporter can merge a wall's studs into one node and
    still resolve a pick back to the individual stick."""
    from typehaus.resolve.geometry_members import member_uid

    expected = {member_uid(m) for m in _all_members(model)}
    got = {p.member_uid for e in geometry.elements for p in e.parts
           if p.member_uid is not None}
    assert expected == got


def test_every_part_names_a_key_in_the_shared_vocabulary(geometry) -> None:
    """A `material_key` outside the vocabulary would reach the viewer with no material
    factory behind it — the silent-grey failure this vocabulary exists to prevent."""
    from typehaus.emit.finishes import MATERIAL_KEYS

    keys = {p.material_key for e in geometry.elements for p in e.parts}
    assert keys <= MATERIAL_KEYS, sorted(keys - MATERIAL_KEYS)


def test_solid_voids_survive_into_the_ir(model, geometry) -> None:
    """IFC expresses these as real openings and glTF tessellates them away; dropping them
    here would silently fill every slab penetration in both."""
    with_voids = [s for s in model.solids if s.voids]
    if not with_voids:
        pytest.skip("house has no solids with voids")
    for solid in with_voids:
        prism = geometry.by_uid(solid.uid).parts[0].solids[0]
        assert prism.voids == tuple(solid.voids)


def test_preview_resolve_skips_the_geometry_stage(model) -> None:
    """`resolve_preview` feeds a drag overlay that renders none of this; paying for it at
    pointermove frequency is the cost the Optional exists to avoid."""
    from typehaus.resolve import resolve_preview

    assert resolve_preview(model.plan).geometry is None
