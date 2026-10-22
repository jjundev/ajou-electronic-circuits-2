# 사용자 방식의 정식 풀이 — 여섯 문항 통합 HTML 실험 검토

2026-10-22, `codex/ec2-learning-style`, 기준 커밋 `36f17b6`. 사용자 확정 #5(원본 workbook 풀이 포함), #6(대표 여섯 문항), #7(단계별 이유 연결)에 따라 구현했다. 자동 커밋·push는 하지 않았다.

## 결과와 범위

E9.05, E9.06, E9.01, P9.23, E9.11, P9.30의 실제 workbook MD는 `## 풀이`부터만 교체했다. 각 파일의 이전 접두부가 바이트 단위로 동일함을 확인했다. 문제 원문·조건·그림·검증용 원문 답은 보존했다.

대표 HTML/동반 MD는 `문제를 읽어요 → 이 문제를 봤을 때 떠올릴 개념과 공식 → 종이에 쓸 첫 줄 → 이렇게 풀어요 → 완성 답과 검산 → 주의할 점 → 조건을 바꾸어 생각해요` 순서다. 별도 핵심 풀이 블록을 없애고 승인된 계산 경로를 실제 start/solve/verify에 통합했다. 중복 그림은 제거하고 측정 조건이나 근사 모델이 다른 그림은 유지했다.

공통 스킬·개인 명세·조립기·발행 검사 기본값은 바꾸지 않았다. 이 결과는 별도 실험본이다. 공통 EPE의 core-first 계약과 answer-overlay 승인을 통과한 정식 발행이라고 표시하지 않았으며, `pilot-manifest.json`에 실험 계약과 사용자 명시 예외를 기록했다. 새로운 corpus에 수정 MD를 복사하고 extract를 다시 수행했다. 이전 대표 HTML·MD·답안 PDF는 SHA-256 동일함을 확인했고, 새 PDF는 생성하지 않았다.

## 실제 검증

- 9장 MD 형식 검사: 110개 파일, 오류 0개. `git diff --check` 통과.
- 독립 수학 검산: 작성자와 다른 에이전트가 새 풀이를 읽기 전에 회로/조건에서 KCL·수치를 유도해 저장한 뒤, 최종 여섯 MD·여섯 조각의 일곱 소문항과 대조했다. 최종 수정 회로의 접속·측정 조건도 다시 대조했다. P9.23의 유한 β 및 추가 근사 조건을 보존했다. 출력저항 정확식·수치 대조는 내부 검산에만 두었다.
- 원문 검토: 원본 PDF 2,4,5,9,10,11,24,25쪽 이미지와 문제 그림을 사용했다. 전체 쪽은 contact sheet, 24·25쪽은 개별 이미지로 대조했다. 일부 원본 예제 쪽에는 인쇄 풀이가 함께 보였으므로 답안이 전혀 시야에 없었던 검산이라고 주장하지 않는다. 검산자는 해당 답을 의도적으로 읽거나 추출하기 전에 KCL에서 새 유도를 저장했다.
- 독립 내용 검토: 일곱 소문항 × 열두 규칙의 의미 검토, 재도전 질문 독립 답안 대조, 본문·요약·원본 MD·동반 MD의 조건/경로/결과 일치 확인.
- 브라우저: 1280×900, 1024×900, 375×812 각각 light/dark 여섯 조합. 모든 측정은 visible 상태, 로컬 자원만 사용. 수식 오류·달러 원문 노출·그림 깨짐·문서/요약 가로 넘침·콘솔 오류 없음. 원문/문제 탭 동작 확인.
- 시각 검토: 최종 회로 일곱 개를 light/dark 열네 이미지로 모두 열어 확인하고 데스크톱/모바일 상단도 확인했다. 노드 전압 라벨/점 26개 테마 쌍의 실제 계산 색이 일치하며 도선과 실제 글리프 간격도 측정했다. 실제 T 분기점 열네 곳을 별도로 열거해 검증했다.

## 검토에서 고친 점

P9.23(b)의 유한 β 단락 KCL 앞에 그 계산에 맞는 전체 모델을 배치하고 출력 단락을 실제 접지 도선으로 표시했다. 접지 전압 라벨은 중립색으로 두며 비분기 접지 끝점의 점을 생략했다. p1–p3 및 p4의 실제 T 접속점 누락을 고쳐, 같은 전기적 노드의 점은 같은 색으로 맞췄다. 수정 후 HTML/동반 MD를 다시 만들고 화면·내용·수학 검토의 최종 파일 해시를 다시 묶었다. 남은 내용/화면 차단 결함은 없다.

## 산출물과 근거

- HTML: `/Users/hyunjun_macbook_pro/.codex/worktrees/ec2-learning-style/전자회로2/.superpowers/ec2-integrated-pilot/output/문제설명_1021_Representative_내방식.html`
- SHA-256: `efc133ab8007cadb930131372c28762d185e72ce9fd8866066fc837151d3e83b`
- 동반 MD: `/Users/hyunjun_macbook_pro/.codex/worktrees/ec2-learning-style/전자회로2/.superpowers/ec2-integrated-pilot/output/.assets/문제설명_1021_Representative_내방식.md`
- SHA-256: `e5bc0b0dcc94817da0f34d0ed36107c262f2a1cacd4e5ac84ec7d0a7747ddfff`
- 실행 폴더: `.superpowers/ec2-integrated-pilot/` (무시되는 실험 자료이며 기존 대표본과 분리).
- 근거: `inputs.json`, `extract/review-1021-Representative/source.json`, `math/blind_derivation.py`, `math/blind-results.json`, `math-review.md/json`, `content-review.md/json`, `browser.json`, `diagram-check.json`, `junction-check.json`, `comparison-preservation.json`, `review-seal.json`, `final-verification.json`.

## 적용 경계

여섯 원본 MD의 풀이 교체는 현재 worktree에 반영했다. 이번 HTML은 한 파일 실험이며 다른 날짜 해설과 공통 생성 스킬의 기본 순서·답안 PDF 추출 구조는 그대로다. 새 사용자 흐름을 공통 생성에 채택하려면 그 계약과 추출 방식을 별도 변경해야 한다.

## 제목 문구 변경

사용자 요청으로 여섯 solve 제목을 `이렇게 풀어요`로 변경했다. 원고 조각·HTML·동반 MD와 재생성용 문구를 동기화했다. 이전 파일은 `title-change/before/`에 보존했으며, 제목 치환을 되돌리면 본문·수식·회로 바이트가 이전 검토본과 정확히 같다. manifest는 해당 파일 해시만 갱신했다. 이전 수학/내용/전체 화면 검토는 제목 변경 전 해시의 근거로 보존하고, 새 제목은 별도 실제 렌더 검사로 확인한다.

## 독립 수식의 행 분리

사용자 요청으로 서로 다른 계산 대상의 식을 각각 독립된 display 행에 배치했다. 같은 양의 `식 = 대입 = 결과` 연속 등식은 유지했다. E9.01의 gm/rπ/ro, E9.11의 NMOS/PMOS gm·ro와 나머지 묶인 display 식을 분리하고 해당 workbook 풀이의 식 사이 bullet 경계도 나눴다. 수식의 값·순서·가정은 변경하지 않았다.

`equation-lines/verification.json`은 변경 전 HTML의 main 영역에 수식 분리 변환만 적용하면 새 HTML과 바이트가 같음을 증명한다. 원본 MD 수식 span 전체와 순서, 원문 접두부, 회로 SVG 바이트도 그대로다. 새 입력으로 extract와 HTML/동반 MD 생성을 다시 수행하고 manifest를 갱신했다. 이전 수학·내용 검토는 위 동등성 근거로 유지하며 새 독립 검산을 했다고 주장하지 않는다. 최종 수정본에서 1280/1024/375 × light/dark 여섯 화면 검사 및 MD 그림/수식 대조를 새로 통과했다. p3·p5 계산 영역 이미지를 실제 열어 각 식이 독립 행에 보임을 확인했다.
