"""SUNNERSTA's stainless bowl and white open frame; sink emitted by its own fixture.

The house keeps the bowl separate for plumbing. Frame geometry must therefore leave the
right-hand sink station open instead of drawing a second sink or a closed cabinet.
"""

from typehaus.model.placeable_symbols._frame import box, rect
from typehaus.model.placeable_symbols._lav_faucets import lav_faucet
from typehaus.model.placeable_symbols._lav_waste import lav_waste
from typehaus.model.placeable_symbols._solid_surface_vanity import deck_height, solid_surface_vanity

FRAME_TOP_FRACTION = 36 / 54.75
FRAME_TUBE_FRACTION = 0.875 / 44.125
SINK_STATION_FRACTION = 18 / 44.125


def sunnersta_frame(width, depth, height):
    rim = height * FRAME_TOP_FRACTION
    tube = min(width, depth) * FRAME_TUBE_FRACTION
    parts = []
    for x in (-width / 2 + tube, width / 2 - tube):
        for y in (-depth / 2 + tube, depth / 2 - tube):
            parts.append(box(x, y, 0, rim, tube, tube, "appliance-white"))
        parts.append(box(x, depth / 2 - tube, rim, height, tube, tube, "appliance-white"))
    for z in (height - tube, rim - tube, height * 0.15):
        parts.append(box(0, depth / 2 - tube, z, z + tube, width - tube, tube, "appliance-white"))
    parts.append(
        box(
            0, 0, height * 0.15, height * 0.15 + tube, width - tube, depth - tube, "appliance-white"
        )
    )
    # House sink station is approximate; keep this opening aligned with its fixture.
    sink_width, sink_depth = width * SINK_STATION_FRACTION, depth * 14 / 22
    sink_x, sink_y = width * 11.0625 / 44.125, depth * .115 / 22
    left, right = sink_x - sink_width / 2, sink_x + sink_width / 2
    front, back = sink_y - sink_depth / 2, sink_y + sink_depth / 2
    for low, high in ((-width / 2, left), (right, width / 2)):
        parts.append(box((low + high) / 2, 0, rim - tube, rim,
                         high - low, depth, "appliance-steel"))
    for low, high in ((-depth / 2, front), (back, depth / 2)):
        parts.append(box(sink_x, (low + high) / 2, rim - tube, rim,
                         sink_width, high - low, "appliance-steel"))
    return (rect(0, 0, width, depth),), tuple(parts)


def sunnersta_sink(width, depth, height):
    strokes, borrowed = solid_surface_vanity(
        width, depth, height, faucet="indy", basin_size_in=(15, 10, 6),
        include_waste=False, top_thickness_in=0.0625
    )
    parts = [
        {**p, "color": "appliance-steel"} if p["color"] == "porcelain" else p
        for p in borrowed
        if p["color"] not in {"appliance-white", "faucet"}
    ]
    deck = deck_height(height, "indy")
    faucet_y = depth / 2 - min(1.25 * .0254, depth * .1)
    parts.extend(lav_faucet(width, depth, deck, height, faucet_y, "indy"))
    basin = next(p for p in parts if p["color"] == "appliance-steel" and "mesh" in p)
    bottom = basin["center"][2] - basin["size"][2] / 2
    parts.extend(lav_waste(depth, deck, bottom, basin["center"][1], base_in=16))
    return strokes, tuple(parts)
