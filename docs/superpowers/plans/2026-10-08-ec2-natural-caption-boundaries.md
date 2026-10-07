# Natural Caption Boundaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 문장·쉼표에서 자막을 교체하고 긴 구절은 두 줄로 표시하여 읽기 흐름을 자연스럽게 만든다.

**Architecture:** subtitles.py에 구두점 기반 의미 분할과 화면 내 줄바꿈을 분리한다. 기존 split_caption 호출 인터페이스와 PCM 기반 SRT 시간을 유지하며 manifest 검사가 유료 호출 전에 모든 자막을 검증한다. 기존 source master에서 자막만 다시 입혀 화면을 검증한다.

**Tech Stack:** 기존 Python/unittest, SRT, libass FFmpeg, 기존 Pretendard 폰트. 새 의존성 없음.

**Spec:** ../specs/2026-10-08-ec2-natural-caption-boundaries-design.md

## Global Constraints
- 문장 종료 온점에서 반드시 자막을 교체하고 서로 다른 문장을 한 cue에 합치지 않는다.
- 수식·괄호 밖 쉼표마다 cue를 교체하고 쉼표를 앞 cue 끝에 남긴다.
- cue당 최대 두 줄, 줄당 최대 34자이며 가능한 경우 한 줄을 사용한다.
- r_O1, g_m1, V_BE, 첨자 토큰은 원자적으로 보존한다.
- text/caption_text 저장 원문, TTS cache key, measured voice_samples를 변경하지 않는다.
- Native 실행, 이미 부착된 codex/ec2-focus-annotations worktree 재사용. 모든 선행 미커밋 변경 보존.
- 원본 PDF/MD, 이전 MP4, 필기 7.5 chars/sec와 회로 카메라 동작은 보존한다.
- 실제 TTS, 패키지 설치, 공개/latest 변경, 커밋은 별도 승인 없이 하지 않는다.
- 구현 승인은 이 계획을 사용자가 검토한 후에 받는다. 이번 요청은 문서 저장까지만이다.

## Review Focus
1. 0.5/E10.13/1,000 및 괄호·인용 안 구두점은 의미 경계가 아니다 — Task 1 보호 구간 테스트.
2. 온점 없는 legacy text와 문장 끝 닫는 따옴표에도 원문 보존/표시용 종결 처리가 일관되어야 한다 — Task 1 호환 테스트.
3. 짧은 쉼표 열거/두 줄 cue는 중복·누락 없이 PCM 구간 안에서 연속 표시되어야 한다 — Task 2 시간/재구성 테스트.
4. 34자 초과 원자 토큰/68자 초과 구절/괄호 불균형은 TTS 전에 구절과 segment id를 알려야 한다 — Task 2 사전 실패 테스트.
5. 두 줄 libass 자막이 기존 900..1080 자막 영역을 넘거나 기호가 잘리면 안 된다 — Task 3 실제 화면 검사 및 캡션 회귀.

---

## File Structure
모든 경로는 worktree 기준이다. 책임별 새 일반 모듈은 만들지 않는다.
- `.agents/skills/ec2-solution-video/scripts/solution_video/subtitles.py`: 보호 구간 의미 분할, 두 줄 wrap, SRT 시간 가중치.
- `.agents/skills/ec2-solution-video/scripts/solution_video/manifest.py`: 모든 segment 자막 사전 검사.
- `.agents/skills/ec2-solution-video/scripts/solution_video/lesson.py`: 기존 split_caption 재사용; 중복 호출은 필요하면 제거하며 별도 정책을 만들지 않는다.
- `.agents/skills/ec2-solution-video/tests/test_subtitles.py`, `test_manifest.py`, `test_cli.py`, `test_guided_acceptance.py`: 분할/시간/사전 실패/실제 대본 회귀.
- `.agents/skills/ec2-solution-video/SKILL.md`, `references/narration-and-timing.md`, `references/verification.md`: 이 스킬 아래에서 저작/검증 규칙 갱신.
- state.py/review_adapter.py/verify.py는 기존 동작 재사용. 변경이 필요하다는 증거 없으면 수정하지 않는다.

### Task 1: 의미 경계와 화면 내 줄바꿈
**Files:** Modify `.agents/skills/ec2-solution-video/scripts/solution_video/subtitles.py:15-26`; Test `.agents/skills/ec2-solution-video/tests/test_subtitles.py`.

**Interfaces:**
- Consumes: `caption_text(segment: dict) -> str` (기존 원문 선택).
- Produces: `caption_units(text: str) -> list[str]` (온점/쉼표 단위, 줄바꿈 없음); `wrap_caption(text: str, max_chars: int = 34, max_lines: int = 2) -> str` (줄바꿈 포함 가능); `split_caption(text: str, max_chars: int = 34) -> list[str]` (각 unit을 wrap한 cue 배열, 기존 호출부 호환).

- [x] **Step 1: Write failing tests**
`test_sentence_and_comma_boundaries`: split_caption('g_m1은 Q₁의 트랜스컨덕턴스이고, r_O1은 Q₁의 출력 저항입니다. 이 두 기호를 구별해 둡니다.') == ['g_m1은 Q₁의 트랜스컨덕턴스이고,','r_O1은 Q₁의 출력 저항입니다.','이 두 기호를 구별해 둡니다.'].
`test_long_sentence_wrap_is_one_cue`: '따라서 Q₁은 이미터가 접지된 공통 이미터 증폭기로 볼 수 있습니다.'는 cue 1개, 줄 2개, 각 len <=34, 공백 정규화 후 원문 동일.
`test_protected_punctuation`: 'E10.13에서 0.5와 1,000을 봅니다. f(X, P)는 같은 식입니다.'는 cue 2개; 괄호/따옴표 안 쉼표는 보존; '(X,P), 다음입니다.'는 cue 2개; 숫자 내부 점/쉼표는 cue를 늘리지 않는다.
`test_legacy_terminal_period`: split_caption('원본을 확인합니다') == ['원본을 확인합니다.']; 입력 문자열은 불변.
`test_quoted_sentence_end`: '“같은 값입니다.” 다음입니다.'는 닫는 따옴표가 앞 cue에 남는 2개 cue.
`test_atomic_tokens_and_layout_errors`: 기호가 줄 중간에서 잘리지 않음; 34자 초과 원자 토큰/두 줄 초과 구절/불균형 괄호/종결 ? ! …는 InputError. 기존 긴 수식 테스트는 새 두 줄 계약에 맞춰 성공/과대 입력을 구분한다.

- [x] **Step 2: Run RED**
Run: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_subtitles.py -v`
Expected: 새 의미 경계/두 줄 assertions 또는 새 인터페이스가 실패한다.

- [x] **Step 3: Implement interfaces**
subtitles.py에 Task Interfaces를 구현한다. bracket/quote stack으로 보호 구간을 추적하고 소수점/식별자 점/숫자 쉼표를 보호한다. 닫는 따옴표 바로 앞의 문장 종결 온점은 spec의 인용 문장 예외를 적용한다. 공백 우선 줄바꿈에서 모든 가능한 분할점 중 두 줄 최대 길이를 만족하며 길이 차이가 가장 작은 점을 선택한다(동률이면 앞의 점). 공백 후보가 없으면 수식 연산자 후보를 사용한다. 내용과 구두점을 보존하고 의미 단위 자체를 길이 때문에 추가 cue로 나누지 않는다.

- [x] **Step 4: Run GREEN**
Run: Step 2 명령. Expected: 모든 자막 단위 테스트 PASS.

- [ ] **Step 5: Conditional commit**
커밋 요청이 있을 때만 이 작업 diff를 구분하여 stage한다. 동일 파일의 선행 미커밋 변경을 섞지 않는다. 메시지: `feat: split captions at sentence and clause boundaries`. 승인 없으면 체크하지 않고 진행한다.

### Task 2: SRT 시간과 유료 호출 전 검사
**Files:** Modify `.agents/skills/ec2-solution-video/scripts/solution_video/subtitles.py:28-37`, `.agents/skills/ec2-solution-video/scripts/solution_video/manifest.py:37-43`; Test `.agents/skills/ec2-solution-video/tests/test_subtitles.py`, `test_manifest.py`, `test_cli.py`, `test_voice.py`, `test_state.py`.

**Interfaces:**
- Consumes: Task 1 `caption_units`, `wrap_caption`, `split_caption`; 기존 `validate_manifest(manifest, layers, coverage, circuit_review)`.
- Produces: 기존 `write_srt(timeline, dest)`의 경로 반환 및 기존 validator 서명 유지. 검사 실패 InputError에는 `segment <id>`와 문제 구절을 포함한다.

- [x] **Step 1: Write failing tests**
`test_semantic_srt_contiguous_pcm`: rate=24000/start=24000/voice_samples=72000/end=240000 입력에서 첫 cue 1초/마지막 cue 4초, 인접 end==next begin, 두 줄은 같은 cue, 줄바꿈 제외 길이로 가중 배분한다. 표시용 마지막 온점 추가는 시간 가중치를 늘리지 않는다.
`test_comma_list_reconstruction`: 'Q₁의 r_O1, 부하의 r_O3, 그리고 R₁입니다.'는 cue 3개이고 정규화 재결합은 원문과 같다. 짧은 cue도 삭제/합치지 않는다.
`test_invalid_caption_before_paid_voice`: explicit caption_text 과대 구절 및 text fallback 과대 구절 각각에 대해 실제 run_stage('tts', ...) 경로를 patch transport/generate_voice로 검사하여 호출 0회, InputError에 segment id/구절 포함. 기존 CLI fixture처럼 준비/gate는 유효하게 구성한다.

- [x] **Step 2: Run RED**
Run: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_cli.py -v` 및 test_subtitles.py/test_manifest.py 동일 패턴.
Expected: 유료 전 검사 및 줄바꿈 시간 assertions FAIL.

- [x] **Step 3: Integrate validation and timing**
manifest.py에서 모든 segment의 caption_text 선택과 split_caption 검사를 수행하고 InputError에 id를 덧붙인다. captions stage에서만 발생하던 잘못된 자막 오류가 check/tts 전에 발생하도록 한다. write_srt는 의미 unit의 표시용 온점 추가 전 길이를 가중치로 사용하고 wrap 출력은 가중치에 넣지 않는다. 현재 24 samples 최소 해상도 오류와 PCM 경계 계약은 유지한다. text/WAV/cache key에는 손대지 않는다.

- [x] **Step 4: Run GREEN and cache/state regressions**
Run: Step 2 명령 + test_voice.py/test_state.py/test_lesson.py 동일 discover 패턴.
Expected: 전체 PASS, caption-only edit cache transport 호출 1회 유지, stale downstream 무효화 유지, legacy fixtures 온점 없는 text도 작동.

- [ ] **Step 5: Conditional commit**
명시적 승인 시 해당 diff만 stage. 메시지: `fix: validate caption layout before speech generation`. 승인 없으면 생략한다.

### Task 3: E10.13 대본·실제 두 줄 화면·저작 문서
**Files:** Test `.agents/skills/ec2-solution-video/tests/test_guided_acceptance.py`, `test_media.py`; Modify `.agents/skills/ec2-solution-video/SKILL.md`, `.agents/skills/ec2-solution-video/references/narration-and-timing.md`, `.agents/skills/ec2-solution-video/references/verification.md`.

**Interfaces:**
- Consumes: Task 1/2 interfaces; 기존 `author_guided(run: Path) -> dict`, `burn_subtitles(master, srt, dest, font) -> Path`.
- Produces: 새로운 무음 자막 검증 MP4, 변경 전후 cue 예시 Markdown, 자막 기술/수동 화면 검증 JSON. 기존 master/샘플/음성 검증 상태 보존.

- [x] **Step 1: Write regression tests**
`test_guided_caption_semantic_coverage`: author_guided 20개 segments 전부 split_caption 성공, 각 cue 최대 두 줄/34자, 문장 사이 혼합 없음, 줄바꿈 제거/공백 정규화 재결합이 caption_text와 동일(표시용 온점 추가만 허용), r_O1/r_O3/g_m1 기호 보존.
`test_two_line_caption_strip`: 기존 libass 캡션 media fixture를 두 줄 cue로 확장하고 자막 픽셀 차이가 900..1080 안에서 나타나며 상단 평균 차이 기존 <=3 조건 유지. 표기 기호/공백 누락은 별도 실제 프레임 검사로 확인한다.

- [x] **Step 2: Run regression tests**
Run: unittest discover의 test_guided_acceptance.py/test_media.py 패턴.
Expected: PASS. 두 줄 strip이 실패하면 기존 font/position 값부터 점검하며 승인 없는 스타일 변경은 하지 않는다.

- [x] **Step 3: Update authoring documentation**
세 문서의 기존 34자 기반 설명을 spec의 의미 단위/두 줄/보호 구간/긴 구절 사전 오류/표시용 온점/시간 근사 계약으로 갱신한다. 문자 수 분할이 의미 경계보다 우선한다는 안내를 남기지 않는다.

- [x] **Step 4: Generate caption-only sample**
기존 scratch run `.superpowers/acceptance-circuit-guided/문제풀이영상/1002/1002_제작자료/실행/20261007-235130-a4a36f76/videos/problem-909657a48313`의 timeline/master를 읽기 전용 입력으로 새 `.superpowers/acceptance-natural-captions/`에 SRT와 final MP4를 만든다. write_srt/burn_subtitles로 실행하며 paid_requests=0, actual_audio=unverified를 기록한다. 이전 run의 상태 stamp나 review를 수정하지 않는다. source master SHA와 새 SRT/final SHA를 기록한다.

- [x] **Step 5: Inspect rendered frames**
새 SRT cue 중 쉼표 끝/온점 끝/두 줄/기호 포함 각 유형의 중간 시각을 FFmpeg로 PNG 추출하고 view_image로 실제 표시를 확인한다. 겹침·두 줄 잘림·기호 누락·상단 풀이 침범 없음이 통과 조건이다. 표시용 원문/cue 목록도 사람이 검토한다. 실제 발화 일치/청취 통과를 주장하지 않는다.

- [x] **Step 6: Run complete regression**
Run: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v`
Run: `node --test .agents/skills/ec2-solution-video/tests/*.cjs`
Run: `git diff --check`
Expected: 모든 활성 테스트 PASS, 기존 opt-in skips는 개별 보고, whitespace 오류 없음.

- [x] **Step 7: Deliver and final review**
Native 실행자는 구현/샘플 후 requesting-code-review로 가장 유능한 모델의 새로운 최종 리뷰어 1명을 요청한다. 이번 변경을 선행 변경 대비 구분하여 검토하고 중요한 문제를 해결한다. 새 검증 샘플을 기존 visualization thread 폴더의 별도 `ec2-natural-captions` 디렉터리에 보존하여 링크한다. 완전한 production verify나 실제 음성 통과 대신 자막 검사 범위를 정확히 보고한다.

- [ ] **Step 8: Conditional commit**
명시적 요청이 있을 때 문서/테스트 및 해당 변경만 stage. 메시지: `test: verify natural captions in solution video`. 선행 작업/새 plans/specs 포함 범위도 확인한다.

## Self-review
Spec 전체 표시/시간/호환 계약은 Task 1/2, 실제 화면/보존은 Task 3에 대응한다. Review Focus 5개는 각 소유 Task 테스트에 배정했다. 인터페이스 이름과 반환 타입은 일치한다. 새 의존성/시간 정렬/음성 재생성 범위를 추가하지 않는다. 사용자 구현 승인 후 Native로 진행 중이다. 조건부 커밋은 승인되지 않아 수행하지 않는다. 두 줄 libass 침범은 MarginV14로 수정했고 단일/두 줄 화면 검사에서 통과했다. 전체 회귀와 최종 리뷰 결과는 실행 기록에 남긴다.

## 실행 결과
2026-10-08 Native 구현 완료. Python171 실행(169 통과/기존 opt-in2 skip), Node5 통과. 독립 리뷰 Important1은 RED→GREEN으로 수정했고 최종 전체 회귀가 통과했다. 60 cue/두 줄10 cue 실제 화면 검사와 전체 디코드 통과. 무음 caption-only 샘플이며 실제 발화 정렬은 미검증. MarginV14는 두 줄 하단영역 검사 실패를 수정한 실행 판단이다. 조건부 커밋은 미승인으로 생략했다.
