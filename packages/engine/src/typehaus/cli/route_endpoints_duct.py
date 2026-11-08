"""Endpoints for re-routing an authored duct or raceway: its own ends, kept.

A duct's size is authored and equal-friction sizing is advice only; a raceway's
elevations are project-frame absolute. Split from ``route_support``; docs/routing.md."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from typehaus.cli.route_metadata import run_metadata as _run_metadata
from typehaus.cli.route_miss import miss

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.cli.route_support import Endpoints
    from typehaus.resolve.model import ResolvedModel


def _duct_endpoints(model: ResolvedModel, duct: Any,
                    problems: list[str]) -> Endpoints | None:
    """Keep the duct's authored ends and allow contacts from the shared connectivity rule.

    An authored duct size wins; equal-friction sizing is advice only."""
    from typehaus.cli.route_support import Endpoints
    from typehaus.resolve.mep_envelopes import insulation_thickness_m, joinable
    from typehaus.resolve.mep_soffit import ducts_are_joined
    from typehaus.routing.trades import duct as duct_trade

    if len(duct.path) < 2 or len(duct.z_m) != len(duct.path):
        miss(problems, duct.tag, "fewer than two vertices or no resolved elevations, "
             "so it has no two ends to route between")
        return None
    lagging = insulation_thickness_m(duct.insulation)
    if lagging is None:
        miss(problems, duct.tag, "insulation states no thickness, so its routing "
             "envelope cannot be established")
        return None
    joined = {other.tag for other in model.ducts
              if other.tag != duct.tag and ducts_are_joined(model, duct.tag, other.tag)
              and joinable(model, duct.tag, other.tag)}
    width, depth = (0.0, 0.0) if duct.diameter_m else (duct.width_m, duct.depth_m)
    origin = _port_terminal(model, duct, 0)
    root = _port_terminal(model, duct, len(duct.path) - 1)
    return Endpoints(
        origin=origin, root=root, advice=_duct_size_advice(model, duct),
        kind="duct", radius_m=duct_trade.radius_m(
            diameter_m=duct.diameter_m, width_m=duct.width_m, depth_m=duct.depth_m) + lagging,
        diameter_m=duct.diameter_m or 0.0, width_m=width, depth_m=depth,
        storey=duct.storey, system=duct.system, falls=False,
        touch=frozenset({duct.tag, *joined}),
        echo=_run_metadata(model, duct.tag, ("material", "insulation", "design_cfm")))


def _conduit_endpoints(model: ResolvedModel, raceway: Any,
                       problems: list[str]) -> Endpoints | None:
    """A raceway keeps its ends too, and carries ``from_ref``/``to_ref`` through.

    Its elevations are **project-frame absolute**, so the proposal is printed at a datum of
    zero — see :func:`~typehaus.cli.cmd_route.route`. A run whose profile the model cannot
    reconstruct is refused rather than flattened: ``conduit_vertical_profile`` is the one
    reading of that, and a run it declines is a run whose z nobody authored.
    """
    from typehaus.cli.route_support import Endpoints
    from typehaus.model.enums import RacewayMaterial
    from typehaus.resolve.mep_queries import conduit_vertical_profile
    from typehaus.resolve.pipe_sections import raceway_outside_diameter_m

    profile = conduit_vertical_profile(raceway)
    if profile is None or len(raceway.path) < 2:
        miss(problems, raceway.tag, "no reconstructable vertical profile, so it has "
             "no elevation to route at", fix="Author start/end elevations on it")
        return None
    path, z = profile
    echo = {key: getattr(raceway, key) for key in ("from_ref", "to_ref", "circuits")
            if getattr(raceway, key, None)}
    if raceway.material != "emt":
        echo["material"] = RacewayMaterial(raceway.material)
    boxes = _pull_boxes(raceway)
    return Endpoints(
        origin=(path[0][0], path[0][1], z[0]), root=(path[-1][0], path[-1][1], z[-1]),
        kind="conduit",
        radius_m=raceway_outside_diameter_m(raceway.trade_size_m or 0.0,
                                            raceway.material) / 2.0,
        diameter_m=raceway.trade_size_m or 0.0, storey=raceway.storey,
        system=raceway.service or "", falls=False, echo=echo,  # "" is a capped spare
        touch=frozenset({raceway.tag}), pull_boxes=boxes)


def _pull_boxes(raceway: Any) -> tuple[tuple[float, float, float], ...]:
    """3D points of the run's authored pull vertices, at the z ``conduit_pulls`` grades."""
    from typehaus.resolve.conduit_pulls import _profile

    profile = _profile(raceway) if raceway.pull_points else None
    if profile is None:
        return ()
    points, indices, _schematic = profile
    return tuple(next(p for p, i in zip(points, indices, strict=True) if i == index)
                 for index in raceway.pull_points if index in indices)


def _port_terminal(model: ResolvedModel, duct: Any, index: int) -> tuple[float, float, float]:
    """Snap a duct end to its equipment's EXACT port; leave approximate ports unchanged.

    The 0.5 m tolerance covers a case's half-diagonal, not merely a joint, so loose ends
    inside a case reach the spigot without capturing the next machine."""
    from typehaus.resolve.mep_ports import port_at

    point = duct.path[index]
    z = duct.z_m[index]
    system = duct.system.value if hasattr(duct.system, "value") else str(duct.system)
    port = port_at(model, point, z, duct_system=system, tolerance_m=0.5)
    return (point[0], point[1], z) if port is None else port.point


def _duct_size_advice(model: ResolvedModel, duct: Any) -> tuple[str, ...]:
    """Compare round-duct equal-friction sizing with the authored size without changing it.

    Rectangular equivalent diameters are outside this reading. New branches use
    resolve.duct_sizing.size_for_cfm rather than inheriting an authored size."""
    from typehaus.resolve.duct_sizing import friction_rate_in_wg_per_100ft, size_for_cfm

    cfm = getattr(duct, "design_cfm", None)
    if not cfm or not duct.diameter_m:
        return ()
    rate = _friction_rate(model)
    want, basis = size_for_cfm(model.plan.library, cfm, material=duct.material,
                               rate_in_wg_per_100ft=rate)
    if want is None:
        return (f"sizing: {basis}",)
    if abs(want.nominal_m - duct.diameter_m) <= 1e-9:
        return (f"sizing: {duct.tag} is the size {cfm:.0f} cfm wants — {basis}",)
    from typehaus.quantities import M_PER_IN
    row = next((r for r in model.plan.library.duct_product_types
                if r.material == duct.material and r.nominal_diameter is not None
                and abs(r.nominal_diameter.meters - duct.diameter_m) <= 1e-6), None)
    drawn = (None if row is None else friction_rate_in_wg_per_100ft(
        cfm, row.bore_diameter.meters, row.roughness_m))
    at = "" if drawn is None else f", against {drawn:.3f} in. w.g./100 ft as drawn"
    return (f'sizing: {duct.tag} is drawn {duct.diameter_m / M_PER_IN:.3g}"; '
            f"{cfm:.0f} cfm at the {rate:.3f} in. w.g./100 ft design rate wants {basis}{at}. "
            "The authored size stands — this is the number, not a decision",)


def _friction_rate(model: ResolvedModel) -> float:
    """``[mep.routing] duct_friction_in_wg_per_100ft`` for this house, or the default."""
    from typehaus.resolve.duct_sizing import (
        DEFAULT_FRICTION_IN_WG_PER_100FT,
        friction_rate_from_preferences,
    )

    root = getattr(model.plan, "source_root", None)
    if root is None:
        return DEFAULT_FRICTION_IN_WG_PER_100FT
    from typehaus.checks import load_preferences

    return friction_rate_from_preferences(load_preferences(Path(root)).mep.routing)
