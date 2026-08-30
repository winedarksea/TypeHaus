"""Presumptive geotechnical values, from the code's own tables.

Every number here is a *presumptive* one — a value a code table permits where no site
investigation exists. That is what makes a result built on them a **screening**, and the
records that use them say so in as many words.

Soil *unit weight* is the exception and it is deliberately not a single number: no code
table publishes one, and it is the input that directly scales the stabilising weight on a
retaining wall's heel. It is carried as a band and every calculation is run at both ends.
Where the two ends disagree about the verdict the calculation reports INCOMPLETE naming the
missing input rather than picking a number; where they agree, the verdict is robust across
the whole plausible range and reporting it is honest.
"""

from __future__ import annotations

from dataclasses import dataclass

#: IBC Table 1806.2 soil classes, by the IRC Table R405.1 group symbols the model declares.
#: Class 4 — "sand, silty sand, clayey sand, silty gravel and clayey gravel (SW, SP, SM, SC,
#: GM and GC)" — is the row every group Minnesota's profile can declare falls in except the
#: clean gravels and the clays.
_IBC_1806_2_CLASS: dict[str, int] = {
    "GW": 3, "GP": 3,
    "SW": 4, "SP": 4, "SM": 4, "SM-SC": 4, "SC": 4, "GM": 4, "GC": 4, "ML": 4,
    "ML-CL": 5, "CL": 5,
}

#: IBC Table 1806.2, by class: allowable vertical bearing (psf), lateral bearing below
#: natural grade (psf per foot of depth), and the coefficient of friction its footnote a
#: applies **to the dead load**.
_IBC_1806_2: dict[int, tuple[float, float, float]] = {
    3: (3000.0, 200.0, 0.35),
    4: (2000.0, 150.0, 0.25),
    5: (1500.0, 100.0, 0.0),   # class 5 carries cohesion instead of friction (130 psf)
}

#: IBC Table 1610.1 equivalent-fluid lateral pressures, psf per foot of depth: (active,
#: at-rest). Keyed by the same group symbols. Active presumes the wall can rotate enough to
#: mobilise the active wedge; a free cantilever normally is designed active, and it is the
#: more favourable of the two.
_IBC_1610_1: dict[str, tuple[float, float]] = {
    "GW": (30.0, 60.0), "GP": (30.0, 60.0), "SW": (30.0, 60.0), "SP": (30.0, 60.0),
    "GM": (45.0, 60.0), "GC": (45.0, 60.0), "SM": (45.0, 60.0), "SM-SC": (45.0, 60.0),
    "ML": (45.0, 60.0),
    "SC": (60.0, 60.0), "ML-CL": (60.0, 60.0), "CL": (60.0, 60.0),
}

#: The band, in pcf. 110 is a loose-to-medium silty gravel; 130 is well compacted. Not a
#: code value — see this module's docstring.
SOIL_UNIT_WEIGHT_BAND_PCF: tuple[float, float] = (110.0, 130.0)

#: Conventional, and not in dispute.
CONCRETE_UNIT_WEIGHT_PCF = 150.0


@dataclass(frozen=True)
class PresumptiveSoil:
    """What the code tables say about one declared soil group."""

    soil_class: str
    ibc_class: int
    active_efp_psf_per_ft: float
    at_rest_efp_psf_per_ft: float
    allowable_bearing_psf: float
    lateral_bearing_psf_per_ft: float
    friction_coefficient: float

    @property
    def citation(self) -> str:
        return (f"IBC Table 1610.1 and Table 1806.2 class {self.ibc_class} "
                f"(presumptive, {self.soil_class})")


def presumptive(soil_class: str | None) -> PresumptiveSoil | None:
    """The code tables' values for a declared group, or ``None`` if it declares none.

    ``None`` is never defaulted around: a calculation with no soil class reports INCOMPLETE
    naming it, because guessing the ground is the one assumption a retaining wall cannot
    survive.
    """
    if not soil_class:
        return None
    key = soil_class.strip().upper()
    ibc_class = _IBC_1806_2_CLASS.get(key)
    pressures = _IBC_1610_1.get(key)
    if ibc_class is None or pressures is None:
        return None
    bearing, lateral, friction = _IBC_1806_2[ibc_class]
    return PresumptiveSoil(
        soil_class=key, ibc_class=ibc_class,
        active_efp_psf_per_ft=pressures[0], at_rest_efp_psf_per_ft=pressures[1],
        allowable_bearing_psf=bearing, lateral_bearing_psf_per_ft=lateral,
        friction_coefficient=friction,
    )


#: IBC Table 1806.2 class 3 — "sandy gravel and/or gravel (GW and GP)". A clean, open-graded
#: washed crushed stone bed is that row: nominal 1" to #4 single-size carries essentially
#: nothing through a #200 sieve, which is the same gradation claim ``FootingBedding.
#: non_frost_susceptible`` already makes about the very same stone.
AGGREGATE_BEARING_CLASS = 3


def aggregate_bed() -> PresumptiveSoil:
    """The base interface where a footing bears on a compacted washed-stone section.

    **Which material the base friction comes from is the interface's, not the backfill's.**
    A footing bearing on 42" of replacement stone slides on stone; taking mu from the
    retained silty gravel behind the wall reads the wrong side of the footing. It is worth
    0.25 -> 0.35 and it is a correctness fix, not a credit: the coefficient describes what
    the concrete is actually sitting on.

    The lateral-bearing and allowable-bearing values move with it for the same reason. Only
    ``active_efp``/``at_rest_efp`` do NOT — those describe the *retained* soil pushing on
    the stem, which is a different material on a different face, so a caller must keep
    taking them from the site's own class.
    """
    bearing, lateral, friction = _IBC_1806_2[AGGREGATE_BEARING_CLASS]
    return PresumptiveSoil(
        soil_class="GP (washed crushed stone bed)", ibc_class=AGGREGATE_BEARING_CLASS,
        # Never used from this object — see the docstring. Carried as zero so that a caller
        # that reached for them by mistake gets an obviously wrong answer rather than a
        # plausible one.
        active_efp_psf_per_ft=0.0, at_rest_efp_psf_per_ft=0.0,
        allowable_bearing_psf=bearing, lateral_bearing_psf_per_ft=lateral,
        friction_coefficient=friction,
    )
