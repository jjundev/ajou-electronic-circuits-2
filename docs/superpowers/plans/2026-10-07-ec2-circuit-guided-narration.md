# Circuit-guided Narration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 회로 근거 → 설명을 동반한 필기 흐름과 기호 자막을 만들고 실제 화면·음성에서 검증한다.

**Architecture:** 기존 reason/write/check, focus.json, annotations.json을 재사용한다. lesson.json은 단계별 교육적 연결을 선언하고 lesson.py가 유료 호출 전과 실제 타임라인 검증에 같은 계약을 적용한다. 음성 text와 caption_text를 분리하며 짧은 의미 단위로 PageMap을 저작한다.

**Tech Stack:** Python unittest, 원본 PDF/SVG, GSAP/HyperFrames, Node 브라우저 검사, Vertex Aoede TTS 기존 어댑터, 24kHz PCM, libass FFmpeg.

**Spec:** ../specs/2026-10-07-ec2-circuit-guided-narration-design.md

## Global Constraints
- 영상 길이는 이해 우선으로 필요한 만큼 늘린다.
- 필기 기본 속도는 7.5 chars/sec, 30fps, 원본 왼쪽→오른쪽 순서와 줄 전체 구도, 12프레임 카메라 전환을 유지한다.
- 음성용 text와 자막용 caption_text를 별도로 저작한다.
- 원문 기호의 대소문자와 첨자를 보존한다. SRT에서 미지원 LaTeX 문자열을 그대로 출력하지 않는다.
- 60프레임(2초)을 초과하는 공백은 현재 입력 해시와 구간을 명시한 의도적 휴지 검토가 없으면 완료를 막는다.
- 70–85% 음성 밀도는 저작 가이드이며 의미 검토나 무음 검사 대신 자동 승인 근거가 되지 않는다.
- TTS의 자연 발화 시간을 변경하지 않는다.
- fake PCM은 기술 검증용이며 실제 음성/교육 품질 통과로 취급하지 않는다.
- 원본 PDF/MD와 이전 샘플을 보존한다.
- 공개·latest 변경·커밋은 별도 명시적 승인 없이 수행하지 않는다.
- 이미 부착된 codex/ec2-focus-annotations worktree에서 진행한다. 기존 미커밋 변경은 선행 구현이므로 보존한다. 실행 방식은 Native다.

## Review Focus
1. 기존 manifest에 caption_text/lesson.json이 없는 입력도 재개 가능해야 한다 — Task 1/2 legacy 회귀.
2. 부하/저항/이득 같은 후반 핵심 단계의 근거 누락을 기술 화면 통과로 감추면 안 된다 — Task 2 누락·순서 mutant, Task 4 의미 검토.
3. 긴 수식과 발음/표기 길이 차이가 있어도 기호가 잘리지 않고 자막이 음성 구간을 벗어나면 안 된다 — Task 1 atomic-token/PCM 경계 검사.
4. 자막만 바꿀 때 오래된 렌더를 재사용하거나 음성을 유료로 재생성하면 안 된다 — Task 1 cache/Task 3 state 회귀.
5. 짧은 음성과 긴 필기, 또는 새 음성 뒤 오래된 휴지 검토로 무음이 통과하면 안 된다 — Task 3 PCM 및 stale-review 검사.

---

## File Structure
모든 아래 경로는 worktree 기준이다. P = .agents/skills/ec2-solution-video/scripts/solution_video, T = .agents/skills/ec2-solution-video/tests. 각 Task의 Files는 실제 경로를 적는다.
- manifest.py: caption_text와 lesson 계약의 진입점.
- subtitles.py: 자막 원문 선택·기호 단위 줄바꿈. 음성 생성은 맡지 않는다.
- lesson.py (신규): 저작 연결/타임라인 연결 검사, 화면 검사에서 쓸 기대값 생성.
- video.py/state.py/verify.py: 검사 단계 연결, 최신 입력 해시, 완료 게이트.
- teaching_check.mjs: 기대 회로 영역과 주석의 실제 가시성 검사.
- guided_acceptance.py (신규): 원문 기반 E10.13 시나리오/분할 저작과 scratch 검증.
- 기존 narration_pacing.py는 재사용한다. 부정 사례는 test_narration_pacing.py에서 보강한다.

### Task 1: 음성 대본과 기호 자막 분리
**Files:**
- Modify: `.agents/skills/ec2-solution-video/scripts/solution_video/manifest.py` (`validate_manifest`)
- Modify: `.agents/skills/ec2-solution-video/scripts/solution_video/subtitles.py` (`write_srt`)
- Test: `.agents/skills/ec2-solution-video/tests/test_manifest.py`
- Test: `.agents/skills/ec2-solution-video/tests/test_subtitles.py`
- Test: `.agents/skills/ec2-solution-video/tests/test_adapter.py` (존재하지 않으면 생성)

**Interfaces:**
- Consumes: manifest segments `{id, kind, text, source_refs, caption_text?: str}`; measured `voice_samples` from `build_timeline`.
- Produces: `caption_text(segment: dict) -> str`, `split_caption(text: str, max_chars: int = 34) -> list[str]` in subtitles.py. `write_srt(timeline, dest)` signature는 유지한다. `text`는 TTS 원고로 그대로 유지한다.

- [x] **Step 1: Write failing tests**
`test_caption_uses_symbols`: text='알 오 원', caption_text='r_O1'이면 SRT에 r_O1 포함, 알 오 원 불포함. `test_legacy_caption_fallback`: 필드 없을 때 text 사용. `test_empty_caption_rejected`: 공백/비문자열은 InputError. `test_atomic_formula_caption`: 공백 없는 긴 수식에서도 r_O1/g_m1/V_BE 및 첨자 기호를 토큰 중간에서 자르지 않으며 정상 토큰 조합 줄은 34자 이하. 34자 초과 단일 토큰은 명확한 저작 오류. `test_caption_pcm_bounds`: 발음과 자막 글자수가 달라도 모든 SRT cue가 measured voice_samples 안에 있고 끝이 정확히 음성 끝과 일치. 정렬은 문장 구간 수준이며 단어 정렬을 주장하지 않는다. `test_caption_change_reuses_voice`: 동일 id/text, 다른 caption_text로 기존 synthesize를 두 번 호출하여 transport 호출 1회, WAV SHA 동일을 확인한다.

- [x] **Step 2: Run RED**
Run: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_subtitles.py' -v`
Expected: 새 자막 선택/토큰 테스트 FAIL. manifest/adapter 테스트도 각 파일명으로 같은 명령을 실행하여 실패 원인을 확인한다.

- [x] **Step 3: Implement caption contract**
manifest validator에서 optional caption_text의 비어 있지 않은 문자열 계약을 적용한다. subtitles.py는 caption_text를 먼저 선택하며 기존 text fallback을 유지한다. 공백과 수식 연산자 경계로 나누되 기호/첨자 토큰을 보존한다. 기존 PCM 구간 가중 분할을 유지한다. review_adapter와 공유 vertex_tts의 cache key는 변경하지 않는다.

- [x] **Step 4: Run GREEN**
Step 2의 세 파일 테스트가 모두 PASS. 음성 transport 입력에는 caption_text가 아닌 text만 반영됨을 확인한다.

- [ ] **Step 5: Commit checkpoint**
사용자가 커밋을 명시적으로 요청한 경우에만 이 Task의 변경을 검토·선별하여 커밋한다. 미승인 상태에서는 ledger에 검증 결과만 기록한다.

### Task 2: 회로 근거와 필기 단계 연결 계약
**Files:**
- Create: `.agents/skills/ec2-solution-video/scripts/solution_video/lesson.py`
- Modify: `.agents/skills/ec2-solution-video/scripts/video.py` (`run_stage` check/tts/retime)
- Modify: `.agents/skills/ec2-solution-video/scripts/solution_video/verify.py`
- Modify: `.agents/skills/ec2-solution-video/tests/teaching_check.mjs`
- Create: `.agents/skills/ec2-solution-video/tests/test_lesson.py`

**Interfaces:**
- Consumes: spec의 lesson.json, manifest, layers, `load_teaching(run, manifest, layers) -> dict | None`, actual timeline.
- Produces in lesson.py: `validate_lesson(lesson: dict, manifest: dict, layers: dict, teaching: dict | None) -> dict`; `load_lesson(run: Path, manifest: dict, layers: dict, teaching: dict | None) -> dict | None`; `lesson_expectations(lesson: dict, manifest: dict, timeline: dict, teaching: dict) -> dict`.
- 기대값은 `{steps:[{step_id, write_segment_id, reason_segment_ids, check_segment_ids, region_ids, annotation_ids}]}`. 타임라인 필드 start_sample/end_sample와 teaching cues/spans를 참조한다. 데이터가 없으면 legacy 유지; guided run은 검증 결과 `lesson_flow`를 보고한다.

- [x] **Step 1: Write failing tests**
`test_guided_core_steps_have_prior_reason`: circuit step의 reason이 write 이전, region/annotation 일치. `test_missing_late_reason_rejected`: 부하/병렬저항/이득 각각 reason 누락 시 step ID 포함 InputError. `test_unknown_or_duplicate_link`: 중복 step, 미지 segment/region/annotation, 잘못된 kind, 다른 step_id 연결 거부. `test_calculation_exemption`: 빈 circuit 목록+비어 있지 않은 exemption_reason만 허용. `test_missing_guided_caption`: guided 모든 segment의 caption_text 필수. `test_legacy_no_lesson`: None 허용. `test_reversed_actual_timing`: authored 순서는 맞아도 실제 write 이전에 reason이 끝나지 않으면 실패. `test_check_before_write_rejected`: check는 해당 write 완료 후. 기존 브라우저 fixture를 변형한 `test_lesson_focus_mutant`는 후반 reason 중 회로 viewbox나 annotation visibility를 풀이 영역으로 바꾸면 lesson_flow 실패해야 한다.

- [x] **Step 2: Run RED**
Run: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_lesson.py' -v`
Expected: 미구현 인터페이스/검증 FAIL.

- [x] **Step 3: Implement lesson validation and screen oracle**
spec schema를 엄격히 검사하고 각 circuit 단계의 source_refs/meaning_notes를 요구한다. check/tts/retime 진입에서 실제 유료 호출 이전에 load_lesson을 실행한다. verify에서 타임라인 순서와 lesson_expectations를 검사한다. teaching_check.mjs는 reason 안정 구간(진입/복귀 12프레임 제외)의 기대 region 및 해당 annotation 가시성을 확인한다. 기존 source pixel/seek/미래 풀이 누출 검사도 계속 적용한다. 근거가 없는 장면을 임의 생성하지 않는다.

- [x] **Step 4: Run GREEN**
Step 2 PASS 및 `test_teaching.py` PASS. fake transport의 invalid lesson 호출 횟수 0 확인. camera/annotation mutant는 반드시 FAIL.

- [ ] **Step 5: Commit checkpoint**
Task 1과 같은 명시적 승인 규칙. 기존 선행 미커밋 변경을 함께 자동 stage하지 않는다.

### Task 3: 실제 필기 음성 공백과 재개 상태 검증
**Files:**
- Modify: `.agents/skills/ec2-solution-video/scripts/solution_video/state.py`
- Modify: `.agents/skills/ec2-solution-video/scripts/solution_video/verify.py`
- Test: `.agents/skills/ec2-solution-video/tests/test_state.py`
- Test: `.agents/skills/ec2-solution-video/tests/test_narration_pacing.py`

**Interfaces:**
- Consumes: Task 2 load_lesson/lesson_expectations, existing `analyze_narration_pacing(timeline: dict, audio: list[dict], run: Path) -> dict`, real PCM sample counts/SHA.
- Produces: lesson.json presence/content와 lesson.py가 script 이후 fingerprint에 포함된다. verify의 lesson_flow 결과는 기존 complete 계산에 포함되고 guided 필수 검사 누락 시 complete=False. narration_pacing 인터페이스/60프레임 임계값은 유지한다.

- [x] **Step 1: Write failing tests**
`test_lesson_edit_invalidates_script`: lesson 연결/제외 이유 변경 및 파일 추가/삭제가 current script 이후 무효화. `test_caption_edit_rebuilds_without_paid_voice`: caption-only 수정 후 script/timing/captions 최신화가 필요하지만 동일 text TTS cache는 WAV SHA 유지/paid transport 추가 0. `test_short_voice_long_write`: 1초 발화 뒤 4초 이상 필기하면 review-required, complete=False. `test_stale_gap_review`: PCM 또는 timeline 변경 뒤 이전 input_hash의 휴지 승인이 무효. `test_60_frame_boundary`: 60프레임은 허용, 61프레임은 review-required. `test_missing_guided_gate_blocks_complete`: lesson 존재 시 lesson_flow 없거나 실패하면 complete=False.

- [x] **Step 2: Run RED**
Run: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_state.py' -v`
기존 구현이 이미 만족하는 pacing 회귀는 GREEN으로 기록하고 새 동작에 해당하는 state/complete 테스트의 RED를 확인한다.

- [x] **Step 3: Implement state/gate integration**
lesson 내용/존재 해시와 모듈을 script 이후에 포함한다. 기존 caption-only manifest 해시 전파를 유지하고 TTS cache 재사용으로 비용을 방지한다. narration_pacing 결과를 새로운 lesson_flow와 별개로 완료 조건에 유지한다. 의도적 휴지 승인으로 빈 필기 대본을 정당화하지 않는다.

- [x] **Step 4: Run GREEN**
Step 2 및 test_narration_pacing.py PASS. malformed lesson가 fingerprint 중 오류를 내면 안전한 입력 오류로 보고하며 오래된 결과로 계속하지 않는다.

- [ ] **Step 5: Commit checkpoint**
명시적 커밋 승인 시만 해당 변경 선별. 기존 실제 음성 미검증 상태는 그대로 기록한다.

### Task 4: E10.13 교육 흐름 저작 및 실제 샘플 승인
**Files:**
- Create: `.agents/skills/ec2-solution-video/tests/guided_acceptance.py`
- Create: `.agents/skills/ec2-solution-video/tests/test_guided_acceptance.py`
- Modify: `.agents/skills/ec2-solution-video/SKILL.md`
- Modify: `.agents/skills/ec2-solution-video/references/narration-and-timing.md`
- Modify: `.agents/skills/ec2-solution-video/references/verification.md`
- Generated scratch only: `.superpowers/acceptance-circuit-guided/` (Git 제외)

**Interfaces:**
- Consumes: Tasks 1–3, existing acceptance.author(run), frozen E10.13 source, existing CLI check/tts/retime/assemble/render/captions/verify.
- Produces: `author_guided(run: Path) -> dict` in guided_acceptance.py; source/map/manifest/coverage/circuit-review/focus/annotations/lesson을 일관되게 저작하고 요약 `{problem_id, core_step_ids, source_hashes}` 반환. 이전 샘플 폴더를 수정하지 않는다.

- [x] **Step 1: Write failing acceptance tests**
`test_four_core_connections`: spec의 가상접지/부하/병렬저항/이득 네 논리 그룹 모두 circuit 근거 있음. `test_split_preserves_original_ids`: glyph/shape 집합 중복·누락 0, 원본 순서 유지. `test_every_write_has_spoken_content_and_symbol_caption`: 지금 쓰는 문장·식에 대한 음성과 caption을 명시; r_O1/g_m1 기호 자막, 발음 대본 분리. `test_fake_audio_never_approves`: synthetic silence로 render 기술 통과해도 narration_pacing/meaning 승인·publish 불가.

- [x] **Step 2: Run RED**
Run: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_guided_acceptance.py' -v`
Expected: 저작 함수 미구현 FAIL.

- [x] **Step 3: Author source-grounded sample and workflow docs**
동결 PDF/MD를 다시 읽고 의미 단위로 기존 PageMap을 분할한다. 긴 원고를 한 write에 붙이지 않는다. 회로 이유를 reason에, 쓰는 내용의 읽기/항 의미를 write에, 필요한 대조를 check에 넣는다. annotation.hide_at을 명시해 현재 표시가 겹치지 않게 한다. SKILL/references에 새 guided 저작·caption·의미 검토 규칙을 반영한다.

- [x] **Step 4: Run technical GREEN**
전체: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v` 및 기존 Node runtime 테스트를 실행한다. scratch의 새 E10.13를 렌더해 content/original_svg/hyperframes/final_media/captions/writing_animation/teaching_animation/writing_flow/lesson_flow PASS를 확인한다. core 단계별 회로 reason·필기 중간 화면과 최종 화면을 눈으로 확인한다. 기호 자막의 실제 libass 픽셀을 확인한다. synthetic 음성 샘플은 기술 검증이라고 표시한다.

- [ ] **Step 5: Validate actual narration**
기존 환경의 키 또는 사용자가 지정한 비공개 env 경로가 있어야 실제 TTS를 실행한다. 키 경로가 없으면 다른 독립 작업은 끝내고 실제 음성 검증만 미완료로 남긴다. 기존 cache/budget, max_attempts=1로 생성한다. retime 후 실제 PCM의 필기 공백을 측정한다. 실패하면 원문 근거 대본/분할을 먼저 검토하고, 재시도 비용이 생기는 수정은 보고하며 무한 생성하지 않는다. 음성을 실제로 들을 수 있는 수단으로 현재 필기/기호/회로와 대조한다. 실제 청취가 불가능하면 audio meaning은 unverified로 두고 샘플 사용자 검토를 요청한다.

- [x] **Step 6: Review and deliver**
Native executing-plans의 전체 변경 최종 독립 리뷰 1회를 수행한다. 네 핵심 단계의 ‘근거 표시→설명→필기’와 표기/발음 의미 일치를 검토한다. 지적 수정 후 필요한 검사만 재실행한다. 새 MP4·대본·현재 SHA 검증 요약을 별도 경로에 전달한다. 무음 샘플과 실제 음성 샘플 상태를 구별하고 publish/latest는 변경하지 않는다.

- [ ] **Step 7: Commit checkpoint**
명시적 승인 시만 요청 범위를 검사 후 커밋한다. 승인 없으면 파일과 검증 기록을 보존한다.

## Self-review
설계의 회로 연결은 Task 2/4, 발화·기호 분리는 Task 1/4, 공백·해시는 Task 3, 실음성·의미 검토는 Task 4에 대응한다. Review Focus 5개는 위 명명 테스트로 각각 고정했다. 공개 lesson 인터페이스는 Task 2에만 정의하고 이후 재사용한다. 준비된 기존 무음/실음성 대기 run을 덮어쓰지 않는다. 기계 검증이 의미 검토를 대체하지 않으며 실제 음성 없이 교육 품질 완료를 주장하지 않는다.

## Execution handoff
Native 선호가 이미 확인되어 있다. 사용자에게 설계/계획 링크를 제공하고 이번 계획이 의도와 일치하는지 검토 응답을 기다린 뒤 executing-plans로 구현한다.

## 실행 상태
구현·9개 기술 게이트·독립 리뷰·무음 샘플 전달 완료. Task 4 Step 5 실제 TTS/청취는 인증파일 경로가 없어 미완료. 유료 호출 0, 커밋·실제 게시 없음.
