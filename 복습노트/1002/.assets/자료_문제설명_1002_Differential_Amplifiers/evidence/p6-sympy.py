# p6 (P10.64, Fig 10.43(a)): NMOS telescopic cascode with PMOS cascode current-source load M5/M7 (M6/M8).
# Half circuit, all gates AC gnd except M1. I_D = I_SS/2 = 0.5 mA. All W/L equal.
import sympy as sp
WL = sp.symbols('WL', positive=True)
vin = sp.symbols('v_in')
vX, vo, vY = sp.symbols('v_X v_o v_Y')
ID = sp.Rational(1,2000)
gn = sp.sqrt(2*sp.Rational(100,10**6)*WL*ID); rn = 1/(sp.Rational(1,10)*ID)
gp = sp.sqrt(2*sp.Rational(50,10**6)*WL*ID);  rp = 1/(sp.Rational(2,10)*ID)
idf = lambda g_,r_,G,D,S: g_*(G-S) + (D-S)/r_   # current into drain (same linear model for PMOS)
eqs = [
  sp.Eq(idf(gn,rn,vin,vX,0) - idf(gn,rn,0,vo,vX), 0),   # node X: M1 drain / M3 source
  sp.Eq(idf(gn,rn,0,vo,vX) + idf(gp,rp,0,vo,vY), 0),    # node out: M3 drain + M5 drain (leaving node)
  sp.Eq(idf(gp,rp,0,vo,vY) - idf(gp,rp,0,vY,0), 0),     # node Y: M5 source / M7 drain (M7 source = VDD = 0)
]
s = sp.solve(eqs,[vX,vo,vY],dict=True)[0]
A_exact = sp.simplify(-s[vo]/vin)
Rn = gn*rn*rn; Rp = gp*rp*rp
A_approx = gn*(Rn*Rp/(Rn+Rp))
print('A_approx(WL) = g_m1[(g_m3 r_o3 r_o1)||(g_m5 r_o5 r_o7)] =', sp.nsimplify(sp.simplify(A_approx)), '=', sp.N(sp.simplify(A_approx/WL),6),'* WL')
wa = sp.solve(sp.Eq(A_approx,200),WL)
print('approx  W/L =', [sp.N(w,6) for w in wa])
we = sp.nsolve(A_exact-200, WL, 30)
print('exact (full KCL) W/L =', sp.N(we,6))
print('exact A at approx W/L =', sp.N(A_exact.subs(WL,wa[0]),6))
print('g_m r_o (n,p) at approx W/L:', sp.N((gn*rn).subs(WL,wa[0]),4), sp.N((gp*rp).subs(WL,wa[0]),4))
print('limit A_exact/A_approx as W/L -> oo (g_m r_o >> 1):', sp.radsimp(sp.limit(sp.simplify(A_exact/A_approx), WL, sp.oo)))
