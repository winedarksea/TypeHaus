"""Per-fixture DFU/WSFU rows — read by the take-off, the checks and the router alike.

Moved out of ``takeoff/plumbing_calc.py`` (which re-exports every name) so the trap-arm walk
in ``resolve/mep_trap_arm`` can size a wet vent off the same rows the permit finding uses.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.resolve.plumbing_tables import DFU_BY_SYMBOL

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
