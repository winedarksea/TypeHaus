import math
D=math.radians
def wedge_q(h,g,phin,om,delta,t,phir,q,strip):
    lean=math.tan(D(om)); best=(0,0); rho=1.0
    while rho<89:
        r=D(rho); width=h*(1/math.tan(r)-lean); area=0.5*h*width
        z1=min(t*math.tan(r)/(1-math.tan(r)*lean),h); s=z1/h
        pe=math.atan(s*math.tan(D(phir))+(1-s)*math.tan(D(phin)))
        W=g*area+q*min(width,strip)
        if r>pe and area>0:
            tilt=D(delta-om); P=W*math.sin(r-pe)/math.cos(r-pe-tilt)
            if P>best[0]: best=(P,rho)
        rho+=0.01
    return best
for g in (110,130):
    ka=40/g; phin=math.degrees(math.asin((1-ka)/(1+ka))); d=2/3*phin
    for q in (0,50):
        for t in (1.0,2.0):
            P,rho=wedge_q(4,g,phin,12,d,t,36,q,2.97-4*math.tan(D(12)))
            tilt=D(d-12);Ph,Pv=P*math.cos(tilt),P*math.sin(tilt)
            print(f"g{g} q{q} rock{t}: P {P:.1f} FSs {math.tan(D(min(36,phin)))*(504.4+Pv)/Ph:.3f}")
