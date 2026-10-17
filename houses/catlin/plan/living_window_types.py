"""House-local window types for the living room's east wall (NOT editable: a catalog).

WT-6348-FIX is the dining picture window, WIN-M-DINING-E: a fixed unit with a 63" x 48"
rough opening, centred on the table at y=18'-0". It is not tempered. Its sill is 33" above
the finished floor, outside R308.4.3's 18" band. Performance follows the library's
16-inch-module presets (`library/windows.py`).
"""

from __future__ import annotations

from typehaus import WindowType, u_us
from typehaus.quantities import ft, inch

WINDOW_TYPES = (
    WindowType(
        tag="WT-6348-FIX", width=inch(63), height=ft(4), operation="fixed",
        u_factor=u_us(0.25), frame_depth=inch(3.25), shgc=0.35, vt=0.5,
        source="House-local fixed picture unit, 63\" x 48\" RO; select a listed "
               "manufacturer configuration that meets the declared whole-window values."),
)
