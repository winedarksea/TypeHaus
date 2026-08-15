"""The trade take-offs, carried verbatim from ``takeoff/``.

Nothing here is derived in this module: every block is the take-off's own return value,
shipped whole so the browser reads the same arithmetic the permit sheets print. That is the
seam's reason to exist — a schedule the UI recomputed could disagree with the one stamped
for permit, so this file is deliberately a courier and never a calculator.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks.registry import Preferences
from typehaus.resolve.model import ResolvedModel
from typehaus.server.model_json_shared import _provenance
from typehaus.source.provenance import Provenance
from typehaus.takeoff.backup_calc import backup_runtime_summary
from typehaus.takeoff.data import data_device_schedule, data_raceway_takeoff, poe_budget
from typehaus.takeoff.electrical import (
    backup_component_rows,
    conduit_takeoff,
    electrical_device_takeoff,
    panel_schedule,
    service_load_summary,
    solar_takeoff,
)
from typehaus.takeoff.hvac import hvac_takeoff
from typehaus.takeoff.lighting import (
    connected_lighting_va,
    light_run_takeoff,
    lighting_controls,
    luminaire_schedule,
)
from typehaus.takeoff.plumbing import plumbing_takeoff


def systems_json(
    model: ResolvedModel,
    provenance: Provenance | None,
    preferences: Preferences | None,
) -> dict[str, Any]:
    """Solar, lighting runs, and the HVAC / plumbing / electrical take-off payloads."""
    return {
        # Rooftop PV modules: the resolver's tilted corner rings (metres), drawn by the
        # viewer as two-ring boxes under the electrical trade toggle.
        "solar_panels": [
            {"uid": panel.uid, "tag": panel.tag, "storey": panel.storey,
             "roof_ref": panel.roof_ref,
             "corners_bottom": [list(point) for point in panel.corners_bottom],
             "corners_top": [list(point) for point in panel.corners_top],
             "watts": panel.watts, "product": panel.product,
             "provenance": _provenance(provenance, panel.tag)}
            for panel in sorted(model.solar_panels, key=lambda item: item.uid)
        ],
        # The electrical take-off, verbatim from takeoff/electrical.py — the same six
        # derivations the E-601 panel-schedule sheet and `haus takeoff` print. The circuits
        # reader is a third surface over one arithmetic, never a second one: a schedule the
        # browser recomputed could disagree with the sheet stamped for permit.
        # `service_load` is None for a house that authors no circuits (the summary would be
        # an estimate over nothing); every other section degrades to an empty list.
        # Linear luminaires: plan polyline + the height it is mounted at, so the viewer can
        # draw a cove where the ceiling actually is. Beside `solar_panels` because both are
        # resolver-owned geometry that is not a placeable.
        "light_runs": [
            {"uid": run.uid, "tag": run.tag, "storey": run.storey,
             "path": [list(point) for point in run.path], "z_m": run.z_m,
             "length_m": run.length_m, "type": run.type_ref, "room": run.room,
             "circuit": run.circuit, "psu_ref": run.psu_ref,
             "controlled_by": list(run.controlled_by),
             "provenance": _provenance(provenance, run.tag)}
            for run in sorted(model.light_runs, key=lambda item: item.uid)
        ],
        # The HVAC reader's whole payload, verbatim from takeoff/hvac.py — the same zone
        # arithmetic mep.heating_capacity checks against, for the same reason the panel
        # schedule is shared. None for a house with no preferences loaded: the zone rows are
        # block loads, and there is no block load without the envelope preferences.
        "hvac": (hvac_takeoff(model, preferences) if preferences is not None else None),
        # The plumbing reader's whole payload, verbatim from takeoff/plumbing.py — riser
        # geometry, fixture units (the same tables mep.pipe_sizing grades with), and the
        # pour-day cast-in list. No preferences dependency: fixture units are code tables.
        "plumbing": plumbing_takeoff(model),
        "electrical": {
            "panel_schedule": panel_schedule(model),
            "service_load": (service_load_summary(model)
                             if model.plan.library.circuits else None),
            "conduit": conduit_takeoff(model),
            "devices": electrical_device_takeoff(model),
            "solar": solar_takeoff(model),
            "backup_components": backup_component_rows(model),
            # The autonomy estimate the E-601 sheet prints, verbatim — same reason the
            # panel schedule is shared rather than recomputed in the browser.
            "backup_runtime": backup_runtime_summary(model),
            # The lighting reader's whole payload, verbatim from takeoff/lighting.py — the
            # same four derivations the E-602 sheet prints, for the same reason the panel
            # schedule is shared: a schedule the browser recomputed could disagree with the
            # one stamped for permit.
            "lighting": {
                "schedule": luminaire_schedule(model),
                "controls": lighting_controls(model),
                "runs": light_run_takeoff(model),
                "connected_va": connected_lighting_va(model),
            },
            # The low-voltage reader's whole payload, verbatim from takeoff/data.py — the
            # three derivations the E-603 sheet prints. Filed under `electrical` beside
            # `lighting` for the same reason that one is: they are separate readers over one
            # trade, not separate trades.
            "data": {
                "devices": data_device_schedule(model),
                "raceways": data_raceway_takeoff(model),
                "poe_budget": poe_budget(model),
            },
        },
    }
