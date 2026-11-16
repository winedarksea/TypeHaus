"""``mep.register_reach`` (3D terminal joints, #136) and ``mep.manifold_feed``."""

from __future__ import annotations

from dataclasses import replace

from _helpers import check_context

from typehaus.checks.mep.manifold_feed import manifold_feed
from typehaus.checks.mep.register_reach import register_reach
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.terminal_joints import END, THROUGH, terminal_joints


def _by_tag(findings, tag):
    return next(f for f in findings if tag in f.element_tags[:1])


def test_a_run_must_end_on_its_terminal_not_pass_through_it(catlin_model) -> None:
    run, tag = "DU-S-HP-SUITE", "REG-S-HP-SUITE"
    joint = terminal_joints(catlin_model)[tag]
    assert joint.kind == END and joint.run == run
    assert _by_tag(register_reach(check_context(model=catlin_model)), tag).result is Result.PASS
    # Run it 30" on past the grille into the suite: the old junction.
    duct = next(d for d in catlin_model.ducts if d.tag == run)
    i, k = joint.end_index, inch(30).meters
    path, z = list(duct.path), list(duct.z_m)
    path[i] = (path[i][0] - joint.axis[0] * k, path[i][1] - joint.axis[1] * k)
    z[i] -= joint.axis[2] * k
    through = replace(duct, path=path, z_m=z)
    catlin_model.ducts = [through if d.tag == run else d for d in catlin_model.ducts]
    assert terminal_joints(catlin_model)[tag].kind == THROUGH
    found = _by_tag(register_reach(check_context(model=catlin_model)), tag)
    assert found.result is Result.FAIL and f"{run} passes through {tag}" in found.message


def test_a_boot_must_reach_its_run_in_z_and_a_manifold_needs_a_feed(catlin_model) -> None:
    ctx = check_context(model=catlin_model)
    assert _by_tag(register_reach(ctx), "REG-S-HP-BED1").result is Result.PASS
    # Lift the wall grille 20" off its trunk: still 0.4" away in plan, no longer connected.
    lifted = [replace(o, body_z0_m=o.body_z0_m + 0.5, body_z1_m=o.body_z1_m + 0.5)
              if o.tag == "REG-S-HP-BED1" else o for o in catlin_model.canvas_objects]
    catlin_model.canvas_objects = lifted
    found = _by_tag(register_reach(check_context(model=catlin_model)), "REG-S-HP-BED1")
    assert found.result is Result.FAIL and "nothing connects them" in found.message

    verdicts = {f.element_tags[0]: f.result for f in manifold_feed(ctx)}
    assert verdicts["EQ-B-ERV-MAN-SUP"] is Result.PASS
    # Take the trunk and riser that feed it away: its two outlets are left unfed.
    feeds = {"DU-B-ERV-SUP-TRUNK", "DU-ERV-RISER-SUP"}
    catlin_model.ducts = [d for d in catlin_model.ducts if d.tag not in feeds]
    verdicts = {f.element_tags[0]: f.result
                for f in manifold_feed(check_context(model=catlin_model))}
    assert verdicts["EQ-B-ERV-MAN-SUP"] is Result.FAIL
    assert verdicts["EQ-B-ERV-MAN-EXH"] is Result.PASS
