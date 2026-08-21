"""``GPart.catalog``: the raw catalog ref the folded finish key throws away."""

from __future__ import annotations

from typehaus.emit.finishes import layer_material_key


def _parts(model, kind: str):
    return [(element, part) for element in model.geometry.elements
            if element.kind == kind for part in element.parts]


def test_wall_layers_carry_their_raw_material_ref(catlin_model):
    """The detail's whole job is telling polyiso from EPS; ``material_key`` cannot.

    Both fold to ``"rigid"`` through ``family_of``, which is right for a viewer material and
    useless for a hatch.
    """
    refs = {part.catalog.material_ref for (_e, part) in _parts(catlin_model, "wall")
            if part.catalog is not None and part.catalog.material_ref}
    assert {"polyiso", "eps"} <= refs
    assert layer_material_key("polyiso", "insulation") == \
           layer_material_key("eps", "insulation")


def test_every_wall_layer_part_is_catalogued(catlin_model):
    for (element, part) in _parts(catlin_model, "wall"):
        assert part.catalog is not None, f"{element.uid}/{part.key}"
        assert part.catalog.name and part.key.endswith(part.catalog.name)
        assert part.catalog.role
        assert part.catalog.thickness_m is not None and part.catalog.thickness_m > 0


def test_roof_bands_and_members_and_decks_are_catalogued(catlin_model):
    roof_refs = {part.catalog.material_ref for (_e, part) in _parts(catlin_model, "roof")
                 if part.catalog is not None}
    assert "standing-seam" in roof_refs

    members = [(element, part) for (element, part) in _parts(catlin_model, "framing")]
    assert members
    for (element, part) in members:
        assert part.catalog is not None, f"{element.uid}/{part.key}"
        assert part.catalog.profile, f"{element.uid}/{part.key} has no profile"

    decks = _parts(catlin_model, "floor")
    assert decks
    assert all(part.catalog is not None and part.catalog.role == "sheathing"
               for (_e, part) in decks)


def test_a_solid_reports_what_it_is_made_of_not_concrete(catlin_model):
    """``section._solid_material``'s walk, moved into the resolver.

    Every solid used to hatch as concrete in section — right for a footing, wrong for a
    composite deck, an aluminium extrusion or a glass baluster panel.
    """
    by_category: dict[str, set[str]] = {}
    for element in catlin_model.geometry.elements:
        solid = next((s for s in catlin_model.solids if s.uid == element.uid), None)
        if solid is None:
            continue
        for part in element.parts:
            if part.catalog is not None and part.catalog.material_ref:
                by_category.setdefault(solid.category, set()).add(part.catalog.material_ref)
    assert by_category, "no solids carried a catalog ref"
    assert by_category.get("footing") == {"concrete"}   # the blanket rule's one right case
    # A composite/aluminium deck is a "slab" category and is not concrete; a polycarbonate
    # glazing panel is not concrete either. Both hatched as concrete before this walk moved.
    assert by_category.get("slab", set()) - {"concrete"}
    assert "concrete" not in by_category.get("glazing", set())


def test_catalog_does_not_reach_model_json(catlin_model):
    """Deliberately not mirrored: a TS type for it is a fifth surface to keep in sync.

    ``test_model_json.py`` would demand one the moment the key appeared.
    """
    from typehaus.server.model_json import model_to_dict

    payload = model_to_dict(catlin_model)
    parts: list[dict] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            if "material_key" in node or "member_uid" in node:
                parts.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    assert not [p for p in parts if "catalog" in p], "GPart.catalog leaked into model.json"
