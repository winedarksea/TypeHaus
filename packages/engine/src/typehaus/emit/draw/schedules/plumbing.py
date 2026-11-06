"""P-601 — the fixture rough-in (stub height) schedule and the pipe insulation schedule.

The rough-in crew had no height anywhere on P-101..P-104 (M2-105). Every number here is
read off the model: a port's station is the fixture type's declared ``ServicePort``, placed
by ``mep_sleeves.placed_port_point``, and measured from the owning room's FINISHED floor
(``room_floor.room_finished_floor_elevation``), which is what "AFF" means. A fixture outside
any room is measured from its storey datum and says so.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.paged_tables import PagedTable, wrap_cells
from typehaus.emit.draw.schedules.structural import _write_paged
from typehaus.emit.draw.typography import feet_inches_8th
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

_DASH = "—"
_SERVICE_TEXT = {"drain": "DRAIN", "water_cold": "CW", "water_hot": "HW"}


def has_plumbing_schedule(model: ResolvedModel) -> bool:
    return bool(rough_in_rows(model))


def rough_in_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    """(fixture, room, type, port, service, height, measured from, stub run) per port."""
    from typehaus.resolve.mep_sleeves import placed_port_point
    from typehaus.resolve.room_floor import room_finished_floor_elevation
    from typehaus.resolve.room_lookup import room_owning

    plan = model.plan
    library = plan.library
    types = {entry.tag: entry for entry in (*library.fixture_types, *library.appliance_types)}
    placed = {obj.tag: obj for obj in model.canvas_objects}
    datum = {storey.tag: storey.elevation.meters for storey in plan.storeys}
    order = {storey.tag: index for index, storey in enumerate(
        sorted(plan.storeys, key=lambda storey: storey.elevation.meters))}
    rows: list[tuple[int, tuple[str, ...]]] = []
    for element in (*plan.elements_of_kind("Fixture"), *plan.elements_of_kind("Appliance")):
        fixture_type = types.get(element.type_ref)
        obj = placed.get(element.tag)
        if fixture_type is None or obj is None:
            continue
        room = room_owning(model, obj.storey, obj.position)
        floor = (room_finished_floor_elevation(model, room) if room is not None
                 else datum.get(obj.storey, 0.0))
        for port in fixture_type.ports:
            service = _SERVICE_TEXT.get(port.service.value)
            point = placed_port_point(model, element.tag, port) if service else None
            if point is None:
                continue
            z = datum.get(obj.storey, 0.0) + point[2]
            run = _stub_run(model, element.tag, port.service.value, (*point[:2], z))
            rows.append((order.get(obj.storey, 0), (
                element.tag, room.tag if room is not None else _DASH, fixture_type.tag,
                port.tag, service, feet_inches_8th((z - floor) / M_PER_IN),
                "fin. floor" if room is not None else f"{obj.storey} datum", run)))
    return tuple(row for _order, row in sorted(rows, key=lambda item: (item[0], item[1])))


def _stub_run(model: ResolvedModel, fixture: str, system: str,
              port: tuple[float, float, float]) -> str:
    """The serving run whose end is nearest the port: the stub, not the trunk behind it."""
    from math import dist

    ends = [(dist((*run.path[i], run.z_m[i]), port), run.tag) for run in model.pipe_runs
            if fixture in run.serves and run.system == system
            and run.z_m and len(run.z_m) == len(run.path) for i in (0, -1)]
    return min(ends)[1] if ends else _DASH


def insulation_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    """(run, system, size, material, insulation, heat trace, LF) for each lagged run."""
    from typehaus.emit.draw.plumbingplan import _SYSTEM_TEXT, _nominal

    rows = []
    for run in sorted(model.pipe_runs, key=lambda run: run.tag):
        if not (run.insulation or run.freeze_protection):
            continue
        rows.append((run.tag, _SYSTEM_TEXT.get(run.system, run.system.replace("_", " ").upper()),
                     _nominal(run.diameter_m / M_PER_IN), (run.material or _DASH).upper(),
                     run.insulation or _DASH, run.freeze_protection or _DASH,
                     f"{run.length_m / M_PER_IN / 12:.1f}"))
    return tuple(rows)


def plumbing_tables(model: ResolvedModel) -> list[PagedTable]:
    tables = [PagedTable("FIXTURE ROUGH-IN (STUB HEIGHTS)",
                         ("Fixture", "Room", "Type", "Port", "Service", "Height",
                          "Measured from", "Run"),
                         rough_in_rows(model))]
    lagged = insulation_rows(model)
    if lagged:
        tables.append(PagedTable("PIPE INSULATION", ("Run", "System", "Size", "Material",
                                                     "Insulation", "Heat trace", "LF"),
                                 wrap_cells(lagged, {4: 44, 5: 30})))
    return tables


def write_plumbing_schedule(pdf, model: ResolvedModel, number: str, name: str, *,
                            page: int = 0) -> None:
    _write_paged(pdf, model, number, name, plumbing_tables(model), page)
