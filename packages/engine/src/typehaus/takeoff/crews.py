"""Crews: which trades one sub bids together, and which the owner does (decision #115).

A trade (``emit/trades.py``) is the smallest scope *some* house bids alone. Which trades a
particular build hands one sub — roofing, siding and gutters to one envelope crew — and
which the owner does is that house's judgement, authored in ``tasks.toml`` as
``[crews.<key>]``. A trade no crew names is its own crew, the way a package nobody splits
is one implicit visit. ``haus bids`` writes one request for quote per crew, and a
``self_performed`` crew's package is the owner's materials list instead.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from typehaus.emit.trades import TRADE_LABELS, TRADES, sequence_rank

CREW_FIELDS = ("label", "trades", "self_performed", "note")


@dataclass(frozen=True)
class Crew:
    key: str
    trades: tuple[str, ...]
    label: str | None = None
    #: The owner does it: no RFQ goes out, the package is a materials list.
    self_performed: bool = False
    note: str | None = None
    #: No ``[crews]`` entry names the trade; the crew is the trade alone.
    implicit: bool = False

    @property
    def title(self) -> str:
        return self.label or " + ".join(TRADE_LABELS.get(t, t) for t in self.trades)

    def as_dict(self) -> dict[str, Any]:
        return {"key": self.key, "title": self.title, "trades": list(self.trades),
                "self_performed": self.self_performed, "implicit": self.implicit,
                "note": self.note}


def load_crews(raw: Any, path: Path) -> dict[str, Crew]:
    """``[crews.<key>]``. Raises on an unknown field or trade, and on a trade two crews
    claim: one row is in one package, so it cannot be bid twice."""
    if not raw:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: 'crews' must be a table of keys")
    out: dict[str, Crew] = {}
    owner: dict[str, str] = {}
    for key, body in raw.items():
        where = f"{path}: [crews.{key}]"
        if not isinstance(body, dict):
            raise ValueError(f"{where} must be a table")
        unknown = set(body) - set(CREW_FIELDS)
        if unknown:
            raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                             f"expected {list(CREW_FIELDS)}")
        trades = tuple(str(t) for t in (body.get("trades") or ()))
        if not trades:
            raise ValueError(f"{where}: missing 'trades'")
        bad = sorted(set(trades) - TRADES)
        if bad:
            raise ValueError(f"{where}: unknown trade(s) {bad}; one of {sorted(TRADES)}")
        for trade in trades:
            if trade in owner:
                raise ValueError(f"{where}: {trade!r} is already in [crews.{owner[trade]}]")
            owner[trade] = str(key)
        out[str(key)] = Crew(key=str(key), trades=tuple(sorted(trades, key=sequence_rank)),
                             label=str(body["label"]) if body.get("label") else None,
                             self_performed=bool(body.get("self_performed", False)),
                             note=str(body["note"]) if body.get("note") else None)
    for key in out:
        if key in TRADES and key not in out[key].trades:
            raise ValueError(f"{path}: [crews.{key}] is named for a trade it does not hold, "
                             "so that trade's own crew would collide with it")
    return out


def crew_lines(crews: Mapping[str, Crew]) -> list[str]:
    """``write_tasks``' half: sorted, one field per line, defaults dropped."""
    from typehaus.takeoff.visit_state import toml_string

    lines: list[str] = []
    for key in sorted(crews):
        crew = crews[key]
        lines.append(f"[crews.{toml_string(key)}]")
        if crew.label:
            lines.append(f"label = {toml_string(crew.label)}")
        lines.append("trades = [" + ", ".join(toml_string(t) for t in crew.trades) + "]")
        if crew.self_performed:
            lines.append("self_performed = true")
        if crew.note:
            lines.append(f"note = {toml_string(crew.note)}")
        lines.append("")
    return lines


def crews_for(trades: Iterable[str], authored: Mapping[str, Crew]) -> dict[str, Crew]:
    """``key -> Crew`` for every crew holding one of ``trades``, in the construction order
    of its first trade present. Each crew's ``trades`` is narrowed to those present."""
    present = set(trades)
    claimed = {t: crew for crew in authored.values() for t in crew.trades}
    out: dict[str, Crew] = {}
    for trade in sorted(present, key=sequence_rank):
        crew = claimed.get(trade)
        if crew is None:
            out[trade] = Crew(key=trade, trades=(trade,), implicit=True)
        elif crew.key not in out:
            out[crew.key] = Crew(key=crew.key, trades=tuple(t for t in crew.trades
                                                            if t in present),
                                 label=crew.label, self_performed=crew.self_performed,
                                 note=crew.note)
    return out
