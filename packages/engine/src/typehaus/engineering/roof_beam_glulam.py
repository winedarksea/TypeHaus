"""A GLULAM roof beam, for ``roof_beam`` — split out because that module is sawn-only by rule.

A decimal ``Beam.size`` (``"5.5x11.875"``) is a glulam sold against its own design values, not
an ``N-2xM``. Graded at 24F-V4 DF, the ordered layup (Rosboro Treated X-Beam,
``BEAM_GLULAM_TREATED_DF``; treated SYP stops at 5-1/4"): ANSI/AWC NDS 2018 Supplement
Table 5A. Wet service (Table 5.3.1), snow ``C_D``
1.15 (Table 2.3.2), and the volume factor ``C_V`` with x = 10 for a Western-species layup
(§5.3.6), which is the smaller of ``C_V`` and ``C_L`` because the deck braces the top edge.

The beam is graded on its own two BEARING POSTS with whatever runs past each, by statics under
the eight load patterns ``overhang_beam.envelope`` walks — the roof's half-area spread uniformly
over the roof-bearing run, excluding unloaded decorative tails. Bearing is over the post's
own width (the cap seats the beam on the post end), at Fc-perp wet, and so is each roof truss's
bottom chord on the beam top (``truss_on_beam``).

**Oracle.** ``houses/catlin/notes/canopy_west_band.md`` §7;
``tests/test_canopy_west_band_calcs.py``.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    Step,
    item_id,
    num,
)
from typehaus.engineering.truss_on_beam import (
    beam_bearing,
    half_span_ft,
    truss_bearing_state,
    truss_seats,
)

KIND = "roof_beam"

#: The ASD combination every strength row here reads; deflection reads snow alone.
D_PLUS_S = ("D + S, unfactored (ASD), C_D 1.15 for snow", (("D", 1.0), ("S", 1.0)))
S_ALONE = ("S alone (IRC Table R301.7 limits live-load deflection)", (("S", 1.0),))

#: 24F-V4 DF, NDS Supplement Table 5A (bending about x-x, tension zone in tension).
FB_PSI = 2400.0
FV_PSI = 265.0
FC_PERP_PSI = 650.0
E_PSI = 1_800_000.0
FT_PSI = 1100.0
#: NDS Table 5.3.1 wet service.
CM_FB, CM_FV, CM_FC_PERP, CM_E, CM_FT = 0.80, 0.875, 0.53, 0.833, 0.80
CD_SNOW = 1.15
VOLUME_EXPONENT = 10.0
DEFLECTION_DENOMINATOR = 240.0
_M_PER_FT = 0.3048


def glulam_section(beam: Any) -> tuple[float, float] | None:
    """``(width in, depth in)`` for a decimal glulam size, else ``None``."""
    size = (getattr(beam, "size", "") or "").strip().lower()
    if "." not in size or "x" not in size:
        return None
    try:
        width, depth = (float(part) for part in size.split("x"))
    except ValueError:
        return None
    return (width, depth) if width > 0.0 and depth > 0.0 else None


def volume_factor(width_in: float, depth_in: float, span_ft: float) -> float:
    exponent = 1.0 / VOLUME_EXPONENT
    return min(1.0, (21.0 / span_ft) ** exponent * (12.0 / depth_in) ** exponent
               * (5.125 / width_in) ** exponent)


def _bearings(ctx: Any, beam: Any) -> tuple[float, float, float, float] | None:
    """``(a ft, back span ft, b ft, bearing width in)`` off the beam's two bearing posts."""
    from typehaus.resolve.framing.profiles import cross_section

    nodes = [ctx.plan.by_tag(beam.start_node), ctx.plan.by_tag(beam.end_node)]
    posts = [ctx.plan.by_tag(ref) for ref in beam.bearing_refs or ()]
    if any(getattr(n, "position", None) is None for n in nodes) or len(posts) != 2 \
            or any(getattr(p, "position", None) is None for p in posts):
        return None
    (x0, y0), (x1, y1) = (n.position.xy_m for n in nodes)
    length = math.hypot(x1 - x0, y1 - y0)
    if length <= 0.0:
        return None
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    stations = sorted(((p.position.xy_m[0] - x0) * ux + (p.position.xy_m[1] - y0) * uy)
                      for p in posts)
    width_in = min((cross_section(p.size).width_m or 0.0) / 0.0254 for p in posts)
    a, s, b = stations[0], stations[1] - stations[0], length - stations[1]
    if s <= 0.0 or width_in <= 0.0:
        return None
    return a / _M_PER_FT, s / _M_PER_FT, b / _M_PER_FT, width_in


def glulam(ctx: Any, roof: Any, beam: Any, tributary_ft2: float,
           length_ft: float) -> EngineeringRecord:
    from typehaus.engineering.overhang_beam import envelope
    from typehaus.engineering.roof_beam import BASIS, BASIS_VERSION, _design_load_psf

    width_in, depth_in = glulam_section(beam)  # type: ignore[misc]
    bearings = _bearings(ctx, beam)
    snow_psf, dead_psf = _design_load_psf(ctx)
    missing = [text for ok, text in (
        (bearings is not None, "two bearing posts on the beam's line (Beam.bearing_refs)"),
        (snow_psf is not None, "preferences.toml [structural] roof_beam_snow_psf"),
    ) if not ok]
    if missing:
        return EngineeringRecord(
            item_id=item_id(KIND, beam.tag), kind=KIND, key=beam.tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{beam.tag}: a glulam roof beam that cannot be graded",
            missing=tuple(missing), element_tags=(roof.tag, beam.tag))
    a_ft, s_ft, b_ft, post_in = bearings  # type: ignore[misc]
    if beam.roof_bearing_insets is not None:
        start_inset, end_inset = (value.feet for value in beam.roof_bearing_insets)
        # An unloaded tail cannot dilute the roof line load or shift it toward a post.
        # This envelope requires the loaded run to reach both bearing posts.
        if min(start_inset, end_inset) < 0 or start_inset > a_ft or end_inset > b_ft:
            return EngineeringRecord(
                item_id=item_id(KIND, beam.tag), kind=KIND, key=beam.tag,
                basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
                summary=f"{beam.tag}: roof-bearing run does not cover both posts",
                missing=("roof-bearing insets confined to the beam's tails beyond its posts",),
                element_tags=(roof.tag, beam.tag))
        a_ft -= start_inset
        b_ft -= end_inset
        length_ft -= start_inset + end_inset
    per_ft = tributary_ft2 / length_ft
    section_modulus = width_in * depth_in ** 2 / 6.0
    inertia = width_in * depth_in ** 3 / 12.0
    cv = volume_factor(width_in, depth_in, s_ft)
    fb = FB_PSI * CM_FB * CD_SNOW * cv
    fv = FV_PSI * CM_FV * CD_SNOW
    fc_perp = FC_PERP_PSI * CM_FC_PERP
    modulus = E_PSI * CM_E
    env = envelope(a_ft, s_ft, b_ft, dead_psf * per_ft, snow_psf * per_ft,  # type: ignore[operator]
                   modulus * inertia, depth_in / 12.0)
    limit_in = s_ft * 12.0 / DEFLECTION_DENOMINATOR
    dead_plf, snow_plf = dead_psf * per_ft, snow_psf * per_ft  # type: ignore[operator]
    loads = (Step("w_D", "dead line load over the roof-bearing run", dead_plf, "plf",
                  "q_D A_t / L", f"{num(dead_psf)} x {num(tributary_ft2)} / {num(length_ft)}"),
             Step("w_S", "snow line load (design snow, drift included)", snow_plf, "plf",
                  "q_S A_t / L", f"{num(snow_psf)} x {num(tributary_ft2)} / {num(length_ft)}"))  # type: ignore[arg-type]
    patterns = (f"w_D on a, s and b; w_S on each of the 8 subsets; a {num(a_ft)}, "
                f"s {num(s_ft)}, b {num(b_ft)} ft")
    statics = "statics, ASCE 7-16 §4.3.3 partial loading"
    f_b = env.moment_lb_ft * 12.0 / section_modulus
    f_v = 1.5 * env.shear_at_d_lb / (width_in * depth_in)
    r_max = max(env.reactions_lb)
    f_p = r_max / (width_in * post_in)
    dims = f"{num(width_in)} x {num(depth_in)}"
    combo, factors = D_PLUS_S
    states = (
        LimitState("bending", f_b, fb, "psi",
                   f"AWC NDS 2018 §5.3 — 24F-V4 DF Fb {FB_PSI:,.0f} psi x C_M {CM_FB} x C_D "
                   f"{CD_SNOW} x C_V {cv:.3f} (x = {VOLUME_EXPONENT:g}); M {env.moment_lb_ft:,.0f}"
                   f" lb-ft over {s_ft:.3f}' with {a_ft:.3f}' / {b_ft:.3f}' past the posts",
                   combination=combo, combination_factors=factors, working=(
                       *loads,
                       Step("M", "largest bending moment over the load patterns",
                            env.moment_lb_ft, "lb-ft", "max |M(x)|", patterns, statics),
                       Step("S", "section modulus", section_modulus, "in^3", "b d^2 / 6",
                            f"{num(width_in)} x {num(depth_in)}^2 / 6"),
                       Step("f_b", "bending stress", f_b, "psi", "12 M / S",
                            f"12 x {num(env.moment_lb_ft)} / {num(section_modulus)}"),
                       Step("C_V", "volume factor (deck braces the top edge, so C_L = 1)",
                            cv, "", "(21/s)^0.1 (12/d)^0.1 (5.125/b)^0.1 <= 1",
                            f"(21/{num(s_ft)})^0.1 x (12/{num(depth_in)})^0.1 x "
                            f"(5.125/{num(width_in)})^0.1", "NDS §5.3.6, x = 10"),
                       Step("F_b'", "allowable bending stress", fb, "psi", "F_b C_M C_D C_V",
                            f"{num(FB_PSI)} x {CM_FB} x {CD_SNOW} x {num(cv)}",
                            "NDS Supplement Table 5A; Table 5.3.1 wet; Table 2.3.2 snow"))),
        LimitState("shear", f_v, fv, "psi",
                   f"NDS §3.4.3.1(a), V at d — Fv {FV_PSI:.0f} psi x C_M {CM_FV} x C_D "
                   f"{CD_SNOW}", combination=combo, combination_factors=factors, working=(
                       *loads,
                       Step("V", "largest shear at d from a post face", env.shear_at_d_lb,
                            "lb", "max |V(x)|, x = d from each face", patterns,
                            "statics; NDS §3.4.3.1(a)"),
                       Step("f_v", "shear stress", f_v, "psi", "1.5 V / (b d)",
                            f"1.5 x {num(env.shear_at_d_lb)} / ({dims})"),
                       Step("F_v'", "allowable shear stress", fv, "psi", "F_v C_M C_D",
                            f"{num(FV_PSI)} x {CM_FV} x {CD_SNOW}",
                            "NDS Supplement Table 5A; Table 5.3.1 wet"))),
        LimitState("bearing on the post", f_p, fc_perp, "psi",
                   f"NDS §3.10 over the {post_in:.2f}\" post end — Fc-perp {FC_PERP_PSI:.0f} psi "
                   f"x C_M {CM_FC_PERP}", combination=combo, combination_factors=factors,
                   working=(
                       *loads,
                       Step("R", "largest post reaction over the load patterns", r_max, "lb",
                            "max R1, R2", patterns, statics),
                       Step("f_c,perp", "bearing stress on the post end", f_p, "psi",
                            "R / (b l_b)", f"{num(r_max)} / ({num(width_in)} x {num(post_in)})"),
                       Step("F_c,perp'", "allowable bearing stress", fc_perp, "psi",
                            "F_c,perp C_M", f"{num(FC_PERP_PSI)} x {CM_FC_PERP}",
                            "NDS Supplement Table 5A; Table 5.3.1 wet"))),
        LimitState("deflection", env.span_deflection_in, limit_in, "in",
                   f"IRC Table R301.7 L/{DEFLECTION_DENOMINATOR:.0f} on snow; E "
                   f"{E_PSI:,.0f} x C_M {CM_E}, I {inertia:.0f} in4",
                   combination=S_ALONE[0], combination_factors=S_ALONE[1], working=(
                       loads[1],
                       Step("E'I", "stiffness", modulus * inertia, "lb-in^2",
                            "E C_M b d^3 / 12",
                            f"{num(E_PSI)} x {CM_E} x {num(width_in)} x {num(depth_in)}^3 / 12",
                            "NDS Supplement Table 5A; Table 5.3.1 wet"),
                       Step("delta", "largest snow-only sag between the posts",
                            env.span_deflection_in, "in", "double integration of M / E'I",
                            "w_S on each subset of a, s, b", "statics"),
                       Step("delta_allow", "allowable deflection", limit_in, "in",
                            "12 s / 240", f"12 x {num(s_ft)} / 240",
                            "IRC Table R301.7"))),
    )
    uniform_plf = per_ft * (snow_psf + dead_psf)  # type: ignore[operator]
    truss_inputs: tuple[Quantity, ...] = ()
    notes: tuple[str, ...] = ("Graded as treated 24F-V4 DF (BEAM_GLULAM_TREATED_DF); a "
                              "substitute must be at least that layup.",)
    if (chord := beam_bearing(ctx, roof, beam)) is not None and (
            seats := truss_seats(ctx, roof, beam, snow_psf, dead_psf)):  # type: ignore[arg-type]
        truss_state, truss_inputs = truss_bearing_state(seats, *chord, FC_PERP_PSI, CM_FC_PERP,
                                                        half_span_ft(ctx, roof))
        states = (*states, truss_state)
        # The beam and its posts are graded at the UNIFORM design snow; the drift gradient puts
        # more on the south post. Model it: the post reactions with each truss at its own load.
        placed = _placed_post_reactions(ctx, beam, seats, a_ft, s_ft)
        uniform_max = max(env.reactions_lb)
        if placed is not None and max(placed) > uniform_max:
            f_placed = max(placed) / (width_in * post_in)
            placed_steps = (
                Step("R_placed", "largest post reaction with each truss at its own load",
                     max(placed), "lb", "max R_south, R_north",
                     f"{num(placed[0])}, {num(placed[1])}", "statics, drift placed per truss"),
                Step("f_c,perp", "bearing stress on the post end", f_placed, "psi",
                     "R_placed / (b l_b)",
                     f"{num(max(placed))} / ({num(width_in)} x {num(post_in)})"),
            )
            states = tuple(
                replace(st, demand=f_placed,
                        citation=st.citation + f"; the drift placed per truss puts "
                        f"{placed[0]:,.0f} / {placed[1]:,.0f} lb on the south / north post, "
                        f"over the uniform model's {uniform_max:,.0f}, and governs",
                        working=(*st.working[:-1], *placed_steps, st.working[-1]))
                if st.name == "bearing on the post" else st for st in states)
        notes = notes + (
            "Bending, shear and deflection take the UNIFORM design snow over the roof-bearing "
            "run, which bounds the drift's gradient; the posts take the larger of that and the "
            "reactions of each truss at its own load" + (
                f" (south {placed[0]:,.0f} lb, north {placed[1]:,.0f} lb)." if placed else "."),)
    governing = max(states, key=lambda state: state.ratio)
    return EngineeringRecord(
        item_id=item_id(KIND, beam.tag), kind=KIND, key=beam.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OK if governing.ratio <= 1.0 else Status.OVER,
        summary=(f"{beam.tag}: a {width_in:g}x{depth_in:g} glulam carrying "
                 f"{tributary_ft2:.0f} sf of {roof.tag} at {snow_psf + dead_psf:.0f} psf — "  # type: ignore[operator]
                 f"d/c {governing.ratio:.2f} on {governing.name}"),
        inputs=(Quantity("width", width_in, "in", 0.01),
                Quantity("depth", depth_in, "in", 0.01),
                Quantity("back_span", s_ft, "ft", 0.01),
                Quantity("overhang_a", a_ft, "ft", 0.01),
                Quantity("overhang_b", b_ft, "ft", 0.01),
                Quantity("tributary_area", tributary_ft2, "ft2", 0.01),
                Quantity("design_snow", snow_psf, "psf", 0.1),  # type: ignore[arg-type]
                Quantity("design_dead", dead_psf, "psf", 0.1),
                Quantity("uniform_load", uniform_plf, "plf", 0.1), *truss_inputs),
        limit_states=states, element_tags=(roof.tag, beam.tag),
        notes=notes)


def _placed_post_reactions(ctx: Any, beam: Any, seats: list, a_ft: float, s_ft: float
                           ) -> tuple[float, float] | None:
    """``(first post, second post)`` lb with each truss at its own reaction, by statics.

    ``a_ft``/``s_ft`` are the first post's station from the beam start and the post spacing."""
    start = ctx.plan.by_tag(beam.start_node)
    end = ctx.plan.by_tag(beam.end_node)
    if start is None or end is None or s_ft <= 0.0:
        return None
    (x0, y0), (x1, y1) = start.position.xy_m, end.position.xy_m
    dx, dy = x1 - x0, y1 - y0
    if min(abs(dx), abs(dy)) > 1e-6:
        return None
    origin, sign = (y0, 1.0 if dy > 0 else -1.0) if abs(dy) > abs(dx) else (
        x0, 1.0 if dx > 0 else -1.0)
    second = a_ft + s_ft
    first = 0.0
    total = 0.0
    for seat in seats:
        at = sign * (seat.station_ft * _M_PER_FT - origin) / _M_PER_FT
        first += seat.reaction_lb * (second - at) / s_ft
        total += seat.reaction_lb
    return first, total - first
