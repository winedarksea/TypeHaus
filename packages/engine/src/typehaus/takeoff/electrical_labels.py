"""NEC field labels and plaques by the each (→ resolve/electrical_labels.py).

One row per NEC row; ``[electrical_labels]`` keys on it (``"690.31(D)(2)"``). A label whose
duty rests on an open question (``condition``) is counted and says so.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel


def electrical_label_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for label in model.electrical_labels:
        row = rows.setdefault(label.section, {
            "section": label.section, "name": f"NEC {label.section} label",
            "count": 0, "conditional": 0, "hosts": []})
        row["count"] = int(row["count"]) + label.quantity  # type: ignore[call-overload]
        if label.condition:
            row["conditional"] = int(row["conditional"]) + label.quantity  # type: ignore[call-overload]
        hosts = row["hosts"]
        assert isinstance(hosts, list)
        if label.host_ref and label.host_ref not in hosts:
            hosts.append(label.host_ref)
    return [{**row, "hosts": sorted(row["hosts"])}  # type: ignore[arg-type]
            for row in (rows[key] for key in sorted(rows))]
