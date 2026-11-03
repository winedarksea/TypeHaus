"""Recalculate screen geometry, local checks and before/after normal house loads.

Exit nonzero for failed OR incomplete new checks. --output writes the same review
artifact even when acceptance is blocked. No files or fixture models are mutated.
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "houses/catlin"))
from plan import entry_screen_finish_spec as spec  # noqa: E402
from plan.entry_screen_finish_checks import concentrated_sill_delta, local_timber_checks  # noqa: E402

from typehaus.checks.run import build_context  # noqa: E402
from typehaus.engineering.pier_basis import wall_line_loads  # noqa: E402
from typehaus.engineering.roof_lateral import roof_winds  # noqa: E402
from typehaus.resolve.assembly_weight import dead_load_plf, wall_line_plf  # noqa: E402
from typehaus.source import load_plan  # noqa: E402


def load_summary(context):
    wall = context.model.wall("W-BW-SCREEN")
    return {
        "wall_dead_load_plf": dead_load_plf(context, wall, wall.z1_m - wall.z0_m),
        "wall_and_upper_band_plf": wall_line_plf(context, wall)[0],
        "wall_reaction_lb": wall_line_loads(context.engineering.context)[0],
        "structural_records": [
            {"key": f"{r.kind}/{r.key}", "status": r.status.value,
             "ratio": r.governing.ratio if r.governing else None}
            for r in context.engineering.values() if any("BW" in tag for tag in r.element_tags)
        ],
    }


def previous_weight_plan(plan):
    """A weight-only comparison, keeping all other current house decisions identical.

    The unchanged north tie relief is retained. Adjust effective density over today's
    net panel area to reproduce yesterday's total panel/support/hardware mass exactly.
    This variant is not a previous-geometry model or an additional door/export test.
    """
    previous_area = spec.panel_net_area_in2(spec.PREVIOUS_PANEL_RUNS_IN)
    previous_mass_lb = (previous_area * spec.PANEL_THICKNESS_IN * spec.LB_PER_IN3
                        + spec.PREVIOUS_SUPPORT_WEIGHT_LB
                        + spec.PREVIOUS_HARDWARE_AND_PAINT_RESERVE_LB)
    materials = tuple(
        material.model_copy(update={"areal_density_kg_m2": previous_mass_lb / 2.2046226218
                                    / (spec.NET_PANEL_AREA_IN2 * 0.0254**2)})
        if material.tag == "entry-screen-white-mdo" else material
        for material in plan.library.materials)
    return plan.model_copy(update={"library": plan.library.model_copy(update={"materials": materials})})


def build_report(context, before):
    from scripts.garage_service_door_clearance import service_door_clearance

    pressure = roof_winds(context.engineering.context)["RF-BW-CANOPY"].pressure_psf
    checks = local_timber_checks(pressure)
    results = service_door_clearance(context.model)
    minimum = min(results, key=lambda result: result.clearance_m)
    clearance_in = minimum.clearance_m / 0.0254
    checks.append({"name": "complete service-door sweep at authored stop including ply screws",
                   "status": "ok" if clearance_in >= 0.25 else "over",
                   "clearance_in": clearance_in, "minimum_in": 0.25,
                   "obstacle": minimum.obstacle, "ratio": 0.25 / clearance_in})
    checks.append({"name": "door sweep with installed end angles and SD9112 heads",
                   "status": "incomplete", "ratio": None,
                   "basis": "end connection geometry unresolved; only ply screws represented"})
    checks.append({"name": "concentrated total sill/hanger effects", "status": "incomplete",
                   "ratio": None, "basis": concentrated_sill_delta(context.model)["acceptance"]})
    after = load_summary(context)
    for record in after["structural_records"]:
        if record["status"] not in ("ok", "no_calc"):
            checks.append({"name": record["key"], **record})
    blocked = [row["name"] for row in checks if row["status"] != "ok"]
    return {
        "acceptance": "blocked" if blocked else "ok", "acceptance_blockers": blocked,
        "scope": "supplemental lower screen only; existing shear and upper-band model retained",
        "panel_cuts_in": [{"start": a, "end": b, "width": b - a,
                           "height": spec.FINISH_TOP_IN - spec.FINISH_BOTTOM_IN, "quantity": 1}
                          for a, b in spec.PANEL_RUNS_IN],
        "net_panel_area_sqft": spec.NET_PANEL_AREA_IN2 / 144,
        "previous_net_panel_area_sqft": spec.panel_net_area_in2(spec.PREVIOUS_PANEL_RUNS_IN) / 144,
        "supports": [asdict(support) for support in spec.SUPPORTS],
        "purchasing": spec.PURCHASING, "candidate_hardware_quantities": spec.HARDWARE_QUANTITIES,
        "support_weight_lb": spec.SUPPORT_WEIGHT_LB,
        "hardware_and_paint_reserve_lb": spec.HARDWARE_AND_PAINT_RESERVE_LB,
        "support_weight_delta_lb": spec.SUPPORT_WEIGHT_LB - spec.PREVIOUS_SUPPORT_WEIGHT_LB,
        "candidate_ply_screws": {"part": spec.PLY_SCREW_PART, "axes": "west, into side grain",
                                  "head_coordinates_in": spec.PLY_SCREWS,
                                  "thread_penetration_in": spec.PLY_SCREW_THREAD_IN},
        "end_connection_missing": spec.END_CONNECTION_MISSING,
        "wind_pressure_psf": pressure, "local_checks": checks,
        "concentrated_sill_effects": concentrated_sill_delta(context.model),
        "before": before, "after": after,
        "wall_reaction_delta_lb": {tag: load - before["wall_reaction_lb"].get(tag, 0)
                                   for tag, load in after["wall_reaction_lb"].items()},
        "door_sweep": {"stop_degrees": context.plan.by_tag("D-G-SERVICE").maximum_opening_degrees,
                       "minimum_clearance_in": clearance_in, "obstacle": minimum.obstacle,
                       "new_hardware_scope": "ply screw heads; end A35Z/SD9112 installation unresolved"},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    house = ROOT / "houses/catlin"
    loaded = load_plan(house)
    if loaded.plan is None:
        raise RuntimeError(loaded.findings)
    previous_context, _ = build_context(previous_weight_plan(loaded.plan), house)
    before = load_summary(previous_context)
    # Registry wind caches belong to the most recently built context, so construct the
    # final model last and finish its report before building another variant.
    context, _ = build_context(loaded.plan, house)
    report = build_report(context, before)
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload)
    print(payload, end="")
    return 1 if report["acceptance"] != "ok" else 0


if __name__ == "__main__":
    sys.exit(main())
