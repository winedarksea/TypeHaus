"""Independent free body of the raised-garden SRW (AB Stones, 12 deg). Plain Python.

Inputs as printed on calcs/tiered_retaining.md. Written from first principles; the only
shared idea with the engine is the method named on the sheet (Coulomb, delta = 2/3 phi,
battered face, two-zone trial wedge).
"""
import math

D = math.radians
def deg(x): return math.degrees(x)

H_R, EMB = 10/3, 2/3
H = H_R + EMB                 # 4.000 ft free body, soil to the base of the base course
B, GW, OM = 0.97, 130.0, 12.0
EFP = 40.0
ZONE_T, ZONE_PHI = 1.0, 36.0
PAD_PHI = 36.0
SHEAR = 645.0
COURSE = 2/3

def phi_from_efp(efp, g):
    ka = efp / g
    return deg(math.asin((1 - ka) / (1 + ka)))

def coulomb_ka(phi, delta, omega, i=0.0):
    """Ka on a back face leaning INTO the fill by omega (beta = 90 - omega from horiz.)."""
    p, d, b, ii = D(phi), D(delta), D(90 - omega), D(i)
    num = math.sin(b + p) ** 2  # Das form uses angle from horizontal measured other way
    # Use the standard Coulomb form with alpha = back-face angle from horizontal (beta here)
    a = b
    num = math.sin(a + p) ** 2
    den = (math.sin(a) ** 2 * math.sin(a - d)
           * (1 + math.sqrt(math.sin(p + d) * math.sin(p - ii)
                            / (math.sin(a - d) * math.sin(a + ii)))) ** 2)
    return num / den

def wedge(h, g, phi_n, omega, delta, zone_t=0.0, zone_phi=None, step=0.001):
    """Culmann scan, planes through the heel. Face reaction inclined (delta - omega) above
    the normal-to-vertical (i.e. P makes delta with the face normal; face leans back omega)."""
    lean = math.tan(D(omega))
    best = (0, None, None, None)
    rho = 1.0
    top = deg(math.atan(1 / lean)) if lean else 89.9
    while rho < top - 0.01:
        r = D(rho)
        area = 0.5 * h * h * (1 / math.tan(r) - lean)
        tphi = math.tan(D(phi_n))
        share = 0.0
        if zone_t:
            z1 = min(zone_t * math.tan(r) / (1 - math.tan(r) * lean), h)
            share = z1 / h
            tphi = share * math.tan(D(zone_phi)) + (1 - share) * tphi
        pe = math.atan(tphi)
        if r > pe and area > 0:
            # force polygon: W vertical, R at pe from plane normal, P at (delta-omega) below horiz
            tilt = D(delta - omega)
            P = g * area * math.sin(r - pe) / math.cos(r - pe - tilt)
            if P > best[0]:
                best = (P, rho, share, deg(pe))
        rho += step
    return best

def body(g, mu_mode="ncma", zone=True, zone_phi=ZONE_PHI, delta_on=None, h=H, gw=GW):
    phi = phi_from_efp(EFP, g)
    delta = (2/3) * (phi if delta_on is None else delta_on)
    P, rho, share, pe = wedge(h, g, phi, OM, delta, ZONE_T if zone else 0.0, zone_phi)
    tilt = D(delta - OM)
    Ph, Pv = P * math.cos(tilt), P * math.sin(tilt)
    W = gw * B * h
    N = W + Pv
    mu = {"ncma": math.tan(D(min(PAD_PHI, phi))), "ibc": 0.25, "pad": math.tan(D(PAD_PHI))}[mu_mode]
    lean = math.tan(D(OM))
    Mo = Ph * h / 3
    Mr = W * (B / 2 + h / 2 * lean) + Pv * (B + h / 3 * lean)
    x = (Mr - Mo) / N
    e = B / 2 - x
    q = N / B * (1 + 6 * e / B) if e <= B / 6 else 2 * N / (3 * x)
    Pc = wedge(h - COURSE, g, phi, OM, delta, ZONE_T if zone else 0.0, zone_phi)[0]
    Vc = Pc * math.cos(tilt)
    return dict(phi=phi, P=P, rho=rho, share=share, pe=pe, Ph=Ph, Pv=Pv, W=W, N=N, mu=mu,
                FSs=mu * N / Ph, FSo=Mr / Mo, q=q, e=e, x=x, Vc=Vc, FSv=SHEAR / Vc,
                efp_h=2 * Ph / h ** 2, exit=h / math.tan(D(rho)))

def show(label, r):
    print(f"{label}: phi {r['phi']:.3f} rho {r['rho']:.3f} share {r['share']:.4f} phi_eq {r['pe']:.3f}"
          f" | P {r['P']:.2f} Ph {r['Ph']:.2f} Pv {r['Pv']:.2f} W {r['W']:.2f} N {r['N']:.2f}"
          f" mu {r['mu']:.4f} | FSs {r['FSs']:.3f} FSo {r['FSo']:.3f} q {r['q']:.1f}"
          f" e {r['e']:.4f} | course V {r['Vc']:.2f} FS {r['FSv']:.2f} | eff. horiz EFP {r['efp_h']:.1f} psf/ft"
          f" exit {r['exit']:.3f}")

print("=== 1. reproduce the graded case ===")
for g in (110, 130):
    show(f"{g} pcf", body(g))
print("\n=== 2. mu = 0.25 (IBC 1806.2 class 4) on the same thrust ===")
for g in (110, 130):
    r = body(g, mu_mode="ibc"); print(f"{g}: FS sliding {r['FSs']:.3f}")
print("\n=== 3. code EFP read literally: 40 psf/ft horizontal over 4.0 ft, no Pv ===")
Ph = 0.5 * EFP * H * H
W = GW * B * H
for mu, lab in ((math.tan(D(phi_from_efp(40, 110))), "tan27.8"), (0.25, "0.25"), (math.tan(D(36)), "tan36")):
    print(f"  Ph {Ph:.1f}  W {W:.1f}  mu {lab}: FS {mu * W / Ph:.3f}")
print("  over the retained 3.33 ft only:", f"Ph {0.5*EFP*H_R**2:.1f} FS(tan27.8) {math.tan(D(27.818))*W/(0.5*EFP*H_R**2):.3f}")
print("\n=== 4. sensitivities ===")
show("no rock 110", body(110, zone=False))
show("rock 34deg 110", body(110, zone_phi=34))
show("delta on rock 24deg 110", body(110, delta_on=36))
print("\n=== 5. all-granular retained prism (terrace fill specified phi>=34/36) ===")
for phif in (34.0, 36.0):
    for g in (110, 130):
        phin = phi_from_efp(EFP, g)
        d = (2/3) * phif
        P = wedge(H, g, phif, OM, d)[0]
        ka = P / (0.5 * g * H * H)
        tilt = D(d - OM)
        Ph, Pv = P * math.cos(tilt), P * math.sin(tilt)
        W = GW * B * H
        N = W + Pv
        lean = math.tan(D(OM))
        Mo = Ph * H / 3
        Mr = W * (B / 2 + H / 2 * lean) + Pv * (B + H / 3 * lean)
        # base interface: pad 36 over court backfill (native phi) -> mu = tan(min)
        for lab, mu in (("mu tan(native)", math.tan(D(min(PAD_PHI, phin)))), ("mu tan36 (granular under pad)", math.tan(D(36)))):
            print(f"  fill phi {phif} g {g}: Ka {ka:.4f} Ph {Ph:.1f} Pv {Pv:.1f} {lab} {mu:.3f}: FSs {mu*N/Ph:.3f}  FSo {Mr/Mo:.3f}")
print("\n=== 6. lower interface: pad (2.0' x 0.5') on native, thrust to -4.5' ===")
for g in (110, 130):
    phi = phi_from_efp(EFP, g)
    h2 = H + 0.5
    W = GW * B * H + 2.0 * 0.5 * 135.0 + 0.5 * H * 120.0 + 0.5 * EMB * g
    # (a) Rankine on vertical virtual back through the pad's heel edge, no wall friction
    ka = (1 - math.sin(D(phi))) / (1 + math.sin(D(phi)))
    PhA = 0.5 * g * ka * h2 * h2
    # (b) Coulomb, vertical virtual back, delta = phi (soil on soil) -- upper-bound friction
    kb = coulomb_ka(phi, phi, 0.0)
    Pb = 0.5 * g * kb * h2 * h2
    mu = math.tan(D(phi))
    print(f"  {g}: N0 {W:.1f}  (a) Rankine Ph {PhA:.1f} FS {mu*W/PhA:.3f}"
          f"  (b) Coulomb d=phi Ph {Pb*math.cos(D(phi)):.1f} Pv {Pb*math.sin(D(phi)):.1f}"
          f" FS {mu*(W+Pb*math.sin(D(phi)))/(Pb*math.cos(D(phi))):.3f}")
    # upper interface block on pad, mu tan36
    r = body(g)
    print(f"      block-on-pad, mu tan36, same thrust as sheet: FS {math.tan(D(36))*r['N']/r['Ph']:.3f}")
print("\n=== 7. options with numbers ===")
for h in (4.0, 4.333, 3.833, 3.667):
    r = body(110, h=h); print(f"  H {h:.3f}: FSs {r['FSs']:.3f} FSo {r['FSo']:.3f}")
# wider rock zone
for t in (1.5, 2.0, 2.97):
    phi = phi_from_efp(EFP, 110); d = 2/3 * phi
    P, rho, sh, pe = wedge(H, 110, phi, OM, d, t, 36.0)
    tilt = D(d - OM); Ph, Pv = P*math.cos(tilt), P*math.sin(tilt)
    print(f"  rock zone {t} ft: P {P:.1f} FSs {math.tan(D(phi))*(GW*B*H+Pv)/Ph:.3f}")
# cap weight credit: 4" AB cap ~ 0.33 ft x 0.97 x 130 (assumed same density; UNVERIFIED cap weight)
r = body(110)
Wcap = 130 * 0.97 * (4/12)
print(f"  + cap (4in, 130pcf assumed, UNVERIFIED) on H=4.0: FSs {r['mu']*(r['N']+Wcap)/r['Ph']:.3f}")
# AB's own resolution (cos delta), AB sample re-check
phi = 30; d = 0.66 * phi
ka = wedge(3.44, 120, phi, 12, d)[0] / (0.5 * 120 * 3.44**2)
print(f"\nAB sample check: Ka {ka:.4f} (AB prints 0.2197)")
