"""``mep.supply_freeze_exposure`` — potable supply in an exterior wall's stud bay.

ADVISORY, and a HOUSE advisory: no code section is cited because none was read for this
rule. The basis is a steady-state layer walk from the room (``interior_setpoint_f``) to the
design outdoor air (``Site.design_temp_heating``) through the resolved layers at the pipe,
``T = T_in - (T_in - T_out) * R_inboard / R_total`` on the pipe's OUTBOARD face. Water
freezes at 32 F; the pipe must clear that by :class:`FreezeAdvisory`'s margin.

The router prices an exterior insulated bay at 96"/ft and that stays; this is the stated
reason a cold line in one is, or is not, a concern. The two things that decide it are what is
outboard of the pipe (continuous insulation holds the bay warm; a bare bay does not) and
where in the bay the pipe sits. A bay with no ``CavityFill`` is credited zero R, and an
assembly with no continuous insulation outboard of the pipe is flagged whatever the number.

Hydrant runs are not graded here: ``mep.hydrant_freeze_depth`` and
``mep.exterior_hydrant_protection`` own them. A run with ``freeze_protection`` is reported
as protected, with the number beside it. Oracle: ``notes/supply_freeze_basis.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.plumbing_common import _advisory_fail
from typehaus.checks.mep.supply_freeze_walk import (
    FreezeAdvisory,
    Piece,
    Profile,
    cavity_pieces,
    pipe_plane_profile,
    vent_trimmed,
    wall_frame,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import PipeSystem
from typehaus.quantities import M_PER_IN

_CID = "mep.supply_freeze_exposure"
CONFIG = FreezeAdvisory()
_SUPPLY = (PipeSystem.WATER_COLD.value, PipeSystem.WATER_HOT.value)
_BASIS = ("house advisory from a steady-state layer walk, not a code requirement")


@dataclass(frozen=True)
class _Reading:
    run: str
    wall: str
    assembly: str
    length_m: float
    profile: Profile
    freeze_protection: str | None


def _hydrant_tags(ctx: CheckContext) -> set[str]:
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    return {e.tag for s in ctx.plan.storeys for e in ctx.plan.storey_elements(s.tag)
            if e.element_kind == "Fixture" and types.get(e.type_ref) is not None
            and types[e.type_ref].plan_symbol == "hydrant"}


def _exterior_framed_walls(ctx: CheckContext) -> list:
    """Walls with a framed bay and a CLADDING layer, a room on one side only."""
    from typehaus.resolve.room_openings import rooms_by_storey, wall_is_exterior

    index = rooms_by_storey(ctx.model)
    out = []
    for wall in ctx.model.walls:
        if wall.is_foundation or not any(ly.function == "cladding" for ly in wall.layers):
            continue
        frame = wall_frame(wall)
        if frame is not None and wall_is_exterior(ctx.model, wall, index):
            out.append((wall, *frame))
    return out


def _readings(ctx: CheckContext, walls: list, runs: list, site_f: tuple[float, float]
              ) -> tuple[list[_Reading], list[tuple[str, str]]]:
    from typehaus.resolve.mep_envelopes import opening_prisms, run_sections

    sections = run_sections(ctx.model)
    cuts: dict[str, list] = {}
    for _t, _d, host, footprint, low, high, _f in opening_prisms(ctx.model, erode_m=0.0):
        cuts.setdefault(host, []).append((footprint, low, high))
    out: list[_Reading] = []
    unreadable: list[tuple[str, str]] = []
    for run in runs:
        if len(run.z_m) != len(run.path):
            continue
        radius = sections[run.tag][0]
        for wall, outward, ring in walls:
            pieces = cavity_pieces(run.path, run.z_m, ring, wall.z0_m, wall.z1_m,
                                   cuts.get(wall.tag, []))
            if not pieces:
                continue
            assembly = ctx.plan.library.resolve_assembly(wall.assembly)
            if assembly is None:
                unreadable.append((run.tag, wall.tag))
                continue
            layers = vent_trimmed(wall, assembly)
            worst = min((_profile(ctx, wall, layers, piece, end, outward, radius, site_f)
                         for piece in pieces for end in ("a", "b")),
                        key=lambda p: (not p.missing, p.temperature_f))
            out.append(_Reading(run.tag, wall.tag, wall.assembly,
                                sum(p.length_m for p in pieces), worst,
                                run.freeze_protection))
    return out, unreadable


def _profile(ctx, wall, layers, piece: Piece, end: str, outward, radius, site_f) -> Profile:
    point, z = (piece.a, piece.za) if end == "a" else (piece.b, piece.zb)
    return pipe_plane_profile(wall, layers, ctx.plan.library, point, z, outward, radius,
                              *site_f)


def _describe(r: _Reading) -> str:
    p = r.profile
    feet = r.length_m / M_PER_IN / 12.0
    return (f"{r.run} runs {feet:.1f} ft in {r.wall}'s stud bay ({r.assembly}), its outboard "
            f"face {p.depth_in:.1f}\" behind the room face")


@check(Tier.ADVISORY, _CID)
def supply_freeze_exposure(ctx: CheckContext) -> list[Finding]:
    """Grade each supply run in an exterior stud bay by the temperature at its pipe plane."""
    hydrants = _hydrant_tags(ctx)
    runs = [r for r in ctx.model.pipe_runs if r.system in _SUPPLY
            and not (r.serves and all(tag in hydrants for tag in r.serves))]
    if not runs:
        return []
    site = ctx.plan.project.site
    heating = site.design_temp_heating
    if heating is None:
        return [_unknown(_CID, "Site.design_temp_heating is not authored, so the pipe-plane "
                               "temperature cannot be walked",
                         fix="author the winter design temperature on the Site")]
    indoor_f, outdoor_f = ctx.preferences.interior_setpoint_f, heating.fahrenheit
    walls = _exterior_framed_walls(ctx)
    readings, unreadable = _readings(ctx, walls, runs, (indoor_f, outdoor_f))
    out = [_unknown(_CID, f"{run} runs in {wall}'s stud bay but its assembly is not in the "
                          "library, so the layer stack cannot be read", (run, wall))
           for run, wall in unreadable]
    if not readings and not unreadable:
        return [_na(_CID, f"none of the {len(runs)} non-hydrant supply runs has any length "
                          f"inside the stud bay of the {len(walls)} exterior framed walls",
                    ())]
    context = (f"{indoor_f:.0f} F indoors, {outdoor_f:.0f} F design outdoors; "
               f"{CONFIG.freezing_f:.0f} F freezing + {CONFIG.margin_f:.0f} F margin = "
               f"{CONFIG.threshold_f:.0f} F; {_BASIS}")
    for r in sorted(readings, key=lambda x: (x.run, x.wall)):
        out.append(_grade(r, context))
    return out


def _unfilled(p: Profile) -> str:
    """A framed layer with no CavityFill is credited zero R, which the reader should know."""
    if not p.unfilled:
        return ""
    return f"; framed layer {p.unfilled[0]} has no CavityFill, credited zero R"


def _grade(r: _Reading, context: str) -> Finding:
    p = r.profile
    tags = (r.run, r.wall)
    where = _describe(r)
    if p.missing:
        return _unknown(_CID, f"{where}: {', '.join(p.missing)} carries no r_per_inch, so the "
                              "walk is incomplete", tags,
                        fix="author r_per_inch on the material")
    number = (f"pipe plane {p.temperature_f:.1f} F (R {p.inboard_r:.1f} inboard, "
              f"R {p.outboard_r:.1f} outboard)")
    cold = p.temperature_f < CONFIG.threshold_f
    bare = p.continuous_r <= 0.0
    if r.freeze_protection:
        return _pass(_CID, f"{where} is protected by {r.freeze_protection}; {number} ({context})",
                     tags)
    if bare or cold:
        reasons = []
        if bare:
            reasons.append("no continuous insulation outboard of the pipe, so the bay's "
                           "cold side is the cladding")
        if cold:
            below = "below freezing" if p.temperature_f < CONFIG.freezing_f else (
                f"within {CONFIG.margin_f:.0f} F of freezing")
            reasons.append(f"{p.temperature_f:.1f} F is {below}")
        text = f"{where}: {number}; " + " and ".join(reasons)
        return _advisory_fail(_CID, f"{text}{_unfilled(p)} ({context})", tags)
    note = _unfilled(p)
    return _pass(_CID, f"{where}: {number}, {p.temperature_f - CONFIG.threshold_f:.1f} F above "
                       f"the line, behind {p.continuous_note} continuous{note} ({context})", tags)
