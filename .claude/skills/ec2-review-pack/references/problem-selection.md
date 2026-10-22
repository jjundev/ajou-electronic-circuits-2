# 복습문제 선별 규칙 (메인 에이전트)

복습문제는 **workbook에 이미 있는 문항 전체를 고르기만** 한다. 자작·변형·일부 소문항 절취는 하지 않는다. 시험 대비를 위해 **기출 우선, 최대 20문항, 참고 풀이 유무와 무관하게 선발**한다. 다른 회차에서 사용한 문항은 항상 제외하며 선행 문제·핵심 기출에도 예외가 없다. 같은 회차 재생성만 자기 이력에서 제외한다. 원문·그림이 불명확하거나 독립 검산이 끝나지 않은 문항은 최종 발행하지 않는다.

새 실행은 manifest에 `"selection_policy": "exam-first-v2"`를 선언한다. 과거 정책이 없는 manifest/팩은 계속 읽을 수 있지만 새 생성에서 생략해 검증을 우회하지 않는다. 아래는 공통 선발 명세이며 해설 저작·독립 검산·발행은 ec2-problem-explain의 기존 게이트를 따른다.

## 1. 후보 목록
```bash
python3 <SKILL>/scripts/problem_index.py --repo <REPO> --used <REPO>/복습노트 --exclude-range <range> --chapters <이번 범위 장, 예: 9,10> --format json --catalog-out <RUN>/exam-catalog > <RUN>/candidates.json
```
- JSON schema v2의 `problems`에는 교과서의 기존 절/난이도 정보와 기출의 `selection`(주제·필요 개념·학습 목표·분류 근거/상태), `subparts`, `depends_on`, `detail_path`가 있다. 기출의 `detail_path`는 `catalog_root` 기준이다. `reference_solution`은 `none | answer_only | solution`, `used_in_ranges`는 이번 회차를 제외한 사용 회차 목록이다. 풀이 상태는 우선순위나 범위·정답 승인 근거가 아니다.
- 상세 JSON은 원본 MD 전체·구획별 본문·exam.yaml·원본/다시 그린 그림 경로를 보존한다. 그림 경로와 `md_path`는 REPO 기준이다. JSON은 출력용 workbook JSON과 다른 선별 자료다.
- 기본 TSV 인터페이스도 유지한다(`--format`을 생략). 새 복습팩은 JSON을 사용한다.
- `--exclude-range <range>`: 이번 range를 다시 돌릴 때, 이번 range 자신의 이전 `.assets/problems.txt`가 USED로 잡혀 같은 문제를 다시 못 고르는 일을 막는다.
- 종료 코드 1이면 stderr의 `ERROR` md는 후보에서 빠진 것이다. 보고서 "미해결"에 적는다(md는 고치지 않는다).
- `used: true`인 id는 이전 팩(이번 range 제외)에서 썼으므로 고르지 않는다. 전제 문항도 사용 이력과 범위를 확인한다.
- `## 풀이`가 없는 기출·교과서 문항도 후보에 포함한다. 원문을 직접 읽고 풀며, 문제은행 원본에 임시 풀이를 써넣지 않는다. 카탈로그 `eligible`은 원문 파싱/그림 확인을 통과했다는 뜻이며 수업 적합성·정답 검증을 뜻하지 않는다.
- 저장된 `from_the_past/json`은 전체 기출 보관본이며 매 실행에 신뢰하지 않는다. 후보 명령은 최신 MD로 RUN 카탈로그를 생성한다. 파싱·그림·중복 ID·의존성 오류가 있으면 고치거나 보고하고 기출 선별을 중단한다. 손상된 카탈로그를 정상 후보로 사용하지 않는다. 복습팩 실행 중 저장소 원본이나 저장 JSON을 갱신하지 않는다.

## 2. 범위 맞추기
- 요약의 `## 교과서 절 대조`에서 "다룸"인 절 번호 집합과 그날 연습할 학습 목표를 만든다(예: `{9.1.1, 9.1.2}`, 반회로 구성·출력저항 계산). 잠깐 언급한 개념과 배운 풀이 방법을 구분한다.
- 교과서 문제: `secnum`이 그 집합의 절이거나 그 하위 절(9.1.2 → 9.1.2.x)인 것만 후보다. `secnum`이 `10.2`처럼 상위 절이면 제목과 원문을 읽고 다룬 내용만으로 풀리는지 판단한다.
- `Design Problems`: 도전 문제로 최대 1개. 원문을 읽고 다룬 절만으로 풀리는 것만.
- 기출: 관련 장 → 전역 `selection.required_concepts`와 소문항별 필요 개념 → 의존성·사용 이력 순으로 좁힌다. 소문항 태그는 비망라적이므로 전역 개념과 함께 읽는다. 그 뒤 상세 JSON의 **원문·조건·구할 것·회로 설명·실제 그림·참고 풀이(있으면)**를 읽고 모든 소문항이 배운 내용만으로 풀리는지 확인한다. 풀이가 없으면 직접 풀어 요구 개념을 판단한다.
- `selection.status`는 `unclassified | draft | reviewed | stale`다. 초안/누락/오래된 분류는 힌트일 뿐 범위 일치 증거가 아니다. reviewed도 현재 수업 범위 적합성이나 정답 검산을 승인한 뜻이 아니다. 분류가 없다는 이유만으로 좋은 문제를 누락시키지 않는다.
- 수업에서 안 다룬 개념(예: 아직 안 배운 주파수 응답, 피드백)이 소문항 하나라도 필요하면 문항 전체를 `deferred`로 보류하고 `missing_concepts`를 기록한다. 이후 회차 생성 시 이전 팩의 `.pack/selection-review.json` 보류 목록을 다시 확인하되 이미 다른 회차에 수록됐다면 항상 제외한다.
- `forbidden_outside_preview` 용어가 핵심인 문제는 제외.

## 3. 기출 우선 구성
- **최대 20문항(선행 문항 포함), 최소 수와 종류별 할당량 없음.** 20개를 억지로 채우지 않는다. 적합한 후보가 0개면 `problems: []`, PDF 없음과 이유를 보고한다.
- 먼저 범위가 맞고 미사용인 기출 전체를 검토한다. 같은 교수·과목(확인된 출처만) → 강의 강조점/요구 풀이 수준 → 다른 유형의 학습 가치 순으로 판단한다. 최신 연도는 동등한 후보 사이에서 참고한다. 근거 없이 빈출/예상 적중이라고 부르지 않는다.
- 기출이 과반 또는 전부여도 좋다. 교과서 예제·연습·장말문제는 빠진 핵심 목표, 기출 전의 기초 연습, 다른 사고 과정, 선행 문제를 보완할 때 넣는다. 각 교과서 문항의 `why`에 보완하는 역할을 명시한다.
- 난이도 개수 비율을 고정하지 않고 핵심 학습 목표와 시험 수준을 우선한다. 절마다 기계적으로 한 문항을 넣지 않는다. 미충족 목표는 coverage에 이유를 남긴다.
- `priority: core`(핵심)와 `extra`(추가 연습)를 구분한다. 핵심만 풀어도 주요 학습 목표를 다루게 하며 핵심의 선행 문제도 핵심이다. `estimated_minutes`는 예상 분(추정), `subpart_count`는 원문 소문항 묶음 수다. 원문이 (a)–(c)를 한 요구문으로 묶었으면 자동 개수는 1묶음일 수 있으므로 보고에서 실제 요구량도 확인한다. 시간·수만으로 학습량이 정확하다고 주장하지 않는다.
- 순서: 수업 개념 흐름과 전제 관계 → 같은 유형 안 기본에서 종합. 선발 우선순위와 출력 순서는 다르므로 기출을 반드시 맨 앞에 몰지 않는다.
- 앞 문제를 전제로 하는 문제(`depends_on`, "Repeat Problem …", "위의 결과", "예제 N.M 변형")는 전제와 함께 넣거나 둘 다 뺀다. 전제가 다른 회차에서 사용됐다면 둘 다 제외한다. 전제가 이미 풀렸다는 이유로 재수록하거나 생략하지 않는다.
- 같은 개념의 식 유도·수치 계산·설계 역산·조건 변경은 다른 연습일 수 있다. 숫자만 바뀌고 풀이가 같으면 대표 하나를 남긴다.
- 이번 range의 수업이 전부 전자회로1 복습(Lec1–2)이면 workbook(9~11장) 범위 밖이므로 0개가 정상이다.

## 4. manifest에 적기
각 문제를 `{id, kind, anchor, date, why, priority, learning_goals, estimated_minutes}`로 적는다(`references/manifest-guide.md`). `why`는 무엇을 연습하며 왜 기출/다른 후보 대신 선택했는지 한 줄. 기출 개수나 풀이 보유 여부를 맞추기 위한 이유는 쓰지 않는다.

`RUN/selection-review.json`을 먼저 작성한다. `policy: exam-first-v2`, 현재 `catalog_sha256`, 다음 배열을 갖는다.
- `candidates`: 선택 문항과 **범위 장의 미사용 기출 전체**의 `{id, disposition: selected|excluded|deferred, scope: in_scope|out_of_scope|unclear, reason}`. deferred에는 `missing_concepts: [미학습 개념]` 필수. selected는 전체 소문항 in_scope여야 한다. 교과서의 유력 탈락 후보도 남긴다. 분류만 읽고 실제 검토한 것처럼 기록하지 않는다.
- `coverage`: `{goal, problem_ids: [선발 ID], gap_reason?: 이유}`. 문항 `learning_goals`와 정확히 연결한다. 핵심 문제로 다루지 못한 목표는 gap_reason을 기록한다.
- `cross_pack_review`: 보고용 객체로 `{missing_types: [...], repeated_types: [...], deferred_ids: [...]}`. 다른 팩의 목록/선발 검토를 읽고 전체 시험 범위의 빈틈·다른 ID 사이 유형 반복·보류 기출을 확인한다. 검토할 자료가 없으면 그 한계를 보고하며 다른 팩을 자동 수정하지 않는다.

문제가 1개 이상이면 확정 뒤 **처음 후보와 같은 `--chapters`, `--used`, `--exclude-range`**로 실행해 선택 근거·카탈로그/내용 해시·전체 소문항·의존성을 기록한다. 이 명령은 AI의 실제 범위 검토를 대신하지 않는다. 문제 0개이면 생략한다.
```bash
python3 <SKILL>/scripts/problem_index.py --repo <REPO> --used <REPO>/복습노트 --exclude-range <range> --chapters <장> --format json --catalog-out <RUN>/exam-catalog --candidates-input <RUN>/candidates.json --selection-manifest <RUN>/manifest.json --selection-review <RUN>/selection-review.json --selection-out <RUN>/selection.json > <RUN>/selection-candidates.json
```
- 원본·후보·사용 이력이 달라지면 기록을 거부한다. `candidates.json`을 새로 만들고 내용을 다시 검토한다. 입력 `candidates.json`에 stdout을 덮어쓰지 않는다.
- 후보 외/USED/중복 ID, 일부 소문항 선택, 전제 누락·역순을 거부한다. 순환 의존성은 어떤 순서도 통과하지 못한다.
- PDF 빌드 전 manifest와 selection.json의 ID·순서를 대조한다. 선별을 바꾸면 기록도 다시 만든다.
- selection v2에는 원문/카탈로그 해시·검토 기록·각 문항 핵심/추가·학습 목표·소문항 수·풀이 상태·예상 시간과 총량이 저장된다. 범위·기출 우선의 의미 판단은 사람이 읽을 수 있는 이유와 에이전트 검토가 담당하며 자동 최적 선발/정답 승인으로 해석하지 않는다.
- 조립기는 `RUN/selection.json`을 `.assets/selection.json`에, 검토 기록을 `.pack/selection-review.json`에 보존한다. 새 팩의 설명 로더는 selection.json을 원본 입력 해시에 포함한다. 문제지 빌드에 `--selection <팩>/.assets/selection.json`을 전달한다. 답안은 승인된 overlay에 묶인 같은 파일을 자동 사용하며 승인 뒤 메타데이터를 바꾸면 재검토한다. 핵심/추가·소문항 묶음 수·예상 시간은 선발 JSON에 유지하되 해설 HTML·동반 MD에는 학습량 행을 출력하지 않는다. PDF 표시는 기존 PDF 정책을 따른다.

## 4.1 참고 풀이 없는 문항의 검증
- 후보 자격과 최종 발행 자격을 구분한다. 작성자는 원문에서 직접 풀고 독립 검토자는 작성자의 결과를 보기 전에 원문/그림에서 따로 푼다. 회로 연결·극성·출력 정의·근사 조건 및 식·수치·단위·극한 조건을 대조한다.
- 답이 일치하지 않으면 원인을 해결하고 재검토한다. 무해설 자체가 disputed는 아니다. 원문 모호/해결 불가/검증 미완료면 withheld로 보고한다. 필요하면 같은 목표의 차순위 후보를 선발하고 목록·원본 snapshot·해설 검토를 정상 절차로 새로 수행한다.
- 참고 풀이 있는 문항도 동일하게 검산한다. SymPy나 같은 식의 수치 재대입만으로 독립 풀이를 대신하지 않는다. 원문 MD에 임시 풀이를 추가하거나 기존 발행 승인 값을 재사용하지 않는다.

## 5. 문제지 먼저 만들기 (4단계 조립에서)
```bash
python3 <REPO>/workbook/build_workbook.py --ids <id1,id2,…(manifest 순서)> --name 복습문제_<range>_<slug> \
  --mode problems --layout video-16x9 --pdf-dir <REPO>/복습노트/<range> --build-dir <RUN>/workbook-build
```
- 초기 결과는 `복습노트/<range>/복습문제_<range>_<slug>-문제.pdf` 하나다. 답안은 자식의 새 핵심 풀이·네 검토·개인화 감사·publish 후 발행된 overlay에서 부모가 만든다. [부모 통합 계약](problem-explain-integration.md)의 답안 제작·렌더 검토·원자적 교체 순서를 따른다. 원본 MD의 참고 풀이로 답안을 선행 제작하지 않는다.
- stderr 줄로 원인을 구분한다.
  - `ERROR <md 경로>: …`(문제 md 자체 오류, 종료 코드 2): 그 id를 후보에서 같은 절의 다른 문제로 바꿔 manifest를 고치고 한 번만 다시 만든다. 또 실패하면 그 id를 빼고 "미해결"로 보고한다.
  - `ERROR <name>: …`(렌더링·Chrome·네트워크 오류, 종료 코드 1): md 문제가 아니므로 id를 바꾸지 않는다. "미해결"로 보고한다.
  - `OVERFLOW <파일>: <id>`(종료 코드 1): PDF는 남는다. 그 문제 쪽이 넘친 것이므로 id를 바꾸지 않고 "미해결"로 보고한다(workbook md 수정은 이 스킬의 일이 아니다).
- 인터넷이 필요하다(Pretendard, KaTeX CDN).
