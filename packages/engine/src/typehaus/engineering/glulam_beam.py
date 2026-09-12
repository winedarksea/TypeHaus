"""The NDS pass on a structural glulam carrying a deck.

**Not an engineering item, since 2026-09-11.** It was one: IRC Table R507.5(1) publishes
spans for sawn lumber in nominal plies and has no row for a glulam, so the beam was
delegated to an engineered design. What that reasoning missed is that the *supplier*
publishes a table — Anthony/Canfor's Power Preserved Glulam Deck Guide tabulates exactly
this beam against exactly this joist span — and reading a published table is a
prescriptive act, not something a seal adds to. The beam is now graded against that row by
``structural.deck_beam_span``, and this module supplies the NDS cross-check beside it.

**The cross-check earns its place**: the deck guide's values are DRY-use, and every one of
these beams stands in weather. The wet-service arithmetic here is what says by how much,
and it runs as an advisory rather than a verdict.

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
``tests/test_pier_calcs.py`` reproduces it. It is no longer a registered ``Oracle`` because
there is no longer a registered kind for it to be the oracle of.
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering.item import LimitState

BASIS = "AWC NDS 2018 Ch. 3 and 5, ANSI 117 combination values, wet service"

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
               joist_span_ft: float) -> tuple[LimitState, ...]:
    """The four NDS limit states for one glulam deck beam, wet service applied.

    Pure arithmetic on four numbers: no model types, no findings, no records. The caller
    decides what a ratio means — ``structural.deck_beam_span`` prints these beside a
    published-table PASS as the cross-check that the table's dry-use values do not cover.
    """
    # Half the joist span each side is this beam's strip of deck. Exact for an interior beam
    # of a regular grid and an over-count for an edge one, which is the safe direction.
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

    return (
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


def describe_states(states: tuple[LimitState, ...]) -> str:
    """The four ratios and the one that governs, in one line a finding can carry."""
    worst = max(states, key=lambda s: s.demand / s.capacity if s.capacity else 0.0)
    ratios = "; ".join(f"{state.name} {state.demand / state.capacity:.2f}"
                       for state in states if state.capacity)
    return f"{ratios} — {worst.name} governs"


def section_of(beam: Any) -> tuple[float, float] | None:
    """Public spelling of ``_section``, for the check that now owns this arithmetic."""
    return _section(beam)
