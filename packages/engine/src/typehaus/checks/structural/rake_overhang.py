"""Is a rake overhang's outlooker cantilever bounded by its own backspan?

** NOTHING GRADED AN OUTLOOKER, AND THAT IS HOW A 6'-0" ROOF EXTRUSION STOOD ON NOTHING. **
Before this module the only mention of the member in the whole check tree was an
interference *exclusion* (``checks/structural/interference.py`` excuses the
``outlooker`` x ``drop_truss`` pair, correctly, because ladder framing passes over the
gable truss by design). The catlin garage carried ``edge_overhangs=(("south", ft(6)),)``
on a roof whose ridge runs north-south, so "south" is a RAKE, and
``resolve/framing/roof_gable.py`` framed it as ladder framing: 2x4 outlookers at 24" o.c.
cantilevering **88 inches off a 24-inch backspan** on a 2x6 barge rafter, with no truss
over the passage at all. The report stayed clean.

**The rule, and why it is a ratio rather than a length.** An outlooker is a cantilever off
the first interior truss, passing over the dropped gable truss to the barge rafter — so its
backspan is one truss bay and nothing else (``roof_gable._outlookers`` sets it from
``layout.positions``). Conventional practice caps a cantilevered outlooker at about its
backspan, and prescriptive ladder framing well below that. This grades the same way
``structural.deck_joist_cantilever`` grades a deck overhang against R507.6.1: the ratio,
against the backspan the model actually resolved, so a roof whose truss spacing changes
re-grades itself instead of being measured against a number typed once.

**There is no IRC section for this and the finding says so.** IRC R802.11 and the AWC/TPI
truss provisions send a rake overhang to the truss designer; a 2x4 lookout is a fabricator
detail, not a prescriptive table. The bound here is the practice limit, and a member past it
is reported as something to put on the truss submittal — not as a code violation it is not.
"""

from __future__ import annotations

from typehaus.checks._authoring import not_applicable
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result

#: A cantilevered outlooker is conventionally held at or under its own backspan. This is a
#: practice limit, not a code one — see the module docstring — and it is deliberately the
#: LOOSER of the two figures in circulation (ladder framing is usually held near half this)
#: so that what it catches is unarguable rather than merely unconventional.
MAX_OUTLOOKER_CANTILEVER_RATIO = 1.0

_M_PER_FT = 0.3048


def _rake_members(ctx: CheckContext) -> list[tuple[str, float, object]]:
    """``(roof tag, truss bay in metres, outlooker)`` for every resolved ladder member.

    ** THE MEMBER DOES NOT CARRY ITS OWN CANTILEVER, AND THAT IS THE TRAP HERE. **
    ``roof_gable._outlookers`` builds each one from the first interior truss all the way to
    the barge rafter, so both its plan length and its ``length_m`` are backspan PLUS
    overhang. Subtracting them gives zero. The backspan is one truss bay by construction —
    the outlooker bears on the first interior truss and passes OVER the dropped gable
    truss — so the bay is read off the roof assembly's own ``FramingSpec``, which is the
    same number the layout positions the trusses on.
    """
    from typehaus.resolve.roof_geometry import roof_structure_framing

    out: list[tuple[str, float, object]] = []
    for roof in ctx.model.roofs:
        spec = roof_structure_framing(ctx.model, roof)
        spacing = getattr(getattr(spec, "spacing", None), "meters", None)
        if not spacing:
            continue
        for member in getattr(roof, "members", ()):
            if member.category == "outlooker":
                out.append((roof.tag, float(spacing), member))
    return out


@check(Tier.STRUCTURAL, "structural.rake_overhang_backspan")
def rake_overhang_backspan(ctx: CheckContext) -> list[Finding]:
    """Rake overhang vs. the outlooker backspan the truss layout actually resolved."""
    members = _rake_members(ctx)
    if not members:
        # Earned, not assumed: every gable in this model is flush or frames no ladder, so
        # the condition this rule governs does not exist here.
        return [not_applicable(
            "structural.rake_overhang_backspan",
            "no roof resolves a rake outlooker — every gable end is flush or trussed to "
            "its own edge, so there is no ladder cantilever to bound")]

    # One finding per roof, on its worst member: thirty identical rows for one bad rake
    # would bury the thing they are reporting.
    worst: dict[str, tuple[float, float, str]] = {}
    for roof_tag, backspan, member in members:
        total = ((member.p1[0] - member.p0[0]) ** 2
                 + (member.p1[1] - member.p0[1]) ** 2) ** 0.5
        overhang = total - backspan
        if total <= 1e-9 or backspan <= 1e-9 or overhang <= 1e-9:
            continue
        ratio = overhang / backspan
        prior = worst.get(roof_tag)
        if prior is None or ratio > prior[0] / max(prior[1], 1e-9):
            worst[roof_tag] = (overhang, backspan, member.child_key)

    out: list[Finding] = []
    for roof_tag in sorted(worst):
        overhang_m, backspan_m, key = worst[roof_tag]
        overhang_ft, backspan_ft = overhang_m / _M_PER_FT, backspan_m / _M_PER_FT
        allowable_ft = backspan_ft * MAX_OUTLOOKER_CANTILEVER_RATIO
        passing = overhang_ft <= allowable_ft + 1e-6
        out.append(_advisory(
            "structural.rake_overhang_backspan",
            f"roof {roof_tag} rake outlooker {key} cantilevers {overhang_ft:.2f}', "
            f"{'within' if passing else 'past'} its {backspan_ft:.2f}' backspan (one truss "
            f"bay) — no IRC table covers a lookout, so this is the practice limit and a "
            f"member past it belongs on the truss submittal",
            (roof_tag,), Result.PASS if passing else Result.FAIL,
            fix_hint=None if passing else
            "shorten the rake overhang, or carry it on real trusses instead of ladder "
            "framing and bear those on something",
        ))
    return out
