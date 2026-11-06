"""The plumber's fixture count and the electrician's opening count.

Neither trade bids off a pipe or wire list: they route their own and price per fixture
setting or per opening. So the count leads, by kind, and the per-item rows carry the room
and the spec sheet. Fixtures come from ``fixture_units`` (every placeable needing water or
drain), devices from the same storey walk ``electrical_device_takeoff`` makes.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from typehaus.takeoff.bid_summaries import SummaryInputs, SummaryTable


def plumbing_summary(inputs: SummaryInputs) -> list[SummaryTable]:
    from typehaus.resolve.fixture_units import _placeable_types, fixture_units
    from typehaus.resolve.plumbing_tables import FIXTURE_CLASS_BY_SYMBOL
    from typehaus.takeoff.cost_codes import cost_code
    from typehaus.takeoff.placeables import placeables_takeoff
    from typehaus.takeoff.product_labels import product_label

    model = inputs.model
    library = model.plan.library
    types = {**_placeable_types(model.plan), **{t.tag: t for t in library.equipment_types}}
    elements = {e.tag: e for e in model.plan.all_elements()
                if e.element_kind in ("Fixture", "Appliance", "Equipment")}
    counts: Counter[str] = Counter()
    rows = []
    for unit in fixture_units(model.plan):
        element = elements.get(unit.tag)
        kind = FIXTURE_CLASS_BY_SYMBOL.get(unit.symbol or "") or unit.symbol or (
            "appliance connection" if getattr(element, "element_kind", "") == "Appliance"
            else "other")
        counts[kind] += 1
        spec = types.get(getattr(element, "type_ref", None) or "")
        product = library.product(getattr(spec, "product_ref", None) or "")
        rows.append((unit.tag, unit.room or "—", kind,
                     getattr(spec, "name", None) or getattr(spec, "tag", "—"),
                     product_label(product) if product else "—",
                     (product.url or "") if product else ""))
    # Equipment the plumber sets: the water heater, its header (filed by the BOM's rule).
    for row in placeables_takeoff(model):
        if row["domain"] != "mechanical" or cost_code(
                "placeables", str(row["type"]), row=row).trade != "plumbing":
            continue
        kind = str(row.get("equipment_kind") or "equipment").replace("_", " ")
        counts[kind] += int(row["count"])
        product = library.product(getattr(types.get(str(row["type"])), "product_ref", None)
                                  or "")
        for tag in row["tags"]:
            room = getattr(elements.get(tag), "room", None) or "—"
            rows.append((tag, room, kind, row.get("name") or row["type"],
                         product_label(product) if product else "—",
                         (product.url or "") if product else ""))
    return [
        SummaryTable("fixture-count", "Fixtures and equipment, by kind", ("Kind", "Count"),
                     tuple(sorted(counts.items()))),
        SummaryTable("fixtures", "Every fixture, with its room and spec sheet",
                     ("Tag", "Room", "Kind", "Type", "Product", "Spec sheet"),
                     tuple(sorted(rows)),
                     ("Supply, drain and vent pipe are in the detailed BOM for a plumber "
                      "who wants it; route your own.",)),
    ]


def electrical_summary(inputs: SummaryInputs) -> list[SummaryTable]:
    from typehaus.takeoff.electrical import panel_schedule
    from typehaus.takeoff.lighting import luminaire_schedule

    model = inputs.model
    storeys = [s.tag for s in model.plan.storeys]
    devices: dict[str, Counter[str]] = defaultdict(Counter)
    for storey in storeys:
        for element in model.plan.storey_elements(storey):
            # A luminaire is an opening too, but it is counted by form below.
            if element.element_kind == "ElectricalDevice" and element.kind.value != "light":
                devices[element.kind.value.replace("_", " ")][storey] += 1
    used = [s for s in storeys if any(c[s] for c in devices.values())]
    device_rows = tuple((kind, *(c[s] for s in used), sum(c.values()))
                        for kind, c in sorted(devices.items()))

    forms: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    for row in luminaire_schedule(model):
        entry = forms[str(row["form"]).replace("_", " ")]
        entry[0] += int(row.get("count") or 0)
        entry[1] += float(row.get("length_ft") or 0.0)
    luminaire_rows = tuple((form, int(count), round(feet, 1))
                           for form, (count, feet) in sorted(forms.items()))

    circuits = panel_schedule(model)
    dedicated = tuple(
        (row["circuit"], row["description"], row["volts"], row["breaker_amps"], row["poles"],
         row["nema"] or "—", "yes" if row["gfci"] else "—", "yes" if row["afci"] else "—",
         row["panel"])
        for row in circuits if row["volts"] == 240 or len(row["devices"]) == 1)
    panels = Counter(str(row["panel"]) for row in circuits)
    return [
        SummaryTable("device-count", "Devices, by kind and storey",
                     ("Kind", *used, "Total"), device_rows,
                     ("Luminaires are counted by form in the next table.",)),
        SummaryTable("luminaire-count", "Luminaires, by form",
                     ("Form", "Count", "Strip LF"), luminaire_rows,
                     ("Types, lamps and models are on E-602.",)),
        SummaryTable("dedicated-circuits", "Dedicated and 240 V circuits",
                     ("Circuit", "Serves", "Volts", "Breaker A", "Poles", "NEMA", "GFCI",
                      "AFCI", "Panel"), dedicated),
        SummaryTable("panels", "Panels", ("Panel", "Circuits"), tuple(sorted(panels.items())),
                     ("Every circuit is on the E-601 panel schedule.",)),
    ]
