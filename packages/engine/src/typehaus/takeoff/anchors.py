"""Sill anchorage, wall ties, cross-floor strapping, and authored connector hardware.

Every count here is derived from resolved geometry — sill-plate construction returns, the
framed studs in exterior walls, and the corner junctions that stack across a floor line —
so a house never states a hardware quantity, only its construction.
"""

from __future__ import annotations

import math
from collections import Counter

from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Connector, KneeBrace
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_catalog import (
    ROLE_BRACE_THROUGH_BOLT,
    ROLE_COIL_STRAP,
    ROLE_EMBEDDED_STRAP_HOLDOWN,
    ROLE_KNEE_BRACE,
    ROLE_MUDSILL_ANCHOR,
    ROLE_STUD_PLATE_TIE,
    hardware_by_model,
    hardware_for_role,
    hardware_for_role_and_nominal,
    hardware_row,
)
from typehaus.takeoff.hardware_config import (
    FT_TO_M,
    IN_TO_M,
    HardwareTakeoffConfig,
    KneeBraceRules,
    SillPlateAnchorRules,
    WallTieRules,
)
from typehaus.takeoff.plan_geometry import centerline_endpoints, merge_coincident_points

_M_TO_FT = 3.280839895013123


def _sill_plate_returns(model: ResolvedModel, category: str) -> list:
    return [ret for ret in model.construction_returns if ret.takeoff_category == category]


def mudsill_anchor_rows(model: ResolvedModel, rules: SillPlateAnchorRules,
                        sill_category: str) -> list:
    """MASA anchors along every wood sill plate that lands on concrete/ICF.

    The sill plates are the resolved construction returns, so this follows the model: a
    framed wall stacked on a concrete wall produces a return, and the return produces its
    anchors at the configured pitch (never fewer than the code minimum per plate piece).
    """
    returns = _sill_plate_returns(model, sill_category)
    if not returns:
        return []
    pitch_m = rules.mudsill_anchor_pitch_ft * FT_TO_M
    by_storey: Counter = Counter()
    total_length_m = 0.0
    for ret in returns:
        count = max(rules.minimum_anchors_per_run,
                    int(math.floor(ret.length_m / pitch_m + 1e-9)) + 1)
        by_storey[ret.storey] += count
        total_length_m += ret.length_m
    item = hardware_for_role(ROLE_MUDSILL_ANCHOR)
    return [hardware_row(
        item, scope="sill plate on concrete", count=int(sum(by_storey.values())),
        by_storey=dict(sorted(by_storey.items())), length_ft=total_length_m * _M_TO_FT,
        basis=(f"{rules.mudsill_anchor_pitch_ft:g} ft o.c. (min "
               f"{rules.minimum_anchors_per_run} per plate run) over "
               f"{len(returns)} sill runs totalling {total_length_m * _M_TO_FT:.1f} LF"))]


def strap_holdown_rows(model: ResolvedModel, rules: SillPlateAnchorRules,
                       sill_category: str) -> list:
    """Embedded strap holdowns at the ends of the sill-plate runs.

    Run ends that meet at a corner or a plate butt joint are one location, not two, so the
    endpoints are merged before they are counted.
    """
    returns = _sill_plate_returns(model, sill_category)
    if not returns:
        return []
    endpoints: list = []
    for ret in returns:
        endpoints.extend(centerline_endpoints(list(ret.outline)))
    locations = merge_coincident_points(
        endpoints, rules.coincident_end_tolerance_in * IN_TO_M)
    count = len(locations) * rules.holdowns_per_run_end
    item = hardware_for_role(ROLE_EMBEDDED_STRAP_HOLDOWN)
    return [hardware_row(
        item, scope="sill plate on concrete", count=count,
        basis=(f"{rules.holdowns_per_run_end} per distinct sill-run end; "
               f"{len(returns)} runs share {len(locations)} end locations"))]


def _is_exterior_framed_wall(wall) -> bool:
    """A wall with a weather skin *and* studs: the walls whose uplift path is strapped."""
    return (any(layer.function == "cladding" for layer in wall.layers)
            and any(member.category == "stud" for member in wall.members))


def stud_plate_tie_rows(model: ResolvedModel, rules: WallTieRules) -> list:
    """One stud-to-plate tie per full-height stud in the framed exterior walls, sized to
    the stud it ties (SP4 on a 2x4, SP6 on a 2x6)."""
    by_profile: dict = {}
    for wall in model.walls:
        if not _is_exterior_framed_wall(wall):
            continue
        for member in wall.members:
            if member.category in rules.tied_stud_categories:
                by_profile.setdefault(member.profile, Counter())[wall.storey] += \
                    rules.ties_per_stud

    rows = []
    for profile in sorted(by_profile):
        by_storey = by_profile[profile]
        item = hardware_for_role_and_nominal(ROLE_STUD_PLATE_TIE, profile)
        rows.append(hardware_row(
            item, scope="framed exterior wall", count=int(sum(by_storey.values())),
            size=profile, by_storey=dict(sorted(by_storey.items())),
            basis=(f"{rules.ties_per_stud} per {profile} "
                   f"{'/'.join(sorted(rules.tied_stud_categories))} at the top plate of "
                   f"every framed exterior wall")))
    return rows


def coil_strap_rows(model: ResolvedModel, rules: WallTieRules) -> list:
    """Coiled strapping lapping the floor band at corners where framed walls stack.

    A corner qualifies when every wall meeting there is a framed exterior wall *and* carries
    another wall above it — that is the joint the strap has to make continuous.
    """
    exterior_framed = {wall.tag: wall for wall in model.walls if _is_exterior_framed_wall(wall)}
    stacked_below = {edge.lower_wall for edge in model.stack_edges}
    lap_m = rules.coil_strap_lap_in * IN_TO_M

    straps: list = []
    for junction in model.junctions:
        if junction.kind not in rules.corner_junction_kinds:
            continue
        tags = [incident.wall_tag for incident in junction.incidents]
        if not tags or any(tag not in exterior_framed or tag not in stacked_below
                           for tag in tags):
            continue
        # The strap crosses the floor band: from the top plate of the wall below to the
        # underside of the wall above, plus a lap onto the framing at each end.
        walls = [exterior_framed[tag] for tag in tags]
        band_m = max((wall.z1_m - (wall.plate_top_z_m or wall.z1_m)) for wall in walls)
        straps.append(band_m + 2.0 * lap_m)

    if not straps:
        return []
    total_ft = sum(straps) * _M_TO_FT
    coils = int(math.ceil(total_ft / rules.coil_strap_coil_length_ft))
    item = hardware_for_role(ROLE_COIL_STRAP)
    # Coiled strapping is ordered by the coil, so the purchasable count *is* the coil count;
    # the straps it is cut into stay visible in the basis.
    return [hardware_row(
        item, scope="stacked corner", count=coils, length_ft=total_ft, coils=coils,
        basis=(f"{len(straps)} straps, one per stacked framed-exterior corner: floor band + "
               f"{rules.coil_strap_lap_in:g} in lap each side, up to "
               f"{max(straps) * _M_TO_FT:.2f} ft each; "
               f"{total_ft:.1f} LF cut from {rules.coil_strap_coil_length_ft:g} ft coils"))]


def _authored_connectors(model: ResolvedModel) -> list:
    return [(storey.tag, element)
            for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if isinstance(element, Connector)]


def _authored_knee_braces(model: ResolvedModel) -> list:
    """Every modeled knee brace, however it is authored.

    A brace is a :class:`KneeBrace` — the wood diagonal plus the hardware that fastens it.
    A plan that carries only the older hardware-side record (a ``Connector`` of kind
    ``KNEEBRACE``, with no member) still bills, so the two spellings never split the count.
    """
    return [(storey.tag, element)
            for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if isinstance(element, KneeBrace)
            or (isinstance(element, Connector) and element.kind is ConnectorKind.KNEEBRACE)]


def knee_brace_rows(model: ResolvedModel, rules: KneeBraceRules) -> list:
    """One connector per knee brace the plan models."""
    braces = _authored_knee_braces(model)
    if not braces:
        return []
    by_storey: Counter = Counter()
    for storey, _ in braces:
        by_storey[storey] += rules.braces_per_location
    item = hardware_for_role(ROLE_KNEE_BRACE)
    return [hardware_row(
        item, scope="braced post/beam joint",
        count=len(braces) * rules.braces_per_location,
        by_storey=dict(sorted(by_storey.items())),
        basis=(f"{rules.braces_per_location} per brace x {len(braces)} modeled knee braces "
               f"({', '.join(element.tag for _, element in braces)})"))]


def brace_bolt_rows(model: ResolvedModel, rules: KneeBraceRules) -> list:
    """Through-bolts for the wood diagonals — only the braces that model a member take them.

    A brace authored as bare hardware has no 2x to bolt, so it contributes no bolts: the
    quantity follows the member the model actually carries.
    """
    braces = [(storey, element) for storey, element in _authored_knee_braces(model)
              if isinstance(element, KneeBrace)]
    if not braces:
        return []
    by_storey: Counter = Counter()
    for storey, _ in braces:
        by_storey[storey] += rules.bolts_per_brace
    item = hardware_for_role(ROLE_BRACE_THROUGH_BOLT)
    return [hardware_row(
        item, scope="knee-brace end", count=len(braces) * rules.bolts_per_brace,
        by_storey=dict(sorted(by_storey.items())),
        basis=(f"{rules.bolts_per_brace} per brace (one each end) x {len(braces)} "
               f"modeled {braces[0][1].member} knee braces"))]


def authored_connector_rows(model: ResolvedModel) -> list:
    """The remaining modeled ``Connector`` hardware (post bases, ties, hangers, clamps).

    Knee braces are billed by :func:`knee_brace_rows`, which applies the per-joint pair
    rule, so they are excluded here to avoid double counting.

    A part that mounts on another catalogued part (``StructuralHardware.requires_role``)
    also bills one of *those* per unit — an S-5! CanDuit pipe clamp is a strap, and it is
    the seam clamp under it that reaches the roof. The carrier count is folded into whatever
    line already bills that role, so the BOM keeps one line per part rather than sprouting a
    near-duplicate beside every ring.
    """
    groups: Counter = Counter()
    carried: Counter = Counter()
    for _storey, element in _authored_connectors(model):
        if element.kind is ConnectorKind.KNEEBRACE:
            continue
        groups[(element.kind.value, element.size)] += 1
        item = hardware_by_model(element.size)
        if item is not None and item.requires_role is not None:
            carried[item.requires_role] += 1

    # Fold each carrier onto the line that already bills its part number, so one part stays
    # one line. A role with no modeled connector of its own opens a line here.
    for role, count in carried.items():
        carrier = hardware_for_role(role)
        key = next((k for k in groups if k[1] == carrier.model), (role, carrier.model))
        groups[key] += count

    rows = []
    for (kind, size), count in sorted(groups.items()):
        item = hardware_by_model(size)
        mounted = carried.get(item.role, 0) if item is not None else 0
        modeled = count - mounted
        basis = f"{modeled} modeled {kind.replace('_', ' ')} connector(s) in the plan"
        if mounted:
            basis += f" + {mounted} carrying a pipe clamp"
        rows.append(hardware_row(
            item, scope="modeled connector", count=count, part_number=size, basis=basis))
    return rows


def anchorage_rows(model: ResolvedModel, config: HardwareTakeoffConfig) -> list:
    """All sill/tie/strap/connector lines, in the order they appear on the BOM."""
    return [
        *mudsill_anchor_rows(model, config.sill_plate_anchors,
                             config.sill_plate_takeoff_category),
        *strap_holdown_rows(model, config.sill_plate_anchors,
                            config.sill_plate_takeoff_category),
        *stud_plate_tie_rows(model, config.wall_ties),
        *coil_strap_rows(model, config.wall_ties),
        *knee_brace_rows(model, config.knee_braces),
        *brace_bolt_rows(model, config.knee_braces),
        *authored_connector_rows(model),
    ]
