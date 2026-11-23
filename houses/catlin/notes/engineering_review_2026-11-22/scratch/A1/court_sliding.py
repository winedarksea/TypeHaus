"""Standalone court sliding review (no typehaus import). Inputs from the calc package + plan."""
import itertools, math
H, HS, T = 10.1198, 9.1198, 1.0          # retained height, stem height, stem thk (ft)
LS, LE, LW = 18.0, 16.3333, 16.3333      # axis lengths (engine convention)
BF_SIDE, BF_S, HEEL = 7.0, 8.3333, 3.0
APRON = 50.4834; APRON_ARM = 5.4362
GC = 150.0
def wall(efp=60, pcf=110, B=BF_SIDE, apron=True):
    thrust = 0.5*efp*H*H + (APRON if apron else 0.0)
    W = T*HS*GC + B*1.0*GC + HEEL*HS*pcf
    return thrust, W
def system(mu=0.35, efp=60, pcf=110, apron=True, extraN=0.0, extraF=0.0):
    tE, wE = wall(efp, pcf, BF_SIDE, apron); tS, wS = wall(efp, pcf, BF_S, apron)
    demand = tS*LS                          # E2/W2 cancel exactly (same symbols)
    N = wE*(LE+LW) + wS*LS + extraN
    return demand, N, mu*N + extraF, (mu*N+extraF)/demand
d, N, F, fs = system()
tE, wE = wall(); tS, wS = wall(B=BF_S)
print(f"thrust {tE:.2f} plf  wE {wE:.1f}  wS {wS:.1f}")
print(f"demand {d:,.0f}  sumN {N:,.0f}  friction {F:,.0f}  FS {fs:.4f}  d/c {1.5/fs:.3f}")
print("per wall own FS (at-rest):", round(0.35*wE/tE,3), round(0.35*wS/tS,3),
      " active40:", round(0.35*wE/wall(40)[0],3), round(0.35*wS/wall(40,B=BF_S)[0],3))
print("\n-- mu sensitivity (at-rest, 110, apron on)")
for mu in (0.25,0.30,0.35,0.45): print(mu, round(system(mu)[3],3))
print("-- active 40:", round(system(efp=40)[3],3), " 130 pcf:", round(system(pcf=130)[3],3),
      " apron off:", round(system(apron=False)[3],3))
print("-- CL backfill (IBC 1610.1 at-rest 100):", round(system(efp=100)[3],3))
# existing concrete the engine does not credit
corner = 2*12267.6                       # free body §12b net per corner x2
w1e1_conc = 2*10.443*(HS*GC + BF_SIDE*GC) # stem+footing only
w1e1_full = 2*10.443*wE
for mu in (0.25,0.35):
    for lab, x in (("corners", corner), ("corners+W1E1 concrete", corner+w1e1_conc),
                   ("corners+W1E1 w/ heel soil", corner+w1e1_full)):
        print(f"mu {mu} + {lab}: FS {system(mu, extraN=x)[3]:.3f}")
# shear key under FT-SG-S, IBC 1806.2 class 3 lateral bearing 200 psf/ft, depth from court floor
for dk in (1.5, 2.0):
    P = 100*((1+dk)**2 - 1)*25.0
    for mu in (0.25,0.35):
        print(f"key {dk}' under S (P={P:,.0f}) mu {mu}: FS {system(mu, extraF=P)[3]:.3f}")
# extra S heel per foot
for dh in (1,2):
    xN = dh*(HS*110+GC)*LS
    print(f"S heel +{dh}': FS {system(extraN=xN)[3]:.3f}  mu.25 {system(0.25, extraN=xN)[3]:.3f}")
print("\n-- blocked face drain: perched water hw above footing UNDERSIDE, bed drains (no uplift)")
def wet(hw, mu=0.35, gsat=125.0, pcf=110):
    K0 = 60/pcf
    def p_int(Hh):  # thrust over Hh height of virtual back, water hw above base
        dz=Hh/2000; tot=0
        for i in range(2000):
            z=(i+0.5)*dz          # height above base
            depth=Hh-z
            above = max(0, Hh-hw)  # thickness above water
            if z>=hw: sv = pcf*depth; u=0
            else: sv = pcf*above + gsat*(hw-z); u=62.4*(hw-z)
            tot += (K0*(sv-u)+u)*dz
        return tot
    th = p_int(H)+APRON
    sub = max(0, min(HS, hw-1.0))    # submerged soil height on heel
    def Wt(B): return T*HS*GC + B*GC + HEEL*((HS-sub)*pcf + sub*gsat)
    N = Wt(BF_SIDE)*(LE+LW) + Wt(BF_S)*LS
    return th, mu*N/(th*LS)
for hw in (0,2,4,6,8,10.12):
    th, f = wet(hw); print(f"hw {hw:5.2f}: thrust {th:7.0f} plf  FS {f:.3f}")
print("-- court flooded to footing top (bed full, equal water both sides): uplift on footings")
up = 62.4*(BF_SIDE*(LE+LW) + BF_S*LS)
print("FS", round(0.35*(N-up)/d,3))
print("\n-- staged backfill grid (note §13 method; apron excluded)")
def staged(fw, fs_, fe, extra_w1=0.0):
    def mem(f, B):
        th = 0.5*60*(H*f)**2
        W = T*HS*GC + B*GC + HEEL*max(0, H*f-1)*110
        return th, W
    tw, ww = mem(fw, BF_SIDE); ts, ws = mem(fs_, BF_S); te, we = mem(fe, BF_SIDE)
    rx = tw*LW - te*LE; ry = ts*LS
    R = math.hypot(rx, ry)
    if R == 0: return None
    return (0.35*(ww*LW+ws*LS+we*LE) + extra_w1)/R
for k in (3,4,6,12):
    for lab, ex in (("loop", 0), ("+W1/E1 note 2965.2", 2*10.443*2965.2*0.35),
                    ("+W1/E1 corrected 2418", 2*10.443*(HS*GC+BF_SIDE*GC)*0.35)):
        worst = min(v for a,b,c in itertools.product(range(13), repeat=3)
                    if max(a,b,c)-min(a,b,c) <= k
                    for v in [staged(a/12,b/12,c/12, ex)] if v is not None)
        print(f"rule <= {k}/12 H  {lab:24s} worst FS {worst:.3f}")
print("\n-- strut (W-SG-ARCH) reaction: engine pinned share vs continuous E2|E1 footing")
w1 = tE; L1 = LE
wE1 = (2/3)*0.5*60*HS**2     # braced E1 bottom reaction, at-rest on its stem (assumed same height)
L2 = 10.443
MB = (w1*L1**3 + wE1*L2**3)/(8*(L1+L2))
R_cont = w1*L1/2 + MB/L1 + wE1*L2/2 + MB/L2
R_simple = w1*L1/2 + wE1*L2/2
cap3 = 0.60*0.45*3000*144*(1-(216/(32*12))**2); cap5 = cap3*5/3
print(f"engine 0.5wL {0.5*w1*L1:,.0f}; simple both spans {R_simple:,.0f}; continuous {R_cont:,.0f}")
for R in (0.5*w1*L1, R_simple, R_cont):
    print(f"  Pu {1.6*R:,.0f}  d/c @3000 {1.6*R/cap3:.3f}  @5000 {1.6*R/cap5:.3f}")
print("\n-- FT-SG-E2 plan bending (deep beam 84in x 12in, span corner->ARCH)")
for share in (1.0, 0.75, 0.43):
    w = share*tE
    for lab, coef in (("simple wL2/8", 8), ("fixed-ish wL2/12", 12)):
        Mu = 1.6*w*L1**2/coef
        for z in (62.0,):
            Tu = Mu*12/z; As = Tu/(0.75*60000)
            print(f"share {share:.2f} {lab}: Mu {Mu:,.0f} ft-lb, Tu {Tu:,.0f} lb, As req {As:.2f} in2 (2 #4 near edge = 0.40)")
print("\n-- overturning / bearing E2 & S (verify sheet)")
for B, toe, lab in ((7.0, 3.0, "E2"), (8.3333, 4.3333, "S")):
    stem = HS*GC; ftg = B*GC; soil = HEEL*HS*110
    Mr = ftg*B/2 + stem*(toe+0.5) + soil*(B-HEEL/2)
    Mo = 0.5*60*H*H*H/3 + APRON*APRON_ARM
    W = stem+ftg+soil; e = B/2 - (Mr-Mo)/W; q = W/B*(1+6*e/B)
    print(lab, f"FSot {Mr/Mo:.3f} e {e:.3f} kern {B/6:.3f} qmax {q:.0f}")
print("\n-- stem: flexure and (ungraded) shear")
Ms = 60*HS**3/6 + 88.0; Mu = 1.6*Ms
As=0.372; d=12-3-0.3125; a=As*60000/(0.85*5000*12); phiMn=0.9*As*60000*(d-a/2)/12
c=a/0.80; et=0.003*(d-c)/c
Vu = 1.6*(0.5*60*HS**2 + 40); phiVc = 0.75*2*math.sqrt(5000)*12*d
print(f"Mu {Mu:,.0f} phiMn {phiMn:,.0f} d/c {Mu/phiMn:.3f} eps_t {et:.4f}; Vu(base,approx) {Vu:,.0f} phiVc {phiVc:,.0f} d/c {Vu/phiVc:.3f}")
print("\n-- study 'blocked-drain-wet' per-foot reproduction (inputs.py defaults, reference layout)")
# approximate: at-rest 60 on ordinary 5.786 + full direct to 9.12 for 'reference' (raised 3.333 against wall) + water 62.4 below 5 ft, buoyant everything
ordh=5.786458; raised=40/12; hw=5.0
dz=HS/2000; th=0; mo=0
import math as m
def strip(q,depth,near,width):
    if depth==0: return q if near==0 else 0
    a1=m.atan(near/depth); a2=m.atan((near+width)/depth); beta=a2-a1; alpha=m.pi/2-(a1+a2)/2
    return 2*q/m.pi*(beta-m.sin(beta)*m.cos(2*alpha))
for i in range(2000):
    z=(i+0.5)*dz
    direct = 60*max(ordh-z,0)
    if z>ordh: direct = 60*max(ordh+raised-z,0)
    sur = strip(120*raised, max(ordh-z,0), 0.0, 3.0)
    p = direct+sur+62.4*max(hw-z,0)
    th+=p*dz; mo+=p*dz*z
gc=150-62.4; gs=120-62.4
W = HS*gc + 7*gc + 3*ordh*gs + 3*raised*gs
print(f"study wet: thrust {th:,.0f} plf  W {W:,.0f}  sliding FS {0.35*W/th:.3f} -> ratio {1.5/(0.35*W/th):.2f}")
