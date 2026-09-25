# 원문 리뷰 J — 커밋 3c41dfd (P10.38–P10.52)

방법: source_pages.py render --dpi 300, PDF p.36(교재 561쪽), p.37(교재 562쪽)을 직접 읽고 `git show 3c41dfd`의 원문과 대조. check_md.py ch10: 151개 파일, 오류 0개.

## 작성자가 애매하다고 한 곳 — 독립 판독
- P10.45 "Verify that is result": 맞음 (인쇄가 "Verify that is result is equal to √2 times"임). 조건 끝의 메모 `- (원문의 "that is result"는 "that this result"의 오식으로 보임)`는 규칙 형식에 맞고, 원문 절 밖(## 조건)에 있어 괜찮음. ("that its result"로도 읽을 수 있으나 "this"도 무리 없음)
- P10.46 식 (10.221): 맞음. $G_m = \partial(I_{D1}-I_{D2})/\partial(V_{in1}-V_{in2})$ 뒤의 마침표와 번호 (10.221)가 인쇄와 같음. 앞 문장 "defined as"와 뒤 문장 "Plot the result …"의 문단 나눔도 인쇄 배치와 맞음.
- P10.47 식 (10.222): 맞음. $I_D = \gamma(V_{GS}-V_{TH})^3$ 뒤의 쉼표, 번호, 이어지는 "where $\gamma$ is a proportionality factor." 모두 인쇄와 같음.

### P10.38 — OK
### P10.39 — OK
### P10.40 — OK
### P10.41 — OK
### P10.42 — OK
### P10.43 — OK
### P10.44 — OK
### P10.45 — OK
### P10.46 — OK
### P10.47 — OK
### P10.48 — OK
- 쪽을 넘어가는 문장("… at which the transconductance drops by a factor of 2.", p.37 왼쪽 단 위)까지 온전히 옮김.
### P10.49 — OK
### P10.50 — OK
### P10.51 — OK
- 소문항 (b)(c)가 p.37 오른쪽 단 위로 넘어간 부분까지 온전함. 소문자 $v_X$, $v_Y$, $v_{in}$ 구분 맞음.
### P10.52 — OK

수정 필요: 없음 (No findings). 번호·별표·SOL·캡션 제외, 하이픈 붙이기, 수치·첨자·부호 모두 인쇄와 일치. 원문과 ## 조건 값 어긋남 없음.
