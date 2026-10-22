---
name: ec2-review-pack
description: 전자회로2 수업의 STT·강의노트·Razavi 교과서로 ELI5 정리노트 HTML(+MD, 그림)을 만들고, 수업 범위에 맞는 미사용 workbook 문제를 기출 우선 최대 20개 선발해 복습문제 PDF(문제+답안)와 검토를 통과한 문제설명 HTML·MD를 날짜별 폴더에 저장한다. 참고 풀이 없는 문제도 직접 풀고 독립 검증한다. "정리노트", "복습문제", "복습팩", "0923 정리해줘" 또는 /ec2-review-pack [MMDD|MMDD-MMDD] [lite]에 사용한다.
---

# 전자회로2 복습팩

메인은 진행·검사 결과·발행을 관리한다. 원문 독해·범위 설계·선발·작성·의미/화면 검토는 **새 컨텍스트의 서브에이전트**가 수행하고 파일로 인계한다. 중간 질문 없이 끝까지 진행하고 커밋은 제안만 한다. 진행은 단계마다 한 줄이다.

인자: `[MMDD | MMDD-MMDD] [lite]`. 산출물은 `복습노트/<range>/`의 정리노트 HTML·문제/답안 PDF·문제설명 HTML이며 MD·그림·목록·자료는 `.assets/`, 선발 검토는 `.pack/`에 둔다. 문제 0개면 PDF·문제설명을 만들지 않는다.

- `SKILL`: 이 파일의 폴더. `REPO`: `git rev-parse --show-toplevel`. `RUN`: `<scratchpad>/review-pack/<range>/`의 새 실행 폴더. `PROFILE`: `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md`.
- 모든 경로는 절대 경로로 전달한다. 에이전트는 지정된 RUN 산출물과 `RUN/work/<역할ID>/`에만 쓴다. 원본 자료는 읽기 전용이다. **최상위 메인만 `복습노트/` 변경·발행·복구를 실행한다.**
- `lite`: 요약·정리노트 작성자는 sonnet(GPT: luna), 부모 내용 리뷰는 생략한다. **부모 개인화 감사는 메인이 실제 수행한다.** 기계·브라우저 검사, 자식 작성 모델·독립 검산·네 검토는 유지한다. 일반 모드의 작성·의미 검토는 opus(GPT: sol); 실제 사용 가능한 모델 ID로 매핑한다.

처음에는 [역할·파일 인계 계약](references/delegation.md)만 읽는다. [단계별 상세](references/execution-guide.md)는 아래에서 지정한 **현재 단계의 제목 범위만** 읽는다. 작성자용 지침·PROFILE 전문·자식 스킬 전체를 메인에 일괄 적재하지 않는다. lite 실제 감사 및 구체적인 실패 조사 때는 해당 근거를 직접 읽는다.

## 절차

### 0. 준비
메인은 상세 `0. 준비`로 저장소·날짜·RUN을 확정하고 `workbook/learning_style.py snapshot`을 실행한다. 필수 자료가 없거나 대상 STT가 없으면 기존 안내/중단 규칙을 따른다. PROFILE 존재와 snapshot을 확인하고 정상 모드의 본문 독해는 담당자에게 맡긴다.

`RUN/run-status.json`에 경로·range·lite·snapshot 경로·단계·역할별 agent ID/산출 경로·수정 횟수·발행/복구 상태를 저장한다.

### 1. 범위 파악
자료 준비자가 상세 `1. 범위 파악`의 1대로 STT·PDF를 조사해 날짜별 자료/누락이 있는 `RUN/source-map.json`과 슬라이드 번호를 보존한 `RUN/slides.txt`를 만든다. 추출 완료 뒤 날짜별 요약자를 가용 슬롯만큼 실행한다.

요약자는 [STT 요약 지시문](references/stt-summary-prompt.md)을 읽고 `RUN/summaries/stt-<MMDD>.md`에 전문 요약을 쓴다. 메인은 완료/누락 상태만 받는다.

### 2. manifest와 문제 선발
범위 설계자가 요약과 [manifest 규칙](references/manifest-guide.md)을 읽고 `RUN/scope.json`과 `RUN/manifest.json`의 범위·토픽 초안을 만든다. 첫 why·마지막 요약/예고·범위 경계를 유지한다.

이어서 문제 선발자 1명이 [선발 규칙](references/problem-selection.md)대로 후보/미사용 기출 전체·실제 그림·모든 소문항을 검토한다. candidates/catalog 생성, manifest의 problems·PDF 링크, `selection-review.json`, `selection.json`, `RUN/work/selection/display-titles.json`을 작성한다. 기출 우선 최대 20개·다른 회차 사용 제외·전체 문항 채택·무해설 차별 금지를 유지한다. 선발 0개 이유도 기록한다.

범위 설계자를 재개해 최종 manifest·위젯 0~2개 배치·`RUN/briefs/<sid>.json`을 확정한다. manifest는 한 번에 한 담당자만 쓴다. 메인은 `scripts/manifest.py <manifest> <REPO>`의 OK와 ID 순서·건수·snapshot을 확인한다. 결함은 담당자에게 돌린다.

### 3. 섹션 작성
메인은 섹션별 브리프 경로로 작성자를 배치 실행한다. 작성자는 [내용 규칙](references/content-rules.md), [PROFILE](references/solution-style.md), 상세 `3. 작성`의 교육·회로·표기 계약을 직접 읽는다. 위젯 담당자만 [위젯 규칙](references/widget-rules.md)을 읽는다. 산출은 `RUN/sections/<sid>.html`과 `RUN/work/<sid>/report.md`다.

자기 검사·적용 질문·규칙 적용/비적용 이유는 보고 파일에 보존한다. 짧은 반환은 학습 내용이나 검토 범위를 줄인다는 뜻이 아니다.

### 4. 조립과 문제지
메인은 상세 `4. 조립`과 [통합 계약](references/problem-explain-integration.md)의 기존 설명 백업/복구 절만 읽는다. 첫 변경 전 기본 팩·설명 백업의 전체 경로·SHA-256을 검증한다. 실패하면 변경하지 않고 재조립에서는 최초 백업을 덮지 않는다.

검증 후 표시 제목 맵을 반영하고 `scripts/assemble.py`로 조립한다. `workbook/build_workbook.py --ids ... --mode problems --selection ... --display-titles ... --layout video-16x9 --pdf-dir ... --build-dir ...`로 **문제지만** 만든다. 정확한 명령/manifest 순서 추출은 상세를 따른다. 원본 MD 오류만 정책대로 교체하며 렌더 오류/OVERFLOW 때문에 문항을 바꾸지 않는다.

### 5. 개인화 감사와 기계 예비 검사
일반 모드는 작성자가 아닌 전담 감사자가 [리뷰 지시문](references/review-prompt.md)의 모든 topic ID·모든 rule ID를 실제 읽고 `RUN/learning-style-audit.json`을 쓴다. lite는 메인이 같은 실제 감사를 수행한다.

메인은 `scripts/check_html.py`를 명시 repo/manifest/note로 실행한다. 문제 1개 이상일 때만 `--defer-answer-pdf`를 쓴다. `PRELIMINARY: answer PDF pending`은 최종 pass가 아니다. 다른 결함은 담당 작성자에게 위치별로 전달한다.

### 6. 내용 리뷰
일반 모드는 작성자가 아닌 리뷰어 1명이 `references/review-prompt.md`대로 사실·범위·선발·적용 질문·전체 개인화 감사를 검토한다. 전문은 `RUN/work/review/report.md`, 반환은 심각도·토픽/섹션·담당자·근거 경로만이다. lite는 이 부모 내용 리뷰만 생략한다.

수정 요청은 작성자별로 모아 전달하고 메인은 재조립/재검사한다. 문제 목록이 바뀐 때만 문제지를 다시 만든다. 내용 리뷰 수정은 한 번, 기계/브라우저 결함 수정은 기존 **공통 최대 2회** 예산을 기록한다.

### 7. 브라우저 검증
브라우저 QA가 [실제 화면 검사](references/browser-check.md)를 수행한다. 자기 서버·브라우저 세션을 단독 소유하고 KaTeX·375px·다크모드·위젯·링크·콘솔·회로 표기 등을 실제 확인한다. 증거/스크린샷은 RUN에 두고 현재 HTML 해시·결함 위치·판정을 반환한다. 답안 링크는 manifest의 정확한 pending 경로만 유예한다.

브라우저가 메인에만 있으면 QA의 검사 요청 파일에 따라 메인이 수행하고 증거를 돌려준다. 접근 못 한 화면을 pass로 기록하지 않는다. 수정 뒤 관련 증거를 갱신하고 소유 서버를 종료한다.

### 8. MD 변환
메인이 `scripts/html2md.py <정리노트 절대경로> --check`의 OK를 확인한다. 누락은 작성자에게 돌려 수정→조립→관련 감사·검사를 다시 한다. 변경된 HTML의 이전 해시 검토는 재사용하지 않는다.

### 9. 문제설명·승인 답안·최종 검사
문제 0개면 skipped-no-problems: snapshot·전체 토픽 감사·유예 없는 최종 노트 검사까지 수행한다.

문제 1개 이상이면 **문제설명 조정자**가 통합 계약과 형제 `ec2-problem-explain`을 읽고 새 EXPLAIN_RUN에서 extract→저작→독립 검산→build/check→네 실제 검토·전체 감사를 진행한다. 메인은 자식 원문·조각·풀이·검토 전문 대신 ready-for-publish 인계 기록을 받는다. **최상위 메인만** 기존 `epe_cli.py publish --run <EXPLAIN_RUN>`를 실행해 발행 게이트와 결과를 확인한다.

extract 뒤 노트·목록·참고 자료를 고정한다. 바뀌면 부모 재검토와 새 EXPLAIN_RUN이 필요하다. 답안은 발행된 현재 overlay/validation으로 RUN에 빌드한다(16:9, 하단 180/1080 자막 여백). PDF QA가 **모든 실제 렌더 페이지**를 승인 HTML과 대조하고 현재 해시에 묶인 `RUN/answer-review.json`을 쓴다.

메인은 상세 `9`와 통합 계약의 명령으로 `scripts/publish_answer.py`를 실행하고 `scripts/check_html.py`의 **유예 없는 최종 통과**를 확인한다. 실패/disputed/오래된 근거는 기존 전체 팩 복구 계약으로 처리한다. CLI 성공만으로 의미/화면 검토를 대신하지 않는다.

### 10. 보고
상세 `10. 보고` 형식으로 파일·문항/범위·선발 이유·기본 팩/설명/답안·감사/검사·백업/withheld·RUN/EXPLAIN_RUN·미해결·커밋 제안을 한 번 보고한다. 보고용 집계는 담당자가 RUN 파일에 기록하고 메인은 필요한 집계만 읽는다. 발행/최종 검사 실패나 withheld가 있으면 **일부 완료**다.

기존 팩에 why만 붙이는 요청은 상세 `기존 팩에 왜 페이지 붙이기` 절만 따른다. 원래 토픽 ID·백업·기계/MD/브라우저 검사를 보존한다. 오류별 중단·복구는 상세 `오류 처리`를 따른다.
