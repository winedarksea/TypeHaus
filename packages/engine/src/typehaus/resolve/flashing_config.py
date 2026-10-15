"""Physical flashing dimensions; display offsets never change these sections."""

from dataclasses import dataclass

from typehaus.quantities import inch


@dataclass(frozen=True)
class FlashingConfig:
    sheet_m: float = inch(0.032).meters
    sill_membrane_m: float = inch(0.060).meters
    perimeter_membrane_m: float = inch(0.020).meters
    head_rise_m: float = inch(3).meters
    outie_head_rise_m: float = inch(2).meters
    head_projection_m: float = inch(0.5).meters
    head_drop_m: float = inch(1.6).meters
    back_dam_m: float = inch(1.5).meters
    end_dam_m: float = inch(6).meters
    pan_drop_m: float = inch(0.75).meters
    perimeter_lap_m: float = inch(2).meters
    hem_m: float = inch(0.25).meters
    drainage_slope: float = 0.25 / 12
    obstacle_clearance_m: float = inch(0.0625).meters
    metal_material: str = "aluminum"


FLASHING = FlashingConfig()
