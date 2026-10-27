"""Shared railing/guard product catalog.

Guards are required by code at every open edge over 30", so "which guard product" is a
question every house asks — but the library had no railing catalog at all, and the only
two entries in the repo lived in house-local catalogs. They are product
definitions with no house-specific geometry (each ``Railing`` instance authors its own run),
so nothing about them was ever catlin-specific.
"""

from __future__ import annotations

from typehaus import RailingType
from typehaus.quantities import inch

RAILING_EXT_ALUMINUM_FASCIA = RailingType(
    tag="RAILING-EXT-ALUMINUM-FASCIA",
    name="Exterior aluminum fascia-mounted guard",
    source="Fascia-mounted aluminum guard, balcony/deck product class",
    # Ultralox: 5" at the mounting face for flat-cut brackets (6" at the outside, high-cut).
    # Width and projection are drawing placeholders until read off the bracket drawing.
    fascia_bracket_height=inch(5),
    fascia_bracket_width=inch(3),
    fascia_bracket_projection=inch(0.25),
)

RAILING_INT_STAIR_GUARD = RailingType(
    tag="RAILING-INT-STAIR-GUARD",
    name="Interior stair guard rail",
    source="Interior stair guard product class",
)

RAILING_EXT_ALUMINUM_SURFACE = RailingType(
    tag="RAILING-EXT-ALUMINUM-SURFACE",
    name="Exterior aluminum surface-mounted guard",
    source="Surface-mounted aluminum guard product class.",
)

ALL_RAILING_TYPES = (
    RAILING_EXT_ALUMINUM_FASCIA,
    RAILING_INT_STAIR_GUARD,
    RAILING_EXT_ALUMINUM_SURFACE,
)
