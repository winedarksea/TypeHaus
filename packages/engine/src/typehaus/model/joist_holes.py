"""``JoistHoleChart`` — an I-joist maker's ALLOWABLE HOLES ladder, keyed by member.

The joist sibling of ``PublishedHole`` (``refs_holes.py``): where a header carries ONE row,
an I-joist's chart is a LADDER — the bigger the hole, the further from the support it must
sit (ESR-1153 Fig. 2 Table A). It lives on the ``Library`` and is matched to a floor by the
resolved member profile, so every deck of that member is graded without a per-floor field.
``resolve/mep_hole_chart.ijoist_hole_verdict`` reads it; the router and the check share it.
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.refs_holes import PublishedHole
from typehaus.quantities import Length


class JoistHoleChart(HausModel):
    """One member's published round-hole ladder, distances from an END support.

    ``rows`` are ``PublishedHole`` rows, each a ``max_diameter`` (the column) and its
    ``zone_from_bearing`` (support face to the hole's nearest EDGE). Only end supports (Table
    A) are transcribed: a hole near an intermediate support is UNKNOWN, never graded on A.
    """

    #: The member, spelled as the model resolves it (``"11.875 TJI 230"``): the retype guard.
    member: str
    #: The document, edition and page.
    source: str
    #: The table read, in its own words.
    table: str
    rows: tuple[PublishedHole, ...]
    #: Clear distance between two holes as a multiple of the largest hole's diameter.
    min_spacing_diameters: float | None = None
    #: A hole this small may go anywhere outside ``field_hole_zone`` of each support.
    field_hole_max: Length | None = None
    field_hole_zone: Length | None = None
    #: What the ladder assumes (load pattern, span type). Printed, compared against nothing.
    condition: str = ""

    @model_validator(mode="after")
    def _chart_is_readable(self) -> JoistHoleChart:
        for name in ("member", "source", "table"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"JoistHoleChart.{name} must name what was read")
        if not self.rows:
            raise ValueError("JoistHoleChart.rows must hold at least one row")
        sizes = [row.max_diameter.meters for row in self.rows]
        if sizes != sorted(sizes) or len(set(sizes)) != len(sizes):
            raise ValueError("JoistHoleChart.rows must ascend by max_diameter")
        if any(row.zone_from_bearing is None for row in self.rows):
            raise ValueError("every JoistHoleChart row states its zone_from_bearing")
        if (self.field_hole_max is None) != (self.field_hole_zone is None):
            raise ValueError("state field_hole_max and field_hole_zone together, or neither")
        if self.min_spacing_diameters is not None and self.min_spacing_diameters <= 0.0:
            raise ValueError("JoistHoleChart.min_spacing_diameters must be positive")
        return self
