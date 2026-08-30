"""Luminaire glyphs — one per ``LuminaireForm`` that has a point instance.

Lighting symbols are drafting convention, not parameterised furniture: a can light is a
circle with an inscribed cross whatever its trim diameter, and a ceiling fan is a hub with
blade lobes whatever its span. So these are hand-drawn here, the way ``plumbing.py`` is,
rather than assembled from ``_families``.

Two things make this family different from every other one in the package:

* **They are small.** A 3" can is a 0.076 m footprint — an order of magnitude under a
  sofa — so every interior tick is clamped as a *fraction* of the object rather than to an
  absolute millimetre floor, and the contract sweep's 0.30x0.10 case (a wide, shallow
  linear fixture) is the shape that actually breaks naive halves.
* **They light.** The ``lamp`` colour role is the emitting face — warm off-white, brighter
  than any other role in the palette — and ``luminaire-housing`` is the trim ring or body
  around it. Nothing here emits in the renderer today (deferred), but the colour split is
  what makes a fixture read as on rather than as a grey puck.

Wall-mounted forms (sconce, wall lamp, mirror light) keep the package's ``+y is the
object's back`` convention, so the wall side is ``+y`` and the light throws toward ``-y``.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import (
    DETAIL_WEIGHT,
    OUTLINE_WEIGHT,
    Part,
    Point,
    Stroke,
    arc,
    box,
    circle,
    clamp,
    line,
    polygon,
    rect,
)

__all__ = ["LIGHTING_SYMBOLS"]

# How thick a housing/trim ring is as a share of the fixture's smaller plan dimension. A
# can's baffle trim really is about this proportion of its aperture at every size sold.
TRIM_SHARE = 0.16
# The plate a wall-mounted fixture is screwed to, as a share of the fixture's depth.
BACKPLATE_SHARE = 0.22


def _plan_size(width: float, depth: float) -> float:
    return min(width, depth)


def recessed_can() -> Builder:
    """A downlight: aperture circle, trim ring, inscribed cross.

    The cross is the mark that distinguishes a can from every other circle on an E-sheet
    (a smoke detector, a round table). Its arms are clamped to the *aperture*, not to an
    absolute length, because a 3" can is 0.076 m across and an absolute tick would leave
    the fixture's own footprint — the one thing no symbol here may do.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        outer_r = _plan_size(width, depth) / 2
        trim = clamp(outer_r * TRIM_SHARE, 0.0, outer_r * 0.3)
        aperture_r = outer_r - trim
        arm = aperture_r * 0.72
        strokes = [circle(0, 0, outer_r, fill="luminaire-housing"),
                   circle(0, 0, aperture_r, fill="lamp", weight=DETAIL_WEIGHT),
                   line((-arm, 0), (arm, 0)), line((0, -arm), (0, arm))]
        # A recessed can is a housing can above the ceiling plane with its lens at the
        # bottom: the lens is what the room sees, so it gets the bottom of the box.
        lens_t = min(height * 0.25, height)
        parts = [box(0, 0, lens_t, height, outer_r * 2, outer_r * 2, "luminaire-housing"),
                 box(0, 0, 0.0, lens_t, aperture_r * 2, aperture_r * 2, "lamp")]
        return tuple(strokes), tuple(parts)

    return build


def panel_light() -> Builder:
    """A flat-panel troffer: the frame rectangle, the lit field, and its diagonals."""

    def build(width: float, depth: float, height: float) -> Geometry:
        frame = clamp(_plan_size(width, depth) * TRIM_SHARE, 0.0,
                      _plan_size(width, depth) * 0.25)
        lit_w, lit_d = width - 2 * frame, depth - 2 * frame
        strokes = [rect(0, 0, width, depth, fill="luminaire-housing"),
                   rect(0, 0, lit_w, lit_d, fill="lamp", weight=DETAIL_WEIGHT),
                   line((-lit_w / 2, -lit_d / 2), (lit_w / 2, lit_d / 2)),
                   line((-lit_w / 2, lit_d / 2), (lit_w / 2, -lit_d / 2))]
        lens_t = min(height * 0.4, height)
        parts = [box(0, 0, lens_t, height, width, depth, "luminaire-housing"),
                 box(0, 0, 0.0, lens_t, lit_w, lit_d, "lamp")]
        return tuple(strokes), tuple(parts)

    return build


def sconce(*, throw: str = "down") -> Builder:
    """A wall fixture: backplate at the wall, half-round body, and a throw chevron.

    ``throw`` draws the light's distribution, which is the whole reason a plan reader
    cares which sconce is which: ``"down"`` is one chevron into the room, ``"updown"``
    two (the theatre convention), ``"spot"`` a narrow wedge.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        plate_d = clamp(depth * BACKPLATE_SHARE, 0.0, depth * 0.35)
        plate_cy = depth / 2 - plate_d / 2
        body_r = min(width / 2, depth - plate_d)
        body_cy = depth / 2 - plate_d
        strokes: list[Stroke] = [
            rect(0, plate_cy, width, plate_d, fill="luminaire-housing"),
            # Half-round body hanging off the plate into the room (180deg..360deg is -y).
            arc(0, body_cy, body_r, 180.0, 360.0, weight=OUTLINE_WEIGHT),
            line((-body_r, body_cy), (body_r, body_cy), weight=OUTLINE_WEIGHT),
        ]
        chevron_w = body_r * 0.55
        tip = -depth / 2
        if throw in ("down", "updown", "spot"):
            span = chevron_w * (0.5 if throw == "spot" else 1.0)
            strokes.append(polygon([(-span, body_cy - body_r * 0.55), (0.0, tip),
                                    (span, body_cy - body_r * 0.55)],
                                   closed=False, weight=DETAIL_WEIGHT))
        if throw == "updown":
            # The up-throw chevron stays *off* the backplate: drawn on the plate it is a
            # dark line on a dark fill, which is exactly the distinction between an
            # up/down sconce and a plain one being invisible on the sheet.
            plate_face = plate_cy - plate_d / 2
            strokes.append(polygon([(-chevron_w, plate_face - body_r * 0.45),
                                    (0.0, plate_face),
                                    (chevron_w, plate_face - body_r * 0.45)],
                                   closed=False, weight=DETAIL_WEIGHT))
        lens_h = min(height * 0.3, height)
        parts = [box(0, plate_cy, 0.0, height, width, plate_d, "luminaire-housing"),
                 box(0, body_cy - body_r / 2, lens_h, height, body_r * 1.6, body_r,
                     "luminaire-housing"),
                 box(0, body_cy - body_r / 2, 0.0, lens_h, body_r * 1.4, body_r * 0.9,
                     "lamp")]
        return tuple(strokes), tuple(parts)

    return build


def pendant() -> Builder:
    """A hanging fixture: the shade circle, its canopy, and the drop cord between them."""

    def build(width: float, depth: float, height: float) -> Geometry:
        shade_r = _plan_size(width, depth) / 2
        canopy_r = shade_r * 0.24
        strokes = [circle(0, 0, shade_r, fill="luminaire-housing"),
                   circle(0, 0, shade_r * 0.62, fill="lamp", weight=DETAIL_WEIGHT),
                   circle(0, 0, canopy_r, weight=DETAIL_WEIGHT)]
        # The type's height is the whole assembly: canopy at the ceiling, cord, shade
        # hanging at the bottom. A pendant drawn as a single box loses the drop, which is
        # the dimension a designer actually argues about.
        shade_h = min(height * 0.34, height)
        canopy_h = min(height * 0.08, height - shade_h)
        parts = [box(0, 0, 0.0, shade_h, shade_r * 2, shade_r * 2, "lamp"),
                 box(0, 0, height - canopy_h, height, canopy_r * 2, canopy_r * 2, "metal"),
                 box(0, 0, shade_h, height - canopy_h, canopy_r * 0.5, canopy_r * 0.5,
                     "metal")]
        return tuple(strokes), tuple(parts)

    return build


def chandelier(*, arms: int = 6) -> Builder:
    """A multi-arm fixture: the body circle, radiating arms, and a lamp at each arm end."""

    def build(width: float, depth: float, height: float) -> Geometry:
        import math

        outer_r = _plan_size(width, depth) / 2
        lamp_r = outer_r * 0.16
        arm_r = outer_r - lamp_r
        hub_r = outer_r * 0.22
        strokes: list[Stroke] = [circle(0, 0, outer_r, weight=DETAIL_WEIGHT),
                                 circle(0, 0, hub_r, fill="luminaire-housing")]
        count = max(3, arms)
        lamp_centres: list[Point] = []
        for index in range(count):
            angle = 2 * math.pi * index / count
            cx, cy = arm_r * math.cos(angle), arm_r * math.sin(angle)
            lamp_centres.append((cx, cy))
            strokes.append(line((hub_r * math.cos(angle), hub_r * math.sin(angle)), (cx, cy)))
            strokes.append(circle(cx, cy, lamp_r, segments=12, fill="lamp",
                                  weight=DETAIL_WEIGHT))
        body_h = min(height * 0.4, height)
        canopy_h = min(height * 0.06, height - body_h)
        parts: list[Part] = [
            box(0, 0, 0.0, body_h, hub_r * 2, hub_r * 2, "luminaire-housing"),
            box(0, 0, height - canopy_h, height, hub_r * 1.2, hub_r * 1.2, "metal"),
            box(0, 0, body_h, height - canopy_h, hub_r * 0.6, hub_r * 0.6, "metal"),
        ]
        parts.extend(box(cx, cy, body_h * 0.3, body_h, lamp_r * 1.6, lamp_r * 1.6, "lamp")
                     for cx, cy in lamp_centres)
        return tuple(strokes), tuple(parts)

    return build


def ceiling_fan_light(*, blades: int = 4) -> Builder:
    """A fan with a light kit: the sweep circle, blade lobes, and the lit hub.

    The blades are drawn as lobes rather than as the fan's real aerofoils because at plan
    scale the only fact worth reading is "this spins and takes the whole ceiling" — the
    swept circle plus four paddles says that at 36" and at 60".
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        import math

        sweep_r = _plan_size(width, depth) / 2
        hub_r = sweep_r * 0.26
        blade_len = sweep_r - hub_r
        blade_half = sweep_r * 0.13
        strokes: list[Stroke] = [circle(0, 0, sweep_r, weight=DETAIL_WEIGHT),
                                 circle(0, 0, hub_r, fill="lamp")]
        count = max(3, blades)
        for index in range(count):
            angle = 2 * math.pi * index / count
            cos, sin = math.cos(angle), math.sin(angle)
            # A paddle: rectangle from the hub out to the sweep, drawn in the blade's
            # own frame and rotated into place here rather than by the consumer.
            corners = ((hub_r, -blade_half), (sweep_r, -blade_half),
                       (sweep_r, blade_half), (hub_r, blade_half))
            strokes.append(polygon([(x * cos - y * sin, x * sin + y * cos)
                                    for x, y in corners],
                                   fill="luminaire-housing", weight=DETAIL_WEIGHT))
        # Vertically: the light kit hangs below the motor housing, the blades sweep
        # between them, and the downrod runs up to the canopy.
        kit_h = min(height * 0.22, height)
        motor_top = min(height * 0.55, height)
        blade_z = (kit_h + motor_top) / 2
        blade_t = min(height * 0.05, motor_top - kit_h) if motor_top > kit_h else height * 0.02
        canopy_h = min(height * 0.06, max(0.0, height - motor_top))
        parts: list[Part] = [
            box(0, 0, 0.0, kit_h, hub_r * 2, hub_r * 2, "lamp"),
            box(0, 0, kit_h, motor_top, hub_r * 1.7, hub_r * 1.7, "luminaire-housing"),
        ]
        for index in range(count):
            angle = 2 * math.pi * index / count
            cos, sin = math.cos(angle), math.sin(angle)
            reach = hub_r + blade_len / 2
            parts.append(box(reach * cos, reach * sin, blade_z - blade_t / 2,
                             blade_z + blade_t / 2,
                             abs(blade_len * cos) + abs(blade_half * 2 * sin),
                             abs(blade_len * sin) + abs(blade_half * 2 * cos),
                             "wood-dark"))
        if canopy_h > 0:
            parts.append(box(0, 0, height - canopy_h, height, hub_r, hub_r, "metal"))
            parts.append(box(0, 0, motor_top, height - canopy_h, hub_r * 0.4, hub_r * 0.4,
                             "metal"))
        return tuple(strokes), tuple(parts)

    return build


def linear_light() -> Builder:
    """A linear fixture: housing rectangle, lit field, centreline.

    One builder covers the tube, the wall lamp and the mirror light — at plan scale all
    three are a rectangle with a lit centre, and the difference between them is the
    mounting and the schedule row, not the glyph.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        end_cap = clamp(width * 0.06, 0.0, width * 0.12)
        lit_w = width - 2 * end_cap
        lit_d = depth * 0.62
        strokes = [rect(0, 0, width, depth, fill="luminaire-housing"),
                   rect(0, 0, lit_w, lit_d, fill="lamp", weight=DETAIL_WEIGHT),
                   line((-lit_w / 2, 0), (lit_w / 2, 0))]
        lens_t = min(height * 0.45, height)
        parts = [box(0, 0, lens_t, height, width, depth, "luminaire-housing"),
                 box(0, 0, 0.0, lens_t, lit_w, lit_d, "lamp")]
        return tuple(strokes), tuple(parts)

    return build


def suspended_linear_light() -> Builder:
    """A cable-hung linear tube: shallow body below, two supports above.

    The declared height is the complete ceiling-to-fixture assembly, not the depth of
    the lamp body.  Keeping the cables as separate parts makes that drop legible in 3D
    while the plan glyph remains the same compact linear-fixture convention.
    """

    linear_strokes = linear_light()

    def build(width: float, depth: float, height: float) -> Geometry:
        strokes, _ = linear_strokes(width, depth, height)
        body_h = min(height * 0.12, 0.0762)  # 3 in. maximum shallow tube housing
        lens_h = body_h * 0.45
        end_cap = clamp(width * 0.06, 0.0, width * 0.12)
        lit_w = width - 2 * end_cap
        lit_d = depth * 0.62
        support_inset = min(width * 0.06, 0.1016)  # no more than 4 in. from an end
        cable_t = min(depth * 0.08, 0.003175)  # 1/8 in. black suspension cable
        parts: list[Part] = [
            box(0, 0, lens_h, body_h, width, depth, "luminaire-housing"),
            box(0, 0, 0.0, lens_h, lit_w, lit_d, "lamp"),
        ]
        for x in (-width / 2 + support_inset, width / 2 - support_inset):
            parts.append(box(x, 0, body_h, height, cable_t, cable_t, "luminaire-housing"))
        return tuple(strokes), tuple(parts)

    return build


LIGHTING_SYMBOLS: dict[str, Builder] = {
    "recessed-can": recessed_can(),
    "panel-light": panel_light(),
    "sconce": sconce(throw="down"),
    "sconce-updown": sconce(throw="updown"),
    "sconce-spot": sconce(throw="spot"),
    "pendant": pendant(),
    "chandelier": chandelier(arms=6),
    "ceiling-fan-light": ceiling_fan_light(blades=4),
    "linear-light": linear_light(),
    "suspended-linear-light": suspended_linear_light(),
}
