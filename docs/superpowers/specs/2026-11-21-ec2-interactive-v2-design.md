# `/ec2-interactive` v2 설계 명세

- 작성일: 2026-11-21
- 상태: 확정 (`#9`–`#12` 기본값 확정)

## 의도
전자회로2 학생이 정리노트 HTML에서 읽은 회로 개념을 회로도 자체를 찌르고·조립하고·근사를 깨뜨려 보며 직관으로 체화할 수 있도록 `/ec2-interactive` 스킬을 개편한다. 기존 3D `<canvas>` 런타임(`dc-runtime.js`, `<x-dc>`)을 폐기하고, `/ec2-review-pack`의 네이티브 SVG 회로도 규약·KaTeX 표기·Playwright 레이아웃 검사(`layout_probe.py`)를 직결한 표준 HTML/SVG 런타임과 3대 아키타입(`probe`, `bench`, `approx`) + 경량 소신호 MNA 솔버로 교체한다. 스킬 코드·문서·테스트 개편 후 가장 최근 복습팩(`복습노트/1120/정리노트_1120_Nonideal_IO_Feedback.html`)에 3개(아키타입별 1개) 자료를 실제 발행·독립검산·브라우저 자동검사·연결까지 완료한다.

## 확정된 결정 사항
| # | 결정 | 확정값 | 비고 |
|---|---|---|---|
| 0 | 전체 아키텍처 | 표준 HTML/SVG 런타임(`lab-template.html` + `lab-runtime.js` + `mna.js`) + `ec2-review-pack` 하네스 직결 | 기존 `x-dc`/3D `<canvas>` 폐기 |
| 1 | 소스·빌드 산출물 | `.assets/자료_인터렉티브_NN_<이름>/lab.js` → 최상위 단일 `인터렉티브_NN_<이름>.html` (`canvas.json` 폐기) | `save.cjs` 배타 번호·`wx`·롤백 유지 |
| 2 | SVG 스타일·CDN | `.fig-ink`/`.fig-accent`/`.fig-danger`/`.fig-dot`/`.fig-text`/`.fig-math`/`.fig-muted`, `data-node-color="blue"\|"red"`, `pretendard@1.3.9`, `katex@0.16.11` | `workbook/vendor_route.py` 오프라인 매핑과 100% 일치 |
| 3 | SVG 인터랙티브 훅 | `data-node`, `data-branch`, `data-elem`, `data-port`, `data-causal-step` 5종 | 정적 정리노트 `<svg>`를 최소 수정으로 인터랙티브화 |
| 4 | 아키타입 + 실시간 확인 | `probe` / `bench` / `approx` 3대 아키타입 + 공통 연속 입력 확인 슬라이더 | 전자회로2 전 단원 포괄 |
| 5 | 수치 계산 엔진 | 하이브리드: 경량 복소수 MNA(`assets/mna.js`) + 주제별 수업 근사식 | 독립 검산은 별도 식/노드 방정식으로 유지 |
| 6 | 레이아웃·시각 자동 검사 | `scripts/probe_interactive.py` (`layout_probe.py`의 `0.6em` `label_gaps`·`overflow`를 전 모드·배지·포트 상태에 적용) | `1440×900`·`375×812` × `light`/`dark` |
| 7 | 3단 셸·접근성 | 기존 3단 레이아웃·`<1024px` 단일 서랍·`Escape` 닫기·44px 타겟·`aria-pressed`·테마 스크롤바 계승 | `references/design.md` |
| 8 | 정리노트 연결기 | `scripts/link-notes.cjs` 유지 (`data-ec2-interactive`, 멱등성, 바이트 보존) | `resolve.cjs`도 유지 |
| 9 | 정리노트 연결 UX | 별도 새 탭 HTML (`인터렉티브_NN_*.html` + `link-notes.cjs`) 유지 | **[기본값 확정]** |
| 10 | 1초 예측 게이트 강도 | 부드러운 선택형 (상단 예측 카드 표시, 건너뛰고 즉시 조작 가능) | **[기본값 확정]** |
| 11 | `1120` 테스트 반영 범위 | `복습노트/1120/`에 3개(`bench`, `probe`, `approx` 각 1개) 실제 발행 + `정리노트_1120` 연결까지 완료 | **[기본값 확정]** |
| 12 | 기존 `1014` 인터랙티브 처리 | 레거시 그대로 보존 (`복습노트/1014` 미수정) | **[기본값 확정]** |

## 제약 조건
- Node.js `>= 20`, Python 3 + Playwright (`workbook/browser_runtime.py`, `workbook/vendor_route.py` 재사용).
- 발행 HTML 외부 리소스는 `https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css`, `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css`, `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js`, `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js`만 허용.
- 생성 SVG 수식은 `NOTATION-01` native `<text class="fig-text fig-math">` + `<tspan baseline-shift="sub" font-size="78%">` 사용(평문 `V_out`/`g_m`·SVG 내 `$...$` 금지), `CIRCUIT-02` 입력 왼쪽·출력 오른쪽 배치 유지.
- 모든 `text` 글리프와 도선 간격 `>= 0.6em`, `overflow <= 1px`, 콘솔·페이지 오류 0건.
- 정리노트 연결은 문맥 안내 문단(`data-ec2-interactive`) 추가 외 원문 바이트·MD·PDF·그림 SHA-256을 절대 변경하지 않음.
- 커밋은 사용자 요청 시에만 수행한다(구현 계획 내 체크포인트 안내 시 작업 규칙에 따른다).
