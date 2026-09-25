# haus: editable
# Catlin assemblies — the concrete mixes this house pours, named by every concrete assembly.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    ConcreteSpec,
    FiberSpec,
    ScmFractions,
    inch,
)


# ---------------------------------------------------------------------------------------
# The mixes this house pours. Three of them, stated once each and named by every concrete
# assembly below, because a mix is a *purchase* — one ticket from one plant — and spelling
# the same numbers out per assembly is how two pours that must be identical stop being.
#
# Until ``ConcreteSpec`` existed none of this was sayable: the engine hardcoded one
# presumptive 3,000 psi for every concrete calc it ran, and cover was regex-scraped out of
# the free-text cage string on a Post. The prose in each ``source=`` below said the right
# thing and nothing read it.
#
# **Fiber is in all three, and it is not the same fiber.** Macro-synthetic carries a
# post-crack residual and is visible at a finished surface, which is fine on a footing, a
# garage slab or a buried wall and wrong on a floor anybody looks at. Micro-monofilament is
# the polishable one — it targets *plastic shrinkage* in the first hours, and the little of
# it that presents at the surface sits in the paste layer a cream polish grinds off. Steel
# fiber is foreclosed anywhere near a finished or exposed face: it rust-stains.
#
# ** F0 ON THE BURIED MIX IS EARNED, NOT ASSUMED. ** ACI's F categories grade freeze-thaw,
# and a strip footing bearing below Ramsey County's 42" frost depth does not freeze. The
# three sunken-garden-face strips are the exception that proves it — they bottom out 8"
# below the garden floor and are frost-protected by wings under IRC R403.3
# (FOOTING_EXPOSED_20 below), which is a detail precisely because the concrete there IS in the
# freezing zone. ``exposure_s`` is left UNSET on all three: nobody has run a soil sulfate
# test, and "S0" would be an assumption wearing a measurement's clothes.
# ** 5,000 psi, AND THAT SETTLES A STANDING OPEN QUESTION. ** IRC Table R402.2's basement-
# wall row is 3,000 psi, which is what every calc in this engine presumed and what
# `notes/sunken_garden_court_free_body.md` §9, `notes/sunken_garden_piers.md` §6 and
# `plans/TODO.md` all flagged as unresolved: **MN Rules 1309.0402 amends R402.2 with a
# FOOTINGS row at 5,000 psi.** Footnote g's 2,500 psi relief needs an approved
# water/vapour-resistance admixture, and footnote h exempts deck/porch post footings, wood
# foundations and floating slabs — a house or garage strip footing is none of those. So the
# amendment applies, 5,000 is the number, and the three notes above are updated to say the
# question is answered rather than open.
#
# w/cm 0.40 rather than a strength-only spec: it is what 5,000 psi wants anyway, and W1
# durability is bought by permeability and not by cylinder strength.
BURIED_MIX = ConcreteSpec(
    fc_psi=5000.0,
    w_cm_max=0.40,
    exposure_f="F0",
    exposure_w="W1",
    exposure_c="C1",
    cover=inch(3.0),
    # ** GALVANIZED, AND ACI DOES NOT REQUIRE IT HERE. ** C1 is "exposed to moisture but not
    # to an EXTERNAL source of chlorides", and Table 19.3.2.1 asks nothing of the bar for it
    # beyond cover. This is the owner's 2026-09-02 call — hot-dip house-wide, epoxy rejected
    # because it delaminates and stainless because it is 4-6x and fights the concrete
    # thermally — taken on the argument that the whole point of a buried pour is that you
    # never see it fail and never get to fix it. Recorded as a decision, not as a code
    # requirement, so nobody later reads it as one and "corrects" a pour that omits it.
    bar_coating="hdg-a767",
    # A767 class 1, chromate-passivated: the 2026-09-02 house-wide HDG call (see the
    # SUNKEN_GARDEN_COLUMN_12 comment). Not waived.
    chromate_treatment="passivated",
    fiber=FiberSpec(kind="macro-synthetic", dose_pcy=4.0),
    scm="25% class F fly ash",
    # The `scm` line read as a whole statement: fly ash only. The cement is still unnamed,
    # so the F3 cap grade on EXPOSED_MIX stays UNKNOWN until the mix design names it.
    scm_fractions=ScmFractions(fly_ash_pct=25.0, slag_pct=0.0, silica_fume_pct=0.0),
    max_aggregate=inch(0.75),
    source="strip footings and buried stems below frost depth: MN Rules 1309.0402's 5,000 psi FOOTINGS amendment to IRC Table R402.2, ACI 318-19 Table 19.3.2.1 for F0/W1/C1, and 3\" cover per Table 20.5.1.3.1(a) cast against and permanently in contact with ground",
)

EXPOSED_MIX = ConcreteSpec(
    fc_psi=5000.0,
    w_cm_max=0.40,
    air_content_pct=6.0,
    air_tolerance_pct=1.5,
    exposure_f="F3",
    exposure_w="W1",
    exposure_c="C2",
    bar_coating="hdg-a767",
    chromate_treatment="passivated",
    fiber=FiberSpec(kind="macro-synthetic", dose_pcy=4.0),
    scm="25% class F fly ash",
    # At Table 26.4.2.2(b)'s 25% fly ash cap exactly, not under it.
    scm_fractions=ScmFractions(fly_ash_pct=25.0, slag_pct=0.0, silica_fume_pct=0.0),
    max_aggregate=inch(0.75),
    source="every exterior and salt-splash pour: ACI 318-19 Table 19.3.2.1 class F3 + C2 — w/cm 0.40, f'c 5,000, 6%+/-1.5 air — with ASTM A767 class 1 galvanized bar. Cover is authored per pour, because on a 12\" round column it costs moment and on a footing it is free",
)

# ** TWO INTERIOR MIXES, BECAUSE MICRO AND MACRO FIBRE ARE NOT THE SAME PURCHASE. ** These
# were one mix until 2026-09-03, and that conflated two products answering two questions:
#
#   * MICRO-monofilament targets PLASTIC shrinkage — the first hours, before the concrete has
#     any strength. It carries no post-crack residual, so it replaces NO steel and no mesh.
#     It is what a thin cap over EPS wants and what a LIGHT trowel embeds cleanly
#     (GCP TB-1204: magnesium bullfloat, jitterbug, finish late), which is why SL-M-DECK is
#     poured from it (notes/mixed_deck_movement_joint.md, which has said "replaces no
#     steel" all along).
#   * MACRO-synthetic carries a measurable post-crack residual (ASTM C1609) and is what ACI
#     544.4R recognises as a replacement for welded wire mesh against DRYING shrinkage and
#     thermal movement. It is also visible at a finished surface, which is exactly why it
#     cannot go in the floor above.
#
# ** THE 2026-09-12 FINISH CHANGE DID NOT MOVE THE FIBRE, AND THE REASON CHANGED. ** The cap
# now takes a coating rather than a cream polish, so the old argument ("what little presents
# at the surface sits in the paste a cream polish removes") is gone. The answer is the same
# fibre for a new reason: the coating route grinds to ICRI CSP 2-3, which would RE-EXPOSE a
# macro fibre rather than remove it, and ANSI/SDI C-2017's mesh substitution needs >=4.0
# lb/cy — a different dose and a different argument, not a drop-in swap. Micro stays.
#
# One mix serving both meant SL-B-FLOOR — 14 CY of basement slab on grade — had nothing at all
# controlling drying shrinkage: no mesh, and a fibre that does not do that job. The house
# elsewhere claims "fibre replaces the mesh", and for EXPOSED_MIX's garage and garden
# slabs that is true. It was not true here, and the fix is a second mix rather than a quieter
# claim.
DECK_CAP_MIX = ConcreteSpec(
    fc_psi=4000.0,
    w_cm_max=0.45,
    exposure_f="F0",
    exposure_w="W0",
    exposure_c="C0",
    bar_coating="black",
    fiber=FiberSpec(kind="micro-synthetic", dose_pcy=1.5,
                    product="monofilament PP, 1/2\" - confirm the dose against the supplier TDS and the finisher before ordering"),
    max_aggregate=inch(0.75),
    source="the deck cap SL-M-DECK, coated: no chloride, no freeze-thaw, so black bar and galvanizing would buy nothing. Micro-MONOFILAMENT fibre, deliberately NOT macro — it targets plastic shrinkage (what a thin cap over EPS is prone to), replaces no steel (ACI 544.4R, ICC-ES ESR-1699), and is the fibre a LIGHT steel trowel embeds. Macro would be re-exposed by the CSP 2-3 grind the coating needs (notes/mixed_deck_movement_joint.md)",
)

# ** NO ENTRAINED AIR, AND THAT IS NOT AN OMISSION. ** Both interior mixes leave air unset,
# and a hard-trowelled floor is the one place where entrained air is actively WRONG. ACI
# 302.1R §5.7.1: "Entrained air is not recommended for concrete to be given a smooth, dense,
# hard-troweled finish because blistering and delamination may occur" — the entrained air
# slows bleed water's rise, the trowel seals a surface over water still coming up, and the
# risk climbs with every percent of air. At the 6% EXPOSED_MIX carries it is already
# a bad bet.
#
# ** AND THE ORDER DESK IS WHERE THIS IS LOST. ** Air is a plant default in Minnesota —
# a winter batch plant ships air-entrained unless told otherwise, and "interior slab" is not
# the instruction. Say "NO ENTRAINED AIR" on the ticket and check the delivered air content
# at the truck, because nothing downstream of the pour can undo it.
#
# F0/W0/C0 is what makes omitting it safe: there is no freeze-thaw indoors to need the air
# for, so the two requirements never collide. They WOULD collide on a hard-trowelled exterior
# slab, and this house has none — the garage and garden slabs take the air and a broom or
# float finish. `structural.concrete_mix_matches_exposure` agrees by construction, because F0
# is not in its air-required set; nothing yet grades the converse, and a rule that says "an
# F1-F3 pour must not be hard-trowelled" has nowhere to read the finish from today.
INTERIOR_SLAB_MIX = ConcreteSpec(
    fc_psi=4000.0,
    w_cm_max=0.45,
    exposure_f="F0",
    exposure_w="W0",
    exposure_c="C0",
    bar_coating="black",
    fiber=FiberSpec(kind="macro-synthetic", dose_pcy=4.0),
    max_aggregate=inch(0.75),
    source="the basement slab on grade SL-B-FLOOR: same 4,000 psi F0/W0/C0 as the polished cap, and the same dose of the same macro-synthetic fibre EXPOSED_MIX carries, so the house buys one macro product and not two. Macro rather than micro because this slab has no mesh and something has to carry drying shrinkage and thermal movement (ACI 544.4R); it is a service floor with a covering over it, so the surface visibility that rules macro out of SL-M-DECK does not apply. Control joints are still required and are not modelled here",
)

# ** THE WASH LAYER'S THICKNESS IS A RENDER DECISION, NOT A CLAIM ABOUT FILM BUILD. ** A
# two-coat mineral silicate wash is a film, not a board; `PAINT_FINISH` above carries such a
# film at inch(0.01) and that is the honest number. It cannot be used here, and the reason is
# the renderer rather than the chemistry.
#
# `Material.coating=True` does NOT stop a WALL layer from drawing: `_is_coating`
# (emit/gltf/emitter.py) is scoped to room FLOOR finishes — a sealer on the deck rather than a
# covering over it — and wall layers draw by thickness regardless. So the wash gets a real
# plane, and at 0.01" that plane sits 5 thousandths of an inch off the concrete behind it, which
# is inside the depth buffer's precision at this scene's scale: the viewer flashes the grey
# substrate through the white face as the camera moves. That was observed, not predicted.
#
# ** 1/8", AND THE DEPTH-BUFFER ARGUMENT THAT USED TO PICK IT IS GONE. ** For a while this
# value was a renderer workaround. `Material.coating=True` does NOT stop a wall layer drawing
# (`_is_coating` is scoped to room FLOOR finishes), so the wash gets a real plane, and at
# `PAINT_FINISH`'s honest inch(0.01) it z-fought: Panel3D's ordinary 24-bit depth buffer on
# `PerspectiveCamera(50, 1, 0.05, 500)` resolves only about z^2 * 1.19e-6 metres (0.48 mm at
# 20 m, 3.2 mm at 52 m), so the viewer flashed grey through the white. Thickening it was a losing
# race — 0.01", 1/16" and 1/8" all still shimmered — and the race is over: the viewer now gives
# every wash surface a `polygonOffset` (`WASH_POLYGON_OFFSET` in ui/src/three/materials.ts),
# which wins the depth test deterministically at ANY camera distance.
#
# So the thickness is free to be a thickness, and 1/8" is kept on build grounds rather than
# render ones: it is two coats plus, on the SRW block, the whole-face Quartz Filler or Bonding
# Coat the Beeckosil TDS requires as a CMU pretreatment — and it is exactly what this house's
# other coating, `foundation-coating-acrylic`, has carried since 2026-09-04. It is deliberately
# NOT `PAINT_FINISH`'s 0.01": that is a brushed latex film on gypsum, which this is not.
#
# ** ONE PARITY CAVEAT. ** glTF has no `polygonOffset`, so an exported .glb opened in a third-party
# viewer can still shimmer here where the live viewer does not. That is a limitation of the
# format, not a reason to re-inflate this number (-> glb-emitter-parity).
#
# Nothing numeric rides on the value: a coating bills by COVERAGE AREA (`Material.coating`'s own
# contract), its R/inch is 0.0, and its vapour rating is authored as a thickness-independent
# PERMEANCE precisely so this cannot leak into the Glaser walk. What it DOES move is geometry —
# each washed wall grows 1/8" — which is why it is a named constant rather than a number buried in
# three layer literals, and why every washed wall carries an `alignment` of HALF this value so the
# pour itself does not move. **Change this and every one of those offsets changes with it.**
_WASH_FILM = inch(0.125)
