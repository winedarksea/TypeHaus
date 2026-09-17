# haus: editable
from typehaus import (
    Door,
    DoorType,
    Node,
    Occupancy,
    Room,
    Wall,
    Window,
    WindowType,
    centered,
    from_node,
    ft,
    inch,
    pt,
    u_us,
)

# The one storey, wired in manifest.py. The editor's wall and room tools append here.
DOOR_TYPES = [
    DoorType(tag="DT-EXT36", width=ft(3), height=ft(6, 8), exterior=True,
             u_factor=u_us(0.20)),
    DoorType(tag="DT-INT32", width=ft(2, 8), height=ft(6, 8)),
]
WINDOW_TYPES = [
    WindowType(tag="WT-3050", width=ft(3), height=ft(5),
               u_factor=u_us(0.25), shgc=0.35, vt=0.5, operation="double_hung"),
]

NODES = []

WALLS = []

OPENINGS = []

ROOMS = []
