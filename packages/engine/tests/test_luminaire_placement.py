"""``advisory.luminaire_placement``: one case per rule, one PASS, on a hand-built context."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.mep.lighting_placement import luminaire_placement
from typehaus.checks.registry import MepPreferences
from typehaus.model import LuminaireForm, LuminaireType, Mount, MountKind, inch
from typehaus.model.enums import DoorOperation
from typehaus.resolve.model import ResolvedCanvasObject

ROOM_RING = [(0, 0), (6, 0), (6, 6), (0, 6)]


def _box(x, y, w, d):
    return [(x - w / 2, y - d / 2), (x + w / 2, y - d / 2), (x + w / 2, y + d / 2),
            (x - w / 2, y + d / 2)]


def _object(tag, kind, type_ref, x, y, z0, z1, w=0.1, d=0.1, mount=None):
    return ResolvedCanvasObject(
        uid=tag, tag=tag, storey="main", domain="x", kind=kind, type_ref=type_ref,
        room="RM", position=(x, y), z_m=z0, rotation_degrees=0.0, footprint=_box(x, y, w, d),
        body_z0_m=z0, body_z1_m=z1, mount=mount)


def _light(tag, x, y, type_ref="CAN", z0=2.4, z1=2.55):
    return _object(tag, "ElectricalDevice", type_ref, x, y, z0, z1,
                   mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=(
                       type_ref == "CAN")))


def _body(tag, x, y, top, kind="Furniture", type_ref="CASE", w=1.0, d=0.6):
    return _object(tag, kind, type_ref, x, y, 0.0, top, w, d)


def _luminaire(tag, form):
    return LuminaireType(tag=tag, name=tag, footprint=(inch(4), inch(4)), height=inch(4),
                         form=form)


def _context(objects, ducts=(), openings=(), extra_appliance_types=()):
    wall = SimpleNamespace(tag="W", storey="main", axis=((0.0, 0.0), (6.0, 0.0)),
                           thickness_m=0.2, depth_layers=lambda: [])
    types = SimpleNamespace(
        electrical_device_types=(_luminaire("CAN", LuminaireForm.RECESSED_CAN),
                                 _luminaire("PANEL", LuminaireForm.PANEL)),
        furniture_types=(SimpleNamespace(tag="CASE", storage=True, work_surface=None),
                         SimpleNamespace(tag="BED", storage=False, work_surface=None)),
        appliance_types=tuple(extra_appliance_types),
        door_types=(SimpleNamespace(tag="DT-OH", operation=DoorOperation.OVERHEAD),))
    room = SimpleNamespace(tag="RM", storey="main", clear_face=(), axis_face=ROOM_RING)
    model = SimpleNamespace(
        canvas_objects=list(objects), light_runs=[], ducts=list(ducts), pipe_runs=[], conduits=[],
        countertops=[], openings=list(openings), rooms=[room], walls=[], ceilings=[],
        wall=lambda tag: wall if tag == "W" else None)
    return SimpleNamespace(plan=SimpleNamespace(library=types), model=model,
                           preferences=SimpleNamespace(mep=MepPreferences()))


def _results(ctx):
    return [(f.result.value, f.element_tags) for f in luminaire_placement(ctx)]


def test_a_clear_can_passes_and_a_bed_headboard_is_not_a_body():
    ctx = _context([_light("CAN-1", 3, 3), _body("BED-1", 3, 3, 1.1, type_ref="BED")])
    assert _results(ctx) == [("pass", ())]


def test_over_a_body_taller_than_a_counter():
    (finding,) = luminaire_placement(_context([_light("CAN-1", 3, 3), _body("CAB-1", 3, 3, 1.1)]))
    assert finding.result.value == "advisory"
    assert finding.message.startswith('CAN-1 is over CAB-1 (top 43" AFF)')
    assert finding.element_tags == ("CAN-1", "CAB-1")


def test_a_downlight_beside_a_tall_face_but_not_a_low_one():
    ctx = _context([_light("CAN-1", 3, 3), _body("TALL", 3, 3.4, 2.2),  # face 0.1 m off the can
                    _light("CAN-2", 1, 1), _body("LOW", 1, 1.4, 0.9)])
    (finding,) = luminaire_placement(ctx)
    assert finding.message.startswith('CAN-1 stands 3.9" from the face of TALL')
    assert finding.element_tags == ("CAN-1", "TALL")


def test_a_duct_hung_under_a_surface_fixture_only():
    duct = SimpleNamespace(tag="DU-1", path=[(2, 3), (4, 3)], z_m=(2.0, 2.0), width_m=0.3,
                           depth_m=0.2)  # top 2.1; the panel's face is at 2.4
    (finding,) = luminaire_placement(_context(
        [_light("PANEL-1", 3, 3, "PANEL"), _light("CAN-1", 3.1, 3)], ducts=[duct]))
    assert finding.message.startswith('PANEL-1 has duct DU-1 crossing it 11.8" below')
    assert finding.element_tags == ("PANEL-1", "DU-1")


def test_garage_door_open_panel_zone_and_opener_rail():
    opener = SimpleNamespace(tag="APPL-OPENER",
                             model_representation=SimpleNamespace(
                                 symbol="liftmaster-87504-267-7ft"))
    door = SimpleNamespace(tag="D", host_wall="W", type_ref="DT-OH", width_m=2.4, height_m=2.1,
                           center_along_m=3.0)
    head = _object("APPL-G-GDO", "Appliance", "APPL-OPENER", 3.8, 3.0, 2.0, None)
    ctx = _context([head, _light("IN-ZONE", 3.0, 1.0), _light("ON-RAIL", 3.77, 2.9),
                    _light("CLEAR", 5.5, 4.5)], openings=[door],
                   extra_appliance_types=[opener])
    found = {f.element_tags[0]: f.message for f in luminaire_placement(ctx)}
    assert set(found) == {"IN-ZONE", "ON-RAIL"}
    assert "open-panel zone of D" in found["IN-ZONE"]
    assert "rail line of APPL-G-GDO to D" in found["ON-RAIL"]


def test_no_luminaire_is_not_applicable():
    assert _results(_context([_body("CAB-1", 3, 3, 1.1)])) == [("not_applicable", ())]
