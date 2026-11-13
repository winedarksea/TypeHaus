"""EG4 storage equipment, front toward -y; cosmetic stations are schematic.

Appearance: 12kPV spec sheet v1.0.9 cover and Indoor 280Ah quick-start
v1.4.0 cover. Size comes from the caller, never from these visual proportions.
"""

import math

from typehaus.model.placeable_symbols._frame import box, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

CORNER_SEGMENTS = 6
STATUS_RING_SEGMENTS = 32


def _rounded_panel(x, y, z, width, thickness, height, radius, color):
    """Extrude a rounded front outline along depth, including closed end caps."""
    radius = min(radius, width / 2, height / 2)
    outline = []
    for cx, cz, start in ((width / 2 - radius, height / 2 - radius, 0),
                          (-width / 2 + radius, height / 2 - radius, 90),
                          (-width / 2 + radius, -height / 2 + radius, 180),
                          (width / 2 - radius, -height / 2 + radius, 270)):
        for step in range(CORNER_SEGMENTS + 1):
            # Capsule ends share tangent points; avoid zero-area side triangles.
            angle = math.radians(start + 90 * step / CORNER_SEGMENTS)
            point = (x + cx + radius * math.cos(angle), z + cz + radius * math.sin(angle))
            if not outline or math.dist(point, outline[-1]) > width * 1e-10:
                outline.append(point)
    if math.dist(outline[0], outline[-1]) < width * 1e-10:
        outline.pop()
    count = len(outline)
    vertices = [(px, face, pz) for face in (y - thickness / 2, y + thickness / 2)
                for px, pz in outline]
    vertices += [(x, y - thickness / 2, z), (x, y + thickness / 2, z)]
    triangles = []
    for index in range(count):
        following = (index + 1) % count
        triangles.extend(((2 * count, following, index),
                          (2 * count + 1, index + count, following + count),
                          (index, following, following + count),
                          (index, following + count, index + count)))
    return mesh_part(vertices, outward(vertices, triangles), color)


def eg4_12kpv(width, depth, height):
    # Reserve a thin front layer and side margins for controls within the authored envelope.
    badge_diameter = min(width * .20, height * .25)
    parts = [
        _rounded_panel(0, depth * .025, height / 2, width * .94, depth * .95,
                       height, width * .025, "eg4-charcoal"),
        _rounded_panel(0, -depth * .465, height * .71, width * .94, depth * .05,
                       height * .58, width * .025, "appliance-steel"),
        _rounded_panel(0, -depth * .49, height * .58, width * .31, depth * .02,
                       height * .18, width * .01, "screen"),
        _rounded_panel(0, -depth * .49, height * .835, badge_diameter, depth * .02,
                       badge_diameter, badge_diameter / 2, "metal-black"),
    ]
    # Side disconnect, Wi-Fi adapter and the two lower-cover catches are the main silhouette cues.
    for x, z, span_x, span_z in ((-.485, .48, .03, .055),
                                (-.485, .25, .03, .065),
                                (.485, .08, .03, .045), (.485, .32, .03, .045)):
        parts.append(box(x * width, -depth * .22, (z - span_z / 2) * height,
                         (z + span_z / 2) * height, span_x * width, depth * .18,
                         "metal-black"))
    parts.append(box(-width * .485, -depth * .22, height * .12, height * .22,
                     width * .018, depth * .065, "eg4-charcoal"))
    return (rect(0, 0, width, depth, fill="appliance-steel"),), tuple(parts)


def eg4_wallmount_indoor(width, depth, height):
    parts = [
        _rounded_panel(0, depth * .02, height * .493, width, depth * .96,
                       height * .986, width * .025, "appliance-steel"),
        _rounded_panel(0, -depth * .465, height * .705, width * .38, depth * .03,
                       height * .435, width * .19, "chrome"),
        _rounded_panel(0, -depth * .485, height * .705, width * .36, depth * .01,
                       height * .425, width * .18, "metal-black"),
        _rounded_panel(0, -depth * .495, height * .80, width * .23, depth * .01,
                       height * .078, width * .005, "screen"),
    ]
    # A silver badge inside a green SOC arc makes the long black control capsule recognizable.
    badge_radius = min(width * .135, height * .12)
    parts.append(_rounded_panel(0, -depth * .495, height * .59,
                                badge_radius * 2, depth * .01, badge_radius * 2,
                                badge_radius, "eg4-charcoal"))
    outer_radius = min(width * .158, height * .14)
    inner_radius = outer_radius * .148 / .158
    vertices = [(radius * math.cos(angle), y, height * .59 + radius * math.sin(angle))
                for y in (-depth * .50, -depth * .49)
                for radius in (inner_radius, outer_radius)
                for angle in (math.radians(145 + 250 * index / STATUS_RING_SEGMENTS)
                              for index in range(STATUS_RING_SEGMENTS + 1))]
    count = STATUS_RING_SEGMENTS + 1
    triangles = []
    for index in range(STATUS_RING_SEGMENTS):
        for a, b, c, d in ((index, index + 1, index + count + 1, index + count),
                           (index + 2 * count, index + 3 * count,
                            index + 3 * count + 1, index + 2 * count + 1),
                           (index, index + 2 * count, index + 2 * count + 1, index + 1),
                           (index + count, index + count + 1,
                            index + 3 * count + 1, index + 3 * count)):
            triangles.extend(((a, b, c), (a, c, d)))
    for index in (0, STATUS_RING_SEGMENTS):
        a, b, c, d = index, index + count, index + 3 * count, index + 2 * count
        faces = ((a, b, c), (a, c, d))
        triangles.extend(faces if index == 0 else tuple((a, c, b) for a, b, c in faces))
    parts.append(mesh_part(vertices, outward(vertices, triangles), "eg4-status-green"))
    # Top terminal covers; omit temporary lifting handles and the optional conduit box.
    for x, color in ((-.25, "metal-black"), (.25, "electrical-orange")):
        parts.append(box(width * x, depth * .14, height * .986, height,
                         width * .055, depth * .08, color))
    return (rect(0, 0, width, depth, fill="appliance-steel"),), tuple(parts)
