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


def outdoor_condenser(*, grille_bars: int = 5) -> Builder:
    """An outdoor heat-pump condenser with its fan guard and front coil grille.

    A generic equipment box disappears against an exterior wall in the 3D view. The fan
    guard is the useful plan-scale cue; the raised top band and front grille make the same
    distinction survive an oblique 3D view without claiming a product-specific casing.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        top_h = height * 0.12
        grille_t = min(depth * 0.12, 0.035)
        fan_r = min(width, depth) * 0.27
        strokes = [rect(0, 0, width, depth, fill="appliance-steel"),
                   circle(0, 0, fan_r, weight=DETAIL_WEIGHT)]
        for index in range(1, max(2, grille_bars)):
            x = -width * 0.43 + width * 0.86 * index / max(2, grille_bars)
            strokes.append(line((x, -depth * 0.42), (x, depth * 0.42)))
        parts = [box(0, 0, 0.0, height - top_h, width, depth, "appliance-steel"),
                 # The shallow, contrasting top reads as the fan guard from above.
                 box(0, 0, height - top_h, height, width * 0.88, depth * 0.88, "metal"),
                 # Keep the coil grille within the declared footprint at the front face.
                 box(0, -depth / 2 + grille_t / 2, height * 0.12, height * 0.78,
                     width * 0.90, grille_t, "metal")]
        return tuple(strokes), tuple(parts)

    return build


def sauna_heater(*, stone_columns: int = 3, stone_rows: int = 3) -> Builder:
    """An electric sauna heater: a steel casing carrying an open bed of stones.

    The stones are the symbol. A heater drawn as a plain box is indistinguishable from the
    water heater standing three rooms away, and the stones are also the thing the room is
    planned around — they are what the upper bench has to sit level with and what the guard
    clearance is measured from. Drawn as a fixed grid rather than a scatter, because the
    glyph has to be byte-identical on every build.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        casing_w, casing_d = width * 0.94, depth * 0.94
        bed_w, bed_d = casing_w * 0.82, casing_d * 0.82
        columns, rows = max(1, stone_columns), max(1, stone_rows)
        stone_r = min(bed_w / columns, bed_d / rows) * 0.34
        strokes = [rect(0, 0, width, depth, fill="appliance-steel"),
                   rect(0, 0, bed_w, bed_d, fill="stone", weight=DETAIL_WEIGHT)]
        for column in range(columns):
            for row in range(rows):
                cx = -bed_w / 2 + bed_w * (column + 0.5) / columns
                cy = -bed_d / 2 + bed_d * (row + 0.5) / rows
                strokes.append(circle(cx, cy, stone_r, segments=10, weight=DETAIL_WEIGHT))
        # The stones sit *in* the top of the casing, not on a shelf above it. The collar
        # around them is four rails rather than one box: a box would enclose the stone bed
        # and hide the only part of this object anyone recognises it by.
        bed_z0 = height * 0.82
        rail_w, rail_d = (casing_w - bed_w) / 2, (casing_d - bed_d) / 2
        parts = [box(0, 0, 0.0, bed_z0, width, depth, "appliance-steel"),
                 box(0, 0, bed_z0, height, bed_w, bed_d, "stone")]
        for sign in (-1, 1):
            parts.append(box(sign * (bed_w + rail_w) / 2, 0, bed_z0, height, rail_w, casing_d,
                             "appliance-steel"))
            parts.append(box(0, sign * (bed_d + rail_d) / 2, bed_z0, height, bed_w, rail_d,
                             "appliance-steel"))
        return tuple(strokes), tuple(parts)

    return build


def meter_socket() -> Builder:
    """A utility meter socket: a grey ringless can with the glass register on its face.

    Not ``panel_board`` at a smaller size and not ``safety_switch`` either — what identifies a
    meter from the driveway is the round glass register on the cover, which neither of those
    has, and the can itself is plain galvanised steel rather than the domain fallback yellow.
    The dome is drawn *into* the front face rather than standing proud of it: the authored
    footprint is the product's overall size, which is what a clearance check measures.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        # The plan circle is the can's register seen from above, so it is sized off the
        # footprint alone — strokes are height-independent by contract. The massed dome takes
        # the same radius, capped so it cannot run off the top or bottom of a shallow can.
        dome_r = min(width, depth) * 0.42
        dome_cz = height * 0.6
        dome_rz = min(dome_r, height * 0.35)
        dome_t = min(depth * 0.5, dome_r)
        strokes = [rect(0, 0, width, depth, fill="metal"),
                   circle(0, 0, dome_r, fill="glass", weight=DETAIL_WEIGHT)]
        parts = [box(0, 0, 0.0, height, width, depth, "metal"),
                 box(0, -depth / 2 + dome_t / 2, dome_cz - dome_rz, dome_cz + dome_rz,
                     dome_r * 2, dome_t, "glass")]
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


def safety_switch() -> Builder:
    """A NEMA 3R disconnect: a small grey enclosure with a rain hood and a side lever.

    Not ``panel_board`` at a smaller size — a load centre is read by its breaker columns, and
    a disconnect has none. What identifies one on site is the operating handle hanging off the
    right-hand side and the hood that sheds water off the cover, so both are the glyph. Both
    are drawn *inside* the declared W x D: the authored footprint is the product's overall
    size, handle and hood included, which is what a clearance check has to measure.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        handle_t = clamp(width * 0.14, 0.015, 0.05)
        handle_cx = width / 2 - handle_t / 2
        body_w = width - handle_t
        body_cx = -handle_t / 2
        body_d = depth * 0.82
        body_cy = depth / 2 - body_d / 2  # the enclosure sits back against its wall
        body_z1 = height * 0.9
        strokes = [rect(body_cx, body_cy, body_w, body_d, fill="metal"),
                   rect(body_cx, body_cy, body_w * 0.8, body_d * 0.62, weight=DETAIL_WEIGHT),
                   rect(handle_cx, body_cy, handle_t, body_d * 0.42,
                        fill="luminaire-housing", weight=DETAIL_WEIGHT)]
        parts = [box(body_cx, body_cy, 0.0, body_z1, body_w, body_d, "metal"),
                 box(body_cx, 0, body_z1, height, body_w, depth, "metal"),
                 box(handle_cx, body_cy, height * 0.38, height * 0.68, handle_t,
                     body_d * 0.42, "luminaire-housing")]
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
    # A stacked pair is one tower with two front-loader doors, so the face splits in
    # elevation and each half gets its own glass — a single centred porthole would sit on
    # the seam between the machines. Only the upper machine wears a console, but the family
    # draws one band at the top, which is where a stack's shared controls actually are.
    "washer-dryer-stacked": appliance_case(doors=2, split="horizontal", porthole=True,
                                           porthole_per_door=True, controls=True),
    "microwave": appliance_case(doors=1, body="appliance-steel"),
    "hood": canopy_hood(),
    "furnace": air_handler(),
    "heat-pump-outdoor": outdoor_condenser(),
    # An ERV/HRV core is the same read at plan scale as any other air-side cabinet — a box
    # with a filter slot and a plenum collar on top — so it shares the builder rather than
    # inventing a glyph that differs only in the label beside it.
    "erv": air_handler(),
    "water-heater": tank(),
    "sauna-heater": sauna_heater(),
    "panel": panel_board(),
    "meter": meter_socket(),
    "disconnect": safety_switch(),
    "register": grille(louvers=5),
}
