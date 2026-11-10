"""Grounding electrodes and bonds, resolved (decision #123).

Declare once (``GroundingStandard``), author the electrodes and bonds, derive the rest:

* a rod resolves its absolute z span;
* a concrete-encased electrode resolves its QUALIFYING bar length off ``model.rebar``: the
  longest line of bars on a footing (pieces summed, laps once) that is #4 or larger, black
  or HDG A767/A1094 (epoxy, stainless and GFRP are out) at 2" or more of bottom cover, summed
  through the ``BarSpec.continues_into`` chain the electrode bar is tied across;
* its earth contact: a foundation-wall host behind insulation is ``no``; a footing on a
  geotextile bed or under side foam is ``ahj`` (NEC 250.52(A)(3) says "in direct contact with
  the earth", and whether a drained bed is that is the inspector's reading);
* a bond resolves its length off its path (plus legs to authored elevations), or the
  straight 3D distance between its two ends, tagged ``straight_line``. No slack is added;
* bonding SYSTEMS are the connected components of the bond graph; the root is the one
  holding the service disconnect (the METER-kind device whose type states ``service_amps``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from typehaus.findings import Finding, Result, Severity

_CID = "integrity.grounding_standard"
_IN = 0.0254
#: Bare conductor outside diameter, inches (Class B stranded; NEC Ch. 9 Table 8).
AWG_OD_IN: dict[str, float] = {"8": 0.146, "6": 0.184, "4": 0.232, "3": 0.260, "2": 0.292,
                               "1": 0.332, "1/0": 0.372, "2/0": 0.418, "3/0": 0.470,
                               "4/0": 0.528}
#: Coatings 250.52(A)(3) accepts: "bare, galvanized, or other electrically conductive coated".
CONDUCTIVE_COATINGS = frozenset({"black", "hdg-a767", "hdg-a1094"})
MIN_COVER_M = 2 * _IN
_FACETS = 8


@dataclass(frozen=True)
class ResolvedElectrode:
    uid: str
    tag: str
    storey: str
    building: str
    kind: str
    use: str
    xy: tuple[float, float]
    z_top_m: float
    z_bottom_m: float
    length_m: float  # rod: driven length; concrete-encased: qualifying bar; ring: its path
    host_tag: str | None = None
    footings: tuple[str, ...] = ()  # concrete-encased: the chain its bar runs through
    bar: int | None = None
    coating: str | None = None
    excluded: tuple[str, ...] = ()  # why bars on the host did not qualify
    earth_contact: str = "yes"  # yes | no | ahj
    earth_reason: str = ""


@dataclass(frozen=True)
class ResolvedBond:
    uid: str
    tag: str
    storey: str
    building: str
    role: str
    from_ref: str
    to_ref: str
    size: str
    material: str
    bare: bool
    path: tuple[tuple[float, float, float], ...]
    length_m: float
    length_basis: str  # "path" | "straight_line" | "unlocated"


@dataclass
class ResolvedGrounding:
    standard: Any | None = None
    electrodes: list[ResolvedElectrode] = field(default_factory=list)
    bonds: list[ResolvedBond] = field(default_factory=list)
    #: Connected components of the bond graph, each a frozenset of tags.
    systems: list[frozenset[str]] = field(default_factory=list)
    #: The service disconnect's tag (the root), or None.
    root: str | None = None
    #: Footing tag -> qualifying electrode-grade bar length on it (any role), metres.
    footing_bar_m: dict[str, float] = field(default_factory=dict)

    def system_of(self, tag: str) -> frozenset[str]:
        return next((s for s in self.systems if tag in s), frozenset({tag}))

    @property
    def root_system(self) -> frozenset[str]:
        return self.system_of(self.root) if self.root else frozenset()

    def electrode(self, tag: str) -> ResolvedElectrode | None:
        return next((e for e in self.electrodes if e.tag == tag), None)


def service_root(plan: Any) -> str | None:
    """The service disconnect: a METER-kind device whose type states ``service_amps``."""
    types = {t.tag: t for t in plan.library.electrical_device_types}
    for el in plan.elements_of_kind("ElectricalDevice"):
        if getattr(el.kind, "value", None) != "meter":
            continue
        if getattr(types.get(el.type_ref or ""), "service_amps", None):
            return el.tag
    return None


def resolve_grounding(model: Any) -> list[Finding]:
    plan = model.plan
    out = ResolvedGrounding()
    findings = _standard_findings(plan)
    standards = [el for el in plan.all_elements() if el.element_kind == "GroundingStandard"]
    out.standard = standards[0] if len(standards) == 1 else None
    out.root = service_root(plan)
    lines = _electrode_lines(model)
    out.footing_bar_m = {tag: max((qual for qual, _bar, _coat in group), default=0.0)
                         for tag, (group, _ex) in lines.items()}
    places: dict[str, tuple[float, float, float]] = {}
    for storey_tag, elements in plan.elements.items():
        for el in elements:
            if el.element_kind == "GroundingElectrode":
                rec = _electrode(model, el, storey_tag, out.standard, lines)
                out.electrodes.append(rec)
                places[rec.tag] = (*rec.xy, rec.z_top_m)
    for storey_tag, elements in plan.elements.items():
        for el in elements:
            if el.element_kind == "BondingConductor":
                out.bonds.append(_bond(model, el, storey_tag, places))
    out.systems = _components(out)
    model.grounding = out
    _emit_solids(model, out)
    return findings


def _standard_findings(plan: Any) -> list[Finding]:
    found = [el for el in plan.all_elements() if el.element_kind == "GroundingStandard"]
    if len(found) > 1:
        tags = tuple(sorted(el.tag for el in found))
        return [Finding(severity=Severity.ERROR, check_id=_CID, result=Result.FAIL,
                        message=f"a house declares at most one GroundingStandard; found "
                                f"{len(found)}: {', '.join(tags)}", element_tags=tags)]
    out = []
    for standard in found:
        for ref in standard.product_refs():
            if plan.library.product(ref) is None:
                out.append(Finding(severity=Severity.ERROR, check_id=_CID, result=Result.FAIL,
                                   message=f"grounding standard {standard.tag} names no "
                                           f"product {ref!r}", element_tags=(standard.tag,)))
    return out


def _electrode_lines(model: Any) -> dict[str, tuple[list[tuple[float, int, str]], list[str]]]:
    """Footing tag -> ([(qualifying line length m, bar, coating)], [exclusion reasons])."""
    solids = {s.tag: s for s in model.solids if s.category == "footing"}
    out: dict[str, tuple[list[tuple[float, int, str]], list[str]]] = {}
    for bars in model.rebar:
        if bars.host_kind != "Footing" or bars.host_tag not in solids:
            continue
        z0 = solids[bars.host_tag].z0_m
        lines: dict[tuple, list] = {}
        excluded: list[str] = []
        for bar in bars.bars:
            if bar.role != "electrode" and not bar.role.startswith("bottom-"):
                continue
            if bar.bar < 4:
                excluded.append(f"#{bar.bar} is smaller than #4 (1/2 in)")
                continue
            if bar.coating not in CONDUCTIVE_COATINGS:
                excluded.append(f"{bar.coating} bar is not an electrically conductive coating")
                continue
            low = min(p[2] for p in bar.path) - bar.diameter_m / 2
            if low - z0 < MIN_COVER_M - 1e-4:
                excluded.append(f"{(low - z0) / _IN:.2f} in of bottom cover is under 2 in")
                continue
            lines.setdefault(_line_key(bar.path), []).append(bar)
        group = [(sum(b.placed_length_m for b in line), line[0].bar, line[0].coating)
                 for line in lines.values()]
        out[bars.host_tag] = (group, sorted(set(excluded)))
    return out


def _line_key(path) -> tuple:
    """One straight bar line: its direction (mod pi) and perpendicular offset, to 1 cm."""
    (x0, y0, _), (x1, y1, _) = path[0], path[-1]
    angle = math.atan2(y1 - y0, x1 - x0) % math.pi
    ux, uy = math.cos(angle), math.sin(angle)
    return (round(angle, 2), round(x0 * uy - y0 * ux, 2))


def _chain(plan: Any, host: str) -> tuple[str, ...]:
    """The footings an electrode bar is tied through, by ``continues_into``, host first."""
    seen: list[str] = []
    todo = [host]
    while todo:
        tag = todo.pop(0)
        if tag in seen:
            continue
        seen.append(tag)
        spec = getattr(plan.by_tag(tag), "reinforcement", None)
        for entry in getattr(spec, "bars", ()):
            if entry.role == "electrode":
                todo.extend(entry.continues_into or ())
    return tuple(seen)


def _electrode(model: Any, el: Any, storey: str, standard: Any, lines) -> ResolvedElectrode:
    plan = model.plan
    building = plan.building_of(storey)
    xy = el.position.xy_m
    top = el.top_elevation.meters
    common = dict(uid=el.uid, tag=el.tag, storey=storey, building=building, kind=el.kind,
                  use=el.use, xy=xy, z_top_m=top, host_tag=el.host_ref)
    if el.kind == "concrete_encased" and el.host_ref:
        chain = _chain(plan, el.host_ref)
        total, bar, coating, excluded = 0.0, None, None, []
        for tag in chain:
            group, ex = lines.get(tag, ([], []))
            excluded.extend(ex)
            if group:
                best = max(group)
                total += best[0]
                bar, coating = bar or best[1], coating or best[2]
        contact, reason = _earth_contact(plan, chain)
        solids = {s.tag: s for s in model.solids if s.tag in chain}
        bottom = min((s.z0_m for s in solids.values()), default=top)
        return ResolvedElectrode(**common, z_bottom_m=bottom, length_m=total, footings=chain,
                                 bar=bar, coating=coating, excluded=tuple(sorted(set(excluded))),
                                 earth_contact=contact, earth_reason=reason)
    length = (el.length.meters if el.length is not None
              else standard.rod_length.meters if standard is not None else 0.0)
    if el.kind == "ring":
        return ResolvedElectrode(**common, z_bottom_m=top, length_m=length)
    return ResolvedElectrode(**common, z_bottom_m=top - length, length_m=length)


def _earth_contact(plan: Any, chain: tuple[str, ...]) -> tuple[str, str]:
    hosts = [plan.by_tag(tag) for tag in chain]
    for host in hosts:
        if host is not None and host.element_kind in ("FoundationWall", "Wall"):
            return "no", f"{host.tag} is a wall; its earth face is behind insulation"
    beds = [el for el in plan.elements_of_kind("FootingBedding") if el.host_ref in chain]
    notes = []
    if any(bed.geotextile for bed in beds):
        notes.append("bears on washed stone over geotextile")
    if any(bed.perimeter_insulation for bed in beds):
        notes.append("side foam on the footing faces")
    if notes:
        return "ahj", ("the footing " + " with ".join(notes)
                       + "; direct earth contact is the AHJ's reading")
    return "yes", ""


def _endpoint(model: Any, tag: str, places, toward=None) -> tuple[float, float, float] | None:
    if tag in places:
        return places[tag]
    for obj in model.canvas_objects:
        if obj.tag == tag:
            return (obj.position[0], obj.position[1], obj.z_m)
    for run in model.pipe_runs:
        if run.tag == tag and run.path:
            zs = run.z_m or [run.z_start_m or 0.0] * len(run.path)
            pts = [(p[0], p[1], z) for p, z in zip(run.path, zs, strict=False)]
            if toward is None:
                return pts[0]
            return min(pts, key=lambda p: math.dist(p[:2], toward[:2]))
    return None


def _bond(model: Any, el: Any, storey: str, places) -> ResolvedBond:
    building = model.plan.building_of(storey)
    common = dict(uid=el.uid, tag=el.tag, storey=storey, building=building, role=el.role,
                  from_ref=el.from_ref, to_ref=el.to_ref, size=el.size, material=el.material,
                  bare=el.bare)
    if len(el.path) >= 2:
        xy = [p.xy_m for p in el.path]
        if el.elevations is not None and len(el.elevations) == len(xy):
            zs = [z.meters for z in el.elevations]
        else:
            a = _endpoint(model, el.from_ref, places)
            zs = [a[2] if a else 0.0] * len(xy)
        pts = tuple((x, y, z) for (x, y), z in zip(xy, zs, strict=False))
        length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        return ResolvedBond(**common, path=pts, length_m=length, length_basis="path")
    a = _endpoint(model, el.from_ref, places)
    b = _endpoint(model, el.to_ref, places, toward=a)
    if a is not None and b is not None:
        a = _endpoint(model, el.from_ref, places, toward=b) or a
        return ResolvedBond(**common, path=(a, b), length_m=math.dist(a, b),
                            length_basis="straight_line")
    return ResolvedBond(**common, path=(), length_m=0.0, length_basis="unlocated")


def _components(out: ResolvedGrounding) -> list[frozenset[str]]:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in out.electrodes:
        find(e.tag)
    for bond in out.bonds:
        parent[find(bond.from_ref)] = find(bond.to_ref)
        find(bond.tag)
        parent[find(bond.tag)] = find(bond.to_ref)
    groups: dict[str, set[str]] = {}
    for tag in list(parent):
        groups.setdefault(find(tag), set()).add(tag)
    return sorted((frozenset(g) for g in groups.values()), key=lambda g: sorted(g)[0])


def _emit_solids(model: Any, out: ResolvedGrounding) -> None:
    from typehaus.resolve.mep import _emit_run_solids
    from typehaus.resolve.sweep import round_profile

    std = out.standard
    rod_r = (std.rod_diameter.meters / 2) if std is not None else 0.3125 * _IN
    for e in out.electrodes:
        if e.kind != "rod":
            continue
        path = [e.xy, e.xy]
        _emit_run_solids(model, e.uid, e.tag, e.storey, path, [e.z_top_m, e.z_bottom_m],
                         round_profile(rod_r, _FACETS), "grounding_electrode")
    for bond in out.bonds:
        if bond.length_basis != "path":  # a straight-line bond is the electrician's route
            continue
        r = AWG_OD_IN.get(bond.size, 0.25) * _IN / 2
        _emit_run_solids(model, bond.uid, bond.tag, bond.storey,
                         [p[:2] for p in bond.path], [p[2] for p in bond.path],
                         round_profile(max(r, 0.004), _FACETS), "grounding_conductor")

