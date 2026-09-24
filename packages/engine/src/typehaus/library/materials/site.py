"""Aggregates, soils, sod and geotextile."""

from __future__ import annotations

from typehaus.model import Material

MATERIALS: tuple[Material, ...] = (
    # The capillary break under it: open-graded crushed stone, compacted, no fines. The
    # break is the *absence* of small pores — water cannot wick up through voids this large —
    # so "4 inches of clean stone" is the specification and a well-graded base course, which
    # compacts better, is the wrong material for the job.
    Material(
        tag="capillary-break-stone",
        name="Compacted open-graded stone (capillary break, #57)",
        r_per_inch=0.0,
        density=1600.0,
        hatch="concrete",
        color="#8f8d88",
        source='IRC R506.2.2: a 4" base course of clean graded sand, gravel or crushed '
        'stone passing a 2" sieve under a slab-on-ground. #57 is the open-graded '
        "stone ACI 302.2R names for the capillary break; the point is the absence "
        "of fines, not the compaction",
    ),
    # The stone a crushed-stone FOOTING is built of, which is not the stone under a slab
    # above and not the stone in a footing bedding. 2024 IRC R403.4.1 specifies it directly —
    # angular, ASTM C33, 1/2" max and 1/16" min, free of organic/clayey/silty soils — and
    # that gradation is finer at the top end than #57 and coarser at the bottom than a base
    # course. It is a structural material here: under R403.5 this stone IS the footing, with
    # a wall bearing on it, rather than a capillary break or a bearing prep under one.
    Material(
        tag="footing-crushed-stone",
        name="Consolidated angular crushed stone footing (IRC R403.4.1)",
        r_per_inch=0.0,
        density=1600.0,
        hatch="concrete",
        color="#7d7b76",
        source="2024 IRC R403.4.1: clean crushed stone free from organic, clayey or "
        "silty soils, angular in nature and meeting ASTM C33, maximum size not "
        "exceeding 1/2 inch and minimum not smaller than 1/16 inch, consolidated "
        "using a vibratory plate in lifts not greater than 8 inches",
    ),
    Material(
        tag="rootzone-sand",
        name='USGA rootzone sand, 12" placed',
        density=1600.0,
        hatch="earth",
        color="#8b7a5e",
        source="USGA Recommendations for a Method of Putting Green Construction, Table 3/4.",
    ),
    Material(
        tag="usga-choker-sand",
        name='USGA intermediate (choker) sand, 2" placed',
        density=1600.0,
        hatch="earth",
        color="#b3a382",
        source="USGA putting-green construction, Table 2 intermediate layer.",
    ),
    Material(
        tag="usga-bridging-gravel",
        name='USGA bridging gravel, 3/8"',
        density=1600.0,
        hatch="gravel",
        color="#a09a90",
        source="USGA putting-green construction, Table 2 gravel gradation.",
    ),
    Material(
        tag="geotextile-separation",
        name="Non-woven geotextile separation fabric",
        perm_rating=100.0,
        hatch="membrane",
        color="#9a9a8c",
        source="AASHTO M288 Class 2 non-woven geotextile.",
    ),
    Material(
        tag="kbg-sod",
        name="Kentucky bluegrass sod, washed or sand-grown",
        density=1000.0,
        hatch="earth",
        color="#5f7a4a",
        finish="planted",
        source="USGA sod requirement for sand-rootzone construction; UMN turf guidance.",
    ),
)
