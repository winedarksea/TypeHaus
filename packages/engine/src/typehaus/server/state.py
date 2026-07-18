"""Server session state — one resolved project + its mutation coordinator (→ 20 §Server).

Holds the loaded plan, the resolved model, and the :class:`ProjectCoordinator` that owns
write safety + the undo journal. ``rebuild`` is the single re-resolve path shared by patches,
undo/redo, and watcher-triggered external edits, so the UI and disk never disagree.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from typehaus.checks import load_preferences
from typehaus.findings import Finding, Severity
from typehaus.resolve import resolve
from typehaus.resolve.model import ResolvedModel
from typehaus.server.model_json import model_to_dict
from typehaus.source import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.provenance import Provenance


@dataclass
class ProjectState:
    house_dir: Path
    coordinator: ProjectCoordinator
    model: ResolvedModel | None = None
    provenance: Provenance = field(default_factory=Provenance)
    findings: list[Finding] = field(default_factory=list)
    ok: bool = False
    _lock: threading.RLock = field(default_factory=threading.RLock)

    @classmethod
    def open(cls, house_dir: Path) -> ProjectState:
        house_dir = house_dir.resolve()
        state = cls(house_dir=house_dir, coordinator=ProjectCoordinator(house_dir))
        state.rebuild()
        return state

    def rebuild(self) -> None:
        """Reload plan source, re-resolve, and refresh findings (the shared rebuild path)."""
        with self._lock:
            result = load_plan(self.house_dir)
            self.provenance = result.provenance
            self.findings = list(result.findings)
            if result.plan is None:
                self.model = None
                self.ok = False
                return
            model, rfindings = resolve(result.plan)
            # The dashboard and `/checks` use the same registry as `haus check`, including
            # M5's building-science warnings; never maintain a second server-only rule path.
            from typehaus.checks import run_from_model

            report = run_from_model(model, rfindings, self.house_dir)
            self.findings.extend(report.findings)
            self.model = model
            self.ok = not any(f.severity is Severity.ERROR for f in self.findings)

    def model_json(self) -> dict[str, Any]:
        with self._lock:
            if self.model is None:
                return {
                    "revision": self.coordinator.revision(),
                    "units": "imperial", "projectNorth": 0.0,
                    "findings": [f.model_dump(mode="json") for f in self.findings],
                    "ok": False,
                }
            payload = model_to_dict(
                self.model,
                revision=self.coordinator.revision(),
                provenance=self.provenance,
                findings=self.findings,
                preferences=load_preferences(self.house_dir),
            )
            payload["ok"] = self.ok
            return payload

    def findings_json(self) -> list[dict[str, Any]]:
        with self._lock:
            return [f.model_dump(mode="json") for f in self.findings]
