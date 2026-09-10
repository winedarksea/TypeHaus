"""S-001 — general structural notes, derived and unconditional.

The sheet a plan checker and a framer both open first, and the set had none: what it used
to have was S-002, gated on "any specification section exists", which on catlin printed a
single bullet. Everything here is read out of the resolved model, the jurisdiction profile
or the wind basis the calculations themselves used — nothing is a constant typed twice.

Decision #32 governs the whole sheet: a value the model does not carry prints
``not stated``, never a plausible default. MNSPECT's rule that no note may say "per code"
in lieu of a dimension is the same rule from the other side, and it is why every block
below either prints a number or admits it has none.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING, Any

from typehaus.emit.draw.schedules.blocks import _lay_out_blocks
from typehaus.emit.draw.sheet_writer import schedule_sheet
from typehaus.resolve.concrete import concrete_spec_of
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff import hardware_takeoff
from typehaus.wind import wind_basis

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.checks.jurisdiction import JurisdictionProfile
    from typehaus.checks.registry import Preferences

#: What an unstated value prints as. One string, so a reader learns it once and so a grep
#: for it finds every gap on the sheet.
NOT_STATED = "not stated"

#: How many assembly tags a block names before it stops listing them. A note that prints
#: nineteen tags on one line is a note nobody reads to the end of.
_MAX_TAGS_LISTED = 6

#: Characters one column holds at the 6 pt monospace ``_lay_out_blocks`` sets. A longer
#: line does not wrap — it runs straight into the next column — so every line is clipped
#: to it on the way out, once, rather than by each block guessing its own budget.
_MAX_LINE_CHARS = 86


def _value(text: object, unit: str = "") -> str:
    if text is None or text == "":
        return NOT_STATED
    return f"{text}{unit}"


def _row(label: str, value: str) -> str:
    return f"{label:<26}{value}"


def _tags(tags: list[str]) -> str:
    kept, budget = [], _MAX_LINE_CHARS - 20
    for tag in tags[:_MAX_TAGS_LISTED]:
        if budget - len(tag) - 2 < 0:
            break
        kept.append(tag)
        budget -= len(tag) + 2
    rest = len(tags) - len(kept)
    return ", ".join(kept) + (f", +{rest} more" if rest else "")


def _assemblies_in_use(model: ResolvedModel) -> list[str]:
    """Every assembly tag some authored element names. Not the library — the building."""
    tags = {tag for element in model.plan.all_elements()
            if isinstance(tag := getattr(element, "assembly", None), str) and tag}
    return sorted(tags)


def _snow_case_rows(site: object, preferences: Preferences | None) -> list[str]:
    """Flat-roof, drift and unbalanced, as far as this model honestly knows them.

    ``p_f`` is DERIVED (0.7 C_e C_t I_s p_g at C_e = I_s = 1.0 and C_t = 1.0, a heated
    building) because that arithmetic is a one-liner nobody disagrees with. The drift is
    AUTHORED, because the engine computes no part of it, and it prints the note that derives
    it rather than a bare number. Unbalanced and sliding print as not computed, which is the
    truth — a blank row would read as "zero".
    """
    ground = getattr(site, "ground_snow_load_psf", None)
    rows: list[str] = []
    if ground:
        rows.append(_row("FLAT-ROOF SNOW (P_F)",
                         f"{0.7 * float(ground):.0f} psf "
                         f"(0.7 C_e C_t I_s P_G, C_e = C_t = I_s = 1.0)"))
    structural = getattr(preferences, "structural", None)
    drift = getattr(structural, "roof_beam_snow_psf", None)
    if drift:
        rows.append(_row("DRIFT / STEP SNOW",
                         f"{float(drift):.1f} psf DESIGN AT THE NORTH ENTRY CANOPY "
                         f"(ASCE 7 SEC 7.7 ROOF-STEP DRIFT OFF THE HOUSE GABLE) — "
                         f"SEE NOTES/NORTH_ENTRY_PIERS.MD SEC 3"))
        rows.append(_row("", "THE DRIFT TRIANGLE REACHES 3'-10\" INTO THE GARAGE ROOF: "
                             "ITS TWO SOUTHERNMOST TRUSSES ARE DRIFT TRUSSES"))
    else:
        rows.append(_row("DRIFT / STEP SNOW", NOT_STATED))
    rows.append(_row("UNBALANCED / SLIDING SNOW",
                     "NOT COMPUTED BY THIS MODEL — DESIGNER OF RECORD"))
    return rows


def design_criteria_block(model: ResolvedModel,
                          profile: JurisdictionProfile | None,
                          preferences: Preferences | None = None) -> list[str]:
    """IRC Table R301.2(1) / IBC 1603.1 climatic and geographic design criteria.

    ** GROUND SNOW ALONE IS NOT WHAT A TRUSS FABRICATOR NEEDS. ** This block printed p_g and
    stopped, and a fabricator reading "50 psf ground snow" prices ordinary trusses. On this
    house the governing roof case is a Sec 7.7 roof-step drift off the north gable that
    roughly doubles the balanced load over the entry canopy and reaches 3.8 ft into the
    garage roof besides. The flat-roof, drift and unbalanced rows below exist so the number
    reaches the sheet the bid is taken from.
    """
    site = getattr(getattr(model.plan, "project", None), "site", None)
    basis = wind_basis(site) if site is not None else None
    lines = [
        _row("CODE EDITION", _value(getattr(profile, "edition", None))),
        _row("MODEL CODE", _value(getattr(profile, "irc_base", None))),
        _row("GROUND SNOW LOAD", _value(getattr(site, "ground_snow_load_psf", None), " psf")),
    ]
    lines.extend(_snow_case_rows(site, preferences))
    # V_ult through ``wind_basis`` rather than off the site directly: a speed with no
    # exposure produces no pressure, and the calcs read it through the same gate. A sheet
    # that printed the half-authored speed would print a number no calculation used.
    if basis is not None:
        lines.append(_row("DESIGN WIND (V_ult)", f"{basis.speed_mph:.0f} mph, "
                                                 f"EXPOSURE {basis.exposure}, "
                                                 f"RISK CATEGORY {basis.risk_category}"))
    else:
        lines.append(_row("DESIGN WIND (V_ult)", NOT_STATED))
    lines.extend([
        _row("FROST DEPTH", _value(getattr(profile, "frost_depth_in", None), " in")),
        _row("SOIL BEARING", _value(getattr(site, "soil_bearing_psf", None)
                                    or getattr(profile, "soil_bearing_psf", None), " psf")),
        _row("SOIL CLASS", _value(getattr(site, "soil_class", None)
                                  or getattr(profile, "soil_class", None))),
        _row("WINTER DESIGN TEMP", _value(_temp_f(getattr(site, "design_temp_heating", None)),
                                          " F")),
        _row("SUMMER DESIGN TEMP", _value(_temp_f(getattr(site, "design_temp_cooling", None)),
                                          " F")),
    ])
    from typehaus.checks.structural.deck_tables import (
        DECK_DEAD_LOAD_PSF,
        DECK_LIVE_LOAD_PSF,
    )
    lines.append(_row("DECK / BALCONY LOAD",
                      f"{DECK_LIVE_LOAD_PSF:.0f} psf LIVE + {DECK_DEAD_LOAD_PSF:.0f} psf "
                      "DEAD (IRC R507.1 / TABLE R301.5)"))
    # The honest gap. Habitable-room, sleeping-room, stair and attic live loads are IRC
    # Table R301.5 rows this model carries nowhere, and printing the table from memory
    # would be exactly the "per code" note MNSPECT rejects.
    lines.append(_row("OTHER R301.5 LOADS", NOT_STATED + " — not carried by this model"))
    lines.append("SEISMIC, WEATHERING, TERMITE, ICE BARRIER, FLOOD, AIR-FREEZING INDEX AND")
    lines.append("MEAN ANNUAL TEMPERATURE ARE " + NOT_STATED.upper() + " IN THIS MODEL.")
    return lines


def _temp_f(temperature: Any) -> float | None:
    if temperature is None:
        return None
    for attribute in ("fahrenheit", "f"):
        value = getattr(temperature, attribute, None)
        if value is not None:
            return round(float(value), 1)
    return None


def concrete_block(model: ResolvedModel) -> list[str]:
    """One paragraph per distinct ``ConcreteSpec``, with the pours that use it.

    Grouped on the spec and not on the assembly: catlin has nineteen concrete assemblies
    and four mixes, and a note that repeated the same mix nineteen times would be a note a
    reader stops reading at the third repeat.
    """
    grouped: dict[tuple, list[str]] = {}
    for tag in _assemblies_in_use(model):
        spec = concrete_spec_of(model.plan, tag)
        if spec is None:
            continue
        key = (spec.fc_psi, spec.w_cm_max, spec.air_content_pct, spec.exposure_f,
               spec.exposure_s, spec.exposure_w, spec.exposure_c,
               round(spec.cover.inches, 3) if spec.cover is not None else None, spec.bar_coating,
               spec.scm,
               round(spec.max_aggregate.inches, 3) if spec.max_aggregate is not None
               else None)
        grouped.setdefault(key, []).append(tag)
    if not grouped:
        return ["No concrete pour in this model states a mix (Assembly layer ConcreteSpec).",
                f"MIX, EXPOSURE CLASS, COVER AND BAR COATING ARE ALL {NOT_STATED.upper()}."]
    lines: list[str] = []
    for index, (key, tags) in enumerate(sorted(grouped.items(), key=lambda item: -item[0][0]),
                                        start=1):
        (fc, w_cm, air, exp_f, exp_s, exp_w, exp_c, cover, coating, scm, aggregate) = key
        lines.append(f"MIX C{index}  {fc:,.0f} psi  w/cm {_value(w_cm)}  "
                     f"AIR {_value(air, '%')}")
        lines.append(f"  ACI 318-19 EXPOSURE  F:{_value(exp_f)}  S:{_value(exp_s)}  "
                     f"W:{_value(exp_w)}  C:{_value(exp_c)}")
        lines.append(f"  COVER {_value(cover, chr(34))}   BAR COATING {_value(coating)}")
        lines.append(f"  SCM {_value(scm)}   MAX AGGREGATE {_value(aggregate, chr(34))}")
        lines.append(f"  POURS: {_tags(tags)}")
    return lines


def wood_framing_block(model: ResolvedModel) -> list[str]:
    """Every distinct ``FramingSpec`` on a STRUCTURE layer some element actually uses."""
    library = model.plan.library
    grouped: dict[tuple, list[str]] = {}
    for tag in _assemblies_in_use(model):
        assembly = library.resolve_assembly(tag)
        if assembly is None:
            continue
        index = assembly.structure_index()
        if index is None:
            continue
        spec = getattr(assembly.layers[index], "framing", None)
        if spec is None:
            continue
        key = (spec.member, round(spec.spacing.inches, 1) if spec.spacing is not None else None,
               spec.double_top_plate, spec.advanced_framing, spec.roof_frame,
               spec.wall_frame, spec.plate_member,
               round(spec.heel_height.inches, 2) if spec.heel_height is not None else None)
        grouped.setdefault(key, []).append(tag)
    lines: list[str] = []
    if not grouped:
        lines.append(f"No assembly in use carries a FramingSpec — SIZES ARE {NOT_STATED}.")
    for key, tags in sorted(grouped.items(), key=lambda item: str(item[0])):
        member, spacing, double_plate, advanced, roof_frame, wall_frame, plate, heel = key
        pitch = f'@ {spacing:.0f}" O.C.' if spacing is not None else "@ SOLVER DEFAULT O.C."
        lines.append(f"{member} {pitch}")
        detail = ["DOUBLE TOP PLATE" if double_plate else "SINGLE TOP PLATE"]
        if plate:
            detail.append(f"PLATES {plate}")
        if advanced:
            detail.append("ADVANCED (IN-LINE) FRAMING")
        if wall_frame == "plate":
            detail.append("LAID FLAT AS A PLATE COURSE — NOT A STUD WALL")
        if roof_frame == "truss":
            detail.append("TRUSSED ROOF"
                          + (f", RAISED HEEL {heel:.2f}\"" if heel is not None else ""))
        lines.append("  " + ", ".join(detail))
        lines.append(f"  ASSEMBLIES: {_tags(tags)}")
    depths = sorted({system.joists.member for system in model.plan.elements_of_kind(
        "FloorSystem") if getattr(system, "joists", None) is not None})
    if depths:
        lines.append("FLOOR DECKS: " + ", ".join(depths))
    # Said out loud because every capacity number downstream depends on it. See memory of
    # ``engineering/post_bearing.py``: it assumes SPF, and no element in this model states
    # a species or a grade.
    lines.append("SPECIES AND GRADE ARE NOT MODELLED. The framing calculations in")
    lines.append("out/calcs/ assume SPF No.2 unless a calc sheet says otherwise; the")
    lines.append("supplier's submittal governs. TRUSSES ARE A DEFERRED SUBMITTAL —")
    lines.append("manufacturer's sealed drawings to the inspector on site.")
    return lines


def anchorage_block(model: ResolvedModel) -> list[str]:
    """The governing rule behind each hardware role, from the takeoff's own ``basis``.

    The schedule of parts and counts stays on S-602. What belongs on a notes sheet is the
    *rule* — the spacing, the embedment, the "one per bearing" — because that is what a
    framer works to and what an inspector measures against.
    """
    rows = hardware_takeoff(model)
    if not rows:
        return [f"No connection hardware is derived from this model — ANCHORAGE {NOT_STATED}."]
    by_role: dict[str, str] = {}
    for row in rows:
        role = str(row.get("role") or "other")
        basis = str(row.get("basis") or "").strip()
        if basis and role not in by_role:
            by_role[role] = basis
    lines: list[str] = []
    for role, basis in sorted(by_role.items()):
        lines.append(role.replace("_", " ").upper())
        lines.append("  " + _clip(basis))
    lines.append("PARTS, PART NUMBERS AND COUNTS: SEE S-602.")
    return lines


def _clip(text: str, limit: int = _MAX_LINE_CHARS) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def structural_specification_block(model: ResolvedModel) -> list[str]:
    """MasterFormat divisions 03 and 05 — and only those; A-002 keeps the remainder."""
    from typehaus.emit.draw.schedules.architectural import specification_sections

    sections = [item for item in specification_sections(model) if item[0][:2] in ("03", "05")]
    if not sections:
        return ["No division 03 or 05 specification content is authored in this model."]
    lines: list[str] = []
    for number, title, bullets in sections:
        lines.append(f"{number}  {title}")
        lines.extend(f"  • {_clip(bullet)}" for bullet in bullets)
    return lines


def limits_block(model: ResolvedModel, house_dir: Path | None) -> list[str]:
    """What this sheet does NOT say. The half of a notes sheet that is usually missing."""
    return [
        "This sheet states what the model carries. It is not a design.",
        "",
        "ENGINEERED ITEMS — every requirement this engine could not answer from a",
        "prescriptive table is listed on S-603 with its governing limit state, and the",
        "arithmetic behind each is in out/calcs/ (`haus calcs`). An item on S-603 that",
        "carries no seal rests on this engine's own calculation and on nothing else.",
        "",
        f"A value printed as \"{NOT_STATED}\" is a value this model does not carry. It is",
        "not a value of zero and not a default: nothing on this sheet is inferred.",
        "",
        "BRACED WALL LINES are drawn on S-103. MEMBER SCHEDULES are on S-101 and S-102.",
        "CONNECTION HARDWARE is scheduled on S-602. FOUNDATIONS are on S-100.",
    ]


def certification_block(profile: JurisdictionProfile | None) -> list[str]:
    """The jurisdiction's own certification sentence — printed here, once, in full.

    Minn. R. 1800.4200 subp. 3 puts the certification on *each* sheet a licensee is
    responsible for, and the ruled NAME / LICENSE NO. / DATE / SIGNATURE lines in every
    S-sheet's title block are that instrument. Subp. 4's sentence is long, so it prints
    here and every title block cross-references it — the same "say it once" split the
    specification sheets use.

    A profile that states no certification adds no block. Lettering Minnesota's sentence
    over another state's set would be a false statement about which board licensed it.
    """
    text = getattr(profile, "seal_certification", None)
    if not text:
        return []
    return [
        *textwrap.wrap(text, width=_MAX_LINE_CHARS),
        "",
        "The signature, typed or printed name, date and licence number are ruled in the",
        "title block of each sheet the licensee is responsible for. This engine never",
        "draws a stamp and never writes engineering.toml: a seal is a human act, and the",
        "set records it rather than performing it.",
        "",
        "An engineered requirement that carries no seal is listed on S-603 and rests on",
        "this engine's own calculation. See out/calcs/ for the arithmetic (`haus calcs`).",
    ]


def _write_structural_notes(pdf, model: ResolvedModel, number: str, name: str, *,
                            profile: JurisdictionProfile | None = None,
                            preferences: Preferences | None = None,
                            house_dir: Path | None = None) -> None:
    """S-001 — the general structural notes sheet, always emitted.

    Unconditional on purpose. The sheet it replaces (S-002) appeared only when the model
    happened to carry a specification section, so the one house with nothing authored — the
    house that most needed a sheet saying what is and is not known — got no sheet at all.
    """
    blocks: list[tuple[str, list[str]]] = [
        ("DESIGN CRITERIA — IRC TABLE R301.2(1)",
         design_criteria_block(model, profile, preferences)),
        ("FOUNDATIONS AND CONCRETE — ACI 318-19", concrete_block(model)),
        ("WOOD FRAMING", wood_framing_block(model)),
        ("ANCHORAGE AND CONNECTIONS", anchorage_block(model)),
        ("STRUCTURAL SPECIFICATIONS — DIVISIONS 03 / 05",
         structural_specification_block(model)),
        ("WHAT THIS SHEET DOES NOT SAY", limits_block(model, house_dir)),
    ]
    certification = certification_block(profile)
    if certification:
        blocks.append(("PROFESSIONAL CERTIFICATION", certification))
    clipped = [(title, [_clip(line) for line in lines]) for title, lines in blocks]
    with schedule_sheet(pdf, model, number, name, heading_xy=(0.03, 0.945)) as fig:
        overflow = _lay_out_blocks(fig, clipped)
        if overflow:
            fig.text(0.03, 0.06,
                     f"NOTE: {overflow} block(s) did not fit and are NOT printed.",
                     fontsize=7, family="monospace", color="#8a1c1c")
