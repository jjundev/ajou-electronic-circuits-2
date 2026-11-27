---
name: ec2-problem-explain
description: "전자회로2 복습팩이 이미 고른 workbook 문제(날짜별 복습노트의 .assets/problems.txt)마다 회로의 위치 표시와 첫 판단·핵심 식·최종 답을 연결한 간략한 문제설명 HTML과 MD를 만들고, 원문 대조·내용·독립 검산·브라우저 검토를 통과한 뒤에만 복습노트에 발행한다. \"문제설명\", \"복습문제 풀이 설명\", \"1007 문제 풀이 설명해줘\"처럼 요청하거나 /ec2-problem-explain [MMDD|MMDD-MMDD]로 부를 때 사용한다. 새 출제·정리노트·PDF·영상은 별도 스킬(ec2-review-pack 등)이다."
---

# 전자회로2 문제풀이 설명

회로에서 내릴 판단 → 종이에 쓸 첫 식 → 답을 얻는 데 필요한 중간식 → 소문항별 답 순으로 쓴다. 10월 중순까지의 중간고사 범위는 익숙한 공식과 계산을 전제로 하고, 이후에도 처음 나오는 판단이나 풀이가 갈리는 단계에만 이유를 한두 문장 붙인다. 문장을 빼면 첫 식을 쓰기 어렵거나 흔한 오답을 피하기 어려운지 기준으로 덜어낸다. 문제 조건이나 그림을 글로 다시 설명하는 문장, 익숙한 공식 정의, 반복 대입·약분은 줄인다. 답이 달라지는 모델·근사·부호는 해당 식 곁에 남기고 답은 한 번 쓴다. 검산을 넣을 때는 이 문항에서 오답을 가려내는 하나를 고른다. 원문 전제와 추가 가정을 구분하며 독립 검산은 모든 소문항에 수행한다.

회로가 풀이 판단에 필요한 문항은 정리노트의 `figure.circuit`와 공용 스타일을 재사용한다. 같은 회로 상태의 SVG를 우선 가져오고, 필요한 연결·측정 상태가 달라진 경우에 해당 회로/가지를 그린다. 그림의 ㉠·㉡·㉢(`fig-loc`)을 해당 첫 식 바로 앞 본문의 같은 기호(`loc`)와 연결한다. 회로는 계산을 읽는 동안 가운데 본문 상단에 고정되며 짧은 화면(높이 500px 미만)과 인쇄에서는 본문 흐름에 놓인다. 적용 형식은 [저작 규칙](references/authoring.md)을 따른다. 중간에 사용자에게 묻지 않고 끝에 한 번 보고한다. 커밋은 제안만 한다.

**한 행에 하나의 식:** 독립된 계산 대상은 각각 별도 display 블록/MD 줄/PDF 행에 쓴다. 서로 다른 $g_m$, $r_\pi$, $r_o$ 계산을 쉼표·\quad·\qquad로 한 줄에 묶지 않는다. 같은 양의 `식 = 대입 = 결과` 연속 등식과 실제 같은 값을 가진 소자의 등식 묶음은 유지할 수 있으며, 폭을 넘으면 단계별로 세로로 나눈다. 설명문의 짧은 기호·조건은 인라인으로 쓸 수 있다.

**같은 회로량에는 한 기호:** 계산 경로에서 이미 이름을 붙인 양은 이후 식과 요약에서도 그 기호를 쓴다. 예를 들어 $R_C\parallel(R_1+R_2)$ 전체가 $R_{\mathrm{out,open}}$이면 $R_L$을 추가하지 않고 개루프 출력저항으로 한 번 적는다. 근사식으로 얻었으면 계산한 첫 줄에 $\approx$를 표시한다. 실제로 별도 부하나 다른 측정 조건의 저항을 뜻하는 기호와 원문 지정 기호는 해당 의미를 유지한다. 내용 검토에서 새로 정의한 기호마다 독립된 회로량을 가리키는지 확인한다.

**기본 근사와 회로 표기:** 공통 `solution-style.md`의 수업 기본 근사를 적용한다. $g_mr_o\gg1$, $g_mR_e\gg1$의 주항을 쓰고 캐스코드의 곱 인자 소자를 밝힌다. 내부 $r_e=1/g_m$는 축퇴 저항과 구분하고 유한 $r_\pi$는 보존한다. 생성 SVG는 NOTATION-01의 native text/tspan 실제 첨자(기본 78%)·Pretendard 600 정체로 통일하고 실제 face 사용을 HTML·독립 SVG·PDF에서 검토한다. CM 이득은 성립 조건을 확인한 $2R_{SS}$ 반회로를 본풀이에 앞세우고 테일 저항 유도는 보충으로 분리한다. 부하 불일치·거울 결합·원문 지정 방법의 예외는 PROFILE CIRCUIT-02를 따른다.

**이득의 계산 순서:** PROFILE GAIN-01에 따라 단별 로딩을 포함한 연쇄 곱이 성립하는지 판단한다. 성립하면 목표 전달비를 중간 노드 기준의 곱으로 먼저 쓰고 각 항을 채운다. 귀환 문항은 포트 역할과 복제 종단부터 읽고, 바로 읽히는 재사용 저항을 항 계산 전에 둔다. 병렬 전류 입력이 노턴 등가로 분리되면 $v_{\mathrm{Th}}=I_{in}R_p$로 놓고 $R_p$에 테브난 전압 기준 이득을 곱한다. 실제 입력 노드까지의 분압은 그 이득에 포함하고 $R_{in,\mathrm{open}}$은 별도로 구한다. 귀환율의 측정 조건과 기준 방향은 해당 식 앞에 놓는다. $G_m$·$R_{out}$ 경로의 적용 조건과 저작 표지는 [저작 규칙](references/authoring.md#전압이득의-계산-순서)을 따른다.

**전압 이득에서 부하 전류 계산:** 원문이 방법을 지정하지 않고 부하 양단의 전압 이득을 바로 구할 수 있으면, 적용한 전압 이득 공식을 먼저 보인 뒤 같은 부하 저항으로 나눈다. 직렬 가지라면 가지 전체의 전압과 저항을 사용한다. 단별 이득은 부호가 포함된 노드 전압비로 쓰고, 회로 연결이 드러나는 병렬저항을 이득식에 유지한다. 이득에 필요하지 않고 다른 회로 상태에서 구하는 임피던스는 이득 계산 뒤에 둔다. [저작 규칙](references/authoring.md#전압이득의-계산-순서)의 예를 따른다.

**귀환 이득과 레이저 출력저항:** 전체 전달비는 PROFILE NOTATION-01의 $A_{\mathrm{open}}$, $A_{\mathrm{closed}}$와 단위를 사용한다. 시험전압으로 루프 이득을 구할 때는 주입점부터 귀환점까지 부호 있는 노드 전압비를 곱하고, 그 결과를 폐루프 이득의 분모 $1+\cdots$에 직접 넣는다. $K$와 $A_{\mathrm{open}}$을 따로 구한 문항은 분모에 $1+KA_{\mathrm{open}}$을 쓴다. 레이저를 직렬로 감지하는 회로의 출력저항은 [귀환 저작 규칙](references/authoring.md#귀환-이득과-레이저-출력저항)의 부하 조건과 식을 따른다.

**표시 제목:** 대상 팩 `.assets/display-titles.json`의 workbook ID별 짧은 제목을 사용한다. 없다면 검토 전에 선정된 ID 전체의 맵을 작성한다. 값에는 `P<n>.` 접두사나 Fig 번호를 넣지 않고 목차·본문·MD에서 생성기가 붙이는 `P<n>. 짧은 제목`을 사용한다. 원본 문제은행 제목과 출처는 유지한다. 맵 변경은 입력 해시를 바꾸므로 기존 승인을 재사용하지 않는다.

## 원고 형식과 발행

신규 저작은 `div.layer.formal.circuit-explanation[data-explanation="solve"]` 하나에 회로와 소문항별 풀이를 통합한다. 원문의 소문항 순서와 마지막 숨김 요약을 따른다. 새 원고는 단독 CLI와 부모 복습팩에서 같은 형식으로 검사한다.

PDF에 실을 회로·판단·계산·답은 [저작 규칙의 단일 원고 예제](references/authoring.md#간략-해설-원고)대로 본문의 보이는 요소에 `data-answer-step`·`data-answer-final`을 붙여 선택한다. 필요한 고정 회로에는 대상 `data-answer-subpart`를 함께 붙인다. 조립기는 최종 stage DOM에서 `answer-overlay.json`을 추출한다. 네 검토·개인화 감사와 입력·명세·산출 해시를 모두 확인한 뒤 발행한다.

**모델 선택.** 문항 작성자, 독립 검산자, 내용 리뷰어에게는 현재 환경에서 서브에이전트에 지정할 수 있는 모델 중 **가장 높은 등급의 모델**을 사용한다. 부모 복습팩에서의 호출과 단독 실행에 모두 적용한다. 선택 가능한 모델이 하나면 그 모델을 사용한다. 환경이 제공하는 등급 순서를 확인할 수 없으면 환경의 기본 모델을 사용하고 이유를 최종 보고에 적는다.

**진행 표시**: 단계마다 한 줄만 쓴다. 예: `3/8 작성 중: 문항 10개 (병렬)`

## 호출 모드
- 단독 호출은 아래 대상 선택과 최종 보고 형식을 유지한다.
- 부모 `ec2-review-pack` 호출은 부모가 확정한 `range`를 `--target`에 명시한다. 최신 팩 자동 선택을 사용하지 않는다. 부모의 `RUN/problem-explain/<새 실행ID>/` 아래 없거나 비어 있는 폴더를 자식 `RUN`으로 쓴다.
- 병렬 부모 호출은 stage-problem-index 채택 직후 분리된 explain-author·explain-blind 브리프의 봉인 원문으로 시작한다. 담당자 둘은 각자 시도 디렉터리에 결과를 쓰고 부모에게 task_id·attempt·receipt를 반환한다. child-coordinator는 승인된 두 결과로 기존 네 검토를 수행한다. 중단 뒤에는 부모가 해시와 시도를 검증한 결과를 이어받는다. 발행은 부모 publish-pack이 담당한다.
- 레거시 부모 호출도 저작·독립 검산·네 검토·publish를 모두 수행한다. 중간 단계 진행만 표시하고 최종 결과는 부모 보고에 합친다. 보호 대상·CLI 옵션·발행 게이트는 동일하다.

## 대상과 보존

- `1007`: `복습노트/1007/.assets/problems.txt`의 순서대로 전 문항.
- `0923-1002`: 정확히 같은 이름의 통합 폴더가 있으면 그 팩, 없으면 범위 안 날짜별 팩을 각각 처리한다. 팩마다 독립 성공/실패다. 통합 폴더와 개별 폴더가 함께 있으면 후보 경로를 보여 주고 멈춘다.
- 인자 없음: `problems.txt`가 있는 팩 중 폴더명 끝 날짜가 가장 늦은 팩. 같은 끝 날짜 후보가 여럿이면 후보를 보여 주고 멈춘다.
- `problems.txt`가 없는 팩(예: 0902·0904)을 지정하면 "문제 없는 팩"으로 멈춘다. 기출 회차·임의 문제 id·설계과제는 대상이 아니다.

새 문제, 정리노트, PDF, 영상, 자동 채점은 만들지 않는다. 원본(`problems.txt`, 문제 md, 문제 그림, 복습문제 PDF, 정리노트 HTML·MD)은 고치지 않는다. 부모의 공통 선발 명세는 `../ec2-review-pack/references/problem-selection.md`(기출 우선 최대 20개, 다른 회차 사용 문항 항상 제외)다. 참고 풀이가 없어도 원문에서 직접 풀고 독립 검산한다. 없음 자체는 disputed가 아니다. md의 `## 풀이`는 참고 답안일 뿐 독립 검산을 대신하지 않는다. md 풀이가 틀렸다고 보이면 고치지 말고 disputed로 보고한다(수정은 `workbook-solution` 몫). 원문이 모호하거나 풀이 불일치가 해결되지 않으면 withheld로 부모에 보고하며 임의로 문제를 바꾸지 않는다. 문항별 실험 링크는 문제설명의 해당 풀이 단계에만 넣는다.

## 경로 약속

- `SKILL` = 이 파일이 있는 폴더(`.claude/skills/ec2-problem-explain`)의 절대 경로
- `REPO` = 이 checkout의 저장소 루트 절대 경로
- `PROFILE` = `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md`의 실제 절대 경로. 작성자·내용 리뷰어가 필수로 읽고 `source.json.learning_style` snapshot과 대조한다.
- `RUN` = `<scratchpad>/ec2-problem-explain/<실행ID>` (실행ID 예: `1007-20261013-1530`). 매번 새로 정하며, 없거나 빈 폴더여야 한다.
- `BUCKET` = `RUN/review-<range>-<slug>/` (팩마다 하나, extract가 만든다)
- 셸 상태는 Bash 호출 사이에 이어지지 않는다. 아래 명령의 `$SKILL`, `$RUN`, `$REPO`, `$BUCKET`은 실행할 때마다 실제 절대 경로로 바꿔 쓰거나, 같은 셸 호출에서 `SKILL=…; RUN=…; REPO=…;`로 먼저 설정한다. `RUN=… python3 … "$RUN"`처럼 인자 확장과 같은 명령 앞에 설정하지 않는다. `cd`는 쓰지 않고 파일도 절대 경로로 넘긴다.

CLI는 [scripts/epe_cli.py](scripts/epe_cli.py) 하나이며 `extract`, `build`, `check`, `publish`, `rerender` 및 선택 실험용 `select-lab` 명령이 있다. 설명은 에이전트가 저작한다. CLI만 실행하면 풀이가 자동으로 써지지 않는다.

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
- 새 팩의 `.assets/selection.json`은 ID·순서와 메타데이터를 검증하고 원본 해시에 포함한다. 핵심/추가·소문항 묶음 수·추정 시간은 selection.json에 보관하고 해설 HTML·동반 MD에는 학습량 행을 출력하지 않는다. PDF 표시는 기존 PDF 정책을 따른다. 저작자가 제목이나 원문에 중복 삽입하지 않는다. 참고 풀이가 없는 source의 reference_steps/reference_answer는 빈 값이며 정상 입력이다.
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

[저작 규칙](references/authoring.md)에 따라 회로의 위치와 그곳에서 내린 판단을 첫 식에 연결한다. 판단이 갈리는 단계에 이유를 짧게 붙이고, 문항 고유의 검산이 유용하면 해당 식 옆에 둔다. $R_{out}$은 [출력저항 표시 기준](references/authoring.md#회로-배치와-출력저항-표시-기준)을 따른다. [내용 검토](references/verification.md)에서 리뷰어가 회로와 본문을 보고 첫 식을 재구성하고 본문·요약·MD·그림의 조건·방향·수치를 대조한다.

### 3. 저작 (문항마다 작성자 1명, 병렬)
- 문항마다 작성자 1명을 **한 메시지에서 병렬로** 띄운다. 위 모델 선택 규칙을 적용한다.
- 브리프 필수 슬롯: `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md` 실제 절대 경로, `BUCKET/source.json.learning_style` snapshot, 원문 `subparts` 순서, 간략 `circuit-explanation` 풀이 구역, 회로 위치 표시와 첫 식의 대응, 소문항별 답안 선택 표지, 마지막 sum, 독립 계산 한 행 규칙, 연쇄 곱이면 목표식·재사용 저항·항별 이득 순서와 귀환율의 시험 방향, 규칙별 적용 위치 또는 비적용 이유 보고.
- 브리프에 적을 것: [저작 규칙](references/authoring.md)의 절대 경로를 먼저 읽으라는 지시, `BUCKET/source.json` 경로와 문항 id(`pN`), 그 문항의 `subparts`, 2에서 정한 참고 자료 경로와 쪽, 출력 파일 `BUCKET/explanations/pN.html` 하나(다른 곳에는 쓰지 않는다), 임시 파일은 `RUN/work/pN/`에만.
- 작성자는 원문·조건·구할 것·그림을 다시 쓰지 않는다(조립기가 md에서 붙인다).
- 회로 브리프에는 PROFILE `CIRCUIT-02`와 [저작 규칙의 회로 기준](references/authoring.md#회로-배치와-출력저항-표시-기준)을 연결한다. 계산과 함께 측정 접속, 생략 근거, 노드 관계를 확인한다. 선택할 고정 회로와 대상 소문항도 명시한다.
- 모든 조각이 모이면 `explanations/`의 파일 집합이 `source.json`의 문항 id 집합과 같은지 확인한다.

### 4. 독립 검산 (작성자와 다른 에이전트)
- 문항마다 검산 에이전트 1명을 위 모델 선택 규칙에 따라 병렬로 띄운다. 그 문항의 작성자를 재사용하지 않는다.
- [검토 기록](references/verification.md)의 `independent` 절을 따른다. 조건과 구할 것만으로 먼저 답을 구하고(SymPy 기호 계산 + 수치 대입, 증명·정성 문항은 논증 검토), 그 뒤에 md `## 풀이`와 조각의 답과 대조한다.
- 검산자에게 전달할 입력과 브리프의 참조는 문제·그림·필요한 이론만 포함하는지 먼저 확인한다. 정답·참고 풀이·설명 조각과 정답 필드가 있는 전체 `source.json`은 전달하지 않는다. 독립 풀이와 evidence를 먼저 저장한 뒤 조정자가 참고 답과 대조한다. 풀이를 저장하기 전에 답이나 풀이가 노출되면 해당 검산 판정과 evidence는 무효다. 노출 사실을 기존 보고에 기록하고, 답을 보지 않은 새 검산자가 처음부터 다시 풀어 정식 evidence를 제출한다. 새 검산자를 확보하지 못하면 독립 검산은 미완료로 두고 발행을 보류한다.
- 산출: SymPy 스크립트 `BUCKET/evidence/pN-sympy.py`와 실행 출력 `BUCKET/evidence/pN-result.txt`, 그리고 소문항별 판정(JSON 형태로 응답: `pN:a` → status/method/conclusion/evidence).
- 조각 답이 틀렸으면 그 작성자에게 고치게 하고 같은 검산을 다시 한다. md `## 풀이`와 독립 검산이 다르면(조각을 어느 쪽에 맞춰도 해소되지 않음) 그 팩을 disputed로 표시한다. 다른 팩은 계속한다.
- evidence는 build가 stage로 복사하므로 **build 전에** 모두 써 둔다.

### 4a. 새 팩의 문항별 회로 실험 (선택)
부모가 새로 작성하는 팩이면 별도 요청 없이 [문항별 회로 실험](references/problem-labs.md)의 선정 절차를 적용한다. 조정자가 채택한 해설과 독립 풀이를 대조한 뒤 후보를 고른다. 적합 후보가 있을 때만 팩당 한 개까지 `ec2-interactive`의 문항 모드를 실행한다. 기존 팩은 명시한 문항의 연결 요청과 기존 연결의 검증된 rerender를 지원한다.
```bash
python3 "$SKILL/scripts/epe_cli.py" select-lab --run "$RUN"
```

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
- `content`: 필수 읽기 `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md` 절대 경로와 `source.json.learning_style`을 브리프에 넣는다. 회로 위치와 첫 식의 대응·한 행에 하나의 식·같은 회로량의 기호 일관성·설명의 간결함과 본문·요약·MD의 답·단위·근사·그림을 대조하고 `learning_style_audit`를 작성한다. 위 모델 선택 규칙을 적용한 별도 리뷰어 1명이 팩의 모든 조각을 읽고 소문항별로 판정한다.
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
- `.assets/자료_문제설명_<range>_<slug>/`: manifest, 조각, evidence, `answer-overlay.json`, `validation.json`(발행 당시 review.json)

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

### 기존 발행분 재렌더링

발행 자료 `.assets/자료_문제설명_<range>_<slug>/`의 manifest와 산출 파일 해시를 확인한 뒤, 조각과 evidence를 새 RUN으로 복사해 stage를 조립한다. 일곱 구역 발행 조각은 이 경로에서 읽는다.

```sh
python3 ".claude/skills/ec2-problem-explain/scripts/epe_cli.py" rerender --repo "<저장소 절대경로>" --target 1007 --run "<비어 있는 새 RUN 절대경로>"
```

`check`와 `publish`도 원래 발행 manifest와 조각의 일치를 다시 확인한다. 발행 자료가 없거나 변경된 조각을 쓰려면 일반 저작 절차로 돌아간다. 재렌더링은 stage까지만 만든다. [재렌더링 검토 계약](references/verification.md#기존-발행분의-재렌더링-검토)에 따라 source_visual·browser를 다시 수행하고, 복사하지 못한 검토도 다시 한다. 네 검토가 모두 통과하면 사용자가 요청한 범위에 따라 별도로 발행한다.

## 본문과 페이지 요약

[페이지 요약 규칙](references/authoring.md#페이지-요약)에 따라 본문과 요약의 핵심과 조건을 맞춘다. 반올림 표시와 긴 식은 [수식과 여백](references/authoring.md#수식과-여백)을 따른다. [화면 검토](references/verification.md#browser-화면-검토-메인-에이전트)에서 중앙 제목·고정 요약 패널 제목·유일한 `.sums#sum-for`와 문제·원문 탭·앵커·저장 키를 확인한다.
