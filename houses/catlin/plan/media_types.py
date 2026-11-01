"""The theatre: a 98" screen on a stand-off mount and the east wall's tapestry, RM-B-PLAY-N
(plan/placeables.py).

The shared FURN-TV-98-WALL is a 4" envelope with the mount folded in. Here the body is the
panel alone and the mount is the placement's ``normal_gap``, so ED-B-PLAY-N-RC1 and -DATA1
(surface boxes, 2 5/8" with cover) sit behind the panel (geometry review C6-E11, adopted
2026-11-01).
"""

from typehaus import FurnitureType, ModelRepresentation, Mount, MountKind, inch

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

#: The east wall's first-reflection hanging: woven cotton, landscape, clipped to
#: FT-TAPESTRY-ROD-96. Its glyph is the outline and the viewer paints the face. The body is
#: the fabric alone; the placement's ``normal_gap`` is the air behind it.
DRAGON_TAPESTRY = FurnitureType(
    tag="FT-TAPESTRY-DRAGON-80X60", name='Medieval dragon woven tapestry, 80" x 60"',
    footprint=(inch(80), inch(0.25)), height=inch(60),
    plan_symbol="wall-tapestry", mount=Mount(kind=MountKind.WALL),
    source="owner, 2026-11-01: Etsy listing 4423258589 (Medieval Tapestry, Vintage Dragon "
           "Blanket), 60 x 80 in. size, hung 80 in. wide. Woven cotton throw on clip rings.",
)

#: Its rod: 96" so the end brackets clear the 80" fabric, a 4" bracket return so the fabric
#: hangs ~3" off the wall. Library rod symbol; the 14 clip rings are billed, not drawn.
TAPESTRY_ROD = FurnitureType(
    tag="FT-TAPESTRY-ROD-96", name='Curtain rod, 96", 1" dia., 4" return, 14 clip rings',
    footprint=(inch(96), inch(4)), height=inch(2),
    model_representation=ModelRepresentation(symbol="curtain-rod"),
    mount=Mount(kind=MountKind.WALL),
    source="Generic 1 in. black adjustable rod (48-96 in.), three brackets with 4 in. return, "
           "masonry anchors; 14 clip rings at about 6 in. Retail, not a selected product.",
)

MEDIA_TYPES = (TV_98_PANEL, DRAGON_TAPESTRY, TAPESTRY_ROD)
