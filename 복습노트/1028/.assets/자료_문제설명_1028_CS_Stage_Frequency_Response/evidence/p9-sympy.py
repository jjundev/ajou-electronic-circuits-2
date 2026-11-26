from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
beta=symbols('beta',positive=True)
ff=Rational(1,10**15); cf=5*ff; cc=10*ff; cp=20*ff; fi=5*10**8; fo=2*10**9
for temp in [26,25]:
 g=1/Rational(temp); rp=beta/g
 rc=(1/(2*pi*fo)-cf/g)/(cf+cc)
 ri=1/(2*pi*fi*(cp+(1+g*rc)*cf))
 rb=ri*rp/(rp-ri)
 gain=-g*rc*(1-ri/rp)
 report('p9:'+str(temp)+'mV','symbolic','수치는 Ω 단위. β가 유한하면 R_B와 소스-출력 이득은 β 함수이다. 목표 극을 등식으로 지정하면 주어진 β에 대해 저항이 유일하므로 추가 최적화 자유도가 없다. 입력저항이 무한한 근사에서는 R_B=R_eff.',gm=g,RC=N(rc,10),R_eff=N(ri,10),RB=rb,gain=gain,min_beta=N(ri*g,8),RB_if_beta100=N(rb.subs(beta,100),9),gain_if_beta100=N(gain.subs(beta,100),9),gain_if_beta_infinite=N(-g*rc,8))
report('p9:main','symbolic','출력 조건 R_C(C_CS+C_μ)+C_μ/g_m=1/(2πf_o)으로 R_C를 먼저 구한다. K=[2πf_i(Cπ+(1+gm RC)Cμ)]^{-1}라 하면 R_B∥rπ=K이고 R_B=K rπ/(rπ−K)이다. β가 미지라 유한 β의 R_B나 전체 이득을 숫자 하나로 확정할 수 없다. 만약 목표가 최소 대역폭이라는 해석이면 큰 R_C와 작은 R_B가 이득에 유리하며 R_B→0으로 입력 극이 목표보다 올라간다. 원문은 극 위치 등식을 지정한다.')
print(json.dumps(result,ensure_ascii=False,indent=2))
