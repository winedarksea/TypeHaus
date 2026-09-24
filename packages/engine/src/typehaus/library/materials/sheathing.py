"""Structural and non-structural wood panels."""

from __future__ import annotations

from typehaus.library.materials._common import _APA
from typehaus.model import Material

MATERIALS: tuple[Material, ...] = (
    Material(
        tag="osb",
        name="OSB sheathing",
        r_per_inch=1.25,
        density=650.0,
        perm_rating=0.4,
        hatch="osb",
        color="#c9a86a",
        source=f'{_APA}: OSB 7/16" 0.91, 15/32-1/2" 0.70, 19/32-5/8" 0.72, '
        '23/32-3/4" 0.49 perm — 0.35-0.45 perm-in across those four thicknesses',
    ),
    Material(
        tag="struct-1-plywood",
        name="Structural 1 plywood",
        r_per_inch=1.25,
        density=600.0,
        perm_rating=0.30,
        hatch="osb",
        color="#c9a86a",
        source=f'{_APA}: 0.8 perm for 3/8" Exterior-type plywood (species-weighted '
        "from a 0.45-1.43 perm dry-cup series) = 0.30 perm-in",
    ),
    # ZIP-R is a bonded WRB/OSB/polyiso/facer sandwich, not a depth of one substance, so its
    # rating is authored as a panel permeance.
    Material(
        tag="zip-r",
        name="ZIP System R-sheathing",
        r_per_inch=4.0,
        vapor_permeance_perms=0.95,
        hatch="osb",
        color="#3f6d3a",
        source="Huber ZIP System R-sheathing published ASTM E96 Procedure B (wet cup) "
        "assembly permeance 0.8-1.1 perm; midpoint of the published range",
    ),
    # Plain ZIP — OSB with a bonded WRB facer, no foam. Unlike ZIP-R it *is* a depth of one
    # substance (the facer is a film), so it carries an R per inch like the OSB it is, and
    # its rating is authored as a panel permeance because the facer, not the wood, governs.
    # The taped seams are what make it the air barrier; the panel is the vapour retarder.
    Material(
        tag="zip-sheathing",
        name="ZIP System sheathing",
        r_per_inch=1.25,
        density=650.0,
        vapor_permeance_perms=2.0,
        hatch="osb",
        color="#3f6d3a",
        source="Huber ZIP System sheathing published ASTM E96 Procedure A (dry cup) "
        'panel permeance 2-3 perm at 7/16-1/2"; low end of the published range',
    ),
    Material(
        tag="plywood-subfloor",
        name='3/4" plywood subfloor',
        r_per_inch=1.25,
        density=600.0,
        perm_rating=0.30,
        hatch="osb",
        color="#c9a86a",
        source=f'{_APA}: 0.8 perm for 3/8" Exterior-type plywood = 0.30 perm-in',
    ),
    Material(
        tag="cabinet-plywood",
        name='Cabinet-grade hardwood plywood (3/4")',
        r_per_inch=1.25,
        density=610.0,
        perm_rating=0.30,
        hatch="lumber",
        color="#c8a97a",
        finish="clear-satin-hardwax-oil",
        source="Hardwood plywood catalog properties; permeance per APA plywood data.",
    ),
    Material(
        tag="cdx-plywood",
        name='5/8" CDX sheathing plywood',
        r_per_inch=1.25,
        density=600.0,
        perm_rating=0.30,
        hatch="osb",
        color="#c9a86a",
        source="APA Rated Sheathing CDX properties and published plywood permeance data.",
    ),
    Material(
        tag="plywood-underlayment-sanded",
        name='23/32" sanded-face underlayment plywood, T&G (Sturd-I-Floor 24 oc)',
        r_per_inch=1.25,
        density=600.0,
        perm_rating=0.30,
        hatch="osb",
        color="#dcc79a",
        source="APA underlayment/subfloor and Sturd-I-Floor published properties.",
    ),
)
