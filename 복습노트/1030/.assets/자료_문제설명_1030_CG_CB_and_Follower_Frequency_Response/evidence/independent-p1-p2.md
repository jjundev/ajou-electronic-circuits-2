# 독립 블라인드 풀이: E11.19, P11.46

사용 자료: blind-p1.json, blind-p2.json과 각 그림만. 아래는 포화 영역 소신호 등가회로, 이상 바이어스·전원 AC 접지, 이상 전류원, 주파수 독립 소자값 가정이다. 접합 및 바디 효과를 생략하는 표준 근사는 g_mb=0, C_sb=C_db=0을 대입한다. 주어진 그림에 기생 커패시턴스가 표시되지 않으므로 아래 C는 MOS 고주파 기생을 포함한 모델이라는 명시적 가정이다. 게이트 저항 및 부하 커패시턴스가 있다면 해당 항을 추가해야 한다.

공통으로 x=M1 소스, y=출력, G1=g_m1+g_mb1이라 두면 λ1=0에 대해 KCL은

(x-vin)/Rs + (G1+s Cx)x = 0,
(G_L+s Cy)y - G1 x = 0.

따라서 H(s)=G1/[(1+Rs G1+s Rs Cx)(G_L+s Cy)]. M1의 게이트와 바디는 AC 접지다. Cx=C_gs1+C_sb1; Cy에는 공통적으로 C_gd1+C_db1이 들어간다. 별도 명시가 없다면 접합 C와 바디 효과를 0으로 두면 된다. 유한 양의 소자값과 비상쇄를 전제로 두 극점은 -(1+Rs G1)/(Rs Cx), -G_L/Cy다.

## E11.19

M2는 다이오드 접속 PMOS이며 λ=0이므로 G_L=g_m2, Cy=C_gd1+C_db1+C_gs2+C_db2. M2의 C_gd2는 양단이 같은 노드여서 기여하지 않는다. 그러므로 극점은

p_x=-(1+Rs(g_m1+g_mb1))/(Rs(C_gs1+C_sb1)),
p_y=-g_m2/(C_gd1+C_db1+C_gs2+C_db2).

바디·접합 기생을 무시하면 p_x=-(1+Rs g_m1)/(Rs C_gs1), p_y=-g_m2/(C_gd1+C_gs2). Rs→0이면 입력 극점은 무한대로 가고 H→G1/(g_m2+s Cy). 예외적으로 두 극점이 같으면 중복극이다.

## P11.46

M1만 λ=0이므로 M2의 g_ds2는 유지한다. 위 공통 H에 다음을 대입한다.

(a) M2의 드레인과 게이트가 전원에 연결된 NMOS, 소스가 출력: G_L=g_m2+g_mb2+g_ds2, Cy=C_gd1+C_db1+C_gs2+C_sb2. M2의 C_gd2, C_db2는 양단이 AC 접지다.

(b) M2의 소스가 전원, 게이트가 고정 바이어스인 PMOS: G_L=g_ds2, Cy=C_gd1+C_db1+C_gd2+C_db2. M2의 v_sg가 변하지 않아 g_m2는 부하 도전도에 들어가지 않는다.

(c) M2의 게이트와 드레인이 출력에 연결된 NMOS: G_L=g_m2+g_ds2, Cy=C_gd1+C_db1+C_gs2+C_db2. M2의 소스·바디가 접지이므로 g_mb2는 기여하지 않고 C_gd2는 단락된다.

각 경우 DC 이득은 G1/[(1+Rs G1)G_L], Rs→0이면 G1/(G_L+s Cy), Cx,Cy가 양수이면 s→∞에서 0이다. (b)에서 g_ds2→0인 이상화의 DC 이득은 발산하므로 임의로 g_ds2를 버릴 수 없다. s→0과 g_ds2→0의 특이성도 주의한다. 모든 커패시턴스를 완전히 생략하면 전달 함수는 위 DC 이득 상수다.

독립 SymPy KCL, 극점·한계 확인은 bucket/evidence/p1-sympy.py, p1-result.txt, p2-sympy.py, p2-result.txt에 기록했다.
