"""A nominal size the section parser cannot read is a guessed member (→ 12 §Checks).

``resolve/framing/profiles.cross_section`` never raises. Anything it cannot read comes back
as the ``_FALLBACK_ACTUAL_IN`` rectangle — 1 1/2" x 5 1/2", a 2x6 — and the two *nominal*
branches do the same thing one level down: a well-formed but unpublished size
(``"3.5x3.5 STEEL"``, ``"L3-1/2x3-1/2x1/4"``, ``"16x16"``) matches the pattern, misses
``LUMBER_ACTUAL``, and is handed back looking exactly like a successful parse. Nothing
downstream can tell the two apart, so the guess propagates in silence: the solid draws at
2x6, the plan cut measures 1 1/2", the interference check clears against a section nobody
authored, and the BOM bills lineal feet of the wrong stock.

The silence in ``cross_section`` is deliberate and stays. Thirty-one modules call it from
inside ``resolve()``, where a raise would abort the build rather than report a defect, and
the parser is not the place to hold an opinion about a house. So the question is asked here
instead, once, against every nominal the model actually carries, and answered as a finding.

**UNKNOWN, not FAIL.** The model cannot say the member is wrong — it can only say it does
not know what section this string names, which is the definition of the third verdict. And
the fix is frequently *not* in the house: two library assemblies name a resilient channel
in a ``FramingSpec``, which is a real product that no lumber pattern will ever spell.
"""

from __future__ import annotations

from collections.abc import Iterator

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, not_applicable, passed, unknown
from typehaus.model.floors import JoistSpec
from typehaus.resolve.framing.profiles import parses

_CHECK_ID = "integrity.member_profile_parses"

#: Element fields holding a nominal member size, as ``(element_kind, field)``. Named
#: explicitly rather than swept by field name, because the *name* is not the tell: a
#: ``Connector.size`` is a product model ("HUC212-3"), a ``Countertop.profile`` an edge
#: treatment ("eased"), and neither is ever handed to ``cross_section``. Every pair below
#: is one that ``resolve/`` really does parse — see ``resolve/envelope.py`` (post, beam) and
#: ``resolve/accessories.py`` (knee brace, wedge).
#:
#: The two ``post_size`` fields reach ``geometry.nominal_actual_m`` rather than
#: ``cross_section`` (``resolve/accessories.py``, ``resolve/railings/parts.py``). That is a
#: second parser with a second silent fallback — an unreadable string comes back as a 2x,
#: 1 1/2" — so the same question applies and ``parses()`` is the same right answer to it.
_ELEMENT_FIELDS: tuple[tuple[str, str], ...] = (
    ("Post", "size"),
    ("Beam", "size"),
    ("KneeBrace", "member"),
    ("KneeBrace", "post_size"),
    ("Wedge", "member"),
    ("Railing", "post_size"),
)

#: ``FramingSpec`` fields naming a nominal. ``web_member`` is included with the three the
#: brief listed: it is the same field on the same record, read by the same parser.
_FRAMING_FIELDS = ("member", "plate_member", "chord_member", "web_member")

#: ``JoistSpec`` fields naming a nominal — a floor deck's own stock, which reaches
#: ``cross_section`` through ``resolve/floors.py`` and ``resolve/ceiling_over.py``.
_JOIST_FIELDS = ("member", "rim_member")


def _authored(ctx: CheckContext) -> Iterator[tuple[str, str, str]]:
    """``(owner, field, profile)`` for every authored nominal in the plan and its catalog."""
    for element in ctx.plan.all_elements():
        for kind, field in _ELEMENT_FIELDS:
            if element.element_kind != kind:
                continue
            value = getattr(element, field, None)
            if isinstance(value, str) and value:
                yield element.tag, f"{kind}.{field}", value
        joists = getattr(element, "joists", None)
        if isinstance(joists, JoistSpec):
            for field in _JOIST_FIELDS:
                value = getattr(joists, field, None)
                if isinstance(value, str) and value:
                    yield element.tag, f"joists.{field}", value
    for assembly in ctx.plan.library.assemblies:
        for layer in assembly.layers:
            spec = getattr(layer, "framing", None)
            if spec is None:
                continue
            for field in _FRAMING_FIELDS:
                value = getattr(spec, field, None)
                if isinstance(value, str) and value:
                    yield f"{assembly.tag}/{layer.name}", f"FramingSpec.{field}", value


def _resolved(ctx: CheckContext) -> Iterator[tuple[str, str, str]]:
    """``(owner, field, profile)`` for every stick the solver actually produced.

    The authored sweep above cannot see these: a solver-chosen header, a stair carriage
    and the girt blocks all mint their profile string in ``resolve/``, and a constant
    mistyped there is as invisible as one mistyped in a house.
    """
    for member in ctx.model.all_members():
        yield f"{member.parent_uid}:{member.child_key}", "FramedMember.profile", member.profile


def _abbreviate(owners: list[str], limit: int = 4) -> str:
    head = ", ".join(owners[:limit])
    return head if len(owners) <= limit else f"{head} and {len(owners) - limit} more"


@check(Tier.INTEGRITY, _CHECK_ID)
def member_profile_parses(ctx: CheckContext) -> list[Finding]:
    seen = 0
    # Keyed on the profile STRING, not on the owner: one misspelling in one library
    # assembly is one defect however many sticks it grew into, and a finding per stick
    # would have buried catlin's single real hit under sixty-four copies of itself.
    #
    # Authored owners are kept apart from resolved ones for the same reason. They are where
    # the fix goes, and there are a handful of them against sixty-four solver-minted sticks
    # that would otherwise crowd them out of the message and out of ``element_tags``.
    authored: dict[str, list[str]] = {}
    grown: dict[str, list[str]] = {}
    fields: dict[str, set[str]] = {}
    for bucket, source in ((authored, _authored(ctx)), (grown, _resolved(ctx))):
        for owner, field, profile in source:
            seen += 1
            if parses(profile):
                continue
            bucket.setdefault(profile, []).append(owner)
            fields.setdefault(profile, set()).add(field)
    bad = sorted({*authored, *grown})

    if not seen:
        return [not_applicable(_CHECK_ID, "this building frames no member: no post, beam, "
                                          "brace, joist deck or framed assembly layer names "
                                          "a nominal size anywhere in the plan")]
    if not bad:
        return [passed(_CHECK_ID, f"every one of the {seen} authored and resolved nominal "
                                  "sizes in this building parses to a real cross-section")]

    findings: list[Finding] = []
    for profile in bad:
        written = sorted(authored.get(profile, ()))
        sticks = grown.get(profile, ())
        where = f"authored on {_abbreviate(written)}" if written else "minted in resolve/"
        if sticks:
            where += f", and {len(sticks)} resolved member(s) carry it"
        findings.append(unknown(
            _CHECK_ID,
            f"nominal size {profile!r} ({', '.join(sorted(fields[profile]))}) names no "
            "section this engine can read, so cross_section() silently hands every "
            'consumer a 1 1/2" x 5 1/2" rectangle instead — the solid, the plan cut, the '
            f"interference check and the BOM row are all a 2x6. {where}",
            tags=tuple(written or sorted(sticks))[:8],
            fix=("spell the member as a size the catalog publishes (a LUMBER_ACTUAL "
                 "nominal, an explicit decimal section like \"3.5x3.5\", or an LVL/LSL/"
                 "I-joist/truss/panel/round form), or give the product its own pattern in "
                 "resolve/framing/profiles.py — a real section, not a parser branch, where "
                 "the member is not lumber at all"),
        ))
    return findings
