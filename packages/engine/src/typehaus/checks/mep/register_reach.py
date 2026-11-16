"""Does a register meet the run it names, and does the run END on it? (3D joints)

Graded from ``resolve/terminal_joints`` (decision #136, amending #126/#129), which reads each
register's face against its run's centreline in 3D: no plan proxy, no reach constant here.

* THROUGH: the run crosses the register's face and carries on into the room: FAIL.
  A grille is a terminal, not a hole a duct passes through: end the run on it.
* UNREACHED: no end of the run meets the face, nor its side: FAIL, no drawn connection.
* END / SIDE: a boot from the run's end (straight or 90) or off its side: PASS, quoting
  the joint's reach, offset and derived entry.
* A 90 END onto the terminal's own (``integral``) collar, its neck stating no ``entry``:
  FAIL. A plain collar takes a run square; one arriving across it needs a stack head
  (``TerminalNeck.entry``) or a straight end.
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
    TURN_90,
    UNREACHED,
    TerminalJoint,
    boot_entry,
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
    integral = {p.other for p in ctx.model.duct_parts if p.kind == "boot" and p.integral}
    entries = _neck_entries(ctx)
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
            across = (joint.kind == END and joint.turn == TURN_90 and el.tag in integral
                      and entries.get(el.tag) is None)
            out.append(_grade(joint, across))
    return out


def _neck_entries(ctx: CheckContext) -> dict[str, str | None]:
    types = {t.tag: t for t in ctx.plan.library.register_types}
    return {o.tag: getattr(getattr(types.get(o.type_ref), "neck", None), "entry", None)
            for o in ctx.model.canvas_objects}


def _grade(joint: TerminalJoint, across: bool = False) -> Finding:
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
    if across:
        return failed(_CID, f"{joint.run} arrives across {joint.register}'s plain integral "
                            f"collar on a 90 ({joint.detail}): author a stack head or end "
                            "the run square", tags,
                      fix=f"give {joint.register}'s neck an entry face (a stack head box), or "
                          f"end {joint.run} straight on the collar")
    return passed(_CID, f"{joint.register}: {joint.detail}, {boot_entry(joint)} entry", tags)
