"""``structural.window_framing_module`` — small openings against the stud grid.

The grid arithmetic itself lives in ``_stud_grid.py``, shared with
``structural.door_framing_module``. What stays here is what is specific to a WINDOW:
:func:`_ro_caps`, the ladder that says how wide a rough opening may be before it breaks more
than one stud. That ladder must not be shared — see the note at the top of ``door_module.py``
for the four catlin doors it would falsely accuse.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._stud_grid import (
    module_origin,
    segment_residue_in,
    structure_framing,
    wall_module,
)
from typehaus.findings import Finding, Result
from typehaus.model.enums import StructuralRole


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
    preference house-wide: the solver lays a wall out on the assembly field, so a house
    with one wall off the declared module would otherwise be graded against a grid nobody
    built. ``_ro_caps`` moves the opening ladder with it, since every rung on it is
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
        framing = structure_framing(assembly)
        if framing is None:
            continue  # concrete / masonry openings do not consume stud bays
        # The module the wall is FRAMED on, which halves on a staggered partition — see
        # _stud_grid.wall_module. Reading straight off ``framing.spacing`` disagrees with
        # the solver by a factor of two on a staggered wall.
        module_in = wall_module(framing, rules.module_in)
        spacing = module_in * 0.0254
        stud_in = member_actual(framing.member)[0]
        unbroken_in, nonbearing_in, bearing_in = _ro_caps(rules, module_in, stud_in)
        role = authored.structural_role
        width_in = opening.width_m / 0.0254
        # The stud *body*, not just its centreline, decides whether the RO clears the bay,
        # so the analysis needs the wall's own member thickness.
        phase, origin = module_origin(ctx, wall, framing, spacing)
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
                residue = segment_residue_in(wall, module_in)
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
