"""Concrete, masonry units and grout."""

from __future__ import annotations

from typehaus.library.materials._common import _UAF
from typehaus.model import Material

MATERIALS: tuple[Material, ...] = (
    Material(
        tag="concrete",
        name="Cast-in-place concrete",
        r_per_inch=0.08,
        density=2400.0,
        perm_rating=3.2,
        hatch="concrete",
        color="#a9a9a9",
        finish="cast-concrete",
        source=f"{_UAF}: 'Concrete, 1:2:4 mix' 3.2 perm-in (1.25 perm at 4\")",
    ),
    Material(
        tag="mortar", name="Cementitious mortar bedding",
        hatch="concrete", color="#a39d90",
        source="Kohler 1196030-2-E: 1-2 in. cement or mortar bed under the bath; "
               "colour is representative, not a specified mortar mix",
    ),
    # --- masonry and concrete commodities ------------------------------------------------
    Material(
        tag="cmu",
        name='Grouted CMU (8")',
        r_per_inch=0.11,
        density=2000.0,
        perm_rating=2.5,
        hatch="concrete",
        color="#b8b3ab",
        finish="cmu",
        source="grouted 8 in. concrete masonry unit wythe; concrete masonry ~2-3 perm-in",
    ),
    Material(
        tag="grout",
        name="Masonry grout",
        r_per_inch=0.08,
        density=2240.0,
        perm_rating=2.5,
        hatch="concrete",
        color="#9a958c",
        source="fills CMU cores; cementitious grout ~2-3 perm-in",
    ),
    Material(
        tag="retaining-block",
        name="Segmental concrete retaining-wall block",
        r_per_inch=0.08,
        density=2200.0,
        perm_rating=2.5,
        hatch="concrete",
        color="#a8a49c",
        finish="cmu",
        source="dry-stacked segmental retaining-wall (SRW) unit, no mortar",
    ),
)
