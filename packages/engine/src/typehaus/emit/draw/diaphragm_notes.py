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
        if spec.panel_edge_blocking and spec.panel_width:
            notes.append(f"PANEL EDGE BLOCKS: {spec.panel_edge_blocking} on edge, bevel top "
                         f"to deck; {spec.panel_width.fmt()} horizontal module from ridge "
                         "on both slopes. Cut standard sheets to fit with 1/8in gaps; "
                         "block every panel edge in every bay.")
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
    return notes
