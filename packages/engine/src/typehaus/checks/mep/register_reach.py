"""Does a register meet the run it names, and does the run END on it? (3D joints)

Graded from ``resolve/terminal_joints`` (decision #136, amending #126/#129), which reads each
register's face against its run's centreline in 3D: no plan proxy, no reach constant here.

* THROUGH: the run crosses the register's face and carries on into the room: FAIL.
  A grille is a terminal, not a hole a duct passes through: end the run on it.
* UNREACHED: no end of the run meets the face, nor its side: FAIL, no drawn connection.
* END / SIDE: a boot from the run's end (straight or 90) or off its side: PASS, quoting
  the joint's reach and offset.
* INLET / DROP: graded elsewhere (``inlet_connection_error``, ``terminal_drops``); skipped.

A register whose run has no elevation per vertex or whose face cannot be placed is UNKNOWN.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check, shared
from typehaus.findings import Finding
from typehaus.resolve.terminal_joints import (
    DROP,
    END,
    INLET,
    SIDE,
    THROUGH,
    UNREACHED,
    TerminalJoint,
    terminal_joints,
)

_CID = "mep.register_reach"


def joints(ctx: CheckContext) -> dict[str, TerminalJoint]:
    """``terminal_joints`` for this model, computed once per check run."""
    return shared(ctx, "terminal_joints", lambda: terminal_joints(ctx.model))


@check(Tier.INTEGRITY, _CID)
def register_reach(ctx: CheckContext) -> list[Finding]:
    """Each register's run ends on its terminal (or takes off beside it): none passes through."""
    found = joints(ctx)
    runs = {d.tag: d for d in ctx.model.ducts if len(d.path) >= 2}
    placed = {o.tag for o in ctx.model.canvas_objects}
    out: list[Finding] = []
    for el in ctx.plan.all_elements():
        if el.element_kind != "Register" or not getattr(el, "duct_ref", None):
            continue
        joint = found.get(el.tag)
        if joint is None:
            run = runs.get(el.duct_ref)
            if run is not None and el.tag in placed:  # no joint: no elevation per vertex
                out.append(unknown(_CID, f"{run.tag} has no elevation per vertex, so "
                                         f"{el.tag}'s connection cannot be read in 3D",
                                   (el.tag, run.tag)))
            continue  # no run, or no placed register: other checks say so
        if joint.kind not in (DROP, INLET):
            out.append(_grade(joint))
    return out


def _grade(joint: TerminalJoint) -> Finding:
    tags = (joint.register, joint.run)
    if joint.kind == THROUGH:
        return failed(_CID, f"{joint.run} passes through {joint.register}: end the run on its "
                            f"terminal ({joint.detail})", tags,
                      fix=f"end {joint.run} behind {joint.register} (a boot), or give the "
                          "register its own run")
    if joint.kind == UNREACHED:
        return failed(_CID, f"{joint.register} names {joint.run} but nothing connects them: "
                            f"{joint.detail}", tags,
                      fix=f"draw {joint.run} to {joint.register}, or name the run that "
                          "serves it")
    assert joint.kind in (END, SIDE), joint.kind
    return passed(_CID, f"{joint.register}: {joint.detail}", tags)
