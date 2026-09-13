"""The girt crossing screw — ``girt_screw/<lowest Wall tag in the group>``.

**Why this item exists.** The catlin truss wall hangs everything outboard of the sheathing
on one screw per crossing, and nothing graded it. ``engineering/wall_panel.py`` grades the
panel and says so in its own "NOT CHECKED" note; ``notes/catlin_truss_engineering.md`` §3
hand-worked the withdrawal and stopped there — it never stated the screw's THREAD length,
never checked whether that thread could clamp the stack, and never checked the head. The
wall's entire load path was resting on a number nobody had finished.

It is decision #65's case and not an UNKNOWN: a demand that can be computed, capacities
that are published, and a design a seal can confirm. It is **register-only**, the
``wall_panel`` precedent — no ``engineered()`` bridge, no ``PermitItemSpec``, no ratchet.
The screw is a component of an assembly no prescriptive table reaches, so there is no
prescriptive check for an engineered record to answer.

Three limit states, and the first is the one the audit found open
---------------------------------------------------------------
* **Thread engagement.** A lag-type screw draws two members together only if the members
  being clamped are spanned by plain SHANK. Every SDWS22 threads 3" at every length
  (IAPMO UES ER-192 Table 7), so the 8" SDWS22800DB this wall specified until 2026-09-12
  stood 1" of thread inside a 6.0" stack and could not pull it tight. FastenMaster
  TimberLOK threads 2" (ICC-ES ESR-1078 Table 1A): 6" of shank against a 6.0" stack, and
  the thread starts where the stud does. Graded as ``stack <= plain shank``, which is the
  same inequality written so a ratio of exactly 1.000 is the correct answer rather than a
  division by zero — and marked ``is_detailing`` for that reason, so it never wins
  ``governing`` from a real force ratio by sitting on its own minimum.
* **Withdrawal** of the embedded thread from the stud.
* **Head pull-through** of the girt, which IS the 1-1/2" side member the report's table
  assumes.

**Capacities are READ, demand is COMPUTED.** The withdrawal and pull-through numbers come
off the screw's evaluation report through ``FramingSpec.standoff_fastener_*`` — authored on
the house, because ``engineering/`` may not import the hardware catalog
(``library/hardware.py`` reaches ``takeoff``). NDS §12.2's ``W = 2850 G^2 D`` is computed
alongside as a cross-check only, never as the grade.

The demand is ``wall_panel``'s, term for term: the same q_h at mean roof height, the same
Zone 5 GC_p and GC_pi, the same 0.6W. It has to be — the panel and the screw carry one
suction, and two numbers for it would mean one of them was wrong.

**One item per geometry, not per wall**, keyed by the lowest member tag. Every
``standoff="block"`` wall on this house resolves to one stack and one module, so
``EXT_2X6`` and ``PLANT_EXT_2X6_HUMID`` are one design and one seal. ``crossing_count`` is
an input so a membership change stales the stamp.

**Oracle.** ``houses/catlin/notes/catlin_truss_engineering.md`` §3;
``tests/test_girt_screw_calcs.py`` reproduces it.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus import wind
from typehaus.engineering.girt_screw_withdrawal import (
    crossing_demand_lb,
    minimum_penetration_in,
    nds_withdrawal_per_in,
    plain_shank_in,
    thread_in_main_member,
    thread_in_side_member,
    tributary_area_ft2,
    withdrawal_lb,
)
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.wall_panel import (
    GC_PI,
    effective_wind_area_ft2,
    external_pressure_coefficient,
    mean_roof_height_ft,
)
from typehaus.model.enums import LayerFunction
from typehaus.resolve.framing.truss_girts import truss_girt_bands

KIND = "girt_screw"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "1"
BASIS = ("ASCE 7-16 §30.3 (C&C, walls) with §2.4.1 0.6W; the screw's own evaluation report "
         "for withdrawal and head pull-through; AWC NDS 2018 §12.1.4.6 / §12.2")

#: The stud module's default when a STRUCTURE layer's ``FramingSpec`` leaves it unset — the
#: same 16" the framing solver falls back to (``framing/tables.DEFAULT_SPACING``). Stated
#: here rather than imported so this leaf does not reach into the solver's tables.
_DEFAULT_STUD_SPACING_IN = 16.0


@dataclass(frozen=True)
class _Crossing:
    """One wall's girt-to-stud crossing, measured off the authored assembly."""

    wall_tag: str
    assembly: str
    course_spacing_in: float
    block_spacing_in: float
    girt_in: float
    block_in: float
    sheathing_in: float
    mean_roof_height_ft: float
    # The screw, all of it authored on the girt band's FramingSpec.
    fastener: str | None
    part: str | None
    diameter_in: float | None
    length_in: float | None
    thread_in: float | None
    withdrawal_lb_per_in: float | None
    pull_through_lb: float | None
    source: str | None
    # The two woods: the girt the head bears on, the stud the thread lands in.
    girt_material: str
    stud_material: str
    stud_specific_gravity: float | None

    @property
    def clamped_stack_in(self) -> float:
        """Girt + block. The sheathing is nailed to the stud and is not being clamped."""
        return self.girt_in + self.block_in

    @property
    def through_in(self) -> float:
        return self.clamped_stack_in + self.sheathing_in


def _crossings(ctx: EngineeringContext) -> list[_Crossing]:
    """Every wall whose outer band is a block-standoff girt.

    Read off the AUTHORED assembly, like ``wall_panel._framing_spacing_in``: a
    ``layer_materials`` override swaps a material and never a ``FramingSpec``, and the
    block's depth is a property of the stack rather than of any one resolved wall.
    """
    catalog = {material.tag: material for material in ctx.plan.library.materials}
    height = mean_roof_height_ft(ctx) or 0.0
    seen: set[str] = set()
    out: list[_Crossing] = []
    for wall in ctx.model.walls:
        bands = truss_girt_bands(ctx.plan, wall.assembly)
        if bands is None or wall.tag in seen:
            continue
        seen.add(wall.tag)
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        if assembly is None:
            continue
        outer = bands[1]
        spec = outer.framing
        if spec is None or spec.spacing is None:
            continue
        structure = next((lay for lay in assembly.layers
                          if lay.function is LayerFunction.STRUCTURE), None)
        if structure is None:
            continue
        stud_spacing = getattr(getattr(structure, "framing", None), "spacing", None)
        stud_spacing_in = (float(stud_spacing.inches) if stud_spacing is not None
                           else _DEFAULT_STUD_SPACING_IN)
        # One tier puts a block on every OTHER stud; two tiers put one at every stud. The
        # same rule ``truss_girts.GirtFrame`` derives its block module from.
        block_spacing_in = stud_spacing_in * (1.0 if bands[0] is not None else 2.0)
        stud = catalog.get(structure.material_ref or "")
        out.append(_Crossing(
            wall_tag=wall.tag, assembly=wall.assembly or "",
            course_spacing_in=float(spec.spacing.inches),
            block_spacing_in=block_spacing_in,
            girt_in=float(outer.thickness.inches),
            block_in=_block_depth_in(assembly, outer.name),
            sheathing_in=sum(float(lay.thickness.inches) for lay in assembly.layers
                             if lay.function is LayerFunction.SHEATHING),
            mean_roof_height_ft=height,
            fastener=spec.standoff_fastener,
            part=spec.standoff_fastener_part,
            diameter_in=spec.standoff_fastener_diameter_in,
            length_in=spec.standoff_fastener_length_in,
            thread_in=spec.standoff_fastener_thread_in,
            withdrawal_lb_per_in=spec.standoff_fastener_withdrawal_lb_per_in,
            pull_through_lb=spec.standoff_fastener_pull_through_lb,
            source=spec.standoff_fastener_source,
            girt_material=outer.material_ref or "",
            stud_material=structure.material_ref or "",
            stud_specific_gravity=getattr(stud, "specific_gravity", None)))
    return out


def _block_depth_in(assembly, outer_name: str) -> float:
    """What the block fills: everything between the sheathing and the girt band.

    Derived, never authored — the same contract ``truss_girts.GirtFrame`` keeps. Moving the
    girt out in an assembly moves the block, the clamped stack and the screw with it.
    """
    names = [layer.name for layer in assembly.layers]
    sheathing = [index for index, layer in enumerate(assembly.layers)
                 if layer.function is LayerFunction.SHEATHING]
    if not sheathing or outer_name not in names:
        return 0.0
    return sum(float(layer.thickness.inches)
               for layer in assembly.layers[sheathing[-1] + 1:names.index(outer_name)])


def _groups(ctx: EngineeringContext) -> dict[str, list[_Crossing]]:
    """One entry per geometry-and-screw, keyed by the lowest member tag.

    Two assemblies that resolve to the same stack, the same two modules and the same screw
    are one design: ``EXT_2X6`` and ``PLANT_EXT_2X6_HUMID`` differ only in an interior
    liner the screw never reaches.
    """
    buckets: dict[tuple, list[_Crossing]] = {}
    for crossing in _crossings(ctx):
        signature = (crossing.course_spacing_in, crossing.block_spacing_in,
                     crossing.girt_in, crossing.block_in, crossing.sheathing_in,
                     crossing.part, crossing.length_in, crossing.thread_in)
        buckets.setdefault(signature, []).append(crossing)
    return {min(c.wall_tag for c in members): sorted(members, key=lambda c: c.wall_tag)
            for members in buckets.values()}


#: The independent hand pass this module is checked against — see ``Oracle``.
oracled_by(
    KIND,
    Oracle(note="catlin_truss_engineering.md", section="§3",
           test="tests/test_girt_screw_calcs.py"),
)


@keys(KIND)
def enumerate_girt_screws(ctx: EngineeringContext) -> list[str]:
    return sorted(_groups(ctx))


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, key, members) for key, members in sorted(_groups(ctx).items())]


def _one(ctx: EngineeringContext, key: str, members: list[_Crossing]) -> EngineeringRecord:
    crossing = members[0]
    tags = tuple(member.wall_tag for member in members)
    ident = item_id(KIND, key)
    basis = wind.wind_basis(ctx.plan.project.site)
    missing: list[str] = []
    if basis is None:
        missing.append("a complete design wind basis on Site "
                       "(design_wind_speed_mph, wind_exposure, risk_category)")
    if crossing.mean_roof_height_ft <= 0.0:
        missing.append("a resolved roof to take the mean roof height from")
    if basis is None or crossing.mean_roof_height_ft <= 0.0:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=key,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{key}: the girt crossing's wind demand could not be computed",
            missing=tuple(missing), element_tags=tags)

    q_h = wind.velocity_pressure_psf(basis, crossing.mean_roof_height_ft)
    area = effective_wind_area_ft2(crossing.course_spacing_in)
    gcp = external_pressure_coefficient(area, "5")
    strength_psf = abs(q_h * (gcp - GC_PI))
    demand_psf = wind.ASD_WIND_FACTOR * strength_psf
    trib = tributary_area_ft2(crossing.block_spacing_in, crossing.course_spacing_in)
    demand_lb = crossing_demand_lb(demand_psf, crossing.block_spacing_in,
                                   crossing.course_spacing_in)

    states: list[LimitState] = []
    thread_in_stud = _states(crossing, demand_lb, states, missing)

    inputs = [
        Quantity("design_wind_speed", basis.speed_mph, "mph", 1.0),
        Quantity("mean_roof_height", crossing.mean_roof_height_ft, "ft", 0.01),
        Quantity("velocity_pressure", q_h, "psf", 0.01),
        Quantity("course_spacing", crossing.course_spacing_in, "in", 0.25),
        Quantity("block_spacing", crossing.block_spacing_in, "in", 0.25),
        Quantity("GCp_zone5", gcp, "", 0.01),
        Quantity("GCpi", GC_PI, "", 0.01),
        Quantity("suction_asd", demand_psf, "psf", 0.01),
        Quantity("tributary_area", trib, "ft2", 0.01),
        Quantity("crossing_demand", demand_lb, "lb", 0.1),
        Quantity("clamped_stack", crossing.clamped_stack_in, "in", 0.01),
        Quantity("through_thickness", crossing.through_in, "in", 0.01),
        Quantity("crossing_count", float(len(members)), "", None),
    ]
    for name, value, unit, quantum in (
            ("fastener_length", crossing.length_in, "in", 0.01),
            ("fastener_thread", crossing.thread_in, "in", 0.01),
            ("fastener_diameter", crossing.diameter_in, "in", 0.001),
            ("withdrawal_per_in", crossing.withdrawal_lb_per_in, "lb/in", 0.1),
            ("head_pull_through", crossing.pull_through_lb, "lb", 1.0),
            ("specific_gravity", crossing.stud_specific_gravity, "", 0.01)):
        if value is not None:
            inputs.append(Quantity(name, value, unit, quantum))
    if thread_in_stud is not None:
        inputs.append(Quantity("thread_in_stud", thread_in_stud, "in", 0.01))

    over = any(not state.ok for state in states)
    status = Status.OVER if over else (Status.INCOMPLETE if missing else Status.OK)
    others = (f", and {len(members) - 1} more wall(s) on the same design"
              if len(members) > 1 else "")
    screw = crossing.fastener or "an unauthored screw"
    return EngineeringRecord(
        item_id=ident, kind=KIND, key=key,
        basis_version=BASIS_VERSION, basis=BASIS, status=status,
        summary=(f"{key}{others}: one {screw} per crossing through a "
                 f"{crossing.clamped_stack_in:g}\" clamped stack, "
                 f"{demand_lb:,.1f} lb ASD suction on "
                 f"{crossing.block_spacing_in:g}\" x {crossing.course_spacing_in:g}\""),
        inputs=tuple(inputs), limit_states=tuple(states), missing=tuple(missing),
        notes=tuple(_notes(crossing, demand_psf, strength_psf, demand_lb, basis,
                           thread_in_stud, len(members))),
        element_tags=tags)


def _states(crossing: _Crossing, demand_lb: float, states: list[LimitState],
            missing: list[str]) -> float | None:
    """The three graded states plus the 6D input check, or the exact field that is absent."""
    absent = [
        (crossing.length_in is None, "standoff_fastener_length_in"),
        (crossing.thread_in is None, "standoff_fastener_thread_in"),
        (crossing.diameter_in is None, "standoff_fastener_diameter_in"),
        (crossing.withdrawal_lb_per_in is None, "standoff_fastener_withdrawal_lb_per_in"),
        (crossing.pull_through_lb is None, "standoff_fastener_pull_through_lb"),
    ]
    named = [field for is_absent, field in absent if is_absent]
    if named:
        missing.extend(
            f"FramingSpec.{field} on the {crossing.assembly or '(unnamed)'} girt band — "
            f"the screw's own report value; nothing here defaults one" for field in named)
        return None
    assert crossing.length_in is not None and crossing.thread_in is not None
    assert crossing.diameter_in is not None
    assert crossing.withdrawal_lb_per_in is not None
    assert crossing.pull_through_lb is not None

    # 1. Thread engagement. Written as `stack <= plain shank` rather than as the equivalent
    #    `thread in the stack <= 0`: a capacity of zero is a ratio of infinity, and a
    #    correctly chosen screw would report as failing. Detailing, because a screw that
    #    fits exactly sits at 1.000 and that is the RIGHT answer, not a governing state.
    shank = plain_shank_in(crossing.length_in, crossing.thread_in)
    jacking = thread_in_side_member(crossing.length_in, crossing.thread_in,
                                    crossing.clamped_stack_in)
    states.append(LimitState(
        "thread engagement (plain shank across the clamped stack)",
        crossing.clamped_stack_in, shank, "in",
        f"a lag-type screw clamps only on plain shank; "
        f"{crossing.length_in:g}\" long less {crossing.thread_in:g}\" thread = {shank:g}\" "
        f"against a {crossing.clamped_stack_in:g}\" stack, leaving {jacking:g}\" of thread "
        f"standing inside it ({crossing.source or 'unsourced'})",
        is_detailing=True))

    # 2. Withdrawal of the embedded thread from the stud.
    thread_in_stud = thread_in_main_member(
        crossing.length_in, crossing.thread_in, crossing.through_in)
    capacity = withdrawal_lb(crossing.withdrawal_lb_per_in, thread_in_stud)
    if thread_in_stud <= 0.0:
        missing.append(
            f"a longer screw: a {crossing.length_in:g}\" screw through "
            f"{crossing.through_in:g}\" of girt, block and sheathing has no thread left in "
            f"the stud")
    else:
        states.append(LimitState(
            "screw withdrawal from the stud", demand_lb, capacity, "lb",
            f"{crossing.withdrawal_lb_per_in:g} lb/in of embedded thread x "
            f"{thread_in_stud:g}\", C_D 1.0 unless the report's own clause permits more "
            f"({crossing.source or 'unsourced'})",
            combination="ASCE 7-16 §2.4.1(7) 0.6W"))

    # 3. Head pull-through of the girt — the side member the table assumes.
    states.append(LimitState(
        "head pull-through of the girt", demand_lb, crossing.pull_through_lb, "lb",
        f"published head pull-through at a {crossing.girt_in:g}\" side member "
        f"({crossing.source or 'unsourced'})",
        combination="ASCE 7-16 §2.4.1(7) 0.6W"))

    # 4. NDS 2018 §12.1.4.6 minimum penetration — an input check, not a force.
    required = minimum_penetration_in(crossing.diameter_in)
    states.append(LimitState(
        "minimum thread penetration (6D)", required, thread_in_stud, "in",
        f"AWC NDS 2018 §12.1.4.6, 6 x {crossing.diameter_in:g}\" shank",
        is_detailing=True))
    return thread_in_stud


def _notes(crossing: _Crossing, demand_psf: float, strength_psf: float, demand_lb: float,
           basis, thread_in_stud: float | None, count: int) -> list[str]:
    notes = [
        f"Strength-level suction is {strength_psf:.1f} psf; {demand_psf:.1f} psf is that at "
        f"0.6W (ASCE 7-16 §2.4.1), and {demand_lb:.1f} lb is that over one crossing's "
        f"{crossing.block_spacing_in:g}\" x {crossing.course_spacing_in:g}\" tributary. "
        f"Zone 5 (corner) governs: one screw pattern runs through both zones.",
        f"Wind basis: {basis.describe()}, K_zt {wind.K_ZT_FLAT:g}, K_d "
        f"{wind.K_D_BUILDINGS:g}, K_e taken as 1.0 (ASCE 7-16 §26.9). The panel above this "
        f"screw (wall_panel) is computed from the same q_h and the same coefficients; two "
        f"numbers for one suction would mean one of them was wrong.",
        f"One seal covers {count} wall(s) — one stack, one block module, one course module "
        f"and one screw are one design. Membership is in the fingerprint as "
        f"`crossing_count`, so adding or removing a wall stales the stamp.",
        "THE SCREW IS THE WHOLE LOAD PATH. There is no second fastener and no nail: the "
        "block bears the cladding's gravity in direct compression on the sheathing, so this "
        "is a pure withdrawal element. A reviewer should read the three states as covering "
        "one connection with no redundancy behind it.",
    ]
    if crossing.diameter_in is not None and crossing.stud_specific_gravity is not None:
        nds = nds_withdrawal_per_in(crossing.stud_specific_gravity, crossing.diameter_in)
        notes.append(
            f"CROSS-CHECK, not the grade: NDS 2018 §12.2 W = 2850 G^2 D at G "
            f"{crossing.stud_specific_gravity:g} and D {crossing.diameter_in:g}\" is "
            f"{nds:.1f} lb/in unadjusted, against the report's tested "
            f"{crossing.withdrawal_lb_per_in:g} lb/in. The tested value governs; the code "
            f"equation is printed so a reviewer can see the two are the same order.")
    notes.append(
        "C_D is taken as 1.0 on the report's withdrawal value. NDS Table 2.3.2 would give "
        "1.6 for wind, but that factor belongs to the NDS equation, and applying it to a "
        "tested allowable whose report does not say so would inflate this capacity by 60% "
        "on a reading nobody made. C_M is 1.0: the thread lands in a stud inside a "
        "continuous ccSPF air and water barrier, dry service. 0.7 is the wet-service "
        "alternate if a reviewer disagrees, and it would take the withdrawal capacity to "
        "70% of the value stated above.")
    notes.append(
        f"REVIEWER ITEM: the main-storey studs are LSL, which is outside the screw report's "
        f"scope. They are graded here at the {crossing.stud_material} value the library "
        f"carries (SPF, G 0.42) — conservative against LP's ~0.50 equivalent — for the PE "
        f"to confirm or replace.")
    if thread_in_stud is not None:
        notes.append(
            f"Thread bookkeeping: {crossing.length_in:g}\" overall, {crossing.thread_in:g}\" "
            f"thread. It crosses girt {crossing.girt_in:g}\" + block "
            f"{crossing.block_in:g}\" + sheathing {crossing.sheathing_in:g}\" = "
            f"{crossing.through_in:g}\", leaving {thread_in_stud:g}\" of thread in the stud. "
            f"The sheathing is nailed to the stud, so it counts on the stud's side of the "
            f"joint and NOT as part of the clamped stack — which is why the stack is "
            f"{crossing.clamped_stack_in:g}\" and not {crossing.through_in:g}\".")
    notes.append(
        "ALTERNATE THAT FAILS, recorded because it was the specified screw until "
        "2026-09-12: Simpson SDWS22800DB, 8\" long with a 3\" thread (IAPMO UES ER-192 "
        f"Table 7). Plain shank 5\" against a {crossing.clamped_stack_in:g}\" stack leaves "
        "1\" of thread inside the members it is meant to clamp, so the joint stands open "
        "however good its withdrawal number is. SDWS221000DB fixes the engagement at 10\"; "
        "the owner wanted an 8\" screw.")
    notes.append(
        "NOT CHECKED, and no seal should read this as covering them: the girt itself in "
        "bending between blocks, the block plies in compression and their bearing on the "
        "sheathing, the sheathing-to-stud nailing this screw's thread relies on, and the "
        "cladding panel, which is graded separately as `wall_panel`.")
    return notes
