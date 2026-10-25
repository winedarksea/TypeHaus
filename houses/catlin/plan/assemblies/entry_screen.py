"""Entry guard/shear wall: west structure; independently supported east thin brick."""
from typehaus import (
    Assembly, ControlLayer, FramingSpec, Layer, LayerBound, LayerDatum, LayerExtent,
    LayerFunction, inch,
)
from plan.entry_screen_finish_spec import (
    BACKER_THICKNESS_IN, BOND_MEMBRANE_THICKNESS_IN, BRICK_THICKNESS_IN,
    DRAINAGE_THICKNESS_IN, FINISH_BOTTOM_IN, FINISH_TOP_IN, PACKING_THICKNESS_IN,
    PLYWOOD_THICKNESS_IN, SETTING_MORTAR_THICKNESS_IN, WRB_THICKNESS_IN,
)

# The backing keeps closing the guard down to -1 inch; masonry starts above splash.
_VENEER_EXTENT = LayerExtent(
    bottom=LayerBound(datum=LayerDatum.WALL_TOP, offset=inch(FINISH_BOTTOM_IN - 48)),
    top=LayerBound(datum=LayerDatum.WALL_TOP, offset=inch(FINISH_TOP_IN - 48)),
)

ENTRY_SCREEN_WALL = Assembly(
    tag="ENTRY_SCREEN_WALL",
    layers=(
        Layer(name="thin-brick-in", material_ref="thin-brick-brown",
              thickness=inch(BRICK_THICKNESS_IN), function=LayerFunction.CLADDING,
              extent=_VENEER_EXTENT),
        Layer(name="setting-mortar-in", material_ref="mvis-thin-brick-mortar",
              thickness=inch(SETTING_MORTAR_THICKNESS_IN), function=LayerFunction.FINISH,
              extent=_VENEER_EXTENT),
        Layer(name="bond-membrane-in", material_ref="mvis-air-water-barrier",
              thickness=inch(BOND_MEMBRANE_THICKNESS_IN), function=LayerFunction.MEMBRANE,
              extent=_VENEER_EXTENT),
        Layer(name="cement-board-in", material_ref="permabase-exterior",
              thickness=inch(BACKER_THICKNESS_IN), function=LayerFunction.SHEATHING,
              extent=_VENEER_EXTENT),
        Layer(name="drainage-in", material_ref="thin-brick-drainage-mat",
              thickness=inch(DRAINAGE_THICKNESS_IN), function=LayerFunction.DRAINAGE,
              extent=_VENEER_EXTENT),
        Layer(name="wrb-in", material_ref="entry-screen-wrb",
              thickness=inch(WRB_THICKNESS_IN), function=LayerFunction.MEMBRANE,
              control=frozenset({ControlLayer.WATER})),
        Layer(name="siding-in", material_ref="entry-screen-exterior-plywood",
              thickness=inch(PLYWOOD_THICKNESS_IN), function=LayerFunction.SHEATHING,
              sheet_length=inch(108)),
        Layer(name="packing-in", material_ref="kdat", thickness=inch(PACKING_THICKNESS_IN),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1.125x1.5", spacing=inch(16), direction="vertical")),
        Layer(name="stud", material_ref="kdat", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16))),
        Layer(name="cdx-out", material_ref="cdx-plywood", thickness=inch(0.625),
              function=LayerFunction.SHEATHING),
        Layer(name="cladding-out", material_ref="corrugated-panel-24", thickness=inch(0.875),
              function=LayerFunction.CLADDING),
    ),
    source="W-BW-SCREEN east finish, 2026-10-25: purchased 1/2in ASTM C1088 Exterior thin "
           "brick matching the house brown blend, grey joints, over MVIS mortar/membrane, "
           "1/2in exterior PermaBASE, 1/4in drainage mat, WRB and 5/8in Exterior plywood. "
           "1-1/8in KDAT packing at studs clears the projecting posts by 1/8in; no veneer "
           "fixings into post faces. WEST 5/8in CDX alone supplies shear; west corrugated, "
           "stud axis and guard geometry retained. Masonry band +2 to +47.5in. See "
           "notes/bw_screen_thin_brick.md for attachment, joints and construction-release gates.",
)
