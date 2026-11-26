from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
s,g,rs,rp,rg,r,cg,cf,cd=symbols('s g_m R_S r_pi R_i R C_pi C_mu C_CS',positive=True)
v,x,vi=symbols('v_b v_o v_i')
# R_i=R_S||r_pi and eta=R_i/R_S. An ideal current-source load is open in AC.
M=Matrix([[1/rg+s*(cg+cf),-s*cf],[g-s*cf,s*(cd+cf)]])
den=expand(M.det()*rg)
B=cd+cf+g*rg*cf;A=rg*(cg*cd+cg*cf+cd*cf)
assert simplify(den-(s*B+s*s*A))==0
h=(rg/rs)*(s*cf-g)/den
m1=1/(rg*(cg+(1+g*r)*cf));m2=1/(r*(cd+(1+1/(g*r))*cf))
assert limit(m1,r,oo)==0 and limit(m2,r,oo)==0
report('p14:a','proof','이상적 전류원 부하와 V_A=∞로 출력의 DC 도전율은 0이다. 유한한 주파수 독립 DC 이득이 없어 통상의 상수 이득 밀러 근사는 적용 불가. 시험 저항 R을 출력에 병렬로 둔 뒤 R→∞로 보내면 두 개의 밀러 노드 극점이 모두 0으로 가므로 유한한 두 번째 극점을 재현하지 못한다.',omega_in_limit=limit(m1,r,oo),omega_out_limit=limit(m2,r,oo))
report('p14:b','exact','Ri=RS∥rπ, η=Ri/RS. C_CS가 모델에 없으면 0으로 둔다. H=η(s Cμ−gm)/(s B+s² A). 정확한 극점은 원점 한 개와 유한한 음의 실수 한 개. β를 무시할 때 Ri=RS.',B=B,A=A,p1=0,p2=-B/A,H=h)
report('p14:main','exact','밀러 근사는 출력 DC 이득의 발산 때문에 한계가 있다. 정확한 전달함수는 p1=0과 p2=−(C_CS+Cμ+gm Ri Cμ)/[Ri(Cπ C_CS+Cπ Cμ+Cμ C_CS)]. C_CS=0이면 p2=−(1+gm Ri)/(Ri Cπ).')
print(json.dumps(result,ensure_ascii=False,indent=2))
