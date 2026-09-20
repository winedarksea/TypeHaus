"""How a frame's lateral load is SHARED between the lines that resist it.

** WHAT THIS REPLACES, AND WHY IT IS A CALCULATION RATHER THAN A JUDGEMENT. **
``roof_moment.roof_base_moments`` used to put the whole of a canopy's frame shear on its
cast concrete columns and credit the sheathed panel on the other line with nothing, on the
stated ground that "relative rigidity between a cast column and a stud panel is a judgement
this engine does not make". That sentence was doing two jobs and only one of them was
honest. Refusing to *guess* a panel's stiffness is right — a wall's racking stiffness comes
out of its fastener schedule, which no geometry records. But once the schedule is stated,
distributing by relative rigidity is IBC 2018 §1604.4 in as many words:

    "The total lateral force shall be distributed to the various vertical elements of the
    lateral force-resisting system in proportion to their rigidities, considering the
    rigidity of the horizontal bracing system or diaphragm."

Three clauses, three things this module computes: the rigidity of each vertical element,
the rigidity of the diaphragm, and — because the second clause only means anything if the
first is decided — **which idealization the deck actually is**.

** THE FLEXIBLE / RIGID TEST IS RUN, NOT ASSUMED. ** ASCE 7-16 §26.2 defines a diaphragm as
flexible when its own midspan deflection is more than **twice** the average storey drift of
the vertical elements under the same load, and SDPWS 4.2.5 repeats it for wood. Both
deflections are computed here from the SDPWS deflection equations, so the answer is a number
with a margin rather than a habit. A flexible deck distributes by TRIBUTARY area (the lines
are independent beams under their own share of the load); a rigid one distributes by
RIGIDITY. They are not two conservatisms to envelope — they are two different structures,
and the test says which one is on the drawing.

** WHERE AN INPUT IS MISSING THIS REFUSES, IT DOES NOT DEFAULT. ** Every function here
returns ``None`` rather than a plausible number when the model does not hold what SDPWS
asks for, in the style ``analytical/shells.py`` already uses for a missing subgrade modulus.
A share computed off a guessed ``G_a`` would move a base moment by a factor of three and
look exactly like a computed one.

** UNITS ARE SDPWS's OWN, WHICH ARE NOT SI AND NOT CONSISTENT. ** The two deflection
equations are calibrated empirical forms: ``v`` in plf, ``h``/``L``/``b``/``W`` in FEET,
``E`` in psi, ``A`` in in², ``G_a`` in kips/inch, and the answer in INCHES. Converting them
to a consistent system and back is how a sign or a thousand goes missing, so they are
written here exactly as the standard prints them.

**Oracle.** ``houses/catlin/notes/entry_column_base_fixity.md`` §7, hand-worked in a
separate pass; ``tests/test_lateral_system_calcs.py`` reproduces it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: NDS 2018 Supplement Table 4A, Spruce-Pine-Fir No.2 — the softest modulus any chord in
#: this repository's houses is built from. It reaches only the BENDING term of the two
#: deflection equations, which on a squat panel is under 3% of the total, so erring soft is
#: both conservative and cheap. A house framing its chords in something stiffer gets a
#: slightly stiffer answer than this and is not credited for it.
CHORD_E_PSI = 1_400_000.0

#: ASCE 7-16 §26.2 / SDPWS 4.2.5: flexible when the diaphragm's own midspan deflection
#: exceeds this multiple of the average drift of the vertical elements.
FLEXIBLE_DRIFT_MULTIPLE = 2.0

#: SDPWS Table 4.2.4 — maximum diaphragm span-to-depth ratio for wood structural panels.
DIAPHRAGM_ASPECT_BLOCKED = 4.0
DIAPHRAGM_ASPECT_UNBLOCKED = 3.0

@dataclass(frozen=True)
class Line:
    """One vertical line of lateral resistance, and what it is worth.

    A LINE, not an element: the north entry canopy's two cast columns stand on one x, act in
    parallel, and are one line whose stiffness is their sum. Splitting them would give the
    diaphragm two supports where the building has one.
    """

    tag: str
    kind: str
    #: Where the line stands along the diaphragm's SPAN axis, feet. Two lines at the same
    #: station are the same line.
    station_ft: float
    #: Lateral stiffness, lb per inch of drift. ``None`` where an input is missing — which
    #: refuses the whole distribution rather than dropping this line out of it, because a
    #: line silently worth zero hands its share to its neighbours.
    stiffness_lb_per_in: float | None
    #: The members this line is made of, for the record's element tags.
    element_tags: tuple[str, ...] = ()
    how: str = ""


@dataclass(frozen=True)
class Distribution:
    """The answer: what fraction of the diaphragm-level shear each line takes."""

    axis: str
    #: True when the deck is RIGID relative to its lines and rigidity governs the split.
    rigid: bool
    diaphragm_deflection_in: float
    average_drift_in: float
    #: line tag -> share of the shear delivered at the diaphragm
    shares: dict[str, float]
    #: line tag -> the drift that share produces, inches
    drifts: dict[str, float]
    basis: str


def cantilever_stiffness_lb_per_in(modulus_psi: float, inertia_in4: float,
                                   height_in: float) -> float | None:
    """``3EI/h³`` — a column fixed at its base and free at its head.

    ** THE SECTION IS GROSS, AND THAT IS THE CONSERVATIVE END FOR THE COLUMN. ** ACI 318-19
    §6.6.3.1.1 permits 0.70 I_g for a column in an elastic lateral analysis. Taking the
    gross section instead makes the column STIFFER, which under a rigidity split hands it a
    LARGER share of the shear — the direction that does not flatter the member this whole
    calculation exists to grade. ``cracked_band`` below runs the other end for the panel,
    which is flattered by exactly the opposite choice.
    """
    if modulus_psi <= 0.0 or inertia_in4 <= 0.0 or height_in <= 0.0:
        return None
    return 3.0 * modulus_psi * inertia_in4 / height_in ** 3


#: ACI 318-19 §6.6.3.1.1's cracked-section factor for a column. Applied when it is the
#: PANEL's demand being graded: a softer column line sheds shear onto the panel.
CRACKED_COLUMN_FACTOR = 0.70


def shear_wall_deflection_in(unit_shear_plf: float, height_ft: float, length_ft: float,
                             apparent_stiffness_kips_per_in: float,
                             chord_area_in2: float,
                             anchorage_slip_in: float) -> float | None:
    """SDPWS 4.3.2 eq. 4.3-1, the three-term deflection of a wood structural panel wall::

        delta = 8 v h^3 / (E A b)  +  v h / (1000 G_a)  +  h d_a / b

    Bending of the wall as a cantilever beam, shear plus nail slip lumped in ``G_a``, and
    the rigid-body rotation the anchorage's own stretch allows. On a squat panel the middle
    term dominates and the first is a rounding error; on a tall narrow one the third does.
    """
    if (length_ft <= 0.0 or height_ft <= 0.0 or chord_area_in2 <= 0.0
            or apparent_stiffness_kips_per_in <= 0.0):
        return None
    bending = (8.0 * unit_shear_plf * height_ft ** 3
               / (CHORD_E_PSI * chord_area_in2 * length_ft))
    shear = unit_shear_plf * height_ft / (1000.0 * apparent_stiffness_kips_per_in)
    rotation = height_ft * max(anchorage_slip_in, 0.0) / length_ft
    return bending + shear + rotation


def diaphragm_deflection_in(unit_shear_plf: float, span_ft: float, depth_ft: float,
                            apparent_stiffness_kips_per_in: float,
                            chord_area_in2: float,
                            chord_splice_slip_in: float) -> float | None:
    """SDPWS 4.2.2 eq. 4.2-1, the midspan deflection of a blocked wood diaphragm::

        delta = 5 v L^3 / (8 E A W)  +  0.25 v L / (1000 G_a)  +  sum(x dc) / (2 W)

    ``v`` is the maximum unit shear at the diaphragm BOUNDARY — the larger line reaction
    divided by the depth — not an average, because the deflection equation is calibrated
    against the worst boundary shear.
    """
    if (span_ft <= 0.0 or depth_ft <= 0.0 or chord_area_in2 <= 0.0
            or apparent_stiffness_kips_per_in <= 0.0):
        return None
    bending = (5.0 * unit_shear_plf * span_ft ** 3
               / (8.0 * CHORD_E_PSI * chord_area_in2 * depth_ft))
    shear = 0.25 * unit_shear_plf * span_ft / (1000.0 * apparent_stiffness_kips_per_in)
    return bending + shear + max(chord_splice_slip_in, 0.0)


def tributary_shares(lines: list[Line]) -> dict[str, float]:
    """The FLEXIBLE idealization: each line carries the deck either side of it, to midspan.

    A flexible deck has no stiffness to redistribute with, so every line is a simple beam
    support under the load standing over it. Two lines make it a half each, which is the
    familiar answer and the one that hides how it was arrived at — the general form is here
    so a third line does not silently get the same treatment.
    """
    stations = sorted({line.station_ft for line in lines})
    if len(stations) == 1:
        return {line.tag: 1.0 / len(lines) for line in lines}
    span = stations[-1] - stations[0]
    if span <= 0.0:
        return {line.tag: 1.0 / len(lines) for line in lines}
    width: dict[float, float] = {}
    for i, x in enumerate(stations):
        lo = stations[0] if i == 0 else (x + stations[i - 1]) / 2.0
        hi = stations[-1] if i == len(stations) - 1 else (x + stations[i + 1]) / 2.0
        width[x] = hi - lo
    out: dict[str, float] = {}
    for line in lines:
        peers = [ln for ln in lines if ln.station_ft == line.station_ft]
        out[line.tag] = width[line.station_ft] / span / len(peers)
    return out


def rigidity_shares(lines: list[Line]) -> dict[str, float] | None:
    """The RIGID idealization: in proportion to stiffness, IBC 2018 §1604.4.

    ** NO TORSIONAL TERM, AND THE REASON IS THAT TWO LINES CANNOT CARRY ONE. ** A rigid
    diaphragm on exactly two parallel lines has no torsional resistance at all: the pair is
    a mechanism about any axis normal to them, and the standard treatment is that the load
    must pass through the stiffness centroid. Inventing a torsional stiffness for that case
    would be arithmetic about a structure that is not there. Three or more lines, and this
    function is an under-count that the caller must not use without one.
    """
    total = 0.0
    for line in lines:
        if line.stiffness_lb_per_in is None:
            return None
        total += line.stiffness_lb_per_in
    if total <= 0.0:
        return None
    return {line.tag: (line.stiffness_lb_per_in or 0.0) / total for line in lines}


def distribute(axis: str, shear_lb: float, lines: list[Line], span_ft: float,
               depth_ft: float, diaphragm_ga_kips_per_in: float | None,
               chord_area_in2: float | None,
               chord_splice_slip_in: float) -> Distribution | None:
    """Run the flexible/rigid test on this deck and return the share it dictates.

    ``lines`` must already carry their stiffnesses; a line whose stiffness is ``None``
    refuses the whole distribution rather than dropping out of it, because a line silently
    worth zero hands its share to its neighbours. The caller re-enters this once or twice to
    settle a panel's own stiffness against the share it lands on — SDPWS states a panel's
    anchorage term at the design shear rather than as a rate, so the pair is very slightly
    coupled — and that loop is the CALLER's, not this function's: the flexible/rigid test
    below must be evaluated exactly once, at one stated distribution.
    """
    if not lines or shear_lb <= 0.0 or span_ft <= 0.0 or depth_ft <= 0.0:
        return None
    if diaphragm_ga_kips_per_in is None or chord_area_in2 is None:
        return None
    rigid = rigidity_shares(lines)
    if rigid is None:
        return None

    # ** THE TEST IS RUN AT THE TRIBUTARY DISTRIBUTION, AND THAT IS NOT AN ARBITRARY PICK. **
    # ASCE 7-16 §26.2 asks whether the deck deflects more than twice as far as its supports
    # drift — that is, whether assuming it FLEXIBLE is self-consistent — so the deflections
    # it compares are the ones the flexible idealization itself produces. Running it at the
    # rigid shares instead makes the answer depend on the assumption under test, and worse,
    # it can oscillate: rigid shares say flexible, tributary shares say rigid, and nothing
    # settles. One distribution, one evaluation, one verdict.
    trial = tributary_shares(lines)
    drifts = {line.tag: (trial[line.tag] * shear_lb / line.stiffness_lb_per_in
                         if line.stiffness_lb_per_in else 0.0)
              for line in lines}
    average = sum(drifts.values()) / len(drifts) if drifts else 0.0
    boundary_v = max(trial.values(), default=0.0) * shear_lb / depth_ft
    diaphragm_delta = diaphragm_deflection_in(boundary_v, span_ft, depth_ft,
                                              diaphragm_ga_kips_per_in, chord_area_in2,
                                              chord_splice_slip_in)
    if diaphragm_delta is None:
        return None
    flexible = average > 0.0 and diaphragm_delta > FLEXIBLE_DRIFT_MULTIPLE * average

    shares = trial if flexible else rigid
    drifts = {line.tag: (shares[line.tag] * shear_lb / line.stiffness_lb_per_in
                         if line.stiffness_lb_per_in else 0.0)
              for line in lines}
    direction = "N-S" if axis == "y" else "E-W"
    ratio = diaphragm_delta / average if average else float("inf")
    basis = (
        f"{direction} shear {shear_lb:,.0f} lb ASD shared by relative rigidity (IBC 2018 "
        f"§1604.4) across {len(lines)} line(s) on a {span_ft:.1f}' x {depth_ft:.1f}' deck. "
        f"Under the tributary split the deck's own midspan deflection is "
        f"{diaphragm_delta:.3f}\" (SDPWS 4.2.2) against an average line drift of "
        f"{average:.3f}\" (SDPWS 4.3.2), i.e. {ratio:.2f}x — ASCE 7-16 §26.2 calls a deck "
        f"FLEXIBLE above {FLEXIBLE_DRIFT_MULTIPLE:.0f}x, so this one is "
        + ("FLEXIBLE and the split is TRIBUTARY" if flexible
           else "RIGID and the split is by RIGIDITY")
    )
    return Distribution(axis=axis, rigid=not flexible,
                        diaphragm_deflection_in=diaphragm_delta,
                        average_drift_in=average, shares=shares, drifts=drifts,
                        basis=basis)


def chord_force_lb(shear_lb: float, span_ft: float, depth_ft: float) -> float | None:
    """``w L² / (8 W)`` at midspan, written in terms of the total shear: ``V L / (8 W)``.

    The diaphragm is a deep beam. Its flanges are the chords, and this is the force one of
    them carries in tension while the other carries it in compression. It is the number that
    decides whether a deck with sheathing on it is a diaphragm or just a lid.
    """
    if span_ft <= 0.0 or depth_ft <= 0.0:
        return None
    return shear_lb * span_ft / (8.0 * depth_ft)


def member_area_in2(profile: str, plies: int) -> float | None:
    """Gross area of ``plies`` of one nominal member, in², or ``None`` if unparseable.

    ** ``CrossSection.width_m`` ALREADY CARRIES A BUILT-UP PROFILE'S PLIES. ** ``"3-2x12"``
    comes back 4.5" wide with ``plies == 3``, not 1.5" wide, so multiplying by that field as
    well triples an area that was already right — 152 in² for a member that is 50. ``plies``
    here is the SPEC's own count, for a chord authored as a nominal section repeated (a
    2-2x4 end post), and it is the only multiplier applied.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    width_in = (section.width_m or 0.0) / 0.0254
    depth_in = (section.depth_m or 0.0) / 0.0254
    if width_in <= 0.0 or depth_in <= 0.0 or plies <= 0:
        return None
    return width_in * depth_in * plies


def round_inertia_in4(diameter_in: float) -> float:
    """``pi d^4 / 64`` — the gross second moment of a solid round column."""
    return math.pi * diameter_in ** 4 / 64.0
