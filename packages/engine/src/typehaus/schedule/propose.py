"""The engine proposes a visit split; the person commits it.

Same commitment as ``routing/``: **there is no ``--write``.** A split is a judgement about
how a sub wants to mobilise — two pours or three, one crew or two — and the engine can see
only what the BOM and the tags make obvious. So this module prints dialect-free TOML for
the owner to paste into ``tasks.toml``, edit, or ignore.

What it can see is real, though. A concrete package on catlin covers footings, foundation
walls and slabs, whose rows are three different BOM families and whose tags are three
different prefixes; proposing them as one arrival would be wrong in a way nobody could
miss, and proposing them as three is right often enough to be worth pasting.

**No lead-time numbers, anywhere.** The default constraints are labels — "windows
delivered and checked against the RO schedule" — because that is a fact somebody
establishes by looking in the garage. How many weeks the supplier quoted is not in this
model and never will be.
"""

from __future__ import annotations

import json
from typing import Any

#: Constraint labels worth proposing per trade. Judgement, authored once, and deliberately
#: not derived: nothing in a geometry model says a crane needs booking.
DEFAULT_CONSTRAINTS: dict[str, tuple[str, ...]] = {
    "earth": ("locates called and marked", "spoil and topsoil stockpile located",
              "erosion control in place before the first cut"),
    "concrete": ("rebar fabricated, delivered and inspected",
                 "P/E/M on site during forming for every sleeve and block-out",
                 "pump or chute access confirmed for the whole pour"),
    "drainage": ("washed rock and filter fabric on site",
                 "discharge daylight or drywell excavated"),
    "framing": ("sealed truss drawings on site", "crane booked",
                "hangers, straps and hold-downs delivered and sorted"),
    "floors": ("subfloor adhesive and fasteners on site",),
    "roof": ("all penetrations set — nothing goes through afterwards",
             "edge metal and underlayment on site", "fall protection rigged"),
    "walls": ("girt screws verified on every wall — inspect the pattern before the "
              "sprayer arrives, it is invisible once the foam is on",
              "sprayer, rig and installer booked; substrate dry and above the product's "
              "minimum temperature",
              "cladding fastener pattern agreed and mocked up"),
    "openings": ("windows delivered and checked against the RO schedule",
                 "flashing tape and sill pans on site",
                 "rough openings measured before the truck is unloaded"),
    "plumbing": ("fixture schedule confirmed against what was ordered",
                 "test equipment on site"),
    "electrical": ("permit filed with the authority named in [authorities], and the "
                   "request for inspection in",
                   "panel and service equipment delivered"),
    "mechanical": ("equipment delivered and staged out of the weather",
                   "balancing report scheduled"),
    "stairs": ("treads and guards fabricated to the as-built rise",),
    "furniture": ("appliances delivered and uncrated", "casework template verified"),
}

#: On every arrival, whatever the trade. The list an owner-builder forgets exactly once.
ARRIVAL_CONSTRAINTS: tuple[str, ...] = (
    "approved plan set on site and current",
    "materials staged where the crew will work",
    "site access, parking and dumpster clear",
    "temporary power and water available",
    "confirmed with the sub 48 hours ahead",
)


#: Row-family order inside a trade, in the order the work actually happens. Replaces an
#: alphabetical sort, which put ``concrete:flatwork`` second and the footings fourth.
#: A family this does not name keeps its BOM order, after the ones that are named.
FAMILY_ORDER: dict[str, tuple[str, ...]] = {
    "earth": ("excavation", "backfill", "grading"),
    "concrete": ("footing", "thermal_break", "wall", "column", "slab", "flatwork"),
    "drainage": ("drain_tile", "drywell", "gutter"),
    "framing": ("post", "beam", "wall_structure", "joist", "truss", "sheathing"),
    "floors": ("joist", "sheet_goods", "floor_finish"),
    "roof": ("sheathing", "membrane", "roofing", "trim", "flashing"),
    "walls": ("insulation", "furring", "cladding", "trim"),
    "openings": ("window", "door", "flashing", "hardware"),
    "plumbing": ("pipe_runs", "plumbing_specialties", "fixtures"),
    "electrical": ("conduit", "devices", "panel", "luminaires"),
    "mechanical": ("ducts", "duct_fittings", "equipment", "registers"),
    "stairs": ("stairs", "railings"),
    "furniture": ("placeables", "appliances"),
}

#: Tag prefix -> the row family that arrival belongs to. The BOM carries no join between
#: an element tag and a BOM row, so this is the map that used to be a character-overlap
#: guess. A prefix this does not name falls to the package's first family, which is honest:
#: the owner edits the globs, and that is exactly why they are globs.
TAG_FAMILY: dict[str, str] = {
    "FT": "footing", "FB": "footing", "W": "wall", "SL": "slab", "DW": "flatwork",
    "PT": "column", "BM": "beam", "FS": "joist", "TR": "trim", "RF": "roofing",
    "WIN": "window", "D": "door", "PR": "pipe_runs", "FX": "fixtures",
    "DU": "ducts", "REG": "registers", "EQ": "equipment", "ED": "devices",
    "CD": "conduit", "ST": "stairs", "RL": "railings", "FURN": "placeables",
    "APPL": "appliances", "DRW": "drywell", "FD": "drain_tile",
}


def family_rank(trade: str, family: str) -> tuple[int, str]:
    """Sort key: declared order first, then the family's own name as a tie-break."""
    key = family.split(":", 1)[-1]
    order = FAMILY_ORDER.get(trade, ())
    return (order.index(key) if key in order else len(order), key)


def _family(row: tuple[str, str]) -> str:
    """A BOM row's family: the section plus the bare key, before any ``:assembly``.

    ``concrete:footing`` and ``concrete:slab`` are two arrivals; ``slab`` and
    ``slab:DECK_EPS_INT`` are the same pour billed twice.
    """
    section, key = row
    return f"{section}:{str(key).split(':')[0]}"


def _tag_family(tag: str) -> str:
    """``FT-B-E2`` -> ``FT-B``. Two segments, because that is where the house's own naming
    stops being a kind and starts being an instance."""
    parts = str(tag).split("-")
    return "-".join(parts[:2]) if len(parts) > 2 else str(tag)


def _label(family: str, tags: tuple[str, ...]) -> str:
    where = ", ".join(sorted({_tag_family(tag) for tag in tags})[:3])
    key = family.split(":", 1)[-1].replace("_", " ")
    return f"{key}{f' — {where}' if where else ''}"


def propose_visits(item: Any, specs: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Split one work package into the arrivals its own BOM rows and tags imply.

    Returns dicts rather than :class:`~typehaus.schedule.model.Visit` objects on purpose:
    a proposal is not a visit until somebody pastes it, and giving it the same type would
    make it one keystroke away from being persisted by accident.
    """
    by_family: dict[str, list[tuple[str, str]]] = {}
    for row in item.rows:
        by_family.setdefault(_family(row), []).append(row)
    if len(by_family) < 2:
        return []

    gating = tuple(sorted(f"insp/{spec.id}" for spec in specs
                          if item.trade in getattr(spec, "gates", ())))
    tags_by_family = _tags_by_family(item, by_family)
    out: list[dict[str, Any]] = []
    previous: str | None = None
    for family in sorted(by_family, key=lambda f: family_rank(item.trade, f)):
        rows = sorted(by_family[family])
        tags = tags_by_family.get(family, ())
        slug = f"{item.slug}/{family.split(':', 1)[-1].split(':')[0]}"
        # Only the first proposed arrival inherits the package's own predecessors; the
        # rest follow the one before, which is the shape a sub actually mobilises in.
        depends_on = (tuple(item.depends_on) + gating) if previous is None else (previous,)
        proposal = {
            "slug": slug,
            "label": _label(family, tags),
            "rows": [{"section": section, "key": key} for section, key in rows],
            "element_tags": list(_globs(tags)),
            "depends_on": list(depends_on),
            "constraints": list(DEFAULT_CONSTRAINTS.get(item.trade, ())
                                + ARRIVAL_CONSTRAINTS),
        }
        proposal["toml"] = _toml(proposal)
        out.append(proposal)
        previous = slug
    return out


def _tags_by_family(item: Any, by_family: dict[str, list[tuple[str, str]]]
                    ) -> dict[str, tuple[str, ...]]:
    """Which of the package's element tags belong to each row family.

    The BOM does not carry the join, so this is a declared map (:data:`TAG_FAMILY`) rather
    than the character-overlap guess it used to be — that guess put footing tags on the
    flatwork arrival about as often as not. A prefix the map does not name falls to the
    package's first family. It is still a *proposal*; the owner edits the globs, which is
    exactly why they are globs.
    """
    families = sorted(by_family, key=lambda f: family_rank(item.trade, f))
    out: dict[str, list[str]] = {family: [] for family in families}
    bare = {family.split(":", 1)[-1]: family for family in families}
    for tag in item.element_tags:
        prefix = str(tag).split("-", 1)[0]
        target = bare.get(TAG_FAMILY.get(prefix, ""), families[0])
        out[target].append(tag)
    return {family: tuple(sorted(tags)) for family, tags in out.items()}


def _globs(tags: tuple[str, ...]) -> tuple[str, ...]:
    """``FT-B-E2``, ``FT-B-W1`` -> ``FT-B-*``. A glob the owner can read and widen."""
    return tuple(sorted({f"{_tag_family(tag)}-*" for tag in tags}))


def _toml(proposal: dict[str, Any]) -> str:
    """Ready to paste. Sorted, quoted, and carrying nothing the owner did not ask for."""
    lines = [f"[visits.{json.dumps(proposal['slug'])}]",
             f"label = {json.dumps(proposal['label'])}"]
    rows = ", ".join(json.dumps(f"{row['section']}:{row['key']}")
                     for row in proposal["rows"])
    lines.append(f"rows = [{rows}]")
    if proposal["element_tags"]:
        tags = ", ".join(json.dumps(tag) for tag in proposal["element_tags"])
        lines.append(f"element_tags = [{tags}]")
    if proposal["depends_on"]:
        deps = ", ".join(json.dumps(dep) for dep in proposal["depends_on"])
        lines.append(f"depends_on = [{deps}]")
    lines.append("constraints = [")
    lines.extend(f"  {{ label = {json.dumps(label)} }},"
                 for label in proposal["constraints"])
    lines.append("]")
    return "\n".join(lines)


def propose_all(work_items: Any, specs: tuple[Any, ...] = ()
                ) -> dict[str, list[dict[str, Any]]]:
    """``package slug -> proposals``, for every package a split is worth proposing on."""
    out: dict[str, list[dict[str, Any]]] = {}
    for item in work_items:
        proposals = propose_visits(item, specs)
        if proposals:
            out[item.slug] = proposals
    return out
