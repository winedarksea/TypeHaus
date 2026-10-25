"""ADVISORY — spacing between electrical devices on opposite faces of acoustic walls."""

from __future__ import annotations

from collections import defaultdict

from typehaus.checks._authoring import not_applicable, passed, unknown
from typehaus.checks.advisory.acoustics import acoustic_wall_tags
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._stud_grid import module_origin, structure_framing
from typehaus.findings import Finding, Result, advisory
from typehaus.model.enums import DeviceKind, PartitionLayout
from typehaus.resolve.framing.tables import DEFAULT_SPACING

CHECK_ID = "advisory.acoustic_box_spacing"
_IN_M = 0.0254
_SUPPORTED_KINDS = frozenset({DeviceKind.RECEPTACLE, DeviceKind.RECEPTACLE_GFCI,
                              DeviceKind.RECEPTACLE_240, DeviceKind.SWITCH})


@check(Tier.ADVISORY, CHECK_ID)
def acoustic_box_spacing(ctx: CheckContext) -> list[Finding]:
    """Flag opposing receptacles/switches less than one stud module apart."""
    walls = {wall.tag: wall for wall in ctx.model.walls}
    selected = acoustic_wall_tags(ctx)
    devices_by_wall: dict[str, list[tuple[object, str, float]]] = defaultdict(list)
    unevaluable_walls: set[str] = set()
    for device in ctx.plan.all_elements():
        if getattr(device, "element_kind", None) != "ElectricalDevice":
            continue
        if getattr(device, "kind", None) not in _SUPPORTED_KINDS:
            continue
        location = getattr(device, "location", None)
        attachment = getattr(location, "attachment", None)
        if attachment is None:
            # Legacy wall_ref identifies the wall but lacks the face/station needed here.
            legacy_wall = getattr(device, "wall_ref", None)
            if legacy_wall in selected:
                unevaluable_walls.add(legacy_wall)
            continue
        wall_tag = attachment.wall_ref
        if wall_tag not in selected:
            continue
        if attachment.face not in {"left", "right"}:
            unevaluable_walls.add(wall_tag)
            continue
        devices_by_wall[wall_tag].append((device, attachment.face,
                                          attachment.distance_from_start.meters))

    out: list[Finding] = []
    for wall_tag, devices in sorted(devices_by_wall.items()):
        left = [entry for entry in devices if entry[1] == "left"]
        right = [entry for entry in devices if entry[1] == "right"]
        if not left or not right:
            continue
        wall = walls.get(wall_tag)
        assembly = ctx.plan.library.resolve_assembly(wall.assembly) if wall else None
        framing = structure_framing(assembly)
        if wall is None or framing is None:
            unevaluable_walls.add(wall_tag)
            continue
        spacing_m = (framing.spacing.meters if framing.spacing is not None
                     else DEFAULT_SPACING.meters)
        if spacing_m <= 0:
            unevaluable_walls.add(wall_tag)
            continue
        phase_m, _ = module_origin(ctx, wall, framing, spacing_m)
        staggered_or_double = framing.layout in {PartitionLayout.STAGGERED,
                                                  PartitionLayout.DOUBLE}
        for first, _, first_station in left:
            for second, _, second_station in right:
                offset_m = abs(first_station - second_station)
                first_bay = int((first_station - phase_m) // spacing_m)
                second_bay = int((second_station - phase_m) // spacing_m)
                if offset_m + 1e-9 >= spacing_m and (staggered_or_double or
                                                      first_bay != second_bay):
                    out.append(passed(
                        CHECK_ID,
                        f"{wall_tag}: {first.tag} and {second.tag} on opposite faces are "
                        f"{offset_m / _IN_M:.1f} in. apart, meeting the {spacing_m / _IN_M:.1f} "
                        "in. spacing recommendation",
                        (wall_tag, first.tag, second.tag),
                    ))
                    continue
                inches = offset_m / _IN_M
                required_inches = spacing_m / _IN_M
                note = (" Offset alone does not establish cavity isolation for this "
                        "staggered/double wall." if staggered_or_double else "")
                out.append(advisory(
                    CHECK_ID,
                    f"{wall_tag}: {first.tag} and {second.tag} on opposite faces are "
                    f"{inches:.1f} in. apart; recommend at least {required_inches:.1f} in. "
                    f"and different stud bays.{note}",
                    (wall_tag, first.tag, second.tag), Result.FAIL,
                    fix=("Relocate one device to another bay. Seal box penetrations and "
                         "follow the tested wall assembly's treatment requirements where "
                         "relocation is impractical."),
                ))
    for wall_tag in sorted(unevaluable_walls):
        out.append(unknown(CHECK_ID,
                           f"{wall_tag}: cannot evaluate acoustic device spacing without "
                           "resolved wall framing and explicit device faces",
                           (wall_tag,)))
    if not out:
        return [not_applicable(CHECK_ID,
                               "no opposing receptacle or switch pair occurs on a selected "
                               "acoustic wall")]
    return out
