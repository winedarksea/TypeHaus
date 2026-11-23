"""Which segmental walls leave the engineering register for the published-chart path.

IRC R404.4 (2018, unamended in the MN 2020 code; UpCodes) engages for walls "not laterally
supported at the top and that retain in excess of 48 inches of unbalanced fill, or retaining
walls exceeding 24 inches in height that resist lateral loads in addition to soil". A wall
inside neither limb needs no engineered design, and where its maker publishes a gravity chart
row the house has authored (``SegmentalWallSpec.chart`` + ``published``) it is read, not
designed (``engineering/srw_chart``, ``checks/structural/srw_chart``).

A leaf: ``segmental_wall`` (scope) and ``srw_chart`` (conditions) both read it.
"""

from __future__ import annotations

#: R404.4 limb 1: unbalanced fill must be IN EXCESS of this to engage.
R404_4_FILL_LIMIT_FT = 4.0


def on_chart_path(wall) -> bool:  # type: ignore[no-untyped-def]
    """The house claims a chart row for this wall and its fill is outside R404.4's limb 1.

    The added-lateral-load limb is a condition of the chart check (no surcharge on the
    terrace), so a drifted wall FAILs there instead of silently re-entering the register.
    """
    spec = getattr(wall, "srw", None)
    fill = getattr(wall, "unbalanced_fill", None)
    if spec is None or spec.chart is None or spec.published is None or fill is None:
        return False
    return fill.feet <= R404_4_FILL_LIMIT_FT + 1e-9
