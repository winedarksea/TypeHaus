"""Duplicate catalog tags are a hard error (→ 12 §Checks).

Every catalog lookup on :class:`Library` is ``next((x for x in catalog if x.tag == tag), None)``
— first match wins, silently. So a house that shadows a library door type with its own entry
of the same tag gets *one* of them, chosen by the order the manifest happened to splat the
tuples together, with nothing anywhere saying a choice was made. The docstrings already
claimed a duplicate tag was a hard error; nothing enforced it. This does.

It runs at INTEGRITY tier, i.e. before any dedupe or retag work touches the catalogs, so a
retag that collides is caught as a collision rather than as a mysterious spec change.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity

# Every tag-keyed catalog on Library. Named explicitly rather than discovered, so adding a
# catalog is a deliberate decision to cover (or not cover) it.
CATALOGS = (
    "materials", "assemblies", "products", "door_types", "window_types", "furniture_types",
    "railing_types", "fixture_types", "appliance_types", "equipment_types",
    "register_types", "electrical_device_types", "circuits", "load_managements",
    "transitions", "construction_rules",
)


@check(Tier.INTEGRITY, "integrity.duplicate_catalog_tag")
def duplicate_catalog_tag(ctx: CheckContext) -> list[Finding]:
    findings: list[Finding] = []
    library = ctx.plan.library
    for catalog in CATALOGS:
        counts: dict[str, int] = {}
        for entry in getattr(library, catalog, ()) or ():
            tag = getattr(entry, "tag", None)
            if tag is None:
                continue
            counts[tag] = counts.get(tag, 0) + 1
        for tag, count in sorted(counts.items()):
            if count > 1:
                findings.append(Finding(
                    severity=Severity.ERROR,
                    check_id="integrity.duplicate_catalog_tag",
                    message=(f"library.{catalog} defines tag {tag!r} {count} times; lookups "
                             "take the first match, so the others are silently unreachable"),
                    element_tags=(tag,),
                    fix_hint=(f"rename or delete the duplicate {catalog} entry — a house "
                              "entry shadowing a library one must not share its tag"),
                    result=Result.FAIL,
                ))
    return findings


# The catalogs whose entries may name a product. ``Library.products`` itself is excluded —
# a product does not reference another product.
_PRODUCT_REF_CATALOGS = tuple(c for c in CATALOGS if c not in {"products", "assemblies"})


@check(Tier.INTEGRITY, "integrity.unknown_product_ref")
def unknown_product_ref(ctx: CheckContext) -> list[Finding]:
    """A ``product_ref`` naming nothing is an ERROR, not a silent blank row.

    The lookup is ``Library.product(tag)``, which returns None for a miss exactly as it does
    for a real absence — so a typo'd ref reads downstream as "no product chosen" and the
    sidebar, the schedules and the estimate all quietly agree about a choice nobody made.
    This is the narrow dangling-reference check for the one field that has no other guard.
    """
    library = ctx.plan.library
    known = {p.tag for p in library.products}
    findings: list[Finding] = []
    for catalog in _PRODUCT_REF_CATALOGS:
        for entry in getattr(library, catalog, ()) or ():
            ref = getattr(entry, "product_ref", None)
            if ref is None or ref in known:
                continue
            tag = getattr(entry, "tag", "?")
            findings.append(Finding(
                severity=Severity.ERROR,
                check_id="integrity.unknown_product_ref",
                message=(f"library.{catalog} entry {tag!r} names product_ref {ref!r}, which no "
                         "entry in library.products defines"),
                element_tags=(tag,),
                fix_hint=(f"add a Product(tag={ref!r}, ...) to the house's product catalog, or "
                          "correct the reference"),
                result=Result.FAIL,
            ))
    return findings


@check(Tier.INTEGRITY, "integrity.register_duct_ref")
def register_duct_ref(ctx: CheckContext) -> list[Finding]:
    """``Register.duct_ref`` names a real ``DuctRun``, or the register says why it needs none.

    The field is a bare string and every consumer reads it defensively — ``_takeoffs`` in
    ``mep.duct_connectivity``, the boot reach, the register schedule — so a typo does not
    error anywhere. It simply reads as "no register names this run", which is the same
    reading as a run that genuinely has no take-off: the grille loses its duct and the trunk
    loses its cap excuse, both silently, and the plan set prints a schedule row pointing at
    nothing.

    ``duct_ref is None`` is reported too, and it is the half that was completely invisible.
    The one honest absence is a ``TRANSFER`` louver: a passive opening between two spaces
    belongs to no ducted system and carries no ``duct_ref`` by construction (see
    ``DuctSystem.TRANSFER``), so it is skipped rather than excused — there is nothing there
    to connect.
    """
    from typehaus.model.enums import DuctSystem

    runs = {element.tag for element in ctx.plan.all_elements()
            if element.element_kind == "DuctRun"}
    findings: list[Finding] = []
    for element in ctx.plan.all_elements():
        if element.element_kind != "Register":
            continue
        if getattr(element, "kind", None) is DuctSystem.TRANSFER:
            continue
        ref = getattr(element, "duct_ref", None)
        if ref is None:
            findings.append(Finding(
                severity=Severity.WARN,
                check_id="integrity.register_duct_ref",
                message=(f"register {element.tag} names no duct_ref, so nothing in the model "
                         "says which run feeds it — the grille is drawn and scheduled with "
                         "no duct behind it"),
                element_tags=(element.tag,),
                fix_hint=("author duct_ref=<DuctRun tag> on the register, or file a passive "
                          "opening as DuctSystem.TRANSFER, which carries no duct by design"),
                result=Result.UNKNOWN,
            ))
            continue
        if ref not in runs:
            findings.append(Finding(
                severity=Severity.ERROR,
                check_id="integrity.register_duct_ref",
                message=(f"register {element.tag} names duct_ref {ref!r}, which no DuctRun "
                         "in this plan defines; every consumer reads the field defensively, "
                         "so the typo shows up as an unserved run rather than as an error"),
                element_tags=(element.tag,),
                fix_hint=f"correct the reference, or add a DuctRun(tag={ref!r}, ...)",
                result=Result.FAIL,
            ))
    if not findings:
        findings.append(Finding(
            severity=Severity.WARN,
            check_id="integrity.register_duct_ref",
            message=(f"every register naming a duct names one of the {len(runs)} DuctRuns in "
                     "this plan, and every register without one is a TRANSFER louver"),
            element_tags=(),
            result=Result.PASS,
        ))
    return findings
