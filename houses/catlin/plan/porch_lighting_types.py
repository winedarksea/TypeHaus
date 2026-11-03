"""Garden flood allowance and its framing-derived underside mount."""

from library.lighting import luminaire_class
from params.sunken_garden import GARDEN_FLOOD_POSITION, GARDEN_FLOOD_SUPPORT_ELEVATION
from typehaus import Mount, MountKind, inch
from typehaus.model.placeable_symbols._flood_light import (
    FLOOD_BEAM_DEGREES,
    FLOOD_DOWNWARD_AIM_DEGREES,
)

# Retain the 20 W / 1,800 lm planning allowance, but give the garden a flood optic.
# The shared narrow flood remains available to houses that actually want a spot.
# Envelope is the Alcon 11414-KN-SM line drawing: 7 5/8" head width, 5" head, 8.7" overall.
GARDEN_FLOOD_TYPE = luminaire_class("ED-T-LT-FLOOD-NARROW").model_copy(update={
    "tag": "ED-T-LT-FLOOD-GARDEN",
    "name": "Sunken garden adjustable LED flood, wet",
    "full_cutoff": False,
    "type_mark": "S",
    "replaceable_lamp": False,
    "plan_symbol": "flood-light",
    "footprint": (inch(7.625), inch(5)),
    "height": inch(8.7),
    "lamp": f"LED integrated, {FLOOD_BEAM_DEGREES:g} deg beam",
    "product_ref": "PROD-ALCON-11414-KN",
    "source": f"Alcon 11414-KN-SM-BK: black wet-listed knuckle flood, switched to 20 W and "
              f"3000K, 0-10 V; knuckle on a box fastened up to the balcony blocking, aimed "
              f"{FLOOD_DOWNWARD_AIM_DEGREES:g} deg below horizontal into the open court. "
              f"Beam and 20 W lumens unpublished; {FLOOD_BEAM_DEGREES:g} deg and "
              "20 W / 1800 lm remain the allowance.",
})
GARDEN_FLOOD_MOUNT = Mount(
    kind=MountKind.CEILING,
    elevation=GARDEN_FLOOD_SUPPORT_ELEVATION - GARDEN_FLOOD_TYPE.height,
)

__all__ = ["GARDEN_FLOOD_TYPE", "GARDEN_FLOOD_MOUNT", "GARDEN_FLOOD_POSITION"]
