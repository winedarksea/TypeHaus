"""Catlin plant catalog — illustrative, counted, never priced (like fixture_types.py).

Mature sizes are the published ones where a source is named; the rest are typical and
marked so. The owner swaps entries here; a swap moves no geometry but a plant's spread.
Foliage materials carry the render colour (``Material.color``) the 3D plants take.
"""

from __future__ import annotations

from typehaus import Material, PlantType, ft, inch

_TYPICAL = "typical nursery size; confirm with the supplier"


def _foliage(tag: str, name: str, color: str) -> Material:
    return Material(tag=tag, name=name, color=color,
                    source="illustrative foliage colour for the 3D planting")


FOLIAGE_MATERIALS = (
    _foliage("foliage-bluestem", "Little bluestem foliage, blue-green", "#7d9a8c"),
    _foliage("foliage-moonbeam", "Coreopsis foliage with pale-yellow bloom", "#c9c96a"),
    _foliage("foliage-chartreuse", "Sedum 'Angelina' foliage, chartreuse", "#b8c93c"),
    _foliage("foliage-caramel", "Heuchera 'Caramel' foliage, apricot", "#c2804a"),
    _foliage("foliage-sedge", "Sedge foliage, mid green", "#6a8a4c"),
    _foliage("foliage-iris", "Blue flag iris foliage, grey-green", "#6f8f78"),
    _foliage("foliage-milkweed", "Swamp milkweed, dark green with pink bloom", "#6d7f4a"),
    _foliage("foliage-perennial", "Mixed perennial foliage", "#6f8c4a"),
    _foliage("foliage-apple", "Apple foliage, deep green", "#4f7a3a"),
)

PLANT_TYPES = (
    # --- the grid field and its accents (params/landscape_gardens.py) ----------------------
    PlantType(tag="PT-SCH-JAZZ", botanical_name="Schizachyrium scoparium", cultivar="Jazz",
              common_name="little bluestem", form="grass", mature_height=inch(30),
              mature_spread=inch(18), foliage_material="foliage-bluestem",
              bloom="blue-green summer, burgundy-bronze autumn",
              source=("https://www.missouribotanicalgarden.org/PlantFinder/"
                      "PlantFinderDetails.aspx?taxonid=299967&isprofile=0&pt=11 "
                      "(24-30 in x 12-18 in, upright, does not flop)")),
    PlantType(tag="PT-COR-MOONBEAM", botanical_name="Coreopsis verticillata",
              cultivar="Moonbeam", common_name="threadleaf coreopsis", form="perennial",
              mature_height=inch(18), mature_spread=inch(24),
              foliage_material="foliage-moonbeam", bloom="pale yellow, June-September",
              source=("https://www.northcreeknurseries.com/plant-name/"
                      "Coreopsis-verticillata-Moonbeam (18 in mound, rhizomatous to ~24 in: "
                      "divide every 3-4 years to hold the grid)")),
    PlantType(tag="PT-SED-ANGELINA", botanical_name="Sedum rupestre", cultivar="Angelina",
              common_name="stonecrop", form="groundcover", mature_height=inch(6),
              mature_spread=inch(18), foliage_material="foliage-chartreuse",
              bloom="yellow, June; chartreuse foliage, orange in winter", source=_TYPICAL),
    PlantType(tag="PT-HEU-CARAMEL", botanical_name="Heuchera villosa", cultivar="Caramel",
              common_name="coral bells", form="perennial", mature_height=inch(12),
              mature_spread=inch(18), foliage_material="foliage-caramel",
              bloom="apricot-caramel foliage all season", source=_TYPICAL),
    # --- the rain garden floor (zone 1); 'Jazz' takes the rim and slopes (zone 3) -----------
    PlantType(tag="PT-CAR-VULP", botanical_name="Carex vulpinoidea",
              common_name="fox sedge", form="grass", mature_height=inch(24),
              mature_spread=inch(18), foliage_material="foliage-sedge",
              bloom="tan seed heads, June-July; takes standing water", source=_TYPICAL),
    PlantType(tag="PT-IRI-VERS", botanical_name="Iris versicolor",
              common_name="blue flag iris", form="perennial", mature_height=inch(30),
              mature_spread=inch(18), foliage_material="foliage-iris",
              bloom="blue-violet, May-June", source=_TYPICAL),
    PlantType(tag="PT-ASC-INCA", botanical_name="Asclepias incarnata",
              common_name="swamp milkweed", form="perennial", mature_height=inch(48),
              mature_spread=inch(24), foliage_material="foliage-milkweed",
              bloom="pink, July-August", source=_TYPICAL),
    # --- the walk pockets (a cycled palette, 16 in sonotube voids) -------------------------
    PlantType(tag="PT-ALL-MILLENIUM", botanical_name="Allium", cultivar="Millenium",
              common_name="ornamental onion", form="perennial", mature_height=inch(18),
              mature_spread=inch(15), foliage_material="foliage-perennial",
              bloom="rose-purple, July-August", source=_TYPICAL),
    PlantType(tag="PT-CAL-NEPETA", botanical_name="Calamintha nepeta",
              common_name="lesser calamint", form="perennial", mature_height=inch(15),
              mature_spread=inch(18), foliage_material="foliage-perennial",
              bloom="white, July-October", source=_TYPICAL),
    PlantType(tag="PT-SPO-TARA", botanical_name="Sporobolus heterolepis", cultivar="Tara",
              common_name="prairie dropseed", form="grass", mature_height=inch(24),
              mature_spread=inch(18), foliage_material="foliage-bluestem",
              bloom="airy seed heads, August", source=_TYPICAL),
    PlantType(tag="PT-SAL-PURP", botanical_name="Salvia officinalis", cultivar="Purpurascens",
              common_name="purple sage", form="shrub", mature_height=inch(18),
              mature_spread=inch(18), foliage_material="foliage-caramel",
              bloom="purple-grey foliage, sub-shrub", source=_TYPICAL),
    # --- the espaliers: three Minnesota cultivars that pollinate one another --------------
    PlantType(tag="PT-MAL-HONEYCRISP", botanical_name="Malus domestica", cultivar="Honeycrisp",
              common_name="apple", form="tree", mature_height=ft(8), mature_spread=ft(6),
              foliage_material="foliage-apple", bloom="white, May", rootstock="Bud 9",
              source="dwarf rootstock held at the trellis height by pruning"),
    PlantType(tag="PT-MAL-ZESTAR", botanical_name="Malus domestica", cultivar="Zestar!",
              common_name="apple", form="tree", mature_height=ft(8), mature_spread=ft(6),
              foliage_material="foliage-apple", bloom="white, May", rootstock="M9",
              source="dwarf rootstock held at the trellis height by pruning"),
    PlantType(tag="PT-MAL-HARALSON", botanical_name="Malus domestica", cultivar="Haralson",
              common_name="apple", form="tree", mature_height=ft(8), mature_spread=ft(6),
              foliage_material="foliage-apple", bloom="white, May", rootstock="Bud 9",
              source="dwarf rootstock held at the trellis height by pruning"),
)
