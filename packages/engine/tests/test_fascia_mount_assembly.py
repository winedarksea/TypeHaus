"""Physical mount fit and shared viewer/export geometry, including the balcony's slope."""

import math
from dataclasses import replace
from types import SimpleNamespace

import pytest
from _railing_fixtures import railing, resolve_railings
from shapely.geometry import Point, Polygon

from typehaus.library.railings import RAILING_EXT_ALUMINUM_FASCIA as PRODUCT
from typehaus.quantities import inch, m, pt
from typehaus.resolve.floor_tilt import DeckPlane
from typehaus.resolve.railings.fascia_assembly import mounting_layout
from typehaus.resolve.railings.fascia_layout import fascia_stations
from typehaus.resolve.railings.fascia_mesh import pierced_plate
from typehaus.resolve.railings.guard_line import guard_post_stations
from typehaus.resolve.railings.spans import deck_surface
from typehaus.takeoff.railings import railing_takeoff


def _guard(path):
    return railing(type_ref=PRODUCT.tag, path=tuple(pt(m(x), m(y)) for x, y in path),
                   fascia_face_offset=inch(1), fascia_bracket_drop=inch(2),
                   infill="balusters", baluster_spacing=inch(4))


@pytest.mark.parametrize("angle", [0, math.pi/5, math.pi/2, math.pi])
@pytest.mark.parametrize("turn,variant", [(1, "outside_corner"), (-1, "inside_corner")])
def test_corner_assembly_rotates_with_both_mounting_faces(angle, turn, variant):
    def rotate(x, y):
        return (x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle))

    guard = _guard([rotate(0, 0), rotate(2, 0), rotate(2, turn*2)])
    model = resolve_railings([guard], types=[PRODUCT])
    assert not model.railing_findings
    layout = mounting_layout(model.plan.library, guard)
    corners = [s for s in layout if s.variant == variant]
    assert len(corners) == 1
    assert len(corners[0].faces) == 2
    assert [s.post for s in layout] == pytest.approx(guard_post_stations(model.plan.library, guard))
    brackets = [s for s in model.solids if "FASCIA-BRACKET" in s.tag]
    assert len(brackets) == len(layout)
    assert sum(s.product == getattr(PRODUCT.fascia_mount, f"{variant}_product")
               for s in brackets) == 1
    assert all(s.body_mesh is not None for s in brackets)
    for index, station in enumerate(layout, 1):
        post = next(s for s in model.solids if s.tag.endswith(f"-POST{index}"))
        face = station.faces[0]
        for point in post.outline:
            relative = tuple(point[i]-station.post[i] for i in range(2))
            assert abs(sum(relative[i]*face.tangent[i] for i in range(2))) < (
                PRODUCT.fascia_mount.pocket_width.meters/2)
            assert abs(sum(relative[i]*face.outward[i] for i in range(2))) < (
                PRODUCT.fascia_mount.pocket_width.meters/2)


def test_unsupported_corner_reports_an_error_without_partial_hardware():
    guard = _guard([(0, 0), (2, 0), (3, 1)])
    model = resolve_railings([guard], types=[PRODUCT])
    assert [f.check_id for f in model.railing_findings] == ["geometry.railing_fascia_layout"]
    assert not model.solids


def test_mounting_flange_has_open_holes_not_a_solid_envelope():
    mesh = pierced_plate(5.64, -5, 0, 0.25,
                         [(-2.315, -0.5, 0.16), (2.315, -4.5, 0.16)])
    caps = []
    for triangle in mesh.triangles:
        points = [mesh.positions[i] for i in triangle]
        if all(abs(p[1]) < 1e-9 for p in points):
            caps.append(Polygon([(p[0], p[2]) for p in points]))
    assert caps
    assert not any(p.covers(Point(inch(-2.315).meters, inch(-0.5).meters)) for p in caps)
    assert any(p.covers(Point(0, inch(-2).meters)) for p in caps)


def test_straight_mount_has_four_full_length_bolts_on_the_catalog_pattern():
    guard = _guard([(0, 0), (2, 0)])
    model = resolve_railings([guard], types=[PRODUCT])
    bolts = next(s.body_mesh for s in model.solids if s.tag.endswith("FASCIA-BOLTS1"))
    # Shaft tips are behind every washer/nut. Read their circles from the emitted mesh,
    # rather than re-running the assembly's hole loop.
    tip_y = max(p[1] for p in bolts.positions)
    tips = {(round(x, 9), round(z, 9)) for x, y, z in bolts.positions if abs(y-tip_y) < 1e-9}
    spec = PRODUCT.fascia_mount
    assert tip_y == pytest.approx(-guard.fascia_face_offset.meters
                                  - spec.wall_thickness.meters + spec.bolt_length.meters)
    for x in (-spec.mounting_hole_spacing[0].meters/2,
              spec.mounting_hole_spacing[0].meters/2):
        for z in (-guard.fascia_bracket_drop.meters-spec.mounting_hole_top_drop.meters,
                  -guard.fascia_bracket_drop.meters-spec.mounting_hole_top_drop.meters
                  -spec.mounting_hole_spacing[1].meters):
            circle = {(px, pz) for px, pz in tips
                      if abs(math.hypot(px-x, pz-z)-spec.bolt_diameter.meters/2) < 1e-8}
            assert len(circle) == 12
            tips -= circle
    assert not tips


def test_deck_surface_samples_the_edge_instead_of_extrapolating_under_outboard_posts():
    plane = DeckPlane((0, 0), 0, (0.1, 0.2))
    deck = SimpleNamespace(deck_top_at=lambda x, y: 3 + plane.lift(x, y))
    surface = deck_surface(deck, [(0, 0), (2, 0), (2, 2)], 0.1)
    assert surface.height_at((1, -0.1)) == pytest.approx(3.1)
    assert surface.height_at((2.1, -0.1)) == pytest.approx(3.2)
    assert surface.height_at((2.1, 1)) == pytest.approx(3.4)


def test_shared_end_omits_its_post_and_all_of_its_mount_hardware():
    first = _guard([(0, 0), (2, 0)])
    # Collinear paths share exactly the same outboard end station.
    second = _guard([(2, 0), (4, 0)]).model_copy(update={
        "uid": "RLSECOND01", "tag": "RL-SECOND", "start_post_ref": first.tag})
    model = resolve_railings([first, second], types=[PRODUCT])
    assert not model.railing_findings
    assert not any(s.tag in ("RL-SECOND-POST1", "RL-SECOND-FASCIA-BRACKET1",
                              "RL-SECOND-FASCIA-BOLTS1") for s in model.solids)


def test_balcony_mounts_follow_deck_and_preserve_order_quantities(catlin_model_ro):
    model = catlin_model_ro
    guard = model.plan.by_tag("RL-SG-BALCONY")
    deck = next(f for f in model.floors if f.tag == "FS-SG-DECK")
    layout = mounting_layout(model.plan.library, guard)
    assert len(layout) == 9
    assert [s.variant for s in layout].count("outside_corner") == 2
    solids = {s.tag: s for s in model.solids if s.host_ref == guard.tag}
    mounts = [s for s in solids.values() if "FASCIA-BRACKET" in s.tag]
    feet = [s for s in solids.values() if "FASCIA-FOOTBLOCK" in s.tag]
    assert len(mounts) == 9
    assert len(feet) == 8
    assert all(s.body_mesh for s in mounts + feet)
    surface = deck_surface(deck, [p.xy_m for p in guard.path],
                           guard.fascia_face_offset.meters + PRODUCT.fascia_post_offset.meters)
    spec = PRODUCT.fascia_mount
    counter = model.plan.by_tag("TR-SG-COUNTER-FLASH-W")
    house_face_y = counter.path[0].y.meters + counter.thickness.meters/2
    north_edge = max(y for _x, y in deck.deck_outline)
    assert all(member.p1[1] == pytest.approx(north_edge + inch(0.5).meters)
               for member in deck.members if member.category == "rim")
    for index in (1, 9):
        post = solids[f"{guard.tag}-POST{index}"]
        assert 0 < house_face_y-max(y for _x, y in post.outline) < inch(4).meters
    for index, station in enumerate(layout, 1):
        post = solids[f"{guard.tag}-POST{index}"]
        mount = solids[f"{guard.tag}-FASCIA-BRACKET{index}"]
        walking_z = surface.height_at(station.post)
        assert mount.z1_m == pytest.approx(walking_z - guard.fascia_bracket_drop.meters)
        assert post.z0_m == pytest.approx(mount.z0_m + spec.insert_thickness.meters)
        assert post.z1_m - walking_z == pytest.approx(inch(42).meters)
        # Every rear washer fits on its actual member, including both corner faces.
        from typehaus.resolve.framing.profiles import cross_section
        bolts = solids[f"{guard.tag}-FASCIA-BOLTS{index}"].body_mesh
        for face in station.faces:
            candidates = []
            for member in deck.members:
                run = math.dist(member.p0, member.p1)
                axis = tuple((member.p1[i]-member.p0[i])/run for i in range(2))
                if member.category in ("rim", "joist") and abs(sum(
                        axis[i]*face.outward[i] for i in range(2))) < 1e-8:
                    distance = abs(sum((member.p0[i]-face.origin[i])*face.outward[i]
                                       for i in range(2)))
                    candidates.append((distance, member, axis, run))
            _distance, member, axis, run = min(candidates, key=lambda item: item[0])
            half = cross_section(member.profile).width_m/2
            rear_face = [p for p in bolts.positions if abs(sum(
                (p[i]-member.p0[i])*face.outward[i] for i in range(2))+half) < 1e-8]
            assert rear_face, mount.tag
            for point in rear_face:
                along = sum((point[i]-member.p0[i])*axis[i] for i in range(2))
                assert -1e-8 <= along <= run+1e-8, (mount.tag, member.child_key)
    assert mounts[0].z1_m > mounts[2].z1_m + inch(2).meters
    gutter = model.plan.by_tag("TR-SG-GUTTER")
    assert min(s.z0_m for s in mounts) - gutter.top_elevation.meters == pytest.approx(
        inch(1).meters)
    row = next(r for r in railing_takeoff(model) if guard.tag in r["tags"])
    assert row["post_count"] == 9
    without_hardware = replace(model, solids=[s for s in model.solids
                              if not s.tag.startswith(f"{guard.tag}-FASCIA-")])
    assert row == next(r for r in railing_takeoff(without_hardware) if guard.tag in r["tags"])


def test_balcony_fascia_tracks_rim_and_foot_fasteners_stay_below_deck(catlin_model_ro):
    model = catlin_model_ro
    deck = next(f for f in model.floors if f.tag == "FS-SG-DECK")
    fascia = model.plan.by_tag("TR-SG-FASCIA")
    boards = [s for s in model.solids if s.tag.startswith("TR-SG-FASCIA-")]
    assert len(boards) == 3
    for board in boards:
        assert board.body_mesh is not None
        for x, y, z in board.body_mesh.positions:
            expected_top = fascia.top_elevation.meters + deck.deck_lift_at(x, y)
            assert min(abs(z-expected_top), abs(z-(expected_top-fascia.depth.meters))) < 1e-8
    # The supporting board is outside the west rim, rather than embedded in it.
    west = next(r for r in deck.members if r.child_key == "rim-0")
    assert max(x for x, _y in boards[0].outline) == pytest.approx(
        west.p0[0] - inch(1.25).meters/2)
    assert not deck.penetrations
    from typehaus.resolve.framing.profiles import cross_section

    # Roll restraints must leave the bolt tails and wrench access outside the wood.
    blocking = []
    for member in deck.members:
        if member.category != "blocking":
            continue
        profile = cross_section(member.profile)
        from typehaus.resolve.geometry import rect_between
        blocking.append(Polygon(rect_between(member.p0, member.p1,
                                              -profile.width_m/2, profile.width_m/2)))
    for solid in model.solids:
        if solid.host_ref != "RL-SG-BALCONY" or "FASCIA-BOLTS" not in solid.tag:
            continue
        mesh = solid.body_mesh
        assert not any(Polygon([mesh.positions[i][:2] for i in triangle]).intersection(
            block).area > 1e-10 for triangle in mesh.triangles for block in blocking), solid.tag
    deck_plan = Polygon(deck.deck_outline)
    for solid in model.solids:
        if (solid.host_ref != "RL-SG-BALCONY" or solid.body_mesh is None
                or not any(part in solid.tag for part in ("BOLTS", "SCREWS", "FOOTBLOCK"))):
            continue
        mesh = solid.body_mesh
        for triangle in mesh.triangles:
            vertices = [mesh.positions[i] for i in triangle]
            heights = [z-deck.deck_top_at(x, y) for x, y, z in vertices]
            if min(heights) < 0 and max(heights) > -(deck.deck_z1_m-deck.deck_z0_m):
                assert Polygon([(x, y) for x, y, _ in vertices]).intersection(
                    deck_plan).area < 1e-10, solid.tag


def test_layout_rejects_repeated_points():
    with pytest.raises(ValueError, match="repeated"):
        fascia_stations([(0, 0), (0, 0)], 1, 0.02, 0.04)


def test_mount_meshes_survive_json_geometry_ir_and_ifc(catlin_model_ro):
    import ifcopenshell
    from _helpers import assert_wire_mesh

    from typehaus.emit.ifc.structural import _solid_body
    from typehaus.server.model_json import model_to_dict

    model = catlin_model_ro
    payload = model_to_dict(model)
    serialized = {s["uid"]: s for s in payload["solids"]}
    exported = ifcopenshell.file(schema="IFC4")
    origin = exported.createIfcAxis2Placement3D(exported.createIfcCartesianPoint((0., 0., 0.)))
    context = exported.createIfcGeometricRepresentationContext(None, "Model", 3, 1e-5, origin)
    for solid in model.solids:
        if (solid.host_ref not in {"RL-SG-BALCONY", "RL-SG-PSTAIR-S", "RL-SG-PSTAIR-N",
                                   "RL-SG-PORCH", "RL-SG-PORCH-SE", "RL-SG-PORCH-NE"}
                or solid.body_mesh is None):
            continue
        assert_wire_mesh(serialized[solid.uid]["body_mesh"],
                         solid.body_mesh.positions, solid.body_mesh.triangles)
        element = model.geometry.by_uid(solid.uid)
        assert any(solid.body_mesh == body for part in element.parts for body in part.solids)
        representation = _solid_body(exported, context, solid)
        assert representation.RepresentationType == "Tessellation"
        face_set = representation.Items[0]
        assert tuple(tuple(p) for p in face_set.Coordinates.CoordList) == solid.body_mesh.positions
        assert tuple(tuple(i-1 for i in tri) for tri in face_set.CoordIndex) == (
            solid.body_mesh.triangles)
    floor = next(f for f in model.floors if f.tag == "FS-SG-DECK")
    served = next(f for f in payload["floors"] if f["tag"] == floor.tag)
    assert served["deck_plane"]["gradient"] == list(floor.deck_plane.gradient)
    assert served["deck_z0_m"] == floor.deck_z0_m
