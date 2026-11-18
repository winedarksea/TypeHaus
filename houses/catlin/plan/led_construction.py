# haus: editable
# LED construction, declared once (decision #137): the channels the surface tape sits in and
# how the 24 V side is wired. Each LuminaireType's LedStrip (plan/lighting_types.py) names its
# tape and channel; the engine builds the section, fills modules, derives the leads
# (resolve/led_leads.py) and bills them in [light_run_materials]. Read 2026-11-17; a figure
# no sheet publishes is left unset (drawn generic, graded UNKNOWN), never guessed.
#   * Stair rail (mark E, 8 mm tape): Diode LED DI-CHB-S2 surface channel, frosted lens.
#   * Garage eaves and gable (mark W, 15 mm IP67 tube): Superlighting QSG-3211, 19.9 mm
#     inside, semi-clear flat PC cover. HL-BAPL057 (15 mm inside) leaves the tube no room.
#     No channel was found that publishes an IP rating: the IP67 is the tube's.
#   * Leads: the smallest of 18/16/14 AWG keeping the lead within 3% of 24 V. An RGB+CCT
#     run wants six conductors; no 6-conductor CL2 cable was found, so the gauge here is the
#     common conductor's and the conductor count is CONFIRM at order.

from typehaus import LedCable, LedChannel, LedStandard, Product, ft, inch, mm

DI_CHB_S2 = Product(tag="PROD-DIODE-DI-CHB-S2", brand="Diode LED", model="DI-CHB-S2", name="Diode LED CHROMAFLEX surface channel S2, frosted lens", url="https://www.diodeled.com/custom/download/productFile/filename/DI-CHB-S2-Specification%20Sheet.pdf", stock_length=inch(48), source="Spec sheet: 0.74 W x 0.57 H in. outside, 0.65 W x 0.34 in. deep inside, frosted lens, 48 or 96 in., IP20. Lens shape and wall thickness not published.")
DI_CHB_S2_ACC = Product(tag="PROD-DIODE-DI-CHB-S2-ACC", brand="Diode LED", model="DI-CHB-S2-ACC", name="Diode LED S2 channel accessory pack (end caps, clips)", url="https://www.diodeled.com/custom/download/productFile/filename/DI-CHB-S2-Specification%20Sheet.pdf", source="Same sheet: end caps and mounting clips, 2 clips per 48 in. stick. Clip spacing not published.")
QSG_3211 = Product(tag="PROD-SLL-QSG-3211", brand="SuperLightingLED", model="QSG-3211", name="Superlighting QSG-3211 flat U-channel for 15 mm strip, semi-clear PC cover", url="https://www.superlightingled.com/u-channel-led-aluminum-flat-profile-for-15mm-wide-strip-light-p-5768.html", source="Listing: 32.3 W x 11.8 H mm outside, 19.9 mm inside, semi-clear flat PC cover, no IP rating. Stick length, end cap and clip not read: CONFIRM.")
CABLE_18_4 = Product(tag="PROD-MONOPRICE-CL2-18-4", brand="Monoprice", model="CL2 18/4", name="18 AWG 4-conductor CL2 in-wall cable", source="Monoprice CL2 4-conductor 18 AWG (retailer listing, 2026-11-17). Gauge and rating as listed; SKU CONFIRM.")
CABLE_16_2 = Product(tag="PROD-SOUTHWIRE-10034-16-2", brand="Southwire", model="Romex SIMpull Control & Signal 16/2", name="16 AWG 2-conductor control and signal cable, TYPE CL2", url="https://cabletechsupport.southwire.com/cablespec/download_spec/?spec=10034", source="Southwire spec 10034: 16 AWG 2/C, legend TYPE CL2, 150 V.")
CABLE_14_2 = Product(tag="PROD-SOUTHWIRE-13093-14-2", brand="Southwire", model="Flat speaker wire 14/2 CL3", name="14 AWG 2-conductor CL3 cable", url="https://www.southwire.com/wire-cable/low-voltage-cable/flat-speaker-wire-cl3/p/SPEC13093", source="Southwire spec 13093: 14 AWG 2/C, UL 13 power-limited, CL3 (a permitted substitute for CL2, NEC 725.154).")
TAPE_CONNECTOR = Product(tag="PROD-COB-TAPE-CONNECTOR", brand="LEDsupply / SuperLightingLED", model="EZClick 2-pin 10 mm; COB-RGBW-ACCESSORIE-1 (12 mm)", name="Solderless COB tape-to-wire connector", url="https://www.ledsupply.com/led-strip-connectors/ezclick-2-pin-white-10mm-ip20-led/cob-strip-connector", source="EZClick 2-pin 10 mm (fixed and the stair rail); SuperLightingLED 12 mm 5-pin for RGBW. No 6-pin RGB+CCT COB connector was found: the coves are soldered or CONFIRM.")

LED_PRODUCTS = (DI_CHB_S2, DI_CHB_S2_ACC, QSG_3211, CABLE_18_4, CABLE_16_2, CABLE_14_2, TAPE_CONNECTOR)

LED_CONSTRUCTION = [
    LedChannel(uid="2MGQ3TGKDS", tag="CH-DIODE-S2", product_ref="PROD-DIODE-DI-CHB-S2", kind="u", outer_width=inch(0.74), outer_depth=inch(0.57), inner_width=inch(0.65), lens="frosted", stick_length=inch(48), end_cap_ref="PROD-DIODE-DI-CHB-S2-ACC", clip_ref="PROD-DIODE-DI-CHB-S2-ACC", source="DI-CHB-S2 sheet, read 2026-11-17. Lens drawn flat (shape not published); back drawn at the derived side wall."),
    LedChannel(uid="2KB028VAZ9", tag="CH-SLL-QSG-3211", product_ref="PROD-SLL-QSG-3211", kind="flat", outer_width=mm(32.3), outer_depth=mm(11.8), inner_width=mm(19.9), lens="clear", source="QSG-3211 listing, read 2026-11-17: semi-clear flat PC cover, drawn clear. Stick length CONFIRM."),
    LedStandard(uid="Y06Y5NED3F", tag="LED-STANDARD", cables=(LedCable(awg=18, product_ref="PROD-MONOPRICE-CL2-18-4", rating="CL2"), LedCable(awg=16, product_ref="PROD-SOUTHWIRE-10034-16-2", rating="CL2"), LedCable(awg=14, product_ref="PROD-SOUTHWIRE-13093-14-2", rating="CL3")), max_drop_pct=3.0, slack=0.10, max_controller_distance=ft(6), connector_ref="PROD-COB-TAPE-CONNECTOR", source="Owner, 2026-11-17 plan: 18/16/14 AWG CL2, 3% drop. A controller sits beside its driver, within 6 ft."),
]
