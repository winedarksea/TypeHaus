"""E-604 — grounding electrode and bonding conductor schedules, with the install notes (#123).

Views of ``model.grounding`` (``resolve/grounding.py``): nothing is summed here, and every
length is the resolved one. A straight-line length is an estimate and is marked ``~``.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.paged_tables import PagedTable, wrap_cells
from typehaus.emit.draw.schedules.structural import _write_paged
from typehaus.model.nec import NEC, cite
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

_DASH = "—"
_FT = 12.0 * M_PER_IN
_KIND = {"rod": "driven rod", "concrete_encased": "concrete-encased", "ring": "ground ring"}
_ROLE = {"gec": "GEC", "bonding_jumper": "bonding jumper", "ibt": "IBT",
         "water_bond": "water pipe bond", "counterpoise": "counterpoise",
         "down_lead": "PV down-lead"}


def has_grounding_schedule(model: ResolvedModel) -> bool:
    g = getattr(model, "grounding", None)
    return g is not None and bool(g.electrodes or g.bonds)


def _ft_in(metres: float) -> str:
    inches = round(metres / M_PER_IN)
    return f"{inches // 12}'-{inches % 12}\""


def electrode_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    rows = []
    for el in sorted(model.grounding.electrodes, key=lambda e: e.tag):
        use = "LPS terminal" if el.use == "lps_terminal" else "grounding electrode"
        if el.kind == "concrete_encased":
            bar = f"#{el.bar} {el.coating}" if el.bar else "no qualifying bar"
            length = f"{_ft_in(el.length_m)} bar ({bar})" if el.length_m else bar
            basis = " + ".join(el.footings) or _DASH
            if el.earth_contact == "ahj":
                basis += f"; AHJ: earth contact — {el.earth_reason}"
            elif el.earth_contact == "no":
                basis += f"; NO earth contact — {el.earth_reason}"
            if el.excluded:
                basis += f"; not qualifying: {'; '.join(el.excluded)}"
        else:
            length = _ft_in(el.length_m) if el.length_m else _DASH
            basis = f"top at {el.z_top_m / _FT:.1f}' project elevation"
        rows.append((el.tag, _KIND.get(el.kind, el.kind), use, length, basis))
    return tuple(rows)


def bond_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    rows = []
    for bond in sorted(model.grounding.bonds, key=lambda b: (b.role, b.tag)):
        lf = (_DASH if bond.length_basis == "unlocated"
              else f"{'~' if bond.length_basis == 'straight_line' else ''}"
                   f"{bond.length_m / _FT:.1f}")
        rows.append((bond.tag, _ROLE.get(bond.role, bond.role), bond.from_ref, bond.to_ref,
                     f"#{bond.size}", "Al" if bond.material == "aluminum" else "Cu",
                     "bare" if bond.bare else "insul.", lf))
    return tuple(rows)


def note_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    standard = model.grounding.standard
    spacing = getattr(getattr(standard, "min_rod_spacing", None), "meters", None)
    notes = [
        "THE CONCRETE-ENCASED ELECTRODE MUST BE TIED AND ITS STUB BROUGHT UP BEFORE THE "
        f"FOOTING POUR ({cite(NEC.CONCRETE_ENCASED)}); IT CANNOT BE ADDED AFTERWARD.",
        "ALL GROUNDING ELECTRODES AND SYSTEMS ARE BONDED TOGETHER SOLID "
        f"({cite(NEC.LIGHTNING_BOND)}): NO RESISTORS, DIODES, CAPACITORS OR OTHER DEVICES "
        "BETWEEN GROUNDING SYSTEMS.",
        "ELECTRODE SYSTEM AND RODS: " + cite(NEC.ELECTRODE_SYSTEM, NEC.ROD_INSTALLATION)
        + (f"; RODS AT LEAST {_ft_in(spacing)} APART." if spacing else "."),
        "GEC SIZE AND INSTALLATION, INTERSYSTEM BONDING TERMINATION, WATER PIPE BOND: "
        + cite(NEC.GEC_SIZE, NEC.GEC_INSTALLATION, NEC.INTERSYSTEM_BONDING, NEC.WATER_PIPE_BOND)
        + ".",
        "CONDUCTOR LENGTHS ARE PLAN LENGTHS WITH NO SLACK; ~ MARKS A STRAIGHT-LINE ESTIMATE "
        "BETWEEN ENDPOINTS.",
    ]
    return tuple((f"{i}.", text) for i, text in enumerate(notes, start=1))


def grounding_tables(model: ResolvedModel) -> list[PagedTable]:
    tables = []
    if model.grounding.electrodes:
        tables.append(PagedTable(
            "GROUNDING ELECTRODE SCHEDULE",
            ("Tag", "Kind", "Use", "Length", "Basis"),
            wrap_cells(electrode_rows(model), {3: 28, 4: 56})))
    if model.grounding.bonds:
        tables.append(PagedTable(
            "BONDING CONDUCTOR SCHEDULE",
            ("Tag", "Role", "From", "To", "Size", "Metal", "Cover", "LF"),
            bond_rows(model)))
    tables.append(PagedTable("GROUNDING NOTES", ("No.", "Note"),
                             wrap_cells(note_rows(model), {1: 80})))
    return tables


def write_grounding_schedule(pdf, model: ResolvedModel, number: str, name: str, *,
                             page: int = 0) -> None:
    _write_paged(pdf, model, number, name, grounding_tables(model), page)
