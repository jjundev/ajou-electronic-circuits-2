# p5 (P10.62, Fig 10.42(a)): NMOS cascode diff pair, ideal current-source loads, ideal tail I_SS.
# Half circuit (P = virtual ground): M1 CS, M3 CG (gate AC gnd), load ideal -> Rout looking down into M3 drain.
import sympy as sp
gm, ro, vin, ID = sp.symbols('g_m r_o v_in I_D', positive=True)
vX, vo = sp.symbols('v_X v_o')
id_ = lambda g,d,s: gm*(g-s) + (d-s)/ro
# full differential circuit with symmetric +-vin/2 handled as half circuit: tail node is AC ground by symmetry
eqs = [sp.Eq(id_(0,vo,vX), 0),               # out node: ideal current source load
       sp.Eq(id_(vin,vX,0) - id_(0,vo,vX), 0)]  # node X between M1 drain and M3 source
s = sp.solve(eqs,[vX,vo],dict=True)[0]
A_half = sp.simplify(-s[vo]/vin)              # |v_o/v_in| per half; diff gain = same magnitude
print('|A_v| exact =', sp.factor(A_half))
print('check exact = g_m r_o (g_m r_o + 1):', sp.simplify(A_half - gm*ro*(gm*ro+1)))
print('limit A/(g_m^2 r_o^2), g_m r_o->oo :', sp.limit(A_half.subs(gm, sp.Symbol('x')/ro)/(sp.Symbol('x')**2), sp.Symbol('x'), sp.oo))
# numbers
mu = sp.Rational(100,10**6); WL = sp.Rational(20,1)/sp.Rational(18,100); lam = sp.Rational(1,10)
gmI = sp.sqrt(2*mu*WL*ID); roI = 1/(lam*ID)
x = sp.simplify(gmI*roI)
print('g_m r_o =', x)
ID_approx = sp.solve(sp.Eq(x**2, 300), ID)[0]
ID_exact = [r for r in sp.solve(sp.Eq(x*(x+1), 300), ID) if r.is_positive][0]
print('approx (A = g_m^2 r_o^2):  I_D =', sp.N(ID_approx,6), ' I_SS =', sp.N(2*ID_approx,6), 'A')
print('exact  (A = g_m r_o(g_m r_o+1)): I_D =', sp.N(ID_exact,6), ' I_SS =', sp.N(2*ID_exact,6), 'A')
print('g_m r_o at approx solution =', sp.N(x.subs(ID,ID_approx),5))
print('ratio exact/approx I_SS =', sp.N(ID_exact/ID_approx,5))
