"""``mep.run_in_joist_flange`` — no run may take any of an I-joist's flange. Ever.

Every I-joist maker forbids cutting, notching or boring a flange, at any size and station
(``mep_bores.i_joist_flange_cut``). ``mep.run_member_crossing`` enforces that for a leg
CROSSING a joist inside the floor's window; nothing graded a riser or a leg running along
the bay whose envelope clips a flange edge, which is how ``PR-B-LAV1-DRAIN`` came to stand
0.765" inside ``joist-0-001``'s flange at 0 FAIL.

Every I-joist floor member is read — joist, sister, I-joist blocking — against the envelope
(``resolve/mep_envelopes``). A leg across a joist or rim stays ``run_member_crossing``'s;
across an I-joist BLOCK it is graded here, since nothing else reads blocking. The cut is
the envelope's plan bite into the flange's width for a riser or a leg along the member, and
its z overlap with the flange for a leg across it.

``Tier.STRUCTURAL``, no ``PermitItemSpec`` — the ``mep.run_member_crossing`` footing.
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
    member_footprint,
    relation,
    z_overlap,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "mep.run_in_joist_flange"
_CROSSING_OWNED = ("joist", "rim")


def i_joist_members(floor) -> list:
    """``(member, footprint, ((z0, z1) top flange, (z0, z1) bottom flange))``."""
    from typehaus.resolve.framing.profiles import cross_section

    out = []
    for member in floor.members:
        section = cross_section(member.profile)
        if (member.z0_m is None or section is None or section.shape != "i_joist"
                or not section.flange_thickness_m or member.p0 == member.p1):
            continue
        solid = member_footprint(member)
        if solid is None:
            continue
        footprint, z0, z1 = solid
        flange = section.flange_thickness_m
        out.append((member, footprint, ((z1 - flange, z1), (z0, z0 + flange))))
    return out


def flange_cuts(ctx: CheckContext) -> dict[tuple[str, str], list[tuple]]:
    """``{(run, floor): [(cut_m, member, leg, face)]}`` for every flange a run's surface takes."""
    from shapely import STRtree

    all_legs = legs(ctx.model)
    out: dict[tuple[str, str], list[tuple]] = {}
    for floor in ctx.model.floors:
        members = i_joist_members(floor)
        if not members:
            continue
        out.setdefault(("", floor.tag), [])
        index = STRtree([footprint for _m, footprint, _f in members])
        for leg in all_legs:
            for position in index.query(leg.footprint):
                member, footprint, flanges = members[int(position)]
                band = band_over(leg, footprint)
                if band is None:
                    continue
                _direction, normal = member_axis(member)
                how = relation(leg, member)
                if how == "across" and member.category in _CROSSING_OWNED:
                    continue
                plan = bite(leg, footprint, normal) if how != "across" else None
                for face, (z0, z1) in zip(("top", "bottom"), flanges, strict=True):
                    depth = z_overlap(leg, band, z0, z1)
                    cut = min(depth, z1 - z0) if plan is None else plan
                    if depth > TOLERANCE_M and cut > TOLERANCE_M:
                        out.setdefault((leg.tag, floor.tag), []).append(
                            (cut, member, leg, face))
    return out


@check(Tier.STRUCTURAL, _CID)
def run_in_joist_flange(ctx: CheckContext) -> list[Finding]:
    """One FAIL per (run, floor) whose envelope takes any flange; one PASS per clean floor."""
    from typehaus.resolve.mep_bores import i_joist_flange_cut

    cuts = flange_cuts(ctx)
    if not cuts:
        return [_na(_CID, "no resolved floor is framed with I-joists")]
    out: list[Finding] = []
    for (tag, floor_tag), found in sorted(cuts.items()):
        if not tag:
            continue
        cut, member, leg, face = max(found, key=lambda hit: hit[0])
        verdict = i_joist_flange_cut(member.profile, cut / M_PER_IN)
        keys = sorted({f"{hit[1].child_key} ({hit[3]})" for hit in found})
        where = at(leg.a) if leg.plan_m < 1e-9 else f"{at(leg.a)}-{at(leg.b)}"
        out.append(_fail(
            _CID,
            f"{leg.kind} {tag} at {where} takes the {face} flange of {floor_tag}'s "
            f"{member.category} {member.child_key}: {verdict.basis}. Flanges met: "
            f"{', '.join(keys)}",
            (tag, floor_tag), fix=verdict.remedy))
    for (tag, floor_tag) in sorted(cuts):
        if not tag and not any(key[1] == floor_tag and key[0] for key in cuts):
            out.append(_pass(_CID, f"{floor_tag}: no run's envelope reaches an I-joist "
                                   "flange", (floor_tag,)))
    return out
