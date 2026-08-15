"""Sill-plate returns: what a framed wall — or a joisted deck — lands on over concrete.

Two finders, one physical detail. A framed wall stacked on a concrete wall gets a PT sill
with sill seal and a capillary break under it; a ``FloorSystem`` bearing on a
``FoundationWall`` gets the same return one element down, laid flat on the bearing ledge.
They live together because they share that detail's materials and treatments — change what
goes under a plate and both have to move.
"""

from __future__ import annotations

from collections.abc import Iterator

from typehaus.model.assembly import ConstructionRule
from typehaus.model.floors import FloorSystem
from typehaus.model.structure import FoundationWall
from typehaus.resolve.construction_assemblies import _framed_wood_layer, _is_concrete
from typehaus.resolve.construction_geometry import (
    _EPS,
    _MIN_STACK_OVERLAP_M,
    _condition_key,
    _stack_overlap,
    _strip,
    _walls_by_storey,
)
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import add, length, normal, scale, sub, unit
from typehaus.resolve.model import (
    ResolvedConstructionReturn,
    ResolvedModel,
    ResolvedWall,
)


# --- finders (one per applies_to predicate) -----------------------------------
# Each yields a fully-formed ResolvedConstructionReturn for the given rule. The finders own
# geometry/placement; ``apply_construction_rules`` owns the solid + book-keeping.
def _find_framed_on_concrete(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """PT sill where a framed wood wall lands on the concrete wall stacked below it."""
    lap = rule.dimension.meters if rule.dimension is not None else 0.0381  # 1.5"
    by_storey = _walls_by_storey(model)
    ordered = sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
    for lower in model.walls:
        lower_asm = model.plan.library.resolve_assembly(lower.assembly)
        if lower_asm is None or not _is_concrete(lower_asm):
            continue
        # Framed walls in the first storey above that carries a collinear wall over it.
        lower_i = next((i for i, s in enumerate(ordered) if s.tag == lower.storey), None)
        if lower_i is None:
            continue
        for upper_s in ordered[lower_i + 1:]:
            hits = []
            for upper in by_storey.get(upper_s.tag, []):
                upper_asm = model.plan.library.resolve_assembly(upper.assembly)
                if upper_asm is None or _framed_wood_layer(upper_asm) is None:
                    continue
                if _is_concrete(upper_asm):  # a concrete tier stacked on concrete is not framed
                    continue
                segment = _stack_overlap(lower, upper)
                if segment is not None:
                    hits.append((upper, upper_asm, segment))
            if not hits:
                continue
            for upper, upper_asm, (p0, p1) in hits:
                bearing = _framed_wood_layer(upper_asm)
                width = bearing.thickness.meters
                run = length(sub(p1, p0))
                direction = unit(sub(p1, p0))
                z0 = upper.z0_m
                yield ResolvedConstructionReturn(
                    uid=f"CR-{lower.uid}-{upper.uid}-sill",
                    tag=rule.tag, storey=upper.storey, kind=rule.kind,
                    applies_to=rule.applies_to, takeoff_category=rule.takeoff_category,
                    material_ref="spf",
                    element_tags=(lower.tag, upper.tag),
                    outline=_strip(p0, direction, run, -width / 2.0, width / 2.0),
                    z0_m=z0, z1_m=z0 + lap, thickness_m=width, length_m=run,
                    lap_m=lap, thermal_continuity=False, sealant="sill-gasket",
                    flashing="capillary-break", returning_layer=bearing.name,
                    condition_key=_condition_key(
                        "wall_foundation", lower.assembly, upper.assembly),
                )
            break  # first storey above with a stack owns this concrete wall


# The plate a joisted deck lands on where it bears on concrete. Laid *flat* — its bearing
# width is the member's depth (3.5") and its build-up is the member's width (1.5") — which
# is why this cannot be authored as a ``Beam`` and has to be a construction return.
_SILL_PLATE_MEMBER = "2x4"


def _floor_run_on_wall(rw: ResolvedWall, system: FloorSystem) \
        -> tuple[tuple[float, float], tuple[float, float]] | None:
    """The stretch of ``rw``'s axis the floor system actually bears over, or None.

    The bearing run is the wall axis clipped to the deck outline's extent along that axis —
    a 20'-axis cross-wall under a 19'-wide deck bills 19' of plate, not 20'.
    """
    a0, a1 = rw.axis
    direction = unit(sub(a1, a0))
    if length(direction) < _EPS:
        return None
    span = length(sub(a1, a0))
    ring = [p.xy_m for p in system.outline]
    if not ring:
        return None

    def proj(point: tuple[float, float]) -> float:
        v = sub(point, a0)
        return v[0] * direction[0] + v[1] * direction[1]

    lo = max(0.0, min(proj(p) for p in ring))
    hi = min(span, max(proj(p) for p in ring))
    if hi - lo < _MIN_STACK_OVERLAP_M:
        return None
    return add(a0, scale(direction, lo)), add(a0, scale(direction, hi))


def _find_floor_on_concrete(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """PT sill plate where a joisted deck bears on a concrete wall.

    The framed-wall case above is a *wall* landing on concrete; this is the same physical
    return one element down — a ``FloorSystem`` whose ``joists.bearing_refs`` names a
    ``FoundationWall``. The plate lies flat on the wall's bearing ledge with its top at the
    joist soffit (one joist depth below the storey datum), sill seal under it and the same
    capillary break, so the joists butt a rim on it instead of sitting on bare concrete.
    """
    plate = cross_section(_SILL_PLATE_MEMBER)
    width = plate.depth_m          # laid flat: the 3.5" face bears
    lap = rule.dimension.meters if rule.dimension is not None else plate.width_m  # 1.5"
    for storey in model.plan.storeys:
        for system in model.plan.storey_elements(storey.tag):
            if not isinstance(system, FloorSystem):
                continue
            z1 = storey.elevation.meters - cross_section(system.joists.member).depth_m
            for ref in system.joists.bearing_refs:
                if not isinstance(model.plan.by_tag(ref), FoundationWall):
                    continue
                rw = model.wall(ref)
                if rw is None:
                    continue
                asm = model.plan.library.resolve_assembly(rw.assembly)
                if asm is None or not _is_concrete(asm):
                    continue
                run_segment = _floor_run_on_wall(rw, system)
                if run_segment is None:
                    continue
                p0, p1 = run_segment
                direction = unit(sub(p1, p0))
                run = length(sub(p1, p0))
                # Land the plate on the deck side of the wall — the bearing ledge is the
                # face the joists come from, not the middle of a 16" pier section.
                n = normal(direction)
                ring = [p.xy_m for p in system.outline]
                centroid = (sum(p[0] for p in ring) / len(ring),
                            sum(p[1] for p in ring) / len(ring))
                toward = sub(centroid, p0)
                side = 1.0 if (toward[0] * n[0] + toward[1] * n[1]) >= 0.0 else -1.0
                far = side * rw.thickness_m / 2.0
                near = side * (rw.thickness_m / 2.0 - width)
                yield ResolvedConstructionReturn(
                    uid=f"CR-{rw.uid}-{system.uid}-sill",
                    tag=rule.tag, storey=storey.tag, kind=rule.kind,
                    applies_to=rule.applies_to, takeoff_category=rule.takeoff_category,
                    material_ref="spf",
                    element_tags=(rw.tag, system.tag),
                    outline=_strip(p0, direction, run, min(near, far), max(near, far)),
                    z0_m=z1 - lap, z1_m=z1, thickness_m=width, length_m=run,
                    lap_m=lap, thermal_continuity=False, sealant="sill-gasket",
                    flashing="capillary-break", returning_layer=_SILL_PLATE_MEMBER,
                    condition_key=_condition_key("floor_foundation", rw.assembly),
                )
