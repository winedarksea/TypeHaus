"""The scorecard's fixed target list (``cli/route_scorecard.py``; docs/routing.md).

A target is a mode and a tag; ``route_scorecard_modes`` says how each mode is proposed.
Rows with no baseline entry cannot fail ``regressions()``: bless them (``--bless``) once
the entry point behind them is built."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreTarget:
    name: str
    #: tree | fixture | run | group | lift | trunk | manifold | house
    mode: str
    #: a run/fixture/room/equipment tag; for ``house`` a label (the scope is below)
    tag: str
    level: str | None = None
    lift: tuple[str, ...] = ()  #: ``lift``: authored runs the tree re-lays
    storey: str | None = None  #: ``house``: --storey
    trades: tuple[str, ...] = ()  #: ``house``: --trades


#: The fixed list: a drain tree per storey, the three fixtures with no 3D vent (TODO C6-E7),
#: the hand-drawn kitchen drain, three supply runs, then (wave 1) a duct per kind, vents,
#: condensate, radon, sump, conduits, a manifold, a basement duct campaign, and the rows
#: whose entry points E1/E2/E4 build (a ``not built`` stub records as a refusal).
TARGETS: tuple[ScoreTarget, ...] = (
    ScoreTarget("tree:basement", "tree", "PR-B-BATH-DRAIN"),
    ScoreTarget("tree:main", "tree", "PR-B-MAIN-DRAIN", level="main"),
    ScoreTarget("tree:second", "tree", "PR-M-S-SUITE-DRAIN"),
    ScoreTarget("fixture:BATH2-TUB", "fixture", "FX-M-BATH2-TUB"),
    ScoreTarget("fixture:SUITEBATH-LAV", "fixture", "FX-S-SUITEBATH-LAV"),
    ScoreTarget("fixture:SUITEBATH-TUBSH", "fixture", "FX-S-SUITEBATH-TUBSH"),
    ScoreTarget("run:KITCH-DRAIN", "run", "PR-B-KITCH-DRAIN"),
    ScoreTarget("run:SUITE-LAV-CW", "run", "PR-S-SUITE-LAV-CW"),
    ScoreTarget("run:BATH2-LAV-HW", "run", "PR-M-BATH2-LAV-HW"),
    ScoreTarget("run:CW-SUITE", "run", "PR-B-CW-SUITE"),
    # Ducts: a 4" round ERV radial, a 6" round heat-pump radial, the rectangular HP supply trunk.
    ScoreTarget("duct:ERV-R-LIVING", "run", "DU-M-ERV-R-LIVING"),
    ScoreTarget("duct:HP-BED2", "run", "DU-S-HP-BED2"),
    ScoreTarget("duct:HP-SUP-TRUNK", "run", "DU-S-HP-SUP"),
    ScoreTarget("duct:ERV-RET-TRUNK", "run", "DU-B-ERV-RET-TRUNK"),
    ScoreTarget("vent:M-BATH2", "run", "PR-M-BATH2-VENT"),
    ScoreTarget("vent:M-KITCH", "run", "PR-M-KITCH-VENT"),
    ScoreTarget("condensate:HEADS", "run", "PR-M-COND-HEADS"),
    ScoreTarget("condensate:WH", "run", "PR-B-WH-COND"),
    ScoreTarget("radon:LEG", "run", "PR-B-RADON-LEG"),
    ScoreTarget("sump:DISCH", "run", "PR-B-SUMP-DISCH"),
    ScoreTarget("conduit:KITCHEN", "run", "CD-B-KITCHEN"),
    ScoreTarget("conduit:WORKSHOP", "run", "CD-B-WORKSHOP"),
    ScoreTarget("manifold:HW-HEADER", "manifold", "EQ-B-HW-HEADER"),
    ScoreTarget("house:basement-duct", "house", "basement-duct", storey="basement",
                trades=("duct",)),
    # E1 / E2 / E4 rows. ``trunk:CW`` reads developed_ft off the trunk proposal alone.
    ScoreTarget("tree:main+lift", "lift", "PR-B-MAIN-DRAIN", level="main",
                lift=("PR-B-HW-KITCH", "PR-B-CW-WH", "PR-B-CW-BATH")),
    ScoreTarget("group:BATH2", "group", "RM-M-BATH2"),
    ScoreTarget("group:SUITEBATH", "group", "RM-S-SUITEBATH"),
    ScoreTarget("tree:CW-TRUNK", "tree", "PR-B-CW-TRUNK"),
    ScoreTarget("trunk:CW", "trunk", "PR-B-CW-TRUNK"),
)
