from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
VT=Rational(25,1000);Ic=Rational(1,2000)
g=Ic/VT;rp=200/g;ro=5/Ic;R=ro/2;Ri=1/(1/Rational(10000)+1/rp)
A=g*R
Cpi,Cmu,Cmu2,Ccs1,Ccs2=symbols('C_pi1 C_mu1 C_mu2 C_CS1 C_CS2',positive=True)
ci=Cpi+(1+A)*Cmu;co=(1+1/A)*Cmu+Cmu2+Ccs1+Ccs2
report('p8:main','symbolic','문제의 I_D1은 그림의 BJT Q1 컬렉터 전류로 해석. 두 컬렉터 전류 크기는 같고 Q2 베이스와 이미터는 AC 접지이다. Cπ2는 신호에 기여하지 않는다. 집적 BJT에서 C_CS를 포함하면 두 컬렉터-기판 용량 모두 출력에 더한다. Cπ,Cμ만의 모형이면 C_CS1=C_CS2=0. 출력의 1.01은 고이득 근사에서 1.',gm=g,rpi=rp,ro1=ro,ro2=ro,Rin=Ri,Rout=R,base_to_output_gain=-A,omega_in=1/(Ri*ci),omega_out=1/(R*co),f_in=1/(2*pi*Ri*ci),f_out=1/(2*pi*R*co))
print(json.dumps(result,ensure_ascii=False,indent=2))
