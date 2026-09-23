"""Catlin plant catalog — illustrative, counted, never priced (like fixture_types.py).

Mature sizes are the published ones where a source is named; the rest are typical and
marked so. The owner swaps entries here; a swap moves no geometry but a plant's spread.
Foliage, bloom, bark and fruit materials carry the render colours (``Material.color``) of
the procedural 3D models, which are built per ``form``: a form swap changes the model.
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
    _foliage("foliage-october-sky", "Switchgrass 'October Sky' foliage, blue-green", "#6f9486"),
    _foliage("foliage-northwind", "Switchgrass 'Northwind' foliage, olive to blue-green",
             "#62805a"),
    _foliage("foliage-iris", "Blue flag iris foliage, grey-green", "#6f8f78"),
    _foliage("foliage-milkweed", "Swamp milkweed, dark green with pink bloom", "#6d7f4a"),
    _foliage("foliage-perennial", "Mixed perennial foliage", "#6f8c4a"),
    _foliage("foliage-apple", "Apple foliage, deep green", "#4f7a3a"),
    # Bloom, bark and fruit: the models' other parts (a type without one uses its foliage).
    _foliage("bloom-moonbeam", "Coreopsis 'Moonbeam' bloom, pale yellow", "#efe08a"),
    _foliage("bloom-allium", "Allium 'Millenium' bloom, rose-purple", "#b0609e"),
    _foliage("bloom-calamint", "Calamint bloom, white", "#eeeef0"),
    _foliage("bloom-iris", "Blue flag iris bloom, blue-violet", "#6c5fb0"),
    _foliage("bloom-milkweed", "Swamp milkweed bloom, pink", "#d77fa0"),
    _foliage("seed-bluestem", "Little bluestem seed heads, bronze", "#a8744a"),
    _foliage("seed-october-sky", "Switchgrass 'October Sky' seed heads, rosy purple",
             "#a0668a"),
    _foliage("seed-northwind", "Switchgrass 'Northwind' seed heads, golden beige", "#c4a878"),
    _foliage("bark-apple", "Apple bark, grey-brown", "#6b5a4a"),
    _foliage("fruit-apple", "Apple fruit, red", "#b3262a"),
)

PLANT_TYPES = (
    # --- the grid field and its accents (params/landscape_gardens.py) ----------------------
    PlantType(tag="PT-SCH-JAZZ", botanical_name="Schizachyrium scoparium", cultivar="Jazz",
              common_name="little bluestem", form="grass", mature_height=inch(30),
              mature_spread=inch(18), foliage_material="foliage-bluestem",
              bloom_material="seed-bluestem",
              bloom="blue-green summer, burgundy-bronze autumn",
              source=("https://www.missouribotanicalgarden.org/PlantFinder/"
                      "PlantFinderDetails.aspx?taxonid=299967&isprofile=0&pt=11 "
                      "(24-30 in x 12-18 in, upright, does not flop)")),
    PlantType(tag="PT-COR-MOONBEAM", botanical_name="Coreopsis verticillata",
              cultivar="Moonbeam", common_name="threadleaf coreopsis", form="perennial",
              mature_height=inch(18), mature_spread=inch(24),
              foliage_material="foliage-moonbeam",
              bloom_material="bloom-moonbeam",
              bloom="pale yellow, June-September",
              source=("https://www.northcreeknurseries.com/plant-name/"
                      "Coreopsis-verticillata-Moonbeam (18 in mound, rhizomatous to ~24 in: "
                      "divide every 3-4 years to hold the grid)")),
    PlantType(tag="PT-SED-ANGELINA", botanical_name="Sedum rupestre", cultivar="Angelina",
              common_name="stonecrop", form="groundcover", mature_height=inch(6),
              mature_spread=inch(18), foliage_material="foliage-chartreuse",
              bloom="yellow, June; chartreuse foliage, orange in winter", source=_TYPICAL),
    PlantType(tag="PT-HEU-CARAMEL", botanical_name="Heuchera villosa", cultivar="Caramel",
              common_name="coral bells", form="perennial", mature_height=inch(12),
              mature_spread=inch(18), foliage_material="foliage-perennial",
              bloom="apricot-caramel foliage all season", source=_TYPICAL),
    # --- the rain garden floor (zone 1); 'Jazz' takes the rim and slopes (zone 3) -----------
    PlantType(tag="PT-PAN-OCTSKY", botanical_name="Panicum virgatum",
              cultivar="Prairie Winds 'October Sky'", common_name="switchgrass", form="grass",
              mature_height=inch(60), mature_spread=inch(30),
              foliage_material="foliage-october-sky", bloom_material="seed-october-sky",
              bloom="rosy-purple seed heads, late summer-fall; blue-green, gold in fall",
              source=("https://www.waltersgardens.com/variety.php?ID=PANOS "
                      "(4.5-5 ft x 2-2.5 ft, upright; withstands periodic flooding)")),
    PlantType(tag="PT-PAN-NORTHWIND", botanical_name="Panicum virgatum", cultivar="Northwind",
              common_name="switchgrass", form="grass", mature_height=inch(60),
              mature_spread=inch(36), foliage_material="foliage-northwind",
              bloom_material="seed-northwind",
              bloom="golden seed heads, late summer; yellow-beige in fall, holds in winter",
              source=("http://pw.waltersgardens.com/variety.php?ID=PANNO "
                      "(4-6 ft x 2-3 ft, rigidly upright clump)")),
    PlantType(tag="PT-IRI-VERS", botanical_name="Iris versicolor",
              common_name="blue flag iris", form="perennial", mature_height=inch(30),
              mature_spread=inch(18), foliage_material="foliage-iris",
              bloom_material="bloom-iris",
              bloom="blue-violet, May-June", source=_TYPICAL),
    PlantType(tag="PT-ASC-INCA", botanical_name="Asclepias incarnata",
              common_name="swamp milkweed", form="perennial", mature_height=inch(48),
              mature_spread=inch(24), foliage_material="foliage-milkweed",
              bloom_material="bloom-milkweed",
              bloom="pink, July-August", source=_TYPICAL),
    # --- the walk pockets (a cycled palette, 16 in sonotube voids) -------------------------
    PlantType(tag="PT-ALL-MILLENIUM", botanical_name="Allium", cultivar="Millenium",
              common_name="ornamental onion", form="perennial", mature_height=inch(18),
              mature_spread=inch(15), foliage_material="foliage-perennial",
              bloom_material="bloom-allium",
              bloom="rose-purple, July-August", source=_TYPICAL),
    PlantType(tag="PT-CAL-NEPETA", botanical_name="Calamintha nepeta",
              common_name="lesser calamint", form="perennial", mature_height=inch(15),
              mature_spread=inch(18), foliage_material="foliage-perennial",
              bloom_material="bloom-calamint",
              bloom="white, July-October", source=_TYPICAL),
    PlantType(tag="PT-SPO-TARA", botanical_name="Sporobolus heterolepis", cultivar="Tara",
              common_name="prairie dropseed", form="grass", mature_height=inch(24),
              mature_spread=inch(18), foliage_material="foliage-bluestem",
              bloom="airy seed heads, August", source=_TYPICAL),
    PlantType(tag="PT-SAL-PURP", botanical_name="Salvia officinalis", cultivar="Purpurascens",
              common_name="purple sage", form="shrub", mature_height=inch(18),
              mature_spread=inch(18), foliage_material="foliage-perennial",
              bloom="purple-grey foliage, sub-shrub", source=_TYPICAL),
    # --- the espaliers: three Minnesota cultivars that pollinate one another --------------
    PlantType(tag="PT-MAL-HONEYCRISP", botanical_name="Malus domestica", cultivar="Honeycrisp",
              common_name="apple", form="tree", mature_height=ft(8), mature_spread=ft(6),
              foliage_material="foliage-apple",
              stem_material="bark-apple", fruit_material="fruit-apple",
              bloom="white, May", rootstock="Bud 9",
              source="dwarf rootstock held at the trellis height by pruning"),
    PlantType(tag="PT-MAL-ZESTAR", botanical_name="Malus domestica", cultivar="Zestar!",
              common_name="apple", form="tree", mature_height=ft(8), mature_spread=ft(6),
              foliage_material="foliage-apple",
              stem_material="bark-apple", fruit_material="fruit-apple",
              bloom="white, May", rootstock="M9",
              source="dwarf rootstock held at the trellis height by pruning"),
    PlantType(tag="PT-MAL-HARALSON", botanical_name="Malus domestica", cultivar="Haralson",
              common_name="apple", form="tree", mature_height=ft(8), mature_spread=ft(6),
              foliage_material="foliage-apple",
              stem_material="bark-apple", fruit_material="fruit-apple",
              bloom="white, May", rootstock="Bud 9",
              source="dwarf rootstock held at the trellis height by pruning"),
)
