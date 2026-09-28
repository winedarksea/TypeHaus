"""Is a stair's raked carriage within a span somebody publishes (→ 12 §checks/structural)?

The IRC sizes no interior stringer, so the prescriptive stand-in for a SAWN cut stringer is
AWC DCA 6 Fig. 28: 6'-0" of horizontal span and a 5" throat. Nothing sawn goes past that
prescriptively. An engineered stringer (LSL, LVL) is graded against the manufacturer's own
stringer table, authored on the flight as ``Stair.published_stringer_span`` and read through
``published.graded_against_published``, so a retype, a lost stringer or a deeper notch
drifts the row to UNKNOWN rather than passing on a stale quotation.

A stringer ledgered full length to a wall (``resolve/stairs/bearing.py``) does not span;
only a flight whose every stringer is carried that way is exempt. The hand check is
``houses/catlin/notes/stair_stringer_basis.md``.
"""

from __future__ import annotations

import math
import re

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.published import graded_against_published
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedStair

CHECK_ID = "structural.stair_stringer"
TREAD_SPAN_ID = "structural.stair_tread_span"

_DCA6 = "AWC DCA 6-2015 Fig. 28"
_SAWN_MAX_RUN_IN = 72.0
_SAWN_MIN_THROAT_IN = 5.0
# IRC Table R301.5 stairs; dead = 1 1/2" oak treads, the carriage and a gypsum soffit.
_LIVE_PSF = 40.0
_DEAD_PSF = 12.0
# IRC Table R301.7 floors: a stair is walked like one.
_DEFLECTION = "L/360"
# The clear span most tread makers publish for a 1 1/2" board; practice, not code.
_TREAD_CLEAR_SPAN_IN = 36.0
_SAWN = re.compile(r"^(?:\d+-)?2x\d+$")
_CARRIED = ("framed-wall-ledger:", "concrete-wall-hanger:")


def _flights(stair: ResolvedStair) -> dict[str, list[FramedMember]]:
    """Stringers keyed by flight: ``stringer-lower-0`` -> ``stringer-lower``."""
    out: dict[str, list[FramedMember]] = {}
    for member in stair.members:
        if member.category == "stringer":
            out.setdefault(member.child_key.rsplit("-", 1)[0], []).append(member)
    return out


def _run_in(member: FramedMember) -> float:
    return math.hypot(member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]) / M_PER_IN


def _carried(stair: ResolvedStair, member: FramedMember) -> bool:
    """True when a wall carries ``member`` over its whole run."""
    connection = member.connection or ""
    if connection.startswith(_CARRIED[1]):
        return True
    if not connection.startswith(_CARRIED[0]):
        return False
    key = f"ledger-{connection.split(':', 1)[1]}-{member.child_key}"
    ledger = next((m for m in stair.members if m.child_key == key), None)
    return ledger is not None and ledger.length_m / M_PER_IN >= _run_in(member) - 0.5


def _throat_in(stair: ResolvedStair, profile: str) -> float:
    riser = stair.riser_height_m / M_PER_IN
    going = (stair.going_depth_m or stair.tread_depth_m) / M_PER_IN
    return cross_section(profile).depth_m / M_PER_IN - riser * going / math.hypot(riser, going)


def _cross(member: FramedMember) -> float:
    """A stringer's station across its flight."""
    return member.p0[1] if abs(member.p1[0] - member.p0[0]) > 1e-6 else member.p0[0]


@check(Tier.STRUCTURAL, CHECK_ID)
def stair_stringer(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        authored = ctx.plan.by_tag(stair.tag)
        for flight, members in sorted(_flights(stair).items()):
            out.append(_grade(stair, authored, flight, members))
    if not out:
        return [_advisory(CHECK_ID, "N/A — no flight in this building has a raked stringer "
                          "carriage", (), Result.NOT_APPLICABLE)]
    return out


def _grade(stair: ResolvedStair, authored, flight: str,
           members: list[FramedMember]) -> Finding:
    subject = f"{stair.tag} {flight}"
    tags = (stair.tag,)
    free = [m for m in members if not _carried(stair, m)]
    if not free:
        return _advisory(CHECK_ID, f"{subject}: every stringer is ledgered full length to a "
                         "wall, so none spans", tags, Result.PASS)
    profile = free[0].profile
    run = max(_run_in(m) for m in free)
    throat = _throat_in(stair, profile)
    if not _SAWN.match(profile):
        spacing = getattr(authored, "stringer_spacing", None)
        width = getattr(authored, "width", None)
        return graded_against_published(
            CHECK_ID, f"{subject} ({len(members)} x {profile})", tags, run / 12.0,
            getattr(authored, "published_stringer_span", None), profile,
            spacing_in=spacing.inches if spacing is not None else None,
            carried_span_ft=width.feet if width is not None else None,
            demand_psf=_LIVE_PSF + _DEAD_PSF, deflection_limit=_DEFLECTION,
            throat_in=throat,
            fix="author Stair.published_stringer_span from the stringer maker's table")
    faults = []
    if run > _SAWN_MAX_RUN_IN + 1e-6:
        faults.append(f"spans {run / 12:.2f}' horizontally, past 6'-0\"")
    if throat < _SAWN_MIN_THROAT_IN - 1e-6:
        faults.append(f"is notched to a {throat:.2f}\" throat, under 5\"")
    if faults:
        return _advisory(
            CHECK_ID, f"{subject}: a sawn {profile} " + " and ".join(faults), tags,
            Result.FAIL, code=_DCA6,
            fix_hint="carry the free stringer on a wall or post, or use an engineered "
                     "stringer (Stair.stringer_profile) graded against its maker's table")
    return _advisory(CHECK_ID, f"{subject}: sawn {profile} spans {run / 12:.2f}' <= 6'-0\" "
                     f"with a {throat:.2f}\" throat >= 5\"", tags, Result.PASS, code=_DCA6)


@check(Tier.STRUCTURAL, TREAD_SPAN_ID)
def stair_tread_span(ctx: CheckContext) -> list[Finding]:
    """The widest clear span a tread board makes between adjacent stringers. Practice only:
    the IRC grades the tread's load (R301.5), not its support spacing."""
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        for flight, members in sorted(_flights(stair).items()):
            stations = sorted(_cross(m) for m in members)
            ply = cross_section(members[0].profile).width_m
            gaps = [(b - a - ply) / M_PER_IN for a, b in zip(stations, stations[1:], strict=False)]
            if not gaps:
                continue
            clear = max(gaps)
            subject = f"{stair.tag} {flight}: treads span {clear:.1f}\" clear between stringers"
            if clear > _TREAD_CLEAR_SPAN_IN + 1e-6:
                out.append(_advisory(
                    TREAD_SPAN_ID, f"ADVISORY — {subject}, past the "
                    f"{_TREAD_CLEAR_SPAN_IN:g}\" most tread makers publish", (stair.tag,),
                    Result.PASS, fix_hint="add a stringer: Stair.stringer_spacing"))
            else:
                out.append(_advisory(TREAD_SPAN_ID, subject, (stair.tag,), Result.PASS))
    return out


__all__ = ["CHECK_ID", "TREAD_SPAN_ID", "stair_stringer", "stair_tread_span"]
