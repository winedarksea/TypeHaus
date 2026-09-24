"""Where a beam's section stands — read by ``mep.run_through_beam`` and by the router.

A run through a beam is a hole in a carrier, and the check graded it while the router
could not see it: catlin's kitchen vent proposal crossed ``BM-M-HALL`` and only the
evaluation said so. One derivation, two readers, as ``mep_envelopes`` is.

A cast beam is left out: a run through concrete is a sleeve question, graded by
``mep.sleeve_coverage`` against ``concrete_crossings`` and refused by the router's own
concrete prisms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

#: Framed-member categories that are carriers rather than a floor's field.
BEAM_MEMBER_CATEGORIES = ("beam", "girder", "ridge_beam")


def beam_sections(model: ResolvedModel) -> list[tuple[str, Any, float, float]]:
    """``(tag, plan polygon, z0, z1)`` for every beam solid and beam framed member."""
    from shapely.geometry import MultiPoint, Polygon

    from typehaus.resolve.assembly_material import is_cast_beam
    from typehaus.resolve.geometry_members import member_box

    out = []
    for solid in model.solids:
        if (solid.category == "beam" and len(solid.outline) >= 3
                and not is_cast_beam(model.plan, model.plan.by_tag(solid.tag))):
            out.append((solid.tag, Polygon(solid.outline), solid.z0_m, solid.z1_m))
    for member in model.all_members():
        if member.category not in BEAM_MEMBER_CATEGORIES:
            continue
        box = member_box(member)
        if box is None:
            continue
        corners = [*box.corners_bottom, *box.corners_top]
        footprint = MultiPoint([(x, y) for x, y, _ in corners]).convex_hull
        if footprint.area <= 0:
            continue
        out.append((f"{member.parent_uid}:{member.child_key}", footprint,
                    min(c[2] for c in corners), max(c[2] for c in corners)))
    return out
