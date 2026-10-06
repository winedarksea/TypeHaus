"""Integration parity with the CLI package over the shared Catlin engineering context."""

import pytest

from typehaus._meta import engine_version
from typehaus.checks import evaluate_permit_checklist
from typehaus.engineering.discovery import engineering_item_ids
from typehaus.takeoff.calc_package import PackageInputs, calc_package
from typehaus.takeoff.calculation_report import calculation_report

# Measured at ~33 s for the full report plus both package renders; quick states live separately.
pytestmark = pytest.mark.slow


def test_report_is_the_same_package_and_lists_every_page(
    catlin_ctx, catlin_check_report, monkeypatch,
):
    context = catlin_ctx
    report = catlin_check_report()
    monkeypatch.setattr("typehaus.takeoff.calculation_report.run_checks", lambda ctx: report)
    actual = calculation_report(context, "live-revision", "catlin", generated="2026-10-05")
    expected = calc_package(PackageInputs(
        house="catlin", model=context.model,
        item_ids=engineering_item_ids(context.engineering, report.findings),
        results=context.engineering, register=context.engineering_register,
        generated="2026-10-05", engine_version=engine_version(),
        profile_name=context.profile.name,
        checklist=evaluate_permit_checklist(report, context.profile),
        model_revision="live-revision",
    ))
    assert actual["files"] == expected
    cover = actual["files"]["00-cover.md"]
    assert "Live model revision" in cover and "live-revision" in cover
    assert "NOT FOR CONSTRUCTION" in cover
    listed = {path for path in expected if "/" not in path}
    for family in actual["families"]:
        listed.update((family["calculation"], family["appendix"]))
        listed.update(member["path"] for member in family["members"])
    assert listed == set(expected)

