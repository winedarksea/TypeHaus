# haus: editable
# Catlin railing products. Geometry is authored by each Railing instance.

from typehaus import RailingType


RAILING_TYPES = (
    RailingType(
        tag="RAILING-EXT-ALUMINUM-FASCIA",
        name="Exterior aluminum fascia-mounted guard",
        source="Catlin balcony/deck guard product",
    ),
    RailingType(
        tag="RAILING-INT-STAIR-GUARD",
        name="Interior stair guard rail",
        source="Catlin attic stair guard product",
    ),
)
