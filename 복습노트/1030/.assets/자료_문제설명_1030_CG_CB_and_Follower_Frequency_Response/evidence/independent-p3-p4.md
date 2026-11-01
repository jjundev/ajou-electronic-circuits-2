# 독립 블라인드 검산: p3, p4

공통: 전원과 고정 바이어스는 소신호 접지, MOS 벌크도 접지라고 둔다. g_oi=1/r_oi. 입력 커패시턴스는 저주파 극한 C_in=lim_(s→0) Y_in/s로 정의한다. 벌크 효과를 무시하는 모델은 g_mb1=0을 대입한다. 게이트 누설은 무시한다.

## p3 (E11.23)
M2 게이트와 소스는 교류 접지이므로 M2는 출력저항 r_o2로 부하한다. M1 소스 노드를 v_s라 두고 G=g_mb1+g_o1+g_o2, C_x를 v_s와 교류 접지 사이의 모든 그 외 기생 용량(예: C_sb1, C_gd2, C_db2)의 합으로 두면 소스 KCL은

(G+s C_x)v_s - g_m1(v_in-v_s) + s C_gs1(v_s-v_in)=0.

따라서 v_s/v_in=(g_m1+s C_gs1)/(g_m1+G+s(C_gs1+C_x)). M1의 게이트-드레인과 게이트-벌크 용량도 포함한 입력 어드미턴스는

Y_in=s(C_gd1+C_gb1)+s C_gs1 (G+s C_x)/(g_m1+G+s(C_gs1+C_x)).

따라서 저주파 입력 커패시턴스는

**C_in = C_gd1+C_gb1+C_gs1 (g_mb1+g_o1+g_o2)/(g_m1+g_mb1+g_o1+g_o2).**

통상 C_gb1을 무시하면 해당 항을 삭제한다. C_gs1만 취급하면 마지막 항만 남는다. λ≠0이므로 g_o1,g_o2를 임의로 0으로 만들지 않는다. g_o1,g_o2,g_mb1→0에서는 C_gs 기여가 0으로 가고 직접 접지된 C_gd1+C_gb1은 남는다. 주파수가 유한할 때 위 Y_in/s는 일반적으로 상수인 커패시턴스가 아니므로 저주파 결과와 구별한다.

## p4 (P11.47)
M2의 게이트와 드레인이 소스 노드에 함께 연결되고 M2 소스·벌크는 교류 접지다. M2는 g_m2+g_o2의 접지 컨덕턴스를 제공한다. H=g_mb1+g_o1+g_m2+g_o2라 놓으면 유일한 커패시터 C_gs1을 포함한 KCL은

H v_s - g_m1(v_in-v_s) + s C_gs1(v_s-v_in)=0.

v_s/v_in=(g_m1+s C_gs1)/(g_m1+H+s C_gs1), Y_in=s C_gs1 H/(g_m1+H+s C_gs1). 따라서

**C_in=C_gs1 (g_mb1+g_o1+g_m2+g_o2)/(g_m1+g_mb1+g_o1+g_m2+g_o2).**

벌크 효과를 무시하면 g_mb1=0이다. g_o1,g_o2,g_mb1→0이어도 C_in→C_gs1 g_m2/(g_m1+g_m2): 다이오드 연결된 M2의 g_m2가 부트스트래핑을 약화한다. 그 후 g_m2→0이면 C_in→0이다.

검산: bucket/evidence/p3-sympy.py 및 p4-sympy.py와 각각의 result.txt. 지정된 blind JSON 두 개와 그림 두 개만 읽었다.
