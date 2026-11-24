# Independent P-M point for a 12" round, (4) #5 on r=3.3125", f'c 5000, fy 60000 (ACI 318-19).
import math
D=12.0; R=6.0; fc=5000; fy=60000; Es=29e6; Ab=0.31; rb=3.3125
b1=0.85-0.05*(fc-4000)/1000
def seg_area_centroid(a):  # circular segment of depth a from top: area, centroid dist from centre
    a=min(max(a,0),D); h=a; th=2*math.acos((R-h)/R)
    A=R*R*(th-math.sin(th))/2
    if A<=0: return 0,0
    yb=4*R*math.sin(th/2)**3/(3*(th-math.sin(th)))
    return A,yb
def point(c, angles):
    a=b1*c; A,yb=seg_area_centroid(a); Cc=0.85*fc*A; P=Cc; M=Cc*yb
    et_max=0
    for t in angles:
        y=rb*math.cos(t)              # +y toward compression face
        d=R-y; eps=0.003*(c-d)/c
        fs=max(-fy,min(fy,Es*eps))
        if d< a: fs-=0.85*fc          # displaced concrete
        P+=fs*Ab; M+=fs*Ab*y
        et_max=max(et_max,-eps)
    ety=fy/Es
    phi=0.65 if et_max<=ety else (0.9 if et_max>=ety+0.003 else 0.65+0.25*(et_max-ety)/0.003)
    return P,M,phi
for name,ang in (("bar on axis",[0,math.pi/2,math.pi,1.5*math.pi]),("45 deg",[math.pi/4+k*math.pi/2 for k in range(4)])):
    for Pu in (1795,3680,4811):
        lo,hi=0.5,12
        for _ in range(80):
            c=(lo+hi)/2; P,M,phi=point(c,ang)
            if phi*P>Pu: hi=c
            else: lo=c
        P,M,phi=point(c,ang); print(f"{name:12s} Pu {Pu}: c {c:.2f} phi {phi:.2f} phiMn {phi*M/12:,.0f} lb-ft")
