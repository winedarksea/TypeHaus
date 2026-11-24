exec(open('court_sliding.py').read().split('print("\\n-- blocked')[0].split('d, N, F, fs = system()')[0])
import math
corner=2*12267.6; w1e1=2*10.443*(9.1198*150+7*150)
def wet(hw, extra, gsat=125.0, pcf=110, mu=0.35):
    K0=60/pcf; Hh=H; dz=Hh/2000; tot=0
    for i in range(2000):
        z=(i+0.5)*dz; depth=Hh-z; above=max(0,Hh-hw)
        if z>=hw: sv=pcf*depth; u=0
        else: sv=pcf*above+gsat*(hw-z); u=62.4*(hw-z)
        tot+=(K0*(sv-u)+u)*dz
    th=tot+APRON; sub=max(0,min(HS,hw-1))
    Wt=lambda B: HS*150+B*150+3*((HS-sub)*pcf+sub*gsat)
    N=Wt(7)*(LE+LW)+Wt(8.3333)*LS+extra
    return mu*N/(th*LS)
for hw in (4,6,8,10.12):
    print(hw, round(wet(hw,0),3), round(wet(hw,corner+w1e1),3), round(wet(hw,corner+w1e1,mu=0.25),3))
