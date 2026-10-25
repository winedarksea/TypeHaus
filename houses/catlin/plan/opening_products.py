"""Window and exterior-door products (2026-10-21, notes/window_and_door_procurement.md §2).

Identity only, never a price (#28). One record per line and operation: every unit is ordered
custom (Drutex builds to size; Andersen 400 sizes in 1/8" steps), so the size lives on the
type and the product names what arrives. NFRC numbers are read from the CPD
(search.nfrc.org) and cited on the types that use them.

NOT ``# haus: editable``: a catalog of definitions.
"""

from __future__ import annotations

from typehaus.model import Product

_DRUTEX_URL = "https://drutex.com/en-us/products/iglo-energy-alu-cover.html"
_DRUTEX = ("Drutex S.A., Bytow PL. IGLO Energy Alucover: 7-chamber uPVC, 93 mm, aluminium "
           "cap outside (RAL 9005 matt), white PVC inside, MACO Multi-Matic. US dealer: DAKAM, "
           "Franklin Park IL. Nail fin plus jamb straps per FL41837's tested anchorage.")

DRUTEX_ALUCOVER_TT = Product(
    tag="PROD-DRUTEX-ALUCOVER-TT", brand="Drutex", model="IGLO Energy Alucover",
    name="IGLO Energy Alucover tilt-turn", url=_DRUTEX_URL,
    source=_DRUTEX + " NFRC line DRU-K-24.")
DRUTEX_ALUCOVER_FIX = Product(
    tag="PROD-DRUTEX-ALUCOVER-FIX", brand="Drutex", model="IGLO Energy Alucover",
    name="IGLO Energy Alucover fixed", url=_DRUTEX_URL,
    source=_DRUTEX + " NFRC line DRU-K-23.")
DRUTEX_ALUCOVER_TILT = Product(
    tag="PROD-DRUTEX-ALUCOVER-TILT", brand="Drutex", model="IGLO Energy Alucover",
    name="IGLO Energy Alucover tilt-only (hopper)", url=_DRUTEX_URL,
    source=_DRUTEX + " NFRC line DRU-K-26. Minimum tilt sash at a 13 1/2\" frame is a quote "
           "item; if it cannot be built the unit goes fixed.")
ANDERSEN_400_CASEMENT = Product(
    tag="PROD-ANDERSEN-400-CASEMENT", brand="Andersen", model="400 Series Casement",
    name="400 Series casement, egress hinge, Black exterior / White interior",
    url="https://andersenwindows.com/windows-and-doors/windows/casement-windows/"
        "400-series-casement-window",
    source="Andersen Corp., Bayport MN. Wood with Perma-Shield vinyl cladding, custom sizes "
           "in 1/8\" steps, factory installation flange. NFRC line AND-N-1. Clear opening "
           "per Andersen's 2025-26 opening specifications (notes/window_and_door_procurement.md "
           "§7).")
THERMATRU_SMOOTHSTAR_FULLLITE = Product(
    tag="PROD-THERMATRU-SMOOTHSTAR-FULLLITE", brand="Therma-Tru",
    model="Smooth-Star full-lite", name="Smooth-Star full-lite inswing French pair, composite frame",
    url="https://www.thermatru.com",
    source="Local prehanger: composite jambs/head, Endura Z-Series Adjustable Inswing (ZAI) sill, "
           "Ultimate Flip-Lever Astragal (FLA) with top/bottom passive-leaf flush bolts, "
           "PanoLock+ with Schlage BE365 keypad deadbolt and passage lever on all three pairs. "
           "Double bore at 5-1/2 inch spacing; confirm stile >= 4 inches and BE365 compatibility. "
           "One glass spec: laminated low-E triple, special quote; impact full-lite fallback. "
           "NFRC THC-M-5-04493-00001 is the provisional performance basis, not a laminated-triple "
           "or pair certification. Prehanger must supply Therma-Tru system approval and pair label.")
THERMATRU_SMOOTHSTAR = Product(
    tag="PROD-THERMATRU-SMOOTHSTAR", brand="Therma-Tru", model="Smooth-Star flush",
    name="Smooth-Star fiberglass flush door, inswing, multipoint lock",
    url="https://www.thermatru.com",
    source="Opaque fiberglass, polyurethane foam core, 1 1/4\" engineered-lumber lock stile, "
           "Therma-Tru Multi-Point Locking System. Stocked by Twin Cities dealers. NFRC line "
           "THC-M-5 (flush, no lite, THC-M-5-03881-00001). A small lite is a catalog option.")
MASONITE_STEEL_FLUSH = Product(
    tag="PROD-MASONITE-STEEL-FLUSH", brand="Masonite", model="Premium Flush steel",
    name="Premium Flush primed steel prehung, outswing, no brickmold, 32in", sku="26849",
    url="https://superarbor.io/products/masonite-32-in-x-80-in-premium-right-hand-outswing-"
        "flush-primed-steel-prehung-front-exterior-door-with-no-brickmold",
    source="Same Premium Flush insulated steel family, nominal 32x80, field-painted black. "
           "Full composite poly-fiber jambs and head required, supplied/approved by prehanger. "
           "26849 is a slab/family reference; its stock frame is not the specified frame. Confirm "
           "west hinge handing, actual frame/RO, hinge axis, sill and stop reinforcement "
           "with prehanger. No NFRC rating needed or claimed for this unconditioned garage.")

CLOPAY_MODERN_STEEL = Product(
    tag="PROD-CLOPAY-MODERN-STEEL", brand="Clopay", model="Modern Steel, Intellicore",
    name="Modern Steel 16x7 flush, Intellicore R-18.4, Black", sku="GDU011",
    url="https://www.clopaydoor.com/residential/buyingguide/garage-door-styles/"
        "contemporary-garage-doors/modern-steel-collection",
    source="3-layer steel, polyurethane core, R-18.4. GDU011 is Home Depot's 16x7 black, "
           "no-window listing. Wind rating for Exp B (q_h 19.3 psf) to confirm with the dealer.")

OPENING_PRODUCTS = (
    DRUTEX_ALUCOVER_TT, DRUTEX_ALUCOVER_FIX, DRUTEX_ALUCOVER_TILT, ANDERSEN_400_CASEMENT,
    THERMATRU_SMOOTHSTAR_FULLLITE, THERMATRU_SMOOTHSTAR, MASONITE_STEEL_FLUSH, CLOPAY_MODERN_STEEL,
)
