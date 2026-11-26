# Compact runner 계약

OpenCode 우선의 파일 인계 절차이며 Codex도 같은 Python CLI를 쓴다. Windows PowerShell에서 저장소 루트 기준 `python .claude/skills/ec2-review-pack/scripts/pack_cli.py` 뒤에 아래 인자를 붙인다. 다른 cwd에서는 CLI도 절대 경로로 전달한다. 모든 repo/run/receipt/request는 실제 절대 경로다. 실행기는 spawn·모델 API를 호출하지 않는다.

## 시작과 조회 — 메인

`init --repo <REPO> [--run <새 RUN>] --range <MMDD 또는 MMDD-MMDD> [--workflow parallel|legacy] --browser-owner <workers|main|unavailable> --pdf-owner <workers|main|unavailable> [--allow-tmp]`

`--run`을 빼면 RUN은 `~/.cache/ec2-review-pack/<range>-<YYYYmmdd-HHMMSS>`이고 응답의 details_path가 그 RUN의 run-status.json이다. `/tmp`, `/private/tmp`, `/var/folders` 아래 RUN은 `--allow-tmp` 없이 거부한다. 재부팅하면 그 폴더가 지워져 상태·receipt·백업을 모두 잃는다. 실행기는 repo·run 경로를 NFC로 저장하고 경로를 NFC로 비교한다. macOS의 `전자회로2` 같은 폴더는 디스크에서 NFD라 작업자가 어느 표기를 써도 같은 경로로 본다.

`init ... --seed-from <보류된 RUN> [--redo <task id,...>] [--redo-note <절대 파일>]`: 이어받기. 아래 `이어받기` 절을 따른다.

owner 기본은 workers다. 도구가 실제 있는 주체를 전달하며 unavailable은 실제 검토 단계에서 blocked다. RUN은 없거나 비어 있어야 한다. snapshot은 `RUN/learning-style.json`이며 init이 만든다. 기존 수기 run-status를 변환하거나 과거 pass를 추정하지 않는다.

`status --run <RUN>` / `next --run <RUN> [--slots <n>]`는 읽기 전용이다. `--slots`를 생략하면 준비된 작업자를 모두 낸다. 현재 파일/해시와 대조한 view를 반환하고 stale을 저장하지 않는다. slots=0은 새 작업자 dispatch만 기다리며 준비된 기계 작업·메인 검토는 진행한다. 상태를 수동 수정하지 않는다.

모든 응답은 `{schema_version,status,phase,next,counts,details_path,error_code}` JSON 한 개이며 개행 포함 Python `len(str)` **2,000자 이하**다. 접힌 목록은 counts와 details_path 또는 이미 아는 RUN/run-status.json에서 필요한 항목만 읽는다. exit 0은 정상/대기, 1은 실행·검증 실패, 2는 사용법 오류다. 장문 stdout/stderr/traceback은 RUN의 작업 로그에 남긴다. CLI 성공을 실제 검토 pass로 해석하지 않는다.

## 병렬 실행 순서

새 RUN의 기본값은 `parallel`이다. 레거시 새 RUN은 `init --workflow legacy`로 시작한다. `--seed-from`은 기존 레거시 RUN의 이어받기 옵션이며 모드를 생략해도 새 레거시 RUN을 만든다. 기존 RUN은 저장한 계약을 따르며 `workflow` 필드가 없는 RUN은 레거시로 이어간다.

1. `next --run <RUN> [--slots <n>]`(생략하면 준비된 작업자를 모두 낸다)의 `actions`, `dispatch`, `review_locally`, `blocked`를 확인한다. `claim`의 지정 경로로 역할을 배정하고 실제 작업자 ID를 `bind`한다. 기계 작업은 슬롯 수와 별도로 `run --action <ID>`로 병행할 수 있다.
2. 시작할 때 source-prep, candidate-index, render-preflight를 함께 연다. selection이 채택되고 stage-problem-index가 봉인되면 explain-author와 explain-blind를 다른 작업자에게 동시에 맡긴다. 저작·독립 풀이가 채택되면 child-coordinator가 검증을 잇는다. 확인문제도 convert-md·selection이 승인되는 즉시 concept-draft → concept-review까지 진행한다. 최종 발행은 publish-pack·final-check 승인 뒤 별도로 진행한다.
3. 작업자는 자신의 브리프에서 `task build-receipt`와 `task check`를 실행한다. 메인은 완료한 작업만 `[{"task_id":"…","attempt":"…","receipt":"/절대/receipt.json"}]` 배열에 모아 `task accept-batch --run <RUN> --submissions <파일>`로 인계한다. 각 항목의 accepted/already_accepted/rejected와 거부 사유를 확인한다. `task accept`, `task check`로 한 항목씩 진단할 수 있다.
4. `advance --run <RUN> --max-actions 4`는 최대 네 기계 작업을 실행한다. 사람이 필요한 작업이나 차단을 만나면 `waiting_for`와 `blocked`에 ID가 나온다. 다음 묶음을 배정하고 계속한다. 결과가 접혔으면 `details_path`에서 해당 항목만 읽는다. 진행 표시는 시도 시작·승인·수정·차단·재개·발행처럼 상태가 변했을 때만 한다.

### 같은 병렬 RUN 재개

`resume --run <RUN> --stopped-attempts <파일>`에 `{"<attempt UUID>":"/절대/근거.json"}`을 준다. 살아 있는 작업자는 계속 소유권을 갖는다. 메인은 호스트가 작업자의 종료를 확인한 뒤 `RUN/host-stops/<attempt>.json`에 아래 필드를 기록한다. 작업자가 쓸 수 있는 시도 폴더의 자기 보고를 중단 증거로 사용하지 않는다.

```json
{"run_id":"<RUN UUID>","task_id":"explain-blind","attempt":"<UUID>","agent_id":"<bound host ID>","status":"completed","receipt":"/실제/worker/receipt.json"}
```

종료된 미완료 작업자는 `status="stopped"`를 쓰고 claim 후 배정 전이면 `agent_id=null`이다. 완료 작업자는 지정 영수증과 현재 고정 바이트를 모두 검증한 뒤 재사용한다. 실제 호스트 중단과 재개를 모두 확인했을 때만 같은 기록에 `host_gap={"interrupted":"<UTC ISO 시각>","resumed":"<UTC ISO 시각>"}`을 덧붙인다. 기계 작업은 자기 시도의 stopped.json, 부모 발행은 해당 시도의 publication/journal.json, 확인문제 발행은 현재 RUN의 concept-check-result.json과 날짜 소유 표시·검산 인증서를 사용한다. 호스트가 비공개 기계 작업의 중단을 확인한 경우 같은 host-stops 형식에 agent_id=null을 쓴다. 완료를 확인했으면 status="completed"와 completion_evidence에 해당 작업의 실제 종료 근거 절대 경로를 쓴다. 발행 근거가 모호하거나 아직 액션 잠금이 살아 있으면 시도를 보존한다. 누락·불일치 근거는 rejected에 표시한다.

`report --run <RUN>`의 report.json에서 각 시도별 대기·실행 구간, 겹친 구간, 확인한 호스트 공백 합집합, 브리프 바이트, 차단 ID와 확인문제 세 단계를 읽는다. 시각은 실행기가 사건을 관측한 UTC 시각이다. 작업자 실제 추론 시간과는 다를 수 있다. 모든 CLI 호출을 셀 검증 RUN은 시작 전부터 끝까지 모든 작업자에 같은 RUN 외부의 절대 폴더 `EC2_CLI_TRACE_DIR`를 전달한다. 설정하지 않으면 RUN에는 변경 명령 호출만 집계한다. 호스트가 제공한 사용량·호출 수는 `RUN/host-observations.json`에 `run_id`와 제공받은 `model_usage`, `host_tool_counts`만 기록한다.

## 레거시 배치·재개 — 메인과 역할 담당자

next.kind는 dispatch/run/review_locally/wait/recover/concept_check/report/blocked다. dispatch는 `task claim --run <RUN> --task <id>`로 먼저 예약한다. 반환 attempt/brief로 새 컨텍스트 작업자를 실행하고 `task bind --run <RUN> --task <id> --attempt <UUID> --agent-id <실제 ID>`로 연결한다. Codex는 spawn_agent(fork_turns="none"), OpenCode는 전체 대화를 복사하지 않는 새 작업 컨텍스트를 사용한다. 작업자 지시문은 [worker-prompt](worker-prompt.md) 템플릿을 채워 쓴다. claim 뒤 brief.json에는 `run_id`와 `attempt`가 들어 있다. 작업자는 반환 전에 `task check --run <RUN> --task <id> --attempt <UUID> --receipt <절대 경로>`를 실행한다. 이 명령은 accept와 같은 검증을 하되 상태를 바꾸지 않고, 실패하면 exit 1과 reason(예: `unresolved successful receipt`, `receipt identity mismatch`)을 돌려준다. 반환 뒤 `task accept --run <RUN> --task <id> --attempt <UUID> --receipt <절대 경로>`를 실행한다. 늦게 온 다른 attempt는 거부한다. 가용 슬롯·독립 역할·기존 담당자 재개 규칙은 [delegation](delegation.md)을 따른다.

브리프는 `RUN/work/<task>/brief.json`이다. role/targets/references/inputs/allowed_outputs/allowed_output_roots/report/receipt/request_paths를 직접 읽는다. author는 section_brief도 읽는다. 실행기가 고정한 inputs를 빼거나 임의 출력을 추가해 쓰기 권한을 늘리지 않는다. [공통 교육 계약](execution-guide.md)의 지정 절은 `profile` 유무와 상관없이 필수다. PROFILE 전체는 브리프에 `profile`이 있을 때만 읽는다.

receipt는 `{schema_version:1,run_id,task_id,attempt,status,inputs,outputs,report,reviews,counts,unresolved}`다. inputs/outputs는 `{path,sha256}` 배열이고 실제 현재 바이트 해시다. status는 done/needs-fix/blocked/ready-for-publish/withheld다. envelope·보고·출력은 허용 RUN 안, 읽기 전용 입력은 REPO 또는 RUN 안이다. reviews는 기존 승인 파일을 참조하며 새 envelope가 실제 검토를 대신하지 않는다. 상세 수식·원문·감사·문항 보고는 파일에 보존하고 최종 반환은 **800자 이하**의 task/status/receipt 경로다(개행 포함 Python len). 조정자는 leaf 브리프에도 같은 제한을 명시한다.

### 역할 파일의 JSON 타입 — receipt 작성 전에 확인

`receipt.inputs`는 **현재 브리프의 inputs 배열을 그대로 복사**한다. 경로/해시 집합이 정확히 같아야 하며 읽었다는 이유로 PDF·참조를 추가하거나 항목을 빼지 않는다. 추가로 발견해 읽은 강의 PDF는 source-map의 `sessions[].pdfs`에 경로 문자열로 기록한다. 실행기는 source-map의 실제 STT/PDF를 별도로 검증·해시 고정한다. 상세 독해 기록은 report에 둔다.

| 필드 | JSON 타입과 값 |
|---|---|
| receipt.inputs / outputs | 객체 배열: 각 항목은 `{"path":"절대 경로","sha256":"현재 바이트의 64자리 hex"}`. inputs는 brief.inputs와 정확히 동일, outputs는 허용 실제 산출만 |
| receipt.report | 보고 파일의 **절대 경로 문자열** 1개. path/sha256 객체가 아님 |
| receipt.reviews | 기존 검토 파일의 **경로 문자열 배열**. 검토 없는 역할은 `[]`; 해시 객체 배열이 아님 |
| receipt.counts / unresolved | 건수 객체 / 미해결 배열 |
| receipt.counts.targets | content-review/browser-qa/standalone-svg-qa의 완료 receipt에 필수인 **실제 검토 대상 ID 문자열 배열**. 현재 brief.targets의 ID 집합과 정확히 일치; 총 개수 숫자나 ID→판정 객체가 아님 |
| source-map.sessions[].stt | REPO 내부 STT **절대 경로 문자열** 1개 |
| source-map.sessions[].pdfs | REPO 내부 PDF **절대 경로 문자열 배열**. path/sha256 객체를 넣지 않음 |
| source-map.sessions[].missing | 누락 이유 문자열 배열. 없음은 `[]` |

content-review와 browser-qa는 실제 검토를 마친 대상만 `counts.targets`로 선언한다. 현재 brief.targets가 `["why-circuit","cascode-gain"]`인 가상 검토의 필드 예시는 `"counts":{"targets":["why-circuit","cascode-gain"],"reviewed":2}`다. ID를 임의 토픽명·섹션명·총 개수로 바꾸지 않는다. `reviewed:2` 같은 집계만으로 coverage를 대신할 수 없고, 아래 source-prep 예시의 counts를 검토 역할에 그대로 쓰지 않는다. 실제 누락이 있으면 done으로 맞춰 쓰지 말고 `status:"needs-fix"`와 unresolved에 대상/이유를 기록한다. 이 메타데이터는 실제 검토·기존 승인 근거를 대체하지 않는다.

아래는 **inputs가 STT 한 개뿐인 가상 브리프**의 타입 예시다. 실제로는 현재 brief.inputs 전체·run_id·claim attempt·산출 해시로 바꾼다. 예시 경로/해시를 승인 근거로 재사용하지 않는다.

```json
{
  "schema_version": 1,
  "run_id": "<현재 run_id>", "task_id": "source-prep", "attempt": "<claim attempt UUID>", "status": "done",
  "inputs": [{"path": "C:/repo/STT/0909 전회2.md", "sha256": "<브리프의 동일 해시>"}],
  "outputs": [
    {"path": "C:/run/source-map.json", "sha256": "<현재 64자리 hex>"},
    {"path": "C:/run/slides.txt", "sha256": "<현재 64자리 hex>"}
  ],
  "report": "C:/run/work/source-prep/report.md",
  "reviews": [], "counts": {"sessions": 1}, "unresolved": []
}
```

같은 역할의 source-map 타입 예시: `{"schema_version":1,"sessions":[{"date":"0909","stt":"C:/repo/STT/0909 전회2.md","pdfs":["C:/repo/강의노트/Lec.pdf"],"status":"ready","missing":[]}]}`. report/reviews/stt/pdfs에 `{path,sha256}` 객체를 넣지 않는다.

source-prep의 source-map.json은 `{schema_version:1,sessions:[{date,stt,pdfs,status,missing}]}`다. 실제 MMDD 집합, REPO 내부 STT/PDF 절대 경로, ready/missing 및 누락 이유 배열을 기록한다. scope.json은 의미 인계물이므로 임의 기계 스키마로 확장하지 않는다. manifest는 scope-draft→selection→scope-final 단일 작성자 순서다. selection은 `RUN/display-titles.json`에 선발 ID와 정확히 같은 키/비어 있지 않은 제목을 반환한다(0개는 {}). runner는 제목을 선택하지 않는다.

기존 순차 RUN의 style-audit/content-review는 브리프의 **audit_output**에 쓴다. 앞 작성자의 감사 파일을 덮지 않는다. content-review의 보완 감사만 단일 작성자 인계로 채택되며 precheck를 다시 수행한다. 브라우저/PDF owner=main은 review_locally: 메인이 실제 근거를 읽고 검사한 뒤 동일 claim/receipt/accept 계약을 수행한다. 도구 없는 작업자에게 pass를 요청하지 않는다.

## 기계 작업·발행 — 최상위 메인

`run --run <RUN> --action <next.action>`으로 한 개만 실행한다. 허용 action: prepare-pack, assemble-note, build-problems, precheck, convert-md, publish-explanation, build-answers, publish-answer, final-check. 기존 assemble/check_html/html2md, workbook 및 자식/publish_answer CLI를 실제 호출하며 구현을 문서에 복제하지 않는다. argv는 shell=False, 현재 sys.executable, 자식 UTF-8 환경이다. 로그/결과는 `RUN/work/actions/<action>/<attempt>/stdout.log`, stderr.log, result.json이다.

순서는 source-prep→날짜별 stt→scope-draft→selection→scope-final→섹션 author→prepare-pack→assemble-note→build-problems(문제 있을 때)→style-audit→precheck→content-review(일반)→browser-qa→convert-md→standalone-svg-qa(SVG가 있을 때)→child-coordinator→publish-explanation→build-answers→pdf-qa→publish-answer→final-check→concept_check→report다. next가 실제 준비 작업을 결정한다. 문제 0개는 자식/PDF만 생략한다.

`next.kind=concept_check`는 신규 RUN의 최종 검사 완료 후 메인이 수행하는 스킬 호출이다. `next.range`와 `next.parent_run`을 [ec2-concept-check](../../../../.agents/skills/ec2-concept-check/SKILL.md)에 넘긴다. 스킬의 `publish` 또는 `withhold`가 현재 final-check 회차의 `RUN/concept-check-result.json`을 남기면 `next`는 `report`로 넘어간다. 확인문제 보류 사유는 report의 `concept_check`에 담기며 부모 팩은 완료로 유지한다. 이 계약이 도입되기 전에 시작된 RUN은 기존 보고 흐름을 따른다. 기존 팩의 수기 보완은 확인문제 자동 호출 대상에서 제외한다.

prepare-pack은 첫 변경 전 기본/설명 두 백업을 검증·재사용하며 제목 맵도 그 뒤 반영한다. 답안은 현재 발행된 승인 overlay/validation으로만 RUN에 빌드한다. 자식 ready-for-publish는 발행 완료가 아니다. [통합 계약](problem-explain-integration.md)의 독립 검산·네 실제 검토·전체 감사와 [화면 검사](browser-check.md), 전 페이지 실제 PDF 검토를 유지한다. precheck의 pending/defer는 final-check 완료가 아니다.

build-answers는 RUN 안(`RUN/answers`)에만 쓴다. 실패해도 팩 inventory가 그대로면 needs_fix이고 next가 같은 action을 다시 요청한다. 고친 뒤 `run --action build-answers`를 다시 실행한다. 실행 중 팩 파일이 바뀌었으면 recovery_required이고 recover 절을 따른다.

## 병렬 RUN의 내용 검토와 수정

`--workflow parallel`에서 assemble-note가 끝나면 structural-precheck, style-audit, content-review가 같은 HTML을 각각 검사한다. 구조 검사는 토픽·레이어·길잡이를 확인한다. 전체 precheck에는 구조 검사, 양쪽 승인으로 만든 현재 감사, 선택한 경우 문제 PDF가 필요하다. 기존 화면·SVG·PDF 검사와 최종 발행 검사는 계속 실행한다.

메인은 양쪽 노트 검토가 돌아오면 같은 후보의 열린 노트 결함을 한 요청으로 모은다. 기계·화면 검토에서 뒤늦게 발견한 결함은 같은 RUN의 새 요청으로 처리한다. `run-status.json`의 `findings`에서 `id`, `review_attempt`, `input_digest`를 읽고 RUN 안에 다음 형태의 파일을 저장한다.

```json
{"id":"correct-note-1","items":[{"finding_id":"<finding id>","review_attempt":"<검토 attempt>","input_digest":"<후보 SHA-256>"}]}
```

`task fix --run <RUN> --request <절대 JSON>`은 해당 작성자를 다시 열고 의존하는 검사를 갱신한다. 작성자는 브리프의 `previous_outputs`를 읽고 `repair_findings`를 새 attempt에서 수정한다. 앞선 수정본이 접수되어 재검토를 기다리는 동안 같은 작성자에게 다른 결함을 배정할 수 있다. 새 작성 attempt는 새 결함만 수정하며, 앞선 결함의 재검토는 그 결함에 배정된 원래 수정 attempt와 채택 파일을 참조한다. 이때 수정 횟수는 원래 수정본에서 확인한 실패만 반영하고, 현재 발행 여부는 현재 후보의 별도 판정을 따른다. 기계 검사 또는 감사 결합 전에 다른 수정본이 채택되어 앞선 버전의 판정이 없으면 그 수정은 `not_reviewed`로 기록하고 현재 후보의 결과만 적용한다. 두 노트 검토의 의견 충돌은 양쪽 검토 attempt가 모두 현재일 때만 수정할 수 있다. 조립기·템플릿에서 발생해 RUN 안에 수정 가능한 담당 파일이 없는 진단은 발생 위치와 보류 사유를 기록한다. 반복 요청·중단·출력 미변경은 수정 횟수를 쓰지 않는다. 검토자는 새 후보에서 원문과 대조한 결과를 [검토 지시문](review-prompt.md)에 따라 제출한다. 같은 결함에서 서로 다른 두 수정본이 미해결 판정을 받으면 그 결함은 `withheld`가 된다. `report.json`의 `findings`에서 근거와 수정·검토 attempt를 확인한다. 미해결·보류 결함이 있으면 팩 발행이 막히고 다른 결함의 수정은 진행할 수 있다.

child-coordinator가 채택된 설명 조각에서 실제 내용 결함을 찾으면 `needs-fix`로 반환하고 `unresolved`에 노트 검토와 같은 필드 `rule`, `target`, `defect`, `severity`(Critical·Important·Minor), `owner_task`, `evidence`를 적는다. `owner_task`는 항상 `explain-author`다. 브리프의 `report.md`에는 심각도 소제목 아래 각 결함을 `- [target] [rule] defect` 한 줄로 적는다. 실행기는 이 결함을 `review_id`가 `child-coordinator`인 `findings`로 기록한다. `input_digest`는 검토한 explain-author 조각 묶음의 다이제스트로, 브리프의 `candidate_digest`와 같다. 메인은 열린 조정자 결함을 모두 한 요청에 담아 `task fix`를 실행한다. 이 요청은 explain-author만 새 attempt로 다시 열고 브리프에 `repair_findings`와 `previous_outputs`를 넣는다. explain-blind의 독립 풀이는 그대로 유지하고, 조정자·explain-verify·답안 PDF·발행 검사는 stale로 바꾼다. 수정본이 접수되면 조정자를 새 attempt로 다시 배정한다. 재배정된 조정자는 브리프의 `recheck_findings`마다 `fix_results`에 `finding_id`, `request_id`, `attempt`(해당 `repair_attempt`), `outcome`, `evidence`를 적는다. 미해결 결함은 같은 `rule`·`target`·`defect`로 `unresolved`에 다시 적는다. 서로 다른 두 수정본에서 미해결이면 `withheld`가 된다. 조정자는 설명 작성자와 다른 에이전트여야 한다. 이 경로가 생기기 전에 결함 기록 없이 needs_fix로 채택된 조정자는 `next`가 새 attempt로 다시 배정한다. 이때 조정자는 위 형식으로 결함을 다시 제출한다.

## 기존 RUN의 수정·중단·복구

`task fix --run <RUN> --request <절대 JSON>`: `{id,category,items:[{task_id,request_path}],waived?:[{id,reason}]}`. content 요청은 needs_fix인 style-audit·content-review report의 `## Critical`·`## Important`·`## Minor` 아래 `- [<id>]` 결함을 모두 덮어야 한다. 토픽·섹션 ID는 `author-<섹션>`, manifest 문제 ID(노트 밖 `[P12.04]` 포함)는 `selection`, 그 밖은 `scope-final`이 담당이다. 담당 task가 items에 없으면 `content fix misses findings: P12.04→selection`처럼 거부하며 예산을 쓰지 않는다. 일부러 고치지 않는 결함은 `waived`에 이유와 함께 적는다. items에 `pdf-qa`가 있으면 build-answers가 stale이 되어 next가 답안 PDF를 RUN에 다시 빌드한다. category=content 또는 machine_browser. 같은 id 재등록은 중복 차감하지 않는다. 내용 최대 1회, 기계/브라우저 **공통 최대 2회**이며 작성자 수나 release로 늘리지 않는다. 기존 담당자를 재개하고 새 attempt를 사용한다.

추가 회차는 사용자가 해당 RUN에 **기계/브라우저 수정 1회 추가를 명시적으로 허용한 경우에만** 메인이 `task authorize-fix --run <RUN> --authorization <절대 JSON>`으로 기록한다. JSON은 `{schema_version:1,id,run_id,category:"machine_browser",extra_rounds:1,approved_by:"user",human_request,request_ref,reason}`의 정확한 필드 집합이며 id·사용자 원문·메시지 참조·이유는 비어 있지 않은 문자열, run_id는 현재 RUN UUID다. 메인은 실제 사용자 메시지를 확인하고 원문/참조를 그대로 기입한다. 이 로컬 기록은 암호학적 사용자 인증을 제공하지 않는다. 자동 승인·추가 grant·content 확장·횟수 초기화는 금지한다.

성공하면 `RUN/authorizations/machine-browser-extra.json`에 불변 사본을 쓰고 상태의 `extra_fix_authorization`에 경로/SHA-256을 기록한다. 현재 카운터를 유지하며 그 RUN의 machine_browser 한도만 2→3으로 계산한다. content 한도는 1, 다른 RUN의 기본 한도는 2다. 같은/다른 id의 재승인은 모두 거절하며 기존 `task fix` 동일 id 재요청은 계속 중복 차감하지 않는다. 승인 후 기존 절차대로 새 `task fix --request`를 등록·claim한다. 승인 파일/상태 참조가 바뀌거나 빠지면 추가 회차를 인정하지 않는다. 승인만으로 작업·근거·검토·발행을 완료 처리하지 않는다.

`task release --run <RUN> --task <id> --attempt <UUID> --reason <실제 확인>`은 메인이 중단/미실행을 실제 확인한 뒤만 실행한다. claim 후 bind 전에도 예약은 유지된다. source/profile 변경은 관련 근거를 stale로 만든다. 자식 extract 뒤 고정 입력 변경은 부모 재검토와 새 EXPLAIN_RUN을 요구한다.

`reconcile --run <RUN> --action <허용 이름>`은 현재 상태에 저장된 해당 action의 attempt만 기존 `reconcile_action`으로 검증·채택한다. attempt 인자는 없으며 이전 attempt 선택이나 명령 재실행은 하지 않는다. 컨트롤러 중단 뒤 `next`가 machine action already running / explicit reconciliation의 wait이면, 메인이 해당 명령과 프로세스 트리가 실제 종료했음을 확인한 뒤 `python .claude/skills/ec2-review-pack/scripts/pack_cli.py reconcile --run <RUN> --action <action>`을 실행한다. 활성 action lock은 그대로 배제하며 성공 stopped.json·현재 입력·선행 근거·정확한 쓰기 집합/inventory·발행 증거를 모두 다시 검증한다. exit 0이면 `next --run <RUN> --slots <가용 수>`로 이어간다. 입증 불가 시 exit 1/recovery_required와 result.json/reconcile-error.txt를 보존하며 상세 경로를 읽는다. `recover`는 별도의 롤백 명령이다. reconcile 실패를 재실행·수동 상태 수정으로 우회하지 않는다.

`recover --run <RUN>`은 기록된 마지막 신뢰 inventory와 현재 파일 및 두 백업이 일치해야 한다. 기본 팩→설명 순서로 복구하며 새 산출은 withheld에 보존한다. 외부 편집/불명확한 부분 쓰기는 recovery_required로 멈추고 덮지 않는다. 실행 중 명령 lock은 프로세스 종료 때 풀린다. 활성 lock 파일을 unlink하지 않는다.

컨트롤러가 실행 중 죽었으면 메인이 소유 명령/프로세스 트리가 멈췄는지 실제 확인해야 한다. stopped.json이 없을 때만 `RUN/work/actions/<action>/<attempt>/stopped-confirmation.json`을 직접 작성한다: `{schema_version:1,attempt,confirmed_by,reason,process}`. process는 해당 process.json 객체(pid와 동일 attempt)와 정확히 같아야 한다. 확인 마커는 성공 exit·발행·알 수 없는 쓰기 소유권을 증명하지 않는다. 신뢰 inventory가 없거나 외부 차이가 있으면 자동 복구/재발행하지 않는다.

## 이어받기 — 메인

보류된 RUN을 다시 돌릴 때 처음부터 init하지 않고 `--seed-from`으로 새 RUN을 만든다. 이전 RUN은 withheld이거나, 저장소 쓰기(백업·발행) 전의 blocked/needs_fix여야 한다. range·repo가 같고 고정 입력(STT·PROFILE·snapshot) 해시가 모두 같아야 하며, 하나라도 다르면 아무것도 이어받지 않고 처음부터 한다. 활성 attempt가 남은 RUN은 거절한다. 이전 일반 RUN은 재개하거나 이어받을 수 있다. 이전 `lite: true` RUN은 같은 범위로 새 RUN을 시작한다.

이어받는 것은 이전 RUN에서 done이고 현재 바이트가 receipt와 일치하며 역할·대상·의존이 같은 작업자 task뿐이다. 실제 범위는 첫 기계 작업 앞(source-prep, stt, scope, selection, scope-final, author)이다. 기계 작업은 저장소에 쓰므로 항상 다시 실행하고, 그 뒤 검토·자식·PDF task도 의존 사슬을 따라 다시 한다. child-coordinator와 pdf-qa는 이어받지 않는다. 파일은 같은 상대 경로로 복사하며 텍스트 속 이전 RUN 경로는 새 RUN 경로로 바꾸고 해시를 다시 기록한다. 이어받은 task는 `carried`에 이전 run_id·attempt를 남긴다.

`--redo`는 실제 결함이 확인된 task id다. 그 task와 뒤 단계는 다시 하며, 이전 산출·보고를 `work/<id>/seed-previous/`에, `--redo-note` 사본을 `requests/seed-redo/`에 두고 brief의 request_paths로 넘긴다. 작업자는 처음부터 쓰지 않고 이것을 고친다. 수정 예산은 새 RUN 기준 0에서 시작하며 이어받기로 한 RUN 안의 한도를 늘리지 않는다. 결과의 `seeded_from`(carried/redo/rejected)은 report에도 실린다. rejected가 있으면 그 이유를 최종 보고에 적는다.

scope-final을 redo하면 init 때는 섹션 작성자를 이어받지 못한다(의존이 아직 끝나지 않음). 이 작성자들은 `seeded_from.deferred`에 남고, 새 scope-final이 accept된 직후 실행기가 다시 시도한다. RUN 경로만 다르고 `briefs/<섹션>.json`이 같으며 이전 `sections/<섹션>.html`이 receipt 해시와 같으면 carried가 된다. 메모 한 줄이라도 다르면 `section brief changed`로 rejected에 남고 그 작성자만 새로 띄운다.

## 보고와 참조 경로

`report --run <RUN>`은 최종 파일·현재 검사·백업·발행·복구·withheld 집계를 파일로 만들고 위치를 반환한다. 최종 미실시/실패는 일부 완료다. 실제 인수 기록은 RUN/runner-acceptance.md에 최종 gate/파일/복구 상태, CLI 최대 길이, 800자 초과 건수, 메인의 원문/스크립트/예시 전문 반입 여부, 실제 요청/cache 통계(없으면 unavailable)를 쓴다. 단일 새 실행과 과거 로그로 A/B 절감률을 주장하지 않는다. synthetic fixture 승인을 실제 인수로 반출하지 않는다.

역할별로 필요한 것만 읽는다: [manifest](manifest-guide.md), [선발](problem-selection.md), [내용](content-rules.md), [요약](stt-summary-prompt.md), [개인 명세](solution-style.md), [위젯](widget-rules.md), [의미·감사](review-prompt.md), [화면](browser-check.md), [단계별 교육·예외](execution-guide.md), [문제설명](problem-explain-integration.md).


## phase 8 독립 SVG 검토

`convert-md` 성공 후 실행기는 action의 명시적 outputs와 verified_files를 실제 `.assets/정리노트_<range>_<slug>.md`, `.assets/figures_<range>/*.svg` 집합·현재 해시와 대조한다. 기대 SVG가 없어지거나 기록과 다르면 0개로 건너뛰지 않는다. 성공한 실제 변환이 SVG를 하나도 내보내지 않았을 때만 `standalone_svg_qa.status=not_required`와 이유를 기록한다. SVG가 있으면 `standalone-svg-qa`가 끝나기 전에는 자식 EXPLAIN_RUN을 할당하거나 문제 0개의 final-check로 진행하지 않는다.

이 역할의 `targets`는 실제 출력 SVG **절대 경로 문자열 배열**이다. 완료 receipt의 `counts.targets`는 실제 검토한 동일 경로를 중복 없이 전부 포함한다. 임의 토픽 ID·파일 개수로 대체하지 않는다. `converted_assets`는 현재 note/md/svgs의 경로·해시를 제공하고, 이 파일들은 전체 PROFILE·부모 근거와 함께 `inputs`에 고정된다. `svg_screenshots`는 각 대상 경로에 대응하는 RUN 내 PNG 출력 경로다. 모든 지정 PNG를 실제 독립 SVG 화면에서 남겨야 하며 각 PNG는 디코딩 검증된다.

쓰기 범위는 `RUN/work/standalone-svg-qa/`의 `report.json`, `report.md`, `screenshots/`, receipt뿐이다. receipt.report는 이 report.md이며 reviews에는 report.json을 포함한다. 실제 확인한 폰트 face·첨자·회로 배치·테마별 가시성·겹침/클리핑·대상 해시와 결함을 보고한다. `html2md --check` 성공이나 스크린샷 파일 생성만으로 실제 화면 검토를 대신하지 않는다. 기존 승인 스키마를 새로 만들거나 pass를 자동 생성하지 않는다.

browser_owner=workers면 dispatch, main이면 review_locally, unavailable이면 blocked다. slots=0은 workers dispatch만 대기시킨다. MD/SVG 변경은 이 검토와 자식/답안/최종 검사를 stale로 만들며, extract 이후 변경은 새 EXPLAIN_RUN을 요구한다. 수정은 기존 machine_browser 공통 최대 2회 예산을 사용한다. 이 검토의 결함으로 원본 문항을 교체하지 않는다.

## 답안 PDF 보고서

PDF QA의 brief.report와 receipt.report는 모두 `RUN/answer-review.md`다. 검토자는 이 실제 페이지별 보고서와 `RUN/answer-review.json`, 전체 `RUN/answer-pages/page-*.png`만 만들고 receipt에 현재 해시를 담는다. JSON evidence에 같은 보고서와 전체 실제 페이지를 포함하며 별도 work/pdf-qa/report.md는 요구하지 않는다.

## 변환 중 예정 답안 PDF 링크와 안전한 재시도

`convert-md`는 답안 발행보다 먼저 실행된다. 문제가 있는 팩에서만 `html2md.py --check --manifest <RUN/manifest.json> --defer-answer-pdf`를 사용한다. manifest의 note 이름과 실제 note 이름이 같아야 하며, MD의 정확한 `../<manifest answer_pdf_name>` 누락만 잠시 유예한다. 다른 파일·하위 경로·fragment가 붙은 링크와 수식·앵커·그림 검사는 그대로 실패시킨다. 기본 `html2md.py --check`는 계속 strict다. 유예 성공은 preliminary일 뿐 답안 발행 승인이 아니다.

최종 `final-check`는 기존 유예 없는 HTML 검사와 함께 기존 MD에 순수 `check_md(note, md)`를 유예 없이 실행한다. 이 단계에서 변환기를 다시 실행하거나 HTML·MD·SVG를 재생성하지 않는다. 따라서 child extract 뒤 고정된 부모 산출물은 유지된다. `standalone-svg-qa`의 실제 화면 승인과 child 이전 순서는 그대로다.

`convert-md`가 비정상 종료해 recovery_required가 된 경우, 동일한 `run --action convert-md` 호출로 새 attempt를 시작할 수 있는 좁은 예외가 있다. 이전 result/started/stopped의 attempt·nonzero exit·입력 목록이 일치하고, 실제 종료 기록이 있으며, inputs·선행 승인·마지막 trusted inventory·stopped inventory·허용 write delta가 모두 현재와 같아야 한다. 다른 작업의 미해결 recovery, invalidated active, 종료 증거 누락, 외부 변경 또는 untrusted inventory는 계속 차단한다. 실행기는 이전 exit 1을 성공으로 바꾸지 않고 이전 폴더와 history를 보존하며, 새로운 UUID에서 다시 실행한다. 이 기계 재시도는 task fix/추가 artifact round를 만들거나 기존 예산을 초기화하지 않는다.

추가 안전 경계: 위 변환 재시도 예외는 child RUN이 할당되기 전의 실패에만 적용한다. 현재/퇴역 EXPLAIN_RUN 또는 child attempt가 있으면 거부하며 부모 재검토 절차를 요구한다. 따라서 extract 뒤 고정된 HTML·MD·SVG를 재변환하는 우회 경로로 사용할 수 없다.
