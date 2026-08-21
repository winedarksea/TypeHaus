"""The slice kernel: exact profiles on hand-built solids, then a sweep over both houses."""

from __future__ import annotations

import pytest

from _helpers import CATLIN, STARTER
from typehaus.resolve.geometry_ir import GBox, GMesh, GPart, GPrism
from typehaus.resolve.geometry_slice import (
    CutPlane,
    nearest_station,
    open_chain_count,
    ring_cut_intervals,
    ring_intervals,
    slice_part,
    slice_solid,
    solid_perp_span,
)

UNIT = ((0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0))


def _rounded(profile, places: int = 9):
    return tuple((round(u, places), round(z, places)) for (u, z) in profile.outline)


# --- CutPlane ------------------------------------------------------------------------

def test_axis_names_match_slice_cut_direction():
    """``"x"`` cuts along world x, so u is x and the station measures y."""
    plane = CutPlane(axis="x", station_m=0.5)
    assert plane.u_of((3.0, 7.0)) == 3.0
    assert plane.perp_of((3.0, 7.0)) == 7.0
    other = CutPlane(axis="y", station_m=0.5)
    assert other.u_of((3.0, 7.0)) == 7.0
    assert other.perp_of((3.0, 7.0)) == 3.0


def test_bad_axis_rejected():
    with pytest.raises(ValueError):
        CutPlane(axis="z", station_m=0.0)


# --- GPrism --------------------------------------------------------------------------

def test_prism_flat_top_is_the_exact_rectangle():
    solid = GPrism(ring=UNIT, z0_m=1.0, z1_m=3.0)
    (profile,) = slice_solid(solid, CutPlane(axis="x", station_m=0.5))
    assert _rounded(profile) == ((0.0, 1.0), (2.0, 1.0), (2.0, 3.0), (0.0, 3.0))


def test_prism_raked_top_interpolates_along_the_cut_edge():
    """A prism raked along u: each crossing reads *its own edge's* blended top, exactly.

    ``top`` runs 1 → 5 → 5 → 1 around the ring, so the two crossing edges are the constant
    ones and the cut face is the true 1 → 5 rake, not a sampled approximation of it.
    """
    solid = GPrism(ring=UNIT, z0_m=0.0, z1_m=5.0, top=(1.0, 5.0, 5.0, 1.0))
    (profile,) = slice_solid(solid, CutPlane(axis="x", station_m=0.5))
    assert _rounded(profile) == ((0.0, 0.0), (2.0, 0.0), (2.0, 5.0), (0.0, 1.0))


def test_prism_top_across_the_cut_is_flat_when_the_rake_runs_perpendicular():
    """``top`` 0 → 0 → 4 → 4 rakes across the *station* axis, so the cut face is level."""
    solid = GPrism(ring=UNIT, z0_m=0.0, z1_m=4.0, top=(0.0, 0.0, 4.0, 4.0))
    (profile,) = slice_solid(solid, CutPlane(axis="x", station_m=0.5))
    assert _rounded(profile) == ((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0))


def test_prism_void_splits_the_span_rather_than_perforating_it():
    """A void is full-height by definition, so it cuts the face in two.

    The old section cut ignored ``solid.voids`` outright and drew a slab straight across a
    stair well.
    """
    void = ((0.5, 0.25), (1.5, 0.25), (1.5, 0.75), (0.5, 0.75))
    solid = GPrism(ring=UNIT, z0_m=0.0, z1_m=1.0, voids=(void,))
    left, right = slice_solid(solid, CutPlane(axis="x", station_m=0.5))
    assert _rounded(left) == ((0.0, 0.0), (0.5, 0.0), (0.5, 1.0), (0.0, 1.0))
    assert _rounded(right) == ((1.5, 0.0), (2.0, 0.0), (2.0, 1.0), (1.5, 1.0))


def test_prism_void_split_keeps_the_rake():
    """A split raked prism re-interpolates its top over each surviving sub-span."""
    solid = GPrism(ring=UNIT, z0_m=0.0, z1_m=5.0, top=(1.0, 5.0, 5.0, 1.0),
                   voids=(((0.5, 0.25), (1.5, 0.25), (1.5, 0.75), (0.5, 0.75)),))
    left, right = slice_solid(solid, CutPlane(axis="x", station_m=0.5))
    # The parent span rises 1 → 5 over u 0 → 2, so each sub-span reads its own share.
    assert _rounded(left)[2:] == ((0.5, 2.0), (0.0, 1.0))
    assert _rounded(right)[2:] == ((2.0, 5.0), (1.5, 4.0))


def test_prism_outside_the_span_is_rejected_in_o1():
    solid = GPrism(ring=UNIT, z0_m=0.0, z1_m=1.0)
    assert solid_perp_span(solid, CutPlane(axis="x", station_m=9.0)) == (0.0, 1.0)
    assert slice_solid(solid, CutPlane(axis="x", station_m=9.0)) == ()


# --- GBox ----------------------------------------------------------------------------

def _member(u0, u1, y, half_width, z0_a, z0_b, z1_a, z1_b):
    """A raked member running along world x at station ``y``, ``half_width`` each side."""
    bottom = ((u0, y - half_width, z0_a), (u1, y - half_width, z0_b),
              (u1, y + half_width, z0_b), (u0, y + half_width, z0_a))
    top = ((u0, y - half_width, z1_a), (u1, y - half_width, z1_b),
           (u1, y + half_width, z1_b), (u0, y + half_width, z1_a))
    return GBox(corners_bottom=bottom, corners_top=top)


def test_box_in_the_cut_plane_yields_the_raked_parallelogram():
    """The rafter case: the two long edges contribute nothing, the two ends cross at t=0.5.

    This is the parallelogram ``_emit_raked_rafter`` hand-built, with no special case.
    """
    solid = _member(0.0, 4.0, y=1.0, half_width=0.05, z0_a=0.0, z0_b=2.0,
                    z1_a=0.3, z1_b=2.3)
    (profile,) = slice_solid(solid, CutPlane(axis="x", station_m=1.0))
    assert _rounded(profile) == ((0.0, 0.0), (4.0, 2.0), (4.0, 2.3), (0.0, 0.3))


def test_box_across_the_cut_shows_its_section_face():
    solid = _member(0.0, 4.0, y=1.0, half_width=0.05, z0_a=0.0, z0_b=0.0,
                    z1_a=1.0, z1_b=1.0)
    (profile,) = slice_solid(solid, CutPlane(axis="y", station_m=2.0))
    assert _rounded(profile) == ((0.95, 0.0), (1.05, 0.0), (1.05, 1.0), (0.95, 1.0))


def test_box_end_face_exactly_on_the_plane_is_nudged_not_slabbed():
    """A cut landing on a member's own end face must not produce a degenerate slab."""
    solid = _member(0.0, 4.0, y=1.0, half_width=0.05, z0_a=0.0, z0_b=0.0,
                    z1_a=1.0, z1_b=1.0)
    (profile,) = slice_solid(solid, CutPlane(axis="y", station_m=0.0))
    us = sorted({round(u, 6) for (u, _z) in profile.outline})
    assert us == [0.95, 1.05]


# --- GMesh ---------------------------------------------------------------------------

def _box_mesh(x0, x1, y0, y1, z0, z1) -> GMesh:
    corners = [(x, y, z) for z in (z0, z1) for (x, y) in
               ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    faces = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6),
             (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2),
             (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0)]
    return GMesh(positions=tuple(corners), triangles=tuple(faces))


def test_mesh_cut_closes_into_a_ring():
    mesh = _box_mesh(0.0, 2.0, 0.0, 1.0, 0.0, 3.0)
    plane = CutPlane(axis="x", station_m=0.5)
    (profile,) = slice_solid(mesh, plane)
    assert open_chain_count(mesh, plane) == 0
    # The ring picks up collinear vertices where the cut crosses a facet diagonal — real
    # points on the real outline, so the contract is the extent, not the vertex count.
    us = [u for (u, _z) in profile.outline]
    zs = [z for (_u, z) in profile.outline]
    assert (round(min(us), 6), round(max(us), 6)) == (0.0, 2.0)
    assert (round(min(zs), 6), round(max(zs), 6)) == (0.0, 3.0)


def test_open_mesh_chain_is_discarded_never_fabricated():
    """A single dangling triangle cannot close, so it draws nothing and is counted."""
    mesh = GMesh(positions=((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
                 triangles=((0, 1, 2),))
    plane = CutPlane(axis="x", station_m=0.5)
    assert slice_solid(mesh, plane) == ()
    assert open_chain_count(mesh, plane) == 1


# --- parts and stations ---------------------------------------------------------------

def test_slice_part_walks_every_solid():
    part = GPart(key="layer:test", material_key="spf", solids=(
        GPrism(ring=UNIT, z0_m=0.0, z1_m=1.0),
        GPrism(ring=UNIT, z0_m=2.0, z1_m=3.0),
    ))
    assert len(slice_part(part, CutPlane(axis="x", station_m=0.5))) == 2


def test_nearest_station_picks_the_representative_member():
    plane = CutPlane(axis="x", station_m=1.0)
    solids = [_member(0.0, 1.0, y=0.4, half_width=0.0, z0_a=0.0, z0_b=0.0,
                      z1_a=1.0, z1_b=1.0),
              _member(0.0, 1.0, y=0.9, half_width=0.0, z0_a=0.0, z0_b=0.0,
                      z1_a=1.0, z1_b=1.0)]
    assert nearest_station(solids, plane) == pytest.approx(0.9)


def test_nearest_station_is_none_when_something_already_crosses():
    plane = CutPlane(axis="x", station_m=1.0)
    solids = [GPrism(ring=UNIT, z0_m=0.0, z1_m=1.0)]
    assert nearest_station(solids, plane) is None


# --- the shim -------------------------------------------------------------------------

def test_shim_matches_the_kernel_on_every_catlin_wall_layer(catlin_model):
    """The seven detail callers must not move underneath the migration.

    Equivalence holds everywhere *except* a ring with a vertex exactly on the plane, which
    is the one case the half-open rule deliberately changes (see ``_crosses_edge``) — those
    are asserted separately below rather than swept under a tolerance.
    """
    checked = 0
    for wall in catlin_model.walls:
        (x0, y0), (x1, y1) = wall.axis
        for direction in ("x", "y"):
            station = ((y0 + y1) / 2.0) if direction == "x" else ((x0 + x1) / 2.0)
            plane = CutPlane(axis=direction, station_m=station)
            for layer in wall.layers:
                if any(abs(plane.perp_of(p) - station) < 1e-12 for p in layer.polygon):
                    continue  # on-plane vertex: the documented divergence
                old = ring_cut_intervals(layer.polygon, direction, station)
                new = ring_intervals(layer.polygon, plane)
                assert [(round(a, 9), round(b, 9)) for a, b in old] == \
                       [(round(a, 9), round(b, 9)) for a, b in new], \
                    f"{wall.tag}/{layer.name} at {direction}={station}"
                checked += 1
    assert checked > 100


def test_the_half_open_rule_is_where_the_two_disagree():
    """A vertex on the plane whose neighbours straddle it: the old rule counts it twice.

    Two crossings at the same u make the total odd, and even-odd pairing then pairs the
    doubled vertex with itself and **silently drops the rest of the span**. The half-open
    rule gives the vertex to exactly one of its edges, so the count is provably even.
    Nudging keeps IR callers away from the case entirely; the shim keeps the old answer for
    the seven detail callers until they move.
    """
    ring = ((0.0, -1.0), (2.0, 0.0), (4.0, 1.0), (4.0, -1.0))
    assert ring_cut_intervals(ring, "x", 0.0) == [(2.0, 2.0)]           # a span lost
    assert ring_intervals(ring, CutPlane(axis="x", station_m=0.0)) == [(2.0, 4.0)]


# --- the sweep ------------------------------------------------------------------------

@pytest.mark.parametrize("house", [CATLIN, STARTER], ids=["catlin", "starter"])
def test_no_open_chains_anywhere_in_either_house(house):
    """Every mesh in the geometry IR closes when cut, at four stations across the plan.

    An open chain means the kernel would have had to invent a closing edge — a drawing that
    claims a solid where the model has a hole. Zero, both houses, or the mesh branch is not
    trustworthy.
    """
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    result = load_plan(house)
    model, _findings = resolve(result.plan)
    meshes = [(element, part, solid)
              for element in model.geometry.elements
              for part in element.parts
              for solid in part.solids
              if isinstance(solid, GMesh)]
    if not meshes:
        pytest.skip(f"{house.name} builds no meshes")

    xs = [p[0] for (_e, _p, mesh) in meshes for p in mesh.positions]
    ys = [p[1] for (_e, _p, mesh) in meshes for p in mesh.positions]
    offenders: list[str] = []
    for axis, values in (("x", ys), ("y", xs)):
        lo, hi = min(values), max(values)
        for fraction in (0.2, 0.4, 0.6, 0.8):
            plane = CutPlane(axis=axis, station_m=lo + (hi - lo) * fraction)
            for (element, part, mesh) in meshes:
                if open_chain_count(mesh, plane):
                    offenders.append(f"{element.uid}/{part.key} at {axis}={plane.station_m}")
    assert not offenders, offenders[:10]


def test_the_slice_kernel_imports_no_third_party():
    """Pyodide runs the whole engine in the browser, and the IR core has to survive that.

    Not a whole-package rule: ``resolve/`` *does* reach for shapely in a handful of
    construction modules today. What must hold is that the slice kernel and everything it
    pulls in stay stdlib-only — that is the reason it lives here rather than in
    ``emit/draw/``, where two modules already import shapely and no test would catch a
    third.
    """
    import ast
    import pathlib
    import sys

    src = pathlib.Path(__file__).resolve().parents[1] / "src"
    allowed = set(sys.stdlib_module_names)
    seen: set[str] = set()
    offenders: list[str] = []

    def visit(module: str) -> None:
        if module in seen:
            return
        seen.add(module)
        path = src / (module.replace(".", "/") + ".py")
        if not path.is_file():
            return
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module] if node.module and node.level == 0 else []
            else:
                continue
            for name in names:
                if name.split(".")[0] == "typehaus":
                    visit(name)
                elif name.split(".")[0] not in allowed:
                    offenders.append(f"{module} imports {name}")

    visit("typehaus.resolve.geometry_slice")
    assert offenders == [], offenders
    assert "typehaus.resolve.geometry_ir" in seen, "the walk found nothing to check"
