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
                "drift case this site carries. **Where the roof declares a diaphragm, the "
                "end trusses' TOP CHORDS are its chords** and carry the axial force "
                "`lateral_system/<roof>` prints as `chord_force_*` IN ADDITION TO the "
                "gravity case — combined axial and bending at that section is the "
                "fabricator's own chart, and the plated splice has to carry the full force "
                "in tension. The splice SLIP the engine assumed "
                "(`DiaphragmSpec.chord_splice_slip`) is the third term of SDPWS 4.2.2 and "
                "decides the rigid/flexible call, so a detail that slips materially more "
                "moves the shear split: confirm it or state the real value. Its bearing and "
                "uplift reaction schedule is "
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
    reason="a masonry wythe stands on a beam that fixes its foot well off the backing wall's "
           "structural face — catlin's W-B-BRICK reaches ~10in brick-to-stud through 6in of "
           "foam and 4in of cavity — and no prescriptive anchor table contemplates that "
           "standoff. TMS 402's engineered path governs: eccentric compression and buckling "
           "of the anchor over its unbraced length, and the wythe's out-of-plane bending "
           "between anchor rows. This engine has no masonry-anchor calculation, and the "
           "anchor is a product selection against a published insulation thickness",
    designer="the masonry anchor supplier's engineer for the product and its published "
             "standoff rating, with the structural engineer of record for the wind demand "
             "and the anchor layout",
    deliverable="a TMS 402 anchor design for the full insulated standoff — anchor type, "
                "spacing both ways, embedment into the backing, and the wythe's out-of-plane "
                "check between rows — plus the supplier's written confirmation that the "
                "product is rated for the insulation thickness it passes through",
    unblocks="the veneer anchorage detail and the wall section through the wythe",
    oracle=(Oracle(note="sunken_garden_veneer_beam.md", section="§5",
                   test="tests/test_veneer_beam_calc.py"),),
))


@keys("veneer_anchor")
def _veneer_anchor_keys(ctx: EngineeringContext) -> list[str]:
    """Every wythe a veneer beam carries — the same relation ``veneer_beam`` keys off."""
    from typehaus.engineering.veneer_beam import carried_wythes

    return carried_wythes(ctx)


# NOTE — ``thermal_break_transfer`` is COMPUTED since 2026-09-20, in
# ``engineering/thermal_break.py``, as a reserve. Its deliverable prose is that module's
# NOT-GRADED note; settlement keeps every item INCOMPLETE until a measured modulus exists.

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
