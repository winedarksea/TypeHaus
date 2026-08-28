"""``structural.window_framing_module`` — small openings against the stud grid.

Split out of ``checks.py`` on 2026-08-28 when the rule stopped being one function: reading
the *host wall's* own module instead of the house preference brought the RO ladder's own
arithmetic (:func:`_ro_caps`) with it, and the file was already over the 500-line bound.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import StructuralRole


def _segment_residue_in(wall: object, module_in: float) -> float:
    """Where a wall segment's stud grid starts, as a residue in inches mod the module.

    The framing solver lays a segment's studs out from **its own start node**
    (``resolve.framing.stud_module`` measures every opening from 0 = that node), so the set
    of stations a window may legally occupy on a wall is a property of that node and not of
    the facade. Two segments are in phase only when their start nodes share this residue; a
    column between storeys needs the same residue, a mirror pair needs residues summing to
    0 mod the module. Reporting it turns "this window is 4" off" into the answer: a facade
    near-miss is almost always an out-of-phase *segment*, which no window move can fix.

    True only while the assembly lays out from the wall — see :func:`_module_origin`, which
    is what an opt-in ``FramingSpec.layout_origin="line"`` changes and which this check must
    follow, or it would report legal stations the solver does not frame.
    """
    (x0, y0), (x1, y1) = wall.axis  # type: ignore[attr-defined]
    # Project the start node onto the segment's own dominant axis — the direction the grid
    # runs — so the residue is comparable between two segments on the same facade.
    along_m = x0 if abs(x1 - x0) >= abs(y1 - y0) else y0
    return (along_m / 0.0254) % module_in


def _module_origin(ctx, wall, framing, spacing_m: float) -> tuple[float, str]:
    """``(phase in metres, how to describe it)`` for this wall's stud grid.

    The framing solver's own arithmetic, asked the same question — the check and the framing
    it checks must never disagree about where the studs are.
    """
    from typehaus.resolve.layout_lines import layout_phase, lines_by_wall

    line = lines_by_wall(ctx.model.layout_lines).get(wall.tag)
    phase = layout_phase(framing, line, wall.tag, spacing_m)
    if getattr(framing, "layout_origin", "wall-start") != "line" or line is None:
        return phase, "segment"
    return phase, line.tag


def _ro_caps(rules, module_in: float, stud_in: float) -> tuple[float, float, float]:
    """``(unbroken, nonbearing, bearing)`` RO caps in inches at *this wall's* module.

    ``preferences.toml`` authors the ladder once, at the house's declared module, and its
    own comment gives the arithmetic behind each rung: one clear bay (module less a stud),
    two bays less the broken stud, and that again less a jack each side. A wall framed on a
    different ``FramingSpec.spacing`` is the SAME rule at a different module, so the rungs
    are re-derived from the geometry rather than a second ladder being authored — a 24"
    o.c. wall's unbroken bay is 22.5" and its nonbearing cap 46.5", and no preference file
    can know that in advance.

    The authored numbers are the geometric ones rounded down to something a window
    schedule can say (14.5 -> 14, 30.5 -> 30, 27.5 -> 27), so that rounding is carried
    across as a per-rung offset instead of being re-invented. At the declared module this
    returns the authored values unchanged, which is what keeps a 16" house's results
    identical.
    """
    def rungs(module: float) -> tuple[float, float, float]:
        unbroken = module - stud_in
        nonbearing = 2.0 * module - stud_in
        return unbroken, nonbearing, nonbearing - 2.0 * stud_in

    authored = (rules.max_window_ro_unbroken_in, rules.max_window_ro_nonbearing_in,
                rules.max_window_ro_bearing_in)
    if abs(module_in - rules.module_in) <= 1e-6:
        return authored
    declared = rungs(rules.module_in)
    here = rungs(module_in)
    shifted = [h - (d - a) for h, d, a in zip(here, declared, authored, strict=True)]
    return shifted[0], shifted[1], shifted[2]


@check(Tier.STRUCTURAL, "structural.window_framing_module")
def window_framing_module(ctx: CheckContext) -> list[Finding]:
    """Keep small openings and one-stud breaks on their host wall's framing module.

    The interruption arithmetic is the solver's own (``resolve.framing.stud_module``): the
    check and the framing it checks must never disagree about how many studs an opening
    costs. That is also why the module read here is the wall's own STRUCTURE
    ``FramingSpec.spacing`` with ``preferences.toml``'s as the fallback, and not the
    preference house-wide: the solver has always laid a wall out on the assembly field, so
    a house with one wall off the declared module was being graded against a grid nobody
    built. The two agreed only while every spacing in the house was 16" (fixed
    2026-08-28); ``_ro_caps`` moves the opening ladder with it, since every rung on it is
    arithmetic on the module.
    """
    from typehaus.model.enums import LayerFunction
    from typehaus.resolve.framing.stud_module import opening_stud_module
    from typehaus.resolve.framing.tables import member_actual

    rules = ctx.preferences.framing
    tolerance = 0.125 * 0.0254
    out: list[Finding] = []
    for opening in ctx.model.openings:
        if opening.is_door or opening.type_ref is None:
            continue
        wall = ctx.model.wall(opening.host_wall)
        authored = ctx.plan.by_tag(opening.host_wall)
        if wall is None or authored is None:
            continue
        structure = next((layer for layer in wall.layers
                          if layer.function == LayerFunction.STRUCTURE.value), None)
        if structure is None or ctx.plan.library.resolve_assembly(wall.assembly) is None:
            continue
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        framing = next((layer.framing for layer in assembly.layers
                        if layer.function is LayerFunction.STRUCTURE), None)
        if framing is None:
            continue  # concrete / masonry openings do not consume stud bays
        module_in = (framing.spacing.inches if framing.spacing is not None
                     else rules.module_in)
        spacing = module_in * 0.0254
        stud_in = member_actual(framing.member)[0]
        unbroken_in, nonbearing_in, bearing_in = _ro_caps(rules, module_in, stud_in)
        role = authored.structural_role
        width_in = opening.width_m / 0.0254
        # The stud *body*, not just its centreline, decides whether the RO clears the bay,
        # so the analysis needs the wall's own member thickness.
        phase, origin = _module_origin(ctx, wall, framing, spacing)
        module = opening_stud_module(opening.center_along_m, opening.width_m, spacing,
                                     stud_in * 0.0254, phase)
        break_note = module.describe()
        maximum = (bearing_in if role is StructuralRole.BEARING else nonbearing_in)
        if width_in > maximum + 1e-6:
            out.append(_advisory(
                "structural.window_framing_module",
                f"window {opening.tag} RO {width_in:.0f}\" exceeds the {maximum:.0f}\" "
                f"{role.value} framing limit ({break_note})", (opening.tag,), Result.FAIL,
                fix_hint=(
                    f"keep RO <= {maximum:.0f}\" so the opening breaks ONE stud line on the "
                    f"{module_in:.0f}\" module this wall is framed on. The bearing cap is "
                    f"just the nonbearing one ({nonbearing_in:.0f}\") less a jack each "
                    f"side, because a BEARING header lands "
                    f"on a jack at each end (R602.7.5) where a NONBEARING one need not "
                    f"(R602.7.4 allows a flat 2x4 nailed to the stud each side). If this "
                    f"width is carrying a glazing-AREA requirement, buy the area back in "
                    f"HEIGHT rather than raising the cap"),
            ))
            continue
        # The ideal position is the one that costs the fewest studs: a bay centre for an
        # even count (a <=14" RO that needs no header at all), a stud line for an odd one,
        # which is what keeps the king/jack framing symmetric.
        header_free_hint = (
            " — at or under the declared header-free width, so on its bay centre it would "
            "need no header at all"
            if width_in <= unbroken_in else "")
        if module.straddles_awkwardly or module.offset_from_ideal_m > tolerance:
            if origin == "segment":
                residue = _segment_residue_in(wall, module_in)
                where = (f"its host segment {wall.tag} lays out from a {residue:.1f}\" "
                         f"residue mod {module_in:.0f}\"")
                hint_tail = ("If the miss is against a window on another segment, move the "
                             "segment's start NODE instead: the grid is a property of that "
                             "node, and no window move fixes an out-of-phase segment")
            else:
                residue = phase / 0.0254
                where = (f"its host segment {wall.tag} lays out from layout line {origin} "
                         f"and reaches the module {residue:.1f}\" along itself")
                hint_tail = ("The grid here is the LINE's, shared with every wall on it, so "
                             "moving this segment's node moves nothing — shift the RO")
            out.append(_advisory(
                "structural.window_framing_module",
                f"window {opening.tag} is {module.offset_from_ideal_m / 0.0254:.1f}\" off "
                f"its {module.ideal_label} and {break_note}; {where}, so the legal "
                f"stations on it are {residue:.1f}\" + n\u00d7{module_in:.0f}\"",
                (opening.tag,), Result.FAIL,
                fix_hint=(f"shift the RO centre onto its {module.ideal_label} so it "
                          f"interrupts {module.minimum_interrupted} stud(s)"
                          f"{header_free_hint}. {hint_tail}"),
            ))
    return out
