"""One-shot codemod: host every wall-mounted placeable on its wall face. Does not ship.

    .venv/bin/python scripts/host_wall_mounts.py houses/catlin [--write]

Resolves the house, matches each ``Mount(kind=WALL)`` body to the wall face it bears on,
and rewrites it as ``location=Location(attachment=WallAttachment(...))`` with ``position``
(and the now-derived ``rotation``, and a deprecated ``wall_ref`` on a device) deleted. The
ops go through ``attach_placeable`` and the server's write-back path (``ProjectCoordinator``),
one source file per patch. Rotation and station are preserved exactly; the normal gap is:

* snapped to 0 within 1/4", or when a non-recessed body is buried (it belongs ON the face);
* kept as the declared ``normal_gap`` when the body stands off up to 3" (rods, sinks);
* kept (negative) for a recessed body.

It REFUSES, and lists for a person, a body with no wall face at its height, one farther
than 3" off, or one whose best face is tied with another wall's.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

from typehaus.resolve import resolve
from typehaus.source import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.macros import attach_placeable
from typehaus.source.ops import DELETE_FIELD, PatchOp, RawExpr

IN = 0.0254
SNAP_M = 0.25 * IN
FLOAT_MAX_M = 3.0 * IN
TIE_M = 0.25 * IN


def _q(value_m: float) -> str:
    """inch(...) source rounded to 1/32"."""
    inches = round(value_m / IN * 32) / 32
    text = f"{inches:.5f}".rstrip("0").rstrip(".")
    return f"inch({text})"


def _present(layer, z0: float, z1: float) -> bool:
    return ((layer.z0_m is None or layer.z0_m < z1 + 1e-6)
            and (layer.z1_m is None or layer.z1_m > z0 - 1e-6))


def _candidates(model, obj):
    """(wall, face, station_m, signed gap_m, rotation_offset_deg) per wall face in reach."""
    z0 = obj.body_z0_m if obj.body_z0_m is not None else obj.z_m
    z1 = obj.body_z1_m if obj.body_z1_m is not None else z0
    out = []
    for wall in model.walls:
        if wall.z1_m <= z0 + 1e-6 or wall.z0_m >= z0 + 1e-6:
            continue
        (x0, y0), (x1, y1) = wall.axis
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 1e-9:
            continue
        tx, ty = (x1 - x0) / length, (y1 - y0) / length
        lx, ly = -ty, tx
        cx, cy = obj.position
        station = (cx - x0) * tx + (cy - y0) * ty
        if station < -1e-6 or station > length + 1e-6:
            continue
        layers = [la for la in wall.layers if _present(la, z0, z1)] or list(wall.layers)
        offsets = [(p[0] - x0) * lx + (p[1] - y0) * ly for la in layers for p in la.polygon]
        if not offsets:
            continue
        body = [(p[0] - x0) * lx + (p[1] - y0) * ly for p in obj.footprint]
        centre = (cx - x0) * lx + (cy - y0) * ly
        wall_angle = math.degrees(math.atan2(ty, tx))
        offset_deg = (obj.rotation_degrees - wall_angle + 180.0) % 360.0 - 180.0
        if centre > 0:
            out.append((wall, "left", station, min(body) - max(offsets), offset_deg))
        else:
            out.append((wall, "right", station, min(offsets) - max(body), offset_deg))
    return out


def _backs_onto(c) -> bool:
    """The body's back (local +y) faces this wall: offset 0 on a right face, 180 on a left."""
    offset = abs(c[4])
    return offset < 1.0 if c[1] == "right" else abs(offset - 180.0) < 1.0


def _break_tie(tied):
    """The face the body's back is turned to; among co-planar collinear walls, the one the
    station sits deepest inside. None when that still leaves more than one."""
    backed = [c for c in tied if _backs_onto(c)] or tied
    if len({c[0].tag for c in backed}) == 1:
        return backed[0]
    gaps = {round(c[3], 4) for c in backed}
    faces = {(round(c[0].axis[1][0] - c[0].axis[0][0], 3) == 0, c[1]) for c in backed}
    if len(gaps) == 1 and len(faces) == 1:

        def interior(c) -> float:
            (x0, y0), (x1, y1) = c[0].axis
            return min(c[2], math.hypot(x1 - x0, y1 - y0) - c[2])

        return max(backed, key=interior)
    return None


def plan_ops(house: Path):
    plan = load_plan(house).plan
    model, _ = resolve(plan)
    storey_of = {el.tag: storey for storey in plan.elements
                 for el in plan.storey_elements(storey)}
    hosted, refused, decided, notes = [], [], [], defaultdict(int)
    for obj in model.canvas_objects:
        if obj.mount is None or obj.mount.kind.value != "wall":
            continue
        element = plan.by_tag(obj.tag)
        if getattr(getattr(element, "location", None), "attachment", None) is not None:
            notes["already hosted"] += 1
            continue
        recessed = obj.mount.recessed_into_host_surface
        cands = [c for c in _candidates(model, obj) if c[3] <= FLOAT_MAX_M
                 and (recessed or c[3] > -6 * IN)]
        if not cands:
            refused.append((obj.tag, obj.kind, "no wall face within 3\" at its height"))
            continue
        cands.sort(key=lambda c: abs(c[3]))
        best = cands[0]
        tied = [c for c in cands if abs(abs(c[3]) - abs(best[3])) < TIE_M]
        if len({c[0].tag for c in tied}) > 1:
            best = _break_tie(tied)
            if best is None:
                refused.append((obj.tag, obj.kind, "tied between " + ", ".join(
                    f"{c[0].tag}/{c[1]}" for c in tied)))
                continue
            decided.append((obj.tag, best[0].tag, [c[0].tag for c in tied]))
        wall, face, station, gap, offset_deg = best
        if recessed:
            kind = "recessed"
        elif abs(gap) <= SNAP_M:
            kind, gap = "snapped", 0.0
        elif gap < 0:
            kind, gap = "unburied", 0.0
        else:
            kind = "stand-off"
        notes[kind] += 1
        hosted.append((obj.tag, obj.kind, storey_of[obj.tag], wall.tag, face, station, gap,
                       offset_deg, kind, element))
    return plan, hosted, refused, decided, notes


def _op(plan, row) -> PatchOp:
    tag, _kind, storey, wall, face, station, gap, offset_deg, _how, element = row
    base = attach_placeable(plan, storey, tag=tag, wall=wall, face=face,
                            distance=station, gap=gap).ops[0]
    location = (f'Location(attachment=WallAttachment(wall_ref="{wall}", face="{face}", '
                f"distance_from_start={_q(station)}, normal_gap={_q(gap)}, "
                f"rotation_offset=deg({round(offset_deg, 2):g})))")
    fields = {**base.fields, "location": RawExpr(location), "rotation": DELETE_FIELD}
    if getattr(element, "wall_ref", None) and element.element_kind == "ElectricalDevice":
        fields["wall_ref"] = DELETE_FIELD
    return PatchOp("update", base.type, tag, fields)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("house", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    plan, hosted, refused, decided, notes = plan_ops(args.house)
    by_kind: dict[str, int] = defaultdict(int)
    for row in hosted:
        by_kind[row[1]] += 1
    print(f"hosted {len(hosted)}: {dict(by_kind)}; {dict(notes)}")
    for row in hosted:
        if row[8] in {"unburied", "stand-off", "recessed"}:
            print(f"  {row[8]:9s} {row[0]} on {row[3]}/{row[4]} gap={row[6] / IN:.2f}\"")
    print(f"tie broken by rule {len(decided)}:")
    for tag, wall, tied in decided:
        print(f"  {tag}: {wall} of {tied}")
    print(f"refused {len(refused)}:")
    for tag, kind, why in refused:
        print(f"  {kind} {tag}: {why}")
    if not args.write:
        return 0
    by_file: dict[Path, list[PatchOp]] = defaultdict(list)
    sources = {p: p.read_text() for p in (args.house / "plan").rglob("*.py")}
    for row in hosted:
        path = next(p for p, s in sources.items() if f'tag="{row[0]}"' in s)
        by_file[path].append(_op(plan, row))
    coordinator = ProjectCoordinator(args.house)
    for path, ops in sorted(by_file.items()):
        coordinator.apply_patch(ops, coordinator.revision())
        print(f"wrote {len(ops)} to {path.relative_to(args.house)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
