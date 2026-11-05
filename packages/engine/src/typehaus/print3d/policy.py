"""What goes into the print, and how: one table from element kind to treatment.

``BODY`` is thickened up to the minimum wall, ``DETAIL`` up to the minimum feature, ``TRIM``
is never thickened and is dropped when thinner than a feature, ``DROP`` never prints and
``LOOSE`` is movable furniture, printed as its own pieces. An unknown kind raises: a new
kind needs a row here, not a silent guess.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Treatment(Enum):
    BODY = "body"
    DETAIL = "detail"
    TRIM = "trim"
    DROP = "drop"
    LOOSE = "loose"


_B, _D, _T, _X = Treatment.BODY, Treatment.DETAIL, Treatment.TRIM, Treatment.DROP

#: IR kinds, plus the placeable pseudo-kinds ``policy.placeable_kind`` names.
KIND_POLICY: dict[str, Treatment] = {
    # The building's body.
    **dict.fromkeys(("wall", "slab", "floor", "ceiling", "roof", "stair", "soffit", "fascia",
                     "column", "beam", "countertop", "slab_band", "slab_platform",
                     "slab_finish", "pad"), _B),
    # Fixed things in the house.
    **dict.fromkeys(("fixture", "appliance", "casework", "equipment", "luminaire_surface",
                     "trellis"), _D),
    # Thin trim: printed only where it is already thick enough.
    **dict.fromkeys(("cladding_trim", "baseboard", "door_casing", "window_return",
                     "window_stool", "gutter", "opening_lining"), _T),
    # Site and landscape.
    **dict.fromkeys(("plant", "earth", "backfill_native", "backfill_cap", "footing", "sub_slab",
                     "drain_tile", "french_drain", "drywell", "area_drain", "area_drain_riser",
                     "sump", "rain_garden_media", "rain_garden_stone", "planting_soil",
                     "planting_fill", "leader_extension", "drain_column", "site"), _X),
    # A downspout stands off the wall on brackets nobody models: printed, it floats.
    "downspout": _X,
    # Structure detail.
    **dict.fromkeys(("framing", "connector", "connector_embedded", "connector_hanger",
                     "panel_strap", "beam_cap", "rebar"), _X),
    # MEP runs, boxes and devices.
    **dict.fromkeys(("pipe_drain", "pipe_vent", "pipe_water_cold", "pipe_water_hot",
                     "pipe_radon", "pipe_sump_discharge", "pipe_sleeve", "duct_supply",
                     "duct_return", "duct_exhaust", "duct_outdoor_air", "duct_transfer",
                     "conduit_power", "conduit_data", "electrical_box", "vent",
                     "terminal_neck", "shutoff", "main_shutoff", "backflow_preventer",
                     "water_hammer_arrestor", "vacuum_breaker", "ro_stub", "cleanout_fitting",
                     "cleanout_extension", "cleanout_cap", "insulation_wrap",
                     "duct_fitting", "duct_damper", "duct_connector", "duct_support",
                     "penetration_seal", "register", "electrical_device",
                     "luminaire_suspended"), _X),
    # Envelope accessories, glazing and leaves (openings print as clean holes).
    **dict.fromkeys(("flashing", "opening_flashing_membrane", "opening_sill_pan", "bug_screen",
                     "seam_clamp", "snow_guard", "movement_joint", "thermal_break",
                     "insulation", "tub_batt", "tub_insulation_return", "tub_mortar_bed",
                     "fireblock", "opening"), _X),
    **dict.fromkeys(("solar_panel", "railing", "railing_infill"), _X),
    "furniture": Treatment.LOOSE,
}

#: What ``--include KIND`` makes of a dropped kind.
INCLUDED_AS: dict[str, Treatment] = {"site": _B, "railing": _T, "railing_infill": _T,
                                     "solar_panel": _D}


@dataclass(frozen=True)
class PrintSettings:
    bed_mm: tuple[float, float, float] = (256.0, 256.0, 256.0)
    margin_mm: float = 4.0
    nozzle_mm: float = 0.4
    #: Default to one and two extrusion widths (Arachne prints two lines at 2x nozzle).
    min_feature_mm: float | None = None
    min_wall_mm: float | None = None
    max_thicken: float = 3.0
    min_piece_m: float = 0.6
    min_island_mm3: float = 2.0
    plate_mm: float = 1.5
    plate_margin_mm: float = 3.0
    scale: int | None = None
    include: frozenset[str] = field(default_factory=frozenset)
    exclude: frozenset[str] = field(default_factory=frozenset)
    furniture: bool = True

    @property
    def feature_mm(self) -> float:
        return self.min_feature_mm if self.min_feature_mm is not None else self.nozzle_mm

    @property
    def wall_mm(self) -> float:
        return self.min_wall_mm if self.min_wall_mm is not None else 2 * self.nozzle_mm


def treatment(kind: str, settings: PrintSettings) -> Treatment:
    if kind not in KIND_POLICY:
        raise ValueError(f"print3d has no policy row for element kind {kind!r}; add one to "
                         "print3d/policy.KIND_POLICY")
    if kind in settings.exclude:
        return Treatment.DROP
    base = KIND_POLICY[kind]
    if kind in settings.include and base is Treatment.DROP:
        return INCLUDED_AS.get(kind, Treatment.DETAIL)
    return base


def placeable_kind(item, product_type, fixed: bool) -> str:
    """The policy row for a canvas object (furniture, fixture, appliance, device)."""
    if item.kind == "Fixture":
        return "fixture"
    if item.kind == "Appliance":
        return "appliance"
    if item.kind == "Equipment":
        return "equipment"
    if item.kind == "Register":
        return "register"
    if item.kind == "Furniture":
        return "casework" if fixed else "furniture"
    form = getattr(getattr(product_type, "form", None), "value", None)
    if form is None:
        return "electrical_device"
    hung = item.suspension_m is not None or form in {"pendant", "chandelier"}
    if hung:
        return "luminaire_suspended"
    return "electrical_device" if form in {"recessed_can", "strip"} else "luminaire_surface"
