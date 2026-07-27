"""Railing product takeoff, grouped by catalog type and storey."""

from typehaus.model.structure import Railing
from typehaus.resolve.model import ResolvedModel


def railing_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Count railing instances by their explicit product reference."""
    groups: dict[tuple[str, str], dict[str, object]] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, Railing):
                continue
            type_ref = element.type_ref or "(untyped railing)"
            key = (type_ref, storey.tag)
            row = groups.setdefault(key, {
                "type": element.type_ref,
                "storey": storey.tag,
                "count": 0,
                "tags": [],
            })
            row["count"] = int(row["count"]) + 1
            tags = row["tags"]
            assert isinstance(tags, list)
            tags.append(element.tag)
    return [
        {**groups[key], "tags": sorted(groups[key]["tags"])}
        for key in sorted(groups)
    ]
