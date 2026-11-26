from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
mu,W,L,Cox,Vov,w,vg=symbols('mu W L Cox Vov omega vg', positive=True)
gm=mu*Cox*W*Vov/L
Cgs=Rational(2,3)*W*L*Cox
current_gain=simplify(gm*vg/(I*w*Cgs*vg))
wt=solve(Abs(current_gain)-1,w)[0]
report('p1:main','symbolic','MOSFET 출력 단락 상태에서 소신호 드레인 전류와 게이트 전류 크기가 같아지는 주파수가 f_T다. C_GD=0에서 i_g=jωC_GS v_gs, i_d=g_m v_gs이므로 ω_T=g_m/C_GS이고 f_T=ω_T/(2π). 포화 장채널 식을 대입한다.',omega_T=wt,f_T=wt/(2*pi))
print(json.dumps(result,ensure_ascii=False,indent=2))
