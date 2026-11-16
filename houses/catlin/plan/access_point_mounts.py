"""Keep ceiling AP backs on their mounting planes as reference thickness changes."""

from library.network_devices import U6_PRO_THICKNESS

from typehaus import Mount, MountKind, ft

KITCHEN_ACCESS_POINT_MOUNT = Mount(kind=MountKind.CEILING, drop=U6_PRO_THICKNESS)
PORCH_ACCESS_POINT_MOUNT = Mount(
    kind=MountKind.CEILING, elevation=ft(8, 6) - U6_PRO_THICKNESS,
)
