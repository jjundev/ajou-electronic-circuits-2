# 통합 해설 실행기 및 대표 산출물 최종 검토

2026-10-22 · codex/ec2-learning-style · HEAD 36f17b6 위 미커밋 변경.

## 결과

공통 조립·검사·답안 추출이 통합 일곱 구역을 처리한다. ‘문제를 읽어요’와 ‘이 문제를 봤을 때 떠올릴 개념과 공식’ 다음에 정식 사용자 풀이를 연결하고 solve 제목은 ‘이렇게 풀어요’다. 새 저작에는 별도 core route·구형 표지를 거부한다. 기존 보이는 본문에 data-answer-step/data-answer-final을 붙여 답안 내용을 선택하며 사본을 만들지 않는다. 독립 계산은 별도 display에 두고 같은 양의 연속 등식은 유지한다.

과거 발행 자료의 순수 legacy 추출은 무결성 검증용으로 유지한다. 혼합 형식, 중첩 선택, 누락 소문항, 불명확한 start 범위, 잘못된 제목·구역 순서는 거부한다. img/svg 자체 선택 시 외곽 요소를 보존한다. rerender도 통합 구조를 검사하고 기존 검토 이월·참조·명세·입력 해시 게이트를 유지한다.

workbook은 승인 overlay의 답안만 단계 경계에서 다음 페이지로 이어 붙인다. 수식·회로 DOM을 이동하며 내용이나 순서를 바꾸지 않는다. 긴 답안에 맞추어 글자를 줄이지 않는다. 너무 큰 단일 요소/답의 아래 경계 넘침은 계속 오류다. 비-overlay A4의 기존 자동 맞춤은 유지한다.

## 산출물

작업 루트: `.superpowers/ec2-integrated-runtime/`.

- HTML: `corpus/복습노트/1021/문제설명_1021_Representative.html`
  - SHA256 baa26ff534cfffa76076580d65ce546f6d08731cc8db5b28089ab3a999a95731
- MD: `corpus/복습노트/1021/.assets/문제설명_1021_Representative.md`
  - SHA256 d2fa08529b2aa00d0b0af36456b557f1abe53b80e0b713ea89ff43e766913bec
- 답안 PDF: `corpus/복습노트/1021/복습문제_1021_Representative-답안.pdf`
  - SHA256 b4aafc6b1ea1313226b2e7503fea7971237e4530bae5b35842ebf491d713a77c

대상은 E9.05, E9.06, E9.01, P9.23(a,b), E9.11, P9.30이다. 정상 EPE extract/build/check/publish를 사용했으며, 그 발행 overlay를 정상 workbook CLI가 소비했다. 답안은 화면 검토 후 publish_answer.py로 정확한 소유 폴더에 설치했다. 실험 전용 조립기나 가짜 validation을 쓰지 않았다. 이전 pilot 및 비교용 대표 산출물은 보존했다.

## 검토 근거

- EPE 전체 208 tests + 92 subtests pass.
- review-pack 전체 185 tests + 183 subtests pass, 기존 1 skip.
- workbook 전체 193 tests + 174 subtests pass.
- 합계 586 tests + 449 subtests pass. 기존 PyMuPDF deprecation 경고 8개는 각 실행에 남는다.
- 구형 route 의존으로 생긴 rerender 실패와 리소스를 구역 밖에 넣던 테스트 fixture를 새 계약에 맞게 수정했다. 기존 리소스 경로·중복 SVG ID 검사 목적은 보존했다.
- 독립 코드 리뷰에서 발견한 미디어 외곽 손실, 혼합 형식 누락, 구형 rerender, 답 전용 페이지 아래 경계, 비-overlay 글자 맞춤 회귀를 실패 재현 테스트 후 수정했다. 최종 독립 코드 리뷰 추가 결함 없음.
- 독립 수학 검산: 7 소문항·retry 모두 pass. 먼저 유도를 저장한 뒤 현재 본문과 대조했다. P9.30은 입력에 일반 gm/ro/이득 참고식이 제공되어 참고 공식 기반 독립 유도로 명시하며 완전한 무답 노출 검산이라고 부르지 않는다.
- 내용 검토: 독립 리뷰어의 7×12 개인화 판정, 선택 답안·MD·요약·조건·부호·단위 대조 pass. 발견한 retry 반복, 생략 전류 표시, KCL 중간 단계, 무부하 회로 조건, 요약/선택 답안의 근사 조건 누락을 보완했다.
- 원문: 새로 렌더한 9장 PDF 2/4/5/9/10/11/24/25쪽 및 여섯 원문 그림을 대조했다. 실제 workbook 질문·조건·그림 prefix와 corpus 입력 바이트 보존 확인.
- HTML: 1280×900, 1024×900, 375×812 × light/dark 6조합 pass. 수식·콘솔·누락 자원·문서/요약 가로 넘침 0. 8회로×2테마 개별 이미지 16장 및 32 전압-색/간격 쌍 검토.
- PDF: 실제 11페이지 PNG를 독립 리뷰어가 모두 개별 열람했다. 72단계·8회로·7소문항과 최종 답 보존. 단계/답 아래·오른쪽 경계, 글자 배율 1, 16:9, 자막 띠 공백 확인. 정확 Rout 전체식 노출·잘림·겹침 없음.

상세 기록: `final-verification.json`, `content/content-review.json`, `content/pdf-review.json`, `math/current-comparison.json`, `source-review.json`, `browser.json`, `diagram-check.json`, `pdf-geometry.json`, `source-preservation.json`, `answer-review.json`, `answer-backup/receipt.json` 및 정상 발행 자료 폴더의 manifest/validation/overlay.

커밋·push·브랜치 변경은 하지 않았다.
