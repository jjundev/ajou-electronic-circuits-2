from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
g,R,Rs,Cg,Cf,Cd=symbols('g_m R_D R_S C_GS C_GD C_DB',positive=True)
def params(g,r,cg,cf,cd):
 a=g*r
 return [-a,1/(Rs*(cg+(1+a)*cf)),1/(r*(cd+(1+1/a)*cf))]
old=params(g,R,Cg,Cf,Cd); new=params(g/2,R,Cg/2,Cf/2,Cd/2)
report('p5:main','symbolic','고정 RD, 고유 기생용량이 폭에 비례하며 ro≫RD라고 둔다. 바이어스 전류와 폭이 함께 절반이므로 V_OV는 동일하고 gm 및 각 기생용량은 절반이다. 저주파 이득은 절반. 고이득의 밀러 지배 입력에서는 입력 극점은 약 4배, 출력 극점은 약 2배. 일반식은 아래 식. 만약 유한 ro를 고려하면 R은 원래 RD∥ro, 변경 후 RD∥(2ro)로 각각 대체한다.',Av_new=new[0],omega_in_new=factor(new[1]),omega_out_new=factor(new[2]),omega_in_ratio=factor(new[1]/old[1]),omega_out_ratio=factor(new[2]/old[2]))
print(json.dumps(result,ensure_ascii=False,indent=2))
