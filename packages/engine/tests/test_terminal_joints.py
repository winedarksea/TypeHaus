"""``resolve/terminal_joints``: how a terminal meets its run, read in 3D (decision #136)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.terminal_faces import TerminalFace
from typehaus.resolve.terminal_joints import (
    END,
    SIDE,
    STRAIGHT,
    THROUGH,
    TURN_90,
    UNREACHED,
    classify,
    terminal_joints,
)

IN = M_PER_IN


def _duct(points, diameter=None, width=None, depth=None):
    return SimpleNamespace(tag="DU-T", path=[(x * IN, y * IN) for x, y, _ in points],
                           z_m=[z * IN for *_, z in points], diameter_m=diameter,
                           width_m=width, depth_m=depth)


def _wall_face(width=12.0, height=6.0, room=3.7):
    """A wall neck's back at the origin, the duct behind it in +x (the old suite grille)."""
    return TerminalFace((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
                        width * IN, height * IN, room * IN, "neck")


def test_a_run_through_its_grille_into_the_room_is_through():
    # DU-S-HP-SUITE at HEAD: 10x8 straight through REG-S-HP-SUITE, 13.3" on into the suite.
    duct = _duct([(17.1, 0, -0.3), (-16.9, 0, -0.3)], width=10 * IN, depth=8 * IN)
    joint = classify("REG-T", duct, _wall_face())
    assert joint.kind == THROUGH, joint.detail
    assert '13.2" on into the room' in joint.detail


def test_a_run_ending_inside_the_neck_is_a_straight_end():
    # The bedroom side boots: a 6" run stops inside the neck, short of the room face.
    duct = _duct([(28.6, 0, -0.5), (-2.8, 0, -0.5)], diameter=6 * IN)
    joint = classify("REG-T", duct, _wall_face())
    assert (joint.kind, joint.turn, joint.end_index) == (END, STRAIGHT, 1)


def test_a_riser_beside_the_neck_back_is_a_90_end():
    # REG-M-RET-STUDY's shape: a 4" riser drops behind the neck and stops just below it.
    duct = _duct([(0.3, 0, 96.0), (0.3, 0, -3.6)], diameter=4 * IN)
    joint = classify("REG-T", duct, _wall_face(4.0, 4.0, 4.7))
    assert (joint.kind, joint.turn) == (END, TURN_90), joint.detail


def test_a_trunk_passing_behind_the_face_is_a_side_joint():
    duct = _duct([(5.0, -40, 0), (5.0, 40, 0)], width=10 * IN, depth=8 * IN)
    joint = classify("REG-T", duct, _wall_face())
    assert joint.kind == SIDE, joint.detail
    assert joint.gap_m == pytest.approx(0.0, abs=1e-9)  # 5" to centre less its 5" half width


def test_a_run_past_a_boots_reach_is_unreached():
    duct = _duct([(30.0, -40, 0), (30.0, 40, 0)], diameter=6 * IN)
    assert classify("REG-T", duct, _wall_face()).kind == UNREACHED


def test_catlin_terminals_all_meet_their_runs(catlin_model_ro):
    joints = terminal_joints(catlin_model_ro)
    bad = {tag: j.detail for tag, j in joints.items() if j.kind in (THROUGH, UNREACHED)}
    assert not bad
    # Once mid-run boots of a plan-only nearest; in 3D each is the end of a riser run.
    for tag in ("REG-B-SUP3", "REG-S-EXH3", "REG-M-RET-STUDY", "REG-A-STUBATH-EXH"):
        assert joints[tag].kind == END, joints[tag].detail
