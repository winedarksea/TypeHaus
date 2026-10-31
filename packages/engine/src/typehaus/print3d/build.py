"""The print pipeline end to end: collect, choose the scale, merge thin parts into their
hosts, thicken, cut, grade furniture."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field

from typehaus.print3d.collect import collect
from typehaus.print3d.furniture import Rejection, furniture_pieces
from typehaus.print3d.merge import merge_into_hosts
from typehaus.print3d.pieces import (
    Band,
    Piece,
    band_extents,
    build_pieces,
    choose_scale,
    cut_bands,
)
from typehaus.print3d.plates import fuse_resting_plates
from typehaus.print3d.policy import PrintSettings, Treatment
from typehaus.print3d.thicken import Thickness, thicken
from typehaus.resolve.model import ResolvedModel


@dataclass
class PrintRun:
    scale: int
    bands: list[Band]
    pieces: list[Piece]
    furniture: list[Piece]
    rejected: list[Rejection]
    kept: Counter
    thickened: list[Thickness]
    too_thin: list[Thickness]
    dropped: Counter
    #: Kind -> parts printed as part of their host (``merge.py``).
    merged: Counter = field(default_factory=Counter)
    #: Furniture pieces whose thin plates were fused into their own base (``plates.py``).
    plated: int = 0
    timings: dict[str, float] = field(default_factory=dict)


def build_print(model: ResolvedModel, settings: PrintSettings) -> PrintRun:
    from typehaus.resolve.site_earth import site_grade_elevation_m

    timings: dict[str, float] = {}
    started = time.perf_counter()
    collection = collect(model, settings)
    house = [item for item in collection.items if item.treatment is not Treatment.LOOSE]
    loose = [item for item in collection.items if item.treatment is Treatment.LOOSE]
    timings["collect"] = _lap(started)
    grade = site_grade_elevation_m(model)
    top = max(item.solid.bounding_box()[5] for item in house)
    scale = choose_scale(band_extents(house, cut_bands(house, grade, top, settings)), settings)
    mm_per_m = 1000.0 / scale
    # A merged ceiling lowers its floor package's underside, so the cuts follow the merge.
    house, loose, merged = merge_into_hosts(model, house, loose, mm_per_m, settings)
    bands = cut_bands(house, grade, top, settings)
    fused = [fuse_resting_plates(item, mm_per_m, settings) for item in loose]
    loose = [item for item, _ in fused]
    results = [thicken(item, mm_per_m, settings) for item in house]
    timings["thicken"] = _lap(started) - timings["collect"]
    kept = [result for result in results if result.solid is not None]
    pieces = build_pieces([result.solid for result in kept], bands, mm_per_m, settings)
    timings["pieces"] = _lap(started) - timings["collect"] - timings["thicken"]
    furniture, rejected = furniture_pieces(loose, mm_per_m, settings) if loose else ([], [])
    timings["furniture"] = _lap(started) - sum(timings.values())
    return PrintRun(scale=scale, bands=bands, pieces=pieces, furniture=furniture,
                    rejected=rejected, kept=Counter(result.item.kind for result in kept),
                    thickened=[result for result in kept if result.factor > 1.0],
                    too_thin=[result for result in results if result.solid is None],
                    dropped=collection.dropped, merged=merged,
                    plated=sum(1 for _, count in fused if count), timings=timings)


def _lap(started: float) -> float:
    return time.perf_counter() - started
