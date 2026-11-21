"""Window install fasteners off ``WindowType.install_fastening`` (decision #147).

Per placed unit: fin fasteners along each side, one ``corner_offset_in`` in from each corner
and every ``fin_pitch_in`` between, plus the jamb straps. A placed type with no spec is not
graded (an UNKNOWN would block the permit print): ``window_install_gaps`` lists it as
unmodelled procurement (decision #47).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from typehaus.hardware.catalog import hardware_by_model
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row

_M_PER_IN = 0.0254


def fin_fasteners(width_in: float, height_in: float, pitch_in: float, offset_in: float) -> int:
    """Fin fasteners round one unit: each side from ``offset_in`` in at both corners."""
    def side(length_in: float) -> int:
        clear = max(0.0, length_in - 2 * offset_in)
        return math.ceil(clear / pitch_in - 1e-9) + 1
    return 2 * side(width_in) + 2 * side(height_in)


def _placed_windows(model: ResolvedModel):
    types = {t.tag: t for t in model.plan.library.window_types}
    walls = {wall.tag: wall for wall in model.walls}
    for opening in model.openings:
        kind = types.get(opening.type_ref or "")
        if opening.kind == "window" and kind is not None:
            wall = walls.get(opening.host_wall)
            yield opening, kind, wall.storey if wall else "building"


def _catalogued(part: str):
    item = hardware_by_model(part)
    if item is None or item.model != part:
        raise LookupError(f"WindowType.install_fastening names {part!r}, not catalogued")
    return item


def window_fastener_rows(model: ResolvedModel) -> list:
    counts: dict[str, Counter] = defaultdict(Counter)
    notes: dict[str, set] = defaultdict(set)
    for _opening, kind, storey in _placed_windows(model):
        spec = kind.install_fastening
        if spec is None:
            continue
        w_in, h_in = kind.width.meters / _M_PER_IN, kind.height.meters / _M_PER_IN
        counts[spec.part][storey] += fin_fasteners(w_in, h_in, spec.fin_pitch_in,
                                                   spec.corner_offset_in)
        notes[spec.part].add(f"{kind.tag}: fin at {spec.fin_pitch_in:g} in, "
                             f"{spec.corner_offset_in:g} in off corners")
        if spec.jamb_straps_per_side and spec.strap_part:
            counts[spec.strap_part][storey] += 2 * spec.jamb_straps_per_side
            notes[spec.strap_part].add(f"{kind.tag}: {spec.jamb_straps_per_side} per jamb")
    return [hardware_row(
        _catalogued(part), scope="window install fasteners", count=sum(by_storey.values()),
        part_number=part, by_storey=dict(sorted(by_storey.items())),
        basis="per placed unit: " + "; ".join(sorted(notes[part])))
        for part, by_storey in sorted(counts.items())]


def window_install_gaps(model: ResolvedModel) -> list[dict[str, object]]:
    """Placed window types with no ``install_fastening``: unmodelled procurement."""
    missing: Counter = Counter()
    for _opening, kind, _storey in _placed_windows(model):
        if kind.install_fastening is None:
            missing[kind.tag] += 1
    return [{"item": "window install fasteners", "type": tag, "units": n,
             "reason": "WindowType.install_fastening not authored"}
            for tag, n in sorted(missing.items())]
