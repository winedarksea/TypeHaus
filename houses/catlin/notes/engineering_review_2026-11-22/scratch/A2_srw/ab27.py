import math
D=math.radians
exec(open('srw_check.py').read().split('def body')[0])
for g in (110,120,130):
    phi=27.0; d=2/3*phi
    for t,lab in ((1.0,'12in rock'),(0.0,'no rock'),(2.0,'24in rock')):
        P,rho,sh,pe=wedge(4.0,g,phi,12,d,t,36.0) if t else wedge(4.0,g,phi,12,d)
        tilt=D(d-12);Ph,Pv=P*math.cos(tilt),P*math.sin(tilt);N=130*.97*4+Pv
        print(f"phi27 g{g} {lab}: P {P:.1f} FSs {math.tan(D(27))*N/Ph:.3f}")
