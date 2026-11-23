"""Lane L3 hand numbers (plain Python, no model load): the D-B-SUNKEN rim header and seats,
the veneer beam's bed, and the veneer ties' tributary widths. Inputs are the plan's authored
dimensions and the published values cited in the notes; run: python3 hand.py"""
import math

# --- 1. The rim header over D-B-SUNKEN (notes/sunken_door_band_header.md §2-§4) -------------
RO, PACK = 63.3125, 6.0                      # in
L = RO + PACK                                # c-c of bearing, in
trib_in = 1.125 + 14.875 / 2                 # edge rim line to half-way to the y=16" line
w = 50.0 * trib_in / 12.0 / 12.0             # lb/in at 40 + 10 psf
P = 325.73                                   # lb, door seat reaction (notes/exterior_door_sill_beam.md §3)
off = 4.96875                                # screw-group centroid in from the RO edge
a = PACK / 2 + off                           # distance from the bearing centre
R = w * L / 2 + P
M = w * L ** 2 / 8 + P * a
print(f"strip {50*trib_in/12:.3f} plf, L {L:.4f} in, a {a:.5f} in")
print(f"R {R:.2f} lb, M {M:.1f} lb-in = {M/12:.1f} lb-ft")
b, d = 2.5, 11.875                           # two 1 1/4" plies
E, Fb, Fv = 1.3e6, 1700.0, 425.0             # ESR-1387 Table 1, 1.3E, joist/beam orientation
Cv = (12 / d) ** 0.092
S = b * d ** 2 / 6
Mcap, Vcap = Fb * Cv * S, 2 / 3 * Fv * b * d
print(f"Cv {Cv:.4f}, S {S:.2f}, Mcap {Mcap:.0f} lb-in -> {M/Mcap:.4f}; Vcap {Vcap:.0f} -> {R/Vcap:.4f}")
I = b * d ** 3 / 12
Lft = L / 12
delta_w = 270 * (w * 12) * Lft ** 4 / (E * b * d ** 3) + 28.8 * (w * 12) * Lft ** 2 / (E * b * d)
delta_p = 2 * P * a * (3 * L ** 2 - 4 * a ** 2) / (24 * E * I)
print(f"deflection: strip {delta_w:.5f} in + seats {delta_p:.5f} in = {delta_w+delta_p:.5f} vs L/240 {L/240:.4f}")
print(f"bearing {R/(PACK*b):.1f} psi of 360 (TJ-8000 p.5 note 2)")
# equivalent uniform loads for the table read
wp = 12 * w
eq_v = wp + 2 * 2 * P / (L / 12) / 2
eq_v = 12 * 2 * R / L
eq_m = 12 * 8 * M / L ** 2
eq_d = wp + 12 * 384 * (2 * P * a * (3 * L ** 2 - 4 * a ** 2) / 48) / (5 * L ** 4)
print(f"equivalent uniform plf: shear {eq_v:.1f}, moment {eq_m:.1f}, deflection {eq_d:.1f}; row 1,582 -> {max(eq_v,eq_m,eq_d)/1582:.4f}")
print(f"hand capacity as uniform at 6'-0\" (72 in): moment {12*8*Mcap/72**2:.0f} plf, shear {12*2*Vcap/72:.0f} plf (table 1,582)")
# jamb stack and bearing (§5)
stack = 1708.35
print(f"jamb: stack {stack} lb; on rim+ply {stack/(PACK*b):.1f} psi; below the band {(stack+R):.1f} lb"
      f" -> host plates {(stack+R)/(PACK*b):.1f} psi, pack studs {(stack+R)/(4*1.5*5.5):.2f} psi")
print(f"rim alone: {stack:.0f}/3760 = {stack/3760:.3f}; {stack/0.5:.0f}/5400 = {stack/0.5/5400:.3f}")
print(f"seat nailing {P/(10/12):.1f}/560 = {P/(10/12)/560:.3f}")

# --- 2. The veneer beam's bed (notes/sunken_garden_veneer_beam.md §6l) -------------------
wy, wf = -6.0, -9.625                        # brick back, front (y in; north toward the house)
brick_w = 268.86                             # plf: 7.4244 ft x 3.625 in x 120 pcf
Hb = 17.75
def bed(B, west=-6.0, label=""):
    cen = west - B / 2
    own = B * Hb * 150 / 144
    res = (brick_w * ((wy + wf) / 2) + own * cen) / (brick_w + own)
    P_ = brick_w + own
    e = abs(res - cen)
    a_ = B / 2 - e
    q = P_ / (B / 12) if e <= B / 6 else 2 * P_ / (3 * a_ / 12)
    print(f"{label} B {B:g}: own {own:.1f}, total {P_:.1f} plf, e {e:.2f} (kern {B/6:.2f}), "
          f"contact {min(B, 3*a_):.2f}, peak {q:.0f} psf, avg {P_/(B/12):.0f} psf")
bed(12.0, label="as drawn")
bed(12.0, label="stone widened 4in south (contact stays the beam's 12in)")
bed(16.0, label="beam widened 4in south")

# --- 3. Tie tributary widths (§6l) --------------------------------------------------------
print(f"tie: 2.67 sf over 24 in rows carries {2.67*144/24:.2f} in of width; 2.0 sf {2*144/24:.1f} in")
