"""Align's closed pivoting carrier; loaded-roll and opening space are checked separately."""

from typehaus.model.placeable_symbols._align_hardware import align_bar
from typehaus.model.placeable_symbols._frame import Part, Stroke


def pivoting_paper_holder(width: float, depth: float, height: float, *,
                          color: str = "brushed-nickel"
                          ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    return align_bar(width, depth, height, width_post_ratio=1.34 / 8.11,
                     depth_post_ratio=1.34 / 3.34, pivoting=True, color=color)
