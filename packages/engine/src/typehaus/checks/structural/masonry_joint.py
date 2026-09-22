"""``structural.masonry_movement_joint`` — a brick wythe's soft end joints, measured.

**Subject.** An anchored clay-masonry veneer: a wall whose STRUCTURE layer is brick (the
``*brick*`` material glob ``emit/trade_rules`` files under masonry) behind a drained AIRGAP.
An interior wythe (the fireplace) has no cavity and no weather, and is out of subject.

**The rule — BIA Technical Note 18A (2019), Eq. 1.** Unrestrained brickwork moves
``0.0009 x length`` (moisture, freezing and thermal, TN 18). A joint of width ``w`` whose
least compressible part takes ``e`` percent absorbs ``w e / 100``. In a series of joints
each takes half a panel from either side; a wythe jointed at BOTH ends gives each end half
its run, one jointed at one end gives that end all of it. Seal depth at least 1/4".

**Per wythe end.** Another wall's STRUCTURE layer standing beyond the end, within 6" and
overlapping it in depth and height, is a rigid return the brick grows into. Such an end
needs a ``MovementJoint`` hosted on the wythe; one that has it is graded against the gap it
actually stands in (drawn width vs the measured gap, to 1/16") and against Eq. 1. A free end
is not graded. No such wythe anywhere is N/A, from every wall examined.

Oracle: ``houses/catlin/notes/sunken_garden_veneer_beam.md`` §6g, reproduced by
``tests/test_masonry_joint.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.checks._authoring import structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, not_applicable

_ID = "structural.masonry_movement_joint"
_CODE = "BIA Technical Note 18A (2019) Eq. 1"
_M_PER_IN = 0.0254
#: TN 18: total unrestrained movement of clay brickwork per unit length.
MOVEMENT_PER_LENGTH = 0.0009
#: TN 18A: "a minimum sealant depth of 1/4 in."
MIN_SEAL_DEPTH_IN = 0.25
_REACH_IN = 6.0  # how far past a wythe end a return is still "the thing it grows into"
_FIT_IN = 1.0 / 16.0
_TOL_M = 1e-4
_Frame = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]


@dataclass(frozen=True)
class _Band:
    tag: str
    u0: float
    u1: float
    n0: float
    n1: float
    z0: float
    z1: float


def _structure(wall: Any) -> Any:
    return next((ly for ly in wall.layers
                 if ly.function == "structure" and not ly.is_cavity and ly.polygon), None)


def _is_veneer(wall: Any) -> bool:
    layer = _structure(wall)
    return (layer is not None and "brick" in layer.material_ref
            and any(ly.function == "airgap" for ly in wall.layers))


def _frame(wall: Any) -> _Frame:
    (ax, ay), (bx, by) = wall.axis
    length = math.hypot(bx - ax, by - ay)
    u = ((bx - ax) / length, (by - ay) / length)
    return (ax, ay), u, (-u[1], u[0])


def _band(wall: Any, frame: _Frame) -> _Band | None:
    layer = _structure(wall)
    if layer is None:
        return None
    (ox, oy), u, n = frame
    us = [(p[0] - ox) * u[0] + (p[1] - oy) * u[1] for p in layer.polygon]
    ns = [(p[0] - ox) * n[0] + (p[1] - oy) * n[1] for p in layer.polygon]
    return _Band(wall.tag, min(us), max(us), min(ns), max(ns), wall.z0_m, wall.z1_m)


def _returns(ctx: CheckContext, wythe: Any, own: _Band, frame: _Frame) -> dict[str, _Band]:
    """The nearest rigid return past each end ("start"/"end"), within reach."""
    out: dict[str, _Band] = {}
    for wall in ctx.model.walls:
        if wall.tag == wythe.tag:
            continue
        band = _band(wall, frame)
        if band is None or (min(band.n1, own.n1) - max(band.n0, own.n0) <= _TOL_M
                            or min(band.z1, own.z1) - max(band.z0, own.z0) <= _TOL_M):
            continue
        for side, gap in (("start", own.u0 - band.u1), ("end", band.u0 - own.u1)):
            if -_TOL_M <= gap <= _REACH_IN * _M_PER_IN:
                held = out.get(side)
                if held is None or gap < _gap(own, held, side):
                    out[side] = band
    return out


def _gap(own: _Band, other: _Band, side: str) -> float:
    return own.u0 - other.u1 if side == "start" else other.u0 - own.u1


def _joints(ctx: CheckContext, tag: str) -> list[Any]:
    return [e for e in _all_joints(ctx) if e.host_ref == tag]


def _all_joints(ctx: CheckContext) -> list[Any]:
    from typehaus.model.trim import MovementJoint

    return [e for e in ctx.plan.all_elements() if isinstance(e, MovementJoint)]


def _node(ctx: CheckContext, tag: str, side: str) -> str:
    wall = next((e for e in ctx.plan.all_elements() if e.tag == tag), None)
    return str(getattr(wall, f"{side}_node", side))


def _stray(joint: Any, host: str, why: str) -> Finding:
    return structural_advisory(_ID, f"{joint.tag} on {host} is graded by nothing: {why}",
                               (joint.tag,), Result.UNKNOWN, code=_CODE)


def _side(joint: Any, own: _Band, frame: _Frame) -> str:
    (ox, oy), u, _n = frame
    us = [(p.xy_m[0] - ox) * u[0] + (p.xy_m[1] - oy) * u[1] for p in joint.path]
    return "start" if sum(us) / len(us) < (own.u0 + own.u1) / 2.0 else "end"


def _width_in(joint: Any) -> float:
    pts = [p.xy_m for p in joint.path]
    return sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:], strict=True)) / _M_PER_IN


def _grade(joint: Any, wythe: str, other: _Band, gap_in: float, run_in: float,
           shared: int) -> Finding:
    tags = (joint.tag, wythe, other.tag)
    if joint.abuts != other.tag:
        return structural_advisory(
            _ID, f"{joint.tag} names {joint.abuts!r} but {wythe}'s end stands against "
                 f"{other.tag}", tags, Result.FAIL, fix_hint=f"abuts={other.tag!r}", code=_CODE)
    if joint.compression_pct is None:
        return structural_advisory(
            _ID, f"{joint.tag}: no compression_pct, so TN 18A Eq. 1 cannot be read",
            tags, Result.UNKNOWN, fix_hint="author the seal's published compression "
                                           "capability (ASTM C920 class)", code=_CODE)
    width = _width_in(joint)
    depth = joint.thickness.meters / _M_PER_IN
    trib = run_in / shared
    need = MOVEMENT_PER_LENGTH * trib
    takes = width * joint.compression_pct / 100.0
    ratio = need / takes if takes > 0 else math.inf
    head = (f"{joint.tag} at {wythe}'s end against {other.tag}: {width:.3f}\" drawn, "
            f"{gap_in:.3f}\" measured")
    if abs(width - gap_in) > _FIT_IN:
        return structural_advisory(
            _ID, f"{head} — the joint no longer fits the gap it was drawn for", tags,
            Result.FAIL, fix_hint="redraw the joint across the wythe's actual end gap",
            code=_CODE)
    bad = ratio > 1.0 or depth + 1e-9 < MIN_SEAL_DEPTH_IN
    return structural_advisory(
        _ID, f"{head}. Movement 0.0009 x {trib:.2f}\" ({run_in:.3f}\" run over {shared} "
             f"joint(s)) = {need:.4f}\" against {width:.3f}\" x {joint.compression_pct:g}% = "
             f"{takes:.4f}\", d/c {ratio:.3f}; seal depth {depth:.3f}\" (TN 18A min "
             f"{MIN_SEAL_DEPTH_IN:g}\"). {joint.material} over {joint.backer or 'no backer'}",
        tags, Result.FAIL if bad else Result.PASS, code=_CODE,
        fix_hint="widen the joint or pick a more compressible seal" if bad else None)


@check(Tier.STRUCTURAL, _ID)
def masonry_movement_joint(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    wythes = [w for w in ctx.model.walls if _is_veneer(w)]
    for wythe in sorted(wythes, key=lambda w: w.tag):
        frame = _frame(wythe)
        own = _band(wythe, frame)
        assert own is not None
        returns = _returns(ctx, wythe, own, frame)
        joints = {_side(j, own, frame): j for j in _joints(ctx, wythe.tag)}
        run_in = (own.u1 - own.u0) / _M_PER_IN
        shared = max(1, sum(1 for side in ("start", "end") if side in joints))
        for side in ("start", "end"):
            other = returns.get(side)
            if other is None:
                continue
            joint = joints.get(side)
            gap_in = _gap(own, other, side) / _M_PER_IN
            if joint is None:
                out.append(structural_advisory(
                    _ID, f"{wythe.tag}'s {_node(ctx, wythe.tag, side)} end stands "
                         f"{gap_in:.3f}\" off {other.tag} "
                         f"with no MovementJoint: the brick grows into it", (wythe.tag,
                                                                               other.tag),
                    Result.FAIL, fix_hint="author a MovementJoint(host_ref=..., abuts=...)",
                    code=_CODE))
                continue
            out.append(_grade(joint, wythe.tag, other, gap_in, run_in, shared))
        out.extend(_stray(j, wythe.tag, f"its {side} end meets nothing within "
                                          f"{_REACH_IN:g}\"")
                   for side, j in joints.items() if side not in returns)
    hosts = {w.tag for w in wythes}
    out.extend(_stray(j, j.host_ref or "(none)", "the host is not an anchored brick veneer")
               for j in _all_joints(ctx) if j.host_ref not in hosts)
    if not out and ctx.model.walls:
        what = ("no end of an anchored brick veneer stands against a rigid return"
                if wythes else "no wall is an anchored brick veneer over a drained cavity")
        out.append(not_applicable(_ID, what, (), code=_CODE))
    return out
