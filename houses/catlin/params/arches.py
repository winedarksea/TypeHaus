"""Arch layout math for the sunken-garden / porch / balcony structure (WP3.1).

Ported from ``catlin_house.py::_arch_voids_for_wall``: N arches of equal clear width,
fixed outer piers, remaining length split into equal interior piers. Returns offsets
along the wall axis (from the wall's start node) to each arch opening's start edge.
"""

from __future__ import annotations


def arch_offsets_ft(
    *,
    wall_length_ft: float,
    n_arches: int,
    arch_width_ft: float,
    outer_pier_ft: float,
) -> list[float]:
    if n_arches < 1:
        return []
    if wall_length_ft <= 0 or arch_width_ft <= 0:
        raise ValueError("Wall length and arch width must be positive")
    if outer_pier_ft < 0:
        raise ValueError("outer_pier_ft must be >= 0")

    middle = wall_length_ft - 2.0 * outer_pier_ft
    interior_piers = max(n_arches - 1, 0)
    remaining = middle - n_arches * arch_width_ft
    if remaining < -1e-9:
        raise ValueError("Arches + outer piers exceed wall length")
    pier = (remaining / interior_piers) if interior_piers else 0.0

    offsets: list[float] = []
    x = outer_pier_ft
    for i in range(n_arches):
        offsets.append(x)
        x += arch_width_ft
        if i < n_arches - 1:
            x += pier
    return offsets
