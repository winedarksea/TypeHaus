"""Structural screws holding furring/battens through continuous exterior insulation.

Walls and the roof are billed as two separate line items on purpose: they share the same
16 in x 24 in fastener grid, but a roof carries far more exterior foam, so its screws are a
different (longer) part. Both counts are derived from the resolved assembly stack — a wall
type is never named here, so adding a second furred-and-foamed wall type bills itself.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.truss_girts import INNER
from typehaus.resolve.framing.truss_wall import (
    BLOCK_SPACING,
    girt_block_tier,
    truss_kind,
    truss_layer_name,
)
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_catalog import (
    ROLE_EXPOSED_FASTENER_PANEL_SCREW,
    ROLE_EXTERIOR_INSULATION_SCREW,
    hardware_row,
    screw_for_required_length,
)
from typehaus.takeoff.hardware_config import (
    ExposedFastenerCladdingRules,
    ExteriorInsulationFastenerRules,
)

# Float slack when a run divides evenly into its spacing (an 18 ft wall at 16 in o.c.).
_GRID_EPSILON = 1e-9

# Layers a screw passes through without anything of it bearing on them, so they never break
# the contact between a screwed strip/deck and the foam it is held off the framing by.
_MEMBRANE_FUNCTIONS = frozenset({"membrane"})

#: Screws per truss-wall block. Two, so the block cannot rotate about a single fastener —
#: which is the whole reason the block is 3-1/2" wide and slid flush to the OUTRIGGER's face
#: rather than centred on it: the outrigger is on the stud line, so that face is the stud's
#: face too, and both screws land inside the 1-1/2" the block laps the stud by.
TRUSS_BLOCK_SCREWS = 2

#: Screws per catlin-truss block. ONE, and that is a design decision rather than an
#: economy: the block cannot rotate because the girt lying across it is continuous and
#: screwed at every block along its run, so a second screw would be resisting a rotation
#: the course itself already prevents. The two tiers are OFFSET half a bay rather than
#: through-screwed, so every screw here is wood-to-wood with continuous lateral support —
#: girt → block → sheathing → stud, or girt → block → girt — and nothing bears on foam.
GIRT_BLOCK_SCREWS = 1


@dataclass(frozen=True)
class ExteriorInsulationFastening:
    """The screwed-strip condition found in one assembly's layer stack."""

    fastened_layer: str          # the furring/batten layer the screw head bears on
    through_thickness_m: float   # everything the screw passes through before the framing
    insulation_thickness_m: float

    def required_screw_length_in(self, rules: ExteriorInsulationFastenerRules) -> float:
        return (self.through_thickness_m / M_PER_IN) + rules.minimum_structural_embedment_in


def exterior_insulation_fastening(
    layer_stack: list, rules: ExteriorInsulationFastenerRules,
) -> "ExteriorInsulationFastening | None":
    """Find the screwed furring condition in an interior→exterior ``(function, thickness_m,
    name)`` stack, or ``None`` when the assembly has none.

    A strip only takes *structural* screws when continuous insulation holds it off the
    framing; a rainscreen batten straight over sheathing takes ordinary siding nails and is
    deliberately not billed here.
    """
    structure_indices = [index for index, (function, _, _) in enumerate(layer_stack)
                         if function in rules.structure_layer_functions]
    if not structure_indices:
        return None
    structure_index = structure_indices[-1]  # outermost structural layer carries the screw
    outboard = list(enumerate(layer_stack))[structure_index + 1:]
    # A layer is only *the screwed one* when it bears on the foam: a wall's furring and a
    # vented roof's battens sit straight on the insulation, and a nailbase roof's top deck
    # does too. A ventilated mat rolled OVER that top deck does not — the mat is held by the
    # cladding's own clips, and the long screws already stopped at the deck beneath it. So
    # the screwed layer is the outermost candidate whose path back to the outermost
    # insulation crosses nothing but membranes.
    insulation_indices = [index for index, (function, _, _) in outboard
                          if function in rules.insulation_layer_functions]
    if not insulation_indices:
        return None
    insulation_index = insulation_indices[-1]
    fastened_index = next(
        (index for index, (function, _, _) in reversed(outboard)
         if function in rules.fastened_layer_functions and index > insulation_index
         and all(between_function in _MEMBRANE_FUNCTIONS
                 for between_function, _, _ in layer_stack[insulation_index + 1:index])),
        None,
    )
    if fastened_index is None:
        return None
    between = layer_stack[structure_index + 1:fastened_index + 1]
    insulation_m = sum(thickness for function, thickness, _ in between
                       if function in rules.insulation_layer_functions)
    if insulation_m <= 0.0:
        return None
    return ExteriorInsulationFastening(
        fastened_layer=layer_stack[fastened_index][2],
        through_thickness_m=sum(thickness for _, thickness, _ in between),
        insulation_thickness_m=insulation_m,
    )


def fastener_grid_count(run_m: float, rise_m: float, strip_spacing_m: float,
                        pitch_m: float) -> int:
    """Screws on a rectangular field: strips at ``strip_spacing_m`` o.c. across ``run_m``,
    fasteners at ``pitch_m`` along each strip up ``rise_m``. Both ends of both axes are
    fastened, hence the ``+ 1`` on each — a 16 ft wall at 16 in o.c. carries 13 strips."""
    if run_m <= 0.0 or rise_m <= 0.0:
        return 0
    strips = int(math.floor(run_m / strip_spacing_m + _GRID_EPSILON)) + 1
    per_strip = int(math.floor(rise_m / pitch_m + _GRID_EPSILON)) + 1
    return strips * per_strip


def _wall_layer_stack(wall) -> list:
    """Interior→exterior ``(function, thickness_m, name)`` for a resolved wall's real
    depth layers (cavity fill shares its host layer's depth and is not a band)."""
    return [(layer.function, layer.thickness_m, layer.name) for layer in wall.depth_layers()]


def _wall_height_m(wall) -> float:
    """Cladding/furring height: exterior walls span floor-to-floor, and a raked top wall
    averages its two end elevations (the strips run the full raked face)."""
    top = ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2.0
    return top - wall.z0_m


def exterior_insulation_screw_rows(model: ResolvedModel,
                                   rules: ExteriorInsulationFastenerRules) -> list:
    """Wall-furring and roof-batten screw lines, one row per (scope, screw length).

    Openings are not deducted: the strips do stop at a rough opening, but the added jamb,
    head, and sill furring around it takes those fasteners back, so the gross grid is the
    estimate a framer orders against.
    """
    strip_spacing_m = rules.strip_spacing_in * M_PER_IN
    pitch_m = rules.fastener_pitch_along_strip_in * M_PER_IN

    Group = dict
    groups: dict = {}

    def add(scope: str, storey: str, fastening: ExteriorInsulationFastening,
            count: int) -> None:
        if count <= 0:
            return
        required_in = fastening.required_screw_length_in(rules)
        item, length_in, part_number = screw_for_required_length(
            ROLE_EXTERIOR_INSULATION_SCREW, required_in)
        key = (scope, part_number)
        group: Group = groups.setdefault(key, {
            "item": item, "length_in": length_in, "part_number": part_number,
            "count": 0, "by_storey": Counter(), "required_in": required_in,
            "fastening": fastening,
        })
        group["count"] += count
        group["by_storey"][storey] += count
        # The governing (thickest) condition sets the screw length for the whole line.
        if required_in > group["required_in"]:
            group["required_in"], group["fastening"] = required_in, fastening

    for wall in model.walls:
        # A TRUSS WALL has no screwed-strip condition at all, and billing it one is the
        # error this branch exists to stop. Its stack reads sheathing -> foam -> furring
        # exactly as a rigid-CI wall's does, so the walk above happily "finds" a strip
        # standing 5" off the studs and orders an 8" screw for every cell of a 16x24 grid.
        # There is no such screw. The outrigger is lap-screwed to a plywood tab, the tab to
        # a block, and only the BLOCK is fastened back to the framing — through 1-1/2" of
        # wood and the sheathing, with no foam in the path, because the foam is sprayed
        # around the truss afterwards. Those screws are billed off the blocks themselves,
        # below, where their count is the model's and not a grid's.
        if truss_layer_name(model.plan, wall.assembly) is not None:
            continue
        fastening = exterior_insulation_fastening(_wall_layer_stack(wall), rules)
        if fastening is None:
            continue
        run_m = length(sub(wall.axis[1], wall.axis[0]))
        add("exterior wall furring", wall.storey, fastening,
            fastener_grid_count(run_m, _wall_height_m(wall), strip_spacing_m, pitch_m))

    for roof in model.roofs:
        assembly = model.plan.library.resolve_assembly(roof.assembly)
        if assembly is None:
            continue
        stack = [(layer.function.value, layer.thickness.meters, layer.name)
                 for layer in assembly.layers]
        fastening = exterior_insulation_fastening(stack, rules)
        if fastening is None:
            continue
        # A roof plane is billed by grid density: the resolved roof carries its true sloped
        # surface area, but not a per-plane run/rise to walk a grid across.
        cell_m2 = strip_spacing_m * pitch_m
        add("roof top deck", roof.storey, fastening,
            int(math.ceil(roof.surface_area_m2 / cell_m2)))

    rows = [*truss_wall_block_screw_rows(model, rules)]
    for (scope, part_number), group in sorted(groups.items()):
        fastening = group["fastening"]
        rows.append(hardware_row(
            group["item"], scope=scope, count=int(group["count"]), part_number=part_number,
            size=f"{group['length_in']:g} in",
            by_storey=dict(sorted(group["by_storey"].items())),
            basis=(f"{rules.strip_spacing_in:g} in o.c. strips x "
                   f"{rules.fastener_pitch_along_strip_in:g} in o.c. fasteners through "
                   f"{fastening.insulation_thickness_m / M_PER_IN:.2f} in exterior insulation "
                   f"({fastening.through_thickness_m / M_PER_IN:.2f} in total penetration + "
                   f"{rules.minimum_structural_embedment_in:g} in embedment = "
                   f"{group['required_in']:.2f} in required)"),
        ))
    return rows


def truss_wall_block_screw_rows(model: ResolvedModel,
                                rules: ExteriorInsulationFastenerRules) -> list:
    """The structural screws holding a truss wall's blocks back to what carries them.

    Counted off the resolved blocks rather than off a grid, because the blocks ARE the grid.
    A rigid-CI wall's 16 x 24 x one-screw schedule is the wrong shape *and* the wrong count
    for either truss, which is why this does not go through :func:`fastener_grid_count`.

    **Two walls, two stories, and the branch is worth stating.** A Swinburne wall
    (``truss_frame.py``) puts a block every 40" up every outrigger on the 16" stud module and
    takes two screws through block + sheathing into the stud. A catlin-truss wall
    (``truss_girts.py``) puts a block under every girt course at every stud station and takes
    ONE screw per block — but the two tiers land in different things, so they are two rows and
    two lengths: block-1 goes through girt + block + sheathing into the stud (5"), block-2
    through girt + block into the inner girt (4-1/2"). Both round up to the same part.

    Length is derived the same way every other screw here is: everything the screw passes
    through, plus the embedment rule. No foam is in the path in either case — every screw is
    wood-to-wood with continuous lateral support, and the ccSPF is sprayed around it
    afterwards — so both land on ordinary structural screws rather than the 8" ones the
    boards they replaced needed.
    """
    from typehaus.resolve.framing.truss_wall import BLOCK_CATEGORY

    groups: dict = {}
    for wall in model.walls:
        kind = truss_kind(model.plan, wall.assembly)
        if kind is None:
            continue
        sheathing_m = sum(layer.thickness_m for layer in wall.depth_layers()
                          if layer.function == "sheathing")
        for member in wall.members:
            if member.category != BLOCK_CATEGORY:
                continue
            block_m = cross_section(member.profile).width_m
            if kind == "girt":
                tier = girt_block_tier(member.child_key)
                if tier is None:
                    continue
                # The screw's head bears on the GIRT and its point lands in the stud (inner
                # tier) or in the inner girt (outer tier), so what it passes through is the
                # girt, then the block, then — for block-1 only — the sheathing.
                through_in = (block_m + block_m
                              + (sheathing_m if tier == INNER else 0.0)) / M_PER_IN
                scope, screws = f"girt wall block-{tier}", GIRT_BLOCK_SCREWS
            else:
                through_in = (block_m + sheathing_m) / M_PER_IN
                scope, screws = "truss wall blocks", TRUSS_BLOCK_SCREWS
            required_in = through_in + rules.minimum_structural_embedment_in
            item, length_in, part_number = screw_for_required_length(
                ROLE_EXTERIOR_INSULATION_SCREW, required_in)
            group = groups.setdefault((scope, part_number, round(required_in, 3)), {
                "item": item, "length_in": length_in, "part_number": part_number,
                "count": 0, "by_storey": Counter(), "required_in": required_in,
                "through_in": through_in, "scope": scope, "kind": kind, "tier": tier
                if kind == "girt" else None,
            })
            group["count"] += screws
            group["by_storey"][wall.storey] += screws

    return [hardware_row(
        group["item"], scope=group["scope"], count=int(group["count"]),
        part_number=group["part_number"], size=f"{group['length_in']:g} in",
        by_storey=dict(sorted(group["by_storey"].items())),
        basis=_block_screw_basis(group, rules),
    ) for _key, group in sorted(groups.items())]


def _block_screw_basis(group: dict, rules: ExteriorInsulationFastenerRules) -> str:
    """The honest sentence behind one block-screw row: what it goes through, and why that many.

    Two different fastening stories share this function because they share the row shape,
    and an estimator reading either one has to be able to re-derive the count from the
    model without opening it.
    """
    penetration = (f"({group['through_in']:.2f} in through + "
                   f"{rules.minimum_structural_embedment_in:g} in embedment = "
                   f"{group['required_in']:.2f} in required)")
    if group["kind"] != "girt":
        return (f"{TRUSS_BLOCK_SCREWS} per block; one block at each end of every outrigger "
                f"run and the rest spread at max {BLOCK_SPACING.inches:g} in o.c., "
                f"outriggers at {rules.strip_spacing_in:g} in o.c. "
                f"{penetration.replace('in through', 'in through block + sheathing')}")
    lands = ("the stud, through girt + block + sheathing" if group["tier"] == INNER
             else "the inner girt, through girt + block")
    offset = ("on the stud line" if group["tier"] == INNER
              else f"mid-bay, {rules.strip_spacing_in / 2:g} in off the block-1 line")
    return (f"{GIRT_BLOCK_SCREWS} per block into {lands}; one block under every girt course "
            f"at each stud station ({rules.strip_spacing_in:g} in o.c., {offset}) plus one "
            f"at each free course end {penetration}")


def _exposed_fastener_cladding_layer(model: ResolvedModel, wall):
    """The wall's outermost CLADDING layer, if its material is face-fastened.

    The gate is ``Material.exposed_fastener`` and nothing else — not the tag, not the
    finish. A clipped or seamed panel's fixings are already inside its $/SF cladding rate,
    so a wall that does not opt in must bill NOTHING here or the screws are billed twice.
    """
    cladding = [layer for layer in wall.depth_layers() if layer.function == "cladding"]
    if not cladding:
        return None
    outermost = cladding[-1]
    material = model.plan.library.material(outermost.material_ref)
    if material is None or not material.exposed_fastener:
        return None
    return outermost


def exposed_fastener_cladding_screw_rows(model: ResolvedModel,
                                         rules: ExposedFastenerCladdingRules) -> list:
    """Panel screws for face-fastened metal wall cladding, one row per screw length.

    Two terms, because they answer to different geometry:

    *Field* — the panel screwed to its supports. One screw per flat between major ribs at
    every support crossing, which is exactly the rectangular grid
    :func:`fastener_grid_count` walks: rib pitch across the run, support pitch up the rise.

    *Sidelap* — a stitch line down each panel-to-panel joint, at one joint per panel
    coverage width, spaced along its height. The field grid cannot produce these: a sidelap
    is not a support, so no support crossing lands on it.

    Openings are not deducted, following the convention of
    :func:`exterior_insulation_screw_rows`: trim, closures and jamb returns take those
    screws back, so the gross count is what a crew orders against.
    """
    rib_pitch_m = rules.rib_pitch_in * M_PER_IN
    support_pitch_m = rules.support_pitch_in * M_PER_IN
    coverage_m = rules.panel_coverage_in * M_PER_IN
    stitch_pitch_m = rules.sidelap_stitch_pitch_in * M_PER_IN

    required_in = rules.panel_thickness_in + rules.support_embedment_in
    item, length_in, part_number = screw_for_required_length(
        ROLE_EXPOSED_FASTENER_PANEL_SCREW, required_in)

    field_by_storey: Counter = Counter()
    sidelap_by_storey: Counter = Counter()
    for wall in model.walls:
        if _exposed_fastener_cladding_layer(model, wall) is None:
            continue
        run_m = length(sub(wall.axis[1], wall.axis[0]))
        rise_m = _wall_height_m(wall)
        if run_m <= 0.0 or rise_m <= 0.0:
            continue
        field_by_storey[wall.storey] += fastener_grid_count(
            run_m, rise_m, rib_pitch_m, support_pitch_m)
        # Joints, not panels. N panels lap at N-1 joints, and a run exactly one coverage
        # wide has no sidelap at all — billing a stitch line there would put screws down a
        # seam that does not exist. A partial last panel still makes a joint, hence ceil.
        joints = max(0, int(math.ceil(run_m / coverage_m - _GRID_EPSILON)) - 1)
        per_joint = int(math.floor(rise_m / stitch_pitch_m + _GRID_EPSILON)) + 1
        sidelap_by_storey[wall.storey] += joints * per_joint

    embedment = (f"{rules.panel_thickness_in:g} in panel + "
                 f"{rules.support_embedment_in:g} in support embedment = "
                 f"{required_in:.2f} in required")
    rows = []
    for scope, by_storey, basis in (
        ("exposed-fastener panel field", field_by_storey,
         f"{rules.rib_pitch_in:g} in o.c. flats between major ribs x "
         f"{rules.support_pitch_in:g} in o.c. supports, openings not deducted "
         f"({embedment})"),
        ("exposed-fastener panel sidelap", sidelap_by_storey,
         f"one stitch line per {rules.panel_coverage_in:g} in panel coverage at "
         f"{rules.sidelap_stitch_pitch_in:g} in o.c. ({embedment})"),
    ):
        count = sum(by_storey.values())
        if count <= 0:
            continue
        rows.append(hardware_row(
            item, scope=scope, count=int(count), part_number=part_number,
            size=f"{length_in:g} in", by_storey=dict(sorted(by_storey.items())),
            basis=basis,
        ))
    return rows
