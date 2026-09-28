"""The stair half of the milling schedule: treads, winder blanks and landing finishes.

Split out of ``takeoff/hardwood.py``, which assembles it with the stools, shelves and
coverage rows under the same row shape (``_piece_row``).
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from typehaus.model.millwork import MillworkStandard
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardwood import _LAYUP_FIELD, _M_TO_IN, _piece_row


def stair_rows(model: ResolvedModel, materials: Mapping[str, object],
                standard: MillworkStandard | None,
                max_board_width_in: float | None) -> list[dict[str, object]]:
    """Treads and landing finishes for the flights the house says are hardwood.

    Counted off the resolved members, exactly as ``takeoff/stairs.py`` does, so a stair with
    winders schedules the winder blanks it really generated: the rectangle its tapered plan
    shape comes out of, grain along the nosing (``stairs.winder_blank_in``).
    """
    if standard is None:
        return []
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.takeoff.stairs import winder_blank_in

    material_ref = standard.tread_material_ref
    scope = set(standard.tread_stairs) if material_ref is not None else set()
    landing_spec = standard.landing_deck
    landing_scope = set(landing_spec.stair_refs) if landing_spec is not None else set()
    if not scope and not landing_scope:
        return []
    also = {"also_in_stair_treads": True, "also_in_stair_finish": True}
    tread_groups: dict[tuple[object, ...], tuple[int, list[str]]] = {}
    deck_groups: dict[tuple[float, ...], tuple[int, list[str]]] = {}
    landing_rows: list[dict[str, object]] = []
    for stair in model.stairs:
        if stair.tag not in scope and stair.tag not in landing_scope:
            continue
        for member in stair.members:
            if member.category not in ("tread", "winder", "landing"):
                continue
            if member.category != "landing" and stair.tag not in scope:
                continue
            # A walking surface lies FLAT, so its thickness is the narrow face of its
            # section and the board's own width is the wide one, whichever order the
            # profile string happens to name them in ("deck 11x1.5" vs "tapered tread").
            section = cross_section(member.profile)
            thickness_in = min(section.width_m, section.depth_m) * _M_TO_IN
            board_in = max(section.width_m, section.depth_m) * _M_TO_IN
            length_in = member.length_m * _M_TO_IN
            if member.category == "winder":
                board_in, length_in = winder_blank_in(member, stair.nosing_depth_m)
            key = (round(thickness_in, 3), round(board_in, 2), round(length_in, 2))
            if member.category == "landing" and landing_spec is not None \
                    and stair.tag in landing_scope:
                landing_rows.extend(_landing_deck_rows(
                    stair.tag, member.child_key, member.length_m * _M_TO_IN,
                    stair.tread_depth_m / 0.0254,
                    board_face_width_in=landing_spec.board_face_width.inches,
                    board_coverage_width_in=landing_spec.board_coverage_width.inches,
                    field_thickness_in=landing_spec.field_thickness.inches,
                    field_material_ref=landing_spec.field_material_ref,
                    nosing_material_ref=landing_spec.nosing_material_ref,
                    nosing_thickness_in=landing_spec.nosing_thickness.inches,
                    nosing_profile=landing_spec.nosing_profile,
                    landing_width_in=board_in,
                    materials=materials,
                    max_board_width_in=max_board_width_in,
                    also=also))
                continue
            if material_ref is None:
                continue
            if member.category == "landing":
                count, tags = deck_groups.get(key, (0, []))
                deck_groups[key] = (count + 1, tags + [stair.tag])
                continue
            use_key = (f"stair {member.category}", *key)
            count, tags = tread_groups.get(use_key, (0, []))
            tread_groups[use_key] = (count + 1, tags + [stair.tag])
    rows = []
    for (use, thickness, run, width), (count, tags) in tread_groups.items():
        rows.append(_piece_row(use, material_ref, materials, count,
                               thickness, run, width, max_board_width_in, tags, also))
    for (thickness, depth, length), (count, tags) in deck_groups.items():
        # Legacy landing declarations remain an area-like field row. A house that supplies
        # ``landing_deck`` gets its surface decomposed into nosing and board courses below.
        rows.append(_piece_row("stair landing deck", material_ref, materials, count,
                               thickness, depth, length, max_board_width_in, tags, also,
                               layup=_LAYUP_FIELD))
    return rows + landing_rows


def _landing_deck_rows(stair_tag: str, landing_key: str,
                       landing_depth_in: float, nosing_depth_in: float,
                       *, board_face_width_in: float, board_coverage_width_in: float,
                       field_thickness_in: float, field_material_ref: str,
                       nosing_material_ref: str, nosing_thickness_in: float,
                       nosing_profile: str, landing_width_in: float,
                       materials: Mapping[str, object],
                       max_board_width_in: float | None,
                       also: Mapping[str, object]) -> list[dict[str, object]]:
    """Expand one landing surface into its nosing, full courses and optional closing rip.

    The T&G closing course is ordered as a full-width blank; its stock quantity therefore
    remains honest even though the installer rips away most of its face width.
    """
    field_depth_in = landing_depth_in - nosing_depth_in
    if field_depth_in <= 1e-9:
        return []
    full_courses = int(math.floor(field_depth_in / board_coverage_width_in + 1e-9))
    closing_coverage_in = field_depth_in - full_courses * board_coverage_width_in
    rows: list[dict[str, object]] = [_piece_row(
        "stair landing nosing", nosing_material_ref, materials, 1,
        nosing_thickness_in, nosing_depth_in, landing_width_in, max_board_width_in,
        [stair_tag], also, profile=nosing_profile)]
    rows[0]["location"] = landing_key
    if full_courses:
        rows.append(_piece_row(
            "stair landing board", field_material_ref, materials, full_courses,
            field_thickness_in, board_face_width_in, landing_width_in, max_board_width_in,
            [stair_tag], also, profile="T&G"))
        rows[-1]["location"] = landing_key
        rows[-1]["stock_note"] = (
            f'{landing_key}: {full_courses} full courses, '
            f'{full_courses * board_coverage_width_in:.3f}" net coverage')
    if closing_coverage_in > 1e-9:
        tongue_allowance_in = board_face_width_in - board_coverage_width_in
        closing_face_in = closing_coverage_in + tongue_allowance_in
        row = _piece_row(
            "stair landing closing board", field_material_ref, materials, 1,
            field_thickness_in, board_face_width_in, landing_width_in, max_board_width_in,
            [stair_tag], also, profile="T&G")
        row["stock_note"] = (
            f'{landing_key}: order one {board_face_width_in:.2f}" T&G blank; rip to '
            f'{closing_face_in:.2f}" face for {closing_coverage_in:.3f}" coverage')
        row["location"] = landing_key
        rows.append(row)
    return rows
