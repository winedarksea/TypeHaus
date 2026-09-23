"""Readable descriptions for BOM and estimate rows — the id kept, a label added.

354 of the reference house's 551 estimate rows described themselves by an engine id
(``BEAM_WHITE_PAINT``, ``ducts · exhaust:semi_rigid:3.0``). A supplier cannot quote from that.
Every placeable type already carries a required plain ``name``; materials carry one;
``Assembly.label`` is the one catalog record that had none. The rest are enum keys, which a
glossary here spells out. Decision: enums and ids stay in the text, always — a label is
appended, never substituted, so the CSV still joins back to ``prices.toml``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

#: What each estimate section is, for a heading or a bid group.
SECTION_LABELS: dict[str, str] = {
    "framing": "Lumber and engineered wood", "sheet_goods": "Sheet goods",
    "hardware": "Connectors and fasteners", "concrete": "Cast and structural solids",
    "floor_heat": "Radiant floor heat", "placeables": "Fixtures, equipment and casework",
    "floor_finishes": "Floor finishes", "envelope_layers": "Assembly layers",
    "wood_surfaces": "Wood surfaces", "countertops": "Countertops",
    "openings": "Windows and doors", "footing_bedding": "Footing bedding",
    "pipe_runs": "Pipe", "pipe_fittings": "Pipe fittings", "ducts": "Ducts",
    "duct_fittings": "Duct fittings", "duct_insulation": "Duct insulation",
    "sleeves": "Cast-in sleeves", "conduit": "Conduit", "conductors": "Conductors",
    "solar_modules": "PV modules", "data_raceways": "Data raceways",
    "plumbing_specialties": "Plumbing specialties", "install_parts": "Installation kits",
    "pipe_insulation": "Pipe insulation", "freeze_protection": "Freeze protection",
    "edge_trim": "Edge trim and flashing", "member_protection": "Member protection tape",
    "wall_structure": "Wall structure by the yard", "reinforcement": "Reinforcing steel",
    "timber": "Timber", "steel_members": "Rolled steel members",
    "railings": "Guards and handrails",
    "construction_returns": "Construction returns", "sill_gaskets": "Sill gaskets",
    "drainage": "Stormwater", "furnishings": "Furnishings", "allowances": "Allowances",
}

def _angle_words(size: str) -> str:
    """``"L3.5x3.5x0.25"`` -> ``"L3-1/2 x 3-1/2 x 1/4"``, the spelling a mill quotes.

    The decimal form is what ``cross_section`` parses and is deliberately the only one the
    plan may author (``integrity.member_profile_parses`` refuses the fraction rather than
    guessing at it); this is the other direction, for a human reading an estimate.
    """
    if not size.startswith("L"):
        return size
    parts = size[1:].split("x")
    return "L" + " x ".join(_fraction_in(part) for part in parts)


#: Framing member categories that are not self-explanatory on a cut list.
ROLE_GLOSSARY: dict[str, str] = {
    "king": "king stud", "jack": "jack stud", "cripple": "cripple stud", "rim": "rim board",
    "raked_plate": "raked top plate", "outlooker": "outlooker", "barge_rafter": "barge rafter",
    "sister_joist": "sister joist", "truss_block": "truss girt block",
    "truss_blocking": "truss ladder blocking", "strapping": "girt strapping",
    "corner": "corner stud", "partition": "partition backer", "landing_framing": "landing framing",
    "newel": "newel post", "winder": "winder tread", "hanger": "hanger board",
    "bearing_stiffener": "bearing stiffener", "seat_cut": "seat cut", "roof_truss": "roof truss",
    "ridge_beam": "ridge beam", "ridge_cap": "ridge cap", "corner_trim": "corner trim",
    "trimmer": "trimmer", "airgap": "vent-gap strip", "furring": "furring",
}

#: (section, bare key) -> label, for keys that are enum values rather than catalog tags.
KEY_GLOSSARY: dict[tuple[str, str], str] = {
    ("pipe_runs", "drain"): "Drain", ("pipe_runs", "vent"): "Vent",
    ("pipe_runs", "water_hot"): "Hot water", ("pipe_runs", "water_cold"): "Cold water",
    ("pipe_runs", "gas"): "Gas", ("pipe_runs", "radon"): "Radon",
    ("pipe_runs", "sump_discharge"): "Sump discharge",
    ("ducts", "supply"): "Supply", ("ducts", "return"): "Return", ("ducts", "exhaust"): "Exhaust",
    ("ducts", "outdoor_air"): "Outdoor air", ("ducts", "dryer"): "Dryer exhaust",
    ("ducts", "transfer"): "Transfer",
    ("light_run_materials", "channel"): "Aluminium channel with diffuser",
    ("light_run_materials", "tape"): "LED tape",
    ("light_run_materials", "end_cap"): "Channel end cap",
    ("light_run_materials", "corner_connector"): "Channel corner connector",
    ("plumbing_specialties", "backflow_preventer"): "Backflow preventer",
    ("plumbing_specialties", "main_shutoff"): "Main shutoff",
    ("plumbing_specialties", "shutoff"): "Shutoff valve",
    ("plumbing_specialties", "vacuum_breaker"): "Vacuum breaker",
    ("plumbing_specialties", "water_hammer_arrestor"): "Water hammer arrestor",
    ("plumbing_specialties", "ro_stub"): "RO stub", ("plumbing_specialties", "penetration_seal"):
    "Penetration seal",
    ("edge_trim", "beam_cap"): "Beam cap", ("edge_trim", "bug_screen"): "Rainscreen bug screen",
    ("edge_trim", "corner_trim"): "Corner trim", ("edge_trim", "drip_flashing"): "Drip flashing",
    ("edge_trim", "edge_cladding"): "Roof edge cladding", ("edge_trim", "fascia"): "Fascia",
    ("edge_trim", "ridge_cap"): "Ridge cap", ("edge_trim", "soffit"): "Eave soffit",
    ("edge_trim", "wall_corner"): "Wall corner closure",
    ("edge_trim", "movement_joint"): "Masonry movement joint",
    ("concrete", "movement_joint"): "Masonry movement joint",
    ("edge_trim", "wrb_counterflashing"): "WRB counterflashing",
    ("drainage", "downspout"): "Downspout", ("drainage", "gutter"): "Gutter",
    ("drainage", "drywell"): "Drywell", ("drainage", "drain_tile"): "Drain tile",
    ("drainage", "french_drain"): "French drain", ("drainage", "sump"): "Sump",
    ("drainage", "leader_extension"): "Leader extension",
    ("drainage", "area_drain"): "Area drain", ("drainage", "area_drain_riser"): "Area drain riser",
    ("drainage", "rain_garden_media"): "Rain garden media",
    ("drainage", "rain_garden_stone"): "Rain garden stone",
    ("concrete", "rain_garden_media"): "Rain garden media",
    ("concrete", "rain_garden_stone"): "Rain garden stone",
    ("concrete", "leader_extension"): "Leader extension",
    ("floor_heat", "electric"): "Electric radiant floor heat cable",
    ("data_raceways", "data"): "Data raceway", ("data_raceways", "spare"): "Spare raceway",
    ("construction_returns", "pt-sill-plate"): "Treated sill plate",
    ("construction_returns", "resilient-channel"): "Resilient channel",
    ("construction_returns", "rim-spray-foam"): "Rim joist spray foam",
    ("construction_returns", "foundation-foam-return"): "Foundation foam return",
    ("construction_returns", "masonry-corner-return"): "Masonry corner return",
    ("construction_returns", "sauna-liner-return"): "Sauna liner return",
    ("concrete", "column"): "Column", ("concrete", "beam"): "Beam", ("concrete", "slab"): "Slab",
    ("concrete", "footing"): "Footing", ("concrete", "pad"): "Pad",
    ("concrete", "thermal_break"): "Thermal break", ("concrete", "soffit"): "Dropped soffit",
    ("concrete", "ceiling"): "Ceiling", ("concrete", "glazing"): "Glazing",
    ("concrete", "bug_screen"): "Rainscreen bug screen", ("concrete", "screen_slat"): "Screen slat",
    ("concrete", "dowel"): "Dowel", ("concrete", "connector"): "Connector",
    # The two families carved off ``connector``. Derived markers never reach a take-off
    # (they are ``derived`` and skipped), but an AUTHORED cast-in or hanger connector does,
    # and a label map with a hole in it prints a raw category key on a bid.
    ("concrete", "connector_embedded"): "Cast-in connector",
    ("concrete", "connector_hanger"): "Joist hanger",
    ("concrete", "ro_stub"): "RO stub", ("concrete", "eave_soffit"): "Eave soffit",
    ("concrete", "wall_corner"): "Wall corner closure",
    ("sill_gaskets", "sill-seal-foam"): "Sill seal foam gasket, under the sill plate",
    ("sill_gaskets", "sill-seal-peel-stick"):
        "Sill seal peel-and-stick membrane, under the sill plate",
    ("railings", "(untyped railing)"): "Guard or handrail, type not yet specified",
    ("railings", "(masonry guard wall)"): "Masonry guard wall",
}

#: Function words a material name may already carry, so "XPS rigid insulation insulation"
#: does not happen (audit:2026-09-12, seven rows).
_FUNCTION_WORDS = ("insulation", "membrane", "sheathing", "cladding", "finish", "barrier",
                   "board", "panel", "paint", "coating", "stone", "sand", "gravel", "sod")


def _profile_label(profile: str) -> str:
    """``0.416667x4.14235 panel`` -> ``7/16" x 4 1/8" formed panel``; ``deck 11x1.5`` ->
    ``11" x 1 1/2" board``; lumber sizes pass through."""
    import re

    m = re.fullmatch(r"(\d[\d.]*)x(\d[\d.]*) panel", profile)
    if m:
        return f"{_fraction_in(m.group(1))} x {_fraction_in(m.group(2))} formed panel"
    m = re.fullmatch(r"deck (\d[\d.]*)x(\d[\d.]*)", profile)
    if m:
        return f"{_fraction_in(m.group(1))} x {_fraction_in(m.group(2))} board"
    return profile


def _fraction_in(value: object) -> str:
    """``0.75`` -> ``3/4"``, ``1.5`` -> ``1 1/2"``, ``3`` -> ``3"``."""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(value)
    whole = int(number)
    part = Fraction(number - whole).limit_denominator(16)
    text = f"{whole}" if whole or not part else ""
    if part:
        text = f"{text} {part}".strip()
    return f'{text}"'


def role_label(category: str) -> str:
    return ROLE_GLOSSARY.get(category, category.replace("_", " "))


@dataclass(frozen=True)
class LabelIndex:
    """What the plan calls its own types, materials and assemblies."""

    types: Mapping[str, str] = field(default_factory=dict)
    materials: Mapping[str, str] = field(default_factory=dict)
    assemblies: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_plan(cls, plan: Any) -> LabelIndex:
        library = plan.library
        types: dict[str, str] = {}
        for name in ("furniture_types", "fixture_types", "appliance_types", "equipment_types",
                     "register_types", "electrical_device_types", "door_types", "window_types",
                     "railing_types"):
            for item in getattr(library, name, ()) or ():
                label = getattr(item, "name", None)
                if label:
                    types[item.tag] = str(label)
        materials = {m.tag: str(m.name) for m in getattr(library, "materials", ()) if m.name}
        assemblies = {a.tag: str(a.label) for a in getattr(library, "assemblies", ())
                      if getattr(a, "label", None)}
        return cls(types=types, materials=materials, assemblies=assemblies)

    def material(self, ref: object) -> str:
        tag = str(ref or "").split(":", 1)[0]
        return self.materials.get(tag, tag)

    def assembly(self, tag: object) -> str:
        return self.assemblies.get(str(tag or ""), str(tag or ""))


EMPTY_LABELS = LabelIndex()


def _fitting(key: str, system: str) -> str | None:
    parts = key.split("-")
    if len(parts) == 3 and parts[0] in ("bend", "elbow") and parts[2].endswith("in"):
        return f"{parts[1]}° {parts[0]}, {_fraction_in(parts[2][:-2])} {system}".strip()
    if len(parts) == 2 and parts[0] == "wye" and parts[1].endswith("in"):
        a, _, b = parts[1][:-2].partition("x")
        return f"Wye {_fraction_in(a)} x {_fraction_in(b)} {system}".strip()
    return None


def _label(section: str, bare: str, row: Mapping[str, Any], labels: LabelIndex) -> str | None:
    """The readable half, or ``None`` when the id is already the best there is."""
    g = lambda name: row.get(name)  # noqa: E731
    if section in ("placeables", "furnishings"):
        return str(g("name") or labels.types.get(bare) or "") or None
    if section == "framing":
        roles = ", ".join(role_label(str(t)) for t in (g("types") or ()))
        size = _profile_label(bare)
        stock = f"{size} {labels.material(g('material'))}".strip() if g("material") else size
        return f"{stock} — {roles}" if roles else None
    if section == "sheet_goods":
        thickness = _fraction_in(g("thickness_in")) if g("thickness_in") else ""
        return f"{labels.material(g('material'))}, {thickness} {g('scope') or ''}".strip(", ")
    if section == "envelope_layers":
        thickness = _fraction_in(g("thickness_in")) if g("thickness_in") else ""
        name = labels.material(g("material"))
        function = str(g("function") or "").split(" ")[0]
        if any(word in name.lower() for word in _FUNCTION_WORDS) or function == "structure":
            function = ""
        return (f"{name} {function}, {thickness} — {g('scope') or ''}"
                .replace(" ,", ",").strip(" —,"))
    if section in ("concrete", "timber"):
        head = KEY_GLOSSARY.get(("concrete", bare), bare.replace("_", " ").capitalize())
        assembly = g("assembly")
        return f"{head} — {labels.assembly(assembly)}" if assembly else head
    if section == "pipe_runs":
        system = KEY_GLOSSARY.get((section, str(g("system") or bare)), str(g("system") or bare))
        size = f", {_fraction_in(g('diameter_in'))}" if g("diameter_in") else ""
        return f"{system} pipe{size}"
    if section == "pipe_fittings":
        return _fitting(bare, str(g("system") or ""))
    if section == "duct_fittings":
        return _fitting(bare, f"{g('system') or ''} duct".strip())
    if section == "ducts":
        system = KEY_GLOSSARY.get((section, str(g("system") or "")), str(g("system") or ""))
        size = _fraction_in(g("diameter_in")) if g("diameter_in") else \
            f"{g('width_in')}x{g('depth_in')}"
        material = str(g("material") or "").replace("_", "-")
        where = f" in {g('routing')}" if g("routing") else ""
        return f"{system} duct, {size} {material}{where}".replace("  ", " ").strip()
    if section == "duct_insulation":
        return f"{g('spec')}, {_fraction_in(g('diameter_in'))} duct" if g("diameter_in") else None
    if section == "sleeves":
        return f"Cast-in sleeve, {_fraction_in(g('sleeve_diameter_in'))}"
    if section == "conduit":
        return f"Conduit, {_fraction_in(g('trade_size_in'))} trade size"
    if section == "conductors":
        return f"Branch-circuit conductors, {g('poles')}-pole circuits"
    if section == "light_run_materials":
        # The key is ``<part>:<luminaire type>``; the part is the word a supplier quotes and
        # the type is the mark it belongs to, which is how the schedule names it.
        part = KEY_GLOSSARY.get((section, bare), bare.replace("_", " ").capitalize())
        mark = g("mark")
        type_ref = str(g("type") or "")
        named = labels.types.get(type_ref) or type_ref
        return f"{part}, type {mark} — {named}" if mark else f"{part} — {named}"
    if section == "plumbing_specialties":
        kind = KEY_GLOSSARY.get((section, str(g("kind") or bare)), str(g("kind") or bare))
        return f"{kind} — {g('model')}" if g("model") else kind
    if section == "pipe_insulation":
        return f"{g('spec')}, {_fraction_in(g('pipe_diameter_in'))} pipe" if g("spec") else None
    if section == "edge_trim":
        kind = KEY_GLOSSARY.get((section, bare), bare.replace("_", " ").capitalize())
        return f"{kind}, {g('profile') or ''} {labels.material(g('material'))}".strip(", ")
    if section == "member_protection":
        width = _fraction_in(g("width_in")) if g("width_in") else ""
        return f"{labels.material(g('material'))}, {width} on {g('scope') or ''}".strip(", ")
    if section == "wall_structure":
        return f"{labels.assembly(g('assembly'))}, {labels.material(g('material'))}"
    if section == "reinforcement":
        return f"{g('bar')} rebar, {g('coating') or 'black'}, {g('scope') or ''}".strip(", ")
    if section == "steel_members":
        # The key IS the AISC section, so left alone the row describes itself with its own
        # id — "L3.5x3.5x0.25" — which is exactly what `looks_like_an_id` is for. Spell the
        # shape out and say the fraction the trade quotes: an estimator reads
        # "L3-1/2 x 3-1/2 x 1/4 steel angle", never a decimal one.
        return f"{_angle_words(bare)} steel {g('shape') or 'member'}"
    if section == "railings":
        head = labels.types.get(bare, bare)
        return f"{head} — {g('style')}" if g("style") else head
    if section == "construction_returns":
        kind = KEY_GLOSSARY.get((section, bare), bare.replace("-", " ").capitalize())
        return f"{kind}, {labels.material(g('material'))}"
    if section == "sill_gaskets":
        return KEY_GLOSSARY.get((section, bare)) or labels.material(bare)
    if section == "drainage":
        kind = KEY_GLOSSARY.get((section, bare), bare.replace("_", " ").capitalize())
        size = f", {_fraction_in(g('size_in'))}" if g("size_in") else ""
        return f"{kind}{size} — {labels.material(g('product'))}" if g("product") else kind
    if section == "footing_bedding":
        return f"Footing bedding — {g('aggregate')}" if g("aggregate") else None
    if section == "floor_finishes":
        return str(g("material") or "") or None
    if section == "floor_heat":
        return KEY_GLOSSARY.get((section, bare))
    if section == "wood_surfaces":
        return f"{labels.material(g('material'))} ({g('kind')})" if g("kind") else None
    if section == "allowances":
        return bare.replace("-", " ").capitalize()
    if section == "openings":
        width, height = g("width_in"), g("height_in")
        size = (f", {_fraction_in(width)} x {_fraction_in(height)}"
                if width is not None and height is not None else "")
        return f"Rough opening, no product assigned{size}" if bare in ("None", "") else None
    if section == "data_raceways":
        size = f", {_fraction_in(g('trade_size_in'))}" if g("trade_size_in") else ""
        return f"{KEY_GLOSSARY.get((section, bare), bare)}{size}"
    if section == "freeze_protection":
        return str(g("spec") or "") or None
    return None


def describe(section: str, key: str, row: Mapping[str, Any] | None = None,
             labels: LabelIndex = EMPTY_LABELS) -> str:
    """``"<label> (<id>)"`` — the id is always in the text, so a CSV still joins back to
    ``prices.toml``. Rows that already carry a readable field (``description``, ``product``,
    ``name``) keep it, with the id appended when the field does not already say it."""
    row = row or {}
    bare = str(key).split(":", 1)[0]
    # ``drainage`` rows carry the material ref in ``product``; that is a tag, not a name.
    readable = () if section == "drainage" else ("description", "product", "name", "label")
    for field_name in readable:
        value = row.get(field_name)
        # A field that merely repeats the key (an allowance's synthetic row) says nothing.
        if (isinstance(value, str) and value and value != str(key)
                and section not in ("placeables", "furnishings")):
            return value if str(key) in value else f"{value} ({key})"
    label = _label(section, bare, row, labels)
    if not label or label == str(key):
        return str(key)
    return f"{label} ({key})"
