"""Raceway, the parts that go with it, and the wire pulled through it.

Moved out of ``takeoff/electrical.py`` (which re-exports the two original names) when
raceway gained a material, fittings and named circuits.
"""

from __future__ import annotations

from typehaus.model.circuit_neutral import conductors_per_circuit, neutral_by_circuit
from typehaus.quantities import M_PER_IN
from typehaus.resolve.conduit_fittings import conduit_parts
from typehaus.resolve.model import ResolvedConduitRun, ResolvedModel

_FT_PER_M = 3.280839895013123


def conduit_price_key(material: str, trade_size_in: float) -> str:
    """The ``[conduit]`` key: a bare size is EMT ("0.75"), anything else names itself."""
    size = str(round(trade_size_in, 2))
    return size if material == "emt" else f"{material.upper()} {trade_size_in:g}"


def bills_as_conduit(run: ResolvedConduitRun) -> bool:
    """Power raceway and every derived sleeve; data and spare trunks bill in data_raceways."""
    return run.derived is not None or run.service not in ("data", None)


def conduit_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of *power* raceway by material and trade size — developed length.

    Data and spare trunks are billed by ``takeoff/data.py`` instead: comms may not share a
    raceway with power (NEC 722.15(A)), so the two are different orders. A derived sleeve
    (a surface box's NM drop, a floor-heat lead) is the electrician's rough-in whatever it
    carries, so it bills here.
    """
    groups: dict[tuple[str, float], dict[str, object]] = {}
    for run in model.conduits:
        if not bills_as_conduit(run):
            continue
        size_in = round(run.trade_size_m / M_PER_IN, 2)
        row = groups.setdefault((run.material, run.trade_size_m), {
            "size": conduit_price_key(run.material, size_in), "material": run.material,
            "trade_size_in": size_in, "runs": 0, "length_m": 0.0, "tags": []})
        row["runs"] = int(row["runs"]) + 1
        row["length_m"] = float(row["length_m"]) + run.length_m
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(run.tag)
    return [
        {"size": row["size"], "material": row["material"],
         "trade_size_in": row["trade_size_in"], "runs": int(row["runs"]),
         "length_ft": round(float(row["length_m"]) * _FT_PER_M, 1),
         "tags": sorted(row["tags"])}
        for row in (groups[key] for key in sorted(groups))
    ]


def conduit_fitting_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Raceway parts by the piece: kind × material × trade size (→ resolve/conduit_fittings).

    Keyed ``"<kind> <MATERIAL> <size>"`` (``"strap EMT 0.75"``), priced each in
    ``[conduit_fittings]``.
    """
    groups: dict[tuple[str, str, float], dict[str, object]] = {}
    for part in conduit_parts(model):
        row = groups.setdefault((part.kind, part.material, part.trade_size_in), {
            "fitting": f"{part.kind} {part.material.upper()} {part.trade_size_in:g}",
            "kind": part.kind, "material": part.material,
            "trade_size_in": part.trade_size_in, "count": 0, "tags": set()})
        row["count"] = int(row["count"]) + part.count
        tags = row["tags"]
        assert isinstance(tags, set)
        tags.add(part.run_tag)
    return [{**row, "tags": sorted(row["tags"])}  # type: ignore[arg-type]
            for row in (groups[key] for key in sorted(groups))]


# Conductors per circuit: the hots, a neutral where ``model/circuit_neutral`` finds one, and
# a ground. Counted singly, because that is how THHN is bought — by the foot, per colour.
def _per_circuit(circuit, neutral: dict[str, bool]) -> int | None:
    if circuit is None or circuit.poles not in (1, 2):
        return None
    return conductors_per_circuit(circuit, neutral.get(circuit.tag, True)) + 1


# Make-up at each end, in the panel and at the device: the conventional residential figure.
_MAKEUP_ALLOWANCE_FT = 10.0


def _terminations(runs: list[ResolvedConduitRun]) -> int:
    """Conductor ends among one circuit's runs: a run's end is continued, not a termination,
    where another of them starts in the box it ends in (``to_ref`` == ``from_ref``)."""
    starts = [run.from_ref for run in runs]
    ends = [run.to_ref for run in runs]
    return (sum(1 for ref in ends if ref is None or ref not in starts)
            + sum(1 for ref in starts if ref is None or ref not in ends))


def _named_rows(model: ResolvedModel, runs: list[ResolvedConduitRun],
                neutral: dict[str, bool]) -> list[dict]:
    """Exact rows: each named circuit over its runs, plus make-up at each termination.
    ``conductors_per_circuit`` is the largest count in the row (a 2-pole may lack a neutral)."""
    circuits = {circuit.tag: circuit for circuit in model.plan.library.circuits}
    by_circuit: dict[str, list[ResolvedConduitRun]] = {}
    for run in runs:
        for tag in run.circuits:
            by_circuit.setdefault(tag, []).append(run)
    groups: dict[int, dict[str, object]] = {}
    for tag, carrying in by_circuit.items():
        circuit = circuits.get(tag)
        per = _per_circuit(circuit, neutral)
        if per is None:
            continue
        # A circuit pulled panel -> box -> device is one pull: 10 ft of make-up, not 20.
        pull_ft = (sum(run.length_m for run in carrying) * _FT_PER_M
                   + _MAKEUP_ALLOWANCE_FT / 2 * _terminations(carrying))
        row = groups.setdefault(circuit.poles, {
            "poles": circuit.poles, "circuits": 0, "conductors_per_circuit": per,
            "length_ft": 0.0, "tags": []})
        row["circuits"] = int(row["circuits"]) + 1
        row["conductors_per_circuit"] = max(int(row["conductors_per_circuit"]), per)
        row["length_ft"] = float(row["length_ft"]) + pull_ft * per
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.extend(f"{run.tag}:{tag}" for run in carrying)
    return [{"poles": row["poles"], "circuits": row["circuits"],
             "conductors_per_circuit": row["conductors_per_circuit"],
             "length_ft": round(float(row["length_ft"]), 1),
             "basis": "named: run length + 5 ft make-up per termination, per conductor",
             "tags": sorted(row["tags"])}
            for row in (groups[key] for key in sorted(groups))]


def conductor_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Conductor lineal feet — what ``conduit_takeoff`` deliberately does not bill.

    A run that names ``circuits`` bills exactly: each circuit's runs plus 5 ft of make-up
    per termination, × conductors. A power trunk that names none keeps the estimate — mean
    raceway run + make-up × every served circuit no run names. Data, spare and derived sleeves pull
    no THHN.
    """
    trunks = [run for run in model.conduits if run.derived is None
              and run.service in ("power_120", "power_240")]
    named = [run for run in trunks if run.circuits]
    estimated = [run for run in trunks if not run.circuits]
    neutral = neutral_by_circuit(model.plan)
    rows = _named_rows(model, named, neutral)
    total_ft = sum(run.length_m * _FT_PER_M for run in estimated)
    if total_ft <= 0.0:
        return rows
    # A named circuit is billed exactly above, so the estimate leaves it out.
    named_tags = {tag for run in named for tag in run.circuits}
    # A circuit nothing names (a panel-mounted SPD) has no home run to pull.
    served = {getattr(element, "circuit", None) for element in model.plan.all_elements()}
    by_poles: dict[int, list[int]] = {}
    for circuit in model.plan.library.circuits:
        per = _per_circuit(circuit, neutral)
        if per is not None and circuit.tag not in named_tags and circuit.tag in served:
            by_poles.setdefault(circuit.poles, []).append(per)
    for poles in sorted(by_poles):
        counts = by_poles[poles]
        pull_ft = total_ft / len(estimated) + _MAKEUP_ALLOWANCE_FT
        estimate = {
            "poles": poles, "circuits": len(counts), "conductors_per_circuit": max(counts),
            "mean_pull_ft": round(pull_ft, 1),
            "length_ft": round(pull_ft * sum(counts), 1),
            "basis": "estimate: mean raceway run + 10 ft make-up, per conductor",
        }
        exact = next((row for row in rows if row["poles"] == poles), None)
        if exact is None:
            rows.append(estimate)
            continue
        # One row per poles value, so the price join and a paid check-off stay unique.
        exact["length_ft"] = round(float(exact["length_ft"]) + float(estimate["length_ft"]), 1)
        exact["named_circuits"] = exact["circuits"]
        exact["circuits"] = int(exact["circuits"]) + int(estimate["circuits"])
        exact["conductors_per_circuit"] = max(int(exact["conductors_per_circuit"]),
                                              int(estimate["conductors_per_circuit"]))
        exact["mean_pull_ft"] = estimate["mean_pull_ft"]
        exact["basis"] = f"{exact['basis']}; plus {estimate['basis']}"
    return sorted(rows, key=lambda row: row["poles"])
