"""Material — the numeric substrate of R-value, takeoffs, and building science (#41)."""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor


class Material(HausModel):
    """A named material. All numeric fields optional; a calc missing one reports
    UNKNOWN rather than crashing (#32). Provenance is one freeform note (#46)."""

    tag: str
    name: str
    # r_per_inch: US R-value per inch of thickness (drives R-value rollup).
    r_per_inch: float | None = None
    # Water-vapour *permeability* — US perm-inch, i.e. perms for one inch of thickness
    # (grain/(ft²·h·inHg·in)). The Glaser walk (→ 50) divides it by the layer thickness.
    # Author this for bulk materials whose vapour resistance scales with depth (foam,
    # mineral wool, lumber, concrete). Sheet goods use ``vapor_permeance_perms`` instead.
    perm_rating: float | None = None
    # Water-vapour *permeance* of the product as installed — US perms, thickness-independent.
    # Author this where the published ASTM E96 rating belongs to the finished sheet rather
    # than to a depth of substance (housewrap, metal cladding, foil facers, composite
    # sheathing panels): dividing such a rating by a nominal thickness would invent a number
    # the test never measured. Takes precedence over ``perm_rating`` when both are present.
    # ``0.0`` is meaningful and distinct from ``None``: a true vapour barrier, not missing data.
    vapor_permeance_perms: float | None = None
    density: float | None = None  # kg/m³ (thermal mass / dead load headroom)
    specific_heat: float | None = None  # J/kg·K (dynamic-sim headroom, unused)
    # Presentation: hatch/color key into the Nordic palette (→ 21 §Nordic preset).
    hatch: str | None = None
    color: str | None = None
    # Presentation: the named 3D finish recipe (coursing module, mortar colour, jitter) this
    # material renders with — "brick", "white-brick", "cmu", "standing-seam". Authoring it is
    # how a material *declares* its appearance; without it the renderers fall back to guessing
    # from substrings in the tag, which cannot tell white brick from red. Recipes are defined
    # once per surface (ui/src/three/materials.ts MASONRY_STYLES, emit/gltf/emitter.py).
    finish: str | None = None
    # A *coating* rather than a covering: a sealer, stain or paint that adds no measurable
    # thickness to what it is applied over. It still bills — by coverage area, with no waste
    # allowance — but it has no plane of its own, so the renderers must not draw one for it.
    # Drawing one is how a sealed slab reads as two floors: the slab, plus a finish plane
    # sitting on the same face (→ TODO "the garage seems to have two floors").
    coating: bool = False
    # The continuous-skin family this cladding belongs to, where a building wears one skin in
    # more than one specification. ``resolve.roof_edge_geometry.continuous_skin_cladding`` asks
    # "do the walls and the roofing read as one unbroken material over a flush edge?", and it
    # used to answer by comparing material TAGS. That is right until a house splits one skin
    # into several tags for a reason that has nothing to do with appearance — seam profile,
    # gauge, coating — at which point tag equality says "mixed cladding" about panels that a
    # roofer runs unbroken from grade to ridge, and the flush edge silently reverts to a
    # fascia-and-drip-edge detail nobody drew.
    #
    # Two materials sharing a ``skin_family`` are one skin for that purpose and no other: it
    # changes no quantity, no price and no building-science number. Leave it None and the old
    # tag comparison is exactly what happens, so no existing house moves.
    skin_family: str | None = None
    # Gypsum board grade, where the material *is* gypsum board. Not a general fire-rating
    # field: residential construction has exactly two rated assemblies (the garage/dwelling
    # separation and a dwelling-unit separation), and putting a fire-resistance rating on
    # every assembly would mean authoring a number for hundreds of walls that nobody tested.
    # The grade of the board, on the other hand, is printed on the board.
    #
    # ``code.R302_5_garage_separation`` reads it for R302.6's 5/8" Type X requirement where
    # habitable space sits above a garage; without it that sub-rule can only report UNKNOWN.
    gypsum_type: Literal["regular", "type-x", "type-c"] | None = None
    # Wood species ("basswood", "oak", "walnut", "elm", ...) where the material *is* a wood
    # product an estimator orders by species. Authoring it is what admits the material into
    # the species-split ``wood_surfaces`` takeoff; a wood-ish tag without it stays out —
    # species by tag-substring guessing is exactly what this field retires.
    species: str | None = None
    # Board feet ordered per square foot of coverage, on nominal stock thickness: 1.0 for
    # 4/4 stock, 1.25 for 5/4. None means "no board-feet figure" — the takeoff omits the
    # column rather than inventing a thickness (#32).
    stock_bf_per_sqft: float | None = None
    # Optional freeform provenance (URL, standard, or "generic assumption") (#46).
    source: str | None = None

    def vapor_permeance_at(self, thickness_inches: float) -> float | None:
        """Permeance in US perms for ``thickness_inches`` of this material, or None.

        None means "not authored" — the caller must report UNKNOWN naming this material
        rather than substitute a default (#32). A returned ``0.0`` is a sourced vapour
        barrier: no vapour crosses it.
        """
        if self.vapor_permeance_perms is not None:
            return self.vapor_permeance_perms
        if self.perm_rating is None or self.perm_rating <= 0.0 or thickness_inches <= 0.0:
            return None
        return self.perm_rating / thickness_inches


register_constructor("Material", Material)
