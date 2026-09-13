"""What a pipe or raceway's nominal size actually measures across the outside.

The exact sibling of :data:`~typehaus.resolve.framing.tables.LUMBER_ACTUAL`, and for the
same reason: a 2x6 is 1 1/2" x 5 1/2" and 3" PVC DWV is **3.500"** across. The author
writes the nominal, because that is the number the code tables, the catalog and the supply
house are all keyed on; the geometry needs the real one.

**Every clearance the engine printed before this module was optimistic.** ``diameter`` is
authored nominal (``inch(3)``) and every consumer swept a circle of radius ``diameter/2``
along the centreline, so a 3" drain was drawn and graded half an inch narrower than the pipe
that gets installed, and 3/4" EMT 0.172" narrower. Catlin carried two real defects behind
exactly that error — ``CD-M-DATA-KITCH`` and ``CD-M-DATA-PORCH``, whose authoring comment
claimed 3/4" EMT "passes between the 8 7/8" chords without a hole in anything" while the
real 0.922" OD put the invert 0.086" inside the bottom chord.

**Three tables, because the material decides, and that is load-bearing rather than
fastidious.** A material-blind IPS table reports 1 1/4" copper at 1.660" when it is 1.375",
and on catlin that one error invents a ``mep.run_in_finished_volume`` finding on
``PR-B-CW-TRUNK`` that does not exist. Iron-pipe-size and copper-tube-size are two different
dimensional systems that happen to share a vocabulary.

**Authored ``diameter`` never changes.** ``mep.pipe_sizing`` keys MN Table 703.2 on the
nominal, and a table row for "3 inch" is not a row for "3.5 inch". This module answers a
different question — how much room does it need — and nothing here feeds a sizing lookup.

**Known debt: the drawn tube is still nominal.** The IFC emitter and the takeoff continue to
sweep ``diameter_m / 2`` this pass, because widening the solid moves ``out/model.json`` and
every IFC golden with it. So the *checks* see the real outside and the *drawings* do not,
which is the conservative direction for a clearance question and the wrong one for a
collision rendering. Closing it is a separate commit with a golden re-bless in it.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN

#: Iron-pipe-size outside diameters, inches, keyed on the nominal the author writes.
#: PVC/ABS DWV, PVC pressure and steel all share this series — ASTM D2665/D1785/F441 and
#: ASME B36.10 agree on the OD at every size in it, which is the whole point of IPS.
IPS_OD_IN: dict[float, float] = {
    0.5: 0.840, 0.75: 1.050, 1.0: 1.315, 1.25: 1.660, 1.5: 1.900,
    2.0: 2.375, 2.5: 2.875, 3.0: 3.500, 4.0: 4.500, 5.0: 5.563, 6.0: 6.625,
    8.0: 8.625,
}

#: Copper-tube-size outside diameters, inches. CTS is **nominal + 1/8"** at every size
#: (ASTM B88), and PEX tubing is built to the same OD series so it fits the same fittings.
#: This is the table whose absence invents findings: 1 1/4" copper is 1.375", not 1.660".
TUBE_OD_IN: dict[float, float] = {
    0.25: 0.375, 0.375: 0.500, 0.5: 0.625, 0.75: 0.875, 1.0: 1.125,
    1.25: 1.375, 1.5: 1.625, 2.0: 2.125, 2.5: 2.625, 3.0: 3.125, 4.0: 4.125,
}

#: Electrical metallic tubing outside diameters, inches (NEC ch. 9 Table 4). A raceway's
#: trade size is a nominal BORE, so the error here runs the other way from a pipe's and is
#: larger in proportion: 3/4" EMT measures 0.922" across, a quarter more than its name.
RACEWAY_OD_IN: dict[float, float] = {
    0.5: 0.706, 0.75: 0.922, 1.0: 1.163, 1.25: 1.510, 1.5: 1.740,
    2.0: 2.197, 2.5: 2.875, 3.0: 3.500, 3.5: 4.000, 4.0: 4.500,
}

#: Materials built to copper-tube size rather than iron-pipe size.
_TUBE_MATERIALS = frozenset({"copper", "pex", "pex-a", "pex-b", "cpvc-cts"})

#: How close an authored nominal must land to a table key to be that size. Nominals are
#: authored as ``inch(3)`` and arrive as metres and back, so the round trip is the only
#: error there is to absorb — a thousandth of an inch is four orders above it and three
#: below the gap between adjacent sizes.
_NOMINAL_TOLERANCE_IN = 1e-3


def _lookup(table: dict[float, float], nominal_in: float) -> float:
    """``table[nominal_in]`` within :data:`_NOMINAL_TOLERANCE_IN`, else the nominal itself.

    **An unknown nominal returns itself, which under-reports the run's size** — the same
    direction every consumer was wrong in before this module existed, so a size nobody has
    tabulated is no worse off than it was. It is not silently safe, and a check quoting
    these numbers should not claim it is.
    """
    for key, od in table.items():
        if abs(key - nominal_in) <= _NOMINAL_TOLERANCE_IN:
            return od
    return nominal_in


def pipe_outside_diameter_m(nominal_m: float, material: str | None) -> float:
    """The outside diameter of a pipe of this authored nominal size and material.

    ``material`` is ``PipeRun.material`` verbatim and may be ``None``: an unstated material
    takes the IPS series, which is the larger of the two at every shared size and therefore
    the conservative read for a clearance.
    """
    if nominal_m <= 0:
        return 0.0
    nominal_in = nominal_m / M_PER_IN
    table = (TUBE_OD_IN if (material or "").strip().lower() in _TUBE_MATERIALS
             else IPS_OD_IN)
    return _lookup(table, nominal_in) * M_PER_IN


def raceway_outside_diameter_m(trade_size_m: float) -> float:
    """The outside diameter of a raceway of this authored trade size.

    **Every raceway is read as EMT**, because ``ConduitRun`` carries no material field to
    read. That is the conservative choice rather than an arbitrary one: rigid PVC conduit is
    *larger* than EMT at every trade size, so reading a PVC run as EMT under-reports it —
    but EMT is what catlin's runs are, what the authoring comments say, and what a
    residential branch circuit in a floor cavity is. Give ``ConduitRun`` a material and this
    function should grow the same two-table shape :func:`pipe_outside_diameter_m` has.
    """
    if trade_size_m <= 0:
        return 0.0
    return _lookup(RACEWAY_OD_IN, trade_size_m / M_PER_IN) * M_PER_IN
