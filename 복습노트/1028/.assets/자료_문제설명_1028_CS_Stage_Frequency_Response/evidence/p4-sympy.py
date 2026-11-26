from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
W,L,V=symbols('W L V',positive=True)
Id=lambda w,v:w*v**2/L
gm=lambda w,v:w*v/L
C=lambda w:w*L
for tag,w in [('a',4*W),('b',W)]:
 vals=dict(width=simplify(w/W),current=simplify(Id(w,V/2)/Id(W,V)),gm=simplify(gm(w,V/2)/gm(W,V)),Cgs=simplify(C(w)/C(W)),fT=simplify((gm(w,V/2)/C(w))/(gm(W,V)/C(W))))
 report('p4:'+tag,'symbolic','각 값은 변경 후/전 비율. f_T는 두 조건 모두 절반.',**vals)
report('p4:main','symbolic','(a) 전류 고정이면 W는 네 배, gm은 두 배, Cgs는 네 배. (b) 폭 고정이면 I_D는 1/4, gm은 절반, Cgs는 동일. 두 경우 f_T는 절반.')
print(json.dumps(result,ensure_ascii=False,indent=2))
