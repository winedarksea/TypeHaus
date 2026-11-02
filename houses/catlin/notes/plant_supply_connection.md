# Plant-room heat-pump supply connection

`REG-S-HP-PLANT` is centred at x=14′8″, y=3′3″. It moves 2′8″ east from the previous
location, leaving approximately 5′ to the actual extract location. Retain 75 cfm and the
existing RH interlock. Aim the double-deflection blades west across the planting. This is
a distribution intent, not a verified window-wash or throw result.

## Parts and dimensioned section

One `REG-T-HP-CEIL-DAMPERED` allowance buys all five items below. The actuator ships with
the damper; it is neither a second purchase nor a second allowance.

| Item | Specification | Installed band above grille face |
|---|---|---|
| Grille | TRUaire **A220V 12X06**, aluminium, white, **without OBD** | face datum |
| Collar | **TH-HP-PLANT-COLLAR-01**, 26ga galvanized, 12×6 passage | 0–½″ |
| Damper | Honeywell Home **ZD12X6TZ**, 12×6 nominal, vertical airflow | ½–4½″ |
| Actuator | Included M847D; conservative 4 1/16″ E-W × 4 31/32″ N-S × 4 41/64″ high box | ½–5 9/64″, west side |
| End boot | **TH-HP-PLANT-BOOT-01**, 26ga galvanized, 12″ E-W × 10″ N-S × 6″ high | 4½–10½″ |
| Service hatch | **TH-HP-PLANT-HATCH-01**, matching PVC cover 12×8 over 10×6 clear opening | cover below face plane |

```text
WEST                                               EAST
                 boot, closed west end       10×6 inlet at x=15′2″
 +10½″           ┌─────────────────────┐       ┌── 6″ level approach ──┐
                 │ turning vane        ├───────┘                       ╲
  +7½″           │                     │                         rise from x=17′6″
  +4½″           └───────12×6──────────┘
                 ┌─────────────────────┐
    +½″  [motor]─┤ ZD12X6TZ, 4″ body   │
     0″  hatch   └─────½″ collar────────┘
                 A220V grille (x=14′8″)
```

The motor is **west**, correcting the initially proposed east position: an east motor
would conflict with the rising feed. The damper's second dimension is the actuator side.
The boot's east inlet is full 10×6, centred 7½″ above the grille face. Its outlet is centred
12×6 downward, with closed side cheeks and a turning vane. Installed dimensions exclude
slip engagements; the fabricator adds engagement lengths without consuming the stated
clear passage or raising the assembly. Use sealed, mechanically secured sheet-metal joints.

The feed remains at its existing elevation across the x=18′ bearing line. It starts
rising at x=17′6″ and finishes at x=15′8″, followed by a 6″ level approach to the boot. The
last elevation is derived from the resolved grille face, not copied from an absolute Z.
The engine checks inlet centre, section, approach direction and a level mouth independently
of its legacy implicit-boot allowance.

The current cavity is z=228⅛–240″ absolute; the grille face resolves to approximately
229.12″. The boot top is approximately 239.62″, leaving **about ⅜″ below the deck**.
The two approximately 14° offset bends remain fabricated fittings; the fitting-pattern
check correctly leaves their throat/shop detail UNKNOWN pending the fabricator's drawing.
These are close design clearances: do not add unmodeled top flanges, insulation or hangers
in that margin. Support the boot and damper from the adjacent joists, not from the PVC
liner. No joist cuts are authorized. Confirm delivered frame, seams and supports before
fabrication; the geometry is an envelope, not a fabrication tolerance certificate.

## Service and humid-room seal

The grille opening alone cannot service the attached side actuator. Provide the separate
hatch at **x=13′4″, y=3′3″**, in the same joist bay. Its matching ½″ PVC screw-fixed cover
is 12×8; the fixed flanged curb has a 10×6 clear passage, a closed-cell EPDM compression
gasket and stainless captive screws. Seal the membrane continuously to the fixed curb
and to the grille collar's fixed perimeter. Neither service operation should peel a
membrane seal. Seal all duct seams against humid room air.

1. Isolate the 24 VAC supply; remove the grille and the gasketed hatch cover.
2. Reach through the hatch to disconnect wiring and release the actuator from its shaft.
   Withdraw it 6″ west, then lower it through the hatch. The modeled withdrawal corridor
   and lowering envelope clear framing, other services and fixtures; the detached motor's
   plan envelope fits inside the 10×6 clear opening.
3. Support the damper, release its accessible internal retaining screws and removable
   collar, and lower the damper through the 12×6 grille opening. Its frame is nominally
   5/32″ undersize per the ZD submittal. The boot stays supported above.
4. Reassemble, restore the compression gaskets, verify the seal and interlock, and
   rebalance to 75 cfm. Keep the actuator, wiring and both withdrawal paths unobstructed.

The model checks the motor box, blade envelope and removal corridors. Tool access,
delivered hardware and hand reach still require a physical dry fit before the liner is
closed. Do not label the assembly fabrication-released on the strength of envelope checks.

Sources: [TRUaire A220 family](https://rectorseal.com/hvac/a220-adjustable-double-deflection/),
[Resideo ZD specifications](https://customer.resideo.com/resources/Techlit/TechLitDocuments/33-00000s/33-00264.pdf),
[M847D dimension drawing](https://customer.resideo.com/resources/Techlit/TechLitDocuments/68-0000s/68-0247.pdf).
