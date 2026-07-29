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
from typehaus.findings import Finding, Result, Severity
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedModel


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


def _storey_is_conditioned(plan: PlanModel, storey_tag: str) -> bool:
    """The prescriptive envelope only binds the conditioned envelope — catlin's detached
    garage (RM-GARAGE, ``conditioned=False``) has no R-49 ceiling requirement."""
    rooms = [el for el in plan.storey_elements(storey_tag) if el.element_kind == "Room"]
    if not rooms:
        return True
    return any(room.conditioned for room in rooms)


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
)


def _is_freestanding_exterior_slab(tag: str) -> bool:
    """Whether a slab floors a freestanding structure outside the conditioned envelope, so
    the R-10 slab minimum does not bind it.

    Slabs carry no room-adjacency relation to derive this from the way walls do (→
    ``_walls_bounding_conditioned_space``), so this one is still a naming convention."""
    return tag.startswith(_FREESTANDING_SLAB_PREFIXES)


def _is_interior_assembly(tag: str) -> bool:
    """Interior partitions/cross-walls carry no prescriptive R-value requirement — they
    aren't part of the thermal envelope. This codebase's own naming convention already
    marks them with an "INT" token (CATLIN_CONC_12_INT, INT_2X6_PLUMBING, ...); the IFC
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
                       if not w.is_foundation and w.uid in envelope_walls}):
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


def _to_finding(row: PrescriptiveRow) -> Finding:
    message = f"{row.role} {row.component}: {row.provided} vs. {row.required} required"
    if row.verdict == "unknown":
        return Finding(severity=Severity.WARN, check_id="code.energy_prescriptive",
                       message=f"UNKNOWN — {row.role} {row.component} {row.provided}",
                       element_tags=(row.component,), result=Result.UNKNOWN)
    if row.verdict == "pass":
        return Finding(severity=Severity.WARN, check_id="code.energy_prescriptive",
                       message=message, element_tags=(row.component,), result=Result.PASS)
    return Finding(severity=Severity.ERROR, check_id="code.energy_prescriptive", message=message,
                   element_tags=(row.component,), result=Result.FAIL)


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
            result=Result.UNKNOWN,
        )]
    return [_to_finding(row) for row in evaluate_envelope(ctx.model, ctx.plan, envelope)]
