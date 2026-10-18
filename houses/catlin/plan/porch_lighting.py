# haus: editable
# Porch ambient/landing light and the independently switched sunken-garden flood.
# No room= on any fitting: the exterior wet-location and dark-sky checks rely on that.

from typehaus import DeviceKind, ElectricalDevice, Mount, MountKind, deg, ft, inch, pt
from typehaus.model import Location, WallAttachment

from .porch_lighting_types import GARDEN_FLOOD_MOUNT, GARDEN_FLOOD_POSITION

PORCH_LIGHTING = [
    # West sitting bay, with the canopy at the balcony joist soffit; wet-rated fan/light.
    ElectricalDevice(uid="QTM0017AAA", tag="ED-M-PORCH-FAN", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 3), inch(-66)), type_ref="ED-T-LT-FAN60",
                     circuit="CKT-LT-MAIN", controlled_by=("ED-M-PORCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 5))),
    ElectricalDevice(uid="QTM0018AAA", tag="ED-M-PORCH-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-S2", face="left", distance_from_start=inch(78),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The first balcony bay is beyond the porch deck and enclosure. The weatherproof
    # box fixes into the modeled blocking from below, leaving the waterproof plank intact.
    # Rotation 0 aims the head south; its downward pose is shared by all 3D consumers.
    ElectricalDevice(uid="QTM001EAAA", tag="ED-M-PORCH-FLOOD", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-FLOOD-GARDEN", position=GARDEN_FLOOD_POSITION,
                     rotation=deg(0), mount=GARDEN_FLOOD_MOUNT,
                     circuit="CKT-LT-MAIN", controlled_by=("ED-M-PORCH-FLOOD-SW",)),
    # Adjacent indoor gangs: porch ambient/landing on one, garden utility light on the other.
    ElectricalDevice(uid="QTM001FAAA", tag="ED-M-PORCH-FLOOD-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-S2", face="left", distance_from_start=inch(82),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # East circulation/landing sconce, between D-M-BALC and WIN-M-LIV-S2. Together with
    # the west fan light it lights the porch even when the garden flood is switched off.
    ElectricalDevice(uid="QTM001GAAA", tag="ED-M-STAIR-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-EXT",
                     circuit="CKT-LT-MAIN", controlled_by=("ED-M-PORCH-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-S2", face="right", distance_from_start=inch(80),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
