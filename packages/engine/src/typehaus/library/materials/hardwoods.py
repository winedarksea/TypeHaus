"""Generic solid woods, independent of any house's milling order or stock thickness."""

from typehaus.library.wood_appearance import NATURAL_WOOD_COLORS, WOOD_SPECIES_NAMES
from typehaus.model.materials import Material

MATERIALS = tuple(
    Material(
        tag=f"{species}-board" if species != "oak" else "white-oak-board",
        name=f"{WOOD_SPECIES_NAMES[species]}, solid board, natural clear",
        hatch="lumber", color=color, species=species, finish="solid-board",
        wood_surface="natural-clear",
        source="Visual baseline: lightly aged, minimally amber satin clear; "
        "plans/wood-appearance.md. No stock thickness or engineering properties implied.",
    )
    for species, color in NATURAL_WOOD_COLORS.items()
)
