import math
def depth(P,h,b,lb=150.0,cap=None):
    d=2.0
    for _ in range(200):
        S1=lb*d/3.0
        if cap: S1=min(S1,cap)
        A=2.34*P/(S1*b)
        dn=0.5*A*(1+math.sqrt(1+4.36*h/A))
        d=0.5*d+0.5*dn
    return d
for name,b in (("shaft 14in",14/12),("PE beff",1.268),("PNE beff",1.451)):
    print(name, round(depth(81.9,1.932,b),3))
# alternative: whole pier moment about grade if base pinned: P at h
# post+pier drag check
q=16.661
post=q*5.5/12*6.1771; print("post drag",post, post/2)
pier=q*14/12*3.0; print("pier drag",pier)
V=post/2+pier; print("V",V)
h=(post/2*3.0+pier*1.5)/V; print("h above grade",h)
print("--- W/GW piers under screen chord base, P=1034.6 at 1.55' (+pack) above grade")
for b in (14/12,):
    for h in (1.55,1.6):
        print(h, round(depth(1034.6,h,b),3), "doubled S1:", round(depth(1034.6,h,b,lb=300),3))
Mu=1034.6/0.6*1.6; print("Mu strength at grade lb-ft",Mu)
