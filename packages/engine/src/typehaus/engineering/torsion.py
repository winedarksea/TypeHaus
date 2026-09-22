"""Torsion on a RIGID diaphragm — the term ``rigidity_shares`` leaves out, and must.

** A RIGID SPLIT BY STIFFNESS ALONE IS NOT IN EQUILIBRIUM UNLESS THE LOAD PASSES THROUGH THE
CENTRE OF RIGIDITY. ** ``diaphragm_basis.rigidity_shares`` divides a storey shear by ``k/Σk``,
which satisfies compatibility (every line drifts the same) and, on its own, satisfies force
equilibrium — but not MOMENT equilibrium about the vertical axis. The leftover moment is
``M_t = V e``, and somewhere in the building it has to be carried.

** THE NOTE THAT SAID TWO PARALLEL LINES CANNOT CARRY ONE WAS WRONG. ** Two parallel lines at
different stations resist a torsional moment perfectly well, as a COUPLE of forces in their
own direction; what they cannot resist is translation ACROSS themselves. So the torsional
inertia here sums ``k d²`` over **every** line in **both** directions, each with its own lever
about the centre of rigidity, and on a two-line-per-axis canopy the pair's own couple is
typically 98% of it. The practical effect is that putting torsion in moves the split back
toward the lever rule, which is what statics wanted all along.

** AN INCREMENT IS ADDED AND A RELIEF IS NOT CREDITED. ** A line on the far side of the centre
of rigidity from the load gets a NEGATIVE torsional force. Crediting it would reduce a graded
member's demand on the strength of an arithmetic refinement, so :attr:`Torsion.multipliers`
floors at 1.0; the raw signed value is kept beside it for the record to print.

**Oracle.** ``houses/catlin/notes/north_entry_canopy_lateral.md`` §8g;
``tests/test_lateral_system_calcs.py`` reproduces it.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.engineering.diaphragm_basis import Line


@dataclass(frozen=True)
class Torsion:
    """What one axis's eccentricity does to that axis's lines."""

    #: ``"x"`` (lines resist east-west) or ``"y"`` (north-south) — the load's direction.
    axis: str
    #: Station of the centre of rigidity along the SPAN axis (the one lines are spread on).
    centre_ft: float
    #: Station of the load resultant on the same axis.
    load_ft: float
    eccentricity_ft: float
    moment_lb_ft: float
    #: ``Σ k d²`` over every line of both directions, lb/in x ft².
    inertia: float
    #: Fraction of ``inertia`` contributed by the lines resisting along ``axis`` — near 1.0
    #: says the pair carries its own torsion and the other axis is a rounding error.
    along_fraction: float
    #: line tag -> direct (rigidity) share force, lb
    direct_lb: dict[str, float]
    #: line tag -> signed torsional force, lb (negative is relief)
    torsional_lb: dict[str, float]
    #: line tag -> (direct + max(torsion, 0)) / direct, floored at 1.0
    multipliers: dict[str, float]
    #: The lines of the OTHER direction and the force the couple puts in each, lb.
    across_lb: dict[str, float]
    #: False where the lines cannot resist a torsional moment at all — a mechanism.
    stable: bool
    how: str


def _station(line: Line, axis: str) -> float | None:
    """The line's coordinate ACROSS the span, i.e. the lever arm axis for ``axis``."""
    return line.x_ft if axis == "y" else line.y_ft


def _across(line: Line, axis: str) -> float | None:
    return line.y_ft if axis == "y" else line.x_ft


def torsional_distribution(axis: str, shear_lb: float, load_station_ft: float,
                           along: list[Line], across: list[Line]) -> Torsion | None:
    """Distribute ``shear_lb`` over ``along`` with the torsion its eccentricity leaves over.

    ``along`` resist in the load's direction; ``across`` resist perpendicular to it and take
    part in the couple only. Every line must carry a stiffness and the coordinates
    :class:`Line` holds — this refuses rather than assuming a position, in the style of
    ``diaphragm_basis``, because a line placed at a guessed station would move ``J`` and
    every share with it.
    """
    if shear_lb <= 0.0 or not along:
        return None
    positions: dict[str, float] = {}
    for line in along:
        station = _station(line, axis)
        if line.stiffness_lb_per_in is None or station is None:
            return None
        positions[line.tag] = station
    total_k = sum(line.stiffness_lb_per_in or 0.0 for line in along)
    if total_k <= 0.0:
        return None
    centre = sum((line.stiffness_lb_per_in or 0.0) * positions[line.tag]
                 for line in along) / total_k

    across_positions: dict[str, float] = {}
    for line in across:
        station = _across(line, axis)
        if line.stiffness_lb_per_in is None or station is None:
            return None
        across_positions[line.tag] = station
    across_k = sum(line.stiffness_lb_per_in or 0.0 for line in across)
    across_centre = (sum((line.stiffness_lb_per_in or 0.0) * across_positions[line.tag]
                         for line in across) / across_k) if across_k > 0.0 else 0.0

    along_j = sum((line.stiffness_lb_per_in or 0.0) * (positions[line.tag] - centre) ** 2
                  for line in along)
    across_j = sum((line.stiffness_lb_per_in or 0.0)
                   * (across_positions[line.tag] - across_centre) ** 2 for line in across)
    inertia = along_j + across_j

    # ** STABILITY IS THE FIRST QUESTION AND THE MAGNITUDE IS THE SECOND. ** Lines all on one
    # station, with nothing perpendicular spread either, are a mechanism about the vertical
    # axis: there is no J to divide by and no distribution to report.
    stable = inertia > 0.0 and bool(across)
    eccentricity = load_station_ft - centre
    moment = shear_lb * eccentricity

    direct = {line.tag: (line.stiffness_lb_per_in or 0.0) / total_k * shear_lb
              for line in along}
    torsional = {
        line.tag: (moment * (line.stiffness_lb_per_in or 0.0)
                   * (positions[line.tag] - centre) / inertia) if stable else 0.0
        for line in along}
    multipliers = {
        tag: (1.0 + max(torsional[tag], 0.0) / direct[tag]) if direct[tag] > 0.0 else 1.0
        for tag in direct}
    couple = {
        line.tag: (moment * (line.stiffness_lb_per_in or 0.0)
                   * (across_positions[line.tag] - across_centre) / inertia) if stable else 0.0
        for line in across}

    direction = "N-S" if axis == "y" else "E-W"
    how = (
        f"{direction}: centre of rigidity at {centre:.3f}' against a load resultant at "
        f"{load_station_ft:.3f}', e = {eccentricity:.3f}', M_t = {moment:,.0f} lb-ft "
        f"distributed by k d / J on J = {inertia:,.0f} lb/in x ft2 "
        f"({along_j / inertia * 100.0:.1f}% of it the {direction} lines' own couple). "
        + ("A RELIEF IS NOT CREDITED: a line on the far side of the centre of rigidity "
           "takes a negative increment and is still graded at its direct share."
           if any(v < 0.0 for v in torsional.values()) else
           "Every line takes an increment; none is relieved.")
        if stable else
        f"{direction}: NO TORSIONAL RESISTANCE — the lines are a mechanism about the "
        f"vertical axis (no line resists across them, or J is zero), so an eccentric "
        f"resultant has nothing to react against")
    return Torsion(axis=axis, centre_ft=centre, load_ft=load_station_ft,
                   eccentricity_ft=eccentricity, moment_lb_ft=moment, inertia=inertia,
                   along_fraction=(along_j / inertia) if inertia > 0.0 else 0.0,
                   direct_lb=direct, torsional_lb=torsional, multipliers=multipliers,
                   across_lb=couple, stable=stable, how=how)


def load_resultant_ft(top_shear_lb: float, top_station_ft: float,
                      head_reactions: dict[str, float],
                      stations: dict[str, float]) -> float | None:
    """Where the diaphragm-level shear acts, feet: the roof's own band plus the head props.

    A propped column hands its head reaction INTO the deck at the column's own station, so
    the deck's resultant is not the roof's centroid whenever the props are off to one side —
    which on a canopy with all its cast columns on one line they always are.
    """
    total = top_shear_lb + sum(head_reactions.values())
    if total <= 0.0:
        return None
    moment = top_shear_lb * top_station_ft
    for tag, reaction in head_reactions.items():
        station = stations.get(tag)
        if station is None:
            return None
        moment += reaction * station
    return moment / total
