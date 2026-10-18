# P10.75 independent check: active-load bipolar pair, Av = gm1 (rO2||rO4) = 100, VA,n = 5 V
from sympy import *
IC, VT, VAn, VAp = symbols('I_C V_T V_An V_Ap', positive=True)
vin, vout = symbols('v_in v_out')
gm = IC/VT; rO2 = VAn/IC; rO4 = VAp/IC
# short-circuit Gm of mirror-loaded pair = gm (Razavi), Rout = rO2||rO4
Av = simplify(gm*rO2*rO4/(rO2+rO4))
print('Av = gm (rO2||rO4) =', Av, ' (I_C cancels)')
sol = solve(Eq(Av, 100), VAp)[0]
print('V_A,p =', simplify(sol))
for vt in (Rational(26, 1000), Rational(25, 1000)):
    print('VT = %s V: V_A,p =' % vt, N(sol.subs({VAn: 5, VT: vt})), 'V')
gmx,gn,gp,vd,vx_,vo_,ve_ = symbols('g_m g_n g_p v_d v_x v_o v_e')
s=solve([Eq((gmx+gp)*vx_+gn*(vx_-ve_)+gmx*(vd/2-ve_),0),
         Eq(gp*vo_+gn*(vo_-ve_)+gmx*(-vd/2-ve_)+gmx*vx_,0),
         Eq(gn*(2*ve_-vx_-vo_)+2*gmx*ve_,0)],[vx_,vo_,ve_],dict=True)[0]
Ae=simplify(s[vo_]/vd)
print('full KCL (finite rO all, base current neglected): |A| =',Ae)
print('  minus gm(2gm+gp)/(2(gm+gp)(gn+gp)):',simplify(Ae-gmx*(2*gmx+gp)/(2*(gmx+gp)*(gn+gp))))
vt=Rational(26,1000); Ic=1; vap=N(sol.subs({VAn:5,VT:vt}))
num={gmx:Ic/vt,gn:Ic/5,gp:Ic/vap}
print('  at VT=26mV, VAp=%.4f: |A_exact| = %.4f  (correction %.3f%%)'%(vap,N(Ae.subs(num)),100*(N(Ae.subs(num))/100-1)))
