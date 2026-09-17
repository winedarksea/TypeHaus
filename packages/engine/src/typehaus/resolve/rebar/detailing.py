"""ACI 318-19 detailing lengths: development, laps, hooks. Pure arithmetic, inches in and out.

A leaf of the rebar layout and the one place these provisions are spelled —
``engineering/deck_post`` delegates its class B lap here. Oracle:
``houses/catlin/notes/rebar_layout_basis.md`` §1, reproduced by
``tests/test_rebar_detailing_oracle.py``.

Assumptions stated once: normalweight concrete (λ 1.0), Grade 60 bar (ψg 1.0), and the
Table 25.4.2.3 "clear spacing ≥ db, cover ≥ db, ties per Code" row — every catlin pour has
2" or more of cover on bars no larger than #6.
"""

from __future__ import annotations

import math
from typing import Literal

from typehaus.model.rebar import BARS

FY_PSI = 60000.0
MIN_LENGTH_IN = 12.0
#: §25.4.1.4: √f'c used for development is capped at 100 psi.
SQRT_FC_CAP = 100.0

HookKind = Literal["std90", "std180", "tie90", "tie135", "tie180"]


def development_length_in(bar: int, fc_psi: float, *, top_cast: bool = False,
                          epoxy: bool = False) -> float:
    """ld in tension, Table 25.4.2.3: ``fy ψt ψe ψg / (25 λ √f'c) · db`` (/20 for #7 and up).

    ψt 1.3 for a bar with more than 12" of fresh concrete cast below it; ψe 1.2 for epoxy
    only — zinc is 1.0 (§25.4.2.5). ψt·ψe is capped at 1.7. Not less than 12".
    """
    db = BARS[bar].diameter_in
    psi = min(1.7, (1.3 if top_cast else 1.0) * (1.2 if epoxy else 1.0))
    divisor = 25.0 if bar <= 6 else 20.0
    root = min(SQRT_FC_CAP, math.sqrt(fc_psi))
    return max(MIN_LENGTH_IN, FY_PSI * psi / (divisor * root) * db)


def development_length_raw_in(bar_diameter_in: float, fc_psi: float) -> float:
    """The same expression with no 12" floor and every ψ 1.0, for a caller that grades it."""
    return FY_PSI / (25.0 * min(SQRT_FC_CAP, math.sqrt(fc_psi))) * bar_diameter_in


def tension_lap_in(bar: int, fc_psi: float, lap_class: str | None = None, *,
                   top_cast: bool = False, epoxy: bool = False) -> float:
    """§25.5.2.1: class A is 1.0 ld, class B 1.3 ld, both ≥ 12". ``None`` means class B."""
    factor = 1.0 if lap_class == "A" else 1.3
    return max(MIN_LENGTH_IN,
               factor * development_length_in(bar, fc_psi, top_cast=top_cast, epoxy=epoxy))


def compression_lap_in(bar: int) -> float:
    """§25.5.5.1 for fy ≤ 60,000 psi: ``0.0005 fy db`` (30 db), ≥ 12"."""
    return max(MIN_LENGTH_IN, 0.0005 * FY_PSI * BARS[bar].diameter_in)


def hook_geometry_in(bar: int, kind: HookKind) -> tuple[float, float, float]:
    """``(angle°, inside bend diameter, straight extension)`` for a hook.

    Standard hooks, Table 25.3.1 (#3–#8): 90° bends 6 db, extension 12 db; 180° bends 6 db,
    extension max(4 db, 2.5"). Stirrup/tie/hoop hooks, Table 25.3.2 (#3–#5): bend 4 db;
    90° and 135° extensions max(6 db, 3"); 180° max(4 db, 2.5"). A 135° tie hook is also the
    §25.3.4 seismic hook. #6+ ties bend at 6 db and extend 12 db at 90°.
    """
    db = BARS[bar].diameter_in
    if kind == "std90":
        return 90.0, 6.0 * db, 12.0 * db
    if kind == "std180":
        return 180.0, 6.0 * db, max(4.0 * db, 2.5)
    small = bar <= 5
    bend = (4.0 if small else 6.0) * db
    if kind == "tie180":
        return 180.0, bend, max(4.0 * db, 2.5)
    if kind == "tie90":
        return 90.0, bend, max(6.0 * db, 3.0) if small else 12.0 * db
    return 135.0, bend, max(6.0 * db, 3.0)


def hook_allowance_in(bar: int, kind: HookKind) -> float:
    """Cut length a hook adds beyond the bar's out-to-out placed dimension.

    The placed run ends at the outside face of the bend, ``D/2 + db`` past the start of the
    arc; the hook is the arc on the bar centreline, ``θ (D + db)/2``, plus the extension.
    """
    angle, bend, extension = hook_geometry_in(bar, kind)
    db = BARS[bar].diameter_in
    arc = math.radians(angle) * (bend + db) / 2.0
    return arc + extension - (bend / 2.0 + db)


#: D5: a circular tie closes with this much overlap beyond its two hooks.
CIRCULAR_TIE_OVERLAP_IN = 6.0
#: D2: the mill length when a spec states none.
DEFAULT_STOCK_IN = 240.0
