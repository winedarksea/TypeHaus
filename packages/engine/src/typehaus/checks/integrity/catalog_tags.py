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
    "materials", "assemblies", "door_types", "window_types", "furniture_types",
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
