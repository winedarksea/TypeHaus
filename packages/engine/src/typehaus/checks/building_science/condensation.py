"""Condensation-risk check: scope the Glaser walk to the envelope and report it (M5 WP5.1).

The profile maths live in :mod:`typehaus.checks.building_science.glaser`; this module
decides *which* assemblies the screening applies to and turns each result into a
`Finding`. A safe assembly still reports — its margin is the answer the M5 acceptance
asks for — so the tier is never silent about an envelope it did evaluate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.checks.building_science.glaser import (  # re-exported: card/CLI/server import here
    CondensationAnalysis,
    CondensationPoint,
    MonthlyAssessment,
    analyze_assembly,
    analyze_assembly_monthly,
    analyze_layers,
    analyze_layers_monthly,
    glaser_layers,
    layer_permeance_perms,
)
from typehaus.checks.code.unvented_roof import r806_5_compliance
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity, not_applicable
from typehaus.model.assembly import Assembly, Layer
from typehaus.model.enums import ControlLayer, LayerFunction, Occupancy
from typehaus.model.spatial import Room
from typehaus.resolve.room_walls import bounding_walls

__all__ = [
    "CondensationAnalysis", "CondensationPoint", "MonthlyAssessment", "analyze_assembly",
    "analyze_assembly_monthly", "analyze_layers", "analyze_layers_monthly",
    "glaser_layers", "conditioned_envelope_assemblies", "conditioned_envelope_surfaces",
    "EnvelopeSurface", "humid_rooms_by_wall", "condensation_risk",
]

# The monthly (ISO 13788-style) worst-month reduction is the pass/fail GATE; the
# 99%-design-hour walk stays as a cold-snap SCREEN under its own finding id.
CHECK_ID = "building_science.condensation"
SCREEN_CHECK_ID = "building_science.condensation.cold_snap"

# Occupancies that are not part of the conditioned (heated/humidified) building volume, so
# the fixed interior design conditions this screening tool assumes do not apply to them.
_UNCONDITIONED = {Occupancy.GARAGE, Occupancy.UNCONDITIONED}


def _carries_thermal_control(assembly: Assembly) -> bool:
    """Does this assembly insulate — i.e. can it plausibly bound conditioned space?

    An exterior wall with no insulation layer and no THERMAL control layer is not part of
    the thermal envelope in a climate-zone-6 house: it is a guard, a screen wall, or a
    site structure that happens to carry cladding. Running an indoor-to-outdoor vapour
    drive across one reports a margin for a gradient that does not exist there.
    """
    layers = list(assembly.default_lining) + list(assembly.layers)
    return any(layer.function == LayerFunction.INSULATION
               or ControlLayer.THERMAL in layer.control
               or bool(layer.cavity_fills)  # a filled stud/joist bay is the insulation
               for layer in layers)


@dataclass(frozen=True)
class EnvelopeSurface:
    """One (assembly, interior condition) pair the Glaser walk actually has to run.

    An assembly tag alone is the wrong unit: the same stack can bound rooms at different
    design RH (e.g. a 35% bedroom and a 70% plant room), and keying the analysis on the tag
    alone would grade every one of them at whichever figure ``Preferences`` states. The
    surface is the pair: which layers, against which interior air.

    ``interior_relative_humidity`` is ``None`` when the room carries no humidity decision
    of its own, which is the ordinary case; the caller then supplies the house-wide figure
    from ``Preferences`` (two of them, in fact — the cold-snap screen and the monthly gate
    use different ones).
    """

    assembly_tag: str
    label: str  # what the finding names: the tag, or "TAG @ ROOM" for a per-room surface
    layers: tuple[Layer, ...]
    room_tag: str | None
    interior_relative_humidity: float | None
    #: A roof surface, as against a wall. Only a roof can take the R806.5 path below, and
    #: only a roof carries a metal panel with nothing but the panel outboard of the deck.
    is_roof: bool = False


def _room_design_rh(room: Room) -> float | None:
    """The authored ``Room``'s own design RH, or None for a house-wide room."""
    return room.interior_design_relative_humidity


def humid_rooms_by_wall(ctx: CheckContext) -> dict[str, list[Room]]:
    """Wall tag -> the authored ``Room``s bounding it that run at their own humidity.

    Only rooms with a humidity decision of their own are mapped, because they are the only
    ones whose bounding assemblies are analysed differently from the house default — and
    because deriving the room→wall relation is a shapely probe per (room, wall) pair
    (:func:`typehaus.resolve.room_walls.bounding_walls`), not a lookup.

    ``Wall.interior_room`` wins where it is authored: it is the explicit statement of which
    side layer 0 faces, and an asymmetric assembly like the sauna's or the plant room's is
    exactly the case where the geometric probe would also name the room on the *cold* side.
    """
    authored: dict[str, dict[str, Room]] = {}
    interior_rooms: dict[str, str] = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if element.element_kind == "Room" and _room_design_rh(element) is not None:
                authored.setdefault(storey.tag, {})[element.tag] = element
            named = getattr(element, "interior_room", None)
            if named is not None:
                interior_rooms[element.tag] = named
    if not authored:
        return {}

    by_wall: dict[str, list[Room]] = {}
    claimed: set[str] = set()
    for wall in ctx.model.walls:
        room_tag = interior_rooms.get(wall.tag)
        room = authored.get(wall.storey, {}).get(room_tag) if room_tag else None
        if room is not None:
            by_wall.setdefault(wall.tag, []).append(room)
            claimed.add(wall.tag)
    for resolved in ctx.model.rooms:
        room = authored.get(resolved.storey, {}).get(resolved.tag)
        if room is None:
            continue
        candidates = [wall for wall, _run in bounding_walls(ctx.model, resolved)]
        for wall in _nearest_along_each_face(resolved, candidates):
            if wall.tag in claimed:
                continue  # an authored interior_room already answered for this wall
            by_wall.setdefault(wall.tag, []).append(room)
    return by_wall


# A second wall this much further from the room face, on the same line, is behind the first
# one rather than beside it. Comfortably more than the mitre/lining jitter that separates two
# genuinely adjacent walls, comfortably less than any real cavity.
_BEHIND_M = 0.05


def _nearest_along_each_face(room: object, walls: list[Any]) -> list[Any]:
    """Drop candidates standing *behind* another candidate on the same line.

    :func:`~typehaus.resolve.room_walls.bounding_walls` answers "is this wall's axis within
    its own half-thickness of the room face", which is the right question for a finish
    running along a wall and the wrong one here: it also picks up a freestanding veneer
    wythe standing off the far side of the wall that actually encloses the room
    (``W-B-BRICK`` behind ``W-B-S2``). A veneer outside the envelope is not a bounding
    assembly of the room inside it, and grading it as one would demand a vapour barrier in
    a wall that has no interior side.
    """
    from shapely.geometry import LineString, Polygon

    face = Polygon(room.clear_face)
    measured = [(wall, LineString(wall.axis)) for wall in walls]
    kept = []
    for wall, axis in measured:
        offset = axis.distance(face)
        direction = _unit(wall.axis)
        behind = any(
            other is not wall
            and abs(_unit(other.axis)[0] * direction[0]
                    + _unit(other.axis)[1] * direction[1]) > 0.999
            and other_axis.distance(face) < offset - _BEHIND_M
            and other_axis.distance(axis) < _BEHIND_M + wall.thickness_m
            for other, other_axis in measured
        )
        if not behind:
            kept.append(wall)
    return kept


def _unit(axis: tuple[tuple[float, float], tuple[float, float]]) -> tuple[float, float]:
    (x0, y0), (x1, y1) = axis
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return ((x1 - x0) / length, (y1 - y0) / length) if length else (1.0, 0.0)


def _effective_lining(ctx: CheckContext, wall_tag: str, room: Room,
                      assembly: Assembly) -> tuple[Layer, ...]:
    """``Room.wall_lining`` / ``WallLiningException`` -> ``assembly.default_lining``.

    Same precedence the resolver applies to wall geometry
    (:func:`typehaus.resolve.rooms.wall_lining_overrides`), restated here against one known
    (wall, room) pair rather than re-derived across the storey. An override on an assembly
    that carries its finish in ``layers`` is ignored, exactly as the resolver ignores it.
    """
    if not assembly.default_lining:
        return ()
    for exception in room.wall_lining_exceptions:
        if exception.wall_ref == wall_tag:
            return tuple(exception.lining)
    if room.wall_lining:
        return tuple(room.wall_lining)
    return tuple(assembly.default_lining)


def conditioned_envelope_surfaces(ctx: CheckContext) -> list[EnvelopeSurface]:
    """Envelope surfaces to screen, in first-seen order — see :class:`EnvelopeSurface`.

    Scope is unchanged from what :func:`conditioned_envelope_assemblies` always applied
    (above-grade clad-and-insulated walls plus roofs, on storeys holding conditioned
    rooms); what is new is that a wall bounding a room which is *run* wet or humid yields
    its own surface, at that room's design RH and against that room's effective lining,
    instead of being folded into the house-wide analysis of its assembly tag.

    A room at the house's own humidity contributes no per-room surface deliberately. Its
    analysis would be identical to the assembly's, so a second finding would only restate
    the first under a longer name — and an accent-wall lining swap (same film, same class)
    is not a different building-science question.
    """
    conditioned: set[str] = set()
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            occ = getattr(element, "occupancy", None)
            if element.element_kind == "Room" and occ not in _UNCONDITIONED:
                conditioned.add(storey.tag)
                break

    humid_by_wall = humid_rooms_by_wall(ctx)
    surfaces: list[EnvelopeSurface] = []
    seen: set[tuple[Any, ...]] = set()

    def _add(tag: str | None, room: Room | None = None,
             wall_tag: str | None = None, *, is_roof: bool = False) -> None:
        if tag is None:
            return
        assembly = ctx.plan.library.resolve_assembly(tag)
        if assembly is None or not _carries_thermal_control(assembly):
            return
        if room is None:
            lining, rh, label, room_tag = tuple(assembly.default_lining), None, tag, None
        else:
            lining = _effective_lining(ctx, wall_tag or "", room, assembly)
            rh = _room_design_rh(room)
            label, room_tag = f"{tag} @ {room.tag}", room.tag
        layers = tuple(lining) + tuple(assembly.layers)
        key = (tag, rh, tuple((ly.name, ly.material_ref, ly.thickness.meters) for ly in layers))
        if key in seen:
            return
        seen.add(key)
        surfaces.append(EnvelopeSurface(tag, label, layers, room_tag, rh, is_roof))

    for wall in ctx.model.walls:
        if wall.storey not in conditioned:
            continue
        if not any(layer.function == "cladding" for layer in wall.layers):
            continue
        # A wall bounding a room run wet or humid contributes only that room's surface:
        # the house-wide walk of the same tag would be the analysis of an interior
        # condition that wall does not have on either face.
        humid = humid_by_wall.get(wall.tag, ())
        if not humid:
            _add(wall.assembly)
        for room in humid:
            _add(wall.assembly, room, wall.tag)
    for roof in ctx.model.roofs:
        if getattr(roof, "storey", None) in conditioned:
            _add(roof.assembly, is_roof=True)
    return surfaces


def conditioned_envelope_assemblies(ctx: CheckContext) -> list[str]:
    """Assembly tags on the conditioned exterior envelope, in first-seen order.

    Glaser screening with an outdoor-air boundary only means something across an assembly
    that actually separates the conditioned interior (70 F / design RH) from the exterior
    at the heating design temperature. It excludes:

    * interior partitions and interior concrete/bearing walls — no cross-envelope gradient;
    * an unconditioned detached garage and freestanding site structures — the interior side
      is not conditioned, so the fixed interior conditions do not apply;
    * below-grade foundation walls — these are ground-coupled (soil near +10 C, not the
      -15 F design air), so an outdoor-air Glaser walk would invent a risk that does not run;
    * clad-but-uninsulated walls (masonry guards, screen walls) — see
      :func:`_carries_thermal_control`.

    An above-grade exterior wall is identified by its outermost cladding layer; the analysis
    is scoped to those walls and to roofs, on storeys that hold conditioned rooms.

    Kept as the tag-only view of :func:`conditioned_envelope_surfaces` for callers that
    only want to know *which assemblies* are on the envelope.
    """
    tags: list[str] = []
    for surface in conditioned_envelope_surfaces(ctx):
        if surface.assembly_tag not in tags:
            tags.append(surface.assembly_tag)
    return tags


def _unknown_finding(analysis: CondensationAnalysis, label: str, check_id: str) -> Finding:
    return Finding(
        severity=Severity.WARN, check_id=check_id,
        message=(f"{label}: UNKNOWN — missing Glaser inputs: "
                 + ", ".join(analysis.unknown_materials)),
        element_tags=(analysis.assembly_tag,), result=Result.UNKNOWN,
        fix_hint="author perm_rating (perm-in) or vapor_permeance_perms (perms) with "
                 "its ASTM E96 / manufacturer source on the named material",
    )


def _gate_finding(assessment: MonthlyAssessment | None, assembly_tag: str) -> Finding:
    """The monthly (ISO 13788-style) gate finding — the pass/fail verdict."""
    if assessment is None:
        return Finding(
            severity=Severity.WARN, check_id=CHECK_ID,
            message="monthly gate (ISO 13788-style): UNKNOWN — Site.monthly_normals is "
                    "not authored (needs 12 MonthlyNormal entries, January..December)",
            element_tags=(assembly_tag,), result=Result.UNKNOWN,
            fix_hint="author Site.monthly_normals from published station normals (e.g. "
                     "NOAA NCEI 1991-2020) so the seasonal gate can run; until then only "
                     "the cold-snap screen is evaluated",
        )
    analysis = assessment.analysis
    if not analysis.known:
        return _unknown_finding(analysis, "monthly gate (ISO 13788-style)", CHECK_ID)
    if analysis.has_risk:
        return Finding(
            severity=Severity.WARN, check_id=CHECK_ID,
            message=(f"monthly gate (ISO 13788-style): dew point reached at "
                     f"{analysis.crossing_layer} ({analysis.crossing_fraction:.0%} through "
                     f"layer) at {assessment.boundary}; "
                     f"{analysis.interior_retarder_note}"),
            element_tags=(analysis.assembly_tag,), result=Result.FAIL,
            fix_hint="this is the gate: a crossing against a monthly *mean* means the "
                     "plane runs wet for weeks, not hours — add exterior insulation, a "
                     "warm-side vapour retarder, or a vented cavity so the plane can dry",
        )
    tightest = analysis.tightest_plane
    assert tightest is not None  # a known analysis always carries its profile
    return Finding(
        severity=Severity.WARN, check_id=CHECK_ID,
        message=(f"monthly gate (ISO 13788-style): no dew-point crossing in any month — "
                 f"worst month {assessment.month} at {assessment.boundary}, tightest plane "
                 f"{analysis.tightest_plane_name} at "
                 f"{tightest.local_relative_humidity:.0%} RH, "
                 f"{tightest.margin_pa:.0f} Pa below saturation; "
                 f"{analysis.interior_retarder_note}"),
        element_tags=(analysis.assembly_tag,), result=Result.PASS,
    )


def _screen_finding(analysis: CondensationAnalysis, boundary: str) -> Finding:
    """The 99%-design-hour walk, relabeled as the cold-snap screen (not the gate)."""
    if analysis.has_risk:
        # ``Result.PASS`` with the crossing spelled out, not ``FAIL``: the fix_hint below
        # says in as many words that this is not the verdict, and a finding that both
        # disclaims being a verdict and files a failure against the tally is a finding
        # arguing with itself. The gate (``CHECK_ID``) owns the pass/fail on this assembly.
        return Finding(
            severity=Severity.WARN, check_id=SCREEN_CHECK_ID,
            message=(f"cold-snap screen: dew point reached at {analysis.crossing_layer} "
                     f"({analysis.crossing_fraction:.0%} through layer) at {boundary}"),
            element_tags=(analysis.assembly_tag,), result=Result.PASS,
            fix_hint="screen only — the monthly (ISO 13788-style) gate is the pass/fail "
                     "verdict; this is the 99% design hour, not a seasonal mean, so a "
                     "crossing here means the plane runs wet during a cold snap and must "
                     "be able to dry, not that the wall fails the gate",
        )
    tightest = analysis.tightest_plane
    assert tightest is not None  # a known analysis always carries its profile
    return Finding(
        severity=Severity.WARN, check_id=SCREEN_CHECK_ID,
        message=(f"cold-snap screen: no dew-point crossing at {boundary} — tightest plane "
                 f"{analysis.tightest_plane_name} at "
                 f"{tightest.local_relative_humidity:.0%} RH, "
                 f"{tightest.margin_pa:.0f} Pa below saturation"),
        element_tags=(analysis.assembly_tag,), result=Result.PASS,
    )


def _r806_5_deferral(ctx: CheckContext, surface: EnvelopeSurface) -> Finding | None:
    """The gate finding for a roof R806.5 hands to a code criterion instead — or None.

    **A steady-state Glaser walk cannot grade an assembly sealed on its cold side.** Under a
    standing-seam panel (0 perm) :func:`~...glaser._vapor_fractions` finds the outermost
    resistance infinite and puts every plane inboard of it at the full *interior* vapour
    pressure, because at steady state with no outward flux the stack equilibrates to the
    warm side. That is the correct limit of the method and a useless verdict: it reports
    100% RH at the deck for every unvented metal roof, at any foam thickness, however it is
    designed — see ``houses/catlin/CLAUDE.md``.

    R806.5 items 5.2 and 5.3 replace the criterion rather than relax it. Air-impermeable
    insulation bonded to the sheathing underside, at the Table R806.5 R-value and itself a
    Class II retarder, IS the condensation control: the table is a dew-point calculation for
    the zone, holding the first condensing surface — the foam's own outer face, which is the
    deck — above the interior dew point, and outward drying is then not required. So the
    honest reading is not a FAIL and not a silent pass: the section this engine now grades
    (``code.R806_5_unvented_roof``) owns the verdict, and this gate reports NOT_APPLICABLE
    naming it.

    The deferral is earned, not assumed, and it is guarded twice. It applies only where the
    code check itself PASSES — an assembly whose foam is below the table, or is not Class
    II, or which carries a ceiling-side Class I retarder, keeps the Glaser gate and its FAIL.
    And it applies only to a roof whose stack really has no drying path: a vented mat or a
    permeable underlayment over the deck leaves the walk something to say, and ``layers``
    (already truncated by :func:`glaser_layers`) ending at a vent plane is the evidence of it.
    """
    if not surface.is_roof:
        return None
    assembly = ctx.plan.library.resolve_assembly(surface.assembly_tag)
    if assembly is None:
        return None
    result = r806_5_compliance(assembly, ctx.plan.library)
    if not (result.deck_contact_insulation and result.complies):
        return None
    # A stack the Glaser walk can still finish — one truncated at a vented cavity, or whose
    # outermost layer is not a vapour barrier — is graded on its own terms. The deferral is
    # for the sealed case, which is the only one the method cannot answer.
    truncated = glaser_layers(list(surface.layers))
    outermost = truncated[-1] if truncated else None
    if outermost is None or len(truncated) < len(surface.layers):
        return None
    permeance = layer_permeance_perms(outermost, ctx.plan.library)
    if permeance is None or permeance > 0.0:
        return None
    assert result.deck_contact_r is not None
    return not_applicable(
        CHECK_ID,
        f"monthly gate (ISO 13788-style): the stack is sealed on its cold side by "
        f"{outermost.name} (0 perm), so a steady-state Glaser walk has no outward flux to "
        f"grade and reads every plane at interior vapour pressure by construction. "
        f"R806.5 item {result.item} replaces that criterion: R-{result.deck_contact_r:.1f} "
        f"of air-impermeable, Class {result.air_impermeable_class} insulation bonded to the "
        f"sheathing underside is the condensation control, and outward drying is not "
        f"required. Graded by code.R806_5_unvented_roof",
        (surface.assembly_tag,), code="R806.5",
    )


@check(Tier.BUILDING_SCIENCE, CHECK_ID)
def condensation_risk(ctx: CheckContext) -> list[Finding]:
    """Per envelope surface: the monthly gate (pass/fail) plus the cold-snap screen.

    The gate runs :func:`analyze_layers` twelve times over ``Site.monthly_normals`` and
    keeps the worst month — a seasonal mean is what an assembly actually has to dry
    against. The 99%-design-hour walk stays, relabeled as a screen: informative about a
    cold snap, never the verdict. When the Glaser inputs themselves are missing, one
    UNKNOWN finding (the gate's) names them instead of repeating itself per surface.

    The unit is a *surface*, not an assembly tag (:class:`EnvelopeSurface`): a wall
    bounding a room run wet or humid is walked again at that room's design RH, because the
    same stack is a different building-science question at 70% RH than at 35%.
    """
    site = ctx.plan.project.site
    heating = site.design_temp_heating
    temperature_f = heating.fahrenheit if heating is not None else None
    findings: list[Finding] = []
    for surface in conditioned_envelope_surfaces(ctx):
        layers = glaser_layers(list(surface.layers))
        screen_rh = (surface.interior_relative_humidity
                     if surface.interior_relative_humidity is not None
                     else ctx.preferences.interior_relative_humidity)
        gate_rh = (surface.interior_relative_humidity
                   if surface.interior_relative_humidity is not None
                   else ctx.preferences.monthly_interior_relative_humidity)
        # Every finding states its boundary condition: a Glaser crossing is only meaningful
        # against the design temperature and interior humidity that produced it.
        boundary = (f"{temperature_f:.0f} F design / {screen_rh:.0%} interior RH"
                    if temperature_f is not None else "the design heating temperature")
        assessment: MonthlyAssessment | None = None
        deferral = _r806_5_deferral(ctx, surface)
        if deferral is not None:
            findings.append(deferral)
        else:
            assessment = analyze_layers_monthly(
                surface.label, layers, ctx.plan.library,
                monthly_normals=site.monthly_normals,
                interior_setpoint_f=ctx.preferences.interior_setpoint_f,
                interior_relative_humidity=gate_rh,
            )
            findings.append(_gate_finding(assessment, surface.label))
        screen = analyze_layers(
            surface.label, layers, ctx.plan.library,
            heating_design_temp_f=temperature_f,
            interior_setpoint_f=ctx.preferences.interior_setpoint_f,
            interior_relative_humidity=screen_rh,
            exterior_relative_humidity=ctx.preferences.exterior_relative_humidity,
        )
        if not screen.known:
            # The gate already named these inputs unless it ran on complete data (or was
            # itself missing its normals while the screen misses the design temperature) —
            # or it deferred to R806.5 and named nothing at all.
            if deferral is not None or assessment is None or assessment.analysis.known:
                findings.append(_unknown_finding(screen, "cold-snap screen",
                                                 SCREEN_CHECK_ID))
            continue
        findings.append(_screen_finding(screen, boundary))
    return findings
