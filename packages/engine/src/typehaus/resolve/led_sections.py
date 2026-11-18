"""LED run sections, built from the type's tape and channel (decision #137).

Every part is a convex ``(key, quad)`` in the run's (across toward the emission side, drop
below the run's height) frame, the frame ``resolve/geometry.light_run_section_shells``
sweeps. A channel is drawn as built: the extrusion (``body``), the tape on its back
(``tape``), the lens across its opening (``lens``), and an ``endcap`` past each open end.
A rigid-bar product (``LedStrip.modules``) is filled with the fewest modules that fit and
swept per module. A type with no ``LedStrip`` keeps the generic half-inch channel.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.model.led import LedChannel, LedStrip

Quad = tuple[tuple[float, float], ...]
Part = tuple[str, Quad]

_LENS_SKIN_M = 0.0012  # a lens drawn this thick
_CAP_M = 0.002  # an end cap stands this far past the run's end
_DOME_RISE = 0.25  # a dome lens bulges this fraction of its chord
_DOME_FACETS = 6
_JOINT_M = 0.001  # a module joint drawn at least this wide, so modules read
_MODULE_TOL_M = 0.0127  # a run may fall short of its modules by this much


def led_channels(plan: Any) -> dict[str, LedChannel]:
    return {el.tag: el for el in plan.all_elements() if isinstance(el, LedChannel)}


def strip_of(product: Any) -> LedStrip | None:
    return getattr(product, "strip", None)


def derive_aperture(authored: str | None, mount_kind: str | None, soffit_ref: str | None) -> str:
    if authored is not None:
        return authored
    return "out" if mount_kind == "wall" and soffit_ref is None else "down"


def _tape_h(strip: LedStrip) -> float:
    from typehaus.resolve.trim_bands import TAPE_HEIGHT_M

    return strip.tape_height.meters if strip.tape_height else TAPE_HEIGHT_M


def _rect(a0: float, a1: float, d0: float, d1: float) -> Quad:
    return ((a0, d0), (a1, d0), (a1, d1), (a0, d1))


def channel_parts(channel: LedChannel, strip: LedStrip, aperture: str) -> tuple[Part, ...]:
    """The channel, lens, tape and end-cap outline, opening ``aperture``."""
    w, depth = channel.outer_width.meters, channel.outer_depth.meters
    back = channel.back_m()
    inner = channel.inner_width_m()
    side = (w - inner) / 2.0
    parts: list[Part] = []
    if channel.ring:
        parts.append(("body", tuple((a.meters, d.meters) for a, d in channel.ring)))
    else:
        parts += [("body", _rect(-w / 2, w / 2, 0.0, back)),
                  ("body", _rect(-w / 2, -w / 2 + side, back, depth)),
                  ("body", _rect(w / 2 - side, w / 2, back, depth))]
    tw = min(strip.tape_width.meters, inner) / 2.0
    th = min(_tape_h(strip), depth - back)
    parts.append(("tape", _rect(-tw, tw, back, back + th)))
    if channel.lens != "none":
        face = depth - (channel.lens_inset.meters if channel.lens_inset else 0.0)
        if channel.lens_shape == "dome":
            rise = inner * _DOME_RISE
            arc = tuple((inner / 2 * math.cos(math.pi * i / _DOME_FACETS),
                         face + rise * math.sin(math.pi * i / _DOME_FACETS))
                        for i in range(_DOME_FACETS + 1))
            parts.append(("lens", arc))
        else:
            parts.append(("lens", _rect(-inner / 2, inner / 2, face - _LENS_SKIN_M, face)))
    parts.append(("endcap", _rect(-w / 2, w / 2, 0.0, max(depth, _lens_bottom(parts)))))
    return tuple(_orient(parts, depth, aperture))


def bar_parts(strip: LedStrip, aperture: str) -> tuple[Part, ...]:
    """A rigid bar with no separate channel (MITTLED): its body and its diffuser face."""
    w, h = strip.tape_width.meters, _tape_h(strip)
    parts = [("body", _rect(-w / 2, w / 2, 0.0, h - _LENS_SKIN_M)),
             ("lens", _rect(-w / 2, w / 2, h - _LENS_SKIN_M, h)),
             ("endcap", _rect(-w / 2, w / 2, 0.0, h))]
    return tuple(_orient(parts, h, aperture))


def _lens_bottom(parts: list[Part]) -> float:
    return max((d for key, quad in parts if key == "lens" for _a, d in quad), default=0.0)


def _orient(parts: list[Part], depth: float, aperture: str) -> list[Part]:
    """Built opening down (back at drop 0); turn to ``up`` (back at the bottom) or ``out``
    (back on the wall at -across, opening toward the emission side, hanging below z)."""
    if aperture == "up":
        return [(k, tuple((a, depth - d) for a, d in q)) for k, q in parts]
    if aperture == "out":
        half = max(abs(a) for _k, q in parts for a, _d in q)
        return [(k, tuple((d - depth / 2.0, a + half) for a, d in q)) for k, q in parts]
    return parts


def section_extent(section) -> tuple[float, float]:
    """(across width, drop depth) a section occupies."""
    across = [a for _k, q in section for a, _d in q]
    drops = [d for _k, q in section for _a, d in q]
    if not across:
        return 0.0, 0.0
    return max(across) - min(across), max(drops) - min(drops)


def fill_modules(lengths_m: tuple[float, ...], run_m: float, gap_m: float) -> tuple[float, ...]:
    """The fewest modules (longest first) whose butted length best fills ``run_m``.

    Most coverage wins, then fewest pieces; a run shorter than every module takes none.
    """
    step = 0.0015875  # 1/16"
    sizes = sorted({round(x / step) for x in lengths_m if x > 0}, reverse=True)
    gap = round(gap_m / step)
    limit = round((run_m + _MODULE_TOL_M) / step)
    best: dict[int, tuple[int, ...]] = {-gap: ()}  # covered length -> pieces
    frontier = [-gap]
    while frontier:
        nxt = []
        for covered in frontier:
            for size in sizes:
                total = covered + gap + size
                if total > limit:
                    continue
                pieces = tuple(sorted(best[covered] + (size,), reverse=True))
                if total not in best or len(pieces) < len(best[total]) or (
                        len(pieces) == len(best[total]) and pieces > best[total]):
                    if total not in best:
                        nxt.append(total)
                    best[total] = pieces
        frontier = nxt
    covered = max(best)
    return tuple(s * step for s in best[covered]) if covered > 0 else ()


def module_spans(modules: tuple[float, ...], run_m: float,
                 gap_m: float) -> tuple[tuple[float, float], ...]:
    """Each module's (start, end) along the run, the set centred on it."""
    if not modules:
        return ()
    joint = max(gap_m, _JOINT_M)
    total = sum(modules) + joint * (len(modules) - 1)
    at = max((run_m - total) / 2.0, 0.0)
    spans = []
    for size in modules:
        spans.append((at, min(at + size, run_m)))
        at += size + joint
    return tuple(spans)


def surface_section(run: Any, product: Any, channels: dict[str, LedChannel],
                    mount_kind: str | None) -> dict[str, Any]:
    """``ResolvedLightRun`` fields for a surface run: section, channel, aperture, modules.

    Empty when the type states no tape: the run keeps the generic channel.
    """
    strip = strip_of(product)
    if strip is None:
        return {}
    aperture = derive_aperture(getattr(run, "aperture", None), mount_kind,
                               getattr(run, "soffit_ref", None))
    channel = channels.get(strip.channel_ref or "")
    if channel is not None:
        return {"section": channel_parts(channel, strip, aperture), "channel_ref": channel.tag,
                "aperture": aperture, "end_caps": True}
    if strip.modules:
        return {"section": bar_parts(strip, aperture), "aperture": aperture, "end_caps": True}
    return {}


def modules_for(product: Any, length_m: float) -> dict[str, Any]:
    strip = strip_of(product)
    if strip is None or not strip.modules:
        return {}
    gap = strip.module_gap.meters if strip.module_gap else 0.0
    modules = fill_modules(tuple(x.meters for x in strip.modules), length_m, gap)
    return {"modules_m": modules, "spans_m": module_spans(modules, length_m, gap)}


# --- the sweep's pieces ---------------------------------------------------------------

def _cut(path, z, start: float, end: float):
    """The polyline between developed stations ``start`` and ``end``."""
    out_p, out_z, at = [], [], 0.0
    for i in range(len(path) - 1):
        (x0, y0), (x1, y1), za, zb = path[i], path[i + 1], z[i], z[i + 1]
        leg = math.dist((x0, y0, za), (x1, y1, zb))
        if leg < 1e-9:
            continue
        lo, hi = max(start - at, 0.0), min(end - at, leg)
        if lo < hi:
            for t in ((lo / leg,) if not out_p else ()) + (hi / leg,):
                out_p.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
                out_z.append(za + (zb - za) * t)
        at += leg
    return out_p, out_z


def run_pieces(run: Any) -> list[tuple[list, list]]:
    """The run's swept pieces: one per module span, else the whole path."""
    path, z = list(run.path), run.vertex_z()
    spans = getattr(run, "spans_m", ())
    if not spans:
        return [(path, z)]
    return [piece for s, e in spans if len((piece := _cut(path, z, s, e))[0]) >= 2]


def cap_pieces(run: Any) -> list[tuple[list, list]]:
    """A short segment just past each open end of each piece, for the ``endcap`` part."""
    if not getattr(run, "end_caps", False):
        return []
    out = []
    for path, z in run_pieces(run):
        for (a, b), za in (((path[1], path[0]), z[0]), ((path[-2], path[-1]), z[-1])):
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy)
            if n < 1e-9:
                continue
            tip = (b[0] + dx / n * _CAP_M, b[1] + dy / n * _CAP_M)
            out.append(([b, tip] if (a, b) == (path[-2], path[-1]) else [tip, b], [za, za]))
    return out
