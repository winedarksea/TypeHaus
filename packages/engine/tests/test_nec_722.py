"""Article 722 numbering and its Catlin reading (2026 NEC, read in print 2026-11-14)."""

from __future__ import annotations

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.model.nec import NEC

_CID = "electrical.limited_energy_wiring"


def test_article_722_numbering():
    for name, section in {
        "LIMITED_ENERGY_SEPARATION": "722.15(A)", "LIMITED_ENERGY_IN_RACEWAY": "722.15(G)",
        "LIMITED_ENERGY_WET": "722.2(B)", "LIMITED_ENERGY_MIXING": "722.13",
        "CLASS_2_INSTALL": "722.140(A)(2)", "CLASS_2_RATING": "722.140(A)(3)",
        "POE_AMPACITY": "Table 722.140(B)(2)", "COMMS_SUPPORT": "722.133(C)",
        "BROADBAND_SUPPORT": "722.135(B)", "BROADBAND_COVER": "Table 722.135(A)",
        "COMMS_DWELLING": "722.131(L)", "LIMITED_ENERGY_TEMPERATURE": "722.27",
    }.items():
        assert getattr(NEC, name) == section, name


def test_catlins_limited_energy_runs_share_no_raceway_and_name_their_wet_gaps(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY, only=_CID)
    found = [f for f in report.findings if f.check_id == _CID]
    assert not [f for f in found if f.result is Result.FAIL]
    passed = {t for f in found if f.result is Result.PASS for t in f.element_tags}
    # Every data and Class 2 raceway, the RSD initiator pair and the laundry track included.
    assert {"CD-M-RSD-INIT", "CR-M-LAUNDRY-24V", "CD-B-DATA-SHOP", "CD-M-DATA-PORCH"} <= passed
    unknown = {t for f in found if f.result is Result.UNKNOWN for t in f.element_tags}
    # Outdoor stretches need wet-listed or metal-sheathed cable (722.2(B)); no cable is authored.
    assert {"CD-M-RSD-INIT", "CD-M-DATA-PORCH", "CD-M-DATA-CAM-PORCH",
            "CD-M-DATA-CAM-CANOPY", "CD-M-DATA-ENTRY"} <= unknown
    assert "CD-B-DATA-SHOP" not in unknown  # wholly indoors
