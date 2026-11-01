"""The theatre screen: a 98" panel on a stand-off mount, RM-B-PLAY-N (plan/placeables.py).

The shared FURN-TV-98-WALL is a 4" envelope with the mount folded in. Here the body is the
panel alone and the mount is the placement's ``normal_gap``, so ED-B-PLAY-N-RC1 and -DATA1
(surface boxes, 2 5/8" with cover) sit behind the panel (geometry review C6-E11, adopted
2026-11-01).
"""

from typehaus import FurnitureType, Mount, MountKind, inch

#: Wall to panel back. Box plus raised cover is 2 5/8"; a flat plug takes the remaining 7/8".
TV_MOUNT_STANDOFF = inch(3.5)

TV_98_PANEL = FurnitureType(
    tag="FT-TV-98-PANEL", name='98" television panel on a 3 1/2" stand-off wall mount',
    footprint=(inch(85.3), inch(3)), height=inch(50.1), plan_symbol="tv-wall",
    mount=Mount(kind=MountKind.WALL),
    source="Owner tier: mid Sony/Samsung QLED, model not chosen. 85.3 x 50.1 in. as the "
           "shared FURN-TV-98; the 3 in. panel depth is a placeholder until the model is "
           "picked. Mount: any listed 98 in. mount with >= 3 1/2 in. wall-to-VESA depth.",
)

MEDIA_TYPES = (TV_98_PANEL,)
