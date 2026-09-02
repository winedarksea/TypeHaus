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
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_catalog import (
    ROLE_BRACE_THROUGH_BOLT,
    ROLE_COIL_STRAP,
    ROLE_EMBEDDED_STRAP_HOLDOWN,
    ROLE_KNEE_BRACE,
    ROLE_LAPPED_BRACE_BOLT,
    ROLE_MUDSILL_ANCHOR,
    ROLE_STUD_PLATE_TIE,
    hardware_by_model,
    hardware_for_role,
    hardware_for_role_and_nominal,
    hardware_row,
)
from typehaus.takeoff.hardware_config import (
    FT_TO_M,
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


def sill_gasket_rows(model: ResolvedModel) -> list[dict[str, object]]:
    """The sill seal under every bearing plate, by the lineal foot, one row per product.

    Read off the same construction returns ``mudsill_anchor_rows`` counts anchors on, so the
    gasket follows the plate exactly: the resolver picked the product from the wall (plain
    closed-cell foam where the plate joint is only a capillary/air break, peel-and-stick
    where it is the air barrier crossing onto the foundation) and stated the compressed
    thickness; this only sums the runs.

    Deliberately its own table rather than a second row inside
    ``construction_returns_takeoff``: that function reconciles 1:1 with
    ``model.construction_returns`` (``test_construction_rules``) and a gasket row alongside
    the plate row would break the invariant the section/3D/IFC render against.
    """
    runs: dict[tuple[str, float], list[float]] = {}
    for ret in model.construction_returns:
        if ret.gasket_product is None:
            continue
        key = (ret.gasket_product, round((ret.gasket_thickness_m or 0.0) / M_PER_IN, 4))
        runs.setdefault(key, []).append(ret.length_m)
    return [
        {"product": product, "thickness_in": thickness_in, "count": len(lengths),
         "length_ft": round(sum(lengths) * _M_TO_FT, 1)}
        for (product, thickness_in), lengths in sorted(runs.items())
    ]


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
        endpoints, rules.coincident_end_tolerance_in * M_PER_IN)
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


def _band_strap_m(wall, lap_m: float) -> float:
    """One strap: across the floor band, plus a lap onto the framing at each end."""
    return (wall.z1_m - (wall.plate_top_z_m or wall.z1_m)) + 2.0 * lap_m


def coil_strap_rows(model: ResolvedModel, rules: WallTieRules) -> list:
    """Coiled strapping carrying tension across the floor band where framed walls stack.

    Two terms, because a corner and a wall run are different conditions:

    * a **corner** where every wall meeting there is a framed exterior wall carrying another
      wall above it — the four-stud packs, which is where the two facades hand off to each
      other and where the strap has the most to do;
    * the **run between** those corners, strapped at ``wall_strap_pitch_ft``.

    The run term matters: corners alone leave the middle of a long facade strapped only by
    nails through a rim board, where uplift is largest on a low-slope roof. The pitch
    matches the mudsill anchors and LTP4 tie plates so the three read as one rhythm.
    """
    exterior_framed = {wall.tag: wall for wall in model.walls if _is_exterior_framed_wall(wall)}
    stacked_below = {edge.lower_wall for edge in model.stack_edges}
    lap_m = rules.coil_strap_lap_in * M_PER_IN

    straps: list = []
    corners = 0
    for junction in model.junctions:
        if junction.kind not in rules.corner_junction_kinds:
            continue
        tags = [incident.wall_tag for incident in junction.incidents]
        if not tags or any(tag not in exterior_framed or tag not in stacked_below
                           for tag in tags):
            continue
        walls = [exterior_framed[tag] for tag in tags]
        straps.append(max(_band_strap_m(wall, lap_m) for wall in walls))
        corners += 1

    # The run between the corners. Counted per wall rather than per junction, and the corner
    # straps above are NOT subtracted: a wall's own end is where its neighbour's corner strap
    # lands, which laps the return face, not this one.
    runs = 0
    pitch_m = rules.wall_strap_pitch_ft * FT_TO_M
    for tag, wall in sorted(exterior_framed.items()):
        if tag not in stacked_below:
            continue
        (x0, y0), (x1, y1) = wall.axis
        length_m = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        count = max(rules.minimum_straps_per_wall, int(length_m / pitch_m))
        straps.extend([_band_strap_m(wall, lap_m)] * count)
        runs += count

    if not straps:
        return []
    total_ft = sum(straps) * _M_TO_FT
    coils = int(math.ceil(total_ft / rules.coil_strap_coil_length_ft))
    item = hardware_for_role(ROLE_COIL_STRAP)
    # Coiled strapping is ordered by the coil, so the purchasable count *is* the coil count;
    # the straps it is cut into stay visible in the basis.
    return [hardware_row(
        item, scope="stacked wall", count=coils, length_ft=total_ft, coils=coils,
        basis=(f"{len(straps)} straps across the floor band: {corners} at stacked "
               f"framed-exterior corners and {runs} along the runs between them at "
               f"{rules.wall_strap_pitch_ft:g} ft o.c. (min "
               f"{rules.minimum_straps_per_wall} per wall); floor band + "
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

    **Two rows, because a lapped foot takes a different bolt.** A brace that butts its post
    is bolted at each end through the strap and the 2x — 6 in reaches. A brace with
    ``KneeBrace.foot_lap`` lies flat on the post face and is bolted through the brace and the
    whole post behind it, so its bolts cross 7 in of wood and both of them land at that one
    end (the head is strapped, not bolted). Same count per brace; different part, and the
    part is the thing an order gets wrong.
    """
    braces = [(storey, element) for storey, element in _authored_knee_braces(model)
              if isinstance(element, KneeBrace)]
    if not braces:
        return []
    groups = {
        (ROLE_BRACE_THROUGH_BOLT, "knee-brace end", "one each end"):
            [b for b in braces if b[1].foot_lap is None],
        (ROLE_LAPPED_BRACE_BOLT, "lapped knee-brace foot", "both at the lapped foot"):
            [b for b in braces if b[1].foot_lap is not None],
    }
    rows = []
    for (role, scope, where), group in groups.items():
        if not group:
            continue
        by_storey: Counter = Counter()
        for storey, _ in group:
            by_storey[storey] += rules.bolts_per_brace
        rows.append(hardware_row(
            hardware_for_role(role), scope=scope,
            count=len(group) * rules.bolts_per_brace,
            by_storey=dict(sorted(by_storey.items())),
            basis=(f"{rules.bolts_per_brace} per brace ({where}) x {len(group)} "
                   f"modeled {group[0][1].member} knee braces")))
    return rows


def authored_connector_rows(model: ResolvedModel) -> list:
    """The remaining modeled ``Connector`` hardware (post bases, ties, hangers, clamps).

    Knee braces are billed by :func:`knee_brace_rows`, which applies the per-joint pair
    rule, so they are excluded here to avoid double counting.

    A part that mounts on another catalogued part (``StructuralHardware.requires_role``)
    also bills one of *those* per unit — an S-5! CanDuit pipe clamp is a strap, and it is
    the seam clamp under it that reaches the roof. That carrier gets its **own row**, same
    part number as any directly modeled clamp of that kind but a different ``scope``, rather
    than being folded into the modeled row's count: the two came from different rules (one
    is authored directly, one is implied by a ring mounted somewhere), and merging their
    counts would erase which is which the moment someone asks why the number is 13. In the
    3D view a ring and the clamp under it stay a single modeled ``Connector`` — this split
    is a BOM-only distinction, not a second solid.
    """
    groups: Counter = Counter()
    carried: Counter = Counter()
    for _storey, element in _authored_connectors(model):
        if element.kind is ConnectorKind.KNEEBRACE:
            continue
        groups[(element.kind.value, element.size)] += 1
        item = hardware_by_model(element.size)
        if item is not None and item.requires_role is not None:
            # Keyed by (carrier role, requiring part) so the basis text can name what asked
            # for the carrier. Two different parts riding the same clamp — a CanDuit ring and
            # a ColorGard rail — must not collapse into one row reading "to mount a pipe
            # clamp": the count would be right and the reason would be a lie.
            carried[(item.requires_role, item.name)] += 1

    rows = []
    for (kind, size), count in sorted(groups.items()):
        item = hardware_by_model(size)
        rows.append(hardware_row(
            item, scope="modeled connector", count=count, part_number=size,
            basis=f"{count} modeled {kind.replace('_', ' ')} connector(s) in the plan"))

    # Carriers required by a pipe clamp but not otherwise modeled: their own row, keyed by
    # the *carrier's* published model so it prices and orders as the same part number.
    for (role, requiring), count in sorted(carried.items()):
        carrier = hardware_for_role(role)
        rows.append(hardware_row(
            carrier, scope="carried-mount", count=count, part_number=carrier.model,
            basis=f"{count} required to mount a modeled {requiring}"))
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
