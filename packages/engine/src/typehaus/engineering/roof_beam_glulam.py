"""A GLULAM roof beam, for ``roof_beam`` — split out because that module is sawn-only by rule.

A decimal ``Beam.size`` (``"5.5x11.875"``) is a glulam sold against its own design values, not
an ``N-2xM``. A 5-1/2" width is a Western-species glulam, so it is graded at the 24F-V4 DF
combination: ANSI/AWC NDS 2018 Supplement Table 5A. Wet service (Table 5.3.1), snow ``C_D``
1.15 (Table 2.3.2), and the volume factor ``C_V`` with x = 10 for a Western-species layup
(§5.3.6), which is the smaller of ``C_V`` and ``C_L`` because the deck braces the top edge.

The beam is graded on its own two BEARING POSTS with whatever runs past each, by statics under
the eight load patterns ``overhang_beam.envelope`` walks — the roof's half-area spread uniformly
over the header's length. Bearing is over the post's own width (the cap seats the beam on the
post end), at Fc-perp wet.

**Oracle.** ``houses/catlin/notes/canopy_west_band.md`` §7;
``tests/test_canopy_west_band_calcs.py``.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)

KIND = "roof_beam"

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
    states = (
        LimitState("bending", env.moment_lb_ft * 12.0 / section_modulus, fb, "psi",
                   f"AWC NDS 2018 §5.3 — 24F-V4 DF Fb {FB_PSI:,.0f} psi x C_M {CM_FB} x C_D "
                   f"{CD_SNOW} x C_V {cv:.3f} (x = {VOLUME_EXPONENT:g}); M {env.moment_lb_ft:,.0f}"
                   f" lb-ft over {s_ft:.3f}' with {a_ft:.3f}' / {b_ft:.3f}' past the posts"),
        LimitState("shear", 1.5 * env.shear_at_d_lb / (width_in * depth_in), fv, "psi",
                   f"NDS §3.4.3.1(a), V at d — Fv {FV_PSI:.0f} psi x C_M {CM_FV} x C_D "
                   f"{CD_SNOW}"),
        LimitState("bearing on the post", max(env.reactions_lb) / (width_in * post_in),
                   fc_perp, "psi",
                   f"NDS §3.10 over the {post_in:.2f}\" post end — Fc-perp {FC_PERP_PSI:.0f} psi "
                   f"x C_M {CM_FC_PERP}"),
        LimitState("deflection", env.span_deflection_in, limit_in, "in",
                   f"IRC Table R301.7 L/{DEFLECTION_DENOMINATOR:.0f} on snow; E "
                   f"{E_PSI:,.0f} x C_M {CM_E}, I {inertia:.0f} in4"),
    )
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
                Quantity("uniform_load", per_ft * (snow_psf + dead_psf), "plf", 0.1)),  # type: ignore[operator]
        limit_states=states, element_tags=(roof.tag, beam.tag),
        notes=("A 5-1/2\" glulam is a Western-species width; 24F-V4 DF is the combination "
               "graded, and the supplier's treated stock must be at least that layup.",))
