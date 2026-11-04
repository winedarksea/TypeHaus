"""The city refuse carts the garage parks: hauler-supplied, so scheduled but never bought."""

from typehaus.model import FurnitureType, inch

# Trash (default size) and recycling are both 64 gal; the 32/96 gal sizes are on request.
CART_64 = FurnitureType(
    tag="FURN-G-CART-64",
    name="Refuse cart, 64 gal, two-wheeled",
    footprint=(inch(22), inch(26.5)),
    height=inch(44),
    plan_symbol="rolling-cart",
    source="Saint Paul coordinated collection, stpaul.gov \"Cart Dimensions\": 64 gal is "
           "22 W x 26.5 D x 44 H.",
)

GARAGE_CART_TYPES = (CART_64,)
