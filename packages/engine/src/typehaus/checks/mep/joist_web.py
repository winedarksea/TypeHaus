"""``mep.run_in_joist_web`` — no run may lie along, or stand in, an I-joist's web.

``mep.run_member_crossing`` grades a leg crossing a joist (a bore through the web), and
``mep.run_in_joist_flange`` a flange the envelope clips. Neither saw a leg running along the
bay INSIDE the web: ``PR-B-CW-TRUNK`` and ``-CW-BATH2`` stood in FS-M-WEST joist 012's web at
0 FAIL. That is not a hole on any maker's chart; it is the web's removal.

The web is the strip of the web's thickness centred in the member's plan, over the z gap
between its flanges. A riser or a leg along the member FAILs when its envelope
(``resolve/mep_envelopes``, lagging included) bites that strip in plan and overlaps that band
in z. A leg across the member is ``run_member_crossing``'s bore and is skipped.

``Tier.STRUCTURAL``, no ``PermitItemSpec`` — the ``mep.run_in_joist_flange`` footing.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.mep.framing_envelope import (
    TOLERANCE_M,
    at,
    band_over,
    bite,
    legs,
    member_axis,
    relation,
    z_overlap,
)
from typehaus.checks.mep.joist_flange import i_joist_members
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "mep.run_in_joist_web"


def _web_strip(member, footprint, thickness_m: float):
    """The web's plan strip: ``thickness_m`` wide, centred across the member's footprint."""
    from shapely.geometry import LineString

    from typehaus.checks.mep.framing_envelope import extent_along

    direction, normal = member_axis(member)
    low, high = extent_along(footprint, normal)
    start, end = extent_along(footprint, direction)
    mid = (low + high) / 2.0
    pad = 1.0
    line = LineString([
        (direction[0] * (start - pad) + normal[0] * mid,
         direction[1] * (start - pad) + normal[1] * mid),
        (direction[0] * (end + pad) + normal[0] * mid,
         direction[1] * (end + pad) + normal[1] * mid)])
    return line.buffer(thickness_m / 2.0, cap_style="flat").intersection(footprint)


def web_hits(ctx: CheckContext) -> dict[str, list[tuple]]:
    """``{floor: [(run, bite_m, member, leg)]}``; every I-joist floor gets a key."""
    from shapely import STRtree

    from typehaus.resolve.framing.profiles import cross_section

    all_legs = legs(ctx.model)
    out: dict[str, list[tuple]] = {}
    for floor in ctx.model.floors:
        webs = []
        for member, footprint, (top, bottom) in i_joist_members(floor):
            thickness = cross_section(member.profile).web_thickness_m
            if not thickness or bottom[1] >= top[0]:
                continue
            strip = _web_strip(member, footprint, thickness)
            if not strip.is_empty:
                webs.append((member, strip, bottom[1], top[0]))
        if not webs:
            continue
        found = out.setdefault(floor.tag, [])
        index = STRtree([strip for _m, strip, _z0, _z1 in webs])
        for leg in all_legs:
            for position in index.query(leg.footprint):
                member, strip, z0, z1 = webs[int(position)]
                band = band_over(leg, strip)
                if band is None or relation(leg, member) == "across":
                    continue
                if z_overlap(leg, band, z0, z1) <= TOLERANCE_M:
                    continue
                depth = bite(leg, strip, member_axis(member)[1])
                if depth > TOLERANCE_M:
                    found.append((leg.tag, depth, member, leg))
    return out


@check(Tier.STRUCTURAL, _CID)
def run_in_joist_web(ctx: CheckContext) -> list[Finding]:
    """One FAIL per (run, floor) standing in a web; one PASS per clean I-joist floor."""
    hits = web_hits(ctx)
    if not hits:
        return [_na(_CID, "no resolved floor is framed with I-joists")]
    out: list[Finding] = []
    for floor_tag, found in sorted(hits.items()):
        if not found:
            out.append(_pass(_CID, f"{floor_tag}: no run's envelope lies in an I-joist web",
                             (floor_tag,)))
            continue
        by_run: dict[str, list[tuple]] = {}
        for hit in found:
            by_run.setdefault(hit[0], []).append(hit)
        for tag, runs in sorted(by_run.items()):
            _tag, depth, member, leg = max(runs, key=lambda hit: hit[1])
            keys = sorted({hit[2].child_key for hit in runs})
            how = "stands through" if leg.is_riser else "runs along inside"
            where = at(leg.a) if leg.is_riser else f"{at(leg.a)}-{at(leg.b)}"
            out.append(_fail(
                _CID,
                f"{leg.kind} {tag} {how} the web of {floor_tag}'s {member.category} "
                f"{member.child_key} ({member.profile}) at {where}: its envelope takes "
                f"{depth / M_PER_IN:.3f}\" of the web between the flanges — not a hole on "
                f"any maker's chart but the web's removal. Webs met: {', '.join(keys)}",
                (tag, floor_tag),
                fix=("take the run below the joists, or between them clear of both webs; "
                     "cross a joist only through a charted web hole")))
    return out
