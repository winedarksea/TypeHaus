"""Markdown for ``haus bids``: a trade's package, a crew's, a trade summary, the README.

Split from ``cmd_bids`` for the file limit. Byte-deterministic throughout (no date, sorted),
so the ``MANIFEST.json`` sha256s mean something. A crew of one trade a sub bids renders
exactly as that trade's package; a crew of several is one document, a part per trade, and a
``self_performed`` crew is the owner's materials list rather than a request for quote
(``takeoff/crews.py``, decision #115).
"""

from __future__ import annotations

from typing import Any

_RFQ = ("Quantities are net of waste unless a line says otherwise; this is a request for "
        "quote, not a purchase order. Price the scope as you would install it and note where "
        "your count differs.")
_OWNER = ("Owner-performed: the materials list for this scope, not a request for quote. "
          "Quantities are net of waste unless a line says otherwise.")


def _groups(package: Any, priced: bool, level: int) -> list[str]:
    from typehaus.emit.md_writer import heading, table

    blocks: list[str] = []
    price_cols = ["unit low", "unit high", "total low", "total high"] if priced else []
    for group in package.groups:
        # The application column only where a line carries one: the lumber, for the ticket.
        noted = any(line.application for line in group.lines)
        blocks.append(heading(group.heading, level))
        blocks.append(table(
            ["item", "quantity", "unit", *(["application"] if noted else []), "detail",
             "storeys", *price_cols],
            [[line.description, line.quantity, line.unit,
              *([line.application] if noted else []), line.detail, ", ".join(line.storeys),
              *((line.unit_price[0], line.unit_price[1], line.total[0], line.total[1])
                if priced and line.unit_price and line.total else
                (("", "", "", "") if priced else ()))]
             for line in group.lines]))
    return blocks


def _appendices(packages: list[Any]) -> list[str]:
    from typehaus.emit.md_writer import bullets, heading, table

    blocks: list[str] = []
    tagged = [line for p in packages if p.recipe.tags_appendix for line in p.lines]
    if tagged:
        blocks.append(heading("Appendix A — elements, per line", 2))
        blocks.append(table(["item", "elements"],
                            [[line.description, ", ".join(line.element_tags) or "—"]
                             for line in tagged]))
    sheets = list(dict.fromkeys(sheet for p in packages for sheet in p.sheets))
    if sheets:
        blocks.append(heading("Appendix B — drawings", 2))
        blocks.append(bullets(sheets))
    allowances = [line for p in packages for line in p.allowances]
    if allowances:
        blocks.append(heading("Appendix C — owner allowances in this trade", 2))
        blocks.append(table(["allowance", "quantity", "unit"],
                            [[line.description, line.quantity, line.unit]
                             for line in allowances]))
    return blocks


def package_markdown(package: Any, loaded: Any, priced: bool) -> str:
    """One trade's package as a request for quote."""
    from typehaus import engine_version
    from typehaus.emit.md_writer import callout, document, heading, kv_block

    return document(
        heading(f"{package.recipe.title} — {loaded.plan.project.name}"),
        kv_block([("House", loaded.plan.project.name), ("Trade", package.label),
                  ("Engine", engine_version()), ("Model hash", loaded.content_hash),
                  ("Lines", len(package.lines))]),
        package.recipe.intro, callout(_RFQ),
        *_groups(package, priced, 2), *_appendices([package]))


def crew_markdown(crew: Any, packages: dict[str, Any], loaded: Any, priced: bool) -> str:
    """One crew's package: its trades' packages as parts of one document."""
    from typehaus import engine_version
    from typehaus.emit.md_writer import callout, document, heading, kv_block

    parts = [packages[t] for t in crew.trades if t in packages]
    if len(parts) == 1 and not crew.self_performed:
        return package_markdown(parts[0], loaded, priced)
    blocks = [
        heading(f"{crew.title} — {loaded.plan.project.name}"),
        kv_block([("House", loaded.plan.project.name), ("Crew", crew.title),
                  ("Trades", ", ".join(p.label for p in parts)),
                  ("By", "owner" if crew.self_performed else "sub"),
                  ("Engine", engine_version()), ("Model hash", loaded.content_hash),
                  ("Lines", sum(len(p.lines) for p in parts))]),
        callout(_OWNER if crew.self_performed else _RFQ),
    ]
    if crew.note:
        blocks.append(crew.note)
    for package in parts:
        blocks += [heading(package.recipe.title, 2), package.recipe.intro,
                   *_groups(package, priced, 3)]
    return document(*blocks, *_appendices(parts))


def summary_markdown(summary: Any, loaded: Any) -> str:
    from typehaus import engine_version
    from typehaus.emit.md_writer import bullets, callout, document, heading, kv_block, table
    from typehaus.emit.trades import TRADE_LABELS

    blocks = [
        heading(f"{summary.title} — {loaded.plan.project.name}"),
        kv_block([("House", loaded.plan.project.name),
                  ("Trade", TRADE_LABELS.get(summary.trade, summary.trade)),
                  ("Engine", engine_version()), ("Model hash", loaded.content_hash)]),
        summary.intro,
        callout(f"The summary to price from. The detailed material list is the "
                f"{TRADE_LABELS.get(summary.trade, summary.trade)} package beside it, for a "
                "sub who wants it; quantities are net of waste."),
    ]
    for item in summary.tables:
        blocks += [heading(item.title, 2), table(item.columns, item.rows)]
        if item.notes:
            blocks.append(bullets(item.notes))
    return document(*blocks)


def readme(crews: dict[str, Any], packages: dict[str, Any], loaded: Any,
           summaries: dict[str, Any]) -> str:
    from typehaus.emit.md_writer import document, heading, table

    return document(
        heading(f"Bid packages — {loaded.plan.project.name}"),
        "One request for quote per crew, unpriced, from the model's bill of materials. A crew "
        "is the trades one sub takes together (`[crews]` in tasks.toml; a trade no crew names "
        "is its own); an owner crew's file is a materials list, not sent out. Where a trade "
        "prices from a schedule, `<trade>-summary.md` is that schedule and the package is the "
        "detail behind it.",
        table(["crew", "by", "trades", "lines", "storeys", "files", "summary"],
              [[crew.title, "owner" if crew.self_performed else "sub",
                ", ".join(packages[t].label for t in crew.trades),
                sum(len(packages[t].lines) for t in crew.trades),
                ", ".join(sorted({s for t in crew.trades for s in packages[t].storeys})),
                f"{key}.md, {key}.csv",
                ", ".join(f"{t}-summary.md" for t in crew.trades if t in summaries) or "—"]
               for key, crew in crews.items()]))
