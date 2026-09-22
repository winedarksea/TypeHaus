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
#: GM and GC)"; class 5 — "clay, sandy clay, silty clay, clayey silt, silt and sandy silt (CL,
#: ML, MH and CH)", so ML is class 5 (it read class 4 until 2026-09-21). SM-SC is a dual
#: symbol the table does not list; both halves are class 4.
_IBC_1806_2_CLASS: dict[str, int] = {
    "GW": 3, "GP": 3,
    "SW": 4, "SP": 4, "SM": 4, "SM-SC": 4, "SC": 4, "GM": 4, "GC": 4,
    "ML": 5, "ML-CL": 5, "CL": 5,
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
#: at-rest), row for row off the code text (up.codes/s/soil-lateral-loads, read 2026-09-21).
#: GM is 40 active, not the 45 the IRC R404.1.2 wall tables group it at; SM-SC, SC and the
#: silts and clays are 100 at rest, not 60. Active presumes the wall can rotate enough to
#: mobilise the active wedge; a free cantilever normally is designed active, and it is the
#: more favourable of the two.
_IBC_1610_1: dict[str, tuple[float, float]] = {
    "GW": (30.0, 60.0), "GP": (30.0, 60.0), "SW": (30.0, 60.0), "SP": (30.0, 60.0),
    "GM": (40.0, 60.0), "GC": (45.0, 60.0), "SM": (45.0, 60.0),
    "SM-SC": (45.0, 100.0), "ML": (45.0, 100.0),
    "SC": (60.0, 100.0), "ML-CL": (60.0, 100.0), "CL": (60.0, 100.0),
}

#: The band, in pcf. 110 is a loose-to-medium silty gravel; 130 is well compacted. Not a
#: code value — see this module's docstring.
SOIL_UNIT_WEIGHT_BAND_PCF: tuple[float, float] = (110.0, 130.0)

#: The ground motion, inches, at which a presumptive allowable is taken as MOBILISED — the
#: secant that turns a code table into a stiffness. IBC §1806.3.4 pairs 2x the tabular
#: lateral bearing with 1/2" of motion at grade; Terzaghi & Peck's 1" settlement criterion
#: is the soft end for vertical bearing. No code publishes the band, so it is run at both
#: ends like the unit weight (``engineering/base_rotation.py``).
MOTION_AT_ALLOWABLE_BAND_IN: tuple[float, float] = (0.25, 1.0)

#: Recorded beside the band, never an end of it: where a verdict turns.
MOTION_AT_ALLOWABLE_SENSITIVITY_IN = 2.0

#: Conventional, and not in dispute.
CONCRETE_UNIT_WEIGHT_PCF = 150.0


def displaced_soil_credit_lb(bearing_area_ft2: float, depth_ft: float) -> float:
    """The weight of the soil a footing REPLACED, lb — a credit against its bearing demand.

    **Net bearing pressure, which is the convention every geotechnical allowable is written
    for.** A presumptive value in IBC Table 1806.2 is what the soil at that depth may carry
    over and above the overburden it was already carrying; counting the full weight of the
    concrete against it charges the ground twice for the same cubic feet, once as the soil
    that was excavated and again as the concrete poured into the hole. Until 2026-09-18 this
    engine took the gross weight, which is conservative but not free: it is what put catlin's
    ``PD-BW-RE`` 1.5% over an allowable it is not in fact over.

    Taken at the LOW end of :data:`SOIL_UNIT_WEIGHT_BAND_PCF`, and that is the whole of the
    judgement here: a credit is conservative at its smallest, the mirror of a demand, so the
    band is not run at both ends the way a demand term is. 110 pcf is a loose silty gravel,
    and native ground at the north entry's depth will be denser than that.

    ``depth_ft`` is the thickness of soil actually displaced — the footing's own depth, not
    its depth below grade: the shaft above it stands in a hole that is backfilled, and this
    engine does not model backfill density.
    """
    return bearing_area_ft2 * depth_ft * SOIL_UNIT_WEIGHT_BAND_PCF[0]


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
    #: Where the CLASS came from — ``"presumed"`` (read regionally, off a survey or a
    #: profile) or ``"geotechnical"`` (an investigation on this parcel). The table values
    #: above are presumptive either way; what moves is whether the row was picked for the
    #: right ground. ``Site.soil_basis`` is the one place a house states it.
    provenance: str = "presumed"
    basis_source: str | None = None
    basis_note: str | None = None

    @property
    def citation(self) -> str:
        return (f"IBC Table 1610.1 and Table 1806.2 class {self.ibc_class} "
                f"(presumptive, {self.soil_class})")


def presumptive(soil_class: str | None, *, basis: object = None) -> PresumptiveSoil | None:
    """The code tables' values for a declared group, or ``None`` if it declares none.

    ``None`` is never defaulted around: a calculation with no soil class reports INCOMPLETE
    naming it, because guessing the ground is the one assumption a retaining wall cannot
    survive.

    ``basis`` is the site's :class:`~typehaus.model.site.SoilBasis`, keyword-only because it
    is provenance and never arithmetic: absent, the class is taken as presumed, which is the
    honest reading of a house that has said nothing about where its soil class came from.
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
        provenance=str(getattr(basis, "provenance", None) or "presumed"),
        basis_source=getattr(basis, "source", None),
        basis_note=getattr(basis, "basis", None),
    )


def soil_is_presumed(soil: PresumptiveSoil | None) -> bool:
    """Whether the soil class this record was graded on is a presumption, not a finding.

    ``None`` — no class at all — is presumed too: the record is INCOMPLETE for want of one,
    and nothing about that is a measurement.
    """
    return soil is None or soil.provenance != "geotechnical"


def soil_provenance_note(soil: PresumptiveSoil | None) -> str:
    """One sentence, in ``base_rotation._stated_soil``'s voice, saying where the soil came
    from — printed on every record that reads a table row off a soil class."""
    if soil is None:
        return ("THE SOIL IS PRESUMED, NOT MEASURED: no soil class is declared at all, so "
                "nothing here rests on a measurement of this parcel.")
    where = (f" — {soil.basis_source} ({soil.basis_note})"
             if soil.basis_source else
             " — no geotechnical investigation is on file for this parcel")
    if soil_is_presumed(soil):
        return (f"THE SOIL IS PRESUMED, NOT MEASURED: the class {soil.soil_class} is read "
                f"regionally{where}, and every value taken from it (EFP, allowable "
                f"bearing, lateral bearing, friction) is a published code table row for "
                f"that presumption. It grades every record built on it as DRAFT; an "
                f"investigation on this parcel confirms or replaces the class, and the gap "
                f"register keeps that open until it does.")
    return (f"THE SOIL CLASS IS ESTABLISHED: {soil.soil_class} from a geotechnical "
            f"investigation on this parcel{where}. The table values read off it are still "
            f"the code's presumptive ones — a report's own allowables replace them element "
            f"by element, not here.")


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
