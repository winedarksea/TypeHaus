"""The fifth build stage: the walls, as shells on springs.

``scope.py`` terminates its walk at a wall and calls the whole item a gap, "no analytical
representation in v1: surface members are a follow-on". That was true of the *project*
graph and was never true of the machinery: :class:`~typehaus.analytical.graph.Plate`,
:class:`~typehaus.analytical.graph.SupportSpring` and
:class:`~typehaus.analytical.graph.PlatePressure` have existed since the courtyard study,
and ``pynite_map``, ``solve`` and ``pynite_script`` all consume them. What was missing was
a **producer** on the project build path. This is it.

**And it refuses, on catlin.** A wall on springs needs a modulus of subgrade reaction, and
that is a geotechnical measurement: IBC Table 1806.2 publishes an allowable bearing
*pressure* and says nothing about how far the soil moves under it. ``preferences.toml``
``[structural]`` holds the two moduli and their basis, all three unauthored here, so this
stage emits no plate and writes the refusal into the export's own gap register — the same
``BasedValue`` refusal ``engineering/retaining_court/inputs`` applies to the coupled model,
now reaching the project graph. A defaulted spring would be a stiffness nobody chose
driving a deflection somebody reads.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from typehaus.analytical.graph import (
    LoadCaseKind,
    Node,
    Plate,
    PlatePressure,
    SupportSpring,
)

FT_TO_M = 0.3048
IN_TO_M = 0.0254
PSF_TO_PA = 47.88025898033584
#: pci (lb/in³, a pressure per inch of settlement) -> N/m per square metre of contact.
PCI_TO_N_M3 = 27144790.0
#: Normalweight concrete, the value the courtyard shell model already uses.
CONCRETE_E_PA = 30.0e9
CONCRETE_POISSON = 0.2

#: Kinds this stage can mesh. ``retaining_system`` is a SYSTEM-level check over walls that
#: are each their own ``retaining_wall`` item, so meshing it would double the wall.
SHELL_KINDS = frozenset({"retaining_wall"})

#: Midpoint strips per plate when averaging the earth-pressure profile over its height —
#: the band average, not a midpoint sample, for the reason ``retaining_court_coupled`` gives.
_PRESSURE_SUBDIVISIONS = 32
_MESH_FT = 2.0


@dataclass
class ShellSet:
    nodes: list[Node] = field(default_factory=list)
    plates: list[Plate] = field(default_factory=list)
    pressures: list[PlatePressure] = field(default_factory=list)
    springs: list[SupportSpring] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    #: item id -> the plate tag carrying it, so ``build._gaps`` can see it is represented.
    tags_by_item: dict[str, str] = field(default_factory=dict)
    #: Every item this stage has already spoken for — meshed or refused. ``build._gaps``
    #: leaves these alone: two lines about one wall, one of them ("surface members are a
    #: follow-on") now false, is worse than either alone.
    spoken_for: set[str] = field(default_factory=set)


def derive_shells(ctx: Any, scope: Any, mesh_ft: float = _MESH_FT) -> ShellSet:
    """Every in-scope wall as a plate mesh on soil springs, or the refusal in words."""

    shells = ShellSet()
    items = [item for item in scope.item_ids
             if ctx.engineering[item].kind in SHELL_KINDS]
    if not items:
        return shells

    shells.spoken_for.update(items)
    vertical_pci, horizontal_pci, basis = _subgrade(ctx)
    missing = [name for name, value in (("soil_vertical_subgrade_pci", vertical_pci),
                                        ("soil_horizontal_subgrade_pci", horizontal_pci))
               if value is None]
    if not missing and not basis:
        missing.append("soil_subgrade_basis")
    if missing:
        shells.gaps.append(
            f"{len(items)} wall item(s) are not meshed as shells: a wall on springs needs "
            f"a modulus of subgrade reaction, and the house authors no "
            f"{', '.join('structural.' + name for name in missing)} in preferences.toml. "
            f"A presumptive bearing pressure is not a stiffness, so "
            f"nothing is defaulted and no plate, pressure or spring is emitted "
            f"({', '.join(items)})")
        return shells

    for item in items:
        record = ctx.engineering[item]
        for tag in record.element_tags:
            wall = _wall(ctx, tag)
            if wall is None:
                shells.gaps.append(
                    f"{item}: element {tag} resolves to no wall, so it cannot be meshed")
                continue
            _mesh_wall(shells, item, record, wall, mesh_ft, vertical_pci, horizontal_pci,
                       basis)
    if shells.plates:
        shells.assumptions.append(
            "a meshed wall is a monolithic uncracked plate on independent one-way soil "
            "springs: no cracked-section stiffness, no spring coupling, and no passive "
            "resistance on the toe face")
    shells.plates.sort(key=lambda plate: plate.id)
    shells.pressures.sort(key=lambda pressure: (pressure.case.value, pressure.plate))
    shells.springs.sort(key=lambda spring: (spring.node, spring.dof))
    shells.nodes.sort(key=lambda node: node.id)
    return shells


def _subgrade(ctx: Any) -> tuple[float | None, float | None, str]:
    structural = getattr(getattr(ctx, "preferences", None), "structural", None)
    return (getattr(structural, "soil_vertical_subgrade_pci", None),
            getattr(structural, "soil_horizontal_subgrade_pci", None),
            getattr(structural, "soil_subgrade_basis", "") or "")


def _wall(ctx: Any, tag: str) -> Any:
    for wall in getattr(ctx.model, "walls", ()):
        if wall.tag == tag:
            return wall
    return None


def _quantity(record: Any, name: str) -> float | None:
    for quantity in record.inputs:
        if quantity.name == name:
            return float(quantity.value)
    return None


def _mesh_wall(shells: ShellSet, item: str, record: Any, wall: Any, mesh_ft: float,
               vertical_pci: float, horizontal_pci: float, basis: str) -> None:
    """One wall's stem, meshed along its own axis and up its own height."""

    (x0, y0), (x1, y1) = wall.axis
    length_m = math.hypot(x1 - x0, y1 - y0)
    height_ft = _quantity(record, "stem_height")
    thickness_ft = _quantity(record, "stem_thickness")
    efp_pcf = _quantity(record, "active_efp")
    retained_ft = _quantity(record, "retained_height")
    if not (height_ft and thickness_ft and efp_pcf and length_m > 0.0):
        shells.gaps.append(
            f"{item}: the record does not publish the stem height, thickness and earth "
            f"pressure a plate mesh needs, so {wall.tag} is not meshed")
        return

    tag = wall.tag
    along = _stations(0.0, length_m, mesh_ft * FT_TO_M)
    up = _stations(0.0, height_ft * FT_TO_M, mesh_ft * FT_TO_M)
    base_z = wall.z0_m
    ids: dict[tuple[int, int], str] = {}

    def node(index: int, level: int) -> str:
        if (index, level) not in ids:
            fraction = along[index] / length_m if length_m else 0.0
            x = x0 + (x1 - x0) * fraction
            y = y0 + (y1 - y0) * fraction
            node_id = f"{tag}-{index:02d}-{level:02d}"
            ids[(index, level)] = node_id
            shells.nodes.append(Node(node_id, x, y, base_z + up[level]))
        return ids[(index, level)]

    count = 0
    for index in range(len(along) - 1):
        for level in range(len(up) - 1):
            corners = (node(index, level), node(index + 1, level),
                       node(index + 1, level + 1), node(index, level + 1))
            plate_id = f"{tag}:{count:03d}"
            count += 1
            shells.plates.append(Plate(
                id=plate_id, tag=tag, i=corners[0], j=corners[1], m=corners[2],
                n=corners[3], thickness_m=thickness_ft * FT_TO_M, material="concrete",
                e_pa=CONCRETE_E_PA, poisson=CONCRETE_POISSON,
                basis=f"monolithic formed stem graded by {item}; uncracked stiffness"))
            shells.pressures.append(PlatePressure(
                case=LoadCaseKind.EARTH, plate=plate_id,
                pressure_pa=_band_average_psf(
                    efp_pcf, retained_ft or height_ft,
                    up[level] / FT_TO_M, up[level + 1] / FT_TO_M) * PSF_TO_PA,
                source=f"{item} active_efp {efp_pcf:,.0f} psf/ft"))
    shells.tags_by_item[item] = tag

    width_m = (_quantity(record, "footing_width") or thickness_ft) * FT_TO_M
    for index in range(len(along)):
        tributary_m = _tributary_m(along, index) * width_m
        base = node(index, 0)
        shells.springs.append(SupportSpring(
            node=base, dof="DZ", stiffness_n_m=vertical_pci * PCI_TO_N_M3 * tributary_m,
            direction="compression",
            basis=f"{vertical_pci:,.0f} pci vertical subgrade over {tributary_m:.3f} m2 "
                  f"of mat — {basis}"))
        shells.springs.append(SupportSpring(
            node=base, dof="DX", stiffness_n_m=horizontal_pci * PCI_TO_N_M3 * tributary_m,
            direction=None,
            basis=f"{horizontal_pci:,.0f} pci horizontal subgrade over {tributary_m:.3f} "
                  f"m2 of buried face — {basis}"))


def _tributary_m(stations: tuple[float, ...], index: int) -> float:
    left = 0.0 if index == 0 else (stations[index] - stations[index - 1]) / 2.0
    right = (0.0 if index == len(stations) - 1
             else (stations[index + 1] - stations[index]) / 2.0)
    return left + right


def _band_average_psf(efp_pcf: float, retained_ft: float, z0_ft: float,
                      z1_ft: float) -> float:
    """The plate's band average of a triangular active profile, not a midpoint sample."""
    total = 0.0
    for step in range(_PRESSURE_SUBDIVISIONS):
        height = z0_ft + (z1_ft - z0_ft) * (step + 0.5) / _PRESSURE_SUBDIVISIONS
        total += efp_pcf * max(0.0, retained_ft - height)
    return total / _PRESSURE_SUBDIVISIONS


def _stations(start: float, end: float, maximum_step: float) -> tuple[float, ...]:
    count = max(1, math.ceil(abs(end - start) / maximum_step))
    return tuple(start + (end - start) * index / count for index in range(count + 1))
