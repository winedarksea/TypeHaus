"""The items this engine will never compute, declared rather than discovered.

Five items — ``header/D-G-OVERHEAD``, ``lateral_uplift/RF-{HOUSE,GARAGE}`` and
``rafter/RF-{HOUSE,GARAGE}`` — reach ``haus engineering`` today only because a check names
an ``engineering_item`` of a kind nobody registered, and ``EngineeringResults.__getitem__``
synthesises a bare ``NO_CALC`` for it. They exist by accident, and their record says only
"no calculation is registered for this kind", which is true and useless: it does not say
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
    reason="the roof is outside the sawn-lumber rafter span table — it either resolves no "
           "rafters at all (trussed, or framed on a ridge beam) or is framed in a profile "
           "the table does not publish, such as an engineered I-joist. Either way the "
           "component manufacturer's sealed design governs and this engine computes none",
    designer="truss or I-joist manufacturer's engineer of record",
    deliverable="a sealed component design and placement plan for the roof, covering the "
                "profile, the bearing reactions, the web stiffener and hanger schedule, "
                "and the ground-snow case this site carries",
    unblocks="Roof framing — the S-105 rafter/truss line and the roof-load permit item",
    oracle=(Oracle(note="catlin_truss_engineering.md",
                   test="tests/test_wind_loads.py"),),
))

_declare(Deferral(
    kind="lateral_uplift",
    reason="the uplift connection schedule over this roof is covered joint by joint, but "
           "its CAPACITY is not evaluated: this engine derives no tributary area, no force "
           "coefficient and no share of the storey shear for any joint in it",
    designer="truss fabricator's engineer of record (uplift reactions), with the "
             "structural engineer of record for the continuous load path below them",
    deliverable="uplift reactions at every bearing, and a connector schedule sized against "
                "them from the truss heel to the foundation",
    unblocks="Wind uplift load path — structural.uplift_capacity",
    oracle=(Oracle(note="uplift_load_path.md",
                   test="tests/test_uplift_load_path.py"),),
))

_declare(Deferral(
    kind="header",
    reason="the opening is wider than the prescriptive header table publishes, and no "
           "engineered beam is authored for it — the supplier's schedule governs",
    designer="overhead-door supplier's header schedule, or the structural engineer of "
             "record where the supplier publishes none",
    deliverable="a header size and bearing detail for the opening width, at this snow and "
                "roof load, with the jamb studs it lands on",
    unblocks="Structural headers — structural.header_prescriptive",
    oracle=(Oracle(note="ridge_beam_detail.md"),),
))


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


@keys("lateral_uplift")
def _uplift_keys(ctx: EngineeringContext) -> list[str]:
    """Every roof. ``structural.uplift_capacity`` names one item per roof unconditionally,
    so this enumeration cannot drift from the check that consumes it."""
    return sorted(roof.tag for roof in ctx.model.roofs)


@keys("rafter")
def _rafter_keys(ctx: EngineeringContext) -> list[str]:
    """Roofs that resolve no rafter member — the trussed case, which is the one this engine
    can never compute. A roof framed in a profile the span table does not publish (catlin's
    RF-HOUSE, on 11-7/8" I-joists at 24") also raises a ``rafter/<tag>`` item; that one is
    reached through the finding that names it, because re-deriving here which profiles the
    table covers would be the same judgement written twice, free to drift."""
    return sorted(roof.tag for roof in ctx.model.roofs
                  if not any(member.category == "rafter" for member in roof.members))


@keys("header")
def _header_keys(_ctx: EngineeringContext) -> list[str]:
    """None enumerated. Whether an opening is over the prescriptive table is a conclusion
    ``structural.header_prescriptive`` reaches from the span table it owns, and re-deriving
    the threshold here would be a second copy of it free to drift. The kind is registered so
    the deferral above answers for every header item the checks do raise."""
    return []
