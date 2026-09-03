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
from typehaus.resolve.framing.profiles import cross_section, plan_cross_section_m
from typehaus.resolve.geometry_members import MINIMUM_EXTENT_M, member_box, member_uid
from typehaus.source import load_plan
from _helpers import HOUSES

TOL = 1e-6


def _all_members(model) -> list:
    members = []
    for owner in (*model.walls, *model.roofs, *model.floors, *getattr(model, "stairs", ()),
                  # Braces (and wedges, the same record) host themselves and reach the IR the
                  # same way; before they did, a knee brace's diagonal was in the model and in
                  # neither the IR nor any section.
                  *getattr(model, "braces", ())):
        members.extend(getattr(owner, "members", ()))
    return members


def _boxable_members(model) -> list:
    """Members `member_box()` can describe. Polygonal stair treads (winders) carry a
    `plan_outline` instead — a trapezoid isn't a box — and are emitted as a GPrism by the
    producer rather than approximated here; see `member_box`'s own docstring."""
    return [m for m in _all_members(model) if m.plan_outline is None]


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
    members = _boxable_members(model)
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
    uprights = [m for m in _boxable_members(model) if m.p0 == m.p1]
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
    for member in _boxable_members(model):
        box = member_box(member)
        bottom_z = {round(c[2], 9) for c in box.corners_bottom}
        expected_bottom = {round(member.z0_m, 9)}
        if member.z0_end_m is not None:
            expected_bottom.add(round(member.z0_end_m, 9))
        assert bottom_z == expected_bottom, member.child_key


def test_raked_members_keep_both_end_elevations(model) -> None:
    raked = [m for m in _boxable_members(model)
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
    for member in _boxable_members(model):
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
    """Width is measured across the run — the IFC sweep's `width_m`.

    *Which* section face lands across the run is the member's own business: one lying flat
    shows the wide `depth_m` there and stands only `width_m` tall — a plate must not come
    out a 1.5" square rod running along the wall instead of a 1.5" x 5.5" board lying on it.
    """
    for member in _boxable_members(model):
        if member.p0 == member.p1:
            continue
        box = member_box(member)
        (ax, ay), (bx, by) = member.p0, member.p1
        run = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / run, (bx - ax) / run
        across = [c[0] * nx + c[1] * ny for c in box.corners_bottom]
        section = cross_section(member.profile)
        # A tapered member (a drainage wedge) authors its own plan width, because its own
        # vertical extent matches neither section dimension and so cannot classify it.
        width = max(member.plan_width_m
                    or plan_cross_section_m(section, member.z1_m - member.z0_m),
                    MINIMUM_EXTENT_M)
        assert max(across) - min(across) == pytest.approx(width, abs=TOL), member.child_key


def test_a_flat_laid_member_lies_on_its_wide_face(model) -> None:
    """The regression the width test above cannot see on its own.

    Every plate, rough sill and blocking course in both houses must come out `depth_m` across
    the run and `width_m` tall — a board lying down, not a stick. Asserted over the real
    houses rather than a fixture because the failure mode was a rule that only looked right
    for the categories somebody remembered to list.
    """
    flat = 0
    for member in _boxable_members(model):
        if member.p0 == member.p1:
            continue
        section = cross_section(member.profile)
        if abs(member.z1_m - member.z0_m - section.width_m) > TOL:
            continue  # standing on edge, or a tapered band with no constant section
        flat += 1
        box = member_box(member)
        (ax, ay), (bx, by) = member.p0, member.p1
        run = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / run, (bx - ax) / run
        across = [c[0] * nx + c[1] * ny for c in box.corners_bottom]
        assert max(across) - min(across) == pytest.approx(
            max(section.depth_m, MINIMUM_EXTENT_M), abs=TOL), member.child_key
    assert flat > 0, "a house with no flat-laid member has no plates — the fixture is wrong"


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


# --- the first emitter switch ----------------------------------------------------------

def test_the_glb_member_mesh_now_carries_the_true_section(model) -> None:
    """`emit/gltf/members.py` builds its box from the IR rather than its own math.

    The bug this pins: the old path used `width_m / 2` as *every* half-extent, so an upright
    2x6 stud exported as a 5.5" square post whose section ignored the wall it stood in — while
    IFC exported the same stud correctly. That is the divergence that made
    WHOLE_HOUSE_GLB_PRIMARY unsafe to turn on.
    """
    from typehaus.emit.gltf.members import _add_member
    from typehaus.emit.gltf.mesh import _MeshBuilder

    uprights = [m for m in _all_members(model) if m.p0 == m.p1]
    assert uprights
    rectangular = 0
    for member in uprights:
        section = cross_section(member.profile)
        builder = _MeshBuilder()
        _add_member(builder, member)
        points = [p for positions, _ in builder._buckets.values() for p in positions]
        assert points, member.child_key
        # glTF swizzles (x, y, z) → (x, z, -y), so plan x/y are components 0 and 2.
        got = sorted((max(p[0] for p in points) - min(p[0] for p in points),
                      max(p[2] for p in points) - min(p[2] for p in points)))
        want = sorted((section.width_m, section.depth_m))
        assert got == pytest.approx(want, abs=TOL), member.child_key
        if abs(section.width_m - section.depth_m) > TOL:
            rectangular += 1
    assert rectangular, "no non-square profile in this house to prove the fix against"


def test_a_member_box_is_still_twelve_triangles(model) -> None:
    """The merged-mesh pick contract (TRIANGLES_PER_MEMBER_BOX in memberBox.ts /
    memberPicking.ts) resolves a face index by dividing by 12. Changing the primitive's
    triangle count would silently select the wrong member."""
    from typehaus.emit.gltf.members import _add_member
    from typehaus.emit.gltf.mesh import _MeshBuilder

    for member in _all_members(model)[:200]:
        builder = _MeshBuilder()
        _add_member(builder, member)
        triangles = sum(len(indices) for _positions, indices in builder._buckets.values()) // 3
        assert triangles == 12, f"{member.child_key} emitted {triangles} triangles"


# --- walls ------------------------------------------------------------------------------

def test_every_wall_becomes_one_element_with_a_part_per_body_layer(model, geometry) -> None:
    """One part per layer with a *body*, which is not one part per layer with *depth*.

    Cavity fill shares the structure layer's polygon, so a part for it would only z-fight
    and neither list carries it. A ``Layer.slot``'s later regions are a different matter:
    they are counted once for depth (a plinth and a field are one 3 5/8" wythe) but each is
    a real course of brick at its own elevation, and building from ``depth_layers()`` left
    the plinth standing alone with nothing above it — in the GLB, in IFC and in section.
    """
    for wall in model.walls:
        element = geometry.by_uid(wall.uid)
        assert element is not None, wall.tag
        expected = [ly for ly in wall.body_layers() if ly.polygon]
        assert len(element.parts) == len(expected), wall.tag


def test_a_raked_wall_carries_per_vertex_tops(model, geometry) -> None:
    """A gable/ToRoof wall stops at its actual rake; a flat bounding-height box would engulf
    and z-fight the roof it carries."""
    from typehaus.resolve.geometry_ir import GPrism
    from typehaus.resolve.geometry_walls import is_raked, wall_top_at

    raked = [w for w in model.walls if is_raked(w)]
    if not raked:
        pytest.skip("house has no raked walls")
    for wall in raked:
        element = geometry.by_uid(wall.uid)
        prisms = [s for p in element.parts for s in p.solids if isinstance(s, GPrism)]
        # The sill band under an opening stays deliberately flat; at least one solid rakes.
        assert any(s.top is not None for s in prisms), wall.tag
        for solid in prisms:
            if solid.top is None:
                continue
            for (x, y), top in zip(solid.ring, solid.top):
                assert top == pytest.approx(wall_top_at(wall, x, y), abs=TOL)


def test_openings_split_their_wall_layer(model, geometry) -> None:
    """A layer hosting an opening becomes piers + sill band + header, so the window reads as
    a void rather than being drawn over."""
    hosts = {o.host_wall for o in model.openings}
    split = [w for w in model.walls if w.tag in hosts and w.depth_layers()]
    if not split:
        pytest.skip("house has no walls hosting openings")
    for wall in split:
        element = geometry.by_uid(wall.uid)
        counts = [len(p.solids) for p in element.parts]
        assert max(counts) > 1, f"{wall.tag} layer was not split around its openings"


def test_arched_openings_produce_a_curved_mesh(model, geometry) -> None:
    """An arch head is one continuous curved soffit carrying the cylinder's analytic normals,
    not a stack of flat strips."""
    from typehaus.resolve.geometry_ir import GMesh

    arched = [o for o in model.openings if o.arch_rise_m > 1e-6]
    if not arched:
        pytest.skip("house has no arched openings")
    meshes = [s for e in geometry.of_kind("wall") for p in e.parts for s in p.solids
              if isinstance(s, GMesh)]
    assert meshes, "arched opening produced no mesh"
    for mesh in meshes:
        assert mesh.normals is not None and len(mesh.normals) == len(mesh.positions)
        # Only the soffit vertices are on the curve; the flat top's are not, or the emitter
        # would shade a flat face as curved.
        assert mesh.curved_vertices
        assert len(mesh.curved_vertices) < len(mesh.positions)


# --- openings ---------------------------------------------------------------------------

def _emitter_opening_points(model, wall, opening) -> list[tuple[float, float, float]]:
    """What `emit/gltf/openings.py` draws for this opening today, back in the plan frame."""
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.gltf.openings import _add_opening_filling

    door_types = {dt.tag: dt for dt in model.plan.library.door_types}
    door_type = door_types.get(opening.type_ref) if opening.is_door else None
    builder = _MeshBuilder()
    _add_opening_filling(
        builder, wall, opening,
        door_type.operation if door_type is not None else None,
        is_glazed=door_type is not None and door_type.glazed,
        is_trimless=door_type is not None and door_type.trimless,
    )
    # glTF swizzles (x, y, z) → (x, z, -y); undo it so both sides speak the plan frame.
    return [(p[0], -p[2], p[1])
            for positions, _ in builder._buckets.values() for p in positions]


def test_opening_products_match_the_emitter_box_for_box(model, geometry) -> None:
    """Shadow parity, no blessed diff: the door/window product is the one piece of geometry
    the emitter and the viewer were *already* mirroring by hand, so the IR has to land on the
    same eleven constants it did."""
    walls_by_tag = {wall.tag: wall for wall in model.walls}
    checked = 0
    for opening in model.openings:
        host = walls_by_tag.get(opening.host_wall)
        if host is None:
            continue
        element = geometry.by_uid(opening.uid)
        assert element is not None, opening.uid
        got = {(round(x, 9), round(y, 9), round(z, 9))
               for part in element.parts for solid in part.solids
               for (px, py) in solid.ring for x, y, z in
               ((px, py, solid.z0_m), (px, py, solid.z1_m))}
        want = {(round(x, 9), round(y, 9), round(z, 9))
                for x, y, z in _emitter_opening_points(model, host, opening)}
        assert got == want, opening.uid
        checked += 1
    assert checked, "house has no openings to compare"


def test_rough_openings_ship_no_product(model, geometry) -> None:
    """A rough opening is a hole, not a product — drawing a frame in one would invent a door
    the take-off never priced."""
    rough = [o for o in model.openings if o.kind == "rough_opening"]
    if not rough:
        pytest.skip("house has no rough openings")
    for opening in rough:
        assert geometry.by_uid(opening.uid).parts == ()


# --- roofs ------------------------------------------------------------------------------

def test_roof_layer_bands_match_the_emitter(model, geometry) -> None:
    """The perpendicular-offset, eave-drift-compensated interpretation is canonical (it is
    what the viewer and the GLB already drew); IFC's vertical-sided prisms are the copy that
    changes. Compared as a triangle *set*, since the IR indexes what the emitter deindexed."""
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.gltf.roofs import _add_roof
    from typehaus.resolve.geometry_ir import GMesh

    if not model.roofs:
        pytest.skip("house has no roofs")
    for roof in model.roofs:
        element = geometry.by_uid(roof.uid)
        assert element is not None, roof.tag
        got = set()
        for part in element.parts:
            for solid in part.solids:
                assert isinstance(solid, GMesh)
                for tri in solid.triangles:
                    got.add(tuple(sorted(tuple(round(c, 9) for c in solid.positions[i])
                                         for i in tri)))
        builder = _MeshBuilder()
        _add_roof(builder, roof, model)
        want = set()
        for positions, indices in builder._buckets.values():
            for i in range(0, len(indices), 3):
                # ...and back out of the glTF swizzle into the plan frame.
                want.add(tuple(sorted(
                    tuple(round(c, 9) for c in (positions[indices[i + k]][0],
                                                -positions[indices[i + k]][2],
                                                positions[indices[i + k]][1]))
                    for k in range(3))))
        # The emitter's mesh also carries the roof's skin members (trim, closure bands); the
        # IR files those under framing, so the layer bands are a subset of what it draws.
        assert got <= want, roof.tag
        assert got, roof.tag


def test_every_roof_layer_is_a_closed_band(model, geometry) -> None:
    """A layer whose eave/rake perimeter is left open imports as a zero-thickness plane —
    which is what a roof looks like in Revit when it is wrong."""
    from typehaus.resolve.geometry_ir import GMesh

    for roof in model.roofs:
        for part in geometry.by_uid(roof.uid).parts:
            mesh = part.solids[0]
            assert isinstance(mesh, GMesh)
            edges: dict[tuple, int] = {}
            for tri in mesh.triangles:
                for i in range(3):
                    a = tuple(round(c, 6) for c in mesh.positions[tri[i]])
                    b = tuple(round(c, 6) for c in mesh.positions[tri[(i + 1) % 3]])
                    key = tuple(sorted((a, b)))
                    edges[key] = edges.get(key, 0) + 1
            assert all(count % 2 == 0 for count in edges.values()), f"{roof.tag}/{part.key}"


# --- floor decks and earth (blessed diffs: nothing drew either) --------------------------

def test_a_floor_with_a_subfloor_gains_a_deck(model, geometry) -> None:
    """Blessed diff 3: joists must not hang in space in either export."""
    from typehaus.model.floors import FloorSystem
    from typehaus.resolve.geometry_ir import GPrism

    decked = [f for f in model.floors if f.deck_outline]
    authored = [f for f in model.floors
                if isinstance(model.plan.by_tag(f.tag), FloorSystem)
                and model.plan.by_tag(f.tag).subfloor is not None]
    if not authored:
        pytest.skip("house has no floor system with a subfloor")
    assert len(decked) == len(authored), "a subfloor was declared but no deck reached the IR"
    for floor in decked:
        deck = next(p for p in geometry.by_uid(floor.uid).parts if p.key == "deck")
        prism = deck.solids[0]
        assert isinstance(prism, GPrism)
        # The deck rides *on* the storey datum — the joists top out there.
        assert prism.z0_m == pytest.approx(floor.deck_z0_m, abs=TOL)
        assert prism.z1_m > prism.z0_m
        joist_tops = {round(m.z1_m, 6) for m in floor.members}
        assert round(prism.z0_m, 6) in joist_tops


def test_a_floor_opening_is_cut_out_of_its_deck(model, geometry) -> None:
    """A stair well the deck is drawn straight over is a floor you fall through in the
    viewer and a solid slab in Revit."""
    decked = [f for f in model.floors if f.deck_outline and f.deck_voids]
    if not decked:
        pytest.skip("house has no decked floor with an opening")
    for floor in decked:
        prism = next(p for p in geometry.by_uid(floor.uid).parts if p.key == "deck").solids[0]
        assert len(prism.voids) == len(floor.deck_voids)
        assert all(len(ring) >= 3 for ring in prism.voids)


def test_the_site_earth_becomes_geometry(model, geometry) -> None:
    """Blessed diff 4: the glTF `earth` trade was empty, so the export had no ground."""
    from typehaus.resolve.geometry_build import EARTH_SHEET_THICKNESS_M
    from typehaus.resolve.geometry_ir import GPrism
    from typehaus.resolve.site_earth import site_grade_elevation_m

    if len(model.plan.project.site.parcel) < 3:
        pytest.skip("house has no parcel ring")
    earth = geometry.of_kind("earth")
    assert len(earth) == 1
    prism = earth[0].parts[0].solids[0]
    assert isinstance(prism, GPrism)
    grade = site_grade_elevation_m(model)
    # Top face *is* grade: soil is what is under the grade plane, not a slab sitting on it.
    assert prism.z1_m == pytest.approx(grade, abs=TOL)
    assert prism.z0_m == pytest.approx(grade - EARTH_SHEET_THICKNESS_M, abs=TOL)


def test_earth_is_cut_by_every_excavated_slab(model, geometry) -> None:
    """The sheet is one plane at grade; without the voids it slices through the basement it
    was dug out for."""
    from typehaus.resolve.site_earth import earth_plane_void_rings

    expected = earth_plane_void_rings(model)
    if not expected:
        pytest.skip("house excavates nothing")
    prism = geometry.of_kind("earth")[0].parts[0].solids[0]
    assert len(prism.voids) == len(expected)


# --- floor decks and the site earth in the glTF export -----------------------------------
# `emit/gltf` derives no geometry of its own: openings and roof bands are serialized from
# the IR, including the subfloor deck and the site earth.

def test_the_glb_opening_product_is_the_ir_product(model, geometry) -> None:
    """The emitter draws exactly the boxes `opening_parts` produced, and no others.

    A regression here means the emitter grew geometry of its own again.
    """
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.gltf.openings import _add_opening_filling

    walls_by_tag = {wall.tag: wall for wall in model.walls}
    door_types = {dt.tag: dt for dt in model.plan.library.door_types}
    checked = 0
    for opening in model.openings:
        host = walls_by_tag.get(opening.host_wall)
        if host is None:
            continue
        element = geometry.by_uid(opening.uid)
        assert element is not None, opening.uid
        door_type = door_types.get(opening.type_ref) if opening.is_door else None
        builder = _MeshBuilder()
        _add_opening_filling(
            builder, host, opening,
            operation=door_type.operation if door_type is not None else None,
            is_glazed=door_type is not None and door_type.glazed,
            is_trimless=door_type is not None and door_type.trimless,
        )
        want = {
            tuple(sorted((round(x, 9), round(y, 9), round(z, 9))
                         for (x, y) in solid.ring for z in (solid.z0_m, solid.z1_m)))
            for part in element.parts for solid in part.solids
        }
        # Corners, back out of the glTF swizzle: every box the emitter drew has to be one of
        # the IR's, and every one of the IR's has to have been drawn.
        got = {
            tuple(sorted(corners))
            for corners in _emitted_box_corners(builder)
        }
        assert got == {tuple(sorted(box)) for box in want}, opening.uid
        checked += 1
    assert checked, "house has no hosted openings"


def _emitted_box_corners(builder) -> list[list[tuple[float, float, float]]]:
    """The distinct 8-corner sets the mesh builder accumulated, in the plan frame."""
    boxes = []
    for positions, _indices in builder._buckets.values():
        # add_prism appends one bottom loop then one top loop per box.
        for start in range(0, len(positions), 8):
            chunk = positions[start:start + 8]
            if len(chunk) < 8:
                continue
            boxes.append([(round(px, 9), round(-pz, 9), round(py, 9))
                          for (px, py, pz) in chunk])
    return boxes


def test_the_glb_ships_the_subfloor_deck_and_the_site_earth(model) -> None:
    """Blessed diffs 3 and 4, at the export boundary: a floor node whose deck is drawn, and
    a non-empty `earth` node."""
    from typehaus.emit.gltf.emitter import emit_gltf_dict

    gltf, _blob = emit_gltf_dict(model, "core")
    trades = [node.get("extras", {}).get("trade") for node in gltf["nodes"]]
    assert "earth" in trades, "the export still has no ground under the building"
    decked = [f for f in model.floors if f.deck_outline]
    if not decked:
        pytest.skip("house has no decked floor")
    # Joists are framing, not floors — the floors trade only carries the deck sheet now.
    floor_nodes = [n for n in gltf["nodes"] if n.get("extras", {}).get("trade") == "floors"
                   and n.get("extras", {}).get("kind") == "floor"]
    assert len(floor_nodes) >= len(decked)
    framing_floor_nodes = [n for n in gltf["nodes"] if n.get("extras", {}).get("trade") == "framing"
                           and n.get("extras", {}).get("kind") == "floor"]
    assert len(framing_floor_nodes) >= len(model.floors)


def test_the_earth_sheet_is_holed_rather_than_drawn_over_the_excavation(model) -> None:
    """Cutting the slabs out of the sheet is the whole point of the voids: an uncut plane at
    grade slices straight through the basement it was dug for."""
    from typehaus.emit.gltf.emitter import _add_earth
    from typehaus.emit.gltf.mesh import _MeshBuilder

    prism = model.geometry.of_kind("earth")
    if not prism:
        pytest.skip("house has no parcel ring")
    voids = prism[0].parts[0].solids[0].voids
    if not voids:
        pytest.skip("house excavates nothing")
    builder = _MeshBuilder()
    _add_earth(builder, model)
    for positions, _indices in builder._buckets.values():
        for (px, _py, pz) in positions:
            x, y = px, -pz
            for ring in voids:
                xs = [p[0] for p in ring]
                ys = [p[1] for p in ring]
                inside = (min(xs) + TOL < x < max(xs) - TOL
                          and min(ys) + TOL < y < max(ys) - TOL)
                assert not inside, f"earth vertex ({x}, {y}) sits inside an excavation"


def test_one_hole_still_cuts_the_four_bands_it_always_did() -> None:
    """The generalized subtraction has to reduce to the single-hole slab path exactly, or
    every slab with a stair well in it changes shape."""
    from typehaus.emit.gltf.mesh import _subtract_rect

    assert _subtract_rect((0.0, 10.0, 0.0, 10.0), (2.0, 4.0, 3.0, 6.0)) == [
        (0.0, 10.0, 0.0, 3.0), (0.0, 10.0, 6.0, 10.0),
        (0.0, 2.0, 3.0, 6.0), (4.0, 10.0, 3.0, 6.0),
    ]


def test_subtracting_holes_that_miss_or_swallow_the_rectangle() -> None:
    """A hole outside the sheet must not delete it, and one covering it must not leave a
    sliver behind — the earth sheet meets both cases (a detached slab, a full-footprint one)."""
    from typehaus.emit.gltf.mesh import _subtract_rect

    whole = (0.0, 4.0, 0.0, 4.0)
    assert _subtract_rect(whole, (9.0, 10.0, 9.0, 10.0)) == [whole]
    assert _subtract_rect(whole, (-1.0, 5.0, -1.0, 5.0)) == []
    # An edge-touching hole takes a bite rather than splitting off a zero-width band.
    assert _subtract_rect(whole, (0.0, 1.0, 0.0, 4.0)) == [(1.0, 4.0, 0.0, 4.0)]
