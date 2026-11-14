"""The bounded decision view behind ``haus route --json --summary``.

Built from the report dict alone, so it reads the same whether the rows came from
``proposals`` or ``accepted``. Full messages stay in ``report.json``; every finding here
carries a JSON pointer into it. Shape: docs/routing.md."""

from __future__ import annotations

from collections import Counter
from typing import Any

from typehaus.cli.route_check_groups import CONSTRUCTION_CHECKS, group_of

_CAP = 10          # items kept in any list
_TEXT = 160        # characters kept of any reason or note
_FINDINGS = 3      # representative findings per grade
_UNPLACED = "no station within"   # route_cleanouts' note for a requirement it could not place


def bore_counts(model: Any, proposal: Any) -> dict[str, int]:
    """Members the proposal passes through, by kind (``route_check_groups.bores``)."""
    if not hasattr(model, "walls"):
        return {}
    from typehaus.cli.route_check_groups import bores

    return dict(sorted(bores(model, [proposal]).items()))


def _text(value: Any) -> str:
    text = str(value)
    return text if len(text) <= _TEXT else text[:_TEXT - 1] + "…"


def _listing(items: list, cap: int = _CAP) -> dict:
    return {"count": len(items), "items": items[:cap]}


def _by_group(findings: list[dict], result: str) -> dict[str, int]:
    return dict(sorted(Counter(group_of(f["check_id"]) for f in findings
                               if f["result"] == result).items()))


def _tally(pairs: list[tuple[str, str, str]], cap: int = 5) -> list[dict]:
    """``(tag, kind, mobility)`` triples as ``{tag, kind, mobility, count}``, commonest first."""
    counts = Counter(pairs)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:cap]
    return [{"tag": tag, "kind": kind, "mobility": mobility, "count": n}
            for (tag, kind, mobility), n in ranked]


def _representative(introduced: list[dict], ptr: str) -> list[dict]:
    """Up to three findings: FAILs before UNKNOWNs, construction checks first, one per check."""
    ranked = sorted(
        (i for i, f in enumerate(introduced) if f["result"] in ("fail", "unknown")),
        key=lambda i: (introduced[i]["result"] != "fail",
                       introduced[i]["check_id"] not in CONSTRUCTION_CHECKS, i))
    first = {introduced[i]["check_id"]: i for i in reversed(ranked)}
    picked = sorted(first.values(), key=ranked.index)[:_FINDINGS]
    picked += [i for i in ranked if i not in picked][:_FINDINGS - len(picked)]
    return [{"ptr": f"{ptr}/introduced/{i}", "check_id": introduced[i]["check_id"],
             "result": introduced[i]["result"], "group": group_of(introduced[i]["check_id"]),
             "message": _text(introduced[i]["message"])} for i in picked]


def grade(evaluation: dict | None, ptr: str, own: set[str],
          mobility: dict[str, str]) -> dict:
    """What the evaluation says: status, FAIL/UNKNOWN by check group, clash tags (with the
    mobility a refusal recorded for the same tag, else ``unknown``)."""
    if evaluation is None:
        return {"status": "ungraded"}
    introduced = evaluation["introduced"]
    clashes = Counter(part for f in introduced if f["result"] == "fail"
                      for tag in f["element_tags"] for part in map(str.strip, tag.split(" + "))
                      if part not in own)
    return {
        "status": "refused" if evaluation["refused"] else "evaluated",
        "reason": _text(evaluation["refused"]) if evaluation["refused"] else None,
        "report_ptr": ptr,
        "fail": _by_group(introduced, "fail"), "unknown": _by_group(introduced, "unknown"),
        "advisory": sum(f["result"] == "advisory" for f in introduced),
        "resolved": len(evaluation["resolved"]),
        "coverage_gaps": _listing([_text(gap) for gap in evaluation["coverage"]], 3),
        "clash_tags": [{"tag": tag, "mobility": mobility.get(tag, "unknown"), "count": n}
                       for tag, n in sorted(clashes.items(), key=lambda kv: (-kv[1], kv[0]))[:5]],
        "findings": _representative(introduced, ptr),
    }


def _metrics(row: dict, ptr: str) -> dict:
    placed = len(row["cleanouts"])
    unplaced = sum(_UNPLACED in note for note in row["notes"] if note.startswith("cleanout ("))
    return {
        "tag": row["tag"], "storey": row.get("storey"), "kind": row["kind"],
        "system": row["system"], "report_ptr": ptr,
        "developed_ft": row["developed_ft"], "bends": row["bends"],
        "cost_in_equivalent": row["cost_in_equivalent"],
        "fittings": {"count": len(row["fittings"]),
                     "gaps": sum(f["catalog"] is None or bool(f["gap"])
                                 for f in row["fittings"])},
        "bores": {**row.get("bores", {}), "total": sum(row.get("bores", {}).values())},
        "cleanouts": {"placed": placed, "required": placed + unplaced},
        "notes": len(row["notes"]),
        "after_paste": _listing([_text(note) for note in row["after_paste"]], 5),
    }


def _refusals(report: dict) -> tuple[list[dict], dict[str, str]]:
    """Per refused target: where it is walled in and by what, blockers grouped by tag/mobility."""
    out, mobility = [], {}
    for item in report.get("refusals", ()):
        blockers = item.get("blockers", ())
        mobility.update({b["tag"]: b["mobility"] for b in blockers})
        out.append({
            "target": item["target"], "service": item.get("service"), "end": item.get("end"),
            "reachable_nodes": item.get("reachable_nodes"),
            "total_nodes": item.get("total_nodes"),
            "by_mobility": dict(sorted(Counter(b["mobility"] for b in blockers).items())),
            "blockers": _tally([(b["tag"], b["kind"], b["mobility"]) for b in blockers]),
            "before_search": _text(item["before_search"]) if item.get("before_search") else None,
        })
    return out, mobility


def decision_view(report: dict) -> dict:
    """The bounded decision view: completion, one entry per candidate, the network grade."""
    key = "accepted" if "accepted" in report else "proposals"
    rows = report[key]
    evaluations = report.get("evaluations", [])
    network = next((i for i, e in enumerate(evaluations) if e["tag"] == "campaign"), None)
    by_tag: dict[str, int] = {}
    for i, evaluation in enumerate(evaluations):
        if i != network:
            by_tag.update({tag: i for tag in evaluation["tag"].split(" + ")})

    refusals, mobility = _refusals(report)
    candidates = []
    for i, row in enumerate(rows):
        candidate = _metrics(row, f"/{key}/{i}")
        j = by_tag.get(row["tag"])
        candidate["grade"] = (
            grade(evaluations[j], f"/evaluations/{j}", {row["tag"]}, mobility)
            if j is not None else None)
        candidates.append(candidate)

    refused = report.get("refused") or [
        {"tag": r["target"], "reason": r["before_search"] or "no route found"} for r in refusals]

    def trimmed(items: Any) -> dict:
        return _listing([{"tag": i["tag"], "reason": _text(i["reason"])} for i in items])

    own = {row["tag"] for row in rows}
    return {
        "mode": "network" if network is not None else "candidates",
        "completion": {
            "termination": report.get("termination"),
            "refused": trimmed(refused),
            "skipped": trimmed(report.get("skipped", ())),
            "refusals": _listing(refusals),
            "problems": _listing([_text(p) for p in report.get("problems", ())], 5),
            "notices": len(report.get("notices", ())),
        },
        "candidates": _listing(candidates, 20),
        "network": (grade(evaluations[network], f"/evaluations/{network}", own, mobility)
                    if network is not None else None),
        **({"orders_tried": report["orders_tried"][:_CAP]} if "orders_tried" in report else {}),
    }
