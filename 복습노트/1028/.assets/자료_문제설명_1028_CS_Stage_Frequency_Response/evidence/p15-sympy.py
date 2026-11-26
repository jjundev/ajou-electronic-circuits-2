from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
r,ri,g,cg,cf,cd=symbols('R R_i g_m C_pi C_mu C_CS',positive=True)
B=cd+cf+g*ri*cf; A=ri*(cg*cd+cg*cf+cd*cf)
b=ri*(cg+cf)+r*B; a=r*A
pole1=limit(-1/b,r,oo);pole2=simplify(limit(-b/a,r,oo))
assert simplify(pole2+B/A)==0
report('p15:main','proof','Ri=RS∥rπ. 출력에 임시 저항 R을 두고 분모 1+b1s+b2s²의 주극점 근사 −1/b1, −b1/b2를 구한 다음 R→∞로 보낸다. 첫 극점은 원점이고 둘째는 유한하다. 두 극이 무한히 분리되는 이상적 극한에서 결과는 p14의 정확한 두 극과 일치한다. C_CS를 생략하면 p2=−(1+gm Ri)/(Ri Cπ).',b1=b,b2=a,p1=pole1,p2=pole2)
print(json.dumps(result,ensure_ascii=False,indent=2))
