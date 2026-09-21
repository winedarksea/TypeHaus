"""The items this engine will never compute, declared rather than discovered.

The trussed roofs and their uplift path — ``rafter/RF-*``, which since 2026-09-14 carries
the uplift reactions too — plus the two ``column_support`` wall tops, reach
``haus engineering`` only because a check
names an ``engineering_item`` of a kind nobody registered, and
``EngineeringResults.__getitem__`` synthesises a bare ``NO_CALC`` for it. They exist by
accident, and their record says only "no calculation is registered for this kind", which is
true and useless: it does not say
*who* designs the thing, *what* they have to hand over, or *which* line of the permit set
stays shut until they do.

That is what a :class:`Deferral` carries. It is not a weaker calculation — the item is
exactly as blocking as it was, and the engine still computes nothing — it is the difference
between an absence and an assignment. ``03-open-items.md`` in the calc package is generated
straight off this table, so an outstanding design is named on a register instead of being
discoverable only by scrolling a terminal.

Registering a kind here also makes it a *registered kind*, which is what puts it in front of
the Phase-1d oracle lint: a deferred item must still say which note reasons about it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typehaus.engineering.item import EngineeringRecord, Oracle, no_calc
from typehaus.engineering.registry import EngineeringContext, keys, oracled_by


@dataclass(frozen=True)
class Deferral:
    """One kind of work this engine hands to somebody else, and to whom.

    ``designer`` is a role and not a person on purpose — "the truss fabricator" survives a
    change of fabricator, and the engine has no business holding a name it cannot verify.
    """

    kind: str
    #: Why this engine computes nothing — the honest sentence, printed as the summary.
    reason: str
    #: Who owns the design of record.
    designer: str
    #: What that designer has to produce before the item can close.
    deliverable: str
    #: The permit-set line the deliverable unblocks.
    unblocks: str
    oracle: tuple[Oracle, ...] = field(default_factory=tuple)

    def record(self, key: str) -> EngineeringRecord:
        return no_calc(self.kind, key, reason=self.reason, oracle=self.oracle)


DEFERRALS: dict[str, Deferral] = {}


def _declare(deferral: Deferral) -> Deferral:
    """Record the deferral, and put its kind in front of the same oracle lint every
    computed kind faces — an item nobody computes still has to say which note reasons
    about it."""
    DEFERRALS[deferral.kind] = deferral
    oracled_by(deferral.kind, *deferral.oracle)
    return deferral


_declare(Deferral(
    kind="rafter",
    reason="the roof resolves no rafter member at all — it is trussed, or framed on a "
           "ridge beam — so there is no member for any span table to describe and the "
           "component manufacturer's sealed design governs. A roof framed in an ENGINEERED "
           "PROFILE is not here: its maker publishes a span table, reading one is a "
           "prescriptive act, and `structural.rafter_span` grades it against an authored "
           "`Roof.published_span` instead (2026-09-11). RF-BW-CANOPY carries a DRIFT "
           "case the fabricator has to be quoted against — a quote priced on \"50 psf "
           "ground snow\" buys ordinary trusses (notes/north_entry_piers.md §3, and "
           "preferences.toml [structural] roof_beam_snow_psf)",
    designer="truss or I-joist manufacturer's engineer of record — the component design "
             "only. The chain below the heel is no longer a second role here: the fabricator "
             "PUBLISHES its reactions, and `structural.truss_reactions` grades that chain "
             "against published connector allowables once they are quoted into the model "
             "(`Roof.published_reactions`, 2026-09-20)",
    deliverable="a sealed component design and placement plan for the roof, covering the "
                "profile, the web stiffener and hanger schedule, and the ground-snow AND "
                "drift case this site carries. Its bearing and uplift reaction schedule is "
                "the intake half: quote each row into `Roof.published_reactions` and the "
                "chain below the heel is graded as a published read, not sealed here",
    unblocks="Roof framing — the S-105 rafter/truss line and the roof-load permit item; "
             "the uplift line (structural.uplift_capacity, structural.truss_reactions) "
             "closes on the quoted reactions",
    oracle=(Oracle(note="catlin_truss_engineering.md",
                   test="tests/test_wind_loads.py"),
            Oracle(note="uplift_load_path.md",
                   test="tests/test_uplift_load_path.py")),
))

# NOTE — there is NO ``lateral_uplift`` deferral any more, and its absence is deliberate
# (2026-09-14). It carried one item per roof, three of them, all UNKNOWN and all waiting on
# a seal, on the reasoning that this engine derives no wind demand for a joint. It does not,
# and it does not have to: the two halves of that question both turned out to be documents.
#
#  - **A rafter-framed roof reads IRC Table R802.11.** The required resistance per
#    connection is published — adopted law, indexed by exposure, spacing, span, speed and
#    pitch — and the connector's allowable is published by its maker. Two table reads
#    compared is a prescriptive act, so ``structural.uplift_capacity`` grades an authored
#    ``Roof.published_uplift`` and mints nothing. ``typehaus/wind_tables.py`` holds the grid.
#  - **A trussed roof folds into ``rafter/<tag>``**, immediately below. No R802.11 row
#    describes a roof that resolves no truss member, and the fabricator who seals the
#    component design is the same person who publishes its uplift reactions. Two items
#    naming one designer and one document was the redundancy, not the deferral.
#
# ``uplift_load_path.md`` stays an oracle, on the ``rafter`` deferral where the work now is.

# NOTE — there is NO ``header`` deferral, and its absence is deliberate (2026-09-11).
# A wide opening's header was deferred here on the reasoning that the IRC table stops at 8'.
# It does, but the beam supplier's own header table does not: reading a published row is a
# prescriptive act and nothing a seal adds to. ``structural.header_prescriptive`` now grades
# against an authored ``Door.published_span``, and a house that authors neither the beam nor
# the row gets UNKNOWN with the hint rather than a deferral naming a designer nobody needs.
# The ``ridge_beam_detail.md`` oracle went with it: it was never about a header.

# NOTE — there is NO ``masonry_slot`` deferral, and its absence is deliberate (2026-09-19).
# A slot cut out of a masonry wythe to let a joist through earned one while it was an
# INVISIBLE NOTCH: nothing in the model showed it, so an item naming a designer was the only
# way the question reached anybody. Catlin's fireplace stub is three piers now with the joist
# pockets authored as real gaps between them, so the geometry IS the statement — the spans,
# the clearances and the bearing are all in the model and all graded
# (``structural.through_deck_clearance``). The plinth course bridging each 4" pocket is
# 9 psi on ~40 psi allowable flexural tension normal to bed joints and arches before it bends;
# that is not a question for a seal. Widen a pocket past ~4 1/2", though, and TMS 402's
# pier/column line (3t = 10 7/8" on a 3 5/8" wythe) starts to bite — which is a reason to
# re-derive the deferral deliberately, not to re-derive it by accident.


_declare(Deferral(
    kind="column_support",
    reason="a fixed-base cast column stands on this wall's top and the concrete underneath "
           "it is graded by nobody. ``deck_post`` computes the column's service axial and "
           "its base moment ON THE COLUMN; the wall is a basement wall answered "
           "prescriptively by IRC Table R404.1.2(8), which publishes no surcharge column "
           "at all, and its strip footing collects no engineered bearing record because "
           "``spread_footing`` scopes off a shared wall footing on the argument that a "
           "``retaining_wall`` record already answers for it — which for a "
           "top-and-bottom-supported wall does not exist. Three things follow and this "
           "engine computes none of them: the wall-top JOINT's own capacity, DEVELOPMENT "
           "of the column dowels into the wall top, and the foundation's ROTATIONAL "
           "RESTRAINT, which every one of those base moments assumes",
    designer="structural engineer of record",
    deliverable="a wall-top connection detail carrying the column's axial and base moment "
                "— dowel size, embedment and development into the stem, any pilaster or "
                "local thickening, and the bearing pressure under the point — plus a "
                "statement of the rotational restraint the fixed-base assumption relies on",
    unblocks="Foundations — the S-100 wall schedule and the column base detail",
    oracle=(Oracle(note="balcony_moment_columns.md", section="§9",
                   test="tests/test_pier_calcs.py"),),
))


@keys("column_support")
def _column_support_keys(ctx: EngineeringContext) -> list[str]:
    """Every wall with a cast, fixed-base column standing on its top.

    Read off ``pier_basis.cast_piers``' own ``shared_wall_footing`` flag rather than
    re-walked, because that flag IS the condition: it is set exactly when a concrete post
    inherits a concrete wall's strip footing as its base, which is the load path this
    deferral is about. Scoped to a column with a base moment — a leaning column hands its
    wall a vertical load and nothing else, and an ordinary bearing needs no assignment.
    """
    from typehaus.engineering.pier_basis import cast_piers

    out = set()
    for pier in cast_piers(ctx):
        if not pier.shared_wall_footing or not pier.lateral_system:
            continue
        support = getattr(ctx.plan.by_tag(pier.tag), "supported_by", None)
        if support:
            out.add(support)
    return sorted(out)


@keys("rafter")
def _rafter_keys(ctx: EngineeringContext) -> list[str]:
    """Roofs that resolve no rafter member — the trussed case, and the only one left here.

    A roof framed in a profile the sawn-lumber table does not publish (catlin's RF-HOUSE, on
    11-7/8" I-joists at 24") used to raise a ``rafter/<tag>`` item too. It no longer does:
    the joist maker publishes a horizontal clear span for it, and
    ``structural.rafter_span`` reads that row rather than delegating the roof.
    """
    return sorted(roof.tag for roof in ctx.model.roofs
                  if not any(member.category == "rafter" for member in roof.members))


# --- The sunken garden's three silent gaps (2026-09-14) -----------------------------------
#
# All three were found by an outside review of the court. What they had in common is the
# thing a deferral fixes: each is a real piece of engineering that this engine computes
# nothing for, and each was invisible — not UNKNOWN, not INCOMPLETE, simply absent from
# ``haus engineering`` and from ``out/calcs/03-open-items.md``. An absence reads exactly like
# a thing with no problem.
#
# **Two cautions, recorded because the obvious fixes are worse.** ``_retaining_walls`` is NOT
# widened to reach the apron: minting isolated-cantilever records for walls whose whole
# problem is that they are *not* isolated makes the register less true, not more. And
# ``foundation.py``'s ``fill_ft < 4.0`` PASS on the apron is left exactly as it is: the check
# says honestly that IRC R404.1.1 does not engage at 3'-4", which is correct. The defect was
# never that check's verdict — it was that nothing else then looked.

_declare(Deferral(
    kind="veneer_beam",
    reason="a cast concrete beam spans between two walls and carries a masonry wythe, and "
           "no registered calculation grades it. `engineering/sunken_garden/veneer_beam.py` "
           "screens flexure, shear, deflection and torsion — at 1.4D on the real mix since "
           "2026-09-14 — but it is a free function that writes a REPORT: it reads no plan, "
           "mints no record, and nothing can be sealed against it. Four things follow and "
           "this engine computes none of them. (1) The END RESTRAINT: the beam is cast "
           "monolithic with the side walls (AN-SG-PLACEMENTS, placement 2), and the "
           "reinforcement continuity through that corner — the top and bottom bars' lap "
           "into the walls' vertical steel — is nobody's number here. (2) TORSION "
           "DETAILING: the wythe is deliberately off-centre, and the factored twist is "
           "below cracking but 1.7x ACI 318-19 §22.7.4.1's threshold, so §9.6.4's closed "
           "hoops and longitudinal steel are owed — the screening says so, no record "
           "carries it. (3) The MASONRY ANCHORS over a ~10in insulated standoff, which no "
           "prescriptive table contemplates and this engine has no calculation for at all. "
           "(4) The SOFT JOINT at each end of the wythe, which the model does not carry",
    designer="structural engineer of record, with the mason's anchor supplier for the "
             "standoff — two roles because the anchor is a product selection against a "
             "published thickness and the beam is not",
    deliverable="a sealed beam design at the as-built section carrying the wythe at 1.4D — "
                "flexural and torsional reinforcement, the lap into each side wall, and the "
                "stirrup form — plus a TMS 402 anchor design for the full insulated "
                "standoff and a movement-joint detail at each end of the wythe",
    unblocks="Foundations — the S-100 beam schedule and the veneer anchorage detail",
    oracle=(Oracle(note="sunken_garden_veneer_beam.md",
                   test="tests/test_sunken_garden_study.py"),),
))

_declare(Deferral(
    kind="thermal_break_transfer",
    reason="a row of bars ties two separate pours across a deliberate insulating break, and "
           "the force in them is authored rather than computed. This engine derives NO "
           "demand for the joint: not the differential settlement between a heated house "
           "footing and a freestanding court wall standing in an open excavation, not the "
           "thermal movement the break exists to permit, not the shear the two pours "
           "exchange. The bar count is set by the board's width and a spacing rule, which "
           "is a detailing rule and not a limit state, and the GFRP bars' own stiffness and "
           "development are manufacturer data the model does not hold. NOTHING GRADES A "
           "THERMAL BREAK FOR CONTINUITY EITHER, so the board's own integrity — it is a "
           "Layer against the fresh head of a pour, held against floating and racking by "
           "nothing — is equally uncomputed",
    designer="structural engineer of record, with the GFRP manufacturer's published bond "
             "and modulus data",
    deliverable="a stated design shear and differential movement across each break, the bar "
                "size, count and embedment that carry them, and the bracing that holds the "
                "board in position during the pour",
    unblocks="Foundations — the thermal-break detail on S-100 and the pour-sequence hold "
             "point it depends on",
    oracle=(Oracle(note="sunken_garden_court_free_body.md", section="§9",
                   test="tests/test_retaining_court.py"),),
))

# NOTE — ``tiered_retaining`` is COMPUTED since 2026-09-20: ``engineering/segmental_wall.py``
# grades the unit's own free body, and its NOT-GRADED note carries this deferral's deliverable
# (global stability of the pair with the geotechnical engineer; the unit, reinforcement and
# levelling pad with the SRW supplier's engineer).


def _footingless_walls(ctx: EngineeringContext) -> list:
    """Every ``FoundationWall`` with no ``Footing`` naming it — it spans or it is a gravity
    unit, and either way the strip-footing calculations do not apply to it."""
    from typehaus.model.structure import Footing, FoundationWall

    hosted = {f.under for f in ctx.plan.all_elements() if isinstance(f, Footing)}
    return [w for w in ctx.plan.all_elements()
            if isinstance(w, FoundationWall) and w.tag not in hosted]


@keys("veneer_beam")
def _veneer_beam_keys(ctx: EngineeringContext) -> list[str]:
    """Footingless walls that something else bears its whole weight on.

    The relation, not a tag or an assembly name: a wall with no footing whose TOP is another
    footingless wall's BOTTOM, where that other wall declares no lateral support of its own.
    That is a veneer wythe standing on a beam — the wythe has nowhere else to go, and the
    beam is the only thing under it.

    Plan overlap is required as well as the elevation match, so two unrelated members that
    happen to share a level are not read as bearing on each other. It is a screening
    predicate and it is stated as one: a beam carrying something other than a wall — a slab
    edge, a stair — is not found here, and a house that builds one should widen this rather
    than assume the silence means no.
    """
    supports: set[str] = set()
    walls = _footingless_walls(ctx)
    axes = {w.tag: _plan_extent(ctx, w.tag) for w in walls}
    for beam in walls:
        if beam.top_elevation is None:
            continue
        for carried in walls:
            if carried.tag == beam.tag or carried.bottom_elevation is None:
                continue
            if getattr(carried, "lateral_support", None) is not None:
                continue
            if abs(carried.bottom_elevation.meters - beam.top_elevation.meters) > 1e-6:
                continue
            if _extents_overlap(axes.get(beam.tag), axes.get(carried.tag)):
                supports.add(beam.tag)
    return sorted(supports)


@keys("thermal_break_transfer")
def _thermal_break_keys(ctx: EngineeringContext) -> list[str]:
    """Every ``Dowel`` carrying a foam block — a structural tie across a deliberate break.

    ``foam_thickness`` is the whole test and it is the right one: a dowel with no block is an
    ordinary pour-joint tie between two pieces of the same structure, which needs no
    assignment. A dowel with one is holding two structures together *through* an insulator
    that was put there to keep them apart, and the force in it is a design question.
    """
    from typehaus.model.structure import Dowel

    return sorted(d.tag for d in ctx.plan.all_elements()
                  if isinstance(d, Dowel) and d.foam_thickness is not None)


def _plan_extent(ctx: EngineeringContext, tag: str):
    """``(x0, y0, x1, y1)`` bounding box of a resolved wall's axis, metres, or ``None``."""
    wall = next((w for w in ctx.model.walls if w.tag == tag), None)
    if wall is None:
        return None
    (ax, ay), (bx, by) = wall.axis
    return min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)


#: How far apart two axis boxes may sit and still be read as one bearing on the other,
#: metres. 1 ft — a wall bearing on a beam is within its own thickness of it, and anything
#: further apart is two members that share an elevation and nothing else.
_BEARING_PLAN_TOLERANCE_M = 0.3048


def _extents_overlap(first, second) -> bool:
    if first is None or second is None:
        return False
    tol = _BEARING_PLAN_TOLERANCE_M
    return (first[0] - tol <= second[2] and second[0] - tol <= first[2]
            and first[1] - tol <= second[3] and second[1] - tol <= first[3])


# --- What `column_base` leaves open (2026-09-18) ------------------------------------------
#
# `engineering/column_base.py` grades the EMBEDMENT a fixed base needs, which was the
# assumption every `deck_post` record named and none graded. Grading it turned three other
# assumptions from "unmentioned" into "mentioned and still ungraded", and an assumption that
# has become visible is exactly the thing that should be on a register rather than in a
# module docstring. None of these is a check FAIL: they are scope, not arithmetic that came
# out wrong, and the plan behind this pass is explicit that a scope gap becomes a named
# deferral and not a red.

_declare(Deferral(
    kind="base_rotation",
    reason="the fixed base of a cast column is graded for STRENGTH — can the ground turn "
           "its shear around (IBC 1807.3.2.1, `engineering/column_base.py`) — and not for "
           "STIFFNESS. `deck_post`'s sway magnifier assumes a base that does not rotate at "
           "all, and a real one does; the magnifier it computes is therefore a lower bound "
           "on a column whose slenderness is already past ACI 318-19 §6.2.5's sway limit. "
           "How the moment SPLITS between the buried shaft and the pad under it is the "
           "same question from the other side, and this engine computes neither: they are "
           "alternative load paths, not additive ones, and dividing them is a "
           "soil-structure interaction problem",
    designer="structural engineer of record, on a geotechnical report",
    deliverable="a rotational spring for each fixed column base — the moment-rotation "
                "relationship the shaft and its pad deliver together — and the sway "
                "amplification that follows from it, or a statement that the base may be "
                "taken as rigid and on what basis",
    unblocks="S-100's column base detail and the canopy frame's drift check",
    oracle=(Oracle(note="entry_column_base_fixity.md", section="§5",
                   test="tests/test_column_base_calcs.py"),),
))


@keys("base_rotation")
def _base_rotation_keys(ctx: EngineeringContext) -> list[str]:
    """Every column `column_base` grades the strength of — the same set, the other question.

    Keyed off that module's own scope rather than re-walked: one set, one definition, and a
    column that leaves the strength check would otherwise keep a stiffness deferral nobody
    would notice was orphaned.
    """
    from typehaus.engineering.column_base import enumerate_column_bases

    return enumerate_column_bases(ctx)


_declare(Deferral(
    kind="column_head_joint",
    reason="what a fixed-base column is fixed AGAINST at its head is a joint this engine "
           "does not grade. catlin's canopy columns carry `BM-BW-RE` on an `SS316-SHIM-35` "
           "stainless standoff pack under an `HGAM10` gusset angle, isolated with EPDM — a "
           "detail chosen for durability and drainage, and one whose MOMENT transfer "
           "nobody has computed. `column_base` and `deck_post` between them assume the "
           "header reaction arrives and the moment stays in the column; whether a shim "
           "stack and a gusset angle deliver that, or whether the joint is closer to a pin "
           "than the analysis assumes, is a connection design. Column SHEAR and TORSION go "
           "with it: the section is large relative to a few hundred pounds, but 'large' is "
           "a judgement and not a calculation",
    designer="structural engineer of record",
    deliverable="a sealed connection detail at each cast column head — the fastener "
                "schedule through the standoff pack, the moment and shear it transfers, "
                "and the torsion the eccentric seat delivers to the column",
    unblocks="S-400's column head detail and the canopy frame's lateral analysis",
    oracle=(Oracle(note="north_entry_piers.md", section="§8d",
                   test="tests/test_pier_calcs.py"),),
))


@keys("column_head_joint")
def _column_head_keys(ctx: EngineeringContext) -> list[str]:
    """Every cast column that IS a lateral system — the head of each one `deck_post` grades
    in bending, whether it stands on a pad, a footing or a wall."""
    from typehaus.engineering.pier_basis import cast_piers

    return sorted(pier.tag for pier in cast_piers(ctx) if pier.lateral_system)
