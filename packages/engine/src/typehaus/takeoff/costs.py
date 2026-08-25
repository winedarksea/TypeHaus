"""Cost tracking state (``costs.toml``) — what was actually bought, beside the estimate.

``prices.toml`` says what a unit *should* cost; nothing recorded what a line actually cost,
whether it has been paid, or which exact product was bought — that lived in a spreadsheet
beside the repo, drifting from the BOM it described. This module is that record, durable in
the house directory and versioned with the plan:

* **entries** — per-BOM-line state, keyed ``(section, price_key)`` with exactly the join
  :func:`typehaus.cli.prices.estimate_costs` uses (``ESTIMATE_PLANS``), so a paid check-off
  points at the same row the estimate prices. A BOM row that later disappears (the plan
  changed) leaves its entry *stale* — surfaced by :func:`costs_payload`, never dropped.
* **extra** — real spend that is on no estimate line at all, so the running total is the
  project's rather than just the modelled material's.

  Its scope NARROWED on 2026-08-20 and the old examples here were stale within a day. Permit
  fees, the dumpster and site delivery used to be the canonical ``extra`` — they are now
  ``[allowances]`` rows in ``prices.toml``, which means they are estimated, cost-coded,
  scheduled by trade, and joined here like any other line. Checking one off as ``extra`` today
  would double it against its own allowance.

  What still belongs in ``extra`` is spend nobody forecast in any form: the change order, the
  replacement for the thing that was damaged, the trip charge for the second visit. If a cost
  is foreseeable, it wants an allowance; ``extra`` is for the ones that were not.

Deliberately outside the PatchOp/undo journal: paying a bill is not a plan edit, and
un-paying one by pressing undo would be a lie about the bank account.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping, Optional

try:  # tomllib is stdlib on 3.11+; the engine still supports 3.9
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on <3.11 only
    import tomli as tomllib  # type: ignore[no-redef]

from typehaus.cli.prices import (ESTIMATE_PLANS, EXCLUDED_FROM_TOTAL, PriceRange, Prices,
                                 ZERO, estimate_costs)

COSTS_FILENAME = "costs.toml"

#: The section names an entry may be filed under: the estimate sections plus ``extra``
#: (which is not an entries section but shares the validation message).
_ENTRY_SECTIONS = frozenset(name for name, *_ in ESTIMATE_PLANS)


@dataclass(frozen=True)
class CostEntry:
    """The owner's state for one BOM line. All fields optional — an entry exists because
    at least one of them is set; clearing every field deletes it (→ ``apply_costs_op``)."""

    paid: bool = False
    paid_date: Optional[str] = None      # "YYYY-MM-DD" prose, not validated as a date
    # The exact product BOUGHT — a SKU, a listing, whatever identifies the box that
    # arrived. Worth writing when it DIFFERS from what the plan specified: the estimate row
    # now carries the specification itself (``product_labels``), so re-typing it here would
    # be a second copy of a fact the model already holds, and the two would drift.
    product: Optional[str] = None
    actual_cost: Optional[float] = None  # what it really cost, once known
    note: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        return not (self.paid or self.paid_date or self.product
                    or self.actual_cost is not None or self.note)

    def as_dict(self) -> dict:
        return {"paid": self.paid, "paid_date": self.paid_date, "product": self.product,
                "actual_cost": self.actual_cost, "note": self.note}


@dataclass(frozen=True)
class ExtraItem:
    """A non-modelled line item: money the project spends that no takeoff row bills."""

    id: str
    name: str
    cost: Optional[PriceRange] = None
    paid: bool = False
    product: Optional[str] = None
    category: Optional[str] = None
    note: Optional[str] = None

    def as_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "cost": self.cost.as_dict() if self.cost is not None else None,
                "paid": self.paid, "product": self.product, "category": self.category,
                "note": self.note}


@dataclass(frozen=True)
class CostsState:
    entries: Mapping[str, Mapping[str, CostEntry]] = field(default_factory=dict)
    extra: tuple[ExtraItem, ...] = ()


# --- load ---------------------------------------------------------------------------------

def _cost_value(raw: Any, where: str) -> Optional[PriceRange]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        value = float(raw)
        if value < 0:
            raise ValueError(f"{where}: cost is negative")
        return PriceRange(value, value)
    if isinstance(raw, dict) and set(raw) == {"low", "high"}:
        low, high = float(raw["low"]), float(raw["high"])
        if low < 0 or high < low:
            raise ValueError(f"{where}: cost needs 0 <= low <= high")
        return PriceRange(low, high)
    raise ValueError(f"{where}: cost must be a number or {{ low = ..., high = ... }}")


def _entry(section: str, key: str, raw: Any, path: Path) -> CostEntry:
    where = f"{path}: [entries.{section}.{key!r}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    known = {"paid", "paid_date", "product", "actual_cost", "note"}
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}")
    actual = raw.get("actual_cost")
    if actual is not None and (isinstance(actual, bool)
                               or not isinstance(actual, (int, float)) or actual < 0):
        raise ValueError(f"{where}: actual_cost must be a non-negative number")
    paid_date = raw.get("paid_date")  # tomllib parses an unquoted date as datetime.date
    return CostEntry(paid=bool(raw.get("paid", False)),
                     paid_date=str(paid_date) if paid_date else None,
                     product=str(raw["product"]) if raw.get("product") else None,
                     actual_cost=float(actual) if actual is not None else None,
                     note=str(raw["note"]) if raw.get("note") else None)


def _extra(index: int, raw: Any, path: Path) -> ExtraItem:
    where = f"{path}: [[extra]] #{index + 1}"
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    known = {"id", "name", "cost", "paid", "product", "category", "note"}
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}")
    if not raw.get("id") or not raw.get("name"):
        raise ValueError(f"{where}: 'id' and 'name' are required")
    return ExtraItem(id=str(raw["id"]), name=str(raw["name"]),
                     cost=_cost_value(raw.get("cost"), where),
                     paid=bool(raw.get("paid", False)),
                     product=raw.get("product") or None,
                     category=raw.get("category") or None,
                     note=raw.get("note") or None)


def load_costs(house_dir: Path) -> CostsState:
    """Read ``costs.toml`` if the house carries one; an absent file is an empty state.

    A *malformed* file raises ``ValueError`` naming the offending key — a mistyped section
    must never silently become an ignored check-off.
    """
    path = Path(house_dir) / COSTS_FILENAME
    if not path.exists():
        return CostsState()
    data = tomllib.loads(path.read_text())
    unknown = set(data) - {"entries", "extra"}
    if unknown:
        raise ValueError(f"{path}: unknown top-level key(s) {sorted(unknown)}; "
                         "expected [entries.<section>.<key>] tables and [[extra]] items")
    entries_raw = data.get("entries") or {}
    if not isinstance(entries_raw, dict):
        raise ValueError(f"{path}: 'entries' must be a table of sections")
    entries: dict[str, dict[str, CostEntry]] = {}
    for section, keys in entries_raw.items():
        if section not in _ENTRY_SECTIONS:
            raise ValueError(f"{path}: unknown entries section {section!r}; "
                             f"expected one of {sorted(_ENTRY_SECTIONS)}")
        if not isinstance(keys, dict):
            raise ValueError(f"{path}: [entries.{section}] must be a table of keys")
        section_entries = {str(key): _entry(section, str(key), raw, path)
                           for key, raw in keys.items()}
        if section_entries:
            entries[section] = section_entries
    extras_raw = data.get("extra") or []
    if not isinstance(extras_raw, list):
        raise ValueError(f"{path}: 'extra' must be an array of tables ([[extra]])")
    extra = tuple(_extra(i, raw, path) for i, raw in enumerate(extras_raw))
    ids = [item.id for item in extra]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{path}: duplicate extra id(s): "
                         f"{sorted({i for i in ids if ids.count(i) > 1})}")
    return CostsState(entries=entries, extra=extra)


# --- write --------------------------------------------------------------------------------

def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return f"{value:g}"
    if isinstance(value, PriceRange):
        return ("{ low = %s, high = %s }" % (f"{value.low:g}", f"{value.high:g}")
                if not value.is_exact else f"{value.low:g}")
    return json.dumps(str(value))  # JSON string escaping is valid TOML basic-string


def write_costs(house_dir: Path, state: CostsState) -> Path:
    """Serialize deterministically: sorted sections/keys, extras in list order, one field
    per line — so a diff of ``costs.toml`` reads as exactly the check-offs that changed."""
    lines = ["# costs.toml — cost tracking (written by Type:Haus; safe to edit by hand).",
             "# [entries.<section>.<key>]: paid / paid_date / product / actual_cost / note",
             "# for the BOM row `estimate_costs` joins as (section, key). `product` is the",
             "# AS-BOUGHT record: write it when it differs from the product the plan",
             "# specifies, which the estimate row already carries (takeoff/product_labels).",
             "# [[extra]]: id / name / cost / paid / product / category / note for spend",
             "# the model does not bill.", ""]
    for section in sorted(state.entries):
        for key in sorted(state.entries[section]):
            entry = state.entries[section][key]
            if entry.is_empty:
                continue
            lines.append(f"[entries.{section}.{json.dumps(key)}]")
            for name, value in (("paid", entry.paid), ("paid_date", entry.paid_date),
                                ("product", entry.product),
                                ("actual_cost", entry.actual_cost), ("note", entry.note)):
                # `paid` is written only when true; every other field only when set.
                # (`value is not False` matters: an actual_cost of 0.0 == False and a
                # membership test would silently drop a recorded freebie.)
                if value is not None and value is not False:
                    lines.append(f"{name} = {_toml_value(value)}")
            lines.append("")
    for item in state.extra:
        lines.append("[[extra]]")
        for name, value in (("id", item.id), ("name", item.name), ("cost", item.cost),
                            ("paid", item.paid), ("product", item.product),
                            ("category", item.category), ("note", item.note)):
            if value is not None and value is not False:
                lines.append(f"{name} = {_toml_value(value)}")
        lines.append("")
    path = Path(house_dir) / COSTS_FILENAME
    path.write_text("\n".join(lines).rstrip("\n") + "\n")
    return path


# --- ops ----------------------------------------------------------------------------------

def _slug(name: str, taken: set) -> str:
    base = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-") or "item"
    slug, n = base, 2
    while slug in taken:
        slug, n = f"{base}-{n}", n + 1
    return slug


def apply_costs_op(state: CostsState, op: Mapping[str, Any]) -> CostsState:
    """One state transition. Raises ``ValueError`` on a malformed op — the server maps
    that to a 400 rather than persisting garbage."""
    kind = op.get("op")
    if kind == "set_entry":
        section, key = op.get("section"), op.get("key")
        if section not in _ENTRY_SECTIONS:
            raise ValueError(f"set_entry: unknown section {section!r}")
        if not key:
            raise ValueError("set_entry: 'key' is required")
        raw = op.get("entry")
        if not isinstance(raw, dict):
            raise ValueError("set_entry: 'entry' must be an object")
        entry = _entry(str(section), str(key), raw, Path("<op>"))
        entries = {s: dict(keys) for s, keys in state.entries.items()}
        if entry.is_empty:  # clearing every field deletes the entry
            entries.get(section, {}).pop(str(key), None)
            if section in entries and not entries[section]:
                del entries[section]
        else:
            entries.setdefault(str(section), {})[str(key)] = entry
        return replace(state, entries=entries)
    if kind == "set_extra":
        raw = op.get("item")
        if not isinstance(raw, dict):
            raise ValueError("set_extra: 'item' must be an object")
        raw = dict(raw)
        if not raw.get("id"):
            raw["id"] = _slug(str(raw.get("name") or ""), {i.id for i in state.extra})
        item = _extra(len(state.extra), raw, Path("<op>"))
        extra = list(state.extra)
        for index, existing in enumerate(extra):
            if existing.id == item.id:
                extra[index] = item
                break
        else:
            extra.append(item)
        return replace(state, extra=tuple(extra))
    if kind == "delete_extra":
        target = op.get("id")
        if not target:
            raise ValueError("delete_extra: 'id' is required")
        if not any(item.id == target for item in state.extra):
            raise ValueError(f"delete_extra: no extra item {target!r}")
        return replace(state, extra=tuple(i for i in state.extra if i.id != target))
    raise ValueError(f"unknown costs op {kind!r} "
                     "(expected set_entry | set_extra | delete_extra)")


# --- payload ------------------------------------------------------------------------------

def costs_payload(bom: dict, prices: Optional[Prices], state: CostsState,
                  areas: Optional[Mapping[str, float]] = None,
                  products: Optional[Mapping[tuple[str, str], str]] = None) -> dict:
    """Everything the costs view needs in one JSON-ready dict.

    ``join`` tells the client how each estimate section maps onto BOM rows (bom key, key
    field, quantity field, unit) — authored once in ``ESTIMATE_PLANS`` so the client never
    re-guesses the join. ``stale`` lists entries whose ``(section, key)`` matches no
    current BOM row: the plan moved on under a check-off, which is a fact the owner must
    see, never silently discard.

    ``areas`` is the $/sf denominator pair (``conditioned`` / ``gross``, from
    ``server/space_summary.build_space_summary``), passed straight through to
    :func:`typehaus.cli.prices.estimate_costs`. Optional because a caller that has no
    resolved model has no honest denominator, and $/sf against a guessed area is worse
    than no $/sf at all — omitted, never zero.

    ``products`` is the *specified* product per ``(section, key)``
    (:func:`typehaus.takeoff.product_labels.product_labels`), which the estimate rows carry
    as a label. It is what makes ``CostEntry.product`` an **as-bought** record rather than a
    second, unchecked copy of the specification: the view can show what was specified, so
    the estimator only writes down what differed.
    """
    estimate = estimate_costs(bom, prices, areas, products) if prices is not None else None
    join = {name: {"bom_key": bom_key, "key_field": key_field,
                   "quantity_field": quantity_field, "unit": unit,
                   # False for a section reported beside the construction total
                   # (furnishings). Two sections may share a bom_key, so a client that
                   # maps bom_key -> section has to keep both, not the last one written.
                   "in_total": name not in EXCLUDED_FROM_TOTAL}
            for name, bom_key, key_field, quantity_field, unit in ESTIMATE_PLANS}
    stale: list[dict] = []
    for section in sorted(state.entries):
        plan = join[section]
        row_keys = {str(row.get(plan["key_field"]))
                    for row in (bom.get(plan["bom_key"]) or [])}
        for key in sorted(state.entries[section]):
            if key not in row_keys:
                stale.append({"section": section, "key": key})

    extra_total = ZERO
    extra_paid = ZERO
    for item in state.extra:
        if item.cost is None:
            continue
        extra_total = extra_total.plus(item.cost)
        if item.paid:
            extra_paid = extra_paid.plus(item.cost)
    actual_paid = sum(entry.actual_cost or 0.0
                      for keys in state.entries.values()
                      for entry in keys.values() if entry.paid)
    paid_count = sum(1 for keys in state.entries.values()
                     for entry in keys.values() if entry.paid)
    totals: dict[str, Any] = {
        "extra": extra_total.as_dict(), "extra_fmt": extra_total.fmt(),
        "extra_paid": extra_paid.as_dict(),
        # Actual dollars recorded against paid BOM lines (entries without an actual_cost
        # contribute nothing — an unknown price must not read as $0 spent).
        "actual_paid": round(actual_paid, 2),
        "paid_entries": paid_count,
    }
    if estimate is not None:
        combined = PriceRange(estimate["total"]["low"],
                              estimate["total"]["high"]).plus(extra_total)
        totals["estimate"] = estimate["total"]
        totals["combined"] = combined.as_dict()
        totals["combined_fmt"] = combined.fmt()
        # Beside, not inside: `combined` stays the build number. A reader who wants the
        # one-number version adds this to it.
        totals["excluded"] = estimate["excluded_total"]
        totals["excluded_fmt"] = estimate["excluded_total_fmt"]
    return {
        "prices_loaded": prices is not None,
        "estimate": estimate,
        "join": join,
        "entries": {section: {key: entry.as_dict() for key, entry in keys.items()}
                    for section, keys in state.entries.items()},
        "extra": [item.as_dict() for item in state.extra],
        "stale": stale,
        "totals": totals,
    }


__all__ = ["COSTS_FILENAME", "CostEntry", "ExtraItem", "CostsState", "load_costs",
           "write_costs", "apply_costs_op", "costs_payload"]
