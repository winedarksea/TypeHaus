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


def hooked_development_length_in(bar: int, fc_psi: float, *, epoxy: bool = False,
                                 confined: bool = False,
                                 enclosed_by_ties: bool = False) -> float:
    """ldh, ACI 318-19 §25.4.3.1: ``fy ψe ψr ψo ψc / (55 λ √f'c) · db^1.5``, ≥ max(8 db, 6").

    A HOOKED bar develops in a fraction of a straight bar's length, which is the whole
    reason a dowel can anchor into a 12" pad at all: a #5 needs about 21" straight at 5,000
    psi and about 9" hooked. Grading a dowel against the straight figure would condemn every
    pad-borne column in a house that is built correctly.

    The ψ factors, per Table 25.4.3.2:

    * ψe 1.2 for epoxy; 1.0 for uncoated AND for zinc (§25.4.2.5 — zinc does not debond).
    * ψr 1.0 where the hook is enclosed by ties or stirrups per §25.4.3.3, else 1.6. A
      column cage's own ties do exactly that where they continue through the joint.
    * ψo 1.0 for a hook confined by ≥ 2-1/2" side cover and a ≥ 2 db tail cover, else 1.25.
    * ψc = f'c/15,000 + 0.6, capped at 1.0 — so it only ever helps below 6,000 psi.
    """
    db = BARS[bar].diameter_in
    psi_e = 1.2 if epoxy else 1.0
    psi_r = 1.0 if enclosed_by_ties else 1.6
    psi_o = 1.0 if confined else 1.25
    psi_c = min(1.0, fc_psi / 15000.0 + 0.6)
    root = min(SQRT_FC_CAP, math.sqrt(fc_psi))
    length = FY_PSI * psi_e * psi_r * psi_o * psi_c / (55.0 * root) * db ** 1.5
    return max(length, 8.0 * db, 6.0)


def compression_lap_in(bar: int) -> float:
    """§25.5.5.1 for fy ≤ 60,000 psi: ``0.0005 fy db`` (30 db), ≥ 12"."""
    return max(MIN_LENGTH_IN, 0.0005 * FY_PSI * BARS[bar].diameter_in)


def hook_geometry_in(bar: int, kind: HookKind, *,
                     galvanized: bool = False) -> tuple[float, float, float]:
    """``(angle°, inside bend diameter, straight extension)`` for a hook.

    Standard hooks, Table 25.3.1 (#3–#8): 90° bends 6 db, extension 12 db; 180° bends 6 db,
    extension max(4 db, 2.5"). Stirrup/tie/hoop hooks, Table 25.3.2 (#3–#5): bend 4 db;
    90° and 135° extensions max(6 db, 3"); 180° max(4 db, 2.5"). A 135° tie hook is also the
    §25.3.4 seismic hook. #6+ ties bend at 6 db and extend 12 db at 90°. A bar bent before
    galvanizing (ASTM A767) bends no tighter than 6 db, ties included.
    """
    db = BARS[bar].diameter_in
    if kind == "std90":
        return 90.0, 6.0 * db, 12.0 * db
    if kind == "std180":
        return 180.0, 6.0 * db, max(4.0 * db, 2.5)
    small = bar <= 5
    bend = (4.0 if small and not galvanized else 6.0) * db
    if kind == "tie180":
        return 180.0, bend, max(4.0 * db, 2.5)
    if kind == "tie90":
        return 90.0, bend, max(6.0 * db, 3.0) if small else 12.0 * db
    return 135.0, bend, max(6.0 * db, 3.0)


def hook_allowance_in(bar: int, kind: HookKind, *, galvanized: bool = False) -> float:
    """Cut length a hook adds beyond the bar's out-to-out placed dimension.

    The placed run ends at the outside face of the bend, ``D/2 + db`` past the start of the
    arc; the hook is the arc on the bar centreline, ``θ (D + db)/2``, plus the extension.
    """
    angle, bend, extension = hook_geometry_in(bar, kind, galvanized=galvanized)
    db = BARS[bar].diameter_in
    arc = math.radians(angle) * (bend + db) / 2.0
    return arc + extension - (bend / 2.0 + db)


def bent_before_galvanizing(coating: str | None) -> bool:
    """ASTM A767 bar is fabricated, then galvanized: its bends follow A767's diameters."""
    return "a767" in (coating or "").lower()


#: IRC Table R608.5.4(1), Grade 60 tension laps — where R404.1.3.3.7.5 sends a foundation
#: wall's splices. Walls lap at the greater of this and ACI class B.
IRC_WALL_LAP_IN = {4: 30.0, 5: 38.0, 6: 45.0}


def wall_lap_in(bar: int, fc_psi: float, lap_class: str | None = None, *,
                top_cast: bool = False) -> float:
    return max(IRC_WALL_LAP_IN.get(bar, 0.0),
               tension_lap_in(bar, fc_psi, lap_class, top_cast=top_cast))


def hooked_development_in(bar: int, fc_psi: float, *, confined_spacing: bool,
                          side_cover_ok: bool, epoxy: bool = False) -> float:
    """ldh, §25.4.3.1(a): ``fy ψe ψr ψo ψc / (55 λ √f'c) · db^1.5``, ≥ max(8 db, 6").

    ψr 1.0 where hooked bars sit ≥ 6 db apart (``confined_spacing``), else 1.6; ψo 1.0 where
    side cover normal to the hook's plane is ≥ 6 db, else 1.25; ψc = f'c/15,000 + 0.6 below
    6,000 psi.
    """
    db = BARS[bar].diameter_in
    psi_r = 1.0 if confined_spacing else 1.6
    psi_o = 1.0 if side_cover_ok else 1.25
    psi_c = fc_psi / 15000.0 + 0.6 if fc_psi < 6000.0 else 1.0
    root = min(SQRT_FC_CAP, math.sqrt(fc_psi))
    ldh = FY_PSI * (1.2 if epoxy else 1.0) * psi_r * psi_o * psi_c / (55.0 * root) * db ** 1.5
    return max(8.0 * db, 6.0, ldh)


#: D5: a circular tie closes with this much overlap beyond its two hooks.
CIRCULAR_TIE_OVERLAP_IN = 6.0
#: D2: the mill length when a spec states none — 40'-0", what a fabricator cuts #4–#6 from.
DEFAULT_STOCK_IN = 480.0
