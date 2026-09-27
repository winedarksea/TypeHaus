"""The shared catalog of pipe and duct fittings — the patterns, and what each one turns.

Same split as ``library/hardware/`` / ``hardware/catalog.py``: the record type is
:class:`~typehaus.hardware.fittings.FittingSpec` and the items are here.

**What is recorded and what is not.** A pattern's *angle* is definitional — ASTM D3311
(``Standard Specification for Drainage, Waste, and Vent (DWV) Plastic Fittings Patterns``)
is what makes a 1/4 bend a 90 degree fitting and a 1/16 bend a 22.5 degree one, and copying
that is not a measurement. A pattern's *laying length* (centre-to-face) is a measurement off
one manufacturer's submittal, it differs between makers at one pattern, and **this repo has
read none**: every ``center_to_face_in`` below is ``None`` with a ``data_note`` saying so.
One submittal HAS been read for a narrower question — where a stack branch's centreline sits
between its two socket stops (Charlotte Pipe, ``_STACK_DIMS``), which is what
``mep.drain_inlet_spacing`` grades two inlets on one barrel against.

That absence has a consequence worth stating plainly, because it is the reason Phase 5 of
the routing roadmap draws no fitting bodies: without a laying length there is no way to turn
a mitred vertex into a solid, and ``mep.fitting_pattern`` reports exactly that rather than
inventing a dimension. Reading four submittals closes it; guessing does not.

**Only patterns this repo is sure of.** The 1/5 bend (72 degrees) is in D3311's pattern list
and is deliberately absent below: it is a specialty part in PVC DWV and putting it in the
catalog would let catlin's 79 degree and 71 degree vertices settle as a stock fitting on the
strength of a row nobody checked was orderable. They stay UNKNOWN, which is what they are.

**Sizes.** DWV starts at 1 1/4 inch, because that is the smallest size D3311 patterns are
made in. A 3/4 inch condensate drain is plumbed in supply tube and its turns are *bends*,
not fittings — so no 3/4 inch DWV row exists here and a 3/4 inch drain's vertices report a
coverage gap rather than matching a part that is not made.
"""

from __future__ import annotations

from typehaus.hardware.fittings import (
    KIND_COMBO,
    KIND_ELBOW,
    KIND_STREET_TEE,
    KIND_STREET_WYE,
    KIND_TEE,
    KIND_WYE,
    SERVICE_DRAIN,
    SERVICE_DUCT,
    SERVICE_SUPPLY,
    SERVICE_VENT,
    FittingSpec,
)

#: The DWV bend patterns, as the fraction of a circle each name states: a 1/4 bend turns a
#: quarter of 360 degrees. ASTM D3311 names all four; the 1/6 is the one people forget is a
#: standard pattern rather than a made bend.
_DWV_BENDS: tuple[tuple[str, float], ...] = (
    ("1/4", 90.0),
    ("1/6", 60.0),
    ("1/8", 45.0),
    ("1/16", 22.5),
)

#: Nominal DWV sizes, inches. 1 1/4 is the smallest D3311 pattern; 4 is the largest a
#: dwelling's building drain takes in this repo's houses.
_DWV_SIZES: tuple[float, ...] = (1.25, 1.5, 2.0, 3.0, 4.0)

_DWV_SOURCE = "ASTM D3311 DWV plastic fitting patterns"
_NO_SUBMITTAL = ("laying length not recorded: no manufacturer submittal has been read into "
                 "this repo, so this pattern names a part and does not dimension one")


def _dwv_elbows() -> list[FittingSpec]:
    """Every D3311 bend, at every DWV size, for both gravity services.

    Drain and vent are two rows rather than one shared row because they are two services on
    the same part: a vent's 1/4 bend is the same casting as a drain's, and a take-off that
    merged them would bill one line for two systems whose *runs* are priced separately.
    """
    out: list[FittingSpec] = []
    for service in (SERVICE_DRAIN, SERVICE_VENT):
        for name, angle in _DWV_BENDS:
            for size in _DWV_SIZES:
                out.append(FittingSpec(
                    tag=f"FIT-DWV-{service.upper()}-{name.replace('/', '')}-{size:g}",
                    name=f"{name} bend, {size:g}\" DWV",
                    service=service, kind=KIND_ELBOW, nominal_in=size,
                    angle_deg=angle,
                    # 10 degrees, the tolerance the fitting take-off has always used, and
                    # for the reason recorded there: a 1/4 bend taking a stack into a branch
                    # pitched at 2 in/ft measures 80.5 degrees, not 90. Past that the pitch
                    # is no longer something a socket absorbs.
                    snap_deg=10.0,
                    source=_DWV_SOURCE, data_note=_NO_SUBMITTAL))
    return out


#: Charlotte Pipe SUB-PAC-PVC-DWV (06/2026), PVC rows at full size (N x N x N), inches, as
#: (branch to top stop, branch to bottom stop or spigot end), each derived from the page's
#: letter dimensions as noted. Read off the drawings 2026-09-26.
_CHARLOTTE = "Charlotte Pipe SUB-PAC-PVC-DWV (06/2026)"
_STACK_DIMS: dict[str, tuple[str, dict[float, tuple[float, float]]]] = {
    # 400 Sanitary Tee, p. 37: A = branch c/l to bottom stop, B = stop to stop.
    KIND_TEE: ("part 400, p. 37: below = A, above = B - A",
               {1.5: (1.0, 1.75), 2.0: (1.375, 2.3125), 3.0: (1.8125, 3.0625),
                4.0: (2.25, 3.875)}),
    # 600 Wye, p. 41: A = stop to stop, B = bottom stop to branch c/l intersection.
    KIND_WYE: ("part 600, p. 41: below = B, above = A - B",
               {1.5: (2.875, 1.125), 2.0: (3.625, 1.375), 3.0: (5.0, 1.625),
                4.0: (6.375, 1.875)}),
    # 501 Combination Wye & 1/8 Bend, p. 40: B = stop to stop, C = branch outlet c/l to
    # bottom stop — the outlet sits ABOVE the top stop.
    KIND_COMBO: ("part 501, p. 40: below = C, above = B - C",
                 {1.5: (-0.4375, 3.9375), 2.0: (-0.6875, 5.125), 3.0: (-1.0625, 7.5625),
                  4.0: (-1.5, 10.0)}),
    # 403 Sanitary Tee, Street, p. 37: B = spigot end to top stop, C = branch c/l to spigot end.
    KIND_STREET_TEE: ("part 403, p. 37: below = C (to spigot end), above = B - C",
                      {1.5: (1.0, 2.5), 2.0: (1.34375, 3.21875), 3.0: (1.8125, 4.5625),
                       4.0: (2.25, 5.625)}),
    # 602 Wye, Street, p. 41: A = spigot end to top stop, B = spigot end to branch c/l.
    KIND_STREET_WYE: ("part 602, p. 41: below = B (to spigot end), above = A - B",
                      {1.5: (2.875, 1.875), 2.0: (3.625, 2.25), 3.0: (5.0, 3.125),
                       4.0: (6.3125, 3.625)}),
}
#: Socket depth: part 116 Cap, p. 32, dimension C (PVC) — a socket with no stop, so its
#: whole depth is what a pipe end fills. The one socket depth the submittal publishes.
_SOCKET_DEPTH: dict[float, float] = {1.5: 1.3125, 2.0: 1.375, 3.0: 1.90625, 4.0: 2.03125}
_STACK_NOTE = ("center_to_face_in not recorded: the submittal row is read as stack stations "
               "(branch_to_top_in / branch_to_bottom_in), not a laying length")
_STACK_LABELS = {KIND_COMBO: ("COMBO", "combination wye & 1/8 bend", 90.0),
                 KIND_STREET_TEE: ("STTEE", "street sanitary tee", 90.0),
                 KIND_STREET_WYE: ("STWYE", "street wye", 45.0)}


def _stack_fields(kind: str, size: float) -> dict:
    """The Charlotte stack stations for a full-size row, or nothing where none was read."""
    note, rows = _STACK_DIMS.get(kind, ("", {}))
    if size not in rows:
        return {"source": _DWV_SOURCE, "data_note": _NO_SUBMITTAL}
    top, bottom = rows[size]
    return {"branch_to_top_in": top, "branch_to_bottom_in": bottom,
            "spigot_bottom": kind in (KIND_STREET_TEE, KIND_STREET_WYE),
            "socket_depth_in": _SOCKET_DEPTH[size],
            "source": f"{_CHARLOTTE} {note}", "data_note": _STACK_NOTE}


def _dwv_stack_patterns() -> list[FittingSpec]:
    """The combo and the two street patterns, full size only — what the submittal was read for."""
    return [FittingSpec(
        tag=f"FIT-DWV-{code}-{size:g}x{size:g}", name=f"{size:g}\" DWV {label}",
        service=SERVICE_DRAIN, kind=kind, nominal_in=size, angle_deg=angle,
        branch_in=size, snap_deg=10.0, **_stack_fields(kind, size))
        for kind, (code, label, angle) in _STACK_LABELS.items()
        for size in sorted(_STACK_DIMS[kind][1])]


def _dwv_branches() -> list[FittingSpec]:
    """Wyes and sanitary tees, every branch size up to the run size.

    The wye is D3311's 45 degree branch and the sanitary tee its 90 degree one; both are
    listed at every reducing combination because that is how they are ordered (a 3x2 wye is
    a part, not a 3 inch wye with something done to it).
    """
    out: list[FittingSpec] = []
    for run_size in _DWV_SIZES:
        for branch in _DWV_SIZES:
            if branch > run_size:
                continue
            for kind, angle, label in ((KIND_WYE, 45.0, "wye"),
                                       (KIND_TEE, 90.0, "sanitary tee")):
                out.append(FittingSpec(
                    tag=f"FIT-DWV-{label.split()[-1].upper()}-{run_size:g}x{branch:g}",
                    name=f"{run_size:g}x{branch:g}\" DWV {label}",
                    service=SERVICE_DRAIN, kind=kind, nominal_in=run_size,
                    angle_deg=angle, branch_in=branch, snap_deg=10.0,
                    **(_stack_fields(kind, run_size) if branch == run_size
                       else {"source": _DWV_SOURCE, "data_note": _NO_SUBMITTAL})))
    return out


#: Copper tube sizes a dwelling's supply runs in, inches (CTS nominal).
_SUPPLY_SIZES: tuple[float, ...] = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)

_SUPPLY_SOURCE = "ASME B16.22 wrought copper solder-joint pressure fittings"


def _supply_elbows() -> list[FittingSpec]:
    """The two elbows B16.22 makes, and only those two.

    **There is no 22.5 degree copper elbow in B16.22.** A shallow turn in tube is a *bend* —
    the tube itself curved, to a radius the tube's own product data bounds — which is a
    different thing from a fitting and is graded as one. Catlin's ``elbow-22.5-1in`` row
    came out of a take-off that snapped an angle to the nearest of three numbers without
    ever asking whether the middle one was a part.
    """
    return [FittingSpec(
        tag=f"FIT-CU-{int(angle)}-{size:g}",
        name=f"{angle:g} degree elbow, {size:g}\" copper",
        service=SERVICE_SUPPLY, kind=KIND_ELBOW, nominal_in=size, angle_deg=angle,
        # Tighter than DWV's: a pressure line carries no pitch for a socket to absorb, so a
        # turn measuring 5 degrees off a stock elbow is a bent tube and not a fitting.
        snap_deg=5.0,
        source=_SUPPLY_SOURCE, data_note=_NO_SUBMITTAL)
        for angle in (90.0, 45.0) for size in _SUPPLY_SIZES]


def _supply_tees() -> list[FittingSpec]:
    """B16.22 tees, every reducing combination up to the run size."""
    return [FittingSpec(
        tag=f"FIT-CU-TEE-{run_size:g}x{branch:g}",
        name=f"{run_size:g}x{branch:g}\" copper tee",
        service=SERVICE_SUPPLY, kind=KIND_TEE, nominal_in=run_size, angle_deg=90.0,
        branch_in=branch, snap_deg=5.0,
        source=_SUPPLY_SOURCE, data_note=_NO_SUBMITTAL)
        for run_size in _SUPPLY_SIZES for branch in _SUPPLY_SIZES if branch <= run_size]


#: Round duct sizes this repo's ventilation runs in, inches.
_DUCT_SIZES: tuple[float, ...] = (3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0)

_DUCT_SOURCE = ("SMACNA HVAC Duct Construction Standards — round gored elbow, "
                "centreline radius 1.5 x diameter")


def _duct_elbows() -> list[FittingSpec]:
    """Gored round elbows at the standard centreline radius.

    The one dimensional field in this whole file that is **not** ``None``: a gored elbow's
    centreline radius is 1.5 times the diameter *by construction standard*, not by one
    maker's submittal, so it is the same copy-a-published-rule the angles are. It is also
    the field a flexible or long-sweep turn is judged against, which is why it is worth
    carrying alone.
    """
    return [FittingSpec(
        tag=f"FIT-DUCT-{int(angle)}-{size:g}",
        name=f"{angle:g} degree gored elbow, {size:g}\" round",
        service=SERVICE_DUCT, kind=KIND_ELBOW, nominal_in=size, angle_deg=angle,
        # A gored elbow is fabricated to the angle asked for; the snap is the drawing
        # tolerance rather than what a socket absorbs.
        snap_deg=5.0,
        bend_radius_in=1.5 * size,
        source=_DUCT_SOURCE,
        data_note="centre-to-face depends on the gore count the fabricator uses")
        for angle in (90.0, 45.0, 30.0) for size in _DUCT_SIZES]


#: Tube that turns by being BENT, by material: (minimum centreline radius as a multiple of the
#: tube's OD, source). Minn. R. 4714.0609 allows flexible tubing to change direction without
#: fittings "in accordance with the manufacturer's instructions", so the maker's rule governs.
#: Uponor's 6 x OD is the tightest-reading of the three PEX-a makers (REHAU and Viega publish
#: 5 x OD cold or with a bend support), so a bend that passes here passes for any of them.
_PEX_BEND = (6.0, "Uponor Professional Plumbing Installation Guide (PLU_InsG_P731_0213) "
                  "p. 9: \"The minimum bend radius of Uponor AquaPEX tubing in any direction "
                  "is six times the outside diameter (6 x OD).\"")
TUBE_BEND_RULES: dict[str, tuple[float, str]] = {"pex": _PEX_BEND, "pex-a": _PEX_BEND}


#: Every catalogued fitting. Sorted by tag so a take-off's row order never depends on the
#: order the helpers above happen to run in.
MEP_FITTINGS: tuple[FittingSpec, ...] = tuple(sorted(
    [*_dwv_elbows(), *_dwv_branches(), *_dwv_stack_patterns(), *_supply_elbows(),
     *_supply_tees(), *_duct_elbows()],
    key=lambda item: item.tag))
