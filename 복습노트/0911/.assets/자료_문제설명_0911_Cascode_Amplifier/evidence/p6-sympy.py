# E9.01 independent check: bipolar cascode, test source at Q1 collector
import sympy as sp
gm,rpi,ro1,ro2,vx,ve,ix=sp.symbols('g_m r_pi r_o1 r_o2 v_x v_e i_x',positive=True)
# node e (Q1 emitter): base AC ground, vbe=-ve
sol=sp.solve([sp.Eq(ix, gm*(-ve)+(vx-ve)/ro1), sp.Eq(ix, ve/ro2+ve/rpi)],[ix,ve],dict=True)[0]
Rout=sp.simplify(vx/sol[ix]); par=ro2*rpi/(ro2+rpi)
print("Rout - [(1+gm(ro2||rpi))ro1+(ro2||rpi)] =",sp.simplify(Rout-((1+gm*par)*ro1+par)))
VT=sp.Rational(26,1000); IC=sp.Rational(1,1000); beta=100; VA=5
g=IC/VT; vals={gm:g,rpi:beta/g,ro1:VA/IC,ro2:VA/IC}
print("gm =",float(g),"rpi =",float(beta/g),"ro =",VA/IC)
print("Rout exact =",float(Rout.subs(vals)),"ohm")
print("Rout approx gm ro1 (ro2||rpi) =",float((gm*ro1*par).subs(vals)),"ohm")
