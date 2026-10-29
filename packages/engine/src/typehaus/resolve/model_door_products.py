"""Immutable resolved door product dimensions, in metres."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CasedDoorSpec:
    operation: str
    width_m: float
    base_z_m: float
    head_z_m: float
    finished_floor_z_m: tuple[float, float]
    finish_faces_m: tuple[float, float]  # relative to product center, not wall axis
    jamb_allowance_m: float
    jamb_thickness_m: float
    casing_reveal_m: float
    leaf_gap_m: float
    leaf_thickness_m: float
    leaf_bottom_z_m: float
    leaf_top_z_m: float
    leaf_normal_m: float
    stop_projection_m: float
    stop_depth_m: float
    undercut_m: float
    pocket_slot_gap_m: float
    track_height_m: float
    track_depth_m: float
    pocket_sign: int
    # The leaf, from ``ResolvedOpening.sizing``; a pocket's runs on into its slot.
    leaf_width_m: float | None = None

    frame_material_ref: str | None = None
    leaf_material_ref: str | None = None
