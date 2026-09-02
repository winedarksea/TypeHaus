"""Structural checks — table-driven, clearly labeled "advisory, not engineering" (→ 12).

Shares one table module with the framing solver (header sizing); adds I-joist span lookup.
"""

from __future__ import annotations

from typehaus.checks._authoring import engineered as _engineered
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.engineering import item_id
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction
from typehaus.model.structure import Footing, FoundationWall

# Simplified allowable joist spans (ft) at 16" o.c., residential floor (40 psf live).
# I-joists by depth; dimensional lumber per IRC R502.3.1(1), SPF #2.
_IJOIST_SPAN_FT: dict[str, float] = {
    "9.5 I-joist": 15.0,
    "11.875 I-joist": 18.5,
    # Same-depth open-web truss, same row: the fabricator's own span table governs at
    # 18'-0" (near the edge of published 11 7/8" open-web tables at L/480 vs the
    # I-joist's L/360), but this table is explicitly advisory, so borrowing the
    # I-joist number here is the honest placeholder until a fabricator table replaces it.
    "11.875 floor truss": 18.5,
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
            # Both branches are engineered work; they differ only in whether anyone has
            # done it. Routing them through the register is what makes the difference
            # visible as a *state* — the authored one PASSes and says AUTHORED, never
            # computed, and both become an item a signoff can cover.
            out.append(_engineered(
                ctx, "structural.header_prescriptive", item_id("header", op.tag),
                f"opening {op.tag} width {op.width_m*3.281:.1f}' exceeds the prescriptive "
                f"header table",
                (op.tag,), code="IRC R602.7", authored=spec,
                fix=None if spec else "author Door.header_spec (or DoorType.header_spec) "
                                     "with the engineered beam"))
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


def _is_frost_insulation(ctx: CheckContext, assembly_tag: str | None) -> bool:
    """Is this assembly a *frost-protection* element rather than a floor?

    R403.3's whole mechanism is a skirt of rigid foam laid out from the foundation, keeping
    the ground under the footing above freezing. Drawn, that is a thin horizontal element of
    nothing but insulation. A slab with a STRUCTURE layer is a floor, whatever else it
    carries, and a floor is not what R403.3 is talking about.
    """
    if not assembly_tag:
        return False
    assembly = ctx.plan.library.resolve_assembly(assembly_tag)
    if assembly is None or assembly.role != "band":
        return False
    return any(layer.function is LayerFunction.INSULATION for layer in assembly.layers)


def _frost_protection_footprints(ctx: CheckContext) -> list[tuple[str, object]]:
    """``(tag, plan polygon)`` for every drawn horizontal frost-protection element."""
    from shapely.geometry import Polygon

    out: list[tuple[str, object]] = []
    for solid in ctx.model.solids:
        if solid.category != "slab" or len(solid.outline) < 3:
            continue
        if not _is_frost_insulation(ctx, solid.assembly):
            continue
        polygon = Polygon(solid.outline)
        if polygon.is_valid and polygon.area > 0.0:
            out.append((solid.tag, polygon))
    return out


@check(Tier.STRUCTURAL, "structural.frost_depth")
def footing_frost_depth(ctx: CheckContext) -> list[Finding]:
    """Check resolved footings and pads against the profile frost depth.

    Frost depth is measured from **the lowest adjacent finished grade** (IRC R403.1.4.1),
    which is not the same thing as the site's grade plane. This check compared every
    footing in the model to one global scalar (``Site.grade``) for as long as it existed,
    and that is exactly the reading that cannot see an excavation: dig an open sunken court
    6'-6" into the site beside the house and the footings along it keep being graded against
    the plane 6'-6" overhead, so a strip with 8" of cover — and a plinth whose bottom is 2"
    *above* the new ground — both report a comfortable 7'-2" and PASS.

    So the grade is derived per footing now (``resolve.site_earth.local_grade_elevation_m``):
    the site plane, lowered by any *open* excavation floor within a frost depth of it. That
    is a strict refinement — a site with nothing dug beside it gets the same single plane it
    always did, and no existing house moves.

    Four outcomes rather than two, because "shallow" turns out to cover several different
    conditions:

    * **PASS** — full cover below the local grade, or short of it but protected by drawn
      horizontal insulation, which is IRC R403.3's frost-protected shallow foundation.
      The R-values and the B/C dimensions of Table R403.3(1) are the *assembly's* authored
      citation; this check grades that the protection is drawn and adjacent, not that it is
      sized. Saying so is the point — a check that claimed to size an FPSF would be the
      engineering this tier promises it is not doing.
    * **PASS** — short of cover in *concrete*, but bearing on a drained non-frost-
      susceptible section that reaches the required depth on its own. That is soil
      replacement: ASCE 32 counts a well-drained NFS layer's thickness toward the design
      frost depth, and IRC R403.1.4.1 lists a foundation built to ASCE 32 among its
      frost-protection methods. The gradation and the drainage are the ``FootingBedding``'s
      authored claim (``non_frost_susceptible`` + ``drain_tile``); what this check measures
      is that the excavation actually bottoms out a frost depth below the same local grade
      every other branch is measured from.
    * **UNKNOWN** — the footing both stands *inside* the excavation that lowered its own
      grade and carries a ``FoundationWall``. That is a retaining structure holding up the
      hole it sits in, which IRC R404.4 sends to an engineered design rather than to any
      prescriptive table; its frost protection belongs to the same design and to the same
      consultant. Standing inside the hole is not by itself enough to say so: a spread bell
      under a freestanding porch column is in the open court too, and retains nothing, so
      what the footing is authored to be *under* has to agree.
    * **FAIL** — a building footing beside an open excavation, short of cover, with no
      protection drawn.

    Still advisory, and still not sizing foundations.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.site_earth import (
        heated_floor_footprint,
        local_grade_elevation_m,
        open_excavation_floors,
    )

    cid = "structural.frost_depth"
    minimum_in = ctx.profile.frost_depth_in
    if minimum_in is None:
        return [Finding(severity=Severity.WARN, check_id=cid,
                        message="UNKNOWN — profile declares no frost depth",
                        result=Result.UNKNOWN)]
    supports = [solid for solid in ctx.model.solids
                if solid.category in ("footing", "pad")]
    if not supports:
        return [Finding(severity=Severity.WARN, check_id=cid,
                        message="UNKNOWN — no resolved footings or pads",
                        result=Result.UNKNOWN)]
    minimum_m = minimum_in * 0.0254
    # Reach and required depth are the same number on purpose: frost drives into the ground
    # from every exposed face, so the excavation that governs a footing is one within about
    # a frost depth of it, and the insulation that protects it is likewise.
    reach_m = minimum_m
    floors = open_excavation_floors(ctx.model)
    sheltered_by = heated_floor_footprint(ctx.model)
    protection = _frost_protection_footprints(ctx)
    # What each footing is authored to sit *under*, and which of those hosts can retain
    # anything. Built once: both are whole-plan scans and neither depends on the footing.
    supported_host = {el.tag: el.under for el in ctx.plan.all_elements()
                      if isinstance(el, Footing)}
    retaining_hosts = {el.tag for el in ctx.plan.all_elements()
                       if isinstance(el, FoundationWall)}
    bedding_by_host = {bed.host: bed for bed in ctx.model.footing_beddings}

    out: list[Finding] = []
    covered = []
    for solid in sorted(supports, key=lambda item: item.tag):
        grade_m, source_tag = local_grade_elevation_m(
            ctx.model, solid.outline, reach_m, floors, sheltered_by)
        cover_in = (grade_m - solid.z0_m) / 0.0254
        where = f" below {source_tag}" if source_tag else " below grade"
        if cover_in >= minimum_in - 1e-6:
            covered.append(solid)
            continue

        # Soil replacement: the concrete stops short, the stone under it does not. Only a
        # *drained* section counts (ASCE 32 is about a well-drained NFS layer), and only
        # one whose own excavation bottom clears the requirement below the same local
        # grade every other branch here is measured from.
        bed = bedding_by_host.get(solid.tag)
        section_in = ((grade_m - bed.z0_m) / 0.0254) if bed is not None else 0.0
        if (bed is not None and bed.non_frost_susceptible is True and bed.drain_tile
                and section_in >= minimum_in - 1e-6):
            out.append(_advisory(
                cid,
                f"{solid.tag} has {cover_in:.0f}\"{where} against the "
                f"{minimum_in:.0f}\" MN profile minimum, and bears on {bed.tag}, a "
                f"drained non-frost-susceptible section excavated to {section_in:.0f}\" "
                f"below that same grade — the required depth is reached by soil "
                f"replacement (ASCE 32, listed as a frost-protection method by IRC "
                f"R403.1.4.1). That the {bed.aggregate} is non-frost-susceptible and that "
                f"the section drains are the bedding's own authored claim, not this "
                f"check's finding",
                (solid.tag, bed.tag), Result.PASS,
            ))
            continue

        here = Polygon(solid.outline) if len(solid.outline) >= 3 else None
        # Standing in the hole is only half of "retains the hole". A spread bell under a
        # freestanding column sits in the open court at 100% overlap and holds nothing
        # back, so R404.4 has nothing to say about it; what the footing is authored to be
        # under decides. Anything that is not a FoundationWall falls through to the depth
        # branches below rather than being called an engineered retaining structure.
        retains = supported_host.get(solid.tag) in retaining_hosts
        inside = retains and source_tag is not None and here is not None and any(
            tag == source_tag and here.intersection(polygon).area > 1e-6
            for tag, polygon, _z in floors)
        if inside:
            # The demonstration case for the whole engineering register, and the reason it
            # is not a fourth Result. This message already said, in prose, that the frost
            # protection "belongs to that engineered design" — and had no way to point at
            # one, so it hard-coded UNKNOWN. It now delegates to the very same item id
            # `structural.foundation_unbalanced_fill` delegates to: one engineer's design
            # over the sunken-garden walls answers both checks, across three walls and the
            # footings under them, with one stamp and one fingerprint.
            host = supported_host.get(solid.tag)
            out.append(_engineered(
                ctx, cid, item_id("retaining_wall", host),
                f"{solid.tag} carries {host} inside the {source_tag} excavation with "
                f"{cover_in:.0f}\" of cover against the {minimum_in:.0f}\" MN profile "
                f"minimum; a structure retaining the excavation it sits in is outside the "
                f"prescriptive path (IRC R404.4) and its frost protection belongs to that "
                f"engineered design",
                (solid.tag,) + ((source_tag,) if source_tag else ()),
                code="IRC R404.4",
                # This rule grades frost cover; the shared item's calculation grades
                # sliding, overturning and bearing. Sharing the item is the point — one
                # design, one stamp, two checks — but inheriting its verdict would let a
                # sliding deficiency be reported as a frost failure, and this check does
                # not get to call an engineered wall non-compliant, only unevaluated.
                defer=True,
            ))
            continue

        shielding = [tag for tag, polygon in protection
                     if here is not None and here.distance(polygon) <= reach_m + 1e-9]
        if shielding:
            out.append(_advisory(
                cid,
                f"{solid.tag} has {cover_in:.0f}\"{where} against the "
                f"{minimum_in:.0f}\" MN profile minimum, and is frost-protected by "
                f"{', '.join(sorted(shielding))} — IRC R403.3, whose Table R403.3(1) "
                f"R-values and B/C dimensions are the insulation assembly's own sourced "
                f"citation, not this check's finding",
                (solid.tag, *sorted(shielding)), Result.PASS,
            ))
            continue

        out.append(_advisory(
            cid,
            f"{solid.tag} base is {cover_in:.0f}\"{where}; {minimum_in:.0f}\" minimum is "
            f"required by the MN profile"
            + ("" if source_tag is None else
               f" — measured from the lowest adjacent grade (IRC R403.1.4.1), which here is "
               f"the floor of the {source_tag} excavation, not the site grade plane"),
            (solid.tag,) + ((source_tag,) if source_tag else ()), Result.FAIL,
        ))

    if covered:
        out.append(_advisory(
            cid,
            f"{len(covered)} resolved footing/pad bases are at least {minimum_in:.0f}\" "
            f"below their lowest adjacent grade",
            tuple(solid.tag for solid in covered), Result.PASS,
        ))
    return out


#: ``FramingPreferences.corner`` -> how many supplemental corner studs that style builds.
_CORNER_STYLE_STUD_COUNT = {"3-stud": 1, "4-stud": 2}


@check(Tier.STRUCTURAL, "structural.corner_style_matches_preference")
def corner_style_matches_preference(ctx: CheckContext) -> list[Finding]:
    """Every corner an assembly declares at the house's own style, BUILT that way.

    ``preferences.toml``'s ``[framing] corner`` is the one place a house states its corner
    style once; nothing else compares it to what the solver actually built, so an override
    that never took effect (e.g. ``corner_style_end="4-stud"`` shipping zero 4-stud corners)
    would otherwise go unnoticed.

    Scoped to walls whose own STRUCTURE ``FramingSpec.corner_style`` already matches the
    declared preference: a wall on a *different* assembly-declared style (the freestanding
    garage's 3-stud walls, while the house's own exterior is 4-stud) is a deliberate,
    per-assembly choice this rule has nothing to say about — comparing every corner in the
    house against one house-wide number would flag that legitimate divergence as though it
    were the same authoring bug. Comparing against ``preferences.toml`` rather than
    re-deriving "what should be built" from the solver's own corner-style resolution is the
    whole point: an independent, human-authored statement is the one thing immune to a bug
    *in* that resolution, which is what let the original four overrides go unnoticed.
    """
    from typehaus.resolve.framing.corners import corner_junctions

    rules = ctx.preferences.framing
    expected = _CORNER_STYLE_STUD_COUNT.get(rules.corner)
    if expected is None:
        return [_advisory(
            "structural.corner_style_matches_preference",
            f"preferences.toml [framing] corner = {rules.corner!r} is not a style the "
            "framing solver speaks (\"3-stud\" or \"4-stud\")",
            (), Result.UNKNOWN,
            fix_hint="set [framing] corner to \"3-stud\" or \"4-stud\"",
        )]
    corners = corner_junctions(ctx.model)
    out: list[Finding] = []
    for wall_tag, endpoints in sorted(corners.owner.items()):
        wall = ctx.model.wall(wall_tag)
        authored = ctx.plan.by_tag(wall_tag)
        if wall is None or authored is None:
            continue
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        spec = next((ly.framing for ly in (assembly.layers if assembly else ())
                    if ly.function is LayerFunction.STRUCTURE), None)
        if spec is None or spec.corner_style != rules.corner:
            continue
        # A course of lumber laid flat frames no studs, so "how many SUPPLEMENTAL corner
        # studs did this end build" has no answer for it — the corner there is a plate lap,
        # which `_append_plates` already resolves by the same rule every sole plate uses.
        # Such a wall still declares a corner_style (the junction solver wants one rule at
        # a node where a plate meets a stud wall, not two that disagree), so it reaches this
        # loop; it is scoped out here rather than being told to build studs it has none of.
        if spec.wall_frame != "studs":
            continue
        for endpoint in sorted(endpoints):
            built = sum(1 for m in wall.members
                       if m.category == "corner"
                       and m.child_key.startswith(f"corner-{endpoint}"))
            if built != expected:
                out.append(_advisory(
                    "structural.corner_style_matches_preference",
                    f"{wall_tag} {endpoint}: built {built} supplemental corner stud(s), "
                    f"preferences.toml declares corner = {rules.corner!r} "
                    f"({expected} expected)",
                    (wall_tag,), Result.FAIL,
                    fix_hint="match the declared style to what is built: update "
                             "preferences.toml's [framing] corner, or the assembly's "
                             "FramingSpec.corner_style / this end's corner_style_"
                             f"{endpoint}",
                ))
    return out
