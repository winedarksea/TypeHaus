"""Appliance, mechanical and electrical glyphs.

Most of these are boxes with a door, so they come straight from ``appliance_case``. The
exceptions earn their own builders: a range is read by its burner pattern, a water heater by
its round tank, and a grille or a panel is read by its louvers/breakers — none of which a
door-and-handle family can express.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Builder, Geometry, appliance_case
from typehaus.model.placeable_symbols._frame import (DETAIL_WEIGHT, box, circle, clamp, line,
                                                     rect)

__all__ = ["APPLIANCE_SYMBOLS"]


def cooktop(*, burners: int = 4, oven: bool = True) -> Builder:
    """A range: the burner pattern that says "cooking" plus a control strip and oven door."""

    def build(width: float, depth: float, height: float) -> Geometry:
        control_d = clamp(depth * 0.14, 0.04, 0.10)
        cook_d = depth - control_d
        cook_cy = -depth / 2 + cook_d / 2
        burner_r = min(width, cook_d) * 0.20
        deck_t = min(0.03, height * 0.2)
        columns = 2 if burners >= 4 else 1
        rows = max(1, burners // max(1, columns))
        strokes = [rect(0, 0, width, depth, fill="appliance-steel"),
                   rect(0, depth / 2 - control_d / 2, width, control_d, weight=DETAIL_WEIGHT)]
        parts = [box(0, cook_cy, 0.0, height - deck_t, width, cook_d, "appliance-white"),
                 box(0, cook_cy, height - deck_t, height, width, cook_d, "appliance-steel"),
                 box(0, depth / 2 - control_d / 2, height - deck_t, height, width, control_d,
                     "appliance-steel")]
        for column in range(columns):
            for row in range(rows):
                cx = -width / 2 + width * (column + 0.5) / columns
                cy = cook_cy - cook_d / 2 + cook_d * (row + 0.5) / rows
                strokes.append(circle(cx, cy, burner_r, weight=DETAIL_WEIGHT))
                parts.append(box(cx, cy, height - deck_t, height, burner_r * 1.9,
                                 burner_r * 1.9, "metal"))
        if oven:  # the oven door face + its handle, the same front-plane convention as a fridge
            door_t = min(0.02, depth * 0.2)
            strokes.append(line((-width * 0.4, -depth / 2 + door_t),
                                (width * 0.4, -depth / 2 + door_t)))
            parts.append(box(0, -depth / 2 + door_t / 2, height * 0.08, height * 0.72,
                             width * 0.94, door_t, "appliance-steel"))
        return tuple(strokes), tuple(parts)

    return build


def canopy_hood() -> Builder:
    """A range hood, drawn as it is seen in plan — from below.

    The reader is looking up at the underside, so the glyph is the canopy outline, the grease
    filter panel inside it, and the blower. Massing is the canopy box plus the chimney that
    carries it to the wall; a recirculating hood has no duct, so nothing leaves that chimney.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        fan_r = min(width, depth) * 0.18
        strokes = [rect(0, 0, width, depth, fill="appliance-steel"),
                   rect(0, 0, width * 0.5, depth * 0.5, weight=DETAIL_WEIGHT),
                   circle(0, 0, fan_r, weight=DETAIL_WEIGHT)]
        canopy_h = height * 0.45
        filter_t = min(0.02, canopy_h * 0.3)
        parts = [box(0, 0, filter_t, canopy_h, width, depth, "appliance-steel"),
                 box(0, 0, 0.0, filter_t, width * 0.5, depth * 0.5, "metal"),
                 # Chimney flush to the object's back (+y), where the wall is.
                 box(0, depth * 0.3, canopy_h, height, width * 0.4, depth * 0.4,
                     "appliance-steel")]
        return tuple(strokes), tuple(parts)

    return build


def tank(*, insulated: bool = True) -> Builder:
    """A water heater: a round tank in plan, massed as a box (massing here stays boxy)."""

    def build(width: float, depth: float, height: float) -> Geometry:
        radius = min(width, depth) / 2
        strokes = [circle(0, 0, radius, fill="appliance-white"),
                   circle(0, 0, radius * 0.82, weight=DETAIL_WEIGHT)]
        parts = [box(0, 0, 0.0, height * 0.92, radius * 1.9, radius * 1.9,
                     "appliance-white" if insulated else "appliance-steel"),
                 box(0, 0, height * 0.92, height, radius * 1.5, radius * 1.5, "metal")]
        return tuple(strokes), tuple(parts)

    return build


def air_handler() -> Builder:
    """A furnace / air handler: a cabinet with a filter slot and a supply plenum on top."""

    def build(width: float, depth: float, height: float) -> Geometry:
        strokes = [rect(0, 0, width, depth, fill="appliance-steel"),
                   rect(0, 0, width * 0.86, depth * 0.86, weight=DETAIL_WEIGHT),
                   line((-width / 2, -depth / 2 + depth * 0.18),
                        (width / 2, -depth / 2 + depth * 0.18))]
        filter_t = min(0.03, depth * 0.2)
        parts = [box(0, 0, 0.0, height * 0.86, width, depth, "appliance-steel"),
                 box(0, 0, height * 0.86, height, width * 0.78, depth * 0.78, "metal"),
                 box(0, -depth / 2 + filter_t / 2, height * 0.1, height * 0.24, width * 0.9,
                     filter_t, "appliance-white")]
        return tuple(strokes), tuple(parts)

    return build


def panel_board() -> Builder:
    """A load centre: the enclosure outline plus its breaker columns."""

    def build(width: float, depth: float, height: float) -> Geometry:
        strokes = [rect(0, 0, width, depth, fill="appliance-steel"),
                   line((0, -depth / 2), (0, depth / 2))]
        face_t = min(0.02, depth * 0.2)
        parts = [box(0, 0, 0.0, height, width, depth, "appliance-steel"),
                 box(0, -depth / 2 + face_t / 2, height * 0.08, height * 0.92, width * 0.86,
                     face_t, "metal")]
        return tuple(strokes), tuple(parts)

    return build


def grille(*, louvers: int = 5) -> Builder:
    """A supply/return register: the louver lines are the whole symbol."""

    def build(width: float, depth: float, height: float) -> Geometry:
        strokes = [rect(0, 0, width, depth, fill="metal")]
        for index in range(1, max(2, louvers)):
            cy = -depth / 2 + depth * index / max(2, louvers)
            strokes.append(line((-width * 0.46, cy), (width * 0.46, cy)))
        parts = [box(0, 0, 0.0, height, width, depth, "metal")]
        return tuple(strokes), tuple(parts)

    return build


APPLIANCE_SYMBOLS: dict[str, Builder] = {
    # A French-door refrigerator: two fresh-food doors over a freezer drawer would need a
    # nested split, so the pair of full-height doors is the honest simplification.
    "refrigerator": appliance_case(doors=2, split="vertical", body="appliance-steel"),
    "range": cooktop(burners=4, oven=True),
    "dishwasher": appliance_case(doors=1, body="appliance-steel"),
    "washer": appliance_case(doors=1, porthole=True, controls=True),
    "dryer": appliance_case(doors=1, porthole=True, controls=True),
    "microwave": appliance_case(doors=1, body="appliance-steel"),
    "hood": canopy_hood(),
    "furnace": air_handler(),
    "water-heater": tank(),
    "panel": panel_board(),
    "register": grille(louvers=5),
}
