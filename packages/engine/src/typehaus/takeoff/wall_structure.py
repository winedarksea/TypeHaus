"""Monolithic wall structure by the square foot and the cubic yard.

A wall's STRUCTURE layer becomes one of two things. If it frames, its studs and plates are
``FramedMember`` records and ``framing_takeoff`` bills them stick by stick. If it does not —
a concrete pour, an ICF core, a CMU or SRW course, a brick wythe — it produces no members,
and it is not a ``ResolvedSolid`` either (walls never enter ``model.solids``), so
``structural_solids_takeoff`` cannot see it. Until this section existed those walls reached
no BOM row at all: on the catlin house that was 43 of 154 walls, ~3,800 sf and ~131 cubic
yards of concrete and masonry — more concrete than the whole priced order the estimate knew
about. ``W-B-BRICK``, the glazed-brick wythe at the sunken garden, is what surfaced it.

This is a *second* section rather than an extension of ``envelope_layers`` for the same
reason ``envelope_layers`` is separate from ``sheet_goods``: concrete is bought by the yard
and ``envelope_layers`` prices everything per square foot. Folding them together would force
one unit onto products that are not bought that way.

The framed/monolithic split is not re-derived here — it is
:func:`typehaus.resolve.framing.solver.frames_as_members`, the same predicate ``frame_wall``
branches on, so the two sections partition the walls exactly and cannot drift apart.

Deliberately out of scope, so a reader does not assume they were forgotten:

* **No masonry unit counts.** ``MasonrySpec.unit_size`` stays unread; area and volume only.
  For hollow CMU and SRW block the volume here is therefore *gross* wall volume, not net
  material — right for pricing a wall by the face, wrong for counting block.
* **No ``also_in_*`` mirror flag.** Nothing else bills these layers: ``structural_solids``
  has no wall category, ``envelope_layers`` excludes STRUCTURE, and ``wood_surfaces`` bills
  only species wood off ``Post`` elements and paneling records.
* **Roofs and floors have the identical hole.** Catlin's roof structure layers are all
  ``spf`` and bill in ``framing``, so nothing is missing today, but a CLT or concrete deck
  would vanish exactly the way these walls did.
* **``scope`` stays ``wall`` / ``foundation wall``.** A freestanding garden wall reads as a
  foundation wall here because that is what is authored (``element_kind="FoundationWall"``,
  ``structural_role=UNKNOWN``); the only discriminator available is a tag-prefix heuristic,
  and a *price* must not depend on a naming convention. The right fix, if wanted, is an
  authored field on the wall — not a substring test.
"""

from __future__ import annotations

from typehaus.resolve.framing.solver import frames_as_members, structure_layer
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.envelope import wall_net_areas_m2
from typehaus.takeoff.framing import _FT3_PER_CUBIC_YARD, _M2_TO_FT2, _M3_TO_FT3


def wall_structure_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Net area and volume per (scope, assembly, material, thickness) of monolithic wall.

    Grouped by *assembly* as well as material so authored intent survives into the order:
    the sunken-garden wall, the retaining block, the porch railing and the brick wythe each
    keep their own row instead of merging into the house's foundation concrete. Areas are
    net of openings — the same face ``envelope_layers`` bills the coverings on — and volume
    is that net area times the structure layer's thickness.
    """
    Row = dict[str, object]
    groups: dict[tuple[str, str, str, float], Row] = {}
    net_areas = wall_net_areas_m2(model)

    for wall in model.walls:
        layer = structure_layer(model.plan, wall.assembly)
        if layer is None or frames_as_members(layer):
            continue
        net_m2 = net_areas[wall.tag]
        thickness_m = layer.thickness.meters
        scope = "foundation wall" if wall.is_foundation else "wall"
        key = (scope, wall.assembly, layer.material_ref, thickness_m)
        row = groups.get(key)
        if row is None:
            row = groups[key] = {"scope": scope, "assembly": wall.assembly,
                                 "material": layer.material_ref,
                                 "thickness_in": round(thickness_m / 0.0254, 3),
                                 "count": 0, "net_area_m2": 0.0, "volume_m3": 0.0,
                                 "tags": []}
        row["count"] = int(row["count"]) + 1
        row["net_area_m2"] = float(row["net_area_m2"]) + net_m2
        row["volume_m3"] = float(row["volume_m3"]) + net_m2 * thickness_m
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(wall.tag)

    rows: list[dict[str, object]] = []
    for key in sorted(groups):
        row = groups[key]
        volume_cuft = round(float(row["volume_m3"]) * _M3_TO_FT3, 1)
        rows.append({
            "scope": row["scope"], "assembly": row["assembly"], "material": row["material"],
            "thickness_in": row["thickness_in"], "count": int(row["count"]),
            "net_area_sqft": round(float(row["net_area_m2"]) * _M2_TO_FT2, 1),
            "volume_cuft": volume_cuft,
            "volume_cubic_yards": round(volume_cuft / _FT3_PER_CUBIC_YARD, 2),
            "tags": sorted(row["tags"]),
        })
    return rows
