"""Starter materials ported/adapted from ifcplot/assemblies.py (→ 02 migration table).

Water-vapour ratings follow the two-field split on ``Material``: ``perm_rating`` is
permeability in US perm-inch for bulk substances, ``vapor_permeance_perms`` is the
thickness-independent ASTM E96 permeance of a finished sheet. Every value below cites the
published test or manufacturer datasheet it came from, per CONTRIBUTING §3. Where the
source publishes a *range* rather than a point value, the midpoint of that published range
is used and the range is quoted in ``source`` so the reader can see the spread; nothing
here is estimated from first principles. A material with no locatable source leaves the
field unset so the Glaser walk reports UNKNOWN naming it (#32) instead of guessing.
"""

from __future__ import annotations

from typehaus.library.materials import cladding as _cladding
from typehaus.library.materials import concrete_masonry as _concrete_masonry
from typehaus.library.materials import finishes as _finishes
from typehaus.library.materials import framing as _framing
from typehaus.library.materials import insulation as _insulation
from typehaus.library.materials import membranes as _membranes
from typehaus.library.materials import sheathing as _sheathing
from typehaus.library.materials import site as _site
from typehaus.model import Material

# Each category keeps its rows in catalog order; the catalog order itself is restored
# below so a first-match lookup and every emitted listing read as before the split.
_ALL = (
    _framing.MATERIALS
    + _sheathing.MATERIALS
    + _insulation.MATERIALS
    + _membranes.MATERIALS
    + _cladding.MATERIALS
    + _finishes.MATERIALS
    + _concrete_masonry.MATERIALS
    + _site.MATERIALS
)
_ORDER = (
    "spf",
    "lsl",
    "lvl",
    "kdat",
    "glulam-treated",
    "osb",
    "struct-1-plywood",
    "zip-r",
    "zip-sheathing",
    "polyiso",
    "fiberglass",
    "mineral-wool",
    "gwb",
    "gwb-x",
    "resilient-channel",
    "air-barrier",
    "waterproofing",
    "drainage-composite",
    "dimple-board",
    "closed-cell-spray-foam",
    "polyethylene",
    "capillary-break-stone",
    "footing-crushed-stone",
    "humid-room-membrane",
    "pvc-panel",
    "fiber-cement",
    "steel-stud",
    "standing-seam",
    "corrugated-panel-26",
    "corrugated-vent-strip",
    "concrete",
    "icf-eps",
    "plywood-subfloor",
    "eps",
    "xps",
    "cedar-tg",
    "cmu",
    "grout",
    "stucco",
    "retaining-block",
    "composite-deck",
    "aluminum-deck",
    "polycarbonate-multiwall",
    "polycarbonate-solid",
    "aluminum-extrusion",
    "latex-paint",
    "gwb-primer",
    "silicate-wash-white",
    "silicate-wash-white-block",
    "silicate-wash-white-brick",
    "oak",
    "lvp",
    "lvp-underlayment",
    "carpet",
    "carpet-pad",
    "tile",
    "tile-uncoupling-membrane",
    "sealed-concrete",
    "polished-concrete",
    "coated-concrete",
    "rubber",
    "vinyl-sheet",
    "eps-deck-form",
    "rootzone-sand",
    "usga-choker-sand",
    "usga-bridging-gravel",
    "geotextile-separation",
    "kbg-sod",
    "roof-deck-vapor-barrier",
    "roof-vent-mat",
    "roof-adhered-butyl-ht",
    "df-select-s4s",
    "cabinet-plywood",
    "cdx-plywood",
    "siding-303-mdo",
    "plywood-underlayment-sanded",
    "sauna-shiplap",
    "pet-felt-panel",
    "polyiso-foil",
    "blown-fiberglass",
    "fiberglass-r19",
    "fiberglass-r30c",
    "roof-underlayment-synthetic",
    "brick",
    "foundation-coating-acrylic",
    "foundation-protection-panel",
)
_BY_TAG = {m.tag: m for m in _ALL}
assert len(_BY_TAG) == len(_ALL) == len(_ORDER)
ALL_MATERIALS: tuple[Material, ...] = tuple(_BY_TAG[t] for t in _ORDER)
