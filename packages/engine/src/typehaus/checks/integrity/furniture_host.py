"""An explicitly fixture-supported furnishing must name its actual support."""

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed
from typehaus.model.spatial import Fixture, Furniture


@check(Tier.INTEGRITY, "integrity.furniture_fixture_host")
def furniture_fixture_host(ctx: CheckContext) -> list[Finding]:
    elements = {element.tag: (storey.tag, element) for storey in ctx.plan.storeys
                for element in ctx.plan.storey_elements(storey.tag)}
    out = []
    for storey, element in elements.values():
        if not isinstance(element, Furniture) or element.host_fixture_ref is None:
            continue
        ref = element.host_fixture_ref
        found = elements.get(ref)
        tags = (element.tag, ref)
        if found is None or not isinstance(found[1], Fixture):
            out.append(failed("integrity.furniture_fixture_host",
                              f"{element.tag} names {ref}, which is not a placed fixture", tags))
        elif found[0] != storey or element.room is None or found[1].room != element.room:
            out.append(failed("integrity.furniture_fixture_host",
                              f"{element.tag} and fixture host {ref} must share a room and storey",
                              tags))
        else:
            out.append(passed("integrity.furniture_fixture_host",
                              f"{element.tag} is supported by fixture {ref}", tags))
    return out or [not_applicable("integrity.furniture_fixture_host",
                                  "no furnishings declare fixture support")]
