"""Blind independent KCL proof for P10.66 from conditions and Fig. 10.87 only.
I_C denotes Q3 collector/tail current, not a single input-branch current.
"""
import sympy as s
I,VT,VA,RC,vcm,vp,i=s.symbols('I_C V_T V_A R_C v_cm v_P i', positive=True)
gm=I/(2*VT) # Q1 or Q2 branch current = I_C/2
rss=VA/I # Q3 finite output resistance
# Each branch i = gm (v_cm - v_P); tail KCL 2i = v_P/rss.
sol=s.solve((s.Eq(i,gm*(vcm-vp)),s.Eq(2*i,vp/rss)),(i,vp), dict=True)[0]
Gm=s.factor(sol[i]/vcm)
Acm=s.factor(-RC*Gm) # each R_C load, signed single-ended output
threshold=s.factor(s.Rational(1,100)*2*(VA+VT))
print('gm_each =',gm)
print('tail_rss =',rss)
print('KCL_solution_i =',sol[i])
print('KCL_solution_vP =',sol[vp])
print('Gm_CM =',Gm)
print('Rout_CM = R_C, because Q1/Q2 VA=infinity')
print('A_CM_single_ended =',Acm)
print('abs(A_CM)<0.01 iff R_C*I_C <',threshold)
print('target_identity =',s.simplify((-Acm)*(2*(VA+VT))-RC*I))
print('large_tail_limit =',s.limit(Acm,VA,s.oo))

