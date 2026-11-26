from sympy import *
import json
result = {}
def report(part, method, conclusion, **values):
    result[part] = dict(method=method, conclusion=conclusion, values={k:str(v) for k,v in values.items()})
gm1,gm2,gb2,o1,o2,Rs=symbols('g_m1 g_m2 g_mb2 r_o1 r_o2 R_S',positive=True)
gs1,gs2,gd1,gd2,db1,db2,sb2=symbols('C_GS1 C_GS2 C_GD1 C_GD2 C_DB1 C_DB2 C_SB2',positive=True)
for tag,drive,loadgm,cgi,cf,co in [('a',gm1,gm2,gs1,gd1,db1+db2+gs2),('b',gm1,gm2+gb2,gs1,gd1,db1+gs2+sb2),('c',gm2,0,gs2,gd2,db1+db2+gd1)]:
 R=1/(1/o1+1/o2+loadgm)
 A=drive*R
 report('p6:'+tag,'symbolic','A=g_m,drive R은 노드간 이득의 절댓값. 표기한 ω는 극의 양의 크기. (b)는 벌크 AC 접지이며 소스-벌크 접합용량/바디효과를 생략하는 모델이면 C_SB2 또는 g_mb2를 0으로 둔다.',R=R,Av=-A,Cin=cgi+(1+A)*cf,Cout=co+(1+1/A)*cf,omega_in=1/(Rs*(cgi+(1+A)*cf)),omega_out=1/(R*(co+(1+1/A)*cf)))
report('p6:main','symbolic','(a) 다이오드 접속 PMOS, (b) 게이트·드레인 AC 접지 NMOS 소스 부하, (c) PMOS 입력과 고정 바이어스 NMOS 부하. 각 값은 p6:a,b,c. 고이득 출력 근사 시 1+1/A를 1로 둔다.')
print(json.dumps(result,ensure_ascii=False,indent=2))
