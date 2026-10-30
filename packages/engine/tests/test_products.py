"""The chosen-product catalog: identity as data, and the guards that keep a ref honest.

``Product`` (model/product.py) makes brand and model structured data instead of prose
buried in a paragraph of ``source`` — readable by the inspector sidebar, a schedule, and
an estimator joining a line to what was bought. These are the four things that have to
stay true about it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from _helpers import CATLIN

from typehaus.checks import build_context
from typehaus.checks.integrity.catalog_tags import unknown_product_ref
from typehaus.model import Product
from typehaus.source import load_plan


def test_catlin_tea_kettle_product_and_supply(catlin_plan):
    from typehaus.model import Appliance, Service

    kettle_type = next(item for item in catlin_plan.library.appliance_types
                       if item.tag == "APPL-SEVERIN-WK3422")
    product = catlin_plan.library.product(kettle_type.product_ref)
    assert (product.brand, product.model) == ("SEVERIN", "WK 3422")
    assert tuple(d.meters for d in kettle_type.footprint) == pytest.approx((0.240, 0.220))
    assert kettle_type.needs == frozenset({Service.POWER_240})
    elements = catlin_plan.elements["main"]
    kettle = next(item for item in elements if isinstance(item, Appliance)
                  and item.tag == "APPL-M-KETTLE")
    assert len(kettle.install_parts) == 1
    assert "6-20P" in kettle.install_parts[0]
    circuit = next(item for item in catlin_plan.library.circuits if item.tag == "CKT-KETTLE")
    assert (circuit.poles, circuit.breaker_amps, circuit.load_va) == (2, 20, 3000)
    assert circuit.gfci


def test_catlin_rivelia_product_and_supply(catlin_plan):
    from typehaus.model import Appliance, Service

    appliance_type = next(item for item in catlin_plan.library.appliance_types
                          if item.tag == "APPL-DELONGHI-EXAM44055W")
    product = catlin_plan.library.product(appliance_type.product_ref)
    assert (product.brand, product.model) == ("De’Longhi", "EXAM44055W")
    assert product.url.endswith("EXAM44055W.html?pid=0132250087")
    assert tuple(d.meters for d in appliance_type.footprint) == pytest.approx(
        (9.75 * 0.0254, 17 * 0.0254))
    assert appliance_type.height.meters == pytest.approx(14.75 * 0.0254)
    assert appliance_type.plan_symbol == "espresso-machine"
    assert appliance_type.needs == frozenset({Service.POWER_120})
    assert len(appliance_type.ports) == 1
    port = appliance_type.ports[0]
    assert port.service == Service.POWER_120
    assert tuple(d.meters for d in port.position) == pytest.approx((0, 8.5 * 0.0254, 0))
    appliance = next(item for item in catlin_plan.elements["main"]
                     if isinstance(item, Appliance) and item.tag == "APPL-M-COFFEE")
    assert appliance.type_ref == appliance_type.tag
    assert not appliance.install_parts


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


def test_catlin_names_no_product_it_has_not_defined(catlin_check_report) -> None:
    """The reference house's own dangling-ref gate, run through the real check pipeline."""
    report = catlin_check_report()
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
        products=(*result.plan.library.products, Product(tag="PROD-TEST", brand="Test")),
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
    assert labels[("sheet_goods", "trex-enhance-basics")] == "Trex Enhance Basics, Tide Pool (TP)"
    assert labels[("stair_treads", "trex-enhance-basics")] == "Trex Enhance Basics, Tide Pool (TP)"
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

pytestmark = pytest.mark.slow


def test_unknown_fixture_part_names_its_role(starter_dir):
    from typehaus.model import ProductPart

    plan = load_plan(starter_dir).plan
    fixture_type = plan.library.fixture_types[0].model_copy(update={
        "parts": (ProductPart(role="faucet", product_ref="MISSING-FAUCET"),),
    })
    plan = _library_with(plan, fixture_types=(fixture_type, *plan.library.fixture_types[1:]))
    ctx, _ = build_context(plan, starter_dir)
    finding = next(f for f in unknown_product_ref(ctx) if "MISSING-FAUCET" in f.message)
    assert "faucet part" in finding.message


def test_fixture_parts_bill_per_instance_and_quantity(catlin_model_ro):
    from typehaus.takeoff.placeables import placeables_takeoff
    from typehaus.takeoff.product_labels import product_labels

    rows = placeables_takeoff(catlin_model_ro)
    from collections import Counter

    faucets = Counter()
    for row in rows:
        if "faucet" in row.get("roles", ()):
            faucets[row["type"]] += row["count"]
    assert faucets["PROD-MOEN-6702"] == 5
    assert faucets["PROD-KRAUS-KBF-1401-SFS"] == 3
    assert faucets["PROD-DURAVIT-B21010001U10"] == 1
    assert "Moen" in product_labels(catlin_model_ro.plan)[("placeables", "PROD-MOEN-6702")]


def _hand_counted(plan, tag):
    cabinet = next(t for t in plan.library.furniture_types if t.tag == tag)
    counts = {}
    for part in cabinet.parts:
        key = (part.role, part.product_ref.removeprefix("PROD-IKEA-"))
        counts[key] = counts.get(key, 0) + part.quantity
    return cabinet.product_ref, counts


def test_sektion_parts_match_the_hand_counts(catlin_plan):
    """notes/ikea_sektion_order.md: the sink base, a peninsula drawer base, the aligned pantry."""
    frame, sink = _hand_counted(catlin_plan, "SEKT-SINK-B36")
    assert frame == "PROD-IKEA-SEKTION-BASE-36-24-30"
    assert sink == {("front", "AXSTAD-DOOR-18-30"): 2, ("hinge", "UTRUSTA-HINGE-110"): 4,
                    ("knob", "BAGGANAS-KNOB-BLACK"): 2, ("leg", "SEKTION-LEG"): 6,
                    ("toe_kick", "FORBATTRA-TOEKICK-84"): 1, ("rail", "SEKTION-RAIL-84"): 1}
    _, drawers = _hand_counted(catlin_plan, "SEKT-B24")
    assert drawers == {("front", "AXSTAD-DRAWER-24-10"): 3, ("drawer", "MAXIMERA-MEDIUM-24-24"): 3,
                       ("pull", "BAGGANAS-PULL-BLACK"): 3, ("leg", "SEKTION-LEG"): 4,
                       ("toe_kick", "FORBATTRA-TOEKICK-84"): 1}
    _, pantry = _hand_counted(catlin_plan, "SEKT-HIGH18-90")
    assert pantry == {("front", "AXSTAD-DOOR-18-30"): 1, ("front", "AXSTAD-DOOR-18-40"): 1,
                      ("front", "AXSTAD-DOOR-18-20"): 1, ("hinge", "UTRUSTA-HINGE-110"): 6,
                      ("knob", "BAGGANAS-KNOB-BLACK"): 3, ("shelf", "UTRUSTA-SHELF-18-24"): 3,
                      ("leg", "SEKTION-LEG"): 4, ("toe_kick", "FORBATTRA-TOEKICK-84"): 1,
                      ("rail", "SEKTION-RAIL-84"): 1}


def test_a_touching_run_buys_whole_sticks():
    from typehaus.takeoff.placeables import _sticks

    def frame(x0, width_in):
        x1 = x0 + width_in * 0.0254
        return [(x0, 0.0), (x1, 0.0), (x1, 0.4), (x0, 0.4)]

    stick = 84 * 0.0254
    touching = [(frame(0.0, 48), 48 * 0.0254), (frame(48 * 0.0254, 54), 54 * 0.0254)]
    assert _sticks(touching, stick) == 2
    short_run = [(frame(0.0, 30), 30 * 0.0254), (frame(30 * 0.0254, 36), 36 * 0.0254)]
    assert _sticks(short_run, stick) == 1
    apart = [(frame(0.0, 30), 30 * 0.0254), (frame(32 * 0.0254, 36), 36 * 0.0254)]
    assert _sticks(apart, stick) == 2


def test_ikea_order_list_covers_every_sektion_frame(catlin_model_ro):
    from typehaus.library.placeables.sektion_parts import hinges_per_door, kitchen_layout
    from typehaus.model.placeable_symbols._sektion_kitchen import KITCHEN_SEKTION_CONFIGURATIONS
    from typehaus.takeoff.order_list import order_list

    library = catlin_model_ro.plan.library
    types = {t.tag: t for t in library.furniture_types}
    placed = [types[o.type_ref] for o in catlin_model_ro.canvas_objects if o.type_ref in types]
    for entry in placed:
        symbol = entry.plan_symbol or ""
        if symbol.startswith("sektion") and symbol != "sektion-cover-panel":
            assert library.product(entry.product_ref).brand == "IKEA", entry.tag
    kitchen = [entry for entry in placed if entry.plan_symbol in KITCHEN_SEKTION_CONFIGURATIONS]
    # Hinges on the kitchen-glyph frames equal the doors their glyphs draw.
    expected = sum(
        hinges_per_door(row.height_in) * row.count
        for entry in kitchen
        for row in kitchen_layout(entry.plan_symbol, round(entry.footprint[0].inches),
                                  entry.height.inches).rows if row.kind == "door")
    billed = sum(part.quantity for entry in kitchen for part in entry.parts
                 if part.product_ref == "PROD-IKEA-UTRUSTA-HINGE-110")
    assert billed == expected > 0
    listing = order_list(catlin_model_ro, "IKEA")
    hinges = next(i for i in listing["items"] if i["product"] == "PROD-IKEA-UTRUSTA-HINGE-110")
    assert hinges["packs"] == -(-hinges["units"] // 2)
    assert not any(row["reason"] == "no product_ref" for row in listing["unresolved"])
