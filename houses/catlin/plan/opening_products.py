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
    name="Smooth-Star fiberglass flush door, inswing, single-point bored prep",
    url="https://www.thermatru.com",
    source="Opaque fiberglass, polyurethane foam core, 1 1/4\" engineered-lumber lock stile, "
           "Single-point double bore, 2-3/8 inch backset, 5-1/2 inch centres. Composite jambs/head, "
           "primed for site paint: black exterior, white interior; quote factory black alternate. "
           "Therma-Tru Security Strike Plate requested, dealer cost/compatibility pending. NFRC line "
           "THC-M-5 (flush, no lite, THC-M-5-03881-00001). A small lite is a catalog option.")
MASONITE_STEEL_FLUSH = Product(
    tag="PROD-MASONITE-STEEL-FLUSH", brand="Masonite", model="Premium Flush steel",
    name="Premium Flush primed steel prehung, outswing, no brickmold, 32in", sku="26849",
    url="https://superarbor.io/products/masonite-32-in-x-80-in-premium-right-hand-outswing-"
        "flush-primed-steel-prehung-front-exterior-door-with-no-brickmold",
    source="Same Premium Flush insulated steel family, nominal 32x80, field-painted black. "
           "Durable composite or metal frame, supplied and approved by prehanger. "
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


# Purchased sets, with no price data in the product catalog.
ENCODE_PLUS = Product(tag='PROD-SCHLAGE-ENCODE-PLUS', brand='Schlage', model='BE499WB CEN 622',
    name='Encode Plus Century matte black deadbolt', url='https://www.schlage.com/en/home/products/BE499WBCENFFF.html', source='Single-point entry deadbolt; 2-3/8 inch backset, 1-3/4 inch leaf.')
PASSAGE_LEVER = Product(tag='PROD-SCHLAGE-PASSAGE-LATITUDE', brand='Schlage', model='F10 LAT 622 CEN',
    name='Century / Latitude passage lever, matte black', url='https://www.schlage.com', source='Passage function; no second keyed lock.')
STRIKE_REINFORCEMENT = Product(tag='PROD-STRIKEMASTER-II-PRO', brand='Safe Homes International', model='StrikeMaster II Pro',
    name='StrikeMaster II Pro jamb reinforcement', url='https://www.asafehome.net', source='Door Armor alternate. Prehanger to coordinate with composite frame and factory security strike; no unapproved stacking.')
DOORSCOPE = Product(tag='PROD-DOORSCOPE-DS2000', brand='Door Scope', model='DS2000',
    name='DoorScope DS2000 viewer', url='https://www.metropolitandoor.com/wp-content/uploads/2018/07/door-scope-installation.pdf', source='2-3/8 inch bore; seal exposed foam core and caulk flange; prehanger to confirm warranty.')
DOOR_SCREWS = Product(tag='PROD-DOOR-3IN-SCREWS', brand='Prehanger approved', model='3 inch structural screw kit',
    name='3 inch hinge / strike screw kit', url='https://www.thermatru.com', source='One installation kit per opening; screw gauge, head and count per approved hinge/strike instructions.')
DOOR_HINGE = Product(tag='PROD-THERMATRU-HINGE', brand='Therma-Tru', model='Prehanger approved hinge',
    name='Exterior door hinge, factory included', url='https://www.thermatru.com', source='Three per leaf; 10/40/70 inch centres are coordination locations pending shop drawings. Included in prehung price.')
PANOLOCK = Product(tag='PROD-ENDURA-PANOLOCK-PLUS', brand='Endura', model='PanoLock+',
    name='PanoLock+ multipoint set', url='https://www.enduraproducts.com/panolock/', source='One set per French pair. Keep locations 10/40/70 inches are coordination positions pending approved shop drawings.')
BE365 = Product(tag='PROD-SCHLAGE-BE365', brand='Schlage', model='BE365',
    name='BE365 keypad deadbolt', url='https://www.schlage.com', source='French active leaf; Endura 2026 Schlage compatibility guide lists BE365 CAM/PLY with adapter F. Selected trim/passage adapter and assembly prep remain unconfirmed.')
FLA_ASTRAGAL = Product(tag='PROD-ENDURA-FLA', brand='Endura', model='Ultimate Flip Lever Astragal',
    name='Ultimate FLA astragal with passive flush bolts', url='https://www.enduraproducts.com', source='One full-height astragal per French pair; included in pair price.')
SECURITY_STRIKE = Product(tag='PROD-THERMATRU-SECURITY-STRIKE', brand='Therma-Tru', model='Security Strike Plate',
    name='Therma-Tru Security Strike Plate', url='https://www.thermatru.com/explore-products/safety-and-security/', source='Requested factory component; dealer to confirm price and compatibility with reinforcement and approved 3 inch screws.')

OPENING_PRODUCTS = (
    ENCODE_PLUS, PASSAGE_LEVER, STRIKE_REINFORCEMENT, DOORSCOPE, DOOR_SCREWS, DOOR_HINGE, PANOLOCK, BE365, FLA_ASTRAGAL, SECURITY_STRIKE,
    DRUTEX_ALUCOVER_TT, DRUTEX_ALUCOVER_FIX, DRUTEX_ALUCOVER_TILT, ANDERSEN_400_CASEMENT,
    THERMATRU_SMOOTHSTAR_FULLLITE, THERMATRU_SMOOTHSTAR, MASONITE_STEEL_FLUSH, CLOPAY_MODERN_STEEL,
)
