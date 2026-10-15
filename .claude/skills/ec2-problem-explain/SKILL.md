---
name: ec2-problem-explain
description: "전자회로2 복습팩이 이미 고른 workbook 문제(복습노트/<range>/.assets/problems.txt)마다 문제의 단서·떠올릴 개념과 공식·첫 줄·단계별 이유·완성 답·검산·함정을 펼친 문제설명 HTML과 MD를 만들고, 원문 대조·내용·독립 검산·브라우저 검토를 통과한 뒤에만 복습노트에 발행한다. \"문제설명\", \"복습문제 풀이 설명\", \"1007 문제 풀이 설명해줘\"처럼 요청하거나 /ec2-problem-explain [MMDD|MMDD-MMDD]로 부를 때 사용한다. 새 출제·정리노트·PDF·영상은 별도 스킬(ec2-review-pack 등)이다."
---

# 전자회로2 문제풀이 입문 설명

Razavi 이론은 읽었지만 회로 문제풀이 경험이 적은 학생에게, 복습팩 문제마다 **문제의 단서 → 떠올릴 개념과 공식 → 첫 줄 → 단계별 이유 → 완성 답 → 검산 → 함정 → 다시 풀기**를 모두 펼쳐 보여 준다. 중간에 사용자에게 묻지 않고 끝에 한 번 보고한다. 커밋은 제안만 한다.

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

새 문제, 정리노트, PDF, 영상, 자동 채점은 만들지 않는다. 원본(`problems.txt`, 문제 md, 문제 그림, 복습문제 PDF, 정리노트 HTML·MD)은 고치지 않는다. md의 `## 풀이`는 참고 답안일 뿐 독립 검산을 대신하지 않는다. md 풀이가 틀렸다고 보이면 고치지 말고 disputed로 보고한다(수정은 `workbook-solution` 몫). 정리노트에 링크를 자동으로 넣지 않는다.

## 경로 약속

- `SKILL` = 이 파일이 있는 폴더(`.claude/skills/ec2-problem-explain`)의 절대 경로
- `REPO` = 저장소 루트
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

### 1. extract
```bash
python3 "$SKILL/scripts/epe_cli.py" extract --repo "$REPO" --target 1007 --run "$RUN"
```
- `--target`은 인자 그대로(`1007`, `0923-1002`), 인자가 없으면 `--target`을 뺀다.
- 팩마다 `BUCKET/source.json`, 빈 `explanations/`, 빈 `evidence/`가 생기고 `RUN/run.json`에 목록이 남는다. 출력의 `extract: …/source.json` 줄이 팩 목록이다.
- 대상 오류(없음·문제 없는 팩·여러 후보)는 메시지를 그대로 보여 주고 멈춘다. 한 팩만 실패하면(종료 코드 1, stderr에 그 팩) 그 팩을 withheld로 적고 나머지는 계속한다.

### 2. 자료 읽기
`BUCKET/source.json`에서 팩의 `range`·`slug`, 문항마다 `id`(`p1`…)·`source`(`<workbook id> · <종류> <번호>`)·`original_html`·`conditions_html`·`ask_html`·`figures_html`·`reference_steps`·`reference_answer`·`subparts`, 그리고 `inputs`(problems.txt·문제 md·그림의 절대 경로)를 확인한다. 작성자에게 넘길 참고 자료를 문항마다 정한다.
- 문제 md: `inputs`의 해당 md(frontmatter의 `section`, `book_page`, `pdf_page`, 그림 id). 기출(`from_the_past/md/…`)은 `textbook_chapters`로 관련 장을 정한다.
- Razavi 교과서: `교과서/마이크로전자회로/<N>장.pdf`의 그 절 쪽(교과서 문항은 md frontmatter `section`·`pdf_page` 근처)과, 같은 장 md 폴더의 관련 예제(`교과서/마이크로전자회로/chNN/README.md` 인덱스로 찾는다).
- 강의자료: 그 절을 다루는 `강의노트/2026F_Lec*_*.pdf`의 슬라이드.
- 같은 날 정리노트: `복습노트/<range>/정리노트_<range>_<slug>.html`(개념 링크의 anchor도 여기서 고른다).
- STT(`STT/<MMDD> 전회2.md`)는 교수님 표현·강조를 확인할 때만 보조로 쓴다.

### 3. 저작 (문항마다 opus 작성자, 병렬)
- 문항마다 작성자 1명을 **한 메시지에서 병렬로** 띄운다. 모델은 opus(GPT: sol)다.
- 브리프에 적을 것: [저작 규칙](references/authoring.md)의 절대 경로를 먼저 읽으라는 지시, `BUCKET/source.json` 경로와 문항 id(`pN`), 그 문항의 `subparts`, 2에서 정한 참고 자료 경로와 쪽, 출력 파일 `BUCKET/explanations/pN.html` 하나(다른 곳에는 쓰지 않는다), 임시 파일은 `RUN/work/pN/`에만.
- 작성자는 원문·조건·구할 것·그림을 다시 쓰지 않는다(조립기가 md에서 붙인다).
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
[검토 기록](references/verification.md)을 읽고 네 검토를 실제로 수행해 `BUCKET/review.json`에 기록한다.
- `source_visual`: `workbook/source_pages.py render`로 원본 쪽을 렌더해 문항 조건·그림·소문항과 대조.
- `content`: 작성자가 아닌 리뷰어 에이전트(opus) 1명이 팩의 모든 조각을 읽고 소문항별로 판정.
- `independent`: 4의 판정을 그대로 옮긴다(evidence 경로는 stage에 복사된 `evidence/`와 같은 이름).
- `browser`: 메인 에이전트가 stage 폴더를 `python3 -m http.server`로 열고(몇 초 뒤 측정), 네 조합 측정은 헤드리스 Playwright [scripts/epe_browser_check.py](scripts/epe_browser_check.py)로 해요(`playwright`·chromium 필요). 내장 브라우저 창은 목차·pager·테마 토글을 눌러 보는 확인에만 쓰고, 그 페이지의 `document.visibilityState`가 `'visible'`일 때만 결과로 써요. `ERR_CONNECTION_RESET` 같은 연결 끊김은 fail이 아니라 다시 실행해요. evidence에 어느 경로로 확인했는지 적어요.
- `references`: 실제로 읽은 저장소 자료의 절대 경로와 SHA-256.
- 내용·화면 결함은 담당 작성자에게 모아서 한 번에 되돌리고, 고친 뒤 5부터 다시 한다(네 검토 모두 다시). 최대 2회.

### 7. publish
```bash
python3 "$SKILL/scripts/epe_cli.py" publish --run "$RUN"
```
- 모든 검토가 `pass`이고 입력·조각·참조·산출 해시가 그대로일 때만 발행된다. 하나라도 `not_run`·`fail`·`disputed`이거나 해시가 바뀌면 그 팩은 보류된다. 다른 팩은 독립으로 발행된다.
- 발행은 설명 소유 파일만 `복습노트/<range>/`로 교체하고, 기존 파일은 `BUCKET/backups/`에 백업하며, 실패하면 복구한다. 출력의 `publish: … backup: …` 줄을 보고에 쓴다.
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
- `.assets/자료_문제설명_<range>_<slug>/`: manifest, 조각, evidence, 로컬 KaTeX·Pretendard, `validation.json`(발행 당시 review.json)

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
- 현재 검토 기준은 `review_policy_version="problem-explain-2026-10-15"`다. build의 review.json과 manifest에 기록하며, 이전 기준이나 기준 없는 기록은 새 발행을 승인하지 못한다. 기존 발행 HTML의 열람에는 영향을 주지 않는다.

### 레이아웃만 바뀐 기존 발행분 재발행

발행 자료 `.assets/자료_문제설명_<range>_<slug>/`의 fragments·evidence를 새 RUN으로 복사하고 stage만 조립한다. CLI의 rerender는 자동 발행하지 않는다.

```sh
python3 ".claude/skills/ec2-problem-explain/scripts/epe_cli.py" rerender --repo "<저장소 절대경로>" --target 1007 --run "<비어 있는 새 RUN 절대경로>"
```

입력·설명 조각·입력 그림·검산 자료·참조 파일이 검증되고 검토 기준도 현재와 같을 때만 content·independent를 재사용한다. 전자회로2는 problems.txt뿐 아니라 문제 MD·그림 전체의 합성 해시가 같아야 한다. 참조 누락·내용 변경·기준 누락/변경이면 content·independent도 not_run으로 되돌리고 실제 검토를 다시 한다. 경로 이전은 실제 대상과 바이트/링크 동등성을 입증할 때만 허용하며, 입증하지 못하면 재검토한다. 원본 HTML의 스타일·실행 스크립트만 바뀐 경우는 과거 입력을 확인할 수 있을 때만 동일 문항으로 인정하고 JSON 정답 데이터는 내용으로 취급한다.

`check` 뒤 source_visual·browser를 실제로 다시 확인한다. 검토 기준이 바뀐 이번 업데이트의 옛 발행분은 내용 검토·독립 검산도 새로 필요하다. 네 검토가 모두 pass인 뒤에만 별도 publish 절차를 사용한다. 사용자가 stage까지만 요청했다면 publish를 실행하지 않는다. 새로 해설을 저작해야 하면 기존 정상 저작 절차로 돌아간다.
