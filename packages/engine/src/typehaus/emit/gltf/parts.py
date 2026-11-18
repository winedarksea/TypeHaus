"""Self-contained glTF part builders: the floor deck, the site earth, light runs, PV
modules and alarm heads. Each writes one source object's triangles into a :class:`_MeshBuilder`."""

from __future__ import annotations

from typehaus.emit.gltf.geometry import _to_gltf
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _color, _material_finish_color
from typehaus.resolve.geometry import light_run_shells
from typehaus.resolve.geometry_ir import GBox, GPrism
from typehaus.resolve.model import ResolvedModel


def _ir_part(model: ResolvedModel, uid: str, key: str):
    """One named part of one IR element, or ``None`` if the model carries no geometry."""
    geometry = getattr(model, "geometry", None)
    return geometry.part(uid, key) if geometry is not None else None


def _add_deck(mb: _MeshBuilder, model: ResolvedModel, floor) -> None:
    """A floor's subfloor sheet, cut by its stair/chase openings.

    Colour follows the deck's *material* the way a wall layer's does — the IR names it
    ``sheathing`` and the exporter decides what sheathing reads as.
    """
    part = _ir_part(model, floor.uid, "deck")
    if part is None:
        return
    color = _material_finish_color(getattr(floor, "deck_material_ref", None), "sheathing")
    for prism in part.solids:
        if isinstance(prism, GBox):  # a tilted deck's plane
            mb.add_gbox(prism, color)
            continue
        mb.add_prism_with_rectangular_voids(list(prism.ring), prism.voids,
                                            prism.z0_m, prism.z1_m, color)


def _add_earth(mb: _MeshBuilder, model: ResolvedModel) -> None:
    """The site earth sheet: the parcel at grade, cut by everything excavated out of it.

    The tone is the viewer's soil brown, but opaque: the viewer's translucency is a
    depth-sorted overlay trick that an importer has no equivalent for, and a see-through
    ground imports into Revit/SketchUp as a puzzle rather than a site.
    """
    part = _ir_part(model, "site-earth", "sheet")
    if part is None:
        return
    for prism in part.solids:
        mb.add_prism_with_rectangular_voids(list(prism.ring), prism.voids,
                                            prism.z0_m, prism.z1_m, _color("earth"))


_LIGHT_RUN_BAND_ROLE = {"back": "cove_channel", "base": "cove_channel", "lip": "cove_channel",
                        "body": "cove_channel", "tape": "led_tape", "lens": "cove_lens",
                        "flange": "cove_flange", "endcap": "cove_channel"}


def _add_light_run(mb: _MeshBuilder, run) -> None:
    """The run's swept section, one prism per part per leg (→ resolve/geometry.py
    ``light_run_section_shells``; the viewer sweeps the same parts from model.json)."""
    for key, faces in light_run_shells(run):
        triangles = []
        for face in faces:
            quad = [_to_gltf(*point) for point in face]
            triangles.append((quad[0], quad[1], quad[2]))
            triangles.append((quad[0], quad[2], quad[3]))
        mb.add_triangles(triangles, _color(_LIGHT_RUN_BAND_ROLE[key]))


def _add_solar_panel(mb: _MeshBuilder, panel) -> None:
    """The resolver's tilted box as triangles — bottom, top, and four side quads."""
    bottom = [_to_gltf(*point) for point in panel.corners_bottom]
    top = [_to_gltf(*point) for point in panel.corners_top]
    color = _color("solar")
    triangles = [
        (bottom[2], bottom[1], bottom[0]), (bottom[3], bottom[2], bottom[0]),
        (top[0], top[1], top[2]), (top[0], top[2], top[3]),
    ]
    for index in range(len(bottom)):
        following = (index + 1) % len(bottom)
        quad = (bottom[index], bottom[following], top[following], top[index])
        triangles.append((quad[0], quad[1], quad[2]))
        triangles.append((quad[0], quad[2], quad[3]))
    mb.add_triangles(triangles, color)


def _add_alarm_head(mb: _MeshBuilder, head) -> None:
    """The resolved head body (→ resolve/alarm_heads.py), the prism the viewer and IFC draw."""
    for prism in head.body.solids:
        if isinstance(prism, GPrism):
            mb.add_prism(list(prism.ring), prism.z0_m, prism.z1_m, _color(f"alarm_{head.kind}"))
