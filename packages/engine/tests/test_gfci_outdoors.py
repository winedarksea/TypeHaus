"""210.8(A)(4): a receptacle on an exterior wall's outer face is outdoors.

Regression: a 0.5 m room tolerance put catlin's 13" exterior walls' outer-face devices
indoors, so none of them was graded for outdoor GFCI.
"""

from typehaus.checks import run_from_model

OUTDOOR = ("ED-M-FRONT-RC1", "ED-M-REAR-RC1", "ED-S-BALCONY-RC1", "ED-A-RADON-RC")


def test_exterior_face_receptacles_grade_as_outdoors(catlin_model_ro):
    findings = run_from_model(catlin_model_ro, [], only="code.E3902_gfci_locations").findings
    for tag in OUTDOOR:
        hits = [f for f in findings if f.message.startswith(f"{tag} ")]
        assert hits and all("(outdoors)" in f.message and f.result.value == "pass"
                            for f in hits), (tag, [f.message for f in hits])
