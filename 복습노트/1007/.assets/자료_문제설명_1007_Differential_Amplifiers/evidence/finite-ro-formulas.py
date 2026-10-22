from independent_circuits import *
gm,ro,rt,rd,dr,rp=s.symbols('gm ro rt RD dR rpi',positive=True)
a,b,t=s.symbols('a b p')
q=s.solve([a/rd+(a-t)/ro+gm*(1-t),b/rd+(b-t)/ro+gm*(1-t),t/rt+(2*t-a-b)/ro-2*gm*(1-t)+2*(t-1)/rp],[a,b,t])
cm=s.factor(q[a]);coeff=s.factor(-cm/(rd*(1+rd/ro)))
print('Symmetric finite-BJT CM=',cm)
print('First-order A_CM_DM for right RD+dR = dR *',coeff)
print('DM symmetric=',-gm*rd/(1+rd/ro))
print('first-order CMRR=',s.factor((gm*rd/(1+rd/ro))/(dr*coeff)))
# MOS limit rpi->oo.
print('MOS CM=',s.factor(s.limit(cm,rp,s.oo)))
print('MOS first-order leakage=',s.factor(s.limit(coeff,rp,s.oo))*dr)
print('MOS first-order CMRR=',s.factor(s.limit((gm*rd/(1+rd/ro))/(dr*coeff),rp,s.oo)))
vt=.026;beta=100.;alpha=beta/(beta+1);ie1=.002;ic1=alpha*ie1;ic2=alpha*ic1;ici=alpha*ic2/2;g2=ic2/vt;g=ici/vt;ro1=10/ic1;ro2=10/ic2;rx=1/(1/ro1+g2/beta);rss=ro2+(1+g2*ro2)*rx
print('BJT symmetric complete=',pair(g,10/ici,rss,10000.,10000.,beta/g))
for g,ri,rtail,RD,dR in [(.001,100000.,50000.,10000.,100.),(.0005,200000.,110000.,10000.,10.)]:
 vals={gm:g,ro:ri,rt:rtail,rd:RD,dr:dR,rp:s.oo};print('MOS finite-ro firstorder',float(s.limit(cm,rp,s.oo).subs(vals)),float(s.limit(coeff,rp,s.oo).subs(vals)*dR))
