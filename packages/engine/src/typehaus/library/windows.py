"""Reusable 16-inch framing-module window presets.

These are dimensional/performance presets, not a claim that one manufacturer stocks every
combination.  A house selects the applicable preset and procurement verifies the final unit.
"""

from __future__ import annotations

from typehaus import WindowType, u_us
from typehaus.quantities import ft, inch

_SOURCE = ("Reusable 16-inch framing-module window preset; select a listed manufacturer "
           "configuration that meets the declared whole-window performance values.")


def _window(tag: str, width, height, operation: str, *, tempered: bool = False,
            u_factor=u_us(0.25), frame_depth=inch(3.25)) -> WindowType:
    return WindowType(tag=tag, width=width, height=height, operation=operation,
                      tempered=tempered, u_factor=u_factor, frame_depth=frame_depth,
                      shgc=0.35, vt=0.5, source=_SOURCE)


WINDOW_TYPES_16_INCH_MODULE = (
    _window("WT-1424", inch(14), ft(2), "awning"),
    _window("WT-1436", inch(14), ft(3), "casement"),
    _window("WT-1448", inch(14), ft(4), "casement"),
    _window("WT-2464", inch(24), ft(5, 4), "casement"),
    _window("WT-2736", inch(27), ft(3), "casement"),
    _window("WT-2748", inch(27), ft(4), "casement"),
    _window("WT-2754", inch(27), ft(4, 6), "casement"),
    _window("WT-2764", inch(27), ft(5, 4), "casement"),
    _window("WT-3036", inch(30), ft(3), "casement"),
    _window("WT-3048", inch(30), ft(4), "casement"),
    _window("WT-3660", ft(3), ft(5), "casement"),
    _window("WT-3660-FIX", ft(3), ft(5), "fixed"),
    _window("WT-1424-FIX", inch(14), ft(2), "fixed"),
    _window("WT-1424-T", inch(14), ft(2), "awning", tempered=True),
    _window("WT-2736-T", inch(27), ft(3), "casement", tempered=True),
    _window("WT-2748-T", inch(27), ft(4), "casement", tempered=True),
    _window("WT-2754-T", inch(27), ft(4, 6), "casement", tempered=True),
    _window("WT-3036-T", inch(30), ft(3), "casement", tempered=True),
    _window("WT-3048-T", inch(30), ft(4), "casement", tempered=True),
    _window("WT-2736-HP", inch(27), ft(3), "fixed", u_factor=u_us(0.14),
            frame_depth=inch(4)),
    _window("WT-3048-HP", inch(30), ft(4), "fixed", u_factor=u_us(0.14),
            frame_depth=inch(4)),
)
