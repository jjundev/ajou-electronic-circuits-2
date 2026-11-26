from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
W,L,V=symbols('W L V',positive=True)
current=lambda w,l,v:w*v**2/l
speed=lambda l,v:v/l**2
x=symbols('x')
newW=solve(current(x,2*L,V)-current(W,L,V),x)[0]
report('p3:a','symbolic','동일 과구동 전압에서 I_D를 유지하려면 W/L 일정.',new_width=newW)
report('p3:b','symbolic','g_m은 그대로이고 C_GS는 네 배이므로 f_T는 1/4. 채널 길이 변조는 1차 설계식에서 무시한다.',speed_ratio=simplify(speed(2*L,V)/speed(L,V)))
print(json.dumps(result,ensure_ascii=False,indent=2))
