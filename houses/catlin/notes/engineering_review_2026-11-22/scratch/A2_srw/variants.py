import math, importlib.util, sys
spec = importlib.util.spec_from_file_location("s", "srw_check.py")
D=math.radians
# terrace below 12" topsoil = rock 36; topsoil + court-face beyond = native phi
def P_rock_top_native(h,g,phin,om,delta,t,phir,top_soil=1.0):
    lean=math.tan(D(om)); best=(0,0)
    rho=1.0
    while rho<89:
        r=D(rho); area=0.5*h*h*(1/math.tan(r)-lean)
        z1=min(t*math.tan(r)/(1-math.tan(r)*lean),h)   # rock along plane from heel up to z1
        z1=min(z1,h-top_soil)
        s=z1/h
        tp=s*math.tan(D(phir))+(1-s)*math.tan(D(phin)); pe=math.atan(tp)
        if r>pe and area>0:
            tilt=D(delta-om); P=g*area*math.sin(r-pe)/math.cos(r-pe-tilt)
            if P>best[0]: best=(P,rho)
        rho+=0.01
    return best
for g in (110,130):
    ka=40/g; phin=math.degrees(math.asin((1-ka)/(1+ka))); d=2/3*phin
    for t in (1.0,2.0,2.97):
        P,rho=P_rock_top_native(4.0,g,phin,12,d,t,36.0)
        tilt=D(d-12); Ph,Pv=P*math.cos(tilt),P*math.sin(tilt); N=130*.97*4+Pv
        mu=math.tan(D(min(36,phin)))
        lean=math.tan(D(12)); Mo=Ph*4/3; Mr=130*.97*4*(.485+2*lean)+Pv*(.97+4/3*lean)
        print(f"g{g} rock {t}ft (top 12in topsoil native): P {P:.1f} FSs {mu*N/Ph:.3f} FSo {Mr/Mo:.3f}")
