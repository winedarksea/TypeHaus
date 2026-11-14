"""AP CT426CFGT40 china, S5 seat and WT173M concealed assembly.

SS-02352 v.01 pp.2–3 supplies the envelopes and connection centres. Internal tank,
frame sections and moulded contours are visual approximations, not fabrication geometry.
The footprint remains the china: concealed parts deliberately extend behind +y and
below the bowl datum (3 in. AFF). Wood bay framing stays in resolve/framing/carriers.py.
"""

from __future__ import annotations

from math import cos, pi, sin

from typehaus.model.placeable_symbols._frame import Part, box, ellipse
from typehaus.model.placeable_symbols._mesh import mesh_part, outward
from typehaus.model.placeable_symbols._round_hardware import round_cylinder

SEGMENTS = 64
BOWL_WIDTH_IN = 14.9375
BOWL_DEPTH_IN = 21.25
BOWL_HEIGHT_IN = 13.125
BOWL_BASE_AFF_IN = 3.0
FRAME_WIDTH_IN = 22.8125
FRAME_TOP_AFF_IN = 45.3125
FRAME_DEPTH_IN = 5.5
# Each contour: width fraction, front depth fraction, rear depth fraction, centre y,
# and elevation in inches above the china's lowest point. Last contours form the basin.
CHINA_SECTIONS = (
    (.54, .80, .74, .13, 0),
    (.66, .88, .78, .11, 1.75),
    (.84, 1.02, .84, .08, 7.5),
    (.98, 1.11, .87, .065, 12.5),
    (1.0, 1.12, .88, .06, 13.125),
    (.74, .67, .23, .04, 13.125),
    (.68, .62, .21, .04, 11.75),
    (.38, .32, .14, .09, 4.5),
    (.20, .16, .10, .15, 3.5),
)
SEAT_SECTIONS = (
    (.99, 1.10, .84, .055, 13.25),
    (.99, 1.10, .84, .055, 14.0),
    (.75, .66, .22, .035, 14.0),
    (.75, .66, .22, .035, 13.25),
)


def _contoured_shell(width, depth, vertical_scale, sections, color, *, ring=False) -> Part:
    positions = []
    for span, front, rear, center, elevation in sections:
        for segment in range(SEGMENTS):
            angle = 2 * pi * segment / SEGMENTS
            longitudinal_radius = rear if sin(angle) >= 0 else front
            positions.append((width * span / 2 * cos(angle),
                              depth * (center + longitudinal_radius / 2 * sin(angle)),
                              elevation * vertical_scale))
    triangles = []
    joins = len(sections) if ring else len(sections) - 1
    for level in range(joins):
        next_level = (level + 1) % len(sections)
        for segment in range(SEGMENTS):
            following = (segment + 1) % SEGMENTS
            a, b = level * SEGMENTS + segment, level * SEGMENTS + following
            c, d = next_level * SEGMENTS + segment, next_level * SEGMENTS + following
            triangles.extend(((a, b, c), (b, d, c)))
    if not ring:
        for level in (0, len(sections) - 1):
            center = len(positions)
            contour = positions[level * SEGMENTS:(level + 1) * SEGMENTS]
            positions.append(tuple(sum(p[i] for p in contour) / SEGMENTS for i in range(3)))
            for segment in range(SEGMENTS):
                a = level * SEGMENTS + segment
                b = level * SEGMENTS + (segment + 1) % SEGMENTS
                triangles.append((center, b, a) if level == 0 else (center, a, b))
    return mesh_part(positions, outward(positions, triangles), color)


def toto_ap(width: float, depth: float, height: float):
    """Product geometry; independent width/depth/height scaling preserves test-size support."""
    sx, sy, sz = width / BOWL_WIDTH_IN, depth / BOWL_DEPTH_IN, height / BOWL_HEIGHT_IN
    wall_y = depth / 2

    def component(cx, cy, bottom, top, span, thickness, color, role):
        part = box(cx * sx, wall_y + cy * sy, bottom * sz, top * sz,
                   span * sx, thickness * sy, color)
        part['role'] = role
        return part

    def cylinder(center, radius, length, axis, color):
        part = round_cylinder(center, radius, length, axis=axis, color=color)
        positions = [(x * sx, wall_y + y * sy, z * sz)
                     for x, y, z in part["mesh"]["positions"]]
        return mesh_part(positions, list(part["mesh"]["triangles"]), color)

    parts = [_contoured_shell(width, depth, sz, CHINA_SECTIONS, 'porcelain'),
             _contoured_shell(width, depth, sz, SEAT_SECTIONS, 'plastic-white', ring=True)]
    # Rear electronics housing and the lid's crowned, closed surface sit above the china.
    parts.append(component(0, -3.0, 13.25, 16.75, 14.5, 5.5,
                           'plastic-white', 'washlet-housing'))
    lid_sections = ((.98, 1.09, .82, .05, 14.125),
                    (.98, 1.09, .82, .05, 14.5),
                    (.90, 1.01, .76, .05, 14.75))
    parts.append(_contoured_shell(width, depth, sz, lid_sections, 'high-gloss-white'))
    for sign in (-1, 1):
        parts.extend([
            component(sign * 10.5, 3.25, -3, 42.3125, 1.8125, FRAME_DEPTH_IN,
                      'metal-black', 'carrier-upright'),
            component(sign * 10.5, 3.25, -3, -2.6, 1.8125, FRAME_DEPTH_IN,
                      'metal', 'carrier-foot'),
        ])
    for bottom, top in ((8.0, 9.5), (19, 20.25), (40.75, 42.3125)):
        parts.append(component(0, 3.25, bottom, top, FRAME_WIDTH_IN, FRAME_DEPTH_IN,
                               'metal-black', 'carrier-crossbar'))
    parts.append(component(0, 3.4, 20.25, 40.75, 18.5, 4.5,
                           'plastic-white', 'concealed-cistern'))
    parts.append(component(0, .7, 29.75, 35, 8.0, 1.4,
                           'metal-black', 'cistern-service-opening'))
    parts.append(component(0, -.1875, 29.25, 35.5, 9.5, .375,
                           'metal', 'flush-plate'))
    for cx, radius in ((-1.5, 1.3), (1.8, .95)):
        button = cylinder((cx, -.42, 32.2), radius, .12, axis=1, color='chrome')
        button['role'] = 'flush-button'
        parts.append(button)
    # Straight connectors and the swept waste bend stay inside the wet wall. The drop
    # centre is the fixture port's +13 7/8 in., 3 1/4 in. behind the finish face.
    for elevation, radius, role in ((10.875, .875, 'flush-inlet'),
                                    (7.8125, 1.5, 'waste-outlet')):
        connector = cylinder((0, .9, elevation), radius, 1.8, axis=1, color='metal-black')
        connector['role'] = role
        parts.append(connector)
    for sign in (-1, 1):
        rod = cylinder((sign * 3.5433, .2, 9.625), .1875, 2.5, axis=1, color='metal')
        rod['role'] = 'bowl-mounting-rod'
        parts.append(rod)
    supply = cylinder((-8.8, 3.25, 8.75), .42, 2.0, axis=2, color='brass')
    supply['role'] = 'carrier-cold-inlet'
    parts.append(supply)
    bend_radius = 2.35
    bend_segments = 16
    positions, triangles = [], []
    for index in range(bend_segments + 1):
        angle = index * pi / (2 * bend_segments)
        for segment in range(SEGMENTS):
            radial_angle = segment * 2 * pi / SEGMENTS
            radial_offset = 1.5 * sin(radial_angle)
            positions.append((1.5 * sx * cos(radial_angle),
                              wall_y + (.9 + (bend_radius + radial_offset) * sin(angle)) * sy,
                              (7.8125 - bend_radius
                               + (bend_radius + radial_offset) * cos(angle)) * sz))
    for index in range(bend_segments):
        for segment in range(SEGMENTS):
            a = index * SEGMENTS + segment
            b = index * SEGMENTS + (segment + 1) % SEGMENTS
            triangles.extend(((a, b, a + SEGMENTS), (b, b + SEGMENTS, a + SEGMENTS)))
    for level in (0, bend_segments):
        contour = positions[level * SEGMENTS:(level + 1) * SEGMENTS]
        center = len(positions)
        positions.append(tuple(sum(p[i] for p in contour) / SEGMENTS for i in range(3)))
        for segment in range(SEGMENTS):
            a = level * SEGMENTS + segment
            b = level * SEGMENTS + (segment + 1) % SEGMENTS
            triangles.append((center, b, a) if level == 0 else (center, a, b))
    bend = mesh_part(positions, outward(positions, triangles), 'metal-black')
    bend['role'] = 'carrier-waste-bend'
    parts.append(bend)
    drop_top = 7.8125 - bend_radius
    drop = cylinder((0, 3.25, (drop_top - 3) / 2),
                    1.5, drop_top + 3, axis=2, color='metal-black')
    drop['role'] = 'carrier-waste-drop'
    parts.append(drop)
    strokes = (ellipse(0, 0, width / 2, depth / 2, fill='porcelain'),)
    return strokes, tuple(parts)
