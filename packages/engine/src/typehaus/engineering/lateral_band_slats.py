"""A slat band across ``lateral_band``'s gap: 45° slats as knee braces, one connector an end.

``resolve/slat_braces.slat_layout`` says which slats there are; this grades them. The two bays
are mirror images with the same joints, so they share the push equally, one in tension and one
in compression. The verticals carry the band's shear only by bending and have none at
mid-band, so the slats crossing it carry their bay's whole half. Everything else follows from
the force one slat carries, ``h`` each way at each end:

* the slat's connector (a rated F1 along the brace) and its buckling;
* the centre post, pushed the SAME way by both bays, in bending, and its end ties;
* the plate screws, lateral plus the tension bay's withdrawal (NDS §12.4.1);
* the header couple and a chord's outward push, which ``wood_roof_post`` reads.

**Oracle.** ``houses/catlin/notes/canopy_west_band.md`` §3a-§3h, §5b;
``tests/test_canopy_west_band_calcs.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.engineering.item import LimitState, Quantity

_M_PER_FT = 0.3048
_IN_PER_M = 1.0 / 0.0254
#: AWC NDS 2018 Supplement Table 4B, Southern Pine No. 2, 2"-4" thick, 2"-4" wide: Fc and
#: E_min, with Table 4B's wet-service C_M (0.8 on Fc, 0.9 on E_min). The slats stand in the
#: weather.
SLAT_FC_PSI = 1450.0
SLAT_EMIN_PSI = 510_000.0
SLAT_FC_CM = 0.8
SLAT_EMIN_CM = 0.9
SLAT_PROFILE = "2x4"
CD_WIND = 1.6


@dataclass(frozen=True)
class SlatBand:
    """A slat band on a wall's line and the one force it is graded on."""

    band: Any
    layout: Any
    shear_lb: float
    crossing: int  # slats crossing mid-band in one bay

    @property
    def per_end_lb(self) -> float:
        """``h``: a slat's horizontal (and vertical) component at each end."""
        return self.shear_lb / 2.0 / self.crossing

    @property
    def slat_lb(self) -> float:
        return self.per_end_lb * math.sqrt(2.0)

    def landings(self, which: str) -> int:
        """Slats of ONE bay landing on ``chord`` | ``sill`` | ``centre`` | ``top``."""
        return sum(1 for s in self.layout.bay(0) if which in (s.low, s.high))

    @property
    def mid_band_ft(self) -> float:
        el, lay = self.band, self.layout
        return (el.base_elevation.meters + lay.plate + lay.height / 2.0) / _M_PER_FT

    def chord_push_lb(self) -> float:
        """A compression bay's outward push on its chord, at mid-band (note §3f)."""
        return self.landings("chord") * self.per_end_lb

    def couple_lb_ft(self) -> float:
        """The two bays' top landings on the header: equal, opposite, mirrored (note §3h)."""
        lay = self.layout
        top = [s for s in lay.bay(0) if s.high == "top"]
        if not top:
            return 0.0
        centroid = sum(lay.height + s.c for s in top) / len(top)
        lever = 2.0 * (lay.width + lay.centre_half - centroid) / _M_PER_FT
        return len(top) * self.per_end_lb * lever


def slat_band_on(ctx: Any, wall: Any, line, panel_top_ft: float, soffit_ft: float,
                 shear_lb: float) -> SlatBand | None:
    """The SlatBrace on ``wall``'s line reaching panel top to soffit, laid out, or ``None``."""
    from typehaus.engineering.lateral_band import _ON_LINE_FT, _offset_and_station
    from typehaus.model.braces import SlatBrace
    from typehaus.resolve.slat_braces import slat_layout

    for el in ctx.plan.all_elements():
        if not isinstance(el, SlatBrace):
            continue
        ends = [_offset_and_station(line, *(c / _M_PER_FT for c in p.xy_m))[0]
                for p in (el.start, el.end)]
        z0, z1 = el.base_elevation.inches / 12.0, el.top_elevation.inches / 12.0
        if max(ends) > _ON_LINE_FT or z0 > panel_top_ft + 0.25 or z1 < soffit_ft - 0.25:
            continue
        layout = slat_layout(el)
        crossing = layout.crossing_mid(0) if layout is not None else 0
        if crossing:
            return SlatBand(el, layout, shear_lb, crossing)
    return None


def band_for_wall(ctx: Any, wall: Any, roof_tag: str, shear_lb: float) -> SlatBand | None:
    """``slat_band_on`` from a wall and its roof, for ``wood_roof_post``."""
    from typehaus.engineering.lateral_band import _beam_z_ft, _line, collector_on

    spec = getattr(ctx.plan.by_tag(roof_tag), "diaphragm", None)
    line = _line(ctx, wall) if wall is not None else None
    if spec is None or line is None or wall.base_elevation is None or wall.top is None:
        return None
    collector = collector_on(ctx, spec, line)
    if collector is None:
        return None
    soffit_ft, _ = _beam_z_ft(collector)
    top_ft = (wall.base_elevation.inches + wall.top.inches) / 12.0
    return slat_band_on(ctx, wall, line, top_ft, soffit_ft, shear_lb)


def slat_rows(ctx: Any, wall: Any, collector: Any, sb: SlatBand, states: list[LimitState],
              notes: list[str], missing: list[str], inputs: list[Quantity]) -> None:
    """The band's own rows (note §3b, §3f, §3g); the frame around it is ``lateral_band``'s."""
    from typehaus.hardware.catalog import ROLE_KNEE_BRACE, allowable_for_model

    el, lay = sb.band, sb.layout
    p, h = sb.slat_lb, sb.per_end_lb
    inputs.extend((Quantity(f"slat_force_{el.tag}", p, "lb", 0.1),
                   Quantity(f"slats_crossing_mid_{el.tag}", sb.crossing, "", 1.0),
                   Quantity(f"slat_bay_width_{el.tag}", lay.width * _IN_PER_M, "in", 0.01),
                   Quantity(f"slat_bay_height_{el.tag}", lay.height * _IN_PER_M, "in", 0.01)))
    notes.append(
        f"BAND, {el.tag}: {len(lay.slats)} slats at 45°, {len(lay.bay(0))} a bay, mirrored to "
        f"rise toward the centre post. The bays share {sb.shear_lb:,.1f} lb equally (mirror "
        f"images, the same joints); the {sb.crossing} crossing mid-band, where the verticals "
        f"carry no shear, take a bay's half: {p:,.1f} lb a slat, tension or compression.")
    allow = allowable_for_model(el.connector, role=ROLE_KNEE_BRACE)
    if allow is None or not allow.lateral_f1_lb:
        missing.append(f"a published F1 along the brace for {el.connector!r}, the connector "
                       f"at each end of {el.tag}'s slats")
    else:
        states.append(LimitState(
            f"{el.tag} slat end, {el.connector}", p, allow.lateral_f1_lb, "lb",
            f"one {el.connector} each end, {allow.citation.split(';')[0]}; {allow.species}; "
            f"in-service MC <= 19% (the canopy's dry-service condition)"))
    _slat_buckling(el, lay, p, states, missing)
    _centre_post(el, lay, sb, states, missing)
    _plate_screws(el, collector, wall, sb, states, missing)
    notes.append(
        f"BAND, {el.tag}: each chord takes {sb.chord_push_lb():,.1f} lb across the band from "
        f"its bay (outward from a compression bay; wood_roof_post grades it); the header "
        f"couple from the slats is {sb.couple_lb_ft():,.1f} lb-ft. Vertical components on "
        f"the centre post cancel; h = {h:,.2f} lb an end.")


def _slat_buckling(el, lay, p, states, missing) -> None:
    from typehaus.resolve.framing.profiles import cross_section

    if el.slat != SLAT_PROFILE:
        missing.append(f"NDS Table 4B values for the {el.slat!r} slats of {el.tag}")
        return
    section = cross_section(el.slat)
    d_in, b_in = section.width_m * _IN_PER_M, section.depth_m * _IN_PER_M
    length_in = max(s.length for s in lay.slats) * _IN_PER_M
    fc_star = SLAT_FC_PSI * SLAT_FC_CM * CD_WIND
    fce = 0.822 * SLAT_EMIN_PSI * SLAT_EMIN_CM / (length_in / d_in) ** 2
    ratio = fce / fc_star
    term = (1.0 + ratio) / 1.6
    cp = term - math.sqrt(term ** 2 - ratio / 0.8)
    states.append(LimitState(
        f"{el.tag} slat buckling", p, fc_star * cp * d_in * b_in, "lb",
        f"NDS §3.7, the longest slat {length_in:.2f}\" about its {d_in:g}\" face, l/d "
        f"{length_in / d_in:.2f}; Table 4B SP No. 2 Fc {SLAT_FC_PSI:g} x wet {SLAT_FC_CM} x "
        f"C_D {CD_WIND}, E_min {SLAT_EMIN_PSI:,.0f} x {SLAT_EMIN_CM}: FcE {fce:.1f} psi, "
        f"C_P {cp:.4f}"))


def _centre_post(el, lay, sb, states, missing) -> None:
    from typehaus.engineering.wood_roof_post import FB_WET_PSI
    from typehaus.hardware.catalog import allowable_for_model

    if el.centre_post != "6x6":
        missing.append(f"NDS Table 4D values for {el.tag}'s {el.centre_post!r} centre post")
        return
    force = 2.0 * sb.landings("centre") * sb.per_end_lb
    span_ft = lay.height / _M_PER_FT
    moment = force * span_ft / 8.0
    fb = moment * 12.0 / (5.5 ** 3 / 6.0)
    states.append(LimitState(
        f"{el.tag} centre post bending", fb, FB_WET_PSI * CD_WIND, "psi",
        f"both bays push it the same way: 2 x {sb.landings('centre')} x {sb.per_end_lb:.2f} = "
        f"{force:,.1f} lb uniform over {span_ft:.4f}', M = {moment:,.1f} lb-ft on a 6x6; "
        f"Table 4D SP No. 2 timbers Fb {FB_WET_PSI:g} x wet C_M 1.0 x C_D {CD_WIND}"))
    allow = allowable_for_model(el.centre_post_tie)
    values = [v for v in (getattr(allow, "lateral_f1_lb", None),
                          getattr(allow, "lateral_f2_lb", None)) if v]
    if not values:
        missing.append(f"a published lateral row for {el.centre_post_tie!r}, the ties at "
                       f"each end of {el.tag}'s centre post")
        return
    states.append(LimitState(
        f"{el.tag} centre post end ties", force / 2.0,
        el.centre_post_ties_each_end * min(values), "lb",
        f"half of {force:,.1f} lb at each plate on {el.centre_post_ties_each_end} "
        f"{el.centre_post_tie}, the lower lateral row; {allow.citation.split(';')[0]}"))


def _plate_screws(el, collector, wall, sb, states, missing) -> None:
    from typehaus.library.hardware.fasteners import SDWS22_WOOD_CITATION, SDWS22_WOOD_ROWS

    row = SDWS22_WOOD_ROWS.get(el.plate_fastener)
    if row is None:
        missing.append(f"an ER-192 wood row for {el.plate_fastener!r}, {el.tag}'s plate screws")
        return
    z, _side, w_per_in, thread, w_max = row
    z_prime = z * CD_WIND
    w_prime = min(w_per_in * thread, w_max) * CD_WIND
    half = el.plate_fasteners / 2.0
    lateral = sb.shear_lb / el.plate_fasteners
    for label, which, into in (("top plate", "top", collector.tag),
                               ("sill", "sill", f"{wall.tag}'s top plate")):
        withdrawal = sb.landings(which) * sb.per_end_lb / half
        resultant = math.hypot(lateral, withdrawal)
        alpha = math.atan2(withdrawal, lateral)
        z_alpha = w_prime * z_prime / (w_prime * math.cos(alpha) ** 2
                                       + z_prime * math.sin(alpha) ** 2)
        states.append(LimitState(
            f"{el.tag} {label} screws into {into}", resultant, z_alpha, "lb",
            f"{el.plate_fasteners} {el.plate_fastener}: {lateral:.2f} lb lateral each, and the "
            f"tension bay's {sb.landings(which)} landings pull {withdrawal:.2f} lb out of each "
            f"of its {half:g}; NDS §12.4.1 at {math.degrees(alpha):.2f}° with Z' {z_prime:g}, "
            f"W'p {w_prime:g} (C_D {CD_WIND}, dry service). {SDWS22_WOOD_CITATION}"))
