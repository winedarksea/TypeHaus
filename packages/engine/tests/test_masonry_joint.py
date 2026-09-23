"""``structural.masonry_movement_joint`` against notes/sunken_garden_veneer_beam.md §6g.

The oracle is the note's hand pass: BIA TN 18A Eq. 1 at W-B-BRICK's two ends, both
jointed, each taking half the run. The court narrowed to 17'-0" on 2026-09-22 and the
wythe with it: x 118"..317.625", a 199.625" run (§6g still prints the 223.625" one).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.findings import Result

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"
_JOINTS = "plan/masonry_joints.py"

#: §6g, by hand.
_ORACLE = {
    "run_in": 199.625,          # 317.625 - 118.000
    "movement_in": 0.089831,    # 0.0009 x 199.625 / 2
    "east_ratio": 0.479,        # / (0.375 x 0.50)
    "west_ratio": 0.045,        # / (4.000 x 0.50)
    "east_alone_ratio": 0.958,  # 0.0009 x 199.625 / 0.1875 — §6g's sensitivity
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
    assert f"d/c {_ORACLE['east_ratio']:.3f}" in east.message
    assert f"d/c {_ORACLE['west_ratio']:.3f}" in west.message
    assert "0.375\" drawn, 0.375\" measured" in east.message
    assert "4.000\" drawn, 4.000\" measured" in west.message


def test_the_fireplace_wythe_is_out_of_subject(findings) -> None:
    """No cavity, no weather: only W-B-BRICK is an anchored veneer."""
    assert all("W-B-BRICK" in f.message for f in findings)


def test_a_missing_joint_is_a_fail_naming_the_end(tmp_path) -> None:
    def drop_east(text: str) -> str:
        start = text.index("    MovementJoint(uid=\"8C4QVJG0H7\"")
        end = text.index("    # WEST", start)
        return text[:start] + text[end:]
    got = _run(_variant(tmp_path, drop_east))
    miss = next(f for f in got if "no MovementJoint" in f.message)
    assert miss.result is Result.FAIL and "N-B-BRICK-E end" in miss.message
    # One joint left: it takes the whole run, 0.0009 x 199.625 / 2.0 = 0.090.
    assert "d/c 0.090" in _joint(got, "MJ-B-BRICK-W").message


def test_a_joint_drawn_off_the_gap_fails(tmp_path) -> None:
    ctx = _variant(tmp_path, lambda t: t.replace("pt(inch(317.625), inch(-13.56))",
                                                 "pt(inch(317.5), inch(-13.56))"))
    east = _joint(_run(ctx), "MJ-B-BRICK-E")
    assert east.result is Result.FAIL and "no longer fits" in east.message


@pytest.mark.parametrize(("pct", "result", "ratio"), [
    # Class 25 at 3/8": 0.0898 / 0.09375 = 0.958 — the shorter run now clears it
    # (it read 1.073 at the 223.625" run), and equals §6g's whole-run sensitivity.
    ("25.0", Result.PASS, _ORACLE["east_alone_ratio"]),
    # Class 12.5 at 3/8": 0.0898 / 0.046875 = 1.916 — OVER.
    ("12.5", Result.FAIL, 1.916),
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
    assert sorted(r["tags"][0] for r in rows) == ["MJ-B-BRICK-E", "MJ-B-BRICK-W"]
    assert all(r["length_ft"] == pytest.approx(89.104 / 12, abs=0.05) for r in rows)
    east = next(r for r in rows if r["tags"] == ["MJ-B-BRICK-E"])
    assert "over 1/2\" Nomaco HBR" in east["material"]
