"""Entry guard and shear wall with direct-mounted white MDO screen panels."""

from plan.entry_screen_finish_spec import (
    FINISH_BOTTOM_IN,
    FINISH_TOP_IN,
    PANEL_RUNS_IN,
    PANEL_THICKNESS_IN,
)
from typehaus import (
    Assembly,
    FramingSpec,
    Layer,
    LayerBound,
    LayerDatum,
    LayerExtent,
    LayerFunction,
    SheathingNailing,
    inch,
)

_FINISH_EXTENT = LayerExtent(
    bottom=LayerBound(datum=LayerDatum.WALL_TOP, offset=inch(FINISH_BOTTOM_IN - 48)),
    top=LayerBound(datum=LayerDatum.WALL_TOP, offset=inch(FINISH_TOP_IN - 48)),
)

ENTRY_SCREEN_WALL = Assembly(
    tag="ENTRY_SCREEN_WALL",
    layers=(
        *(
            Layer(
                name=f"mdo-in-{index}",
                material_ref="entry-screen-white-mdo",
                thickness=inch(PANEL_THICKNESS_IN),
                function=LayerFunction.CLADDING,
                extent=_FINISH_EXTENT,
                slot="east-screen-panels",
                run_span=(inch(start), inch(end)),
            )
            for index, (start, end) in enumerate(PANEL_RUNS_IN, 1)
        ),
        Layer(
            name="stud",
            material_ref="kdat",
            thickness=inch(3.5),
            function=LayerFunction.STRUCTURE,
            framing=FramingSpec(member="2x4", spacing=inch(16)),
        ),
        Layer(
            name="cdx-out",
            material_ref="cdx-plywood",
            thickness=inch(0.625),
            function=LayerFunction.SHEATHING,
            nailing=SheathingNailing(
                part="S8ACN",
                edge_oc_in=4.0,
                field_oc_in=12.0,
                blocked=True,
                source="canopy_west_band.md 4a: SDPWS-2015 Table 4.3A 8d at 4 in edges; "
                "SDPWS 4.3.7.1 12 in field",
            ),
        ),
        Layer(
            name="cladding-out",
            material_ref="corrugated-panel-24",
            thickness=inch(0.875),
            function=LayerFunction.CLADDING,
        ),
    ),
    source="Owner selected white painted 3/4in exterior MDO, directly screwed to framing. "
    "Four removable panels, 1/4in behind timber; no WRB or ventilation cavity. "
    "Six supplemental 2x4 edge nailers and three 2x6 centre plies; scheduled dead load included. Lower timber attachment acceptance blocked pending local connection checks. "
    "Seal all faces, edges and holes; see notes/entry_screen_mdo.md.",
)
