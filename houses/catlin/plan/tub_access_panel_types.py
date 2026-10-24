"""Removable Corian leaves fabricated with the Bath2 tub apron."""

from typehaus.model import FurnitureType, ModelRepresentation, Mount, MountKind, inch

_PANEL_SOURCE = (
    "Bath2 tub apron: 12 mm Corian Glacier White or equal, drawn 1/2 in. thick, "
    "flush with the fixed apron. Dimensions are the leaf; leave a 1/8 in. reveal "
    "on all four edges. Lift-out, no hinges, exposed frame or handle. Concealed "
    "retainers and stops must leave the stated service opening clear when removed; "
    "fabricator to detail retention and suction-cup removal before fabrication. "
    "Sheet stock is included in the gross apron area; per-each pricing covers "
    "cutting, edge finishing and retention only. See notes/bath2_tub_deck_finish.md."
)

TUB_ACCESS_PANEL_2015 = FurnitureType(
    tag="FT-CATLIN-TUB-ACCESS-2015", name='Corian lift-out tub apron leaf, 20" x 15"',
    footprint=(inch(20), inch(0.5)), height=inch(15),
    plan_symbol=None, mount=Mount(kind=MountKind.WALL),
    product_ref="PROD-CORIAN-GLACIER-WHITE",
    model_representation=ModelRepresentation(
        symbol="solid-surface-access-leaf",
        material_refs={"solid-surface-white": "solid-surface-fabricated"}),
    source=_PANEL_SOURCE,
)
TUB_ACCESS_PANEL_1414 = FurnitureType(
    tag="FT-CATLIN-TUB-ACCESS-1414", name='Corian lift-out tub apron leaf, 14" x 14"',
    footprint=(inch(14), inch(0.5)), height=inch(14),
    plan_symbol=None, mount=Mount(kind=MountKind.WALL),
    product_ref="PROD-CORIAN-GLACIER-WHITE",
    model_representation=ModelRepresentation(
        symbol="solid-surface-access-leaf",
        material_refs={"solid-surface-white": "solid-surface-fabricated"}),
    source=_PANEL_SOURCE,
)
