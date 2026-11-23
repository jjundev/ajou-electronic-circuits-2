---
name: ec2-interactive
description: '전자회로2 복습노트 날짜나 주제로 회로도·파형·그래프를 연동하는 인터랙티브 HTML을 만들고 기존 정리노트의 관련 설명에 새 탭 링크를 연결한다. 인터랙티브 자료 제작, 움직이는 회로 자료, 기존 인터랙티브 링크 연결 또는 /ec2-interactive [MMDD|MMDD-MMDD|주제]에 사용한다. 정리노트·문제·PDF·영상 생성은 별도 스킬이다.'
---

# 전자회로2 인터랙티브 자료

네이티브 SVG 회로도, 경량 소신호 솔버(`assets/mna.js`), 3대 아키타입(`probe`·`bench`·`approx`)과 공통 3단 셸(`assets/lab-template.html`·`assets/lab-runtime.js`)을 하나의 `lab.js` 명세로 엮어 단일 HTML을 만든다. 실행 예제는 `references/example-lab.js`다. 생성부터 4단계 검증·저장·정리노트 연결까지 일괄 진행하고 결과를 보고하며, 중간 승인을 기본 흐름에 추가하지 않는다.

**인자:** `[MMDD | MMDD-MMDD | 주제]`. 날짜는 적합한 주제 2–4개, 명시 주제는 1개다(적합 후보가 하나면 1개만 생성). 인자가 없으면 `NO_ARG`와 사용법을 보고한다.

**산출물:** 팩 최상위 `인터렉티브_NN_<이름>.html`, `.assets/자료_인터렉티브_NN_<이름>/`의 `lab.js`·`brief.md`·`validation.json`, 정리노트 HTML의 문맥 안내 링크(`data-ec2-interactive`). 이름은 한국어를 쓰고 고유명사·기호만 영어로 남긴다(예: `귀환_종단_조립_벤치`).

**경로와 불변 원칙:** `SKILL`은 이 파일이 있는 실제 폴더, `REPO`는 저장소 루트, `RUN`은 시스템 임시 폴더의 고유 실행 경로, `DEST`는 `resolve.cjs` 결과의 `folder`다. 모든 도구에 절대 경로를 넘기며 NFC/NFD 경로를 손으로 재조립하지 않고 JSON 출력 경로를 그대로 사용한다. 안내 링크 외 정리노트 본문·`.widget`·스타일·스크립트, 정리노트 MD·PDF·복습문제는 수정하지 않는다. 기존 자료 덮어쓰기·자동 커밋·외부 게시·영상·SPICE 생성을 하지 않는다.

**기존 자료 연결만 요청:** 새 자료를 만들지 않고 요청 범위의 기존 노트·자료를 읽어 8–9단계만 실행한다(`전체`는 `복습노트/` 아래 기존 자료 전체).

**기존 실험 수정 요청:** HTML에 표시된 원본 `lab.js`와 공통 셸을 수정하고, `build.cjs`로 기존 위치의 HTML을 재생성한다. 검증을 갱신하고, 문제설명에 연결된 실험은 `lab-validation.json`과 해당 팩 매니페스트의 파일 해시도 대조한다.

## 문제설명에서 문항 모드로 호출
`ec2-problem-explain`이 전달한 `lab/brief.json`과 원문·해설 근거로 문항별 실험 한 개를 만든다. 주제 점수와 날짜별 수량 대신 브리프의 한 가지 조작과 관찰을 따른다. 3–6단계 검증을 수행해 같은 임시 `lab/`에 `lab.js`, `index.html`, `lab-validation.json`을 반환한다. 검증 기록은 아래 네 게이트와 `source_sha256`, `html_sha256`, `brief_sha256`을 포함한다. 현재 문항과 결선·기호·가정·정답 방향을 대조하고 예시값은 화면에 표시한다. 빌드 출력은 소스 옆에 두어 재생성 경로가 발행 후에도 유효하게 한다. 스테이징과 발행은 호출한 문제설명 또는 부모 복습팩이 담당한다.

### 0. 준비

`복습노트/`, `STT/`, `강의노트/`, `교과서/마이크로전자회로/`, Node.js ≥20, Python Playwright(`scripts/probe_interactive.py` 실행용)를 확인한다. 누락은 실제 경로와 함께 보고한다. `RUN`을 만들고 수정 대상 정리노트의 바이트 백업과 기존 MD·PDF·그림 SHA-256을 기록한다.

### 1. 대상 풀기

`node "$SKILL/scripts/resolve.cjs" "$REPO" "<인자>"`를 실행해 `RUN/target.json`을 저장한다. 출력은 `kind`, `folder`, `exists`, `date`, `notes`, `noteHtml`, `stt`, `stts`, `existing`, `next`다.

정확한 날짜 폴더를 우선하고 없으면 해당 날짜를 포함하는 범위 팩(모든 STT를 `stts`로 반환)을 고른다. `MMDD-MMDD`는 그 이름의 기존 팩만 허용하며, 겹치는 범위 팩이 여럿이면 `AMBIGUOUS_TARGET`과 후보 폴더를 보고한다. `STT`만 있으면 새 팩 자리다. 주제는 H2/H3 제목을 우선해 최신 팩을 선택하고 없으면 `복습노트/주제별/`을 쓴다. `NO_TARGET`·`NO_ARG`는 즉시 중단한다.

### 2. 주제와 아키타입 고르기

`references/topic-selection.md` 기준으로 `notes`·`stts`·강의노트·교재를 대조해 점수(3점 이상 우선)를 매기고 주제별 아키타입(`probe`, `bench`, `approx`)을 결정한다. 정리노트에 이미 `.widget`이 있는 절은 단순 열람형 위젯을 회로 조작·인과 맥동·포트 조립·근사 붕괴 실험 등 능동 조작으로 확장하는 경우만 선정하고, 단순 반복이나 다음 시간 예고는 제외한다. 후보가 없으면 이유를 보고한다.

주제별 `RUN/<n>/brief.md`에 제목·파일명·아키타입·점수·기존 `.widget` 확장점·모드·조작 범위·대표 설정·인과 단계·예측 질문·오개념 3개·모델 가정·근거 절/쪽·`(교과서 보충)`·정리노트 연결 계획을 기록한다.

### 3. `lab.js` 작성

`references/lab-api.md`, `references/design.md`, `references/example-lab.js`를 읽고 `RUN/<n>/lab.js`를 작성한다.

- **네이티브 SVG (`CIRCUIT-02`):** `.fig-ink`, `.fig-accent`, `.fig-danger`, `.fig-dot`, `.fig-text`, `.fig-math`, `.fig-muted`, `.sym`, `data-node-color="blue"|"red"`만 사용한다. SVG 하드코딩 hex와 평문 `_`/`$...$` 첨자를 금지하고 `<tspan baseline-shift="sub" font-size="78%">`를 사용한다. 허용 CDN 4종 외 외부 URL을 쓰지 않는다.
- **5종 `data-*` 훅과 배지:** `data-node`, `data-branch`, `data-elem`, `data-port`, `data-causal-step`을 선언·반환값과 정확히 일치시키고, `<g data-badges><g data-badge-for="...">` 슬롯을 도선에서 0.6em 이상 떨어진 여백에 둔다.
- **MNA와 UI 계약:** `evaluate(state, mna)` 안에서 `assets/mna.js`의 `solveCircuit`을 써 회로·배지·타일·진단·플롯을 단일 모델로 계산한다. 카드가 가리키는 조작과 관측값이 있을 때 `predict.check`를 작성한다. 선택 후 ‘회로에서 확인’을 누르면 검증 조작을 적용하고 같은 모델의 수치와 이유를 보여준다. ‘바로 실험하기’는 현재 회로에서 이어간다. 모드마다 `mistakes` 3개를 채운다.

### 4. 기계 검사 (`check.cjs` & `steps.cjs`) — 게이트 1

```bash
node "$SKILL/scripts/check.cjs" "$RUN/<n>/lab.js"
node "$SKILL/scripts/steps.cjs" "$RUN/<n>/lab.js"
```

`check.cjs`가 `ok`(종료 0)를 내야 하며(`SCHEMA_INVALID`, `MISTAKES_INVALID`, `HEX_IN_SVG`, `SVG_TEXT_NOTATION`, `HOOK_MISSING`, `EXTERNAL_URL`, `EVAL_THROW`, `EVAL_NON_FINITE` 모두 해결), `steps.cjs`로 `buildProbeStates` 전 상태의 타일·노드·진단 스냅샷을 뽑아 검토 자료로 넘긴다.

### 5. 내용·독립 수치 검토 (`circuit-verification.md`) — 게이트 2

작성자가 아닌 검토자(또는 별도 독립 검토 패스)에게 `lab.js`, `brief.md`, 실제 근거 자료, `steps.cjs` 출력을 전달한다. `references/circuit-verification.md`에 따라 `mna.js` 재호출이 아닌 **별도의 해석식·복소수 전달함수·KCL/노드방정식**으로 기본 상태, 대표 설정, 파라미터 끝값, 오조립·특이(`bench`) 및 근사 붕괴(`approx`) 상태를 독립 검산한다.

Critical/Important 결함은 수정 뒤 4–5단계를 재실행하며, 해결하지 못하거나 독립 검산을 수행할 수 없으면 `not_run`/`fail`로 남기고 해당 자료만 보류한다.

### 6. 빌드, 오프라인 프로브 & 실제 브라우저 확인 — 게이트 3·4

```bash
node "$SKILL/scripts/build.cjs" "$RUN/<n>/lab.js" "$RUN/<n>/preview.html"
python3 "$SKILL/scripts/probe_interactive.py" "$RUN/<n>/preview.html" --widths 1440,375 --themes light,dark --out "$RUN/<n>/probe.json"
```

- **게이트 3 (`probe_interactive.py`):** 오프라인 Playwright로 `window.__EC2_LAB__`의 모든 프로브 상태(`listProbeStates`/`applyProbeState`)를 `1440`·`375` 폭과 `light`·`dark` 테마에서 순회하며 콘솔/페이지 오류, 미등록 외부 요청, 가로 스크롤·오버플로, KaTeX 렌더링, `0.6em` `label_gaps`, 모바일 단일 서랍·`Escape` 닫기를 검증해 `defect_count === 0`(종료 0)을 확인한다.
- **게이트 4 (실제 브라우저 확인):** `probe_interactive.py` 통과 후 **Codex 내부 브라우저(`iab`)를 우선** 사용한다. `cua_repl`에서 로컬 HTTP 미리보기의 `preview.html`을 열고, `1440×900`·`375×812` 각각에서 라이트·다크를 확인한다. 예측 카드가 있으면 응답 → 회로에서 확인 → 관측값·설명, 건너뛰기 전후 회로 유지, 설명 패널을 닫았을 때의 위치를 확인한다. 해당 실험의 포트 팝오버(`Enter`/`Space`/`Arrow`/`Escape`), 소자 토글, 슬라이더 끝값, `+Δv` 인과 맥동, 근사 플롯도 직접 조작한다. 대표 수치·상태 변화, 라벨 겹침, 패널 대비와 콘솔 오류를 확인한다.

**로컬 HTTP 미리보기:** `127.0.0.1`에만 바인딩하는 임시 서버에서 이번 검증에 필요한 HTML과 참조하는 로컬 리소스만 제공한다. 정리노트와 실험 파일을 함께 검사할 때 상대 URL이 동작하도록 원래 상대 위치를 유지한다. 테스트한 URL은 검증 기록에 남기고, 작업용 서버는 검사 후 종료한다. 사용자가 미리보기 주소도 요청했다면 접속 가능한 임시 주소를 전달한다.

**Playwright 폴백:** `iab` 도구가 없거나, 허용된 미리보기 접근·뷰포트 설정·조작 확인이 해당 세션에서 불가능할 때 남은 게이트 4 항목을 Playwright 브라우저에서 같은 조건으로 직접 조작하고 화면을 확인한다. 브라우저 정책이 차단한 동작은 해당 제한을 따른다. 관찰된 UI 결함은 수정하고 다시 검사한다. 게이트 3의 오프라인 Playwright 프로브는 매번 실행한다.

`RUN/<n>/validation.json`에 `lab.js`의 현재 `source_sha256`과 4개 게이트(`machine`, `numeric_independent`, `probe`, `browser`)의 `pass`/`fail`/`not_run`, 독립 검산 기준값, 발견/수정 내역을 기록한다. 브라우저 증거에는 항목별 실제 브라우저, URL, 뷰포트·테마, 조작 결과와 폴백을 썼을 때의 이유(`fallback_reason`)를 남긴다. 소스가 바뀌면 해시와 4개 게이트를 다시 갱신한다.

### 7. 저장 (`save.cjs`)

4개 게이트가 모두 `pass`이고 `validation.json`의 `source_sha256`이 현재 `lab.js`와 일치할 때만 자료별로 순차 저장한다:

```bash
node "$SKILL/scripts/save.cjs" "$RUN/<n>/lab.js" "$DEST" "<이름>"
```

출력 JSON(`{"nn", "html", "dir"}`)의 경로를 사용해 `brief.md`·`validation.json`을 `dir`로 복사한다(`save.cjs`는 `dir/lab.js`와 최상위 HTML만 쓰며 기존 번호를 덮어쓰지 않는다). 저장된 최종 HTML을 6단계의 브라우저 우선순위로 다시 열어 핵심 조작과 콘솔 오류 없음을 확인한다.

### 8. 정리노트 연결 (`link-notes.cjs`)

`references/note-links.md`에 따라 `noteHtml`의 관련 절과 저장된 자료를 대조해 `RUN/note-links.json`을 작성한다.

```bash
node "$SKILL/scripts/link-notes.cjs" "$RUN/note-links.json" --dry-run
node "$SKILL/scripts/link-notes.cjs" "$RUN/note-links.json"
```

`--dry-run`의 `skipped` 사유를 확인한 뒤 적용하고, 재실행해 `changed: false`를 확인한다. 링크는 노트 기준 상대 URL과 `target="_blank" rel="noopener noreferrer"`를 쓰며 `(새 탭)` 같은 문구를 붙이지 않는다.

### 9. 무결성 확인 및 보고

- 정리노트 연결에서 `added`만 있으면 삽입된 `<p class="interactive-note" data-ec2-interactive="...">` 블록을 제거했을 때 백업 원 HTML과 바이트 단위 동등한지 확인한다(`updated`는 해당 링크의 `target`/`rel` 보정 외 원문 바이트 유지).
- 정리노트 링크와 위젯을 브라우저에서 검증할 때도 6단계의 우선순위를 따른다. 관련 절에서 링크를 직접 열어 기존 노트 탭이 유지되고 새 탭에서 저장된 실험의 핵심 조작이 작동하는지 확인한다.
- 기존 정리노트 MD·PDF·그림의 SHA-256이 작업 전과 같은지 대조한다.
- 저장된 실제 절대 경로, 주제 선정 이유(아키타입 및 `.widget` 확장 근거), 4개 게이트 결과와 수정 내역, 연결 절별 `added`/`updated`/`unchanged`/`skipped`, 보류 사유, `RUN`/백업 경로를 보고한다. 실행하지 않은 검사는 완료로 보고하지 않으며, 요청이 없으면 커밋하지 않는다.
