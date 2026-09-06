"""Catlin railing catalog — the one guard product the shared library does not carry.

``library/railings.py`` holds RAILING-EXT-ALUMINUM-FASCIA and RAILING-INT-STAIR-GUARD, and
both stay there. What it has no entry for is a SURFACE-mounted exterior aluminium guard,
which is what RL-SG-PORCH became on 2026-09-03 when its west and east legs were found to
run along 12" concrete wall tops — a substrate that takes ESR-3485's four 1/4" x 3"
baseplate anchors directly and wants no fascia bracket at all.

**Why a second type rather than reusing the fascia one.** The two are the same alloy, the
same finish, the same 42" and the same run, and they are NOT the same order: a fascia guard
is bought with a bracket kit at every post and a surface guard is bought with its post
welded to a baseplate. ``takeoff/railings.py`` groups by ``type_ref``, and prices.toml
carries a rate per type, so one type_ref for both would bill fascia brackets on a wall top
where none exist and average two labour rates that differ by the fascia premium.

House-local rather than promoted: the library keeps the fascia type alone until a second
house asks for this one, per CONTRIBUTING.md. Tags are disjoint from the library's, which
``integrity.duplicate_catalog_tag`` proves.

NOT ``# haus: editable``: a catalog type definition is not a placed instance. The Railing
that references this tag lives in ``params/sunken_garden.py``.
"""

from __future__ import annotations

from typehaus import RailingType

RAILING_EXT_ALUMINUM_SURFACE = RailingType(
    tag="RAILING-EXT-ALUMINUM-SURFACE",
    name="Exterior aluminum surface-mounted guard",
    source="Surface-mounted aluminum guard, deck/porch product class — Williams "
           "Architectural Products 42\" black (ICC-ES ESR-3485; 6063/6005A alloys, "
           "AAMA-grade powder coat, maximum post spacing 91.3\" at 42\"), Fortress Al13 "
           "Home as the alternate. Posts arrive welded to a 5\" x 5\" baseplate and take "
           "four 1/4\" x 3\" corrosion-resistant anchors into concrete, or four through-"
           "bolts into framing where there is no concrete under them",
)

RAILING_TYPES = (RAILING_EXT_ALUMINUM_SURFACE,)
