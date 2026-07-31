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

_M_TO_IN = 39.37007874015748

# MN Plumbing Code Table 702.1 (private). A tub-shower is one fixture, valued as a tub.
DFU_BY_SYMBOL: dict[str, float] = {
    "toilet": 3.0,          # water closet, 1.6 gpf gravity tank
    "lavatory": 1.0,
    "vanity": 1.0,          # a lavatory in a cabinet
    "tub": 2.0,
    "tub-shower": 2.0,
    "shower": 2.0,
    "kitchen-sink": 2.0,    # incl. food-waste grinder / dishwasher branch
    "washer": 3.0,          # clothes washer, 2" standpipe
    # A stacked pair is one washer for fixture-unit purposes: the heat-pump dryer above it
    # discharges condensate to an indirect waste, which is not a drainage fixture.
    "washer-dryer-stacked": 3.0,
    "dishwasher": 2.0,
    "laundry-sink": 2.0,
    "floor-drain": 2.0,
}

# MN Plumbing Code Table 610.3 (private): (total, hot, cold) WSFU per fixture.
WSFU_BY_SYMBOL: dict[str, tuple[float, float, float]] = {
    "toilet": (2.5, 0.0, 2.5),   # flush tank
    "lavatory": (1.0, 0.75, 0.75),
    "vanity": (1.0, 0.75, 0.75),
    "tub": (4.0, 3.0, 3.0),
    "tub-shower": (4.0, 3.0, 3.0),
    "shower": (2.0, 1.5, 1.5),
    "kitchen-sink": (1.5, 1.0, 1.0),
    "washer": (4.0, 3.0, 3.0),
    "washer-dryer-stacked": (4.0, 3.0, 3.0),  # the dryer half takes no water
    "dishwasher": (1.5, 1.5, 0.0),
    "laundry-sink": (1.5, 1.0, 1.0),
    "hydrant": (2.5, 0.0, 2.5),  # hose bibb
}

# MN Plumbing Code Table 703.2: max DFU on a horizontal drainage branch, by size (in).
DRAIN_BRANCH_CAPACITY_DFU: tuple[tuple[float, float], ...] = (
    (1.25, 1.0),
    (1.5, 3.0),
    (2.0, 6.0),
    (3.0, 35.0),
    (4.0, 216.0),
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

# MN Plumbing Code Table 1002.2: max trap-arm length (inches) by trap-arm size (inches).
TRAP_ARM_MAX_IN: dict[float, float] = {
    1.25: 30.0,
    1.5: 42.0,
    2.0: 60.0,
    3.0: 72.0,
    4.0: 120.0,
}


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
        wsfu = WSFU_BY_SYMBOL.get(symbol)
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


def required_drain_diameter_in(dfu: float) -> float | None:
    """Smallest horizontal-branch size carrying ``dfu`` (Table 703.2); None = beyond it."""
    for size_in, capacity in DRAIN_BRANCH_CAPACITY_DFU:
        if dfu <= capacity + 1e-9:
            return size_in
    return None


def required_supply_size_in(wsfu: float) -> float | None:
    """Smallest supply branch carrying ``wsfu`` (simplified Table 610.4 column)."""
    for size_in, capacity in SUPPLY_BRANCH_CAPACITY_WSFU:
        if wsfu <= capacity + 1e-9:
            return size_in
    return None


def trap_arm_limit_in(diameter_m: float) -> float | None:
    """Max trap-arm length for a trap-arm diameter (Table 1002.2); None = no row."""
    diameter_in = round(diameter_m * _M_TO_IN, 2)
    for size_in, limit in TRAP_ARM_MAX_IN.items():
        if abs(diameter_in - size_in) < 0.06:
            return limit
    return None
