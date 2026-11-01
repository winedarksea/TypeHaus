"""What the bore checks grade against: which walls R602.6 calls bearing or exterior, and how
wide the hole through a stud is for a lagged pipe.

Split out of ``routing_bores.py`` (C6-E3/E4, 2026-11-01), which reads both.

**Exterior is "faces outdoors", not "has a room on one side".** R602.6 gives an exterior
wall's studs the bearing limit (40% bore). ``room_openings.wall_is_exterior`` is a thermal
reading: an attic partition beside an unroomed stair void (``W-A-HALL-S``) has modelled
space on one side only and read as exterior. The weather skin is the honest test — a wall
with sheathing or cladding outboard (``envelope_geometry.carries_a_weather_skin``) stands
in the weather; a gypsum partition does not, whatever is beside it.

**Lagging stops at the framing unless a run says otherwise.** Field practice cuts a pipe's
jacket back at each stud or plate and bores for the bare pipe; ``PipeRun.lagging_at_framing``
states it per run, defaulting to ``"stops"``. A ``"continuous"`` run is bored at its lagged
OD. Either way an insulated run's finding says which, so the stop is printed, not assumed.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, shared


def bearing_wall_tags(ctx: CheckContext) -> frozenset[str]:
    """Every wall some floor's joists actually bear on, plus every foundation wall.

    Read from ``JoistSpec.bearing_refs`` — the model's own statement of what carries what.
    """
    tags = {wall.tag for wall in ctx.model.walls if wall.is_foundation}
    for floor in ctx.model.floors:
        system = ctx.model.plan.by_tag(floor.tag)
        tags.update(getattr(getattr(system, "joists", None), "bearing_refs", ()) or ())
    return frozenset(tags)


def outdoor_wall_tags(ctx: CheckContext) -> frozenset[str]:
    """Walls that face outdoors: a weather skin outboard, or earth (a foundation)."""
    from typehaus.resolve.envelope_geometry import carries_a_weather_skin

    def build() -> frozenset[str]:
        return frozenset(wall.tag for wall in ctx.model.walls
                         if wall.is_foundation or carries_a_weather_skin(wall))

    return shared(ctx, "routing_bore_scope.outdoor", build)


def r602_6_role(ctx: CheckContext) -> dict[str, str]:
    """``{wall tag: "bearing" | "exterior"}``; a wall absent is a non-bearing partition."""
    def build() -> dict[str, str]:
        roles = dict.fromkeys(outdoor_wall_tags(ctx), "exterior")
        roles.update(dict.fromkeys(bearing_wall_tags(ctx), "bearing"))
        return roles

    return shared(ctx, "routing_bore_scope.roles", build)


def lagging_at_framing(ctx: CheckContext) -> dict[str, tuple[float, str]]:
    """``{pipe run tag: (radius added at a bore in m, phrase)}`` for every lagged run.

    A run whose spec states no thickness is bored bare and says the thickness is unread.
    """
    from typehaus.model.mep import PipeRun
    from typehaus.quantities import M_PER_IN
    from typehaus.resolve.mep_envelopes import insulation_thickness_m

    def build() -> dict[str, tuple[float, str]]:
        out: dict[str, tuple[float, str]] = {}
        for run in ctx.model.pipe_runs:
            if not run.insulation:
                continue
            element = ctx.model.plan.by_tag(run.tag)
            mode = element.lagging_at_framing if isinstance(element, PipeRun) else "stops"
            thick = insulation_thickness_m(run.insulation)
            if mode == "stops":
                out[run.tag] = (0.0, f"its {run.insulation} lagging stops at the framing "
                                     "and the bare pipe is bored")
            elif thick is None:
                out[run.tag] = (0.0, f"its {run.insulation} lagging runs through the "
                                     "framing at a thickness the spec does not state; "
                                     "bored bare")
            else:
                out[run.tag] = (thick, f"its {run.insulation} lagging runs through the "
                                       f"framing, so the bore takes "
                                       f"{2 * thick / M_PER_IN:.2f}\" more")
        return out

    return shared(ctx, "routing_bore_scope.lagging", build)
