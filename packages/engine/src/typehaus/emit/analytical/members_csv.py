"""One row per analytical member, for the single-member tools a PE actually types into.

ForteWEB, WoodWorks Sizer and Enercalc import nothing. What they need is a table a person
reads across: this member, this section, this material and modulus, this length, these end
conditions, this much load per case. That is this file. Everything in it comes from the
analytical graph, so it cannot disagree with the IFC or the PyNite script.

US units, because that is what those tools take: inches for the section, feet for length
and coordinates, plf for line loads, pounds for point loads, psi for the modulus.

**A node load appears on every member meeting that node.** A column top carrying the storey
shear shows it, and so does the beam landing there — the row answers "what arrives at this
member", which is the single-member question, not "what is the load path total".
"""

from __future__ import annotations

import csv
from pathlib import Path

from typehaus.analytical.graph import AnalyticalModel, Member
from typehaus.analytical.pynite_map import (
    LB_PER_FT_PER_N_PER_M,
    M_TO_IN,
    N_TO_LB,
    PA_TO_PSI,
    section_name,
    section_properties,
    support_label,
)

_FT_PER_M = 1.0 / 0.3048

BASE_COLUMNS = (
    "member_id", "tag", "category", "section", "shape", "width_in", "depth_in",
    "material", "E_psi", "e_basis", "length_ft",
    "n0", "n0_x_ft", "n0_y_ft", "n0_z_ft",
    "n1", "n1_x_ft", "n1_y_ft", "n1_z_ft",
    "release_i", "release_j", "support_i", "support_j", "area_in2", "Iy_in4", "Iz_in4",
    "item_ids",
)


def case_columns(model: AnalyticalModel) -> tuple[str, ...]:
    """Two columns per load case: the vertical line load, and the point load arriving."""
    names = sorted({case.kind.value for case in model.cases})
    return tuple(part for name in names for part in (f"{name}_plf", f"{name}_point_lb"))


def write_members_csv(model: AnalyticalModel, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    cases = sorted({case.kind.value for case in model.cases})
    # newline="" + an explicit lineterminator: csv must own the line endings, or Windows
    # gets \r\r\n and the file stops being byte-comparable across platforms.
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(BASE_COLUMNS + case_columns(model))
        for member in sorted(model.members, key=lambda m: m.id):
            writer.writerow(_row(model, member, cases))
    return path


def _row(model: AnalyticalModel, member: Member, cases: list[str]) -> list[object]:
    n0, n1 = model.node(member.n0), model.node(member.n1)
    area, iy, iz, _ = section_properties(member.section)
    row: list[object] = [
        member.id, member.tag, member.category, section_name(member), member.section.shape,
        _num(member.section.width_m * M_TO_IN), _num(member.section.depth_m * M_TO_IN),
        member.material, _num(member.e_pa * PA_TO_PSI), member.e_basis,
        _num(model.length_m(member) * _FT_PER_M),
        n0.id, *(_num(v * _FT_PER_M) for v in n0.xyz),
        n1.id, *(_num(v * _FT_PER_M) for v in n1.xyz),
        "moment released" if member.releases.i_moment else "continuous",
        "moment released" if member.releases.j_moment else "continuous",
        _support(model, member.n0), _support(model, member.n1),
        _num(area), _num(iy), _num(iz),
        " ".join(member.item_ids),
    ]
    for case in cases:
        row.append(_num(_line_load_plf(model, member, case)))
        row.append(_num(_point_load_lb(model, member, case)))
    return row


def _support(model: AnalyticalModel, node_id: str) -> str:
    """``fixed`` / ``pinned`` / ``pinned+RX``, or blank where the member end bears on nothing."""
    supports = model.supports_at(node_id)
    return support_label(supports[0]) if supports else ""


def _line_load_plf(model: AnalyticalModel, member: Member, case: str) -> float:
    """Vertical (GZ) line load, negative down, averaged over the FULL member length.

    A trapezoid is reported as its mean: a single-member tool takes one number, and the mean
    is the one that reproduces the total load. The PyNite script and the IFC carry the real
    trapezoid — this column is a summary and the header says plf, not "w1/w2".
    """
    total = 0.0
    for load in model.loads_on(member.id):
        if load.case.value == case and load.direction == "GZ":
            total += 0.5 * (load.w0_n_m + load.w1_n_m) * (load.x1 - load.x0)
    return total * LB_PER_FT_PER_N_PER_M


def _point_load_lb(model: AnalyticalModel, member: Member, case: str) -> float:
    """Resultant magnitude of the point loads on the member and at its two end nodes."""
    fx = fy = fz = 0.0
    for load in model.member_point_loads:
        if load.member == member.id and load.case.value == case:
            fx += load.p_n if load.direction == "GX" else 0.0
            fy += load.p_n if load.direction == "GY" else 0.0
            fz += load.p_n if load.direction == "GZ" else 0.0
    for load in model.node_loads:
        if load.node in (member.n0, member.n1) and load.case.value == case:
            fx += load.fx_n
            fy += load.fy_n
            fz += load.fz_n
    return (fx * fx + fy * fy + fz * fz) ** 0.5 * N_TO_LB


def _num(value: float) -> str:
    """Fixed 4 decimals: Excel reads it as a number, and two runs write the same bytes."""
    return f"{value:.4f}"
