"""Variant-controlled sunken-garden choices, kept separate from its large geometry module."""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.source.parameter_overrides import parameter


@dataclass(frozen=True)
class SunkenGardenOption:
    planting_layout: str
    raised_soil_height_in: float
    planting_width_in: float
    planter_setback_in: float
    cladding: str
    stem_thickness_in: float
    footing_width_in: float
    footing_toe_in: float
    # Heel growth outboard, toe and the others' outboard reach unchanged (court sliding study,
    # notes/court_sliding_levers_study.md). Drawn: FT-SG-S +6" with a #5 @ 9" heel top bar
    # (free body §15n); a grown heel's top-x takes heel_top_bar @ heel_top_spacing_in.
    south_heel_extension_in: float = 6.0
    side_heel_extension_in: float = 0.0
    heel_top_bar: int = 5
    heel_top_spacing_in: float = 9.0

    @property
    def is_reference(self) -> bool:
        return self.planting_layout == "reference"

    @property
    def has_raised_bed(self) -> bool:
        return self.planting_layout in ("against-wall", "setback")

    @property
    def needs_court_guard(self) -> bool:
        return self.planting_layout == "against-wall"


def _option() -> SunkenGardenOption:
    option = SunkenGardenOption(
        planting_layout=parameter("sunken_garden.planting_layout", "reference"),
        raised_soil_height_in=parameter("sunken_garden.raised_soil_height_in", 40.0),
        planting_width_in=parameter("sunken_garden.planting_width_in", 36.0),
        planter_setback_in=parameter("sunken_garden.planter_setback_in", 36.0),
        cladding=parameter("sunken_garden.cladding", "brick"),
        stem_thickness_in=parameter("sunken_garden.stem_thickness_in", 12.0),
        footing_width_in=parameter("sunken_garden.footing_width_in", 84.0),
        footing_toe_in=parameter("sunken_garden.footing_toe_in", 36.0),
        south_heel_extension_in=parameter("sunken_garden.south_heel_extension_in", 6.0),
        side_heel_extension_in=parameter("sunken_garden.side_heel_extension_in", 0.0),
        heel_top_bar=parameter("sunken_garden.heel_top_bar", 5),
        heel_top_spacing_in=parameter("sunken_garden.heel_top_spacing_in", 9.0),
    )
    if option.planting_layout not in {"reference", "yard-grade", "against-wall", "setback"}:
        raise ValueError("sunken_garden.planting_layout must be reference, yard-grade, "
                         "against-wall, or setback")
    if option.cladding not in {"brick", "fiber-cement"}:
        raise ValueError("sunken_garden.cladding must be brick or fiber-cement")
    if option.has_raised_bed and option.raised_soil_height_in != 30.0:
        raise ValueError("proposed raised-bed variants require 30 inches of soil")
    if option.has_raised_bed and option.planting_width_in not in {24.0, 36.0}:
        raise ValueError("proposed raised-bed width must be 24 or 36 inches")
    if option.planting_layout == "setback" and option.planter_setback_in != 36.0:
        raise ValueError("setback planters require a 36-inch clear strip")
    if option.stem_thickness_in not in {10.0, 12.0}:
        raise ValueError("sunken-garden stems must be 10 or 12 inches in the sizing study")
    if not 48.0 <= option.footing_width_in <= 84.0 or option.footing_width_in % 6:
        raise ValueError("sunken-garden footing width must be 48..84 inches in 6-inch steps")
    if min(option.south_heel_extension_in, option.side_heel_extension_in) < 0.0:
        raise ValueError("sunken-garden heel extensions grow the heel; they cannot cut it")
    heel = option.footing_width_in - option.stem_thickness_in - option.footing_toe_in
    if option.footing_toe_in < 12.0 or heel < 12.0:
        raise ValueError("sunken-garden footing toe and heel must each be at least 12 inches")
    return option


OPTION = _option()

