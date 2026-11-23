"""Section 4 of a family calculation: the working, limit state by limit state.

Review E-02: a sheet that prints only ``demand / capacity`` makes the PE rebuild every number.
Each worked member prints its symbols in plain words, its free-body sketch, a summary table,
then every limit state's :class:`~typehaus.engineering.item.Step` chain (equation, numbers
substituted, result, source) and the load combinations used. E-06: a family whose members
run different calculations (different limit states) is worked once per such template.
"""

from __future__ import annotations

from collections.abc import Sequence

from typehaus.emit.md_writer import bullets, table
from typehaus.engineering.item import EngineeringRecord, LimitState, sheet_spec
from typehaus.takeoff.calc_collapse import RefIndex
from typehaus.takeoff.calc_labels import label, unit_text, value_text
from typehaus.takeoff.calc_numfmt import num, ratio_text


def _signature(record: EngineeringRecord) -> tuple[str, ...]:
    names = sorted({s.name for s in record.limit_states if not s.is_detailing})
    return tuple(names) if names else (f"<{record.status.value}>",)


def templates(records: Sequence[EngineeringRecord],
              order: Sequence[EngineeringRecord]) -> list[list[EngineeringRecord]]:
    """Members grouped by the limit states they run; groups in ``order``'s order (worst
    first), members within a group in that order too."""
    groups: dict[tuple[str, ...], list[EngineeringRecord]] = {}
    for record in order:
        groups.setdefault(_signature(record), []).append(record)
    return list(groups.values())


def _form(state: LimitState) -> tuple[str, str]:
    if state.is_safety_factor:
        return (f"{num(state.demand)} required / {num(state.capacity)} achieved",
                "FS required / achieved")
    if state.is_detailing:
        return (f"{num(state.demand)} required / {num(state.capacity)} provided",
                "required / provided")
    return f"{num(state.demand)} / {num(state.capacity)}", "demand / capacity"


def _symbols(record: EngineeringRecord) -> str:
    return table(
        ["Symbol", "Meaning", "Value", "Unit"],
        [[f"`{q.name}`", label(record.kind, q) or "—", value_text(q, num),
          unit_text(q) or "—"] for q in record.inputs])


def _figure(record: EngineeringRecord) -> str:
    draw = sheet_spec(record.kind).figure
    figure = draw(record) if draw is not None else None
    if figure is None:
        return ""
    body = "\n".join(figure.lines)
    caption = f"\n\n{figure.caption}" if figure.caption else ""
    return f"**Free body — {figure.title}** (not to scale)\n\n```\n{body}\n```{caption}"


def _summary(record: EngineeringRecord, refs: RefIndex) -> str:
    rows = []
    for state in record.limit_states:
        form, _basis = _form(state)
        name = f"**{state.name}**" if state is record.governing else state.name
        rows.append([name, f"{form} {state.unit}".strip(), ratio_text(state.ratio),
                     state.combination or "—", refs.cite(state.citation)])
    return table(["Limit state", "Demand / capacity", "= d/c", "Load combination",
                  "Ref."], rows)


def _working(record: EngineeringRecord, refs: RefIndex) -> str:
    blocks = []
    bare = []
    seen: set[tuple[str, float]] = set()
    for state in record.limit_states:
        if not state.working:
            bare.append(state.name)
            continue
        form, basis = _form(state)
        verdict = "within" if state.ok else "OVER"
        head = (f"**{state.name}** — {refs.cite(state.citation)}"
                + (f", {state.combination}" if state.combination else ""))
        tail = (f"{basis}: {form} {state.unit} = d/c {ratio_text(state.ratio)}, "
                f"{verdict}.").replace("  ", " ")
        fresh = [step for step in state.working if (step.symbol, step.value) not in seen]
        reused = [step.symbol for step in state.working if (step.symbol, step.value) in seen]
        seen.update((step.symbol, step.value) for step in state.working)
        lines = [step.text() for step in fresh]
        if reused:
            lines.insert(0, "as above: " + ", ".join(f"`{sym}`" for sym in reused))
        blocks.append(head + "\n\n" + bullets(lines) + "\n\n" + tail)
    if bare:
        blocks.append(f"Working not yet itemised for {len(bare)} of "
                      f"{len(record.limit_states)} state(s); see each one's reference.")
    return "\n\n".join(blocks)


def _combinations(record: EngineeringRecord) -> str:
    used: dict[str, list[str]] = {}
    for state in record.limit_states:
        if state.combination:
            used.setdefault(state.combination, []).append(state.name)
    if not used:
        return ""
    return "**Load combinations used**\n\n" + table(
        ["Combination", "Limit states"], [[combo, ", ".join(names)]
                                          for combo, names in used.items()])


def worked_member(record: EngineeringRecord, refs: RefIndex) -> str:
    blocks = [f"Worked at **`{record.item_id}`**."]
    if record.inputs:
        blocks.append(_symbols(record))
    else:
        blocks.append("_This member consumed no input; nothing is computed here._")
    if figure := _figure(record):
        blocks.append(figure)
    if not record.limit_states:
        blocks.append("_No limit state is computed. What governs is named under "
                      "**Result**._")
        return "\n\n".join(blocks)
    blocks.append(_summary(record, refs))
    if working := _working(record, refs):
        blocks.append(working)
    if combos := _combinations(record):
        blocks.append(combos)
    return "\n\n".join(blocks)


def render_worked(records: Sequence[EngineeringRecord], order: Sequence[EngineeringRecord],
                  refs: RefIndex) -> str:
    """Section 4's body: one worked member per template, worst template first."""
    groups = templates(records, order)
    if len(groups) == 1:
        return worked_member(groups[0][0], refs)
    blocks = [f"{len(groups)} calculations in this family, each worked at its worst member."]
    for letter, group in zip("abcdefghijklmnopqrstuvwxyz", groups, strict=False):
        tags = ", ".join(f"`{r.key}`" for r in group)
        blocks.append(f"### 4{letter} — {tags}")
        blocks.append(worked_member(group[0], refs))
    return "\n\n".join(blocks)
