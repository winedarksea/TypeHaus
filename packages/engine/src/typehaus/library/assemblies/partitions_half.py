"""1/2" gypsum siblings of the partition presets in ``partitions.py``.

``_HALF`` denotes 1/2-inch gypsum thickness, not wall height.

Same framing, same face names (``gwb-a``/``gwb-b``, ``gwb-resilient``/``gwb-direct``) so a
per-wall ``layer_materials`` swap carries over. ``stc`` is set only from a published test of
the same build with 1/2" board; elsewhere it is None and the source says why.

The source of every number here is NRC IRC-IR-761, Halliwell, Nightingale, Warnock & Birta,
"Gypsum Board Walls: Transmission Loss Data" (1998), doi:10.4224/20331556 — "13 mm" in its
codes is 12.7 mm (1/2") board. It has no Type C rows. Its single-row wood-stud tests are all
insulated: 13 mm board + 90 mm batt, no channel, is STC 33-34 (TL-93-166, TL-93-188), so a
batt alone does not buy a 1/2" wall anywhere near STC 45.
"""

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

_IR761 = "NRC IRC-IR-761 (1998), https://doi.org/10.4224/20331556"
_HALF = inch(0.5)


def _gwb(name: str, material: str = "gwb") -> Layer:
    return Layer(name=name, material_ref=material, thickness=_HALF,
                 function=LayerFunction.FINISH)


_RC = Layer(name="resilient-channel", material_ref="resilient-channel", thickness=inch(0.5),
            function=LayerFunction.FURRING,
            framing=FramingSpec(member="25 ga. resilient channel", spacing=inch(24),
                                direction="horizontal"))

INT_2X4_PARTITION_HALF = Assembly(
    tag="INT_2X4_PARTITION_HALF",
    layers=(
        PAINT_FINISH_A,
        _gwb("gwb-a"),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4")),
        _gwb("gwb-b"),
        PAINT_FINISH_B,
    ),
    source=("2x4 at 16 in. o.c., 1/2 in. gypsum each side, uninsulated. No STC: "
            f"{_IR761} tests no uninsulated 13 mm wood-stud wall, and USG SA924 lists "
            "this build only at 5/8 in."),
)

INT_2X4_RC_HALF = Assembly(
    tag="INT_2X4_RC_HALF",
    layers=(
        _gwb("gwb-resilient"),
        _RC,
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16)),
              cavity=CavityFill(material_ref="fiberglass")),
        _gwb("gwb-direct"),
    ),
    stc=42,
    source=(f"{_IR761} p.155, G13_WS90(406)_GFB90_RC13(610)_G13, test TL-93-128: one "
            "layer 13 mm gypsum each side, 90 mm wood studs 406 o.c., 90 mm glass fibre, "
            "resilient channels 610 o.c. one side - STC 42 (p.154, TL-94-001, channel on "
            "the other face: also 42)"),
)

# Latex is a finish over the cited acoustic build; STC describes the tested gypsum/stud core.
# Type X, not regular board, because Type X is what NRC tested at the target: the same build
# in regular 13 mm board is STC 42-43 (p.269 TL-93-434, p.268 TL-93-228).
INT_2X4_STAGGERED_X_HALF = Assembly(
    tag="INT_2X4_STAGGERED_X_HALF",
    layers=(
        PAINT_FINISH_A,
        _gwb("gwb-a", "gwb-x"),
        Layer(name="staggered-studs", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16), plate_member="2x6",
                                  layout=PartitionLayout.STAGGERED),
              cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
        _gwb("gwb-b", "gwb-x"),
        PAINT_FINISH_B,
    ),
    stc=45,
    source=(f"{_IR761} p.266, G13_SWS140(406)_GFB90_G13, test TL-93-208: one layer 13 mm "
            "Type X gypsum each side, staggered wood studs on 140 mm plates 406 o.c., 90 mm "
            "glass fibre - STC 45 (the lower of two runs; p.267 TL-93-247 is 47)"),
)

# Type C + batt was the reviewers' sound wall. Nothing publishes it at 1/2" on wood; the
# nearest tested build (13 mm Type X + 90 mm batt, TL-93-188) is STC 34, so no number here.
INT_2X4_TYPEC_BATT = Assembly(
    tag="INT_2X4_TYPEC_BATT",
    layers=(
        _gwb("gwb-a", "gwb-c"),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16)),
              cavity=CavityFill(material_ref="fiberglass")),
        _gwb("gwb-b", "gwb-c"),
    ),
    source=("2x4 at 16 in. o.c., 3.5 in. fiberglass, 1/2 in. Type C each side. No STC: no "
            f"1/2 in. Type C wood-stud test found; {_IR761} TL-93-188 (13 mm Type X, 90 mm "
            "mineral fibre) is STC 34 — use INT_2X4_RC (STC 48) where a rating matters"),
)

INT_2X6_PLUMBING_HALF = Assembly(
    tag="INT_2X6_PLUMBING_HALF",
    layers=(
        PAINT_FINISH_A,
        _gwb("gwb-a"),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        _gwb("gwb-b"),
        PAINT_FINISH_B,
    ),
    interfaces=(STUD_BEARING,),
    source="wet wall — 2x6 depth for a 3 in. stack, 1/2 in. gypsum; no STC claimed",
)

INT_2X6_STAGGERED_PLUMBING_HALF = Assembly(
    tag="INT_2X6_STAGGERED_PLUMBING_HALF",
    layers=(
        PAINT_FINISH_A,
        _gwb("gwb-a"),
        Layer(name="staggered-studs", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", plate_member="2x6", spacing=inch(16),
                                  layout=PartitionLayout.STAGGERED),
              cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
        _gwb("gwb-b"),
        PAINT_FINISH_B,
    ),
    interfaces=(STUD_BEARING,),
    source=("wet wall, non-bearing — the regular-board staggered build NRC rates STC 42 "
            f"({_IR761} TL-93-434) plus paint layers the test did not carry, so no STC is "
            "claimed here"),
)

INT_2X6_BRG_HALF = Assembly(
    tag="INT_2X6_BRG_HALF",
    layers=(
        PAINT_FINISH_A,
        _gwb("gwb-a"),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", layout_origin="line")),
        _gwb("gwb-b"),
        PAINT_FINISH_B,
    ),
    interfaces=(STUD_BEARING,),
    source=("interior bearing partition, 2x6 SPF studs (IRC R602.3), 1/2 in. gypsum each "
            f"face; no STC: {_IR761} tests no single-row 140 mm wood stud wall"),
)

INT_2X6_BRG_RC_HALF = Assembly(
    tag="INT_2X6_BRG_RC_HALF",
    variant_of="INT_2X6_BRG_HALF",
    substitute=(
        Substitution(
            span=layers("gwb-a", "stud"),
            replacement=(
                _gwb("gwb-a"),
                _RC,
                Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x6", layout_origin="line"),
                      cavity=CavityFill(material_ref="fiberglass")),
            ),
        ),
    ),
    source="INT_2X6_BRG_HALF with 1/2 in. resilient channel at 24 in. o.c. on face a and "
           "a fiberglass batt; decoupled, but not a tested build, so no STC",
)

INT_2X6_BRG_PLUMBING_HALF = Assembly(
    tag="INT_2X6_BRG_PLUMBING_HALF",
    variant_of="INT_2X6_BRG_HALF",
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
    source="bearing wet wall, 1/2 in. gypsum: continuous 2x6 studs with a 5.5 in. "
           "fiberglass batt; no STC",
)

HALF_PARTITIONS: tuple[Assembly, ...] = (
    INT_2X4_PARTITION_HALF,
    INT_2X4_RC_HALF,
    INT_2X4_STAGGERED_X_HALF,
    INT_2X4_TYPEC_BATT,
    INT_2X6_PLUMBING_HALF,
    INT_2X6_STAGGERED_PLUMBING_HALF,
    INT_2X6_BRG_HALF,
    INT_2X6_BRG_RC_HALF,
    INT_2X6_BRG_PLUMBING_HALF,
)
