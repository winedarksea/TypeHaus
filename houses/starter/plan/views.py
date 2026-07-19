"""Starter authored detail slices — A-401+ (→ Permit-ready plan set Phase 6)."""

from typehaus import Slice, SliceKind, ft, pt

DETAIL_SLICES = [
    # Typical exterior wall section — south wall, main + upper storeys, full height.
    Slice(uid="SVD901AAAA", tag="SL-D-WALLTYP", kind=SliceKind.DETAIL,
         title="Typical exterior wall section",
         cut_origin=pt(ft(12), ft(0)), cut_direction="y",
         crop=(pt(ft(-1), ft(-6)), pt(ft(8), ft(20)))),
]
