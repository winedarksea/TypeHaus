"""The items this engine will never compute, declared rather than discovered.

The trussed roofs and their uplift path — ``rafter/RF-*``, which since 2026-09-14 carries
the uplift reactions too — reach ``haus engineering`` only because a check
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
    reason="the roof resolves no rafter member at all (it is trussed, or framed on a ridge "
           "beam), so no span table describes it and the component manufacturer's design "
           "governs. A roof framed in an engineered profile is not here: its maker's "
           "published span table is read directly. RF-BW-CANOPY carries a drift case the "
           "fabricator has to be quoted against; a quote on ground snow alone buys "
           "ordinary trusses (notes/north_entry_piers.md §3)",
    designer="truss or I-joist manufacturer's engineer of record, for the component only. "
             "The truss fabricator's design is the component only; the chain below the heel "
             "is checked against its published reactions once they are entered",
    deliverable="a sealed component design and placement plan for the roof, covering the "
                "profile, the web stiffener and hanger schedule, and the ground-snow and "
                "drift case this site carries, within the criteria the order states: the "
                "loads, the drift on each truss, the bearings, the deflection limits and the "
                "maximum net uplift per heel. Where the roof declares a diaphragm, the first "
                "and last trusses' top chords carry the chord force the lateral calculation "
                "prints, in addition to gravity, with the plated splice in tension. No "
                "splice-slip value is asked for. The supplier's reaction schedule is quoted "
                "onto the roof and checked against the specified reactions",
    unblocks="Roof framing, the S-603 rafter/truss line and the roof-load permit item; the "
             "supplier's reactions close the component line once entered, the supporting "
             "structure being already checked on the specified ones",
    oracle=(Oracle(note="catlin_truss_engineering.md",
                   test="tests/test_wind_loads.py"),
            Oracle(note="canopy_truss_criteria.md",
                   test="tests/test_truss_criteria.py"),
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


# NOTE — there is NO ``column_support`` deferral any more (2026-09-20). The wall-top joint
# under a fixed-base column — bearing, shear friction, dowel tension and development — is
# computed by ``engineering/column_support.py``, which carries this deferral's residue (the
# pilaster question) in its NOT-GRADED note; rotational restraint is ``base_rotation``'s.


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


# --- The sunken garden's silent gaps (2026-09-14) -----------------------------------
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

# ``veneer_beam`` LEFT this list on 2026-09-20: it is a registered calculation now
# (``engineering/veneer_beam.py``), and its deliverable's prose moved into that record's
# NOT-GRADED note. The masonry anchors it used to carry unnamed are their own item below.

_declare(Deferral(
    kind="veneer_anchor",
    reason="the anchored brick stands 6 1/2in back of its backing's studs, past the 4 1/2in the "
           "adopted Minnesota edition's tie table (IRC Table R703.8.4(1), 2018 base) allows and "
           "with no W2.8 row. The 2024 IRC's table carries a W2.8 adjustable-wire row to "
           "6 5/8in, and the ties are detailed to it: every tie on a stud, none into a "
           "concrete end, W2.8 with two pintle legs. The item is a dependency on the code in "
           "force on the permit application date, not a design left undone",
    designer="the owner, as the permit applicant: the application date is the owner's to set",
    deliverable="the permit application filed on or after the date Minnesota's 2024-based "
                "residential code takes effect, when the profile's edition carries the row and "
                "this item retires with no house edit; failing that, a written request to the "
                "building official under IRC R104.11 to accept the 2024 row, made before the "
                "application",
    unblocks="the veneer anchorage detail and the wall section through the wythe",
    oracle=(Oracle(note="sunken_garden_veneer_beam.md", section="§6k, §6l",
                   test="tests/test_veneer_cavity.py"),),
))


@keys("veneer_anchor")
def _veneer_anchor_keys(ctx: EngineeringContext) -> list[str]:
    """Every anchored wythe the adopted IRC table does not cover — the measurement
    ``structural.veneer_cavity_width`` grades, not the beam it stands on."""
    from typehaus.veneer_ties import beyond_table

    return beyond_table(ctx.model, ctx.irc_base)


# NOTE — ``thermal_break_transfer`` is COMPUTED since 2026-09-20, in
# ``engineering/thermal_break.py``, as a reserve. Its deliverable prose is that module's
# NOT-GRADED note; settlement keeps every item INCOMPLETE until a measured modulus exists.

# NOTE — ``tiered_retaining`` is RETIRED (2026-11-23): R404.4 does not engage at <= 48" of fill,
# and the raised-garden legs are read off Allan Block's Table 1.3 by
# ``structural.srw_gravity_chart`` (``engineering/srw_chart``). Nothing is deferred for them.


def _footingless_walls(ctx: EngineeringContext) -> list:
    """Every ``FoundationWall`` with no ``Footing`` naming it — it spans or it is a gravity
    unit, and either way the strip-footing calculations do not apply to it."""
    from typehaus.model.structure import Footing, FoundationWall

    hosted = {f.under for f in ctx.plan.all_elements() if isinstance(f, Footing)}
    return [w for w in ctx.plan.all_elements()
            if isinstance(w, FoundationWall) and w.tag not in hosted]






# --- What `column_base` leaves open (2026-09-18) ------------------------------------------
#
# `engineering/column_base.py` grades the EMBEDMENT a fixed base needs, which was the
# assumption every `deck_post` record named and none graded. Grading it turned three other
# assumptions from "unmentioned" into "mentioned and still ungraded", and an assumption that
# has become visible is exactly the thing that should be on a register rather than in a
# module docstring. None of these is a check FAIL: they are scope, not arithmetic that came
# out wrong, and the plan behind this pass is explicit that a scope gap becomes a named
# deferral and not a red.

# NOTE — there is NO ``base_rotation`` deferral any more (2026-09-20): the base's STIFFNESS
# is computed in ``engineering/base_rotation.py``, which carries this deferral's residue —
# how the moment splits between the buried shaft and the pad — in its NOT-GRADED note.


# NOTE — there is NO ``column_head_joint`` deferral any more (2026-09-20). The head is
# computed by ``engineering/column_head_joint.py``, and what its deliverable still asked of a
# seal — the fastener schedule through the pack, and whether the joint really is the free
# head the analysis assumes — is that module's NOT-GRADED note.
