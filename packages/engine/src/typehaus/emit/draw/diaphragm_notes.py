"""Construction fastening instructions for both sides of a declared roof joint."""

from typehaus.model import Roof


def diaphragm_framing_notes(model, roof):
    notes = []
    element = model.plan.by_tag(roof.tag)
    if isinstance(element, Roof) and element.diaphragm:
        spec = element.diaphragm
        notes.append(f"DIAPHRAGM DECK: {spec.fastening}.")
        for recipe in spec.collector_blocking:
            material = model.plan.library.material(recipe.material)
            wood = material.name if material else f"UNRESOLVED WOOD {recipe.material}"
            notes.append(f"COLLECTOR {recipe.collector}, {wood}: {recipe.fastening}")
        if spec.panel_edge_blocking:
            notes.append(_panel_note(model, spec.panel_edge_blocking, ""))
    for owner in model.plan.all_elements():
        if not isinstance(owner, Roof) or owner.diaphragm is None:
            continue
        delivery = owner.diaphragm.delivers_to
        if not (delivery and delivery.joint_nailing
                and roof.tag in (owner.tag, delivery.roof)):
            continue
        recipe = delivery.joint_nailing
        material = model.plan.library.material(recipe.material)
        wood = material.name if material else f"UNRESOLVED WOOD {recipe.material}"
        notes.append(f"JOINT {owner.tag} TO {delivery.roof}, {wood}: {recipe.fastening}")
        notes.append(f"JOINT ATTACHMENT BASIS: {recipe.source}.")
        # The owner's continuous first sheet course reaches this roof's first bay.
        panel = owner.diaphragm.panel_edge_blocking
        if roof.tag == delivery.roof and recipe.continuous_deck and panel:
            notes.append(_panel_note(model, panel, f" IN THE FIRST BAY, FROM {owner.tag}"))
    return notes


def _panel_note(model, panel, where):
    material = model.plan.library.material(panel.material)
    wood = material.name if material else f"UNRESOLVED WOOD {panel.material}"
    return (f"PANEL EDGE BLOCKS{where}, {wood}: {panel.stock} on edge, bevel top to deck; "
            f"{panel.module.fmt()} horizontal module from ridge on both slopes. Cut standard "
            "sheets to fit with 1/8in gaps; block every panel edge in every bay. "
            f"{panel.fastening}")
