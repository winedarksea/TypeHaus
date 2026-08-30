"""Starter assemblies ported from ifcplot/assemblies.py (→ 02 migration table, WP1.3)."""

from __future__ import annotations

from typehaus.model import (
    Assembly,
    AssemblyInterface,
    CavityFill,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    MasonrySpec,
    PartitionLayout,
    inch,
)

# The load-bearing face the junction solver binds a concrete↔concrete return on (#44):
# the pour's inboard face, named by LAYER, not index, so an outboard skin may be added
# without invalidating the transition.
_CONCRETE_BEARING = AssemblyInterface(role="bearing", layer_name="concrete", outboard=False)

# The same mechanism for a stud wall: two framed walls are "continuous" through a
# corner/tee when they publish the same bearing material (SPF↔SPF), regardless of the
# finish either side of it.
_STUD_BEARING = AssemblyInterface(role="bearing", layer_name="stud", outboard=False)

# Painted gypsum lining. Layer order is interior → exterior everywhere the lining is
# consumed (``list(default_lining) + list(layers)``), so the paint is *first*: it is the
# room-side face, and that position is what makes it the assembly's warm-side vapour
# retarder in the Glaser walk (IRC R702.7 / R702.7.1 Class III, → checks/building_science).
_PAINT_FINISH = Layer(name="paint", material_ref="latex-paint", thickness=inch(0.01),
                      function=LayerFunction.FINISH,
                      control=frozenset({ControlLayer.VAPOR}))

_GWB_LINING = (
    _PAINT_FINISH,
    Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
)

# 2x4 wall with 1" continuous exterior insulation.
HOUSE_WALL_2X4_WITH_CI = Assembly(
    tag="HOUSE_WALL_2X4_WITH_CI",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4"),
              control={ControlLayer.THERMAL},
              cavity=CavityFill(material_ref="fiberglass")),
        Layer(name="osb", material_ref="osb", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="wrb", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="ci", material_ref="polyiso", thickness=inch(1.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        # Furring + cladding as separate layers (the catlin-house siding-stack pattern):
        # the furring is a drained-and-back-vented rainscreen cavity open to outdoor air,
        # so the Glaser walk truncates there and the fiber-cement (no published ASTM E96
        # rating) never blocks a permeance verdict for the wall behind it.
        Layer(name="furring", material_ref="spf", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical")),
        Layer(name="cladding", material_ref="fiber-cement", thickness=inch(0.3125),
              function=LayerFunction.CLADDING),
    ),
    default_lining=_GWB_LINING,
    source="Adapted from catlin-house ifcplot/assemblies.py",
)

# 2x6 wall with ZIP-R exterior sheathing (the PGH envelope).
HOUSE_WALL_2X6_WITH_ZIPR = Assembly(
    tag="HOUSE_WALL_2X6_WITH_ZIPR",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6"),
              control={ControlLayer.THERMAL},
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="zip-r", material_ref="zip-r", thickness=inch(1.5),
              function=LayerFunction.SHEATHING,
              control={ControlLayer.AIR, ControlLayer.WATER, ControlLayer.THERMAL}),
        # Furring + cladding split, same rationale as HOUSE_WALL_2X4_WITH_CI above.
        Layer(name="furring", material_ref="spf", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical")),
        Layer(name="cladding", material_ref="fiber-cement", thickness=inch(0.3125),
              function=LayerFunction.CLADDING),
    ),
    default_lining=_GWB_LINING,
    source="Adapted from catlin-house ifcplot/assemblies.py",
)

# ICF garage foundation/wall — layered solid + arithmetic unit takeoff (#23).
GARAGE_ICF = Assembly(
    tag="GARAGE_ICF",
    layers=(
        Layer(name="eps-ext", material_ref="icf-eps", thickness=inch(2.625),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="concrete", material_ref="concrete", thickness=inch(6.0),
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="ICF-6", core_fill=True,
                                  rebar_spacing=inch(16))),
        Layer(name="eps-int", material_ref="icf-eps", thickness=inch(2.625),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    interfaces=(_CONCRETE_BEARING,),
    default_lining=_GWB_LINING,
)

# --- cast concrete foundation walls ----------------------------------------------
#
# The generic 8"/12" family. A house draws the pour from here rather than re-minting it,
# and adds its own outermost protective skin (parge, panel, veneer) on top of a ``_CORE``
# tuple where it wants one — that skin is a colour and exposure decision, which is a house
# decision, while the pour, the damp-proofing, the two staggered 2" XPS courses and the
# bearing face are not.
#
# **8" vs 12" is a soil/height question, never a default.** IRC Table R404.1.2(8) is what
# decides it: at 45 psf/ft equivalent fluid density, a 10' wall retaining 7' of unbalanced
# fill takes 12" plain but 8" reinforced #6 @ 48" o.c. vertical. The 12" members here exist
# for the cases the table (or a cast deck bearing on the wall top beside the sill) actually
# earns them; picking one without reading the row for the wall's own height, backfill and
# soil class is how an unreinforced 8" wall gets built where the table required steel.
# ``structural.foundation_unbalanced_fill`` grades this from the STRUCTURE layer, so the
# thickness authored here is the thickness that gets checked.

_R404_SOURCE = ("IRC Table R404.1.2(8), plain and minimally reinforced concrete "
                "foundation walls: 45 psf/ft equivalent fluid density, 10 ft maximum "
                "wall height, 7 ft unbalanced backfill")

# Bare pours for interior cross / bearing walls — soil on neither face.
#
# **The ``INT`` token is load-bearing and must stay underscore-delimited.**
# ``mn_energy._is_interior_assembly`` is literally ``"INT" in tag.split("_")``; without it
# a bare concrete wall between two conditioned rooms is graded as basement envelope and
# fails on R-1.5. The token must not lead the tag either — ``INT_*`` is the acoustic
# namespace, whose test demands a published STC and a URL, and a cast wall has no lab test
# to cite.
FOUNDATION_WALL_8_INT = Assembly(
    tag="FOUNDATION_WALL_8_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source=_R404_SOURCE + "; 8 in. requires #6 at 48 in. o.c. vertical",
)

FOUNDATION_WALL_12_INT = Assembly(
    tag="FOUNDATION_WALL_12_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source=_R404_SOURCE + "; 12 in. reads NR (no vertical reinforcement required)",
)

# Below-grade envelope cores, interior→exterior from the pour outward: whatever is inboard
# of the concrete is the consuming house's business, and so is whatever protects the foam
# outboard of it. Exported as bare layer tuples so a house can splat one and append its own
# skin without re-typing the pour — ``FOUNDATION_WALL_*_XPS4`` below are the skinless
# assemblies for a house that wants the core as-is.
#
# 2 x 2" rather than one 4" board: staggered joints, and 2" is the stocked thickness.
# Damp-proofing outboard of the pour and inboard of the foam is IRC R406.1's position.
FOUNDATION_WALL_8_XPS4_CORE = (
    Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
          function=LayerFunction.STRUCTURE),
    Layer(name="damp-proof", material_ref="air-barrier", thickness=inch(0.05),
          function=LayerFunction.MEMBRANE,
          control={ControlLayer.AIR, ControlLayer.WATER}),
    Layer(name="xps-a", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    Layer(name="xps-b", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
)

FOUNDATION_WALL_12_XPS4_CORE = (
    Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
          function=LayerFunction.STRUCTURE),
    *FOUNDATION_WALL_8_XPS4_CORE[1:],
)

# 8" + damp-proofing + 4" XPS = 12.05" total, ~R-21.8.
FOUNDATION_WALL_8_XPS4 = Assembly(
    tag="FOUNDATION_WALL_8_XPS4",
    layers=FOUNDATION_WALL_8_XPS4_CORE,
    interfaces=(_CONCRETE_BEARING,),
    source=_R404_SOURCE + "; 8 in. requires #6 at 48 in. o.c. vertical. Exterior "
                          "insulation 2 x 2 in. XPS over damp-proofing per IRC R406.1",
)

# 12" + the same tail = 16.05".
FOUNDATION_WALL_12_XPS4 = Assembly(
    tag="FOUNDATION_WALL_12_XPS4",
    layers=FOUNDATION_WALL_12_XPS4_CORE,
    interfaces=(_CONCRETE_BEARING,),
    source=_R404_SOURCE + "; 12 in. reads NR (no vertical reinforcement required). "
                          "Exterior insulation 2 x 2 in. XPS over damp-proofing per "
                          "IRC R406.1",
)


HOUSE_ROOF = Assembly(
    tag="HOUSE_ROOF",
    layers=(
        Layer(name="rafter", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x12"),
              control={ControlLayer.THERMAL},
              cavity=CavityFill(material_ref="mineral-wool", framing_factor=0.1)),
        Layer(name="deck", material_ref="osb", thickness=inch(0.625),
              function=LayerFunction.SHEATHING),
        Layer(name="membrane", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.06),
              function=LayerFunction.CLADDING),
    ),
    default_lining=(
        _PAINT_FINISH,
        Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
)

# STC-rated interior partition presets (#50).  STC is always a published test result,
# never a value calculated from the layers below.  Preserve each source's framing and
# lining configuration when selecting one; substitutions require a new tested rating.
#
# These deliberately get NO paint layer, and the sentence above is the reason: each is a
# transcription of one published lab test, and its gypsum lives in ``layers`` (the tested
# core) rather than in ``default_lining`` (the finish tier a room may override). Adding a
# layer to a stack whose whole value is that it matches a specific tested build is how the
# cited STC stops describing what is drawn. These walls are painted in reality; the paint is
# a finish-schedule fact about the rooms either side, not part of the rated assembly.
INT_2X4_PARTITION = Assembly(
    tag="INT_2X4_PARTITION",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=36,
    source=("ROCKWOOL, How to Soundproof a Room: 2x4 wood studs at 16 in. o.c., "
            "3.5 in. Comfortbatt, 5/8 in. gypsum both sides, STC 36; "
            "https://www.rockwool.com/north-america/advice-and-inspiration/blog/"
            "using-acoustic-insulation-to-soundproof-a-room/"),
)

INT_2X4_RC = Assembly(
    tag="INT_2X4_RC",
    layers=(
        Layer(name="gwb-resilient", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="resilient-channel", material_ref="resilient-channel", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="25 ga. resilient channel", spacing=inch(24),
                                  direction="horizontal")),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16)),
              cavity=CavityFill(material_ref="fiberglass")),
        Layer(name="gwb-direct", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=48,
    source=("USG/UL U305, USG-US-CA-EN-W-P-1-08: 2x4 wood studs at 16 in. o.c., "
            "3.5 in. fiberglass, 1/2 in. resilient channel at 24 in. o.c., 5/8 in. "
            "gypsum each side, STC 48; "
            "https://assemblies-tools.usg.com/content/usgcom/en_CA_east/design-studio/"
            "wall-assemblies/assembly-detail.30235.html"),
)

INT_2X4_RC_DOUBLE_GWB = Assembly(
    tag="INT_2X4_RC_DOUBLE_GWB",
    layers=(
        Layer(name="gwb-a-outer", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="gwb-a-inner", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="resilient-channel", material_ref="resilient-channel", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="25 ga. resilient channel", spacing=inch(24),
                                  direction="horizontal")),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16)),
              cavity=CavityFill(material_ref="fiberglass")),
        Layer(name="gwb-b-inner", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="gwb-b-outer", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=54,
    source=("USG/UL U301: 2x4 wood studs at 16 in. o.c., 3.5 in. fiberglass, 1/2 in. "
            "resilient channel at 24 in. o.c., two 5/8 in. gypsum layers each side, STC 54; "
            "https://assemblies-tools.usg.com/content/usgcom/en/design-studio/"
            "assemblies/assembly-detail.30269.html"),
)

INT_2X4_STAGGERED_DOUBLE_GWB = Assembly(
    tag="INT_2X4_STAGGERED_DOUBLE_GWB",
    layers=(
        Layer(name="gwb-a-outer", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="gwb-a-inner", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="staggered-studs", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16), plate_member="2x6",
                                  layout=PartitionLayout.STAGGERED,
                                  stagger_gap=inch(1.5)),
              cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
        Layer(name="gwb-b-inner", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="gwb-b-outer", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=52,
    source=("USG/GA WP 5530: 2x4 wood studs staggered on 2x6 plates (16 in. o.c. per "
            "face, 8 in. combined rhythm), "
            "3.5 in. fiberglass, two 5/8 in. gypsum layers each side, STC 52; "
            "https://assemblies-tools.usg.com/content/usgcom/en/design-studio/"
            "assemblies/assembly-detail.30226.html"),
)

INT_2X4_DOUBLE_STUD_MINERAL_WOOL = Assembly(
    tag="INT_2X4_DOUBLE_STUD_MINERAL_WOOL",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.5),
              function=LayerFunction.FINISH),
        Layer(name="double-studs", material_ref="spf", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16),
                                  layout=PartitionLayout.DOUBLE,
                                  stagger_gap=inch(1)),
              cavity=CavityFill(material_ref="mineral-wool", thickness=inch(3.5))),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.5),
              function=LayerFunction.FINISH),
    ),
    stc=52,
    source=("ROCKWOOL Acoustic Wall Assemblies Catalog, IWS-11 / NGC 2010072: 2x4 "
            "wood double-stud wall at 16 in. o.c. with a 1 in. air gap, 3.5 in. "
            "Comfortbatt per row, 1/2 in. gypsum each side, STC 52; "
            "https://www.rockwool.com/syssiteassets/o2-rockwool/documentation/technical-guides/"
            "commercial/acoustic-wall-assemblies-catalog-techincal-guide.pdf"),
)

# --- wet-wall partitions ---------------------------------------------------------
#
# Generic plumbing-chase partitions: 2x6-deep (5.5") so a 3" stack fits the cavity with
# clearance either side of the pipe, gypsum carried in ``layers`` (not a lining) because
# each carries paint face-by-face rather than a shared finish. No STC rating is claimed
# for either — that is what separates them from the STC family above, which transcribes
# a single published lab build end to end. ``INT_2X6_STAGGERED_PLUMBING`` shares its stud
# layout (2x4 studs staggered on 2x6 plates, 16 in. o.c. per face) with
# ``INT_2X4_STAGGERED_DOUBLE_GWB`` above and cites the same USG/GA WP 5530 test for that
# framing geometry, but carries a single layer of gypsum per face rather than a double
# layer, so it does not inherit that assembly's STC 52 rating.
_PAINT_FINISH_A = Layer(name="paint-a", material_ref="latex-paint", thickness=inch(0.01),
                        function=LayerFunction.FINISH,
                        control={ControlLayer.VAPOR})
_PAINT_FINISH_B = Layer(name="paint-b", material_ref="latex-paint", thickness=inch(0.01),
                        function=LayerFunction.FINISH,
                        control={ControlLayer.VAPOR})

INT_2X6_PLUMBING = Assembly(
    tag="INT_2X6_PLUMBING",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="wet wall — 2x6 depth for a 3 in. stack",
)

INT_2X6_STAGGERED_PLUMBING = Assembly(
    tag="INT_2X6_STAGGERED_PLUMBING",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="staggered-studs", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", plate_member="2x6", spacing=inch(16),
                                  layout=PartitionLayout.STAGGERED,
                                  stagger_gap=inch(1.5)),
              cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="wet wall, non-bearing — 2x4 staggered on 2x6 plates per USG/GA WP 5530 "
           "(16 in. o.c. per face, 8 in. combined), 3.5 in. fiberglass sound batt; the "
           "framing geometry is the tested one, the single-layer gypsum face is not, so "
           "no STC is claimed",
)

STARTER_FLOOR = {"subfloor": "plywood-subfloor", "joist": "11.875 I-joist"}

# Assemblies whose R-value / card should render for M1 acceptance.
ALL_ASSEMBLIES: tuple[Assembly, ...] = (
    HOUSE_WALL_2X4_WITH_CI,
    HOUSE_WALL_2X6_WITH_ZIPR,
    GARAGE_ICF,
    FOUNDATION_WALL_8_INT,
    FOUNDATION_WALL_12_INT,
    FOUNDATION_WALL_8_XPS4,
    FOUNDATION_WALL_12_XPS4,
    HOUSE_ROOF,
    INT_2X4_PARTITION,
    INT_2X4_RC,
    INT_2X4_RC_DOUBLE_GWB,
    INT_2X4_STAGGERED_DOUBLE_GWB,
    INT_2X4_DOUBLE_STUD_MINERAL_WOOL,
    INT_2X6_PLUMBING,
    INT_2X6_STAGGERED_PLUMBING,
)
