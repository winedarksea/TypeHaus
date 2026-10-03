"""Five suspended LED ribbons that undulate in elevation, with a brass canopy."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._curved_band import curved_elevation_band
from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, Part, Stroke, box, rect

# 64 chords per sine cycle keep the silhouette error below 0.13 mm at the 4-inch amplitude.
WAVE_SAMPLES_PER_CYCLE = 64


def wave_chandelier(*, strips: int = 5, waves: float = 2.0, samples: int | None = None) -> Builder:
    """Flat LED strips side by side in plan, each undulating up and down, out of phase.

    Every strip is a sine in ELEVATION along the long axis with its own phase and amplitude,
    so neighbours crest where the other troughs. Each strip has two connected ribbon solids:
    a gold body over a lit underside, with analytic normals for smooth shading.
    Cables drop from each strip's crest nearest either end onto one
    canopy. Height is the whole assembly, as ``suspended_linear_light``.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        count = max(1, strips)
        segment_count = max(1, samples if samples is not None
                            else math.ceil(abs(waves) * WAVE_SAMPLES_PER_CYCLE))
        strip_w = min(0.0254, depth / (count * 1.5))  # 1" flat strip
        spread = depth - strip_w
        half_l = width / 2
        canopy_h = min(height * 0.04, 0.0254)
        body_h = min(0.0254, height * 0.06)
        lamp_h = body_h * 0.3
        amp_max = min(0.1016, height * 0.1)  # 4" swing either side
        cable_t = min(0.003175, strip_w * 0.3)
        omega = 2 * math.pi * waves / width
        xs = [-half_l + width * step / segment_count for step in range(segment_count + 1)]
        strokes: list[Stroke] = [rect(0, 0, width, depth, weight=DETAIL_WEIGHT)]
        parts: list[Part] = [box(0, 0, height - canopy_h, height, width, depth, "brass")]
        profiles = []
        for index in range(count):
            y = 0.0 if count == 1 else -spread / 2 + spread * index / (count - 1)
            phase = index * 2 * math.pi / count
            amp = amp_max * (0.7 + 0.3 * ((index * 0.6180339887) % 1.0))
            profiles.append((y, phase, amp, [amp * math.sin(omega * x + phase) for x in xs]))
        floor = min(min(zs) for *_, zs in profiles) - body_h / 2
        for y, phase, amp, zs in profiles:
            strokes.append(rect(0, y, width, strip_w, fill="brass", weight=DETAIL_WEIGHT))
            zs = [z - floor for z in zs]
            curve = [(x, z, amp * omega * math.cos(omega * x + phase))
                     for x, z in zip(xs, zs, strict=True)]
            parts.append(curved_elevation_band(curve, y, strip_w, -body_h / 2,
                                                -body_h / 2 + lamp_h, "lamp"))
            parts.append(curved_elevation_band(curve, y, strip_w, -body_h / 2 + lamp_h,
                                                body_h / 2, "brass"))
            # A cable at the crest nearest each end, so it rises onto the canopy.
            for target in (-0.7 * half_l, 0.7 * half_l):
                n = round((omega * target + phase - math.pi / 2) / (2 * math.pi))
                reach = half_l - cable_t / 2
                x = min(max((math.pi / 2 + 2 * math.pi * n - phase) / omega, -reach), reach)
                top = amp * math.sin(omega * x + phase) - floor + body_h / 2
                parts.append(box(x, y, top, height - canopy_h, cable_t, cable_t, "brass"))
        return tuple(strokes), tuple(parts)

    return build

