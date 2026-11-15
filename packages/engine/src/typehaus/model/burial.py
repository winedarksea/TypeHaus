"""Table 300.7(A), minimum cover for underground wiring, 0-1000 V ac (2026 NEC).

Read in print by the owner 2026-11-14. A leaf: no resolved model here, only the table and the
two notes that change how it is read. Rule text is paraphrased in
``docs/code-notes/nec-2026-paraphrase-300.md``; ``checks/mep/conduit_burial.py`` grades a model against it.

Cells are inches (the printed millimetres are the same cells at 25 mm per inch). A column is
the wiring method, a row the place it is buried. **Note 4**: where a Column 1-3 method serves
a Column 4 or 5 circuit, the shallowest of the applicable columns governs (``shallowest_in``).
**Note 1**: cover is the shortest distance from the top of the buried conductor or raceway to
the top of finished grade, concrete or similar cover (``cover_in``). Notes 2, 3, 5 and 6 are
carried as text in ``NOTES``: concrete encasement of 2 in. envelope, shallower where conductors
rise to terminations or access, solid rock, and directly buried EMT meeting 358.10.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

IN: Final = 0.0254


class BurialColumn(Enum):
    """The five printed columns."""

    DIRECT_BURIAL = 1  # direct burial cables or conductors
    RMC_IMC = 2  # rigid metal conduit or intermediate metal conduit
    RACEWAY = 3  # EMT, nonmetallic raceways listed for direct burial, other approved
    RESIDENTIAL_GFCI = 4  # residential branch circuits, 120 V or less, GFCI, 20 A OCPD at most
    LANDSCAPE = 5  # irrigation / landscape lighting, 30 V or less, UF or identified cable


class BurialLocation(Enum):
    """The seven printed rows."""

    ALL_OTHER = "all locations not specified below"
    TRENCH_UNDER_CONCRETE = "in trench below 2 in. thick concrete or equivalent"
    UNDER_BUILDING = "under a building"
    UNDER_SLAB = "under a 4 in. concrete exterior slab, no vehicles, slab 6 in. past the run"
    UNDER_ROAD = "under streets, highways, roads, alleys, driveways and parking lots"
    DWELLING_DRIVEWAY = "one- and two-family dwelling driveways and outdoor parking"
    AIRPORT = "in or under airport runways, with adjacent areas where trespass is prohibited"


@dataclass(frozen=True)
class Cover:
    """One cell: the cover in inches, and the in-raceway figure where the cell prints two."""

    inches: float
    in_raceway_in: float | None = None  # slab row, Columns 4 and 5: 6 direct, 4 in a raceway
    raceway_only: bool = False  # under a building: Columns 1, 4, 5 only in a raceway or MC/MI

    def for_method(self, in_raceway: bool) -> float:
        if in_raceway and self.in_raceway_in is not None:
            return self.in_raceway_in
        return self.inches


_L = BurialLocation
_C = BurialColumn


def _row(*cells: Cover) -> dict[BurialColumn, Cover]:
    return dict(zip(_C, cells, strict=True))


def _n(*inches: float) -> dict[BurialColumn, Cover]:
    return _row(*(Cover(v) for v in inches))


_RW = Cover(0, raceway_only=True)
_SLAB_DB = Cover(6, in_raceway_in=4)

#: Columns 1..5 per row, as printed. Column 5's "all other" cell (6) carries footnotes 1 and 2.
TABLE_300_7_A: Final[dict[BurialLocation, dict[BurialColumn, Cover]]] = {
    _L.ALL_OTHER: _n(24, 6, 18, 12, 6),
    _L.TRENCH_UNDER_CONCRETE: _n(18, 6, 12, 6, 6),
    _L.UNDER_BUILDING: _row(_RW, Cover(0), Cover(0), _RW, _RW),
    _L.UNDER_SLAB: _row(Cover(18), Cover(4), Cover(4), _SLAB_DB, _SLAB_DB),
    _L.UNDER_ROAD: _n(24, 24, 24, 24, 24),
    _L.DWELLING_DRIVEWAY: _n(18, 18, 18, 12, 18),
    _L.AIRPORT: _n(18, 18, 18, 18, 18),
}

NOTES: Final = {
    1: "cover: shortest distance from the top of the buried run to the top of finished grade, "
       "concrete or similar cover",
    2: "a raceway approved for burial only where concrete encased needs a 2 in. envelope",
    3: "lesser depths where cables or conductors rise for terminations or splices, or access",
    4: "a Column 1-3 method serving a Column 4 or 5 circuit may use the shallowest depth",
    5: "solid rock: a metal raceway, or a direct-burial nonmetallic one under 2 in. of concrete "
       "down to the rock",
    6: "directly buried EMT shall also meet 358.10",
}

UNDER_SLAB_MIN_THICKNESS_IN: Final = 4.0
UNDER_SLAB_EDGE_IN: Final = 6.0  # slab extends this far past the run
TRENCH_CONCRETE_IN: Final = 2.0
#: Column 4 reaches 120 V or less and an OCPD of 20 A or less, with GFCI protection.
COLUMN_4_MAX_VOLTS: Final = 120
COLUMN_4_MAX_AMPS: Final = 20


def column_for(material: str) -> BurialColumn:
    """The method column for a ``RacewayMaterial`` value. EMT and PVC are Column 3; ENT is
    not listed for direct burial, so it is not given a column (``ValueError``)."""
    if material in ("emt", "pvc"):
        return _C.RACEWAY
    if material in ("rmc", "imc"):
        return _C.RMC_IMC
    raise ValueError(f"no Table 300.7(A) column for raceway material {material!r}")


def circuit_columns(material: str, *, volts: float | None, amps: float | None,
                    gfci: bool) -> tuple[BurialColumn, ...]:
    """Columns a run may read: its method's, plus Column 4 when the circuit qualifies."""
    columns = [column_for(material)]
    if gfci and volts is not None and amps is not None \
            and volts <= COLUMN_4_MAX_VOLTS and amps <= COLUMN_4_MAX_AMPS:
        columns.append(_C.RESIDENTIAL_GFCI)
    return tuple(columns)


def min_cover_in(location: BurialLocation, column: BurialColumn, *,
                 in_raceway: bool = True) -> float:
    """One cell, in inches."""
    return TABLE_300_7_A[location][column].for_method(in_raceway)


def shallowest_in(location: BurialLocation, columns: tuple[BurialColumn, ...], *,
                  in_raceway: bool = True) -> tuple[float, BurialColumn]:
    """Note 4: the shallowest permitted depth over ``columns``, and the column that gives it."""
    return min(((min_cover_in(location, c, in_raceway=in_raceway), c) for c in columns),
               key=lambda pair: (pair[0], pair[1].value))


def cover_in(top_of_run_z_m: float, surface_z_m: float) -> float:
    """Note 1: inches from the TOP of the run up to the top of grade, concrete or similar."""
    return (surface_z_m - top_of_run_z_m) / IN
