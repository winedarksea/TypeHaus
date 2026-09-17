"""``mep.run_interference`` — two runs may not occupy the same space.

**The largest hole in the MEP set, and it was known.** ``plans/TODO.md`` has carried "37 MEP
interpenetrations remain in the NW column" since 2026-09-15, measured by hand, because
nothing in the engine could report them: ``mep.duct_soffit_occupancy`` grades what shares a
modelled ``Soffit``, ``mep.duct_joist_bay_occupancy`` what shares a bay, and outside those
two rooms a duct and a drain drawn through each other draw exactly like a duct and a drain
that miss.

The predicate is envelope against envelope — the real outside diameter plus insulation, one
prism per segment over that segment's own z range, all of it
:mod:`typehaus.resolve.mep_envelopes`' derivation and the same one the router avoids. A
check that measured a different solid from the one the router plans against would make the
loop impossible to close.

**Contact is not always a clash.** Three things legitimately put two runs in one place and
all three are earned from the model rather than from a naming convention:

* **a fitting** — either run *ending on* the other, which is a wye, a tee, an elbow or a
  riser into a trunk (``mep_envelopes.runs_are_joined``, the generalisation of the rule
  ``mep.duct_connectivity`` already uses);
* **a sleeve** — a rough opening whose ``penetration_for`` names both;
* **a run against itself**, which is not a pair.

Everything else is two things in one hole.

``Tier.STRUCTURAL`` and **no ``PermitItemSpec``**, the same footing as
``mep.run_member_crossing`` and ``mep.run_over_void``: no IRC section says "do not draw a
duct through a drain", and a CODE tier would trip the coverage test and the ``code_ref``
requirement dishonestly. ``CheckReport.counts()`` counts any ``Result.FAIL`` regardless of
severity, so the weight is the same where it matters.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "mep.run_interference"

#: Overlap below this is coordinate noise rather than a clash. A sixteenth of an inch is the
#: grid every coordinate in this repo is authored on, so anything under it is two runs that
#: were drawn to touch.
TOUCH_TOLERANCE_M = 0.0015875


@check(Tier.STRUCTURAL, _CID)
def run_interference(ctx: CheckContext) -> list[Finding]:
    """Every pair of runs, envelope against envelope, in plan and in elevation.

    One finding per interfering pair, naming the **deepest** interpenetration and where it
    is. A builder with a finding needs to know which two and by how much; "the basement is
    congested" is not an instruction.

    A pair whose envelopes merely touch within :data:`TOUCH_TOLERANCE_M` is not reported —
    two runs drawn to touch are drawn to touch — and a run the model does not place in z at
    all is named as a coverage gap rather than graded against a drawing convention.
    """
    from shapely import STRtree

    from typehaus.resolve.mep_envelopes import envelopes, runs_are_joined
    from typehaus.resolve.mep_queries import schematic_conduits

    # **A schematic raceway is not graded, it is disclosed.** Two end elevations say where
    # a run starts and ends and nothing about the six feet between; grading that against the
    # "rises at its last point" convention reports clashes with a drawing rather than with a
    # building, and on catlin it is 100-odd of them. The tags come back as a coverage gap
    # below, which is the honest half of the same sentence.
    gaps = schematic_conduits(ctx.model)
    shells = [e for e in envelopes(ctx.model) if e.prisms and e.tag not in gaps]
    if len(shells) < 2:
        return [_unknown(_CID, "fewer than two runs resolve an envelope in this model, so "
                               "no two of them can occupy one place")]

    tracks = {e.tag: _track(ctx, e.tag) for e in shells}
    sleeved = _sleeved_pairs(ctx)

    flat = [(shell.tag, prism) for shell in shells for prism in shell.prisms]
    index = STRtree([prism.footprint for _tag, prism in flat])

    worst: dict[tuple[str, str], tuple[float, float, int, int]] = {}
    for position, (tag, prism) in enumerate(flat):
        for other_position in index.query(prism.footprint):
            other_position = int(other_position)
            if other_position <= position:
                continue
            other_tag, other = flat[other_position]
            if other_tag == tag:
                continue
            pair = (tag, other_tag) if tag < other_tag else (other_tag, tag)
            if pair in sleeved or runs_are_joined(tracks[tag], tracks[other_tag]):
                continue
            overlap_z = min(prism.z1_m, other.z1_m) - max(prism.z0_m, other.z0_m)
            if overlap_z <= TOUCH_TOLERANCE_M:
                continue
            shared = prism.footprint.intersection(other.footprint)
            if shared.is_empty or shared.area <= 0:
                continue
            # The plan measure is the SHORTER of the two widths the shared area implies,
            # which is the depth one run is inside the other rather than the length of the
            # overlap. A duct crossing a drain at right angles shares a long thin sliver;
            # reporting its length would say "18 inches of clash" about a half-inch graze.
            depth = _penetration_depth(shared)
            if depth <= TOUCH_TOLERANCE_M:
                continue
            score = min(depth, overlap_z)
            if pair not in worst or score > worst[pair][0]:
                worst[pair] = (score, depth, prism.segment, other.segment)

    out: list[Finding] = [
        _fail(_CID,
              f"{a} and {b} interpenetrate: {depth / M_PER_IN:.2f}\" of overlap in plan "
              f"between leg {sa + 1} of {a} and leg {sb + 1} of {b}, and their envelopes "
              f"share {score / M_PER_IN:.2f}\" of elevation — neither run ends on the other "
              "(so this is not a fitting) and no rough opening names them both (so it is "
              "not a sleeve)",
              (a, b),
              fix="re-route one of the two — `haus route --run <tag> --avoid <the other>` "
                  "proposes a lane and `--evaluate` grades it — or give them a shared "
                  "penetration if what is drawn is really one hole")
        for (a, b), (score, depth, sa, sb) in sorted(worst.items())]

    if not out:
        out.append(_pass(_CID, f"{len(shells)} runs resolve an envelope and no two of them "
                               "share a place they are not jointed or sleeved at", ()))
    if gaps:
        out.append(_unknown(
            _CID, f"{len(gaps)} raceway(s) hold two end elevations and a drawing convention "
                  f"rather than a per-vertex profile, so what they clear between those ends "
                  f"is not graded: {', '.join(gaps[:6])}"
                  + (f" (+{len(gaps) - 6} more)" if len(gaps) > 6 else "")
                  + ". Author ConduitRun.elevations to place them in z",
            gaps))
    return out


def _track(ctx: CheckContext, tag: str) -> tuple[tuple, tuple]:
    """``(path, z)`` for one run — the pair ``runs_are_joined`` compares."""
    from typehaus.resolve.mep_envelopes import run_polylines

    for _kind, other, path, z in run_polylines(ctx.model):
        if other == tag:
            return (path, z)
    return ((), ())


def _sleeved_pairs(ctx: CheckContext) -> set[tuple[str, str]]:
    """Pairs of runs a single rough opening names as its reason for existing.

    Two runs through one sleeve are two runs through one sleeve. The hole was authored for
    both of them, which is a statement somebody made on purpose, and it is the only place
    this check takes the model's word rather than its geometry.
    """
    from typehaus.resolve.mep_envelopes import opening_prisms

    out: set[tuple[str, str]] = set()
    for _tag, _door, _host, _prism, _low, _high, names in opening_prisms(ctx.model):
        tags = sorted(set(names))
        for i, first in enumerate(tags):
            for second in tags[i + 1:]:
                out.add((first, second))
    return out


def _penetration_depth(shared) -> float:
    """How deep one envelope is inside the other, from their shared plan area.

    The minimum width of the intersection, approximated as ``area / longest side of its
    bounding box``. A right-angle crossing shares a long thin sliver; its LENGTH is the
    other run's width and says nothing, and its WIDTH is the depth of the intrusion.
    """
    minx, miny, maxx, maxy = shared.bounds
    longest = max(maxx - minx, maxy - miny)
    return shared.area / longest if longest > 0 else 0.0
