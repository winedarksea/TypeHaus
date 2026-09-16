"""Contract tests for deterministic, candidate-based drawing annotation layout.

The general solver complements :mod:`typehaus.emit.draw.annotate`'s column helpers.  Its
coordinates are model inches, while text height, obstacle clearance, and scale conversion
retain the existing printed-point convention.
"""

from __future__ import annotations

from typehaus.emit.draw.annotation_layout import (
    AnnotationRequest,
    Candidate,
    SegmentObstacle,
    Viewport,
    resolve_annotations,
)


def _overlaps(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _request(key: str, *positions: tuple[float, float], priority: int = 0,
             text: str | None = None, rotation: float = 0.0) -> AnnotationRequest:
    return AnnotationRequest(
        key=key,
        text=text or key,
        target=(5.0, 5.0),
        candidates=tuple(Candidate(at=position, rotation=rotation) for position in positions),
        height_pt=7.0,
        priority=priority,
    )


def test_resolver_is_deterministic_and_preserves_request_identity() -> None:
    requests = (
        _request("first", (4.0, 5.0), (1.0, 8.0)),
        _request("second", (4.0, 5.0), (5.5, 8.0)),
    )
    viewport = Viewport((0.0, 0.0, 10.1, 10.1))

    first = resolve_annotations(requests, viewport=viewport, scale=1.0)
    second = resolve_annotations(requests, viewport=viewport, scale=1.0)

    assert first == second
    assert tuple(placed.request.key for placed in first.placements) == ("first", "second")
    assert not _overlaps(first.placements[0].box, first.placements[1].box)
    assert not first.diagnostics


def test_priority_decides_who_keeps_a_shared_preferred_position() -> None:
    low = _request("low", (4.0, 5.0), (1.0, 8.0), priority=1)
    high = _request("high", (4.0, 5.0), (7.0, 8.0), priority=10)

    result = resolve_annotations((low, high), viewport=Viewport((0.0, 0.0, 10.0, 10.0)),
                                 scale=1.0)
    by_key = {placed.request.key: placed for placed in result.placements}

    assert by_key["high"].candidate == high.candidates[0]
    assert by_key["low"].candidate == low.candidates[1]


def test_segment_obstacle_blocks_only_its_buffered_linework() -> None:
    request = _request("grade", (4.0, 5.0), (4.0, 7.0))
    obstacle = SegmentObstacle(start=(3.5, 5.0), end=(6.5, 5.0), clearance_pt=1.0)

    result = resolve_annotations(
        (request,), viewport=Viewport((0.0, 0.0, 10.0, 10.0)),
        obstacles=(obstacle,), scale=1.0,
    )

    assert result.placements[0].candidate == request.candidates[1]
    assert not result.diagnostics


def test_multiline_rotated_bounds_remain_inside_viewport() -> None:
    request = _request(
        "bearing", (9.8, 5.0), (5.0, 5.0), text="N 01° E\n120.00'", rotation=90.0,
    )
    viewport = Viewport((0.0, 0.0, 10.1, 10.1))

    result = resolve_annotations((request,), viewport=viewport, scale=1.0)
    placed = result.placements[0]

    assert placed.candidate == request.candidates[1]
    assert (viewport.bounds[0] <= placed.box[0] <= placed.box[2] <= viewport.bounds[2]
            and viewport.bounds[1] <= placed.box[1] <= placed.box[3] <= viewport.bounds[3])
    assert placed.box[3] - placed.box[1] > placed.box[2] - placed.box[0]


def test_impossible_placement_is_retained_and_diagnosed() -> None:
    request = _request("required-setback", (5.0, 5.0))
    blocking = SegmentObstacle(start=(0.0, 5.0), end=(10.0, 5.0), clearance_pt=10.0)

    result = resolve_annotations(
        (request,), viewport=Viewport((0.0, 0.0, 10.0, 10.0)),
        obstacles=(blocking,), scale=1.0,
    )

    assert len(result.placements) == 1, "required drawing text must never disappear"
    assert result.placements[0].request.key == "required-setback"
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.key == "required-setback"
    assert diagnostic.conflicts
