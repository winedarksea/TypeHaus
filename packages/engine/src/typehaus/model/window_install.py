"""``WindowInstallFastening`` — a flanged window's install fasteners (decision #147).

Placed as ``WindowType.install_fastening``; ``takeoff/window_fasteners.py`` counts the fin
fasteners round each placed unit's perimeter, the corner fasteners and any jamb straps. A
flanged type without one is listed as unmodelled procurement, never graded.
"""

from __future__ import annotations

from pydantic import Field

from typehaus.model.base import HausModel


class WindowInstallFastening(HausModel):
    """Fin fastener and pitch, its first fastener off each corner, and optional straps."""

    part: str
    fin_pitch_in: float = Field(gt=0)
    corner_offset_in: float = Field(ge=0)
    jamb_straps_per_side: int = Field(default=0, ge=0)
    strap_part: str | None = None
    code_row: str = ""
    source: str = ""
