"""Shared railing/guard product catalog.

Guards are required by code at every open edge over 30", so "which guard product" is a
question every house asks — but the library had no railing catalog at all, and the only
two entries in the repo lived in ``houses/catlin/plan/railing_types.py``. They are product
definitions with no house-specific geometry (each ``Railing`` instance authors its own run),
so nothing about them was ever catlin-specific.
"""

from __future__ import annotations

from typehaus import RailingType

RAILING_EXT_ALUMINUM_FASCIA = RailingType(
    tag="RAILING-EXT-ALUMINUM-FASCIA",
    name="Exterior aluminum fascia-mounted guard",
    source="Fascia-mounted aluminum guard, balcony/deck product class",
)

RAILING_INT_STAIR_GUARD = RailingType(
    tag="RAILING-INT-STAIR-GUARD",
    name="Interior stair guard rail",
    source="Interior stair guard product class",
)

STARTER_RAILING_TYPES = (RAILING_EXT_ALUMINUM_FASCIA, RAILING_INT_STAIR_GUARD)
