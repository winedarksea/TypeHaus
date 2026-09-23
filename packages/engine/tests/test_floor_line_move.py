"""``JoistSpec.line_overrides``: one regular joist line moved off the module.

The line keeps its index (so its child key), is laid at the new station and is tied and
billed like any other. A station matching no line, or a move out of the field or within
6" of another line, is refused and the line stays where the module put it.
"""

from __future__ import annotations

from test_floor_extra_line import _joist_count, _joists

from typehaus.hardware.config import UpliftTieRules
from typehaus.joints.bearing import bearing_connections
from typehaus.model import (
    Assembly,
    Beam,
    Building,
    DeckLayer,
    FloorSystem,
    JoistSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Project,
    Site,
    Storey,
    degF,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve

_SPF = Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9)
_EXT = Assembly(tag="EXT", layers=(
    Layer(name="stud", material_ref="spf", thickness=inch(5.5),
          function=LayerFunction.STRUCTURE),))


def _model(moves=()):
    project = Project(name="LM", project_uuid="00000000-0000-4000-8000-0000000000e2",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90)),
                      building=Building(name="LM"))
    storey = Storey(uid="ST000000e2", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(9))
    plan = PlanModel(project=project, library=Library(materials=(_SPF,), assemblies=(_EXT,)),
                     storeys=(storey,))
    nodes = tuple(Node(uid=f"N000000f0{i}", tag=tag, position=pt(ft(x), ft(y)), open_end=True)
                  for i, (tag, x, y) in enumerate((("N-SW", 0, 0), ("N-SE", 16, 0),
                                                   ("N-NE", 16, 10), ("N-NW", 0, 10))))
    beams = (Beam(uid="B000000f01", tag="BM-S", start_node="N-SW", end_node="N-SE",
                  size="3-2x12"),
             Beam(uid="B000000f02", tag="BM-N", start_node="N-NW", end_node="N-NE",
                  size="3-2x12"))
    floor = FloorSystem(
        uid="FS000000e2", tag="FS-M",
        joists=JoistSpec(member="2x8", spacing=inch(16), direction="y",
                         bearing_refs=("BM-S", "BM-N"), line_overrides=tuple(moves)),
        subfloor=DeckLayer(material_ref="spf", thickness=inch(0.75)), service="deck")
    return resolve(plan.with_elements("main", (*nodes, *beams, floor)))


def _line(model, key):
    (member,) = [m for m in _joists(model) if m.child_key == f"joist-0-{key}-0"]
    return member.p0[0] / inch(1).meters


def _refusals(findings):
    return [f for f in findings if f.check_id == "integrity.floor_line_move"]


def test_a_moved_line_keeps_its_key_tie_and_bill():
    base, _ = _model()
    model, findings = _model([(inch(96), inch(98.5))])  # line 006: 8'-0" -> 8'-2 1/2"
    assert not _refusals(findings)
    assert abs(_line(model, "006") - 98.5) < 1e-6
    assert abs(_line(model, "005") - 80.0) < 1e-6  # neighbours untouched
    rules = UpliftTieRules()
    assert len(bearing_connections(model, rules)) == len(bearing_connections(base, rules))
    assert _joist_count(model) == _joist_count(base)


def test_a_station_matching_no_line_is_refused():
    base, _ = _model()
    model, findings = _model([(inch(97), inch(99))])
    (refusal,) = _refusals(findings)
    assert "matches no laid joist line" in refusal.message
    assert {m.p0 for m in _joists(model)} == {m.p0 for m in _joists(base)}


def test_a_move_within_6_inches_of_a_neighbour_is_refused():
    model, findings = _model([(inch(96), inch(108))])  # 4" off 112"
    (refusal,) = _refusals(findings)
    assert "under the 6\"" in refusal.message
    assert abs(_line(model, "006") - 96.0) < 1e-6


def test_a_move_out_of_the_field_is_refused():
    _, findings = _model([(inch(96), ft(20))])
    (refusal,) = _refusals(findings)
    assert "outside the joist field" in refusal.message
