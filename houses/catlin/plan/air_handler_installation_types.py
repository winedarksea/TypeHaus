"""Attic installation selection; cabinet facts remain in the shared Gree catalog."""

import math

from typehaus import (
    AirHandlerInstallation,
    ClearancePolicy,
    ClearanceZone,
    DrainFittings,
    Footprint2D,
    Product,
    Service,
    ServicePort,
    inch,
    pt,
)
from typehaus.library.hvac_equipment import GREE_FLEXX_ULTRA_24_AH

SS3 = Product(
    tag="PROD-RECTORSEAL-97089", brand="RectorSeal", model="97089 / SS3 Gen3",
    name="Safe-T-Switch SS3 auxiliary-pan float switch, 24 VAC",
    url="https://rectorseal.com/safe-t-switch-ss3-new/",
    source="RectorSeal R50109-0724: tested to UL 508; 1-2 in deep auxiliary pans; "
           "24 VAC, 1.25 A, 6 ft leads. Body drawing is undimensioned. The model reserves "
           "1.6 x 1.58 x 3.55 in and free float travel; verify delivered body/bracket and "
           "wet-test shutdown before overflow. Interrupt the outdoor cooling call while "
           "preserving Gree's required blower delay and R32 mitigation controls.",
)
PAN = Product(
    tag="PROD-HP1-SHOP-PAN", brand="Shop-fabricated", model="49.5 x 27.25 x 2 in",
    name="Watertight galvanized emergency pan, 1/16-inch design sheet",
    source="Catlin installation design 2026-11-17: full bottom, sealed corners, no outlet; "
           "49.5 x 27.25 in outside, 2 in high. Supported continuously on existing platform. "
           "Fabricator to confirm gauge, seams and bearing under the two rails.",
)
RAIL = Product(
    tag="PROD-HP1-SUPPORT-RAIL", brand="Shop-fabricated", model="3 x 1.5 x 0.125 in tube",
    name="21 1/4-inch galvanized rectangular support rail with tapered bearing shim",
    source="Two cut rails across the cabinet depth, 36 in apart; 3 in high, 1.5 in wide, "
           "1/8 in wall. Continuous nonabsorbent tapered shim pitches cabinet south at "
           "1/8 in/ft. Verify permissible cabinet bearing stations and pan point loads.",
)
TRAP = Product(
    tag="PROD-HP1-PRIMARY-TRAP", brand="Field-fabricated", model="3/4 in Schedule 40 PVC",
    name="Primary condensate feeder, union, trap, capped cleanout and open vent assembly",
    source="Gree indoor IOM section 4.4 printed p.25: 2 in inlet/outlet drop, 3 in seal, "
           "vent minimum 2 in above inlet. Male adapter, 90, union, two tees, two 90s and "
           "cap, billed here once; the secondary keeps Gree's factory choke plug (parts list "
           "76718209). PR-A-COND-HP1 takeoff starts at the outlet tee. Drawn at Charlotte "
           "Schedule 40 takeoffs.",
)
AIR_HANDLER_INSTALLATION_PRODUCTS = (SS3, PAN, RAIL, TRAP)

CHARLOTTE_DC_PR = "Charlotte Pipe DC-PR pressure catalog, Schedule 40"
FITTINGS = DrainFittings(
    pipe_outer_diameter=inch(1.05), pipe_wall=inch(0.113),
    hub_outer_diameter=inch(1.375),
    adapter_projection=inch(29 / 32), elbow_center_to_hub=inch(1.3125),
    tee_center_to_hub=inch(1.5), cap_length=inch(1), cap_socket_depth=inch(0.75),
    plug_projection=inch(0.25), union_length=inch(1.75), union_outer_diameter=inch(2),
    source=f"{CHARLOTTE_DC_PR}, 3/4 in: pipe 1.050 OD x .113 (p.27); tee 2400 H 1 1/2 "
           "(p.31); 90 S x S H 1 5/16 (p.36); male adapter 2109 L 1 5/8 less T 23/32 "
           "(p.46); cap 2116 L 1, S 3/4 (p.50); MPT plug 2113 L 1 less T 3/4 and union "
           "2710 L 1 3/4 (p.52). Charlotte publishes no ODs: Spears 3/4 in sheets give hub "
           "M 1 5/16 +-1/16 (406-007, 447-007, 497-007), adapter hex 1 11/32 (436-007), "
           "union nut 1 31/32 (497-007), inside these 1 3/8 / 2 in allowances. The plug "
           "envelope stands in for Gree's factory choke plug 76718209.",
)

INSTALLATION = AirHandlerInstallation(
    pan_width=inch(49.5), pan_depth=inch(27.25), pan_height=inch(2), pan_sheet=inch(0.0625),
    rail_height=inch(3), rail_width=inch(1.5), rail_wall=inch(0.125),
    rail_centers=(inch(-18), inch(18)),
    cabinet_slope_in_per_ft=0.125,
    # The house target, not the 1/8 floor: the feeder is 13 3/4 in of horizontal pipe.
    feeder_slope_in_per_ft=0.25,
    # Adapter 29/32 + 90 hub 1 5/16 + a visible 1/4 in of pipe to cement.
    primary_elbow_offset=inch(2.5),
    # East of both the cabinet and pan, preserving the front service rectangle.
    trap_inlet_x=inch(27.25), trap_leg_spacing=inch(3),
    trap_outlet_drop=inch(2), trap_seal_depth=inch(3),
    vent_rise_above_inlet=inch(2.5), cleanout_rise_above_inlet=inch(2.5),
    float_switch_x=inch(-7.25), float_switch_inset=inch(1),
    float_switch_width=inch(1.6), float_switch_depth=inch(1.58),
    float_switch_height=inch(3.55), float_trip_depth=inch(1),
    fittings=FITTINGS,
    float_switch_product_ref=SS3.tag,
    source="Gree indoor IOM section 4.4, printed p.25: pitch >=1/8 in/ft toward drain; "
           "trap inlet/outlet drop >=2 in, seal >=3 in, downstream vent >=2 in above inlet; "
           "p.22: reserve easy disconnection of the main drain (the union). "
           "Pan/rails are Catlin shop designs. SS3 envelope remains provisional.",
)


def _installed_ports():
    ports = []
    angle = INSTALLATION.pitch_radians
    for port in GREE_FLEXX_ULTRA_24_AH.ports:
        direction = port.direction
        if direction is not None:
            x, y, z = direction
            direction = (x, y * math.cos(angle) - z * math.sin(angle),
                         y * math.sin(angle) + z * math.cos(angle))
        ports.append(port.model_copy(update={
            "position": tuple(inch(v) for v in INSTALLATION.pitched_point_in(
                tuple(v.inches for v in port.position))),
            "direction": direction,
        }))
    primary = next(port for port in ports if port.tag == "condensate_primary")
    outlet = INSTALLATION.drain_setout(tuple(v.inches for v in primary.position)).outlet_tee
    ports.append(ServicePort(
        tag="condensate_trap_outlet", service=Service.DRAIN,
        position=tuple(inch(v) for v in outlet),
        connection_size=inch(0.75), direction=(0, -1, 0),
        notes="Installation trap outlet; datum inherits the schematic cabinet drain station. "
              "PR-A-COND-HP1 continues from here at 1/4 in/ft.",
    ))
    return tuple(ports)


_front = -10.625 - 18.125 * math.sin(INSTALLATION.pitch_radians)
ATTIC_AIR_HANDLER_TYPE = GREE_FLEXX_ULTRA_24_AH.model_copy(update={
    "tag": "EQ-T-HP1-AH-INSTALLED",
    "name": "Gree FXU24 horizontal-left ducted air handler with Catlin pan, rails, trap and SS3",
    "air_handler_installation": INSTALLATION,
    "plan_symbol": "gree-flexx-ultra-24-horizontal",
    "ports": _installed_ports(),
    "clearances": (ClearanceZone(
        footprint=Footprint2D(points=tuple(pt(inch(x), inch(y)) for x, y in (
            (-21.75, _front), (21.75, _front),
            (21.75, _front - 24), (-21.75, _front - 24)))),
        purpose="24 inch front-panel access, measured from pitched cabinet's southmost face",
        policy=ClearancePolicy.REQUIRED,
        source="Gree FXU24 submittal p.6; pitch from indoor IOM section 4.4",
    ),),
    "source": GREE_FLEXX_ULTRA_24_AH.source + " Installation: " + INSTALLATION.source,
})

AIR_HANDLER_INSTALLATION_TYPES = (ATTIC_AIR_HANDLER_TYPE,)
