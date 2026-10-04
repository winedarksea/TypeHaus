"""Pinned 6x6 KDAT roof posts: wet-service column, cap, base and pier anchor.

Oracle: houses/catlin/notes/canopy_garage_diaphragm.md §5a.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
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

KIND = "wood_roof_post"
#: 2: head and base lateral rows in both directions; the panel chords join (2026-09-30).
#: 3: a slat band's outward push on its chords, N-S (2026-10-04).
BASIS_VERSION = "3"
BASIS = ("AWC NDS 2018 Supplement Table 4D, Southern Pine No. 2 timbers, wet-service row; "
         "NDS §3.7 column stability and §3.9 combined stress; ICC-ES ESR-2604 Table 3 "
         "(AC/ACE); ICC-ES ESR-3096 Table 5 (A35); ICC-ES ESR-3050 Table 1 (CBSQ)")
oracled_by(KIND, Oracle(note="canopy_garage_diaphragm.md", section="§5a",
                        test="tests/test_wood_roof_post_calcs.py"),
           Oracle(note="canopy_west_band.md", section="§5",
                  test="tests/test_canopy_west_band_calcs.py"))

# Table 4D explicitly publishes these Southern Pine timber values for WET service.
SIDE_IN = 5.5
FC_WET_PSI = 525.0
FB_WET_PSI = 850.0
EMIN_WET_PSI = 440_000.0
CD_SNOW = 1.15
CD_WIND = 1.60
SAWN_C = 0.8
SLENDERNESS_LIMIT = 50.0
R507_4_HEIGHT_FT = 14.0


def column_stability(length_in: float, fc_star_psi: float) -> tuple[float, float]:
    """NDS §3.7.1.5: (FcE, Cp), K = 1 at pinned head and foot."""
    fce = 0.822 * EMIN_WET_PSI / (length_in / SIDE_IN) ** 2
    ratio = fce / fc_star_psi
    term = (1.0 + ratio) / (2.0 * SAWN_C)
    cp = term - math.sqrt(term ** 2 - ratio / SAWN_C)
    return fce, cp


@dataclass(frozen=True)
class _Case:
    """One wood roof post and what it sees: its drag, and a framed panel's plate, if any."""

    tag: str
    width_ft: float
    length_ft: float
    below: str | None
    pressure_psf: float
    wind: Any
    wall: Any = None


def _posts(ctx: EngineeringContext) -> list[_Case]:
    """Every KDAT post a roof's bearing beam names — pinned posts, and the chords a shear
    panel is framed around (``within_wall``), which the roof's demand leaves out but which
    carry the panel's out-of-plane load and their own ends' reactions all the same."""
    from typehaus.engineering.roof_lateral import bearing_beams, roof_winds
    from typehaus.model.structure import Post
    from typehaus.resolve.framing.profiles import cross_section

    out: dict[str, _Case] = {}
    for wind in roof_winds(ctx).values():
        roof = ctx.plan.by_tag(wind.roof_tag)
        for beam in bearing_beams(ctx, roof):
            for ref in beam.bearing_refs or ():
                post = ctx.plan.by_tag(ref)
                if not isinstance(post, Post) or post.height is None or ref in out \
                        or post.assembly not in _KDAT:
                    continue
                wall = ctx.plan.by_tag(post.within_wall) if post.within_wall else None
                out[ref] = _Case(ref, (cross_section(post.size).width_m or 0.0) / 0.3048,
                                 post.height.inches / 12.0, post.supported_by,
                                 wind.pressure_psf, wind, wall)
    return sorted(out.values(), key=lambda c: c.tag)


_KDAT = {"POST_KDAT", "POST_KDAT_WRAPPED_PVC"}


@keys(KIND)
def enumerate_posts(ctx: EngineeringContext) -> list[str]:
    return [case.tag for case in _posts(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, case) for case in _posts(ctx)]


def _plate_load(ctx: EngineeringContext, case: _Case, header: Any, base_ft: float
                ) -> tuple[float, float, str]:
    """``(P lb, a ft above the base, basis)`` — a framed panel's top-plate reaction.

    The panel spans vertically from its sill to its top plate and the band over it from that
    plate to the header soffit; the plate's line load between the chord faces, half to each
    chord, as a point load at the plate. Taken on the full solid face (the slats are ~50%
    open, so this is the conservative end).
    """
    from typehaus.engineering.lateral_band import _beam_z_ft
    from typehaus.engineering.lateral_lines import panel_chords_ft

    wall = case.wall
    chords = panel_chords_ft(ctx, wall) if wall is not None else None
    if chords is None or wall.top is None or wall.base_elevation is None:
        return 0.0, 0.0, ""
    panel_top = (wall.base_elevation.inches + wall.top.inches) / 12.0
    soffit, _top = _beam_z_ft(header)
    band = max(soffit - panel_top, 0.0)
    clear = chords[0] - case.width_ft
    line = case.pressure_psf * (wall.top.inches / 24.0 + band / 2.0)
    load = line * clear / 2.0
    return load, panel_top - base_ft, (
        f"{wall.tag}'s top plate: {case.pressure_psf:.2f} psf x ({wall.top.inches / 12:.3f}'/2 "
        f"+ {band:.3f}'/2) = {line:.2f} plf over {clear:.3f}' clear, half = {load:.1f} lb at "
        f"+{panel_top:.3f}'")


def _one(ctx: EngineeringContext, case: _Case) -> EngineeringRecord:
    from typehaus.engineering.holdown_anchor import round_pier_anchor
    from typehaus.engineering.holdown_anchor import states as anchor_states
    from typehaus.engineering.lateral_band_slats import band_for_wall
    from typehaus.engineering.lateral_lines import panel_chords_ft, panel_runs_along
    from typehaus.engineering.pier_basis import (
        DECK_DEAD_LOAD_PSF,
        _round_size,
        design_roof_snow_psf,
        roof_tributaries,
    )
    from typehaus.engineering.roof_lateral import bearing_beams
    from typehaus.engineering.wood_roof_post_joints import EndDemands, joint_rows
    from typehaus.hardware.catalog import hardware_by_model
    from typehaus.model.enums import ConnectorKind
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi
    from typehaus.resolve.framing.profiles import cross_section

    element = ctx.plan.by_tag(case.tag)
    header = next((b for b in bearing_beams(ctx, ctx.plan.by_tag(case.wind.roof_tag))
                   if case.tag in (b.bearing_refs or ())), None)
    base = next((e for e in ctx.plan.all_elements()
                 if getattr(e, "kind", None) is ConnectorKind.POST_BASE
                 and case.tag in (getattr(e, "connects", ()) or ())), None)
    pier = ctx.plan.by_tag(case.below or "")
    pier_size = _round_size(getattr(pier, "size", "") or "") if pier else None
    trib = roof_tributaries(ctx)[0].get(case.tag, 0.0)
    missing = [text for ok, text in (
        (element.size == "6x6", f"NDS wet-service values for {element.size!r}"),
        (trib > 0, "a roof tributary on the post"),
        (header is not None, "a roof header bearing on the post"),
        (base is not None and base.elevation is not None, "an authored post base"),
        (pier_size is not None, "a round concrete pier under the base"),
    ) if not ok]
    tags = tuple(t for t in (case.tag, getattr(header, "tag", None), case.below,
                              getattr(base, "tag", None)) if t)
    if missing:
        return _incomplete(case.tag, tags, missing)

    snow, snow_basis = design_roof_snow_psf(ctx)
    length_in = case.length_ft * 12.0
    area = SIDE_IN ** 2
    section_modulus = SIDE_IN ** 3 / 6.0
    # The KDAT material is 600 kg/m³ in the catalog; the actual 5.5-inch square is 7.87 plf.
    weight_plf = 600.0 * (SIDE_IN * 0.0254) ** 2 * 0.3048 * 2.20462262185
    axial = trib * (DECK_DEAD_LOAD_PSF + snow) + weight_plf * case.length_ft
    fc_star = FC_WET_PSI * CD_SNOW
    fce, cp = column_stability(length_in, fc_star)
    fc_prime = fc_star * cp
    fc_actual = axial / area
    drag_plf = case.pressure_psf * case.width_ft
    own_half = drag_plf * case.length_ft / 2.0
    base_ft = base.elevation.inches / 12.0
    plate, a_ft, plate_basis = _plate_load(ctx, case, header, base_ft)
    b_ft = case.length_ft - a_ft
    moment_lb_ft = drag_plf * case.length_ft ** 2 / 8.0
    if plate:
        moment_lb_ft += plate * a_ft * b_ft / case.length_ft
    uplift = max(trib * (case.pressure_psf - 0.6 * DECK_DEAD_LOAD_PSF), 0.0)
    head_uplift = uplift
    couple_note = ""
    push = push_head = push_base = 0.0
    moment_basis = "own drag" + (f" + {plate_basis}" if plate else "")
    chords = panel_chords_ft(ctx, case.wall) if case.wall is not None else None
    if chords is not None:
        axis = "y" if panel_runs_along(ctx, case.wall, "y") else "x"
        shear = case.wind.delivered_lb(axis)
        depth_ft = (cross_section(header.size).depth_m or 0.0) / 0.3048
        couple = shear * depth_ft
        couple_note = (f" plus the band's couple {shear:,.1f} lb x {depth_ft:.3f}' header "
                       f"depth / {chords[0]:.3f}'")
        band = band_for_wall(ctx, case.wall, case.wind.roof_tag, shear)
        if band is not None:
            # The slats' own couple on the header (note §3h); the larger of the two, and
            # nothing favourable credited.
            if band.couple_lb_ft() > couple:
                couple = band.couple_lb_ft()
                couple_note = (f" plus {band.band.tag}'s couple on the header "
                               f"{couple:,.1f} lb-ft / {chords[0]:.3f}'")
            # A compression bay pushes this chord OUTWARD, off the plates, so it spans base
            # to head under the push (note §5b). The N-S case: it does not meet the plate.
            push = band.chord_push_lb()
            a_p = band.mid_band_ft - base_ft
            push_head = push * a_p / case.length_ft
            push_base = push * (case.length_ft - a_p) / case.length_ft
            ns_moment = (drag_plf * case.length_ft ** 2 / 8.0
                         + push * a_p * (case.length_ft - a_p) / case.length_ft)
            if ns_moment > moment_lb_ft:
                moment_lb_ft = ns_moment
                moment_basis = (f"N-S: own drag + {band.band.tag}'s push {push:,.1f} lb at "
                                f"{a_p:.4f}' above the base")
        head_uplift += couple / chords[0]
    fb_actual = moment_lb_ft * 12.0 / section_modulus
    # This exceeds the NDS §3.9 compression-squared term for fc/Fc' < 1 and retains
    # the §3.9 second-order amplification, so it is a conservative uniaxial screen.
    interaction = fc_actual / fc_prime + fb_actual / (FB_WET_PSI * CD_WIND)
    interaction /= 1.0 - fc_actual / fce
    beam_axis = _beam_axis(ctx, header)
    demands = EndDemands(
        head_along=own_half + push_head, base_along=own_half + push_base,
        head_across=own_half + (plate * a_ft / case.length_ft if plate else 0.0),
        base_across=own_half + (plate * b_ft / case.length_ft if plate else 0.0),
        head_uplift=head_uplift, base_uplift=uplift, plate_lb=plate)
    states = [
        LimitState("NDS column slenderness", length_in / SIDE_IN, SLENDERNESS_LIMIT, "",
                   "NDS 2018 §3.7.1.4, pinned K = 1", is_detailing=True),
        LimitState("NDS wet-service axial", axial, fc_prime * area, "lb",
                   f"Table 4D Fc {FC_WET_PSI:g} psi (wet row) x C_D {CD_SNOW:g} x "
                   f"C_P {cp:.3f}; FcE {fce:.0f} psi, D + S ({snow_basis})"),
        LimitState("NDS combined axial and bending", interaction, 1.0, "",
                   f"§3.9 conservative uniaxial screen; axial stress {fc_actual:.1f} psi, "
                   f"moment {moment_lb_ft:.1f} lb-ft ({moment_basis}), bending stress "
                   f"{fb_actual:.1f} psi, wet Fb {FB_WET_PSI:g} x C_D {CD_WIND:g}"),
        LimitState("IRC R507.4 height cross-check", case.length_ft, R507_4_HEIGHT_FT, "ft",
                   "2018 IRC Table R507.4, 6x6; the NDS snow check governs this roof",
                   is_detailing=True),
    ]
    states += joint_rows(ctx, case.tag, beam_axis, demands, missing)
    base_item = hardware_by_model(base.size or "")
    pier_fc = fc_psi(concrete_spec_for(ctx.plan, pier)) or 3000.0
    if not getattr(base_item, "anchorage_in_rating", False):
        anchor = round_pier_anchor(f"{case.tag} base", pier_size[0], pier_fc)
        states += anchor_states(anchor, uplift, own_half,
                                f"net 0.6D + 0.6W uplift {uplift:.1f} lb",
                                f"own post drag {own_half:.1f} lb")
    if missing:
        return _incomplete(case.tag, tags, missing)
    governing = max((s for s in states if not s.is_detailing),
                    key=lambda s: s.demand / s.capacity if s.capacity else float("inf"))
    return EngineeringRecord(
        item_id=item_id(KIND, case.tag), kind=KIND, key=case.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if any(not s.ok for s in states) else Status.OK,
        summary=f"{case.tag}: wet-service 6x6 KDAT, {governing.name} governs at "
                f"{governing.demand / governing.capacity:.2f}",
        inputs=(Quantity("roof_tributary_ft2", trib, "ft2", 0.01),
                Quantity("post_length_in", length_in, "in", 0.01),
                Quantity("pier_fc_psi", pier_fc, "psi", 1.0),
                Quantity("axial_lb", axial, "lb", 1.0),
                Quantity("uplift_lb", uplift, "lb", 1.0),
                Quantity("head_uplift_lb", head_uplift, "lb", 1.0),
                Quantity("plate_load_lb", plate, "lb", 1.0),
                Quantity("band_push_lb", push, "lb", 1.0)),
        limit_states=tuple(states), element_tags=tags,
        notes=(("The PVC wrap is a nonstructural finish. It needs an open, drained base and "
                "an inspectable/removable panel; it contributes no column capacity."
                if element.assembly == "POST_KDAT_WRAPPED_PVC" else
                f"{case.tag} is a chord of {case.wall.tag}; its IN-PLANE hold-down and base "
                f"shear are graded on the lateral_system record, and this one grades its "
                f"out-of-plane (E-W) ends and any band push across it (N-S)."
                if case.wall is not None else ""),
               f"Head uplift is the net roof uplift {uplift:.1f} lb{couple_note}.",
               "DRY SERVICE at every connector: the caps, angles and base are rated for wood "
               "at or under 19% moisture (ESR-2604 §3.2.2, ESR-3050 §4.1). The posts stand "
               "on 1in drained standoffs under the roof; verify MC before the parts go on. "
               "The column itself is graded on the WET row."))


def _beam_axis(ctx: EngineeringContext, beam: Any) -> str:
    ends = [ctx.plan.by_tag(beam.start_node), ctx.plan.by_tag(beam.end_node)]
    (x0, y0), (x1, y1) = (e.position.xy_m for e in ends)
    return "y" if abs(y1 - y0) >= abs(x1 - x0) else "x"


def _incomplete(tag: str, tags: tuple, missing: list[str]) -> EngineeringRecord:
    return EngineeringRecord(item_id=item_id(KIND, tag), kind=KIND, key=tag,
                             basis_version=BASIS_VERSION, basis=BASIS,
                             status=Status.INCOMPLETE,
                             summary=f"{tag}: wood roof post cannot be graded",
                             missing=tuple(missing), element_tags=tags)
