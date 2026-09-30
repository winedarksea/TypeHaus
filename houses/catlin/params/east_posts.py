"""The canopy's EAST supports, in whichever of three systems `EAST_POST_SYSTEM` names.

`params/north_entry_frame.py` owns the one switch — `EAST_POST_SYSTEM`, one of
`"steel" | "kdat" | "cast"` — and calls `east_supports` once; `params/breezeway.py` calls
`east_head_parts` once for the joints. Everything that differs between the three lives in
`_EAST_VARIANTS`, beside its siblings, so a switch is "change one word, `haus fmt`,
`haus check`" and lands on a state `tests/test_catlin_east_post_variants.py` has already
graded at 0 FAIL. The arithmetic for all three is `notes/canopy_garage_diaphragm.md`.

**Tags and uids are stable across variants.** `BM-BW-RE` always bears on `PT-BW-RE` /
`PT-BW-RNE` (uids `BWPT03AAAA` / `BWPT04AAAA`), whatever they are made of, so the header's
`bearing_refs` and the IFC GlobalIds never move. The pads keep `PD-BW-RE` / `-RNE`. What
exists in one variant only — the two piers under a post, and each variant's head and base
parts — carries a uid minted once with `typehaus.model.ids.new_uid()` and pasted into the
table; `haus fmt` never visits `params/`.

**steel**: HSS 4x4x1/4 A500 Gr C, galvanized after
fabrication (ASTM A123) and powder-coated, pinned at both ends on a 12" pier whose top is
3'-0" above grade — clear of the salted walk's splash and the snow pile. A welded U-saddle
with HDG through-bolts and a butyl isolation layer at the head; a welded base plate on
cast-in HDG anchors and levelling nuts over an open, drained gap at the foot — the house's
standoff rule, no grout pad. Stainless and galvanized never share a joint.
**kdat** (owner 2026-09-29): a 6x6 KDAT post as `PT-BW-CW`, on the same pier, an
`ACE6Z`/`AC6Z` head on the glulam and a cast-in `CBSQ66-SDS2` base (2026-09-30), with a
removable, drained PVC column wrap. The wrap is
nonstructural and is kept clear of both the cap and standoff base.
**cast**: the 2026-09-20 design — 12" rounds poured full height from a common −10'-2" plane,
fixed at the base, shim pack + cast-in `HETA20Z` pair at the head.
"""

from typehaus import Connector, ConnectorKind, Pad, Post, ft, pt

from params.column_heads import CBSQ66_HEAD, HETA20Z_PAIR_HEAD

#: The pier top under a pinned east post: 3'-0" over `Site.grade` (−2'-10"), i.e. +0'-2".
PIER_TOP_FT = 2 / 12

#: Variant-specific values only. Every uid here was minted once and must never be re-typed.
_EAST_VARIANTS = {
    "steel": dict(
        post_size="HSS4x4x0.25", post_assembly="POST_STEEL_HSS", pier_size="12 round",
        piers={"RE": ("34ET0SKQAZ", "PT-BW-PE"), "RNE": ("1NKNZQCQTQ", "PT-BW-PNE")},
        moment_piers=frozenset(),
        head=("POST_CAP", "HSS4-SADDLE-HDG",
              {"RE": ("ESY785KNZ4", "CN-BW-SADDLE-RE"), "RNE": ("QN548ZBCM5", "CN-BW-SADDLE-RNE")}),
        base=("POST_BASE", "HSS4-BASEPL-HDG",
              {"RE": ("FPZXKCRQH6", "CN-BW-SBASE-RE"), "RNE": ("3E7T1DXNSZ", "CN-BW-SBASE-RNE")}),
        pier_head=None,
        prices=('"HSS4x4x0.25"', "HSS4-SADDLE-HDG", "HSS4-BASEPL-HDG"),
        roof_note=("EAST header lands on PT-BW-RE and PT-BW-RNE, HSS 4x4x1/4 A500 Gr C STEEL "
                   "POSTS, galvanized after fabrication (ASTM A123) + powder-coated, PINNED "
                   "both ends: welded U-saddle with 2 - 5/8in HDG through-bolts over butyl at "
                   "the head; welded base plate on 2 - 5/8in F1554 Gr 36 HDG cast-in anchors "
                   "and levelling nuts over an OPEN, DRAINED gap at the foot — NEVER GROUT "
                   "IT. The posts stand on 12in piers PT-BW-PE / -PNE whose tops are 3ft 0in "
                   "above grade. Stainless and galvanized never share a joint"),
        landing_note=("PT-BW-PE (house plane) and PT-BW-PNE (garage plane) are 12in piers "
                      "to +0ft 2in under the pinned steel east posts"),
    ),
    "kdat": dict(
        post_size="6x6", post_assembly="POST_KDAT_WRAPPED_PVC",
        # 14": the CBSQ's 3" side cover (params/north_entry_frame.py::_PIER_SIZE).
        pier_size="14 round",
        piers={"RE": ("34ET0SKQAZ", "PT-BW-PE"), "RNE": ("1NKNZQCQTQ", "PT-BW-PNE")},
        moment_piers=frozenset(),
        # The header ENDS on PT-BW-RE (an ACE6 end cap) and runs on past PT-BW-RNE (an AC6):
        # ESR-2604 §3.1.3. The uids are the CCQ caps' own: one part per head, re-typed.
        head=("POST_CAP", {"RE": "ACE6Z", "RNE": "AC6Z"},
              {"RE": ("X0QPPRBG1X", "CN-BW-CAP-E"), "RNE": ("11X4C8QHB6", "CN-BW-CAP-NE")}),
        base=("POST_BASE", "CBSQ66-SDS2",
              {"RE": ("5WR0KMFPJJ", "CN-BW-BASE-E"), "RNE": ("T1V9W4G4TW", "CN-BW-BASE-NE")}),
        pier_head=CBSQ66_HEAD,
        prices=("AC6Z", "ACE6Z", "A35Z", "CBSQ66-SDS2"),
        roof_note=("EAST header lands on PT-BW-RE and PT-BW-RNE, 6x6 KDAT posts PINNED both "
                   "ends: an ACE6Z end cap (RE) and an AC6Z cap (RNE), MAX nailing, HDG 16d, "
                   "with A35Z angles on the free post faces up to the glulam soffit for the "
                   "across-beam direction; CBSQ66-SDS2 bases CAST INTO 12in piers PT-BW-PE / "
                   "-PNE, tops 3ft 0in above grade, straps >= 3in from the pier edge. Each "
                   "east post has a NONSTRUCTURAL removable PVC column wrap: leave its bottom "
                   "OPEN above the pier wash so the 1in standoff and post end drain and can be "
                   "inspected; vent at the top below the cap; do not fasten through a cap or "
                   "base. Verify post MC <= 19% before closing the wrap (ESR-2604 §3.2.2)"),
        landing_note=("PT-BW-PE (house plane) and PT-BW-PNE (garage plane) are 12in piers "
                      "to +0ft 2in under the pinned KDAT east posts"),
    ),
    "cast": dict(
        post_size="12 round", post_assembly="PIER_CONCRETE_12", pier_size="12 round",
        piers={},
        # The one common plane both shafts bear on (entry_column_base_fixity.md §6a): equal
        # shafts are equal stiffness, 50/50 E-W whatever the diaphragm does.
        deep_base_ft=-(10 + 2 / 12),
        moment_piers=frozenset({"PT-BW-RE", "PT-BW-RNE"}),
        head=None, base=None, pier_head=HETA20Z_PAIR_HEAD,
        prices=("SS316-SHIM-35", "HETA20Z"),
        roof_note=("EAST header lands on PT-BW-RE and PT-BW-RNE, 12in CAST CONCRETE COLUMNS "
                   "running unbroken from a common -10ft 2in pad plane to the header soffit, "
                   "FIXED at the base, sharing E-W with W-G-S by rigidity; a shim pack + a "
                   "cast-in HETA20Z strap pair at the top, NOT a post cap. Cast each pad "
                   "BEFORE the strip beside it bears (house side 1ft 4-9/16in below "
                   "FT-B-N1..N4; garage side 3ft 2in below FT-GF-S1/-S3)"),
        landing_note=("EXCEPT the east line: PT-BW-RE and PT-BW-RNE bottom at -11ft 2in on "
                      "their own common plane and carry on ABOVE the bearing plane as "
                      "full-height columns — one continuous pour each, pad to header soffit"),
    ),
}

#: `head` / `base` connector kinds, by name, so the table stays a plain literal.
_KINDS = {"POST_CAP": ConnectorKind.POST_CAP, "POST_BASE": ConnectorKind.POST_BASE}


def variant(system):
    if system not in _EAST_VARIANTS:
        raise ValueError(f"EAST_POST_SYSTEM must be one of {sorted(_EAST_VARIANTS)}, "
                         f"not {system!r}")
    return _EAST_VARIANTS[system]


def full_height_columns(system):
    """The east supports that are cast columns running footing to header — `cast` only."""
    return ("PT-BW-RE", "PT-BW-RNE") if system == "cast" else ()


def east_radius_ft(system):
    """Half the round the walk is notched around at grade: the pier, or the cast column."""
    return float(variant(system)["pier_size"].split()[0]) / 24.0


def moment_piers(system):
    return variant(system)["moment_piers"]


def east_supports(system, *, x_ft, stations, header_soffit_ft, moment_cage, house_pad,
                  garage_pad):
    """``(posts, piers, pads)`` for the east line.

    ``stations`` maps ``"RE"``/``"RNE"`` to ``(uid, y_ft)`` of the post the header bears on;
    ``house_pad`` / ``garage_pad`` are ``(pad uid, outline factory, moment-pad top ft,
    thickness ft)`` — the plane each side's pad sits on in the pinned variants.
    """
    spec = variant(system)
    posts, piers, pads = [], [], []
    for key, (uid, y_ft) in stations.items():
        pad_uid, outline, pad_top_ft, pad_thick_ft = house_pad if key == "RE" else garage_pad
        pad_tag = f"PD-BW-{key}"
        if system == "cast":
            base_ft = spec["deep_base_ft"]
            posts.append(Post(
                uid=uid, tag=f"PT-BW-{key}", position=pt(ft(x_ft), ft(y_ft)),
                head_connector=spec["pier_head"], size="12 round",
                height=ft(header_soffit_ft - base_ft), assembly="PIER_CONCRETE_12",
                vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.',
                reinforcement=moment_cage, supported_by=pad_tag))
            pads.append(Pad(uid=pad_uid, tag=pad_tag, outline=outline(y_ft),
                            thickness=ft(1.0), assembly="PIER_BASE_12",
                            bottom_elevation=ft(base_ft - 1.0)))
            continue
        pier_uid, pier_tag = spec["piers"][key]
        piers.append(Post(
            uid=pier_uid, tag=pier_tag, position=pt(ft(x_ft), ft(y_ft)),
            head_connector=spec["pier_head"], size=spec["pier_size"],
            height=ft(PIER_TOP_FT - pad_top_ft), assembly="PIER_CONCRETE_12",
            vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.',
            reinforcement=moment_cage, supported_by=pad_tag))
        pads.append(Pad(uid=pad_uid, tag=pad_tag, outline=outline(y_ft),
                        thickness=ft(pad_thick_ft), assembly="PIER_BASE_12",
                        bottom_elevation=ft(pad_top_ft - pad_thick_ft)))
        posts.append(Post(
            uid=uid, tag=f"PT-BW-{key}", position=pt(ft(x_ft), ft(y_ft)),
            size=spec["post_size"], height=ft(header_soffit_ft - PIER_TOP_FT),
            assembly=spec["post_assembly"], supported_by=pier_tag))
    return posts, piers, pads


def east_head_parts(system, *, x_ft, stations, header_soffit_ft, cast_parts):
    """The head and base connectors of the east line. ``cast_parts`` builds today's pack +
    HETA pair and is called only for `cast`, so its uids stay where they always were."""
    spec = variant(system)
    if system == "cast":
        return cast_parts()
    out = []
    for part, elevation in ((spec["head"], header_soffit_ft), (spec["base"], PIER_TOP_FT)):
        kind, sizes, by_key = part
        for key, (uid, tag) in by_key.items():
            post = f"PT-BW-{key}"
            below = spec["piers"][key][1]
            size = sizes[key] if isinstance(sizes, dict) else sizes
            # A CBSQ is oriented: its F2 row along the line the screen resists (N-S, y).
            out.append(Connector(
                uid=uid, tag=tag, kind=_KINDS[kind],
                position=pt(ft(x_ft), ft(stations[key])), elevation=ft(elevation), size=size,
                axis="y" if size == "CBSQ66-SDS2" else None,
                connects=(("BM-BW-RE", post) if kind == "POST_CAP" else (post, below))))
    return out


def roof_note(system):
    """The east-line sentence `AN-BW-ROOF` prints, so the drawing follows the switch."""
    return variant(system)["roof_note"]


def landing_note(system):
    """The east-pier sentence `AN-BW-STRUCTURE` prints."""
    return variant(system)["landing_note"]
