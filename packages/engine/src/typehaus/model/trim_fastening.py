"""``TrimFastening`` — how a trim material is fixed to wood (decision #147).

Placed as ``Material.trim_fastening``; ``takeoff/trim_fasteners.py`` counts it per billed
run: ``(ceil(length / pitch) + 1) x rows``.
"""

from __future__ import annotations

from pydantic import Field

from typehaus.model.base import HausModel


class TrimFastening(HausModel):
    """The fastener (a catalog model), its pitch along the run, and rows across it."""

    part: str
    pitch_in: float = Field(gt=0)
    rows: int = Field(default=1, ge=1)
    # The prescriptive row this restates; empty means special (listed on S-001).
    code_row: str = ""
    source: str = ""
