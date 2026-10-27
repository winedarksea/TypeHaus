"""Catlin's chosen exterior door products (2026-10-25; catalog, not editable).

House-local overrides merged by tag in plan/manifest.py. The three French pairs share
Therma-Tru Smooth-Star full-lite, composite frames and Endura hardware. Laminated triple
and the assembled pair's label remain dealer items; the CPD row is a provisional basis.
The opaque front entry, steel garage service door and sectional retain separate types.
"""

from __future__ import annotations

from typehaus import DoorCatalogDimensions, DoorHardwareItem, JambFraming, inch, DoorType, DoorwayProductSpec, DoorwayTreatment, u_us
from typehaus.quantities import ft

from plan.opening_products import (
    ENCODE_PLUS, PASSAGE_LEVER, STRIKE_REINFORCEMENT, DOORSCOPE, DOOR_SCREWS,
    DOOR_HINGE, PANOLOCK, BE365, FLA_ASTRAGAL, SECURITY_STRIKE,
    THERMATRU_SMOOTHSTAR_FULLLITE, CLOPAY_MODERN_STEEL, MMI_STEEL_SIX_PANEL, THERMATRU_SMOOTHSTAR,
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
MMI_OUTSWING_SILL = DoorwayTreatment(threshold=DoorwayProductSpec(
    product_ref=MMI_STEEL_SIX_PANEL.tag, variant="Included composite fixed outswing sill",
    role="sill", source_url=MMI_STEEL_SIX_PANEL.url,
    source_drawing="MMI Z0364688R complete prehung unit; retain factory sill and seals",
    installation="Full-width supported pan; moving leaf/sweep >=1 inch above deck"))

CLOPAY_BOTTOM = DoorwayTreatment(threshold=DoorwayProductSpec(
    product_ref=CLOPAY_MODERN_STEEL.tag, variant="UNKNOWN — bottom seal and aluminum retainer section",
    role="bottom_seal", source_url="https://www.clopaydoor.com/residential-garage-doors/modern-steel-collection",
    source_drawing="Modern Steel construction description; dimensioned installed seal section pending",
    installation="Leaf-mounted vinyl seal in aluminum retainer; no floor-spanning threshold"))


_JAMB = JambFraming(kings=2, jacks=2, blocking=True,
                    bay_fill_ref="closed-cell-spray-foam")
_SHIM = "Solid composite shims directly behind strike and every multipoint keep; "
_SCREWS = "3 inch hinge/strike screws into framing; approved gauge/head; low-expansion foam at frame gap."
_ENTRY_HARDWARE = (
    *(DoorHardwareItem(role="hinge", product_ref=DOOR_HINGE.tag, height=inch(height),
        installation="Coordination height; verify factory hinge locations. " + _SCREWS)
      for height in (10, 40, 70)),
    DoorHardwareItem(role="passage", product_ref=PASSAGE_LEVER.tag, height=inch(36),
        installation="Century / Latitude 622 passage lever; 2-3/8 inch backset."),
    DoorHardwareItem(role="deadbolt", product_ref=ENCODE_PLUS.tag, height=inch(41.5),
        installation=_SHIM + "BE499WB CEN 622; double bore at 5-1/2 inch centres. " + _SCREWS),
    DoorHardwareItem(role="strike_reinforcement", product_ref=STRIKE_REINFORCEMENT.tag,
        height=inch(41.5), installation=_SHIM + "StrikeMaster II Pro; Door Armor alternate. "
        "Coordinate with composite frame and factory strike; no unapproved stacking. " + _SCREWS),
    DoorHardwareItem(role="strike_reinforcement", product_ref=SECURITY_STRIKE.tag,
        height=inch(41.5), installation="Dealer to confirm factory Security Strike Plate cost and "
        "compatibility with reinforcement and specified screws before ordering."),
    DoorHardwareItem(role="viewer", product_ref=DOORSCOPE.tag, height=inch(60),
        installation="DS2000: seal 2-3/8 inch bore through foam core; caulk exterior flange; "
        "confirm warranty for drilling 1-3/4 inch leaf."),
    DoorHardwareItem(role="fastener", product_ref=DOOR_SCREWS.tag, installation=_SCREWS),
)
_FRENCH_HARDWARE = (
    *(DoorHardwareItem(role="hinge", product_ref=DOOR_HINGE.tag, quantity=2,
        height=inch(height), installation="Two leaves; coordination height, verify shop drawings. "
        + _SCREWS) for height in (10, 40, 70)),
    DoorHardwareItem(role="passage", product_ref=PASSAGE_LEVER.tag, height=inch(36),
        installation="One passage set on active leaf; verify PanoLock+ compatibility."),
    DoorHardwareItem(role="deadbolt", product_ref=BE365.tag, height=inch(41.5),
        installation=_SHIM + "BE365 on active leaf; Endura 2026 Schlage compatibility list: adapter F. Confirm selected trim and passage adapter."),
    DoorHardwareItem(role="multipoint", product_ref=PANOLOCK.tag, height=inch(40),
        installation=_SHIM + "One set per pair; keep coordination at 10/40/70 inches, "
        "confirm factory positions before blocking. " + _SCREWS),
    DoorHardwareItem(role="astragal", product_ref=FLA_ASTRAGAL.tag,
        installation="Full-height passive-leaf FLA; top and bottom flush bolts."),
    DoorHardwareItem(role="fastener", product_ref=DOOR_SCREWS.tag, installation=_SCREWS),
)

DOOR_TYPES = (
    DoorType(
        tag="DT-EXT-SWING36", width=ft(3), height=ft(6, 8), exterior=True, function="entry",
        hardware=_ENTRY_HARDWARE, jamb_framing=_JAMB,
        field_finish=("door-paint-black", "door-paint-white"),
        u_factor=u_us(0.15), product_ref=THERMATRU_SMOOTHSTAR.tag, doorway=THERMATRU_SILL,
        source="D-M-ENTRY, inswing single, opaque. NFRC THC-M-5-03881-00001: flush, no lite, "
               "U 0.15. Single-point Encode Plus; field-painted black outside / white inside."),
    DoorType(
        tag="DT-EXT-SWING32-G", width=inch(34), height=inch(81.5), exterior=True,
        function="entry", product_ref=MMI_STEEL_SIX_PANEL.tag, doorway=MMI_OUTSWING_SILL,
        jamb_framing=JambFraming(kings=2, jacks=1, blocking=True),
        catalog_dimensions=DoorCatalogDimensions(
            nominal_width=inch(32), nominal_height=inch(80),
            unit_width=inch(33.5), unit_height=inch(81),
            source_url=MMI_STEEL_SIX_PANEL.url,
            source_drawing="MMI Z0364688R product details: unit and suggested rough opening"),
        source="D-G-SERVICE: stock MMI Z0364688R six-panel insulated steel prehung, "
               "6-9/16 composite frame. West hinges, outswing, black outside/white inside. "
               "34x81.5 framed opening, nominal 32x80 purchased unit. "
               "STHD14 on garage face of two full-height east king studs; one jack inboard. "
               "Retain factory sill; set support from delivered unit; see service-door note."),
    DoorType(
        tag="DT-EXT-FRENCH60", width=ft(5), height=ft(6, 8), exterior=True, function="entry",
        operation="double_swing", glazed=True, tempered=True,
        u_factor=u_us(0.21), shgc=0.12, vt=0.27, product_ref=THERMATRU_SMOOTHSTAR_FULLLITE.tag,
        doorway=ENDURA_ZAI_SILL, hardware=_FRENCH_HARDWARE, jamb_framing=_JAMB,
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

# This catalog RO applies only to the two installations in this pass. The main-floor
# balcony retains its existing authored dimensions until its separate installation review.
DOOR_TYPES = (*DOOR_TYPES, DOOR_TYPES[2].model_copy(update={
    "tag": "DT-EXT-FRENCH60-CATALOG", "width": inch(63.3125), "height": inch(82.875),
    "catalog_dimensions": DoorCatalogDimensions(
        nominal_width=inch(60), nominal_height=inch(80),
        unit_width=inch(62.5625), unit_height=inch(82),
        source_url="https://outdoorsandsecurity.widen.net/content/lpxemo2dti/original/"
                   "2026-Arch-Comp-BOOK---ARCH-1-Dimensional-Data.pdf",
        source_drawing="2026 Arch 1.4 French inswing, 7/8 astragal; Endura assembly dimension confirmation pending"),
    "source": "Catalog nominal 60x80 pair; 62-9/16x82 unit; 63-5/16x82-7/8 RO "
              "includes the 3/8-inch pan allowance over the published 82-1/2-inch RO. "
              "These are Therma-Tru 7/8-astragal dimensions, not confirmation of the FLA assembly. "
              + DOOR_TYPES[2].source,
}))

HOUSE_DOOR_TAGS = frozenset(t.tag for t in DOOR_TYPES)
