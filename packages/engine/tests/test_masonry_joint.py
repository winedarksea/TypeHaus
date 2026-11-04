"""``structural.masonry_movement_joint`` against notes/sunken_garden_veneer_beam.md §6g.

The oracle is the note's hand pass: BIA TN 18A Eq. 1 at W-B-BRICK's two ends, both
jointed, each taking half the run. Since 2026-11-04 (§6k) both joints are 1/2" Class 50
silicone and the wythe runs x 114.5"..317.5", a 203.0" run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.findings import Result

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"
_JOINTS = "plan/masonry_joints.py"

#: §6k, by hand.
_ORACLE = {
    "run_in": 203.0,            # 317.5 - 114.5
    "movement_in": 0.09135,     # 0.0009 x 203.0 / 2
    "ratio": 0.365,             # / (0.5 x 0.50), both ends
    "alone_ratio": 0.731,       # 0.0009 x 203.0 / 0.25 — one joint takes the whole run
}


def _joint(findings, tag):
    return next(f for f in findings if f.message.startswith(f"[advisory, not engineering] {tag}"))


def _run(ctx):
    from typehaus.checks.structural.masonry_joint import masonry_movement_joint
    return masonry_movement_joint(ctx)


@pytest.fixture(scope="module")
def findings(catlin_ctx):
    return _run(catlin_ctx)


def _variant(tmp_path, edit):
    from _helpers import copy_house

    from typehaus.checks.run import build_context
    from typehaus.source import load_plan

    house = copy_house(_CATLIN, tmp_path / "house")
    source = house / _JOINTS
    source.write_text(edit(source.read_text()))
    loaded = load_plan(house)
    assert loaded.plan is not None, [f.message for f in loaded.findings]
    return build_context(loaded.plan, house)[0]


def test_both_ends_pass_at_the_hand_ratios(findings) -> None:
    east, west = _joint(findings, "MJ-B-BRICK-E"), _joint(findings, "MJ-B-BRICK-W")
    assert east.result is Result.PASS and west.result is Result.PASS
    assert f"{_ORACLE['run_in']:.3f}\" run over 2 joint(s)" in east.message
    assert f"= {_ORACLE['movement_in']:.4f}\"" in east.message
    for joint in (east, west):
        assert f"d/c {_ORACLE['ratio']:.3f}" in joint.message
        assert "0.500\" drawn, 0.500\" measured" in joint.message


def test_the_fireplace_wythe_is_out_of_subject(findings) -> None:
    """No cavity, no weather: only W-B-BRICK is an anchored veneer."""
    assert all("W-B-BRICK" in f.message for f in findings)


def test_a_missing_joint_is_a_fail_naming_the_end(tmp_path) -> None:
    def drop_east(text: str) -> str:
        start = text.index("    MovementJoint(uid=\"8C4QVJG0H7\"")
        end = text.index("    MovementJoint(uid=\"H1GWTPAS9B\"", start)
        return text[:start] + text[end:]
    got = _run(_variant(tmp_path, drop_east))
    miss = next(f for f in got if "no MovementJoint" in f.message)
    assert miss.result is Result.FAIL and "N-B-BRICK-E end" in miss.message
    # One joint left: it takes the whole run.
    assert f"d/c {_ORACLE['alone_ratio']:.3f}" in _joint(got, "MJ-B-BRICK-W").message


def test_a_joint_drawn_off_the_gap_fails(tmp_path) -> None:
    ctx = _variant(tmp_path, lambda t: t.replace("pt(inch(317.5), inch(-9.5))",
                                                 "pt(inch(317.375), inch(-9.5))"))
    east = _joint(_run(ctx), "MJ-B-BRICK-E")
    assert east.result is Result.FAIL and "no longer fits" in east.message


@pytest.mark.parametrize(("pct", "result", "ratio"), [
    # Class 25 at 1/2": 0.09135 / 0.125 = 0.731 — why the spec names Class 50.
    ("25.0", Result.PASS, _ORACLE["alone_ratio"]),
    # Class 12.5 at 1/2": 0.09135 / 0.0625 = 1.462 — OVER.
    ("12.5", Result.FAIL, 1.462),
])
def test_a_less_compressible_seal_is_graded_not_assumed(tmp_path, pct, result, ratio) -> None:
    ctx = _variant(tmp_path, lambda t: t.replace('abuts="W-SG-E1", compression_pct=50.0',
                                                 f'abuts="W-SG-E1", compression_pct={pct}'))
    east = _joint(_run(ctx), "MJ-B-BRICK-E")
    assert east.result is result and f"d/c {ratio:.3f}" in east.message


def test_an_unstated_capability_is_unknown(tmp_path) -> None:
    ctx = _variant(tmp_path, lambda t: t.replace('abuts="W-SG-E1", compression_pct=50.0,',
                                                 'abuts="W-SG-E1",'))
    east = _joint(_run(ctx), "MJ-B-BRICK-E")
    assert east.result is Result.UNKNOWN and "compression_pct" in east.message


def test_the_joints_bill_by_the_foot(catlin_model_ro) -> None:
    from typehaus.takeoff.edge_trim import edge_trim_takeoff

    rows = [r for r in edge_trim_takeoff(catlin_model_ro) if r["category"] == "movement_joint"]
    assert sorted(t for r in rows for t in r["tags"]) == ["MJ-B-BRICK-E", "MJ-B-BRICK-W"]
    assert sum(r["length_ft"] for r in rows) == pytest.approx(2 * 89.104 / 12, abs=0.1)
    assert all("over 5/8\" closed-cell backer rod" in r["material"] for r in rows)
