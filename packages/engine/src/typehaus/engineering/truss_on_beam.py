"""A roof truss's bottom chord bearing on a roof beam, for ``roof_beam`` (decision #108).

The truss reaction goes into the beam top perpendicular to grain over the chord's width
times the length of chord that actually sits on the beam. That length is read off the
resolved truss and beam, never assumed: the heel is set at the outside face of bearing and
the bottom chord runs across the whole support, so a truss on a 5 1/2" header bears 5 1/2"
— and one whose chord stops at the beam centreline bears half that. Catlin's canopy did,
until the headers moved onto the garage's truss bearing lines (geometry review C3-E6).

**Reaction (C-4, 2026-11-23).** Per truss: the design load at ITS station times its own
tributary width times the beam's half of the span. The tributary is half the distance to each
neighbouring truss (a neighbour may stand in an abutting roof: the garage's gable truss
shares the joint bay), or the roof edge. The authored drift triangle is placed, not
averaged: the beams' design snow is the triangle's mean over the roof, its slope is the
authored surcharge over the authored drift width, and the snow at a truss is the mean plus
that slope times the truss's offset from the roof's middle, downwind of the drift's source.
Without the three authored numbers or a downwind roof, every truss takes the design snow.

**Capacity.** The glulam's Fc-perp at wet service. ``C_b`` is NDS 2018 §3.10.4's
``(l_b + 0.375) / l_b`` on the chord's 1 1/2" width where the chord's face is at least 3"
from the beam end; the end truss, flush with the beam end, takes 1.0. The chord's own
Fc-perp is the truss designer's check and is higher (SPF 425 psi, dry, under the roof).

**Oracle.** ``houses/catlin/notes/canopy_west_band.md`` §7c.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.engineering.item import LimitState, Quantity, Step, num

_M_PER_IN = 0.0254
_M_PER_FT = 0.3048
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


@dataclass(frozen=True)
class TrussSeat:
    """One truss's bearing on the beam."""

    key: str
    station_ft: float
    width_ft: float
    snow_psf: float
    reaction_lb: float
    #: Beam end to the chord's nearer face, inches.
    edge_in: float


@dataclass(frozen=True)
class DriftTriangle:
    """The authored roof-step drift, as a surcharge that falls off downwind of its source roof.

    The source's design snow is the triangle's mean over the source; the slope is the authored
    surcharge over the authored drift width. ``sign`` points downwind along ``along``.
    """

    source_tag: str
    along: int
    sign: float
    mean_psf: float
    slope_psf_per_ft: float
    peak_psf: float
    balanced_psf: float
    middle_m: float

    def surcharge_psf(self, at_m: float) -> float:
        raw = self.mean_psf + self.slope_psf_per_ft * self.sign * (self.middle_m - at_m) / _M_PER_FT
        return min(max(raw, 0.0), self.peak_psf)


def drift_triangle(ctx: Any, source: Any) -> DriftTriangle | None:
    """The drift ``source`` (a roof graded at the authored design snow) casts onto a TRUSSED
    roof abutting it, else ``None``: without the three authored numbers or a downwind roof
    there is no triangle to place."""
    from typehaus.engineering.snow_drift import abutting

    structural = getattr(getattr(ctx, "preferences", None), "structural", None)
    design = getattr(structural, "roof_beam_snow_psf", None)
    balanced = getattr(structural, "roof_beam_balanced_snow_psf", None)
    peak = getattr(structural, "roof_beam_drift_surcharge_psf", None)
    width = getattr(structural, "roof_beam_drift_width_ft", None)
    if not (design and balanced and peak and width):
        return None
    for other in sorted(ctx.model.roofs, key=lambda r: r.tag):
        if other.tag == source.tag or not any(m.category == "roof_truss" for m in other.members):
            continue
        found = abutting(source.footprint, other.footprint)
        if found is not None:
            along, sign = found
            ring = [p[along] for p in source.footprint]
            return DriftTriangle(source.tag, along, sign, design - balanced, peak / width, peak,
                                 balanced, (min(ring) + max(ring)) / 2.0)
    return None


def _stations_along(ctx: Any, roof: Any, along: int) -> list[float]:
    """Truss stations (m) along the beam of ``roof`` and of any roof abutting it along the
    same axis: a neighbour truss shares the bay between, whichever roof it belongs to."""
    from typehaus.engineering.snow_drift import abutting

    out = [m.p0[along] for m in roof.members if m.category == "roof_truss"]
    for other in ctx.model.roofs:
        if other.tag != roof.tag and abutting(roof.footprint, other.footprint) is not None:
            out += [m.p0[along] for m in other.members if m.category == "roof_truss"]
    return sorted(set(round(v, 5) for v in out))


def truss_widths(ctx: Any, roof: Any) -> list[tuple[Any, float]]:
    """``(member, tributary width ft)`` of every truss of ``roof``: half the distance to each
    neighbour (in any abutting roof), the roof edge where there is none."""
    span_axis = 1 if roof.ridge_direction == "x" else 0
    along = 1 - span_axis
    edges = [p[along] for p in roof.footprint]
    stations = _stations_along(ctx, roof, along)
    out = []
    for member in roof.members:
        if member.category != "roof_truss":
            continue
        at = round(member.p0[along], 5)
        i = stations.index(at)
        south = (stations[i - 1] + at) / 2.0 if i else min(edges)
        north = (at + stations[i + 1]) / 2.0 if i + 1 < len(stations) else max(edges)
        out.append((member, (north - south) / _M_PER_FT))
    return out


def half_span_ft(ctx: Any, roof: Any) -> float:
    """The roof's span-axis reach shared between its bearing lines, ft."""
    span_axis = 1 if roof.ridge_direction == "x" else 0
    reach = [p[span_axis] for p in roof.footprint]
    refs = len(getattr(ctx.plan.by_tag(roof.tag), "bearing_refs", ()) or ()) or 2
    return (max(reach) - min(reach)) / refs / _M_PER_FT


def truss_seats(ctx: Any, roof: Any, beam: Any, snow_psf: float,
                dead_psf: float) -> list[TrussSeat]:
    """Every truss of ``roof`` crossing ``beam``, each at its own load (see the module note)."""
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.roof_geometry import roof_structure_framing

    spec = roof_structure_framing(ctx.model, roof)
    solid = next((s for s in ctx.model.solids if s.tag == beam.tag), None)
    if spec is None or spec.roof_frame != "truss" or solid is None:
        return []
    along = 1 - (1 if roof.ridge_direction == "x" else 0)
    lo, hi = min(p[along] for p in solid.outline), max(p[along] for p in solid.outline)
    chord_m = cross_section(spec.chord_member or spec.member).width_m
    drift = drift_triangle(ctx, roof)
    half = half_span_ft(ctx, roof)
    out: list[TrussSeat] = []
    for member, width_ft in truss_widths(ctx, roof):
        at = member.p0[along]
        if not lo <= at <= hi:
            continue
        snow = snow_psf if drift is None else drift.balanced_psf + drift.surcharge_psf(at)
        out.append(TrussSeat(
            key=member.child_key, station_ft=at / _M_PER_FT, width_ft=width_ft, snow_psf=snow,
            reaction_lb=(snow + dead_psf) * width_ft * half,
            edge_in=min(at - chord_m / 2.0 - lo, hi - at - chord_m / 2.0) / _M_PER_IN))
    return out


def beam_bearing(ctx: Any, roof: Any, beam: Any) -> tuple[float, float] | None:
    """``(chord width in, least bearing length in)`` of the trusses on ``beam``, else ``None``."""
    bearing = truss_bearing_on(ctx, roof, beam)
    return None if bearing is None else (bearing[0], bearing[1])


def truss_bearing_state(seats: list[TrussSeat], chord_in: float, length_in: float,
                        fc_perp_psi: float, cm: float, half_ft: float = 0.0,
                        ) -> tuple[LimitState, tuple[Quantity, ...]]:
    """The governing truss's limit state and the inputs it reads, for ``fingerprint``."""
    rows = []
    for seat in seats:
        cb = (chord_in + 0.375) / chord_in if seat.edge_in >= 3.0 and chord_in < 6.0 else 1.0
        rows.append((seat.reaction_lb / (chord_in * length_in) / (fc_perp_psi * cm * cb),
                     seat, cb))
    _, worst, cb = max(rows, key=lambda row: row[0])
    everyone = "; ".join(f"{s.key} {s.reaction_lb:,.0f} lb on {s.width_ft:.3f}' at "
                         f"{s.snow_psf:.1f} psf snow" for s in seats)
    load_psf = worst.reaction_lb / (worst.width_ft * half_ft) if half_ft else 0.0
    stress = worst.reaction_lb / (chord_in * length_in)
    working = (
        Step("R_t", f"reaction of {worst.key}, the governing truss", worst.reaction_lb, "lb",
             "(q_S + q_D) w_t l", f"{num(load_psf)} x {num(worst.width_ft)} x {num(half_ft)}",
             f"snow {num(worst.snow_psf)} psf at its station; w_t its tributary width, l the "
             f"beam's share of the span"),
        Step("f_c,perp", "chord bearing stress on the beam top", stress, "psi",
             "R_t / (b_chord l_b)", f"{num(worst.reaction_lb)} / ({num(chord_in)} x "
             f"{num(length_in)})"),
        Step("C_b", "bearing area factor", cb, "", "(l_b + 0.375) / l_b, or 1.0 within 3 in. "
             "of the beam end", f"({num(chord_in)} + 0.375) / {num(chord_in)}" if cb != 1.0
             else "chord face under 3 in. from the beam end", "NDS §3.10.4"),
        Step("F_c,perp'", "allowable bearing stress on the beam", fc_perp_psi * cm * cb, "psi",
             "F_c,perp C_M C_b", f"{num(fc_perp_psi)} x {cm} x {num(cb)}",
             "NDS Supplement Table 5A; Table 5.3.1 wet"))
    state = LimitState(
        "truss bearing on the beam", stress,
        fc_perp_psi * cm * cb, "psi",
        f"AWC NDS 2018 §3.10 — {worst.key} governs, {worst.reaction_lb:,.0f} lb over the "
        f"{chord_in:g}\" chord x {length_in:.3f}\" on the beam ({everyone}); Fc-perp "
        f"{fc_perp_psi:.0f} psi x C_M {cm} x C_b {cb:.3f} (§3.10.4"
        f"{', chord face under 3 in. from the beam end' if cb == 1.0 else ''})",
        combination="D + S, unfactored (ASD), C_D 1.15 for snow",
        combination_factors=(("D", 1.0), ("S", 1.0)), working=working)
    inputs = (Quantity("truss_chord_width", chord_in, "in", 0.01),
              Quantity("truss_bearing_length", length_in, "in", 0.01),
              Quantity("truss_reaction_max", max(s.reaction_lb for s in seats), "lb", 1.0))
    return state, inputs
