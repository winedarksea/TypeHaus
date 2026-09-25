"""How many wall tags does this house carry, and are any two of them the same wall?

A wall tag is one geometry stack (decision #70): every wall carrying it gets the same
detail drawing, IFC wall type, takeoff row and condition key. That is what makes the tag
count a real cost — the derived-detail condition graph is keyed on assembly *pairs*, the
G-002 ENVELOPE block truncates, and the builder has to look each one up.

So a difference that is only *which material* fills a layer is not a tag. It is
``Wall.layer_materials``, the way cladding colour already is. Two tags whose resolved
stacks agree layer by layer on everything but ``material_ref`` are one wall drawn twice,
and that is what this fails on.

The rest is reported as fact, not verdict: tags nothing references, and the histogram.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks._authoring import advisory_fail
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity


def _note(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    """A fact worth printing that is nobody's failure — see ``advisory/checks.py::_note``."""
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.PASS)


_CID = "advisory.assembly_variety"


def _shape(assembly: Any) -> str | None:
    """The stack with the materials taken out — what a detail drawing would show.

    Everything but ``material_ref`` counts, because nothing else in a layer is overridable
    per wall: thickness, function, framing spec, cavity fill and extent all belong to the
    tag. ``default_lining`` and ``interfaces`` come along whole.
    """
    if not assembly.layers:
        return None
    # ``repr`` of the dumps, because a dump holds dicts and a dict is not hashable. Field
    # order is the model's own and so is stable across assemblies.
    return repr((
        [layer.model_dump(exclude={"material_ref"}) for layer in assembly.layers],
        [layer.model_dump() for layer in assembly.default_lining],
        [iface.model_dump() for iface in assembly.interfaces],
    ))


@check(Tier.ADVISORY, _CID)
def assembly_variety(ctx: CheckContext) -> list[Finding]:
    """No two wall tags are the same stack in different materials; plus the inventory."""
    library = ctx.plan.library
    refs: dict[str, int] = {}
    wall_refs: dict[str, int] = {}
    for element in ctx.plan.all_elements():
        tag = getattr(element, "assembly", None)
        if not isinstance(tag, str):
            continue
        refs[tag] = refs.get(tag, 0) + 1
        if element.element_kind == "Wall":
            wall_refs[tag] = wall_refs.get(tag, 0) + 1

    out: list[Finding] = []

    # Material-only twins. Resolve first, so a variant is compared as the wall it builds.
    shapes: dict[str, list[str]] = {}
    for tag in sorted(wall_refs):
        resolved = library.resolve_assembly(tag)
        if resolved is None:
            continue
        shape = _shape(resolved)
        if shape is None:
            continue
        shapes.setdefault(shape, []).append(tag)
    for tags in shapes.values():
        if len(tags) < 2:
            continue
        for i, first in enumerate(tags):
            for second in tags[i + 1:]:
                out.append(advisory_fail(
                    _CID,
                    f"wall assemblies {first} and {second} are the same stack and differ "
                    "only in which material fills a layer — fold them into one tag and "
                    "state the difference with Wall.layer_materials (#70)",
                ))

    unreferenced = sorted(a.tag for a in library.assemblies if a.tag not in refs)
    if unreferenced:
        out.append(_note(
            _CID,
            f"{len(unreferenced)} assembly tag(s) no element references — delete each, or "
            f"say in a comment that it is a named revert ({', '.join(unreferenced)})",
        ))

    if wall_refs:
        once = sorted(tag for tag, n in wall_refs.items() if n == 1)
        detail = f" ({', '.join(once)})" if once else ""
        out.append(_note(
            _CID,
            f"{len(wall_refs)} wall assemblies across {sum(wall_refs.values())} walls, "
            f"{len(once)} used once{detail}",
        ))
    return out
