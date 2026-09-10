"""A drip flashing's ``back_side`` must actually face the building.

``Flashing.back_side`` names which side of the ``p0 -> p1`` path faces the building, and on
a ``DRIP_FLASHING`` it is load bearing rather than cosmetic: the run resolves as a bent
angle whose turn-down hangs off the *outboard* end. Point it the wrong way and the piece
that is supposed to throw water clear throws it back behind the cladding instead.

Nothing graded it. The field is authored per run, usually by a small helper that derives it
from an "outward" direction, and the derivation is only correct for the path direction that
helper happens to walk. Reverse a run's endpoints, or reuse the formula on a run that
travels along a different axis, and the value inverts with no geometric consequence the
model reports — the resolver builds a bend either way and every takeoff, drawing and
quantity is satisfied. ``houses/catlin/plan/storeys/garage.py`` says so in as many words
where it authors its stem loop: "Get one direction wrong and the drip points at the wall
with no finding: nothing grades ``back_side``. Confirm it in the viewer."

**The rule.** The back-side normal must point *toward* the body the run trims. The path's
left-hand normal is ``resolve/geometry.normal(d) = (-dy, dx)``; the right-hand normal is its
negation. Whichever ``back_side`` names, it has to aim at the reference point below rather
than away from it.

**The reference point** is the centroid of every drip run's path points on the same storey.
Drip runs are authored as a loop around the body they trim — a roof's four edges, a stem
wall's four faces — so that centroid is the inside of the loop, and "toward it" is "toward
the building" for every run in it. The host is deliberately *not* consulted: a run's
``host_ref`` names a roof or a gutter, and at plan level neither carries a plan footprint to
take a centroid of, while a gutter runs parallel to the drip and so names no side at all.

**What is deliberately not graded.** A ``vertical`` run's path spans the cladding thickness
rather than travelling along the building, so its plan normal means nothing. And a run whose
reference point falls on its own path line cannot be judged at all: a lone run on a storey
is its own centroid, so "toward" has no direction. Both are reported UNKNOWN rather than
guessed, because the failure this check exists to catch is precisely a value that looks
plausible from either side.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import TrimKind
from typehaus.model.trim import Flashing
from typehaus.quantities import M_PER_IN

_CHECK_ID = "integrity.drip_flashing_back_side"

#: How far off a run's own line the reference point must fall before "toward it" names a
#: side at all. A run 6" from the centroid of what it trims is not a run around a body.
_DEGENERATE_M = 6.0 * M_PER_IN


def _xy(point) -> tuple[float, float]:
    return (point.x.meters, point.y.meters)


def _back_normal(p0: tuple[float, float], p1: tuple[float, float],
                 back_side: str) -> tuple[float, float] | None:
    """The unit normal on ``back_side`` of the path, or None for a zero-length run."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0.0:
        return None
    dx, dy = dx / length, dy / length
    # resolve/geometry.normal is the LEFT (90 deg CCW) normal; right is its negation.
    return (-dy, dx) if back_side == "left" else (dy, -dx)


@check(Tier.INTEGRITY, _CHECK_ID)
def drip_flashing_back_side(ctx: CheckContext) -> list[Finding]:
    runs = [e for e in ctx.plan.all_elements()
            if isinstance(e, Flashing) and e.kind is TrimKind.DRIP_FLASHING]
    if not runs:
        return [not_applicable(_CHECK_ID, "no drip flashing is modelled in this building")]

    storey_of: dict[str | None, str] = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            storey_of[getattr(element, "tag", None)] = storey.tag

    # The loop fallback: every drip path point on a storey, so a run with no host is judged
    # against the inside of the loop its siblings form.
    by_storey: dict[str | None, list[tuple[float, float]]] = {}
    for run in runs:
        by_storey.setdefault(storey_of.get(run.tag), []).extend(_xy(p) for p in run.path)

    findings: list[Finding] = []
    correct = 0
    for run in runs:
        if getattr(run, "vertical", False):
            findings.append(unknown(
                _CHECK_ID, f"{run.tag} is a vertical run — its path spans the cladding "
                           "thickness, so a plan normal does not name a side of the "
                           "building", tags=(run.tag,)))
            continue
        p0, p1 = _xy(run.path[0]), _xy(run.path[-1])
        back = _back_normal(p0, p1, run.back_side)
        if back is None:
            findings.append(unknown(_CHECK_ID, f"{run.tag} has a zero-length path",
                                    tags=(run.tag,)))
            continue

        points = by_storey.get(storey_of.get(run.tag)) or []
        if len(points) < 4:
            findings.append(unknown(
                _CHECK_ID, f"{run.tag} has too few sibling drip runs on its storey to form a "
                           "loop — nothing names which side of it is the building",
                tags=(run.tag,)))
            continue
        reference = (sum(p[0] for p in points) / len(points),
                     sum(p[1] for p in points) / len(points))

        mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
        to_reference = (reference[0] - mid[0], reference[1] - mid[1])
        # Only the component along the normal matters: the along-path component is where the
        # run sits on the edge, not which side of it the building is.
        toward = to_reference[0] * back[0] + to_reference[1] * back[1]
        if abs(toward) < _DEGENERATE_M:
            findings.append(unknown(
                _CHECK_ID,
                f"{run.tag} sits within 6\" of its storey's drip loop centroid measured "
                "across its own line — too close to name a side", tags=(run.tag,)))
            continue
        if toward > 0.0:
            correct += 1
            continue
        findings.append(failed(
            _CHECK_ID,
            f"{run.tag} is back_side=\"{run.back_side}\", which points its back "
            f"{abs(toward) / M_PER_IN:.0f}\" AWAY from the loop those runs form — the "
            "turn-down therefore hangs on the building side and throws water behind "
            "the cladding",
            tags=(run.tag,),
            fix=(f"set back_side=\"{'right' if run.back_side == 'left' else 'left'}\" on "
                 f"{run.tag}, or reverse its path endpoints — back_side names the side of "
                 "p0->p1 that faces the building")))

    if not findings:
        return [passed(_CHECK_ID, f"all {correct} drip flashing runs carry a back_side "
                                  "facing the building they trim")]
    return findings
