"""The ``plumbing`` block of model.json: riser geometry, fixture units, and the takeoff.

Presentation data only, in the reader contract every other block follows: nothing is
recomputed in the browser, missing values are ``None`` (rendered "—"), and every row
carries ``uid``/``tag`` so the reader can zoom the plan. The fixture-unit arithmetic is
imported from ``takeoff/plumbing_calc.py`` — the same functions ``checks/mep/plumbing.py``
grades with — so the public page and the permit findings can never disagree.

Fittings are *counted* off geometry rather than estimated, and the counting itself now lives
in :mod:`typehaus.resolve.mep_fittings` — the one reading this take-off, the duct take-off,
``mep.fitting_pattern`` and the router's proposal all share. No fitting element exists in
the schema, and none needs to: a fitting is where two pipes meet, which the geometry already
says. What this module keeps is the *row*, because a row is a price and the price list is
the house's.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_fittings import (
    FAMILY_PIPE,
    MIN_FITTING_TURN_DEG,
    family_records,
    fitting_records,
    order_key,
    size_text,
    takeoff_rows,
)
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.plumbing_calc import (
    branch_load,
    fixture_units,
    required_drain_diameter_in,
    required_supply_size_in,
)

_M_TO_FT = 3.280839895


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
            "diameter_in": round(run.diameter_m / M_PER_IN, 2), "material": run.material,
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
        diameter_in = round(run.diameter_m / M_PER_IN, 2)
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


#: Kept as this module's spelling of the shared constants, so a reader of the plumbing
#: take-off does not have to go looking for where a turn stops being a grade change.
_MIN_FITTING_TURN_DEG = MIN_FITTING_TURN_DEG
_elbow_key = order_key
_size_text = size_text


def fitting_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Elbows and wyes **counted off the geometry**, by system, fitting and size.

    A reader of :func:`~typehaus.resolve.mep_fittings.fitting_records` now, filtered to the
    pipe family. An elbow is a turn measured on the run's own 3D polyline — a vertical drop
    meeting a horizontal branch is the 90° it actually is, a rolled offset the 45° it
    actually is — and snapped to the stock angle it is bought as. A wye comes from
    ``drain_tie_ins``' real geometric parent inference for the drainage graph, which yields
    *both* diameters, so the row is sized correctly rather than at the larger of the two.

    Supply tees are not counted. There is no equivalent parent inference for a pressurised
    system (a water branch has no invert to arrive above, so nothing distinguishes a tee
    from two runs crossing), and a guess billed as a count is worse than an absence: the
    fittings a supply manifold takes are in the ``[pipe_runs]`` per-foot rate, whose basis
    note says so.

    **Four keys, not seven.** ``takeoff_rows`` also carries the catalogued part and the
    coverage gap; they are dropped here on purpose. This row joins ``prices.toml`` and lands
    in ``model.json``, and what a fitting *is* belongs to ``mep.fitting_pattern``, which
    grades it — not to the sheet the estimator prices off.
    """
    rows = takeoff_rows(family_records(fitting_records(model), FAMILY_PIPE))
    return [{"system": row["system"], "fitting": row["fitting"],
             "count": row["count"], "tags": row["tags"]} for row in rows]


def cast_in_list(model: ResolvedModel) -> list[dict[str, object]]:
    """The pour-day sheet: every cast-in sleeve with its host, coordinates, and axis."""
    return [{
        "tag": s.tag, "uid": s.uid, "storey": s.storey, "host": s.host_slab,
        "host_category": s.host_category, "axis": s.axis, "purpose": s.purpose,
        "x_ft": round(s.center[0] * _M_TO_FT, 2),
        "y_ft": round(s.center[1] * _M_TO_FT, 2),
        "center_z_ft": (round(s.center_z_m * _M_TO_FT, 2)
                        if s.center_z_m is not None else None),
        "pipe_in": round(s.pipe_d_m / M_PER_IN, 2),
        "sleeve_in": round(s.sleeve_d_m / M_PER_IN, 2),
        "serves": s.serves_fixture,
        "offset_in": (round(s.offset_m / M_PER_IN, 2) if s.offset_m is not None
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
               round(run.diameter_m / M_PER_IN, 2))
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
            "fittings": fitting_takeoff(model),
            "cast_in": cast_in_list(model),
            "hydrants": hydrant_rows(model),
            "accessories": accessory_rows(model),
        },
    }
