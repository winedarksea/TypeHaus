"""A roof truss's bottom chord bearing on a roof beam, for ``roof_beam`` (decision #108).

The truss reaction goes into the beam top perpendicular to grain over the chord's width
times the length of chord that actually sits on the beam. That length is read off the
resolved truss and beam, never assumed: the heel is set at the outside face of bearing and
the bottom chord runs across the whole support, so a truss on a 5 1/2" header bears 5 1/2"
— and one whose chord stops at the beam centreline bears half that. Catlin's canopy did,
until the headers moved onto the garage's truss bearing lines (geometry review C3-E6).

**Reaction.** The beam's own uniform load (the record's ``uniform_load``, plf) times the
truss spacing: the field truss, on the same load the beam was designed for. Conservative
against the truss's own tributary, because the beam spreads the roof's edge overhangs over
its loaded run.

**Capacity.** The glulam's Fc-perp at wet service, ``C_b`` taken as 1.0 (AWC NDS 2018
§3.10.4 would allow (l_b + 0.375)/l_b on a 1 1/2" chord away from the beam end; the end truss
sits flush with the beam end, where it does not apply). The chord's own Fc-perp is the truss
designer's check and is higher (SPF 425 psi, dry, under the roof).

**Oracle.** ``houses/catlin/notes/canopy_west_band.md`` §7 2026-10-31 amendment.
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering.item import LimitState, Quantity

_M_PER_IN = 0.0254
#: Below this a truss "on" the beam is a corner touching it, not a bearing.
_MIN_OVERLAP_M = 1e-4


def truss_bearing_on(ctx: Any, roof: Any, beam: Any) -> tuple[float, float, float] | None:
    """``(chord width in, least bearing length in, truss spacing in)`` of the trusses on
    ``beam``, or ``None`` where the roof is not trussed or none of its trusses crosses it."""
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.roof_geometry import roof_structure_framing

    spec = roof_structure_framing(ctx.model, roof)
    solid = next((s for s in ctx.model.solids if s.tag == beam.tag), None)
    if spec is None or spec.roof_frame != "truss" or solid is None or spec.spacing is None:
        return None
    span_axis = 1 if roof.ridge_direction == "x" else 0
    along_axis = 1 - span_axis
    across = [p[span_axis] for p in solid.outline]
    along = [p[along_axis] for p in solid.outline]
    lengths = []
    for member in roof.members:
        if member.category != "roof_truss":
            continue
        station = member.p0[along_axis]
        if not min(along) <= station <= max(along):
            continue
        lo, hi = sorted((member.p0[span_axis], member.p1[span_axis]))
        overlap = min(hi, max(across)) - max(lo, min(across))
        if overlap > _MIN_OVERLAP_M:
            lengths.append(overlap)
    if not lengths:
        return None
    chord = cross_section(spec.chord_member or spec.member).width_m
    return chord / _M_PER_IN, min(lengths) / _M_PER_IN, spec.spacing.inches


def truss_bearing_state(bearing: tuple[float, float, float], uniform_plf: float,
                        fc_perp_psi: float, cm: float) -> tuple[LimitState, tuple[Quantity, ...]]:
    """The limit state and the inputs it reads, for ``fingerprint``."""
    chord_in, length_in, spacing_in = bearing
    reaction_lb = uniform_plf * spacing_in / 12.0
    state = LimitState(
        "truss bearing on the beam", reaction_lb / (chord_in * length_in), fc_perp_psi * cm,
        "psi",
        f"AWC NDS 2018 §3.10 — truss reaction {reaction_lb:,.0f} lb ({uniform_plf:.1f} plf x "
        f"{spacing_in:g}\" o.c.) over the {chord_in:g}\" chord x {length_in:.3f}\" on the beam; "
        f"Fc-perp {fc_perp_psi:.0f} psi x C_M {cm}, C_b 1.0")
    inputs = (Quantity("truss_chord_width", chord_in, "in", 0.01),
              Quantity("truss_bearing_length", length_in, "in", 0.01),
              Quantity("truss_spacing", spacing_in, "in", 0.01))
    return state, inputs
