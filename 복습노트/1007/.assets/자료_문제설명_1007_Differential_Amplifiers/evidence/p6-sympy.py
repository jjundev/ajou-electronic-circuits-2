import sympy as s
import json

g,g3,r3,r4,R,d=s.symbols('gm1 gm3 ro3 ro4 Rd DeltaRd',positive=True)
for name,T in [('single',r3),('cascode',r3+r4+g3*r3*r4)]:
 C=s.factor(g*R/(d/(1/g+2*T)));print(name,'Rtail=',T,'CMRR=',C,'numeric=',C.subs({g:.001,g3:.002,r3:100000,r4:100000,R:10000,d:100}))
print('dominant improvement=',g3*r4)

# Final comparison: original has no small-mismatch assumption; retain mean load.
vid=s.symbols("vid")
v1=-g*R*vid/2
v2=g*(R+d)*vid/2
Adm=s.factor((v1-v2)/vid)
assert s.simplify(Adm+g*(R+d/2))==0
print("finite mismatch Adm=",Adm,"CMRR dominant mean-load=",s.factor(-Adm*2*r3/d))
