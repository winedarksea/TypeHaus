"""Woodford Y34-6-SS and NIDEL 34HD-BR, dimensions in inches.

Y34_Y1CATALOG.pdf (Rev. 9/25): 27.5 above grade to the nozzle datum,
9 above that to the closed lever, 1 NPS casing (1.315 OD), 3/4 hose nozzle.
Woodford Y34 Stainless Steel Sell Sheet: 304 stainless casing, orange iron head.
VACUUM BREAKERS.pdf (Rev. 08/22): 34HD, 3/4 FHT inlet / MHT outlet, ASSE 1011.
Casting profiles and breaker envelope are visual approximations calibrated against
those illustrations and the 1.0625 OD hose thread; they are not shop dimensions.
"""

from dataclasses import dataclass

YARD_HYDRANT_SYMBOL = "woodford-y34ss"
VACUUM_BREAKER_PRODUCT = "Woodford-34HD-BR"
HYDRANT_SYMBOLS = frozenset({"hydrant", YARD_HYDRANT_SYMBOL})


@dataclass(frozen=True)
class YardHydrantDimensions:
    casing_outside_diameter: float = 1.315
    casing_top: float = 26.75
    nozzle_height: float = 27.5
    height: float = 36.5
    width: float = 2.4
    depth: float = 9.6
    nozzle_forward: float = 4.25
    hose_thread_diameter: float = 1.0625
    nozzle_thread_length: float = 0.55
    casting_width: float = 1.45
    lever_width: float = 0.55
    pivot_diameter: float = 0.48
    packing_nut_diameter: float = 1.05
    packing_nut_height: float = 0.6
    # (depth, elevation), with the outlet toward -depth; local z=0 is grade.
    casting_profile: tuple[tuple[float, float], ...] = (
        (-0.85, 26.5), (0.85, 26.5), (0.95, 28.1), (0.15, 29.4),
        (-0.9, 29.4), (-1.3, 30.1), (-2.0, 30.1), (-2.1, 29.2),
        (-4.6, 29.2), (-4.8, 28.55), (-4.8, 28.05), (-3.7, 28.05),
        (-3.55, 28.6), (-2.4, 28.6), (-1.55, 28.2),
    )
    lever_profile: tuple[tuple[float, float], ...] = (
        (-2.1, 29.2), (-1.65, 29.2), (-1.1, 35.85), (0.8, 35.85),
        (0.8, 36.5), (-1.6, 36.5),
    )
    # The open loop's bars preserve the gap rather than filling it with an orange slab.
    handle_loop: tuple[tuple[float, float], ...] = (
        (0.25, 35.25), (1.45, 35.1), (2.0, 33.8), (3.2, 32.8),
        (3.65, 31.6), (3.65, 29.0), (3.25, 28.45), (0.85, 28.15),
    )
    handle_bar_diameter: float = 0.4
    linkage_diameter: float = 0.3
    linkage_bottom: float = 29.7
    linkage_top: float = 35.2
    linkage_depth: float = 0.1


@dataclass(frozen=True)
class VacuumBreakerDimensions:
    diameter: float = 1.45
    length: float = 2.05
    thread_diameter: float = 1.0625
    thread_length: float = 0.5
    engagement: float = 0.35
    collar_length: float = 0.45
    body_radius: float = 0.67
    vent_radius: float = 0.51
    vent_band_length: float = 0.12
    vent_count: int = 8
    vent_bridge_width: float = 0.1
    stop_screw_radius: float = 0.08
    stop_screw_length: float = 0.32


Y34SS = YardHydrantDimensions()
BREAKER_34HD = VacuumBreakerDimensions()
