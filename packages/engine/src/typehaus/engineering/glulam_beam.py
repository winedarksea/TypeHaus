"""The NDS pass on a structural glulam carrying a deck.

**An engineering item again, since 2026-09-18, and the round trip is the point.** It was
one until 2026-09-11, when it was retired on the reasoning that the *supplier* publishes a
table — Anthony/Canfor's Power Preserved Glulam Deck Guide tabulates exactly this beam
against exactly this joist span — and reading a published table is a prescriptive act, not
something a seal adds to. That reasoning is still right about the table. What it got wrong
is which member the table describes.

** THE PUBLISHED ROW IS DRY-USE AND THESE BEAMS STAND IN WEATHER. ** That was known on the
day the kind was retired — it is written into the row's own ``condition`` string, and this
module's wet-service arithmetic ran beside the PASS as an *advisory*. So the verdict came
from a row that does not cover the member, and the only calculation modelling the real
service condition was the one carrying no weight. Worse, in leaving the registered-kind
tuple it left the seal machinery entirely: no record, no fingerprint, and — the part that
would have caught it — **no oracle lint**, so nothing checked that its hand-worked note
still existed or still agreed.

``PublishedSpan.service_condition`` now makes the mismatch loud: the published read goes
UNKNOWN naming it, and this record carries the verdict.

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

**Hand-worked basis.** ``houses/catlin/notes/balcony_moment_columns.md`` §5;
``tests/test_pier_calcs.py`` reproduces it. It is a registered ``Oracle`` again, which is
what ``tests/test_calc_package.py``'s lint checks.
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by

KIND = "glulam_beam"

BASIS = "AWC NDS 2018 Ch. 3 and 5, ANSI 117 combination values, wet service"

#: Bumped whenever the arithmetic below changes.
#:
#: 1: the kind as it stood before 2026-09-11.
#: 2: re-registered 2026-09-18, with ``C_D`` a parameter rather than a frozen 1.0.
#: 3: 2026-09-22, each beam loaded with its own tributary (``_beam_tributary_ft``), not the
#:    full joist span.
BASIS_VERSION = "3"

#: IRC R507.1 / Table R301.5 — 40 psf live plus 10 psf dead, re-exported from
#: ``typehaus/loads.py``. One definition since 2026-09-18; there were three.
from typehaus.loads import (  # noqa: E402,F401  (DECK_TOTAL_LOAD_PSF is a re-export)
    DECK_DEAD_LOAD_PSF,
    DECK_LIVE_LOAD_PSF,
    DECK_TOTAL_LOAD_PSF,
)

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
#:
#: ** IT IS THE DEFAULT AND NO LONGER A CONSTANT IN THE ARITHMETIC. ** ``nds_states`` took
#: this literal, which structurally forbade a snow case: a glulam carrying a roof rather
#: than a deck is graded at 1.15 and there was no way to say so short of editing the module.
#: A frozen factor is a frozen load case wearing a constant's clothing.
LOAD_DURATION_FACTOR = 1.0
#: AWC NDS Table 2.3.2 — snow. Named so a caller grading a roof-carrying glulam has the
#: figure rather than a magic number.
SNOW_LOAD_DURATION_FACTOR = 1.15

#: IRC Table R301.7 — the deflection limit for a floor member under live load.
LIVE_DEFLECTION_DENOMINATOR = 360.0

#: IRC R507.6 — the minimum bearing a deck beam takes on wood or metal; on concrete or
#: masonry it is 3". These beams land on cast columns, so 3" is the figure.
BEARING_LENGTH_IN = 3.0

_M_PER_FT = 0.3048




def _joist_span_ft(ctx: Any, deck: Any) -> float | None:
    """The deck's joist SPAN, from the resolved joist members — bearing line to bearing line.

    A joist's drawn length includes its cantilevers and the span is what it bears over, so
    the overhang comes back off the two outer bays. ``resolve/floors.py`` adds it to those
    bays only, one end each, so a member is carrying a cantilever exactly when one of its
    tips sits on the joist field's outer extent.

    A restatement of ``checks/structural/deck.py::_Deck.joist_span_ft``, for the leaf-package
    import rule and on the same terms ``pier_basis`` states its tributary rule: if one moves,
    move the other. It stays here, and not in the check, because ``pier_basis`` and
    ``post_bearing`` both read it and neither may import ``checks``.
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


def _beam_tributary_ft(ctx: Any, deck: Any, beam: Any) -> float | None:
    """Width of deck ``beam`` carries: half of each adjacent bay, plus the joists' overhang
    on whichever side it is the outermost bearing.

    Bearing lines are the deck's ``bearing_refs`` beams, at their nodes' coordinate along
    the joist axis, and the joist field's two outer bearings (its extent less the
    cantilevers, read as :func:`_joist_span_ft` reads them). ``None`` when the beam or the
    joist field does not place.
    """
    resolved = next((f for f in ctx.model.floors if f.tag == deck.tag), None)
    joists = [m for m in resolved.members if m.category == "joist"] if resolved else []
    if not joists:
        return None
    axis = 0 if (deck.joists.direction or "x") == "x" else 1

    def line_of(element: Any) -> float | None:
        nodes = [ctx.plan.by_tag(getattr(element, name, None) or "")
                 for name in ("start_node", "end_node")]
        if any(n is None or getattr(n, "position", None) is None for n in nodes):
            return None
        return sum(n.position.xy_m[axis] for n in nodes) / 2.0

    here = line_of(beam)
    if here is None:
        return None
    spec = deck.joists
    base = spec.cantilever.meters if spec.cantilever is not None else 0.0
    start = spec.cantilever_start.meters if spec.cantilever_start is not None else base
    end = spec.cantilever_end.meters if spec.cantilever_end is not None else base
    low = min(min(m.p0[axis], m.p1[axis]) for m in joists)
    high = max(max(m.p0[axis], m.p1[axis]) for m in joists)
    lines = [low + start, high - end]
    for ref in spec.bearing_refs or ():
        element = ctx.plan.by_tag(ref)
        if element is not None and (c := line_of(element)) is not None:
            lines.append(c)
    # one line per bearing, however many ways it was found (3" is well inside a beam width)
    merged: list[float] = []
    for c in sorted(lines):
        if not merged or c - merged[-1] > 0.0762:
            merged.append(c)
    i = min(range(len(merged)), key=lambda k: abs(merged[k] - here))
    width = 0.0
    width += (merged[i] - merged[i - 1]) / 2.0 if i > 0 else start
    width += (merged[i + 1] - merged[i]) / 2.0 if i < len(merged) - 1 else end
    return width / _M_PER_FT


def _section(beam: Any) -> tuple[float, float] | None:
    """``(width in, depth in)`` of the beam's true section."""
    from typehaus.resolve.framing.profiles import cross_section

    try:
        profile = cross_section(beam.size)
    except (KeyError, ValueError):
        return None
    return (float(profile.width_m) / 0.0254, float(profile.depth_m) / 0.0254)


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


def nds_states(width_in: float, depth_in: float, span_ft: float,
               tributary_ft: float, *,
               load_duration_factor: float = LOAD_DURATION_FACTOR,
               live_psf: float = DECK_LIVE_LOAD_PSF,
               dead_psf: float = DECK_DEAD_LOAD_PSF) -> tuple[LimitState, ...]:
    """The four NDS limit states for one glulam deck beam, wet service applied.

    Pure arithmetic on four numbers: no model types, no findings, no records. ``C_D`` and
    the two load intensities are PARAMETERS with a deck's values as their defaults — a
    glulam carrying a roof is graded at snow and Table 2.3.2's 1.15, and while ``C_D`` was a
    module constant read inside this function there was no way to express that at all.
    """
    # ``tributary_ft`` is this beam's strip of deck (``_beam_tributary_ft``).
    load_plf = (live_psf + dead_psf) * tributary_ft
    live_plf = live_psf * tributary_ft

    moment_lb_in = load_plf * span_ft ** 2 / 8.0 * 12.0
    section_modulus = width_in * depth_in ** 2 / 6.0
    inertia = width_in * depth_in ** 3 / 12.0

    volume = _volume_factor(width_in, depth_in, span_ft)
    fb = GLULAM_FB_PSI * WET_FB * load_duration_factor * volume
    fv = GLULAM_FV_PSI * WET_FV * load_duration_factor
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

    return (
        LimitState("bending", bending_psi, fb, "psi",
                   f"AWC NDS 2018 §3.3 — Fb {GLULAM_FB_PSI:,.0f} psi (24F-V5M1/SP) x C_M "
                   f"{WET_FB:.2f} (Table 5.3.1, wet service) x C_D "
                   f"{load_duration_factor:.2f} (Table 2.3.2) x C_V "
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
                   f"{live_psf:.0f} psf live load alone — E "
                   f"{GLULAM_E_PSI:,.0f} psi x C_M {WET_E:.3f}"),
    )


def describe_states(states: tuple[LimitState, ...]) -> str:
    """The four ratios and the one that governs, in one line a finding can carry."""
    worst = max(states, key=lambda s: s.demand / s.capacity if s.capacity else 0.0)
    ratios = "; ".join(f"{state.name} {state.demand / state.capacity:.2f}"
                       for state in states if state.capacity)
    return f"{ratios} — {worst.name} governs"


def section_of(beam: Any) -> tuple[float, float] | None:
    """Public spelling of ``_section``, for the check that now owns this arithmetic."""
    return _section(beam)


# ---------------------------------------------------------------------------------------
# The registered kind.
# ---------------------------------------------------------------------------------------

oracled_by(
    KIND,
    Oracle(note="balcony_moment_columns.md", section="§5",
           test="tests/test_pier_calcs.py"),
)


def _glulam_deck_beams(ctx: EngineeringContext) -> dict[str, tuple[Any, Any]]:
    """``beam tag -> (beam, deck)`` for every glulam a ``service="deck"`` FloorSystem bears on.

    **Keyed on the beam's own MATERIAL, not on the IRC table falling short.** "Off the end of
    R507.5(1)" is the check's question and lives in ``checks/structural/deck_tables.py``,
    which this package may not import. The material is the fact that makes the member this
    module's business: a glulam has no nominal-ply row anywhere in the IRC, and its
    supplier's table is dry-use.
    """
    from typehaus.model.floors import FloorSystem
    from typehaus.model.structure import Beam
    from typehaus.resolve.assembly_material import assembly_structure_material

    out: dict[str, tuple[Any, Any]] = {}
    for deck in ctx.plan.all_elements():
        if not isinstance(deck, FloorSystem) or deck.service != "deck":
            continue
        for ref in deck.joists.bearing_refs or ():
            beam = ctx.plan.by_tag(ref)
            if not isinstance(beam, Beam) or beam.ledger_on:
                continue
            material = assembly_structure_material(ctx.plan, beam.assembly) or ""
            if material.startswith("glulam"):
                out.setdefault(beam.tag, (beam, deck))
    return out


@keys(KIND)
def enumerate_glulam_beams(ctx: EngineeringContext) -> list[str]:
    return sorted(_glulam_deck_beams(ctx))


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    beams = _glulam_deck_beams(ctx)
    return [_one(ctx, tag, beam, deck) for tag, (beam, deck) in sorted(beams.items())]


def _span_ft(ctx: EngineeringContext, beam: Any) -> float | None:
    start = ctx.plan.by_tag(beam.start_node or "")
    end = ctx.plan.by_tag(beam.end_node or "")
    if start is None or end is None:
        return None
    (x0, y0), (x1, y1) = start.position.xy_m, end.position.xy_m
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / _M_PER_FT


def _one(ctx: EngineeringContext, tag: str, beam: Any, deck: Any) -> EngineeringRecord:
    ident = item_id(KIND, tag)
    tags = (tag, deck.tag)
    section = _section(beam)
    span_ft = _span_ft(ctx, beam)
    joist_span_ft = _joist_span_ft(ctx, deck)
    tributary_ft = _beam_tributary_ft(ctx, deck, beam)
    missing = [name for name, value in (
        (f"a resolvable cross-section for Beam.size {beam.size!r}", section),
        ("two placed nodes to take the beam's span between", span_ft),
        (f"resolved joists on {deck.tag} to take the carried span from", joist_span_ft),
        (f"a placed bearing line for {tag} among {deck.tag}'s joists", tributary_ft),
    ) if value is None]
    if missing:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{tag}: the NDS pass on this glulam could not run",
            missing=tuple(missing), element_tags=tags)

    width_in, depth_in = section
    states = nds_states(width_in, depth_in, span_ft, tributary_ft)
    volume = _volume_factor(width_in, depth_in, span_ft)
    worst = max(states, key=lambda s: s.demand / s.capacity if s.capacity else 0.0)
    over = any(not state.ok for state in states)

    inputs = (
        Quantity("width", width_in, "in", 0.001),
        Quantity("depth", depth_in, "in", 0.001),
        Quantity("span", span_ft, "ft", 0.01),
        Quantity("tributary", tributary_ft, "ft", 0.01),
        Quantity("live_load", DECK_LIVE_LOAD_PSF, "psf", 0.1),
        Quantity("dead_load", DECK_DEAD_LOAD_PSF, "psf", 0.1),
        # ** THE REFERENCE VALUES AND EVERY ADJUSTMENT, IN THE FINGERPRINT. ** These are
        # what a seal over this beam is a statement about: re-grade it at a different layup,
        # in dry service, or at snow's C_D and the record is about a different member. The
        # lesson `retaining_wall` learned on 2026-09-18, applied at registration rather than
        # after the fact.
        Quantity("Fb", GLULAM_FB_PSI, "psi", 1.0),
        Quantity("Fv", GLULAM_FV_PSI, "psi", 1.0),
        Quantity("Fc_perp", GLULAM_FC_PERP_PSI, "psi", 1.0),
        Quantity("E", GLULAM_E_PSI, "psi", 1.0),
        Quantity("C_M_bending", WET_FB, "", 0.001),
        Quantity("C_M_shear", WET_FV, "", 0.001),
        Quantity("C_M_bearing", WET_FC_PERP, "", 0.001),
        Quantity("C_M_modulus", WET_E, "", 0.001),
        Quantity("C_D", LOAD_DURATION_FACTOR, "", 0.001),
        Quantity("C_V", volume, "", 0.001),
        Quantity("bearing_length", BEARING_LENGTH_IN, "in", 0.01),
    )
    notes = (
        f"WET SERVICE, and it is the whole reason this is an engineered item rather than a "
        f"table read. The supplier's deck-guide row that covers this beam is published "
        f"DRY-USE (AWC NDS 2018 Table 5.3.1 C_M: {WET_FB:.2f} on Fb, {WET_FV:.3f} on Fv, "
        f"{WET_FC_PERP:.2f} on Fc-perp, {WET_E:.3f} on E), and this beam stands in weather "
        f"with no enclosure above it. `structural.deck_beam_span` refuses the row on "
        f"`PublishedSpan.service_condition` and this record carries the verdict.",
        f"C_V {volume:.3f} (NDS §5.3.6, x = 20) and C_L are NOT cumulative — §5.3.6 takes "
        f"the LESSER — and the joist field holds the compression edge every 16\", so C_L is "
        f"1.0 and C_V governs. Leaving C_V out is the commonest error in a hand check here.",
        f"Tributary {tributary_ft:.2f}' of a {joist_span_ft:.2f}' joist span: half of each "
        f"adjacent bay, plus the joist overhang where this is the outermost bearing.",
        "Not graded: lateral-torsional buckling at an unsheathed stage, connection design at "
        "either end, the cantilever beyond the columns (IRC R507.5.1 grades that), and "
        "long-term creep deflection.",
        f"The member is this deep because the owner wanted planter margin, not because a "
        f"span demanded it: {worst.name} governs at "
        f"{worst.demand / worst.capacity:.2f} of capacity.",
    )
    return EngineeringRecord(
        item_id=ident, kind=KIND, key=tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{tag}: a {width_in:g}\" x {depth_in:g}\" glulam spanning "
                 f"{span_ft:.2f}' carrying {tributary_ft:.2f}' of a {joist_span_ft:.2f}' "
                 f"joist span, WET service — "
                 f"{describe_states(states)}"),
        inputs=inputs, limit_states=states, notes=notes, element_tags=tags)
