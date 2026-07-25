"""Assembly delta compare (#53, → 21b §Variant compare) — the "perfecting" surface.

Pick two or three assemblies (any mix of plan, ``library/`` and variant declarations) and
see what choosing one over another actually costs: R-value, built thickness, layer count,
framing member + spacing, STC when the assembly carries a lab test. The first assembly named
is the baseline every other is measured against, so the delta row reads the way the question
is asked ("is the double-stud wall worth 4¾″ of hallway over resilient channel?").

Model-free by construction: it reads authored ``Assembly`` definitions through
:func:`typehaus.analysis.assembly_metrics`, so it needs no resolve and serves the CLI, the
inspector card, and the compare sheet from one computation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from typehaus.analysis import AssemblyMetrics, assembly_metrics
from typehaus.model.plan import Library

# Metrics the delta row carries, in the order a designer reads them. Each entry is
# (metric key, unit label) — the renderer never hardcodes this list.
DELTA_METRICS: tuple[tuple[str, str], ...] = (
    ("r_value", "R"),
    ("thickness_in", "in"),
    ("layer_count", "layers"),
    ("stc", "STC"),
)


@dataclass(frozen=True)
class MetricDelta:
    """One metric of one candidate assembly, against the baseline assembly."""

    metric: str
    unit: str
    baseline: float | None      # None => UNKNOWN on the baseline side (#32)
    candidate: float | None

    @property
    def delta(self) -> float | None:
        if self.baseline is None or self.candidate is None:
            return None
        return round(self.candidate - self.baseline, 4)

    def as_dict(self) -> dict:
        return {"metric": self.metric, "unit": self.unit, "baseline": self.baseline,
                "candidate": self.candidate, "delta": self.delta}


@dataclass
class AssemblyComparison:
    """Side-by-side metrics for 2–3 assemblies plus each candidate's delta row."""

    metrics: list[AssemblyMetrics] = field(default_factory=list)
    deltas: dict[str, list[MetricDelta]] = field(default_factory=dict)

    @property
    def baseline_tag(self) -> str:
        return self.metrics[0].tag

    def as_dict(self) -> dict:
        return {
            "baseline": self.baseline_tag,
            "assemblies": [item.as_dict() for item in self.metrics],
            "deltas": {tag: [d.as_dict() for d in rows] for tag, rows in self.deltas.items()},
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())
        return path


def _metric_value(metrics: AssemblyMetrics, key: str) -> float | None:
    if key == "r_value":
        return round(metrics.r_value.value.r_us, 3) if metrics.r_value.known else None
    if key == "thickness_in":
        return round(metrics.thickness_in, 4)
    if key == "layer_count":
        return float(metrics.layer_count)
    if key == "stc":
        return float(metrics.stc) if metrics.stc is not None else None
    raise KeyError(f"unknown assembly metric {key!r}")


def compare_assemblies(library: Library, tags: list[str]) -> AssemblyComparison:
    """Compare 2+ assemblies of one library; the first tag is the baseline.

    Variants resolve against their base (``Library.resolve_assembly``) so a fork compares as
    the wall it would actually build, not as its substitution list.
    """
    if len(tags) < 2:
        raise ValueError("assembly compare needs at least two assembly tags")
    resolved = []
    for tag in tags:
        asm = library.resolve_assembly(tag)
        if asm is None:
            raise ValueError(f"no assembly {tag!r} in this plan's library")
        resolved.append(assembly_metrics(asm, library))

    comparison = AssemblyComparison(metrics=resolved)
    baseline = resolved[0]
    for candidate in resolved[1:]:
        comparison.deltas[candidate.tag] = [
            MetricDelta(metric=key, unit=unit,
                        baseline=_metric_value(baseline, key),
                        candidate=_metric_value(candidate, key))
            for key, unit in DELTA_METRICS
        ]
    return comparison
