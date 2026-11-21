"""Trim-to-wood fasteners off ``Material.trim_fastening`` (decision #147).

Per billed run of a material that authors one: ``(ceil(length / pitch) + 1) x rows`` — a
fastener at each end and every pitch between, ``rows`` across the board. The runs are the
edge-trim fascia, soffit and corner runs and the interior base and casing pieces.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from typehaus.hardware.catalog import hardware_by_model
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.edge_trim import edge_trim_runs
from typehaus.takeoff.hardware_row import hardware_row

#: Edge-trim categories fixed to wood along their length.
_EDGE_CATEGORIES = frozenset({"fascia", "soffit", "corner_trim"})


def fasteners_per_run(length_m: float, pitch_in: float, rows: int = 1) -> int:
    """One at each end and every ``pitch_in`` between, ``rows`` across."""
    return (math.ceil(length_m / (pitch_in * M_PER_IN) - 1e-9) + 1) * rows


def _runs(model: ResolvedModel):
    """(material, storey, length_m, what) for every run this module counts."""
    for run in edge_trim_runs(model):
        if run["category"] in _EDGE_CATEGORIES:
            length_m = float(run["length_m"])  # type: ignore[arg-type]
            yield str(run["material"]), str(run["storey"]), length_m, str(run["category"])
    for base in model.base_runs:
        if base.kind == "trim":
            yield base.material_ref, base.storey, base.length_m, "base"
    for casing in model.door_casings:
        for piece in casing.pieces:
            yield casing.material_ref, casing.storey, piece.length_m, "casing"


def trim_fastener_rows(model: ResolvedModel) -> list:
    """One row per fastener model, by storey, with each material's rule in the basis."""
    specs = {m.tag: m.trim_fastening for m in model.plan.library.materials
             if m.trim_fastening is not None}
    if not specs:
        return []
    counts: dict[str, Counter] = defaultdict(Counter)
    notes: dict[str, Counter] = defaultdict(Counter)
    for material, storey, length_m, what in _runs(model):
        spec = specs.get(material)
        if spec is None:
            continue
        counts[spec.part][storey] += fasteners_per_run(length_m, spec.pitch_in, spec.rows)
        notes[spec.part][(material, what, spec.pitch_in, spec.rows)] += 1
    rows = []
    for part, by_storey in sorted(counts.items()):
        item = hardware_by_model(part)
        if item is None or item.model != part:
            raise LookupError(f"Material.trim_fastening names {part!r}, which is not catalogued")
        basis = "; ".join(f"{material} {what} x{n} runs at {pitch:g} in, {across} row(s)"
                          for (material, what, pitch, across), n in sorted(notes[part].items()))
        rows.append(hardware_row(
            item, scope="trim fasteners", count=sum(by_storey.values()), part_number=part,
            by_storey=dict(sorted(by_storey.items())),
            basis=f"(ceil(run / pitch) + 1) x rows per run: {basis}"))
    return rows
