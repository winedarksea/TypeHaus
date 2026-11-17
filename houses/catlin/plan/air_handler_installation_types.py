"""Attic installation selection; cabinet facts remain in the shared Gree catalog."""

import math

from typehaus import (
    AirHandlerInstallation,
    ClearancePolicy,
    ClearanceZone,
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
    name="Primary condensate trap, capped cleanout and downstream open vent assembly",
    source="Gree indoor IOM section 4.4 printed p.25: 2 in inlet/outlet drop, 3 in seal, "
           "vent minimum 2 in above inlet. Includes local feeder and fittings, billed here "
           "once; PR-A-COND-HP1 takeoff starts at the trap outlet. Fitting/socket takeouts "
           "and cleanout access require installer dry-fit.",
)
AIR_HANDLER_INSTALLATION_PRODUCTS = (SS3, PAN, RAIL, TRAP)

INSTALLATION = AirHandlerInstallation(
    float_switch_product_ref=SS3.tag,
    source="Gree indoor IOM section 4.4, printed p.25: pitch >=1/8 in/ft toward drain; "
           "trap inlet/outlet drop >=2 in, seal >=3 in, downstream vent >=2 in above inlet. "
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
    ports.append(ServicePort(
        tag="condensate_trap_outlet", service=Service.DRAIN,
        position=tuple(inch(v) for v in INSTALLATION.trap_outlet_in(primary.position[2].inches)),
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
