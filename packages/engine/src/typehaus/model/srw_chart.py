"""The section a segmental wall's published gravity-chart row assumes, as the house draws it.

A maker's gravity chart (Allan Block Table 1.3) is true for a SECTION: unit, setback, a cap on
top, a buried base course, wall rock, a drain, a compacted founding fill, a level bed. This is
that section, authored beside ``SegmentalWallSpec.published`` (the row quoted). The chart check
(``engineering/srw_chart``) compares every field to what the model draws and FAILs on drift.
"""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class SrwDrain(HausModel):
    """The drain pipe at the back of the base trench, and where it lets go."""

    #: Pipe as specified, e.g. "4 in perforated, in filter sock".
    pipe: str
    #: Tag of a FootingBedding whose ``wall_column`` receives it (an underground drainage
    #: system, the AB manual's alternative to daylight).
    outlet_ref: str


class SrwChartSection(HausModel):
    """What the quoted chart row assumes, per wall. Absent = the row is not claimed."""

    #: The row's column: the unit's setback (12 for "12° AB Stones only"). The wall's own
    #: batter must be at least this.
    batter_deg: float
    #: Friction angle of the soil row read (27 for the clay row); the soil must meet it.
    soil_phi_deg: float
    #: Cap unit's height; the chart's exposed height includes it.
    cap_height: Length
    #: Least buried block, and least wall rock behind the unit.
    min_buried: Length
    min_wall_rock: Length
    #: Founding-fill compaction, % of Standard Proctor, and the lift it is placed in (the
    #: house's own spec; nothing in the model draws it, so the check prints it).
    founding_compaction_pct: float
    lift: Length
    drain: SrwDrain | None = None


register_constructor("SrwDrain", SrwDrain)
register_constructor("SrwChartSection", SrwChartSection)
