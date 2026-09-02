"""Sill-plate returns: what a framed wall — and the joists beside it — land on over concrete.

**One plate, one finder.** A framed wall stacked on a concrete wall gets a PT sill with sill
seal and a capillary break under it, and a ``FloorSystem`` bearing on the same
``FoundationWall`` bears on that same board. Two separate predicates here — one per element —
would double-bill wherever both fire and leave a coverage gap wherever only the floor bears,
so ``_find_framed_on_concrete`` takes the **union** of the two runs. ``_framed_on_slab`` is
the third case and stays separate — a partition standing on a slab shares the materials but
not the run.
"""

from __future__ import annotations

from collections.abc import Iterator

from typehaus.model.assembly import ConstructionRule
from typehaus.model.floors import FloorSystem
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
from typehaus.resolve.framing.solver import _structure_polygon, band_axis
from typehaus.resolve.geometry import add, length, normal, scale, sub, unit
from typehaus.resolve.model import (
    ResolvedConstructionReturn,
    ResolvedModel,
    ResolvedWall,
)

#: The compressed, in-place sill-seal thickness used when an assembly's ``FramingSpec``
#: does not state one. Matches ``BasementToFramedWallConfig.sill_gasket_in`` — the drawing
#: config states it in inches for the detail writer, and it is the same building fact.
_COMPRESSED_SILL_GASKET_M = 0.0625 * 0.0254

#: What a sill-seal *is*, for the BOM. Plain closed-cell foam sill seal on the walls whose
#: plate joint is only a capillary and air break inside the envelope; a peel-and-stick
#: foam (Protecto Wrap style) where that joint is the air barrier crossing the foundation.
SILL_GASKET_FOAM = "sill-seal-foam"
SILL_GASKET_PEEL_STICK = "sill-seal-peel-stick"


def _assembly_is_clad(asm) -> bool:
    """Does this assembly carry a weather skin — i.e. is it an envelope wall?

    Derived, never named. This is the assembly-only half of the test the engine already
    makes twice: ``takeoff/anchors._is_exterior_framed_wall`` asks the same question of a
    *resolved* wall's layers (and additionally that it has studs), and
    ``checks/code/mn_residential/_common._wall_is_exterior`` is the canonical form, deriving
    it from whether modelled space exists on one side or two. Neither is usable here — sills
    resolve before framing, and rooms are not what a sill-seal product depends on — but a
    cladding layer answers it from the assembly alone, which is what this stage has.
    """
    if asm is None:
        return False
    return any(getattr(layer.function, "value", layer.function) == "cladding"
               for layer in asm.layers)


def _sill_gasket(asm, fallback_asm=None) -> tuple[str, float]:
    """``(product, compressed thickness in metres)`` for the seal under this plate.

    ``FramingSpec.sill_gasket_product`` overrides; otherwise a clad (envelope) wall gets the
    peel-and-stick form because its plate joint is where the air barrier crosses onto the
    foundation, and everything else gets plain foam. ``fallback_asm`` is what a run with no
    framed wall over it is graded on — a plate under joists on bare pour.
    """
    graded = asm if asm is not None else fallback_asm
    product = None
    thickness = None
    for layer in (asm.layers if asm is not None else ()):
        spec = getattr(layer, "framing", None)
        if spec is None:
            continue
        if getattr(spec, "sill_gasket_product", None) is not None:
            product = spec.sill_gasket_product
        if getattr(spec, "sill_gasket", None) is not None:
            thickness = spec.sill_gasket.meters
    if product is None:
        product = (SILL_GASKET_PEEL_STICK if _assembly_is_clad(graded)
                   else SILL_GASKET_FOAM)
    return product, (thickness if thickness is not None
                     else _COMPRESSED_SILL_GASKET_M)


# --- finders (one per applies_to predicate) -----------------------------------
# Each yields a fully-formed ResolvedConstructionReturn for the given rule. The finders own
# geometry/placement; ``apply_construction_rules`` owns the solid + book-keeping.
def _find_framed_on_concrete(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """PT sill on top of a concrete wall — for the framed wall AND for the joists.

    **One board, one return.** The framed wall above and the floor beside it land on the same
    plate: the wall's own 2x6 mudsill runs the length of the pour and the I-joists and their
    rim bear on it too. Two rules — one per element — would bill that plate twice over every
    run where both are present, which is most of this basement, so the run is the **union**
    of the framed-wall stack runs and the floor systems' bearing runs on the same wall.

    Without the union there is a real coverage gap: W-B-CN carries 14.22 LF of wall against
    only 10.17 LF of plate, and W-B-CS 13.83 against 13.00 — the remainder is the stretch
    where a floor bears and no framed wall stacks, which would order no plate at all.

    The plate sits **on the concrete**, at ``lower.z1_m``, not at the framed wall's own base
    — a flat-bearing-seat wall's base sits well above the pour, and the plate is what bridges
    the gap between them.
    """
    lap = rule.dimension.meters if rule.dimension is not None else 0.0381  # 1.5"
    by_storey = _walls_by_storey(model)
    ordered = sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
    flat_plate = cross_section(_SILL_PLATE_MEMBER)
    for lower in model.walls:
        lower_asm = model.plan.library.resolve_assembly(lower.assembly)
        if lower_asm is None or not _is_concrete(lower_asm):
            continue
        a0, a1 = lower.axis
        span = length(sub(a1, a0))
        if span < _EPS:
            continue
        direction = unit(sub(a1, a0))

        # ``a0``/``direction`` bound as defaults, not closed over: the helper is only ever
        # called inside this iteration, but a late-binding closure over a loop variable is
        # the kind of thing that is true until someone moves the call (ruff B023).
        def _project(point: tuple[float, float],
                     a0: tuple[float, float] = a0,
                     direction: tuple[float, float] = direction) -> float:
            v = sub(point, a0)
            return v[0] * direction[0] + v[1] * direction[1]

        # --- what lands on this pour ------------------------------------------------
        # Framed walls in the first storey above that carries a collinear wall over it.
        lower_i = next((i for i, s in enumerate(ordered) if s.tag == lower.storey), None)
        if lower_i is None:
            continue
        pieces: list[tuple[float, float, object]] = []
        for upper_s in ordered[lower_i + 1:]:
            hits = []
            for upper in by_storey.get(upper_s.tag, []):
                upper_asm = model.plan.library.resolve_assembly(upper.assembly)
                if upper_asm is None or _framed_wood_layer(upper_asm) is None:
                    continue
                if _is_concrete(upper_asm):  # a concrete tier on concrete is not framed
                    continue
                segment = _stack_overlap(lower, upper)
                if segment is not None:
                    hits.append((upper, upper_asm, segment))
            if not hits:
                continue
            for upper, upper_asm, (p0, p1) in hits:
                t0, t1 = sorted((_project(p0), _project(p1)))
                pieces.append((t0, t1, (upper, upper_asm)))
            break  # first storey above with a stack owns this concrete wall

        # Floor systems whose joists bear on this wall — the same plate, one element down.
        for storey in model.plan.storeys:
            for system in model.plan.storey_elements(storey.tag):
                if not isinstance(system, FloorSystem):
                    continue
                if lower.tag not in system.joists.bearing_refs:
                    continue
                run_segment = _floor_run_on_wall(lower, system)
                if run_segment is None:
                    continue
                t0, t1 = sorted(_project(p) for p in run_segment)
                pieces.append((t0, t1, (system, storey)))
        if not pieces:
            continue

        # --- the union ---------------------------------------------------------------
        # Merged so the board is billed once. A merged run takes its width, its side-shift
        # and its condition key from the framed wall on it when there is one — that is the
        # board the carpenter sets — and falls back to the flat-laid 2x4 ledge plate where a
        # floor bears on bare pour with nothing stacked over it.
        pieces.sort(key=lambda piece: piece[0])
        merged: list[tuple[float, float, list]] = []
        for t0, t1, owner in pieces:
            if merged and t0 <= merged[-1][1] + _EPS:
                prev0, prev1, owners = merged[-1]
                merged[-1] = (prev0, max(prev1, t1), [*owners, owner])
            else:
                merged.append((t0, t1, [owner]))

        for t0, t1, owners in merged:
            run = t1 - t0
            if run < _MIN_STACK_OVERLAP_M:
                continue
            p0 = add(a0, scale(direction, t0))
            framed = next((o for o in owners if isinstance(o[0], ResolvedWall)), None)
            floors = [o for o in owners if not isinstance(o[0], ResolvedWall)]
            floor_tags = tuple(o[0].tag for o in floors)
            if framed is not None:
                upper, upper_asm = framed
                bearing = _framed_wood_layer(upper_asm)
                width = bearing.thickness.meters
                # ``_stack_overlap`` returns the run on the *lower* wall's axis, but the
                # plate belongs under the upper wall's studs, and an ``alignment=face(...)``
                # wall's axis is not its centreline. Slide the strip sideways onto the
                # structure band the studs are laid in — the same correction
                # resolve/floors.py and stairs/bearing.py already make.
                anchor = add(p0, sub(band_axis(upper.axis, _structure_polygon(upper))[0],
                                     upper.axis[0]))
                lo, hi = -width / 2.0, width / 2.0
                uid = f"CR-{lower.uid}-{upper.uid}-sill"
                storey_tag = upper.storey
                element_tags = (lower.tag, upper.tag, *floor_tags)
                returning = bearing.name
                condition = _condition_key("wall_foundation", lower.assembly, upper.assembly)
            else:
                system, storey = floors[0]
                # Land the plate on the deck side of the wall — the bearing ledge is the
                # face the joists come from, not the middle of a 16" pier section.
                width = flat_plate.depth_m       # laid flat: the 3.5" face bears
                n = normal(direction)
                ring = [p.xy_m for p in system.outline]
                centroid = (sum(p[0] for p in ring) / len(ring),
                            sum(p[1] for p in ring) / len(ring))
                toward = sub(centroid, p0)
                side = 1.0 if (toward[0] * n[0] + toward[1] * n[1]) >= 0.0 else -1.0
                far = side * lower.thickness_m / 2.0
                near = side * (lower.thickness_m / 2.0 - width)
                anchor = p0
                lo, hi = min(near, far), max(near, far)
                uid = f"CR-{lower.uid}-{system.uid}-sill"
                storey_tag = storey.tag
                element_tags = (lower.tag, *floor_tags)
                returning = _SILL_PLATE_MEMBER
                condition = _condition_key("floor_foundation", lower.assembly)
            gasket_product, gasket_t = _sill_gasket(
                framed[1] if framed is not None else None,
                model.plan.library.resolve_assembly(lower.assembly))
            yield ResolvedConstructionReturn(
                uid=uid,
                tag=rule.tag, storey=storey_tag, kind=rule.kind,
                applies_to=rule.applies_to, takeoff_category=rule.takeoff_category,
                material_ref="kdat",
                element_tags=element_tags,
                outline=_strip(anchor, direction, run, lo, hi),
                # On the pour, not at the framed wall's base — a flat-bearing-seat wall's
                # base sits well above it, and the plate is what bridges them.
                z0_m=lower.z1_m, z1_m=lower.z1_m + lap, thickness_m=width, length_m=run,
                lap_m=lap, thermal_continuity=False, sealant="sill-gasket",
                flashing="capillary-break", returning_layer=returning,
                gasket_product=gasket_product, gasket_thickness_m=gasket_t,
                condition_key=condition,
            )
    yield from _framed_on_slab(model, rule, lap)


def _framed_on_slab(model: ResolvedModel, rule: ConstructionRule,
                    lap: float) -> Iterator[ResolvedConstructionReturn]:
    """The same PT sill where a framed wall stands on a concrete *slab* rather than a wall.

    IRC R317.1(2)/(3) does not care which pour it is: wood in direct contact with concrete
    or resting on a slab in contact with the ground is preservative-treated, over a sill
    gasket, over a capillary break. Every basement partition in a house with a slab floor
    needs this detail — catlin's sauna, ESS-closet and bathroom partitions among them.

    Matched geometrically, not by tag: the wall's base sits at the slab's top face within a
    plate's thickness, and its axis midpoint falls inside the slab's outline. Nothing here
    fires for a wall on a wall — that is the case above, which owns the storey-stack
    condition key and would otherwise bill the same plate twice.
    """
    from shapely.geometry import Point, Polygon

    slabs = [solid for solid in model.solids
             if solid.category == "slab" and len(solid.outline) >= 3
             and _is_concrete_ref(model, solid.assembly)]
    if not slabs:
        return
    stacked_on_concrete = set()
    for wall in model.walls:
        lower_asm = model.plan.library.resolve_assembly(wall.assembly)
        if lower_asm is not None and _is_concrete(lower_asm):
            for other in model.walls:
                if other is not wall and _stack_overlap(wall, other) is not None:
                    stacked_on_concrete.add(other.tag)
    for wall in model.walls:
        if wall.tag in stacked_on_concrete or wall.is_foundation:
            continue
        asm = model.plan.library.resolve_assembly(wall.assembly)
        if asm is None or _is_concrete(asm):
            continue
        bearing = _framed_wood_layer(asm)
        if bearing is None:
            continue
        a0, a1 = wall.axis
        run = length(sub(a1, a0))
        if run < _MIN_STACK_OVERLAP_M:
            continue
        mid = ((a0[0] + a1[0]) / 2.0, (a0[1] + a1[1]) / 2.0)
        slab = next((s for s in slabs
                     if abs(s.z1_m - wall.z0_m) <= lap + _EPS
                     and Polygon(s.outline).buffer(_EPS).contains(Point(mid))), None)
        if slab is None:
            continue
        width = bearing.thickness.meters
        direction = unit(sub(a1, a0))
        anchor = add(a0, sub(band_axis(wall.axis, _structure_polygon(wall))[0],
                             wall.axis[0]))
        gasket_product, gasket_t = _sill_gasket(asm)
        yield ResolvedConstructionReturn(
            uid=f"CR-{slab.uid}-{wall.uid}-sill",
            tag=rule.tag, storey=wall.storey, kind=rule.kind,
            applies_to=rule.applies_to, takeoff_category=rule.takeoff_category,
            material_ref="kdat",
            element_tags=(slab.tag, wall.tag),
            outline=_strip(anchor, direction, run, -width / 2.0, width / 2.0),
            z0_m=wall.z0_m, z1_m=wall.z0_m + lap, thickness_m=width, length_m=run,
            lap_m=lap, thermal_continuity=False, sealant="sill-gasket",
            flashing="capillary-break", returning_layer=bearing.name,
            gasket_product=gasket_product, gasket_thickness_m=gasket_t,
            condition_key=None,
        )


def _is_concrete_ref(model: ResolvedModel, assembly: str | None) -> bool:
    if assembly is None:
        return False
    asm = model.plan.library.resolve_assembly(assembly)
    return asm is not None and _is_concrete(asm)


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
