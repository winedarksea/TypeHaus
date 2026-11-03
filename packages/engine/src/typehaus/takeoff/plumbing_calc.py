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

from dataclasses import dataclass

from typehaus.quantities import M_PER_IN  # noqa: F401 - cli/route_support imports it here

# The code tables live in resolve/plumbing_tables (the router reads them too); re-exported
# here, where the take-off, the checks and the tests have always imported them.
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

# MN Plumbing Code Table 610.3 (private): (total, hot, cold) WSFU per fixture.
WSFU_BY_SYMBOL: dict[str, tuple[float, float, float]] = {
    "toilet": (2.5, 0.0, 2.5),   # flush tank
    "toilet-wall-hung": (2.5, 0.0, 2.5),  # concealed flush tank, same demand
    "lavatory": (1.0, 0.75, 0.75),
    "lavatory-wall-hung": (1.0, 0.75, 0.75),
    "drawer-vanity": (1.0, 0.75, 0.75),
    "drawer-vanity-indy": (1.0, 0.75, 0.75),
    "sektion-vanity-indy": (1.0, 0.75, 0.75),
    "sunnersta-sink": (1.0, 0.75, 0.75),
    "door-drawer-vanity": (1.0, 0.75, 0.75),
    "sektion-vanity": (1.0, 0.75, 0.75),
    "vanity": (1.0, 0.75, 0.75),
    "solid-surface-vanity": (1.0, 0.75, 0.75),
    "tub": (4.0, 3.0, 3.0),
    "kohler-underscore-6036": (4.0, 3.0, 3.0),
    "kohler-underscore-6032": (4.0, 3.0, 3.0),
    "tub-shower": (4.0, 3.0, 3.0),
    "shower": (2.0, 1.5, 1.5),
    "shower-neo-angle": (2.0, 1.5, 1.5),
    "kitchen-sink": (1.5, 1.0, 1.0),
    "kitchen-sink-undermount-single": (1.5, 1.0, 1.0),
    "washer": (4.0, 3.0, 3.0),
    "washer-dryer-stacked": (4.0, 3.0, 3.0),  # the dryer half takes no water
    "dishwasher": (1.5, 1.5, 0.0),
    "laundry-sink": (1.5, 1.0, 1.0),
    "hydrant": (2.5, 0.0, 2.5),  # hose bibb
}

# Trim mounted on a fixture that carries the row (a Roman tub filler on its bath): the
# host's row is the demand, so the trim's is zero rather than missing. A branch serving the
# trim names the host too, which is what sizes it.
HOST_COUNTED_SYMBOLS: frozenset[str] = frozenset({"roman-tub-filler"})

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

@dataclass(frozen=True)
class FixtureUnits:
    """One fixture's code loads. ``None`` fields mean the table has no row — UNKNOWN."""

    tag: str
    symbol: str
    room: str | None
    dfu: float | None
    wsfu_total: float | None
    wsfu_hot: float | None
    wsfu_cold: float | None

    def as_dict(self) -> dict:
        return {
            "tag": self.tag, "symbol": self.symbol, "room": self.room, "dfu": self.dfu,
            "wsfu_total": self.wsfu_total, "wsfu_hot": self.wsfu_hot,
            "wsfu_cold": self.wsfu_cold,
        }


def _placeable_types(plan) -> dict:
    return {t.tag: t for t in (*plan.library.fixture_types, *plan.library.appliance_types)}


def fixture_units(plan) -> list[FixtureUnits]:
    """Per-fixture DFU/WSFU rows for every drain- or water-needing placeable."""
    from typehaus.model.enums import Service

    types = _placeable_types(plan)
    rows: list[FixtureUnits] = []
    for element in plan.all_elements():
        if element.element_kind not in ("Fixture", "Appliance"):
            continue
        placeable_type = types.get(element.type_ref)
        if placeable_type is None:
            continue
        needs = placeable_type.needs
        if not needs & {Service.DRAIN, Service.WATER_HOT, Service.WATER_COLD}:
            continue
        symbol = placeable_type.plan_symbol
        dfu = DFU_BY_SYMBOL.get(symbol) if Service.DRAIN in needs else 0.0
        wsfu = (0.0, 0.0, 0.0) if symbol in HOST_COUNTED_SYMBOLS else WSFU_BY_SYMBOL.get(symbol)
        rows.append(FixtureUnits(
            tag=element.tag, symbol=symbol, room=getattr(element, "room", None),
            dfu=dfu,
            wsfu_total=wsfu[0] if wsfu is not None else None,
            wsfu_hot=(wsfu[1] if wsfu is not None and Service.WATER_HOT in needs else
                      0.0 if wsfu is not None else None),
            wsfu_cold=wsfu[2] if wsfu is not None else None,
        ))
    return rows


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
