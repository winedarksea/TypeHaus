"""White painted exterior MDO for the sheltered entry screen."""

from plan.entry_screen_finish_spec import (
    ACCESSORY_AREAL_DENSITY_KG_M2,
    PANEL_THICKNESS_IN,
    WOOD_DENSITY_KG_M3,
)
from typehaus import Material

MATERIALS_ENTRY_SCREEN = [
    Material(
        tag="entry-screen-white-hardware",
        name="White headed 304 stainless screws",
        density=8000,
        color="#f5f5f0",
        finish="metal",
    ),
    Material(
        tag="entry-screen-white-mdo",
        product_ref="PROD-BW-MDO",
        name="Roseburg DuraGard Premium MDO, 3/4in, exterior white paint",
        density=WOOD_DENSITY_KG_M3,
        areal_density_kg_m2=WOOD_DENSITY_KG_M3 * PANEL_THICKNESS_IN * 0.0254
        + ACCESSORY_AREAL_DENSITY_KG_M2,
        color="#f5f5f0",
        source="600 kg/m3 plywood plus five 2x4 edge nailers and 2lb hardware/paint "
        "reserve, distributed over net panel area once. Not a shear layer.",
    ),
]
