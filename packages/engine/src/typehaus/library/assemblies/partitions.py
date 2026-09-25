"""Interior partitions: the STC family and the wet walls."""

from __future__ import annotations

from typehaus.library.assemblies._layers import (
    PAINT_FINISH_A,
    PAINT_FINISH_B,
    STUD_BEARING,
)
from typehaus.model import (
    Assembly,
    CavityFill,
    FramingSpec,
    Layer,
    LayerFunction,
    PartitionLayout,
    Substitution,
    inch,
    layers,
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
# a finish-schedule fact about the rooms either side, not part of the rated assembly, and
# ``takeoff/derived_paint.py`` bills it on every face that bounds a used room.
# ** THE CAVITY IS EMPTY, AND THAT IS A DELIBERATE OWNER DECISION. **
#
# None of the walls this preset carries is somewhere sound isolation is worth paying for,
# and where it IS worth
# paying for, the answer is `INT_2X4_RC` below — the same studs and the same board with a
# resilient channel, STC 48 on a real published test, twelve points clear of anything a
# batt in this cavity can buy. A batt is the wrong lever; decoupling is the right one.
#
# **WHAT THIS COSTS, STATED PLAINLY, BECAUSE IT IS NOT NOTHING.** In catlin the walls left
# on this preset include three bathroom-to-bedroom partitions (`W-S-SBS` primary bath to
# primary suite, `W-M-BDN1` ensuite to bedroom, `W-A-BATH-S` guest bath to guest bed) and
# `W-M-HS3`, living room to laundry. Those were flagged to the owner and accepted. If any
# of them is ever regretted, the fix is a retype to `INT_2X4_RC`, not a batt put back here.
#
# ** THE R-VALUE THIS ASSEMBLY REPORTS IS OPTIMISTIC AND THE CARD CANNOT SAY SO. ** With no
# `CavityFill`, `analysis._layer_rsi` bills the 3-1/2" STRUCTURE layer as SOLID SPF over
# 100 % of the area, so the card reads R-6.4 for a wall whose honest whole-assembly value
# is nearer R-2.5-3 (an empty vertical cavity is an air space worth about R-1 in total, not
# 3-1/2" of wood). This is the same trap `GARAGE_WALL_2X6` documents in
# `houses/catlin/plan/assemblies.py`, where an unfilled bay read R-14.3 against an honest
# R-7-8. It is harmless HERE only because nothing grades an interior partition's R — the
# `INT` token takes it out of `mn_energy` entirely. Do not quote the card for this one.
#
# ** THE stc IS 34, AND THE SPACING IS WHY IT IS NOT 35 OR 37. ** USG's SA924 catalogue
# publishes this exact 4-3/4" build — 2x4 at 16 OR 24 o.c., one layer of 5/8" FIRECODE
# gypsum each side, no insulation, UL Des U305/U314 — as THREE separate tested numbers,
# and the stud spacing picks which one applies:
#
#   * **STC 34** at **16" o.c.** (test USG-30-FT-G&H)  <- this assembly: FramingSpec
#     defaults to 16" and every catlin wall on this preset frames at 16".
#   * STC 37 at 24" o.c. (test USG-860807) — fewer, more flexible connections between the
#     leaves is worth three points on the same materials.
#   * STC 46 at 24" o.c. with 3" SAFB (test BBN-700725).
#
# **That last pair is the honest measure of what emptying this cavity costs: NINE points,
# not one.** On USG's own 24" rows the batt is worth nine.
# The decision to empty the cavity stands on the argument at the top of this block — that
# decoupling, not absorption, is the right lever, and INT_2X4_RC is where it lives — and
# not on the batt being worth little.
INT_2X4_PARTITION = Assembly(
    tag="INT_2X4_PARTITION",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=34,
    source=("USG SA924 Drywall/Wood Framed Systems: wood stud partition, 2x4 at 16 in. "
            "o.c., one layer 5/8 in. SHEETROCK FIRECODE gypsum each side, uninsulated, "
            "UL Des U305/U314 - STC 34 at 16 in. spacing (test USG-30-FT-G&H); the same "
            "build is STC 37 at 24 in. o.c. and STC 46 at 24 in. o.c. with 3 in. SAFB; "
            "https://www.usg.com/content/dam/USG/pdpmovedocuments/"
            "drywall-wood-framed-systems-SA924.pdf . Cavity intentionally empty "
            "(2026-08-31): where sound isolation matters the house uses INT_2X4_RC "
            "(STC 48), not a batt in this bay."),
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
                                  layout=PartitionLayout.STAGGERED),
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

# Shares INT_2X4_STAGGERED_DOUBLE_GWB's framing geometry — 2x4 studs staggered on 2x6
# plates, 16 in. o.c. per face, same USG/GA WP 5530 test — but carries a single 5/8 in.
# gypsum layer per face rather than a double layer, the same relationship
# INT_2X6_STAGGERED_PLUMBING already has to it below: the framing geometry is the tested
# one, the single-layer gypsum face is not, so no stc= is claimed. Cheaper than dropping
# the cavity fill instead — gwb runs $1.55-2.65/SF installed against fiberglass's
# $0.90-1.75/SF (`prices.toml`), so a whole layer of gypsum is the more expensive half of
# this assembly to cut, not the insulation.
INT_2X4_STAGGERED_GWB = Assembly(
    tag="INT_2X4_STAGGERED_GWB",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="staggered-studs", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16), plate_member="2x6",
                                  layout=PartitionLayout.STAGGERED),
              cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    source=("2x4 studs staggered on 2x6 plates per USG/GA WP 5530 (16 in. o.c. per face, "
            "8 in. combined), 3.5 in. fiberglass, single 5/8 in. gypsum layer each face; "
            "the framing geometry is the tested one, the double-layer gypsum face is not, "
            "so no STC is claimed — a comparable single-layer staggered-stud build is "
            "commonly listed around STC 48, e.g. "
            "https://commercial-acoustics.com/sound-advice/staggered-stud-wall-stc/"),
)

INT_2X4_DOUBLE_STUD_MINERAL_WOOL = Assembly(
    tag="INT_2X4_DOUBLE_STUD_MINERAL_WOOL",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.5),
              function=LayerFunction.FINISH),
        Layer(name="double-studs", material_ref="spf", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16),
                                  layout=PartitionLayout.DOUBLE),
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
INT_2X6_PLUMBING = Assembly(
    tag="INT_2X6_PLUMBING",
    layers=(
        PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        PAINT_FINISH_B,
    ),
    interfaces=(STUD_BEARING,),
    source="wet wall — 2x6 depth for a 3 in. stack",
)

INT_2X6_STAGGERED_PLUMBING = Assembly(
    tag="INT_2X6_STAGGERED_PLUMBING",
    layers=(
        PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="staggered-studs", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", plate_member="2x6", spacing=inch(16),
                                  layout=PartitionLayout.STAGGERED),
              cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        PAINT_FINISH_B,
    ),
    interfaces=(STUD_BEARING,),
    source="wet wall, non-bearing — 2x4 staggered on 2x6 plates per USG/GA WP 5530 "
           "(16 in. o.c. per face, 8 in. combined), 3.5 in. fiberglass sound batt; the "
           "framing geometry is the tested one, the single-layer gypsum face is not, so "
           "no STC is claimed",
)


# --- bearing and deeper wet walls ---------------------------------------------------------
#
# The 2x6 bearing partition and its variants, and the wet-wall family grown past a 2x6. None
# claims an STC rating: none is a tested build.
INT_2X6_BRG = Assembly(
    tag="INT_2X6_BRG",
    layers=(
        PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", layout_origin="line")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        PAINT_FINISH_B,
    ),
    interfaces=(STUD_BEARING,),
    source="interior bearing partition, 2x6 SPF studs (IRC R602.3), 5/8 in. gypsum each face",
)

INT_2X6_BRG_RC = Assembly(
    tag="INT_2X6_BRG_RC",
    variant_of="INT_2X6_BRG",
    substitute=(
        Substitution(
            span=layers("gwb-a", "stud"),
            replacement=(
                Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
                      function=LayerFunction.FINISH),
                Layer(name="resilient-channel", material_ref="resilient-channel",
                      thickness=inch(0.5), function=LayerFunction.FURRING,
                      framing=FramingSpec(member="25 ga. resilient channel",
                                          spacing=inch(24), direction="horizontal")),
                Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x6", layout_origin="line"),
                      cavity=CavityFill(material_ref="fiberglass")),
            ),
        ),
    ),
    source="INT_2X6_BRG with 1/2 in. resilient channel at 24 in. o.c. on face a and a "
           "fiberglass batt in the bay; decoupled, but not a tested build, so no STC",
)

INT_2X6_BRG_PLUMBING = Assembly(
    tag="INT_2X6_BRG_PLUMBING",
    variant_of="INT_2X6_BRG",
    substitute=(
        Substitution(
            span=layers("stud", "stud"),
            replacement=(
                Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x6"),
                      cavity=CavityFill(material_ref="fiberglass", thickness=inch(5.5))),
            ),
        ),
    ),
    source="bearing wet wall: continuous 2x6 studs (a staggered bearing wall fails "
           "structural.wet_wall_bearing) with a 5.5 in. fiberglass batt",
)

INT_2X6_PLUMBING_BATT = Assembly(
    tag="INT_2X6_PLUMBING_BATT",
    variant_of="INT_2X6_PLUMBING",
    substitute=(
        Substitution(
            span=layers("stud", "stud"),
            replacement=(
                Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x6"),
                      cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
            ),
        ),
    ),
    source="INT_2X6_PLUMBING with the 3.5 in. fiberglass sound batt "
           "INT_2X6_STAGGERED_PLUMBING carries",
)

INT_2X8_PLUMBING = Assembly(
    tag="INT_2X8_PLUMBING",
    variant_of="INT_2X6_PLUMBING",
    substitute=(
        Substitution(
            span=layers("stud", "stud"),
            replacement=(
                Layer(name="stud", material_ref="spf", thickness=inch(7.25),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x8")),
            ),
        ),
    ),
    source="wet wall at 2x8 depth: a 3 in. drain (3.500 in. OD) clears IRC R602.6's 60% of "
           "7.25 in. = 4.35 in., which a 2x6's 3.30 in. does not",
)

INT_ESS_CLOSET_STEEL = Assembly(
    tag="INT_ESS_CLOSET_STEEL",
    layers=(
        PAINT_FINISH_A,
        Layer(name="gwb-x-a", material_ref="gwb-x", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="steel-stud", material_ref="steel-stud", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16))),
        Layer(name="gwb-x-b", material_ref="gwb-x", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        PAINT_FINISH_B,
    ),
    source="non-combustible enclosure for a battery (ESS) room, NFPA 855 / IRC R328 intent: "
           "25 ga. steel C-stud at 16 in. o.c., 5/8 in. Type X both faces. Not a rated "
           "assembly and not claimed as one — no tested assembly number is cited",
)

INT_ESS_CLOSET_STEEL_6 = Assembly(
    tag="INT_ESS_CLOSET_STEEL_6",
    variant_of="INT_ESS_CLOSET_STEEL",
    substitute=(
        Substitution(
            span=layers("steel-stud", "steel-stud"),
            replacement=(
                Layer(name="steel-stud", material_ref="steel-stud", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x6", spacing=inch(16))),
            ),
        ),
    ),
    source="INT_ESS_CLOSET_STEEL on a 6 in. 25 ga. steel C-stud, for a pipe the 3-5/8 in. "
           "web cannot pass",
)
