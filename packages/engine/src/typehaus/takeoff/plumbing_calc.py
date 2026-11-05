"""Fixture-unit arithmetic — one module, two consumers (checks + plumbing reader).

Shared-derivation invariant (same as ``takeoff/hvac.py::heating_zones`` ↔
``checks/mep/hvac.py``): the ``mep.pipe_sizing``/``mep.trap_arm_length`` checks and the
plumbing reader's tables import these functions, so the permit finding and the public
page can never disagree.

Tables are the Minnesota Plumbing Code (chapter 4714, a UPC adoption):
- Table 702.1 — drainage fixture units (DFU), private use
- Table 610.3 — water supply fixture units (WSFU), private use
- Table 703.2 — horizontal drainage branch capacity in DFU by pipe size
- Table 1002.2 — maximum trap-arm (trap to vent) length by trap-arm size

Values are keyed by the fixture type's ``plan_symbol`` — the one stable vocabulary the
placeable library already carries. A symbol with no row returns None, and every consumer
reports UNKNOWN rather than guessing (never a silent zero).
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN  # noqa: F401 - cli/route_support imports it here

# The code tables and fixture-unit rows live in resolve (the router reads them too);
# re-exported here, where the take-off, the checks and the tests have always imported them.
from typehaus.resolve.fixture_units import (  # noqa: F401
    HOST_COUNTED_SYMBOLS,
    WSFU_BY_SYMBOL,
    FixtureUnits,
    _placeable_types,
    fixture_units,
)
from typehaus.resolve.plumbing_tables import (  # noqa: F401
    BATHROOM_GROUP_SYMBOLS,
    DFU_BY_SYMBOL,
    DRAIN_BRANCH_CAPACITY_DFU,
    MINIMUM_DRAIN_IN_BY_SYMBOL,
    TRAP_ARM_MAX_IN,
    WET_VENT_HORIZONTAL_MIN_IN,
    WET_VENT_MIN_IN,
    WET_VENT_VERTICAL_MAX_FIXTURES,
    WET_VENT_VERTICAL_MAX_IN,
    WET_VENT_VERTICAL_UPPER_DFU_MAX,
    required_drain_diameter_in,
    trap_arm_limit_in,
)

# Simplified from MN Plumbing Code Table 610.4: max WSFU by supply branch size,
# assuming 46–60 psi street pressure and a developed length under 100' — the common
# residential column. The assumption is recorded here because the full table is
# pressure- and length-indexed and this module deliberately carries one column of it.
SUPPLY_BRANCH_CAPACITY_WSFU: tuple[tuple[float, float], ...] = (
    (0.5, 4.0),
    (0.75, 14.0),
    (1.0, 32.0),
    (1.25, 64.0),
)

def branch_load(run_serves: tuple[str, ...], units_by_tag: dict[str, FixtureUnits],
                system: str) -> tuple[float | None, tuple[str, ...]]:
    """Accumulated fixture units on one run: (load, unresolved fixture tags).

    ``system`` is the run's PipeSystem value; drain runs accumulate DFU, water runs the
    matching WSFU column. A served tag with no row (or a None table value) is returned as
    unresolved — the caller reports UNKNOWN, never a partial sum passed off as complete."""
    total = 0.0
    unresolved: list[str] = []
    for tag in run_serves:
        row = units_by_tag.get(tag)
        value = None
        if row is not None:
            if system == "drain":
                value = row.dfu
            elif system == "water_hot":
                value = row.wsfu_hot
            elif system == "water_cold":
                value = row.wsfu_cold
        if value is None:
            unresolved.append(tag)
        else:
            total += value
    return (total if not unresolved else None), tuple(unresolved)


def required_supply_size_in(wsfu: float) -> float | None:
    """Smallest supply branch carrying ``wsfu`` (simplified Table 610.4 column)."""
    for size_in, capacity in SUPPLY_BRANCH_CAPACITY_WSFU:
        if wsfu <= capacity + 1e-9:
            return size_in
    return None
