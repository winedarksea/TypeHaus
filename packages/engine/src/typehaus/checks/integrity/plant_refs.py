"""Every plant, bed, accent and pocket names something that exists."""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import Slab
from typehaus.model.landscape import Plant, PlantingBed, Trellis


def _error(msg: str, tag: str) -> Finding:
    return Finding(severity=Severity.ERROR, check_id="integrity.plant_type_ref", message=msg,
                   element_tags=(tag,), result=Result.FAIL)


@check(Tier.INTEGRITY, "integrity.plant_type_ref")
def plant_type_ref(ctx: CheckContext) -> list[Finding]:
    plan = ctx.plan
    types = {t.tag for t in plan.library.plant_types}
    materials = {m.tag for m in plan.library.materials}
    out: list[Finding] = []
    for ptype in plan.library.plant_types:
        for role in ("foliage", "bloom", "stem", "fruit"):
            ref = getattr(ptype, f"{role}_material")
            if ref and ref not in materials:
                out.append(_error(f"plant type {ptype.tag} names {role} material {ref!r}, "
                                  f"which the library lacks", ptype.tag))
    for element in plan.all_elements():
        if isinstance(element, Plant):
            refs = [element.type_ref]
            if element.trellis_ref and not isinstance(plan.by_tag(element.trellis_ref), Trellis):
                out.append(_error(f"{element.tag} is trained on {element.trellis_ref!r}, "
                                  f"which is not a Trellis", element.tag))
        elif isinstance(element, PlantingBed):
            refs = [element.type_ref]
            if element.accents is not None:
                refs.extend(element.accents.type_refs)
            if (element.grid is None) == (element.pockets is None):
                out.append(_error(f"bed {element.tag} needs exactly one of grid or pockets",
                                  element.tag))
            if (element.soil_depth or element.fill_depth) and len(element.outline) < 3:
                out.append(_error(f"bed {element.tag} builds soil or fill but has no "
                                  f"outline to build it over", element.tag))
            if element.grid is not None:
                refs.extend(element.grid.type_refs)
            if element.pockets is not None:
                refs.extend(element.pockets.type_refs)
                for slab in element.pockets.slab_refs:
                    if not isinstance(plan.by_tag(slab), Slab):
                        out.append(_error(f"bed {element.tag} plants pockets in {slab!r}, "
                                          f"which is not a Slab", element.tag))
        else:
            continue
        for ref in refs:
            if ref not in types:
                out.append(_error(f"{element.tag} names plant type {ref!r}, which the "
                                  f"library does not carry", element.tag))
    return out
