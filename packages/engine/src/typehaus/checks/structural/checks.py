"""Structural checks — table-driven, clearly labeled "advisory, not engineering" (→ 12).

Shares one table module with the framing solver (header sizing); adds I-joist span lookup.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import StructuralRole
from typehaus.resolve.site_earth import site_grade_elevation_m

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

# The o.c. spacing ``_IJOIST_SPAN_FT`` is published at. A floor framed at anything else has
# no row here and reports UNKNOWN rather than borrowing this one.
_IJOIST_TABLE_SPACING_IN = 16.0

# Widest span ``resolve.framing.tables.header_size`` still answers prescriptively (R602.7);
# anything longer is an engineered beam in that table and here.
_PRESCRIPTIVE_HEADER_SPAN_FT = 8.0




@check(Tier.STRUCTURAL, "structural.header_prescriptive")
def header_within_prescriptive(ctx: CheckContext) -> list[Finding]:
    """Flag openings whose header exceeds prescriptive width (needs engineering)."""
    from typehaus.quantities import m

    out: list[Finding] = []
    for op in ctx.model.openings:
        if op.width_m > m(8.0 * 0.3048).meters:  # > 8'
            # An authored Door/DoorType.header_spec IS the engineered beam: the framing
            # solver emits it verbatim, so the opening no longer rides the table at all.
            spec = None
            source = ctx.plan.by_tag(op.tag) if ctx.plan is not None else None
            spec = getattr(source, "header_spec", None)
            if spec is None and source is not None:
                type_ref = getattr(source, "type_ref", None)
                door_type = ctx.plan.by_tag(type_ref) if type_ref else None
                spec = getattr(door_type, "header_spec", None)
            if spec:
                out.append(_advisory(
                    "structural.header_prescriptive",
                    f"opening {op.tag} width {op.width_m*3.281:.1f}' exceeds the "
                    f"prescriptive header table; engineered header authored: {spec}",
                    (op.tag,), Result.PASS))
            else:
                out.append(_advisory(
                    "structural.header_prescriptive",
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
    """Compare resolved interior-floor joist spans against the declared span table.

    Exterior decks are excluded by ``FloorSystem.service``: they carry a different load case
    and are graded against IRC R507 / AWC DCA6 in ``checks/structural/deck.py`` instead.
    """
    from typehaus.model.floors import FloorSystem

    out: list[Finding] = []
    authored = {el.tag: el for el in ctx.plan.all_elements()
                if isinstance(el, FloorSystem)}
    decks = {tag for tag, el in authored.items() if el.service == "deck"}
    floors = [floor for floor in ctx.model.floors if floor.tag not in decks]
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
        # The table above is published at one spacing. Reading the floor's actual o.c. and
        # reporting UNKNOWN off it beats printing 16" over a deck framed at something else:
        # the answer would be wrong in the unconservative direction at a wider spacing.
        spec = authored.get(floor.tag)
        spacing = spec.joists.spacing if spec is not None else None
        spacing_in = spacing.inches if spacing is not None else _IJOIST_TABLE_SPACING_IN
        if abs(spacing_in - _IJOIST_TABLE_SPACING_IN) > 1e-6:
            out.append(Finding(
                severity=Severity.WARN, check_id="structural.ijoist_span",
                message=(f"UNKNOWN — floor {floor.tag} is framed at {spacing_in:.0f}\" o.c. "
                         f"and this table is published only at "
                         f"{_IJOIST_TABLE_SPACING_IN:.0f}\" o.c."),
                element_tags=(floor.tag,), result=Result.UNKNOWN))
            continue
        span_ft = max(member.length_m for member in joists) / 0.3048
        if span_ft > allowable + 1e-6:
            out.append(_advisory(
                "structural.ijoist_span",
                f"floor {floor.tag} {profile} span {span_ft:.1f}' exceeds the "
                f"{allowable:.1f}' table limit at {spacing_in:.0f}\" o.c.",
                (floor.tag,), Result.FAIL,
            ))
        else:
            out.append(_advisory(
                "structural.ijoist_span",
                f"floor {floor.tag} {profile} span {span_ft:.1f}' is within the "
                f"{allowable:.1f}' table limit at {spacing_in:.0f}\" o.c.",
                (floor.tag,), Result.PASS,
            ))
    return out


@check(Tier.STRUCTURAL, "structural.frost_depth")
def footing_frost_depth(ctx: CheckContext) -> list[Finding]:
    """Check resolved footings and pads against the profile frost depth.

    Frost depth is measured **from finished grade**, not from the project datum: the two
    coincide only while ``Site.grade`` is 0. Every sibling grade-dependent rule reads
    ``site.grade``, and this one now does too (via ``site_grade_elevation_m``, which falls
    back to the main-floor datum when the site declares no grade). This deliberately does
    not size foundations or replace engineering; it catches the common omission of a
    shallow detached-structure pad.
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
    grade_m = site_grade_elevation_m(ctx.model)
    shallow = [solid for solid in supports if solid.z0_m > grade_m - minimum_m + 1e-9]
    if shallow:
        return [_advisory(
            "structural.frost_depth",
            f"{solid.tag} base is {(grade_m - solid.z0_m) / 0.0254:.0f}\" below grade; "
            f"{minimum_in:.0f}\" minimum is required by the MN profile",
            (solid.tag,), Result.FAIL,
        ) for solid in shallow]
    return [_advisory(
        "structural.frost_depth",
        f"{len(supports)} resolved footing/pad bases are at least {minimum_in:.0f}\" below grade",
        tuple(solid.tag for solid in supports), Result.PASS,
    )]


def _segment_residue_in(wall: object, module_in: float) -> float:
    """Where a wall segment's stud grid starts, as a residue in inches mod the module.

    The framing solver lays a segment's studs out from **its own start node**
    (``resolve.framing.stud_module`` measures every opening from 0 = that node), so the set
    of stations a window may legally occupy on a wall is a property of that node and not of
    the facade. Two segments are in phase only when their start nodes share this residue; a
    column between storeys needs the same residue, a mirror pair needs residues summing to
    0 mod the module. Reporting it turns "this window is 4" off" into the answer: a facade
    near-miss is almost always an out-of-phase *segment*, which no window move can fix.
    """
    (x0, y0), (x1, y1) = wall.axis  # type: ignore[attr-defined]
    # Project the start node onto the segment's own dominant axis — the direction the grid
    # runs — so the residue is comparable between two segments on the same facade.
    along_m = x0 if abs(x1 - x0) >= abs(y1 - y0) else y0
    return (along_m / 0.0254) % module_in


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
            residue = _segment_residue_in(wall, rules.module_in)
            out.append(_advisory(
                "structural.window_framing_module",
                f"window {opening.tag} is {module.offset_from_ideal_m / 0.0254:.1f}\" off "
                f"its {module.ideal_label} and {break_note}; its host segment "
                f"{wall.tag} lays out from a {residue:.1f}\" residue mod "
                f"{rules.module_in:.0f}\", so the legal stations on it are "
                f"{residue:.1f}\" + n\u00d7{rules.module_in:.0f}\"",
                (opening.tag,), Result.FAIL,
                fix_hint=(f"shift the RO centre onto its {module.ideal_label} so it "
                          f"interrupts {module.minimum_interrupted} stud(s)"
                          f"{header_free_hint}. If the miss is against a window on another "
                          f"segment, move the segment's start NODE instead: the grid is a "
                          f"property of that node, and no window move fixes an out-of-phase "
                          f"segment"),
            ))
    return out
