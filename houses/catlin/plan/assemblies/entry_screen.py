"""Entry guard and shear wall with recessed east aluminum cassette regions."""
from plan.entry_screen_finish_spec import (
    AIRSPACE_THICKNESS_IN,
    FINISH_BOTTOM_IN,
    FINISH_TOP_IN,
    METAL_THICKNESS_IN,
    PANEL_RUNS_IN,
    WRB_THICKNESS_IN,
)
from typehaus import (
    Assembly,
    ControlLayer,
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
        *(Layer(name=f"cassette-in-{index}", material_ref="entry-screen-bone-white-aluminum",
                thickness=inch(METAL_THICKNESS_IN), function=LayerFunction.CLADDING,
                extent=_FINISH_EXTENT, slot="east-cassettes",
                run_span=(inch(start), inch(end)))
          for index, (start, end) in enumerate(PANEL_RUNS_IN, 1)),
        Layer(name="vent-in", material_ref="air", thickness=inch(AIRSPACE_THICKNESS_IN),
              function=LayerFunction.AIRGAP),
        Layer(name="wrb-in", material_ref="entry-screen-wrb", thickness=inch(WRB_THICKNESS_IN),
              function=LayerFunction.MEMBRANE, control=frozenset({ControlLayer.WATER})),
        Layer(name="stud", material_ref="kdat", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16))),
        Layer(name="cdx-out", material_ref="cdx-plywood", thickness=inch(0.625),
              function=LayerFunction.SHEATHING,
              nailing=SheathingNailing(
                  part="S8ACN", edge_oc_in=4.0, field_oc_in=12.0, blocked=True,
                  source="canopy_west_band.md 4a: SDPWS-2015 Table 4.3A 8d at 4 in edges; "
                         "SDPWS 4.3.7.1 12 in field")),
        Layer(name="cladding-out", material_ref="corrugated-panel-24", thickness=inch(0.875),
              function=LayerFunction.CLADDING),
    ),
    source="Four removable Bone White 0.050in PVDF aluminum cassettes, recessed 1/4in "
           "behind post faces, over a continuous WRB and drained ventilated space. "
           "Support edges and stiffeners off studs and blocking; isolate aluminum from "
           "treated wood and dissimilar metals. Detail, movement and load verification pending.",
)
