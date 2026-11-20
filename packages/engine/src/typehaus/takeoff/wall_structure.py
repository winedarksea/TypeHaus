"""Monolithic wall structure by the square foot and the cubic yard.

A wall's STRUCTURE layer becomes one of two things. If it frames, its studs and plates are
``FramedMember`` records and ``framing_takeoff`` bills them stick by stick. If it does not —
a concrete pour, an ICF core, a CMU or SRW course, a brick wythe — it produces no members,
and it is not a ``ResolvedSolid`` either (walls never enter ``model.solids``), so
``structural_solids_takeoff`` cannot see it. ``W-B-BRICK``, the glazed-brick wythe at the
sunken garden, is what surfaced the gap.

This is a *second* section rather than an extension of ``envelope_layers`` for the same
reason ``envelope_layers`` is separate from ``sheet_goods``: concrete is bought by the yard
and ``envelope_layers`` prices everything per square foot. Folding them together would force
one unit onto products that are not bought that way.

The framed/monolithic split is not re-derived here — it is
:func:`typehaus.resolve.framing.solver.frames_as_members`, the same predicate ``frame_wall``
branches on, so the two sections partition the walls exactly and cannot drift apart.

Deliberately out of scope, so a reader does not assume they were forgotten:

* **Only the takeoff reads every structure layer.** The other consumers of
  ``structure_layer`` / ``Assembly.structure_index`` still take the first one, and that was
  checked when ``Layer.slot`` arrived rather than assumed:
  ``resolve/assembly_material.py`` and ``emit/gltf/palette.py`` want a fallback colour for a
  *solid*, ``emit/draw/foundation_schedule.py`` and ``emit/draw/section.py`` want a
  thickness. Every region of a slot carries the same thickness by rule, so the schedule and
  the section are unaffected; the two colour fallbacks pick the first region's material,
  which for a split row is a presentation choice and not a quantity.
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

import math

from typehaus.model.enums import LayerFunction
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.solver import frames_as_members
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.stairs.well_wall import face_only
from typehaus.takeoff.envelope import wall_layer_net_area_m2, wall_net_areas_m2
from typehaus.takeoff.framing import _FT3_PER_CUBIC_YARD, _M2_TO_FT2, _M3_TO_FT3

_ON_LINE_M = 0.003  # a member this close to a wall's axis is on it
_GAP_M = 0.006  # uncovered length a stair-framed wall may leave (a 1/4" fit-up)


def stair_framed_walls(model: ResolvedModel) -> set[str]:
    """Face-only walls a stair frames end to end (a U-stair's well partition).

    Their sticks bill in [framing] as the stair's ``partition`` members, so the unframed
    STRUCTURE layer is not a second, monolithic quantity. A wall the stair's partition and
    the columns on its line do not cover end to end keeps its monolithic row.
    """
    parts = [m for stair in model.stairs for m in stair.members if m.category == "partition"]
    if not parts:
        return set()
    columns = [s.outline for s in model.solids if s.category == "column"]
    return {wall.tag for wall in model.walls
            if not wall.members and face_only(model.plan, wall.assembly)
            and _covered_end_to_end(wall, parts, columns)}


def _covered_end_to_end(wall, parts, columns) -> bool:
    (ax, ay), (bx, by) = wall.axis
    length = math.hypot(bx - ax, by - ay)
    if length < 1e-9:
        return False
    ux, uy = (bx - ax) / length, (by - ay) / length

    def along(points) -> list[float] | None:
        if any(abs((x - ax) * uy - (y - ay) * ux) > _ON_LINE_M for x, y in points):
            return None
        return [(x - ax) * ux + (y - ay) * uy for x, y in points]

    covered = []
    for m in parts:
        ss = along((m.p0, m.p1))
        if ss is not None and m.z0_m < wall.z1_m and m.z1_m > wall.z0_m:
            pad = cross_section(m.profile).width_m / 2.0 if m.p0 == m.p1 else 0.0
            covered.append((min(ss) - pad, max(ss) + pad))
    if not covered:
        return False
    for outline in columns:  # a post on the line backs the boards past the partition
        xs, ys = [p[0] for p in outline], [p[1] for p in outline]
        if along((((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0),)) is not None:
            ss = [(x - ax) * ux + (y - ay) * uy for x, y in outline]
            covered.append((min(ss), max(ss)))
    reach = 0.0
    for lo, hi in sorted(covered):
        if lo > reach + _GAP_M:
            return False
        reach = max(reach, hi)
    return reach >= length - _GAP_M


def wall_structure_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Net area and volume per (scope, assembly, material, thickness) of monolithic wall.

    Grouped by *assembly* as well as material so authored intent survives into the order:
    the sunken-garden wall, the retaining block, the porch railing and the brick wythe each
    keep their own row instead of merging into the house's foundation concrete. Areas are
    net of openings — the same face ``envelope_layers`` bills the coverings on — and volume
    is that net area times the structure layer's thickness.

    **Every** monolithic STRUCTURE layer bills, not just the first one. An assembly may
    split one row of its stack into regions at a height (``Layer.slot``), and those regions
    are different materials at different prices — catlin's brick wythe is a brown plinth
    under a lapis field with two gold registers in it, and asking
    :func:`~typehaus.resolve.framing.solver.structure_layer` for "the" structure layer would
    miss every region but the first. A banded region takes its own band area from
    :func:`~typehaus.takeoff.envelope.wall_layer_net_area_m2` — the same helper
    ``envelope_layers`` uses, so a covering and the thing it covers cannot disagree about
    how tall a band is. An unbanded layer still gets the whole wall face, so no existing
    row moved.
    """
    Row = dict[str, object]
    groups: dict[tuple[str, str, str, float], Row] = {}
    net_areas = wall_net_areas_m2(model)
    stair_framed = stair_framed_walls(model)

    for wall in model.walls:
        if wall.tag in stair_framed:
            continue
        asm = model.plan.library.resolve_assembly(wall.assembly)
        if asm is None:
            continue
        authored = {layer.name: layer for layer in asm.layers}
        scope = "foundation wall" if wall.is_foundation else "wall"
        for resolved in wall.layers:
            if resolved.function != LayerFunction.STRUCTURE.value:
                continue
            layer = authored.get(resolved.name)
            if layer is None or frames_as_members(layer):
                continue
            net_m2 = wall_layer_net_area_m2(model, wall, resolved, net_areas[wall.tag])
            if net_m2 <= 0.0:
                continue
            thickness_m = layer.thickness.meters
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
            if wall.tag not in tags:
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
