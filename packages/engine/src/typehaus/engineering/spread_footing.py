"""A belled pier's bearing on the ground — ``spread_footing/<Post tag>``.

The item ``structural.deck_footing_size`` hands off when a deck post bears on a ``Footing``
rather than a ``Pad``. That is not the check failing to reach: it is the honest statement
that IRC Table R507.3.1 publishes flat-pad rows and these are augered shafts with belled
bases, which the table has no row for and never will.

What it does instead is the question R507.3.1 actually asks — is the pressure under the bell
inside the presumptive allowable — answered in numbers a reviewer can disagree with.

**Oracle.** ``houses/catlin/notes/sunken_garden_piers.md``, hand-worked in a separate pass;
``tests/test_pier_calcs.py`` reproduces it.

**Screening, not a design.** Presumptive code-table values only, no geotechnical report; no
settlement, no group effect, no uplift and no lateral case. See ``retaining_basis`` for the
same disclaimer at more length — it is the same site and the same missing boring.
"""

from __future__ import annotations

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.pier_basis import (
    DECK_DEAD_LOAD_PSF,
    DECK_LIVE_LOAD_PSF,
    _Pier,
    cast_piers,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys
from typehaus.engineering.soil import CONCRETE_UNIT_WEIGHT_PCF, presumptive

KIND = "spread_footing"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "1"
BASIS = "IRC R507.3.1; IBC Table 1806.2 presumptive values"


def _piers_on_their_own_footing(ctx: EngineeringContext) -> list[_Pier]:
    """The subset ``cast_piers`` yields that this module governs — one with a ``Footing``.

    ``cast_piers`` also yields a pier on a ``Pad``, and a ``Pad`` **is** an IRC Table
    R507.3.1 row: ``structural.deck_footing_size`` sizes it against the same tributary and
    the same presumptive soil, prescriptively. Minting an engineered bearing record beside
    that one would put two authorities on one number and gain nothing — the table publishes
    the flat-pad case, which is exactly what a pad is. What has no row is the augered BELL,
    and a bell arrives as a ``Footing``.

    ``shared_wall_footing`` is excluded for the identical reason at the other end of the
    scale. Since 2026-09-03 ``cast_piers`` also yields a column standing on a concrete
    foundation WALL, carried by that wall's continuous strip footing — catlin's four balcony
    corner columns on W-SG-W1/E1. That footing already has an authority:
    ``structural.foundation_unbalanced_fill`` grades it as ``retaining_wall/<tag>``, on the
    wall's own bearing, sliding and overturning. Computing a point pressure on the same
    concrete from this side would be a second answer to one question, and the weaker of the
    two — a strip footing under a wall does not bear like an isolated pad under a post.
    """
    return [pier for pier in cast_piers(ctx)
            if pier.footing_tag and not pier.shared_wall_footing]


@keys(KIND)
def enumerate_piers(ctx: EngineeringContext) -> list[str]:
    return [pier.tag for pier in _piers_on_their_own_footing(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, pier) for pier in _piers_on_their_own_footing(ctx)]


def _one(ctx: EngineeringContext, pier: _Pier) -> EngineeringRecord:
    tags = tuple(t for t in (pier.tag, pier.footing_tag) if t)
    soil = presumptive(getattr(ctx, "soil_class", None))
    if soil is None:
        return EngineeringRecord(
            item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{pier.tag}: the bearing check could not run",
            missing=("a declared soil class (Site/profile soil_class)",),
            element_tags=tags)

    # **The bell bears on the SITE's own soil, not on a replacement section, and that is the
    # one judgement in this module.** The retaining footings sit on 42" of washed stone and
    # `retaining_basis._base_interface` reads IBC class 3 off it for exactly that reason.
    # These two do not: `params/sunken_garden.py` augered both bells to frost depth
    # precisely so they would bear on undisturbed soil, and what they carry is a
    # 7" LEVELLING course (`SPEC.pier_levelling_bedding_in`), not a soil replacement. A
    # 7" course spreads load into the native soil within inches of the bell, so crediting
    # the stone's 3,000 psf here would be reading a 42" section's allowable off a bedding
    # that is a sixth of it. The site's class governs, which is the conservative direction.
    bearing = (pier.service_lb + pier.footing_weight_lb) / pier.bearing_area_ft2
    states = (
        LimitState("bearing", bearing, soil.allowable_bearing_psf, "psf",
                   f"IBC Table 1806.2 class {soil.ibc_class} ({soil.soil_class}), "
                   f"presumptive"),
    )
    over = any(not state.ok for state in states)
    inputs = (
        Quantity("tributary_area", pier.tributary_ft2, "ft2", 0.01),
        Quantity("bell_width", pier.footing_width_in, "in", 0.5),
        Quantity("bell_depth", pier.footing_depth_in, "in", 0.5),
        Quantity("bearing_area", pier.bearing_area_ft2, "ft2", 0.001),
        Quantity("column_diameter", pier.diameter_in, "in", 0.5),
        Quantity("column_height", pier.height_in, "in", 0.01),
        Quantity("carried_dead", pier.carried_dead_lb, "lb", 1.0),
        Quantity("dead_load", pier.dead_lb, "lb", 1.0),
        Quantity("live_load", pier.live_lb, "lb", 1.0),
        Quantity("allowable_bearing", soil.allowable_bearing_psf, "psf", 1.0),
        Quantity("concrete_unit_weight", CONCRETE_UNIT_WEIGHT_PCF, "pcf", 1.0),
    )
    notes = (
        f"SCREENING on presumptive code values, not a design: {soil.citation}. No "
        f"geotechnical report is on file for this site.",
        f"Service load {pier.service_lb:,.0f} lb + {pier.footing_weight_lb:,.0f} lb of bell "
        f"over {pier.bearing_area_ft2:.2f} ft2. Tributary {pier.tributary_ft2:.1f} ft2 at "
        f"{DECK_DEAD_LOAD_PSF:.0f} psf dead + {DECK_LIVE_LOAD_PSF:.0f} psf live (IRC "
        f"Table R301.5), plus the column's own {pier.self_weight_lb:,.0f} lb.",
        "THE BELL IS READ AS A CIRCLE. `resolve/envelope.py` draws a post-hosted footing as "
        "a SQUARE of side `width`, and `params/sunken_garden.py` calls that number a bell "
        "DIAMETER — taking the square would credit 27% more bearing area than exists.",
        "Bearing is taken on the SITE's own class, not on the washed-stone value the "
        "retaining footings earn: these bells were augered to frost depth to bear on "
        "undisturbed soil, and their 7\" levelling course is not a soil replacement.",
        "Not checked: settlement, group effect, uplift, lateral load on the shaft.",
        "AND THERE IS NO DEPTH OR WIDTH BONUS TO CLAIM. IBC 1806.3.3's 'increase for depth' "
        "raises LATERAL bearing only, and 1806.3 is scoped to resistance to lateral loads; "
        "2018 IBC has no provision raising presumptive VERTICAL pressure for a deeper or "
        "wider footing. (The +20%/ft, 3x cap some references remember is 1997 UBC Table "
        "18-I-A and did not carry into the IBC.) The only sanctioned escalators are 1806.1's "
        "one-third with the alternative wind/seismic combinations, and 1806.2's 'data to "
        "substantiate the use of higher values' — which means a boring, not a table.",
    )
    if pier.carried_dead_lb or pier.tributary_ft2 <= 0.0:
        notes = notes + (
            f"This pier carries a post standing ON it as well as its own deck share — the "
            f"{pier.tributary_ft2:.1f} ft2 above includes what that post hands down, which "
            f"is the share `structural.deck_footing_size`'s N/A on it promised would be "
            f"picked up here.",
        )

    return EngineeringRecord(
        item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{pier.tag} on a {pier.footing_width_in:.0f}\" belled pier: "
                 f"{bearing:,.0f} psf against the {soil.allowable_bearing_psf:,.0f} psf "
                 f"IBC Table 1806.2 presumes for {soil.soil_class}"),
        inputs=inputs, limit_states=states, notes=notes, element_tags=tags)
