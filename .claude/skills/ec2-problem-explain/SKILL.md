---
name: ec2-problem-explain
description: "전자회로2 복습팩이 이미 고른 workbook 문제(날짜별 복습노트의 .assets/problems.txt)마다 문제의 단서·떠올릴 개념과 공식·첫 줄·단계별 이유·완성 답·검산·함정을 펼친 문제설명 HTML과 MD를 만들고, 원문 대조·내용·독립 검산·브라우저 검토를 통과한 뒤에만 복습노트에 발행한다. \"문제설명\", \"복습문제 풀이 설명\", \"1007 문제 풀이 설명해줘\"처럼 요청하거나 /ec2-problem-explain [MMDD|MMDD-MMDD]로 부를 때 사용한다. 새 출제·정리노트·PDF·영상은 별도 스킬(ec2-review-pack 등)이다."
---

# 전자회로2 문제풀이 입문 설명

Razavi 이론은 읽었지만 문제풀이 경험이 적은 학생에게 개인 명세에 맞춘 해설을 쓴다. 문항별 표시 순서는 **문제를 읽어요 → 이 개념과 공식을 떠올려요 → 종이에 쓸 첫 줄 → 이렇게 풀어요 → 완성 답과 검산 → 주의할 점 → 조건을 바꾸어 생각해요**다. 별도 핵심 풀이를 앞에 붙이지 않고 사용자 방식의 계산 경로를 start/solve/verify의 정식 풀이로 통합한다. 개념·이유·유도는 필요한 단계에 연결하며 같은 풀이를 두 번 쓰지 않는다. 중간에 사용자에게 묻지 않고 끝에 한 번 보고한다. 커밋은 제안만 한다.

**한 행에 하나의 식:** 독립된 계산 대상은 각각 별도 display 블록/MD 줄/PDF 행에 쓴다. 서로 다른 $g_m$, $r_\pi$, $r_o$ 계산을 쉼표·\quad·\qquad로 한 줄에 묶지 않는다. 같은 양의 `식 = 대입 = 결과` 연속 등식과 실제 같은 값을 가진 소자의 등식 묶음은 유지할 수 있으며, 폭을 넘으면 단계별로 세로로 나눈다. 설명문의 짧은 기호·조건은 인라인으로 쓸 수 있다.

**기본 근사와 회로 표기:** 공통 `solution-style.md`의 수업 기본 근사를 적용한다. $g_mr_o\gg1$, $g_mR_e\gg1$의 주항을 쓰고 캐스코드의 곱 인자 소자를 밝힌다. 내부 $r_e=1/g_m$는 축퇴 저항과 구분하고 유한 $r_\pi$는 보존한다. 생성 SVG는 NOTATION-01의 native text/tspan 실제 첨자(기본 78%)·Pretendard 600 정체로 통일하고 실제 face 사용을 HTML·독립 SVG·PDF에서 검토한다. CM 이득은 성립 조건을 확인한 $2R_{SS}$ 반회로를 본풀이에 앞세우고 테일 저항 유도는 보충으로 분리한다. 부하 불일치·거울 결합·원문 지정 방법의 예외는 PROFILE CIRCUIT-02를 따른다.

**표시 제목:** 대상 팩 `.assets/display-titles.json`의 workbook ID별 짧은 제목을 사용한다. 없다면 검토 전에 선정된 ID 전체의 맵을 작성한다. 값에는 `P<n>.` 접두사나 Fig 번호를 넣지 않고 목차·본문·MD에서 생성기가 붙이는 `P<n>. 짧은 제목`을 사용한다. 원본 문제은행 제목과 출처는 유지한다. 맵 변경은 입력 해시를 바꾸므로 기존 승인을 재사용하지 않는다.

## 통합 구조와 현재 도구의 적용 경계

공통 조립·검사는 확정한 일곱 구역의 통합 본문을 받는다. 새 저작에는 별도 route나 구형 core 표지를 허용하지 않는다. `epe_solution.py`는 본문의 기존 요소에 붙인 `data-answer-step`/`data-answer-final`을 검사하고, `epe_core.py`·`epe_render.py`는 최종 stage DOM에서 같은 내용을 `answer-overlay.json`으로 추출한다. 과거 발행 자료를 검증하는 구형 route 추출은 유지하되 새 build의 저작 형식으로 재사용하지 않는다.

PDF에는 [저작 규칙](references/authoring.md)의 선택 표지를 쓴 핵심 회로·판단·계산·최종 답을 담는다. 상세 이유·유도·검산은 HTML 본문에 유지한다. 내용·개인화 감사·독립 검산·원문·브라우저 검토와 현재 입력/명세/산출 해시가 승인되어야 발행된다. 표지 누락이나 미지원 원고는 withheld이며 숨긴 중복 풀이·검사 우회·과거 승인 재사용으로 해결하지 않는다.


**모델 이름**: 이 문서의 opus는 Claude 기준이다. Claude가 아닌 환경(GPT)에서는 opus 대신 sol을 쓴다.

**진행 표시**: 단계마다 한 줄만 쓴다. 예: `3/8 작성 중: 문항 10개 (병렬)`

## 호출 모드
- 단독 호출은 아래 대상 선택과 최종 보고 형식을 유지한다.
- 부모 `ec2-review-pack` 호출은 부모가 확정한 `range`를 `--target`에 명시한다. 최신 팩 자동 선택을 사용하지 않는다. 부모의 `RUN/problem-explain/<새 실행ID>/` 아래 없거나 비어 있는 폴더를 자식 `RUN`으로 쓴다.
- 부모 호출도 저작·독립 검산·네 검토·publish를 모두 수행한다. 중간 단계 진행만 표시하고 최종 결과는 부모 보고에 합친다. 보호 대상·CLI 옵션·발행 게이트는 동일하다.

## 대상과 보존

- `1007`: `복습노트/1007/.assets/problems.txt`의 순서대로 전 문항.
- `0923-1002`: 정확히 같은 이름의 통합 폴더가 있으면 그 팩, 없으면 범위 안 날짜별 팩을 각각 처리한다. 팩마다 독립 성공/실패다. 통합 폴더와 개별 폴더가 함께 있으면 후보 경로를 보여 주고 멈춘다.
- 인자 없음: `problems.txt`가 있는 팩 중 폴더명 끝 날짜가 가장 늦은 팩. 같은 끝 날짜 후보가 여럿이면 후보를 보여 주고 멈춘다.
- `problems.txt`가 없는 팩(예: 0902·0904)을 지정하면 "문제 없는 팩"으로 멈춘다. 기출 회차·임의 문제 id·설계과제는 대상이 아니다.

새 문제, 정리노트, PDF, 영상, 자동 채점은 만들지 않는다. 원본(`problems.txt`, 문제 md, 문제 그림, 복습문제 PDF, 정리노트 HTML·MD)은 고치지 않는다. 부모의 공통 선발 명세는 `../ec2-review-pack/references/problem-selection.md`(기출 우선 최대 20개, 다른 회차 사용 문항 항상 제외)다. 참고 풀이가 없어도 원문에서 직접 풀고 독립 검산한다. 없음 자체는 disputed가 아니다. md의 `## 풀이`는 참고 답안일 뿐 독립 검산을 대신하지 않는다. md 풀이가 틀렸다고 보이면 고치지 말고 disputed로 보고한다(수정은 `workbook-solution` 몫). 원문이 모호하거나 풀이 불일치가 해결되지 않으면 withheld로 부모에 보고하며 임의로 문제를 바꾸지 않는다. 정리노트에 링크를 자동으로 넣지 않는다.

## 경로 약속

- `SKILL` = 이 파일이 있는 폴더(`.claude/skills/ec2-problem-explain`)의 절대 경로
- `REPO` = 이 checkout의 저장소 루트 절대 경로
- `PROFILE` = `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md`의 실제 절대 경로. 작성자·내용 리뷰어가 필수로 읽고 `source.json.learning_style` snapshot과 대조한다.
- `RUN` = `<scratchpad>/ec2-problem-explain/<실행ID>` (실행ID 예: `1007-20261013-1530`). 매번 새로 정하며, 없거나 빈 폴더여야 한다.
- `BUCKET` = `RUN/review-<range>-<slug>/` (팩마다 하나, extract가 만든다)
- 셸 상태는 Bash 호출 사이에 이어지지 않는다. 아래 명령의 `$SKILL`, `$RUN`, `$REPO`, `$BUCKET`은 실행할 때마다 실제 절대 경로로 바꿔 쓰거나, 같은 셸 호출에서 `SKILL=…; RUN=…; REPO=…;`로 먼저 설정한다. `RUN=… python3 … "$RUN"`처럼 인자 확장과 같은 명령 앞에 설정하지 않는다. `cd`는 쓰지 않고 파일도 절대 경로로 넘긴다.

CLI는 [scripts/epe_cli.py](scripts/epe_cli.py) 하나이며 `extract`, `build`, `check`, `publish`, `rerender` 다섯 명령이 있다. 설명은 에이전트가 저작한다. CLI만 실행하면 풀이가 자동으로 써지지 않는다.

## 절차

### 0. 준비
1. `REPO`에 `복습노트/`, `교과서/마이크로전자회로/`, `workbook/problem.py`, `workbook/source_pages.py`가 모두 있는지 확인한다. 없으면 "전자회로2 저장소에서만 동작해요"라고 알리고 멈춘다.
2. `python3 --version`이 3.10 이상인지 확인한다. 실행기는 표준 라이브러리와 저장소 workbook 모듈만 쓴다.
3. 독립 검산용 SymPy를 확인하고, 없으면 설치한다.
   ```bash
   python3 -c "import sympy; print(sympy.__version__)" || pip3 install --user --break-system-packages sympy
   ```

4. `PROFILE`을 실제로 읽는다. extract는 현재 명세의 원본 바이트 snapshot을 필수로 저장한다. 누락·변경은 새 저작/검토 대상이며 구버전 검토로 대체하지 않는다.

### 1. extract
```bash
python3 "$SKILL/scripts/epe_cli.py" extract --repo "$REPO" --target 1007 --run "$RUN"
```
- `--target`은 인자 그대로(`1007`, `0923-1002`), 인자가 없으면 `--target`을 뺀다.
- 팩마다 `BUCKET/source.json`, 빈 `explanations/`, 빈 `evidence/`가 생기고 `RUN/run.json`에 목록이 남는다. 출력의 `extract: …/source.json` 줄이 팩 목록이다.
- 새 팩의 `.assets/selection.json`은 ID·순서와 메타데이터를 검증하고 원본 해시에 포함한다. 핵심/추가·소문항 묶음 수·추정 시간은 생성기가 표시한다. 저작자가 제목이나 원문에 중복 삽입하지 않는다. 참고 풀이가 없는 source의 reference_steps/reference_answer는 빈 값이며 정상 입력이다.
- 대상 오류(없음·문제 없는 팩·여러 후보)는 메시지를 그대로 보여 주고 멈춘다. 한 팩만 실패하면(종료 코드 1, stderr에 그 팩) 그 팩을 withheld로 적고 나머지는 계속한다.

### 2. 자료 읽기
`BUCKET/source.json`에서 팩의 `range`·`slug`, 문항마다 `id`(`p1`…)·`source`(`<workbook id> · <종류> <번호>`)·`original_html`·`conditions_html`·`ask_html`·`figures_html`·`reference_steps`·`reference_answer`·`subparts`, 그리고 `inputs`(problems.txt·문제 md·그림의 절대 경로)를 확인한다. 작성자에게 넘길 참고 자료를 문항마다 정한다.
- 문제 md: `inputs`의 해당 md(frontmatter의 `section`, `book_page`, `pdf_page`, 그림 id). 기출(`from_the_past/md/…`)은 `textbook_chapters`로 관련 장을 정한다.
- 기출 선별 JSON은 부모가 문제를 고를 때 사용하는 자료다. 선택 후에는 기존 기출 ID를 `problems.txt`로 받고 MD·그림에서 extract한다. `selection`의 필요 개념은 참고 자료를 찾는 보조 정보이며 draft·stale을 검토 완료로 해석하지 않는다. 문항 전체와 모든 소문항을 설명한다. JSON의 분류 상태나 MD 참고 풀이가 원문 대조·독립 검산·네 검토를 대신하지 않는다.
- Razavi 교과서: `교과서/마이크로전자회로/<N>장.pdf`의 그 절 쪽(교과서 문항은 md frontmatter `section`·`pdf_page` 근처)과, 같은 장 md 폴더의 관련 예제(`교과서/마이크로전자회로/chNN/README.md` 인덱스로 찾는다).
- 강의자료: 그 절을 다루는 `강의노트/2026F_Lec*_*.pdf`의 슬라이드.
- 같은 날 정리노트: `복습노트/<range>/정리노트_<range>_<slug>.html`(개념 링크의 anchor도 여기서 고른다).
- STT(`STT/<MMDD> 전회2.md`)는 교수님 표현·강조를 확인할 때만 보조로 쓴다.

### 핵심 규칙을 실제 풀이로 연결하기

[저작 규칙](references/authoring.md)의 교육적 연결·retry 기준을 적용한다. 핵심 규칙 → 작은 상태 변화 또는 기호 조작 → 실제 첫 식 → 유도를 연결하고, 범용 재계산 문구 대신 조건을 바꿔 규칙을 적용하는 질문을 쓴다. 허용된 보충 정확식에도 같은 기준을 적용하되 $R_{out}$은 아래 표시/검산 경계를 따른다. [내용 검토](references/verification.md)에서 리뷰어가 첫 식과 retry 답을 재구성하고 본문·요약·MD·그림의 조건·방향·수치를 대조한다. 구조 검사와 수학 검산만으로 교육적 연결을 승인하지 않는다.

### 3. 저작 (문항마다 opus 작성자, 병렬)
- 문항마다 작성자 1명을 **한 메시지에서 병렬로** 띄운다. 모델은 opus(GPT: sol)다.
- 브리프 필수 슬롯: `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md` 실제 절대 경로, `BUCKET/source.json.learning_style` snapshot, 원문 `subparts` 순서, 통합 일곱 구역(understand → recall → start → solve → verify → pitfall → retry), solve 제목 `이렇게 풀어요`, 마지막 sum, 독립 계산 한 행 규칙, 규칙별 적용 위치 또는 비적용 이유 보고.
- 브리프에 적을 것: [저작 규칙](references/authoring.md)의 절대 경로를 먼저 읽으라는 지시, `BUCKET/source.json` 경로와 문항 id(`pN`), 그 문항의 `subparts`, 2에서 정한 참고 자료 경로와 쪽, 출력 파일 `BUCKET/explanations/pN.html` 하나(다른 곳에는 쓰지 않는다), 임시 파일은 `RUN/work/pN/`에만.
- 작성자는 원문·조건·구할 것·그림을 다시 쓰지 않는다(조립기가 md에서 붙인다).
- 브리프의 회로 슬롯: PROFILE의 `CIRCUIT-02`와 [저작 규칙](references/authoring.md)의 “소신호 등가회로 그림”을 적용한다. start/solve의 해당 계산 앞에는 측정 조건을 실제 연결한 회로·생략 근거·노드 관계를 보인다. $G_m$의 출력 단락 접지와 $R_{out}$의 입력 영점·시험원을 구별하고, 입력·노드·축퇴 저항을 식과 대응시키고, 병렬쌍은 전류원 왼쪽/$r_o$ 오른쪽으로 둔다. 상세 KCL/KVL에 필요한 모델은 start(필요시 solve)에 보존한다. $R_{out}$ 정확 전체 모델은 아래 예외가 아니면 내부 검산에만 둔다. 유한 β·$r_o$가 필요한 핵심을 큰 β 그림으로 바꾸지 않는다. 순수 DC는 제외한다. 같은 목적의 그림을 핵심/상세로 복제하지 않으며 측정 조건·필수 모델이 다르면 필요한 그림을 해당 단계에 둔다.
- 출력 배치 필수: 입력은 왼쪽, 출력 단자·출력 라벨·출력 시험원/단락 접속은 오른쪽에 둔다. 회로로 유입하는 시험전류는 오른쪽에서 왼쪽으로 그리며, 내부 제어 전류원의 방향·전압 극성·실제 접속은 유지한다. 전기적으로 같은 노드라는 이유로 출력 접속을 왼쪽이나 중앙에 두지 않는다. 풀이 본문·HTML·PDF에서 각각 확인한다.
- 병렬 가지 순서 필수: 제어 전류원과 $r_o$가 병렬이면 반드시 **제어 전류원 왼쪽 → $r_o$ 또는 병렬 합성 저항 오른쪽 → 출력 접속 맨 오른쪽** 순서로 그린다. 입력은 그 왼쪽, 이미터/소스 축퇴 저항은 해당 노드 아래에 둔다. $r_o$를 생략한 축약 모델에는 없는 저항을 추가하지 않는다. 그 모델의 제어원 위치를 병렬쌍의 배치 규칙으로 일반화하지 않는다. 풀이 본문의 모든 SVG와 답안 PDF에서 소자·단자 전체 배치를 대조하고, 전기적 등가성만으로 위치 불일치를 승인하지 않는다.
- 노드 점과 시험 표기 필수: 접지 표기만 하는 비분기 단자와 접지 기호의 직접 접속점을 제외하고, 입력·출력·시험 노드와 이름을 붙인 전압 노드에는 연결 위치가 분명한 눈에 보이는 점을 찍는다. 출력 시험전압 노드의 점은 출력 도선의 실제 맨 끝이자 가장 오른쪽 단자에 둔다. 점 오른쪽으로 도선(ink)이 더 이어지거나 연장된 도선 중간에 점이 놓이면 안 된다. 시험 노드 전압 $V_t(+)$는 그 끝점 위에 둔다. 유입 시험전류는 오른쪽에서 왼쪽으로 흐르며, 왼쪽을 향하는 $i_t$ 화살표는 $V_t$ 점 왼쪽의 도선 구간에 둔다. $i_t$ 라벨도 점 왼쪽에서 그 화살표 아래나 곁에 둔다. 화살표 전체가 점 왼쪽에 머물고 점을 덮지 않도록 화살표 꼬리와 점 사이에 작은 간격을 남긴다. 화살표나 전류 라벨을 점 오른쪽에 놓지 않는다. 다른 시험 기호($v_x/i_x$ 등)를 쓰면 같은 배치와 정의를 적용한다. 선 교차만 있고 연결되지 않은 곳에는 점을 찍지 않는다. 라이트·다크 HTML과 실제 답안 PDF에서 점·라벨·화살표의 분리와 가시성을 각각 확인한다.
- 회로 안 글자와 점의 정돈: SVG 안에는 소자 이름·값·제어 전류원 라벨(예: $g_mv_\pi$), 노드 이름·극성·방향처럼 실제 회로를 읽는 표기를 남긴다. 분석용 $G_m$ 제목·측정 조건 문구·유도 설명은 그림 아래 figcaption이나 수식 문단에 둔다. 출력 단락·입력 영점의 실제 연결은 그림에 보존한다. 접지 입력 위의 독립 제목 `Rout`처럼 불필요한 제목은 옮겨 중복하지 않고 삭제한다. 가까운 노드 관계는 유도 설명이 아니고 겹치지 않을 때만 남길 수 있다. 접지 표기만 하는 비분기 단자·접지 기호의 직접 접속점은 제외하고 입력·출력·시험 단자, 이름 붙인 내부 전압 노드, 실제 분기 접속점의 점은 유지하되 이름도 분기도 없는 직선 도선 중간의 장식 점은 없앤다. 모든 도선에 점을 추가하라는 규칙이 아니다. $V_{out}(+)$·$V_t$ 등 라벨은 아래첨자까지 포함한 실제 글리프 경계상자가 도선에서 최소 0.6em(보통 화면에서 약 8px) 떨어지게 배치한다. 텍스트 기준선 간격만 확인하지 않는다. 필요하면 라벨을 옮기고 viewBox 위쪽 여백을 늘린다. 풀이 본문의 모든 SVG를 열거하여 라이트·다크 HTML과 실제 답안 PDF의 보통 보기 크기에서 이 간격·클리핑·겹침을 확인한다. 병렬 제어원 왼쪽/$r_o$ 오른쪽/출력 맨 오른쪽, 맨 끝 $V_t$ 점 오른쪽 도선 없음, 점 왼쪽의 왼쪽 방향 $i_t$와 라벨 배치도 유지한다.
- 접지·전압 라벨·노드 색 대응: 접지 기호에 직접 닿는 점과 접지만 표시하는 비분기 입력 단자의 점은 생략한다. 접지로 이어지는 회로라도 별도의 실제 분기 접속점·이름 있는 비접지 노드는 유지한다. $v_e$ 등 전압 이름은 다른 소자나 저항 옆으로 멀리 밀지 않고 해당 노드 바로 곁에 둔다. 아래첨자·극성을 포함한 실제 글리프 경계로 도선과 최소 0.6em 간격을 확보하면서 가능하면 0.6–1em 정도의 가까운 간격을 목표로 한다. 혼잡 때문에 더 벌리면 배치 이유를 검토에 기록한다. 노드 점과 해당 전압 이름·극성은 같은 파랑 또는 빨강으로 묶는다. 주요 신호 경로를 따라 파랑·빨강을 교대하고 가까운 전압 라벨끼리 최대한 다른 색을 쓴다. 같은 전기적 노드는 다른 위치의 점도 같은 색이며, 모든 인접 노드를 반대색으로 만드는 그래프 채색을 강제하지 않는다. 접지 표기·도선·소자/제어원 라벨·전류 화살표/라벨·본문 수식의 색은 이 노드 색 규칙으로 바꾸지 않는다. 색 없이도 노드 이름과 극성으로 구분되어야 한다. SVG에는 대응 노드 식별자와 색을 명시하고, HTML 테마와 PDF에서 실제 계산된 색이 파랑/빨강인지 확인한다. PDF의 문항 종류별 초록/주황 `--kind`를 노드 파랑의 대체값으로 사용하지 않는다. 풀이 본문의 모든 SVG와 MD에 참조된 같은 그림, 라이트·다크 HTML 및 실제 답안 PDF에서 접지 점 생략·가까운 라벨·점/전압 색 일치를 검토한다.
- 출력저항 표시/검산 경계: $R_{out}$은 처음부터 유효한 근사식으로 시작하고 조건과 $\approx$를 유지한다. 이 규칙은 생성하는 풀이 본문(start/solve/verify·formal/보충 포함) HTML·요약·동반 MD·답안 PDF 모두에 적용한다. 정확식 → 근사식 유도나 정확식과 수치 비교를 학습 본문에 추가하지 않는다. 정확한 $R_{out}$의 전체 모델·유도·수치/극한 대조는 내부 독립 검산 evidence에만 둔다. 원문이 정확식·유한 β 전체 결과 또는 수업 기본 큰 곱 근사와 반대인 조건·수치를 명시하면 예외 이유를 짧게 밝히고 필요한 모델과 결과를 제시한다. 유한 β 또는 $r_o$가 있다는 사실만으로 예외를 선언하지 않는다. 이 제한은 $R_{out}$에 한정하며 다른 개념의 필요한 상세 유도를 줄이지 않는다.
- 모든 조각이 모이면 `explanations/`의 파일 집합이 `source.json`의 문항 id 집합과 같은지 확인한다.

### 4. 독립 검산 (작성자와 다른 에이전트)
- 문항마다 검산 에이전트 1명(opus, 병렬)을 띄운다. 그 문항의 작성자를 재사용하지 않는다.
- [검토 기록](references/verification.md)의 `independent` 절을 따른다. 조건과 구할 것만으로 먼저 답을 구하고(SymPy 기호 계산 + 수치 대입, 증명·정성 문항은 논증 검토), 그 뒤에 md `## 풀이`와 조각의 답과 대조한다.
- 산출: SymPy 스크립트 `BUCKET/evidence/pN-sympy.py`와 실행 출력 `BUCKET/evidence/pN-result.txt`, 그리고 소문항별 판정(JSON 형태로 응답: `pN:a` → status/method/conclusion/evidence).
- 조각 답이 틀렸으면 그 작성자에게 고치게 하고 같은 검산을 다시 한다. md `## 풀이`와 독립 검산이 다르면(조각을 어느 쪽에 맞춰도 해소되지 않음) 그 팩을 disputed로 표시한다. 다른 팩은 계속한다.
- evidence는 build가 stage로 복사하므로 **build 전에** 모두 써 둔다.

### 5. build·check
```bash
python3 "$SKILL/scripts/epe_cli.py" build --run "$RUN"
python3 "$SKILL/scripts/epe_cli.py" check --run "$RUN"
```
- build는 `BUCKET/stage/<id>/`에 발행 위치와 같은 구조로 `문제설명_<range>_<slug>.html`과 `.assets/`의 `문제설명_<range>_<slug>.md`, `figures_…/`, `자료_…/`를 만들고 `BUCKET/stage.json`, `BUCKET/review.json`(모든 검토 `not_run`, `artifact_hashes` 포함)을 새로 쓴다. **다시 build하면 review.json이 초기화되므로 검토 기록은 마지막 build 뒤에 쓴다.**
- check는 `BUCKET/machine.json`을 쓰고 `check: machine PASS (수학·화면 검토는 별도)`를 출력해야 한다. 실패 메시지(구역·소문항·수식 구분자·자원·해시)는 담당 작성자에게 되돌리고, 고친 뒤 build부터 다시 한다. 최대 2회, 그래도 남으면 그 팩을 withheld로 보고한다.

### 6. 검토 기록
[검토 기록](references/verification.md)을 읽고 네 검토와 `learning_style_audit`의 모든 소문항·규칙 감사를 실제로 수행해 `BUCKET/review.json`에 기록한다.
- `source_visual`: `workbook/source_pages.py render`로 원본 쪽을 렌더해 문항 조건·그림·소문항과 대조.
- `content`: 필수 읽기 `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md` 절대 경로와 `source.json.learning_style`을 브리프에 넣는다. 일곱 구역 순서·`이렇게 풀어요` 제목·식별 행 분리와 본문·요약·MD의 답·단위·근사·그림을 대조하고 `learning_style_audit`를 작성한다. 작성자가 아닌 리뷰어 에이전트(opus) 1명이 팩의 모든 조각을 읽고 소문항별로 판정.
- `independent`: 4의 판정을 그대로 옮긴다(evidence 경로는 stage에 복사된 `evidence/`와 같은 이름).
- `browser`: 메인 에이전트가 stage 폴더를 `python3 -m http.server`로 열고(몇 초 뒤 측정), 네 조합 측정은 헤드리스 Playwright [scripts/epe_browser_check.py](scripts/epe_browser_check.py)로 해요(`playwright`·chromium 필요). 내장 브라우저 창은 목차·pager·테마 토글을 눌러 보는 확인에만 쓰고, 그 페이지의 `document.visibilityState`가 `'visible'`일 때만 결과로 써요. `ERR_CONNECTION_RESET` 같은 연결 끊김은 fail이 아니라 다시 실행해요. evidence에 어느 경로로 확인했는지 적어요.
- `references`: 실제로 읽은 저장소 자료의 절대 경로와 SHA-256.
- 내용·화면 결함은 담당 작성자에게 모아서 한 번에 되돌리고, 고친 뒤 5부터 다시 한다(네 검토 모두 다시). 최대 2회.

### 7. publish
```bash
python3 "$SKILL/scripts/epe_cli.py" publish --run "$RUN"
```
- 네 검토와 전체 `learning_style_audit`가 실제 `pass`이고 입력·조각·참조·산출 해시가 그대로일 때만 발행된다. 하나라도 `not_run`·`fail`·`disputed`이거나 해시가 바뀌면 그 팩은 보류된다. 다른 팩은 독립으로 발행된다.
- 발행은 설명 소유 파일만 `복습노트/<range>/`로 교체하고, 기존 파일은 `BUCKET/backups/`에 백업하며, 실패하면 복구한다. 출력의 `publish: … backup: …` 줄을 보고에 쓴다.
- `answer-overlay.json`은 자료 폴더에 발행되고 같은 폴더 `validation.json`이 이를 승인한다. 자식은 PDF를 직접 교체하지 않는다. 부모가 이 overlay로 RUN 안의 답안을 빌드·렌더 검토한 후 `publish_answer.py`로 교체한다. 단독 호출의 PDF는 기존 파일을 유지한다.
- 사용자 호출 범위 안이므로 발행 전에 다시 묻지 않는다.

### 8. 보고
부모 호출이면 아래 RUN·팩별 상태·문항/소문항 수·파일 또는 stage·백업·disputed·보류 이유를 부모에 반환하고 별도 최종 보고로 끝내지 않는다. 단독 호출은 다음 형식으로 끝낸다.
```
## 문제설명 <target> 완료
- RUN: <RUN>
- <range> (<slug>): published | withheld — <보류 이유>
  - 문항 N개 / 소문항 M개 (main 포함)
  - HTML: 복습노트/<range>/문제설명_<range>_<slug>.html
  - MD: 복습노트/<range>/.assets/문제설명_<range>_<slug>.md
  - 백업: <RUN>/review-<range>-<slug>/backups
  - disputed: <pN(workbook id): md 풀이 값 vs 독립 검산 값> (없으면 "없음")
- 커밋 제안: git add 복습노트/<range>/문제설명_<range>_<slug>.html 복습노트/<range>/.assets && git commit -m "docs(notes): add problem explanations <range>"
```
withheld 팩은 HTML·MD 줄 대신 stage 경로를 적는다.

## 산출 위치

`복습노트/<range>/` 아래:
- `문제설명_<range>_<slug>.html` (`slug`는 같은 폴더 `정리노트_<range>_<slug>.html`의 것)
- `.assets/문제설명_<range>_<slug>.md`: 링크는 `../`로 팩 폴더를 가리킨다
- `.assets/figures_문제설명_<range>_<slug>/`: 문제·설명 그림 복사본
- `.assets/자료_문제설명_<range>_<slug>/`: manifest, 조각, evidence, `answer-overlay.json`, 로컬 KaTeX·Pretendard, `validation.json`(발행 당시 review.json)

읽음 상태는 원 정리노트와 다른 `ec2-problem-explain-review-<range>-<slug>` 키로 저장된다.

## 오류 처리
| 상황 | 동작 |
|---|---|
| 저장소가 아님 | 알리고 멈춤 |
| 대상 없음·문제 없는 팩·여러 후보 | extract 메시지와 후보 경로를 보여 주고 멈춤 |
| extract의 `문항 <id>: …`(소문항 표지 중복·md 없음·그림 없음) | 그 팩만 withheld. 메시지와 md 경로를 보고하고 md는 고치지 않음 |
| `RUN은 비어 있어야 해요` | 새 실행ID로 RUN을 다시 정함 |
| `추출 데이터 또는 원본 변경` | 원본이 실행 중 바뀜. 새 RUN으로 extract부터 다시 |
| check 실패 2회 | 그 팩 withheld, 이유 보고 |
| 독립 검산과 md `## 풀이` 불일치 | 그 팩 disputed(발행 보류), md는 고치지 않음 |
| `발행 보류: …` / `검토 후 생성 파일 변경` / `참조 자료 변경` | 원인을 고쳐 build부터 다시 검토. 안 되면 withheld |
| SymPy 설치 실패 | 수치 대입만으로 검산하고 method와 evidence에 그 사실을 적음 |
| 포트 사용 중 | 다른 빈 포트 사용 |
| `playwright` 없음(epe_browser_check 종료 코드 2) | `pip3 install --user --break-system-packages playwright` 후 `python3 -m playwright install chromium` |
| 화면 측정 중 `ERR_CONNECTION_RESET`(`flaky_rerun`) | 서버 연결 끊김이라 fail로 두지 않고 다시 실행 |


## 공통 업데이트: 대상·화면·검토 기준

- `all`: 기존 복습팩만 끝 날짜 내림차순으로 처리한다. 과제·forecast는 자동 선택하지 않는다. 전자회로2는 `.assets/problems.txt`가 있는 팩만 선택한다. 여러 후보는 명시 경로(전자회로2는 날짜 범위)로 해소하고 새 문제를 출제하지 않는다.
- 화면: 1024px 이상은 목차와 문제 패널이 기본으로 함께 열린다. 저장된 닫힘 선택은 유지한다. 문제 패널은 `문제 | 원문` 탭, 왼쪽·오른쪽 붙이기·띄우기, 이동·크기 조절을 지원한다. 상태 키는 `od-panels:explain:v2:prob`다. 원문 없는 문항은 원문 탭을 숨기고, 모바일은 해설 위 `문제 보기`로 펼친다. 그림 확대와 인쇄 원문 보존도 검토한다.
- 객관식: 입력에 명시된 정답 모델의 보기 ID·순서·정답·mode가 실제 보기와 맞을 때만 클릭 판정·알림·다시 풀기를 제공한다. 모델 없음/불일치는 정적 표시하고 진단한다. 해설 문장이나 보기 위치로 정답 모델을 추측하지 않는다. 전자회로2 workbook 입력은 정적 표시한다.
- 현재 검토 기준은 `review_policy_version="problem-explain-2026-10-21-learning-style"`다. build의 review.json과 manifest에 기록하며, 이전 기준이나 기준 없는 기록은 새 발행을 승인하지 못한다. 기존 발행 HTML의 열람에는 영향을 주지 않는다.

### 레이아웃만 바뀐 기존 발행분 재발행

발행 자료 `.assets/자료_문제설명_<range>_<slug>/`의 fragments·evidence를 새 RUN으로 복사하고 stage만 조립한다. CLI의 rerender는 자동 발행하지 않는다.

```sh
python3 ".claude/skills/ec2-problem-explain/scripts/epe_cli.py" rerender --repo "<저장소 절대경로>" --target 1007 --run "<비어 있는 새 RUN 절대경로>"
```

입력·설명 조각·입력 그림·검산 자료·참조 파일이 검증되고 검토 기준도 현재와 같을 때만 content·independent와 개인화 감사를 재사용한다. 현재 명세 바이트와 snapshot·전체 소문항 감사도 일치해야 한다. 전자회로2는 problems.txt뿐 아니라 문제 MD·그림 전체의 합성 해시가 같아야 한다. 참조 누락·내용 변경·기준 누락/변경이면 content·independent도 not_run으로 되돌리고 실제 검토를 다시 한다. 경로 이전은 실제 대상과 바이트/링크 동등성을 입증할 때만 허용하며, 입증하지 못하면 재검토한다. 원본 HTML의 스타일·실행 스크립트만 바뀐 경우는 과거 입력을 확인할 수 있을 때만 동일 문항으로 인정하고 JSON 정답 데이터는 내용으로 취급한다.

`check` 뒤 source_visual·browser를 실제로 다시 확인한다. 검토 기준이 바뀐 이번 업데이트의 옛 발행분은 내용 검토·독립 검산도 새로 필요하다. 네 검토가 모두 pass인 뒤에만 별도 publish 절차를 사용한다. 사용자가 stage까지만 요청했다면 publish를 실행하지 않는다. 새로 해설을 저작해야 하면 기존 정상 저작 절차로 돌아간다.

## 본문과 페이지 요약의 계약

요약은 본문의 핵심 개념·작동 원리·성립 조건·혼동 구분을 압축하며 항목 수의 고정 상한을 두지 않는다. 본문에 없는 사실을 요약에만 추가하지 않고 보충의 범위·출처·불확실성을 유지한다. 긴 회로식은 패널 폭 안에서 읽히도록 여러 수식 줄로 나눈다. 중앙 제목과 고정 패널 제목은 유지하며 우측 중복 주제·문항 제목은 출력하지 않는다. `sum-for`는 `.sums` 컨테이너의 유일한 ID로 보존하고 제목 대입 JS를 만들지 않는다. 문제·보기·정답·해설·원문 탭·앵커·저장 키는 보존한다.

모든 학습 토픽에 대해 자료·토픽별 일반·강조·주의·보충의 서로 다른 핵심을 별도 행으로 감사한다. 본문 주장·대응 요약 문장·판정/생략 이유와 `pass | unresolved`를 기록하고 보완 뒤 실제 요약을 다시 읽는다. 기존 동반 MD와 재생성 원고를 동기화하되 없는 MD 형식을 만들지 않는다. 검증 JSON은 `{schema_version:1, html, html_sha256, audit_path, audit_sha256, semantic_status, browser_status, evidence, unresolved}`이며 실제 검사 뒤에만 상태를 갱신한다. 파일 해시 변경 후 기존 증거는 갱신 전까지 오래된 근거다.


**수치 표시:** 계산 결과는 소수점 둘째 자리까지 반올림해 표시한다. 정수·짧은 소수에 불필요한 0이나 말줄임표를 붙이지 않는다. 내부 계산은 반올림 전 정밀도를 유지하고, 반올림한 결과는 등호 대신 근사 기호로 구별한다. 간단한 분수·근호는 유지할 수 있으며 원문 입력값·요구 정밀도는 보존한다.
