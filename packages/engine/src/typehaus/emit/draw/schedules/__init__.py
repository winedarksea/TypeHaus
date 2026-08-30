"""Table pages of the permit set, one module per trade.

``sheets.py`` owns the sheet *index* — what pages exist, in what order, at what size.
This package owns what goes on the table pages themselves, which is where nearly all of
that module's length was. The split is by trade because that is how the sheets are
numbered (A-6xx, S-1xx, E-6xx) and how a reader looks for them.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.architectural import (
    _write_cover,
    _write_energy_sheet,
    _write_general_notes,
    _write_opening_schedule,
)
from typehaus.emit.draw.schedules.compare import write_compare_sheet
from typehaus.emit.draw.schedules.electrical import (
    _has_data_content,
    _write_data_schedule,
    _write_luminaire_schedule,
    _write_panel_schedule,
)
from typehaus.emit.draw.schedules.structural import (
    _write_framing_bom,
    _write_engineering_register,
    _write_hardware_schedule,
)
from typehaus.emit.draw.schedules.tables import _add_table

__all__ = [
    "_add_table",
    "_has_data_content",
    "_write_cover",
    "_write_data_schedule",
    "_write_energy_sheet",
    "_write_framing_bom",
    "_write_general_notes",
    "_write_engineering_register",
    "_write_hardware_schedule",
    "_write_luminaire_schedule",
    "_write_opening_schedule",
    "_write_panel_schedule",
    "write_compare_sheet",
]
