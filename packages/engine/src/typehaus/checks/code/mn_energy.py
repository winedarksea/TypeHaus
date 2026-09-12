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
from typehaus.checks.registry import CheckContext, Preferences, Tier, check
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
    # Same column, not a second number. IRC Table N1102.1.2 carries ONE fenestration
    # U-factor for climate zone 6 and R202 makes a glazed door fenestration, so a French or
    # sliding leaf is graded on the window limit. The separate "door U-factor" column of the
    # 2009-era table is gone; what remains is R402.3.4's exemption for ONE side-hinged
    # opaque door of 24 sf or less, which is why an opaque exterior leaf that states nothing
    # is not reported as a gap below.
    door_u_max: float = 0.32


MN_ZONE_6 = PrescriptiveEnvelope()


@dataclass(frozen=True)
class PrescriptiveRow:
    """One EN-1 table row: a component checked against its MN zone-6 requirement."""

    component: str  # tag (assembly, window type, or door type)
    role: str  # "roof" | "above-grade wall" | "foundation wall" | "slab" | "window" | "door"
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

    **Measured from the wall's BODY, not from ``axis`` +/- half its thickness.** ``axis`` is
    the wall's *alignment reference*, and only a centreline-aligned wall puts that in the
    middle: a wall authored ``alignment=face(...)`` carries its whole depth to ONE side of
    the axis, so half-thickness is both the wrong distance and the wrong direction. For a
    centreline wall the two formulations are identical — the body reaches exactly half the
    thickness either way — so nothing that was classified correctly moves.

    It matters at real margins. catlin's `W-B-BRICK` is a freestanding glazed-brick wythe
    standing in the open air of the sunken garden court, separated from the conditioned
    basement by the court wall's concrete and 4" of XPS; it is not an envelope wall and its
    R-1.6 is not a defect. Under the old formulation it sat 0.27" outside the reach and was
    excluded by luck. Growing its air gap by 1/2" (2026-09-04, the parge-deletion fix) moved
    the axis 1/2" inboard AND the half-thickness 1/4" outward, which flipped it in and
    reported a spurious R-15 FAIL. From the body its nearest face is 4.05" off the room
    polygon and it is excluded on the geometry rather than on a coincidence.
    """
    from shapely.geometry import Polygon

    rooms: dict[str, list[Polygon]] = {}
    for room in model.rooms:
        if room.conditioned and len(room.clear_face) >= 3:
            rooms.setdefault(room.storey, []).append(Polygon(room.clear_face))
    bounding: set[str] = set()
    for wall in model.walls:
        near = rooms.get(wall.storey, ())
        if not near:
            continue
        # The room polygon is the *interior face*, so a bounding wall's body lands on it or
        # just off it; the tolerance absorbs lining/junction resolution. Distances are taken
        # per layer rather than over a union — an overlay of every wall's layers would be a
        # lot of GEOS work to answer a question min() already answers.
        bodies = [Polygon(ly.polygon) for ly in wall.depth_layers() if len(ly.polygon) >= 3]
        if not bodies:
            continue
        if any(body.distance(poly) <= _ENVELOPE_ADJACENCY_TOLERANCE_M
               for poly in near for body in bodies):
            bounding.add(wall.uid)
    return frozenset(bounding)


# How far a wall's BODY may sit off a conditioned room's interior face and still be that
# room's enclosure. It was "beyond the wall's own half-thickness" while the measurement was
# taken from ``axis``; the half-thickness is now in the body itself, so this is the whole
# slack and it absorbs lining and junction resolution only.
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
    # The north-face heat-pump equipment pad (catlin's SL-M-HP1PAD,
    # params/hp1_north_pad.py), added 2026-09-04 when System 1's condenser crossed from the
    # south pocket. Same argument as SL-M-HP3PAD one entry up, and named in full for the
    # same reason: 9.27 sf on grade east of the garage under an outdoor unit on 18" legs,
    # with nothing conditioned above it.
    "SL-M-HP1PAD",
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

    # Only EXTERIOR doors: the prescriptive table grades the thermal envelope, and an
    # interior leaf is not on it. DT-INT-SWING30-GLAZED is glazed and states no U-factor —
    # a loop over every door type would report that as a gap in the envelope it is not part
    # of. An exterior OPAQUE leaf with nothing stated is left silent for R402.3.4's
    # side-hinged-door exemption; a GLAZED one is fenestration and owes a number.
    for door_type in plan.library.door_types:
        if not door_type.exterior:
            continue
        if door_type.u_factor is None:
            if door_type.glazed:
                rows.append(PrescriptiveRow(door_type.tag, "door",
                                            f"U-{envelope.door_u_max:.2f}",
                                            "UNKNOWN (no U-factor)", "unknown"))
            continue
        u = door_type.u_factor.u_us
        verdict = "pass" if u <= envelope.door_u_max + 1e-6 else "fail"
        rows.append(PrescriptiveRow(door_type.tag, "door", f"U-{envelope.door_u_max:.2f}",
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


@dataclass(frozen=True)
class AirLeakageSummary:
    """The blower-door line, as both the check and G-004/G-005 need it.

    One function, two consumers — the same shape as ``evaluate_envelope``. ``result`` is a
    ``Result`` so the sheet can colour the row exactly as the check graded it, and
    ``message`` is the one sentence both print; nothing downstream re-derives a verdict from
    the numbers and risks disagreeing with the finding beside it.
    """

    max_ach50: float
    ach50: float | None
    cfm50: float | None
    result: Result
    message: str
    fix_hint: str | None = None


def air_leakage_summary(prefs: Preferences) -> AirLeakageSummary:
    """Grade the authored blower-door result against N1102.4.1.2's flat 3.0 ACH50.

    ``cfm50`` without ``ach50`` is UNKNOWN, not a conversion: dividing CFM50 by a volume
    this engine does not resolve as a single figure would turn a *measurement* into an
    estimate, which is the one thing a blower-door number must never become.
    """
    def summary(result: Result, message: str, fix_hint: str | None = None
                ) -> AirLeakageSummary:
        return AirLeakageSummary(max_ach50=_MAX_ACH50, ach50=prefs.ach50, cfm50=prefs.cfm50,
                                 result=result, message=message, fix_hint=fix_hint)

    if prefs.cfm50 is not None and prefs.ach50 is None:
        return summary(Result.UNKNOWN,
                       f"UNKNOWN — the house states cfm50 = {prefs.cfm50:g} but no ach50, "
                       "and converting between them needs a conditioned volume this engine "
                       "does not resolve")
    if prefs.ach50 is None:
        return summary(Result.UNKNOWN,
                       "UNKNOWN — no blower-door result authored ([envelope].ach50 in "
                       f"preferences.toml); N1102.4.1.2 requires {_MAX_ACH50:g} ACH50 or "
                       "less")
    if prefs.ach50 > _MAX_ACH50 + 1e-9:
        return summary(Result.FAIL,
                       f"envelope leaks {prefs.ach50:g} ACH50; N1102.4.1.2 allows at most "
                       f"{_MAX_ACH50:g}",
                       "tighten the air barrier, or correct [envelope].ach50 to the tested "
                       "value")
    return summary(Result.PASS,
                   f"envelope tests at {prefs.ach50:g} ACH50 (<= {_MAX_ACH50:g})")


@check(Tier.CODE, "code.N1102_4_air_leakage")
def air_leakage(ctx: CheckContext) -> list[Finding]:
    """N1102.4.1.2 — envelope air leakage at or under 3.0 ACH50.

    This is the one energy requirement with a *test* behind it rather than a table lookup,
    and the number is already authored: ``preferences.ach50`` (or ``cfm50``, which wins
    when both are present because a test report states CFM50 and the ACH50 is derived from
    it — see the Preferences docstring). All of the grading lives in
    ``air_leakage_summary`` so the energy sheet prints the finding rather than its own
    second opinion.
    """
    summary = air_leakage_summary(ctx.preferences)
    severity = Severity.ERROR if summary.result is Result.FAIL else Severity.WARN
    return [Finding(
        severity=severity, check_id="code.N1102_4_air_leakage", code_ref=_AIR_LEAKAGE_REF,
        message=summary.message, fix_hint=summary.fix_hint, result=summary.result)]
