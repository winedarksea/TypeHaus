"""Catlin's chosen exterior door products (2026-10-25; catalog, not editable).

House-local overrides merged by tag in plan/manifest.py. The three French pairs share
Therma-Tru Smooth-Star full-lite, composite frames and Endura hardware. Laminated triple
and the assembled pair's label remain dealer items; the CPD row is a provisional basis.
The opaque front entry, steel garage service door and sectional retain separate types.
"""

from __future__ import annotations

from typehaus import DoorType, DoorwayProductSpec, DoorwayTreatment, u_us
from typehaus.quantities import ft

from plan.opening_products import (
    THERMATRU_SMOOTHSTAR_FULLLITE, CLOPAY_MODERN_STEEL, MASONITE_STEEL_FLUSH, THERMATRU_SMOOTHSTAR,
)

_FULLLITE = ("NFRC THC-M-5-04493-00001: full-lite E366/Argon/i89, U 0.21, SHGC 0.12, VT 0.27. "
             "https://search.nfrc.org/search/cpd/cpd_search_detail.aspx?cpdnum=THC-M-5-04493-00001. "
             "This row does not certify the requested laminated triple or assembled pair.")

# Source-backed research records, not approved shop sections. The selected door lines
# do not establish the ordered sill variant (notes/doorway_product_sections.md).
THERMATRU_SECTION = DoorwayProductSpec(
    product_ref=THERMATRU_SMOOTHSTAR.tag,
    variant="Composite adjustable inswing sill — design selection; installed section pending",
    role="sill", source_url="https://outdoorsandsecurity.widen.net/content/6ybzlyty7g/"
    "original/2026-Arch-Comp-BOOK---COMP-7-Sills.pdf",
    source_drawing="2026 Comp 7.3/7.10; supplier must identify depth, sweep and installed section",
    installation="Inswing single; positive-normal orientation and seat height unverified")
ENDURA_ZAI_SECTION = DoorwayProductSpec(
    product_ref=THERMATRU_SMOOTHSTAR_FULLLITE.tag,
    variant="Endura Z-Series Adjustable Inswing (ZAI) sill — installed section pending",
    role="sill", source_url="https://www.enduraproducts.com/adjustable-door-sills-2/",
    source_drawing="Endura Z-Series Sill Options p.5, ZAI4565FN: 4-9/16 x 1-3/8 inches; "
                   "exact installed section and Therma-Tru pair approval pending",
    installation="Inswing French pair; supplier to confirm sill variant, sweep, support and drainage")
THERMATRU_SILL = DoorwayTreatment(threshold=THERMATRU_SECTION)
ENDURA_ZAI_SILL = DoorwayTreatment(threshold=ENDURA_ZAI_SECTION)
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
        u_factor=u_us(0.21), shgc=0.12, vt=0.27, product_ref=THERMATRU_SMOOTHSTAR_FULLLITE.tag,
        doorway=ENDURA_ZAI_SILL,
        source=f"Inswing French pair, composite frame and Endura hardware. {_FULLLITE} "
               "Pair NFRC/NAFS label under Therma-Tru system approval and laminated low-E triple "
               "CPD row are dealer items; impact full-lite fallback needs its own confirmed rating."),
    DoorType(
        tag="DT-EXT-OVERHEAD192", width=ft(16), height=ft(7), exterior=True,
        operation="overhead", function="overhead", product_ref=CLOPAY_MODERN_STEEL.tag,
        doorway=CLOPAY_BOTTOM,
        source="Clopay Modern Steel, Intellicore R-18.4, Black. Unconditioned garage: no "
               "NFRC rating is needed or claimed."),
)

HOUSE_DOOR_TAGS = frozenset(t.tag for t in DOOR_TYPES)
