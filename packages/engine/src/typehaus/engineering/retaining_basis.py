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

BASIS = "IRC R404.4; IBC 1610.1 / 1806.2 presumptive values"

#: IRC R404.4's own requirement, and the only number here that is not a lookup.
REQUIRED_FS = 1.5

#: IRC Table R402.2's minimum specified compressive strength for foundation walls and other
#: vertical concrete **exposed to the weather** in a severe weathering region. Minnesota is
#: severe by rule and not by map: MN Rules 1309.0301 subp. 2 amends Table R301.2(1) and
#: writes "Severe" into the weathering column outright, so IRC Figure R301.2(4) never has to
#: be read. (Figure R301.2(3) is the wrong number — that was the 2012/2015 IRC.) It is
#: a code MINIMUM standing in for a mix design nobody has written: ``Material`` carries no
#: ``f'c`` field, so no house can state one, and reading a strength out of a material tag
#: would be the same guess ``FootingBedding`` refuses about its own gradation. Assuming more
#: than the code floor is the unsafe direction, so the floor is what is assumed.
PRESUMPTIVE_FC_PSI = 3000.0

#: Grade 60, per IRC Table R404.1.2(8) footnote b.
REINFORCEMENT_FY_PSI = 60000.0

#: IBC 2018 §1605.2 Eq. 16-2..16-7 (ASCE 7-16 §2.3.1): the strength-design load factor on H,
#: lateral earth pressure, where H adds to the effect. Every other term in this module is a
#: SERVICE-load safety factor, because IBC §1807.2.3 says in as many words that §1605's
#: combinations do not apply to the FS-1.5 stability check. Flexure is the one limit state
#: ACI 318 states in strength terms, so it — and only it — carries this.
EARTH_PRESSURE_LOAD_FACTOR = 1.6

#: (area in^2, diameter in) by bar designation. ASTM A615 standard sizes.
_BAR: dict[int, tuple[float, float]] = {
    3: (0.11, 0.375), 4: (0.20, 0.500), 5: (0.31, 0.625),
    6: (0.44, 0.750), 7: (0.60, 0.875), 8: (0.79, 1.000),
}

#: ACI 318-19 Table 20.5.1.3.1 — cast-in-place concrete exposed to earth and weather.
_COVER_IN = {True: 2.0, False: 1.5}   # keyed on "#6 or larger"

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
                 fc_psi: float = PRESUMPTIVE_FC_PSI) -> tuple[float, float, str]:
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
    parsed = parse_reinforcement(geometry.vertical_reinforcement)
    if parsed is None:
        section = b_in * h_in ** 2 / 6.0
        capacity = 0.60 * 5.0 * fc_psi ** 0.5 * section / 12.0
        return demand, capacity, (f"PLAIN, f'c {fc_psi:,.0f} psi — and ACI 318 R22.6.3 does "
                                  f"not cover an unsupported wall as plain concrete at all")

    bar, spacing_in = parsed
    area_in2, diameter_in = _BAR[bar]
    as_per_ft = area_in2 * b_in / spacing_in
    depth_in = h_in - _COVER_IN[bar >= 6] - diameter_in / 2.0
    a_in = as_per_ft * REINFORCEMENT_FY_PSI / (0.85 * fc_psi * b_in)
    capacity = 0.90 * as_per_ft * REINFORCEMENT_FY_PSI * (depth_in - a_in / 2.0) / 12.0
    return demand, capacity, (f"#{bar} @ {spacing_in:.0f}\" o.c., As {as_per_ft:.3f} in2/ft, "
                              f"d {depth_in:.2f}\", f'c {fc_psi:,.0f} psi")


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
    )


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
