# 문제풀이 영상 구도·필기·설명 흐름 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 회로에서 돌아온 풀이의 구도를 안정시키고 수식을 왼쪽부터 공개하며 작성 중 설명 공백을 줄인다.

**Architecture:** 원문 대응 순서와 화면 공개 순서를 분리한다. 명시적으로 저작한 줄·가로 영역을 compiler로 정규화해 timeline과 camera가 공유한다. 대본은 기존 step/write 구조로 세분화하고 실측 WAV의 공백을 검증한다.

**Tech Stack:** 기존 Python/unittest, PyMuPDF, SVG/JavaScript, GSAP/HyperFrames, Chrome/puppeteer, FFmpeg, 24kHz PCM. 새 의존성 없음.

**Spec:** `docs/superpowers/specs/2026-10-07-ec2-writing-flow-design.md`

## Global Constraints

- 같은 줄 왼쪽→오른쪽 강제. 같은 가로 영역 내 수직 이동과 명시적인 줄바꿈/열 전환은 허용한다.
- 본문 높이 최소 26px; 1920×1080, 30fps, 24kHz mono, 자막 영역 y=900..1080.
- 연필 기본 길이 160px, 최대 ±2°; 실제 설정과 sprite bounds를 계산한다. 한 연필 controller를 유지한다.
- 회로 전환과 구간 이동은 12프레임 smoothstep; 이동 중 필기하지 않는다.
- 발화 목표는 필기 시간의 약 70–85%; 필기 중 2초를 넘는 연속 음성 공백은 검토 대상이다. 읽기 hold는 별도다.
- 원본 풀이·PDF·복습노트·ec2-review-video는 수정하지 않는다. 원문 순서와 원본 SVG outline/배치를 보존한다.
- 기존 typing은 유지한다. 새 pencil 생성/retime에 writing_units가 없으면 저작 필요 오류를 내며 조용히 이전 순서로 대체하지 않는다.
- fake PCM을 실제 음성 의미 검토/게시 완료로 승인하지 않는다. 공백을 맞추려 무제한 자동 유료 재생성하지 않는다.
- 사용자 기존 Native 선택을 유지한다. 구현은 계획 확인 이후 직접 수행하고 마지막에 한 번 fresh reviewer를 사용한다.
- 기존 미커밋 회로 포커스/주석 변경과 본 작업을 같은 관리 작업트리에서 보존한다. 커밋·push·merge는 현재 승인되지 않았다. 아래 commit 단계는 명시적인 커밋 승인 이후에만 실행하고 이전 변경을 무단 포함하지 않는다.

## Review Focus

1. 한 PDF 줄에 본문·첨자·위첨자가 서로 다른 paint 순서로 놓인 경우 — 원문 검사를 유지하면서 가로 역행 없이 공개한다. Task 1/2.
2. 긴 분수선·근호선이 여러 가로 영역을 가로지르는 경우 — 미래 영역이 먼저 보이지 않고 최종 전체가 원본과 같다. Task 1/2.
3. 2단 풀이와 긴 한 줄이 26px 기준으로 안 들어오는 경우 — 다른 열과 섞이지 않고 명시한 구간에서만 이동한다. Task 1/3.
4. 회로 주석 직후 줄바꿈, 400px 연필, 임의 seek가 겹치는 경우 — 이동 도중 작성하지 않으며 bounds와 누적 주석 상태를 보존한다. Task 3/5.
5. WAV 내부 침묵·짧거나 긴 WAV·대본 변경 후 오래된 리뷰가 섞이는 경우 — 실제 공백을 보고하고 캐시/검토 상태를 정확히 갱신한다. Task 4/5.

---

## 작업 위치와 파일 구조

현재 작업트리: `/Users/hyunjun_macbook_pro/.codex/worktrees/ec2-focus-annotations/전자회로2`, branch `codex/ec2-focus-annotations`. 실행 시작 시 상태와 첨부를 재확인하고 기존 변경을 보존한다. 모든 아래 경로는 작업트리 상대 경로다.

- `scripts/solution_video/writing_units.py` (신규): 저작 단위 validation/정규화만 담당.
- `scripts/solution_video/writing_camera.py` (신규): 단위별 화면 fit/가로 구간 카메라만 담당.
- `scripts/solution_video/narration_pacing.py` (신규): PCM speech interval과 필기 공백 지표만 담당.
- 위 scripts 접두 경로는 `.agents/skills/ec2-solution-video/`이다.
- 기존 `manifest.py`, `pdf_pages.py`, `reveal.py`: 원문 계약과 공개 단위 연결.
- 기존 `composition.py`, `focus.py`, assets `writing.js`, `player.js`: 공유 단위의 렌더/카메라 연결.
- 기존 `state.py`, `verify.py`, `scripts/video.py`: 해시·재개·검증 연결.
- 기존 tests와 신규 `test_writing_units.py`, `test_writing_camera.py`, `test_narration_pacing.py`, `test_writing_flow.py`, `writing_flow_check.mjs`: 독립 oracle와 회귀 검증.
- 기존 SKILL 및 references `pdf-and-coverage.md`, `narration-and-timing.md`, `verification.md`: 해당 작업의 저작/검증 절차.

## 데이터 계약

PageMap step의 기존 `glyph_ids`, `shape_ids`는 수정하지 않는다. 새 `writing_units`는 다음 형태다:

```json
{"id":"u1","line_id":"line1","chunk_id":"chunk1","column_id":"col1","band":[510,540],"glyph_ids":["g1","gSub"],"shape_ids":[],"camera_break_before":false}
```

- 목록 순서가 공개 순서다. ID는 safe ASCII이며 전역 유일하다. 같은 line_id 내 band는 겹치지 않고 x가 증가한다. column 변경은 새 line_id를 요구한다. 같은 line의 chunk 변경은 camera_break_before=true를 요구한다.
- 각 glyph는 자기 bbox를 덮는 band들에만 속한다. band를 넘는 glyph/shape는 여러 unit에 나타날 수 있으며 각 piece는 bbox와 band의 교집합이다. 교집합은 완전한 면적 coverage, 중복 면적 0을 요구한다. 0면적 공백 glyph는 한 unit에만 배정한다.
- glyph/shape 모두 누락·외부 ID·완전하지 않은 clip coverage를 거부한다. 여러 unit에 걸친 긴 선은 분할 clip으로 공개한다.
- `WritingUnit` 정규화 결과: 위 저작 필드 + `step_id`, `bbox`, `pieces`. 각 `WritingPiece`는 `kind: glyph|shape`, `id`, `clip_bbox`를 갖는다. glyph/shape 최종 완료 event는 마지막 piece 완료 때 발생한다.
- timeline `writing_unit_spans`: `{unit_id,step_id,line_id,chunk_id,start_frame,end_frame}`. pencil move/draw spans는 기존 필드를 유지하고 `unit_id`, `piece_index`, `clip_bbox`를 추가한다. 동일 glyph의 여러 piece를 허용한다. 완료 event는 ID당 하나다.
- shape에는 가짜 glyph/text를 만들지 않는다. draw span은 `target_kind: glyph|shape`로 구분하고 renderer에서 해당 bbox를 사용한다. 공백은 기존처럼 연필을 숨긴다.

### Task 1: 원문을 보존하는 공개 단위 계약

**Files:** Create `.agents/skills/ec2-solution-video/scripts/solution_video/writing_units.py`; Modify 같은 폴더 `manifest.py`, `pdf_pages.py`; Test `.agents/skills/ec2-solution-video/tests/test_writing_units.py`, `test_manifest.py`; Modify reference `pdf-and-coverage.md`.

**Interfaces:** Consumes `layers: dict` (glyphs, shapes, map). Produces `compile_writing_units(layers: dict) -> list[WritingUnit]`와 `WritingUnit`, `WritingPiece` TypedDict. 잘못된 단위는 `InputError`를 발생시킨다. 원문 검사 함수의 signature는 유지한다.

- [x] **Step 1: 실패 테스트 작성.** `test_subscripts_do_not_change_source_order`: compile 후 기존 glyph_ids와 coverage.pdf_text 불변, unit band 증가. `test_fraction_and_radical_pieces_cover_original`: 각 target piece 면적 합=원본 bbox 면적, 중복=0. `test_columns_and_invalid_units`: 열/줄 혼합, band 역행, duplicate unit ID, unknown ID, missing/overlapping clip 각각 InputError. `test_pencil_missing_units_requires_authoring`: 새 pencil에 누락 시 저작 필요 메시지; typing은 허용.
- [x] **Step 2: RED 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_writing_units.py -v`; 신규 compiler 부재로 FAIL을 확인한다.
- [x] **Step 3: 위 signature 구현 및 계약 연결.** 자동으로 PDF paint 순서를 교정하지 않는다. 저작자가 line/column/band를 확인한다. 기존 원문 검증은 그대로 두고 단위 검증을 추가한다. clip 경계 허용 오차는 0.01pt, 공개 역행 허용 오차는 0.01pt이다. typing/pencil 모드 요구는 CLI check/retime 연결 시 Task 5에서 적용한다.
- [x] **Step 4: GREEN 확인.** 위 command 및 `test_manifest.py`, `test_pdf_pages.py`를 각각 같은 discover 방식으로 실행; 모두 PASS.
- [ ] **Step 5: 승인된 경우에만 해당 파일을 stage하고 `feat: define spatial writing units` 커밋.** 공유 파일의 기존 미커밋 변경을 분리할 수 없으면 승인까지 보류한다.

### Task 2: 가로 영역 순서로 공개하는 timeline·renderer

**Files:** Modify scripts `reveal.py`, `teaching.py`; assets `writing.js`, `player.js`; tests `test_reveal.py`, `test_writing_runtime.cjs`, `browser_check.mjs`; Create tests `writing_flow_check.mjs`.

**Interfaces:** Consumes Task 1 `compile_writing_units(layers)`. Produces 기존 signature `build_timeline(manifest,layers,audio,config,writing=None,*,minimum_frames=None) -> dict`의 새 unit/piece spans. `writing.js`는 glyph/shape piece를 frame에서 계산하여 `PenState` 하나를 반환한다. 최종 완료 events는 기존 소비자와 호환된다.

- [x] **Step 1: 실패 테스트 작성.** `test_unit_order_is_spatial_not_paint_order`: 첫 unit의 모든 draw가 다음 unit보다 먼저 끝남. `test_fraction_shape_has_no_future_leak`: 첫 band 작성 중 분수선의 오른쪽은 안 보임. `test_piece_final_event_once`: target 완료 event=1개. Node/browser에서 순방향·직접 seek·역방향 seek의 공개 clip 상태 동일, 완성 원본 pixel diff=0, 미래 piece pixel=0, same-line unit x 역행=0을 assert한다.
- [x] **Step 2: RED 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_reveal.py -v` 및 `node --test .agents/skills/ec2-solution-video/tests/test_writing_runtime.cjs`; 추가 assertions가 기존 순서/renderer에서 실패해야 한다.
- [x] **Step 3: timeline/renderer 연결.** 같은 unit 안에서는 왼쪽→오른쪽 piece 시작점 순, 동일 x에서는 위→아래, 마지막 tie는 기존 paint_order를 사용한다. band 이동 후 이전 band로 돌아가지 않는다. 서로 다른 piece의 끝 위치는 이동 출발점으로 저장한다. 기존 최대 5글자/초 규칙을 유지하며 shape piece draw 최소 18프레임. 기존 shape_anchor event는 piece 공개 대상 shape에 중복 적용하지 않고 마지막 piece 완료 event로 대체한다. 이전 piece clip을 누적해 glyph 완료 전에도 가려지지 않게 한다. 모든 상태를 frame으로 재계산하고 controller 외에 pen DOM을 조작하지 않는다.
- [x] **Step 4: GREEN 확인.** 위 commands와 `test_teaching.py`, `test_composition.py`를 실행; 기존 회로 주석/원본 완성 게이트 포함 PASS.
- [ ] **Step 5: 승인된 경우에만 scoped `feat: reveal math from left to right` 커밋.**

### Task 3: 줄 전체 fit와 회로 복귀 카메라

**Files:** Create scripts `writing_camera.py`, tests `test_writing_camera.py`; Modify scripts `composition.py`, `focus.py`, `reveal.py`; tests `test_focus.py`, `test_composition.py`, `writing_flow_check.mjs`.

**Interfaces:** Consumes WritingUnit 및 timeline unit spans. Produces `build_writing_camera_keys(layers: dict, timeline: dict, units: list[WritingUnit]) -> list[dict]`. `pencil_camera_keys(manifest,layers,timeline)`는 이 compiler를 호출한다. 공개를 12프레임 늦추는 구간 이동 slot은 `writing_unit_spans` 앞에 timeline이 예약한다. focus compiler는 첫 글자 대신 다음 unit의 완성된 구도 key를 선택한다.

- [x] **Step 1: 실패 테스트 작성.** `test_return_fits_whole_next_line`: 복귀 완료 때 다음 line의 모든 glyph/shape와 pen envelope가 x=0..1920,y=0..900 안, 본문>=26px. `test_fitting_line_has_one_view`: 해당 line draw 기간 카메라 viewbox 불변. `test_long_line_requires_authored_chunks`: 불가능한 한 chunk는 InputError, 명시한 chunks는 경계에만 이동. `test_column_change_and_long_pen`: 2단 순서 보존, 400px pen bounds 충족. `test_transition_has_no_draw`: 모든 12fr transition과 draw interval의 교집합=0.
- [x] **Step 2: RED 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_writing_camera.py -v`; 전체 줄 fit 및 compiler 부재 FAIL.
- [x] **Step 3: 위 signature 구현.** chunk 전체 union + 각 tip의 실제 sprite envelope를 fit한다. 기본 본문28px, 필요 시26px까지 축소; 26px에서도 안 들어오면 저작된 chunk split을 요구한다. feasible viewbox 가운데 해당 chunk 중심에 가장 가까운 구도를 선택하며 glyph별 재센터/pen mirror 변경을 하지 않는다. 기존 수동 camera가 unit 구간과 충돌하면 명확한 InputError. 원본 move 출발점은 마지막 draw 시점 카메라로 계산한다.
- [x] **Step 4: GREEN 확인.** 위 command와 `test_focus.py`, `test_composition.py`, `test_teaching_runtime.cjs` 실행; 전환·최종 전체 화면·누적 주석 PASS.
- [ ] **Step 5: 승인된 경우에만 scoped `fix: frame complete writing lines` 커밋.**

### Task 4: 설명 밀도와 실제 음성 공백 검증

**Files:** Create scripts `narration_pacing.py`, tests `test_narration_pacing.py`; Modify scripts `verify.py`; references `narration-and-timing.md`, `verification.md`.

**Interfaces:** Produces `speech_intervals(pcm_path: Path) -> list[tuple[int,int]]` (절대 WAV sample의 end-exclusive 구간), `analyze_narration_pacing(timeline: dict, audio: list[dict], run: Path) -> dict`. report 필드 `input_hash`, `segments` (segment_id, voiced_ratio, longest_gap_frames, gaps), `status: passed|review-required`, `evidence_hashes`. 실제 의미/발음 검토는 별도 audio-review를 유지한다.

- [x] **Step 1: 실패 테스트 작성.** 24k PCM synthetic tone/zero를 사용해 `test_internal_and_tail_silence`: 내부+뒤 padding 포함 61fr 공백은 review-required,60fr는 통과. `test_read_hold_excluded`: read_hold만 지표에서 제외. `test_short_long_and_missing_voice`: 짧은 음성 공백 보고, 긴 WAV 잘리지 않음, 잘못된 rate/hash는 InputError. `test_ratio_is_guidance_not_forced_tts`: 70–85% 밖은 안내하되 추가 유료 요청=0. `test_pacing_does_not_approve_audio_meaning`: metric PASS로 audio meaning을 자동 승인하지 않음.
- [x] **Step 2: RED 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_narration_pacing.py -v`; 신규 API 부재 FAIL.
- [x] **Step 3: 지표와 저작 지침 구현.** 20ms RMS window, -40dBFS 기준, 100ms 이하 내부 gap 연결로 speech interval을 추정한다. 이는 실제 단어 정렬이 아니다. write의 첫 move부터 마지막 draw 완료까지 window를 분석하고 중간 camera 이동 시간도 포함한다. intent가 있는 2초 초과 공백은 별도 `verification/pacing-review.json`에 input_hash/gap 위치/근거를 저작해야 하며 미처리 gap은 완료를 막는다. 목표 비율 분모는 실제 draw/move 필기 프레임, 분자는 그 프레임과 speech의 교집합이다. renderer/오디오를 지표 맞추기 위해 변형하지 않는다.
- [x] **Step 4: GREEN 확인.** 위 command와 `test_verify.py`, `test_media.py`, `test_voice.py` 실행; fake 제한과 PCM 보존 PASS.
- [ ] **Step 5: 승인된 경우에만 scoped `feat: review narration gaps during writing` 커밋.**

### Task 5: 재개 해시·실자료·유성 샘플 통합

**Files:** Modify scripts `state.py`, `verify.py`, `scripts/video.py`; tests `test_state.py`, `test_cli.py`, `test_verify.py`; Create tests `test_writing_flow.py`; Modify tests `teaching_acceptance.py`, `test_teaching_acceptance.py`와 SKILL.md. 실행 자료는 ignored scratch 아래에만 작성한다.

**Interfaces:** Consumes Tasks 1–4의 API. 기존 CLI 명령 `check`, `tts`, `retime`, `assemble`, `verify` 유지. 새 verification 항목 `writing_flow`, `narration_pacing`과 그 evidence hashes를 결과에 포함한다. content 리뷰 해시는 writing_units를 포함하고 tool hash에는 새 modules/oracle를 포함한다. `verification/narration-pacing.json`을 지표/evidence 출력으로 저장하고 `verification/pacing-review.json`을 verify FACTORS에 포함한다.

- [x] **Step 1: 실패 테스트 작성.** `test_units_and_script_invalidate_correct_stages`: unit 변경 시 layers/content/timing/composition 리뷰 무효화, 대본 변경 시 voice/음성 리뷰 무효화, camera tool만 변경하면 PCM 파일과 유료 요청 수 불변. `test_old_pencil_requires_units_typing_kept`: check/retime은 pencil units 누락 거부. `test_pacing_review_hash_stale`: WAV 변경 후 이전 gap 승인 거부. `test_mutated_order_or_camera_blocks_completion`: 실제 composition 순서/카메라 mutation에 independent browser oracle 실패.
- [x] **Step 2: RED 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_writing_flow.py -v`; 신규 통합 항목 부재 FAIL.
- [x] **Step 3: CLI/state/verify 연결.** existing content+audio review 계약을 유지한다. 독립 oracle는 authored bands/원본 geometry에서 기대 순서와 fit를 계산하며 renderer의 결과를 기대값으로 복사하지 않는다. 이전 fake teaching acceptance도 새 계약에 맞게 unit을 저작하되 원본 source/PDF는 보존한다. 실패는 명시적으로 보고하며 typing/무음으로 대체하지 않는다.
- [x] **Step 4: 전체 GREEN 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_*.py'`와 `node --test .agents/skills/ec2-solution-video/tests/test_writing_runtime.cjs .agents/skills/ec2-solution-video/tests/test_teaching_runtime.cjs` 실행; PASS/skip 이유 기록. `git diff --check` 통과. opt-in이 요구되는 native browser 검사는 실제 실행으로 별도 증거를 남긴다.
- [x] **Step 5: 실자료 시각 검증.** E10.11, E10.13, 2021-1_중간-Q3를 별도 scratch run에서 저작하고 기존 CLI로 retime/assemble/render/captions/verify. 분수/근호가 이 세 문항에 없으면 별도 synthetic native SVG/browser 검사를 포함한다. E10.13 복귀 직전·직후·수식 끝, Q3 열 전환, 최종 전체 화면을 직접 확인한다. fake 자료는 technical-only로 남긴다.
- [ ] **Step 6: 유성 E10.13 샘플 제작.** 원자료에 근거해 step을 줄/항별로 나누고 각 write에 이유·항 의미·회로 연결 문장을 작성한다. 기존 내용 검토/TTS cache/budget 절차로 실제 음성을 한 번 생성하고 measured PCM으로 합성한다. 70–85% 목표와 >2초 gap 목록을 보고한다. 청취할 수 없으면 audio meaning은 unverified로 유지하고 샘플 확인을 사용자에게 요청한다. 기존 sample 보존, 새 결과는 별도 자연스러운 제목으로 visualization 폴더에 보존; 정식 publish/latest는 변경하지 않는다.
- [x] **Step 7: 최종 fresh review.** Native implementer 작업을 마친 뒤 applicable executing-plans/requesting-code-review 지침의 fresh reviewer 한 번만 사용한다. findings를 재현/수정하고 해당 검증을 다시 실행한다. 미커밋 상태면 working-tree diff와 신규 파일을 모두 review package에 포함하고 기준 SHA를 기록한다.
- [ ] **Step 8: 승인된 경우에만 scoped `test: verify complete writing flow` 커밋.** 기존 변경과 새 작업의 범위를 확인하고 scratch/media/개인 설정을 stage하지 않는다. 승인 없으면 미커밋 상태와 증거를 보존한다.

## 자체 검토와 실행 인계

- 설계의 줄 전체 구도: Task 3; 원문/공개 순서 분리 및 2차원 수식: Tasks 1–2; 설명 보강/공백: Tasks 4–5.
- Review Focus의 다섯 조건은 각 task 테스트에 배정했다. signature/type/property는 데이터 계약과 일치한다.
- 공개 영역 저작은 의도적으로 명시적인 입력이다. ambiguous PDF를 자동 판별한 척하지 않는다.
- 실자료 기술 PASS, 실제 음성 의미 검토, 사용자 샘플 확인을 구분한다. 70–85%는 저작 목표이고 2초 초과 공백 처리는 검증 조건이다.
- 실행 방법은 기존 Native 선택을 유지한다. 사용자에게 계획이 의도를 담았는지 확인받은 뒤 구현한다. Native 실행 승인을 받아 Tasks 1–4 구현·검증을 완료했다. Task 5의 실자료 렌더 검증과 유성 샘플 상태는 실행 ledger에 기록한다. 실제 음성은 인증 입력 전에는 생성 완료로 표시하지 않는다.
