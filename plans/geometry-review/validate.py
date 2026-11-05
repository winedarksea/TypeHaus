"""Validate findings/*.json against a findings schema (stdlib only; no jsonschema in .venv).

Usage: .venv/bin/python plans/geometry-review/validate.py [--schema PATH] [findings/S1.json ...]
The schema defaults to round 1's; round 2 passes 2026-11-04/findings.schema.json.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCHEMA: dict = {}


def _check(value, schema, path, errors):
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    t = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool,
             "integer": int, "number": (int, float)}
    if t and not isinstance(value, types[t]):
        errors.append(f"{path}: expected {t}, got {type(value).__name__}")
        return
    if t == "object":
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing {key}")
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                _check(value[key], sub, f"{path}.{key}", errors)
    elif t == "array":
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: {len(value)} items > {schema['maxItems']}")
        for i, item in enumerate(value):
            _check(item, schema.get("items", {}), f"{path}[{i}]", errors)
    elif t == "string" and "pattern" in schema and not re.match(schema["pattern"], value):
        errors.append(f"{path}: {value!r} !~ {schema['pattern']}")
    elif t == "number" and not schema.get("minimum", 0) <= value <= schema.get("maximum", 1e9):
        errors.append(f"{path}: {value} out of range")


def main(argv):
    global SCHEMA
    schema_path = HERE / "findings.schema.json"
    if "--schema" in argv:
        i = argv.index("--schema")
        schema_path = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    SCHEMA = json.loads(schema_path.read_text())
    paths = [Path(p) for p in argv] or sorted((schema_path.parent / "findings").glob("*.json"))
    bad = 0
    for p in paths:
        errors: list[str] = []
        try:
            _check(json.loads(p.read_text()), SCHEMA, p.stem, errors)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON: {exc}")
        n = len(json.loads(p.read_text()).get("findings", [])) if not errors else "?"
        print(f"{'OK ' if not errors else 'BAD'} {p.name}: {n} findings")
        for e in errors[:20]:
            print("   ", e)
        bad += bool(errors)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
