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
