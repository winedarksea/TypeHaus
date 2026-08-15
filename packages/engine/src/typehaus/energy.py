"""A transparent block-load estimate, not a replacement for Manual J (M5 WP5.3).

This module is the import surface, not the implementation. The estimate now lives with the
other advisory physics analyses it already shared helpers with, in
:mod:`typehaus.checks.building_science` — ``energy_scope`` (what is inside the thermal
boundary, and how much of each plane a zone owns) and ``energy_load`` (the UA and air-side
arithmetic over that scope). It belongs there because it *is* one of them: it reads the WWR
check's facade helpers, ``checks.code.mn_energy`` reads its conditioned-storey rule back,
and its report ships in model.json's ``building_science`` block beside ``wwr`` and
``condensation``.

Everything the pass ever exported stays reachable from ``typehaus.energy`` — the CLI, the
HVAC take-off, the energy sheet, the MN energy check and model.json all import it here.
"""

from __future__ import annotations

from typehaus.checks.building_science.energy_load import (
    _AIR_SENSIBLE_BTU_PER_CFM_F,
    _GROUND_COUPLED_KINDS,
    EnergyReport,
    LoadComponent,
    _assembly_r_value,
    _infiltration_cfm,
    _two_by_four_vs_six,
    _ventilation_cfm,
    estimate_block_load,
)
from typehaus.checks.building_science.energy_scope import (
    _FREESTANDING_SLAB_PREFIXES,
    _FREESTANDING_WALL_PREFIXES,
    _M2_TO_FT2,
    _M3_TO_FT3,
    _WALL_SCOPE_SLOP_M,
    _WALL_SIDE_PROBE_FRACTIONS,
    _WALL_SIDE_PROBE_SLOP_M,
    _conditioned_rooms,
    _is_envelope_wall,
    _opening_in_scope,
    _polygon_scope_fraction,
    _room_scope,
    _stands_between_conditioned_rooms,
    _storey_is_conditioned,
    _volume_ft3,
    _wall_scope_fraction,
)

__all__ = [
    "EnergyReport",
    "LoadComponent",
    "estimate_block_load",
    # Private, but imported by name elsewhere in the tree (checks.code.mn_energy reads
    # ``_storey_is_conditioned``; the energy-sheet tests read ``_is_envelope_wall``), so the
    # whole pre-split surface stays addressable from this module.
    "_AIR_SENSIBLE_BTU_PER_CFM_F",
    "_FREESTANDING_SLAB_PREFIXES",
    "_FREESTANDING_WALL_PREFIXES",
    "_GROUND_COUPLED_KINDS",
    "_M2_TO_FT2",
    "_M3_TO_FT3",
    "_WALL_SCOPE_SLOP_M",
    "_WALL_SIDE_PROBE_FRACTIONS",
    "_WALL_SIDE_PROBE_SLOP_M",
    "_assembly_r_value",
    "_conditioned_rooms",
    "_infiltration_cfm",
    "_is_envelope_wall",
    "_opening_in_scope",
    "_polygon_scope_fraction",
    "_room_scope",
    "_stands_between_conditioned_rooms",
    "_storey_is_conditioned",
    "_two_by_four_vs_six",
    "_ventilation_cfm",
    "_volume_ft3",
    "_wall_scope_fraction",
]
