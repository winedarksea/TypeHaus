"""What the mix is made of, against the exposure class it claims (→ 12 §checks/structural).

``concrete_durability`` grades w/cm, f'c and air. This module grades the rest of ACI 318-19
Table 19.3.2.1 and its satellites, one check id each: chloride ion, the SCM caps, the
sulfate cement type, ASR, and the galvanized bar's chromate treatment.

Like ``concrete_durability``, it grades the spec against the class, never the class against
the site. Findings are one per MIX, not per pour. An unauthored input is UNKNOWN. N/A is
earned only where every mix states the class and none triggers the rule.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from typehaus.checks._authoring import structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.concrete_durability import pour_specs
from typehaus.findings import Finding, Result, not_applicable, passed, unknown

#: Table 19.3.2.1, water-soluble Cl- in % by mass of cementitious, NONPRESTRESSED (ASTM
#: C1218 at 28-42 days). Prestressed is 0.06 in every class; this model has no tendons.
CHLORIDE_LIMIT_PCT = {"C0": 1.00, "C1": 0.30, "C2": 0.15}

#: Table 26.4.2.2(b), F3: % of total cementitious by mass.
F3_FLY_ASH_MAX, F3_SLAG_MAX, F3_SILICA_FUME_MAX = 25.0, 50.0, 10.0
F3_FLY_ASH_PLUS_SF_MAX, F3_TOTAL_MAX = 35.0, 50.0

#: ASTM C1778 Table 2: risk level by exposure row and aggregate class R0-R3. Only the two
#: wet rows are reachable here, because W1/W2 is what triggers the rule (§26.4.2.2(d)).
#: "Exposed to alkalis in service" includes deicing salt (footnote 3), which is class C2.
ASR_RISK = {"humid_or_buried": (1, 3, 4, 5), "alkalis_in_service": (1, 4, 5, 6)}
#: C1778 Table 3: prevention level by risk level (1-6) and structure class S1-S4.
#: ``None`` is the S4-at-risk-6 cell, where construction is not permitted.
ASR_PREVENTION = {
    1: ("V", "V", "V", "V"), 2: ("V", "V", "W", "X"), 3: ("V", "W", "X", "Y"),
    4: ("W", "X", "Y", "Z"), 5: ("X", "Y", "Z", "ZZ"), 6: ("Y", "Z", "ZZ", None),
}
ASR_LEVELS = ("V", "W", "X", "Y", "Z", "ZZ")

_GALVANIZED = ("hdg-a767", "hdg-a1094")


def _mixes(ctx: CheckContext, cid: str, code: str) -> list[Finding] | dict[Any, list[Any]]:
    """Group pours by their mix, or return the N/A / UNKNOWN that ends the check early."""
    specs = pour_specs(ctx.plan)
    if not specs:
        return [not_applicable(cid, "this model contains no concrete pour that names an "
                               "assembly", code=code)]
    groups: dict[Any, list[Any]] = {}
    for element, spec in specs:
        if spec is not None:
            groups.setdefault(spec, []).append(element)
    if not groups:
        return [unknown(cid, f"{len(specs)} concrete pour(s) and none states a ConcreteSpec",
                        tuple(sorted(el.tag for el, _ in specs))[:8], code=code)]
    return groups


def _label(spec: Any, pours: list[Any]) -> str:
    classes = "/".join(c for c in (spec.exposure_f, spec.exposure_s, spec.exposure_w,
                                   spec.exposure_c) if c)
    on = sorted({pour.assembly for pour in pours})
    where = f" on {', '.join(on[:3])}{' and others' if len(on) > 3 else ''}" if on else ""
    return f"the {spec.fc_psi:,.0f} psi {classes or 'unclassed'} mix{where}"


def _run(ctx: CheckContext, cid: str, code: str, fix: str,
         applies: Callable[[Any], bool | None],
         grade: Callable[[Any], tuple[Result, str]], absent: str) -> list[Finding]:
    """Grade each mix ``applies`` is True for. ``applies`` returns None when the mix does
    not state what decides it, and that mix is silence, as in ``concrete_durability``."""
    groups = _mixes(ctx, cid, code)
    if isinstance(groups, list):
        return groups
    out: list[Finding] = []
    undecided = 0
    for spec, pours in sorted(groups.items(), key=lambda kv: min(p.tag for p in kv[1])):
        verdict = applies(spec)
        if verdict is None:
            undecided += 1
            continue
        if not verdict:
            continue
        result, why = grade(spec)
        subjects = tuple(sorted(p.tag for p in pours))[:8]
        message = f"{_label(spec, pours)} ({len(pours)} pour(s)): {why}"
        if result is Result.FAIL:
            out.append(structural_advisory(cid, message, subjects, Result.FAIL, fix, code=code))
        elif result is Result.UNKNOWN:
            out.append(unknown(cid, message, subjects, code=code, fix=fix))
        else:
            out.append(passed(cid, message, subjects, code=code))
    if out:
        return out
    if undecided:
        return [unknown(cid, f"{undecided} mix(es) do not state {absent}, so this rule has "
                        "nothing to grade them against", code=code)]
    return [not_applicable(cid, f"every mix states {absent} and none is one this rule "
                           "governs", code=code)]


# --- chloride ion, Table 19.3.2.1 ------------------------------------------------------


def _chloride(spec: Any) -> tuple[Result, str]:
    limit = CHLORIDE_LIMIT_PCT[spec.exposure_c]
    if spec.chloride_ion_max_pct is None:
        return (Result.UNKNOWN, f"class {spec.exposure_c} caps water-soluble chloride at "
                f"{limit:.2f}% of cementitious and the mix states no limit")
    ok = spec.chloride_ion_max_pct <= limit + 1e-9
    return (Result.PASS if ok else Result.FAIL,
            f"chloride {spec.chloride_ion_max_pct:.2f}% against class {spec.exposure_c}'s "
            f"{limit:.2f}%")


@check(Tier.STRUCTURAL, "structural.concrete_chloride_limit")
def concrete_chloride_limit(ctx: CheckContext) -> list[Finding]:
    """ACI 318-19 Table 19.3.2.1's water-soluble chloride limit for the stated C class."""
    return _run(ctx, "structural.concrete_chloride_limit", "ACI 318-19 Table 19.3.2.1",
                "author `chloride_ion_max_pct` from the mix submittal (ASTM C1218)",
                lambda s: None if s.exposure_c is None else True, _chloride, "a C class")


# --- SCM caps, Table 26.4.2.2(b) --------------------------------------------------------


def _blended(cement: Any) -> bool:
    """A cement that may carry its own pozzolan or slag. C595 IL is limestone only."""
    return cement.standard == "ASTM C1157" or (
        cement.standard == "ASTM C595" and not cement.designation.upper().startswith("IL"))


def scm_problems(fractions: Any) -> list[str]:
    fly, slag, fume = fractions.fly_ash_pct, fractions.slag_pct, fractions.silica_fume_pct
    rows = (("fly ash or other pozzolans", fly, F3_FLY_ASH_MAX),
            ("slag cement", slag, F3_SLAG_MAX), ("silica fume", fume, F3_SILICA_FUME_MAX),
            ("fly ash + silica fume", fly + fume, F3_FLY_ASH_PLUS_SF_MAX),
            ("fly ash + slag + silica fume", fly + slag + fume, F3_TOTAL_MAX))
    return [f"{name} {value:g}% over the {cap:g}% cap" for name, value, cap in rows
            if value > cap + 1e-9]


def _scm(spec: Any) -> tuple[Result, str]:
    fractions = spec.scm_fractions
    if fractions is None:
        return (Result.UNKNOWN, "class F3 caps SCMs and the mix states no measured fractions"
                + (f" (prose only: {spec.scm!r})" if spec.scm else ""))
    problems = scm_problems(fractions)
    if problems:
        return (Result.FAIL, "; ".join(problems))
    if spec.cement is None:
        return (Result.UNKNOWN, "the added SCMs are within the F3 caps, but the cement is "
                "not named. A blended C595/C1157 cement's own pozzolan or slag counts toward "
                "the same caps")
    if _blended(spec.cement) and not fractions.includes_blended_cement:
        return (Result.UNKNOWN, f"{spec.cement.standard} {spec.cement.designation} is a "
                "blended cement and the fractions do not say they include its SCM content")
    return (Result.PASS, f"fly ash {fractions.fly_ash_pct:g}%, slag {fractions.slag_pct:g}%, "
            f"silica fume {fractions.silica_fume_pct:g}% are within every F3 cap")


@check(Tier.STRUCTURAL, "structural.concrete_scm_caps")
def concrete_scm_caps(ctx: CheckContext) -> list[Finding]:
    """ACI 318-19 Table 26.4.2.2(b)'s SCM caps on an F3 (deicing) pour."""
    return _run(ctx, "structural.concrete_scm_caps", "ACI 318-19 Table 26.4.2.2(b)",
                "author `scm_fractions` and `cement` from the mix design",
                lambda s: None if s.exposure_f is None else s.exposure_f == "F3",
                _scm, "an F class")


# --- sulfate cement type, Table 19.3.2.1 -------------------------------------------------


def _resists(cement: Any, grade: str) -> bool | None:
    """Does the cement carry the MS/HS resistance ``grade`` asks? None where only a C3A
    content the model does not hold could say (Table 19.3.2.1 footnote on Type I/III)."""
    name = cement.designation.upper().replace(" ", "")
    if cement.standard == "ASTM C150":
        types = set(name.split("/"))
        wanted = {"II", "V"} if grade == "MS" else {"V"}
        if types & wanted:
            return True
        return None if types & {"I", "III"} else False
    if cement.standard == "ASTM C595":
        return "(HS)" in name or (grade == "MS" and "(MS)" in name)
    return name == "HS" or (grade == "MS" and name == "MS")


def _sulfate(spec: Any) -> tuple[Result, str]:
    cls = spec.exposure_s
    if cls == "S0":
        return (Result.PASS, "class S0 places no restriction on the cement type")
    if spec.cement is None:
        return (Result.UNKNOWN, f"class {cls} restricts the cement type and the mix names "
                "no cement")
    grade = "MS" if cls == "S1" else "HS"
    named = f"{spec.cement.standard} {spec.cement.designation}"
    resists = _resists(spec.cement, grade)
    if resists is None:
        return (Result.UNKNOWN, f"{named} meets class {cls} only below a C3A limit this "
                "model does not hold")
    if not resists:
        return (Result.FAIL, f"{named} is not a {grade} cement, which class {cls} requires "
                "(or a combination qualified under §26.4.2.2(c))")
    if cls == "S3":
        option_2 = (spec.w_cm_max is not None and spec.w_cm_max <= 0.40 + 1e-9
                    and spec.fc_psi >= 5000.0)
        pozzolan = spec.scm_fractions is not None and (
            spec.scm_fractions.fly_ash_pct + spec.scm_fractions.slag_pct > 0.0)
        if not (option_2 or pozzolan):
            return (Result.UNKNOWN, f"{named} is HS, but class S3 also needs option 2's "
                    "0.40 / 5,000 psi or option 1's pozzolan or slag, and neither is stated")
    return (Result.PASS, f"{named} meets class {cls}")


@check(Tier.STRUCTURAL, "structural.concrete_sulfate_cement")
def concrete_sulfate_cement(ctx: CheckContext) -> list[Finding]:
    """ACI 318-19 Table 19.3.2.1's cementitious types for the stated S class."""
    return _run(ctx, "structural.concrete_sulfate_cement", "ACI 318-19 Table 19.3.2.1",
                "author `cement` (standard + designation), or state the S class from a "
                "soil sulfate test (ASTM C1580)",
                lambda s: None if s.exposure_s is None else True, _sulfate, "an S class")


# --- ASR, §26.4.2.2(d) and ASTM C1778 ------------------------------------------------------


def asr_required(spec: Any) -> tuple[int, str | None] | None:
    """(risk level, prevention level required), or None without a structure class."""
    row = "alkalis_in_service" if spec.exposure_c == "C2" else "humid_or_buried"
    risk = ASR_RISK[row][int(spec.asr.aggregate_class[1])]
    if spec.asr.structure_class is None:
        return None
    return (risk, ASR_PREVENTION[risk][int(spec.asr.structure_class[1]) - 1])


def _asr(spec: Any) -> tuple[Result, str]:
    asr = spec.asr
    if asr is None:
        return (Result.UNKNOWN, f"class {spec.exposure_w} asks for evidence the aggregate is "
                "not alkali-silica reactive or that ASR is mitigated, and the mix states "
                "no aggregate reactivity class")
    if asr.aggregate_class == "R0":
        return (Result.PASS, "R0 aggregate is risk level 1, prevention V (none needed)")
    required = asr_required(spec)
    if required is None:
        return (Result.UNKNOWN, f"{asr.aggregate_class} aggregate needs a C1778 structure "
                "class to set the prevention level")
    risk, level = required
    if level is None:
        return (Result.FAIL, f"risk level {risk} on an S4 structure is not permitted")
    if asr.prevention_level is None:
        return (Result.UNKNOWN, f"risk level {risk} on {asr.structure_class} needs "
                f"prevention {level} and the mix states none")
    ok = ASR_LEVELS.index(asr.prevention_level) >= ASR_LEVELS.index(level)
    return (Result.PASS if ok else Result.FAIL,
            f"{asr.aggregate_class} / {asr.structure_class}: risk level {risk} needs "
            f"prevention {level}, the mix provides {asr.prevention_level}")


@check(Tier.STRUCTURAL, "structural.concrete_asr")
def concrete_asr(ctx: CheckContext) -> list[Finding]:
    """ACI 318-19 §26.4.2.2(d) on a W1/W2 pour, by ASTM C1778's prescriptive tables."""
    return _run(ctx, "structural.concrete_asr", "ACI 318-19 §26.4.2.2(d); ASTM C1778",
                "author `asr=AsrSpec(...)` from the aggregate's C1293/C1260 result",
                lambda s: None if s.exposure_w is None else s.exposure_w in ("W1", "W2"),
                _asr, "a W class")


# --- chromate treatment, ASTM A767 / A1094 --------------------------------------------------


def _chromate(spec: Any) -> tuple[Result, str]:
    if spec.chromate_treatment is None:
        return (Result.UNKNOWN, "galvanized bar is chromate-passivated unless the purchaser "
                "waives it, and the spec says neither")
    if spec.chromate_treatment == "waived":
        return (Result.PASS, "chromate treatment WAIVED by the purchaser; fresh-concrete "
                "hydrogen evolution then rests on the cement's own chromate")
    return (Result.PASS, "galvanized bar chromate-passivated per the standard")


@check(Tier.STRUCTURAL, "structural.galvanized_bar_chromate")
def galvanized_bar_chromate(ctx: CheckContext) -> list[Finding]:
    """ASTM A767 / A1094: the order must say whether the zinc is chromate-treated."""
    return _run(ctx, "structural.galvanized_bar_chromate", "ASTM A767; ASTM A1094",
                "author `chromate_treatment` on the mix carrying the galvanized bar",
                lambda s: None if s.bar_coating is None else s.bar_coating in _GALVANIZED,
                _chromate, "a bar coating")
