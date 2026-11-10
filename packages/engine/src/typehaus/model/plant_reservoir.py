"""Plant reservoir design allowances; calibrated volumes are not inferred from its mesh.

The BRUTE's outside profile is a drawing envelope, not an internal capacity curve. Fill and
cutoff marks must be established with measured water before this budget is commissioned.
"""

from dataclasses import dataclass

from typehaus.quantities import M_PER_IN

US_GALLON_M3 = 0.003785411784


@dataclass(frozen=True)
class ReservoirGeometry:
    body_diameter_in: float = 15.63
    handle_width_in: float = 18.0
    rim_height_in: float = 17.13
    installed_height_in: float = 21.0
    envelope_depth_in: float = 18.0
    discharge_height_in: float = 19.13
    discharge_x_in: float = 0.0
    discharge_y_in: float = 5.75
    inlet_height_in: float = 19.63
    # Bracket, taper, wall and water-line heights are illustrative pending delivered parts.
    bottom_radius_share: float = 0.82
    wall_thickness_in: float = 0.12
    normal_water_height_in: float = 15.0
    cutoff_height_in: float = 2.0
    rack_width_in: float = 36.0
    rack_depth_in: float = 12.0
    rack_height_in: float = 24.0
    pump_centres_in: tuple[float, float] = (-8.0, 8.0)
    pump_envelope_in: tuple[float, float, float] = (9.0, 4.5, 4.5)


@dataclass(frozen=True)
class ReservoirWaterBudget:
    nominal_gallons: float = 10.0
    normal_fill_gallons: float = 9.0
    unusable_gallons: float = 1.0
    reserve_gallons: float = 1.0
    vacation_days: int = 10
    plants_per_zone: int = 12
    zone_count: int = 2
    emitter_gallons_per_hour: float = 0.5
    maximum_fill_gallons_per_minute: float = 0.1
    # Acceptance limits, not manufacturer response-time claims. Includes water travel.
    detection_seconds: float = 60.0
    valve_closure_seconds: float = 15.0
    # Includes both full 50-ft 0.600-inch-ID headers, 100 ft of 0.170-inch-ID outlet
    # tube, suction legs and filter bodies; remeasure if installed lengths increase.
    retained_line_gallons: float = 1.75
    displaced_floor_area_m2: float = 36 * 12 * M_PER_IN**2

    @property
    def watering_gallons(self) -> float:
        return self.normal_fill_gallons - self.unusable_gallons - self.reserve_gallons

    @property
    def maximum_daily_gallons(self) -> float:
        return self.watering_gallons / self.vacation_days

    @property
    def daily_zone_runtime_seconds(self) -> float:
        return (
            self.maximum_daily_gallons
            / self.zone_count
            / (self.plants_per_zone * self.emitter_gallons_per_hour)
            * 3600
        )

    @property
    def fault_release_gallons(self) -> float:
        return (
            self.nominal_gallons
            + self.retained_line_gallons
            + self.maximum_fill_gallons_per_minute
            * (self.detection_seconds + self.valve_closure_seconds)
            / 60
        )

    def spill_depth_m(self, floor_area_m2: float, tank_footprint_m2: float) -> float:
        available = floor_area_m2 - tank_footprint_m2 - self.displaced_floor_area_m2
        if available <= 0:
            raise ValueError("reservoir containment requires positive unobstructed floor area")
        return self.fault_release_gallons * US_GALLON_M3 / available


RESERVOIR_GEOMETRY = ReservoirGeometry()
RESERVOIR_WATER_BUDGET = ReservoirWaterBudget()
