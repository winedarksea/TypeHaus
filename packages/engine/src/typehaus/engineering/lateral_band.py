"""The band between a shear panel's top and its collector — ``lateral_system``'s band rows.

** A PANEL SELECTED BY PLAN FOOTPRINT IS NOT A PANEL THE DECK REACHES. ** ``lateral_lines``
finds a panel under a roof by where it stands in plan, not by how tall it is. A panel that
tops out below its collector's soffit leaves a band the shear must cross. So:

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

from typehaus.engineering.canopy_service import DRY_UNDER_ROOFING
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
            strapped = _strapped_out(ctx, wall, notes)
            _end_bearing(ctx, wall, collector, shear_lb, panel_top_ft, states, strapped)
            _collector_clips(ctx, roof_tag, collector, shear_lb, states, missing, inputs)
            if strapped:
                return BandResult(handled=True)
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
    strapped = _strapped_out(ctx, wall, notes)
    _end_bearing(ctx, wall, collector, shear_lb, panel_top_ft, states, strapped)
    _collector_clips(ctx, roof_tag, collector, shear_lb, states, missing, inputs)
    if strapped:
        return BandResult(handled=True)
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


def _strapped_out(ctx, wall, notes) -> bool:
    """A tension strap at the panel's top, along its line, into another wall: the shear
    leaves there and never reaches the chords' bases (G5, 2026-11-23). It is graded as a
    tie joint of the deck the panel stands on (``deck_tie``), with the panel's share in it."""
    from typehaus.engineering.deck_tie import TENSION_TIE_ROLES
    from typehaus.hardware.catalog import hardware_by_model
    from typehaus.model.elements import Wall

    for el in ctx.plan.all_elements():
        connects = getattr(el, "connects", ()) or ()
        item = hardware_by_model(getattr(el, "size", "") or "")
        if wall.tag not in connects or item is None or item.role not in TENSION_TIE_ROLES:
            continue
        others = [t for t in connects if t != wall.tag and isinstance(ctx.plan.by_tag(t), Wall)]
        if others and getattr(el, "axis", None) == _axis_of(ctx, wall):
            notes.append(
                f"{wall.tag}'s shear leaves at its top plate through {el.tag} ({el.size}) "
                f"into {others[0]}, graded with the panel's share in deck_tie; the chords' "
                f"overturning, base shear, pier pull-out and pad rows carry no N-S and are "
                f"not graded here (notes/north_entry_piers.md §10p).")
            return True
    return False


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


def _end_bearing(ctx, wall, collector, shear_lb, panel_top_ft, states,
                 strapped: bool = False) -> None:
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
    # Strapped out at the top plate, the base plate and sill carry no N-S to a chord.
    rows = (("top plate", "plate-top", 0.0),) + (
        () if strapped else (("base plate and sill", "plate-bottom", sill_in2),))
    for label, prefix, extra in rows:
        area = _members_bearing_on(resolved, prefix, face, line) + extra
        if area <= 0.0:
            continue
        states.append(LimitState(
            f"{wall.tag} {label} end bearing on a chord", shear_lb / area, fc_perp, "psi",
            f"the whole {shear_lb:,.1f} lb into ONE chord face over {area:.2f} in2 of end "
            f"grain — AWC NDS 2018 Supplement Table 4D Southern Pine No. 2 timbers Fc-perp "
            f"{POST_FC_PERP_PSI:.0f} psi x wet C_M {POST_FC_PERP_CM}; compression only, so "
            f"it needs no moment connection and serves either direction"))


def _collector_clips(ctx, roof_tag, collector, shear_lb, states, missing, inputs) -> None:
    from typehaus.engineering.collector_attachment import collector_attachment_missing
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
    attachment_missing = collector_attachment_missing(
        ctx.model, roof_tag, collector.tag, [clip for clip, _capacity in rated])
    missing.extend(attachment_missing)
    each = shear_lb / len(rated)
    # The open front adds its chord force to the plate it shares with this row.
    inputs.append(Quantity(f"collector_clip_each_{collector.tag}", each, "lb", 1.0))
    worst = min(rated, key=lambda r: r[1])
    states.append(LimitState(
        f"{collector.tag} eave collector clips", each, worst[1], "lb",
        f"{len(rated)} x {worst[0].size} blocking to {collector.tag}, the lower lateral "
        f"direction of the catalog row, {shear_lb:,.1f} lb shared equally; {DRY_UNDER_ROOFING}"
        + ("; NOMINAL ONLY — the blocking attachment is missing" if attachment_missing else "")))


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
    _pullout_rows(ctx, bases, piers, tension, states, missing)
    _pad_bearing_rows(ctx, bases, piers, shear_lb * height / lever, states, missing)
    item = hardware_by_model(spec.holdown)
    if getattr(item, "anchorage_in_rating", False):
        notes.append(f"{spec.holdown} is cast in and its uplift row is measured through the "
                     f"concrete (cracked), so no separate anchor and no ACI 318 Ch. 17 row "
                     f"stands in for it; the straps want >= 3in to the pier edge.")
    return True


#: The low end of ``soil.SOIL_UNIT_WEIGHT_BAND_PCF``: the band end that holds LESS down.
_PRISM_PCF = 110.0


def _pullout_rows(ctx, bases, piers, tension, states, missing) -> None:
    """Each chord's pier against the full chord tension, at ASCE 7-16 §2.4.1's 0.6D.

    Decision 15 (review C-1). Held down by the shaft, the doweled pad, the soil prism standing
    on the pad's projection (grade to pad top, the low end of the unit-weight band), and the
    post and wall dead the pier carries; never the roof or deck dead (the net roof uplift in
    the tension already spends the roof's 0.6D). ``north_entry_piers.md`` §6d.
    """
    from typehaus.engineering.footing_pier import grade_ft
    from typehaus.engineering.soil import CONCRETE_UNIT_WEIGHT_PCF
    from typehaus.model.structure import Pad

    grade = grade_ft(ctx)
    for tag in sorted({t for b in bases for t in b.connects if t in piers}):
        pier = piers[tag]
        pad = ctx.plan.by_tag(getattr(ctx.plan.by_tag(tag), "supported_by", "") or "")
        if grade is None or not isinstance(pad, Pad) or pad.bottom_elevation is None:
            missing.append(f"the pad under {tag} and Site.grade, for its pull-out row")
            continue
        area = _pad_area_ft2(pad)
        thick = pad.thickness.inches / 12.0
        top = pad.bottom_elevation.inches / 12.0 + thick
        shaft_ft2 = pier.gross_area_in2 / 144.0
        pad_lb = area * thick * CONCRETE_UNIT_WEIGHT_PCF
        prism_lb = max(area - shaft_ft2, 0.0) * max(grade - top, 0.0) * _PRISM_PCF
        held = pier.self_weight_lb + pad_lb + prism_lb + pier.carried_dead_lb \
            + pier.wall_dead_lb
        states.append(LimitState(
            f"{tag} pier pull-out under the tension chord", tension, 0.6 * held, "lb",
            f"0.6 x (shaft {pier.self_weight_lb:,.0f} + doweled pad {pad.tag} "
            f"{area:.2f} ft2 x {thick * 12:.0f}\" {pad_lb:,.0f} + soil over the pad "
            f"{grade - top:.2f}' at {_PRISM_PCF:.0f} pcf {prism_lb:,.0f} + post "
            f"{pier.carried_dead_lb:,.0f} + wall {pier.wall_dead_lb:,.0f}) lb, ASCE 7-16 "
            f"§2.4.1 0.6D + 0.6W; no deck or roof dead credited"))


def _pad_area_ft2(pad) -> float:
    ring = [p.xy_m for p in pad.outline]
    return abs(sum(a[0] * b[1] - b[0] * a[1]
                   for a, b in zip(ring, ring[1:] + ring[:1], strict=False))) / 2.0 / _M_PER_FT ** 2


def _pad_bearing_rows(ctx, bases, piers, overturning, states, missing) -> None:
    """The compression chord's pad, ASCE 7-16 §2.4.1 D + 0.75L + 0.75S + 0.75(0.6W) (review
    C-6): gravity plus the overturning couple, gross on the pad against the presumptive
    allowable (IBC Table 1806.2). The gravity-only case is ``structural.deck_footing_size``'s."""
    from typehaus.engineering.soil import CONCRETE_UNIT_WEIGHT_PCF, presumptive
    from typehaus.model.structure import Pad

    soil = presumptive(getattr(ctx, "soil_class", None), basis=getattr(ctx, "soil_basis", None))
    for tag in sorted({t for b in bases for t in b.connects if t in piers}):
        pier = piers[tag]
        pad = ctx.plan.by_tag(getattr(ctx.plan.by_tag(tag), "supported_by", "") or "")
        if soil is None or not isinstance(pad, Pad):
            missing.append(f"a soil class and the pad under {tag}, for its bearing row")
            continue
        area = _pad_area_ft2(pad)
        pad_lb = area * pad.thickness.inches / 12.0 * CONCRETE_UNIT_WEIGHT_PCF
        load = pier.dead_lb + pad_lb + 0.75 * pier.live_lb + 0.75 * overturning
        states.append(LimitState(
            f"{pad.tag} bearing under the compression chord", load / area,
            soil.allowable_bearing_psf, "psf",
            f"(D {pier.dead_lb:,.0f} + pad {pad_lb:,.0f} + 0.75 x L+S {pier.live_lb:,.0f} + "
            f"0.75 x overturning {overturning:,.0f}) lb / {area:.2f} ft2, gross, no displaced "
            f"soil credited; {soil.citation}"))


def _axis_of(ctx, wall) -> str:
    (x0, y0), (x1, y1) = _line(ctx, wall)
    return "y" if abs(y1 - y0) >= abs(x1 - x0) else "x"
