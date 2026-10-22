"""Blind independent calculation for P10.64 from conditions and Fig. 10.43(a) only.
Units: mA, V, mS, kOhm. This script is reviewer evidence, not student content.
"""
import sympy as s
w=s.symbols('w', positive=True)
I=s.Rational(1,2) # branch current, mA
mun=s.Rational(1,10) # 100 uA/V^2 = .1 mA/V^2
mup=s.Rational(1,20) # 50 uA/V^2 = .05 mA/V^2
lamn=s.Rational(1,10); lamp=s.Rational(1,5)
gn=s.sqrt(2*mun*w*I) # mS
gp=s.sqrt(2*mup*w*I)
ron=1/(lamn*I); rop=1/(lamp*I) # kOhm
# Fig: M1/M3 bottom NMOS cascode; M7/M5 PMOS top cascode.
Rn=gn*ron*ron
Rp=gp*rop*rop
Rout=s.factor(Rn*Rp/(Rn+Rp))
Gm=gn
A=s.factor(Gm*Rout)
sol=s.solve(s.Eq(A,200),w)[0]
print('I_each_mA =',I)
print('gm_n_mS =',gn,'gm_p_mS =',gp)
print('ro_n_kOhm =',ron,'ro_p_kOhm =',rop)
print('R_bottom_kOhm =',Rn,'R_top_kOhm =',Rp)
print('R_parallel_kOhm =',Rout)
print('gain_magnitude =',A)
print('common_W_over_L_exact =',s.simplify(sol))
print('common_W_over_L_decimal =',s.N(sol,12))
print('gain_at_solution =',s.simplify(A.subs(w,sol)))
print('gm_n_ro_n =',s.N((gn*ron).subs(w,sol),8),'gm_p_ro_p =',s.N((gp*rop).subs(w,sol),8))
# Internal-only full two-MOS low-frequency small-signal check: show dominant-order limit, not a student answer.
Rne=ron+ron+gn*ron*ron
Rpe=rop+rop+gp*rop*rop
Gme=gn*(gn+1/ron)/(gn+2/ron)
Ae=s.factor(Gme*Rne*Rpe/(Rne+Rpe))
print('leading_term_limit_ratio =',s.limit(Ae/A,w,s.oo))
print('full_model_at_leading_solution_internal =',s.N(Ae.subs(w,sol),10))
