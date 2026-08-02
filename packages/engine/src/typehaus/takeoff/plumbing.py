"""The ``plumbing`` block of model.json: riser geometry, fixture units, and the takeoff.

Presentation data only, in the reader contract every other block follows: nothing is
recomputed in the browser, missing values are ``None`` (rendered "—"), and every row
carries ``uid``/``tag`` so the reader can zoom the plan. The fixture-unit arithmetic is
imported from ``takeoff/plumbing_calc.py`` — the same functions ``checks/mep/plumbing.py``
grades with — so the public page and the permit findings can never disagree.

The fitting counts are *estimates from geometry* (bends → elbows, shared vertices → tees);
no fitting element exists in the schema, and the rows say "estimated" for that reason.
"""

from __future__ import annotations

import math

from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.plumbing_calc import (
    branch_load,
    fixture_units,
    required_drain_diameter_in,
    required_supply_size_in,
)

_M_TO_FT = 3.280839895
_M_TO_IN = 39.37007874015748
_ELBOW_MIN_TURN_DEG = 20.0
_TEE_TOL_M = 0.02


def riser_runs(model: ResolvedModel) -> list[dict[str, object]]:
    """Raw routed geometry per run — the reader projects it, never re-derives it."""
    rows: list[dict[str, object]] = []
    for run in model.pipe_runs:
        vertices = []
        for i, (x, y) in enumerate(run.path):
            z = run.z_m[i] if run.z_m is not None and i < len(run.z_m) else None
            vertices.append([round(x, 4), round(y, 4),
                             round(z, 4) if z is not None else None])
        rows.append({
            "tag": run.tag, "uid": run.uid, "storey": run.storey, "system": run.system,
            "diameter_in": round(run.diameter_m * _M_TO_IN, 2), "material": run.material,
            "length_ft": round(run.length_m * _M_TO_FT, 1),
            "serves": list(run.serves),
            "wall_refs": [w for w in run.wall_refs if w is not None],
            "vertices": vertices,
        })
    return rows


def fixture_unit_rows(model: ResolvedModel) -> dict[str, object]:
    """Per-fixture DFU/WSFU plus per-run accumulated loads and required sizes.

    Drain loads roll up the whole upstream subtree (``resolve/mep.py::accumulated_serves``)
    exactly as ``mep.pipe_sizing`` grades them — the shared-derivation invariant."""
    from typehaus.resolve.mep import accumulated_serves

    units = fixture_units(model.plan)
    units_by_tag = {row.tag: row for row in units}
    rolled_up = accumulated_serves(model.pipe_runs)
    run_rows: list[dict[str, object]] = []
    for run in model.pipe_runs:
        if run.system not in ("drain", "water_hot", "water_cold"):
            continue
        serves = (rolled_up.get(run.tag, tuple(run.serves))
                  if run.system == "drain" else tuple(run.serves))
        if not serves:
            continue
        load, unresolved = branch_load(serves, units_by_tag, run.system)
        required = None
        if load is not None:
            required = (required_drain_diameter_in(load) if run.system == "drain"
                        else required_supply_size_in(load))
        diameter_in = round(run.diameter_m * _M_TO_IN, 2)
        status = None
        if load is not None:
            status = ("unknown" if required is None
                      else "pass" if diameter_in + 0.06 >= required else "fail")
        run_rows.append({
            "tag": run.tag, "uid": run.uid, "system": run.system,
            "diameter_in": diameter_in, "serves": list(serves),
            "load": load, "unit": "DFU" if run.system == "drain" else "WSFU",
            "required_in": required, "status": status,
            "unresolved": list(unresolved),
        })
    return {
        "fixtures": [row.as_dict() for row in units],
        "runs": run_rows,
        "total_dfu": (sum(row.dfu for row in units if row.dfu is not None)
                      if units else None),
        "total_wsfu": (sum(row.wsfu_total for row in units
                           if row.wsfu_total is not None) if units else None),
    }


def _turn_angle_deg(a, b, c) -> float:
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 90.0  # a vertical drop meeting a horizontal segment is a turn
    dot = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(dot))


def fitting_estimate(model: ResolvedModel) -> list[dict[str, object]]:
    """Estimated elbows (interior bends) and tees (vertices shared between runs of one
    system), grouped by system + diameter. Estimates, not a schema — labeled as such."""
    counts: dict[tuple[str, float, str], int] = {}
    for run in model.pipe_runs:
        diameter = round(run.diameter_m * _M_TO_IN, 2)
        for i in range(1, len(run.path) - 1):
            if _turn_angle_deg(run.path[i - 1], run.path[i],
                               run.path[i + 1]) >= _ELBOW_MIN_TURN_DEG:
                key = (run.system, diameter, "elbow (estimated)")
                counts[key] = counts.get(key, 0) + 1
    for i, run_a in enumerate(model.pipe_runs):
        for run_b in model.pipe_runs[i + 1:]:
            if run_a.system != run_b.system:
                continue
            for va in run_a.path:
                if any(math.hypot(va[0] - vb[0], va[1] - vb[1]) <= _TEE_TOL_M
                       for vb in run_b.path):
                    diameter = round(max(run_a.diameter_m, run_b.diameter_m) * _M_TO_IN, 2)
                    key = (run_a.system, diameter, "tee (estimated)")
                    counts[key] = counts.get(key, 0) + 1
                    break
    return [{"system": system, "diameter_in": diameter, "fitting": fitting,
             "count": count}
            for (system, diameter, fitting), count in sorted(counts.items())]


def cast_in_list(model: ResolvedModel) -> list[dict[str, object]]:
    """The pour-day sheet: every cast-in sleeve with its host, coordinates, and axis."""
    return [{
        "tag": s.tag, "uid": s.uid, "storey": s.storey, "host": s.host_slab,
        "host_category": s.host_category, "axis": s.axis, "purpose": s.purpose,
        "x_ft": round(s.center[0] * _M_TO_FT, 2),
        "y_ft": round(s.center[1] * _M_TO_FT, 2),
        "center_z_ft": (round(s.center_z_m * _M_TO_FT, 2)
                        if s.center_z_m is not None else None),
        "pipe_in": round(s.pipe_d_m * _M_TO_IN, 2),
        "sleeve_in": round(s.sleeve_d_m * _M_TO_IN, 2),
        "serves": s.serves_fixture,
        "offset_in": (round(s.offset_m * _M_TO_IN, 2) if s.offset_m is not None
                      else None),
    } for s in sorted(model.sleeves, key=lambda s: s.tag)]


def hydrant_rows(model: ResolvedModel) -> list[dict[str, object]]:
    from typehaus.model.enums import Service

    types = {t.tag: t for t in model.plan.library.fixture_types}
    rows = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Fixture":
                continue
            fixture_type = types.get(element.type_ref)
            if (fixture_type is None or fixture_type.plan_symbol != "hydrant"
                    or Service.WATER_COLD not in fixture_type.needs):
                continue
            feeds = [r.tag for r in model.pipe_runs
                     if r.system == "water_cold" and element.tag in r.serves]
            rows.append({
                "tag": element.tag, "uid": element.uid, "storey": storey.tag,
                "type_ref": element.type_ref, "room": element.room,
                "supply_runs": feeds, "source": fixture_type.source,
            })
    return rows


def pipe_takeoff_by_material(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet grouped by (system, material, finish, diameter) — what an estimator orders.

    ``finish`` joins the key because lacquered copper is a different line than bare copper:
    the lacquer is applied labour and a separate product, and a house that runs both — as
    this one does, copper where it is seen against concrete and PEX everywhere else — would
    otherwise roll them into one row and price the coating over all of it.
    """
    groups: dict[tuple[str, str, str, float], dict[str, object]] = {}
    for run in model.pipe_runs:
        key = (run.system, run.material or "—", run.finish or "—",
               round(run.diameter_m * _M_TO_IN, 2))
        entry = groups.setdefault(key, {"length_m": 0.0, "runs": 0, "tags": []})
        entry["length_m"] += run.length_m
        entry["runs"] += 1
        entry["tags"].append(run.tag)
    return [{"system": system, "material": material, "finish": finish,
             "diameter_in": diameter, "runs": int(entry["runs"]),
             "length_ft": round(float(entry["length_m"]) * _M_TO_FT, 1),
             "tags": sorted(entry["tags"])}
            for (system, material, finish, diameter), entry in sorted(groups.items())]


def accessory_rows(model: ResolvedModel) -> list[dict[str, object]]:
    """Every in-line device, one row each, for the plumbing sheet's specialties schedule.

    Not the rolled-up BOM section (``takeoff/plumbing_specialties.py``): a schedule prints
    one line per device with its tag, where it is, and what it protects, because that is
    what an inspector walks the house with."""
    return [
        {"tag": acc.tag, "kind": acc.kind, "storey": acc.storey, "system": acc.system,
         "pipe_ref": acc.pipe_ref, "room": acc.room, "model": acc.model,
         "accessible": acc.accessible, "serves": list(acc.serves),
         "install_parts": list(acc.install_parts)}
        for acc in sorted(model.pipe_accessories, key=lambda a: a.tag)
    ]


def plumbing_takeoff(model: ResolvedModel) -> dict[str, object]:
    """The whole ``plumbing`` block (→ server/model_json.py)."""
    return {
        "riser": riser_runs(model),
        "fixture_units": fixture_unit_rows(model),
        "takeoff": {
            "pipe": pipe_takeoff_by_material(model),
            "fittings": fitting_estimate(model),
            "cast_in": cast_in_list(model),
            "hydrants": hydrant_rows(model),
            "accessories": accessory_rows(model),
        },
    }
