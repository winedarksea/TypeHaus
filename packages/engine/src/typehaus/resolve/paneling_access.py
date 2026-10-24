"""Visible apron joints around a tub enclosure's removable service leaves."""

from math import hypot


def tub_access_cutouts(model):
    """Wall-local rectangles, including each leaf's perimeter reveal.

    Keep the gross apron takeoff: the removable leaves are cut from the same sheet.
    Only the fixed-face geometry loses these rectangles.
    """
    canvas = {item.tag: item for item in model.canvas_objects}
    cutouts = {}
    for storey in model.plan.storeys:
        for fixture in model.plan.storey_elements(storey.tag):
            spec = getattr(fixture, "tub_enclosure", None)
            if spec is None:
                continue
            reveal = spec.access_panel_reveal.meters
            for ref in spec.access_panel_refs:
                panel = canvas.get(ref)
                if panel is None:
                    continue  # The enclosure resolver reports unresolved references.
                wall = model.wall(panel.attachment_wall)
                if wall is None or wall.tag not in spec.knee_wall_refs:
                    continue
                (x0, y0), (x1, y1) = wall.axis
                length = hypot(x1 - x0, y1 - y0)
                stations = [((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / length
                            for x, y in panel.footprint]
                cutouts.setdefault((wall.tag, panel.attachment_face), []).append((
                    min(stations) - reveal, max(stations) + reveal,
                    panel.body_z0_m - wall.base_ref_z_m - reveal,
                    panel.body_z1_m - wall.base_ref_z_m + reveal))
    return cutouts
