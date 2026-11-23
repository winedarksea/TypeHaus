# Standalone: balcony glulam BM-SG-BLE under D+L (as graded) and D+S with ASCE 7-16 7.7 leeward drift.
import numpy as np
ys, yf, yr, yn = -10.5, -9.8333, -2.5, -0.8333   # south end, front brg, rear brg, north end (ft)
face = -0.5625                                    # house cladding face, y (ft)
trib = 9.75
b, d = 3.5, 11.875
S = b*d*d/6; A = b*d
y = np.linspace(ys, yn, 20001); dy = y[1]-y[0]
def drift(yv, pd=50.3, w=9.8):
    dist = face - yv
    return np.where(dist < w, pd*(1-dist/w), 0.0)
def reactions(q):           # q plf along y; two supports
    F = q.sum()*dy; Mf = (q*(y-yf)).sum()*dy
    Rr = Mf/(yr-yf); Rf = F-Rr; return Rf, Rr
def moments(q):
    Rf, Rr = reactions(q)
    M = np.array([ -(q[:j]*(y[j]-y[:j])).sum()*dy + (Rf*(y[j]-yf) if y[j]>yf else 0) + (Rr*(y[j]-yr) if y[j]>yr else 0) for j in range(0,len(y),200) ])
    return M
def run(name, qpsf, CD, Lb=3.0, Cb=1.0):
    q = trib*qpsf
    Rf, Rr = reactions(q); M = moments(q)
    fc = max(Rf,Rr)/(b*Lb); cap = 740*0.53*Cb
    fb = abs(M).max()*12/S; Fb = 2400*0.8*CD
    print(f"{name:42s} Rf {Rf:6.0f} Rr {Rr:6.0f}  bearing {fc:5.0f}/{cap:5.0f}={fc/cap:4.2f}  bending {fb:5.0f}/{Fb:5.0f}={fb/Fb:4.2f}")
    return Rf, Rr
one = np.ones_like(y)
run("D+L 50 psf (record, Lb 3in)", 50*one, 1.0)
# live on span+north overhang only (pattern)
qpat = 10*one + 40*((y>=yf).astype(float))
run("D+L pattern, live off south overhang", qpat, 1.0)
for bal in (35.0, 42.0):
    q = 10 + bal + drift(y)
    run(f"D+S bal {bal:.0f} + drift (Lb 3in)", q, 1.15)
    run(f"D+S bal {bal:.0f} + drift (Lb 3.5in, Cb 1.107)", q, 1.15, 3.5, (3.5+0.375)/3.5)
# average snow over deck
dd = np.linspace(face-(-0.8333), face-(-10.5), 1000)
print("avg drift on deck psf", (50.3*np.clip(1-dd/9.8,0,None)).mean())
# column axial (equal split vs statics), factored 1.2D+1.6L
D = 10*trib; L = 40*trib
Rf_D, Rr_D = reactions(D*one); Rf_L, Rr_L = reactions(L*((y>=yf).astype(float)))
print("rear col: 1.2D+1.6L statics", 1.2*Rr_D+1.6*Rr_L, " equal split", 1.2*471+1.6*1885)
Rf_Lp, _ = reactions(L*((y<=yr).astype(float)))
print("front col: D only reaction", Rf_D, " equal-split D", 471, "; front L max", Rf_Lp)
