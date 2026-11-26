from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
s,g,r,rs,cg,cf,cd=symbols('s g R R_S C_g C_f C_d',nonzero=True)
v,x,vi=symbols('v_g v_o v_i')
eq1=(v-vi)/rs+s*cg*v+s*cf*(v-x)
eq2=x/r+s*cd*x+s*cf*(x-v)+g*v
sol=solve([eq1,eq2],[v,x]);h=factor(sol[x]/vi)
b1=rs*(cg+cf)+r*(cd+cf)+g*r*rs*cf
b2=rs*r*(cg*cd+cg*cf+cf*cd)
assert simplify(h-r*(s*cf-g)/(1+b1*s+b2*s**2))==0
report('p10:main','symbolic','두 노드 KCL을 연립. g=g_m1+g_m2, R=r_o1∥r_o2, C_g=C_GS1+C_GS2, C_f=C_GD1+C_GD2, C_d=C_DB1+C_DB2이다. 전달함수 H=R(s C_f−g)/(1+b1 s+b2 s²). 영점은 +g/C_f로 우반평면이다.',b1=b1,b2=b2,H=h)
print(json.dumps(result,ensure_ascii=False,indent=2))
