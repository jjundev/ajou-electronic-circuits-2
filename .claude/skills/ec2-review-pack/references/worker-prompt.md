# 작업자 지시문 템플릿

메인은 `task claim` 응답의 attempt와 brief로 아래 자리표시자를 채워 새 컨텍스트 작업자에게 그대로 넘긴다. 이 밖의 설명은 붙이지 않는다. 할 일은 브리프에 있다.

## 병렬 브리프에 `input_paths`가 있는 경우

브리프의 `reference_sections`에 적힌 절과 직접 입력을 읽는다. 브리프에 `profile`이 있으면 PROFILE 전체를 읽는다. `explain-author`와 `explain-blind`는 봉인된 문제·그림만 연다. 브리프에 `candidate_pack`이 있으면 해당 비공개 후보를 연다. 출력과 보고서는 이 시도 디렉터리에만 쓴다.

작업자가 `submission.json`에 쓰는 필드는 `status`, `report`, `outputs`(파일 경로 배열), `reviews`(검토 파일 경로 배열), `counts`, `unresolved`다. 수정 결과에는 해당하는 `fix_results`와 `reconciliations`도 포함한다. 시도 ID, 입력 목록, 파일 해시는 실행기가 기록한다. 보고서의 차단 지적은 구조화된 unresolved와 하나씩 대응시킨다. 수정 재검토에서는 브리프의 `repair_attempt`, `repair_outputs`, `repair_candidate`와 현재 후보를 각각 확인하고 필요하면 서로 다른 두 화면을 첨부한다.

`approval_plan`이 있는 통과 제출은 `reviews`에 시도 루트의 `target-reviews.json` 경로를 포함한다. 그 파일은 `pending`의 각 대상 ID를 키로 갖는 JSON 객체다. 실제 검사한 대상에 `status="pass"`와 구체적인 `evidence`를 쓴다. 노트·독립 SVG는 실제 브라우저 엔진·버전·플랫폼을 확인하여 `renderer`에 쓴다. 실행기의 `render_context`와 일치하는 화면만 재사용할 수 있다. `reusable`의 검토자·판정·화면은 실행기가 원래 기록으로 연결한다. 브리프의 재사용 사유와 새 검사 사유를 확인한다.

- 독립 풀이는 각 대상의 `method`, `conclusion`, 수치 풀이의 `tolerance`와 `residual`을 쓴다. build/check에서 볼 수 있는 independent.json에는 본인이 새로 판단한 항목만 있다. 채택할 때 실행기가 원래 검산자의 승인과 합쳐 현재 문항 순서의 결과를 조정자에게 전달한다. 조정자는 이 결과와 현재 설명 조각을 대조하고 내용·개인화·원문·브라우저 검토를 모두 수행한다.
- 노트 화면은 토픽별 데스크톱 1280×900·모바일 375×812와 light·dark를 실제로 확인하고 브리프가 실제 Chromium으로 남긴 해당 대상·테마의 PNG를 열어 보고 지정된 절대 경로를 `image`에 쓴다. 작업자가 연 후보의 대상·테마·크기와 캡처가 일치하는지 확인한다. 요약 전환·보존·탐색·콘솔 등 browser-check의 나머지 검사도 현재 후보에서 직접 수행한다. 필수 work/browser/report.json의 `interactions`에는 desktop-light, desktop-dark, mobile-light, mobile-dark 각각에 대해 브리프의 interaction_checks 항목별 관찰을 적는다. 위젯이나 PDF가 없는 경우에는 근거를 적는다. Markdown 보고서에도 결과를 기록한다.
- 독립 SVG는 각 파일을 독립 문서로 열어 두 테마, WOFF2 face, 첨자, 접속·가시성을 검사한다. 새 판정에는 지정한 `image`에 실제 PNG를 저장하고, 양 테마에서 확인한 근거를 `evidence`에 쓴다. 기존 report.json·report.md와 counts.targets의 전체 SVG 목록을 제출한다.
- 답안 PDF는 후보 자체와 전체 쪽 순서를 확인하고, 새 판정마다 브리프가 지정한 실제 `image`를 열어 승인된 설명·표기·회로·자막 여백을 대조한다. 넘침이 없으면 `overflow=[]`를 기록한다. `geometry_hints.path`는 인쇄 좌표(pt)의 글리프와 도선 근접 후보 목록이다. 표시된 쪽은 화면에서 판정한 근거를 `geometry_evidence`에 쓴다. 래스터 그림·곡선과 표시가 없던 쪽도 직접 확인한다. 보고서를 쓴 뒤 실행기가 전체 쪽의 증거와 현재 해시로 answer-review.json을 조립한다.
- 판정을 보류하거나 결함을 발견하면 실제 상황에 맞는 상태, 보고서, 근거·화면, 구조화된 지적을 제출한다. 브리프에 지정된 기존 역할 산출(감사 파일, 보고서 등)은 계속 필요하다. 독립 풀이 결과와 PDF용 answer-review.json 및 복사된 쪽 그림만 실행기가 대신 조립한다.

메인에게 task_id·attempt·receipt 절대 경로를 함께 반환한다. 시도가 바뀌면 이전 출력 위치를 유지하고 메인이 현재 인계 묶음에서 판정하도록 한다. 호스트 중단 확인은 메인이 담당한다.

반환 전 같은 시도 ID로 아래 명령을 순서대로 실행한다. `<RUN>`은 부모 RUN이고 `<python>`은 브리프의 `python` 값이다.

```sh
<python> <SKILL>/scripts/pack_cli.py task build-receipt --run <RUN> --task {task_id} --attempt {attempt} --submission <submission.json의 절대 경로>
<python> <SKILL>/scripts/pack_cli.py task check --run <RUN> --task {task_id} --attempt {attempt} --receipt <브리프 receipt의 절대 경로>
```

두 명령이 성공하면 task ID, 상태, receipt 경로와 미해결 사항을 반환한다. 채택은 메인이 한다.

## 기존 브리프의 처음 실행

```text
당신은 ec2-review-pack의 {role} 작업자다. 브리프: {brief}
run_id={run_id} attempt={attempt} — receipt에는 이 두 값만 쓴다.
1. 브리프를 직접 읽고, 브리프에 `reference_sections`가 있으면 거기 적힌 절을, 없으면 `references`에 적힌 절을 inputs와 함께 읽는다. 브리프에 `profile`이 있으면 PROFILE 전체를 읽는다.
2. 쓰기는 브리프의 allowed_outputs와 allowed_output_roots 안에서만 한다. 원본·저장소·RUN/repo 링크는 읽기 전용이다.
3. 경로 문자열은 모두 NFC 절대 경로로 쓴다(macOS 폴더 이름은 NFD일 수 있다).
4. receipt 형식은 runner-contract.md의 `배치·재개` 절과 `역할 파일의 JSON 타입` 절을 따른다. done·ready-for-publish이면 unresolved=[]이고 비차단 메모는 report에만 적는다.
5. Write 도구가 막히면 Bash heredoc으로 report와 receipt를 쓴다.
6. 다른 에이전트를 띄우지 않는다(child-coordinator는 브리프의 leaf_contract만 따른다). claim·bind·accept·fix·run 같은 상태 명령은 실행하지 않는다.
7. 반환 전에 반드시 실행한다:
   <python> <SKILL>/scripts/pack_cli.py task check --run <RUN> --task {task_id} --attempt {attempt} --receipt <receipt 절대 경로>
   status가 ok가 아니면 reason을 고치고 다시 실행한다.
8. 최종 반환은 800자 이하: task id, receipt status, receipt 경로, 미해결 한 줄.
```

## 수정·재검토로 다시 실행

```text
당신은 ec2-review-pack의 {role} 작업자다. 같은 task의 수정 차례다. 브리프: {brief}
run_id={run_id} attempt={attempt} — 이전 attempt 값은 쓰지 않는다.
브리프 request_paths의 요청과 seed-previous의 이전 산출을 먼저 읽고, 처음부터 다시 쓰지 말고 고친다.
나머지 규칙(허용 출력, NFC, receipt 형식, 상태 명령 금지)은 처음 실행과 같다.
반환 전 task check를 실행해 ok를 확인하고, 800자 이하로 task id·status·receipt 경로를 반환한다.
```
