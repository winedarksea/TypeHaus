"""Geometry of winder deck support, tier bearing, and concentrated floor reactions."""

from __future__ import annotations

from types import SimpleNamespace

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from typehaus.checks._authoring import structural_advisory
from typehaus.checks.registry import Tier, check
from typehaus.checks.structural.stairs import _bearing_element_under
from typehaus.findings import Result, not_applicable
from typehaus.model.floors import FloorSystem
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section

CHECK_ID = "structural.winder_box_support"
CONTACT_TOLERANCE_M = 1e-6
AREA_TOLERANCE_M2 = 1e-7


def winder_support_problems(stair, authored, model) -> list[str]:
    problems = []
    previous = None
    previous_top = None
    previous_supports = None
    spec = authored.winder_framing
    for index in range(stair.winder_count):
        decks = [m for m in stair.members
                 if m.child_key.startswith(f"stair-subdeck-{index:03d}-")]
        frames = [m for m in stair.members if m.child_key.startswith(
            (f"landing-rim-winder{index}-", f"landing-joist-winder{index}-"))]
        if not decks or not frames:
            problems.append(f"box {index + 1} is missing its deck or framing")
            continue
        deck = unary_union([Polygon(m.plan_outline) for m in decks])
        supports = unary_union([Polygon(m.plan_outline) for m in frames])
        buffered = supports.buffer(CONTACT_TOLERANCE_M)
        if any(not buffered.covers(Polygon(m.plan_outline).boundary) for m in decks):
            problems.append(f"box {index + 1} has an unsupported plywood edge or seam")
        if any(abs(m.z0_m - frames[0].z1_m) > CONTACT_TOLERANCE_M for m in decks):
            problems.append(f"box {index + 1} plywood does not contact its framing")
        if any(abs(m.z1_m - m.z0_m - spec.subdeck_thickness.meters)
               > CONTACT_TOLERANCE_M for m in decks):
            problems.append(f"box {index + 1} plywood thickness differs from its specification")
        oak = next(m for m in stair.members if m.child_key == f"winder-{index:03d}")
        if abs(oak.z0_m - decks[0].z1_m) > CONTACT_TOLERANCE_M:
            problems.append(f"box {index + 1} oak does not contact its plywood")
        if previous is not None:
            if any(abs(m.z0_m - previous_top) > CONTACT_TOLERANCE_M for m in frames):
                problems.append(f"box {index + 1} is not seated on the preceding plywood")
            if supports.difference(previous.buffer(CONTACT_TOLERANCE_M)).area > AREA_TOLERANCE_M2:
                problems.append(f"box {index + 1} bearing extends beyond the preceding plywood")
            if any(not previous_supports.covers(LineString((m.p0, m.p1)))
                   for m in frames if m.child_key.startswith("landing-rim-")):
                problems.append(f"box {index + 1} rim bearing line lacks blocking "
                                "below its plywood")
        else:
            floors = [floor for floor in model.floors if floor.storey == stair.storey
                      and floor.deck_outline and Polygon(floor.deck_outline).covers(deck)]
            if not floors or all(abs(f.deck_top_at(*deck.centroid.coords[0]) - frames[0].z0_m)
                                 > CONTACT_TOLERANCE_M for f in floors):
                problems.append("first box is not seated on the modeled structural floor")
        voids = deck.difference(buffered)
        pieces = [voids] if isinstance(voids, Polygon) else list(getattr(voids, "geoms", ()))
        nx, ny = stair.winder_turn.normals[0]
        stock_width = cross_section(spec.rim_profile).width_m
        for piece in pieces:
            if not isinstance(piece, Polygon) or piece.area <= AREA_TOLERANCE_M2:
                continue
            stations = [x * nx + y * ny for x, y in piece.exterior.coords]
            if max(stations) - min(stations) + stock_width > (
                    spec.support_spacing.meters + CONTACT_TOLERANCE_M):
                problems.append(f"box {index + 1} exceeds its maximum support spacing")
                break
        previous, previous_top = deck, decks[0].z1_m
        previous_supports = buffered
    departing = [m for m in stair.members if m.child_key.startswith(
        f"landing-rim-winder{stair.winder_count - 1}-") and "-ply" in m.child_key]
    if spec.departing_rim_plies > 1 and len(departing) != spec.departing_rim_plies:
        problems.append("departing rim does not contain its specified plies")
    for member in stair.members:
        if member.category != "stringer":
            continue
        rim = next((m for m in departing if Polygon(m.plan_outline).buffer(
            CONTACT_TOLERANCE_M).covers(Point(member.p0))), None)
        if rim is None or min(member.z1_m, rim.z1_m) <= max(member.z0_m, rim.z0_m):
            problems.append(f"{member.child_key} does not meet the departing rim")
    for post in (m for m in stair.members if m.category == "newel"):
        if _bearing_element_under(SimpleNamespace(model=model), post.p0, post.z0_m):
            continue
        reinforced = False
        for floor in model.floors:
            floor_spec = model.plan.by_tag(floor.tag)
            if floor.storey != stair.storey or not isinstance(floor_spec, FloorSystem):
                continue
            for index, reinforcement in enumerate(floor_spec.reinforcements):
                if reinforcement.plies < 2 or not reinforcement.blocking:
                    continue
                members = [m for m in floor.members if m.child_key.startswith(f"sister-{index}-")]
                geometry = unary_union([Polygon(member_footprint(m)[0]) for m in members])
                if geometry.buffer(CONTACT_TOLERANCE_M).covers(Point(post.p0)):
                    reinforced = True
        if not reinforced:
            problems.append(f"{post.child_key} has no wall, beam, slab, "
                            "or reinforced floor load path")
    return problems


@check(Tier.STRUCTURAL, CHECK_ID)
def winder_box_support(ctx):
    out = []
    for stair in ctx.model.stairs:
        if stair.winder_turn is None:
            continue
        problems = winder_support_problems(stair, ctx.plan.by_tag(stair.tag), ctx.model)
        out.append(structural_advisory(
            CHECK_ID, f"{stair.tag}: " + ("; ".join(problems) if problems else
            "plywood edges/seams supported; tiers bear on structural decks; "
            "stringers meet departing rim; newel reaction has a load path"),
            (stair.tag,), Result.FAIL if problems else Result.PASS))
    return out or [not_applicable(CHECK_ID, "no winder platform boxes")]
