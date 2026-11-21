"""Every authored fastening spec, as S-001 lists it (decision #147).

Built from the authored fields, not from the counts: sheathing and subfloor nailing
(``Layer.nailing``, ``DeckLayer.nailing``), concealed panel screws, trim fastening, window
install fastening and the girt and sill-seat screws. A spec citing a ``code_row`` restates
the code and folds into one general note line; the rest are listed.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.hardware.catalog import hardware_by_model
from typehaus.model.floors import FloorSystem
from typehaus.resolve.model import ResolvedModel


@dataclass(frozen=True)
class FasteningSpec:
    use: str
    part: str
    finish: str
    spacing: str
    code_row: str = ""
    source: str = ""


def _finish(part: str) -> str:
    item = hardware_by_model(part)
    return (item.finish or "") if item is not None and item.model == part else ""


def _assemblies_in_use(model: ResolvedModel) -> list[str]:
    return sorted({tag for element in model.plan.all_elements()
                   if isinstance(tag := getattr(element, "assembly", None), str) and tag})


def _nailing(spec, host: str) -> FasteningSpec:
    edges = "all panel edges" if spec.blocked else "supported edges"
    return FasteningSpec(
        use=host, part=spec.part, finish=_finish(spec.part),
        spacing=f'{spec.edge_oc_in:g}" {edges} / {spec.field_oc_in:g}" field',
        code_row=spec.code_row, source=spec.source)


def fastening_specs(model: ResolvedModel) -> list[FasteningSpec]:
    """One entry per distinct spec; ``use`` names every host that carries it."""
    library = model.plan.library
    found: dict[tuple, tuple[FasteningSpec, set[str]]] = {}

    def add(spec: FasteningSpec, host: str) -> None:
        key = (spec.part, spec.spacing, spec.code_row, spec.source)
        found.setdefault(key, (spec, set()))[1].add(host)

    used_materials: set[str] = set()
    for tag in _assemblies_in_use(model):
        assembly = library.resolve_assembly(tag)
        for layer in assembly.layers if assembly else ():
            used_materials.add(layer.material_ref)
            if layer.nailing is not None:
                # By assembly: one material (CDX) is a wall at 6"/12" and a roof at 4"/4".
                add(_nailing(layer.nailing, ""), f"{tag} {layer.name}")
            framing = getattr(layer, "framing", None)
            if framing is not None and framing.standoff_fastener_part:
                add(FasteningSpec("", framing.standoff_fastener_part,
                                  _finish(framing.standoff_fastener_part),
                                  "one per block crossing, through girt + block + sheathing",
                                  source=framing.standoff_fastener_source or ""),
                    "girt to stud")
            course = getattr(framing, "sill_course", None) if framing is not None else None
            if course is not None:
                add(FasteningSpec("", course.fastener_part, _finish(course.fastener_part),
                                  f"{course.seat_rows} rows x {course.screws_per_row} per seat",
                                  source=course.source), "door sill beam seat to rim")
    for storey in model.plan.storeys:
        for system in model.plan.storey_elements(storey.tag):
            if isinstance(system, FloorSystem) and system.subfloor is not None:
                used_materials.add(system.subfloor.material_ref)
                if system.subfloor.nailing is not None:
                    add(_nailing(system.subfloor.nailing, ""),
                        f"{system.subfloor.material_ref} subfloor")
    for material in library.materials:
        if material.panel_fastener_part and material.tag in used_materials:
            pitch = (f'{material.panel_fastener_pitch_in:g}" along the fastened edge'
                     if material.panel_fastener_pitch_in else "one per support crossing")
            add(FasteningSpec("", material.panel_fastener_part,
                              _finish(material.panel_fastener_part), pitch),
                f"{material.tag} panel")
        if material.trim_fastening is not None:
            trim = material.trim_fastening
            add(FasteningSpec("", trim.part, _finish(trim.part),
                              f'{trim.rows} per {trim.pitch_in:g}" and at each end',
                              trim.code_row, trim.source), f"{material.tag} trim")
    placed = {o.type_ref for o in model.openings if o.kind == "window"}
    for kind in library.window_types:
        spec = kind.install_fastening
        if spec is not None and kind.tag in placed:
            add(FasteningSpec("", spec.part, _finish(spec.part),
                              f'fin {spec.fin_pitch_in:g}", {spec.corner_offset_in:g}" '
                              "off corners", spec.code_row, spec.source),
                f"{kind.tag} install")
    return [FasteningSpec(", ".join(sorted(hosts)), spec.part, spec.finish, spec.spacing,
                          spec.code_row, spec.source)
            for spec, hosts in sorted(found.values(), key=lambda item: item[0].part)]
