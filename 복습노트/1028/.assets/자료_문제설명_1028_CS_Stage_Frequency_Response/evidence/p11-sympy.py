from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
s=symbols('s');rs=200;r=2000;g=Rational(1,150)
ff=Rational(1,10**15);cg=250*ff;cf=80*ff;cd=100*ff
ti=rs*(cg+(1+g*r)*cf);to=r*(cd+(1+1/(g*r))*cf)
b1=rs*(cg+cf)+r*(cd+cf)+g*rs*r*cf;b2=rs*r*(cg*cd+cg*cf+cd*cf)
hz=lambda w:N(w/(2*pi),10)
wm=[1/ti,1/to];wp=sorted([ (b1+sign*sqrt(b1*b1-4*b2))/(2*b2) for sign in [-1,1] ])
wa=[1/b1,b1/b2];z=g/cf
hm=-g*r/((1+s*ti)*(1+s*to))
he=-g*r*(1-s/z)/(1+b1*s+b2*s**2)
hd=-g*r/(1+s*b1)
hd2=-g*r*(1-s/z)/((1+s/wa[0])*(1+s/wa[1]))
def db(h,x):
 return round(20*log(abs(complex(h.subs(s,2*pi*I*x*10**6))),10).evalf(),3)
def f3(h):
 import math
 lo,hi=1.0,1e10;target=float(g*r)/math.sqrt(2)
 for _ in range(75):
  f=(lo+hi)/2
  if abs(complex(h.subs(s,I*2*pi*f)))>target:lo=f
  else:hi=f
 return round((lo+hi)/2/1e6,4)
grid=[1,100,250,500,1000,2500,5000,10000,25000]
for p,h,ws,desc in [('a',hm,wm,'밀러 상수 이득을 적용한 2극 저역통과. 출력의 역이득 항을 생략하면 출력 극점은 442.10 MHz가 된다.'),('b',he,wp,'정확한 2극·우반평면 영점 전달함수.'),('c',hd,wa,'저주파 단일 주극점 모델. ωp2≈b1/b2까지 복원한 두 극 근사도 별도 기록. 단일 극 응답은 높은 주파수에서 정확도가 낮아진다.')]:
 report('p11:'+p,'exact' if p=='b' else 'symbolic',desc,H=h,poles_Hz=[hz(v) for v in ws],RHP_zero_Hz=hz(z) if p=='b' else '해당 모형 참조',f3_MHz=f3(h),MHz_grid=grid,dB=[db(h,v) for v in grid])
report('p11:main','exact','저주파 이득 −13.3333 V/V. p11:a,b,c에 동일 축을 그릴 수 있는 주파수 응답 표 포함. 정확한 분모 1+b1s+b2s², 영점은 우반평면. 주극점 2극 복원 모델은 선택적으로 이용할 수 있다.',b1_s=b1,b2_s2=b2,H_dominant_two_poles=hd2,dominant_two_pole_f3_MHz=f3(hd2),dominant_two_pole_dB=[db(hd2,v) for v in grid])
print(json.dumps(result,ensure_ascii=False,indent=2))
