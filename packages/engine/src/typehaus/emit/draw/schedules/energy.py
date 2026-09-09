"""G-004 and G-005 — the two energy sheets a Minnesota plan check actually asks for.

**G-004 is compliance**: which path the house is taking, the prescriptive table it is
taking it by, the window-to-wall ratio, and the blower-door target with the tested number
beside it. **G-005 is ventilation and the certificate**: MN 1322 R403.5's whole-house
worksheet, R303.3's local exhaust per bathroom, the equipment that serves both, the block
load, and the Energy Code Compliance Certificate that gets posted at the panel.

Every number is read from one of the two pure summaries the checks grade against —
``mn_energy.air_leakage_summary`` and ``mn_residential.ventilation.whole_house_summary`` —
so a sheet can never state a rate the finding beside it disagrees with. What the model does
not carry prints ``NOT MODELLED`` or a ruled blank line, never a default: a certificate
posted at a panel is a statement somebody is answerable for.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.resolve.model import ResolvedModel

if TYPE_CHECKING:  # pragma: no cover — annotations only
    from typehaus.checks.registry import Preferences

#: What a value the model does not carry prints as. One string, so a reader learns it once.
NOT_MODELLED = "NOT MODELLED"

#: Compliance path. This engine grades the prescriptive tables of MN 1322 / IRC N1102.1.2
#: and nothing else — there is no ResCheck total-UA trade-off and no performance model
#: behind it, so the sheet names the path it really took rather than the one it might have.
_COMPLIANCE_PATH = ("PRESCRIPTIVE — MN 1322 (IRC N1102.1.2), CLIMATE ZONE 6. "
                    "No total-UA trade-off and no performance path is claimed.")


def _write_energy_sheet(pdf, model: ResolvedModel, number: str, name: str,
                        preferences: Preferences | None = None) -> None:
    """G-004 — compliance path, the prescriptive envelope, WWR, and air leakage.

    The block load moved to G-005, where the equipment it sizes is scheduled. What replaced
    it here is the pair of statements a reviewer opens this sheet to find: *which* path, and
    *what* the envelope has to test at.
    """
    from typehaus.checks.building_science.wwr import wwr_summary
    from typehaus.checks.code.mn_energy import air_leakage_summary, evaluate_envelope
    from typehaus.checks.registry import Preferences

    prefs = preferences if preferences is not None else Preferences()
    rows = list(evaluate_envelope(model, model.plan))
    unknown = sum(1 for row in rows if row.verdict == "unknown")
    failing = sum(1 for row in rows if row.verdict == "fail")
    with schedule_sheet(pdf, model, number, name) as fig:
        section(fig, 0.04, 0.925, "COMPLIANCE PATH")
        fig.text(0.04, 0.905, _COMPLIANCE_PATH, fontsize=8, family="monospace", va="top")
        fig.text(0.04, 0.885,
                 f"{len(rows)} envelope component(s) evaluated · {failing} FAIL · "
                 f"{unknown} UNKNOWN. An UNKNOWN row is a component this model cannot "
                 f"grade, not a component that complies.",
                 fontsize=7.5, family="monospace", va="top")

        section(fig, 0.04, 0.855, "PRESCRIPTIVE ENVELOPE — MN 1322, CLIMATE ZONE 6")
        _add_table(fig, [(r.component, r.role, r.required, r.provided, r.verdict.upper())
                         for r in rows],
                   ("Component", "Use", "Required", "Provided", "Verdict"),
                   bbox=(0.04, 0.50, 0.92, 0.33))

        section(fig, 0.04, 0.455, "WINDOW-TO-WALL RATIO")
        wwr = wwr_summary(model)
        wwr_rows = [("OVERALL", f"{wwr['overall']:.1%}")]
        wwr_rows.extend((item.facade, f"{item.ratio:.1%}") for item in wwr["per_facade"])
        _add_table(fig, wwr_rows, ("Facade", "Glazing / gross wall"),
                   bbox=(0.04, 0.28, 0.38, 0.15))

        section(fig, 0.46, 0.455, "ENVELOPE AIR LEAKAGE — N1102.4.1.2")
        leakage = air_leakage_summary(prefs)
        _add_table(fig, _air_leakage_rows(leakage),
                   ("", ""), bbox=(0.46, 0.28, 0.50, 0.15))
        fig.text(0.04, 0.24, _AIR_LEAKAGE_NOTE, fontsize=7.5, family="monospace", va="top")


#: The standing air-leakage note. The test is a *field* act, so the sheet says who does it
#: and where the result goes rather than treating the authored number as the end of it.
_AIR_LEAKAGE_NOTE = (
    "A blower-door test is required. The test is performed by a certified third party at\n"
    "rough-in or at final, and the report goes to the authority having jurisdiction before\n"
    "the final inspection. The tested result is entered on the certificate on G-005.")


def _air_leakage_rows(leakage) -> list[tuple[str, str]]:
    tested = (f"{leakage.ach50:g} ACH50" if leakage.ach50 is not None
              else "NOT TESTED — see the note below")
    rows = [("REQUIRED", f"{leakage.max_ach50:g} ACH50 at 50 Pa"),
            ("MODEL STATES", tested),
            ("VERDICT", leakage.result.value.upper())]
    if leakage.cfm50 is not None:
        rows.insert(2, ("CFM50", f"{leakage.cfm50:g}"))
    return rows


# --- G-005 ------------------------------------------------------------------------------


def _write_ventilation_sheet(pdf, model: ResolvedModel, number: str, name: str,
                             preferences: Preferences | None = None) -> None:
    """G-005 — ventilation, the equipment that provides it, and the MN certificate.

    The certificate is the reason this sheet exists as its own page: MN 1322 R401.3 wants a
    permanent record posted at the electrical panel, and a reviewer wants to see the fields
    on it before the drywall goes on. It is printed with its blanks ruled — the tested
    ACH50 and the installer's signature are field acts, and an engine that filled them in
    would be forging them.
    """
    from typehaus.checks.code.mn_energy import air_leakage_summary
    from typehaus.checks.code.mn_residential.ventilation import whole_house_summary
    from typehaus.checks.registry import Preferences
    from typehaus.energy import estimate_block_load

    prefs = preferences if preferences is not None else Preferences()
    vent = whole_house_summary(model, model.plan)
    with schedule_sheet(pdf, model, number, name) as fig:
        section(fig, 0.04, 0.925, "WHOLE-HOUSE VENTILATION — MN 1322 R403.5")
        _add_table(fig, _whole_house_rows(vent), ("", "", ""),
                   bbox=(0.04, 0.745, 0.60, 0.16))

        section(fig, 0.68, 0.925, "LOCAL EXHAUST — R303.3 / M1507.3")
        _add_table(fig, _local_exhaust_rows(model, prefs), ("Room", "Verdict", "Rate"),
                   bbox=(0.68, 0.745, 0.28, 0.16))

        section(fig, 0.04, 0.715, "MECHANICAL EQUIPMENT AND RATED EFFICIENCIES")
        _add_table(fig, _equipment_rows(model),
                   ("Tag", "Kind", "Type", "Heating", "Cooling", "Efficiency"),
                   bbox=(0.04, 0.50, 0.92, 0.19))

        section(fig, 0.04, 0.465, "BLOCK LOAD — NOT A MANUAL J")
        load = estimate_block_load(model, prefs)
        load_rows = [(c.kind, f"{c.area_ft2:,.0f}", f"{c.ua_btu_per_hour_f:,.1f}")
                     for c in load.components]
        load_rows.append(("TOTAL HEATING", "", f"{load.heating_load_btu_per_hour:,.0f} BTU/h"))
        load_rows.append(("TOTAL COOLING", "",
                          f"{load.cooling_load_btu_per_hour:,.0f} BTU/h "
                          f"({load.cooling_tons:.1f} tons)"))
        _add_table(fig, load_rows, ("Component", "Area (ft2)", "UA / total"),
                   bbox=(0.04, 0.13, 0.42, 0.30))
        fig.text(0.04, 0.115,
                 "NOT A MANUAL J — a transparent block-load estimate only."
                 + (" Unknown inputs: " + ", ".join(load.unknown_inputs)
                    if load.unknown_inputs else ""),
                 fontsize=7, family="sans-serif", wrap=True)

        _draw_certificate(fig, model, prefs, vent, air_leakage_summary(prefs))


def _whole_house_rows(vent) -> list[tuple[str, str, str]]:
    """R403.5's two rates against what the modelled equipment provides."""
    if vent is None:
        return [("CONDITIONED AREA", NOT_MODELLED,
                 "no conditioned room area resolves, so no rate can be stated")]
    provided = (f"{vent.provided_cfm:.0f} cfm" if vent.provided_cfm is not None
                else NOT_MODELLED)
    rows = [
        ("CONDITIONED FLOOR AREA", f"{vent.conditioned_area_ft2:,.0f} sf",
         "resolved rooms flagged conditioned"),
        ("BEDROOMS", f"{vent.bedrooms}", "bedroom-occupancy rooms"),
        ("TOTAL RATE (TVR)", f"{vent.total_rate_cfm:.0f} cfm",
         "0.02 cfm/sf + 15 cfm x (bedrooms + 1)"),
        ("CONTINUOUS RATE (CVR)", f"{vent.continuous_rate_cfm:.0f} cfm",
         "at least 50% of TVR, never under 40 cfm"),
        ("PROVIDED", provided, ", ".join(vent.unit_tags) or NOT_MODELLED),
    ]
    if vent.reason:
        rows.append(("GAP", "", vent.reason))
    return rows


def _local_exhaust_rows(model: ResolvedModel, prefs: Preferences) -> list[tuple[str, ...]]:
    """One row per bathroom, from ``code.R303_3_local_exhaust`` itself.

    The rule is run, not re-derived: the numbers a reviewer reads here are the numbers the
    finding was graded on. Calling the one check directly rather than the whole registry
    keeps this sheet off the several-second path the cover pays for.
    """
    from typehaus.checks.code.mn_residential.ventilation import bathroom_exhaust
    from typehaus.checks.registry import CheckContext
    from typehaus.checks.run import resolve_profile

    ctx = CheckContext(plan=model.plan, model=model, preferences=prefs,
                       profile=resolve_profile(prefs))
    rows: list[tuple[str, ...]] = []
    for finding in bathroom_exhaust(ctx):
        room = finding.element_tags[0] if finding.element_tags else ""
        message = finding.message
        room = room or message.split(" ", 1)[0]
        rows.append((room, finding.result.value.upper(), _rate_from(message)))
    return rows or [("—", NOT_MODELLED, "no bathroom-occupancy room resolves")]


def _rate_from(message: str) -> str:
    """The cfm figure out of the check's own sentence, or what it said instead.

    The check states the rate it graded in prose; lifting it keeps one number in the set.
    A message with no cfm in it (an operable-window pass, an unrated grille) is reported by
    what it does say, clipped — never as a blank, which would read as "no requirement".
    """
    words = message.replace(",", " ").split()
    for index, word in enumerate(words):
        if word.startswith("cfm") and index:
            return f"{words[index - 1]} cfm"
    if "operable window" in message:
        return "operable window"
    return message[:34]


def _equipment_rows(model: ResolvedModel) -> list[tuple[str, ...]]:
    """Every authored ``Equipment`` joined to its type's published ratings.

    HSPF2/SEER2/AFUE are printed only where the type carries them. A heat pump whose type
    states no HSPF2 prints ``NOT MODELLED`` — the certificate has a line for the number and
    an invented one is the failure mode this sheet exists to avoid.
    """
    types = {item.tag: item for item in model.plan.library.equipment_types}
    rows: list[tuple[str, ...]] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Equipment":
                continue
            spec = types.get(element.type_ref or "")
            rows.append((
                element.tag,
                str(getattr(element.kind, "value", element.kind or "—")).upper(),
                element.type_ref or "—",
                _btuh(getattr(spec, "heating_capacity_btuh", None)),
                _btuh(getattr(spec, "cooling_capacity_btuh", None)),
                _efficiency(spec),
            ))
    return sorted(rows) or [("—", NOT_MODELLED, "", "", "", "")]


def _btuh(value: float | None) -> str:
    return f"{value:,.0f}" if value else "—"


def _efficiency(spec) -> str:
    parts = [f"{label} {value:g}" for label, value in
             (("HSPF2", getattr(spec, "hspf2", None)),
              ("SEER2", getattr(spec, "seer2", None)),
              ("AFUE", getattr(spec, "afue", None)),
              ("SRE", getattr(spec, "sensible_recovery_effectiveness", None)))
             if value is not None]
    return " / ".join(parts) if parts else NOT_MODELLED


# --- the certificate --------------------------------------------------------------------

#: The MN Energy Code Compliance Certificate's field list, in the order the state form runs.
#: A field the model cannot derive is printed with a ruled blank rather than dropped: a
#: certificate missing a line reads as a certificate that had nothing to say there.
_CERTIFICATE_ROLES = (
    ("CEILING / ROOF", "roof"),
    ("ABOVE-GRADE WALL", "above-grade wall"),
    ("FOUNDATION WALL", "foundation wall"),
    ("SLAB / BELOW SLAB", "slab"),
    ("WINDOWS", "window"),
)

_CERTIFICATE_BLANKS = (
    "TESTED ENVELOPE LEAKAGE  __________ ACH50 @ 50 Pa      DATE  ____________",
    "TESTED DUCT LEAKAGE      __________ cfm25              DATE  ____________",
    "MAKEUP AIR               ______________________________________________",
    "COMBUSTION AIR           ______________________________________________",
    "CONTRACTOR / INSTALLER   ______________________  SIGNED  ______________",
)


def _draw_certificate(fig, model: ResolvedModel, prefs, vent, leakage) -> None:
    """MN 1322 R401.3 — the certificate that gets posted at the electrical panel."""
    section(fig, 0.50, 0.465,
            "ENERGY CODE COMPLIANCE CERTIFICATE — TO BE POSTED AT THE PANEL")
    _add_table(fig, _certificate_rows(model, vent, leakage), ("Field", "Value"),
               bbox=(0.50, 0.265, 0.46, 0.165))
    fig.text(0.50, 0.245, "RADON CONTROL PER MN 1303.2400 — SEE S-100.",
             fontsize=7, family="monospace", weight="bold", va="top")
    # The blanks stop clear of figure fraction 0.11, where the title block starts.
    y = 0.215
    for line in _CERTIFICATE_BLANKS:
        fig.text(0.50, y, line, fontsize=6.5, family="monospace", va="top")
        y -= 0.019


def _certificate_rows(model: ResolvedModel, vent, leakage) -> list[tuple[str, str]]:
    from typehaus.checks.code.mn_energy import evaluate_envelope

    by_role: dict[str, list[str]] = {}
    for row in evaluate_envelope(model, model.plan):
        by_role.setdefault(row.role, []).append(row.provided)
    rows = [(label, " / ".join(sorted(set(by_role.get(role, [])))) or NOT_MODELLED)
            for label, role in _CERTIFICATE_ROLES]
    rows.append(("DESIGN ENVELOPE LEAKAGE",
                 f"{leakage.ach50:g} ACH50 (target {leakage.max_ach50:g})"
                 if leakage.ach50 is not None
                 else f"target {leakage.max_ach50:g} ACH50 — not yet tested"))
    if vent is not None:
        rows.append(("MECHANICAL VENTILATION",
                     f"TVR {vent.total_rate_cfm:.0f} cfm / CVR "
                     f"{vent.continuous_rate_cfm:.0f} cfm; "
                     + (f"{vent.provided_cfm:.0f} cfm provided by "
                        f"{', '.join(vent.unit_tags)}"
                        if vent.provided_cfm is not None else NOT_MODELLED)))
    rows.append(("RADON", "SEE S-100 — MN 1303.2400 (system, vent and fan "
                          "location are shown there)"))
    return rows
