"""Free vertical panel edges: a freestanding screen's open ends."""

from __future__ import annotations

from typehaus.library.trim.catalog import PROFILES
from typehaus.model.cladding_trim import TrimCondition
from typehaus.resolve.cladding_trim.runs import add_vertical_run, kit_faces


def resolve_screen_ends(model) -> None:
    """One kit end trim on each open end of a panel-clad wall, full panel height."""
    entries = list(kit_faces(model, TrimCondition.SCREEN_END))
    for junction in model.junctions:
        if junction.kind != "open_end":
            continue
        for incident in junction.incidents:
            for face, key in entries:
                if face.wall.tag != incident.wall_tag:
                    continue
                station = sum(p * c for p, c in zip(junction.point, face.d, strict=True))
                at_lo = abs(station - face.lo) < abs(station - face.hi)
                add_vertical_run(model, face, PROFILES[key], key,
                                 f"TRIM-{face.wall.tag}-END-{'LO' if at_lo else 'HI'}",
                                 face.lo if at_lo else face.hi, face.z0, face.z1,
                                 1.0 if at_lo else -1.0)
