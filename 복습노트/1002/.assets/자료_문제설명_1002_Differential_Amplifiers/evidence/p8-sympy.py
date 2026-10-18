# p8 (2021-1 midterm Q3). V_T=25mV, beta=200, V_A=5V, ideal I1 / top sources / I_EE.
import sympy as sp
VT=sp.Rational(25,1000); beta=200; VA=5
def bjt(IC): gm=IC/VT; return gm, beta/gm, VA/IC
vin=sp.symbols('v_in'); vX,vo,it,vt=sp.symbols('v_X v_o i_t v_t')
ic=lambda g,r,b,c,e: g*(b-e)+(c-e)/r
ib=lambda rp,b,e: (b-e)/rp
# ---- (1) circuit (a): Q2 CE (1 mA), Q1 CB cascode (I1=0.5 mA), Q3 PNP current source (0.5 mA) at node X
g1,rp1,ro1=bjt(sp.Rational(1,2000)); g2,rp2,ro2=bjt(sp.Rational(1,1000)); g3,rp3,ro3=bjt(sp.Rational(1,2000))
# Q3: base Vb3, emitter VCC -> both AC gnd: just ro3 from X to gnd
def solve_a(vin_val, itest):
    eqX = sp.Eq(ic(g2,ro2,vin_val,vX,0) + vX/ro3 - (ic(g1,ro1,0,vo,vX)+ib(rp1,0,vX)), 0)
    eqO = sp.Eq(ic(g1,ro1,0,vo,vX) - itest, 0)      # test current itest injected into out node
    return sp.solve([eqX,eqO],[vX,vo],dict=True)[0]
Rout_a = sp.simplify(solve_a(0,1)[vo])
Av_a = sp.simplify(solve_a(1,0)[vo])
R = 1/(1/ro2+1/ro3+1/rp1)
print('(a) ro1,ro2,ro3,rpi1 =',ro1,ro2,ro3,rp1,' R=ro2||ro3||rpi1 =',sp.N(R))
print('(a) Rout exact =',sp.N(Rout_a,6),' approx g_m1 r_O1 R =',sp.N(g1*ro1*R,6))
print('(a) Av exact =',sp.N(Av_a,6),' approx -g_m2 * g_m1 r_O1 R =',sp.N(-g2*g1*ro1*R,6))
# ---- (2) circuit (b): half circuit, I_C=0.5 mA each, RP across C-E of Q3 (Q4)
RP=10000
gq,rpq,roq=bjt(sp.Rational(1,2000))
def solve_b(vin_val,itest):
    i3 = ic(gq,roq,0,vo,vX) + (vo-vX)/RP      # current into top of (Q3 || RP) from out
    eqX = sp.Eq(ic(gq,roq,vin_val,vX,0) - i3 - ib(rpq,0,vX), 0)
    eqO = sp.Eq(i3 - itest, 0)
    return sp.solve([eqX,eqO],[vX,vo],dict=True)[0]
Rh = sp.simplify(solve_b(0,1)[vo]); Ah = sp.simplify(solve_b(1,0)[vo])
Rb = 1/(1/roq+1/rpq); Rc = 1/(1/roq+sp.Rational(1,RP))
print('(b) ro=',roq,' rpi=',rpq,' ro3||RP=',sp.N(Rc),' ro1||rpi3=',sp.N(Rb))
print('(b) Rout per side exact =',sp.N(Rh,6),' approx g_m3(r_O3||R_P)(r_O1||r_pi3)=',sp.N(gq*Rc*Rb,6))
print('(b) Rout differential (out1-out2) exact =',sp.N(2*Rh,6),' approx =',sp.N(2*gq*Rc*Rb,6))
print('(b) A_d=(vo1-vo2)/(vi1-vi2) exact =',sp.N(Ah,6),' approx -g_m1*g_m3(r_O3||R_P)(r_O1||r_pi3) =',sp.N(-gq*gq*Rc*Rb,6))
