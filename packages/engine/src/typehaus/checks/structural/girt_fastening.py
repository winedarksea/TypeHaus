"""The girt crossing screw, read off its evaluation report: ``structural.girt_fastening``.

One TimberLOK per crossing is the whole load path of the truss wall's cladding. Its capacities
are PUBLISHED: ICC-ES ESR-1078 Table 2 (withdrawal per inch of embedded thread) and Table 3
(head pull-through at a 1-1/2" side member), and a reviewer opens the report, finds the row and
closes the question. So this is a prescriptive read, the way ``structural.cladding_wind`` reads
the panel's table, and ``girt_screw/*`` left the engineering register on 2026-11-22
(decision 21). The authored numbers are the house's read, on the girt band's
``FramingSpec.standoff_fastener_*``; the demand is computed here.

**The refusals are the substance.** A quoted row is true for the row, so before anything is
graded the authored values are held against ``girt_fastening_table``: the part, its length and
thread (Table 1A); the stud and girt specific gravity the rows are indexed by; the 1.25"
minimum embedded thread; the 1-1/2" minimum side member; the report named. Any mismatch is
UNKNOWN naming it, never a PASS off a stale quotation.

**Demand is ``typehaus.wind``'s, term for term with ``structural.cladding_wind``** (one suction
for the panel and the screw behind it): q_h at the mean roof height above the lowest adjacent
ground, Zone 5 GC_p, GC_pi, 0.6W; times the girt's and the panel's continuity over a simple
span. **ASCE 7-16 §2.4.1 combination 5 (D + 0.6W)** adds the gravity prying: the weight acts
parallel to the sheathing, hung off its face, and tips each block onto its screw.

**Capacities carry the NDS 11.3 factors the report sends its values to** (ESR-1078 §4.1.2):
C_D 1.6 for wind on withdrawal and pull-through, never on the 1,300 lbf Table 1A tension; C_M
0.70 on the girt's pull-through (the KDAT girt wet-cycles, as ``cladding_fastener`` already
reads it), the stud's withdrawal dry. Lateral + withdrawal is NDS 12.4.1 (ESR §4.1.6).
**LSL studs are outside ESR-1078 §3.2 and take no read** (UNKNOWN naming the scope).

**Oracle.** ``houses/catlin/notes/catlin_truss_engineering.md`` §3-§4;
``tests/test_girt_fastening.py`` reproduces it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus import wind
from typehaus.checks._authoring import structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural import girt_fastening_table as table
from typehaus.findings import Finding, Result, not_applicable
from typehaus.model.enums import LayerFunction
from typehaus.resolve.framing.truss_girts import truss_girt_bands

_ID = "structural.girt_fastening"
_CODE = "ICC-ES ESR-1078 (reissued 2026-01), Tables 1A, 2, 3, 4; AWC NDS 2018 11.3, 12.4.1"
#: Engineered wood the report's §3.2 leaves out ("Use of the screws in engineered wood
#: products ... is outside the scope"), by library tag, with no other published route here.
#: LSL has one (ESR-1387 Table 2 + NDS 12.2.2.1, ``girt_fastening_table``), so it is not listed.
_EWP_STUDS = frozenset({"lvl", "psl"})
_LSL = "lsl"
#: The stud module's default when a STRUCTURE layer leaves it unset (``framing/tables``).
_DEFAULT_STUD_SPACING_IN = 16.0


@dataclass(frozen=True)
class _Crossing:
    """One wall's girt-to-stud crossing, measured off the authored assembly."""

    wall_tag: str
    assembly: str
    course_in: float
    block_in: float
    girt_in: float
    block_depth_in: float
    sheathing_in: float
    fastener: str | None
    part: str | None
    diameter_in: float | None
    length_in: float | None
    thread_in: float | None
    withdrawal: float | None
    pull_through: float | None
    source: str | None
    girt_sg: float | None
    stud_sg: float | None
    stud_material: str
    girt_density: float
    panel_in: float

    @property
    def stack_in(self) -> float:
        """Girt + block. The sheathing is nailed to the stud and is not being clamped."""
        return self.girt_in + self.block_depth_in

    @property
    def through_in(self) -> float:
        return self.stack_in + self.sheathing_in


def _block_depth_in(assembly, outer_name: str) -> float:
    """What the block fills: everything between the sheathing and the girt band (derived)."""
    names = [layer.name for layer in assembly.layers]
    sheathing = [i for i, layer in enumerate(assembly.layers)
                 if layer.function is LayerFunction.SHEATHING]
    if not sheathing or outer_name not in names:
        return 0.0
    return sum(float(layer.thickness.inches)
               for layer in assembly.layers[sheathing[-1] + 1:names.index(outer_name)])


def _crossings(ctx: CheckContext) -> list[_Crossing]:
    """Every wall whose outer band is a block-standoff girt, read off the AUTHORED assembly
    (a ``layer_materials`` override swaps a material, never a ``FramingSpec``)."""
    catalog = {material.tag: material for material in ctx.plan.library.materials}
    out: list[_Crossing] = []
    for wall in ctx.model.walls:
        bands = truss_girt_bands(ctx.plan, wall.assembly)
        if bands is None:
            continue
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        outer = bands[1]
        spec = outer.framing
        if assembly is None or spec is None or spec.spacing is None:
            continue
        structure = next((lay for lay in assembly.layers
                          if lay.function is LayerFunction.STRUCTURE), None)
        if structure is None:
            continue
        # The RESOLVED stud: a wall may override the assembly's (the main-storey studs are LSL).
        resolved = next((lay for lay in wall.layers
                         if lay.function == LayerFunction.STRUCTURE.value), None)
        stud_ref = (resolved.material_ref if resolved is not None
                    else structure.material_ref) or ""
        panel = [lay for lay in assembly.layers if lay.function is LayerFunction.CLADDING]
        stud_spacing = getattr(getattr(structure, "framing", None), "spacing", None)
        stud_in = (float(stud_spacing.inches) if stud_spacing is not None
                   else _DEFAULT_STUD_SPACING_IN)
        # One tier puts a block on every OTHER stud; two tiers put one at every stud.
        block_in = stud_in * (1.0 if bands[0] is not None else 2.0)
        out.append(_Crossing(
            wall_tag=wall.tag, assembly=wall.assembly or "",
            course_in=float(spec.spacing.inches), block_in=block_in,
            girt_in=float(outer.thickness.inches),
            block_depth_in=_block_depth_in(assembly, outer.name),
            sheathing_in=sum(float(lay.thickness.inches) for lay in assembly.layers
                             if lay.function is LayerFunction.SHEATHING),
            fastener=spec.standoff_fastener, part=spec.standoff_fastener_part,
            diameter_in=spec.standoff_fastener_diameter_in,
            length_in=spec.standoff_fastener_length_in,
            thread_in=spec.standoff_fastener_thread_in,
            withdrawal=spec.standoff_fastener_withdrawal_lb_per_in,
            pull_through=spec.standoff_fastener_pull_through_lb,
            source=spec.standoff_fastener_source,
            girt_sg=getattr(catalog.get(outer.material_ref or ""), "specific_gravity", None),
            stud_sg=getattr(catalog.get(stud_ref), "specific_gravity", None),
            stud_material=stud_ref,
            girt_density=float(getattr(catalog.get(outer.material_ref or ""), "density",
                                       None) or 0.0),
            panel_in=float(panel[-1].thickness.inches) if panel else 0.0))
    return out


def _groups(ctx: CheckContext) -> dict[str, list[_Crossing]]:
    """One design per geometry-and-screw, keyed by the lowest wall tag (as the old item was)."""
    buckets: dict[tuple, list[_Crossing]] = {}
    for crossing in _crossings(ctx):
        signature = (crossing.course_in, crossing.block_in, crossing.girt_in,
                     crossing.block_depth_in, crossing.sheathing_in, crossing.part,
                     crossing.length_in, crossing.thread_in, crossing.girt_sg,
                     crossing.stud_sg, crossing.stud_material)
        buckets.setdefault(signature, []).append(crossing)
    return {min(c.wall_tag for c in members): sorted(members, key=lambda c: c.wall_tag)
            for members in buckets.values()}


def _missing(crossing: _Crossing) -> list[str]:
    fields = (("standoff_fastener_part", crossing.part),
              ("standoff_fastener_diameter_in", crossing.diameter_in),
              ("standoff_fastener_length_in", crossing.length_in),
              ("standoff_fastener_thread_in", crossing.thread_in),
              ("standoff_fastener_withdrawal_lb_per_in", crossing.withdrawal),
              ("standoff_fastener_pull_through_lb", crossing.pull_through),
              ("standoff_fastener_source", crossing.source))
    return [name for name, value in fields if value is None]


def _drift(crossing: _Crossing, thread_in_stud: float) -> str | None:
    """What stops the authored read describing this crossing, or ``None``."""
    assert crossing.part and crossing.length_in is not None and crossing.thread_in is not None
    assert crossing.withdrawal is not None and crossing.pull_through is not None
    if "ESR-1078" not in (crossing.source or ""):
        return "the authored source does not name ICC-ES ESR-1078, the report these rows are"
    dims = table.TIMBERLOK_1A.get(crossing.part)
    if dims is None:
        return (f"{crossing.part!r} is not a TimberLOK in ESR-1078 Table 1A "
                f"({', '.join(table.TIMBERLOK_1A)}), whose Tables 2 and 3 are these rows")
    if (abs(dims[0] - crossing.length_in) > 0.01 or abs(dims[1] - crossing.thread_in) > 0.01
            or abs(crossing.diameter_in - table.SHANK_DIAMETER_IN) > 0.0005):
        return (f"Table 1A has {crossing.part} at {dims[0]:g}\" overall, {dims[1]:g}\" thread, "
                f"{table.SHANK_DIAMETER_IN:g}\" shank; authored {crossing.length_in:g}\", "
                f"{crossing.thread_in:g}\", {crossing.diameter_in:g}\"")
    if crossing.stud_material in _EWP_STUDS:
        return (f"the studs are {crossing.stud_material}, an engineered wood product, and "
                f"ESR-1078 §3.2 puts engineered wood outside the report's scope")
    if crossing.stud_sg is None or crossing.girt_sg is None:
        return "the stud or girt Material declares no specific_gravity to index the rows by"
    w_row = table.row_at(table.WITHDRAWAL_LB_PER_IN, crossing.stud_sg)
    p_row = table.row_at(table.PULL_THROUGH_LB, crossing.girt_sg)
    if w_row is None or p_row is None:
        return (f"stud SG {crossing.stud_sg:g} or girt SG {crossing.girt_sg:g} is below "
                f"Table 2/3's lowest row (0.42)")
    if crossing.stud_material == _LSL:
        pass  # withdrawal is NDS 12.2.2.1 at ESR-1387's G, not an ESR-1078 row
    elif crossing.withdrawal > w_row + 1e-6:
        return (f"authored withdrawal {crossing.withdrawal:g} lb/in exceeds Table 2's "
                f"{w_row:g} at the stud's SG {crossing.stud_sg:g}")
    if crossing.pull_through > p_row + 1e-6:
        return (f"authored pull-through {crossing.pull_through:g} lb exceeds Table 3's "
                f"{p_row:g} at the girt's SG {crossing.girt_sg:g}")
    if thread_in_stud + 1e-6 < table.MIN_EMBEDDED_THREAD_IN:
        return (f"Table 2 is for at least {table.MIN_EMBEDDED_THREAD_IN:g}\" of embedded "
                f"thread and the stud gets {thread_in_stud:g}\"")
    if crossing.girt_in + 1e-6 < table.MIN_SIDE_MEMBER_IN:
        return (f"Table 3 is for a {table.MIN_SIDE_MEMBER_IN:g}\" side member and the girt "
                f"is {crossing.girt_in:g}\"")
    return None


def _demand(ctx: CheckContext, crossing: _Crossing) -> tuple[float, float, float] | str:
    """(q_h, ASD suction psf, ASD lb per crossing), or the sentence naming what is missing."""
    basis = wind.wind_basis(ctx.plan.project.site)
    height = wind.mean_roof_height_ft(ctx.model)
    if basis is None:
        return ("the site declares no complete design wind basis (design_wind_speed_mph, "
                "wind_exposure, risk_category)")
    if not height:
        return "no resolved roof gives a mean roof height for q_h"
    q_h = wind.velocity_pressure_psf(basis, height)
    area = wind.effective_wind_area_ft2(crossing.course_in)
    _, asd = wind.cladding_pressure_asd_psf(q_h, area, "5", sign="negative")
    return q_h, asd, table.crossing_demand_lb(asd, crossing.block_in, crossing.course_in)


@check(Tier.STRUCTURAL, _ID)
def girt_fastening(ctx: CheckContext) -> list[Finding]:
    groups = _groups(ctx)
    if not groups:
        if not ctx.model.walls:
            return []
        return [not_applicable(
            _ID, "no wall stands on a block-standoff girt band, the only assembly whose "
                 "crossing screw this rule reads a published row for", (), code=_CODE)]
    return [_one(ctx, key, members) for key, members in sorted(groups.items())]


def _one(ctx: CheckContext, key: str, members: list[_Crossing]) -> Finding:
    crossing, tags = members[0], tuple(m.wall_tag for m in members)
    more = f" and {len(members) - 1} more wall(s)" if len(members) > 1 else ""
    subject = (f"{key}{more}: one {crossing.fastener or 'unauthored screw'} per "
               f"{crossing.block_in:g}\" x {crossing.course_in:g}\" crossing")
    absent = _missing(crossing)
    if absent:
        return structural_advisory(
            _ID, f"{subject} cannot be read without FramingSpec.{', '.join(absent)} on the "
                 f"girt band; nothing here defaults a report value", tags, Result.UNKNOWN,
            code=_CODE)
    demand = _demand(ctx, crossing)
    if isinstance(demand, str):
        return structural_advisory(_ID, f"{subject}: the wind demand cannot be computed — "
                                        f"{demand}", tags, Result.UNKNOWN, code=_CODE)
    q_h, suction, load = demand
    assert crossing.length_in is not None and crossing.thread_in is not None
    assert crossing.withdrawal is not None and crossing.pull_through is not None
    embedded = table.thread_in_main_member(crossing.length_in, crossing.thread_in,
                                           crossing.through_in)
    shank = table.plain_shank_in(crossing.length_in, crossing.thread_in)
    jacked = table.thread_in_side_member(crossing.length_in, crossing.thread_in,
                                         crossing.stack_in)
    # A fact about the building, whatever the report rows say: graded before they are.
    if crossing.stack_in > shank + 1e-6:
        return structural_advisory(
            _ID, f"{subject}: a lag-type screw clamps only on plain shank. "
                 f"{crossing.length_in:g}\" less {crossing.thread_in:g}\" thread leaves "
                 f"{shank:g}\" against a {crossing.stack_in:g}\" clamped stack, so {jacked:g}\" "
                 f"of thread stands inside it and jacks the girt off the block", tags,
            Result.FAIL, code=_CODE, fix_hint="a screw with a shorter thread or a longer "
                                              "plain shank")
    drift = _drift(crossing, embedded)
    if drift is not None:
        return structural_advisory(
            _ID, f"{subject}: the authored ESR-1078 read no longer describes this wall — "
                 f"{drift}", tags, Result.UNKNOWN,
            fix_hint="re-read ESR-1078 Tables 1A, 2 and 3 at the model's own screw, stud and "
                     "girt, and re-author the standoff_fastener_* values")

    # Capacities, NDS 11.3 applied: C_D 1.6 for wind on wood-controlled states (never the
    # screw's own tension), C_M 0.70 on the wet-cycling girt's pull-through, stud dry.
    lsl = crossing.stud_material == _LSL
    w_unit = (table.nds_wood_screw_withdrawal_per_in(table.LSL_WITHDRAWAL_EDGE_SG,
                                                     crossing.diameter_in)
              if lsl else crossing.withdrawal)
    w_ref = w_unit * embedded
    withdrawal = w_ref * table.C_D_WIND
    pull = crossing.pull_through * table.WET_SERVICE_FACTOR * table.C_D_WIND
    # LSL is outside Tables 2-4 as well: its lateral column is held at the 0.42 floor.
    lateral_row = table.row_at(table.LATERAL_LB, min(crossing.stud_sg or 0.0,
                                                     crossing.girt_sg or 0.0,
                                                     table.LSL_WITHDRAWAL_EDGE_SG if lsl
                                                     else 1.0))
    # Gravity: parallel to the sheathing, hung off its face, so it shears the joint and pries
    # each block onto its screw (note §3.5a). Combination 5 adds it to 0.6W; dead alone is D.
    weight, moment, pry = table.prying(
        crossing.block_in, crossing.course_in, crossing.girt_in, crossing.block_depth_in,
        max(m.panel_in for m in members), crossing.girt_density)
    tension = load + pry
    ratios = {"withdrawal": tension / withdrawal, "head pull-through": tension / pull,
              "screw tension": tension / table.TENSILE_LB}
    dead = {"dead alone, withdrawal": pry / (w_ref * table.C_D_DEAD),
            "dead alone, pull-through": pry / (crossing.pull_through
                                               * table.WET_SERVICE_FACTOR * table.C_D_DEAD)}
    if lateral_row is None:
        return structural_advisory(
            _ID, f"{subject}: the stud's and girt's SG is below Table 4's lowest row (0.42)",
            tags, Result.UNKNOWN, code=_CODE)
    lateral = min(lateral_row) * table.C_D_WIND * table.WET_SERVICE_FACTOR
    alpha = math.atan2(tension, weight)
    resultant = math.hypot(tension, weight)
    z_alpha = table.combined_allowable_lb(withdrawal, lateral, alpha)
    ratios["combined lateral + withdrawal"] = resultant / z_alpha
    ratios.update(dead)
    governing = max(ratios, key=ratios.__getitem__)
    over = ratios[governing] > 1.0 + 1e-9
    withdrawal_basis = (
        f"NDS 12.2.2.1 W = 2850 G^2 D at ESR-1387 Table 2's TimberStrand LSL equivalent SG "
        f"{table.LSL_WITHDRAWAL_EDGE_SG:g} (installed in edge; ESR-1078 §3.2 leaves LSL out, "
        f"so no Table 2 row)," if lsl else
        f"Table 2 withdrawal at SG {crossing.stud_sg:g},")
    lsl_note = (
        "the LSL stud's withdrawal applies the NDS wood-screw equation, written for ASME "
        "B18.6.1 screws, to this proprietary rolled-thread screw (it gives 95 lb/in against "
        "ESR-1078 Table 2's tested 170 at the same SG, so it is the lower bound), and "
        "the screw enters the stud's narrow edge; " if lsl else "")
    text = (
        f"{subject}: D + 0.6W, ASCE 7-16 §2.4.1(5), {tension:.1f} lb of screw tension = "
        f"{load:.1f} lb suction ({suction:.2f} psf Zone 5 at q_h {q_h:.2f} psf x "
        f"{table.tributary_area_ft2(crossing.block_in, crossing.course_in):.2f} sf x girt "
        f"{table.GIRT_CONTINUITY:g} x panel {table.PANEL_CONTINUITY:.3f}) + {pry:.1f} lb prying "
        f"({weight:.1f} lb of cladding, girt and block hung off the sheathing, "
        f"{moment:.1f} in-lb over {table.BLOCK_FACE_IN / 2.0:g}\"), with {weight:.1f} lb "
        f"of shear. {withdrawal_basis} {w_unit:.1f} lb/in "
        f"x {embedded:g}\" embedded x C_D {table.C_D_WIND:g} = {withdrawal:.0f} lb (d/c "
        f"{ratios['withdrawal']:.3f}); Table 3 pull-through {crossing.pull_through:g} lb at a "
        f"{crossing.girt_in:g}\" side member, SG {crossing.girt_sg:g}, x C_M "
        f"{table.WET_SERVICE_FACTOR:g} x C_D {table.C_D_WIND:g} = {pull:.0f} lb (d/c "
        f"{ratios['head pull-through']:.3f}); Table 1A tension {table.TENSILE_LB:g} lb, no "
        f"factor (d/c {ratios['screw tension']:.3f}); NDS 12.4.1 combined, Table 4 "
        f"Z {min(lateral_row):g} x C_D x C_M = {lateral:.0f} lb, Z'a {z_alpha:.0f} lb at "
        f"{math.degrees(alpha):.1f} deg (d/c {ratios['combined lateral + withdrawal']:.3f}); "
        f"dead alone at C_D {table.C_D_DEAD:g} d/c {max(dead.values()):.3f}. Plain shank "
        f"{shank:g}\" spans the {crossing.stack_in:g}\" stack. Governing: {governing}")
    if over:
        return structural_advisory(
            _ID, f"{text}, past its published row ({crossing.source})", tags, Result.FAIL,
            code=_CODE, fix_hint="a tighter girt course or block module, or a heavier row")
    return structural_advisory(
        _ID, f"{text} — a prescriptive read of a published report. Conditions the engine does "
             f"not check: {lsl_note}the stud stays dry behind the foam, the girt wet-cycles (the "
             f"0.70 is applied to it); the lateral value is Table 4's 2-1/2\" row read for a "
             f"thicker side member as its footnote 2 permits; ACQ-D girt stock at retention "
             f"<= 0.40 pcf, exposure conditions 1 and 3 of Table 6 (§4.1.7); installed "
             f"perpendicular, head flush, no lead hole ({crossing.source})",
        tags, Result.PASS, code=_CODE)
