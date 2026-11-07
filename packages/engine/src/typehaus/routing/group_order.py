"""The order a bathroom group is laid in under UPC 908.2 (horizontal wet venting).

The dry-vented fixture's drain and its vent go first, then the wet-vented arms in flow order,
the water closet last (908.2.1.4). Roles come from the code text as quoted in
``houses/catlin/notes/mep_group_wet_vent_basis.md`` §1, §3:

* 908.2.1.3: a non-WC fixture is wet-vented only where the vent opening is not below its
  weir, so a wall-trapped lavatory cannot be wet-vented off a floor-level vent. It keeps its
  own dry vent and ties conventionally (908.2.1.5), unless it is the dry-vented fixture.
* 908.2.1: only one wet-vented drain may discharge upstream of the dry-vent connection.
* The most upstream floor-level fixture is dry-vented, so its drain passes the others on its
  way to the tie (§4 option S, §5 option Y): a sequential router lays the dry drain before it
  knows where the arms join. A lavatory dry-venting a tub upstream of it (§5 option X) is
  not chosen: the check grades its drop as a 908.1 vertical, an owner/AHJ question.
* 908.2.1.2: the wet vent is 2" for 4 DFU or less, 3" for 5 or more, its whole length — and
  never under 3" where a water closet discharges to it (710.1).
* A member the caller could not lay wet is held to its own vent (``own``); any free fixture
  may then carry the dry vent (908.2.1.1), so the WC can still be wet-vented.

Flow order is plan (Manhattan) distance to the group's tie, farthest first. Pure data in,
no model: ``cli/cmd_route_group`` measures the members.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.resolve.plumbing_tables import (
    MINIMUM_DRAIN_IN_BY_SYMBOL,
    WET_VENT_HORIZONTAL_MIN_IN,
)


@dataclass(frozen=True)
class Member:
    """One drained fixture of the group, as measured from the model."""

    tag: str
    symbol: str
    dfu: float
    #: Its trap weir sits at the floor (an under-floor trap): wet-ventable off a floor tee.
    floor_level: bool
    #: Plan distance from its drain point to the group's tie, metres.
    flow_m: float

    @property
    def is_wc(self) -> bool:
        return self.symbol.startswith("toilet")


@dataclass(frozen=True)
class GroupOrder:
    dry: str
    #: Wet-vented arms in laying order (flow order, upstream first), the WCs not among them.
    wet: tuple[str, ...]
    #: Water closets, laid last (908.2.1.4).
    last: tuple[str, ...]
    #: Members that keep their own dry vent and authored tie (908.2.1.3/908.2.1.5).
    own_vent: tuple[str, ...]
    #: Wet-vented members upstream of the dry fixture in flow order (908.2.1: at most one).
    upstream: tuple[str, ...]
    dfu: float
    wet_vent_in: float
    why: str

    @property
    def laying(self) -> tuple[str, ...]:
        return (self.dry, *self.wet, *self.last)


def group_order(members: list[Member], own: frozenset[str] = frozenset()
                ) -> GroupOrder | str:
    """The roles and laying order, or why the group cannot be wet-vented. ``own`` names
    members held to their own vent (a wet arm the caller could not lay)."""
    flow = sorted(members, key=lambda m: (-m.flow_m, m.tag))
    wcs = tuple(m.tag for m in flow if m.is_wc)
    others = [m for m in flow if not m.is_wc]
    floor = [m for m in others if m.floor_level and m.tag not in own]
    free = [m for m in others if m.tag not in own]
    if not free:
        return "no fixture but a water closet free to carry the dry vent"
    # The fallback: any free fixture may carry the dry vent (908.2.1.1), the WC then wet.
    dry = floor[0] if floor else free[0]
    eligible = [m for m in floor if m is not dry]
    up = [m for m in eligible if m.flow_m > dry.flow_m]
    # 908.2.1: one upstream at most — the nearest one keeps the wet vent, the rest their own.
    keep_up = up[-1:] if up else []
    wet = tuple(m.tag for m in eligible if m not in up or m in keep_up)
    held = tuple(m.tag for m in others if m is not dry and m.tag not in wet)
    laid = [m for m in members if m.tag in (dry.tag, *wet, *wcs)]
    dfu = sum(m.dfu for m in laid)
    size = max(next(d for limit, d in WET_VENT_HORIZONTAL_MIN_IN if dfu <= limit + 1e-9),
               *(MINIMUM_DRAIN_IN_BY_SYMBOL.get(m.symbol, 0.0) for m in laid))  # 710.1
    why = (f"{dry.tag} is dry-vented "
           + ("(the most upstream floor-level fixture)" if dry in floor
              else "(no floor-level fixture free; 908.2.1.1)")
           + (f"; {', '.join(held)} keep their own vent" if held else "")
           + f"; {dfu:g} DFU on the wet vent, Ø{size:g}\" its whole length (908.2.1.2)")
    return GroupOrder(dry=dry.tag, wet=wet, last=wcs, own_vent=held,
                      upstream=tuple(m.tag for m in keep_up), dfu=dfu, wet_vent_in=size,
                      why=why)

