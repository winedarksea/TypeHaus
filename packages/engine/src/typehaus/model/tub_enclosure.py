"""Placed drop-in bath enclosure; dimensions are construction, not symbol decoration."""

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class TubEnclosureSpec(HausModel):
    """References stay on the fixture so moving it recomputes its enclosure detail.

    The support envelope approximates the basin bottom, not a manufacturer bearing pad.
    Lower returns are a proposed detail and never replace the mortar support.
    """

    knee_wall_refs: tuple[str, str]
    access_panel_refs: tuple[str, ...]
    deck_ref: str
    insulation_material_ref: str = "mineral-wool"
    batt_thickness: Length = inch(3.5)
    lower_return_thickness: Length = inch(3.5)
    lower_return_projection: Length = inch(3.5)
    mortar_bed_thickness: Length = inch(1)
    support_width: Length = inch(43)
    support_depth: Length = inch(25.625)
    shell_clearance: Length = inch(0.125)
    service_side_clearance: Length = inch(0)

    @model_validator(mode="after")
    def _positive_dimensions(self):
        for name in ("batt_thickness", "lower_return_thickness", "lower_return_projection",
                     "mortar_bed_thickness", "support_width", "support_depth"):
            if getattr(self, name).meters <= 0:
                raise ValueError(f"{name} must be positive")
        if self.shell_clearance.meters < 0 or self.service_side_clearance.meters < 0:
            raise ValueError("Enclosure clearances cannot be negative")
        if not self.access_panel_refs or len(set(self.access_panel_refs)) != len(
                self.access_panel_refs):
            raise ValueError("A tub enclosure needs one or more distinct access panels")
        if len(set(self.knee_wall_refs)) != 2:
            raise ValueError("A tub enclosure needs two distinct knee walls")
        return self


register_constructor("TubEnclosureSpec", TubEnclosureSpec)
