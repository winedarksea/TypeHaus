"""Night-light motion sensor: IKEA MYGGSPRAY, the product and its device type.

NOT editable (types are never written back by a UI drag). Instances: ``plan/motion_sensors.py``;
register row and open verifications: ``notes/smart_home.md``. Owner chose it 2026-11-02.
"""

from typehaus import ElectricalDeviceType, Product, inch

MYGGSPRAY = Product(
    tag="PROD-IKEA-MYGGSPRAY", brand="IKEA", model="MYGGSPRAY 806.194.51",
    name="MYGGSPRAY wireless motion sensor, smart",
    url="https://www.ikea.com/us/en/p/myggspray-wireless-motion-sensor-smart-80619451/",
    source="IKEA page and manual AA-2664594-4-100, read 2026-11-02: Matter over Thread "
           "(E2494/E2706), 2x AAA/HR03 (~15 months on LADDA), IP67, 0..40 C, mount at most "
           "2 m (78.7\") high, screw or adhesive. Width 1 5/8\" (IKEA); a test measured 72 x "
           "39.5 mm (techtest.org). DEPTH NOT PUBLISHED: 1\" is an allowance. Joins HA over "
           "Thread through the ZBT-2 border router; HA support rests on IKEA's 'any Matter "
           "system with a Thread border router' claim, community-unconfirmed. "
           "Local-only register: notes/smart_home.md.")

# Battery: no branch circuit, no port, no box. Wall-mounted on the finished face.
DEVICE_TYPES = (
    ElectricalDeviceType(
        tag="ED-T-MOTION-MYGGSPRAY", name="Motion sensor, battery, Matter/Thread (IKEA MYGGSPRAY)",
        footprint=(inch(1.625), inch(1)), height=inch(2.75), needs=frozenset(), ports=(),
        device_box=False, product_ref=MYGGSPRAY.tag, source=MYGGSPRAY.source),
)
