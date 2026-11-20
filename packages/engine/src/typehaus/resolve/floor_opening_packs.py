"""A floor-opening trimmer pack that stands on a wall top along its run.

``resolve/floor_openings`` runs a pack carrying a header bearing to bearing. Where the pack
stands on a wall's top (a foundation wall's sill, a bearing wall's plates) the whole way, it
spans nothing and carries the header straight down, so it stops just past that header's
hanger and leaves the wall top beyond it free (the wall-top ties of ``joints/wall_top``).
"""

from __future__ import annotations

from typehaus.quantities import inch

#: A pack standing on a wall top stops this far past its last header: a face-mount hanger's
#: 2" flange (C-C-2026 p. 155, HHUS410) and 1" of trimmer beyond it for the flange nails.
_PAST_HEADER_M = inch(3.0).meters
#: A wall top this far under the deck still seats it: a sill and its gasket.
_SEAT_DROP_M = inch(2.0).meters


def sill_borne_run(model, seat_z, along_x, pack, run, header_runs, edges) -> tuple:
    """A pack standing on a wall top over its whole run spans nothing: it stops
    ``_PAST_HEADER_M`` past the header it carries instead of running on to a bearing line."""
    run0, run1 = run
    for side, (runs, edge) in enumerate(zip(header_runs, edges, strict=True)):
        carried = [r.width_m for r in runs
                   if r.start_m <= pack[1] + 1e-9 and r.end_m >= pack[0] - 1e-9]
        if not carried:
            continue
        if side == 0:
            stop = edge - max(carried) - _PAST_HEADER_M
            if stop > run0 + 1e-9 and _on_wall_top(model, seat_z, along_x, pack, stop, run1):
                run0 = stop
        else:
            stop = edge + max(carried) + _PAST_HEADER_M
            if stop < run1 - 1e-9 and _on_wall_top(model, seat_z, along_x, pack, run0, stop):
                run1 = stop
    return run0, run1


def _on_wall_top(model, seat_z, along_x, pack, lo, hi) -> bool:
    """Do walls seating this deck, end to end, stand under ``pack`` (across) over ``lo..hi``
    (along), their structure layer wide enough to take the whole pack? A released interior
    partition (its plate 3/4" under the deck, ``resolve/partition_top``) seats nothing."""
    from typehaus.resolve.partition import is_interior_partition

    across, along = (1, 0) if along_x else (0, 1)
    spans = []
    for wall in model.walls:
        if is_interior_partition(model, wall, frozenset()):
            continue
        top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
        (a0, a1) = wall.axis[0][:2], wall.axis[1][:2]
        if not seat_z - _SEAT_DROP_M - 1e-3 <= top <= seat_z + 1e-3 \
                or abs(a0[across] - a1[across]) > 1e-6:
            continue
        points = [p for layer in wall.layers if layer.function == "structure"
                  for p in layer.polygon]
        if points and min(p[across] for p in points) <= pack[0] + 1e-9 \
                and max(p[across] for p in points) >= pack[1] - 1e-9:
            spans.append((min(p[along] for p in points), max(p[along] for p in points)))
    cursor = lo
    for start, end in sorted(spans):
        if start > cursor + 1e-9:
            break
        cursor = max(cursor, end)
    return bool(spans) and cursor >= hi - 1e-9
