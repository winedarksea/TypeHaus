"""The partition top plate's SDPW spacing, graded against the row Simpson publish.

``takeoff/partition_fasteners.py`` bills the screw that spans an interior partition's 3/4"
deflection gap and says so out loud: *a schedule, not a design*. Simpson do publish a
maximum-SPACING table for this fastener (IAPMO UES ER-192 Table 37; Fastening Systems
Technical Guide C-F-2025TECHSUP pp. 100–101) and reading it is a PRESCRIPTIVE act — a
reviewer opens the document, finds the row, and the question is closed. So this grades the
schedule's own pitch against a ``PublishedSpan`` authored on a wall, through
``checks/structural/published.py``, exactly as ``structural.slab_published_span`` does.

**It is ONE group item, keyed by the lowest partition tag**, on the ``girt_screw/W-A-N1``
precedent (``wall_panel/W-A-N1``'s, until that item became a published read): one table row governs every partition top in the house, the row is authored
once, and the check grades the WORST case of the population against it. Fifty-odd separate
findings would be fifty readings of one document.

**The guards the row cannot hold are held here, and every one is answered from the model.**
``PublishedSpan`` carries the two the machinery compares — the maximum spacing itself and
the wall height the row is indexed by — plus the load basis. The rest come out of
``houses/catlin/notes/partition_top_deflection.md`` §7.4, which is the joist maker's half
of the document, and each is answered off the resolved section rather than asserted:

* the **supporting flange** is at least 1-1/8" thick (ER-192's own gate) and the screw's
  minimum penetration lands inside it;
* the **edge distance** from a screw on the member centreline clears 5/8" (TB-206 fn [3]);
* the **end distance** and the **on-centre spacing** clear 6" (TB-206 Table 1's nearest
  published row, 16d common into the wide face of a TJI 110/210/230 flange — a conservative
  stand-in, not a citation);
* the supporting member is a **TJI flange or a floor-truss chord**, never a SIP, a web or a
  plate connector — a wall standing under one is refused by the take-off and never reaches
  a row here;
* and **no Weyerhaeuser spacing row may be cited for this fastener.** TB-206 fn [1] extends
  the nail spacings to wood screws only where the root diameter is at or under the fattest
  nail listed, 16d common at 0.162", and the SDPW19600's shank is 0.195". So Weyerhaeuser
  publish NO row for it and fn [12] hands the question back to the fastener maker. A row
  quoting them here is a drift UNKNOWN, not a PASS.

A measured shortfall — a flange too thin, an edge or end distance too short — is a FAIL: it
is a fact about the building. A guard the model cannot answer, or a row citing the wrong
document, is UNKNOWN: the row has stopped describing the building rather than damning it.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.published import graded_against_published
from typehaus.findings import Finding, Result, not_applicable
from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
from typehaus.model.elements import Wall
from typehaus.resolve.partition_fasteners import PartitionTopJoint, partition_top_joints

_CHECK_ID = "structural.partition_deflection_spacing"

#: ASCE 7-22 §4.3.2 / IBC 1607.16: the minimum lateral load an interior partition is
#: designed for, and the load Simpson's own maximum-spacing table is published at. The two
#: agreeing is why this check can answer the row's load-basis guard at all; a house that
#: ever designs a partition for more than this drifts the row, which is the point.
_PARTITION_LATERAL_PSF = 5.0

#: ER-192's gate on the member a SDPW may be driven into, in inches.
_MIN_FLANGE_IN = 1.125
#: TB-206 fn [3], recommended edge distance on a TJI 230 flange.
_MIN_EDGE_IN = 0.625
#: TB-206 Table 1, 16d common into the wide face of a TJI 110/210/230 flange: the nearest
#: published row, quoted as a conservative stand-in and never as a citation (fn [1] puts
#: this screw outside the table, fn [12] hands it back to Simpson).
_MIN_END_IN = 6.0
_MIN_PITCH_IN = 6.0

#: The screw's own minimum penetration into the supporting member, past the sleeve
#: (C-F-2025TECHSUP p. 100, the SDPW19600's 3/4"). The gate on a SOLID member, where
#: ER-192's flange rule has nothing to say.
_MIN_PENETRATION_IN = 0.75

#: Documents whose spacing rows may NOT be cited for this fastener — guard 11.
_REFUSED_SOURCES = ("weyerhaeuser", "tb-206", "tb206", "tj-4000")


@check(Tier.STRUCTURAL, _CHECK_ID)
def partition_deflection_spacing(ctx: CheckContext) -> list[Finding]:
    """The house's partition-top screw schedule, against one published spacing row."""
    rules = DEFAULT_HARDWARE_TAKEOFF_CONFIG.partition_deflection
    joints, _refusals = partition_top_joints(ctx.model, rules)
    if not joints:
        return [not_applicable(
            _CHECK_ID,
            "no wall in this building is an interior partition running the full storey "
            "height with framing over it, so no top plate here stands clear of a deck on "
            "deflection screws and there is no spacing for a table to answer")]

    key = min(joint.wall_tag for joint in joints)
    authored = ctx.plan.by_tag(key)
    row = getattr(authored, "published_span", None) if isinstance(authored, Wall) else None
    tags = (key,)
    subject = (f"the SDPW DEFLECTOR schedule at {len(joints)} partition tops "
               f"(group item, keyed on {key})")

    fail, unanswered = _hard_guards(joints)
    if fail is not None:
        return [_finding(fail, tags, Result.FAIL,
                         "the members over these partitions cannot take this fastener as "
                         "detailed — retype the deck, move the joint, or have it designed")]
    if unanswered is not None:
        return [_finding(unanswered, tags, Result.UNKNOWN,
                         "give the member a profile this engine can parse, or have the "
                         "joint designed")]

    if row is not None and _cites_a_refused_source(row.source):
        return [_finding(
            f"{subject}: the authored row cites {row.source!r}, and no Weyerhaeuser "
            "spacing row may be quoted for this fastener — TB-206 fn [1] extends its nail "
            "spacings to screws only at a root diameter of 0.162\" or less and this shank "
            "is 0.195\", so fn [12] hands the question back to the fastener maker",
            tags, Result.UNKNOWN,
            "re-author the PublishedSpan against Simpson's own ER-192 Table 37 / "
            "C-F-2025TECHSUP maximum-spacing table")]

    worst = max(joints, key=lambda joint: joint.pitch_in)
    return [graded_against_published(
        _CHECK_ID,
        f"{subject}, at its widest pitch — {worst.wall_tag}, {worst.scope}",
        tags, worst.pitch_in / 12.0, row, _model_member(joints),
        carried_span_ft=max(joint.height_in for joint in joints) / 12.0,
        demand_psf=_PARTITION_LATERAL_PSF,
        fix="author Wall.published_span on the lowest-tagged interior partition with "
            "Simpson's maximum-spacing row for the SDPW this house's top-plate condition "
            "is published at — span = the row's maximum o.c. spacing, carried_span = the "
            "wall height it is indexed by")]


def _finding(message: str, tags: tuple[str, ...], result: Result, hint: str) -> Finding:
    from typehaus.checks._authoring import structural_advisory

    return structural_advisory(_CHECK_ID, message, tags, result, fix_hint=hint)


def _cites_a_refused_source(source: str) -> bool:
    lowered = (source or "").lower()
    return any(name in lowered for name in _REFUSED_SOURCES)


def _model_member(joints: list[PartitionTopJoint]) -> str | None:
    """Every distinct supporting member these screws land in, as the model spells them.

    One string rather than one row per deck, because one table row governs the whole
    schedule: retype any deck over any partition and this string moves, which is exactly
    the drift the row's ``member`` guard is for. ``None`` where no profile parses, which
    makes ``published.py`` skip the comparison rather than invent a mismatch.
    """
    profiles = sorted({section.profile for joint in joints for section in joint.supports})
    return "; ".join(profiles) if profiles else None


def _hard_guards(joints: list[PartitionTopJoint]) -> tuple[str | None, str | None]:
    """``(fail, unknown)`` — the measured shortfalls, and the guards nothing answered.

    A shortfall is a FAIL: it is a fact about the building. A member whose profile parses
    to nothing is UNKNOWN: the guard was not checked, which is not the same as met.

    The screw goes in through the WIDE face of the flange by construction: a joist or
    rafter stands on edge, so its flange's wide face IS the soffit and a screw driven up
    through the plate can meet nothing else. That is guard 9, answered by the orientation
    rather than by a field.

    A ``rect`` section — a solid rim board, a sawn blocking course — takes the screw in the
    full depth of solid wood and has no flange to gate. It gets the edge-distance guard off
    half its plan width and nothing else; ER-192's 1-1/8" is a rule about an engineered
    flange, and reading it onto a solid member would refuse a joint nobody doubts.
    """
    for joint in joints:
        for section in joint.supports:
            if section.shape is None:
                return None, (
                    f"{joint.wall_tag}: the member over it, {section.profile!r}, resolves "
                    "no section, so its thickness, its edge distance and the screw's "
                    "penetration are all unanswered")
            if section.shape in ("i_joist", "floor_truss", "roof_truss"):
                thickness_in = section.flange_thickness_in
                edge_in = (None if section.flange_width_in is None
                           else section.flange_width_in / 2.0)
                gate_in, what = _MIN_FLANGE_IN, "flange"
            elif section.shape == "rect":
                thickness_in = section.depth_in
                edge_in = None if section.width_in is None else section.width_in / 2.0
                gate_in, what = _MIN_PENETRATION_IN, "solid section"
            else:
                return (f"{joint.wall_tag}: the member over it is {section.profile!r}, a "
                        f"{section.shape} — an SDPW is published into an I-joist flange, a "
                        "truss chord or solid wood, never a SIP, a web or a plate "
                        "connector"), None
            if thickness_in is None or edge_in is None:
                return None, (
                    f"{joint.wall_tag}: {section.profile!r} resolves no {what} thickness "
                    "or width, so the screw's penetration and its edge distance are "
                    "unanswered")
            if thickness_in + 1e-9 < gate_in:
                return (f"{joint.wall_tag}: the {section.profile} {what} is "
                        f"{thickness_in:.3g} in thick, under the {gate_in:g} in the "
                        "screw's minimum penetration needs inside it"), None
            if edge_in + 1e-9 < _MIN_EDGE_IN:
                return (f"{joint.wall_tag}: a screw on the {section.profile} centreline "
                        f"has {edge_in:.3g} in of edge distance, under TB-206 fn [3]'s "
                        f"{_MIN_EDGE_IN:g} in"), None
        if joint.pitch_in + 1e-9 < _MIN_PITCH_IN:
            return (f"{joint.wall_tag}: the schedule puts screws {joint.pitch_in:.3g} in "
                    f"apart, under the {_MIN_PITCH_IN:g} in minimum on-centre spacing of "
                    "the nearest published row"), None
        if joint.end_distance_in is not None and joint.end_distance_in + 1e-9 < _MIN_END_IN:
            return (f"{joint.wall_tag}: a screw lands {joint.end_distance_in:.3g} in from a "
                    f"member end, under the {_MIN_END_IN:g} in minimum end distance of the "
                    "nearest published row"), None
    return None, None
