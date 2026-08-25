"""Catlin product catalog — brand and model number, as structured data (→ model/product.py).

Every product here was already chosen; it was chosen in *prose*. ``APPL-LG-WASHTOWER``'s
``name`` says "LG WashTower WKHC252HBA" and its ``source`` says it again in a paragraph, and
neither is something the sidebar, the schedules or the estimate can read — a reader chasing
"what did we actually buy" had to parse an English sentence. That is the "disconnected
document" problem in miniature, and this file is the fix: one record per chosen product,
referenced by ``product_ref`` from the type or material that is it.

**Identity only, never a price** (``plans/01-decisions.md`` #28). Not a dollar figure, not a
vendor, not availability — those belong to ``prices.toml`` and ``costs.toml``, which are the
house's own documents and stay outside the model. ``library/hardware.py`` has shipped
manufacturer + model since the connector catalog landed; this is the same split, written down.

NOT ``# haus: editable``: like ``appliance_types.py`` and ``lighting_types.py`` this is a
catalog of definitions, not placed instances. Nothing here is draggable in the UI.

**The prose stays.** Each type's ``name=`` and ``source=`` are unchanged — this record carries
the identity, the ``source`` keeps the reasoning (why Frigidaire and not LG, why no water is
connected, what the datasheet said and when it was read), and rewriting the names to avoid
saying a model number twice would churn every schedule and its tests for no gain.
"""

from __future__ import annotations

from typehaus.model import Product

# --- the LG kitchen and laundry ---------------------------------------------------------
#
# The owner's LG choice, three machines (plan/appliance_types.py). The model number IS the
# order — LG sells the WashTower in two finishes (WKHC252HBA black steel, WKHC252HWA white),
# so the letter that ends the model is a real distinction and not a suffix to trim.
LG_WASHTOWER = Product(
    tag="PROD-LG-WKHC252HBA", brand="LG", model="WKHC252HBA",
    name="WashTower (washer + heat-pump dryer)",
    source="LG USA spec sheet, read 2026-08-24 — see APPL-LG-WASHTOWER for the dimensions "
           "and the electrical requirement this identity was chosen against.",
)
LG_INDUCTION_RANGE = Product(
    tag="PROD-LG-LSIL6336FE", brand="LG", model="LSIL6336FE",
    name="InstaView 30\" induction slide-in range",
    source="LG Pro Builder spec sheet, read 2026-08-24. The LG STUDIO LSIS6338F is the same "
           "chassis in Studio trim; several retailers show it discontinued.",
)
LG_DISHWASHER = Product(
    tag="PROD-LG-LDTS5552S", brand="LG", model="LDTS5552S",
    name="QuadWash 24\" dishwasher with TrueSteam and 3rd rack",
    source="LG USA listing and owner's manual, read 2026-08-24.",
)

# --- the Frigidaire cold-storage pair ----------------------------------------------------
#
# Not LG, and the reason is the bay rather than the badge — ``plan/appliance_types.py``'s
# note carries it in full. Two products, one order: they stand against each other, which is
# what TWINSPAIRKIT is for.
FRIGIDAIRE_ALL_REFRIGERATOR = Product(
    tag="PROD-FRIGIDAIRE-FPRU19F8WF", brand="Frigidaire", model="FPRU19F8WF",
    name="Professional 19 cu ft all-refrigerator column",
    source="Frigidaire spec sheet rev 10/21 and the shared Use & Care manual, read 2026-08-24.",
)
FRIGIDAIRE_ALL_FREEZER = Product(
    tag="PROD-FRIGIDAIRE-FPFU19F8WF", brand="Frigidaire", model="FPFU19F8WF",
    name="Professional 19 cu ft all-freezer column",
    source="Frigidaire spec sheet rev 10/21 and the shared Use & Care manual, read 2026-08-24.",
)

# --- mechanical and the backup microgrid -------------------------------------------------
#
# The Rheem tank is the one product in the house whose designation genuinely differs by
# channel: ``PROPH80 T2 RH400-30`` is the plumbing-wholesale number and
# ``XE80T10HS45U0`` the retail/AHRI one, for the same 80-gallon ProTerra. ``sku`` is where
# that second number belongs — it is what an order may actually be placed against.
RHEEM_PROTERRA_80 = Product(
    tag="PROD-RHEEM-PROPH80", brand="Rheem", model="PROPH80 T2 RH400-30",
    name="ProTerra 80 gal hybrid heat-pump water heater (EcoNet)",
    sku="XE80T10HS45U0",
    source="Rheem ProTerra datasheet — see EQ-T-WATER-HEATER for the 4.5 kW element and the "
           "30A/240V circuit this identity was chosen against.",
)
# "12kPV" is the PV *input*, not the output — the naming trap EQ-T-EG4-12KPV's note exists to
# defuse. Carried as the model because it is what EG4 prints on the box and what an order
# names; the 8 kW that matters to the autonomy calc stays on the EquipmentType, where a
# number belongs.
EG4_12KPV = Product(
    tag="PROD-EG4-12KPV", brand="EG4", model="12kPV",
    name="12kPV hybrid inverter",
    source="EG4 spec sheet, read 2026-08-02.",
)
EG4_POWERPRO_WALLMOUNT = Product(
    tag="PROD-EG4-POWERPRO-WM", brand="EG4", model="PowerPro WallMount Indoor",
    name="PowerPro WallMount Indoor 14.3 kWh LFP battery",
    source="EG4 product literature — UL 9540 listing declared on EQ-T-ESS-BATT, which is "
           "where a check reads it.",
)
# The ventilator. It is the one machine in this house whose *identity* changed a number the
# checks read: the placeholder it replaced carried SRE 0.75 with a `# TODO verify datasheet`
# against it, and the real unit's certified figure at this site's -15 F design temperature
# is 0.65. Picking the product moved the block load, which is the whole argument for
# recording what was actually bought.
BROAN_B210E75RT = Product(
    tag="PROD-BROAN-B210E75RT", brand="Broan", model="B210E75RT",
    name="B210E75RT energy recovery ventilator, 210 CFM",
    source="Broan published specifications, read 2026-08-25 — see EQ-T-BROAN-B210E75RT "
           "(plan/mep_erv.py) for the airflow, the port size and the two SRE figures, and "
           "for why the -13 F one is the one authored.",
)


PRODUCTS = (
    LG_WASHTOWER, LG_INDUCTION_RANGE, LG_DISHWASHER,
    FRIGIDAIRE_ALL_REFRIGERATOR, FRIGIDAIRE_ALL_FREEZER,
    RHEEM_PROTERRA_80, EG4_12KPV, EG4_POWERPRO_WALLMOUNT,
    BROAN_B210E75RT,
)
