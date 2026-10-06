# ec2-review-video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 생명과학의 주제별 복습 영상 제작 흐름을 전자회로2 프로젝트 로컬 스킬로 독립 이식하고 과목 자료·회로 설명에 맞춘다.

**Architecture:** 제작 스크립트·자산·회귀를 독립 복사한다. 전자회로2의 source 연결과 단일 HTML 템플릿을 조정하고, 회로 검토 기록을 기존 단계·검증 지문에 연결한다. 콘텐츠 선정·의미 검토는 에이전트가 담당하고 프로그램은 계약과 현재 상태를 검사한다.

**Tech Stack:** Python 3 표준 라이브러리·unittest, 문제 frontmatter용 PyYAML, 로컬 GSAP·KaTeX·Pretendard, HyperFrames CLI, FFmpeg/ffprobe, Node/Puppeteer 기반 기존 브라우저 검사. 버전 업그레이드·추가 렌더 엔진은 범위 밖이다.

**Spec:** [2026-10-06-ec2-review-video-design.md](../specs/2026-10-06-ec2-review-video-design.md). 실행자는 설계와 이 계획을 함께 읽는다.

## Global Constraints

아래 값은 설계의 전역 제약을 따른다.

- 스킬 이름은 ec2-review-video, 위치는 전자회로2/.agents/skills/ec2-review-video/이다.
- 기존 생명과학 저장소·전자회로2 ec2-review-pack·STT·강의자료·교과서·workbook은 수정하지 않는다.
- 한국어 Aoede, Vertex AI Express, gemini-2.5-flash-tts, ko-KR를 기본 설정으로 계승한다. 현재 서비스 가용성을 확인했다는 뜻은 아니다.
- 1920×1080, 30fps, PCM 24000Hz, Pretendard, 다크모드 고정을 유지한다.
- 로컬 런타임 자산은 GSAP 3.13.0, KaTeX 0.16.11, Pretendard 1.3.9로 동결하며 출처·라이선스를 보존한다. 생명과학의 런타임 코드와 전자회로2 템플릿에서 확인한 버전을 따른다.
- 주제별 목표 길이는 60–180초다. 실제 음성 길이를 사용하고 필요한 개념을 길이에 맞춰 삭제하지 않는다. 사용자 요청 또는 설명상 필요한 변경은 duration_override_reason에 기록한다.
- 기본 자동 제작이다. --review일 때만 전체 선정·장면 구성을 묶어 검토한다. --resume 및 목소리 교체를 지원한다.
- budget_usd=null을 유지하고 사용량 ledger를 기록한다. 공급자·모델·목소리를 자동 대체하지 않는다.
- GOOGLE_API_KEY/GEMINI_API_KEY 또는 명시적 --env-file을 사용한다. 키나 기존 .env를 복사하거나 자동 탐색하지 않는다.
- 유료 API 호출 없는 fake transport·로컬 PCM으로 개발 회귀를 수행한다. 실제 제작은 별도 단계로 실행·보고한다.
- 출력은 복습영상/<기간>/의 제목 있는 최종 MP4 N개와 <기간>_제작자료/ 하나다. N=0도 가능하다.
- 기존 결과·이전 버전을 보존한다. 모든 선정 영상 검증 전에는 최신 결과를 교체하지 않는다.
- 이 계획 작성 단계에서는 스킬 구현·영상 제작·커밋·푸시를 수행하지 않는다. 구현 시에도 푸시와 생성 영상 커밋은 별도 요청에 따른다.

## Review Focus

- RF1: problems.txt가 없거나 ID 원문이 누락됨 — 문제 없는 노트는 제작 가능하고 누락 ID는 보고하며 관련 claim은 확정하지 않는다. Task 2.
- RF2: Unicode·중복 ID·상속 순환·저장소 밖 경로 — 조용히 다른 원자료를 선택하지 않고 명시 오류로 종료한다. Task 2.
- RF3: review-template 부재·KaTeX 파일 누락·긴 수식 — 단일 템플릿은 정상, 의존 파일 누락은 조립 오류, 수식 넘침은 브라우저 검증 실패다. Task 3.
- RF4: 그림·발화·검토 증거 변경 — 오래된 회로 검토는 TTS/최종 검증에 사용되지 않는다. Task 4.
- RF5: 일부 영상 실패·0개 선정·재음성 출력 — 성공분·이전 결과를 보존하고 전체 검증 전 최신 결과를 바꾸지 않는다. Task 5.

---

## 실행 경로와 파일 구성

- REPO: 이 계획이 있는 전자회로2 저장소. 계획 당시 절대 경로는 /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2 (실제 macOS 경로는 NFD일 수 있으므로 파일 탐색 결과를 사용).
- ORIGIN: /Users/hyunjun_macbook_pro/Documents/Univ/생명과학/.agents/skills/bio-review-video/.
- 확인한 ORIGIN 저장소 HEAD: 6f0a5153f5ffe90be5ec460fad8cf4cf7df5d592. 구현 시 작업 트리 변경을 함께 확인하고 다른 버전이면 변화가 계약에 미치는 영향을 확인한다.
- S: REPO/.agents/skills/ec2-review-video/.
- PACK: REPO/.claude/skills/ec2-review-pack/.
- 아래 명령은 REPO를 작업 디렉터리로 실행한다. worktree 실행 시 REPO만 실제 반환 경로로 바꾸고 자료 누락을 확인한다.
- 실데이터 검증은 읽기 전용이다. 테스트 산출물은 TemporaryDirectory 또는 실행자가 확보한 scratch 경로에 둔다.

| 파일 | 책임 |
|---|---|
| S/SKILL.md, S/agents/openai.yaml | 호출·단계·완료 보고 |
| S/assets/{defaults.json,vertex-direction.txt,video-layout.css,fonts/} | 제작 기본값·화면·폰트 |
| S/references/{selection-and-batches,sources-and-coverage,narration-and-motion,voice-and-budget,rendering-and-verification}.md | 기존 단계의 전자회로2 계약 |
| S/references/circuit-semantics.md | 회로 검토와 자료 예시 |
| S/scripts/lib/course_sources.py (신규) | 문제 ID·참조·그림 연결 |
| S/scripts/lib/sources.py | 노트/PDF/목록 발견·추가 출처·source ID/hash |
| S/scripts/lib/theme.py, composition.py | 단일 템플릿·로컬 수식 조립 |
| S/scripts/lib/circuit.py (신규) | 회로 검토 JSON의 구조·지문·증거 확인 |
| S/scripts/lib/state.py, verify.py, batch.py, S/scripts/video.py | 검토 gate와 단계·최종 결과 연결 |
| S/scripts/lib/{__init__,budget,cache,manifest,render,revoice,selection,subtitles,timing,vertex_tts}.py | 독립 복사한 기존 기능 |
| S/tests/ | 기존 13개 test_*.py와 아래 신규·수정 검사, 로컬 smoke·브라우저 검사 |

커밋 단계는 구현 변경의 체크포인트다. 실행 시 커밋 권한이 없으면 검증된 변경 목록만 남기고 진행하며, 권한이 있으면 각 Task의 명령으로 해당 범위만 커밋한다. 계획 작성 중에는 실행하지 않는다.

### Task 1: 독립 실행 가능한 제작 코드와 스킬 연결

**Files:**
- Create: S/SKILL.md, S/agents/openai.yaml, S/assets/, S/references/.
- Create: ORIGIN/scripts/ 전체를 S/scripts/로, ORIGIN/tests/ 전체를 S/tests/로 독립 복사.
- Create: S/tests/test_portability.py.
- Modify after copy: S/tests/test_theme.py, test_composition.py, integration_smoke.py 및 원본 과목 경로를 사용하는 다른 테스트.
- 제외: __pycache__, .DS_Store, .env, 인증·실행 결과·음성 캐시.

**Interfaces:**
- Consumes: ORIGIN의 공개 스킬 파일과 PACK/assets/note-template.html.
- Produces: 기존 CLI main(argv: list[str] | None = None) -> int와 prepare/plan-check/prepare-set/resume-set/check/tts/assemble/render/verify/publish-set/revoice/burn-subtitles 명령.
- stage·manifest schema v1과 기본 설정 값을 유지한다. 일반 정리노트 요청은 ec2-review-pack으로 연결한다.

- [x] **Step 1: 독립성 테스트 작성.** test_portability.py에 CLI --help 종료 코드 0, import된 lib 모듈의 __file__이 S/scripts 아래, 기본값 voice=Aoede/width=1920/height=1080/fps=30/sample_rate=24000/budget_usd=None을 assert한다. 템플릿 테스트가 생명과학 pack 경로를 요구하지 않도록 PACK의 임시 복사본을 사용한다.
- [x] **Step 2: 실패 확인.** Run: python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -p test_portability.py -v. 복사 전 video.py·lib 미존재로 실패해야 한다.
- [x] **Step 3: 독립 복사와 연결.** 제외 목록으로 복사하고 SKILL·openai.yaml·references의 실제 호출·경로·예시를 ec2로 바꾼다. 테스트에 남은 생물학 fixture 문구는 이 단계에서 의미 없는 전체 치환을 하지 않는다. fixture ID·assert 변경은 함께 처리한다. 기존 과목 경로를 사용하는 테스트는 임시 pack fixture로 바꾸고 review-template이 필요한 기존 회귀에는 테스트 안에서만 fixture를 제공한다.
- [x] **Step 4: 회귀 확인.** Run: python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -v. fake transport·PCM 회귀와 독립성 테스트가 전부 OK여야 한다. 아직 source 연결·단일 템플릿 실사용을 완성했다고 보고하지 않는다.
- [ ] **Step 5: 체크포인트.** git add .agents/skills/ec2-review-video && git commit -m "feat: add standalone ec2 review video workflow"

### Task 2: 전자회로2 원자료와 문제 ID 연결

**Files:**
- Create: S/scripts/lib/course_sources.py, S/tests/test_course_sources.py.
- Modify: S/scripts/lib/sources.py, batch.py, S/scripts/video.py, S/tests/test_sources.py, test_cli.py.
- Modify: S/references/sources-and-coverage.md, selection-and-batches.md.
- Tests: TemporaryDirectory에서 만든 note/PDF/list/frontmatter/figure fixture. 실제 자료는 변경하지 않는다.

**Interfaces:**
- Consumes: 기존 discover 결과와 source record {id,kind,path,sha256}; cache.file_hash.
- Produces: resolve_problem_sources(repo: Path, ids: list[str]) -> dict: {files: list[dict], missing_problem_ids: list[str], relations: list[dict]}.
- files는 {kind,path}이며 kind=problem-md/figure. relations는 {from_path,to_path,role}이고 role=depends_on/figure/reference다.
- Produces: discover(repo: Path | str, selector: str, *, extra_sources: tuple[str, ...] = ()) -> dict. 기존 range/files/missing_optional을 유지하고 missing_problem_ids/relations를 추가한다. discover가 모든 files에 기존 규칙의 안정적인 ID/hash를 부여하고 relations의 경로를 from_id/to_id로 변환한다.
- Produces: prepare_set(repo, selector, plan, config, review=False, *, extra_sources=()) -> Path. discover에 추가 출처를 전달한다.
- CLI prepare, plan-check, prepare-set에 반복 --source PATH를 추가한다. 다른 명령은 동결 스냅샷을 쓴다. --from-run과 --source의 동시 사용은 오류다.

- [x] **Step 1: 실패 테스트 작성.** test_discovers_pdf_list_and_problem_closure는 fixture의 E10.11, P10.66, 2021-1_중간-Q3와 상속 문제·PNG가 inventory에 한 번씩 들어가고 relations가 source ID로 연결됨을 assert한다. test_absent_problem_list_is_optional은 missing_problem_ids=[]와 정상 note 발견을 assert한다. test_missing_id_is_reported는 누락한 P10.99를 목록으로 반환하고 가짜 source를 만들지 않음을 assert한다. test_duplicate_id_cycle_and_escape_rejected는 각각 SourceError를 assert한다. test_explicit_sources_freeze_and_reject_outside_repo는 명시 STT/PDF 추가와 ../ 탈출 거부, snapshot 원본 hash 보존을 assert한다.
- [x] **Step 2: 실패 확인.** Run: python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -p test_course_sources.py -v. 신규 resolver·인자 부재로 실패해야 한다.
- [x] **Step 3: resolver 구현.** 기존 교과서 chNN/{예제,연습문제,장말문제}와 from_the_past/md/<회차>/Qn.md를 NFC로 탐색하고 yaml.safe_load로 필요한 id/depends_on/refs/figures를 읽는다. workbook/problem.py를 import하지 않는다. 조회 대상 ID의 중복·상속 순환은 오류, 없는 ID는 누락 목록으로 반환한다. 로컬 MD 그림 링크와 ID 참조를 따라가되 실제 repo 경계 밖·없는 참조 그림은 구체적인 SourceError다. 외부 URL은 source 파일로 다운로드하지 않는다.
- [x] **Step 4: 발견·CLI 연결 구현.** sources.py는 노트 폴더의 problems.txt(kind=problem-list), 문제 PDF(kind=questions-pdf), 답안 PDF(kind=answers-pdf)를 추가한다. extra_sources는 repo 내부 실제 파일만 받으며 supplemental-md/pdf/html/figure로 기록한다. batch·single prepare의 스냅샷 메타데이터에 relations를 보존한다. source_reviews는 figure 외 새 자료에도 실제 검토 기록을 요구한다. missing_problem_ids를 plan-check/prepare 출력에 노출하고 스킬 문서에 해당 ID 근거의 claim 확정 금지를 명시한다.
- [x] **Step 5: 검사.** Run: python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -v. RF1·RF2, 원자료 변경·범위·동결 회귀가 모두 OK여야 한다. 실자료 읽기 확인은 REPO의 0902와 1002에 discover만 호출하고 0902 정상, 1002의 PDF·목록·문제 MD 발견을 확인한다. 이 명령은 산출물·API 요청을 만들지 않는다.
- [ ] **Step 6: 체크포인트.** git add .agents/skills/ec2-review-video && git commit -m "feat: connect ec2 note and workbook sources"

### Task 3: 단일 템플릿과 회로·수식 화면

**Files:**
- Modify: S/scripts/lib/theme.py, composition.py, S/assets/video-layout.css.
- Modify: S/tests/test_theme.py, test_composition.py, test_tts.py, browser_check.mjs, integration_smoke.py.
- Modify: S/assets/defaults.json, vertex-direction.txt, S/references/narration-and-motion.md.
- Create: S/assets/runtime/fonts/Pretendard-{Regular,SemiBold,Bold}.woff2, S/assets/runtime/vendor/gsap.min.js, S/assets/runtime/vendor/katex/의 배포 dist 파일·fonts/, S/assets/runtime/SOURCE.md.
- Create: S/tests/fixtures/circuit-scene/manifest.json, scene.html, scene.motion.json.

**Interfaces:**
- Consumes: snapshot_theme(pack, run) -> dict; assemble(manifest,timeline,theme,run) -> list[dict]; stage_assets(source,run).
- Produces: 동일 signatures. theme.templates의 note와 review는 동일한 note-template 스냅샷·CSS metadata를 참조한다. theme.tokens에는 두 key가 동일 값으로 남는다.
- fixture: 명시적 이상적 MOS 소신호 차동쌍, I_SS=100μA, Δi=10μA, i1=60μA/i2=40μA와 KCL. 값·단위·가정을 화면에 표시한다. 실제 강의 예제와 동일하다고 소개하지 않는 검증용 fixture다.

- [x] **Step 1: 실패 테스트 작성.** test_note_only_supports_both_kinds는 review-template 없는 임시 pack의 note/review 조립 성공·동일 template hash·dark shell·pager/localStorage 스크립트 미실행을 assert한다. test_math_needs_complete_local_assets는 katex.min.js/css/auto-render.min.js/fonts 중 하나라도 빠지면 조립 실패를 assert한다. test_pronunciation_payload_keeps_display_text는 원문 g_m/r_O/V_GS를 보존하면서 API payload만 승인 발음으로 바뀜을 assert한다. test_circuit_state_coordinates_match_values는 fixture 좌표가 60:40 전류 비와 맞고 증가량·감소량·합을 독립 계산 값과 비교한다.
- [x] **Step 2: 실패 확인.** Run: python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -p test_theme.py -v 및 test_composition.py. 단일 템플릿·완전 로컬 asset gate가 없는 항목에서 실패해야 한다.
- [x] **Step 3: 로컬 자산 확보.** GSAP 3.13.0·Pretendard 1.3.9 공개 라이브러리 파일은 검증한 기존 로컬 배포본에서 복사하거나 해당 버전 배포본을 scratch에 확보한다. KaTeX는 템플릿과 같은 0.16.11을 로컬 패키지에서 찾고 없으면 npm pack katex@0.16.11 --pack-destination SCRATCH로 확보해 dist 파일을 assets/runtime/vendor/katex에 둔다. GSAP은 같은 방식으로 gsap@3.13.0의 dist/gsap.min.js를 쓸 수 있다. fonts의 세 WOFF2와 KaTeX CSS·JS·fonts를 함께 동결하고 SOURCE.md에 버전·출처·라이선스·해시를 남긴다. 스킬 실행 기본 --assets-from은 S/assets/runtime이다. API 키·원본 제작자료·음성은 가져오지 않는다.
- [x] **Step 4: 화면 조립 구현.** theme.py에서 note만 snapshot하고 review를 같은 metadata에 연결한다. composition.py의 KaTeX 필수 파일·fonts 검사를 보강한다. 원본 CSS는 수정하지 않고 video-layout.css로 회로·그래프·수식의 영상 배치를 조절한다. 이름이 긴 기호부터 발음 치환되도록 defaults의 순서를 명시하고 캐시 key의 pronunciation을 유지한다. 실제 발화는 기호 나열보다 설명 문장으로 작성한다.
- [x] **Step 5: 브라우저 검사 보강.** browser_check.mjs는 역방향 seek·양 OS 테마 회귀를 유지하며 .katex-error, 렌더되지 않은 math fixture, .katex-display 가로 넘침, canvas/SVG·수식 영역의 경계를 검사하고 화면 안 .video-caption 수가 0임을 요구한다. 기존 scene 크기·글꼴·token 검사를 유지한다. fixture 노드 라벨·부호는 대표 프레임을 직접 대조한다.
- [x] **Step 6: 검사.** Run: python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -v. RF3·발음 payload·수치 fixture가 OK여야 한다. browser 실실행은 Task 5에서 로컬 도구·asset을 확보한 뒤 수행한다.
- [ ] **Step 7: 체크포인트.** git add .agents/skills/ec2-review-video && git commit -m "feat: render ec2 circuit scenes from note template"

### Task 4: 회로 검토 계약과 제작 gate

**Files:**
- Create: S/scripts/lib/circuit.py, S/references/circuit-semantics.md, S/tests/test_circuit.py.
- Modify: S/scripts/video.py, S/scripts/lib/state.py, verify.py, batch.py.
- Modify: S/tests/{_util,test_cli,test_state,test_verify,test_selection}.py.
- Modify: S/SKILL.md, S/references/{sources-and-coverage,rendering-and-verification}.md.

**Interfaces:**
- Consumes: manifest schema v1, 동결 source record, scene fragments, cache.digest/file_hash.
- Produces: circuit_fingerprint(run: Path, manifest: dict) -> str: manifest + source/inputs.json + source/inputs/* + source/scene-fragments/*의 상대 경로별 hash를 digest한다. 보고서·음성·verification은 제외한다.
- Produces: validate_circuit_review(run: Path, manifest: dict) -> list[str]; require_circuit_review(run: Path, manifest: dict) -> None. 후자는 오류가 있으면 CircuitReviewError(ValueError)를 발생시킨다.
- source/circuit-review.json={schema_version:1,input_hash:str,scenes:list[dict]}.
- scene row={scene_id,checks:list[dict]}. 모든 manifest 장면이 정확히 한 번 등장한다.
- checks의 domain은 model/topology/polarity/derivation/assumptions/numeric-visual의 여섯 값이다. 각 domain을 한 번씩 작성하며 status=passed 또는 not-applicable, reason은 비어 있지 않아야 한다. source_ids는 manifest source ID 목록, locators는 출처 위치 목록이며 passed에는 둘 다 비어 있지 않아야 한다. not-applicable은 수식 없는 문맥 장면 등 해당되지 않는 근거를 적는다. 어떤 장면도 여섯 항목 전체를 not-applicable로 건너뛸 수 없다.
- 선택적 numerical 증거 파일은 RUN 내부 path/hash 목록으로 기록하며 검토기가 존재·경계·해시를 확인한다. 의미 판단·수치 식의 진위는 에이전트가 대조한다.
- verify_run의 기존 content domain에 회로 검토 결과를 결합하며 DOMAINS의 여섯 값은 유지한다.

- [x] **Step 1: 실패 테스트 작성.** test_missing_or_stale_review_blocks_tts는 load_key/live_transport가 호출되지 않음과 nonzero CLI 종료를 assert한다. test_every_scene_and_domain_required는 빠진 scene/domain, 중복, 모르는 source ID, 근거 없는 passed, 전체 not-applicable을 오류로 assert한다. test_report_not_in_own_fingerprint는 보고서 생성 전후 circuit_fingerprint 동일을 assert한다. test_modified_fragment_or_evidence_invalidates_review는 source·발화·motion 변경과 증거 hash 변조에서 오류 및 resume의 coverage/script 재개를 assert한다. test_verified_media_does_not_override_failed_circuit_review는 여섯 기존 domain 보고가 passed여도 complete=False를 assert한다.
- [x] **Step 2: 실패 확인.** Run: python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -p test_circuit.py -v. 신규 gate 부재로 실패해야 한다.
- [x] **Step 3: circuit.py 구현.** 정의한 schema·signature·오류 계약만 구현한다. 자동 KCL 증명·임의 식 eval·그래프 식 추론은 추가하지 않는다. circuit-semantics.md에 MOS/BJT·DC/AC·CM/DM·단일 종단/차동·동작영역·근사·비유의 경계를 검토 예시로 쓴다. 숫자 좌표는 식·단위·대표 입력을 독립 계산한 근거를 남긴다.
- [x] **Step 4: 단계와 최종 검증 연결.** CLI check와 tts 전에 require_circuit_review를 호출한다. coverage/script fingerprint와 check의 output_hashes에 circuit-review 및 명시적 증거 파일을 포함한다. 입력 변경 시 recover가 이 단계부터 무효화하며 기존 성공 음성 cache는 보존한다. verify_run의 content 및 batch._verified에도 gate를 연결해 보고서 조작·불완전 검토가 publish를 우회하지 않게 한다. 공유 fixture는 현재 source hash와 유효 검토를 생성하는 helper를 제공한다.
- [x] **Step 5: 검사.** Run: python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -v. RF4, pre-TTS gate·순환 없는 지문·재검증·기존 배치 회귀 모두 OK여야 한다.
- [ ] **Step 6: 체크포인트.** git add .agents/skills/ec2-review-video && git commit -m "feat: require current circuit review before video production"

### Task 5: 전달·재개·재음성 및 실제 로컬 렌더 수용 검사

**Files:**
- Modify: S/tests/test_selection.py, test_revoice.py, integration_smoke.py.
- Modify if checks expose defects: S/scripts/lib/batch.py, revoice.py, S/scripts/video.py.
- Modify: S/SKILL.md, agents/openai.yaml, S/references/selection-and-batches.md, rendering-and-verification.md.
- Create: S/references/acceptance.md. 환경·증거·실제 검증 범위만 기록한다.

**Interfaces:**
- Consumes: Tasks 1–4의 CLI·source·theme·회로 gate와 기존 publish_set/resume_set.
- Produces: 기존 BATCH 출력 계약 유지. 모든 선정 clip 검증 후 제목 MP4 N개 + 공통 제작자료 하나를 전달한다.
- 기존 prepare --from-run/revoice의 단일 실행 결과 정리는 별도 CLI를 늘리지 않고 SKILL 절차에서 처리한다. 이동 전후 상대 경로·소스 link·지문·이전 버전 보존을 확인한다.
- 로컬 integration_smoke.py는 Task 3 fixture + 로컬 PCM + Task 4 회로 검토를 사용한다. 실제 발음·학습 내용 청취 완료를 표시하지 않는다.

- [x] **Step 1: 회귀 추가.** test_zero_topics_makes_no_api_or_mp4, test_partial_batch_preserves_previous_latest_and_sibling_audio, test_changed_circuit_review_prevents_publish, test_revoice_preserves_original_and_export_layout를 작성한다. assert는 API 호출 0, latest bytes 유지, 성공 PCM hash 유지, 기존 MP4 hash·link 보존, 최상위 제목 MP4 N개와 제작자료 폴더 하나다. 기존 covered 시나리오는 fixture를 전자회로2 gate까지 통과하도록 보강하고 같은 assertion을 중복 생성하지 않는다.
- [x] **Step 2: 회귀 실행.** Run: python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -v. 새 assertion이 노출하는 결함이 있으면 실패를 기록한다. 이미 충족한 보존 계약은 억지로 red를 만들지 않는다.
- [x] **Step 3: 전달과 문서 완성.** 발견된 재개·출력 결함만 최소 수정한다. SKILL에 전체 노트 선정·회로 장면·영문 기호 발음·0/N개·전체 복습·자막·재음성의 실제 명령을 연결한다. 운영 명령은 HyperFrames entry skill을 먼저 읽고 local asset·도구 경로를 확인하도록 한다. 1002를 수용 예시로 쓰되 수업 범위 밖 주제나 유료 TTS 실행을 자동 추가하지 않는다.
- [x] **Step 4: 정적 수용 확인.** Run: python3 /Users/hyunjun_macbook_pro/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/ec2-review-video 및 전체 unittest. frontmatter·참조 경로·스킬 naming과 동작 회귀가 통과해야 한다. git diff --check, git status --short에서 허용된 스킬 파일 외 수정이 없어야 한다. 전달받은 설계/계획 파일은 보존한다.
- [x] **Step 5: 로컬 렌더 smoke.** HyperFrames entry skill을 읽고 기존 로컬 HF_ENTRY, ASSETS, PUPPETEER_PACKAGE_JSON, CHROME_EXE와 ffmpeg/ffprobe를 탐색한다. API 키는 필요 없다. 실제 절대 경로로 python3 S/tests/integration_smoke.py --run SCRATCH_RUN --assets ASSETS --hyperframes-entry HF_ENTRY를 실행한다. 이어 node S/tests/browser_check.mjs SCRATCH_RUN PUPPETEER_PACKAGE_JSON CHROME_EXE를 실행한다. 기대 결과: media/audio/source 기술 검사 passed, browser status=passed, 1920×1080·30fps·실측 PCM 동기화. 대표 프레임·역방향 seek·회로 값·수식·자막 영역을 직접 확인한다. 필요한 도구가 없으면 구체적 누락과 unverified를 남기며 성공을 주장하지 않는다.
- [x] **Step 6: 수용 기록.** acceptance.md에 실행 명령·fixture 조건·검사 결과와 실제 Aoede 발음/음성 내용 검증은 아직 미실행임을 적는다. 실제 영상 요청에서는 인증 가용성 확인 → 선정 → 전체 파이프라인 → 청취·최종 프레임·verify·publish로 완료한다. 무료 smoke를 실제 제작 완료로 대체하지 않는다.
- [ ] **Step 7: 체크포인트.** git add .agents/skills/ec2-review-video && git commit -m "test: verify ec2 video delivery and local rendering"

## 계획 자체 검토 기록

- 설계 대응: 독립 이식=Task 1, 출처·선정 범위=Task 2+각 단계 문서, 화면·음성=Task 3, 회로 의미·변경 감지=Task 4, 출력·재개·검증=Task 5.
- Review Focus RF1–RF5 각각의 테스트를 해당 소유 Task에 배치했다.
- 기존 schema v1과 함수 signatures를 유지하고 추가 resolver·extra_sources·circuit 인터페이스를 한 곳에서 정의했다.
- 알고리즘 본문을 계획에 복제하지 않고 파일·signature·assert·명령·판정 기준만 고정했다.
- 계획 작성은 소스 구현과 구분한다. 실행 방식은 사용자가 계획 검토 후 선택한다.

## 구현 결과 (2026-10-07)

5개 작업 구현·검증 완료. 전체 회귀 81개, 로컬 PCM 렌더 및 편집 소스·브라우저 검사 통과. 독립 리뷰의 Important 2건 수정, Minor 조회 명령 예시 보류. 커밋·푸시는 요청이 없어 수행하지 않았고 체크포인트도 미실행이다. 실제 유료 Aoede 음성 검증은 미실행이다. 세부 검증 범위는 스킬 references/acceptance.md에 기록했다.
