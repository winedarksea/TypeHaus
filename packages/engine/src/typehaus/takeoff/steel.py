"""Rolled steel members by the foot — the one structural family a volume rate cannot buy.

A ``Beam`` or a ``Post`` reaches the estimate through ``structural_solids``, which measures
VOLUME and is priced by the cubic yard out of ``[concrete]`` (cast) or ``[timber]`` (wood).
A steel angle fits neither: steel is bought by the foot of a named section, an L3-1/2 x 3-1/2
x 1/4 and an L3-1/2 x 3-1/2 x 3/8 are different purchases at the same bounding box, and a
$/cy rate on 0.01 cy prices a lintel at nothing. ``BM-M-FIRE-LINTEL`` billed exactly $0 for
nine days because of it (``plans/TODO.md``), and the trap was live for every steel member
anybody might author next.

So this is a table of its own, keyed on the member's own ``size`` string — the AISC section
— and priced by the LINEAL FOOT, with ``ea`` available for a shop-fabricated piece bought as
one part. The rows are EXCLUDED from ``structural_solids`` (``framing.py`` calls
:func:`steel_member_tags`), because a member that bills here must not also bill there.

WHAT COUNTS AS STEEL, and it is deliberately narrow: a profile whose ``cross_section``
resolves ``shape == "angle"``. That is the only rolled shape this engine's profile grammar
parses today — there is no W, C or HSS pattern — so widening the test would be guessing at
strings nobody can author. When one of those patterns lands, name its shape here.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel

_FT_PER_IN = 1.0 / 12.0

#: ``CrossSection.shape`` values billed by this table. See the module docstring.
STEEL_SHAPES = frozenset({"angle"})


def _sizes_by_tag(model: ResolvedModel) -> dict[str, str]:
    """Every plan element that carries a free-string ``size``, keyed by tag."""
    out: dict[str, str] = {}
    for element in model.plan.all_elements():
        size = getattr(element, "size", None)
        tag = getattr(element, "tag", None)
        if isinstance(size, str) and size and isinstance(tag, str):
            out[tag] = size
    return out


def _length_m(solid) -> float:
    """The member's long dimension: a beam runs in plan, a post runs in z."""
    xs = [x for x, _y in solid.outline]
    ys = [y for _x, y in solid.outline]
    if not xs:
        return 0.0
    return max(max(xs) - min(xs), max(ys) - min(ys), solid.z1_m - solid.z0_m)


def steel_member_rows(model: ResolvedModel) -> list[tuple[str, str, float]]:
    """``(tag, size, length_m)`` for every solid this table claims."""
    sizes = _sizes_by_tag(model)
    out: list[tuple[str, str, float]] = []
    for solid in model.solids:
        if solid.derived:
            continue
        size = sizes.get(solid.tag)
        if not size or cross_section(size).shape not in STEEL_SHAPES:
            continue
        out.append((solid.tag, size, _length_m(solid)))
    return out


def steel_member_tags(model: ResolvedModel) -> frozenset[str]:
    """Solid tags billed here, so ``structural_solids`` can leave them out."""
    return frozenset(tag for tag, _size, _length in steel_member_rows(model))


def steel_members_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per AISC section: count, lineal feet, and the members in it.

    ``weight_lb`` is deliberately ABSENT. A section's weight per foot is published data this
    engine does not carry — ``cross_section`` reads a bounding box and a leg thickness, not
    an AISC table — and deriving it from the drawn solid would bill the bounding box, which
    on an angle is about 7x the steel. Steel is quoted by the foot of a named section here
    for exactly that reason; a fabricator converts to weight off the section name.
    """
    groups: dict[str, dict[str, object]] = {}
    for tag, size, length_m in steel_member_rows(model):
        row = groups.get(size)
        if row is None:
            row = groups[size] = {"size": size, "shape": cross_section(size).shape,
                                  "count": 0, "length_ft": 0.0, "tags": []}
        row["count"] = int(row["count"]) + 1
        row["length_ft"] = float(row["length_ft"]) + length_m / M_PER_IN * _FT_PER_IN
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(tag)
    return [{**groups[size], "length_ft": round(float(groups[size]["length_ft"]), 2),
             "tags": sorted(groups[size]["tags"])}  # type: ignore[arg-type]
            for size in sorted(groups)]
