"""Soffit ladder rungs deflect less than L/360 under the ceiling they carry.

The generator (``resolve/framing/soffit.py``) will lay a rung across a box of any width.
It has no bearer concept and no span limit, so a soffit that grew wider — SF-S-HP1 went
from a 35" hall box to a 77" bulkhead when the air handler moved into it — silently kept
its 2x2 rungs at 16" o.c. across 72 3/4". Nothing objected, because nothing was asked.

**What this grades, and what it deliberately does not.** Only the rungs: they are the
members that span, and they are what the underside gypsum hangs on. The rails are plates
screwed to the deck above and carry nothing between supports. The rung set is read
straight off ``soffit.members`` filtered on :data:`SOFFIT_RUNG_KEY_PREFIX`, and the span
is the member's own ``length_m`` — so the check cannot drift from what the generator
actually built. The z-extent tells it whether the stick is laid flat (the generator's
convention, and the right one: a flat rung is a nailer) or on edge.

Deflection only. Bending and shear on a 5 psf ceiling over a 6-foot 2x2 are nowhere near
governing, and stating a stress ratio for them would dress up an arithmetic identity as an
analysis. δ = 5wL⁴/384EI, simply supported, uniform load — a rung is a simple span between
two rails and nothing continuous crosses it.

A soffit with no framing gets **no finding at all**, not UNKNOWN: it is drawn but not
built, there is no lumber to grade, and ``mep.duct_soffit_occupancy`` already reports the
missing ``FramingSpec`` once. Reporting it twice would put a second UNKNOWN into a house
held to none.
"""

from __future__ import annotations

from typehaus.checks._authoring import not_applicable as _not_applicable
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.soffit import (
    SOFFIT_HEADER_KEY_PREFIX,
    SOFFIT_RUNG_KEY_PREFIX,
)
from typehaus.resolve.framing.tables import member_actual
from typehaus.resolve.model import FramedMember

_CHECK_ID = "structural.soffit_rung_span"
_OPENING_CHECK_ID = "structural.soffit_opening"

# SPF No.2 modulus of elasticity, NDS Supplement Table 4A. The same 1.4e6 psi the deck and
# joist tiers use; a soffit rung is ordinary dimension lumber and there is no reason for it
# to be graded against a different species than the joists it hangs from.
_E_PSI = 1_400_000.0

# Ceiling dead load, psf. 5/8" gypsum on the soffit's underside and both its returns, plus
# the lumber itself and a light fixture allowance. There is NO LIVE LOAD term: nothing
# walks on a soffit, nothing is stored in one, and IRC Table R301.5 has no line for the
# underside of a bulkhead. Loading one anyway would be inventing a load case to be
# conservative about, which is not the same thing as being conservative.
_CEILING_DEAD_LOAD_PSF = 5.0

# L/360. IRC Table R301.7's limit for a ceiling with brittle finishes, which is exactly
# what a gypsum-lined soffit is — the failure mode being designed against is a cracked
# joint at the box's underside, not a collapse.
_DEFLECTION_DENOMINATOR = 360.0

# No span table publishes a 2x2 ceiling rung: IRC Table R802.5.1 starts at 2x4 and assumes
# an attic. So the span limit here is computed rather than looked up, and the constants
# above are the whole of the input.


def _deflection_in(span_in: float, i_in4: float, tributary_in: float) -> float:
    """δ = 5wL⁴/384EI, in inches, for a simply supported uniformly loaded rung."""
    w = _CEILING_DEAD_LOAD_PSF * (tributary_in / 12.0) / 12.0  # lb per inch of run
    return 5.0 * w * span_in ** 4 / (384.0 * _E_PSI * i_in4)


def _moment_of_inertia_in4(profile: str, laid_flat: bool) -> float:
    """I about the bending axis, from the dressed section and how the stick lies.

    Laid flat — the generator's convention — the rung bends about its WEAK axis, and that
    is why upsizing a flat rung buys so little: b and h swap, so I grows with the depth
    linearly instead of cubically.
    """
    thickness_in, depth_in = member_actual(profile)
    if laid_flat:
        b, h = depth_in, thickness_in
    else:
        b, h = thickness_in, depth_in
    return b * h ** 3 / 12.0


@check(Tier.STRUCTURAL, _CHECK_ID)
def soffit_rung_span(ctx: CheckContext) -> list[Finding]:
    """Every generated soffit rung, graded on deflection against L/360."""
    framed = [soffit for soffit in ctx.model.soffits if soffit.members]
    if not framed:
        # Earned N/A: the model was read and no soffit in it carries framing. A soffit
        # authored without a FramingSpec is drawn, not built; there is no rung to grade
        # and no input missing.
        return [_not_applicable(_CHECK_ID, "no soffit in the model resolved any ladder "
                                "framing, so there is no rung to grade")]
    out: list[Finding] = []
    for soffit in framed:
        rungs = [m for m in soffit.members
                 if m.child_key.startswith(SOFFIT_RUNG_KEY_PREFIX)]
        if not rungs:
            # A box short enough that every station is an end station is closed by end
            # blocking alone. Blocking between two rails 16" apart is not a span.
            continue
        worst = max(rungs, key=lambda m: m.length_m)
        span_in = worst.length_m / M_PER_IN
        thickness_in, depth_in = member_actual(worst.profile)
        z_extent_in = (worst.z1_m - worst.z0_m) / M_PER_IN
        # >= so a square section (a 2x2, where thickness == depth) reads as FLAT, which is
        # what the generator lays and what the message should say. I is the same either way.
        laid_flat = abs(z_extent_in - depth_in) >= abs(z_extent_in - thickness_in)
        i_in4 = _moment_of_inertia_in4(worst.profile, laid_flat)
        tributary_in = _tributary_in(rungs, worst)
        delta_in = _deflection_in(span_in, i_in4, tributary_in)
        ratio = span_in / delta_in if delta_in > 0 else float("inf")
        lie = "flat" if laid_flat else "on edge"
        detail = (f"soffit {soffit.tag}: {len(rungs)} {worst.profile} rungs laid {lie}, "
                  f"longest {span_in:.2f}\" at {tributary_in:.1f}\" tributary — "
                  f"I {i_in4:.3f} in^4, {delta_in:.3f}\" of deflection under "
                  f"{_CEILING_DEAD_LOAD_PSF:.0f} psf of ceiling dead load, L/{ratio:.0f}")
        if ratio >= _DEFLECTION_DENOMINATOR:
            out.append(_pass(_CHECK_ID, detail + f" against L/{_DEFLECTION_DENOMINATOR:.0f}",
                             (soffit.tag,)))
        else:
            out.append(_advisory(
                _CHECK_ID,
                detail + f" — short of IRC R301.7's L/{_DEFLECTION_DENOMINATOR:.0f} for a "
                "ceiling with brittle finishes. Deepen the rung with FramingSpec.member "
                "while holding the rails at FramingSpec.plate_member, so the cavity width "
                "does not move with it",
                (soffit.tag,), Result.FAIL))
    return out


def _tributary_in(rungs: list[FramedMember], worst: FramedMember) -> float:
    """The worst rung's share of the ceiling, in inches of run.

    Derived from the actual station spacing rather than read off ``FramingSpec.spacing``,
    for the same reason the span is: the generator lays its stations on the module grid and
    drops the two ends, so the authored spacing is an input to that, not a description of
    what got built. One rung in the whole box carries the box.
    """
    if len(rungs) < 2:
        return max((m.length_m for m in rungs), default=0.0) / M_PER_IN
    axis = 0 if abs(worst.p1[0] - worst.p0[0]) < abs(worst.p1[1] - worst.p0[1]) else 1
    stations = sorted(m.p0[axis] for m in rungs)
    gaps = [(b - a) / M_PER_IN for a, b in zip(stations, stations[1:], strict=False)]
    return max(gaps) if gaps else 0.0


# --- framed openings -------------------------------------------------------------------
#
# A hatch through a soffit is not a rung problem and it is not a duct problem. It is the
# one place in a ladder where a member is deliberately cut, and the member that replaces
# it runs the OTHER way — along the box, between the two stations bounding the hole. That
# header is what the panel's frame screws to and what the cut rung stubs bear on, and
# nothing graded it until openings became authorable.
#
# What it carries, and why the number comes out so large on a small hatch: the stubs left
# either side of the hole are short, so their reactions are ounces, and the panel itself is
# a piece of ceiling. The check exists for the case that is NOT small — head off three
# rungs for a 4-foot hatch and the header spans 64" of 2x4 laid flat, which is a real
# deflection question and a cracked joint at the panel's edge.


def _point_load_deflection_in(span_in: float, i_in4: float, load_lb: float) -> float:
    """δ = PL³/48EI — every point load taken at MIDSPAN, wherever it really lands.

    Conservative by construction: a load at midspan deflects a simple beam more than the
    same load anywhere else on it. A hatch is headed off between two stations and its stubs
    sit wherever the module put them, so placing each reaction exactly costs a station map
    and buys a number that is smaller than this one.
    """
    return load_lb * span_in ** 3 / (48.0 * _E_PSI * i_in4)


@check(Tier.STRUCTURAL, _OPENING_CHECK_ID)
def soffit_opening(ctx: CheckContext) -> list[Finding]:
    """Every framed hatch through a soffit ladder, graded on its header's deflection."""
    openings = [soffit for soffit in ctx.model.soffits if soffit.openings]
    if not openings:
        # Earned N/A, not silence: the model was read and no soffit authors an opening.
        # A soffit with no hatch is the norm, and "there is nothing to head off" is a fact
        # about this building rather than a missing input.
        return [_not_applicable(_OPENING_CHECK_ID, "no soffit in the model authors a "
                                "framed opening, so there is no header to grade")]
    out: list[Finding] = []
    for soffit in openings:
        headers = [m for m in soffit.members
                   if m.child_key.startswith(SOFFIT_HEADER_KEY_PREFIX)]
        rungs = [m for m in soffit.members
                 if m.child_key.startswith(SOFFIT_RUNG_KEY_PREFIX)]
        for tag, ring in soffit.openings:
            xs = [x for x, _ in ring]
            ys = [y for _, y in ring]
            width_in = (max(xs) - min(xs)) / M_PER_IN
            depth_in = (max(ys) - min(ys)) / M_PER_IN
            mine = [m for m in headers
                    if m.child_key.startswith(f"{SOFFIT_HEADER_KEY_PREFIX}{tag}-")]
            if not mine:
                # A hole reaching both rails is framed by the rails themselves. Legal, and
                # worth saying out loud rather than passing in silence: it means the hatch
                # is the full clear width of the box.
                out.append(_pass(
                    _OPENING_CHECK_ID,
                    f"soffit {soffit.tag} opening {tag}: {width_in:.1f}\" x "
                    f"{depth_in:.1f}\" clear, full width of the ladder — the rails carry "
                    "its long edges and no header is framed",
                    (soffit.tag, tag)))
                continue
            worst = max(mine, key=lambda m: m.length_m)
            span_in = worst.length_m / M_PER_IN
            thickness_in, profile_depth_in = member_actual(worst.profile)
            z_extent_in = (worst.z1_m - worst.z0_m) / M_PER_IN
            laid_flat = (abs(z_extent_in - profile_depth_in)
                         >= abs(z_extent_in - thickness_in))
            i_in4 = _moment_of_inertia_in4(worst.profile, laid_flat)
            # A quarter of the hatch: the panel's board bears on four edges, two of them
            # these headers and two of them the rungs that bound the hole.
            panel_tributary_in = min(width_in, depth_in) / 4.0
            delta_in = _deflection_in(span_in, i_in4, panel_tributary_in)
            # Plus every rung stub that now ends on this header rather than running through.
            stubs = [m for m in rungs if _bears_on(m, worst)]
            stub_load_lb = sum(
                _CEILING_DEAD_LOAD_PSF * (16.0 / 12.0) / 12.0 * (m.length_m / M_PER_IN) / 2.0
                for m in stubs)
            delta_in += _point_load_deflection_in(span_in, i_in4, stub_load_lb)
            ratio = span_in / delta_in if delta_in > 0 else float("inf")
            detail = (f"soffit {soffit.tag} opening {tag}: {width_in:.1f}\" x "
                      f"{depth_in:.1f}\" clear, headed off with {len(mine)} "
                      f"{worst.profile} header(s), longest {span_in:.2f}\" carrying "
                      f"{len(stubs)} cut rung stub(s) — {delta_in:.4f}\" of deflection, "
                      f"L/{ratio:.0f}")
            if ratio >= _DEFLECTION_DENOMINATOR:
                out.append(_pass(
                    _OPENING_CHECK_ID,
                    detail + f" against L/{_DEFLECTION_DENOMINATOR:.0f}",
                    (soffit.tag, tag)))
            else:
                out.append(_advisory(
                    _OPENING_CHECK_ID,
                    detail + f" — short of IRC R301.7's L/{_DEFLECTION_DENOMINATOR:.0f} "
                    "for a ceiling with brittle finishes. Shorten the opening so it heads "
                    "off fewer stations, or deepen the rung stock with FramingSpec.member",
                    (soffit.tag, tag), Result.FAIL))
    return out


def _bears_on(rung: FramedMember, header: FramedMember) -> bool:
    """Whether ``rung``'s cut end lands on ``header``.

    Geometric, not by key: the generator names a stub after its station and a header after
    its opening, so pairing them by name would be a second encoding of a relationship the
    coordinates already state.
    """
    header_axis = 0 if abs(header.p1[0] - header.p0[0]) > abs(header.p1[1] - header.p0[1]) else 1
    across_axis = 1 - header_axis
    line = header.p0[across_axis]
    lo, hi = sorted((header.p0[header_axis], header.p1[header_axis]))
    for end in (rung.p0, rung.p1):
        if (abs(end[across_axis] - line) <= 1e-6
                and lo - 1e-6 <= end[header_axis] <= hi + 1e-6):
            return True
    return False
