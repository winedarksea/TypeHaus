"""The finish override changes themed faucets alone, keeping placement and plumbing fixed."""

from _helpers import CATLIN

from typehaus.source import load_plan


def test_brushed_nickel_changes_only_theme_faucet_identity_and_material(catlin_plan):
    variant = load_plan(CATLIN, parameter_overrides={"finish.bath_theme": "brushed-nickel"}).plan
    assert variant is not None
    before = {entry.tag: entry for entry in catlin_plan.library.fixture_types}
    after = {entry.tag: entry for entry in variant.library.fixture_types}
    changed = []
    for tag, original in before.items():
        themed = any(part.product_ref == "PROD-MOEN-6702" for part in original.parts)
        expected = original.model_dump()
        if themed:
            changed.append(tag)
            for part in expected["parts"]:
                if part["product_ref"] == "PROD-MOEN-6702":
                    part["product_ref"] = "PROD-MOEN-6702BN"
            expected["model_representation"]["material_refs"]["faucet"] = "faucet-brushed-nickel"
        assert after[tag].model_dump() == expected
    assert len(changed) == 4  # the 30 in. type is placed twice
    assert tuple(variant.all_elements()) == tuple(catlin_plan.all_elements())
