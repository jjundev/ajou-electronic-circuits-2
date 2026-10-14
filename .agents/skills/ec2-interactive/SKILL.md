---
name: ec2-interactive
description: '전자회로2 복습노트 날짜나 주제로 회로도·파형·그래프를 연동하는 인터랙티브 HTML을 만들고 기존 정리노트의 관련 설명에 새 탭 링크를 연결한다. 인터랙티브 자료 제작, 움직이는 회로 자료, 기존 인터랙티브 링크 연결 또는 /ec2-interactive [MMDD|MMDD-MMDD|주제]에 사용한다. 정리노트·문제·PDF·영상 생성은 별도 스킬이다.'
---

# 전자회로2 인터랙티브 자료

회로도·파형·보데 선도를 같은 상태와 수치 모델로 연결해요. 공통 셸은 `assets/template.dc.html`, 실행 예제는 `references/example-frequency-response.dc.html`이에요. 생성부터 검토·저장·정리노트 연결까지 진행하고 결과를 보고해요. 중간 승인을 기본 흐름에 추가하지 않아요.

**인자:** `[MMDD | MMDD-MMDD | 주제]`. 날짜는 적합한 주제 2–4개, 명시 주제는 1개예요. 적합한 후보가 하나면 하나만 만들어요. 인자 없으면 NO_ARG와 사용법을 보고해요.

**산출물:** 팩 최상위 `인터렉티브_NN_<이름>.html`, `.assets/자료_인터렉티브_NN_<이름>/`의 Main.dc.html·canvas.json·brief.md·validation.json, 정리노트 HTML의 문맥 안내 링크예요. 이름은 한국어를 쓰고 고유명사·기호만 영어로 남겨요(예: CS_이득과_대역폭).

**경로:** SKILL은 이 파일이 있는 실제 폴더, REPO는 저장소 루트, RUN은 시스템 임시 폴더의 고유 실행 ID, DEST는 resolve 결과의 folder예요. 모든 도구에는 절대 경로를 전달해요. PowerShell 변수는 호출마다 재설정하거나 절대 경로를 직접 써요. NFC/NFD 경로를 손으로 재조립하지 않고 JSON의 실제 경로를 사용해요.

링크 안내 외 정리노트 본문·위젯·스타일·스크립트, 정리노트 MD·PDF·복습문제는 유지해요. 기존 자료를 덮어쓰거나 외부 Design 게시·자동 커밋·영상·SPICE 생성을 하지 않아요.

**기존 자료 연결만 요청:** 새 자료를 만들지 않아요. 요청 범위의 노트와 기존 자료를 읽고 8–9단계를 실행해요. `전체`는 복습노트의 기존 자료 전체예요.

### 0. 준비

복습노트/, STT/, 강의노트/, 교과서/마이크로전자회로/와 Node.js >=20을 확인해요. 누락은 실제 경로와 함께 보고해요. RUN을 만들고 수정할 노트의 byte 백업과 기존 MD·PDF·그림 SHA-256을 남겨요.

### 1. 대상 풀기

`node scripts/resolve.cjs REPO 인자`를 실행하고 target.json을 저장해요. 출력은 kind, folder, exists, date, notes(`.assets/`의 정리노트), noteHtml, stt, stts, existing, next예요.

정확한 날짜 폴더를 우선하고 없으면 해당 날짜를 포함하는 범위 팩을 골라요. 범위 팩이면 모든 STT를 stts로 반환해요. MMDD-MMDD는 그 이름의 기존 팩만 허용해요. 여러 범위가 겹치면 AMBIGUOUS_TARGET을 보고하고 후보 폴더를 보여줘요. STT만 있으면 새 팩 자리예요. 주제는 H2/H3 제목을 우선하고 최신 팩을 선택해요. 없으면 복습노트/주제별/이에요. NO_TARGET·NO_ARG는 대상 처리를 중단해요.

### 2. 주제 고르기

`references/topic-selection.md`로 점수를 매겨요. notes·stts·강의노트·교재 범위를 대조해요. 기존 위젯을 반복하는 후보보다 추가 학습 목표가 있는 후보를 골라요. 다음 시간 예고와 부적합 후보는 제외해요. 후보 없음은 이유를 보고해요.

주제별 RUN 폴더에 brief.md를 작성해요. 회로·수식·조작 범위·모드·단계·오개념 3개·단순화·근거 절/쪽·교과서 보충·정리노트 연결을 기록해요.

### 3. 작성

`references/scene-api.md`와 `references/design.md`를 읽어요. 템플릿의 제목·좌우 슬롯·네 훅(topic, buildScene, extraState, extraVals)만 바꿔요. 공통 상단 바·테마·모바일 서랍·단계·테마 스크롤바를 유지해요. 기본은 회전 없는 평면이에요. 의미 있는 과정에만 playback을 써요.

회로 연결·AC 접지·종속원 방향·반전 부호·Hz/rad/s·선형 이득/dB를 명시해요. 화면·숫자 패널·현재 표식은 같은 모델에서 계산해요. 1014 예제는 scripts/frequency-model.cjs와 scripts/frequency-topics.cjs를 사용해요.

```powershell
node "$SKILL/scripts/make-frequency-example.cjs" cs "$RUN/cs/Main.dc.html"
node "$SKILL/scripts/make-frequency-example.cjs" two "$RUN/two/Main.dc.html"
```

그 밖의 주제는 예제를 복사만 하지 않고 적합한 모델을 구현해요. 수업 밖 내용은 패널에 `(교과서 보충)`이라고 표시해요. 단계에 f를 쓰면 phase는 해당 시점 재생 바의 ` · `로 나뉜 과정 이름과 같아야 해요(STEP_OFF_PHASE 검사).

### 4. 기계 검사

`node scripts/check.cjs Main.dc.html`, `node scripts/steps.cjs Main.dc.html`을 실행해요. 셸·마크업 구멍·이벤트·단계·빈 장면·NaN 오류를 해결하고 기본·대표 설정·조작 끝값을 테스트해요. 테스트는 `node --test`로 tests/*.test.cjs 전체를 실행해요.

### 5. 내용·독립 수치 검토

작성자가 아닌 검토자에게 Main.dc.html·브리프·실제 근거 자료·steps 출력을 전달해요. `references/circuit-verification.md`에 따라 회로 연결·문구·단계·근사 조건을 대조하고 별도의 복소수 전달함수로 기본·대표 설정·끝값을 검산해요. 계산 모듈을 다시 호출하는 것은 독립 검산이 아니에요.

허용된 실제 도구와 모델을 사용해요. 고정 모델 치환을 가정하지 않아요. 별도 검토를 수행할 수 없으면 not_run을 남기고 그 자료를 보류해요. Critical/Important를 모아 한 차례 수정하고 관련 검사를 다시 수행해요. 해결하지 못하면 해당 자료만 보류해요.

### 6. 브라우저 확인

`node scripts/build.cjs Main.dc.html preview.html`로 빌드해요(assets/dc-runtime.js 내장). RUN만 localhost 서버로 제공하고 자신이 띄운 프로세스 ID를 기록해요. Windows Start-Process는 -WindowStyle Hidden을 사용해요.

1440×900·375×812에서 라이트·다크 모두 확인해요. 콘솔 오류, 가로 스크롤, 잘린 라벨을 검사하고 모든 슬라이더 끝값·대표 설정·모드·단계·재생/정지·스크럽·속도·패널 너비·서랍·Escape를 실제 조작해요. 극점·전체 대역폭·단위·파형과 패널을 대조해요. VM draw만으로 브라우저 pass를 기록하지 않아요.

validation.json에는 현재 source_sha256과 machine/content/numeric_independent/browser의 pass/fail/not_run 및 실제 증거, assumptions, supplements, findings를 기록해요. 소스가 바뀌면 해시와 관련 검토를 갱신해요.

### 7. 저장

네 검토가 모두 pass이고 해시가 일치할 때만 자료별로 순차 저장해요.

```powershell
node "$SKILL/scripts/save.cjs" "$RUN/<n>/Main.dc.html" "$DEST" "<이름>"
```

출력 JSON의 nn/html/dir을 사용해요. Main.dc.html과 canvas.json은 도구가 만들어요. brief.md·validation.json을 dir로 복사해요. 저장된 HTML을 다시 열어 핵심 조작과 콘솔을 확인해요. 번호는 기존 HTML과 .assets 제작 폴더를 모두 세고, 배타적으로 파일을 만들어 덮어쓰지 않아요. 실패 시 자신이 만든 부분 파일만 정리해요.

### 8. 정리노트 연결

`references/note-links.md`대로 실제 저장 경로와 절을 대조하여 RUN/note-links.json을 작성해요. 관련 설명 바로 뒤에 관찰할 내용을 담은 한 문장과 새 탭 링크를 넣어요. 표식은 data-ec2-interactive예요. 상대 URL·target="_blank" rel="noopener noreferrer"를 사용해요. `(새 탭)` 같은 표시 문구는 붙이지 않는다.

`node scripts/link-notes.cjs 명세.json --dry-run` 결과를 읽고 skipped 이유를 확인한 뒤 apply해요. 재실행 changed:false를 확인해요. 링크 목적지가 모두 존재하고 새 탭에 올바른 자료가 열리며 원 노트가 유지되는지 확인해요. added만 있으면 삽입 문단을 제거한 결과가 원 HTML과 byte-equivalent여야 해요. updated가 있으면 기존 링크의 target·rel 보정만 허용하고 나머지 원문 바이트를 대조해요. 기존 MD·PDF·그림 해시를 대조해요.

### 9. 보고

실제 자료 절대 경로, 주제 선정 이유·모드·조작·가정·보충, 검토 결과와 수정, 연결 절별 added/updated/unchanged/skipped, 보류 이유, RUN/백업 경로를 보고해요. 실행하지 않은 검사는 완료로 표현하지 않아요. 커밋은 요청이 있을 때만 해요.
