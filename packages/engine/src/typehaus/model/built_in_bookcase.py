"""Generated board geometry for :class:`BuiltInBookcaseSpec`.

The local frame matches ordinary placeables: the run is centered at the origin, its front is
at negative y, and its back meets positive y.  Consumers apply the existing place-local
transform, keeping a wall-attached run consistent in every output.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from typehaus.model.types import BuiltInBookcaseSpec


@dataclass(frozen=True)
class BuiltInBookcasePart:
    """A rectangular board in a bookcase-local coordinate frame, in metres."""

    role: str
    bay_index: int | None
    center: tuple[float, float, float]
    size: tuple[float, float, float]
    material_ref: str | None = None

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
    width += spec.west_filler_width.meters
    depth = spec.shelf_depth.meters + spec.back_thickness.meters
    height = max(bay.height.meters for bay in spec.bays)
    return width, depth, height


def built_in_bookcase_parts(spec: BuiltInBookcaseSpec) -> tuple[BuiltInBookcasePart, ...]:
    """Return stepped backs, full-height dividers, and evenly distributed boards.

    A divider shared by two bays rises to their maximum height.  Board centers include both
    the base and top, with their outer faces exactly inside the stated bay height.  A bay
    with a ``closed_base_height`` gets a front panel below it and its boards above it.
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
    filler = spec.west_filler_width.meters
    if filler > 0:
        parts.append(BuiltInBookcasePart(
            "filler", None, (left + filler / 2, shelf_center_y,
                              spec.bays[0].height.meters / 2),
            (filler, shelf_depth, spec.bays[0].height.meters),
        ))
    cursor = left + filler + divider
    for index, bay in enumerate(spec.bays):
        bay_lefts.append(cursor)
        clear_width = bay.clear_width.meters
        height = bay.height.meters
        parts.append(BuiltInBookcasePart(
            "back", index, (cursor + clear_width / 2, back_center_y, height / 2),
            (clear_width, back, height),
        ))
        base = bay.closed_base_height.meters
        if base > 0:
            # Carcass stock, inset between the dividers, flush with the shelf fronts.
            parts.append(BuiltInBookcasePart(
                "front_panel", index,
                (cursor + clear_width / 2, -depth / 2 + divider / 2, base / 2),
                (clear_width, divider, base),
            ))
        count = bay.horizontal_board_count
        for board_index in range(count):
            center_z = base + board / 2 + board_index * (height - base - board) / (count - 1)
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
        x = left + filler + divider / 2 if divider_index == 0 else bay_lefts[divider_index - 1] + \
            spec.bays[divider_index - 1].clear_width.meters + divider / 2
        parts.append(BuiltInBookcasePart(
            "divider", None, (x, shelf_center_y, height / 2), (divider, shelf_depth, height),
        ))
    return _apply_bookcase_fronts(spec, parts, depth)


def _apply_bookcase_fronts(
    spec: BuiltInBookcaseSpec, parts: list[BuiltInBookcasePart], depth: float,
) -> tuple[BuiltInBookcasePart, ...]:
    """Replace the front of sheet panels with solid nosings, within the same envelope."""
    nosing_depth = spec.shelf_nosing_depth.meters
    result = []
    dividers = [part for part in parts if part.role == "divider"]
    strips = []
    if nosing_depth:
        for index, divider in enumerate(dividers):
            x, _, z = divider.center
            width, _, height = divider.size
            strip_width = spec.face_strip_width.meters
            if index == 0:
                x += (strip_width - width) / 2
            elif index == len(dividers) - 1:
                x -= (strip_width - width) / 2
            strips.append(BuiltInBookcasePart(
                "face_strip", None, (x, -depth / 2 + nosing_depth / 2, z),
                (strip_width, nosing_depth, height)))
    for part in parts:
        panel = replace(part, material_ref=spec.panel_material_ref)
        if nosing_depth and part.role == "front_panel":
            index = part.bay_index
            assert index is not None
            left = strips[index].center[0] + strips[index].size[0] / 2
            right = strips[index + 1].center[0] - strips[index + 1].size[0] / 2
            panel_height = part.size[2] - (
                spec.shelf_nosing_height.meters - spec.horizontal_board_thickness.meters)
            if panel_height <= 0:
                continue
            panel = replace(panel, center=((left + right) / 2, part.center[1], panel_height / 2),
                            size=(right - left, part.size[1], panel_height))
        if nosing_depth and part.role in {"horizontal_board", "divider"}:
            x, y, z = part.center
            width, panel_depth, height = part.size
            panel = replace(panel, center=(x, y + nosing_depth / 2, z),
                            size=(width, panel_depth - nosing_depth, height))
            if part.role == "horizontal_board":
                # Face strips lap the panel edges; butt the nosing between them so the
                # solid pieces never overlap, and keep its top flush with the plywood.
                index = part.bay_index
                assert index is not None
                left = strips[index].center[0] + strips[index].size[0] / 2
                right = strips[index + 1].center[0] - strips[index + 1].size[0] / 2
                # Rip the floor-level nosing rather than extending it below the case.
                nosing_height = min(spec.shelf_nosing_height.meters, part.z1_m)
                result.append(BuiltInBookcasePart(
                    "shelf_nosing", index,
                    ((left + right) / 2, -depth / 2 + nosing_depth / 2,
                     part.z1_m - nosing_height / 2),
                    (right - left, nosing_depth, nosing_height)))
        result.append(panel)
    return tuple([*result, *strips])
