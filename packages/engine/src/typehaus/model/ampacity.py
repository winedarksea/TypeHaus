"""Table 310.16 (2026 NEC) ampacities, the 310.12(A) dwelling-service rule, Table 310.15(C)(1)
the NM cap of 334.80(A) and the standard OCPD ratings of Table 240.6(A).

Transcribed from the printed table the owner sent 2026-11-14, rows 16 AWG (Cu) / 14 AWG (Al)
through 600 kcmil, 30 °C ambient, at most three current-carrying conductors. Table 310.17
(free air) and the 310.15(B) ambient corrections are paraphrased in the docs, not coded: no
check reads them. A leaf under ``model``.
"""

from __future__ import annotations

from typing import Final, Literal

ConductorMaterial = Literal["cu", "al"]

SIZES: Final = ("16", "14", "12", "10", "8", "6", "4", "3", "2", "1", "1/0", "2/0", "3/0",
                "4/0", "250", "300", "350", "400", "500", "600")

#: size -> (60 °C, 75 °C, 90 °C) amperes. Copper.
COPPER: Final[dict[str, tuple[int, int, int]]] = dict(zip(SIZES, (
    (10, 15, 20), (15, 20, 25), (20, 25, 30), (30, 35, 40), (40, 50, 55), (55, 65, 75),
    (70, 85, 95), (85, 100, 115), (95, 115, 130), (110, 130, 145), (125, 150, 170),
    (145, 175, 195), (165, 200, 225), (195, 230, 260), (215, 255, 290), (240, 285, 320),
    (260, 310, 350), (280, 335, 380), (320, 380, 430), (350, 420, 475)), strict=True))

#: Aluminum or copper-clad aluminum; no 16 AWG row. 14 AWG is copper-clad only.
ALUMINUM: Final[dict[str, tuple[int, int, int]]] = dict(zip(SIZES[1:], (
    (10, 15, 20), (15, 20, 25), (25, 30, 35), (35, 40, 45), (40, 50, 55), (55, 65, 75),
    (65, 75, 85), (75, 90, 100), (85, 100, 115), (100, 120, 135), (115, 135, 150),
    (130, 155, 175), (150, 180, 205), (170, 205, 230), (195, 230, 260), (210, 250, 280),
    (225, 270, 305), (260, 310, 350), (285, 340, 385)), strict=True))

#: Footnote 2: these values serve only for adjustment or correction.
ADJUSTMENT_ONLY: Final = frozenset({("cu", "16", 75), ("cu", "16", 90),
                                    ("al", "14", 75), ("al", "14", 90)})

_COLUMN: Final = {60: 0, 75: 1, 90: 2}
_SERVICE_MIN_SIZE: Final = "8"


def ampacity(material: str, size: str, temp_c: int) -> int:
    """Table 310.16 value; ``material`` is "cu" or "al" (copper-clad included)."""
    rows = COPPER if material == "cu" else ALUMINUM
    return rows[size][_COLUMN[temp_c]]


def dwelling_service_conductor(rating_a: float, material: str) -> str:
    """310.12(A): the smallest conductor whose 75 °C ampacity is at least 83% of the rating.

    Valid for 100-400 A single-phase dwelling services with no correction factors; it matches
    Table 310.12(A) at every standard rating, and gives a rating between rows its own size.
    """
    need = 0.83 * rating_a
    for size in SIZES[SIZES.index(_SERVICE_MIN_SIZE):]:
        if (material == "cu" or size in ALUMINUM) and ampacity(material, size, 75) >= need - 1e-9:
            return size
    raise ValueError(f"no conductor to 600 kcmil carries {need:.0f} A")


#: Table 310.15(C)(1): upper bound of a conductor count -> percent of the table ampacity.
_ADJUSTMENT: Final = ((3, 100), (6, 80), (9, 70), (20, 50), (30, 45), (40, 40))


def adjustment_factor(current_carrying: int) -> float:
    """310.15(C)(1): more than three current-carrying conductors derate the ampacity."""
    for limit, percent in _ADJUSTMENT:
        if current_carrying <= limit:
            return percent / 100
    return 0.35


def nm_ampacity(size: str, current_carrying: int = 3) -> int:
    """334.80(A), copper NM: the 90 °C value adjusted, never above the 60 °C value."""
    return min(int(ampacity("cu", size, 90) * adjustment_factor(current_carrying) + 1e-9),
               ampacity("cu", size, 60))


#: Table 240.6(A), standard ampere ratings of fuses and inverse-time breakers (fuses add
#: 1, 3, 6 and 601, which no breaker takes). Nonstandard ratings are permitted.
STANDARD_OCPD_A: Final = (10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150,
                          175, 200, 225, 250, 300, 350, 400, 450, 500, 600, 700, 800, 1000,
                          1200, 1600, 2000, 2500, 3000, 4000, 5000, 6000)


def next_standard_rating(amps: float) -> int:
    """240.4(B): the next standard rating above ``amps`` (above, so a standard value is itself
    not eligible: 240.4(B)(2) wants an ampacity that is not a standard rating)."""
    return next(a for a in STANDARD_OCPD_A if a > amps)


#: Table 250.122 (printed 2026-11-14): OCPD rating not exceeding -> (copper, aluminum or
#: copper-clad aluminum) wire EGC. Sizes above 600 kcmil are in the table, not in SIZES.
EGC_TABLE: Final = (
    (15, "14", "12"), (20, "12", "10"), (60, "10", "8"), (100, "8", "6"), (200, "6", "4"),
    (300, "4", "2"), (400, "3", "1"), (500, "2", "1/0"), (600, "1", "2/0"),
    (800, "1/0", "3/0"), (1000, "2/0", "4/0"), (1200, "3/0", "250"), (1600, "4/0", "350"),
    (2000, "250", "400"), (2500, "350", "600"), (3000, "400", "600"), (4000, "500", "750"),
    (5000, "700", "1250"), (6000, "800", "1250"))
_ORDER: Final = (*SIZES, "700", "750", "800", "1250")


def egc_minimum(ocpd_a: float, material: str) -> str:
    """250.122: the smallest wire EGC for an OCPD of ``ocpd_a`` amperes; ``material`` is
    ``"cu"`` or ``"al"`` (copper-clad aluminum shares the aluminum column)."""
    for rating, cu, al in EGC_TABLE:
        if ocpd_a <= rating:
            return cu if material == "cu" else al
    raise ValueError(f"no Table 250.122 row above {EGC_TABLE[-1][0]} A")


def size_at_least(size: str, minimum: str) -> bool:
    """Whether conductor ``size`` is no smaller than ``minimum`` (same material)."""
    return _ORDER.index(size) >= _ORDER.index(minimum)


def is_size(size: str) -> bool:
    """Whether ``size`` is a conductor size this module knows (AWG or kcmil string)."""
    return size in _ORDER


#: 240.4(D) small conductors: (material, size) -> the largest OCPD, after correction.
#: 18/16 Cu and 14 CCA carry load and OCPD-type conditions, so they are not rows here.
SMALL_CONDUCTOR_MAX_OCPD: Final = {("cu", "14"): 15, ("cu", "12"): 20, ("cu", "10"): 30,
                                   ("al", "12"): 15, ("al", "10"): 25}
_CONDITIONAL_SMALL: Final = frozenset({("cu", "18"), ("cu", "16"), ("al", "14")})
_SIXTY_C_MAX_SIZE: Final = "1"  # 110.14(C)(1)(a): conductors 14-1 AWG
_SIXTY_C_MAX_OCPD_A: Final = 100


def termination_column(ocpd_a: float, size: str, authored: int | None = None) -> int:
    """110.14(C)(1): 60 °C for circuits of 100 A or less (14-1 AWG), else 75 °C; an authored
    column (equipment listed and identified for it) overrides."""
    if authored is not None:
        return authored
    small = _ORDER.index(size) <= _ORDER.index(_SIXTY_C_MAX_SIZE)
    return 60 if ocpd_a <= _SIXTY_C_MAX_OCPD_A and small else 75


def max_ocpd(material: str, size: str, temp_c: int, *, next_size_up: bool) -> int | None:
    """The largest OCPD 240.4 lets protect this conductor: its Table 310.16 ampacity, the next
    standard rating above a nonstandard one where 240.4(B) is allowed, capped by 240.4(D).
    None where the conductor is a conditional 240.4(D) row or outside the table."""
    rows = COPPER if material == "cu" else ALUMINUM
    if (material, size) in _CONDITIONAL_SMALL or size not in rows:
        return None
    amps = ampacity(material, size, temp_c)
    limit = amps
    if next_size_up and amps not in STANDARD_OCPD_A and next_standard_rating(amps) <= 800:
        limit = next_standard_rating(amps)
    cap = SMALL_CONDUCTOR_MAX_OCPD.get((material, size))
    return min(limit, cap) if cap is not None else limit


def smallest_size_for(ocpd_a: float, material: str, temp_c: int | None = None) -> str | None:
    """The smallest conductor 240.4 lets an ``ocpd_a`` breaker protect (no 240.4(B)); the
    reference size for 250.122(D)'s "enlarged". ``temp_c`` None reads 110.14(C)(1)."""
    for size in SIZES:
        column = termination_column(ocpd_a, size, temp_c)
        top = max_ocpd(material, size, column, next_size_up=False)
        if top is not None and top >= ocpd_a:
            return size
    return None
