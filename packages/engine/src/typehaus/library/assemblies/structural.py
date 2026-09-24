"""Structural members and bearing bodies: beams, posts, a segmental wall, a stone footing."""

from __future__ import annotations

from typehaus.model import Assembly, ControlLayer, Layer, LayerFunction, MasonrySpec, inch

# Member assemblies: a Beam or Post names one, and the ply count or size comes from the
# element (``Beam.size``), so each is a single ply of the product.
BEAM_LVL = Assembly(
    tag="BEAM_LVL",
    layers=(
        Layer(name="lvl", material_ref="lvl", thickness=inch(1.75),
              function=LayerFunction.STRUCTURE),
    ),
    source="laminated veneer lumber beam, 1-3/4 in. plies built up per Beam.size; untreated, "
           "interior only",
)
BEAM_KDAT = Assembly(
    tag="BEAM_KDAT",
    layers=(
        Layer(name="kdat", material_ref="kdat", thickness=inch(1.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="kiln-dried-after-treatment southern pine, 1-1/2 in. plies built up per Beam.size "
           "(AWPA U1 UC3B/UC4A per exposure)",
)
BEAM_GLULAM_TREATED = Assembly(
    tag="BEAM_GLULAM_TREATED",
    layers=(
        Layer(name="glulam", material_ref="glulam-treated", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="preservative-treated southern pine structural glulam, 3-1/2 in. wide, "
           "24F-V5M1/SP (ANSI A190.1); wet-service factors apply outdoors",
)
POST_KDAT = Assembly(
    tag="POST_KDAT",
    layers=(
        Layer(name="kdat-post", material_ref="kdat", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="6x6 kiln-dried-after-treatment post, ground-contact rated (AWPA U1 UC4B)",
)
RETAINING_BLOCK_12 = Assembly(
    tag="RETAINING_BLOCK_12",
    layers=(
        Layer(name="srw-block", material_ref="retaining-block", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="AB Stones 8x12x18 SRW unit", coursing=inch(8.0),
                                  core_fill=True)),
    ),
    source="segmental retaining wall, Allan Block AB Stones (8 x 12 x 18 in.) dry-stacked, "
           "cores filled with wall rock (Allan Block Engineering Manual)",
)
FOOTING_STONE_20 = Assembly(
    tag="FOOTING_STONE_20",
    layers=(
        Layer(name="stone", material_ref="footing-crushed-stone", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE),
    ),
    source="20 in. x 8 in. consolidated crushed-stone strip footing (2024 IRC R403.5, stone "
           "per R403.4.1, sized against Table R403.4)",
)

# IRC R403.3 frost-protected shallow foundation wings (Figure R403.3(3)): horizontal XPS
# bands. What a given AFI requires over dimensions B and C is the house's own read.
FROST_WING_XPS_1IN = Assembly(
    tag="FROST_WING_XPS_1IN",
    role="band",
    layers=(
        Layer(name="xps-wing", material_ref="xps", thickness=inch(1.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="IRC R403.3 Figure R403.3(3) horizontal insulation wing, 1 in. XPS (R-5)",
)
FROST_WING_XPS_2IN = Assembly(
    tag="FROST_WING_XPS_2IN",
    role="band",
    layers=(
        Layer(name="xps-wing", material_ref="xps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="IRC R403.3 Figure R403.3(3) horizontal insulation wing, 2 in. XPS (R-10)",
)
