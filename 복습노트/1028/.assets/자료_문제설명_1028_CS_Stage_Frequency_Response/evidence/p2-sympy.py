from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
ratio=Rational(100,400)*(Rational(1000,65))**2
report('p2:main','exact','동일 이동도, 장채널 포화 모형에서 f_T ∝ V_OV/L²를 사용한다. 1 μm=1000 nm.',ratio=ratio,factor=N(ratio,8))
print(json.dumps(result,ensure_ascii=False,indent=2))
