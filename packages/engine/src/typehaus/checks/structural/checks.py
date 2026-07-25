"""Structural checks — table-driven, clearly labeled "advisory, not engineering" (→ 12).

Shares one table module with the framing solver (header sizing); adds I-joist span lookup.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import StructuralRole

# Simplified allowable joist spans (ft) at 16" o.c., residential floor (40 psf live).
# I-joists by depth; dimensional lumber per IRC R502.3.1(1), SPF #2.
_IJOIST_SPAN_FT: dict[str, float] = {
    "9.5 I-joist": 15.0,
    "11.875 I-joist": 18.5,
    "14 I-joist": 22.0,
    "16 I-joist": 25.0,
    "2x6": 9.9,
    "2x8": 13.1,
    "2x10": 16.4,
    "2x12": 19.1,
}

# Widest span ``resolve.framing.tables.header_size`` still answers prescriptively (R602.7);
# anything longer is an engineered beam in that table and here.
_PRESCRIPTIVE_HEADER_SPAN_FT = 8.0


def _advisory(cid: str, msg: str, tags: tuple[str, ...], result: Result,
              fix_hint: str | None = None) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid,
                   message=f"[advisory, not engineering] {msg}", element_tags=tags,
                   result=result, fix_hint=fix_hint)


@check(Tier.STRUCTURAL, "structural.header_prescriptive")
def header_within_prescriptive(ctx: CheckContext) -> list[Finding]:
    """Flag openings whose header exceeds prescriptive width (needs engineering)."""
    from typehaus.quantities import m

    out: list[Finding] = []
    for op in ctx.model.openings:
        if op.width_m > m(8.0 * 0.3048).meters:  # > 8'
            out.append(_advisory("structural.header_prescriptive",
                                 f"opening {op.tag} width {op.width_m*3.281:.1f}' exceeds "
                                 "prescriptive header table — requires engineered beam",
                                 (op.tag,), Result.FAIL))
    return out


@check(Tier.STRUCTURAL, "structural.floor_opening_header")
def floor_opening_header_within_prescriptive(ctx: CheckContext) -> list[Finding]:
    """Flag floor-opening headers whose span is past the prescriptive header table.

    ``resolve/floors.py`` sizes an opening header's ply count off that same table and, past
    it, carries the widest multi-ply the catalog stocks so the member is at least drawn at a
    believable size. That is a placeholder for a designed beam, not a substitute for one —
    this is where the drawing set says so. Wall openings are covered by
    ``structural.header_prescriptive``; floor openings had no equivalent.
    """
    from typehaus.quantities import ft, m

    limit = ft(_PRESCRIPTIVE_HEADER_SPAN_FT)
    out: list[Finding] = []
    for floor in ctx.model.floors:
        for member in floor.members:
            if member.category != "header":
                continue
            if m(member.length_m).feet > limit.feet + 1e-9:
                out.append(_advisory(
                    "structural.floor_opening_header",
                    f"floor {floor.tag} opening header {member.child_key} spans "
                    f"{member.length_m / 0.3048:.1f}', past the "
                    f"{_PRESCRIPTIVE_HEADER_SPAN_FT:.0f}' prescriptive table — the emitted "
                    f"{member.profile} is a placeholder for an engineered beam",
                    (floor.tag,), Result.FAIL,
                    fix_hint=("declare a bearing wall or beam under this opening edge, or "
                              "have the header designed"),
                ))
    return out


@check(Tier.STRUCTURAL, "structural.ijoist_span")
def ijoist_span(ctx: CheckContext) -> list[Finding]:
    """Compare resolved I-joist spans against the declared 16-inch-o.c. table."""
    out: list[Finding] = []
    floors = ctx.model.floors
    if not floors:
        out.append(Finding(severity=Severity.WARN, check_id="structural.ijoist_span",
                           message="UNKNOWN — no resolved FloorSystem span to check",
                           result=Result.UNKNOWN))
        return out
    for floor in floors:
        joists = [member for member in floor.members if member.category == "joist"]
        if not joists:
            out.append(Finding(severity=Severity.WARN, check_id="structural.ijoist_span",
                               message=f"UNKNOWN — floor {floor.tag} has no generated joists",
                               element_tags=(floor.tag,), result=Result.UNKNOWN))
            continue
        profile = joists[0].profile
        allowable = _IJOIST_SPAN_FT.get(profile)
        if allowable is None:
            out.append(Finding(severity=Severity.WARN, check_id="structural.ijoist_span",
                               message=f"UNKNOWN — no span-table row for {profile}",
                               element_tags=(floor.tag,), result=Result.UNKNOWN))
            continue
        span_ft = max(member.length_m for member in joists) / 0.3048
        if span_ft > allowable + 1e-6:
            out.append(_advisory(
                "structural.ijoist_span",
                f"floor {floor.tag} {profile} span {span_ft:.1f}' exceeds the "
                f"{allowable:.1f}' table limit at 16\" o.c.", (floor.tag,), Result.FAIL,
            ))
        else:
            out.append(_advisory(
                "structural.ijoist_span",
                f"floor {floor.tag} {profile} span {span_ft:.1f}' is within the "
                f"{allowable:.1f}' table limit at 16\" o.c.", (floor.tag,), Result.PASS,
            ))
    return out


@check(Tier.STRUCTURAL, "structural.frost_depth")
def footing_frost_depth(ctx: CheckContext) -> list[Finding]:
    """Check resolved footings and pads against the profile frost depth.

    The project datum is grade, so a negative solid base is directly comparable to the
    jurisdictional frost depth.  This deliberately does not size foundations or replace
    engineering; it catches the common omission of a shallow detached-structure pad.
    """
    minimum_in = ctx.profile.frost_depth_in
    if minimum_in is None:
        return [Finding(severity=Severity.WARN, check_id="structural.frost_depth",
                        message="UNKNOWN — profile declares no frost depth",
                        result=Result.UNKNOWN)]
    supports = [solid for solid in ctx.model.solids
                if solid.category in ("footing", "pad")]
    if not supports:
        return [Finding(severity=Severity.WARN, check_id="structural.frost_depth",
                        message="UNKNOWN — no resolved footings or pads",
                        result=Result.UNKNOWN)]
    minimum_m = minimum_in * 0.0254
    shallow = [solid for solid in supports if solid.z0_m > -minimum_m + 1e-9]
    if shallow:
        return [_advisory(
            "structural.frost_depth",
            f"{solid.tag} base is {-solid.z0_m / 0.0254:.0f}\" below grade; "
            f"{minimum_in:.0f}\" minimum is required by the MN profile",
            (solid.tag,), Result.FAIL,
        ) for solid in shallow]
    return [_advisory(
        "structural.frost_depth",
        f"{len(supports)} resolved footing/pad bases are at least {minimum_in:.0f}\" below grade",
        tuple(solid.tag for solid in supports), Result.PASS,
    )]


@check(Tier.STRUCTURAL, "structural.window_framing_module")
def window_framing_module(ctx: CheckContext) -> list[Finding]:
    """Keep Catlin's small openings and one-stud breaks on the 16" framing module.

    The interruption arithmetic is the solver's own (``resolve.framing.stud_module``): the
    check and the framing it checks must never disagree about how many studs an opening
    costs.
    """
    from typehaus.model.enums import LayerFunction
    from typehaus.resolve.framing.stud_module import opening_stud_module
    from typehaus.resolve.framing.tables import member_actual

    rules = ctx.preferences.framing
    spacing = rules.module_in * 0.0254
    tolerance = 0.125 * 0.0254
    out: list[Finding] = []
    for opening in ctx.model.openings:
        if opening.is_door or opening.type_ref is None:
            continue
        wall = ctx.model.wall(opening.host_wall)
        authored = ctx.plan.by_tag(opening.host_wall)
        if wall is None or authored is None:
            continue
        structure = next((layer for layer in wall.layers if layer.function == LayerFunction.STRUCTURE.value),
                         None)
        if structure is None or ctx.plan.library.resolve_assembly(wall.assembly) is None:
            continue
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        framing = next((layer.framing for layer in assembly.layers
                        if layer.function is LayerFunction.STRUCTURE), None)
        if framing is None:
            continue  # concrete / masonry openings do not consume stud bays
        role = authored.structural_role
        width_in = opening.width_m / 0.0254
        # The stud *body*, not just its centreline, decides whether the RO clears the bay,
        # so the analysis needs the wall's own member thickness.
        module = opening_stud_module(opening.center_along_m, opening.width_m, spacing,
                                     member_actual(framing.member)[0] * 0.0254)
        break_note = module.describe()
        maximum = (rules.max_window_ro_bearing_in if role is StructuralRole.BEARING
                   else rules.max_window_ro_nonbearing_in)
        if width_in > maximum + 1e-6:
            out.append(_advisory(
                "structural.window_framing_module",
                f"window {opening.tag} RO {width_in:.0f}\" exceeds the {maximum:.0f}\" "
                f"{role.value} framing limit ({break_note})", (opening.tag,), Result.FAIL,
                fix_hint=(f"a {role.value} window this wide needs an engineered header; keep "
                          f"RO <= {maximum:.0f}\" to stay on the prescriptive module"),
            ))
            continue
        # The ideal position is the one that costs the fewest studs: a bay centre for an
        # even count (a <=14" RO that needs no header at all), a stud line for an odd one,
        # which is what keeps the king/jack framing symmetric.
        header_free_hint = (
            " — at or under the declared header-free width, so on its bay centre it would "
            "need no header at all"
            if width_in <= rules.max_window_ro_unbroken_in else "")
        if module.straddles_awkwardly or module.offset_from_ideal_m > tolerance:
            out.append(_advisory(
                "structural.window_framing_module",
                f"window {opening.tag} is {module.offset_from_ideal_m / 0.0254:.1f}\" off "
                f"its {module.ideal_label} and {break_note}; resize/reposition to the "
                f"{rules.module_in:.0f}\" module", (opening.tag,), Result.FAIL,
                fix_hint=(f"shift the RO centre onto its {module.ideal_label} so it "
                          f"interrupts {module.minimum_interrupted} stud(s)"
                          f"{header_free_hint}"),
            ))
    return out
