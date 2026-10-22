"""Garden flood allowance and its framing-derived underside mount."""

from library.lighting import luminaire_class
from params.sunken_garden import GARDEN_FLOOD_POSITION, GARDEN_FLOOD_SUPPORT_ELEVATION
from typehaus import Mount, MountKind
from typehaus.model.placeable_symbols._flood_light import (
    FLOOD_BEAM_DEGREES,
    FLOOD_DOWNWARD_AIM_DEGREES,
)

# Retain the 20 W / 1,800 lm planning allowance, but give the garden a flood optic.
# The shared narrow flood remains available to houses that actually want a spot.
# The SKU is a 3" recessed trim (plan/products_lighting.py); the symbol and mount stay the
# surface-hung box until the balcony plank question is settled.
GARDEN_FLOOD_TYPE = luminaire_class("ED-T-LT-FLOOD-NARROW").model_copy(update={
    "tag": "ED-T-LT-FLOOD-GARDEN",
    "name": "Sunken garden adjustable LED flood, shielded, wet",
    "type_mark": "S",
    "plan_symbol": "flood-light",
    "lamp": f"LED integrated, {FLOOD_BEAM_DEGREES:g} deg beam",
    "product_ref": "PROD-ALCON-14119-3ND-TFBK-B60",
    "source": f"Alcon 14119-3ND-TFBK-B60-30K-NC-RB: black 3-inch adjustable wet-listed trim, "
              f"60 deg full flood, 3000K; underside-mounted at the balcony front, aimed "
              f"{FLOOD_DOWNWARD_AIM_DEGREES:g} deg below horizontal into the open court. "
              "60 deg delivered lumens unpublished; 20 W / 1800 lm remains the allowance.",
})
GARDEN_FLOOD_MOUNT = Mount(
    kind=MountKind.CEILING,
    elevation=GARDEN_FLOOD_SUPPORT_ELEVATION - GARDEN_FLOOD_TYPE.height,
)

__all__ = ["GARDEN_FLOOD_TYPE", "GARDEN_FLOOD_MOUNT", "GARDEN_FLOOD_POSITION"]
