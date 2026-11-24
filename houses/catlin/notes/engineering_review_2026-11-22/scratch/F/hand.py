import math
# thermal break: board thrusts at 3.5 psi cap
A={'TB-E1':8*84,'TB-W1':8*84,'STEM-E':1313.2,'STEM-W':1313.2,'BRKBM':17.75*216}
T={k:3.5*v for k,v in A.items()}; tot=sum(T.values()); print('thrust',T,tot)
net=tot-5161; print('slab edge',net, net/(3.5*432),'avg psi', net/(3.5*432)/33.33)
# house sliding
print('FS',(0.25*280144+1703.9*19)/27316)
# BEF near line, plain 25x15 in plan, Ec 57000 sqrt 5000
Ec=57000*math.sqrt(5000); I=15*25**3/12; k=3700*3.5/1.5
lam=(k/(4*Ec*I))**0.25; print('lam',lam,'1/lam',1/lam,'lamL',lam*432)
q=13419/216; a=108
y1=q/k*(1-math.exp(-lam*a)*math.cos(lam*a))
other=tot-13419-5161
x=108; y2=other*lam/(2*k)*math.exp(-lam*x)*(math.cos(lam*x)+math.sin(lam*x))
y=y1+y2; print('y',y1,y2,y,'psi',y*3700/1.5,'ratio',y*3700/1.5/33.33)
# compliant
print('closure',5.5e-6*30*323,'/0.125=',5.5e-6*30*323/0.125, 'remaining',0.125-5.5e-6*30*323)
# band header
L=63.3125/2+6; Lf=L/12
seat=15*121.605/12*Lf+50*Lf+2*50*0.44271*Lf+2*15*119.25/12*Lf
print('seat',seat, 'upper',seat-15*119.25/12*Lf-50*.44271*Lf)
for nm,P in [('with plies',1171.13),('rim only',seat)]:
  print(nm,'conc',P/3760,'plf',P/0.5/5400)
print('rim on plate',(seat+138.27)/(1.25*6)/425, 'plate on rim',seat/(1.25*6)/425)
print('rim header p6',47.88/792)
# sill seat added: 325.73 lb near each end, 5" in from RO edge
R=325.73; Ls=69.3125; a_=3+5  # seat centroid ~5in inside RO + 3in half seat
V=138.27+R*(Ls-a_)/Ls; print('shear w/ sill',V,V/7897,'plate brg',(1846.62+R)/21/425)
# veneer beam bedded eccentricity
Pb=268.86; Pc=221.9; e_b=(-7.8125)-(-12); e=Pb*e_b/(Pb+Pc); B=12
print('e',e,'B/6',B/6)
P=Pb+Pc; qmax=2*P/(3*((B/2-e)/12)); print('qmax psf',qmax)
# veneer geometry
print('brick-to-stud now',6.0+0.5,'needed shift',6.5-4.5)
