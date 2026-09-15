"""Classification rules over the trade vocabulary: which trade a material, an assembly
layer, a solid, a framing member or a placeable belongs to.

Split from :mod:`typehaus.emit.trades` (the vocabulary itself) so the tables that *name*
trades stay short and the rules that *pick* one are in one place for the viewer
(``resolve/geometry_build.py``, ``emit/gltf``, ``server/model_json``) and the BOM
(``takeoff/cost_codes.py``) to share. Facts beat spelling: a rule reads a material ref, a
layer function, a domain, a member category — never a display name.
"""

from __future__ import annotations

import fnmatch

from typehaus.emit.trades import FALLBACK_TRADE, TRADES, sequence_rank, solid_trade

# --- materials --------------------------------------------------------------------------

#: Material-ref glob -> trade, first match wins. Only refs whose trade is on their face; a
#: ref that says nothing (``air-barrier``, ``aluminum``) falls to the layer/section rule.
MATERIAL_TRADE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("gwb*", "drywall"),
    ("resilient-channel*", "drywall"),
    ("*paint*", "paint"),
    ("foundation-coating*", "paint"),
    # The court's mineral silicate wash, both substrate variants. A coating is the painter's
    # arrival, not the mason's and not the millworker's — without this it fell through every
    # pattern below to the section fallback. Mirrors `foundation-coating*` above; note the
    # glob has to precede `*brick*` and `retaining-block*`, since the wash goes on both.
    ("silicate-wash*", "paint"),
    ("*spray-foam*", "insulation"),
    ("*fiberglass*", "insulation"),
    ("blown-*", "insulation"),
    ("mineral-wool*", "insulation"),
    ("polyiso*", "insulation"),
    ("xps*", "insulation"),
    ("eps*", "insulation"),
    ("icf-eps*", "insulation"),
    ("humid-room-membrane", "insulation"),   # interior vapour control, hung with the foam
    ("*sod", "landscaping"),
    ("rootzone*", "landscaping"),
    ("usga-*", "landscaping"),
    ("geotextile*", "landscaping"),
    ("retaining-block*", "landscaping"),     # segmental retaining wall units
    ("capillary-break-stone", "earth"),
    # A crushed-stone FOOTING is structure, but it is not a pour and no concrete sub places
    # it: it is the same crew, the same hole and the same plate compactor as the beddings
    # above and the capillary break beside it, and it is inspected at the same hold. Sending
    # it to the concrete trade would schedule a footing into the pour sequence that has
    # nothing to pour, and put it in a package the excavator has already left.
    ("footing-crushed-stone", "earth"),
    ("*brick*", "masonry"),
    ("cmu*", "masonry"),
    ("standing-seam*", "roofing"),
    ("roof-*", "roofing"),
    ("concrete", "concrete"),
    ("tile*", "tile"),
    ("siding-*", "siding"),
    ("board-batten*", "siding"),
    ("corrugated-panel*", "siding"),
    ("pbr-panel*", "siding"),
    # A deck plank is the finished walking surface, not the deck's structure: it is laid
    # last, over a frame the carpenter already signed off, and it is the row an owner prices
    # against LVP and oak. The joists and the rim under it stay framing, where they belong.
    ("composite-deck*", "flooring"),
    ("aluminum-deck*", "flooring"),
    ("plywood-subfloor*", "framing"),
    ("cabinet-plywood", "millwork"),        # audit:2026-09-12#envelope_layers:cabinet-plywood
    ("*plywood*", "framing"),
    # An equipment stand's extrusion is set by the HVAC installer with the unit on it
    # (audit:2026-09-12#concrete:column:EQUIP_STAND_ALUM).
    ("aluminum-extrusion", "mechanical"),
    ("spf", "framing"), ("kdat", "framing"), ("lvl", "framing"), ("glulam*", "framing"),
    ("*-timber", "framing"), ("douglas*", "framing"),
    ("sauna-shiplap", "millwork"),
    ("pvc-panel", "millwork"),
    ("*-tg", "millwork"),
    ("pet-felt*", "millwork"),
    ("marble-look*", "tile"),               # audit:2026-09-12#wood_surfaces:marble-look-panel
)


def material_trade(material_ref: str | None) -> str | None:
    """The trade a material ref names on its face, or ``None`` when it does not."""
    if not material_ref:
        return None
    ref = material_ref.strip().lower().split(":", 1)[0]
    for pattern, trade in MATERIAL_TRADE_PATTERNS:
        if fnmatch.fnmatchcase(ref, pattern):
            return trade
    return None


# --- assembly layers ------------------------------------------------------------------

#: Layer function -> the trade it takes when neither material nor scope says otherwise.
#: Every ``LayerFunction`` plus the spellings the takeoff and the IR emit.
LAYER_FUNCTION_TRADE: dict[str, str] = {
    "structure": "framing",
    "sheathing": "framing",
    "membrane": "siding",
    # A drained plane is the DRAINAGE trade's, not siding's: it goes on with the tile, the
    # stone and the backfill, by the crew that is already in the hole, and it is inspected
    # at `insp/foundation_backfill` alongside them. Sending it to siding would schedule a
    # buried drainage board after the roof was on.
    "drainage": "drainage",
    "insulation": "insulation",
    "insulation (cavity)": "insulation",
    "airgap": "siding",
    "air_gap": "siding",
    "furring": "siding",
    "cladding": "siding",
    "finish": "drywall",
    "lining": "drywall",
}

_ROOF_SCOPES = ("roof",)
_CEILING_SCOPES = ("roof ceiling", "ceiling")
# "foundation wall" is ``takeoff/envelope.py``'s scope for a wall flagged ``is_foundation``,
# and it belongs here for the same reason "slab" does: the membrane on a foundation wall is
# applied by the concrete/earth crew against green concrete and buried the same week. Left
# out, it fell through to the siding branch below and the below-grade waterproofing
# scheduled after the roof was on — with ``insp/foundation_backfill`` ("Waterproofing,
# drainage and backfill") waiting on it from the other side.
_POUR_SCOPES = ("slab", "footing", "foundation wall")


def layer_trade(function: str | None, scope: str | None = None,
                material: str | None = None) -> str:
    """The trade an assembly layer belongs to. Material first, then function × scope."""
    from_material = material_trade(material)
    if from_material is not None:
        return from_material
    key = (function or "").strip().lower()
    where = (scope or "").strip().lower()
    if key.startswith("insulation"):
        return "insulation"
    if key == "cladding":
        return "roofing" if where in _ROOF_SCOPES else "siding"
    if key == "membrane":
        if where in _ROOF_SCOPES:
            return "roofing"
        if where in _POUR_SCOPES:
            return "concrete"        # under-slab vapour retarder, below-grade waterproofing
        if where in _CEILING_SCOPES:
            return "insulation"      # ceiling vapour retarder goes up with the blown fill
        return "siding"              # WRB / air barrier on a wall
    if key in ("finish", "lining"):
        return "millwork" if material else "drywall"
    if key == "structure":
        return "framing"
    return LAYER_FUNCTION_TRADE.get(key, FALLBACK_TRADE)


def layer_trades(layers, scope: str = "wall") -> tuple[str, ...]:
    """The trade SET of a layer stack, in sequence order, deduplicated. ``layers`` are
    resolved layers (``function``/``material_ref``) or catalog layers (``function`` is an
    enum)."""
    found: set[str] = set()
    for layer in layers:
        function = getattr(layer, "function", None)
        function = function.value if hasattr(function, "value") else function
        found.add(layer_trade(function, scope, getattr(layer, "material_ref", None)))
    # Sequence order, framing last: the sticks are their own node, so a body's primary
    # trade should be the skin a reader sees (siding, drywall, roofing), not the studs.
    return tuple(sorted(found, key=lambda t: (t == "framing", sequence_rank(t))))


def assembly_trades(plan, assembly_tag: str | None, scope: str) -> tuple[str, ...]:
    """The trade set of a catalog assembly's layer stack (a roof, whose resolved record
    carries no layers)."""
    assembly = plan.library.resolve_assembly(assembly_tag) if assembly_tag else None
    layers = getattr(assembly, "layers", ()) or ()
    return layer_trades(layers, scope) or (FALLBACK_TRADE,)


# --- solids -----------------------------------------------------------------------------

#: Categories a concrete ``structure_material`` turns into a pour (a cast column) — the
#: mirror of a laid deck in a ``slab`` row.
_CAST_BY_MATERIAL = frozenset({"column", "post", "beam"})
#: Categories whose material may say "not a pour": a plank deck, a sod green, an XPS wing.
#:
#: ** "footing" JOINED ON 2026-09-15 AND IT USED TO BE UNCONDITIONAL. ** Every footing
#: this engine had ever resolved was concrete, so a footing took its category's trade
#: and its material was never consulted. 2024 IRC R403.5 ends that: a consolidated
#: crushed-stone footing is a footing in every structural sense — under a wall, with a
#: width, a depth and a bearing plane, carrying load — and no concrete sub places it.
#: Without this it billed to the concrete trade, which would schedule it into a pour
#: sequence with nothing to pour, in a package the excavator has already left.
_LAID_BY_MATERIAL = frozenset({"slab", "pad", "footing"})


def solid_trades(category: str | None, material: str | None = None) -> tuple[str, ...]:
    """The trade set of a resolved solid: its category, overridden by a material that
    positively says otherwise. A row with no material has said nothing."""
    key = (category or "").strip().lower()
    trade = solid_trade(key)
    mat = (material or "").strip().lower()
    if key in _CAST_BY_MATERIAL and mat == "concrete":
        return ("concrete",)
    if key in _LAID_BY_MATERIAL and mat and mat != "concrete":
        laid = material_trade(mat) or "framing"
        # FPSF wing foam is laid on the bearing soil in the foundation sequence, by the
        # foundation contractor (adjudicated audit:2026-09-12#concrete:slab:SG_FROST_WING).
        return ("concrete",) if laid == "insulation" else (laid,)
    return (trade,)


# --- placeables and members -----------------------------------------------------------

#: Canvas-object domain -> viewer trade. Casework is domain ``furniture`` and the BOM files
#: it under millwork (``cost_codes``); the viewer keeps it with the furniture until a
#: ``FurnitureType.built_in`` flag exists. Accepted divergence, flagged in the plan.
CANVAS_DOMAIN_TRADE: dict[str, str] = {
    "plumbing": "plumbing",
    "electrical": "electrical",
    "mechanical": "mechanical",
    "appliance": "furniture",
    "furniture": "furniture",
    "opening": "openings",
}

#: Framing member categories that are the stair builder's, not the framer's.
STAIR_MEMBER_CATEGORIES = frozenset({
    "stringer", "tread", "riser", "winder", "newel", "landing", "landing_framing",
})

#: Member category -> trade, where a ``framing_by_size`` row's ``types`` are all one of
#: these. Anything mixed, or a category not named, is the framer's stick.
MEMBER_CATEGORY_TRADE: dict[str, str] = {
    **{category: "stairs" for category in STAIR_MEMBER_CATEGORIES},
    "gutter": "drainage",
    "insulation": "insulation",
    "airgap": "siding", "air_gap": "siding", "furring": "siding",
    "corner_trim": "siding", "fascia": "siding", "soffit": "siding", "cladding": "siding",
    "ridge_cap": "roofing",
}


def member_types_trade(types) -> str:
    """The trade of a lumber row from the member categories it rolls up."""
    trades = {MEMBER_CATEGORY_TRADE.get(str(t).lower(), "framing") for t in (types or ())}
    return trades.pop() if len(trades) == 1 else "framing"


#: Record families the viewer and the glTF emitter route without a category: the trade
#: each carries. Mirrored into the manifest as ``recordFamilyTrades``.
RECORD_FAMILY_TRADES: dict[str, tuple[str, ...]] = {
    "earth": ("earth",),
    # Washed stone under a footing with the perimeter tile bedded in it: the excavator
    # places it before the pour (so the BOM files the row under earth, ahead of concrete in
    # the sequence) and it is the head of the drainage run (so the viewer shows it under
    # either chip, drainage first).
    "footing_bedding": ("drainage", "earth"),
    "floor_deck": ("framing",),
    "room_floor": ("flooring",),
    "stair": ("stairs",),
    "soffit_framing": ("framing",),
    "brace": ("framing",),
    "solar_panel": ("electrical",),
    "light_run": ("electrical",),
    "paneling": ("millwork",),
    "opening": ("openings",),
    "wall_lumber": ("framing",),
}


def _validate() -> None:
    named = {t for _p, t in MATERIAL_TRADE_PATTERNS} | set(LAYER_FUNCTION_TRADE.values())
    named |= set(CANVAS_DOMAIN_TRADE.values()) | set(MEMBER_CATEGORY_TRADE.values())
    named |= {t for ts in RECORD_FAMILY_TRADES.values() for t in ts}
    unknown = sorted(named - TRADES)
    if unknown:
        raise ValueError(f"trade_rules names trades that do not exist: {unknown}")


_validate()
