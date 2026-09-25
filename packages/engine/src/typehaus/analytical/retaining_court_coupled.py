"""Coupled five-wall PyNite shell model for a retaining court (a U of retaining walls).

The analytical layer owns solver orchestration. This model is deliberately unavailable when
site/connection stiffness or balcony reactions are missing. It never substitutes fixed
supports or zero column loads and calls that a pass.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict

from typehaus.analytical.graph import (
    AnalyticalModel,
    Combination,
    LoadCase,
    LoadCaseKind,
    Member,
    Node,
    NodeLoad,
    Plate,
    PlatePressure,
    SupportSpring,
)
from typehaus.analytical.solve import SolveResult, solve
from typehaus.engineering.retaining_court.inputs import CourtDesignInput, PlantingProfile
from typehaus.engineering.retaining_court.loads import pressure_at_height_psf
from typehaus.resolve.framing.profiles import CrossSection

FT_TO_M = 0.3048
IN_TO_M = 0.0254
LB_TO_N = 4.4482216152605
PSF_TO_PA = 47.88025898033584
PCI_TO_N_M3 = 27144790.0
CONCRETE_E_PA = 30.0e9

#: Midpoint strips per plate when averaging the earth-pressure profile over its height.
#: 32 resolves the ordinary-yard knee and the strip-surcharge curvature to well under a
#: percent on any mesh this model is run at, and the cost is one arithmetic loop per plate.
_PRESSURE_SUBDIVISIONS = 32

_PressureAdder = Callable[[str, float, float, float], None]


class _WallOptions(TypedDict):
    height_ft: float
    thickness_in: float
    mesh_ft: float
    pressure: _PressureAdder


@dataclass(frozen=True)
class CoupledAnalysisResult:
    successful: bool
    model: AnalyticalModel | None
    solve_result: SolveResult | None
    equilibrium_error: float | None
    maximum_translation_in: float | None
    unresolved: tuple[str, ...]


class _Mesh:
    def __init__(self) -> None:
        self.nodes: dict[tuple[int, int, int], Node] = {}
        self.plates: list[Plate] = []

    def node(self, x_ft: float, y_ft: float, z_ft: float) -> str:
        key = (round(x_ft * 12000), round(y_ft * 12000), round(z_ft * 12000))
        if key not in self.nodes:
            node_id = f"SGS-{key[0]}-{key[1]}-{key[2]}"
            self.nodes[key] = Node(node_id, x_ft * FT_TO_M, y_ft * FT_TO_M, z_ft * FT_TO_M)
        return self.nodes[key].id

    def wall(self, *, tag: str, axis: str, fixed_ft: float, start_ft: float, end_ft: float,
             height_ft: float, thickness_in: float, mesh_ft: float,
             pressure_multiplier: float, pressure: _PressureAdder) -> None:
        along = _stations(start_ft, end_ft, mesh_ft)
        vertical = _stations(0.0, height_ft, mesh_ft)
        for a0, a1 in zip(along, along[1:], strict=False):
            for z0, z1 in zip(vertical, vertical[1:], strict=False):
                if axis == "y":
                    corners = ((fixed_ft, a0, z0), (fixed_ft, a1, z0),
                               (fixed_ft, a1, z1), (fixed_ft, a0, z1))
                else:
                    corners = ((a0, fixed_ft, z0), (a1, fixed_ft, z0),
                               (a1, fixed_ft, z1), (a0, fixed_ft, z1))
                ids = tuple(self.node(*corner) for corner in corners)
                plate_id = f"{tag}:{len(self.plates):03d}"
                self.plates.append(Plate(
                    id=plate_id, tag=tag, i=ids[0], j=ids[1], m=ids[2], n=ids[3],
                    thickness_m=thickness_in * IN_TO_M, material="concrete",
                    e_pa=CONCRETE_E_PA, poisson=0.2,
                    basis="monolithic formed wall; cracked stiffness sensitivity required",
                ))
                pressure(plate_id, z0, z1, pressure_multiplier)

    def footing(self, *, tag: str, x0_ft: float, x1_ft: float, y0_ft: float, y1_ft: float,
                depth_ft: float, mesh_ft: float) -> None:
        xs = _stations(x0_ft, x1_ft, mesh_ft)
        ys = _stations(y0_ft, y1_ft, mesh_ft)
        for x0, x1 in zip(xs, xs[1:], strict=False):
            for y0, y1 in zip(ys, ys[1:], strict=False):
                ids = (self.node(x0, y0, 0.0), self.node(x1, y0, 0.0),
                       self.node(x1, y1, 0.0), self.node(x0, y1, 0.0))
                self.plates.append(Plate(
                    id=f"{tag}:{len(self.plates):03d}", tag=tag,
                    i=ids[0], j=ids[1], m=ids[2], n=ids[3],
                    thickness_m=depth_ft * FT_TO_M, material="concrete",
                    e_pa=CONCRETE_E_PA, poisson=0.2,
                    basis="monolithic reinforced footing plate",
                ))


def _stations(start: float, end: float, maximum_step: float) -> tuple[float, ...]:
    count = max(1, math.ceil(abs(end - start) / maximum_step))
    return tuple(start + (end - start) * index / count for index in range(count + 1))


def build_coupled_model(design: CourtDesignInput, planting: PlantingProfile, *,
                        mesh_ft: float = 2.0, west_multiplier: float = 1.0,
                        east_multiplier: float = 1.0, include_veneer_tie: bool = True,
                        include_porch_bracing: bool = False) -> AnalyticalModel:
    """Create wall shells, two cross-members, soil springs and four column loads."""

    vertical_pci = design.soil.vertical_support_pci.value
    horizontal_pci = design.soil.horizontal_support_pci.value
    reactions = design.connections.balcony_reactions_lb.value
    missing = []
    if vertical_pci is None:
        missing.append("vertical soil-support modulus")
    if horizontal_pci is None:
        missing.append("horizontal soil-support modulus")
    if reactions is None:
        missing.append("four balcony-column reactions")
    if missing:
        raise ValueError("coupled model requires " + ", ".join(missing))
    # These are validated together above so the solver never sees a partial soil support.
    assert (vertical_pci is not None and horizontal_pci is not None
            and reactions is not None)

    mesh = _Mesh()
    pressures: list[PlatePressure] = []

    def add_pressure(plate_id: str, z0_ft: float, z1_ft: float, multiplier: float) -> None:
        """The plate's **band average**, not a midpoint sample.

        A shell element carries one uniform pressure, so the only question is which single
        number it gets. Sampling the profile at the plate's centre was exact for a linear
        profile and wrong for this one: the earth pressure has a knee where the ordinary
        yard line meets the stem, and the finite-strip surcharge is curved everywhere. Where
        that knee lands inside a coarse element, a midpoint sample can miss the element's
        true mean badly — which is why the 4-ft and 2-ft meshes drifted 22% apart the moment
        the ordinary retained height moved to the model's 5.7865 ft.

        Averaging over the band fixes the mesh-convergence claim at its cause rather than by
        widening the tolerance, and it conserves total thrust for any profile this
        subdivision resolves.
        """
        low, high = sorted((z0_ft, z1_ft))
        span = high - low
        if span <= 0.0:
            value = pressure_at_height_psf(design, planting, low)
        else:
            steps = _PRESSURE_SUBDIVISIONS
            step = span / steps
            value = sum(
                pressure_at_height_psf(design, planting, low + (index + 0.5) * step)
                for index in range(steps)
            ) / steps
        pressures.append(PlatePressure(LoadCaseKind.EARTH, plate_id,
                                       multiplier * value * PSF_TO_PA,
                                       "band-averaged actual profile plus FHWA finite-strip "
                                       "surcharge"))

    width = design.geometry.clear_width_ft + design.geometry.stem_thickness_in / 12.0
    tags = design.geometry.walls
    north, middle, south = -8.0, 0.0, design.geometry.retained_side_length_ft
    height = design.geometry.concrete_stem_height_ft
    common: _WallOptions = {
        "height_ft": height,
        "thickness_in": design.geometry.stem_thickness_in,
        "mesh_ft": mesh_ft,
        "pressure": add_pressure,
    }
    # Opposite wall normals require opposite pressure signs. The south wall's order points
    # its local normal toward the court; the equilibrium test catches any future reversal.
    mesh.wall(tag=tags.left_upper, axis="y", fixed_ft=0.0, start_ft=north, end_ft=middle,
              pressure_multiplier=west_multiplier, **common)
    mesh.wall(tag=tags.left, axis="y", fixed_ft=0.0, start_ft=middle, end_ft=south,
              pressure_multiplier=west_multiplier, **common)
    mesh.wall(tag=tags.right_upper, axis="y", fixed_ft=width, start_ft=middle, end_ft=north,
              pressure_multiplier=east_multiplier, **common)
    mesh.wall(tag=tags.right, axis="y", fixed_ft=width, start_ft=south, end_ft=middle,
              pressure_multiplier=east_multiplier, **common)
    mesh.wall(tag=tags.end, axis="x", fixed_ft=south, start_ft=width, end_ft=0.0,
              pressure_multiplier=1.0, **common)

    stem_half = design.geometry.stem_thickness_in / 24.0
    toe, heel = design.geometry.toe_ft, design.geometry.heel_ft
    end_ext = design.geometry.end_toe_extension_ft
    mesh.footing(tag=f"{tags.left_upper}/{tags.left} footing", x0_ft=-stem_half - heel,
                 x1_ft=stem_half + toe,
                 y0_ft=north, y1_ft=south, depth_ft=design.geometry.footing_depth_ft,
                 mesh_ft=mesh_ft)
    mesh.footing(tag=f"{tags.right_upper}/{tags.right} footing", x0_ft=width - stem_half - toe,
                 x1_ft=width + stem_half + heel, y0_ft=north, y1_ft=south,
                 depth_ft=design.geometry.footing_depth_ft, mesh_ft=mesh_ft)
    mesh.footing(tag=f"{tags.end} footing", x0_ft=-stem_half - heel, x1_ft=width + stem_half + heel,
                 y0_ft=south - stem_half - toe - end_ext, y1_ft=south + stem_half + heel,
                 depth_ft=design.geometry.footing_depth_ft, mesh_ft=mesh_ft)

    beam_section = CrossSection("rect", design.geometry.stem_thickness_in * IN_TO_M,
                                17.75 * IN_TO_M)
    members = [Member(
        id=tags.cross, tag=tags.cross, category="beam",
        n0=mesh.node(0.0, middle, 0.0), n1=mesh.node(width, middle, 0.0),
        section=beam_section, material="concrete", e_pa=CONCRETE_E_PA,
        e_basis="specified 5,000 psi normalweight concrete",
        item_ids=(f"retaining_system/{tags.cross}",),
    )]
    if include_veneer_tie:
        members.append(Member(
            id=tags.tie, tag=tags.tie, category="beam",
            n0=mesh.node(0.0, north, height), n1=mesh.node(width, north, height),
            section=beam_section, material="concrete", e_pa=CONCRETE_E_PA,
            e_basis="specified 5,000 psi normalweight concrete",
        ))

    base_nodes = [node for node in mesh.nodes.values() if abs(node.z_m) < 1e-9]
    footing_area_ft2 = (2.0 * (south - north) * design.geometry.footing_width_ft
                        + (width + 2.0 * (stem_half + heel)) * design.geometry.footing_width_ft
                        - 2.0 * design.geometry.footing_width_ft ** 2
                        # the end toe's extra strip, less its laps onto the two legs
                        + end_ext * (width + 2.0 * (stem_half + heel)
                                     - 2.0 * design.geometry.footing_width_ft))
    tributary_area_m2 = footing_area_ft2 * FT_TO_M ** 2 / len(base_nodes)
    springs: list[SupportSpring] = []
    for node in base_nodes:
        springs.extend((
            SupportSpring(node.id, "DZ", vertical_pci * PCI_TO_N_M3 * tributary_area_m2,
                          "-", design.soil.vertical_support_pci.basis),
            SupportSpring(node.id, "DX", horizontal_pci * PCI_TO_N_M3 * tributary_area_m2,
                          None, design.soil.horizontal_support_pci.basis),
            SupportSpring(node.id, "DY", horizontal_pci * PCI_TO_N_M3 * tributary_area_m2,
                          None, design.soil.horizontal_support_pci.basis),
            SupportSpring(node.id, "RX", 1.0e8, None,
                          "footing rotational support; sensitivity check required"),
            SupportSpring(node.id, "RY", 1.0e8, None,
                          "footing rotational support; sensitivity check required"),
            SupportSpring(node.id, "RZ", 1.0e6, None,
                          "numerical drilling stabilization; exclude from design reactions"),
        ))
    base_ids = {node.id for node in base_nodes}
    for node in mesh.nodes.values():
        if node.id in base_ids:
            continue
        for dof in ("RX", "RY", "RZ"):
            springs.append(SupportSpring(
                node.id, dof, 1.0e-3, None,
                "negligible rotational spring suppresses shell drilling mechanisms",
            ))

    top_locations = ((0.0, north), (width, north), (0.0, middle), (width, middle))
    node_loads = [NodeLoad(LoadCaseKind.DEAD, mesh.node(x, y, height), fz_n=-load * LB_TO_N,
                           source="balcony-column reaction")
                  for (x, y), load in zip(top_locations, reactions, strict=True)]
    wall_length_ft = 2.0 * (south - north) + width
    concrete_weight_lb = (
        wall_length_ft * design.geometry.stem_thickness_in / 12.0 * height
        + footing_area_ft2 * design.geometry.footing_depth_ft
    ) * 150.0
    heel_soil_weight_lb = (wall_length_ft * heel
                           * design.soil.ordinary_retained_height_ft.value
                           * design.soil.unit_weight_pcf.value)
    distributed_weight_n = (concrete_weight_lb + heel_soil_weight_lb) * LB_TO_N / len(base_nodes)
    node_loads.extend(NodeLoad(
        LoadCaseKind.DEAD, node.id, fz_n=-distributed_weight_n,
        source="concrete and actual non-overlapping heel-soil weight proxy",
    ) for node in base_nodes)
    if include_porch_bracing:
        # A declared stiffness is required before this branch can become real. Keeping the
        # flag visible but adding no spring prevents accidental credit to ordinary paving.
        raise ValueError("porch bracing requested without framing/connection stiffness")
    return AnalyticalModel(
        nodes=tuple(mesh.nodes.values()), members=tuple(members), supports=(),
        cases=(LoadCase(LoadCaseKind.DEAD, "balcony reactions and concrete dead-load proxy"),
               LoadCase(LoadCaseKind.EARTH, "actual soil profile and finite-strip surcharge")),
        node_loads=tuple(node_loads), plates=tuple(mesh.plates),
        support_springs=tuple(springs), plate_pressures=tuple(pressures),
        combinations=(Combination("SERVICE", {LoadCaseKind.DEAD: 1.0,
                                                LoadCaseKind.EARTH: 1.0},
                                  "service response; strength combinations are separate"),),
        include_unit_case_combinations=False,
        scope=(f"retaining_system/{tags.cross}", "retaining_court/coupled"),
        assumptions=("wall corners share mesh nodes and are monolithic",
                     "porch framing receives no bracing credit",
                     "vertical foundation contact is compression-only"),
        gaps=("global stability and settlement require geotechnical analysis",
              "GFRP thermal-break connection stiffness is not credited"),
    )


def analyse_coupled(design: CourtDesignInput, planting: PlantingProfile,
                    **kwargs) -> CoupledAnalysisResult:
    """Solve or return an explicit incomplete/unsuccessful result."""

    try:
        model = build_coupled_model(design, planting, **kwargs)
    except ValueError as exc:
        return CoupledAnalysisResult(False, None, None, None, None, (str(exc),))
    result = solve(model)
    if not result.stable:
        return CoupledAnalysisResult(False, model, result, None, None, result.warnings)
    combo = "SERVICE"
    applied = sum(abs(load.fz_n) for load in model.node_loads)
    vertical_reaction = sum(reaction.fz_n for (node, case), reaction in result.reactions.items()
                            if case == combo)
    equilibrium = abs(vertical_reaction - applied) / max(applied, 1.0)
    translation = max(
        math.sqrt(dx * dx + dy * dy + dz * dz)
        for (node, case), (dx, dy, dz) in result.node_displacements_m.items() if case == combo
    ) / IN_TO_M
    successful = equilibrium <= 0.01
    unresolved = () if successful else (f"global vertical equilibrium error {equilibrium:.2%}",)
    return CoupledAnalysisResult(successful, model, result, equilibrium, translation, unresolved)
