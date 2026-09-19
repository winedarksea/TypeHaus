"""Generated board geometry for :class:`BuiltInBookcaseSpec`.

The local frame matches ordinary placeables: the run is centered at the origin, its front is
at negative y, and its back meets positive y.  Consumers apply the existing place-local
transform, keeping a wall-attached run consistent in every output.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.types import BuiltInBookcaseSpec


@dataclass(frozen=True)
class BuiltInBookcasePart:
    """A rectangular board in a bookcase-local coordinate frame, in metres."""

    role: str
    bay_index: int | None
    center: tuple[float, float, float]
    size: tuple[float, float, float]

    @property
    def outline(self) -> list[tuple[float, float]]:
        x, y, _ = self.center
        width, depth, _ = self.size
        return [(x - width / 2, y - depth / 2), (x + width / 2, y - depth / 2),
                (x + width / 2, y + depth / 2), (x - width / 2, y + depth / 2)]

    @property
    def z0_m(self) -> float:
        return self.center[2] - self.size[2] / 2

    @property
    def z1_m(self) -> float:
        return self.center[2] + self.size[2] / 2


def built_in_bookcase_dimensions(spec: BuiltInBookcaseSpec) -> tuple[float, float, float]:
    """Return overall width, depth, and highest point implied by ``spec``."""
    width = sum(bay.clear_width.meters for bay in spec.bays)
    width += (len(spec.bays) + 1) * spec.divider_thickness.meters
    depth = spec.shelf_depth.meters + spec.back_thickness.meters
    height = max(bay.height.meters for bay in spec.bays)
    return width, depth, height


def built_in_bookcase_parts(spec: BuiltInBookcaseSpec) -> tuple[BuiltInBookcasePart, ...]:
    """Return stepped backs, full-height dividers, and evenly distributed boards.

    A divider shared by two bays rises to their maximum height.  Board centers include both
    the base and top, with their outer faces exactly inside the stated bay height.
    """
    width, depth, _ = built_in_bookcase_dimensions(spec)
    divider = spec.divider_thickness.meters
    board = spec.horizontal_board_thickness.meters
    shelf_depth = spec.shelf_depth.meters
    back = spec.back_thickness.meters
    left = -width / 2
    shelf_center_y = -depth / 2 + shelf_depth / 2
    back_center_y = depth / 2 - back / 2
    parts: list[BuiltInBookcasePart] = []
    bay_lefts: list[float] = []
    cursor = left + divider
    for index, bay in enumerate(spec.bays):
        bay_lefts.append(cursor)
        clear_width = bay.clear_width.meters
        height = bay.height.meters
        parts.append(BuiltInBookcasePart(
            "back", index, (cursor + clear_width / 2, back_center_y, height / 2),
            (clear_width, back, height),
        ))
        count = bay.horizontal_board_count
        for board_index in range(count):
            center_z = board / 2 + board_index * (height - board) / (count - 1)
            parts.append(BuiltInBookcasePart(
                "horizontal_board", index,
                (cursor + clear_width / 2, shelf_center_y, center_z),
                (clear_width, shelf_depth, board),
            ))
        cursor += clear_width + divider
    for divider_index in range(len(spec.bays) + 1):
        if divider_index == 0:
            height = spec.bays[0].height.meters
        elif divider_index == len(spec.bays):
            height = spec.bays[-1].height.meters
        else:
            height = max(spec.bays[divider_index - 1].height.meters,
                         spec.bays[divider_index].height.meters)
        x = left + divider / 2 if divider_index == 0 else bay_lefts[divider_index - 1] + \
            spec.bays[divider_index - 1].clear_width.meters + divider / 2
        parts.append(BuiltInBookcasePart(
            "divider", None, (x, shelf_center_y, height / 2), (divider, shelf_depth, height),
        ))
    return tuple(parts)
