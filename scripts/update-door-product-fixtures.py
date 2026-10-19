"""Regenerate the cased-door cross-language fixtures after intentional geometry changes."""
import json
from dataclasses import asdict, fields, replace
from pathlib import Path

from typehaus.emit.door_surfaces import door_part_color, door_part_surface
from typehaus.model import DoorType
from typehaus.quantities import m
from typehaus.resolve.door_product_spec import resolve_cased_door
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model import ResolvedLayer, ResolvedOpening, ResolvedWall

fixture_path = Path(__file__).resolve().parents[1] / "ui/src/three/builders/casedDoorFixtures.json"
fixtures = json.loads(fixture_path.read_text())
for fixture in fixtures:
    source_wall = fixture["wall"]
    layers = tuple(ResolvedLayer(
        name=layer["name"], material_ref=layer["material"], function=layer["function"],
        thickness_m=layer["thickness_m"], polygon=tuple(map(tuple, layer["polygon"])))
        for layer in source_wall["layers"])
    wall = ResolvedWall(**{field.name: source_wall[field.name] for field in fields(ResolvedWall)
                           if field.name in source_wall and field.name != "layers"}, layers=layers)
    source_opening = fixture["opening"]
    opening = ResolvedOpening(**{
        field.name: source_opening[field.name] for field in fields(ResolvedOpening)
        if field.name in source_opening and field.name != "cased_product"})
    product_type = DoorType(tag="DT", width=m(opening.width_m), height=m(opening.height_m),
                           operation=fixture["operation"])
    specification = resolve_cased_door(wall, opening, product_type,
        finished_floors=tuple(source_opening["cased_product"]["finished_floor_z_m"]))
    source_opening["cased_product"] = asdict(specification)
    boxes = []
    for part in opening_parts(wall, replace(opening, cased_product=specification),
                              product_type.operation):
        for solid in part.solids:
            points = [(x, z, -y) for x, y in solid.ring for z in (solid.z0_m, solid.z1_m)]
            boxes.append({
                "part": part.key,
                "bounds": [min(p[i] for p in points) for i in range(3)] + [
                    max(p[i] for p in points) for i in range(3)],
                "finish": part.material_key,
                "color": door_part_color(part, {}, linear_paint_defaults=True),
                "surface": door_part_surface(part),
            })
    fixture["boxes"] = boxes

# Each box gets a row, making intentional shape diffs reviewable without a thousand-line file.
rows = []
for fixture in fixtures:
    entries = [f'    "{key}": {json.dumps(value)}' 
               for key, value in fixture.items() if key != "boxes"]
    boxes = ",\n".join(f"      {json.dumps(box)}" for box in fixture["boxes"])
    rows.append("  {\n" + ",\n".join(entries) + ',\n    "boxes": [\n' + boxes + "\n    ]\n  }")
fixture_path.write_text("[\n" + ",\n".join(rows) + "\n]\n")
