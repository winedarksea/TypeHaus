"""Fixture hosting is explicit support, never an excuse to ignore an invalid placement."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from shapely.geometry import box

from typehaus.checks.advisory.backing_fixings import fixing_support
from typehaus.checks.integrity.furniture_host import furniture_fixture_host
from typehaus.checks.integrity.wall_mounts import best_host
from typehaus.model import Fixture, Furniture, Mount, MountKind, ft, inch, pt
from typehaus.model.placeable_symbols import model_parts
from typehaus.quantities import M_PER_IN as IN
from typehaus.resolve.model import ResolvedCanvasObject


@pytest.mark.parametrize("host_ref,host_room,host_storey,valid", [
    ("VAN", "BATH", "main", True),
    ("MISSING", "BATH", "main", False),
    ("VAN", "OTHER", "main", False),
    ("VAN", "BATH", "upper", False),
])
def test_host_must_be_a_fixture_in_same_room_and_storey(host_ref, host_room, host_storey, valid):
    holder = Furniture(uid="HOLDER0001", tag="HOLDER", type_ref="TP", room="BATH",
                       position=pt(ft(1), ft(1)), host_fixture_ref=host_ref)
    host = Fixture(uid="VANITY0001", tag="VAN", type_ref="VANITY", room=host_room,
                   position=pt(ft(2), ft(1)))
    plan = SimpleNamespace(storeys=[SimpleNamespace(tag="main"), SimpleNamespace(tag="upper")],
                           storey_elements=lambda tag: ([holder] if tag == "main" else [])
                           + ([host] if tag == host_storey else []))
    findings = furniture_fixture_host(SimpleNamespace(plan=plan))
    assert [finding.result.value for finding in findings] == ["pass" if valid else "fail"]


def test_fixture_reference_to_furniture_is_rejected():
    items = [Furniture(uid="HOLDER0001", tag="HOLDER", type_ref="TP", room="BATH",
                       position=pt(ft(1), ft(1)), host_fixture_ref="CHAIR"),
             Furniture(uid="CHAIR00001", tag="CHAIR", type_ref="CHAIR", room="BATH",
                       position=pt(ft(2), ft(1)))]
    plan = SimpleNamespace(storeys=[SimpleNamespace(tag="main")], storey_elements=lambda _: items)
    assert furniture_fixture_host(SimpleNamespace(plan=plan))[0].result.value == "fail"


def test_named_fixture_must_physically_support_the_whole_body_height():
    host = ResolvedCanvasObject(uid="VAN", tag="VAN", storey="main", domain="plumbing",
        kind="Fixture", type_ref="VANITY", room="BATH", position=(1.5, 0.5), z_m=0,
        body_z0_m=0, body_z1_m=1, rotation_degrees=0,
        footprint=tuple(box(1, 0, 2, 1).exterior.coords))
    holder = ResolvedCanvasObject(uid="TP", tag="TP", storey="main", domain="furniture",
        kind="Furniture", type_ref="TP", room="BATH", position=(0.95, 0.5), z_m=0.6,
        body_z0_m=0.6, body_z1_m=0.7, rotation_degrees=-90,
        footprint=tuple(box(0.9, 0.4, 1, 0.6).exterior.coords), host_fixture_ref="VAN",
        mount=Mount(kind=MountKind.WALL, elevation=inch(24)))
    model = SimpleNamespace(canvas_objects=[host, holder])
    assert best_host(model, holder).gap_m == pytest.approx(0)
    assert best_host(model, replace(holder, body_z1_m=1.1)) is None
    assert best_host(model, replace(holder, room="OTHER")) is None
    floating = replace(holder, footprint=tuple(box(0.5, 0.4, 0.6, 0.6).exterior.coords))
    assert best_host(model, floating).gap_m == pytest.approx(0.4)


def test_post_support_uses_actual_wood_and_correct_face():
    from typehaus.model.enums import LayerFunction
    from typehaus.resolve.model import FramedMember, ResolvedLayer, ResolvedWall

    wall = ResolvedWall(uid="W", tag="W", storey="main", assembly="TEST",
        axis=((0, 0), (1, 0)), z0_m=0, z1_m=3,
        layers=(ResolvedLayer(name="stud", material_ref="spf",
            function=LayerFunction.STRUCTURE.value, thickness_m=6 * IN,
            polygon=tuple(box(0, -3 * IN, 1, 3 * IN).exterior.coords)),))
    block = FramedMember(parent_uid="W", child_key="backing-0-000", category="blocking",
        profile="2x6", p0=(0.1, 2.25 * IN), p1=(0.9, 2.25 * IN),
        z0_m=23.25 * IN, z1_m=28.75 * IN, length_m=0.8)
    wall = replace(wall, members=(block,))
    assert fixing_support(wall, "left", (0.5, 4 * IN), 26 * IN) == [block]
    assert not fixing_support(wall, "right", (0.5, -4 * IN), 26 * IN)
    assert not fixing_support(wall, "left", (0.5, 4 * IN), 29 * IN)
    assert not fixing_support(replace(wall, members=()), "left", (0.5, 4 * IN), 26 * IN)


def test_holder_symbol_post_centres_match_fixing_stations():
    parts = model_parts("pivoting-paper-holder", 8.11 * IN, 3.34 * IN, 1.34 * IN)
    plates = [part for part in parts if part["shape"] == "cylinder-depth"
              and part["size"][0] == pytest.approx(1.34 * IN)]
    assert [part["center"][0] / IN for part in plates] == pytest.approx([-3.385, 3.385])
    assert all(part["center"][2] / IN == pytest.approx(0.67) for part in plates)
