# 전자회로2 개인 풀이 명세 통합 검증 — 2026-10-21

대표 6문항·7소문항의 실제 핵심 풀이와 상세 HTML/MD를 저작하고, 작성자와 다른 검산자·내용 리뷰어의 검토를 거쳐 임시 corpus에 발행했다. 승인된 핵심 풀이 overlay를 실제 workbook CLI가 소비한 답안 PDF도 검토 후 안전 발행했다. 기존 수업 날짜 폴더나 원본 문제·PDF·그림·손풀이는 변경하지 않았다.

## 검증 범위와 결과 위치

- 개인 명세: `docs/learning/solution-style.md`, SHA256 `0e16323519ab712526b9eea11de4cd10d3ea5d1af974f60e3ad73a15edcd7183`. 작성자·내용 리뷰어가 실제로 읽었다.
- 보존 RUN: `/Users/hyunjun_macbook_pro/.codex/worktrees/ec2-learning-style/전자회로2/.superpowers/ec2-learning-style-validation`. 자체 `.gitignore`가 있으며 폐기 가능한 SDD 작업 폴더 밖에 있다. 아래 증거 경로는 이 RUN 기준이다.
- HTML: `corpus/복습노트/1021/문제설명_1021_Representative.html`.
- MD·overlay·발행 검토: 같은 팩 `.assets/문제설명_1021_Representative.md`, `.assets/자료_문제설명_1021_Representative/{answer-overlay,validation}.json`.
- 답안 PDF: `corpus/복습노트/1021/복습문제_1021_Representative-답안.pdf`. **총 7쪽: 6문항 답안 + 기존 E9.06 Hint 1쪽**이다.
- 최종 stage: `explain/review-1021-Representative/stage/e7002d1e10b24dccbd866ff00aec8378`.
- HTML SHA256: `8d4e00d238946011e7067c07aa9367fd93fcf9c4cfc924f0a45ab0941c43c200`.
- PDF SHA256: `07be9193cf23261b060df8e719d2360ddb0f4d576cd2dd2606e681da2c00fa85`.

corpus의 최소 정리노트는 링크 확인용 fixture다. 실제 검증 범위는 여섯 문제설명과 그 핵심 답안이며, 개인화된 부모 개념 노트 전체를 저작·검토했다는 뜻은 아니다. 문제 PDF는 여섯 실제 원문으로 별도 렌더했다.

## 실제 수학·내용 검토

네 E 예제는 `blind-e-math`, P9.23/P9.30은 `independent-math`의 별도 검산자가 원문 조건에서 먼저 풀었다. 초기 다른 검산자의 E 예제 답안 노출은 공개되어 있으며 그 검토를 blind E 근거로 재사용하지 않았다. 최종 작성물과의 대조 보고서는 각 폴더 `final-comparison.md/json`에 있다. 여섯 `pN-sympy.py`와 실행 결과는 build 전에 bucket `evidence/`에 복사했고 최종 stage에도 동일 바이트로 포함했다.

별도 내용 리뷰어의 `content-review/review-records.json`은 최종 HTML/MD에 연결된 7소문항 판정과 **84개 규칙별 적용·비적용 근거**를 담는다. retry는 리뷰어가 질문만 보고 먼저 푼 뒤 작성자 답과 비교했다. 이는 학생의 숙달 측정이 아니다.

| 문항 | 반영·검산 사례 | 최종 판정 |
|---|---|---|
| E9.05 | μA→mA, 20 kΩ 중간값, 목표→5/4 mS→W/L15.625 역산. 주항 설계와 전체 모델13.225를 구별하고 540/500 kΩ로 검산. | pass |
| E9.06 | RP가 위 M1의 D–S에 연결됨을 그림으로 확인. ra=ro1∥RP 치환, 정확식과 두 주항 조건, RP→0에서 ro2 검산. | pass |
| E9.01 | 원문에 없는 VT26mV 가정을 명시. 1/26 S=1000/26 mS와 유한 β 병렬을 복원. 주항328.947 kΩ와 전체335.658 kΩ 구별. | pass |
| P9.23 (a/b) | 위 Q2 입력·이미터 축퇴, 단락 Gm와 입력 영점 Rout 분리. 유한 β 정확식과 추가 큰 β 근사 조건 유지. 같은 조건의 보통 캐스코드보다 작은 전압 이득을 명시. | pass |
| E9.11 | 소자별 gm/ro→Ron/Rop 병렬→−GmRout. 내부 반올림 없이−319.516 V/V, 교재−318은 중간 반올림 차이로 설명. 중복 Vb2 인쇄 표기와 AC 해석 한계를 보존. | pass |
| P9.30 | ID·L·λ·공정 상수 고정→각 gm의 √N→이득 N배. 반전 부호와 주항 조건 유지. 원문의 잘못된 식9.79 참조를 보존하고 직접 유도. | pass |

수치 바이어스 허용 범위를 묻지 않은 문항에 BIAS 규칙의 부등식을 억지로 추가하지 않았다. 회로·단위·부호·근사 조건은 핵심, 상세, 요약, MD 사이에서 독립 대조했다. 원본 시각 대조는 여섯 PDF crop과 최종 stage 원문 필드·그림 해시를 비교했다.

## 실제 브라우저·PDF 확인

최종 `browser-release.json`, `browser-release-1024.json`: 1280×900, 1024×900, 375×812의 light/dark **6조합 통과**. 문서 가로 넘침, KaTeX 오류, raw dollar, 누락 이미지, 외부 요청, 콘솔 오류가 없었다. viewport 캡처 전체를 실제로 확인했고, 재작성 후에는 이전에 본 이미지와 바이트가 같은 캡처를 확인하고 바뀐 p4 네 캡처를 다시 열었다. `headless-visual-review.json`과 `screenshot-release-equivalence.json`에 범위를 기록했다.

`browser-release-contract.json`은 **41개 실제 조작 검사**를 기록한다. 1023→1024 기본 열림·저장한 닫힘 유지, pointer 이동·크기 조절·경계, 문제/원문 탭, 모바일 접힘·펼침, 원문 그림 확대, 인쇄 시 여섯 문제·원문 보존, 네 조합의 요약 전환·읽음 저장을 확인했다. 입력에 객관식 정답 모델이 없어 정적 표시를 확인했고 채점이나 푼 문제 상태를 만들어 주장하지 않았다. 인쇄 진단 PDF는 DOM·텍스트 보존 검사이며 전체 23쪽 화면 승인으로 보고하지 않는다.

메인 에이전트는 별도로 실제 보이는 IAB에서 최종 e700 문항 이동·문제 펼침·테마·요약·목차를 조작했다(`native-browser-review-e700.json`). 앞선 1280×720 native 검사 기록은 이전 stage 기록으로 보존했고 새 HTML에 거짓으로 다시 연결하지 않았다. 중간 후보의 한 요청에서 발생한 ERR_CONNECTION_RESET은 재실행했으며 최종 6조합은 깨끗하다.

최종 답안 PDF는 `pdftoppm -png -r 120`으로 새 `answer-pages-07be9193cf23/`에 **정확히 7쪽**을 렌더했고 전부 열어 확인했다. p4의 a/b 단계·최종 답이 빠짐없이 보이고, p5의 √3/√2와 p6의 √N, 제어 전압·전류 화살표·단위·첨자가 보인다. 모든 쪽은 1440×810pt의 16:9이며 하단135pt(1080px 기준180px)에 텍스트·그림이 침범하지 않는다. `answer-review.md/json`, `answer-geometry.json`이 실제 증거다. 메인 에이전트도 5쪽을 독립적으로 열어 확인했다(`root-pdf-observation.json`).

기존 A4 기준에서 상속한 typography 설정을 유지했다. E9.01/P9.23/E9.11의 solution 계수0.8은 기존 기준에서 온 값이고 수학 scale은1이다. 이번 작업은 폰트 축소나 새 상세 PDF를 도입하지 않았다. 안전 발행 기록은 `answer-publication/receipt.json`이다.

## 실제 발견한 결함과 수정

1. **답 영역의 회로가 사라짐:** `.sol-answer`에는 그림 스타일이 없어 SVG 선의 computed stroke가 `none`이었다. 실제 렌더 회귀를 RED로 확인하고 단계·답 영역에 같은 그림 규칙을 적용했다.
2. **제곱근 기호 소실:** 실제 PDF PNG에서 √3이3처럼 보였다. 광범위한 SVG 크기 규칙이 KaTeX radical SVG 높이를0.015625px로 찌그러뜨렸다. 단계·답 영역 모두에서 `.katex svg`를 그림 크기 규칙에서 제외했다. 실제 렌더 테스트는 RED 높이0.046875px에서 GREEN으로 바뀌었고 최종 PDF에서 기호를 다시 확인했다. 폰트·페이지 배치를 바꾸지 않았다.
3. **P9.23 핵심 넘침:** 첫 PDF의 OVERFLOW는 보류했다. 중복된 핵심 식·문장만 줄이고 회로, a/b 답, 모델 조건을 유지했다. 상세 일곱 구역·요약은 바이트 그대로였다. 별도 내용·수학 리뷰가 최종 원고를 다시 승인한 뒤 렌더해 넘침이 없어졌다.
4. **retry 기호 모호함:** E9.01 질문에 `이 풀이에서 정의한 re=ro2∥rπ1`을 명시해 intrinsic emitter resistance와 혼동하지 않게 했다. 독립 리뷰어가 다시 확인했다.

## 실행·회귀 증거

실행 Python은 `.superpowers/sdd/2026-10-21-ec2-learning-style/venv/bin/python`이다. 새 런타임 의존성은 추가하지 않았다. 최종 코드 기준으로 세 suite를 별도 프로세스에서 실행했다.

| 명령 (`python -m pytest … -q`) | 최종 결과 | 로그 |
|---|---|---|
| `.claude/skills/ec2-problem-explain/tests` | 190 passed, 92 subtests, 46.06s | `suite-epe-final.txt` |
| `.claude/skills/ec2-review-pack/tests` | 185 passed, 1 skipped, 183 subtests, 26.72s | `suite-parent-final.txt` |
| `workbook/tests` | 188 passed, 174 subtests, 56.13s | `suite-workbook-final.txt` |

Skip은 분리 worktree의 형제 ML 템플릿이 없는 cross-course 비교 1개다. 브라우저·PDF 테스트를 건너뛰지 않았다. 각 suite의 기존 fitz/PyMuPDF/SWIG 경고8개는 남아 있으므로 경고 없는 출력이라고 주장하지 않는다. `git diff --check`도 통과했다.

신규 `test_personalized_pipeline.py` 7개는 실제 CLI subprocess로 extract→build→합성 검토→publish→workbook answers를 연결한다. 합성 승인은 실제 corpus에 옮기지 않았다. a/b·그림 문항, core→JSON, 원본 바이트 보존, 미검토/명세/overlay/원문/그림 변경 거부, 기존 답안 sentinel 보존을 확인한다. 부모 복구 검사는 실제 발행 묶음을 백업하고 실제 자식 입력 검증 실패를 발생시킨 뒤 문서의 복구 recipe를 실행해 노트·목록·PDF·설명 전체 바이트와 실제 consumer의 재사용을 확인한다. 이미 정상인 경로는 회귀 테스트로 기록했으며 가짜 생산 코드 실패를 만들지 않았다.

실제 실행은 `epe_cli.py build/check/publish --run <RUN>/explain`, `render-answers.py`의 실제 workbook CLI (`--mode answers --answer-overlay … --layout video-16x9`), `publish_answer.py --repo <RUN>/corpus …`로 재현 가능하다. 원본/corpus 15파일 해시 동등성은 `copied-source-preservation.json`, 손풀이 원본 보존은 메인 에이전트의 `source-preservation.json`에 있다. 전체 수업 팩 재생성, merge, push는 하지 않았다.

## 최종 전체 브랜치 검토

독립 리뷰어가 코드 기준 `0b71eaa..d1f49b1`의 변경 52파일과 발행·검토 증거를 대조했다. 판정은 **Ready to merge: Yes**이며 Critical·Important·새로 조치할 Minor 이슈는 없다. 코드·테스트를 바꾸지 않고 이 최종 기록만 덧붙였다.

[전체 코드 리뷰와 실행 중 판단 기록](2026-10-21-ec2-learning-style-final-review.md)에 범위·근거·기존 경고·미판정 경계를 기록했다. 생성물을 포함한 보존 RUN과 작업 브랜치는 통합 선택 전까지 유지한다.
