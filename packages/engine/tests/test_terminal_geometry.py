"""Terminal metal stays open while fit envelopes and product identities stay conservative."""

import math
from types import SimpleNamespace

import numpy as np
import pytest
from shapely.geometry import Point, Polygon

from typehaus import Mount, MountKind, TerminalNeck, inch
from typehaus.emit.gltf.canvas_objects import CanvasDrawContext, draw_canvas_object
from typehaus.resolve.geometry import opening_center
from typehaus.resolve.geometry_walls import cuts_layer, layer_solids
from typehaus.resolve.model import ResolvedCanvasObject
from typehaus.resolve.terminal_geometry import (
    face_mesh,
    neck_mesh,
    resolve_terminal_faces,
    shell,
    terminal_frame,
    tube,
)
from typehaus.solids3d.recorder import SolidRecorder
from typehaus.takeoff.placeables import placeables_takeoff


def _projected_triangles(mesh, axes=(0, 1)):
    return [Polygon([(mesh.positions[i][axes[0]], mesh.positions[i][axes[1]]) for i in tri])
            for tri in mesh.triangles]


@pytest.mark.parametrize("section", ["round", "rectangular"])
def test_neck_has_an_open_passage_and_closed_metal(section):
    import trimesh

    mesh = tube(.1, .1, .08, section)
    assert not any(p.covers(Point(0, 0)) for p in _projected_triangles(mesh))
    metal = trimesh.Trimesh(vertices=mesh.positions, faces=mesh.triangles, process=True)
    assert metal.is_watertight
    assert metal.volume > 0
    assert np.min(metal.area_faces) > 0


def test_dimensioned_round_inlet_is_a_hole_in_the_back_plate():
    from typehaus.resolve.terminal_geometry import circle

    mesh = shell(.3, .2, .1, "rectangular", ((0, 0, .1), (0, 0, 1), circle(.08)))
    rear = [p for p, tri in zip(_projected_triangles(mesh), mesh.triangles, strict=True)
            if all(abs(mesh.positions[i][2] - .1) < 1e-9 for i in tri)]
    assert rear and not any(p.covers(Point(0, 0)) for p in rear)
    assert any(p.covers(Point(.1, 0)) for p in rear)


@pytest.mark.parametrize("style,double", [("rectangular_grille", False),
                                         ("rectangular_grille", True), ("disc_valve", False),
                                         ("laser_cut_chevron", False)])
def test_faces_have_visible_air_gaps_and_stay_within_catalog_bounds(style, double):
    mesh = face_mesh(.3, .3, .0254, style, double)
    points = np.array(mesh.positions)
    assert np.all(points.min(axis=0) >= np.array([-.15, -.15, 0]) - 1e-9)
    assert np.all(points.max(axis=0) <= np.array([.15, .15, .0254]) + 1e-9)
    projected = _projected_triangles(mesh)
    # A grid through the face must see daylight; a solid massing box covers every sample.
    assert any(not any(p.covers(Point(x, y)) for p in projected)
               for x in np.linspace(-.13, .13, 15) for y in np.linspace(-.13, .13, 15))


@pytest.mark.parametrize("kind", [MountKind.WALL, MountKind.CEILING, MountKind.FLOOR])
@pytest.mark.parametrize("rotation", [0, 90, 180, 37])
@pytest.mark.parametrize("back_sign", [-1, 1])
def test_neck_mounting_and_rotation_preserve_the_envelope(kind, rotation, back_sign):
    from typehaus.resolve.terminal_necks import _box

    obj = ResolvedCanvasObject(
        uid="R", tag="R", storey="S", domain="mechanical", kind="Register", type_ref="T",
        room=None, position=(1, 2), z_m=3, rotation_degrees=rotation,
        footprint=((.99, 1.99), (1.01, 1.99), (1.01, 2.01), (.99, 2.01)),
        body_z0_m=3, body_z1_m=3.02, mount=Mount(kind=kind), attachment_wall="W")
    angle = math.radians(rotation)
    back = (-math.sin(angle) * back_sign, math.cos(angle) * back_sign)
    wall = SimpleNamespace(axis=((1 + back[0], 2 + back[1]),
                                 (1 + back[0] + math.cos(angle),
                                  2 + back[1] + math.sin(angle))))
    model = SimpleNamespace(wall=lambda _: wall)
    neck = TerminalNeck(width=inch(4), height=inch(4), depth=inch(3),
                        part="collar", section="round")
    mesh = neck_mesh(model, obj, neck)
    ring, bottom, top = _box(model, obj, neck)
    envelope = Polygon(ring).buffer(1e-9)
    assert all(envelope.covers(Point(x, y)) and bottom - 1e-9 <= z <= top + 1e-9
               for x, y, z in mesh.positions)


def test_unspecified_face_and_neck_keep_the_legacy_geometry():
    obj = SimpleNamespace(kind="Register", type_ref="T")
    model = SimpleNamespace(plan=SimpleNamespace(library=SimpleNamespace(
        register_types=[SimpleNamespace(tag="T", face_style=None)])), canvas_objects=[obj])
    resolve_terminal_faces(model)
    assert model.canvas_objects[0] is obj


def test_mudroom_is_one_grille_over_a_panel_cut_without_changed_framing(catlin_model_ro):
    model = catlin_model_ro
    obj = next(o for o in model.canvas_objects if o.tag == "REG-M-XFER-MUD")
    opening = next(o for o in model.openings if o.tag == "AO-M-XFER-MUD")
    wall = model.wall("W-M-STRW")
    assert obj.body_mesh is not None
    assert not any(s.tag.startswith(obj.tag + "-NECK") for s in model.solids)
    assert not opening.framing_required
    assert cuts_layer(wall, "mdo-stair", opening)
    assert cuts_layer(wall, "paint-stair", opening)
    assert cuts_layer(wall, "paint-nook", opening)
    assert not cuts_layer(wall, "gwb-mudroom-upper", opening)
    assert not cuts_layer(wall, "stud", opening)
    assert wall.z0_m + opening.sill_m + opening.height_m / 2 == pytest.approx(
        (obj.body_z0_m + obj.body_z1_m) / 2, abs=1e-8)
    assert (opening_center(wall, opening)[1]
            == pytest.approx(obj.position[1]))
    layer = next(layer for layer in wall.layers if layer.name == "mdo-stair")
    patch_centre = Point(sum(x for x, _ in layer.polygon) / len(layer.polygon),
                         obj.position[1])
    hole_z = wall.z0_m + opening.sill_m + opening.height_m / 2
    solids = layer_solids(wall, layer.polygon, [opening], layer_name=layer.name)
    assert not any(s.z0_m < hole_z < s.z1_m and Polygon(s.ring).covers(patch_centre)
                   for s in solids)
    rows = [r for r in placeables_takeoff(model) if obj.tag in r["tags"]]
    assert len(rows) == 1 and rows[0]["count"] == 1
    assert "included_products" not in rows[0]


def test_faces_share_the_glb_and_json_mesh(catlin_model_ro):
    from typehaus.server.model_json_document import _document_header
    from typehaus.server.model_json_mesh import decode_mesh

    # Test the actual GLB drawing entrypoint, bypassing symbol rebuilding.
    model = catlin_model_ro
    context = CanvasDrawContext.of(model)
    obj = next(o for o in model.canvas_objects if o.tag == "REG-M-SUP1")
    recorder = SolidRecorder()
    draw_canvas_object(recorder, obj, context)
    assert len(recorder.primitives) == 1
    assert recorder.primitives[0].solid is obj.body_mesh
    wire = _document_header(model, revision="test", content_hash="test", provenance=None,
                            findings=None, preferences=None)
    encoded = next(o["body_mesh"] for o in wire["canvas_objects"] if o["uid"] == obj.uid)
    decoded = decode_mesh(encoded)
    assert decoded["triangles"] == list(obj.body_mesh.triangles)
    assert np.allclose(decoded["positions"], obj.body_mesh.positions, atol=encoded["quantum"])


def test_ifc_keeps_terminal_identity_and_shared_mesh(catlin_ifc_path, catlin_model_ro):
    import ifcopenshell

    model = catlin_model_ro
    file = ifcopenshell.open(str(catlin_ifc_path))
    for tag in ("REG-M-XFER-MUD", "REG-M-SUP1", "REG-S-HP-STAIR", "REG-A-RET1"):
        obj = next(o for o in model.canvas_objects if o.tag == tag)
        entity = next(e for e in file.by_type("IfcAirTerminal") if e.Name == tag)
        mesh = entity.Representation.Representations[0].Items[0]
        assert mesh.is_a("IfcTriangulatedFaceSet")
        assert np.allclose(mesh.Coordinates.CoordList, obj.body_mesh.positions)
        assert [tuple(i - 1 for i in tri) for tri in mesh.CoordIndex] == list(
            obj.body_mesh.triangles)
    assert not any(e.Name == "REG-M-XFER-MUD-NECK" for e in file.by_type("IfcDuctFitting"))
    for tag in ("REG-M-SUP1-NECK", "REG-S-HP-STAIR-NECK"):
        solid = next(s for s in model.solids if s.tag == tag)
        entity = next(e for e in file.by_type("IfcDuctFitting") if e.Name == tag)
        mesh = entity.Representation.Representations[0].Items[0]
        assert np.allclose(mesh.Coordinates.CoordList, solid.body_mesh.positions)


@pytest.mark.parametrize("tag,projection_in", [
    ("REG-M-SUP1", .625), ("REG-B-SUP1", .625), ("REG-B-SUP2", .55),
    ("REG-M-RET-STUDY", .625), ("REG-A-RET1", .1875),
])
def test_erv_trim_projects_into_the_room_with_openings(catlin_model_ro, tag, projection_in):
    import trimesh

    model = catlin_model_ro
    obj = next(o for o in model.canvas_objects if o.tag == tag)
    origin, across, up, into_host = terminal_frame(model, obj)
    local = (np.array(obj.body_mesh.positions) - origin) @ np.array([across, up, into_host]).T
    projection = inch(projection_in).meters
    assert local[:, 2].min() == pytest.approx(-projection)
    assert local[:, 2].max() == pytest.approx(0, abs=1e-9)
    metal = trimesh.Trimesh(vertices=local, faces=obj.body_mesh.triangles, process=True)
    assert metal.is_watertight and metal.is_winding_consistent

    spec = next(t for t in model.plan.library.register_types if t.tag == obj.type_ref)
    if spec.face_style == "disc_valve":
        centre, rim = sorted(metal.split(), key=lambda part: part.bounds[0, 2])
        assert centre.bounds[0, 2] < rim.bounds[0, 2] < 0
        assert centre.extents[0] == pytest.approx(spec.disc_diameter.meters)
        assert np.linalg.norm(rim.vertices[:, :2], axis=1).min() > centre.extents[0] / 2
    else:
        # The face has webbing at its center and open round cutouts to either side.
        caps = [Polygon(metal.vertices[tri, :2]) for tri in metal.faces
                if np.allclose(metal.vertices[tri, 2], -projection)]
        assert any(cap.covers(Point(0, 0)) for cap in caps)
        assert not any(cap.covers(Point(inch(1.7).meters, 0)) for cap in caps)


def test_panel_cut_opens_its_back_paint_without_cutting_the_next_layer():
    wall = SimpleNamespace(
        layers=[SimpleNamespace(name="back-paint", thickness_m=0),
                SimpleNamespace(name="stud", thickness_m=.14)],
        layer_depth_m=lambda name, face: .0127)
    opening = SimpleNamespace(depth_m=.0127, depth_from="exterior")
    assert cuts_layer(wall, "back-paint", opening)
    assert not cuts_layer(wall, "stud", opening)


def test_side_entry_boot_has_a_closed_back_and_an_open_face():
    from typehaus.resolve.terminal_geometry import rectangle

    mesh = shell(.3, .2, .1, "rectangular",
                 ((.15, 0, .05), (1, 0, 0), rectangle(.1, .06)))
    caps = _projected_triangles(mesh)
    rear = [p for p, tri in zip(caps, mesh.triangles, strict=True)
            if all(abs(mesh.positions[i][2] - .1) < 1e-9 for i in tri)]
    front = [p for p, tri in zip(caps, mesh.triangles, strict=True)
             if all(abs(mesh.positions[i][2]) < 1e-9 for i in tri)]
    assert any(p.covers(Point(0, 0)) for p in rear)
    assert not any(p.covers(Point(0, 0)) for p in front)


@pytest.mark.parametrize("entry", [None, "bottom", "back"])
def test_neck_is_a_closed_lipped_box_cut_on_its_entry_face(entry):
    """Wall neck 4x8x5 1/4: open face, lip past the walls, the entry face cut, the rest shut."""
    import trimesh

    from typehaus.resolve.neck_solids import LIP_M

    i = 0.0254
    obj = ResolvedCanvasObject(
        uid="R", tag="R", storey="S", domain="mechanical", kind="Register", type_ref="T",
        room=None, position=(0, 0), z_m=1, rotation_degrees=0,
        footprint=((-.05, -.01), (.05, -.01), (.05, .01), (-.05, .01)),
        body_z0_m=1, body_z1_m=1.2, mount=Mount(kind=MountKind.WALL), attachment_wall="W")
    model = SimpleNamespace(wall=lambda _: SimpleNamespace(axis=((-1, 1), (1, 1))))
    neck = TerminalNeck(width=inch(4), height=inch(8), depth=inch(5.25), part="box",
                        section="rectangular", entry=entry)
    mesh = neck_mesh(model, obj, neck)
    metal = trimesh.Trimesh(vertices=mesh.positions, faces=mesh.triangles, process=True)
    assert metal.is_watertight and metal.volume > 0
    pts = np.array(mesh.positions)
    # Local x is world x; the back is +y (the wall's side); the lip reaches 1/2" past x.
    assert pts[:, 0].max() == pytest.approx(2 * i + LIP_M)
    back_y, mid_z = pts[:, 1].max(), 1.1
    bottom_z, mid_y = mid_z - 4 * i, back_y - 2.625 * i

    def covered(axes, at, probe):
        tris = [t for t in mesh.triangles if all(abs(mesh.positions[k][axes[2]] - at) < 1e-6
                                                 for k in t)]
        return any(Polygon([(mesh.positions[k][axes[0]], mesh.positions[k][axes[1]])
                            for k in t]).covers(Point(probe)) for t in tris)

    # The back: open (None), cut to the run (back), shut (bottom). The bottom: cut or shut.
    assert covered((0, 2, 1), back_y, (0, mid_z)) is (entry == "bottom")
    assert covered((0, 1, 2), bottom_z, (0, mid_y)) is (entry != "bottom")
