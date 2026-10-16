import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
gm,r1,re,vt,ve,it,g2,vi=s.symbols('gm r1 re vt ve it g2 vi',positive=True)
# upper CB collector current= (vt-ve)/r1-gm*ve; emitter KCL=ve/re+(ve-vt)/r1+gm*ve+g2*vi=0
sol=s.solve([s.Eq(it,(vt-ve)/r1-gm*ve),s.Eq(ve/re+(ve-vt)/r1+gm*ve+g2*vi,0)],[vt,ve]);rr=s.simplify(sol[vt].subs(vi,0)/it);av=s.simplify(sol[vt].subs(it,0)/vi);print('Rout',rr,'Av',av)
vals={gm:s.Rational(2,100),r1:10000,re:s.Rational(10000,3),g2:s.Rational(4,100)};print('exact',rr.subs(vals),av.subs(vals));print('dominant', (gm*r1*re).subs(vals),(-g2*gm*r1*re).subs(vals));print('part1 current .5mA gm .02 ro1=ro2=10k Av=-50')
print("Independent conclusion: (1)Ic1=.5mA Av=-50; (2)Re=ro2||ro3=3333ohm,Rout approx666667ohm,Av approx-26667; exact Rout676667 Av-26800 without base-current loading")

# Post-reference adjudication: 'neglect base currents' applies to DC mirrors; beta=200 implies rpi1=beta/gm1 in AC model.
rpi=s.symbols('rpi',positive=True)
rload=1/(1/re+1/rpi)
rrbeta=s.simplify(rr.subs(re,rload));avbeta=s.simplify(av.subs(re,rload))
print('finite-beta Rout exact',rrbeta,'Av exact',avbeta)
vals[rpi]=10000
print('finite-beta exact',rrbeta.subs(vals),avbeta.subs(vals))
print('finite-beta dominant',(gm*r1*rload).subs(vals),(-g2*gm*r1*rload).subs(vals))
print('gmro scaled limit exact/dominant',s.limit(rrbeta/(gm*r1*rload),gm,s.oo))
print('part1 corrected arithmetic: .02*(10000||10000)=-100')
assert (gm*r1*rload).subs(vals)==500000
assert (-g2*gm*r1*rload).subs(vals)==-20000
