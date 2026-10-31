"""Drywall accessories by the LF: beads and the LED shadow-gap bead (decision #103).

One row per (kind, material, room) off ``ResolvedModel.drywall_trims``
(→ resolve/drywall_trims.py). ``pieces`` sums each contiguous record's stock lengths, the
count a supplier quotes. Priced on ``material`` in ``[drywall_trims]``.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.model import ResolvedModel

_FT = 0.3048
KIND_LABELS = {
    "led_profile": "LED shadow-gap bead", "outside_corner": "Outside corner bead",
    "termination": "J-bead termination", "tile_reveal": "Tile-stop reveal",
    "door_l_bead": "Trimless door L-bead", "window_corner": "Window return corner bead",
    "window_frame": "Window return frame bead",
}


def drywall_trim_rows(model: ResolvedModel) -> list[dict[str, object]]:
    length: dict[tuple[str, str, str], float] = defaultdict(float)
    pieces: dict[tuple[str, str, str], int] = defaultdict(int)
    tags: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for trim in model.drywall_trims:
        key = (trim.kind, trim.material_ref, trim.room or "")
        length[key] += trim.length_m
        pieces[key] += trim.pieces
        tags[key].update(trim.tags)
    return [{"kind": kind, "material": material, "room": room or None,
             "length_ft": round(length[key] / _FT, 1), "pieces": pieces[key],
             "tags": sorted(tags[key])}
            for key in sorted(length) for kind, material, room in (key,)]
