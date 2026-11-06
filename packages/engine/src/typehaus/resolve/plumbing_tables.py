"""The pure MN Plumbing Code (UPC) tables the checks, the take-off and the router share.

Moved out of ``takeoff/plumbing_calc.py`` (which re-exports every name) so ``routing`` may
read the trap-arm, wet-vent and branch-size rules the checks grade: a router aimed at a
different limit from the check that judges it cannot close the loop.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN

# MN Plumbing Code Table 702.1 (private). A tub-shower is one fixture, valued as a tub.
DFU_BY_SYMBOL: dict[str, float] = {
    "toilet": 3.0,          # water closet, 1.6 gpf gravity tank
    # A wall-hung WC is the same 3 DFU: Table 702.1 values the fixture, not its mounting.
    "toilet-wall-hung": 3.0,
    "lavatory": 1.0,
    "lavatory-wall-hung": 1.0,
    "drawer-vanity": 1.0,
    "drawer-vanity-indy": 1.0,
    "sektion-vanity-indy": 1.0,
    "sunnersta-sink": 1.0,
    "door-drawer-vanity": 1.0,
    "sektion-vanity": 1.0,
    "vanity": 1.0,          # a lavatory in a cabinet
    "solid-surface-vanity": 1.0,  # an integral-bowl top: a lavatory
    "tub": 2.0,
    "kohler-underscore-6036": 2.0,  # same bath load; product geometry is independent
    "kohler-underscore-6032": 2.0,
    "tub-shower": 2.0,
    "shower": 2.0,
    # A neo-angle pan is a shower: the cut corner is a plan outline, not a drainage fact.
    "shower-neo-angle": 2.0,
    "kitchen-sink": 2.0,    # incl. food-waste grinder / dishwasher branch
    "kitchen-sink-undermount-single": 2.0,
    "washer": 3.0,          # clothes washer, 2" standpipe
    # A stacked pair is one washer for fixture-unit purposes: the heat-pump dryer above it
    # discharges condensate to an indirect waste, which is not a drainage fixture.
    "washer-dryer-stacked": 3.0,
    "dishwasher": 2.0,
    "laundry-sink": 2.0,
    "floor-drain": 2.0,
}

#: What a plumber counts a fixture as when pricing per setting: one class per symbol in
#: ``DFU_BY_SYMBOL`` / ``WSFU_BY_SYMBOL`` (a test holds the three in step).
FIXTURE_CLASS_BY_SYMBOL: dict[str, str] = {
    "toilet": "water closet", "toilet-wall-hung": "water closet (wall-hung, carrier)",
    **dict.fromkeys(("lavatory", "lavatory-wall-hung", "drawer-vanity", "drawer-vanity-indy",
                     "sektion-vanity-indy", "door-drawer-vanity", "sektion-vanity", "vanity",
                     "solid-surface-vanity"), "lavatory"),
    "sunnersta-sink": "bar sink",
    **dict.fromkeys(("tub", "kohler-underscore-6036", "kohler-underscore-6032"), "bathtub"),
    "tub-shower": "tub/shower",
    "shower": "shower", "shower-neo-angle": "shower",
    "kitchen-sink": "kitchen sink", "kitchen-sink-undermount-single": "kitchen sink",
    "washer": "clothes washer", "washer-dryer-stacked": "clothes washer",
    "dishwasher": "dishwasher", "laundry-sink": "laundry sink",
    "floor-drain": "floor drain", "hydrant": "hose bibb / wall hydrant",
    "roman-tub-filler": "tub filler (trim on its bath)",
}

# MN Plumbing Code 710.1 (UPC 710.1): no water closet discharges to a drain smaller than
# 3". Table 703.2 alone does not say so — a 3 DFU closet sits comfortably inside the 2"
# row's 6 DFU — and sizing a closet branch from capacity alone is the classic table-only
# error. Only the fixtures the rule actually names appear here; a symbol with no row has no
# floor, which is the honest reading rather than a defensive one.
MINIMUM_DRAIN_IN_BY_SYMBOL: dict[str, float] = {
    "toilet": 3.0,
    "toilet-wall-hung": 3.0,
}

# MN Plumbing Code Table 703.2: max DFU on a horizontal drainage branch, by size (in).
DRAIN_BRANCH_CAPACITY_DFU: tuple[tuple[float, float], ...] = (
    (1.25, 1.0),
    (1.5, 3.0),
    (2.0, 6.0),
    (3.0, 35.0),
    (4.0, 216.0),
)

# MN Plumbing Code Table 1002.2: max trap-arm length (inches) by trap-arm size (inches).
TRAP_ARM_MAX_IN: dict[float, float] = {
    1.25: 30.0,
    1.5: 42.0,
    2.0: 60.0,
    3.0: 72.0,
    4.0: 120.0,
}


# MN Plumbing Code 908 (2018 UPC, Minn. R. 4714.0050) wet venting. Sources: 908.2.x text per
# IAPMO TIA UPC-001-12 (908.2.1 where permitted, .1 vent connection, .2 size, .3 trap arm,
# .4 water closet last, .5 additional fixtures); 908.2.2 as quoted and applied to the ENTIRE
# wet vent by MN Plumbing Board PB0225 (2026-02-24); 908.1 as summarized on MN DLI's
# "Vertical Wet Venting" sheet (1/22). Horizontal: ≥2" for ≤4 DFU, ≥3" for ≥5 DFU.
# Vertical: upper fixtures 1-2 DFU, ≤4 fixtures, one storey, ≤6 ft developed, each section
# one size over the larger of the upper fixture's waste and the Table 703.2 size for its
# sum, never under 2". 908.1.1's per-section split is graded on the whole section.
WET_VENT_HORIZONTAL_MIN_IN: tuple[tuple[float, float], ...] = ((4.0, 2.0), (float("inf"), 3.0))
WET_VENT_VERTICAL_MAX_IN = 72.0
WET_VENT_VERTICAL_MAX_FIXTURES = 4
WET_VENT_VERTICAL_UPPER_DFU_MAX = 2.0
WET_VENT_MIN_IN = 2.0
#: A bathroom group (UPC 204.0): water closet, lavatories, bath/shower, bidet, floor drain.
#: Horizontal wet venting admits no other fixture (908.2.1).
BATHROOM_GROUP_SYMBOLS: frozenset[str] = frozenset(
    k for k in DFU_BY_SYMBOL
    if not k.startswith(("kitchen-sink", "washer")) and k not in {"dishwasher", "laundry-sink"})


def required_drain_diameter_in(dfu: float) -> float | None:
    """Smallest horizontal-branch size carrying ``dfu`` (Table 703.2); None = beyond it."""
    for size_in, capacity in DRAIN_BRANCH_CAPACITY_DFU:
        if dfu <= capacity + 1e-9:
            return size_in
    return None


def trap_arm_limit_in(diameter_m: float) -> float | None:
    """Max trap-arm length for a trap-arm diameter (Table 1002.2); None = no row."""
    diameter_in = round(diameter_m / M_PER_IN, 2)
    for size_in, limit in TRAP_ARM_MAX_IN.items():
        if abs(diameter_in - size_in) < 0.06:
            return limit
    return None
