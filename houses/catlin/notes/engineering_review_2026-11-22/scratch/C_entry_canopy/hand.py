import math
print("== drift check")
pg=50; g=min(0.13*pg+14,30); pf=0.7*1.0*1.2*1.0*pg
hd=0.43*36**(1/3)*(pg+10)**0.25-1.5; pd=hd*g; w=4*hd
print(f"gamma {g:.2f} pf {pf:.1f} hd {hd:.3f} pd {pd:.2f} w {w:.2f}")
ps,pn=47.1,16.3   # surcharge at canopy south/north edge (prefs)
L=6.0
avg=(ps+pn)/2; print("avg surcharge",avg, "design", pf+avg)
Rs=L*(2*ps+pn)/6; Ru=avg*L/2
trib=13.3333
print("south support surcharge share psf-ft",Rs,"vs uniform",Ru,"extra lb per post",trib*(Rs-Ru))
print("== truss reactions, per truss, on header (half span 13.333 ft)")
def p_at(y):  # y from canopy south edge
    return pf + ps-(ps-pn)*y/L
for name,y,wid in (("T1",37.333-37.219,1.114),("T2",39.333-37.219,2.0),("T3",41.333-37.219,1.974)):
    R=(p_at(y)+10)*wid*trib
    print(name, round(p_at(y),1), round(R), "fc_perp psi", round(R/(1.5*5.5),1))
Fcp=650*0.53
print("Fc-perp' Cb1.0",Fcp,"Cb1.25",Fcp*1.25, " engine 2492 lb ->", 2492/8.25, 2492/8.25/Fcp, 2492/8.25/(Fcp*1.25))
print("== N-S diaphragm chord (screen + east end strap = simple span)")
V=1034.57
for Lsp,d in ((24,6),(23.23,4.0),(23.23,5.95)):
    print(Lsp,d, round(V*Lsp/(8*d),1))
print("== uplift per truss heel (engine surrogate 16.832 psf, 0.6D 6 psf)")
for wid in (1.114,2.0,1.974):
    a=wid*trib; print(round(a,1),"sf net", round((16.832-6)*a,1))
print("== pad PD-BW-W (2.5x1.5x1.0), pier W")
D=1882.5; S=2948+205; Ldeck=199.6; pad=3.75*150; OT=1804.0
for lab,P in (("D+S+L",D+pad+S+Ldeck),("D+0.75(S+L)+0.75*0.6W",D+pad+0.75*(S+Ldeck)+0.75*OT)):
    print(lab, round(P), "gross psf", round(P/3.75), "net", round((P-110*3.75)/3.75))
print("== pier pullout PT-BW-GW (tension chord) 0.6D")
shaft=(6.333-1.349)*math.pi*(7/12)**2*150
padw=4*1*150
soil=(4-math.pi*(7/12)**2)*(6.333-2.833)*110
wall=157; post=60
R=0.6*(shaft+padw+soil+wall+post)
print("shaft",round(shaft),"pad",padw,"soil prism",round(soil),"0.6D resist",round(R))
for T in (1804.0, V*7.41/4.979):
    print("T",round(T),"d/c",round(T/R,2))
print("PT-BW-W:")
shaftw=(8.953-1.349)*math.pi*(7/12)**2*150; soilw=(3.75-math.pi*(7/12)**2)*(8.953-2.833)*110
Rw=0.6*(shaftw+562.5+soilw+157+60); print(round(Rw), round(1804/Rw,2))
print("== girt screw")
Kd=0.85
def Kh(h): return 2.01*(max(h,15)/1200)**(2/7)
for h in (25.64, 25.64+2.833, 25.64+9.12):
    q=0.00256*Kh(h)*Kd*115**2; p=0.6*q*(1.4+0.18); dem=p*32*24/144
    print(f"h {h:.2f} Kh {Kh(h):.3f} q {q:.2f} p_asd {p:.2f} demand {dem:.1f} pull-thru {dem/200:.3f}")
for f,lab in ((1.0,"tributary"),(1.25,"2-span girt"),(1.25*1.1,"2-span girt x panel 1.1")):
    print(lab, round(97.47*f,1), round(97.47*f/200,3))
