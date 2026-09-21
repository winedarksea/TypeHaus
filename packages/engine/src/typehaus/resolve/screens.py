"""Resolve actual on-edge slat sections without inventing column/footing demand."""

import math

from typehaus.findings import element_error
from typehaus.model.screens import SlatScreen
from typehaus.resolve.model import ResolvedSolid


def slat_count(screen: SlatScreen) -> int:
    """How many slats this screen resolves to. ** ONE rule, because it is not obvious. **

    The run is packed face-to-gap-to-face and centred, so the count is the number of
    ``face + gap`` pitches that fit once the trailing gap is added back. Anything that needs
    a slat's weight, its part count or its spacing reads this rather than restating it —
    ``resolve/assembly_weight._slat_screen_plf`` is the second caller.
    """
    x0, y0 = screen.start.xy_m
    x1, y1 = screen.end.xy_m
    length = math.hypot(x1 - x0, y1 - y0)
    face, gap = screen.slat_face.meters, screen.clear_gap.meters
    if length <= 0.0 or face <= 0.0 or gap < 0.0 or length < face:
        return 0
    return math.floor((length + gap) / (face + gap) + 1e-9)


def resolve_screens(model):
    findings = []
    for storey in model.plan.storeys:
        for screen in model.plan.storey_elements(storey.tag):
            if not isinstance(screen, SlatScreen):
                continue
            x0, y0 = screen.start.xy_m
            x1, y1 = screen.end.xy_m
            length = math.hypot(x1 - x0, y1 - y0)
            face, depth, gap = (
                v.meters for v in (screen.slat_face, screen.slat_depth, screen.clear_gap)
            )
            if min(face, depth, screen.height.meters) <= 0 or gap < 0 or length < face:
                findings.append(
                    element_error(
                        "integrity.slat_screen", "invalid slat screen dimensions", screen.tag
                    )
                )
                continue
            if model.plan.by_tag(screen.supported_by) is None:
                findings.append(
                    element_error("integrity.slat_screen", "missing screen support", screen.tag)
                )
                continue
            dx, dy = (x1 - x0) / length, (y1 - y0) / length
            count = slat_count(screen)
            margin = (length - (count * face + (count - 1) * gap)) / 2
            for index in range(count):
                station = margin + face / 2 + index * (face + gap)
                cx, cy = x0 + station * dx, y0 + station * dy
                outline = tuple(
                    (cx + along * dx - across * dy, cy + along * dy + across * dx)
                    for along, across in (
                        (-face / 2, -depth / 2),
                        (face / 2, -depth / 2),
                        (face / 2, depth / 2),
                        (-face / 2, depth / 2),
                    )
                )
                model.solids.append(
                    ResolvedSolid(
                        f"{screen.uid}-s{index:03d}",
                        f"{screen.tag}-SLAT-{index:02d}",
                        storey.tag,
                        "screen_slat",
                        outline,
                        screen.base_elevation.meters,
                        screen.base_elevation.meters + screen.height.meters,
                        screen.assembly,
                    )
                )
    return findings
