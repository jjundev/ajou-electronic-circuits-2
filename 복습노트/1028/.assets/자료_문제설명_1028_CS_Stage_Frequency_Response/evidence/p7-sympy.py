from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
R=symbols('R_L',positive=True)
values={}
for temp in [26,25]:
 vt=Rational(temp,1000); gm=Rational(1,1000)/vt
 rpi=100/gm; ri=1/(1/Rational(200)+1/rpi)
 ff=Rational(1,10**15); ti=ri*(100+(1+gm*R)*20)*ff
 to=(R*(30+20)+20/gm)*ff
 values[str(temp)+'mV_in_MHz']=N((1/(2*pi*ti*10**6)).subs(R,2000),7)
 values[str(temp)+'mV_out_MHz']=N((1/(2*pi*to*10**6)).subs(R,2000),7)
 if temp==26:
  diff=expand((ti-to)/ff)
  assert diff.coeff(R)>0 and diff.subs(R,0)>0
  gap=str(diff)
report('p7:a','exact','VT=26 mV 또는 25 mV의 두 관례를 계산. 두 경우 모두 입력 극점이 더 낮으며 입력이 대역폭을 제한한다. 고이득 출력 근사에서 1+1/(gm RL)≈1로 두면 출력은 1.592 GHz.',**values)
report('p7:b','proof','불가능. τ_in-τ_out는 R_L에 관한 선형식으로 절편과 기울기가 모두 양수이다. 따라서 모든 양의 R_L에서 입력 극점이 더 낮다.',tau_difference_femtoseconds=gap)
print(json.dumps(result,ensure_ascii=False,indent=2))
