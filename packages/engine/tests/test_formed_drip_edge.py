"""The formed drip edge's section: one ring every reader sweeps the same way.

``trim_bands.formed_drip_legs`` makes the four legs, ``geometry_members._ring_sweep`` sweeps
them, the section slicer cuts them, and IFC writes them — pinned here against each other.
"""

from __future__ import annotations

import math

import pytest

from typehaus.resolve.geometry_ir import GSweep
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.geometry_slice import CutPlane, slice_solid, sweep_mesh
from typehaus.resolve.model import FramedMember, SeatCut
from typehaus.resolve.trim_bands import formed_drip_legs

IN = 0.0254
SLOPE = 0.5


def _legs(slope: float = SLOPE):
    return formed_drip_legs(
        slope=slope, deck_top_at_edge_m=0.70 * IN, flange_back_m=-3.25 * IN,
        bend_m=-1.25 * IN, nose_floor_m=1.055 * IN, face_in_m=0.833 * IN,
        face_bottom_m=-3.26 * IN, kick_m=0.5 * IN, shell_m=0.4167 * IN)


def _convex(quad) -> bool:
    signs = set()
    for i in range(4):
        (ax, ay), (bx, by), (cx, cy) = quad[i], quad[(i + 1) % 4], quad[(i + 2) % 4]
        cross = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
        if abs(cross) > 1e-15:
            signs.add(cross > 0)
    return len(signs) == 1


@pytest.mark.parametrize("slope", [SLOPE, 0.0])
def test_every_leg_is_a_convex_quad(slope) -> None:
    legs = _legs(slope)
    assert set(legs) == {"flange", "nose", "face", "kick"}
    assert all(_convex(quad) for quad in legs.values())


def test_the_flange_lies_on_the_pitched_deck_one_shell_thick() -> None:
    """Underside on ``deck_top - slope * u``; thickness a shell measured square to the slope."""
    (u0, z0), (u1, z1), (u2, z2), (u3, z3) = _legs()["flange"]
    for u, z in ((u0, z0), (u1, z1)):
        assert z == pytest.approx(0.70 * IN - SLOPE * u)
    assert z3 - z0 == pytest.approx(0.4167 * IN * math.hypot(1.0, SLOPE))
    assert (u1 - u0) == pytest.approx(2.0 * IN)


def test_the_nose_never_rises_outward_and_clears_its_floor() -> None:
    (u_in, z_in), (u_out, z_out), _top_out, _top_in = _legs()["nose"]
    assert u_out > u_in and z_out <= z_in
    assert min(z_in, z_out) >= 1.055 * IN - 1e-12


def test_the_kick_turns_out_and_down_at_45_degrees() -> None:
    (u0, z0), (u1, z1), _c, _d = _legs()["kick"]
    assert u1 - u0 == pytest.approx(z0 - z1) == pytest.approx(0.5 * IN)


def _ringed(rise: float = 0.0) -> FramedMember:
    quad = _legs()["face"]
    return FramedMember(
        parent_uid="R", child_key="eave-hi-drip-edge-face", category="drip_edge",
        profile="0.4167x4.3 panel", p0=(1.0, 0.0), p1=(1.0, 3.0), z0_m=5.0, z1_m=5.11,
        length_m=3.0, z0_end_m=5.0 + rise, z1_end_m=5.11 + rise,
        section_ring=tuple((-(u - 0.02), z) for u, z in quad))


def test_ring_sweep_matches_its_own_section_cut() -> None:
    """Cut square to the run, a level sweep's section IS its ring, placed at the axis."""
    member = _ringed()
    solid = member_solid(member)
    assert isinstance(solid, GSweep)
    profile, = slice_solid(solid, CutPlane(axis="x", station_m=1.5))
    expected = {(round(1.0 + s, 9), round(5.0 + t, 9)) for s, t in member.section_ring}
    # The run goes +y, whose left normal is -x: a ring's +s lands at smaller x.
    mirrored = {(round(1.0 - s, 9), round(5.0 + t, 9)) for s, t in member.section_ring}
    got = {(round(u, 9), round(z, 9)) for u, z in profile.outline}
    assert got == mirrored and got != expected


def test_a_rising_sweep_is_cut_where_the_station_has_carried_it() -> None:
    """A rake piece climbs: halfway along, its section sits half the rise higher."""
    flat = slice_solid(member_solid(_ringed()), CutPlane(axis="x", station_m=1.5))[0]
    risen = slice_solid(member_solid(_ringed(rise=0.6)), CutPlane(axis="x", station_m=1.5))[0]
    assert min(z for _, z in risen.outline) == pytest.approx(
        min(z for _, z in flat.outline) + 0.3)
    mesh_cut = slice_solid(sweep_mesh(member_solid(_ringed(rise=0.6))),
                           CutPlane(axis="x", station_m=1.5))[0]
    assert min(z for _, z in mesh_cut.outline) == pytest.approx(
        min(z for _, z in risen.outline))


# --- IFC parity: the written solid bounds exactly what the IR sweeps --------------------

def _gsweep_bbox(solid: GSweep):
    points = list(solid.profile) + [tuple(a + b for a, b in zip(p, solid.extrude, strict=True))
                                    for p in solid.profile]
    return tuple((min(c), max(c)) for c in zip(*points, strict=True))


def _ifc_bbox(rep):
    item, = rep.Items
    if item.is_a("IfcFacetedBrep"):
        points = [tuple(p.Coordinates) for face in item.Outer.CfsFaces
                  for bound in face.Bounds for p in bound.Bound.Polygon]
    else:
        pos = item.Position
        origin = pos.Location.Coordinates
        z = pos.Axis.DirectionRatios
        x = pos.RefDirection.DirectionRatios
        y = (z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0])
        points = []
        for px, py in (p.Coordinates for p in item.SweptArea.OuterCurve.Points):
            base = tuple(o + px * a + py * b for o, a, b in zip(origin, x, y, strict=True))
            points += [base, tuple(c + item.Depth * d for c, d in zip(base, z, strict=True))]
    return tuple((min(c), max(c)) for c in zip(*points, strict=True))


def _rafter() -> FramedMember:
    return FramedMember(
        parent_uid="R", child_key="rafter-0", category="rafter", profile="2x10",
        p0=(0.0, 0.0), p1=(3.0, 0.0), z0_m=2.5, z1_m=2.74, length_m=3.35,
        z0_end_m=4.0, z1_end_m=4.24,
        seat=SeatCut(plate_top_z_m=2.45, heel=(0.14, 0.0), seat_run_m=0.14))


@pytest.mark.parametrize("member", [_rafter(), _ringed(), _ringed(rise=0.6)],
                         ids=["rafter", "eave-leg", "rake-leg"])
def test_ifc_solid_bounds_the_ir_sweep(member) -> None:
    pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import lowlevel as ll
    from typehaus.emit.ifc.roof import member_representation

    f = ll.new_file("test")
    ll.create_entity(f, "IfcProject", name="test")
    body = ll.add_context(f)
    rep = member_representation(f, body, member)
    solid = member_solid(member)
    assert isinstance(solid, GSweep)
    for (lo, hi), (want_lo, want_hi) in zip(_ifc_bbox(rep), _gsweep_bbox(solid), strict=True):
        assert lo == pytest.approx(want_lo, abs=1e-9)
        assert hi == pytest.approx(want_hi, abs=1e-9)
