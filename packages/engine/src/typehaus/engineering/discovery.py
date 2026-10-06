"""The requirements named by checks plus the engineering kinds that enumerate themselves."""

from collections.abc import Iterable, Mapping

from typehaus.engineering.item import EngineeringRecord
from typehaus.findings import Finding


def engineering_item_ids(
    results: Mapping[str, EngineeringRecord], findings: Iterable[Finding],
) -> tuple[str, ...]:
    named = {finding.engineering_item for finding in findings if finding.engineering_item}
    return tuple(sorted(named | set(results)))
