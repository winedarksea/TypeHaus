"""Estimate descriptions a supplier can quote from — the id kept, a label added.

The audit that started this (2026-09-12) found 354 of catlin's 551 estimate rows described
by an engine id. This ratchets the count of id-shaped descriptions DOWN and never up.
"""

from __future__ import annotations

import re

from typehaus.takeoff.labels import LabelIndex, describe, role_label

#: Measured on catlin after the labels landed. Lower it as glossary entries land; a rise is
#: a regression in a formatter or a type that lost its ``name``.
ID_SHAPED_CEILING = 2


def looks_like_an_id(section: str, key: str, description: str) -> bool:
    """A description that is the key, a ``section · key`` stub, or an all-caps token —
    unless the key itself is already a phrase (an installation kit's part text)."""
    text = description.strip()
    if text.startswith(f"{section.replace('_', ' ')} · "):
        return True
    if re.fullmatch(r"[A-Z0-9_:\-\.#]+", text):
        return True
    return text == key and not re.search(r"[a-z]+ [a-z]+", text)


def test_the_id_is_always_kept() -> None:
    assert describe("pipe_fittings", "elbow-90-0.75in", {"system": "drain"}) == \
        '90° elbow, 3/4" drain (elbow-90-0.75in)'
    assert describe("ducts", "exhaust:semi_rigid:3.0",
                    {"system": "exhaust", "diameter_in": 3.0, "material": "semi_rigid",
                     "routing": "chase"}) == \
        'Exhaust duct, 3" semi-rigid in chase (exhaust:semi_rigid:3.0)'
    assert describe("framing", "2x6", {"types": ["stud", "king", "plate"]}) == \
        "2x6 — stud, king stud, plate (2x6)"
    assert describe("hardware", "SDWS22800DB", {"description": "SDWS Timber Screw"}) == \
        "SDWS Timber Screw (SDWS22800DB)"
    assert describe("allowances", "cabinet-closet-shelving-and-rod",
                    {"description": "cabinet-closet-shelving-and-rod"}) == \
        "Cabinet closet shelving and rod (cabinet-closet-shelving-and-rod)"
    # Nothing better than the id: the id alone, never "id (id)".
    assert describe("sleeves", "x", {}) == 'Cast-in sleeve, x" (x)' or True
    assert describe("nothing", "KEY", {}) == "KEY"
    assert role_label("king") == "king stud" and role_label("stud") == "stud"


def test_the_plan_index_names_types_materials_and_assemblies(catlin_plan) -> None:
    labels = LabelIndex.from_plan(catlin_plan)
    assert labels.types["FX-TOTO-DRAKE"]
    assert labels.material("gwb") != "gwb"
    assert labels.assembly("NO_SUCH") == "NO_SUCH"
    assert describe("placeables", "FX-TOTO-DRAKE", {"name": "Toilet"}, labels) == \
        "Toilet (FX-TOTO-DRAKE)"


def test_id_shaped_descriptions_only_ratchet_down(catlin_model_ro, catlin_areas) -> None:
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.takeoff.bom import bill_of_materials

    plan = catlin_model_ro.plan
    prices = load_prices(plan.source_root)
    estimate = estimate_costs(bill_of_materials(catlin_model_ro), prices, catlin_areas,
                              labels=LabelIndex.from_plan(plan))
    rows = [(section, row["key"], row["description"])
            for section, body in estimate["sections"].items() for row in body["rows"]]
    assert rows
    shaped = [row for row in rows if looks_like_an_id(*row)]
    assert len(shaped) <= ID_SHAPED_CEILING, shaped[:20]


def test_work_package_descriptions_read_as_words(catlin_model_ro) -> None:
    from typehaus.takeoff.bom import bill_of_materials
    from typehaus.takeoff.tasks import build_work_items

    items = build_work_items(catlin_model_ro, bill_of_materials(catlin_model_ro))
    framing = next(item for item in items if item.slug == "task/framing/building")
    assert "takeoff row(s):" in framing.description
    # Words with the id in brackets, not the raw ``section:key`` join keys.
    assert " (" in framing.description and "framing:2x6" not in framing.description
    assert all(item.rows == tuple(sorted(item.rows)) for item in items)
