# 역할·파일 인계 계약

목표는 메인의 원문·풀이·화면 독해를 담당자에게 옮기는 것이다. 품질 기준·실제 검토·발행 게이트는 그대로 유지한다. 메인은 진입점과 이 계약을 읽고, 상세 절차는 현재 단계만 연다.

## 실행과 컨텍스트

- Codex는 `spawn_agent`에 `fork_turns: "none"`을 써서 새 컨텍스트로 시작한다. 다른 환경도 대화 전체를 복사하지 않는 서브에이전트를 쓴다. 필요한 정보는 아래 브리프 파일에 명시한다.
- 독립 작업은 **현재 가용 슬롯만큼 배치**한다. 4슬롯이면 메인+직접 작업자 최대 3명, 자식 조정자 실행 중에는 메인+조정자+작업자 최대 2명이다. 남은 작업은 대기열에 두며 순서 의존 단계는 병렬화하지 않는다.
- 이전 단계 작업을 끝내고 자식 조정자를 실행한다. 조정자는 또 다른 조정자를 만들지 않는다. 중첩 spawn이 불가능하면 조정자가 작업 브리프를 파일로 남기고 반환하고, 메인이 해당 leaf들을 실행한 뒤 같은 조정자를 재개한다. 독립 검산자/내용 리뷰어를 작성자로 대체하지 않는다.
- 수정은 기존 담당자를 재개한다(Codex `followup_task`). 담당자를 재개할 수 없을 때만 같은 브리프와 수정 요청 경로로 새 작업자를 띄운다.
- 메인이 STT·교과서·전체 후보 JSON·HTML/SVG·모든 스크린샷·자식 검토 전문을 재독하는 것을 기본 경로로 삼지 않는다. 결함 위치·해시·승인 상태가 불명확하면 필요한 범위의 근거를 직접 확인한다. lite 부모 감사는 예외가 아니라 지정된 메인 작업이다.
- 서브에이전트가 없거나 실제 검사 도구에 접근할 수 없으면 조용히 검토를 생략하지 않는다. 메인 실행이 필요한 작업을 표시하고 실제 수행하거나 미실시/보류로 보고한다.

## 브리프는 경로로 전달

메인/범위 설계자는 `RUN/briefs/<역할ID>.json`에 다음을 쓴다. 호출 메시지는 `역할`, `브리프 절대 경로`, `반환 형식`이면 충분하다. 수업 원문·PROFILE 전문·다른 역할의 전체 브리프를 메시지에 복제하지 않는다.

| 항목 | 브리프에 담을 값 |
|---|---|
| 실행 | 역할 ID, range, lite, REPO/RUN/SKILL/PROFILE 절대 경로, snapshot 파일 경로 |
| 계약 | 읽을 참조 문서와 제목 범위, manifest/scope/source-map 등 입력 파일 경로 |
| 담당 범위 | 날짜 또는 섹션/토픽/문항 ID, 필요한 STT·요약·교과서 PDF와 쪽 |
| 출력 | 허용 산출물 절대 경로, `RUN/work/<역할ID>/`, 완료/실패 인계 경로 |
| 섹션 전용 | 금지어·예고 토픽·해당 links·widget 배치·why의 뒤 토픽 목록·문제 수 |
| 선행조건 | 앞 단계 산출/검사, snapshot, 고정 입력의 해시, 수정 요청 파일(있을 때) |

snapshot **파일 경로**로 전체 객체를 전달한다. 담당자는 이를 읽고 실제 PROFILE 해시와 대조하며 manifest/source에 객체 전체를 넣는다. 경로만 받았다는 이유로 규칙·원문·참조 자료를 읽지 않아도 되는 것은 아니다.

작성·내용/개인화 감사 브리프에는 execution-guide의 `기본 근사와 회로 표기`, `전압이득의 계산 순서`, `확정한 문제 해설 형식`, `본문과 페이지 요약의 계약`, `수치 표시`, `HTML 가독성 생성·검사`도 읽을 범위로 포함한다. 이 공통 계약은 단계 밖에 있다는 이유로 누락하지 않는다. PROFILE 전체와 원문 조건을 유지한다.

## 역할과 산출

| 역할 | 직접 읽는 상세/참조 | RUN 안 산출과 인계 |
|---|---|---|
| 자료 준비자 | execution-guide `1`의 1, STT·PDF | `source-map.json`, `slides.txt`; 날짜별 PDF/미게시/추출 실패 |
| 날짜별 요약자 | stt-summary-prompt, 해당 STT 전체·자료 | `summaries/stt-<날짜>.md`; 기존 총평 3줄 |
| 범위 설계자 | manifest-guide, 모든 요약·필요한 근거 | `scope.json`, manifest 초안→선발 후 확정본, `briefs/<sid>.json`, `work/scope/decisions.md` |
| 문제 선발자 | problem-selection 전체, scope·후보·이력·원문/그림 | candidates/catalog, manifest의 problems/links, selection-review/selection, 표시 제목 후보, `work/selection/report.md` |
| 섹션 작성자 | content-rules, PROFILE, execution-guide `3`, 해당 근거; widget-rules는 담당자만 | `sections/<sid>.html`, `work/<sid>/report.md` |
| 개인화 감사자 | review-prompt의 감사 계약, PROFILE, manifest·전체 토픽 | `learning-style-audit.json`; 일반 모드 전담자, lite 메인 |
| 내용 리뷰어 | review-prompt 전체·원문 근거·선발 기록 | 전체 감사 재검토, `work/review/report.md`; lite 생략 |
| 브라우저 QA | browser-check 전체·PROFILE의 화면 기준 | `work/browser/` 증거·실제 이미지·`report.json` |
| 문제설명 조정자 | problem-explain-integration 부모 호출·형제 스킬/참조 | EXPLAIN_RUN 전체 stage/검산/검토, `child-receipt.json`; 발행 직전 반환 |
| PDF QA | 통합 계약 `답안 PDF 렌더 검토 기록`·승인 HTML/overlay | `answer-pages/`, `answer-review.md`, `answer-review.json` |

`scope.json`은 날짜별 배운 절/슬라이드·예고/금지어 근거·필요 PDF/쪽·미루거나 제외한 내용·관련 요약 경로를 보관하는 작업 인계물이다. 새 검증기 입력으로 가정하지 않는다. 기존 manifest/selection/audit/review JSON 스키마는 바꾸지 않는다.

manifest 소유권은 **설계자 초안 → 선발자 → 설계자 확정** 순서다. 동시 편집하지 않는다. 위젯은 설계자가 미리 0~2개만 지정하고 이유를 기록한다. 최종 섹션 브리프의 링크·문제 수는 선발 완료본을 따른다. 문제 수/순서가 바뀌면 선발 기록과 영향받은 브리프도 갱신한다.

## 짧은 응답과 상세 기록

각 역할은 자세한 내용·수식·원문 근거·자기 검사·결함 목록을 자신의 보고 파일에 쓴다. 메인에 반환하는 응답은 **8줄 이내**로 다음 순서다. 긴 JSON 전문이나 코드 블록을 응답에 붙이지 않는다.

1. 역할/담당 ID와 상태(`done | needs-fix | blocked`; 자식은 별도 계약의 `ready-for-publish | withheld`).
2. 산출물 및 상세 보고의 절대 경로.
3. 검사 대상 입력/산출의 현재 해시 또는 그 인계 파일 경로.
4. 건수·누락·미해결과 다음 담당; 결함은 심각도·where(topic/section/problem ID)·근거 경로.

짧은 응답의 pass나 일반 작업 인계 기록은 **기존 검사·승인 JSON을 대체하지 않는다**. 검토자는 실제 자료/화면을 확인한 뒤 기존 형식으로 기록한다. 메인은 schema/현재 snapshot·입출력 해시·대상 전체 coverage·미해결·CLI 종료 코드를 확인한다. 렌더 명령의 exit 0만으로 의미·화면 pass를 만들지 않는다.

브라우저/PDF QA는 모든 필요한 화면을 직접 확인한다. 화면·페이지 목록, 테마/폭, 실제 검사 결과, HTML/PDF/overlay 및 증거의 SHA-256을 보고 파일에 남긴다. 공용 브라우저만 있으면 순차 단독 사용하거나 메인에 구체적인 작업 요청을 인계한다. 브라우저가 없는 에이전트가 검사한 것으로 보고하지 않는다.

## 메인의 상태와 발행 경계

- `RUN/run-status.json`에는 현재 단계, 역할별 상태/agent ID/브리프/산출/보고 경로, 최초 백업 경로, 현재 manifest·snapshot·노트 해시, 내용 수정 횟수와 **기계/브라우저 공통 수정 횟수**, EXPLAIN_RUN·발행 결과·복구 경로를 저장한다. 긴 내용 대신 경로로 이어진다.
- 명령의 장문 stdout/stderr는 `RUN/work/<역할ID>/` 로그에 저장하고 메인에는 종료 코드·검사 요약·오류 위치만 출력한다. 실패 시 해당 오류 부분을 읽는다. 원본/증거 전체를 터미널에 출력해 인계하지 않는다.
- 메인만 최초 백업·정리, 표시 제목 맵 반영, assemble/MD 변환, 복습노트로의 epe publish/답안 publish, 전체 복구와 최종 검사를 실행한다. RUN 내부 후보/렌더/의미/화면 검토는 위임한다. `RUN/repo`는 쓰기 권한의 예외가 아니다.
- source/manifest/HTML/명세 변경은 관련 작성·감사·화면 검토를 무효화한다. 자식 extract 후 고정 입력이 바뀌면 부모 재검토와 새 EXPLAIN_RUN이다. 스냅샷 교체나 오래된 pass로 통과시키지 않는다.
- 컨텍스트가 압축되거나 담당자가 바뀌면 run-status와 현재 인계/검사 파일을 읽고 이어간다. 이미 끝난 원문 독해·작성·검토 대화를 다시 펼치지 않는다. 최종 완료 여부는 메인이 실제 발행 게이트/최종 검사와 복구 상태로 판정한다.
