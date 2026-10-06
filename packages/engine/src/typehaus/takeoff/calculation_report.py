"""The live calculation reader's payload, shared by HTTP and the browser engine."""

from threading import Lock

from typehaus._meta import engine_version, generation_date
from typehaus.checks import CheckContext, evaluate_permit_checklist, run_checks
from typehaus.engineering.discovery import engineering_item_ids
from typehaus.takeoff.calc_family import appendix_filename, families, family_filename
from typehaus.takeoff.calc_package import PackageInputs, calc_package
from typehaus.takeoff.calc_sheet import sheet_filename


class CalculationReportCache:
    """One engine's package, invalidated by its model, preferences, signoffs, or issue date."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._key: tuple[str, ...] | None = None
        self._payload: dict | None = None

    def get(self, ctx: CheckContext, revision: str, house: str) -> dict:
        generated = generation_date()
        key = (revision, house, repr(ctx.preferences), repr(ctx.engineering_register), generated)
        # This lock only guards report computation; editors can adopt a newer model
        # while the reader finishes its captured snapshot. Exceptions are never cached.
        with self._lock:
            if self._key == key and self._payload is not None:
                return self._payload
            payload = calculation_report(ctx, revision, house, generated=generated)
            self._key, self._payload = key, payload
            return payload


def calculation_report(
    ctx: CheckContext, revision: str, house: str, *, generated: str | None = None,
) -> dict:
    report = run_checks(ctx)
    item_ids = engineering_item_ids(ctx.engineering, report.findings)
    inputs = PackageInputs(
        house=house, model=ctx.model, item_ids=item_ids, results=ctx.engineering,
        register=ctx.engineering_register, generated=generated or generation_date(),
        engine_version=engine_version(), profile_name=ctx.profile.name,
        checklist=evaluate_permit_checklist(report, ctx.profile), model_revision=revision,
        # A live edit can precede disk writeback, so a source hash would name another model.
        content_hash="",
    )
    groups = []
    for kind, records in families(inputs.records).items():
        groups.append({
            "kind": kind,
            "calculation": f"calcs/{family_filename(kind)}",
            "appendix": appendix_filename(kind),
            "members": [{"item_id": record.item_id,
                         "path": f"appendix/{sheet_filename(record.item_id)}"}
                        for record in records],
        })
    return {"revision": revision, "files": calc_package(inputs), "families": groups}
