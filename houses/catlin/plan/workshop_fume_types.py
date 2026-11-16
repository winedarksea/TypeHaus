"""The workshop's solder-fume extractor: a benchtop carbon-filter unit, not a ducted hood.

NOT editable (``needs`` is a ``frozenset``). The instance is in ``plan/workshop_fume.py``.
The ERV's bench valve (REG-B-RET1, 6 cfm) is a near-source room extract only; capture at the
joint is this unit's job (owner, 2026-11-15; DESIGN-LOG "Workshop bench extract").
"""

from typehaus import ApplianceType, Product, Service, ServicePort
from typehaus.model import mm

HAKKO_FA400 = Product(
    tag="PROD-HAKKO-FA400-04", brand="Hakko", model="FA400-04",
    name="FA-400 benchtop smoke absorber, 120 V, activated-carbon filter",
    url="https://www.hakko.com/english/products/hakko_fa400_spec.html",
    source="Hakko FA-400 spec page and manual, read 2026-11-15: 166 W x 212 H x 113 D mm, "
           "0.91 kg, ~18 W, 1.1 m3/min (38.8 cfm) vertical / 0.5 m3/min horizontal. "
           "Filter is a consumable (A1001 carbon). Or equal: Weller Zero Smog class.",
)

FA400 = ApplianceType(
    tag="APPL-HAKKO-FA400-04", name="Benchtop solder-fume extractor (Hakko FA-400)",
    product_ref=HAKKO_FA400.tag,
    footprint=(mm(166), mm(113)), height=mm(212),
    needs=frozenset({Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120,
                       position=(mm(0), mm(-56), mm(0))),),
    source="Hakko FA-400, cord and plug to ED-B-WORKSHOP-RC2. Recirculating: filters the "
           "plume within ~6-8 in. of the nozzle and returns the air to the room.",
)

WORKSHOP_FUME_PRODUCTS = (HAKKO_FA400,)
WORKSHOP_FUME_APPLIANCE_TYPES = (FA400,)
