"""``JoistSpec.extra_lines``: a full-span joist at an authored coordinate, off the module.

The catlin porch track runs WITH its joists and needs a joist under it wherever the module
puts none. The line is a joist like every other — tied at each bearing, billed, measured —
and one closer than 6" to a regular line is refused, since ``joints/bearing.py`` would fold
its tie into its neighbour's.
"""

from __future__ import annotations

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
from typehaus.takeoff.framing import framing_takeoff

_SPF = Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9)
_EXT = Assembly(tag="EXT", layers=(
    Layer(name="stud", material_ref="spf", thickness=inch(5.5),
          function=LayerFunction.STRUCTURE),))


def _model(extra=(), reinforcements=()):
    project = Project(name="XL", project_uuid="00000000-0000-4000-8000-0000000000e1",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90)),
                      building=Building(name="XL"))
    storey = Storey(uid="ST000000e1", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(9))
    plan = PlanModel(project=project, library=Library(materials=(_SPF,), assemblies=(_EXT,)),
                     storeys=(storey,))
    nodes = tuple(Node(uid=f"N000000e0{i}", tag=tag, position=pt(ft(x), ft(y)), open_end=True)
                  for i, (tag, x, y) in enumerate((("N-SW", 0, 0), ("N-SE", 16, 0),
                                                   ("N-NE", 16, 10), ("N-NW", 0, 10))))
    beams = (Beam(uid="B000000e01", tag="BM-S", start_node="N-SW", end_node="N-SE",
                  size="3-2x12"),
             Beam(uid="B000000e02", tag="BM-N", start_node="N-NW", end_node="N-NE",
                  size="3-2x12"))
    floor = FloorSystem(
        uid="FS000000e1", tag="FS-X",
        joists=JoistSpec(member="2x8", spacing=inch(16), direction="y",
                         bearing_refs=("BM-S", "BM-N"), extra_lines=tuple(extra)),
        reinforcements=tuple(reinforcements),
        subfloor=DeckLayer(material_ref="spf", thickness=inch(0.75)), service="deck")
    return resolve(plan.with_elements("main", (*nodes, *beams, floor)))


def _joists(model):
    return [m for m in model.floors[0].members if m.category == "joist"]


def _joist_count(model):
    return sum(row["pieces"] for row in framing_takeoff(model)
               if row["category"] == "joist" and row["profile"] == "2x8")


def test_the_extra_line_is_a_full_span_joist_tied_and_billed():
    base, _ = _model()
    model, findings = _model([inch(102)])  # 8'-6": 6" off the 8'-0" regular line
    assert not [f for f in findings if f.severity.value == "error"]
    extra = [m for m in _joists(model) if "-x00-" in m.child_key]
    assert len(extra) == 1
    (line,) = extra
    assert abs(line.p0[0] - inch(102).meters) < 1e-9
    assert abs(line.length_m - _joists(base)[0].length_m) < 1e-9
    # its own tie at each bearing: two more than the field alone
    rules = UpliftTieRules()
    assert len(bearing_connections(model, rules)) == len(bearing_connections(base, rules)) + 2
    assert _joist_count(model) == _joist_count(base) + 1


def test_the_regular_lines_keep_their_keys():
    base, _ = _model()
    model, _ = _model([inch(102)])
    keys = {m.child_key for m in _joists(base)}
    assert keys <= {m.child_key for m in _joists(model)}


def test_a_line_under_6_inches_from_a_regular_joist_is_refused():
    model, findings = _model([inch(100)])  # 4" off 8'-0"
    errors = [f for f in findings if f.check_id == "integrity.floor_extra_line"]
    assert len(errors) == 1 and "under the 6\"" in errors[0].message
    assert not [m for m in _joists(model) if "-x" in m.child_key]


def test_a_line_outside_the_field_is_refused():
    _, findings = _model([ft(20)])
    assert any("outside the joist field" in f.message for f in findings
               if f.check_id == "integrity.floor_extra_line")


def test_a_block_beside_an_extra_line_stops_at_it():
    from typehaus.model import JoistReinforcement

    block = JoistReinforcement(at=pt(inch(102), ft(5)), plies=1, blocking=True)
    model, _ = _model([inch(102)], [block])
    blocks = [m for m in model.floors[0].members if m.category == "blocking"]
    assert blocks
    # cut between the extra line (102") and its 96"/112" neighbours, never across it
    for m in blocks:
        lo, hi = sorted((m.p0[0], m.p1[0]))
        assert hi <= inch(102).meters - inch(0.75).meters + 1e-9 or \
            lo >= inch(102).meters + inch(0.75).meters - 1e-9


def test_two_extra_lines_within_6_inches_of_each_other_are_refused():
    """A duplicate, and a near-sibling 4" off, each lay one line only."""
    for extra in ([inch(102), inch(102)], [inch(102), inch(106)]):
        model, findings = _model(extra)
        errors = [f for f in findings if f.check_id == "integrity.floor_extra_line"]
        assert len(errors) == 1 and "from another extra line" in errors[0].message, extra
        assert len([m for m in _joists(model) if "-x" in m.child_key]) == 1
