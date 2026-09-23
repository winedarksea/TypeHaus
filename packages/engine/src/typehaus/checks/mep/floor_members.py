"""``mep.run_through_floor_member`` — a trimmer, header or block standing in a run's way.

``mep.run_member_crossing`` grades joists and rims, and only legs that CROSS them inside the
floor's window. Nothing graded a framing member against a run's envelope otherwise: when
``FO-M-ERV-OA`` was framed on 2026-09-15 its full-bay LVL trimmer packs landed on six live
risers at 0 FAIL. This reads every solid (non-I-joist) floor member — trimmer, header,
blocking, a solid-sawn joist or rim — against the envelope (``resolve/mep_envelopes``):

* a **riser** through a member's plan, or a leg running **along** inside it, occupies the
  member itself: that is not a hole anyone drills, it is the member's removal. FAIL.
* a leg **across** a trimmer, header or block is a bore, graded by ``mep_bores`` — which is
  an honest UNKNOWN for an LVL, whose holes come off the maker's chart. Across a joist or a
  rim it is ``mep.run_member_crossing``'s, and skipped here.

A riser through a FLAT member (a block laid on its face) is a drilled hole, not a removal,
and is graded as a bore. I-joist members are ``mep.run_in_joist_flange``'s; the 2x6 boxes
framed around a crossing are ``mep.run_through_blocking``'s, and both are skipped.
``Tier.STRUCTURAL``, no ``PermitItemSpec`` — the ``mep.run_through_beam`` footing.
"""

from __future__ import annotations

import re

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
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

_CID = "mep.run_through_floor_member"
#: Categories ``mep.run_member_crossing`` owns when a leg crosses them.
_CROSSING_OWNED = ("joist", "rim")
#: The 2x6 box ``resolve/floor_blocking`` frames AROUND a crossing run; its fit is
#: ``blocking_conflicts``, graded by ``mep.run_through_blocking``.
_BOX_PART = re.compile(r"-(rail-top|rail-bottom|cheek-lo|cheek-hi)$")


def solid_members(floor) -> list:
    """``(member, footprint, z0, z1)`` for every non-I-joist member this check reads."""
    from typehaus.resolve.framing.profiles import cross_section

    out = []
    for member in floor.members:
        key = member.child_key
        if member.z0_m is None or key.startswith("bearing-block") or _BOX_PART.search(key):
            continue
        section = cross_section(member.profile)
        if section is None or section.shape == "i_joist" or member.p0 == member.p1:
            continue
        solid = member_footprint(member)
        if solid is not None:
            out.append((member, *solid))
    return out


def _plan_width(footprint, normal) -> float:
    from typehaus.checks.mep.framing_envelope import extent_along

    low, high = extent_along(footprint, normal)
    return high - low


def _bore(member, diameter_in: float):
    from typehaus.resolve.mep_bores import header_bore, joist_bore

    if member.category == "header":
        return header_bore(member.profile, diameter_in)
    return joist_bore(member.profile, diameter_in)


@check(Tier.STRUCTURAL, _CID)
def run_through_floor_member(ctx: CheckContext) -> list[Finding]:
    """One finding per (run, floor) whose envelope meets a solid floor member."""
    from shapely import STRtree

    floors = [(floor, solid_members(floor)) for floor in ctx.model.floors]
    floors = [(floor, solids) for floor, solids in floors if solids]
    if not floors:
        return [_na(_CID, "no resolved floor carries a solid (non-I-joist) member")]
    all_legs = legs(ctx.model)
    out: list[Finding] = []
    for floor, solids in floors:
        index = STRtree([footprint for _m, footprint, _z0, _z1 in solids])
        hits: dict[str, list[tuple]] = {}
        for leg in all_legs:
            for position in index.query(leg.footprint):
                member, footprint, z0, z1 = solids[int(position)]
                band = band_over(leg, footprint)
                if band is None or z_overlap(leg, band, z0, z1) <= TOLERANCE_M:
                    continue
                _direction, normal = member_axis(member)
                how = relation(leg, member)
                flat = how == "riser" and z1 - z0 < _plan_width(footprint, normal)
                if how == "across" or flat:
                    if member.category not in _CROSSING_OWNED or flat:
                        hits.setdefault(leg.tag, []).append(("bore", member, leg, 0.0))
                    continue
                depth = bite(leg, footprint, normal)
                if depth > TOLERANCE_M:
                    hits.setdefault(leg.tag, []).append((how, member, leg, depth))
        out.extend(_grade(tag, floor, found) for tag, found in hits.items())
        if not hits:
            out.append(_pass(_CID, f"{floor.tag}: no run's envelope meets any of its "
                                   f"{len(solids)} solid member(s)", (floor.tag,)))
    return out


def _grade(tag: str, floor, found: list[tuple]) -> Finding:
    occupied = [hit for hit in found if hit[0] != "bore"]
    if occupied:
        how, member, leg, depth = max(occupied, key=lambda hit: hit[3])
        keys = sorted({hit[1].child_key for hit in occupied})
        verb = ("stands through" if how == "riser" else "runs along inside")
        where = at(leg.a) if how == "riser" else f"{at(leg.a)}-{at(leg.b)}"
        return _fail(
            _CID,
            f"{leg.kind} {tag} {verb} {floor.tag}'s {member.category} {member.child_key} "
            f"({member.profile}) at {where}: its {2 * leg.radius_m / M_PER_IN:.2f}\" "
            f"envelope reaches {depth / M_PER_IN:.3f}\" into the member over its depth — not "
            f"a hole anyone drills but the member's removal. Members met: "
            f"{', '.join(keys)}",
            (tag, floor.tag),
            fix=("move the run clear of the member's faces, or re-frame the member (and any "
                 "opening it trims) around the run; a vertical hole through a floor member is "
                 "never on a chart"))
    verdicts = [(member, leg, _bore(member, 2 * leg.radius_m / M_PER_IN))
                for _how, member, leg, _d in found]
    bad = [v for v in verdicts if v[2].ok is False]
    unsure = [v for v in verdicts if v[2].ok is None]
    member, leg, verdict = (bad or unsure or verdicts)[0]
    where = (f"{leg.kind} {tag} crosses {floor.tag}'s {member.category} {member.child_key} "
             f"at {at(leg.a)}-{at(leg.b)}")
    if bad:
        return _fail(_CID, f"{where}: {verdict.basis}", (tag, floor.tag),
                     fix=verdict.remedy or "take the leg under or around the member")
    if unsure:
        return _unknown(_CID, f"{where}: {verdict.basis}", (tag, floor.tag),
                        fix=verdict.remedy)
    return _pass(_CID, f"{where}: {verdict.basis}", (tag, floor.tag))
