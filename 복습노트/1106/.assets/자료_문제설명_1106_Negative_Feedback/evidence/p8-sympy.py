# p8 (P12.5) verify-B: closed-loop gains Y/X of Fig 12.80(a)-(d), solved by full KCL, checked vs A_OL/(1+T)
# T convention: T = -V_r/V_t (see p7). lambda=0.
import sympy as sp
A1,K,R1,R2,RD,gm3,gm1,gmb1,X=sp.symbols('A1 K R1 R2 R_D g_m3 g_m1 g_mb1 X',positive=True)
Y,n1,n2=sp.symbols('Y n1 n2')
out={}
# (a)
s=sp.solve([sp.Eq(Y,A1*(X-K*n1)),sp.Eq(n1,Y*R2/(R1+R2))],[Y,n1],dict=True)[0]; out['a']=sp.simplify(s[Y]/X)
T={'a':A1*K*R2/(R1+R2)}
# (b) X on - input, n2 on + input
s=sp.solve([sp.Eq(Y,A1*(n2-X)),sp.Eq(n1,Y*R2/(R1+R2)),sp.Eq(-n2/RD,gm3*n1)],[Y,n1,n2],dict=True)[0]; out['b']=sp.simplify(s[Y]/X)
T['b']=A1*gm3*RD*R2/(R1+R2)
# (c)
s=sp.solve([sp.Eq(Y,A1*(n1-X)),sp.Eq(-n1/RD,gm3*Y)],[Y,n1],dict=True)[0]; out['c']=sp.simplify(s[Y]/X)
T['c']=A1*gm3*RD
# (d) gate = n1 = A1(X-Y), source = Y
s=sp.solve([sp.Eq(n1,A1*(X-Y)),sp.Eq(gm1*(n1-Y)-gmb1*Y,Y/R2)],[Y,n1],dict=True)[0]
out['d_body']=sp.simplify(s[Y]/X); out['d']=sp.simplify(out['d_body'].subs(gmb1,0))
T['d']=A1*gm1*R2/(1+gm1*R2)
AOL={'a':A1,'b':-A1,'c':-A1,'d':A1*gm1*R2/(1+gm1*R2)}
for k in ['a','b','c','d']:
    chk=sp.simplify(out[k]-AOL[k]/(1+T[k]))
    print("Y/X(%s) ="%k,sp.factor(out[k]),"  check A_OL/(1+T) diff:",chk,"  A1->oo:",sp.limit(out[k],A1,sp.oo))
print("(d) with body effect:",sp.factor(out['d_body']))
