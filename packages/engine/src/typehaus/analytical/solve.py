"""Solve the analytical graph in PyNite, in process, and hand the answers back in SI.

The oracle end of the analytical lane: a hand-worked note states what a bent does, and this
reproduces it from the same graph the IFC, the DXF and the CSV are written from. If the
solve disagrees with the note, one of the two is wrong and the export is not shippable.

PyNite is an optional dependency (``typehaus[fea]``) and is imported inside ``solve`` — the
``analytical`` package must import on a plain install, because ``emit`` reads its graph.

Results come back in SI, the units the graph is in: newtons, newton-metres. Sign convention
is PyNite's own — a **reaction**, so a downward gravity load gives a positive ``fz_n``, and
a wind push in +X gives a negative ``fx_n`` at the base.
"""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass, field

from typehaus.analytical.graph import AnalyticalModel
from typehaus.analytical.pynite_map import (
    N_TO_LB,
    NM_TO_LB_IN,
    PyniteInputs,
    build_inputs,
)

_MISSING = (
    "PyNite is not installed. The analytical solve is an optional extra: "
    "pip install typehaus[fea]"
)


@dataclass(frozen=True)
class Reaction:
    """A support reaction in SI, in global axes (X, Y, Z with Z up)."""

    fx_n: float = 0.0
    fy_n: float = 0.0
    fz_n: float = 0.0
    mx_nm: float = 0.0
    my_nm: float = 0.0
    mz_nm: float = 0.0


@dataclass(frozen=True)
class MemberExtremes:
    max_abs_moment_nm: float
    max_abs_shear_n: float
    max_axial_n: float          # the largest-magnitude axial, signed as PyNite reports it


@dataclass(frozen=True)
class SolveResult:
    #: ``(node id, combo name)`` → reaction. The combo name is a load case's own name for
    #: the unit per-case combos ``pynite_map`` always writes.
    reactions: dict[tuple[str, str], Reaction]
    member_extremes: dict[tuple[str, str], MemberExtremes]
    stable: bool
    warnings: tuple[str, ...] = ()
    inputs: PyniteInputs | None = field(default=None, repr=False)


def solve(model: AnalyticalModel) -> SolveResult:
    """Build the PyNite model from ``model``'s call list, run a linear solve, convert back."""
    try:
        from Pynite import FEModel3D
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(_MISSING) from exc

    inputs = build_inputs(model)
    fe = _assemble(FEModel3D(), inputs)

    warnings: list[str] = []
    if not inputs.combos:
        return SolveResult({}, {}, stable=False,
                           warnings=("no load cases: nothing to solve",), inputs=inputs)
    # PyNite reports an unstable degree of freedom by PRINTING it and carrying on, and
    # raises only when the matrix is outright singular. Both are answers about the model,
    # not crashes: capture the console so a released beam end nobody restrained arrives in
    # ``warnings`` instead of vanishing into a test runner's swallowed stdout.
    console = io.StringIO()
    try:
        with contextlib.redirect_stdout(console):
            # check_statics writes a table; the caller wants values, not a report.
            fe.analyze_linear(log=False, check_stability=True, check_statics=False, sparse=True)
    except Exception as exc:  # noqa: BLE001 - a singular matrix is a modelling answer
        return SolveResult({}, {}, stable=False,
                           warnings=(f"solve failed: {type(exc).__name__}: {exc}",
                                     *_console_lines(console)),
                           inputs=inputs)
    warnings.extend(_console_lines(console))

    return SolveResult(
        reactions=_reactions(fe, inputs),
        member_extremes=_extremes(fe, inputs),
        stable=True,
        warnings=tuple(warnings),
        inputs=inputs,
    )


def _console_lines(console: io.StringIO) -> tuple[str, ...]:
    return tuple(line.strip() for line in console.getvalue().splitlines() if line.strip())


def _assemble(fe, inputs: PyniteInputs):
    """The one place the call list becomes a model. ``pynite_script.py`` mirrors it exactly."""
    for name, x, y, z in inputs.nodes:
        fe.add_node(name, x, y, z)
    for name, e, g, nu, rho in inputs.materials:
        fe.add_material(name, e, g, nu, rho)
    for name, a, iy, iz, j in inputs.sections:
        fe.add_section(name, a, iy, iz, j)
    for name, i_node, j_node, material, section, rotation in inputs.members:
        fe.add_member(name, i_node, j_node, material, section, rotation=rotation)
    for name, flags in inputs.releases:
        fe.def_releases(name, *flags)
    for node, dx, dy, dz, rx, ry, rz in inputs.supports:
        fe.def_support(node, dx, dy, dz, rx, ry, rz)
    for member, direction, w1, w2, x1, x2, case in inputs.dist_loads:
        fe.add_member_dist_load(member, direction, w1, w2, x1, x2, case=case)
    for member, direction, p, x, case in inputs.pt_loads:
        fe.add_member_pt_load(member, direction, p, x, case=case)
    for node, direction, p, case in inputs.node_loads:
        fe.add_node_load(node, direction, p, case=case)
    for name, factors in inputs.combos:
        fe.add_load_combo(name, dict(factors))
    return fe


def _reactions(fe, inputs: PyniteInputs) -> dict[tuple[str, str], Reaction]:
    out: dict[tuple[str, str], Reaction] = {}
    for node_name, *_ in inputs.supports:
        node = fe.nodes[node_name]
        for combo in inputs.combo_names:
            out[(node_name, combo)] = Reaction(
                fx_n=float(node.RxnFX[combo]) / N_TO_LB,
                fy_n=float(node.RxnFY[combo]) / N_TO_LB,
                fz_n=float(node.RxnFZ[combo]) / N_TO_LB,
                mx_nm=float(node.RxnMX[combo]) / NM_TO_LB_IN,
                my_nm=float(node.RxnMY[combo]) / NM_TO_LB_IN,
                mz_nm=float(node.RxnMZ[combo]) / NM_TO_LB_IN,
            )
    return out


def _extremes(fe, inputs: PyniteInputs) -> dict[tuple[str, str], MemberExtremes]:
    out: dict[tuple[str, str], MemberExtremes] = {}
    for member_name, *_ in inputs.members:
        member = fe.members[member_name]
        for combo in inputs.combo_names:
            moment = max(
                abs(getter(axis, combo))
                for getter in (member.max_moment, member.min_moment)
                for axis in ("My", "Mz")
            )
            shear = max(
                abs(getter(axis, combo))
                for getter in (member.max_shear, member.min_shear)
                for axis in ("Fy", "Fz")
            )
            hi, lo = member.max_axial(combo), member.min_axial(combo)
            out[(member_name, combo)] = MemberExtremes(
                max_abs_moment_nm=float(moment) / NM_TO_LB_IN,
                max_abs_shear_n=float(shear) / N_TO_LB,
                max_axial_n=float(hi if abs(hi) >= abs(lo) else lo) / N_TO_LB,
            )
    return out
