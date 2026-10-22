"""Blind independent X11.08; inherited circuit independently derived again."""
import sympy as sp
s=sp.symbols('s')
Rs,Rd,Ci,Cl,g,vin,w,wp=sp.symbols('RS RD Cin CL gm vin omega omega_p',positive=True)
vg,vo=sp.symbols('vg vo')
kg=sp.Eq((vg-vin)/Rs+s*Ci*vg,0);kd=sp.Eq(vo/Rd+s*Cl*vo+g*vg,0)
sol=sp.solve([kg,kd],[vg,vo]);H=sp.factor(sol[vo]/vin)
print('Inherited original Fig11.11: sourceground NMOS, inputRS+Cin atgate, outputRD+CL, lambda0, no reversecoupling. Own two-node KCL:',kg,kd)
print('Own derived H:',H)
H_eq=sp.factor(H.subs(Ci,Rd*Cl/Rs))
print('Equal pole condition RSCin=RDCL ->',H_eq)
M2=sp.simplify((H_eq.subs(s,sp.I*w)*sp.conjugate(H_eq.subs(s,sp.I*w)))/(g*Rd)**2)
M=1/(1+(w*Rd*Cl)**2)
assert sp.simplify(M2-M*M)==0
print('Normalized amplitude=1/[1+(omega/omega_p)^2], omega_p=1/(RDCL).')
u=sp.symbols('u',positive=True)
r=1/(1+u*u)
u3=sp.solve(sp.Eq(r,1/sp.sqrt(2)),u)[0]
u3=sp.sqrt(sp.sqrt(2)-1)
print('Conventional3dB/halfpower condition amplitude1/sqrt2, squared amplitude1/2.')
print('omega3dB / omega_p exact:',u3,'numeric:',sp.N(u3,16))
print('Positive root from1+u^2=sqrt2; discard negative frequency.')
print('Residual normalized amplitude vs1/sqrt2:',sp.simplify(r.subs(u,u3)-1/sp.sqrt(2)))
assert sp.simplify(r.subs(u,u3)-1/sp.sqrt(2))==0
print('Hz result f3dB=sqrt(sqrt2-1)*omega_p/(2pi)=sqrt(sqrt2-1)*fp.')
print('At common pole, normalized amplitude:',r.subs(u,1),'dB:',sp.N(20*sp.log(r.subs(u,1),10),16))
print('At halfpower root dB:',sp.N(20*sp.log(r.subs(u,u3),10),16))
print('Exactly3.000dB instead of conventional halfpower gives ratio:',sp.N(sp.sqrt(10**sp.Rational(3,20)-1),16))
print('Conventional3dB target is -3.0102999566dB; difference is normal corner-bandwidth convention.')
assert 0<u3<1
print('u->0 amplitude:',sp.limit(r,u,0),'u->infinity:',sp.limit(r,u,sp.oo))
print('BLIND SYMBOLIC HALFPOWER ROOT PASS')
