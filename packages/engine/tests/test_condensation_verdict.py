"""The condensation verdict the check and the displays share (``condensation_verdict``).

The UI card, the Building Science reader and ``haus explain --card`` used to plot the
99%-design-hour walk and badge its crossing RISK, while the check graded that walk as a
screen and passed EXT_2X6 on the monthly gate (and deferred ROOF to R806.5). ``status`` is
the gate's; the screen rides alongside and is never the verdict.
"""

from __future__ import annotations

from test_building_science_monthly_gate import _LIBRARY, _NORMALS, _framed_wall

from typehaus.checks.building_science.condensation_verdict import assess_layers
from typehaus.checks.building_science.glaser import CondensationAnalysis
from typehaus.checks.registry import Preferences
from typehaus.model import Layer, LayerFunction, Site, degF, ft, inch


def _site(normals=_NORMALS) -> Site:
    return Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                design_temp_cooling=degF(90), monthly_normals=normals)


def _verdict(ci_in: float, site: Site | None = None):
    outboard = ([Layer(name="ci", material_ref="eps", thickness=inch(ci_in),
                       function=LayerFunction.INSULATION)] if ci_in else [])
    wall = _framed_wall("W", *outboard)
    return assess_layers("W", list(wall.layers), wall, _LIBRARY, site=site or _site(),
                         preferences=Preferences(), is_roof=False)


def test_a_cold_snap_crossing_does_not_make_a_passing_wall_a_risk() -> None:
    """4" of EPS: the -15 F hour crosses, every monthly mean clears. The status is safe."""
    verdict = _verdict(4.0)
    assert verdict.screen.has_risk
    assert verdict.status == "safe"
    payload = verdict.as_dict()
    assert payload["status"] == "safe"
    assert payload["screen"]["status"] == "risk"
    assert payload["gate_month"] in ("December", "January", "February")
    # The plotted profile is the gate's worst month, not the design hour.
    assert payload["points"] == verdict.gate.analysis.as_dict()["points"]


def test_a_gate_crossing_is_the_only_risk() -> None:
    assert _verdict(0.0).status == "risk"


def test_no_monthly_normals_is_unknown_not_the_screen() -> None:
    verdict = _verdict(4.0, _site(normals=()))
    assert verdict.status == "unknown"
    assert verdict.as_dict()["points"] == verdict.screen.as_dict()["points"]


def test_a_crossing_at_a_layer_face_names_the_interface() -> None:
    near_face = CondensationAnalysis("X", (), crossing_layer="stud", crossing_fraction=0.97,
                                     plane_names=("gwb", "stud", "sheathing"))
    assert near_face.crossing_description == (
        "the outboard face of stud (inner face of sheathing)")
    mid = CondensationAnalysis("X", (), crossing_layer="stud", crossing_fraction=0.56,
                               plane_names=("gwb", "stud", "sheathing"))
    assert mid.crossing_description == "stud (56% through layer)"


def test_catlin_payload_follows_the_check(catlin_model_ro) -> None:
    """EXT_2X6 passes the gate with a cold-snap note; ROOF is deferred to R806.5."""
    from conftest import CATLIN

    from typehaus.checks import load_preferences
    from typehaus.server.model_json_document import _building_science

    science = _building_science(catlin_model_ro, load_preferences(CATLIN))
    assert science is not None
    by_tag = {item["assembly"]: item for item in science["condensation"]}
    wall = by_tag["EXT_2X6"]
    assert wall["status"] == "safe"
    assert wall["screen"]["status"] == "risk"
    assert wall["screen"]["crossing_description"] == (
        "the outboard face of stud (inner face of sheathing)")
    roof = by_tag["ROOF"]
    assert roof["status"] == "deferred"
    assert roof["deferred_to"] == "code.R806_5_unvented_roof"
