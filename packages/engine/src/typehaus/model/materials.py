"""Material — the numeric substrate of R-value, takeoffs, and building science (#41)."""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor


class Material(HausModel):
    """A named material. All numeric fields optional; a calc missing one reports
    UNKNOWN rather than crashing (#32). Provenance is one freeform note (#46)."""

    tag: str
    name: str
    # r_per_inch: US R-value per inch of thickness (drives R-value rollup).
    r_per_inch: float | None = None
    perm_rating: float | None = None  # US perms (Glaser input, → 50)
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
    # Optional freeform provenance (URL, standard, or "generic assumption") (#46).
    source: str | None = None


register_constructor("Material", Material)
