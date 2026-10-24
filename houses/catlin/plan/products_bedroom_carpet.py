"""Provisional bedroom carpet and cushion, owner 2026-10-23; prices in prices.toml."""

from typehaus.model import Product

BEDROOM_CARPET_PRODUCTS = (
    Product(tag="PROD-STAINMASTER-SWEET-SPOT-I-ROMANO", brand="STAINMASTER PetProtect",
            model="7L89100101", name="Sweet Spot I, Romano textured nylon carpet, 12 ft wide",
            url="https://www.lowes.com/pd/5013298681",
            source='Provisional owner selection 2026-10-23: warm ivory/cream direction; '
                   'confirm Romano sample beside adjacent finishes. Published nylon, '
                   '48.8 oz/yd2 face weight, 0.56-inch pile height; twist unverified. '
                   'Pile height is not total carpet thickness including backing. '
                   'Light warm greige is the alternative color direction. '
                   'Sample, current quote, roll/seam layout and measured assembly '
                   'remain pending; notes/bedroom_carpet.md.'),
    Product(tag="PROD-FUTURE-FOAM-150553488-33", brand="Future Foam",
            model="150553488-33", sku="203393650",
            name='Rebond carpet cushion, 8 lb/ft3 density, 7/16 inch thick',
            url="https://www.homedepot.com/p/203393650",
            source='Provisional bedroom cushion 2026-10-23. Confirm carpet manufacturer '
                   'acceptance and warranty requirements before purchase. A manufacturer-'
                   'approved 3/8-inch, 8 lb/ft3 cushion is the height-coordination '
                   'alternative, not a selected product. Theater/stair pad stays separate; '
                   'notes/bedroom_carpet.md.'),
)
