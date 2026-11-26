from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
g=Rational(2,1000)/Rational(200,1000);r=1000;rs=200
ff=Rational(1,10**15);cg=50*ff;cf=10*ff;cd=15*ff
b=rs*(cg+cf)+r*(cd+cf)+g*rs*r*cf
a=rs*r*(cg*cd+cg*cf+cf*cd)
ti=rs*(cg+(1+g*r)*cf);to=r*(cd+(1+1/(g*r))*cf)
hz=lambda x:float(x/(2*pi*10**9))
M=sorted([hz(1/ti),hz(1/to)])
E=sorted([hz((b+k*sqrt(b**2-4*a))/(2*a)) for k in [-1,1]])
report('p12:a','symbolic','밀러 근사, λ나 ro 자료가 없어 ro≫RD. 낮은 쪽은 입력, 높은 쪽은 출력이다. 출력의 1/(gmRD)를 생략하면 출력 극점은 6.3662 GHz.',gm=g,omega_in=1/ti,omega_out=1/to,f_sorted_GHz=M)
report('p12:b','exact','정확한 2노드 KCL 분모에서 두 근을 계산한다. 두 고유 극점을 입력/출력 각각으로 분리하지 않는다.',b1_s=b,b2_s2=a,f_sorted_GHz=E)
report('p12:main','exact','밀러 근사는 정확한 저주파 극점을 높게, 고주파 극점을 낮게 평가한다.',miller_over_exact=[M[i]/E[i] for i in range(2)])
print(json.dumps(result,ensure_ascii=False,indent=2))
