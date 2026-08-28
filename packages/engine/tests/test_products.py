"""The chosen-product catalog: identity as data, and the guards that keep a ref honest.

A product used to be prose — ``name="LG WashTower WKHC252HBA (washer + heat-pump dryer)"``
with the model number buried again in a paragraph of ``source``. Nothing could read it: not
the inspector sidebar, not a schedule, not an estimator joining a line to what was bought.
``Product`` (model/product.py) makes brand and model structured, and these are the four
things that have to stay true about it.
"""

from __future__ import annotations

from pathlib import Path

from typehaus.checks import build_context, run
from typehaus.checks.integrity.catalog_tags import unknown_product_ref
from typehaus.model import Product
from typehaus.source import load_plan
from _helpers import CATLIN


def _library_with(plan, **updates):
    return plan.model_copy(update={"library": plan.library.model_copy(update=updates)})


def test_a_product_round_trips_through_the_loader(catlin_plan) -> None:
    """The catalog survives ``load_plan`` intact — tag, brand, model and the source note."""
    product = catlin_plan.library.product("PROD-LG-WKHC252HBA")
    assert product is not None, [p.tag for p in catlin_plan.library.products]
    assert (product.brand, product.model) == ("LG", "WKHC252HBA")
    assert product.source and "2026-08-24" in product.source
    # Identity only: a price field here would be decision #28 violated in the one place it
    # would be least visible. Assert the shape rather than trusting the docstring.
    assert not {f for f in Product.model_fields} & {"price", "cost", "unit_price", "vendor"}


def test_the_washtower_type_resolves_to_its_brand_and_model(catlin_plan) -> None:
    """The end-to-end join the sidebar makes: appliance type -> product_ref -> Product."""
    appliance = next(a for a in catlin_plan.library.appliance_types
                     if a.tag == "APPL-LG-WASHTOWER")
    product = catlin_plan.library.product(appliance.product_ref)
    assert product is not None
    assert product.brand == "LG"
    assert product.model == "WKHC252HBA"
    # The prose stays authoritative for the reasoning — the ref is what a machine follows,
    # not a replacement for the name the schedules print.
    assert "WKHC252HBA" in appliance.name


def test_catlin_names_no_product_it_has_not_defined() -> None:
    """The reference house's own dangling-ref gate, run through the real check pipeline."""
    result = load_plan(CATLIN)
    assert result.plan is not None
    report = run(result.plan, CATLIN)
    assert [f for f in report.findings if f.check_id == "integrity.unknown_product_ref"] == []


def test_a_dangling_product_ref_is_an_error(starter_dir: Path) -> None:
    result = load_plan(starter_dir)
    assert result.plan is not None
    materials = result.plan.library.materials
    assert materials, "starter defines no materials to point at a product"
    broken = _library_with(result.plan, materials=(
        materials[0].model_copy(update={"product_ref": "PROD-NOT-A-THING"}), *materials[1:]))
    ctx, _ = build_context(broken, starter_dir)
    findings = unknown_product_ref(ctx)
    assert len(findings) == 1
    assert findings[0].severity.value == "error"
    assert "PROD-NOT-A-THING" in findings[0].message
    assert "materials" in findings[0].message


def test_a_resolvable_product_ref_is_silent(starter_dir: Path) -> None:
    """The other half of the guard: a ref that resolves must produce no finding at all."""
    result = load_plan(starter_dir)
    assert result.plan is not None
    materials = result.plan.library.materials
    fixed = _library_with(
        result.plan,
        products=(Product(tag="PROD-TEST", brand="Test"),),
        materials=(materials[0].model_copy(update={"product_ref": "PROD-TEST"}), *materials[1:]),
    )
    ctx, _ = build_context(fixed, starter_dir)
    assert unknown_product_ref(ctx) == []


def test_a_duplicate_product_tag_is_the_same_hard_error_as_any_catalog(starter_dir: Path) -> None:
    """``products`` is a tag-keyed catalog, so ``Library.product`` has the same first-match
    hazard every other lookup has — it must be covered by the duplicate check, not exempt."""
    from typehaus.checks.integrity.catalog_tags import CATALOGS, duplicate_catalog_tag

    assert "products" in CATALOGS
    result = load_plan(starter_dir)
    assert result.plan is not None
    twin = Product(tag="PROD-TWIN", brand="Test")
    doubled = _library_with(result.plan, products=(twin, twin))
    ctx, _ = build_context(doubled, starter_dir)
    findings = [f for f in duplicate_catalog_tag(ctx) if "PROD-TWIN" in f.message]
    assert len(findings) == 1
    assert findings[0].severity.value == "error"
    assert "library.products" in findings[0].message


# --- the costs join (phase 3): the specification reaches the estimate row -----------------

def test_every_product_ref_source_is_a_real_estimate_section() -> None:
    """``PRODUCT_REF_SOURCES`` is a second reading of ``ESTIMATE_PLANS``' join, not a
    parallel one — a section name that drifts would silently label nothing."""
    from typehaus.cli.prices import ESTIMATE_PLANS
    from typehaus.takeoff.product_labels import PRODUCT_REF_SOURCES

    sections = {name for name, *_ in ESTIMATE_PLANS}
    assert not set(PRODUCT_REF_SOURCES) - sections


def test_product_labels_key_on_the_section_and_the_price_key(catlin_plan) -> None:
    from typehaus.takeoff.product_labels import product_labels

    labels = product_labels(catlin_plan)
    assert labels[("placeables", "APPL-LG-WASHTOWER")] == "LG WKHC252HBA"
    # The same appliance is priced into both halves of the placeables split.
    assert labels[("furnishings", "APPL-LG-WASHTOWER")] == "LG WKHC252HBA"
    # A type that names no product contributes no key at all — never an empty label.
    assert ("placeables", "APPL-DISPOSAL") not in labels


def test_the_estimate_row_carries_the_specified_product_and_no_price_moves(
        catlin_plan, catlin_areas) -> None:
    """The label rides along and changes nothing: same totals, same rows, one more field."""
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.resolve import resolve
    from typehaus.takeoff import bill_of_materials
    from typehaus.takeoff.product_labels import product_labels

    model, _findings = resolve(catlin_plan)
    bom = bill_of_materials(model)
    prices = load_prices(CATLIN)
    assert prices is not None, "catlin ships a prices.toml"
    plain = estimate_costs(bom, prices, catlin_areas)
    labelled = estimate_costs(bom, prices, catlin_areas, product_labels(catlin_plan))
    assert labelled["total"] == plain["total"]
    row = next(r for r in labelled["sections"]["placeables"]["rows"]
               if r["key"] == "APPL-LG-WASHTOWER")
    assert row["product"] == "LG WKHC252HBA"
    # A row with no specified product carries no key, rather than a null one: an absent
    # product and a product recorded as nothing are different facts.
    assert all("product" not in r or r["product"]
               for body in labelled["sections"].values() for r in body["rows"])
    # Without the map nothing but hardware labels anything — the caller that passes no
    # products gets exactly the payload it got before.
    assert all("product" not in r
               for section, body in plain["sections"].items() if section != "hardware"
               for r in body["rows"])


def test_hardware_reads_its_product_off_the_bom_row(catlin_plan, catlin_areas) -> None:
    """``StructuralHardware`` already carries manufacturer + model, so the hardware section
    answers "which product is this line?" with no ``Product`` record and no map."""
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.resolve import resolve
    from typehaus.takeoff import bill_of_materials

    model, _findings = resolve(catlin_plan)
    prices = load_prices(CATLIN)
    assert prices is not None
    estimate = estimate_costs(bill_of_materials(model), prices, catlin_areas)
    rows = estimate["sections"]["hardware"]["rows"]
    assert rows and any(r.get("product", "").startswith("Simpson Strong-Tie") for r in rows)
