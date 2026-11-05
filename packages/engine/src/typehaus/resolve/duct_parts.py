"""The ``duct_parts`` resolve stage: every part and hanger off the house's ``DuctStandard`` (#114).

After ``terminal_ducts`` (every run's final z) and before ``geometry``, which draws them.
Without a standard nothing is derived and nothing changes.
"""

from __future__ import annotations

from typing import Any

from typehaus.findings import Finding
from typehaus.resolve.duct_standard import duct_standard


def resolve_duct_parts(plan: Any, model: Any) -> list[Finding]:
    from typehaus.resolve.duct_branches import branch_parts
    from typehaus.resolve.duct_part_solids import part_solids
    from typehaus.resolve.duct_supports import derive_supports
    from typehaus.resolve.duct_terminations import end_landings, termination_parts

    standard, findings = duct_standard(plan)
    if standard is None:
        return findings
    model.duct_parts.extend(branch_parts(model, standard))
    model.duct_parts.extend(termination_parts(model, standard, end_landings(model)))
    model.duct_supports.extend(derive_supports(model, standard))
    part_solids(model)
    return findings
