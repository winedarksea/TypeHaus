"""S-100's steel: the foundation pours' reinforcement, and the cast columns' cages.

Split out of ``foundation_schedule``, which re-exports these names. Selectors and marks are
imported function-local, as in ``foundation_notes``: ``foundation_schedule`` imports this
module at the top, so the module-level edge runs one way only.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from typehaus.emit.draw.schedule_block import ScheduleTable
from typehaus.emit.draw.structural_common import inches_text
from typehaus.resolve.model import ResolvedModel

if TYPE_CHECKING:
    from typehaus.model.assembly import ConcreteSpec
    from typehaus.model.rebar import ReinforcementSpec


def reinforcement_schedule(model: ResolvedModel) -> ScheduleTable:
    """The steel in the foundation pours, one row per bar role.

    Reads ``ReinforcementSpec`` off the elements S-100 draws and prints nothing where a
    pour carries none: ACI 318-19 §14.1.4 permits plain concrete in a footing, so an absent
    spec is legal, not a hole to fill with a plausible mat. ELEMENT keys back through the
    sheet's own marks (FW1, F2, S3), which the reader can find on the drawing.
    """
    from typehaus.emit.draw.foundation_schedule import _abbreviate, foundation_marks
    from typehaus.resolve.concrete import concrete_spec_of

    marks = foundation_marks(model)
    mark_of = {**marks.wall, **marks.footing, **marks.pad, **marks.slab}
    grouped: dict[tuple[str, str, str], list[tuple[str, str]]] = {}
    specs: dict[tuple[str, str, str], ReinforcementSpec] = {}
    for element in _reinforced_elements(model):
        spec = element.reinforcement
        key = (element.element_kind, spec.model_dump_json()
               if hasattr(spec, "model_dump_json") else repr(spec),
               _cover_text(spec, concrete_spec_of(model.plan, getattr(element, "assembly",
                                                                     None))))
        grouped.setdefault(key, []).append(
            (mark_of.get(element.tag, element.tag), element.tag))
        specs[key] = spec
    rows: list[tuple[str, ...]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(),
                                                  key=lambda item: item[0][0]), start=1):
        spec = specs[key]
        element_kind, _identity, cover = key
        keys = _abbreviate(", ".join(sorted({mark for mark, _tag in members})), 20)
        lap = spec.lap_class or "—"
        # One row per group, the roles in one cell: rows are this sheet's height and its scale
        # (tests/test_schedule_columns.py), and a group reads as one schedule line anyway.
        rows.append((f"R{index}", f"{keys} ({len(members)})",
                     " + ".join(_bar_text(bar) for bar in spec.bars), cover, lap))
    return ScheduleTable(
        title="FOUNDATION REINFORCEMENT SCHEDULE",
        columns=("MARK", "ELEMENT", "STEEL", "COVER", "LAP"),
        rows=tuple(rows),
    )


_ROLE_ABBREV = {"vertical": "V", "horizontal": "H", "top-x": "TX", "top-y": "TY",
                "bottom-x": "BX", "bottom-y": "BY", "ties": "TIES", "stirrups": "STIR",
                "dowels": "DWL", "rib": "RIB"}


def _bar_text(bar) -> str:
    """``V #5 @ 41"``, ``H (3) #4``, ``DWL #6`` — role, count or spacing, layers, zone."""
    quantity = (f' @ {bar.spacing.inches:g}"' if bar.spacing is not None
                else f" ({bar.count})" if bar.count is not None else "")
    text = f"{_ROLE_ABBREV.get(bar.role, bar.role.upper())} #{bar.bar}{quantity}"
    if bar.layers > 1:
        text += f" x{bar.layers}"
    if bar.zone is not None:
        text += f" {bar.zone.feet:g}' EA END"
    return text


def _reinforced_elements(model: ResolvedModel) -> list[Any]:
    """Foundation-scope pours carrying an authored ``ReinforcementSpec``, in tag order.
    The four kinds this sheet draws as foundation, plus a cast ``Beam`` (a grade beam); a cast
    pier is a ``Post`` with a cage of its own, in ``column_reinforcement_schedule``."""
    from typehaus.emit.draw.foundation_schedule import slabs_on_grade

    kinds = {"FoundationWall", "Footing", "Pad", "Slab", "Beam"}
    # A slab only where the sheet marks it (on grade): a suspended deck's steel is not a
    # foundation schedule's, and its rows cost this sheet its scale.
    on_grade = {slab.tag for slab in slabs_on_grade(model)}
    return sorted((element for element in model.plan.all_elements()
                   if element.element_kind in kinds
                   and (element.element_kind != "Slab" or element.tag in on_grade)
                   and getattr(element, "reinforcement", None) is not None),
                  key=lambda element: element.tag)


def _cover_text(spec: ReinforcementSpec, concrete: ConcreteSpec | None) -> str:
    """The element's own cover, else the mix's, else the truth. The element outranks the
    mix by design: a stem cast against earth buys cover the plant ticket knows nothing
    about."""
    if spec.cover is not None:
        return inches_text(spec.cover.inches)
    if concrete is not None and concrete.cover is not None:
        return f"{inches_text(concrete.cover.inches)} (MIX)"
    return "NOT STATED"


def column_reinforcement_schedule(model: ResolvedModel) -> ScheduleTable:
    """The cage in every cast ``Post`` (pier or column), one row per identical cage.

    Read off the authored ``ReinforcementSpec``; a dowel set that says "one per vertical"
    carries no count of its own, so the count is the resolved set's (``model.rebar``), and
    printed only where every column in the row agrees.
    """
    from typehaus.resolve.concrete import concrete_spec_of

    resolved = {bars.host_tag: Counter(bar.role for bar in bars.bars)
                for bars in model.rebar if bars.host_kind == "Post"}
    grouped: dict[tuple[str, str, str], list[Any]] = {}
    for post in sorted((e for e in model.plan.all_elements()
                        if e.element_kind == "Post"
                        and getattr(e, "reinforcement", None) is not None),
                       key=lambda e: e.tag):
        spec = post.reinforcement
        cover = _cover_text(spec, concrete_spec_of(model.plan, post.assembly))
        grouped.setdefault((str(post.size), spec.model_dump_json(), cover), []).append(post)
    rows: list[tuple[str, ...]] = []
    for (size, _identity, cover), posts in grouped.items():
        spec = posts[0].reinforcement
        cells = {"vertical": "—", "ties": "—", "dowels": "—"}
        for bar in spec.bars:
            if bar.role not in cells:
                continue
            counts = {resolved.get(post.tag, Counter())[bar.role] for post in posts}
            count = bar.count if bar.count is not None else (
                counts.pop() if len(counts) == 1 and 0 not in counts else None)
            text = (f'#{bar.bar} @ {bar.spacing.inches:g}"' if bar.spacing is not None
                    else f"({count}) #{bar.bar}" if count is not None else f"#{bar.bar}")
            if bar.embedment is not None:
                text += f" {inches_text(bar.embedment.inches)} EMB"
            cells[bar.role] = text
        rows.append((f"{_tag_family([post.tag for post in posts])} ({len(posts)})",
                     size.upper(), cells["vertical"], cells["ties"], cells["dowels"], cover,
                     spec.lap_class or "—"))
    return ScheduleTable(
        title="CAST COLUMN / PIER REINFORCEMENT",
        columns=("COLUMNS", "SIZE", "VERT", "TIES", "DOWELS", "COVER", "LAP"),
        rows=tuple(rows),
    )


def _tag_family(tags: list[str]) -> str:
    """``PT-BW-GW/PE/W``: the shared dash-prefix once, then each tag's own tail."""
    stems = {tag.rsplit("-", 1)[0] for tag in tags}
    if len(tags) < 2 or len(stems) != 1:
        return ", ".join(tags)
    stem = stems.pop()
    return f"{stem}-" + "/".join(tag[len(stem) + 1:] for tag in tags)
