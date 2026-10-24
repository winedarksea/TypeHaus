"""ÄNGSJÖN/ORRSJÖN and Chulton, with their distinct fronts and base construction.

Cabinet/top envelopes follow the catalog. Bowl mouths and decorative profiles are visual
approximations from product photos, independent of the authored plumbing connection points.
"""

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box
from typehaus.model.placeable_symbols._lav_waste import lav_waste
from typehaus.model.placeable_symbols._sektion_fronts import axstad_front, round_bar
from typehaus.model.placeable_symbols._solid_surface_vanity import deck_height, solid_surface_vanity

REVEAL_IN = 0.125
WALL_IN = 0.75
ORRSJON_BOWL_IN = (22.0, 13.0, 5.0)
CHULTON_BOWL_IN = (18.0, 12.0, 6.0)


def drawer_vanity(
    width: float, depth: float, height: float, *, door_fronts: bool = False, faucet: str = "genta"
) -> Geometry:
    bowl = CHULTON_BOWL_IN if door_fronts else ORRSJON_BOWL_IN
    thickness_in = 0.75 if door_fronts else 2.5
    strokes, parts = solid_surface_vanity(
        width,
        depth,
        height,
        fronts=(0.5, 0.5),
        faucet=faucet,
        basin_size_in=bowl,
        top_thickness_in=thickness_in,
        include_waste=False,
    )
    deck = deck_height(height, faucet)
    scale = min(
        width / (30.9375 if door_fronts else 37),
        depth / (22.4375 if door_fronts else 21.75),
        deck / (36 if door_fronts else 27.625),
    )
    wall, reveal = WALL_IN * scale, REVEAL_IN * scale
    case_width = width - (0.9375 if door_fronts else 1) * scale
    case_depth = depth - (1.25 if door_fronts else 0.75) * scale
    # Remove the borrowed SEKTION body, including its recessed-panel mesh faces.
    body = [part for part in parts if part["color"] != "appliance-white"]
    cabinet_top = deck - thickness_in * scale
    bottom = 3 * scale if door_fronts else 0
    cabinet_y = (depth - case_depth) / 2
    front_y = depth / 2 - case_depth + wall / 2
    for sign in (-1, 1):
        body.append(
            box(
                sign * (case_width - wall) / 2,
                cabinet_y,
                bottom,
                cabinet_top,
                wall,
                case_depth,
                "appliance-white",
            )
        )
    body.append(box(0, cabinet_y, bottom, bottom + wall, case_width, case_depth, "appliance-white"))
    if door_fronts:
        drawer_bottom = cabinet_top * 0.70
        for sign in (-1, 1):
            x = sign * case_width / 4
            body.extend(
                axstad_front(
                    case_width / 2 - reveal,
                    front_y - wall / 2,
                    wall,
                    bottom + wall,
                    drawer_bottom - reveal,
                    center_x=x,
                )
            )
            # Raised center panels, rather than AXSTAD's recessed center.
            body.append(
                box(
                    x,
                    front_y - wall / 2,
                    bottom + 3 * scale,
                    drawer_bottom - 2 * scale,
                    case_width / 2 - 4 * scale,
                    wall / 2,
                    "appliance-white",
                )
            )
        body.extend(
            axstad_front(
                case_width - reveal,
                front_y - wall / 2,
                wall,
                drawer_bottom + reveal,
                cabinet_top - reveal,
            )
        )
        body.append(
            box(
                0,
                front_y - wall / 2,
                drawer_bottom + 2 * scale,
                cabinet_top - 2 * scale,
                case_width - 4 * scale,
                wall / 2,
                "appliance-white",
            )
        )
        for z in (bottom + wall, drawer_bottom, cabinet_top):
            body.append(
                box(
                    0,
                    front_y,
                    z - wall / 2,
                    z + wall / 2,
                    case_width,
                    wall * 1.3,
                    "appliance-white",
                )
            )
        # Four feet and a raised apron leave a visible opening under the cabinet.
        for sign in (-1, 1):
            for side in (-1, 1):
                body.append(
                    box(
                        sign * (case_width / 2 - scale),
                        cabinet_y + side * (case_depth / 2 - scale),
                        0,
                        bottom,
                        2 * scale,
                        2 * scale,
                        "appliance-white",
                    )
                )
        body.append(
            box(0, depth / 2 - wall / 2, deck, deck + 3.3125 * scale, width, wall, "porcelain")
        )
        pull_y = front_y - wall / 2 - 0.5 * scale
        z = (drawer_bottom + cabinet_top) / 2
        body.append(
            round_bar((-2.5 * scale, pull_y, z), (2.5 * scale, pull_y, z), 0.15 * scale, "chrome")
        )
        for sign in (-1, 1):
            x, z = sign * scale, drawer_bottom - 4.5 * scale
            body.append(
                round_bar(
                    (x, pull_y, z - 2.5 * scale),
                    (x, pull_y, z + 2.5 * scale),
                    0.15 * scale,
                    "chrome",
                )
            )
    else:
        for index in range(2):
            low = index * cabinet_top / 2 + reveal
            high = (index + 1) * cabinet_top / 2 - reveal
            body.append(box(0, front_y, low, high, case_width - reveal, wall, "appliance-white"))
            # ÄNGSJÖN's integrated recessed grip runs across each slab drawer.
            body.append(
                box(
                    0,
                    front_y - wall / 2,
                    high - reveal,
                    high,
                    case_width - 2 * wall,
                    reveal,
                    "casework-shadow",
                )
            )
    if not door_fronts:
        body = [{**part, "color": "high-gloss-white"}
                if part["color"] == "appliance-white" else part for part in body]
    bowl_shell = next(p for p in body if p["color"] == "porcelain" and "mesh" in p)
    body.extend(lav_waste(depth, deck, bowl_shell["center"][2] - bowl_shell["size"][2]/2,
                          bowl_shell["center"][1], space_saving=not door_fronts))
    return strokes, tuple(body)
