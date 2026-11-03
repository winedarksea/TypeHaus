"""Which walls IRC R602.6 grades as bearing or exterior — read by the bore checks and the
router alike (``checks/mep/routing_bore_scope``, ``routing/members``).

Bearing is the model's own statement (``JoistSpec.bearing_refs``) plus every foundation
wall. Exterior is "faces outdoors" — a weather skin outboard, or earth — not "has a room on
one side", which reads an attic partition beside a stair void as exterior.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel


def bearing_wall_tags(model: ResolvedModel) -> frozenset[str]:
    """Every wall some floor's joists actually bear on, plus every foundation wall."""
    tags = {wall.tag for wall in model.walls if wall.is_foundation}
    for floor in model.floors:
        system = model.plan.by_tag(floor.tag)
        tags.update(getattr(getattr(system, "joists", None), "bearing_refs", ()) or ())
    return frozenset(tags)


def outdoor_wall_tags(model: ResolvedModel) -> frozenset[str]:
    """Walls that face outdoors: a weather skin outboard, or earth (a foundation)."""
    from typehaus.resolve.envelope_geometry import carries_a_weather_skin

    return frozenset(wall.tag for wall in model.walls
                     if wall.is_foundation or carries_a_weather_skin(wall))


def r602_6_roles(model: ResolvedModel) -> dict[str, str]:
    """``{wall tag: "bearing" | "exterior"}``; a wall absent is a non-bearing partition."""
    roles = dict.fromkeys(outdoor_wall_tags(model), "exterior")
    roles.update(dict.fromkeys(bearing_wall_tags(model), "bearing"))
    return roles
