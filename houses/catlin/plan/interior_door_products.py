"""Interior door products: every leaf flush and smooth (owner, 2026-11-20).

Identity only, never a price (#28). One record per family; the width SKUs are in ``sku`` /
``source``. Home Depot numbers were read from listing text on 2026-11-20, not from an
opened page (the site refuses automated reads): confirm the handing and width at order.
Where no retail SKU exists, ``model`` stays empty and the record names the class.
Per-door use: notes/interior_door_schedule.md.

NOT ``# haus: editable``: a catalog of definitions.
"""

from __future__ import annotations

from typehaus.model import Product

_HD = "https://www.homedepot.com/p/"

FLUSH_HC_PREHUNG = Product(
    tag="PROD-STEVES-FLUSH-HC-PREHUNG", brand="Steves & Sons", model="x62H1WASAE",
    name="Flush Hollow Core White Primed Composite Single Prehung Interior Door, 1 3/8in",
    sku="J/M/N/Q62H1WASAE + RH/LH",
    url=_HD + "Steves-Sons-32-in-x-80-in-Flush-Hollow-Core-Primed-White-Composite-Single-"
              "Prehung-Interior-Door-N62H1WASAERH/204609586",
    source="Width letter J 24 / M 30 / N 32 / Q 36, handing RH/LH: J62H1WASAERH (HD 204609584), "
           "M62H1WASAERH (204609585), M62H1WASAELH (204609581), N62H1WASAERH (204609586), "
           "N62H1WASAELH (204609582), Q62H1WASAELH (204609583); J..LH and Q..RH by the "
           "pattern. Not the split-jamb WASARJ line. A leaf shorter than 80in (D-B-CLOSET) "
           "is cut down and its bottom rail re-glued from the offcut.")
FLUSH_SC_PREHUNG = Product(
    tag="PROD-MASONITE-FLUSH-SC-PREHUNG", brand="Masonite", model="65726",
    name="No Panel Primed Composite Solid Core Single Prehung Interior Door, 4-9/16in flat jamb",
    sku="HD 100040543 / store 736801 (32in RH)",
    url=_HD + "Masonite-32-in-x-80-in-No-Panel-Right-Handed-Primed-Composite-Solid-Core-"
              "Single-Prehung-Interior-Door-4-9-16-in-Flat-Jamb-65726/100040543",
    source="Steves & Sons sells no flush solid-core prehung (5- and 6-panel only). The 30in and "
           "LH numbers are unread; DT-INT-DOUBLE60's pair has no retail SKU and is prehung "
           "by the yard from two 30in slabs of this line.")
FLUSH_HC_SLAB_24 = Product(
    tag="PROD-STEVES-FLUSH-HC-SLAB-24", brand="Steves & Sons", model="J62H1FADLC99",
    name="Flush Hollow Core White Primed Hardboard Composite Interior Door Slab, 24x80",
    sku="HD 204609477",
    url=_HD + "Steves-Sons-32-in-x-80-in-Flush-Hollow-Core-White-Primed-Hardboard-Composite-"
              "Interior-Door-Slab-N62H1FADLC99/204609479",
    source="24in slab J62H1FADLC99 (HD 204609477); the 32in sibling N62H1FADLC99 is the page "
           "linked. D-M-MUDC's two bypass leaves, and D-A-POCKET's 24x36 access leaf cut from "
           "one with its bottom rail re-glued.")
FLUSH_HC_SLAB_36 = Product(
    tag="PROD-MASONITE-FLUSH-HC-SLAB-36", brand="Masonite", model="14548",
    name="No Panel Primed White Smooth Flush Hardboard Hollow Core Composite Interior Door "
         "Slab, 36x80", sku="HD 202289103",
    url=_HD + "questions/Masonite-36-in-x-80-in-No-Panel-Primed-White-Smooth-Flush-Hardboard-"
              "Hollow-Core-Composite-Interior-Door-Slab-14548/202289103/4",
    source="The pocket leaf. Steves' 36in flush HC slab was not found at retail.")
JOHNSON_138F482D = Product(
    tag="PROD-JOHNSON-138F482D", brand="Johnson Hardware", model="138F482D",
    name="138F 24in 2-Door Bypass Hardware Set, 48in track (mill track, nylon wheel hanger)",
    url="https://johnsonhardware.com/138f-sliding-bypass-door-hardware",
    source="Set: 138F-048 track (6063-T6, 3.459 x 2.187in, drawing 138F600x600.jpg), four 1120 "
           "hangers (125 lb per door; 200 lb takes the 1125), one 2135 bottom guide, two #30 "
           "cup pulls (30US3, 2 1/8in bore), 2155 stop, 1712 wrench; 1060 soft-close optional. "
           "1 3/8in doors only. Install sheet IN183834 (Rev 9/23): opening width 2 doors = 2W - "
           "1in, height = door + 2 3/8in, 3/8in at the floor, hanger to door top 1 3/4-2 1/4in, "
           "pull centred 36in up.")
FLUSH_BIFOLD = Product(
    tag="PROD-IMPACT-PLUS-FLUSH-BIFOLD", brand="Impact Plus", model="BFP344-6080W",
    name="Flush primed MDF solid-core 4-panel bifold, 60x80",
    source="No stock 56in flush bifold exists (Steves flush HC bifolds are 24 and 36in units; "
           "Masonite and JELD-WEN stock 48/60in are 6-panel). Basis: the 60in unit, each panel "
           "trimmed 1in at its hinge stile to the 4'-8in opening; confirm with the supplier, "
           "else a custom 56in unit. Listing text only.")
STEEL_FLUSH_PREHUNG = Product(
    tag="PROD-MASTERCRAFT-FLUSH-STEEL-36", brand="Mastercraft (Menards)", model="4140314",
    name="Primed flush steel prehung exterior door, 36x80, 24 ga, 1 3/4in foam core",
    sku="4140314 RH outswing / 4140315 LH",
    url="https://www.menards.com/main/doors-windows-millwork/exterior-doors/front-doors/"
        "mastercraft-reg-flush-steel-prehung-exterior-door/4140314/p-1500273189704.htm",
    source="D-B-SHOP, ordered without its sill. 4-9/16in frame, RO 38 1/4 x 82in (Menards).")
STEEL_FULL_LITE_PREHUNG = Product(
    tag="PROD-MASTERCRAFT-FULL-LITE-STEEL-30", brand="Mastercraft (Menards)",
    name="Primed steel full-lite prehung exterior door, 30x80, tempered",
    url="https://www.menards.com/main/doors-windows-millwork/exterior-doors/front-doors/"
        "mastercraft-reg-primed-steel-full-lite-prehung-exterior-door/4145474/"
        "p-1517988688983-c-9356.htm",
    source="D-S-PLANT. The 36in unit is 4145474; a 30in sibling and its tempered glazing are "
           "unread, so no model: Mastercraft class, or equal.")
SAUNA_DOOR = Product(
    tag="PROD-SAUNA-DOOR-24", brand="Finnleo",
    name="All-wood insulated sauna door, 24x80, cedar, no lock",
    source="Basis of design, or equal (Saunacore, Superior Saunas): no 24in all-wood SKU was "
           "confirmed at retail. Superior's cedar all-wood door is ~27 3/8 x 80 3/8in.")
GLAZED_SLAB = Product(
    tag="PROD-TRIMLITE-1LITE-TEMPERED", brand="Trimlite",
    name="1-lite stile-and-rail primed slab, clear tempered glass, 30x80",
    source="D-M-STUDY wants the 1 3/4in slab; the 1 3/8in sibling 2668PRI1501CLET is the one "
           "read (listing text). Or equal: ARK Design W-1L-CG-30 (HD 332141977).")
SC_SLAB_134 = Product(
    tag="PROD-FLUSH-SC-SLAB-134", brand="Trimlite",
    name="Flush primed hardboard solid-core slab, 1 3/4in, 32x80",
    source="D-M-BED2's push-set leaf. Trimlite 2868FSCPHB / JELD-WEN THDJW160700219 are the "
           "32in flush solid-core slabs read; their thickness is unread, so order the 1 3/4in.")
HOLLOW_METAL_LITE = Product(
    tag="PROD-HOLLOW-METAL-24-LITE", brand="Steelcraft",
    name="Hollow-metal flush door, narrow tempered vision lite, KD frame, 24x80",
    source="D-B-ESS. Basis of design, or equal Ceco / Republic: a distributor special order "
           "(stock KD frames start at 32in), no retail SKU.")

INTERIOR_DOOR_PRODUCTS = (
    FLUSH_HC_PREHUNG, FLUSH_SC_PREHUNG, FLUSH_HC_SLAB_24, FLUSH_HC_SLAB_36, JOHNSON_138F482D,
    FLUSH_BIFOLD, STEEL_FLUSH_PREHUNG, STEEL_FULL_LITE_PREHUNG, SAUNA_DOOR, GLAZED_SLAB,
    SC_SLAB_134, HOLLOW_METAL_LITE,
)
