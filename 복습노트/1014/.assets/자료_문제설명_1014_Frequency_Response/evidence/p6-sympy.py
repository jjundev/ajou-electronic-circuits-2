import sympy as S
from math import log10,pi,sqrt

s,g,R,C,vi,x,y=(S.Symbol('s',real=True),S.Symbol('g',positive=True),S.Symbol('R',positive=True),S.Symbol('C',positive=True),S.Symbol('vi',real=True),S.Symbol('x',real=True),S.Symbol('y',real=True))
sol=S.solve([(1/R+s*C)*x+g*vi,(1/R+s*C)*y+g*x],[x,y]);H=S.factor(sol[y]/vi)
print('two-node cascade KCL H=',H);assert S.simplify(H-(g*R)**2/(1+s*R*C)**2)==0
print('atwp relative amplitude=.5,db=',20*log10(.5),'combined3dBratio=',sqrt(sqrt(2)-1));assert abs(1/(1+(sqrt(sqrt(2)-1))**2)-1/sqrt(2))<1e-12
