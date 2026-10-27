"""Stock inventory for the formed cladding and roof-edge trim that has been resolved.

One section, three kinds of row: ``trim`` (a catalog piece or a custom cut, by part and
stock length), ``supply`` (closure, tape, sealant and fasteners, by the foot or each) and
``roof`` (Image II eave, rake and ridge pieces counted from the roofs' derived edge runs).
Every row carries ``count`` and ``length_ft``; a price in ``ea`` reads ``count`` and one in
``LF`` reads ``length_ft`` (``ALTERNATE_UNITS``).
"""

from __future__ import annotations

from math import ceil

from typehaus.library.trim.metal_sales import (
    IMAGE_II_EXTENDED_EAVE,
    IMAGE_II_FLAT_CLEAT,
    IMAGE_II_OFFSET_CLEAT,
    IMAGE_II_RAKE_CLEAT,
    IMAGE_II_RESIDENTIAL_RAKE,
    IMAGE_II_RIDGE_COVER,
    PANEL_CLOSURE,
    PROFILES,
    RESIDENTIAL_RAKE_FACE_IN,
    SUPPLIES,
    TrimProfile,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.model import ResolvedModel

_FT = 0.3048
#: Products whose joint to the frame or panel is sealed along the whole run (K7 joint).
_SEALED = {"WINDOW_JAMB_CUSTOM", "WINDOW_SILL_CUSTOM", "OPENING_HEAD", "DOOR_HEAD_CUSTOM"}
_CLOSED_BY_PANEL = {"OPENING_HEAD", "WINDOW_SILL_CUSTOM", "CORRUGATED_BASE"}
_LAP_SEALANT_FT = 1.0
_FLAT_CLEAT_SPACING_FT = 1.5


def catalog_roof_edge(member) -> bool:
    """Whether a derived roof member is billed here as an Image II piece, not by edge_trim."""
    return (member.category in {"drip_edge", "ridge_closure"}
            or (member.category == "corner_trim" and member.connection == "roof:panel-rake")
            or (member.category == "ridge_cap" and member.connection == "ridge:closed-cap"))


class _Rows:
    def __init__(self) -> None:
        self.rows: dict[tuple, dict[str, object]] = {}

    def add(self, kind, part, profile, stock, *, count, length_m, tag, unit="ea", note=""):
        row = self.rows.setdefault((kind, str(part), stock), {
            "kind": kind, "part": str(part), "profile": profile, "stock_length_in": stock,
            "count": 0.0, "cut_length_ft": 0.0, "unit": unit, "tags": [], "note": note})
        row["count"] = float(row["count"]) + count
        row["cut_length_ft"] = float(row["cut_length_ft"]) + length_m / _FT
        row["tags"].append(tag)

    def finish(self) -> list[dict[str, object]]:
        out = []
        for key in sorted(self.rows, key=lambda k: tuple(map(str, k))):
            row = self.rows[key]
            row["count"] = int(round(float(row["count"])))
            row["cut_length_ft"] = row["length_ft"] = round(float(row["cut_length_ft"]), 2)
            row["quantity"] = row["length_ft"] if row["unit"] == "LF" else row["count"]
            row["tags"] = sorted(set(row["tags"]))
            out.append(row)
        return out


def _part(profile: TrimProfile, stock: float, key: str) -> str:
    matches = [number for gauge, finish, length, number in profile.part_numbers
               if gauge == 24 and length == stock and finish in {"PVDF", "varies"}]
    return matches[0] if matches else key


def _supply(rows: _Rows, part: str, length_m: float, tag: str, *, count: float = 1.0) -> None:
    name, unit, _ = SUPPLIES[part]
    rows.add("supply", part, name, None, count=count, length_m=length_m if unit == "LF" else 0.0,
             tag=tag, unit=unit)


def _wall_trim_rows(model: ResolvedModel, rows: _Rows) -> None:
    plan = getattr(model, "plan", None)
    finish = {m.tag: m.finish for m in plan.library.materials} if plan else {}
    host_wall = {o.tag: o.host_wall for o in getattr(model, "openings", ())}
    panel_finish = {}
    for wall in getattr(model, "walls", ()):
        for layer in wall.layers:
            if layer.function == "cladding" and finish.get(layer.material_ref):
                panel_finish[wall.tag] = finish[layer.material_ref]
    for solid in model.solids:
        if solid.category != "cladding_trim":
            continue
        profile = PROFILES.get(solid.product or "")
        if profile is None or solid.trim_length_m is None or solid.trim_stock_length_in is None:
            raise ValueError(f"{solid.tag}: cladding trim lacks profile or stock metadata")
        stock, length = solid.trim_stock_length_in, solid.trim_length_m
        if stock not in profile.stock_lengths_in or length <= 0 or length > stock * M_PER_IN + 1e-9:
            raise ValueError(f"{solid.tag}: invalid cut or stock length")
        part = _part(profile, stock, solid.product)
        rows.add("trim", part, profile.name, stock, count=1, length_m=length, tag=solid.tag,
                 unit="LF" if profile.custom else "ea")
        host = getattr(solid, "host_ref", None)
        panel = panel_finish.get(host_wall.get(host, host))
        closure = profile.closure
        if closure is None and solid.product in _CLOSED_BY_PANEL:
            closure = PANEL_CLOSURE.get(panel or "")
        if closure and solid.product not in {"BBD_C_CLOSURE"}:
            _supply(rows, closure, length, solid.tag)
        suffix = solid.tag.rsplit("-", 1)[-1]
        lap_index = suffix.isdigit() and int(suffix) > 1
        if solid.product in _SEALED:
            _supply(rows, "tube-sealant", length, solid.tag)
        if lap_index:
            _supply(rows, "tube-sealant", _LAP_SEALANT_FT * _FT, solid.tag)
        if profile.name == "1.25 inch Base":
            _supply(rows, "butyl-tape", length, solid.tag)
        role = profile.fastener_role.replace("_", "-")
        fasteners = ceil(length / M_PER_IN / profile.fastener_spacing_in) * profile.fastener_rows
        fasteners += profile.lap_fasteners if lap_index else 0
        _supply(rows, role, 0.0, solid.tag, count=fasteners)


def _runs(roof, suffix: str):
    """Derived edge members ending in ``suffix``, keyed on their run."""
    for member in roof.members:
        if member.child_key.endswith(suffix):
            yield member.child_key[: -len(suffix)], member


def _pieces(rows, profile, key, length_m, tag, lap_in=None, note=""):
    lap = (profile.hem_notch_in or profile.min_lap_in) if lap_in is None else lap_in
    for start, end, stock in split_stock_run(
            length_m, tuple(v * M_PER_IN for v in profile.stock_lengths_in), lap * M_PER_IN):
        stock_in = round(stock / M_PER_IN, 6)
        rows.add("roof", _part(profile, stock_in, key), profile.name, stock_in, count=1,
                 length_m=end - start, tag=tag, note=note)


def roof_face_in(member) -> float:
    return (member.z1_m - member.z0_m) / M_PER_IN


def _roof_edge_rows(model: ResolvedModel, rows: _Rows) -> None:
    from typehaus.library.trim.metal_sales import IMAGE_II_RAKE_4IN_CUSTOM

    for roof in model.roofs:
        for run, face in _runs(roof, "-drip-edge-face"):
            tag = f"{roof.tag}:{run}"
            if run.startswith("eave"):
                _pieces(rows, IMAGE_II_EXTENDED_EAVE, "IMAGE_II_EXTENDED_EAVE", face.length_m,
                        tag, note="specify pitch")
                _pieces(rows, IMAGE_II_OFFSET_CLEAT, "IMAGE_II_OFFSET_CLEAT", face.length_m,
                        tag, 0.0)
            elif roof.tag != "RF-HOUSE":
                _rake(rows, roof_face_in(face), face.length_m, tag, IMAGE_II_RAKE_4IN_CUSTOM)
        for run, face in _runs(roof, "-panel-rake-face"):
            _rake(rows, roof_face_in(face), face.length_m, f"{roof.tag}:{run}",
                  IMAGE_II_RAKE_4IN_CUSTOM)
        for member in roof.members:
            if member.category == "ridge_cap" and member.connection == "ridge:closed-cap":
                tag = f"{roof.tag}:{member.child_key}"
                _pieces(rows, IMAGE_II_RIDGE_COVER, "IMAGE_II_RIDGE_COVER", member.length_m,
                        tag, 2.0, "specify pitch")
                _supply(rows, "58603XX", 2 * member.length_m, tag)
                _supply(rows, "6403899", 4 * member.length_m, tag)


def _rake(rows, face_in, length_m, tag, custom) -> None:
    """Stock Residential Rake where its 2-5/8 in leg covers the face, else the 4 in custom."""
    if face_in <= RESIDENTIAL_RAKE_FACE_IN + 1e-6:
        _pieces(rows, IMAGE_II_RESIDENTIAL_RAKE, "IMAGE_II_RESIDENTIAL_RAKE", length_m, tag, 1.0)
    else:
        rows.add("roof", "IMAGE_II_RAKE_4IN_CUSTOM", custom.name, None, count=1,
                 length_m=length_m, tag=tag, unit="LF")
    _pieces(rows, IMAGE_II_RAKE_CLEAT, "IMAGE_II_RAKE_CLEAT", length_m, tag, 0.0)
    if "RF-HOUSE" not in tag:
        rows.add("roof", _part(IMAGE_II_FLAT_CLEAT, 122.0, "IMAGE_II_FLAT_CLEAT"),
                 IMAGE_II_FLAT_CLEAT.name, None,
                 count=ceil(length_m / _FT / _FLAT_CLEAT_SPACING_FT) + 1, length_m=0.0, tag=tag)


def cladding_trim_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Group cut pieces by catalog part and purchased stock length, with their supplies.

    A piece is ordered independently; combining short cuts into a shop cutting plan
    requires an explicit packing calculation and is not assumed here.
    """
    rows = _Rows()
    _wall_trim_rows(model, rows)
    if getattr(model, "roofs", None):
        _roof_edge_rows(model, rows)
    return rows.finish()
