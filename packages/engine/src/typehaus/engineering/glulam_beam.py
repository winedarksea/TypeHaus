"""A structural glulam carrying a deck — ``deck_beam/<Beam tag>``.

IRC Table R507.5(1) publishes spans for **sawn lumber**, in nominal plies: 2x8 through 2x12,
one to three of them. There is no row for a glulam, an LVL or an LSL and there never will
be — an engineered member is sold against its own published design values, not against a
species table — which is why ``structural.deck_beam_span`` hands one here rather than
reporting a gap in the table (decision #65).

**What governs, and what does not.** These are catlin's three balcony beams: 3-1/2" x
11-7/8" preservative-treated southern yellow pine, 24F-V5M1/SP, spanning 8'-8" between the
corner columns at 50 psf over a 10'-0" joist span. Bending governs at about a third of
capacity; shear and bearing are not close, and deflection is nowhere near L/360. The member
is that deep because the owner wanted planter margin, not because a span demanded it, and
the record says so rather than implying the depth was solved for.

**Wet service.** Every one of these stands in weather with no enclosure above it, so
AWC NDS Table 5.3.1's wet-service factors apply and are applied: ``C_M`` 0.80 on Fb, 0.875
on Fv, 0.53 on Fc-perp and 0.833 on E. A glulam design value quoted dry and used outdoors
is the single most common way to overstate one of these by a quarter.

**Oracle.** ``houses/catlin/notes/balcony_moment_columns.md`` §5, hand-worked in a separate
pass; ``tests/test_pier_calcs.py`` reproduces it.
"""

from __future__ import annotations

import math
import re
from typing import Any

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys

KIND = "deck_beam"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "1"
BASIS = "IRC R507.5 (no row); AWC NDS 2018 Ch. 3 and 5, ANSI 117 combination values"

#: IRC R507.1 / Table R301.5 — 40 psf live plus 10 psf dead. The same numbers
#: ``checks/structural/deck_tables.py`` publishes, restated because ``engineering`` may not
#: import ``checks``.
DECK_LIVE_LOAD_PSF = 40.0
DECK_DEAD_LOAD_PSF = 10.0
DECK_TOTAL_LOAD_PSF = DECK_LIVE_LOAD_PSF + DECK_DEAD_LOAD_PSF

#: ANSI A190.1 / APA EWS combination 24F-V5M1/SP (southern pine, balanced layup), the
#: combination Anthony Power Preserved and Boise Cascade both stock in a treated beam.
#: Reference design values, DRY, before any adjustment.
GLULAM_FB_PSI = 2_400.0        # bending, tension zone stressed in tension
GLULAM_FV_PSI = 300.0          # shear parallel to grain (SP layups; DF layups are 265)
GLULAM_FC_PERP_PSI = 740.0     # compression perpendicular to grain
GLULAM_E_PSI = 1_800_000.0     # modulus of elasticity

#: AWC NDS 2018 Table 5.3.1 wet-service factors for structural glued laminated timber —
#: applied whenever the member stands in weather, which every deck beam here does. These
#: are the whole reason a glulam quoted off a supplier's dry table is 25% optimistic
#: outdoors.
WET_FB = 0.80
WET_FV = 0.875
WET_FC_PERP = 0.53
WET_E = 0.833

#: AWC NDS Table 2.3.2 — the load duration factor for occupancy live load on a floor or
#: deck. Not 1.15 (snow) and emphatically not 1.6 (wind): a deck's governing case is people.
LOAD_DURATION_FACTOR = 1.0

#: IRC Table R301.7 — the deflection limit for a floor member under live load.
LIVE_DEFLECTION_DENOMINATOR = 360.0

#: IRC R507.6 — the minimum bearing a deck beam takes on wood or metal; on concrete or
#: masonry it is 3". These beams land on cast columns, so 3" is the figure.
BEARING_LENGTH_IN = 3.0

_M_PER_FT = 0.3048


#: The sections IRC Table R507.5(1) actually publishes: 2x8, 2x10 and 2x12, one to three
#: plies, spelled the way ``Beam.size`` spells them ("2x10", "2-2x10", "3-2x12"). A section
#: outside this set has no row and is this module's business.
#:
#: **Restated rather than imported.** ``engineering`` is a leaf package and may not import
#: ``checks`` (see ``engineering/__init__``), so the scoping predicate is written out here
#: the way ``pier_basis``'s tributary rule is. If ``checks/structural/deck_tables.py`` ever
#: publishes a wider table, this set moves with it —
#: ``tests/test_pier_calcs.py`` asserts the two agree on the landed house, which is what
#: keeps them honest.
_SAWN_TABLE_SECTION = re.compile(r"^(?:[123]-)?2x(?:8|10|12)$")


def _beams(ctx: EngineeringContext) -> list[tuple[Any, Any, float, float]]:
    """``(deck, beam, clear span ft, tributary joist span ft)`` for every off-table deck beam.

    Scoped exactly as ``checks/structural/deck.py::deck_beam_span``'s engineered branch is:
    a beam named by a ``service="deck"`` FloorSystem's ``joists.bearing_refs`` whose section
    has no row in IRC Table R507.5(1). A beam the table DOES publish is graded there,
    prescriptively, and minting a second record for it would be two authorities on one span.
    """
    from typehaus.model.floors import FloorSystem
    from typehaus.model.structure import Beam

    out: list[tuple[Any, Any, float, float]] = []
    for deck in sorted((e for e in ctx.plan.all_elements()
                        if isinstance(e, FloorSystem) and e.service == "deck"),
                       key=lambda d: d.tag):
        joist_span = _joist_span_ft(ctx, deck)
        if joist_span is None:
            continue
        for ref in sorted(deck.joists.bearing_refs or ()):
            beam = ctx.plan.by_tag(ref)
            if not isinstance(beam, Beam):
                continue
            if _SAWN_TABLE_SECTION.match(beam.size or ""):
                continue
            span = _beam_span_ft(ctx, beam)
            if span is None:
                continue
            out.append((deck, beam, span, joist_span))
    return out


def _joist_span_ft(ctx: EngineeringContext, deck: Any) -> float | None:
    """The deck's joist SPAN, from the resolved joist members — bearing line to bearing line.

    A joist's drawn length includes its cantilevers and the span is what it bears over, so
    the overhang comes back off the two outer bays. ``resolve/floors.py`` adds it to those
    bays only, one end each, so a member is carrying a cantilever exactly when one of its
    tips sits on the joist field's outer extent.

    A restatement of ``checks/structural/deck.py::_Deck.joist_span_ft``, for the import rule
    above and on the same terms ``pier_basis`` states its tributary rule: if one moves, move
    the other.
    """
    resolved = next((f for f in ctx.model.floors if f.tag == deck.tag), None)
    if resolved is None:
        return None
    joists = [m for m in resolved.members if m.category == "joist"]
    if not joists:
        return None
    axis = 0 if (deck.joists.direction or "x") == "x" else 1
    spec = deck.joists
    base = spec.cantilever.meters if spec.cantilever is not None else 0.0
    start_ft = (spec.cantilever_start.meters
                if spec.cantilever_start is not None else base) / _M_PER_FT
    end_ft = (spec.cantilever_end.meters
              if spec.cantilever_end is not None else base) / _M_PER_FT

    ends = [sorted((m.p0[axis], m.p1[axis])) for m in joists]
    low = min(a for a, _ in ends)
    high = max(b for _, b in ends)
    spans = []
    for (a, b), member in zip(ends, joists, strict=True):
        span_ft = member.length_m / _M_PER_FT
        if abs(a - low) < 1e-6:
            span_ft -= start_ft
        if abs(b - high) < 1e-6:
            span_ft -= end_ft
        spans.append(span_ft)
    return max(spans)


def _beam_span_ft(ctx: EngineeringContext, beam: Any) -> float | None:
    """The longest clear span between the supports this beam names.

    A beam bearing on two posts spans between them; one bearing on three spans the widest
    gap. Cantilevers past the end supports are NOT span — R507.5.1 bounds an overhang
    separately — so the walk is over the bearing stations only, exactly as
    ``checks/structural/deck.py::_beam_span_ft`` does it.
    """
    stations: list[tuple[float, float]] = []
    for ref in beam.bearing_refs or ():
        element = ctx.plan.by_tag(ref)
        position = getattr(element, "position", None)
        if position is not None:
            stations.append(position.xy_m)
    if len(stations) < 2:
        return None
    stations.sort()
    return max(math.dist(a, b) for a, b in zip(stations, stations[1:], strict=False)) \
        / _M_PER_FT


def _section(beam: Any) -> tuple[float, float] | None:
    """``(width in, depth in)`` of the beam's true section."""
    from typehaus.resolve.framing.profiles import cross_section

    try:
        profile = cross_section(beam.size)
    except (KeyError, ValueError):
        return None
    return (float(profile.width_m) / 0.0254, float(profile.depth_m) / 0.0254)


@keys(KIND)
def enumerate_beams(ctx: EngineeringContext) -> list[str]:
    return [beam.tag for _deck, beam, _span, _joist in _beams(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(deck, beam, span, joist)
            for deck, beam, span, joist in _beams(ctx)]


def _volume_factor(width_in: float, depth_in: float, span_ft: float) -> float:
    """AWC NDS 2018 §5.3.6 ``C_V`` for a southern pine layup (x = 20).

    ``C_V = (21/L)^(1/x) (12/d)^(1/x) (5.125/b)^(1/x)``, capped at 1.0. It is the size effect
    that makes a deep glulam weaker per square inch than a shallow one, and it is the factor
    most often left out of a hand check of one of these. ``C_V`` and the beam stability
    factor ``C_L`` are NOT cumulative — §5.3.6 says the LESSER applies — and on a beam whose
    compression edge is held by a joist field every 16", ``C_L`` is 1.0, so ``C_V`` governs.
    """
    exponent = 1.0 / 20.0
    factor = ((21.0 / span_ft) ** exponent * (12.0 / depth_in) ** exponent
              * (5.125 / width_in) ** exponent)
    return float(min(factor, 1.0))


def _one(deck: Any, beam: Any, span_ft: float, joist_span_ft: float) -> EngineeringRecord:
    section = _section(beam)
    tags = (deck.tag, beam.tag)
    if section is None:
        return EngineeringRecord(
            item_id=item_id(KIND, beam.tag), kind=KIND, key=beam.tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{beam.tag}: the section '{beam.size}' does not resolve to a profile",
            inputs=(), limit_states=(),
            missing=(f"a resolvable cross-section for {beam.tag}. `Beam.size` is "
                     f"'{beam.size}'; write a true section like '3.5x11.875' rather than a "
                     f"nominal one, which resolves through LUMBER_ACTUAL to something else",),
            notes=(), element_tags=tags)

    width_in, depth_in = section
    # Half the joist span each side is this beam's strip of deck. Exact for an interior beam
    # of a regular grid and an over-count for an edge one, which is the safe direction; the
    # record prints the strip so a reviewer can disagree with it.
    tributary_ft = joist_span_ft
    load_plf = DECK_TOTAL_LOAD_PSF * tributary_ft
    live_plf = DECK_LIVE_LOAD_PSF * tributary_ft

    moment_lb_in = load_plf * span_ft ** 2 / 8.0 * 12.0
    section_modulus = width_in * depth_in ** 2 / 6.0
    inertia = width_in * depth_in ** 3 / 12.0

    volume = _volume_factor(width_in, depth_in, span_ft)
    fb = GLULAM_FB_PSI * WET_FB * LOAD_DURATION_FACTOR * volume
    fv = GLULAM_FV_PSI * WET_FV * LOAD_DURATION_FACTOR
    fc_perp = GLULAM_FC_PERP_PSI * WET_FC_PERP
    modulus = GLULAM_E_PSI * WET_E

    bending_psi = moment_lb_in / section_modulus
    # NDS §3.4.3.1(a): the shear taken at a distance d from the support on a member with no
    # load applied within d of it. Simply supported and uniformly loaded, that is
    # w(L/2 - d), and 1.5 V / A is the rectangular-section shear stress.
    shear_lb = load_plf * (span_ft / 2.0 - depth_in / 12.0)
    shear_psi = 1.5 * max(shear_lb, 0.0) / (width_in * depth_in)
    bearing_psi = (load_plf * span_ft / 2.0) / (width_in * BEARING_LENGTH_IN)
    deflection_in = (5.0 * (live_plf / 12.0) * (span_ft * 12.0) ** 4
                     / (384.0 * modulus * inertia))
    deflection_limit_in = span_ft * 12.0 / LIVE_DEFLECTION_DENOMINATOR

    states = (
        LimitState("bending", bending_psi, fb, "psi",
                   f"AWC NDS 2018 §3.3 — Fb {GLULAM_FB_PSI:,.0f} psi (24F-V5M1/SP) x C_M "
                   f"{WET_FB:.2f} (Table 5.3.1, wet service) x C_D "
                   f"{LOAD_DURATION_FACTOR:.2f} (Table 2.3.2, occupancy live) x C_V "
                   f"{volume:.3f} (§5.3.6 volume factor, x = 20)"),
        LimitState("shear parallel to grain", shear_psi, fv, "psi",
                   f"AWC NDS 2018 §3.4.3.1(a), V taken at d from the support — Fv "
                   f"{GLULAM_FV_PSI:,.0f} psi x C_M {WET_FV:.3f}"),
        LimitState("bearing, compression perpendicular", bearing_psi, fc_perp, "psi",
                   f"AWC NDS 2018 §3.10 over IRC R507.6's {BEARING_LENGTH_IN:.0f}\" on "
                   f"concrete — Fc-perp {GLULAM_FC_PERP_PSI:,.0f} psi x C_M "
                   f"{WET_FC_PERP:.2f}"),
        LimitState("live-load deflection", deflection_in, deflection_limit_in, "in",
                   f"IRC Table R301.7 L/{LIVE_DEFLECTION_DENOMINATOR:.0f} on the "
                   f"{DECK_LIVE_LOAD_PSF:.0f} psf live load alone — E "
                   f"{GLULAM_E_PSI:,.0f} psi x C_M {WET_E:.3f}"),
    )
    over = any(not state.ok for state in states)
    worst = max(states, key=lambda s: s.demand / s.capacity if s.capacity else 0.0)

    return EngineeringRecord(
        item_id=item_id(KIND, beam.tag), kind=KIND, key=beam.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{beam.tag}: a {width_in:.3g}\" x {depth_in:.4g}\" structural glulam "
                 f"spanning {span_ft:.2f}' under {load_plf:,.0f} plf — d/c "
                 f"{bending_psi / fb:.2f} in bending, and {worst.demand / worst.capacity:.2f} "
                 f"on {worst.name}, which governs"),
        inputs=(
            Quantity("beam_width", width_in, "in", 0.0625),
            Quantity("beam_depth", depth_in, "in", 0.0625),
            Quantity("clear_span", span_ft, "ft", 0.01),
            Quantity("joist_span", joist_span_ft, "ft", 0.01),
            Quantity("uniform_load", load_plf, "plf", 1.0),
            Quantity("Fb_adjusted", fb, "psi", 1.0),
            Quantity("volume_factor", volume, "", 0.001),
            Quantity("E_adjusted", modulus, "psi", 1000.0),
        ),
        limit_states=states,
        notes=(
            f"IRC Table R507.5(1) tabulates SAWN sections in nominal plies (2x8 to 2x12, "
            f"one to three). A {beam.size} glulam has no row in it, which is why this is an "
            f"engineered item and not a gap in the table.",
            f"LOAD: {DECK_TOTAL_LOAD_PSF:.0f} psf (IRC R507.1: {DECK_LIVE_LOAD_PSF:.0f} "
            f"live + {DECK_DEAD_LOAD_PSF:.0f} dead) over a {tributary_ft:.2f}' strip = "
            f"{load_plf:,.0f} plf. The strip is the joist span this beam carries, exact for "
            f"an interior beam of a regular grid and an over-count for an edge one.",
            f"WET SERVICE IS APPLIED, and it is the difference between this record and a "
            f"supplier's span table: C_M takes Fb to {fb:,.0f} psi from "
            f"{GLULAM_FB_PSI:,.0f}, and E to {modulus:,.0f} psi. A glulam quoted dry and "
            f"built outdoors is overstated by a quarter in bending and a sixth in stiffness.",
            f"DEPTH IS NOT SPAN-DRIVEN HERE. At d/c {bending_psi / fb:.2f} in bending and "
            f"{deflection_in / deflection_limit_in:.2f} on deflection this section is not "
            f"working hard. It is deep because the owner wanted margin for planters, which "
            f"is a decision rather than a calculation — see the note.",
            "SCREENING: no lateral-torsional buckling check (C_L is 1.0 with the compression "
            "edge held by a joist field at 16\" o.c., and §5.3.6 takes the lesser of C_L and "
            "C_V, so C_V governs and is applied); no notch, no connection, no cantilever "
            "and no vibration criterion. A stamped design is what closes those.",
        ),
        element_tags=tags)
