"""Surface post hardware and explicit bearing conditions at its stations."""

from typing import Literal

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class SurfaceMountSpec(HausModel):
    product: str
    stair_bottom_clearance: Length
    bottom_clearance: Length
    base_width: Length
    display_base_thickness: Length
    display_hole_spacing: Length
    wood_screw_diameter: Length
    wood_screw_length: Length
    concrete_anchor_diameter: Length
    concrete_anchor_length: Length
    display_head_width: Length
    display_head_height: Length
    source: str

    @model_validator(mode="after")
    def validate_dimensions(self):
        if any(isinstance(value := getattr(self, name), Length) and value.meters <= 0
               for name in type(self).model_fields):
            raise ValueError("surface mount dimensions must be positive")
        if self.display_hole_spacing >= self.base_width:
            raise ValueError("surface mount holes must fit within the base")
        return self


class SurfacePostMount(HausModel):
    """Bearing top; optional rectangular backing below the finished tread.

    Backing dimensions are along rail / across rail / vertical; the offset is in
    project x/y so the block can span the actual adjacent stringer faces.
    """

    elevation: Length
    substrate: Literal["wood", "concrete"]
    backing_size: tuple[Length, Length, Length] | None = None
    backing_offset: tuple[Length, Length] | None = None
    finish_thickness: Length | None = None

    @model_validator(mode="after")
    def validate_backing(self):
        if self.backing_size is not None:
            if (self.substrate != "wood" or self.backing_offset is None
                    or self.finish_thickness is None):
                raise ValueError("wood backing requires an offset and finish thickness")
            if any(value.meters <= 0 for value in self.backing_size):
                raise ValueError("backing dimensions must be positive")
        return self
