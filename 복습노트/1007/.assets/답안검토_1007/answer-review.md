# 1007 답안 PDF 최종 실제 렌더 검토

main이 최종 PNG 19쪽 전부 열어 확인했다. 최종 렌더 종료0, overflow=[]; 모든 페이지1440×810pt(16:9), 하단1/6픽셀전부흰색. 원문·핵심회로·판단·계산·최종답을 승인overlay와 start/solve/verify에 대조했고 누락/겹침/잘림 없음. 파랑/빨강 노드 색과 출력오른쪽·시험전류왼쪽·끝점라벨분리를 실제 PDF에서 확인했다.

p7 이어지는쪽의 문제패널만 padding-top/bottom4mm→2.5mm로 조정했다. 글자15.119px·문제텍스트·수학·19쪽규격·자막여백은 그대로이며 workbook 소스는수정하지않았다. 초기OVERFLOW는최종패널영역으로추적했고 수정후기존실제렌더러 overflow검사0을확인했다.

- 1쪽: pass — p1 CM 반회로·KCL·식10.224·최종조건
- 2쪽: pass — p2 Gm 단락·Rout 입력영점 시험원 두 회로와 근사식
- 3쪽: pass — p2 단일종단 ACM 최종값·차동CM0
- 4쪽: pass — p3 DM 첫식·소자전류·gm/ro 계산
- 5쪽: pass — p3 DM -100·CM 실제회로·RSS≈2MΩ·ACM≈-5e-3
- 6쪽: pass — p3 두 소문항 최종답·극성·gmro 조건
- 7쪽: pass — p4 유한rpi·ro3·R1 실제연결과CM반회로·분기점/노드색
- 8쪽: pass — p4 CM-DM 최종답·큰beta·테일근사조건
- 9쪽: pass — p5 CMRR 정의·CE DM 그림·테일rpi·최종조건
- 10쪽: pass — p6 CM회로·RD+ΔRD/2 일반식·테일배율
- 11쪽: pass — p6 (a)/(b) 최종값·근사조건·작은불일치와구분
- 12쪽: pass — p7 원문6소문항·바이어스·입력범위·DM/CM/누출
- 13쪽: pass — p7 CMRR10100/80.09dB·폭2배7171.07/77.11dB·6최종답·반올림약·패널여백수정후모두보임
- 14쪽: pass — p8 PMOS ratio·실제RL/KCL·양의전류전압이득
- 15쪽: pass — p8 +RL/N 최종답·포화/CLM0조건
- 16쪽: pass — p9 a/b 전후출력·변화량·이상전류원compliance조건
- 17쪽: pass — p10 VT26mV·Gm/Rout 블록·전류소거
- 18쪽: pass — p10 VAp65/12≈5.42V·주항목표100·큰beta조건
- 19쪽: pass — p3 Hint 부록의CM 반회로 설명
