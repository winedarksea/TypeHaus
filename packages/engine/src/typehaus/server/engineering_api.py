"""Read-only engineering calculations over the current in-memory model."""

from typing import Any

from typehaus.checks import build_context_from_model
from typehaus.takeoff.calculation_report import CalculationReportCache


def register_engineering_routes(app: Any, state: Any) -> None:
    from fastapi.responses import JSONResponse

    reports = CalculationReportCache()

    @app.get("/reports/engineering")
    def get_engineering_calculations() -> Any:
        # Capture model, revision, preferences and register together. Arithmetic runs
        # outside the edit lock, like the background checks over their resolved snapshot.
        with state._lock:
            if state.model is None:
                return JSONResponse({"error": "model does not resolve"}, status_code=409)
            revision = state.revision()
            try:
                ctx = build_context_from_model(
                    state.model, state._resolve_findings, state.house_dir)
            except (OSError, ValueError) as exc:
                return JSONResponse({"error": str(exc)}, status_code=422)
        return JSONResponse(reports.get(ctx, revision, state.house_dir.name))
