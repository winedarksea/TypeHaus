"""Table 250.66 and Table 250.102(C)(1) (2026 NEC), as held in ``docs/code-notes/nec-2026-paraphrase-250.md``.

Both tables row by the largest ungrounded conductor (or the summed area of parallel sets),
in identical bands; they differ only in the top row. A leaf under ``model``.
"""

from __future__ import annotations

from typing import Final

#: Upper bound of each band in kcmil (inf: no bound): copper, aluminum (or copper-clad).
_CU_BANDS: Final = ("2", "1/0", "3/0", "350", "600", "1100", None)
_AL_BANDS: Final = ("1/0", "3/0", "250", "500", "900", "1750", None)
#: Table 250.66, copper GEC per band.
GEC_CU: Final = ("8", "6", "4", "2", "1/0", "2/0", "3/0")
#: Table 250.102(C)(1), copper jumper per band; the top band is Note 1's 12 1/2% (None).
JUMPER_CU: Final = ("8", "6", "4", "2", "1/0", "2/0", None)
#: 250.104(A)(1): the water-piping bonding jumper is never required larger than 3/0 Cu.
WATER_BOND_CAP_CU: Final = "3/0"


def kcmil(size: str) -> float:
    """Circular-mil area / 1000 of an AWG or kcmil size, from the AWG definition."""
    size = size.strip().lstrip("#")
    if size.endswith("/0"):
        gauge = 1 - int(size[:-2])
    elif int(size) >= 250:
        return float(size)
    else:
        gauge = int(size)
    diameter_mils = 5.0 * 92 ** ((36 - gauge) / 39)
    return diameter_mils ** 2 / 1000


def band(area_kcmil: float, material: str) -> int:
    """The row index (0 = smallest) for a conductor area of ``material`` ("cu"/"al")."""
    bounds = _CU_BANDS if material == "cu" else _AL_BANDS
    for i, top in enumerate(bounds):
        if top is None or area_kcmil <= kcmil(top) * 1.0005:
            return i
    return len(bounds) - 1


def larger(a: str, b: str) -> bool:
    """Whether AWG/kcmil size ``a`` is at least ``b``."""
    return kcmil(a) >= kcmil(b) * 0.9995
