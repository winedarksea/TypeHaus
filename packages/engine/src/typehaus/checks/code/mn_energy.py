"""MN climate-zone-6 prescriptive envelope check (→ Permit-ready plan set Phase 7).

``evaluate_envelope`` is the pure analysis both the check and the EN-1 sheet consume (the
same "one function, two consumers" shape as ``analyze_wwr``/``estimate_block_load``).
Per-assembly rows are tri-state: an assembly with ``unknown_materials`` (missing
``r_per_inch``) surfaces UNKNOWN, never a silent PASS — the honest-EN-1 point of this phase.
A component only earns a row when the prescriptive table actually binds it: interior
partitions/floors between two conditioned spaces and freestanding unconditioned structures
are scoped out rather than reported as failures they are not.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.analysis import assembly_r_value
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.energy import _storey_is_conditioned
from typehaus.findings import Finding, Result, Severity
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.roof_edge_geometry import skin_layers


@dataclass(frozen=True)
class PrescriptiveEnvelope:
    """MN 2024 Residential Code, IRC Table N1102.1.2, climate zone 6 (Minnesota)."""

    ceiling_r: float = 49.0
    wood_wall_r: float = 21.0
    floor_r: float = 30.0
    basement_wall_r: float = 15.0
    slab_r: float = 10.0
    window_u_max: float = 0.32


MN_ZONE_6 = PrescriptiveEnvelope()


@dataclass(frozen=True)
class PrescriptiveRow:
    """One EN-1 table row: a component checked against its MN zone-6 requirement."""

    component: str  # tag (assembly or window type)
    role: str  # "roof" | "above-grade wall" | "foundation wall" | "slab" | "window"
    required: str  # "R-49" | "U-0.32"
    provided: str  # "R-95.2" | "UNKNOWN (missing r_per_inch: ...)"
    verdict: str  # "pass" | "fail" | "unknown"




def _walls_bounding_conditioned_space(model: ResolvedModel) -> frozenset[str]:
    """Uids of the walls that actually enclose conditioned space.

    This was a tag-prefix list — ``("W-SG-", "W-RG-")`` — i.e. one house's naming convention
    compiled into the engine's Minnesota energy check. Any other house's porch walls were
    checked against R-21 and failed, and renaming catlin's would have silently changed the
    result. The relation is derivable: a wall is part of the thermal envelope when it runs
    along the boundary of a conditioned room on its own storey, which is what the freestanding
    porch, retaining, planter, and detached-garage walls do not do.
    """
    from shapely.geometry import LineString, Polygon

    rooms: dict[str, list[Polygon]] = {}
    for room in model.rooms:
        if room.conditioned and len(room.clear_face) >= 3:
            rooms.setdefault(room.storey, []).append(Polygon(room.clear_face))
    bounding: set[str] = set()
    for wall in model.walls:
        axis = LineString(wall.axis)
        # The room polygon is the *interior face*, so a bounding wall sits about half its
        # thickness away from it; the tolerance absorbs lining/junction resolution.
        reach = wall.thickness_m / 2 + _ENVELOPE_ADJACENCY_TOLERANCE_M
        if any(axis.distance(poly) <= reach for poly in rooms.get(wall.storey, ())):
            bounding.add(wall.uid)
    return frozenset(bounding)


# How far a wall axis may sit from a conditioned room's interior face and still be that
# room's enclosure, beyond the wall's own half-thickness.
_ENVELOPE_ADJACENCY_TOLERANCE_M = 0.05


# Tag prefixes of slabs belonging to a freestanding structure that is not part of the
# conditioned envelope, but which are filed on one of the house's own storey keys because
# they share the plan frame (→ Phase 2's sleeve check hit the same "one storey key, several
# physical structures" seam). ``_storey_is_conditioned`` therefore cannot see past them.
_FREESTANDING_SLAB_PREFIXES = (
    # The sunken-garden structure's decks: the porch composite deck and the balcony aluminum
    # deck are exterior walking surfaces over open air, not thermal-envelope floors.
    "SL-SG-",
    # The detached garage's slab-on-grade. Its storey datum is the ICF stem top, so the slab
    # is filed on "main"; the same structure's GARAGE_ROOF/GARAGE_WALL_2X6 are already
    # excluded here by RM-GARAGE's ``conditioned=False``, and its floor is no different.
    "SL-G-",
    # The breezeway's composite decking. It is an unheated exterior walking surface on
    # joists over open air between two structures, filed on "main" because that is the datum
    # its joists top out at — no more a thermal-envelope slab than the porch deck above.
    "SL-BW-",
    # The north-side heat-pump equipment pad (catlin's SL-M-HP3PAD, params/hp3_pad.py). It
    # is filed on "main" because that is the plan frame, but it is a 6.9 sf pour on grade in
    # the yard slot carrying an outdoor condenser on 18" legs — nothing above it is
    # conditioned, and there is no envelope for an R-10 slab edge to belong to. Named in
    # full rather than by a family prefix: it is one pad, not a zone, and "SL-M-" is the
    # house's own storey key.
    "SL-M-HP3PAD",
)


def _is_freestanding_exterior_slab(tag: str) -> bool:
    """Whether a slab floors a freestanding structure outside the conditioned envelope, so
    the R-10 slab minimum does not bind it.

    Slabs carry no room-adjacency relation to derive this from the way walls do (→
    ``_walls_bounding_conditioned_space``), so this one is still a naming convention."""
    return tag.startswith(_FREESTANDING_SLAB_PREFIXES)


def _carries_a_weather_skin(wall: ResolvedWall) -> bool:
    """Whether this wall has an outboard side for the prescriptive table to bind.

    ``_walls_bounding_conditioned_space`` asks a PLAN question — does this wall run along a
    conditioned room's boundary — and that is the right question for a wall. It is the
    wrong one for a bearing element that is not a wall in the enclosure sense: a 2x plate
    laid flat on a deck under a story-and-a-half roof runs along the room's edge and
    encloses nothing, because there is no sheathing, no foam and no cladding on it. The
    thermal envelope at that line runs from the wall BELOW the plate up to the roof
    ABOVE it, and the plate sits inside both.

    Grading such a course against R-21 is a category error, and it is the same category
    error whichever way it is dressed: a bare plate cannot reach R-21 at any thickness,
    so the row is a permanent FAIL that says nothing about the building.

    The signal is the one ``resolve/roof_edge.py`` and ``resolve/envelope.py`` already use
    for exactly this element — an empty ``skin_layers()``, i.e. no SHEATHING layer and so
    nothing outboard of one. A wall with a skin is checked as it always was; this only
    reaches the framing courses. Note that a *forgotten* cladding is not silently excused:
    an assembly with a SHEATHING layer and nothing over it still carries a skin and still
    earns its row.
    """
    return bool(skin_layers(wall))


def _is_interior_assembly(tag: str) -> bool:
    """Interior partitions/cross-walls carry no prescriptive R-value requirement — they
    aren't part of the thermal envelope. This codebase's own naming convention already
    marks them with an "INT" token (FOUNDATION_WALL_12_INT, INT_2X6_PLUMBING, ...); the IFC
    emitter's ``Pset_WallCommon.IsExternal`` uses the same signal on the wall tag."""
    return "INT" in tag.split("_")


def _row_for_assembly(plan: PlanModel, tag: str, role: str, required_r: float) -> PrescriptiveRow:
    assembly = plan.library.resolve_assembly(tag)
    if assembly is None:
        return PrescriptiveRow(tag, role, f"R-{required_r:.0f}",
                               f"UNKNOWN (assembly {tag} not found)", "unknown")
    result = assembly_r_value(assembly, plan.library)
    if result.value is None:
        return PrescriptiveRow(tag, role, f"R-{required_r:.0f}", result.fmt(), "unknown")
    r = result.value.r_us
    verdict = "pass" if r + 1e-6 >= required_r else "fail"
    return PrescriptiveRow(tag, role, f"R-{required_r:.0f}", f"R-{r:.1f}", verdict)


def evaluate_envelope(model: ResolvedModel, plan: PlanModel,
                      envelope: PrescriptiveEnvelope = MN_ZONE_6) -> list[PrescriptiveRow]:
    """Classify every roof/wall/slab assembly + window type and check it against the MN
    zone-6 prescriptive table. Pure — no Findings, no CheckContext; the check below and
    the EN-1 sheet both consume this directly."""
    rows: list[PrescriptiveRow] = []

    for tag in sorted({roof.assembly for roof in model.roofs
                       if _storey_is_conditioned(plan, roof.storey)}):
        rows.append(_row_for_assembly(plan, tag, "roof", envelope.ceiling_r))
    envelope_walls = _walls_bounding_conditioned_space(model)
    for tag in sorted({w.assembly for w in model.walls
                       if not w.is_foundation and w.uid in envelope_walls
                       and _carries_a_weather_skin(w)}):
        if _is_interior_assembly(tag):
            continue
        rows.append(_row_for_assembly(plan, tag, "above-grade wall", envelope.wood_wall_r))
    for tag in sorted({w.assembly for w in model.walls
                       if w.is_foundation and w.uid in envelope_walls}):
        if _is_interior_assembly(tag):
            continue
        rows.append(_row_for_assembly(plan, tag, "foundation wall", envelope.basement_wall_r))
    for slab in sorted((s for s in model.solids if s.category == "slab"
                       and _storey_is_conditioned(plan, s.storey)
                       and not _is_freestanding_exterior_slab(s.tag)), key=lambda s: s.tag):
        if slab.assembly is None:
            rows.append(PrescriptiveRow(slab.tag, "slab", f"R-{envelope.slab_r:.0f}",
                                        "UNKNOWN (no assembly authored)", "unknown"))
            continue
        # A slab between two conditioned storeys is an interior floor, not an envelope
        # element — catlin's 9" main-floor deck has conditioned basement below and
        # conditioned living space above. Same "INT" naming signal the wall loops use.
        if _is_interior_assembly(slab.assembly):
            continue
        row = _row_for_assembly(plan, slab.assembly, "slab", envelope.slab_r)
        rows.append(PrescriptiveRow(slab.tag, row.role, row.required, row.provided,
                                    row.verdict))

    for window_type in plan.library.window_types:
        if window_type.u_factor is None:
            rows.append(PrescriptiveRow(window_type.tag, "window",
                                        f"U-{envelope.window_u_max:.2f}", "UNKNOWN (no U-factor)",
                                        "unknown"))
            continue
        u = window_type.u_factor.u_us
        verdict = "pass" if u <= envelope.window_u_max + 1e-6 else "fail"
        rows.append(PrescriptiveRow(window_type.tag, "window", f"U-{envelope.window_u_max:.2f}",
                                    f"U-{u:.2f}", verdict))
    return rows


_PRESCRIPTIVE_REF = "N1102.1.2"


def _to_finding(row: PrescriptiveRow) -> Finding:
    message = f"{row.role} {row.component}: {row.provided} vs. {row.required} required"
    if row.verdict == "unknown":
        return Finding(severity=Severity.WARN, check_id="code.energy_prescriptive",
                       message=f"UNKNOWN — {row.role} {row.component} {row.provided}",
                       element_tags=(row.component,), code_ref=_PRESCRIPTIVE_REF,
                       result=Result.UNKNOWN)
    if row.verdict == "pass":
        return Finding(severity=Severity.WARN, check_id="code.energy_prescriptive",
                       message=message, element_tags=(row.component,),
                       code_ref=_PRESCRIPTIVE_REF, result=Result.PASS)
    return Finding(severity=Severity.ERROR, check_id="code.energy_prescriptive", message=message,
                   element_tags=(row.component,), code_ref=_PRESCRIPTIVE_REF,
                   result=Result.FAIL)


@check(Tier.CODE, "code.energy_prescriptive")
def energy_prescriptive(ctx: CheckContext) -> list[Finding]:
    """Check the envelope against *this jurisdiction's* prescriptive table.

    The table is read off the profile rather than assumed: a profile that states no climate
    zone gets an honest UNKNOWN, not Minnesota's numbers applied to someone else's house.
    """
    envelope = ctx.profile.climate
    if envelope is None:
        return [Finding(
            severity=Severity.WARN, check_id="code.energy_prescriptive",
            message=(f"UNKNOWN — profile {ctx.profile.name} states no prescriptive envelope "
                     "table, so no component requirement can be evaluated"),
            code_ref=_PRESCRIPTIVE_REF, result=Result.UNKNOWN,
        )]
    return [_to_finding(row) for row in evaluate_envelope(ctx.model, ctx.plan, envelope)]


# N1102.4.1.2 (MN Rules 1322): the blower-door result must not exceed 3.0 air changes per
# hour at 50 Pa. Minnesota amends the IRC's climate-zone table to a flat 3.0 statewide.
_MAX_ACH50 = 3.0
_AIR_LEAKAGE_REF = "N1102.4.1.2"


@check(Tier.CODE, "code.N1102_4_air_leakage")
def air_leakage(ctx: CheckContext) -> list[Finding]:
    """N1102.4.1.2 — envelope air leakage at or under 3.0 ACH50.

    This is the one energy requirement with a *test* behind it rather than a table lookup,
    and the number is already authored: ``preferences.ach50`` (or ``cfm50``, which wins
    when both are present because a test report states CFM50 and the ACH50 is derived from
    it — see the Preferences docstring).

    Deriving ACH50 from CFM50 needs the conditioned volume, which this engine does not
    resolve as a single figure. So a house that states only ``cfm50`` reports UNKNOWN with
    that reason rather than a volume guess: the whole point of a blower-door number is that
    it is measured.
    """
    cid = "code.N1102_4_air_leakage"
    prefs = ctx.preferences
    if prefs.cfm50 is not None and prefs.ach50 is None:
        return [Finding(
            severity=Severity.WARN, check_id=cid, code_ref=_AIR_LEAKAGE_REF,
            message=(f"UNKNOWN — the house states cfm50 = {prefs.cfm50:g} but no ach50, and "
                     "converting between them needs a conditioned volume this engine does "
                     "not resolve"),
            result=Result.UNKNOWN)]
    if prefs.ach50 is None:
        return [Finding(
            severity=Severity.WARN, check_id=cid, code_ref=_AIR_LEAKAGE_REF,
            message=("UNKNOWN — no blower-door result authored ([envelope].ach50 in "
                     f"preferences.toml); N1102.4.1.2 requires {_MAX_ACH50:g} ACH50 or less"),
            result=Result.UNKNOWN)]
    if prefs.ach50 > _MAX_ACH50 + 1e-9:
        return [Finding(
            severity=Severity.ERROR, check_id=cid, code_ref=_AIR_LEAKAGE_REF,
            message=(f"envelope leaks {prefs.ach50:g} ACH50; N1102.4.1.2 allows at most "
                     f"{_MAX_ACH50:g}"),
            fix_hint="tighten the air barrier, or correct [envelope].ach50 to the tested value",
            result=Result.FAIL)]
    return [Finding(
        severity=Severity.WARN, check_id=cid, code_ref=_AIR_LEAKAGE_REF,
        message=f"envelope tests at {prefs.ach50:g} ACH50 (<= {_MAX_ACH50:g})",
        result=Result.PASS)]
