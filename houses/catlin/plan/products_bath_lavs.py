"""Bathroom component identities; published sheets archived in notes/assets, read 2026-10-24.

Rough-in stations are installation design, not dimensions inferred from product photos.
Purchased top/basin combinations include their overflow and drain hardware.
"""

from typehaus.model import Product

MOEN_6702 = Product(
    tag="PROD-MOEN-6702", brand="Moen", model="Genta LX 6702", sku="6702",
    name="Genta LX single-hole lavatory faucet, chrome, metal pop-up included",
    url="https://www.moen.com/products/6702",
    source="Moen 6702sp.pdf, read 2026-10-24, notes/assets/moen-6702-spec.pdf: "
           "8 7/16 in. overall, 4 9/16 in. reach, 3/8 compression supplies; optional "
           "4 in. centerset plate. 2 1/2 in. recommended rear clearance. Not for 8 in. drilling.",
)
MOEN_6702BN = MOEN_6702.model_copy(update={
    "tag": "PROD-MOEN-6702BN", "model": "Genta LX 6702BN", "sku": "6702BN",
    "name": "Genta LX single-hole lavatory faucet, brushed nickel, metal pop-up included",
})
KRAUS_INDY = Product(
    tag="PROD-KRAUS-KBF-1401-SFS", brand="Kraus", model="Indy KBF-1401SFS", sku="KBF-1401SFS",
    name="Indy single-hole basin faucet, spot-free stainless steel",
    url="https://www.kraususa.com/media/catalog/product/documentation/KBF-1401-Spec-Sheet.pdf",
    source="Kraus KBF-1401 specification, read 2026-10-24, notes/assets/kraus-kbf-1401-spec.pdf: "
           "6 1/4 in. high, 5 1/8 in. reach, 4 5/8 in. spout height; 23 5/8 in. "
           "integrated supplies, 3/8 compression, 1 1/2 in. maximum deck. Drain separate.",
)
ANGSJON_36 = Product(
    tag="PROD-IKEA-ANGSJON-36", brand="IKEA", model="ÄNGSJÖN 36", sku="905.353.52",
    name="ÄNGSJÖN 36 x 21 x 25 1/8 in. wall-hung two-drawer vanity, high-gloss white",
    url="https://www.ikea.com/us/en/p/angsjoen-bathroom-vanity-with-drawers-high-gloss-white-90535352/",
    source="IKEA US 905.353.52 and AA-2400655-5 assembly PDF, read 2026-10-24, "
           "archived in notes/assets; rear plumbing space behind drawers, supplied suspension rail. "
           "Cabinet height is above mount base. House installation: 36 in. rim. "
           "Assembly does not publish a fixed trap outlet station; use installation setout.",
)
ORRSJON_37 = Product(
    tag="PROD-IKEA-ORRSJON-37", brand="IKEA", model="ORRSJÖN 37", sku="695.169.06",
    name="ORRSJÖN 37 x 21 3/4 in. white ceramic single bowl top, overflow, single faucet hole",
    url="https://www.ikea.com/us/en/p/orrsjoen-sink-white-69516906/",
    source="IKEA US January 2026 ÄNGSJÖN guide and AA-2376395-4, read 2026-10-24, "
           "notes/assets: 37 x 21 3/4 x 2 1/2 in., centered single bowl and faucet. "
           "RÄNNILEN separately packaged. No dimensioned bowl/drain center or fixed wall "
           "stub elevation in the installation sheet; house setout recorded in lav_types.py.",
)
RANNILEN = Product(
    tag="PROD-IKEA-RANNILEN", brand="IKEA", model="RÄNNILEN 1-bowl",
    name="RÄNNILEN single-bowl space-saving water trap and overflow drain",
    url="https://www.ikea.com/us/en/assembly_instructions/raennilen-water-trap-1-bowl__AA-2141893-6-100.pdf",
    source="IKEA US AA-2141893-6, read 2026-10-24, archived in notes/assets: "
           "1 1/2 in. wall outlet; cut-to-fit horizontal/vertical tubes, no fixed AFF outlet. "
           "IKEA US pairs it with ORRSJÖN; accepted under owner policy.",
)
CHULTON_30 = Product(
    tag="PROD-KOHLER-REC39579", brand="Kohler", model="Chulton K-REC39579-ASB-0",
    name="Chulton 30 in. white floor vanity, quartz top and undermount vitreous china bowl",
    url="https://www.kohler.com/en/products/vanities/shop-vanities/chulton-30-bathroom-vanity-cabinet-with-sink-and-quartz-top-rec39579-asb",
    source="Kohler white-model dimensioned image, read 2026-10-24, "
           "notes/assets/kohler-chulton-30-dimensions.jpg: 30 15/16 x 22 7/16 in., "
           "39 5/16 in. overall including backsplash; explicitly ONE faucet hole, so 6702 fits. "
           "Retailer grouped listing says 8 in. widespread; maker image for ASB-0 controls. "
           "Rim height and rough-ins remain APPROXIMATE pending installation drawing.",
)
SEKTION_30 = Product(
    tag="PROD-IKEA-SEKTION-WALL-30-AXSTAD", brand="IKEA", model="SEKTION 30x15x30 AXSTAD",
    sku="694.614.71", name="SEKTION 30 x 14 3/4 x 30 in. wall cabinet, two AXSTAD matte white doors",
    url="https://www.ikea.com/us/en/p/sektion-wall-cabinet-with-2-doors-white-axstad-matte-white-s69461471/",
    source="IKEA US listing, read 2026-10-24; shelf/hinges included, suspension rail separate. "
           "House-fabricated plumbing chase and Corian bowl setout, not an IKEA bathroom assembly.",
)
SEKTION_24 = SEKTION_30.model_copy(update={
    "tag": "PROD-IKEA-SEKTION-WALL-24-AXSTAD", "model": "SEKTION 24x15x30 AXSTAD",
    "sku": "594.645.35", "name": "SEKTION 24 x 14 3/4 x 30 in. wall cabinet, two AXSTAD matte white doors",
    "url": "https://www.ikea.com/us/en/p/sektion-wall-cabinet-with-2-doors-white-axstad-matte-white-s59464535/",
})
HOUSE_TRAP = Product(
    tag="PROD-DEARBORN-707BN-1", brand="Dearborn", model="707BN-1", sku="707BN-1",
    name="1 1/4 in. 17 ga chrome-plated brass P-trap with cleanout and brass nuts; 1 1/2 in. wall adapter",
    url="https://www.oatey.com/products/P_041193054678/dearborn-114-in-brass-tubular-ptrap-with-cleanout",
    source="Oatey Dearborn 1 1/4 in. cleanout P-trap listing, read 2026-10-24; "
           "707BN-1, 17 ga chrome-plated brass. Installation uses a listed 1 1/2 in. "
           "wall transition; wall arm height is house installation design, not SKU geometry.",
)
SUNNERSTA_SINK = Product(
    tag="PROD-IKEA-SUNNERSTA-SINK", brand="IKEA", model="SUNNERSTA integral sink",
    name="SUNNERSTA kitchenette's included stainless sink (included in kitchenette price)",
    source="Owner selection 2026-10-24: existing SUNNERSTA sink; bowl station unverified, "
           "ports APPROXIMATE. This identity carries no separate sink charge.",
)
BATH_LAV_PRODUCTS = (MOEN_6702, MOEN_6702BN,
                     KRAUS_INDY, ANGSJON_36, ORRSJON_37, RANNILEN, CHULTON_30,
                     SEKTION_30, SEKTION_24, HOUSE_TRAP, SUNNERSTA_SINK)
