"""Thin parts printed as part of their hosts instead of being dropped (decision #106).

A countertop is fused to the casework it sits on, a ceiling to the floor package it hangs
from, and a placeable hung on a fixture, a wall or a countertop run to that host. Hosts come
from ownership the model already states — the countertop's ``hosts``, a placeable's
``host_fixture_ref``/``attachment_wall`` — or from geometry for a ceiling: the floor or slab
package whose underside its top touches, by most plan overlap. Never from a tag prefix.

A fused part thinner than its minimum grows toward its host to that minimum, its exposed
face fixed: the growth goes into the host, so no cap applies and the part keeps its look.
The merged item takes its host's kind and treatment, so a ceiling lowers its floor's cut.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace

from typehaus.print3d.collect import PrintItem
from typehaus.print3d.policy import PrintSettings, Treatment
from typehaus.resolve.model import ResolvedModel
from typehaus.solids3d.convert import union

#: The packages a ceiling may hang from.
CEILING_HOST_KINDS = frozenset({"floor", "slab", "slab_band", "slab_platform"})
#: A ceiling's top within this of a package's underside touches it, metres.
CONTACT_M = 0.005
#: A plan overlap smaller than this is an edge touch, not support, m².
MIN_OVERLAP_M2 = 0.01


def merge_into_hosts(model: ResolvedModel, house: list[PrintItem], loose: list[PrintItem],
                     mm_per_m: float, settings: PrintSettings,
                     ) -> tuple[list[PrintItem], list[PrintItem], Counter]:
    """(house, loose, merged kind -> count): each part unioned into one host's item."""
    items = {item.uid: item for item in [*house, *loose]}
    hosts = _host_map(model, house, loose)

    def owner_of(uid: str) -> str:
        while uid in hosts:
            uid = hosts[uid]
        return uid

    parts_of: dict[str, list[PrintItem]] = {}
    for uid in sorted(hosts):
        parts_of.setdefault(owner_of(uid), []).append(items[uid])
    fused = {}
    for owner_uid, parts in parts_of.items():
        host = items[owner_uid]
        solids = [host.solid, *(_grown(part, host, mm_per_m, settings) for part in parts)]
        fused[owner_uid] = replace(host, solid=union(solids))
    merged = Counter(items[uid].kind for uid in hosts)
    return ([fused.get(item.uid, item) for item in house if item.uid not in hosts],
            [item for item in loose if item.uid not in hosts], merged)


def _host_map(model: ResolvedModel, house: list[PrintItem], loose: list[PrintItem],
              ) -> dict[str, str]:
    """part uid -> the uid it fuses to (a house item, or a part that has one)."""
    house_items = {item.uid: item for item in house}
    loose_uids = {item.uid for item in loose}
    by_tag = {obj.tag: obj.uid for obj in model.canvas_objects}
    wall_uid = {wall.tag: wall.uid for wall in model.walls}
    hosts: dict[str, str] = {}
    for top in sorted(model.countertops, key=lambda record: record.uid):
        members = sorted({by_tag[tag] for tag in top.hosts if tag in by_tag})
        bases = [house_items[uid] for uid in members if uid in house_items]
        if top.uid not in house_items or not bases:
            continue
        hosts[top.uid] = max(bases, key=lambda item: (item.solid.volume(), item.uid)).uid
        # A loose member of the run (an end panel, a cover) prints with the slab.
        hosts.update({uid: top.uid for uid in members if uid in loose_uids})
    objects = {obj.uid: obj for obj in model.canvas_objects}
    for item in loose:
        obj = objects.get(item.uid)
        if obj is None or item.uid in hosts:
            continue
        owner = by_tag.get(obj.host_fixture_ref or "") or wall_uid.get(obj.attachment_wall or "")
        if owner in house_items:
            hosts[item.uid] = owner
    packages = [item for item in house if item.kind in CEILING_HOST_KINDS]
    for item in house:
        if item.kind == "ceiling":
            owner = _ceiling_host(item, packages)
            if owner is not None:
                hosts[item.uid] = owner.uid
    return hosts


def _ceiling_host(ceiling: PrintItem, packages: list[PrintItem]) -> PrintItem | None:
    """The package whose underside the ceiling's top touches, by most plan overlap."""
    x0, y0, _, x1, y1, top = ceiling.solid.bounding_box()
    footprint = None
    best: tuple[float, str, PrintItem] | None = None
    for package in packages:
        px0, py0, pz0, px1, py1, _ = package.solid.bounding_box()
        if abs(pz0 - top) > CONTACT_M or px0 >= x1 or x0 >= px1 or py0 >= y1 or y0 >= py1:
            continue
        footprint = footprint if footprint is not None else ceiling.solid.project()
        overlap = (footprint ^ package.solid.project()).area()
        if overlap >= MIN_OVERLAP_M2 and (best is None or (overlap, package.uid) > best[:2]):
            best = (overlap, package.uid, package)
    return best[2] if best is not None else None


def _grown(part: PrintItem, host: PrintItem, mm_per_m: float, settings: PrintSettings):
    """The part thickened along z toward its host to its minimum, the far face fixed."""
    if part.treatment is Treatment.LOOSE:
        return part.solid  # hung hardware: fused as drawn
    target_m = (settings.wall_mm if part.treatment is Treatment.BODY
                else settings.feature_mm) / mm_per_m
    _, _, z0, _, _, z1 = part.solid.bounding_box()
    if z1 - z0 >= target_m or z1 <= z0:
        return part.solid
    host_box = host.solid.bounding_box()
    toward_down = (host_box[2] + host_box[5]) / 2 < (z0 + z1) / 2
    anchor = z1 if toward_down else z0
    factor = target_m / (z1 - z0)
    return (part.solid.translate((0.0, 0.0, -anchor)).scale((1.0, 1.0, factor))
            .translate((0.0, 0.0, anchor)))
