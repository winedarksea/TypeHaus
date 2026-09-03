"""The shared free body under every retaining-wall record — geometry, one load case, limits.

Split out of ``retaining_wall.py`` as a pure move with no behaviour change. It exists
because two modules need the same arithmetic and one of them
needs the other: ``retaining_system`` sums a whole closed loop as one free body and must
``analyse()`` each member to do it, while ``retaining_wall``'s per-wall record has to quote
the system's answer back. Two modules importing each other is a cycle; three, with the
mechanics at the bottom, is not.

``retaining_wall`` re-exports :class:`_Geometry` and :func:`analyse` under their old names,
so ``tests/test_retaining_wall_calc.py`` — whose ORACLE is the frozen hand pass — imports
and passes untouched.

**Oracle.** ``houses/catlin/notes/sunken_garden_retaining_screening.md`` §4 for the isolated
free cantilever; ``houses/catlin/notes/sunken_garden_court_free_body.md`` for the closed
loop and for the stem section. A calculation that only agrees with itself is not verified.

Conventions, so that a reader comparing rows compares like with like:

* moments are taken about the **toe**, per lineal foot of wall;
* a safety factor is carried as ``required / achieved`` so that, like every strength ratio
  beside it, **> 1 is over**;
* **passive resistance on the toe is neglected** unless the model can establish the toe's
  embedment. It is the standard conservative treatment and it barely matters here — on the
  catlin walls the toe is buried 6 1/2" and contributes under 1% of the resistance;
* **the wall stands ON its footing.** ``FoundationWall.bottom_elevation`` is the wall's own
  underside, which ``resolve/envelope.py::_resolve_footing`` makes the footing's TOP. So the
  stem is the wall's full height, and ``H`` for the free body is that height **plus** the
  footing depth — soil bears on the back of the heel as well as the back of the stem, and
  the surface being slid along is the footing's underside.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from typehaus.engineering.item import LimitState
from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.soil import (
    CONCRETE_UNIT_WEIGHT_PCF,
    SOIL_UNIT_WEIGHT_BAND_PCF,
    PresumptiveSoil,
    aggregate_bed,
)
from typehaus.model.enums import LayerFunction
from typehaus.model.rebar import BARS
from typehaus.resolve.concrete import concrete_spec_for, cover_in, fc_psi

BASIS = "IRC R404.4; IBC 1610.1 / 1806.2 presumptive values"

#: IRC R404.4's own requirement, and the only number here that is not a lookup.
REQUIRED_FS = 1.5

#: IRC Table R402.2's minimum specified compressive strength for foundation walls and other
#: vertical concrete **exposed to the weather** in a severe weathering region. Minnesota is
#: severe by rule and not by map: MN Rules 1309.0301 subp. 2 amends Table R301.2(1) and
#: writes "Severe" into the weathering column outright, so IRC Figure R301.2(4) never has to
#: be read. (Figure R301.2(3) is the wrong number — that was the 2012/2015 IRC.) It is
#: a code MINIMUM, and now only the **fallback**: a house that authors a ``ConcreteSpec`` on
#: its pour's assembly is graded on the mix it specified, and this value applies only where
#: none is authored. Every record says which of the two it read, because a capacity
#: understated by a presumptive strength and one computed from a real mix design are
#: different claims that a reader cannot tell apart from the number alone. Assuming more
#: than the code floor is the unsafe direction, so the floor is what the fallback assumes.
PRESUMPTIVE_FC_PSI = 3000.0

#: Grade 60, per IRC Table R404.1.2(8) footnote b.
REINFORCEMENT_FY_PSI = 60000.0

#: IBC 2018 §1605.2 Eq. 16-2..16-7 (ASCE 7-16 §2.3.1): the strength-design load factor on H,
#: lateral earth pressure, where H adds to the effect. Every other term in this module is a
#: SERVICE-load safety factor, because IBC §1807.2.3 says in as many words that §1605's
#: combinations do not apply to the FS-1.5 stability check. Flexure is the one limit state
#: ACI 318 states in strength terms, so it — and only it — carries this.
EARTH_PRESSURE_LOAD_FACTOR = 1.6

#: ASTM A615 bar sizes, from the shared pure-data table. ``model/rebar.py`` owns it because
#: ``takeoff/`` has to weigh a bar it must never ask ``engineering/`` about: a BOM that
#: imported a calc module would move every time a ``BASIS_VERSION`` moved.
_BAR = BARS

#: ACI 318-19 Table 20.5.1.3.1 — cast-in-place concrete exposed to earth and weather.
_COVER_IN = {True: 2.0, False: 1.5}   # keyed on "#6 or larger"

#: ACI 318-19 Table 20.5.1.3.1(a) — concrete cast against and permanently in contact with
#: ground. A strip footing is poured into a trench, so this is its condition and not the
#: "exposed to earth or weather" row a formed stem takes.
_FOOTING_COVER_IN = 3.0

#: ACI 318-19 §14.5.1.7 — a PLAIN footing cast against soil is computed on its thickness
#: less 2". Capacity goes as h squared, so this is a sixth of a 12" strip given away before
#: any number is computed. It applies to the plain branch only: a reinforced section is
#: graded on ``d``, which already measures from the bar to the compression face.
_PLAIN_SOIL_CAST_DEDUCTION_IN = 2.0

_M_PER_FT = 0.3048


@dataclass(frozen=True)
class _Geometry:
    """One wall's stem and footing, in feet, per lineal foot of wall."""

    tag: str
    stem_thickness_ft: float
    stem_height_ft: float
    footing_width_ft: float
    footing_depth_ft: float
    toe_ft: float
    heel_ft: float
    retained_height_ft: float
    #: Depth of soil in front of the toe, where the model establishes one. Neglected (0.0)
    #: otherwise — see the module docstring.
    toe_embedment_ft: float = 0.0
    #: ``FoundationWall.vertical_reinforcement`` verbatim, or None for a plain section.
    #: Parsed by :func:`stem_flexure`; an unparseable string is treated as no steel, which
    #: is the conservative reading and reports as such.
    vertical_reinforcement: str | None = None
    #: The f'c this wall's assembly SPECIFIES, or None where it specifies none. None is not
    #: 3,000 psi — it is "this model does not say", and :func:`stem_flexure` falls back to
    #: ``PRESUMPTIVE_FC_PSI`` and names which of the two it used.
    specified_fc_psi: float | None = None
    #: The FOOTING's own reinforcement, structured — the toe and heel are a different
    #: section from the stem and carry different bars. ``None`` means the model does not say,
    #: which for a 4'-0" toe is not a silence anything may fill: see :func:`footing_flexure`.
    footing_reinforcement: object | None = None
    #: The clear cover this wall's assembly SPECIFIES, inches, or None for the ACI
    #: Table 20.5.1.3.1 minimum. Cover is subtracted from the stem thickness to get ``d``,
    #: so 3" on a 12" stem is roughly -16% flexural capacity against 1-1/2": it is a
    #: durability decision that spends section, and it must be graded on what was authored.
    specified_cover_in: float | None = None


@dataclass(frozen=True)
class _Case:
    """One load case's results — a lateral pressure and a soil unit weight."""

    label: str
    efp_psf_per_ft: float
    soil_pcf: float
    thrust_plf: float
    weight_plf: float
    resistance_plf: float
    resisting_moment: float
    overturning_moment: float
    bearing_psf: float
    eccentricity_ft: float

    @property
    def fs_sliding(self) -> float:
        return self.resistance_plf / self.thrust_plf if self.thrust_plf else float("inf")

    @property
    def fs_overturning(self) -> float:
        return (self.resisting_moment / self.overturning_moment
                if self.overturning_moment else float("inf"))


def analyse(geometry: _Geometry, soil: PresumptiveSoil, *, at_rest: bool = False,
            soil_pcf: float = SOIL_UNIT_WEIGHT_BAND_PCF[0],
            base: PresumptiveSoil | None = None) -> _Case:
    """One load case, per lineal foot, moments about the toe.

    ``soil`` is the **retained** material — it sets the pressure on the stem. ``base`` is
    what the footing actually **bears on**, and it sets the friction, the passive term and
    the allowable bearing. They are usually the same and here they are not: these footings
    sit on 42" of replacement stone, and sliding happens at that interface, not against the
    silty gravel behind the wall. Defaults to ``soil`` so a wall bearing on its own subgrade
    needs no second argument.

    Kept a free function taking plain numbers so the oracle test can drive it straight from
    the hand calc's own table without building a model.
    """
    base = base or soil
    efp = soil.at_rest_efp_psf_per_ft if at_rest else soil.active_efp_psf_per_ft
    height = geometry.retained_height_ft

    # Triangular active (or at-rest) thrust, resultant at H/3 above the base.
    thrust = 0.5 * efp * height * height
    overturning = thrust * height / 3.0

    # Dead load only. IBC Table 1806.2 footnote a applies the friction coefficient to the
    # dead load, and nothing here is anything else.
    stem = geometry.stem_thickness_ft * geometry.stem_height_ft * CONCRETE_UNIT_WEIGHT_PCF
    footing = (geometry.footing_width_ft * geometry.footing_depth_ft
               * CONCRETE_UNIT_WEIGHT_PCF)
    # The column of soil standing on the heel — the term the heel exists for, and the one a
    # footing centred on its stem throws away half of.
    on_heel = geometry.heel_ft * geometry.stem_height_ft * soil_pcf
    weight = stem + footing + on_heel

    passive = 0.5 * base.lateral_bearing_psf_per_ft * geometry.toe_embedment_ft ** 2
    resistance = base.friction_coefficient * weight + passive

    resisting = (footing * geometry.footing_width_ft / 2.0
                 + stem * (geometry.toe_ft + geometry.stem_thickness_ft / 2.0)
                 + on_heel * (geometry.footing_width_ft - geometry.heel_ft / 2.0))

    # Resultant location, eccentricity from the footing's centre, and the trapezoidal
    # bearing pressure at the toe.
    arm = (resisting - overturning) / weight if weight else 0.0
    eccentricity = geometry.footing_width_ft / 2.0 - arm
    bearing = (weight / geometry.footing_width_ft
               * (1.0 + 6.0 * eccentricity / geometry.footing_width_ft))

    return _Case(
        label=("at-rest" if at_rest else "active") + f" {efp:.0f} psf/ft, soil {soil_pcf:.0f} pcf",
        efp_psf_per_ft=efp, soil_pcf=soil_pcf,
        thrust_plf=thrust, weight_plf=weight, resistance_plf=resistance,
        resisting_moment=resisting, overturning_moment=overturning,
        bearing_psf=bearing, eccentricity_ft=eccentricity,
    )


def parse_reinforcement(spec: str | None) -> tuple[int, float] | None:
    """``'#6 @ 10" o.c.'`` -> ``(6, 10.0)``. ``None`` where nothing parses.

    Deliberately strict about the two things that carry meaning — the bar number and the
    spacing — and indifferent to everything around them, because the field is free text a
    house authors for a drawing. A string this cannot read is reported as **no steel**: the
    conservative reading, and one the record names rather than swallows.
    """
    if not spec:
        return None
    match = re.search(r"#\s*(\d+)\s*@\s*([0-9]+(?:\.[0-9]+)?)", spec)
    if match is None:
        return None
    bar = int(match.group(1))
    spacing_in = float(match.group(2))
    if bar not in _BAR or spacing_in <= 0.0:
        return None
    return bar, spacing_in


def stem_flexure(geometry: _Geometry, case: _Case,
                 fc_psi: float | None = None) -> tuple[float, float, str]:
    """``(Mu, phi_Mn, how)`` for the stem at the top of the footing, ft-lb per foot of wall.

    **This is a limit state this engine had not computed before, and on the
    catlin walls the plain section is 4.5x over.** A base restraint fixes sliding and does
    not touch it: the moment is generated by the same soil, on the same stem, about a point
    a few inches from where the restraint acts.

    The cantilever is taken from the **top of the footing**, so the height is the soil above
    it — ``retained_height_ft`` less the footing depth — and not the ``H`` the stability free
    body slides along. The pressure is whatever ``case`` was run at, which is what keeps the
    section and the base graded on one load case rather than two.

    Strength design, because that is the only design method ACI 318 has published since
    318-08 struck the alternate one:

    * plain, ACI 318-19 §14.5.2 — ``Mn = 5 lambda sqrt(f'c) Sm``, ``phi = 0.60``
      (Table 21.2.1), ``Sm = b h^2 / 6`` on the gross section. **Reported, and not because
      ACI permits it**: R22.6.3 says the plain-concrete wall provisions apply "only for
      walls laterally supported in such a manner as to prohibit relative lateral
      displacement at top and bottom", and that the Code "does not cover walls without
      horizontal support ... Such laterally unsupported walls are to be designed as
      reinforced concrete members." A retaining wall is unsupported at the top by
      definition — which is the same condition that trips IRC R404.4. So an unreinforced
      stem here is not a section that fails a check; it is a section outside the Code, and
      the number is carried only to say how far outside;
    * reinforced, ACI 318-19 §22.3 — ``Mn = As fy (d - a/2)``, ``a = As fy / (0.85 f'c b)``,
      ``phi = 0.90`` for the tension-controlled section this is (checked below);
    * demand ``Mu = 1.6 M``, IBC 2018 §1605.2 / ASCE 7-16 §2.3.1 on H.

    **This is the one row in the module that is factored, and that is deliberate.** IBC 2018
    §1807.2.3 is explicit that the FS 1.5 against sliding and overturning is a SERVICE-level
    check — "the load combinations of Section 1605 shall not apply to this requirement.
    Instead, design shall be based on ... 1.0 times other nominal loads" — so every safety
    factor above is computed on unfactored loads, and putting 1.6H into them would
    double-count the conservatism. Section strength is the separate question §1605.2 does
    govern. Two checks, two load paths, and mixing them is the classic error here.

    The steel is on the **retained** face: that is where the cantilever puts the tension, and
    getting it on the wrong face is the classic way a correctly-sized wall falls over.
    """
    stem_ft = geometry.retained_height_ft - geometry.footing_depth_ft
    service = 0.5 * case.efp_psf_per_ft * stem_ft ** 2 * stem_ft / 3.0
    demand = EARTH_PRESSURE_LOAD_FACTOR * service

    b_in = 12.0
    h_in = geometry.stem_thickness_ft * 12.0
    # An explicit argument wins (a test pinning one number), then the wall's own authored
    # mix, then the code floor. The third is named in the returned prose so a reader can see
    # a presumptive strength for what it is.
    if fc_psi is None:
        fc_psi = geometry.specified_fc_psi or PRESUMPTIVE_FC_PSI
    fc_note = (f"f'c {fc_psi:,.0f} psi" if geometry.specified_fc_psi
               else f"f'c {fc_psi:,.0f} psi PRESUMPTIVE (no mix specified)")
    parsed = parse_reinforcement(geometry.vertical_reinforcement)
    if parsed is None:
        section = b_in * h_in ** 2 / 6.0
        capacity = 0.60 * 5.0 * fc_psi ** 0.5 * section / 12.0
        return demand, capacity, (f"PLAIN, {fc_note} — and ACI 318 R22.6.3 does "
                                  f"not cover an unsupported wall as plain concrete at all")

    # Cover comes off ``d`` directly, so an authored 3" for durability costs real capacity
    # and must not be quietly credited with the table minimum's longer lever arm.
    capacity, how = reinforced_flexure(h_in, fc_psi, parsed, geometry.specified_cover_in)
    return demand, capacity, f"{how}, {fc_note}"


def reinforced_flexure(h_in: float, fc_psi: float, parsed: tuple[int, float],
                       cover_in: float | None,
                       *, default_cover_in: float | None = None) -> tuple[float, str]:
    """``(phi*Mn in ft-lb per foot of section, how)`` for a singly-reinforced 12" strip.

    ACI 318-19 §22.3: ``Mn = As fy (d - a/2)``, ``a = As fy / (0.85 f'c b)``, ``phi = 0.90``
    on a tension-controlled section, which every wall and footing section in this house is
    by an enormous margin.

    Factored out of :func:`stem_flexure` so the stem and the FOOTING are graded by one
    function rather than two that agree today. They are the same question asked about two
    cantilevers — a stem about the top of its footing, a toe about the face of its stem —
    and the only thing that differs between them is which cover table applies.
    """
    bar, spacing_in = parsed
    area_in2, diameter_in = _BAR[bar].area_in2, _BAR[bar].diameter_in
    b_in = 12.0
    as_per_ft = area_in2 * b_in / spacing_in
    fallback = default_cover_in if default_cover_in is not None else _COVER_IN[bar >= 6]
    used_cover = cover_in if cover_in is not None else fallback
    cover_note = ("" if cover_in is not None
                  else " (ACI Table 20.5.1.3.1 minimum, none specified)")
    depth_in = h_in - used_cover - diameter_in / 2.0
    a_in = as_per_ft * REINFORCEMENT_FY_PSI / (0.85 * fc_psi * b_in)
    capacity = 0.90 * as_per_ft * REINFORCEMENT_FY_PSI * (depth_in - a_in / 2.0) / 12.0
    return capacity, (f"#{bar} @ {spacing_in:.0f}\" o.c., As {as_per_ft:.3f} in2/ft, "
                      f"cover {used_cover:.2f}\"{cover_note}, d {depth_in:.2f}\"")


def bar_for_roles(spec: object, roles: tuple[str, ...]) -> tuple[int, float] | None:
    """``(bar, spacing_in)`` for the first bar in ``spec`` whose role is one of ``roles``.

    A footing mat is authored by role — ``bottom-x`` is the transverse bottom steel that
    carries the toe, ``top-x`` the transverse top steel that carries the heel — and a bar in
    the wrong role is not a bar this section can use. ``None`` where the spec is absent, has
    no bar in any of those roles, or states a COUNT rather than a spacing: a strip footing
    is billed and graded per foot of run, and "four bars" says nothing about a foot of it.

    The conservative contract :func:`parse_reinforcement` keeps is kept here too — anything
    this cannot read is reported as NO steel, never as assumed steel.
    """
    if spec is None:
        return None
    for entry in getattr(spec, "bars", ()) or ():
        if entry.role not in roles or entry.spacing is None:
            continue
        spacing_in = float(entry.spacing.inches)
        if entry.bar not in _BAR or spacing_in <= 0.0:
            continue
        return entry.bar, spacing_in
    return None


def footing_states(geometry: _Geometry, case: _Case) -> tuple[LimitState, ...]:
    """Toe flexure, heel flexure and one-way shear on the footing STRIP.

    **These footings have a 4'-0" toe and nothing graded it.** ``_limit_states`` computed the
    bearing pressure under the strip and never asked whether the strip could carry it — which
    is a stability analysis of a rigid body, not a design of the concrete in it. A 4'-0"
    cantilever under 1,275 psf is a real flexural member, and the answer as PLAIN concrete is
    5x over: this is not a formality that passes on inspection.

    Same convention as :func:`stem_flexure` and for the same reason: the safety factors above
    are SERVICE-level per IBC §1807.2.3, and section strength is the separate question
    §1605.2 governs, so only these rows carry ``EARTH_PRESSURE_LOAD_FACTOR``.

    **Two deliberate conservatisms, each of which removes a load-factor argument rather than
    winning one.**

    * The **toe** is designed for the upward soil pressure ALONE. The footing's own weight
      (and any soil over the toe) pushes down and relieves it, and is dropped. Keeping it
      would mean factoring a *relieving* dead load, which ASCE 7 takes at 0.9 and this module
      has no combination machinery for; dropping it costs about 8% of the moment and costs no
      argument at all.
    * The **heel** is designed for the downward soil column and concrete ALONE, with the
      upward bearing pressure under it dropped. That is the mirror image and the standard
      one: the heel's job is to hold a column of earth down, and the pressure that would
      help is the pressure that vanishes exactly when the wall starts to rotate.

    The critical section for flexure is the face of the stem (ACI 318-19 §13.2.7.1(a), a
    concrete wall). For one-way shear it is ``d`` from that face for a reinforced section and
    ``h`` from it for a plain one (§14.5.5.2(a)), which is what the two branches differ by.
    """
    toe_ft, heel_ft = geometry.toe_ft, geometry.heel_ft
    width_ft, depth_ft = geometry.footing_width_ft, geometry.footing_depth_ft
    if width_ft <= 0.0 or depth_ft <= 0.0:
        return ()

    fc_psi = geometry.specified_fc_psi or PRESUMPTIVE_FC_PSI
    fc_note = (f"f'c {fc_psi:,.0f} psi" if geometry.specified_fc_psi
               else f"f'c {fc_psi:,.0f} psi PRESUMPTIVE (no mix specified)")
    h_in = depth_ft * 12.0
    cover_in = _footing_cover_in(geometry)

    # The trapezoid, toe end first. ``case.bearing_psf`` is q at the TOE; the heel end
    # follows from the same eccentricity with the sign flipped.
    q_toe = case.bearing_psf
    q_heel = (case.weight_plf / width_ft
              * (1.0 - 6.0 * case.eccentricity_ft / width_ft))
    slope = (q_toe - q_heel) / width_ft            # psf per foot, falling toward the heel

    # --- toe: cantilever about the front face of the stem, upward pressure only ----------
    q_face = q_toe - slope * toe_ft
    toe_service = (q_face * toe_ft * toe_ft / 2.0
                   + 0.5 * (q_toe - q_face) * toe_ft * (2.0 * toe_ft / 3.0))
    toe_demand = EARTH_PRESSURE_LOAD_FACTOR * toe_service

    # --- heel: the soil column and the concrete over it, bearing pressure dropped --------
    stem_height_ft = geometry.retained_height_ft - depth_ft
    soil_on_heel = heel_ft * stem_height_ft * case.soil_pcf
    concrete_on_heel = heel_ft * depth_ft * CONCRETE_UNIT_WEIGHT_PCF
    heel_service = (soil_on_heel + concrete_on_heel) * heel_ft / 2.0
    heel_demand = EARTH_PRESSURE_LOAD_FACTOR * heel_service

    toe_bars = bar_for_roles(geometry.footing_reinforcement, ("bottom-x", "bottom-y"))
    heel_bars = bar_for_roles(geometry.footing_reinforcement, ("top-x", "top-y"))

    toe_capacity, toe_how = _footing_flexural_capacity(h_in, fc_psi, toe_bars, cover_in)
    heel_capacity, heel_how = _footing_flexural_capacity(h_in, fc_psi, heel_bars, cover_in)

    # --- one-way shear on the toe, the governing of the two cantilevers -----------------
    if toe_bars is not None:
        depth_in = h_in - cover_in - _BAR[toe_bars[0]].diameter_in / 2.0
        offset_ft = min(depth_in / 12.0, toe_ft)
        # ACI 318-19 §22.5.5.1: Vc = 2 lambda sqrt(f'c) b d, phi 0.75 (Table 21.2.1).
        shear_capacity = 0.75 * 2.0 * fc_psi ** 0.5 * 12.0 * depth_in
        shear_how = (f"ACI 318-19 §22.5.5.1 Vc = 2 lambda sqrt(f'c) b d, phi 0.75, at d "
                     f"{depth_in:.2f}\" from the stem face — {fc_note}")
    else:
        plain_h_in = max(h_in - _PLAIN_SOIL_CAST_DEDUCTION_IN, 0.0)
        offset_ft = min(plain_h_in / 12.0, toe_ft)
        # ACI 318-19 §14.5.5.1(a): Vn = (4/3) lambda sqrt(f'c) b h, phi 0.60.
        shear_capacity = 0.60 * (4.0 / 3.0) * fc_psi ** 0.5 * 12.0 * plain_h_in
        shear_how = (f"ACI 318-19 §14.5.5.1(a) PLAIN, Vn = (4/3) lambda sqrt(f'c) b h, phi "
                     f"0.60, at h {plain_h_in:.1f}\" from the stem face — §14.5.1.7 takes 2\" "
                     f"off a footing cast against soil — {fc_note}")
    cut_ft = toe_ft - offset_ft
    q_cut = q_toe - slope * cut_ft
    shear_demand = EARTH_PRESSURE_LOAD_FACTOR * 0.5 * (q_toe + q_cut) * cut_ft

    return (
        LimitState("toe flexure", toe_demand, toe_capacity, "ft-lb/ft",
                   f"ACI 318-19 §13.2.7.1 at the stem face, strength design at 1.6H over a "
                   f"{toe_ft:.2f}' toe — {toe_how}, {fc_note}"),
        LimitState("heel flexure", heel_demand, heel_capacity, "ft-lb/ft",
                   f"ACI 318-19 §13.2.7.1 at the stem face, strength design at 1.6H on a "
                   f"{heel_ft:.2f}' heel carrying {stem_height_ft:.2f}' of soil at "
                   f"{case.soil_pcf:.0f} pcf — {heel_how}, {fc_note}"),
        LimitState("footing one-way shear", shear_demand, shear_capacity, "lb/ft",
                   shear_how),
    )


def _footing_cover_in(geometry: _Geometry) -> float:
    """Clear cover to the footing mat: what the pour specifies, else ACI's cast-against-earth 3"."""
    spec = geometry.footing_reinforcement
    authored = getattr(spec, "cover", None) if spec is not None else None
    if authored is not None:
        return float(authored.inches)
    if geometry.specified_cover_in is not None:
        return geometry.specified_cover_in
    return _FOOTING_COVER_IN


def _footing_flexural_capacity(h_in: float, fc_psi: float, parsed: tuple[int, float] | None,
                               cover_in: float) -> tuple[float, str]:
    """``(phi*Mn ft-lb/ft, how)`` — reinforced where a mat is authored, PLAIN where none is.

    **Plain is what the model actually says, and it is not a formality.** ACI 318-19 §14.1.4
    permits a plain concrete footing, so a mat this engine cannot read is graded as the plain
    section it then is, and reported OVER if the plain section will not carry the moment —
    which on a 4'-0" toe it will not, by a factor of five. That is the honest reading: an
    INCOMPLETE here would say "the model is silent", where the truth is "the model is silent
    AND the section that silence implies does not work".
    """
    if parsed is None:
        plain_h_in = max(h_in - _PLAIN_SOIL_CAST_DEDUCTION_IN, 0.0)
        section = 12.0 * plain_h_in ** 2 / 6.0
        capacity = 0.60 * 5.0 * fc_psi ** 0.5 * section / 12.0
        return capacity, (f"PLAIN — no mat authored on this Footing, so §14.5.2.1(a) "
                          f"Mn = 5 lambda sqrt(f'c) Sm on a 12\" x {plain_h_in:.1f}\" gross "
                          f"section (§14.5.1.7 takes 2\" off a pour cast against soil)")
    return reinforced_flexure(h_in, fc_psi, parsed, cover_in,
                              default_cover_in=_FOOTING_COVER_IN)


def _limit_states(case: _Case, geometry: _Geometry, soil: PresumptiveSoil,
                  base: PresumptiveSoil | None = None) -> tuple[LimitState, ...]:
    """The five comparisons, all in the demand/capacity convention (> 1 is over)."""
    base = base or soil
    flexure_demand, flexure_capacity, flexure_how = stem_flexure(geometry, case)
    return (
        LimitState("sliding", REQUIRED_FS, case.fs_sliding, "", "IRC R404.4",
                   is_safety_factor=True),
        LimitState("overturning", REQUIRED_FS, case.fs_overturning, "", "IRC R404.4",
                   is_safety_factor=True),
        LimitState("bearing", case.bearing_psf, base.allowable_bearing_psf, "psf",
                   f"IBC Table 1806.2 class {base.ibc_class}"),
        # Outside the middle third the heel lifts and the trapezoid above stops describing
        # the real pressure distribution, so this is a validity check on the row above it as
        # much as a limit state of its own.
        LimitState("eccentricity", abs(case.eccentricity_ft),
                   geometry.footing_width_ft / 6.0, "ft", "kern of the base (B/6)"),
        # The SECTION, not the base. Everything above it is a stability question about a
        # rigid body; this is the only row that asks whether the concrete can carry the
        # moment the soil puts in it, and it is the row a base restraint does not help.
        LimitState("stem flexure", flexure_demand, flexure_capacity, "ft-lb/ft",
                   f"ACI 318 strength design at 1.6H — {flexure_how}"),
        # The FOOTING as a section, which is the other half of the same omission the row
        # above closed for the stem: a 4'-0" toe under a thousand-odd psf is a cantilever,
        # and nothing here had ever asked whether it carries.
    ) + footing_states(geometry, case)


def _base_interface(ctx: EngineeringContext, wall) -> PresumptiveSoil | None:  # type: ignore[no-untyped-def]
    """What the footing under this wall actually bears on.

    Sliding happens at the base, so the friction coefficient describes the interface there —
    not the backfill behind the stem. Where a ``FootingBedding`` replaces the subgrade with a
    compacted washed-stone section, that stone is the bearing material and IBC Table 1806.2's
    gravel row is the right one.

    The gradation claim is not inferred from the ``aggregate`` free-text string, which would
    be reading a soil classification out of a substring — the same guess ``FootingBedding``'s
    own docstring refuses. It is taken from ``non_frost_susceptible``, which is an authored
    ASTM D422 claim (<6% passing the #200 sieve) about that very stone, and a bed that makes
    it is by that claim a clean open-graded gravel. A bedding that does not declare it falls
    back to the site's own class, which is the conservative direction.
    """
    from typehaus.model.structure import Footing, FootingBedding

    footing = next((f for f in ctx.plan.all_elements()
                    if isinstance(f, Footing) and f.under == wall.tag), None)
    hosts = {wall.tag} | ({footing.tag} if footing is not None else set())
    for bedding in ctx.plan.all_elements():
        if (isinstance(bedding, FootingBedding) and bedding.host_ref in hosts
                and getattr(bedding, "non_frost_susceptible", None) is True):
            return aggregate_bed()
    return None


def _geometry(ctx: EngineeringContext, wall) -> tuple[_Geometry | None, list[str]]:  # type: ignore[no-untyped-def]
    """The stem and footing dimensions, or the names of what the model does not carry."""
    from typehaus.model.structure import Footing

    tag = wall.tag
    missing: list[str] = []

    # The mix this wall's assembly specifies, if it specifies one. ``None`` all the way
    # through means "unstated", which ``stem_flexure`` falls back on and names — never a
    # silent default, per decision #32.
    spec = concrete_spec_for(ctx.plan, wall)

    thickness_in = _structure_thickness_in(ctx, wall.assembly)
    if thickness_in is None:
        missing.append(f"a concrete STRUCTURE layer on assembly {wall.assembly}")

    if wall.top_elevation is None or wall.bottom_elevation is None:
        missing.append(f"top_elevation/bottom_elevation on {tag}")
        wall_height = None
    else:
        wall_height = (wall.top_elevation.meters - wall.bottom_elevation.meters) / _M_PER_FT

    footing = next((f for f in ctx.plan.all_elements()
                    if isinstance(f, Footing) and f.under == tag), None)
    if footing is None:
        missing.append(f"a Footing under {tag}")

    if wall.unbalanced_fill is None:
        # Deliberately not derived from Site.grade here. The check's proxy measures to a
        # single global grade plane, and a wall with a terrace against it — which is exactly
        # the condition that sends a wall to R404.4 — is what a plane cannot describe. A
        # retaining-wall design against an understated height is worse than none.
        missing.append(f"an authored unbalanced_fill on {tag} (the grade-plane proxy is not "
                       f"a safe input for a retaining-wall design)")

    if missing:
        return None, missing

    width_ft = footing.width.meters / _M_PER_FT
    depth_ft = footing.depth.meters / _M_PER_FT
    # **The wall stands ON the footing.**
    # ``resolve/envelope.py::_resolve_footing`` puts a wall-hosted footing at
    # ``z1 = wall.z0_m`` — footing TOP = wall BOTTOM, the footing entirely below the wall.
    # W-SG-E2 resolves z0 -118.4375" / z1 +6.0" and FT-SG-E2 z0 -130.4375" / z1 -118.4375",
    # which is that convention measured. Getting this backwards subtracts ``depth_ft`` from
    # a height that never contained it: the stem, and the column of soil standing on the
    # heel beside it, both end up counted a foot short.
    stem_ft = wall_height
    thickness_ft = thickness_in / 12.0
    # **Which side is the heel, and why it cannot be assumed.** A centred footing (the
    # historical case, ``Footing.offset`` unset) has toe == heel and the question does not
    # arise. An offset one is the whole point of the field — toe and heel do different jobs
    # and want different widths — and then reading the sign backwards silently swaps the
    # term that carries the stabilising soil for the one that does not.
    #
    # ``resolve/orientation`` is the authority: ``resolve_wall_geometry`` puts the assembly's
    # interior face on the ``-sign * normal(start->end)`` side, so the EXTERIOR — the face
    # the soil is retained against — is at ``+sign``. ``Footing.offset`` is in that same
    # left-normal frame, so ``offset * sign`` is the offset measured toward the heel.
    offset_ft = 0.0
    if footing.offset is not None and footing.offset.meters:
        signed, sign_missing = _heelward_offset(ctx, wall, footing)
        if sign_missing is not None:
            return None, [sign_missing]
        offset_ft = signed
    half = (width_ft - thickness_ft) / 2.0
    heel_ft = half + offset_ft
    toe_ft = half - offset_ft
    if heel_ft < 0.0 or toe_ft < 0.0:
        return None, [f"a footing under {tag} that reaches past its own stem "
                      f"(offset {offset_ft:.2f}' on a {width_ft:.2f}' base)"]
    return _Geometry(
        tag=tag,
        stem_thickness_ft=thickness_ft,
        stem_height_ft=stem_ft,
        footing_width_ft=width_ft,
        footing_depth_ft=depth_ft,
        toe_ft=toe_ft,
        heel_ft=heel_ft,
        vertical_reinforcement=getattr(wall, "vertical_reinforcement", None),
        footing_reinforcement=getattr(footing, "reinforcement", None),
        specified_fc_psi=fc_psi(spec),
        specified_cover_in=cover_in(spec),
        # **Two different heights, and conflating them was the other half of the same slip.**
        # ``unbalanced_fill`` is the IRC quantity — fill against the wall, measured to the
        # base of the wall — and it is what R404.1.1's 48" threshold and Table R404.1.2(8)'s
        # rows are read against. ``H`` for a *stability* free body runs from the top of the
        # retained soil to the **underside of the footing**, because soil bears on the back
        # of the stem and on the back of the heel alike, and the base being slid along is the
        # footing's underside. On these walls that is 10.37' against 11.37', and the thrust
        # between them differs by 20%.
        retained_height_ft=wall.unbalanced_fill.meters / _M_PER_FT + depth_ft,
    ), []



def _heelward_offset(ctx: EngineeringContext, wall, footing) -> tuple[float, str | None]:  # type: ignore[no-untyped-def]
    """``Footing.offset`` in feet, signed **toward the heel**, or the name of what is missing.

    The sign comes from the storey's winding, and an unrecoverable winding is refused rather
    than defaulted. ``UNRECOVERABLE_WINDING_OUTWARD_SIGN`` is +1 — a real value a real
    structure can also have — so a caller that simply took it would get a plausible answer
    and no warning, on the one input where being wrong swaps the toe for the heel. A
    component with no closed loop has zero signed outer-loop area, and that is the test.
    """
    from typehaus.resolve.orientation import resolve_storey_windings, wall_outward_sign

    resolved = next((w for w in ctx.model.walls if w.tag == wall.tag), None)
    if resolved is None:
        return 0.0, f"a resolved {wall.tag} to take the footing offset's sign from"
    windings = resolve_storey_windings(ctx.plan, resolved.storey)
    key = windings.component_key_for_wall(wall)
    if not windings.outer_loop_area_by_component_key.get(key):
        return 0.0, (f"a recoverable winding on {wall.tag}'s structure — its footing is "
                     f"authored off-centre and nothing says which side the heel is on")
    sign = wall_outward_sign(ctx.plan, wall, resolved.storey, windings.sign_for_wall(wall))
    return footing.offset.meters / _M_PER_FT * sign, None


def _structure_thickness_in(ctx: EngineeringContext, assembly_tag: str) -> float | None:
    """The concrete STRUCTURE layer's nominal thickness. The foam over it retains nothing."""
    assembly = next((a for a in ctx.plan.library.assemblies if a.tag == assembly_tag), None)
    if assembly is None:
        return None
    for layer in assembly.layers:
        if layer.function is LayerFunction.STRUCTURE:
            return round(layer.thickness.inches * 2.0) / 2.0
    return None
