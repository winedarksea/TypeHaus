"""Stock inventory for the formed cladding and roof-edge trim that has been resolved.

One section, three kinds of row: ``trim`` (a catalog piece or a custom cut, by part and
stock length), ``supply`` (closure, tape, sealant and fasteners, by the foot or each) and
``roof`` (Image II eave, rake and ridge pieces counted from the roofs' derived edge runs).
Every row carries ``count`` and ``length_ft``; a price in ``ea`` reads ``count`` and one in
``LF`` reads ``length_ft`` (``ALTERNATE_UNITS``).
"""

from __future__ import annotations

from math import ceil, dist

from typehaus.library.trim.metal_sales import (
    BOX_GUTTER_STRAP_SPACING_FT,
    IMAGE_II_EXTENDED_EAVE,
    IMAGE_II_FLAT_CLEAT,
    IMAGE_II_OFFSET_CLEAT,
    IMAGE_II_RAKE_CLEAT,
    IMAGE_II_RESIDENTIAL_RAKE,
    IMAGE_II_RIDGE_COVER,
    IMAGE_II_VENTED_STEP_RIDGE,
    PANEL_CLOSURE,
    PROFILES,
    RESIDENTIAL_RAKE_FACE_IN,
    SUPPLIES,
    TrimProfile,
)
from typehaus.model.trim import Gutter
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.roof_edge_geometry import roof_edge_runs
from typehaus.resolve.roof_image_ii import wrapped_image_ii_edges

_FT = 0.3048
#: Products whose joint to the frame or panel is sealed along the whole run (K7 joint).
_SEALED = {"PBR_WINDOW_JAMB", "WINDOW_JAMB_CUSTOM", "WINDOW_SILL_CUSTOM", "OPENING_HEAD",
           "DOOR_HEAD_CUSTOM"}
_CLOSED_BY_PANEL = {"OPENING_HEAD", "WINDOW_SILL_CUSTOM", "CORRUGATED_BASE"}
_LAP_SEALANT_FT = 1.0
_FLAT_CLEAT_SPACING_FT = 1.5
#: One pop rivet per 16 in Image II rib, on each side of a vented ridge's step cover.
_RIDGE_RIB_IN = 16.0


def catalog_roof_edge(member) -> bool:
    """Whether a derived roof member is billed here as an Image II piece, not by edge_trim."""
    return (member.category in {"drip_edge", "ridge_closure"}
            or (member.category == "corner_trim" and member.connection == "roof:panel-rake")
            or (member.category == "ridge_cap"
                and member.connection in {"ridge:closed-cap", "ridge:image-ii-vented"}))


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
    # A panel end on a perforated strip takes no closure; the strip bills with the screens.
    on_strip = {(s.host_ref, "head" if "-HEADSTRIP-" in s.tag else "base")
                for s in model.solids
                if s.category == "bug_screen" and s.product == "PANEL_END_STRIP"}
    for solid in model.solids:
        if solid.category != "cladding_trim":
            continue
        if solid.product == "EPDM_BASE_ISOLATION":
            if solid.trim_length_m is None or solid.trim_length_m <= 0:
                raise ValueError(f"{solid.tag}: isolation lacks installed length")
            _supply(rows, "epdm-isolation", solid.trim_length_m, solid.tag)
            continue
        if solid.product in {"6460800", "6411499", "corrugated-outside-closure"}:
            if solid.trim_length_m is None or solid.trim_length_m <= 0:
                raise ValueError(f"{solid.tag}: wall-top closure lacks installed length")
            _supply(rows, solid.product, solid.trim_length_m, solid.tag)
            if solid.product == "6411499":
                _supply(rows, "butyl-tape", solid.trim_length_m, solid.tag)
            continue
        profile = PROFILES.get(solid.product or "")
        if profile is None or solid.trim_length_m is None or solid.trim_stock_length_in is None:
            raise ValueError(f"{solid.tag}: cladding trim lacks profile or stock metadata")
        stock, length = solid.trim_stock_length_in, solid.trim_length_m
        stock_lengths = profile.stock_lengths_in
        if solid.product == "RAINSCREEN_BASE_Z":
            wall = model.wall(solid.host_ref)
            assembly = model.plan.library.resolve_assembly(wall.assembly) if wall else None
            spec = assembly.rainscreen_base_flashing if assembly else None
            stock_lengths = (round(spec.stock_length.meters / M_PER_IN, 6),) if spec else ()
        if stock not in stock_lengths or length <= 0 or length > stock * M_PER_IN + 1e-9:
            raise ValueError(f"{solid.tag}: invalid cut or stock length")
        part = _part(profile, stock, solid.product)
        rows.add("trim", part, profile.name, stock, count=1, length_m=length, tag=solid.tag,
                 unit="LF" if profile.custom else "ea")
        if solid.product == "RAINSCREEN_BASE_Z":
            if solid.tag.rsplit("-", 1)[-1] != "1":
                _supply(rows, "tube-sealant", _LAP_SEALANT_FT * _FT, solid.tag)
            continue
        host = getattr(solid, "host_ref", None)
        panel = panel_finish.get(host_wall.get(host, host))
        closure = profile.closure
        if closure is None and solid.product in _CLOSED_BY_PANEL:
            closure = PANEL_CLOSURE.get(panel or "")
        end = ("head" if solid.product == "OPENING_HEAD"
               else "base" if solid.tag.startswith(f"TRIM-{host}-BASE-") else None)
        closed = closure and solid.product not in {"BBD_C_CLOSURE"} \
            and (host, end) not in on_strip
        if closed:
            _supply(rows, closure, length, solid.tag)
        suffix = solid.tag.rsplit("-", 1)[-1]
        lap_index = suffix.isdigit() and int(suffix) > 1
        if solid.product in _SEALED:
            _supply(rows, "tube-sealant", length, solid.tag)
        if lap_index:
            _supply(rows, "tube-sealant", _LAP_SEALANT_FT * _FT, solid.tag)
        if profile.name == "1.25 inch Base" and closed:
            _supply(rows, "butyl-tape", length, solid.tag)  # beds the closure
        role = profile.fastener_role.replace("_", "-")
        fasteners = ceil(length / M_PER_IN / profile.fastener_spacing_in) * profile.fastener_rows
        fasteners += profile.lap_fasteners if lap_index else 0
        if fasteners:  # a taped-in Z drip head takes none
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


def _eave_pieces(rows, length_m, tag, cleat: bool = True) -> None:
    _pieces(rows, IMAGE_II_EXTENDED_EAVE, "IMAGE_II_EXTENDED_EAVE", length_m, tag,
            note="specify pitch")
    if cleat:
        _pieces(rows, IMAGE_II_OFFSET_CLEAT, "IMAGE_II_OFFSET_CLEAT", length_m, tag, 0.0)


def _roof_edge_rows(model: ResolvedModel, rows: _Rows) -> None:
    for roof in model.roofs:
        # A derived drip on a fascia edge: its face is graded against the stock rake leg.
        for run, face in _runs(roof, "-drip-edge-face"):
            tag = f"{roof.tag}:{run}"
            if run.startswith("eave"):
                _eave_pieces(rows, face.length_m, tag)
            else:
                _rake(rows, face.length_m, tag, roof_face_in(face), barge=True)
        # The Image II catalog pieces on the wrapped edges (roof_image_ii) are the stock by design.
        # The pan hems onto the Extended Eave's own lip, no cleat (RDM 5/2024 p. 31).
        for run, member in _runs(roof, "-image-ii-eave"):
            _eave_pieces(rows, member.length_m, f"{roof.tag}:{run}", cleat=False)
        # A rake's foot over the eave leg is the same stock piece, notched at the corner.
        feet = dict(_runs(roof, "-image-ii-rake-foot"))
        for run, member in _runs(roof, "-image-ii-rake"):
            barge = _has_barge(model, roof, run)
            foot = feet[run].length_m if run in feet else 0.0
            _rake(rows, member.length_m + foot, f"{roof.tag}:{run}", barge=barge)
        for member in roof.members:
            if member.category != "ridge_cap":
                continue
            tag = f"{roof.tag}:{member.child_key}"
            if member.connection == "ridge:closed-cap":
                _pieces(rows, IMAGE_II_RIDGE_COVER, "IMAGE_II_RIDGE_COVER", member.length_m,
                        tag, 2.0, "specify pitch")
                _supply(rows, "58603XX", 2 * member.length_m, tag)
                _supply(rows, "6403899", 4 * member.length_m, tag)
            elif member.connection == "ridge:image-ii-vented":
                _pieces(rows, IMAGE_II_VENTED_STEP_RIDGE, "IMAGE_II_VENTED_STEP_RIDGE",
                        member.length_m, tag, 2.0, "specify pitch")
                _supply(rows, "cobra-vented-closure", member.length_m, tag)
                _supply(rows, "6403899", 4 * member.length_m, tag)
                ribs = ceil(member.length_m / M_PER_IN / _RIDGE_RIB_IN)
                _supply(rows, "trim-pop-rivet", 0.0, tag, count=2 * ribs)


def _has_barge(model: ResolvedModel, roof, key: str) -> bool:
    """Whether the run ``key`` hangs on a fascia (barge) board, the one the flat cleat fixes to.

    A wrapped edge has no board under it (the house's rakes, and a garage or canopy gable
    that another roof continues across), so it takes the rake and its cleat but no flat cleat.
    """
    run = next(r for r in roof_edge_runs(roof) if r.key == key)
    return run.edge_name not in wrapped_image_ii_edges(model, roof)


def _rake(rows, length_m, tag, face_in: float = RESIDENTIAL_RAKE_FACE_IN, *,
          barge: bool) -> None:
    """A stock Residential Rake 52126XX and its cleats; no catalog rake takes a deeper face."""
    if face_in > RESIDENTIAL_RAKE_FACE_IN + 1e-6:
        raise ValueError(f"{tag}: a {face_in:.3f} in rake face is past the stock 2-5/8 in leg "
                         "and no catalog piece covers it")
    _pieces(rows, IMAGE_II_RESIDENTIAL_RAKE, "IMAGE_II_RESIDENTIAL_RAKE", length_m, tag, 1.0)
    _pieces(rows, IMAGE_II_RAKE_CLEAT, "IMAGE_II_RAKE_CLEAT", length_m, tag, 0.0)
    if barge:
        rows.add("roof", _part(IMAGE_II_FLAT_CLEAT, 122.0, "IMAGE_II_FLAT_CLEAT"),
                 IMAGE_II_FLAT_CLEAT.name, None,
                 count=ceil(length_m / _FT / _FLAT_CLEAT_SPACING_FT) + 1, length_m=0.0, tag=tag)


def _catalog_gutter_rows(model: ResolvedModel, rows: _Rows) -> None:
    """Catalog box gutters by part: the sticks, a lap bead per joint, end caps, straps, rivets.

    One left and one right end cap close each run, and straps hang at
    ``BOX_GUTTER_STRAP_SPACING_FT`` with one at each end, each on a pop rivet.
    """
    plan = getattr(model, "plan", None)
    if plan is None:
        return
    for storey in plan.storeys:
        for element in plan.storey_elements(storey.tag):
            profile = PROFILES.get(getattr(element, "product", None) or "")
            if not isinstance(element, Gutter) or profile is None:
                continue
            points = [p.xy_m for p in element.path]
            length_m = sum(dist(a, b) for a, b in zip(points[:-1], points[1:], strict=True))
            stock_m = tuple(v * M_PER_IN for v in profile.stock_lengths_in)
            pieces = split_stock_run(length_m, stock_m, profile.min_lap_in * M_PER_IN)
            for start, end, stock in pieces:
                stock_in = round(stock / M_PER_IN, 6)
                rows.add("trim", _part(profile, stock_in, element.product), profile.name,
                         stock_in, count=1, length_m=end - start, tag=element.tag)
            if len(pieces) > 1:
                _supply(rows, "tube-sealant", _LAP_SEALANT_FT * _FT * (len(pieces) - 1),
                        element.tag)
            _supply(rows, "58081XX", 0.0, element.tag)
            _supply(rows, "58082XX", 0.0, element.tag)
            straps = ceil(length_m / _FT / BOX_GUTTER_STRAP_SPACING_FT) + 1
            _supply(rows, "58092XX", 0.0, element.tag, count=straps)
            _supply(rows, "trim-pop-rivet", 0.0, element.tag, count=straps)


def cladding_trim_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Group cut pieces by catalog part and purchased stock length, with their supplies.

    A piece is ordered independently; combining short cuts into a shop cutting plan
    requires an explicit packing calculation and is not assumed here.
    """
    rows = _Rows()
    _wall_trim_rows(model, rows)
    _catalog_gutter_rows(model, rows)
    if getattr(model, "roofs", None):
        _roof_edge_rows(model, rows)
    return rows.finish()
