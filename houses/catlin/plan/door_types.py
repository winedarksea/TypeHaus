"""Catlin's exterior door types: the chosen products (2026-10-21, NOT editable: a catalog).

Redefines the library's exterior presets by tag, merged in `plan/manifest.py` as the windows
are. Owner's selection (notes/window_and_door_procurement.md §2): Cascadia Universal
fiberglass for the three French pairs, an opaque Therma-Tru Smooth-Star for the front door
(2026-10-21 later: the Cascadia line is glazed-only, and the owner wants a solid door), a
commodity Masonite steel outswing for the garage, a Clopay sectional. ``D-G-SERVICE`` is a different product from ``D-M-ENTRY``, so it
takes its own tag rather than one tag meaning two doors.
"""

from __future__ import annotations

from typehaus import DoorType, u_us
from typehaus.quantities import ft

from plan.opening_products import (
    CASCADIA_UNIVERSAL_DOOR, CLOPAY_MODERN_STEEL, MASONITE_STEEL_FLUSH, THERMATRU_SMOOTHSTAR,
)

# Every Cascadia swing door is glazed: the CPD line carries no opaque infill, so only the
# French pairs use it.
_CASCADIA = ("NFRC CWL-K-27-00344-00001 (inswing) / -00415-00001 (outswing): E180/Arg/Clear/"
             "Arg/E180 triple, central gasket, U 0.15, SHGC 0.33, VT 0.42. Tempered.")

DOOR_TYPES = (
    DoorType(
        tag="DT-EXT-SWING36", width=ft(3), height=ft(6, 8), exterior=True, function="entry",
        u_factor=u_us(0.15), product_ref=THERMATRU_SMOOTHSTAR.tag,
        source="D-M-ENTRY, inswing single, opaque. NFRC THC-M-5-03881-00001: flush, no lite, "
               "U 0.15. Multipoint lock."),
    DoorType(
        tag="DT-EXT-SWING36-G", width=ft(3), height=ft(6, 8), exterior=True, function="entry",
        product_ref=MASONITE_STEEL_FLUSH.tag,
        source="D-G-SERVICE, outswing into the rarely heated garage. Insulated steel, flush; "
               "unconditioned, so no NFRC rating is needed or claimed."),
    DoorType(
        tag="DT-EXT-FRENCH60", width=ft(5), height=ft(6, 8), exterior=True, function="entry",
        operation="double_swing", glazed=True, tempered=True,
        u_factor=u_us(0.15), shgc=0.33, vt=0.42, product_ref=CASCADIA_UNIVERSAL_DOOR.tag,
        source=f"Double leaf, NAFS inswing double R-PG35. {_CASCADIA} The CPD lists the "
               "single leaf; the pair's own label is a quote item."),
    DoorType(
        tag="DT-EXT-OVERHEAD192", width=ft(16), height=ft(7), exterior=True,
        operation="overhead", function="overhead", product_ref=CLOPAY_MODERN_STEEL.tag,
        source="Clopay Modern Steel, Intellicore R-18.4, Black. Unconditioned garage: no "
               "NFRC rating is needed or claimed."),
)

HOUSE_DOOR_TAGS = frozenset(t.tag for t in DOOR_TYPES)
