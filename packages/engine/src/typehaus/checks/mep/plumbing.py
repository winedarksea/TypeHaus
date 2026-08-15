"""Plumbing checks (→ Permit-ready plan set Phase 2) — the family index.

The checks themselves live in three topic modules, one band each, because one file held
all of them and grew past the point where any of it could be read:

* ``plumbing_supply`` — potable water: hydrant bury depth and freeze protection, hot-water
  insulation, visible-pipe material preference.
* ``plumbing_dwv`` — drain/waste/vent: slope, vent termination and reachability, trap-arm
  length, fixture-unit sizing, and the wet-wall occupancy/bearing pair.
* ``plumbing_concrete`` — the pour-day band: sleeve alignment and coverage, under-slab
  bedding cover, footing clearance, sewer exit invert.

``mep.sleeve_alignment`` is the pre-pour guarantee this family was built around: a
cast-in-place sleeve more than 1/2" off the fixture's expected drain point moves before the
concrete crew pours, so it is a CODE-tier FAIL, not an advisory suggestion.

Sizing tables come from ``typehaus.takeoff.plumbing_calc`` — the same functions the
plumbing reader uses, so the permit finding and the public page can never disagree.

This module stays importable under its original name: it is the import every call site
already names, and importing it is what registers all sixteen checks.
"""

from __future__ import annotations

from typehaus.checks.mep.plumbing_concrete import (  # noqa: F401 - re-export + register
    _missing_sleeve_findings,
    footing_clearance,
    sewer_exit_invert,
    sleeve_alignment,
    sleeve_coverage,
    under_slab_burial,
)
from typehaus.checks.mep.plumbing_dwv import (  # noqa: F401 - re-export + register
    drain_slope,
    pipe_sizing,
    trap_arm_length,
    vent_reachability,
    vent_termination_height,
    wet_wall_bearing,
    wet_wall_occupancy_check,
)
from typehaus.checks.mep.plumbing_supply import (  # noqa: F401 - re-export + register
    exterior_hydrant_protection,
    hot_water_insulation,
    hydrant_freeze_depth,
    pipe_material_preference,
)
