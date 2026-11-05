"""IRC 2018 Table R403.1(1) — minimum concrete footing size, light-frame construction.

Read off up.codes (Minnesota 2020 Residential Code, IRC 2018 Chapter 4) 2026-11-05; the
50 psf band was corroborated cell for cell by the 2026-11-04 geometry review (C2 E1). Cells
are (W, T) in inches by soil bearing column. Footnote a: interpolation allowed,
extrapolation not. Footnote b: a 32-foot-wide house with a load-bearing centre wall; per
2 ft of width, +/- 2" of W and 1" of T, T never under 6".

Table R403.1(3) is for houses whose above-grade walls are concrete or masonry; a light-frame
house on a concrete basement stays on this table, whose "plus basement" rows carry the wall.
"""

from __future__ import annotations

SOIL_COLUMNS_PSF: tuple[float, ...] = (1500.0, 2000.0, 2500.0, 3000.0, 3500.0, 4000.0)
SNOW_BANDS_PSF: tuple[float, ...] = (20.0, 30.0, 50.0, 70.0)
FOUNDATIONS: tuple[str, ...] = ("slab", "crawl", "basement")
BASIS_WIDTH_FT = 32.0
MIN_THICKNESS_IN = 6.0
MIN_WIDTH_IN = 12.0

_Row = tuple[tuple[float, float], ...]


def _r(*cells: str) -> _Row:
    return tuple((float(w), float(t)) for w, t in (c.split("x") for c in cells))


_6 = "12x6"
# (snow band) -> (stories, foundation) -> cells at SOIL_COLUMNS_PSF
TABLE_R403_1_1: dict[float, dict[tuple[int, str], _Row]] = {
    20.0: {
        (1, "slab"): _r(_6, _6, _6, _6, _6, _6),
        (1, "crawl"): _r(_6, _6, _6, _6, _6, _6),
        (1, "basement"): _r("18x6", "14x6", _6, _6, _6, _6),
        (2, "slab"): _r(_6, _6, _6, _6, _6, _6),
        (2, "crawl"): _r("16x6", _6, _6, _6, _6, _6),
        (2, "basement"): _r("22x6", "16x6", "13x6", _6, _6, _6),
        (3, "slab"): _r("14x6", _6, _6, _6, _6, _6),
        (3, "crawl"): _r("19x6", "14x6", _6, _6, _6, _6),
        (3, "basement"): _r("25x8", "19x6", "15x6", "13x6", _6, _6),
    },
    30.0: {
        (1, "slab"): _r(_6, _6, _6, _6, _6, _6),
        (1, "crawl"): _r("13x6", _6, _6, _6, _6, _6),
        (1, "basement"): _r("19x6", "14x6", _6, _6, _6, _6),
        (2, "slab"): _r(_6, _6, _6, _6, _6, _6),
        (2, "crawl"): _r("17x6", "13x6", _6, _6, _6, _6),
        (2, "basement"): _r("23x6", "17x6", "14x6", _6, _6, _6),
        (3, "slab"): _r("15x6", _6, _6, _6, _6, _6),
        (3, "crawl"): _r("20x6", "15x6", _6, _6, _6, _6),
        (3, "basement"): _r("26x8", "20x6", "16x6", "13x6", _6, _6),
    },
    50.0: {
        (1, "slab"): _r(_6, _6, _6, _6, _6, _6),
        (1, "crawl"): _r("16x6", _6, _6, _6, _6, _6),
        (1, "basement"): _r("21x6", "16x6", "13x6", _6, _6, _6),
        (2, "slab"): _r("14x6", _6, _6, _6, _6, _6),
        (2, "crawl"): _r("19x6", "14x6", _6, _6, _6, _6),
        (2, "basement"): _r("25x7", "19x6", "15x6", _6, _6, _6),
        (3, "slab"): _r("17x6", "13x6", _6, _6, _6, _6),
        (3, "crawl"): _r("22x6", "17x6", "13x6", _6, _6, _6),
        (3, "basement"): _r("28x9", "21x6", "17x6", "14x6", _6, _6),
    },
    70.0: {
        (1, "slab"): _r(_6, _6, _6, _6, _6, _6),
        (1, "crawl"): _r("18x6", "13x6", _6, _6, _6, _6),
        (1, "basement"): _r("24x7", "18x6", "14x6", _6, _6, _6),
        (2, "slab"): _r("16x6", _6, _6, _6, _6, _6),
        (2, "crawl"): _r("21x6", "16x6", "13x6", _6, _6, _6),
        (2, "basement"): _r("27x9", "20x6", "16x6", "14x6", _6, _6),
        (3, "slab"): _r("19x6", "14x6", _6, _6, _6, _6),
        (3, "crawl"): _r("25x7", "18x6", "15x6", _6, _6, _6),
        (3, "basement"): _r("30x10", "23x6", "18x6", "15x6", "13x6", _6),
    },
}


def _lerp(xs: tuple[float, ...], x: float) -> tuple[int, int, float]:
    """Bracketing indices and fraction for ``x`` inside ``xs`` (clamped by the caller)."""
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            return i, i + 1, (x - xs[i]) / (xs[i + 1] - xs[i])
    return len(xs) - 1, len(xs) - 1, 0.0


def required_footing_in(stories: int, foundation: str, snow_psf: float, soil_psf: float,
                        house_width_ft: float) -> tuple[float, float]:
    """(W, T) in inches, interpolated (footnote a) and width-adjusted (footnote b).

    The caller has already refused what the table cannot read: more than three stories,
    snow over 70 psf, soil under 1,500 psf. Snow under 20 reads the 20 band; soil over
    4,000 reads the 4,000 column, which only ever asks for more.
    """
    snow = max(snow_psf, SNOW_BANDS_PSF[0])
    soil = min(soil_psf, SOIL_COLUMNS_PSF[-1])
    s0, s1, fs = _lerp(SNOW_BANDS_PSF, snow)
    c0, c1, fc = _lerp(SOIL_COLUMNS_PSF, soil)

    def cell(band: float, dim: int) -> float:
        row = TABLE_R403_1_1[band][(stories, foundation)]
        return row[c0][dim] + (row[c1][dim] - row[c0][dim]) * fc

    w, t = ((cell(SNOW_BANDS_PSF[s0], d) * (1 - fs) + cell(SNOW_BANDS_PSF[s1], d) * fs)
            for d in (0, 1))
    steps = (house_width_ft - BASIS_WIDTH_FT) / 2.0
    return max(w + 2.0 * steps, MIN_WIDTH_IN), max(t + steps, MIN_THICKNESS_IN)
