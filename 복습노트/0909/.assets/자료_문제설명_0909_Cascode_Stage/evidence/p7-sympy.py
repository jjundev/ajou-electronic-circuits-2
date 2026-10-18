# Independent check P9.18 (Fig 9.53): widths x N, L and I fixed, lambda ~ 1/L
import sympy as sp
N,k,W,L,I,c=sp.symbols('N k W L I c',positive=True)
gm=lambda w: sp.sqrt(2*k*(w/L)*I); ro=1/((c/L)*I)   # lambda=c/L unchanged
R=lambda w: gm(w)*ro*ro
print('ro after/before =',sp.simplify(ro/ro),' gm ratio =',sp.simplify(gm(N*W)/gm(W)))
print('approx Rout ratio (Eq.9.23) =',sp.simplify(R(N*W)/R(W)))
Re=lambda w:(1+gm(w)*ro)*ro+ro
x=sp.Symbol('x',positive=True)
ratio=sp.simplify(Re(N*W)/Re(W)); print('exact ratio =',ratio)
print('exact ratio with gm ro=x, x->oo:',sp.limit(((1+sp.sqrt(N)*x)+1)/((1+x)+1),x,sp.oo))
