"""Table 310.16 (2026 NEC) ampacities, the 310.12(A) dwelling-service rule, Table 310.15(C)(1)
and the NM cap of 334.80(A).

Transcribed from the printed table the owner sent 2026-11-14, rows 16 AWG (Cu) / 14 AWG (Al)
through 600 kcmil, 30 °C ambient, at most three current-carrying conductors. Table 310.17
(free air) and the 310.15(B) ambient corrections are paraphrased in the docs, not coded: no
check reads them. A leaf under ``model``.
"""

from __future__ import annotations

from typing import Final

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
