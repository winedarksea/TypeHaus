"""The band between a shear panel's top and its collector — ``lateral_system``'s band rows.

** A PANEL SELECTED BY PLAN FOOTPRINT IS NOT A PANEL THE DECK REACHES. ** ``lateral_lines``
finds a panel under a roof by where it stands in plan, and until 2026-09-30 nothing asked how
tall it was. ``W-BW-SCREEN`` tops out at +4'-0" and its collector's soffit is at +6'-4 1/8":
the N-S shear had to cross that band through two pinned 6x6s and caps with no lateral row, and
the record said it landed "directly on the panel's top plate". So, generically:

* where the panel's top is below the collector's soffit and nothing AUTHORED bridges the band
  (a ``SlatBrace``, or ``StrapBrace`` legs, on the wall's line reaching from the panel top
  onto the collector), the record is INCOMPLETE and names the gap;
* where a slat band bridges it, ``lateral_band_slats`` grades the slats, the centre post and the
  plate screws, and the frame rows below follow as for straps;
* where straps bridge it, each load direction's tension straps are graded on their coil-strap
  row — steel, and the nails that fit at the post end, pro-rated off the row — and the frame
  around them: the top plate and the base plates bearing END-ON against the chords
  (compression only, so either direction), the eave collector's clips, and the chords'
  overturning taken over the FULL height, deck to base, against the hold-down's own row, with
  the in-plane base shear all on ONE base, because the base plates bear in compression only.

**Oracle.** ``houses/catlin/notes/canopy_west_band.md`` §3-§5;
``tests/test_canopy_west_band_calcs.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.engineering.item import LimitState, Quantity

_M_PER_FT = 0.3048
#: How far off the wall's line a strap or a collector may stand and still be ON it, ft.
_ON_LINE_FT = 0.5
#: A band shorter than this is a plate joint, not a band, ft.
_GAP_FT = 1.0 / 12.0
#: NDS 2018 Supplement Table 4D, Southern Pine No. 2 timbers, Fc-perp, and NDS Table 4.3.8's
#: wet C_M on it — the chord post the plates bear on is graded wet like the rest of it.
POST_FC_PERP_PSI = 375.0
POST_FC_PERP_CM = 0.67


@dataclass
class BandResult:
    """What the band rows found. ``handled`` means the hold-down was graded here."""

    handled: bool = False


def _line(ctx: Any, wall: Any) -> tuple[tuple[float, float], tuple[float, float]] | None:
    from typehaus.engineering.lateral_lines import _ends_ft

    return _ends_ft(ctx, wall)


def _offset_and_station(line, x: float, y: float) -> tuple[float, float]:
    (x0, y0), (x1, y1) = line
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    return abs((x - x0) * uy - (y - y0) * ux), (x - x0) * ux + (y - y0) * uy


def collector_on(ctx: Any, spec: Any, line) -> Any | None:
    """The DiaphragmSpec collector beam running along the wall's line, or ``None``."""
    for tag in getattr(spec, "collector_refs", ()) or ():
        beam = ctx.plan.by_tag(tag)
        ends = [ctx.plan.by_tag(getattr(beam, n, "") or "") for n in ("start_node", "end_node")]
        if beam is None or any(getattr(e, "position", None) is None for e in ends):
            continue
        offsets = [_offset_and_station(line, *(c / _M_PER_FT for c in e.position.xy_m))[0]
                   for e in ends]
        if max(offsets) <= _ON_LINE_FT:
            return beam
    return None


def _beam_z_ft(beam: Any) -> tuple[float, float]:
    from typehaus.resolve.framing.profiles import cross_section

    top = float(beam.top_elevation.inches) / 12.0
    return top - (cross_section(beam.size).depth_m or 0.0) / _M_PER_FT, top


def band_rows(ctx: Any, roof_tag: str, wall: Any, spec: Any, shear_lb: float,
              states: list[LimitState], notes: list[str], missing: list[str],
              inputs: list[Quantity]) -> BandResult:
    """Grade the band over ``wall``; ``handled`` when the full-height hold-down was graded."""
    from typehaus.model.braces import StrapBrace

    line = _line(ctx, wall)
    collector = collector_on(ctx, spec, line) if line is not None else None
    if collector is None or wall.base_elevation is None or wall.top is None:
        return BandResult()
    soffit_ft, top_ft = _beam_z_ft(collector)
    panel_top_ft = float(wall.base_elevation.inches + wall.top.inches) / 12.0
    band_ft = soffit_ft - panel_top_ft
    if band_ft <= _GAP_FT:
        return BandResult()
    inputs.append(Quantity(f"band_height_{wall.tag}", band_ft, "ft", 0.001))
    straps = []
    for el in ctx.plan.all_elements():
        if not isinstance(el, StrapBrace):
            continue
        a = _offset_and_station(line, *(c / _M_PER_FT for c in el.start.xy_m))
        b = _offset_and_station(line, *(c / _M_PER_FT for c in el.end.xy_m))
        z = sorted((el.start_elevation.inches / 12.0, el.end_elevation.inches / 12.0))
        if max(a[0], b[0]) <= _ON_LINE_FT and z[0] <= panel_top_ft + 0.25 \
                and z[1] >= soffit_ft:
            straps.append((el, a[1], b[1]))
    if not straps:
        from typehaus.engineering.lateral_band_slats import slat_band_on, slat_rows

        band = slat_band_on(ctx, wall, line, panel_top_ft, soffit_ft, shear_lb)
        if band is not None:
            slat_rows(ctx, wall, collector, band, states, notes, missing, inputs)
            _end_bearing(ctx, wall, collector, shear_lb, panel_top_ft, states)
            _collector_clips(ctx, roof_tag, collector, shear_lb, states, missing)
            return BandResult(handled=_holdown_rows(ctx, wall, wall.shear_panel, shear_lb,
                                                    top_ft, states, notes, missing, inputs))
        missing.append(
            f"a brace across the {band_ft * 12:.2f}\" band between {wall.tag}'s top "
            f"(+{panel_top_ft:.3f}') and {collector.tag}'s soffit (+{soffit_ft:.3f}'): the "
            f"panel is under the roof in PLAN, but the deck's shear has to cross that band to "
            f"reach it, and nothing authored does — it would bend the chords through their "
            f"caps. Author a SlatBrace or StrapBraces on the line, or bring the panel to "
            f"the collector")
        return BandResult(handled=True)
    _strap_rows(wall, straps, shear_lb, states, notes, inputs)
    _end_bearing(ctx, wall, collector, shear_lb, panel_top_ft, states)
    _collector_clips(ctx, roof_tag, collector, shear_lb, states, missing)
    return BandResult(handled=_holdown_rows(ctx, wall, wall.shear_panel, shear_lb, top_ft,
                                            states, notes,
                                            missing, inputs))


def _strap_rows(wall, straps, shear_lb, states, notes, inputs) -> None:
    from typehaus.library.hardware.simpson_caps_bases import (
        COIL_STRAP_CITATION,
        COIL_STRAP_ROWS,
    )

    for sense, label in ((1, "toward the wall's end node"), (-1, "toward its start node")):
        # A strap is in tension when the deck pushes its TOP end away from its BOTTOM end.
        group = []
        for el, s_start, s_end in straps:
            z0, z1 = el.start_elevation.inches / 12.0, el.end_elevation.inches / 12.0
            s_bot, s_top = (s_start, s_end) if z0 < z1 else (s_end, s_start)
            if (s_top - s_bot) * sense > 0:
                group.append((el, abs(s_top - s_bot), abs(z1 - z0)))
        if not group:
            continue
        run = min(g[1] for g in group)
        rise = max(g[2] for g in group)
        theta = math.atan2(rise, run)
        tension = shear_lb / math.cos(theta) / len(group)
        el = group[0][0]
        row = COIL_STRAP_ROWS.get(el.product)
        inputs.append(Quantity(f"strap_tension_{wall.tag}_{'+' if sense > 0 else '-'}",
                               tension, "lb", 1.0))
        if row is None:
            notes.append(f"{el.product} has no coil-strap row in the catalog; the band's "
                         f"straps are not graded")
            continue
        steel, row_lb, row_nails, nail = row
        per_nail = row_lb / (row_nails / 2.0)
        nails = min(g[0].fasteners_each_end for g in group)
        capacity = min(steel, per_nail * nails)
        states.append(LimitState(
            f"{wall.tag} band strap tension, push {label}", tension, capacity, "lb",
            f"{COIL_STRAP_CITATION}; {shear_lb:,.1f} lb / cos {math.degrees(theta):.2f}° "
            f"over {len(group)} strap(s); the lesser of the steel {steel:,.0f} lb and "
            f"{nails} {nail} at the post end x {per_nail:.1f} lb, the row pro-rated by "
            f"its own nails"))
        notes.append(
            f"BAND, push {label}: {len(group)} tension strap(s) at {math.degrees(theta):.2f}° "
            f"carry {shear_lb:,.1f} lb; their vertical component "
            f"{shear_lb * math.tan(theta):,.1f} lb lifts the bottom-end chord and presses the "
            f"collector down — internal to the frame, and inside the full-height overturning "
            f"below. Compression straps are slack by assumption.")


def _members_bearing_on(wall, prefix: str, face: float, line) -> float:
    """Area, in², of ``wall``'s plate courses whose end butts the chord face at ``face``."""
    from typehaus.resolve.framing.profiles import cross_section

    area = 0.0
    for m in wall.members:
        if not m.child_key.startswith(prefix):
            continue
        ends = [_offset_and_station(line, m.p0[0] / _M_PER_FT, m.p0[1] / _M_PER_FT)[1],
                _offset_and_station(line, m.p1[0] / _M_PER_FT, m.p1[1] / _M_PER_FT)[1]]
        if any(abs(e - face) < 0.02 for e in ends):
            depth_in = (cross_section(m.profile).depth_m or 0.0) / 0.0254
            area += depth_in * (m.z1_m - m.z0_m) / 0.0254
    return area


def _end_bearing(ctx, wall, collector, shear_lb, panel_top_ft, states) -> None:
    """The top and base plates bear END-ON on a chord's inner face: compression only, and
    the two chords are the same section, so one face answers for either direction."""
    from typehaus.model.structure import Beam
    from typehaus.resolve.framing.profiles import cross_section

    line = _line(ctx, wall)
    resolved = ctx.model.wall(wall.tag)
    posts = [ctx.plan.by_tag(t) for t in wall.shear_panel.chord_refs]
    if resolved is None or len(posts) != 2 or any(p is None for p in posts):
        return
    stations = sorted((_offset_and_station(line, *(c / _M_PER_FT for c in p.position.xy_m))[1],
                       p) for p in posts)
    s_lo, post = stations[0][0], stations[0][1]
    face = s_lo + (cross_section(post.size).width_m or 0.0) / _M_PER_FT / 2.0
    # The sill the panel stands on, hung between the chords, bears on the same face.
    sills = [b for b in ctx.plan.all_elements()
             if isinstance(b, Beam) and set(b.bearing_refs or ()) == set(p.tag for p in posts)
             and b.top_elevation is not None and b.top_elevation.inches / 12.0 < panel_top_ft]
    sill_in2 = sum(((cross_section(b.size).width_m or 0.0) / 0.0254)
                   * ((cross_section(b.size).depth_m or 0.0) / 0.0254) for b in sills)
    fc_perp = POST_FC_PERP_PSI * POST_FC_PERP_CM
    for label, prefix, extra in (("top plate", "plate-top", 0.0),
                                 ("base plate and sill", "plate-bottom", sill_in2)):
        area = _members_bearing_on(resolved, prefix, face, line) + extra
        if area <= 0.0:
            continue
        states.append(LimitState(
            f"{wall.tag} {label} end bearing on a chord", shear_lb / area, fc_perp, "psi",
            f"the whole {shear_lb:,.1f} lb into ONE chord face over {area:.2f} in2 of end "
            f"grain — AWC NDS 2018 Supplement Table 4D Southern Pine No. 2 timbers Fc-perp "
            f"{POST_FC_PERP_PSI:.0f} psi x wet C_M {POST_FC_PERP_CM}; compression only, so "
            f"it needs no moment connection and serves either direction"))


def _collector_clips(ctx, roof_tag, collector, shear_lb, states, missing) -> None:
    from typehaus.hardware.catalog import allowable_for_model
    from typehaus.model.enums import ConnectorKind

    # Lateral ties only: the heel's uplift tie (HURRICANE_TIE) names the same pair and is
    # not a collector, whatever its F1 row says.
    clips = [el for el in ctx.plan.all_elements()
             if set(getattr(el, "connects", ()) or ()) == {roof_tag, collector.tag}
             and getattr(el, "kind", None) is ConnectorKind.TENSION_TIE
             and getattr(el, "size", None)]
    rated = []
    for clip in clips:
        allow = allowable_for_model(clip.size)
        values = [v for v in (getattr(allow, "lateral_f1_lb", None),
                              getattr(allow, "lateral_f2_lb", None)) if v]
        if values:
            rated.append((clip, min(values)))
    if not rated:
        missing.append(f"a rated collector connection along {collector.tag}: the deck's "
                       f"{shear_lb:,.0f} lb reaches it through the truss heels and the eave "
                       f"blocking, and heel ties rated for uplift carry ~110 lb lateral each")
        return
    each = shear_lb / len(rated)
    worst = min(rated, key=lambda r: r[1])
    states.append(LimitState(
        f"{collector.tag} eave collector clips", each, worst[1], "lb",
        f"{len(rated)} x {worst[0].size} blocking to {collector.tag}, the lower lateral "
        f"direction of the catalog row, {shear_lb:,.1f} lb shared equally"))


def _holdown_rows(ctx, wall, spec, shear_lb, top_ft, states, notes, missing, inputs) -> bool:
    """Overturning over the FULL height — collector top to the chord bases — on the base."""
    from typehaus.engineering.column_head_joint import _net_uplift
    from typehaus.engineering.lateral_lines import panel_chords_ft
    from typehaus.engineering.pier_basis import cast_piers
    from typehaus.hardware.catalog import allowable_for_model, hardware_by_model
    from typehaus.model.enums import ConnectorKind

    chords = panel_chords_ft(ctx, wall)
    if chords is None or not spec.holdown:
        return False
    lever = chords[0]
    bases = [el for el in ctx.plan.all_elements()
             if getattr(el, "kind", None) is ConnectorKind.POST_BASE
             and set(spec.chord_refs) & set(getattr(el, "connects", ()) or ())
             and getattr(el, "size", None) == spec.holdown]
    allow = allowable_for_model(spec.holdown)
    if len(bases) != 2 or allow is None or allow.uplift_lb is None:
        missing.append(f"the hold-down {spec.holdown} authored under both chords of "
                       f"{wall.tag} with a published uplift")
        return True
    base_ft = min(b.elevation.inches / 12.0 for b in bases)
    height = top_ft - base_ft
    piers = {p.tag: p for p in cast_piers(ctx)}
    uplift = max((_net_uplift(ctx, piers[t], notes=[]) or 0.0)
                 for b in bases for t in b.connects if t in piers) if piers else 0.0
    tension = shear_lb * height / lever + uplift
    inputs.extend((Quantity(f"chord_tension_{wall.tag}", tension, "lb", 1.0),
                   Quantity(f"overturning_height_{wall.tag}", height, "ft", 0.001)))
    lateral = allow.lateral_f1_lb
    along = all(getattr(b, "axis", None) == _axis_of(ctx, wall) for b in bases)
    if along and allow.lateral_f2_lb:
        lateral = allow.lateral_f2_lb
    states.append(LimitState(
        f"{wall.tag} chord hold-down, full height", tension, allow.uplift_lb, "lb",
        f"{spec.holdown}: {shear_lb:,.1f} lb x {height:.3f}' (collector top to the chord "
        f"bases) / {lever:.3f}' chord lever = {shear_lb * height / lever:,.1f} lb, plus the "
        f"column's net roof uplift {uplift:,.1f} lb (0.6D + 0.6W); no wall dead load "
        f"credited. {allow.citation.split(';')[0]}"))
    if lateral:
        states.append(LimitState(
            f"{wall.tag} chord base shear, one base", shear_lb, lateral, "lb",
            f"{spec.holdown} {'F2, oriented along the panel' if along else 'lower lateral'}: "
            f"the base plates bear on ONE chord in compression, so the whole in-plane shear "
            f"reaches one base, which is the compression chord — no uplift on it to combine"))
    item = hardware_by_model(spec.holdown)
    if getattr(item, "anchorage_in_rating", False):
        notes.append(f"{spec.holdown} is cast in and its uplift row is measured through the "
                     f"concrete (cracked), so no separate anchor and no ACI 318 Ch. 17 row "
                     f"stands in for it; the straps want >= 3in to the pier edge.")
    return True


def _axis_of(ctx, wall) -> str:
    (x0, y0), (x1, y1) = _line(ctx, wall)
    return "y" if abs(y1 - y0) >= abs(x1 - x0) else "x"
