"""Score the working tree against a recorded baseline, and say what moved.

The other half of the loop from ``route_eval``. ``--evaluate`` grades a *proposal* against
an in-memory candidate; this grades the **house as it now stands on disk** — after a person
pasted something, ran ``haus fmt`` and saved — against a snapshot taken before they started.
An agent iterating on a branch needs both: the first says "would this help", the second says
"did it".

**A baseline is a file, not a git operation.** No ``git stash`` (shared across worktrees),
no sandbox copy (it can be torn mid-edit by another session): `haus trial --record` writes
``out/trials/baseline.json`` and the scorecard diffs against that. What the loop does with
git — branch, commit explicit paths, delete the branch — is the person's, and it is spelled
out in the ``route-run`` skill rather than automated here.

**Every tier is recorded and the diff is filtered.** Recording only the MEP set would make a
baseline useless the moment somebody wanted to ask a different question, and re-recording to
change the question would mean re-recording after the edit — which is exactly the mistake
that makes a scorecard lie.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.findings import Finding

#: Where a baseline lives, relative to the house. Under ``out/`` because it is a generated
#: artefact and is regenerated rather than maintained — the same rule ``out/calcs/`` follows.
BASELINE_PATH = Path("out") / "trials" / "baseline.json"

#: The default question: what a route proposal can break. ``all`` restores every check.
#: The same filter ``route_eval`` uses, so "would this help" and "did it" cannot disagree
#: about what counts.
MEP_PREFIXES = ("mep.", "integrity.", "structural.member_interference")

#: What a trial cannot see, whatever the tree says. Printed on every scorecard — including
#: a clean one — because an absent finding reads as a pass, and a loop that iterates on the
#: report is the one reader who cannot recover from that.
KNOWN_GAPS: tuple[str, ...] = (
    "mep.run_interference and mep.run_through_stud ARE graded, and this house "
    "blanket-suppresses both — a trial with suppression on cannot see the open "
    "campaign's score at all. Run --no-suppress to score against it",
    "a proposal's fittings are counted from turns, never modelled — Phase 5",
)


@dataclass
class Scorecard:
    """What changed between a baseline and the tree as it now stands."""

    house: str
    baseline_hash: str = ""
    current_hash: str = ""
    engine: str = ""
    profile: str = ""
    new_fail: list[dict] = field(default_factory=list)
    resolved_fail: list[dict] = field(default_factory=list)
    new_unknown: list[dict] = field(default_factory=list)
    resolved_unknown: list[dict] = field(default_factory=list)
    #: Run-schedule rows for runs that are new or whose geometry digest moved.
    moved_runs: list[dict] = field(default_factory=list)
    #: What is not graded yet, said out loud — an absent finding reads as a pass.
    coverage: list[str] = field(default_factory=lambda: list(KNOWN_GAPS))
    notes: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.new_fail else 0

    def as_dict(self) -> dict:
        return {
            "house": self.house, "baseline_hash": self.baseline_hash,
            "current_hash": self.current_hash, "engine": self.engine,
            "profile": self.profile, "new_fail": self.new_fail,
            "resolved_fail": self.resolved_fail, "new_unknown": self.new_unknown,
            "resolved_unknown": self.resolved_unknown, "moved_runs": self.moved_runs,
            "coverage": self.coverage, "notes": self.notes,
        }


def _key(row: dict) -> tuple:
    """What makes two findings the same finding across two runs.

    The message is in the key deliberately: a check that still FAILs but by a different
    number has told you something, and folding the two into one would hide exactly the
    improvement a loop is looking for.
    """
    return (row.get("check_id"), row.get("result"),
            tuple(sorted(row.get("element_tags") or ())), row.get("message"))


def _row(finding: Finding) -> dict:
    data = finding.model_dump(mode="json")
    return {"check_id": data.get("check_id"), "result": _value(data.get("result")),
            "severity": _value(data.get("severity")),
            "element_tags": list(data.get("element_tags") or ()),
            "message": data.get("message"),
            "code_ref": data.get("code_ref"),
            "authority": _value(data.get("authority"))}


def _value(item: Any) -> Any:
    return item.get("value") if isinstance(item, dict) else item


def _digest(row: dict) -> str:
    """A geometry fingerprint for one run: its path, its elevations and its size.

    Hashed rather than stored so a scorecard says "this run moved" without a reader having
    to diff two coordinate lists — and so a run that was merely re-tagged does not read as
    a move.
    """
    import hashlib

    payload = json.dumps({k: row.get(k) for k in
                          ("path", "z", "size_in", "developed_ft", "storey")},
                         sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def record(directory: Path, *, suppress: bool = True) -> dict:
    """Build the baseline payload for the house as it now stands. Every tier, every run.

    ``suppress=False`` lifts ``[checks] suppress`` for this record alone, the way
    ``checks/run.run`` does. Without it a house working an open campaign — catlin
    blanket-suppresses ``mep.run_interference`` — records *zero* of the very findings the
    loop is trying to move, and a route that made things worse scores clean.

    The flag is written into the payload and :func:`score` refuses a mismatch: a baseline
    taken suppressed and scored unsuppressed reports every suppressed finding as NEW, and
    the reverse reports every one of them as fixed. Both are worse than no scorecard.
    """
    from dataclasses import replace

    from typehaus import engine_version
    from typehaus.checks import build_context, run_checks
    from typehaus.resolve import resolve
    from typehaus.source import load_plan
    from typehaus.takeoff.runs import run_schedule

    loaded = load_plan(directory)
    if loaded.plan is None:
        raise ValueError("the house does not load; there is nothing to record")
    model, _findings = resolve(loaded.plan)
    ctx, _ = build_context(model.plan, directory)
    if not suppress:
        # ctx is freshly built above and belongs to this call, so clearing the field on it
        # cannot reach another reader; `replace` keeps every other preference intact.
        ctx.preferences = replace(ctx.preferences, suppressed=frozenset())
    report = run_checks(ctx)
    return {
        "house": str(directory),
        "content_hash": loaded.content_hash,
        "engine": engine_version(),
        "profile": getattr(ctx.profile, "name", ""),
        "suppress": suppress,
        "findings": [_row(f) for f in report.findings],
        "runs": {row["tag"]: {"digest": _digest(row), "row": row}
                 for row in run_schedule(model)},
    }


def score(directory: Path, baseline: dict, *, checks: str = "mep",
          suppress: bool = True) -> Scorecard:
    """Diff the tree against ``baseline``, filtered to the chosen check set.

    Refuses outright when the baseline was recorded under the other suppression setting.
    A scorecard is a difference of two measurements and two measurements of different
    things do not have one.
    """
    # A baseline written before the flag existed carries no key; it was recorded
    # suppressed, which is what the old `record` did unconditionally.
    was = bool(baseline.get("suppress", True))
    if was != suppress:
        raise ValueError(
            f"the baseline was recorded with suppression {'ON' if was else 'OFF'} and "
            f"this trial is scoring with it {'ON' if suppress else 'OFF'}. Every "
            "suppressed finding would read as new (or as fixed) and the scorecard would "
            "be nonsense — re-record with "
            f"`haus trial {directory} --record"
            f"{'' if suppress else ' --no-suppress'}`")
    current = record(directory, suppress=suppress)
    card = Scorecard(house=str(directory),
                     baseline_hash=baseline.get("content_hash", ""),
                     current_hash=current["content_hash"],
                     engine=current["engine"], profile=current["profile"])

    if baseline.get("engine") != current["engine"]:
        card.notes.append(
            f"the baseline was recorded on engine {baseline.get('engine')!r} and this is "
            f"{current['engine']!r} — a finding that appeared or vanished may be the "
            "engine's doing rather than the edit's. Re-record on a clean tree to be sure")
    if baseline.get("profile") != current["profile"]:
        card.notes.append(f"jurisdiction profile changed: "
                          f"{baseline.get('profile')!r} -> {current['profile']!r}")
    if card.baseline_hash == card.current_hash:
        card.notes.append("no plan file changed since the baseline — every difference "
                          "below, if any, is the engine's")

    keep = (lambda row: True) if checks == "all" else (
        lambda row: str(row.get("check_id", "")).startswith(MEP_PREFIXES)
        or row.get("severity") == "error")
    before = {_key(r): r for r in baseline.get("findings", ()) if keep(r)}
    after = {_key(r): r for r in current["findings"] if keep(r)}

    for key, row in after.items():
        if key in before:
            continue
        (card.new_fail if row["result"] == "fail"
         else card.new_unknown if row["result"] == "unknown" else []).append(row)
    for key, row in before.items():
        if key in after:
            continue
        (card.resolved_fail if row["result"] == "fail"
         else card.resolved_unknown if row["result"] == "unknown" else []).append(row)

    old_runs = baseline.get("runs", {})
    for tag, entry in current["runs"].items():
        was = old_runs.get(tag)
        if was is None or was.get("digest") != entry["digest"]:
            card.moved_runs.append({**entry["row"],
                                    "status": "new" if was is None else "moved"})
    for tag in sorted(set(old_runs) - set(current["runs"])):
        card.moved_runs.append({"tag": tag, "status": "deleted"})

    card.coverage = _coverage(card, suppress=suppress)
    return card


def _coverage(card: Scorecard, *, suppress: bool = True) -> list[str]:
    """What this scorecard cannot see. Stated, because a silent hole reads as a pass.

    The suppression gap is the first line and is dropped under ``--no-suppress`` — it is
    the one entry that a flag actually closes, and leaving it printed there would teach a
    reader to ignore the block.
    """
    out = [g for g in KNOWN_GAPS if suppress or "suppress" not in g]
    if card.moved_runs and not (card.new_fail or card.new_unknown):
        out.append("runs moved and no MEP finding changed, which may mean the move is "
                   "clean or may mean nothing grades it — check the two lines above")
    return out


def load_baseline(directory: Path) -> dict | None:
    path = directory / BASELINE_PATH
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def write_baseline(directory: Path, payload: dict) -> Path:
    path = directory / BASELINE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    # Temp file + replace, the same write path `schedule/site_ops` uses: a baseline half
    # written by an interrupted run would score every later trial against nonsense.
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    import os

    os.replace(temp, path)
    return path


def render(card: Scorecard) -> list[str]:
    """The scorecard as console lines."""
    lines = [f"[bold]trial {card.house}[/bold]  "
             f"engine {card.engine}, profile {card.profile or '—'}"]
    for note in card.notes:
        lines.append(f"  [dim]{note}[/dim]")
    for label, rows, colour in (("NEW FAIL", card.new_fail, "red"),
                                ("NEW UNKNOWN", card.new_unknown, "yellow"),
                                ("RESOLVED FAIL", card.resolved_fail, "green"),
                                ("RESOLVED UNKNOWN", card.resolved_unknown, "green")):
        for row in rows:
            lines.append(f"  [{colour}]{label} {row['check_id']}: "
                         f"{row['message']}[/{colour}]")
    if not (card.new_fail or card.new_unknown or card.resolved_fail
            or card.resolved_unknown):
        lines.append("  [green]no finding changed in the chosen set[/green]")
    for row in card.moved_runs:
        detail = (f"{row.get('developed_ft', 0):.1f} LF developed"
                  if "developed_ft" in row else "")
        lines.append(f"  [cyan]{row['status'].upper():<8}{row['tag']:<28}{detail}[/cyan]")
    for note in card.coverage:
        lines.append(f"  [yellow]not graded: {note}[/yellow]")
    return lines
