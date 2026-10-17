"""Framing cut from custom-milled stock, in the milling schedule.

A view, like the rest of ``hardwood``: the member is billed in ``framing`` and these rows say
so (``also_in_framing``). Only a ``FramedMember`` whose material ``requires_custom_milling``
appears — an exposed bay's oak blocking course, say. Ordinary framing is the yard's. A
stair's members are skipped: ``hardwood_stairs.stair_rows`` is the one owner of its millwork.

Pieces are cut to length, so rows group by (use, material, profile, finished length).
"""

from __future__ import annotations

from collections.abc import Mapping

from typehaus.resolve.framing.tables import member_actual
from typehaus.resolve.model import ResolvedModel

_M_TO_IN = 39.37007874
_ALSO = {"also_in_framing": True}
_USE_BY_CATEGORY = {"blocking": "blocking", "plate": "plate"}


def framing_rows(model: ResolvedModel, materials: Mapping[str, object],
                 max_board_width_in: float | None) -> list[dict[str, object]]:
    from typehaus.takeoff.hardwood import _piece_row

    tag_of = {w.uid: w.tag for w in model.walls}
    stair_uids = {stair.uid for stair in model.stairs}
    groups: dict[tuple[str, str, str, float], list[str]] = {}
    for member in model.all_members():
        ref = member.material
        if member.parent_uid in stair_uids:
            continue
        if ref is None or not getattr(materials.get(ref), "requires_custom_milling", False):
            continue
        use = _USE_BY_CATEGORY.get(member.category, member.category)
        key = (use, ref, member.profile,
               round((member.cut_length_m or member.length_m) * _M_TO_IN, 2))
        groups.setdefault(key, []).append(tag_of.get(member.parent_uid, member.parent_uid))
    rows = []
    for (use, ref, profile, length_in), tags in groups.items():
        thickness_in, width_in = member_actual(profile)
        rows.append(_piece_row(use, ref, materials, len(tags), thickness_in, width_in,
                               length_in, max_board_width_in, sorted(set(tags)), _ALSO))
    return rows
