"""The Image II eave's leader text: each piece by catalog name and part number, the three
water paths, and every provisional item marked as one.

Anchors come from ``eave_anchors``; a piece the cut misses gets no leader. Part numbers are
read from the library profiles, so a catalog change re-letters the sheet.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.eave_anchors import EaveCut
from typehaus.library.trim import metal_sales
from typehaus.library.trim._image_ii import IMAGE_II_EXTENDED_EAVE
from typehaus.library.trim.profile import TrimProfile

#: The strip-in's width is the resolver's provisional 9" (``roof_image_ii_eave``).
_STRIP_NOTE = "9\" PROVISIONAL (width: GCP)"
#: Where along the pan and the eave leg the water-path leaders land, inches inboard of the
#: cladding face: up the slope from the piece leaders so the two never share a point.
_HANGER_SHORT = "PROVISIONAL gutter hanger: bracket and sealed fastener pending"
_PAN_FIELD_IN = -3.5
_LEG_FIELD_IN = -2.0


def _catalog(profile: TrimProfile) -> str:
    parts = sorted({number for *_rest, number in profile.part_numbers})
    return f"{profile.name} {'/'.join(parts)}"


def _gutter_profile(product: str | None) -> TrimProfile | None:
    profile = getattr(metal_sales, product, None) if product else None
    return profile if isinstance(profile, TrimProfile) else None


def _nearest_out(pieces: EaveCut, points, target_in: float):
    """The top point of ``points`` nearest ``target_in`` out from the face."""
    if not points:
        return None
    best = min(abs(pieces.out(p) - target_in) for p in points)
    close = [p for p in points if abs(pieces.out(p) - target_in) <= best + 0.1]
    return max(close, key=lambda p: p[1])


def eave_piece_labels(pieces: EaveCut, compact: bool = False) -> list:
    """``(anchor, text)`` for every eave piece and water path the cut passes through.

    ``compact`` (a small-scale sheet, where the lip and the face line are each one point)
    names the hook with the pan hem round it and the gutter back with the face over it, and
    hangs water paths 1 and 3 on those two leaders, where each path ends.
    """
    eave = _catalog(IMAGE_II_EXTENDED_EAVE)
    part = IMAGE_II_EXTENDED_EAVE.part_numbers[0][-1]
    gutter = _gutter_profile(pieces.gutter_product)
    gutter_name = _catalog(gutter) if gutter is not None else "box gutter"
    strip = (pieces.strip_in(), f"strip-in over both flanges, {_STRIP_NOTE}")
    flange = (pieces.gutter_flange(), f"{gutter_name}: flange UNDER the eave leg")
    water_1, water_2, water_3 = _water_paths(pieces)
    if compact:
        return [
            (pieces.pan_hem(), f"Image II pan hemmed around the {part} hook (1-1/2\" "
                               f"doubled lip), crimped. {water_1[1]}"),
            strip,
            (pieces.gutter_back(), f"{eave}, 24 ga: face OVER the gutter back. "
                                   f"{water_3[1]}"),
            flange,
            water_2,
        ]
    return [
        (pieces.pan_hem(), "Image II pan hemmed around hook, crimped"),
        (pieces.eave_hook(), f"{part} hook: 1-1/2\" doubled lip"),
        strip,
        (pieces.eave_face(), f"{eave}, 24 ga"),
        flange,
        (pieces.gutter_back(), "gutter back BEHIND the eave face"),
        water_1, water_2, water_3,
    ]


def _water_paths(pieces: EaveCut) -> list:
    return [
        (_nearest_out(pieces, pieces.pan_end, _PAN_FIELD_IN),
         "WATER 1: pan -> lip hem -> trough -> N outlet"),
        (_nearest_out(pieces, pieces.eave, _LEG_FIELD_IN),
         "WATER 2, secondary: membrane -> strip-in -> eave leg -> out at the pan hem "
         "return -> trough"),
        (pieces.wall_head(),
         "WATER 3, wall head: gutter flange + eave leg; face over gutter back"),
    ]


def provisional_hanger(support_labels, compact: bool = False) -> list:
    """The support leaders, the gutter hanger's marked PROVISIONAL.

    ``compact`` shortens the hanger's note to what is open; the enlarged sheet keeps its
    measured fixing.
    """
    out = []
    for target, text in support_labels:
        if "hanger" in text.lower():
            text = (_HANGER_SHORT if compact else text if "provisional" in text.lower()
                    else f"PROVISIONAL {text}")
        out.append((target, text))
    return out
