"""Resolve actual on-edge slat sections without inventing column/footing demand."""

import math

from typehaus.findings import element_error
from typehaus.model.screens import SlatScreen
from typehaus.resolve.model import ResolvedSolid


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
            count = math.floor((length + gap) / (face + gap) + 1e-9)
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
