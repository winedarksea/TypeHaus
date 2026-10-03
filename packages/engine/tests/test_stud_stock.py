"""A ``layer_materials`` override on a wall's stud layer restocks its stud line."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.model.refs import LayerMaterial
from typehaus.resolve.framing.stud_stock import stamp_stud_stock
from typehaus.resolve.model import FramedMember
from typehaus.takeoff import framing_bom_by_size

_STUD_LINE = {"stud", "king", "jack", "cripple", "corner"}
_LSL_WALLS = {"W-M-S1", "W-M-S2", "W-M-E1", "W-M-N1", "W-M-N1B", "W-M-N2", "W-M-N3",
              "W-M-N3B", "W-M-W1B", "W-M-W1", "W-M-W1C", "W-M-W2", "W-M-W3", "W-M-W4",
              "W-M-C1", "W-M-C2", "W-M-C3", "W-M-C5", "W-M-C5B"}


def _members() -> tuple[FramedMember, ...]:
    p = (0.0, 0.0)
    return tuple(FramedMember("W", f"{cat}-0", cat, "2x6", p, p, 0.0, 2.4, 2.4)
                 for cat in ("stud", "king", "jack", "cripple", "corner",
                             "plate", "header", "sill", "blocking"))


def _wall(*overrides: LayerMaterial):
    rw = SimpleNamespace(layers=(
        SimpleNamespace(name="stud", function="structure", is_cavity=False),
        SimpleNamespace(name="sheathing", function="sheathing", is_cavity=False)))
    return rw, SimpleNamespace(layer_materials=overrides)


def test_override_stamps_the_stud_line_only() -> None:
    rw, authored = _wall(LayerMaterial(layer="stud", material="lsl"))
    out = stamp_stud_stock(_members(), rw, authored)
    assert {m.category for m in out if m.material == "lsl"} == _STUD_LINE
    assert all(m.material is None for m in out if m.category not in _STUD_LINE)


def test_no_override_or_other_layer_leaves_members_alone() -> None:
    members = _members()
    for authored_overrides in ((), (LayerMaterial(layer="sheathing", material="osb"),)):
        rw, authored = _wall(*authored_overrides)
        assert stamp_stud_stock(members, rw, authored) is members


def test_catlin_main_bearing_walls_bill_lsl(catlin_model) -> None:
    by_wall: dict[str, set[str | None]] = {}
    for wall in catlin_model.walls:
        for m in wall.members:
            if m.category in _STUD_LINE:
                by_wall.setdefault(wall.tag, set()).add(m.material)
    assert {tag for tag, mats in by_wall.items() if "lsl" in mats} == _LSL_WALLS
    for tag in _LSL_WALLS:
        assert by_wall[tag] == {"lsl"}, tag
    plates = [m for w in catlin_model.walls if w.tag in _LSL_WALLS for m in w.members
              if m.category == "plate"]
    assert plates and all(m.material is None for m in plates)
    rows = {(r["profile"], r["material"]) for r in framing_bom_by_size(catlin_model)}
    assert ("2x6", "lsl") in rows
