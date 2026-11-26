from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
s,g,rs,o1,o2,cg,cf,cd1,cf2,cd2=symbols('s g_m1 R_S r_o1 r_o2 C_GS1 C_GD1 C_DB1 C_GD2 C_DB2',positive=True)
r=1/(1/o1+1/o2); cd=cd1+cf2+cd2
b=rs*(cg+cf)+r*(cd+cf)+g*rs*r*cf
a=rs*r*(cg*cd+cg*cf+cd*cf)
assert simplify((1/b)*(b/a)-1/a)==0
report('p13:main','symbolic','상단 PMOS의 게이트와 소스가 AC 접지여서 g_m2 v_gs2=0이고 C_GD2+C_DB2가 출력 접지 용량으로 들어간다. R=r_o1∥r_o2, C_d=C_DB1+C_GD2+C_DB2. 분모 1+b1s+b2s²에서 충분히 분리된 두 극은 s_p1≈−1/b1, s_p2≈−b1/b2. 주파수(Hz)는 절댓값을 2π로 나눈다.',R=r,Cd=cd,b1=b,b2=a,p1=-1/b,p2=-b/a)
print(json.dumps(result,ensure_ascii=False,indent=2))
