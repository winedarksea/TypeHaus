"""Catlin's exterior door types: the chosen products (2026-10-21, NOT editable: a catalog).

Redefines the library's exterior presets by tag, merged in `plan/manifest.py` as the windows
are. Owner's selection (notes/window_and_door_procurement.md §2): Cascadia Universal
fiberglass for the three French pairs, an opaque Therma-Tru Smooth-Star for the front door
(2026-10-21 later: the Cascadia line is glazed-only, and the owner wants a solid door), a
commodity Masonite steel outswing for the garage, a Clopay sectional. ``D-G-SERVICE`` is a different product from ``D-M-ENTRY``, so it
takes its own tag rather than one tag meaning two doors.
"""

from __future__ import annotations

from typehaus import DoorType, DoorwayProductSpec, DoorwayTreatment, u_us
from typehaus.quantities import ft

from plan.opening_products import (
    CASCADIA_UNIVERSAL_DOOR, CLOPAY_MODERN_STEEL, MASONITE_STEEL_FLUSH, THERMATRU_SMOOTHSTAR,
)

# Every Cascadia swing door is glazed: the CPD line carries no opaque infill, so only the
# French pairs use it.
_CASCADIA = ("NFRC CWL-K-27-00344-00001 (inswing) / -00415-00001 (outswing): E180/Arg/Clear/"
             "Arg/E180 triple, central gasket, U 0.15, SHGC 0.33, VT 0.42. Tempered.")

# Source-backed research records, not approved shop sections. The selected door lines
# do not establish the ordered sill variant (notes/doorway_product_sections.md).
THERMATRU_SECTION = DoorwayProductSpec(
    product_ref=THERMATRU_SMOOTHSTAR.tag,
    variant="Composite adjustable inswing sill — design selection; installed section pending",
    role="sill", source_url="https://outdoorsandsecurity.widen.net/content/6ybzlyty7g/"
    "original/2026-Arch-Comp-BOOK---COMP-7-Sills.pdf",
    source_drawing="2026 Comp 7.3/7.10; supplier must identify depth, sweep and installed section",
    installation="Inswing single; positive-normal orientation and seat height unverified")
CASCADIA_SECTION = DoorwayProductSpec(
    product_ref=CASCADIA_UNIVERSAL_DOOR.tag,
    variant="High-performance inswing sill — design selection; installed section pending",
    role="sill", source_url="https://www.cascadiawindows.com/files/file/6a7e455007bf8/"
    "Door-Page---Profile--Install-Details-Inswing-Door-double--triple-glazed---20260813.pdf",
    source_drawing="UW6, 2026-07-30, detail 2 (2026-08-13 download); pair approval pending",
    installation="Inswing French pair; installed section, angle, support and drainage need supplier approval")
THERMATRU_SILL = DoorwayTreatment(threshold=THERMATRU_SECTION)
CASCADIA_SILL = DoorwayTreatment(threshold=CASCADIA_SECTION)
MASONITE_SILL = DoorwayTreatment(threshold=DoorwayProductSpec(
    product_ref=MASONITE_STEEL_FLUSH.tag, variant="UNKNOWN — prehanger's outswing sill",
    role="sill", source_url="https://www.masonite.com/discover-and-learn/door-buying-key-terms/",
    source_drawing="Supplier must identify outswing sill section; generic steel slab is insufficient",
    installation="Outswing garage service door; preserve authored raised rough sill"))
CLOPAY_BOTTOM = DoorwayTreatment(threshold=DoorwayProductSpec(
    product_ref=CLOPAY_MODERN_STEEL.tag, variant="UNKNOWN — bottom seal and aluminum retainer section",
    role="bottom_seal", source_url="https://www.clopaydoor.com/residential-garage-doors/modern-steel-collection",
    source_drawing="Modern Steel construction description; dimensioned installed seal section pending",
    installation="Leaf-mounted vinyl seal in aluminum retainer; no floor-spanning threshold"))

DOOR_TYPES = (
    DoorType(
        tag="DT-EXT-SWING36", width=ft(3), height=ft(6, 8), exterior=True, function="entry",
        u_factor=u_us(0.15), product_ref=THERMATRU_SMOOTHSTAR.tag, doorway=THERMATRU_SILL,
        source="D-M-ENTRY, inswing single, opaque. NFRC THC-M-5-03881-00001: flush, no lite, "
               "U 0.15. Multipoint lock."),
    DoorType(
        tag="DT-EXT-SWING32-G", width=ft(2, 8), height=ft(6, 8), exterior=True, function="entry",
        product_ref=MASONITE_STEEL_FLUSH.tag, doorway=MASONITE_SILL,
        source="D-G-SERVICE, outswing onto the deck from the rarely heated garage. Insulated steel, flush; "
               "unconditioned, so no NFRC rating is needed or claimed. Full composite poly-fiber jambs "
               "and head required; prehanger to approve steel-leaf compatibility and hinge/overhead-stop "
               "reinforcement. Confirm actual frame, RO, hinge axis and sill dimensions before ordering."),
    DoorType(
        tag="DT-EXT-FRENCH60", width=ft(5), height=ft(6, 8), exterior=True, function="entry",
        operation="double_swing", glazed=True, tempered=True,
        u_factor=u_us(0.15), shgc=0.33, vt=0.42, product_ref=CASCADIA_UNIVERSAL_DOOR.tag,
        doorway=CASCADIA_SILL,
        source=f"Double leaf, NAFS inswing double R-PG35. {_CASCADIA} The CPD lists the "
               "single leaf; the pair's own label is a quote item."),
    DoorType(
        tag="DT-EXT-OVERHEAD192", width=ft(16), height=ft(7), exterior=True,
        operation="overhead", function="overhead", product_ref=CLOPAY_MODERN_STEEL.tag,
        doorway=CLOPAY_BOTTOM,
        source="Clopay Modern Steel, Intellicore R-18.4, Black. Unconditioned garage: no "
               "NFRC rating is needed or claimed."),
)

HOUSE_DOOR_TAGS = frozenset(t.tag for t in DOOR_TYPES)
