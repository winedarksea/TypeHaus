"""Derived sheet goods must name catalog materials; exterior openings must be flashed.

* ``integrity.derived_solid_material`` — a derived solid (opening flashing, a fitted cap,
  a formed drip) whose material the catalog does not have. The look falls back to a
  category colour and the IFC and inspector material rows are empty, all silently.
* ``integrity.opening_flashing_coverage`` — an exterior window or door the resolver drew
  no flashing for. ADVISORY (WARN, UNKNOWN): the opening may well be flashed on site, but
  the model says nothing about how, and a reader of the 3D would assume it was.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Result, advisory, failed, not_applicable, passed

_MATERIAL = "integrity.derived_solid_material"
_COVERAGE = "integrity.opening_flashing_coverage"


@check(Tier.INTEGRITY, _MATERIAL)
def derived_solid_material(ctx: CheckContext) -> list:
    catalog = {m.tag for m in ctx.plan.library.materials or ()}
    unknown: dict[str, list[str]] = {}
    for solid in ctx.model.solids:
        if solid.derived and solid.material and solid.material not in catalog:
            unknown.setdefault(solid.material, []).append(solid.tag)
    if not unknown:
        return [passed(_MATERIAL, "every derived solid names a catalog material")]
    return [failed(_MATERIAL,
                   f"{len(tags)} derived solid(s) name material {material!r}, which the "
                   f"catalog has no entry for (e.g. {sorted(tags)[0]})",
                   tuple(sorted(tags)[:5]),
                   fix="add the Material to the library, or name an existing one")
            for material, tags in sorted(unknown.items())]


def _weather_wall(wall) -> bool:
    """A wall with a cladding or a water-control layer has a weather face."""
    return any(layer.function == "cladding" or "water" in (layer.control or ())
               for layer in wall.layers)


@check(Tier.INTEGRITY, _COVERAGE)
def opening_flashing_coverage(ctx: CheckContext) -> list:
    walls = {wall.tag: wall for wall in ctx.model.walls}
    exterior = [o for o in ctx.model.openings if o.kind in ("window", "door")
                and o.host_wall in walls and _weather_wall(walls[o.host_wall])]
    if not exterior:
        return [not_applicable(_COVERAGE, "no window or door is in a wall with a weather face")]
    flashed = {s.host_ref for s in ctx.model.solids
               if s.category == "opening_flashing_membrane"}
    missing = sorted((o for o in exterior if o.tag not in flashed), key=lambda o: o.tag)
    if not missing:
        return [passed(_COVERAGE, f"all {len(exterior)} exterior openings draw their flashing")]
    return [advisory(
        _COVERAGE,
        f"ADVISORY — {o.tag}: an exterior {o.kind} in {o.host_wall} draws no opening "
        "flashing. Its wall has a weather face but no cladding layer of its own (a separate "
        "veneer, say), so no head, membrane or pan is derived and the model is silent on how "
        "this opening is flashed",
        (o.tag, o.host_wall), Result.UNKNOWN,
        fix="specify the flashing in the house's notes; a veneer's own opening flashing "
            "(IRC R703.8.5) is not modelled either")
        for o in missing]
