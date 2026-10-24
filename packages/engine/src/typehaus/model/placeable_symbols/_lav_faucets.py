"""Genta LX 6702 and Indy KBF-1401 silhouettes from the archived maker sheets.

Reach and height are published dimensions; surface profiles are illustrative. The Genta
envelope includes raised-handle travel, while its spout sits much lower than its lever.
"""

from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.placeable_symbols._sektion_fronts import round_bar

INCH_M = 0.0254
FAUCET_DIMENSIONS_IN = {
    "genta": (8.4375, 4.5625, 4.0625, 1.5625),
    "indy": (6.25, 5.125, 4.625, 1.375),
}


def faucet_band(height: float, faucet: str = "genta") -> float:
    return min(FAUCET_DIMENSIONS_IN[faucet][0] * INCH_M, height * 0.24)


def _blade(points, width):
    """Extrude a side profile across the faucet to preserve the sloping spout."""
    vertices = [(x, y, z) for x in (-width / 2, width / 2) for y, z in points]
    count = len(points)
    triangles = []
    for index in range(1, count - 1):
        triangles.extend(((0, index + 1, index), (count, count + index, count + index + 1)))
    for index in range(count):
        following = (index + 1) % count
        triangles.extend(
            ((index, following, following + count), (index, following + count, index + count))
        )
    return mesh_part(vertices, triangles, "faucet")


def lav_faucet(width, depth, deck, height, center_y, faucet="genta"):
    overall, reach_in, outlet_in, body_in = FAUCET_DIMENSIONS_IN[faucet]
    scale = min((height - deck) / overall, width / 5, depth / 8)
    reach, outlet, radius = reach_in * scale, outlet_in * scale, body_in * scale / 2
    top = deck + overall * scale
    tip = center_y - reach
    parts = [
        round_bar(
            (0, center_y, deck + scale * 0.15),
            (0, center_y, deck + (7.125 if faucet == "genta" else overall - 0.5) * scale),
            radius,
            "faucet",
        ),
        round_bar(
            (0, center_y, deck + scale * 0.08), (0, center_y, deck + scale * 0.3), scale, "faucet"
        ),
    ]
    if faucet == "genta":
        # Broad descending outlet and a separate top paddle distinguish the Genta.
        profile = [
            (center_y, deck + 5.3125 * scale),
            (tip + 0.7 * scale, deck + 5.3125 * scale),
            (tip, deck + 4.55 * scale),
            (tip, deck + outlet),
            (tip + 0.95 * scale, deck + 4.72 * scale),
            (center_y, deck + 4.72 * scale),
        ]
        parts.append(_blade(profile, body_in * scale))
        parts.append(
            _blade(
                [
                    (center_y + 0.6 * scale, deck + 7.125 * scale),
                    (center_y - 3.1 * scale, top - 0.2 * scale),
                    (center_y - 3.1 * scale, top),
                    (center_y + 0.6 * scale, deck + 7.325 * scale),
                ],
                body_in * scale,
            )
        )
    else:
        profile = [
            (center_y, deck + 3.65 * scale),
            (tip, deck + outlet),
            (tip, deck + outlet + 0.45 * scale),
            (center_y, deck + 4.15 * scale),
        ]
        parts.append(_blade(profile, 1.65 * scale))
        parts.append(
            _blade(
                [
                    (center_y + 0.5 * scale, top - 0.5 * scale),
                    (center_y - 3.375 * scale, top - 0.25 * scale),
                    (center_y - 3.375 * scale, top),
                    (center_y + 0.5 * scale, top - 0.25 * scale),
                ],
                1.5 * scale,
            )
        )
    return parts
