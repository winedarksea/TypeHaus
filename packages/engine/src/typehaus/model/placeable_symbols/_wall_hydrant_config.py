"""Woodford Model 19P wall faucet, inch inputs.

Reference: https://www.woodfordmfg.com/Woodford/Wall_Faucet_PDF/19CATALOG.pdf
Rev. 10/23: 3/4 MHT outlet, P inlet (3/4 MPT / 1/2 FPT), oval wheel,
polycarbonate flange and integral RK-19VB breaker. External casting dimensions
are visual approximations from the parts drawing, not manufacturing dimensions.
The modeled barrel reaches the project's 10.25-inch wall stack; installation
slope and concealed valve internals remain the installation detail's responsibility.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class WallHydrantDimensions:
    width: float = 3.0
    depth: float = 14.25
    height: float = 4.25
    barrel_length: float = 10.25
    barrel_diameter: float = 0.875
    barrel_axis_height: float = 2.25
    inlet_diameter: float = 1.05
    inlet_length: float = 0.7
    flange_width: float = 3.0
    flange_height: float = 2.75
    flange_thickness: float = 0.2
    mounting_screw_spacing: float = 2.3
    mounting_screw_diameter: float = 0.18
    mounting_screw_length: float = 0.12
    casting_width: float = 1.0
    # Depth measured outward from the wall face, height relative to the barrel axis.
    casting_profile: tuple[tuple[float, float], ...] = (
        (0.0, -0.5), (0.55, -0.5), (0.7, -1.0), (1.65, -1.75),
        (2.35, -1.4), (1.45, -0.45), (1.45, 0.55), (0.0, 0.55),
    )
    body_diameter: float = 1.15
    body_length: float = 2.4
    packing_diameter: float = 0.8
    packing_length: float = 0.65
    stem_diameter: float = 0.3
    handle_forward: float = 3.65
    handle_width: float = 2.65
    handle_height: float = 2.0
    handle_thickness: float = 0.3
    handle_opening_diameter: float = 0.67
    handle_hub_diameter: float = 0.6
    handle_spoke_width: float = 0.17
    handle_screw_diameter: float = 0.2
    handle_screw_length: float = 0.12
    breaker_forward: float = 0.85
    breaker_diameter: float = 1.05
    breaker_base_height: float = 0.45
    breaker_height: float = 1.55
    breaker_cap_height: float = 0.25
    nozzle_forward: float = 2.0
    nozzle_bottom: float = 0.0
    nozzle_thread_length: float = 0.55
    nozzle_neck_length: float = 0.45
    nozzle_neck_diameter: float = 1.12
    hose_thread_diameter: float = 1.0625
    hose_bore_diameter: float = 0.75


MODEL_19 = WallHydrantDimensions()
