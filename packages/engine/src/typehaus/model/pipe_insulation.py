"""Pipe insulation, declared once (decision #154): the ``DuctStandard.insulations`` pattern.

``PipeRun.insulation`` stays a string; it names a ``PipeInsulationRow`` here (and is the
``[pipe_insulation]`` price key). ``mep.pipe_insulation`` grades the row's ``r_value``
against the R-3 MN 1322 inherits from the 2012 IECC R403.4.2.
"""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length


class PipeInsulationRow(HausModel):
    """A pipe-insulation spec: its wall and the R the product publishes for it.

    ``r_value`` is the product's own figure for that wall, never derived here: pipe R is
    not thickness x R/in (cylindrical geometry). An unread figure stays ``None`` and
    grades UNKNOWN.
    """

    spec: str
    thickness: Length
    r_value: float | None = None
    material_ref: str | None = None
    product_ref: str | None = None
    source: str


@register_element
class PipeInsulationStandard(Element):
    """The house's pipe-insulation specs, one per plan (``mep.pipe_insulation``)."""

    insulations: tuple[PipeInsulationRow, ...] = ()

    def insulation(self, spec: str | None) -> PipeInsulationRow | None:
        return next((r for r in self.insulations if spec and r.spec == spec), None)


for _name, _obj in (("PipeInsulationRow", PipeInsulationRow),
                    ("PipeInsulationStandard", PipeInsulationStandard)):
    register_constructor(_name, _obj)
