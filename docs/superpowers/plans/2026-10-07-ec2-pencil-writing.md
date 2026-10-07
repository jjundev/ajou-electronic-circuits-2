# 전자회로2 연필 필기 애니메이션 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 PDF 답안 공개에 원본 윤곽을 유지하는 점진 공개와 연필 PNG 한 장의 움직임을 추가한다.

**Architecture:** 기존 추출 결과를 보존하고 timeline에 이동·작성 구간을 추가한다. 브라우저는 원본 SVG에 추가한 clip과 연필 위치를 프레임으로 재구성한다. 작성 설정과 asset 지문을 음성 설정에서 분리해 retime과 재개가 저장된 WAV를 재사용하게 한다.

**Tech Stack:** Python 3 / unittest / PyMuPDF / Pillow, JavaScript / Node node:test / SVG / 로컬 GSAP / puppeteer-core / Chrome / HyperFrames / libass FFmpeg.

**Spec:** [2026-10-07-ec2-pencil-writing-design.md](../specs/2026-10-07-ec2-pencil-writing-design.md). 기존 제작 계약은 [2026-10-07-ec2-solution-video-design.md](../specs/2026-10-07-ec2-solution-video-design.md)와 `.agents/skills/ec2-solution-video/SKILL.md`를 함께 읽는다.

## Global Constraints

- PDF 답안의 문장·기호·수치·순서·줄바꿈·윤곽을 보존하며 완성 화면은 원본과 같아야 한다. 재조판·원본 이미지 교체로 결함을 숨기지 않는다.
- 1920×1080 / 30fps / mono PCM 24kHz를 유지한다. PDF 전체의 기존 16:9 또는 legacy 배치를 유지하고 자막 예약 영역은 하단 180px다.
- 신규 기본은 pencil, 최대 5글자/초, 인접 이동 1프레임 + 작성 5프레임, 긴 이동 최소 8프레임, 읽기 여유 0.75초, 촉부터 끝까지 160px, 최대 ±2°다.
- SVG 글자는 왼쪽→오른쪽 공개다. 실제 획순, 손, 효과음, 도형 필기, 단어별 음성 동기화는 구현하지 않는다.
- 작성 파일이 없는 기존 실행은 기존 타이핑으로 읽는다. 명시적 typing 기본 속도는 7글자/초다. 기존 production 영상·PDF·노트·ec2-review-video를 수정하지 않는다.
- 기존 연필 PNG와 프롬프트를 보존한다. 현재 PNG SHA256은 8f09ff6af2689c9cb50bab4382c4d18a46639312ea8d2edf42ad82c774d20269다.
- TTS 공급자·모델·Aoede 설정은 유지한다. retime과 개발 검증은 유료 호출 0이며 fake PCM을 production 게시/실제 음성 검토로 승인하지 않는다.
- 자동 전역 설치·CLI 업그레이드를 하지 않는다. 실행 시 로컬 의존성 경로를 확인하고 누락은 명시적으로 보고한다.
- plan 작성 턴에는 실행 코드·이미지·Git 커밋을 만들지 않는다. 아래 Commit 단계는 사용자 커밋 권한이 있을 때만 실행하고, 없으면 변경/검증 기록을 남긴다. push/merge는 별도 명시 요청이 있어야 한다.
- 실행 방법은 Native와 별도 관리 워크트리로 선택됐다. 구현 시 using-git-worktrees 지침에 따라 격리를 확인한다. 미커밋 상태인 연필 asset 세 파일과 이 spec/plan이 새 worktree에 자동 포함되지 않으므로 필요한 파일만 복사하고 해시를 확인한다.

## Review Focus

1. 기존 clip/transform/shared defs와 다중 svg_ids: 원래 모양을 유지하고 미래 글자가 새지 않아야 한다 — Task 3.
2. 공백·겹치는 첨자·단계/2단 이동: 허공 필기와 거짓 줄바꿈 없이 승인 순서와 완료 이벤트를 보존해야 한다 — Tasks 2, 3.
3. 네 모서리·확대·마지막 hold: 연필 전체와 촉이 1920×900 영역 안에 있고 완성 화면에서 사라져야 한다 — Task 3.
4. 기존 run·작성 설정 변경·asset 누락/변조: 올바른 단계부터 재개하고 WAV와 유료 요청 수를 보존해야 한다 — Tasks 1, 4.
5. 되감기·마스크 해제 직전·최종 MP4: 임의 seek 결과와 전체 공개 픽셀이 같고 실제 하드 자막 미디어까지 검증되어야 한다 — Tasks 3, 5.

---

## 파일 구조와 책임

아래 `S`는 파일 경로 표기용 `.agents/skills/ec2-solution-video`의 약칭이다. 실행 명령은 repo 루트에서 실행한다. Python 테스트는 기존 unittest fixture와 모듈 import 방식을 사용한다.

| 파일 | 책임 |
|---|---|
| Create `S/assets/writing-defaults.json`, `S/scripts/solution_video/writing.py` | 신규/legacy 작성 설정, 검증, asset metadata 로딩 |
| Modify `S/assets/pencil/pencil-yellow-v1.json` | 보정한 tip_px·end_px 추가; PNG/프롬프트 유지 |
| Modify `S/scripts/solution_video/{contracts,reveal}.py` | writing_spans 타입과 순수 타이밍 생성 |
| Create `S/assets/writing.js`; modify `S/assets/{player.js,layout.css}` | 프레임 상태·원본 보존 clip·연필 배치 |
| Modify `S/scripts/solution_video/composition.py` | 연필 동결·HTML 연결·작성 시작 기준 카메라 |
| Modify `S/scripts/video.py`, `S/scripts/solution_video/state.py` | prepare/retime CLI, stage별 지문 |
| Modify `S/tests/browser_check.mjs`, `S/scripts/solution_video/verify.py` | 실제 composition의 공개·seek·연필 게이트 |
| Create `S/tests/test_writing.py`, `S/tests/test_writing_runtime.cjs` | 설정/asset 단위 검사, 순수 JS 상태 검사 |
| Modify `S/tests/{test_reveal,test_composition,test_state,test_cli,test_verify,test_acceptance}.py`, `acceptance.py` | 회귀·실제 PDF 수용 검사 |
| Modify `S/SKILL.md`, `S/references/{narration-and-timing,verification}.md`; Create `docs/superpowers/reviews/2026-10-07-ec2-pencil-writing.md` | 사용자 명령·제약·실제 검증 범위 |

## Task 1: 작성 설정과 승인된 연필 asset 계약

**Files:** 위 `writing-defaults.json`, `writing.py`, 연필 metadata, `test_writing.py`.

**Interfaces:**
- Produces `default_writing(mode: str = 'pencil') -> dict`, `load_writing(run: Path, config: dict) -> dict`, `validate_writing(value: dict) -> None`.
- Produces `load_pencil_asset(asset_dir: Path) -> dict` with file, width, height, sha256, tip_px: [float,float], end_px: [float,float]. 부호 있는 회전/반전은 좌표를 바꾸지 않는다.
- 작성 설정 키는 schema_version, mode, chars_per_second, pencil_length_px, adjacent_move_frames, lifted_move_frames, tilt_degrees, read_hold_seconds, asset_id다. 값/검증 범위는 spec 그대로다. load_writing은 파일이 없으면 config의 기존 속도·hold를 가진 typing을 반환한다.

- [x] **Step 1: 실패 테스트 작성.** `test_new_defaults_and_legacy_fallback`, `test_invalid_writing_values`, `test_pencil_asset_contract`를 추가한다. 핵심 단언은 아래와 같고 NaN/Infinity·bool 프레임·알 수 없는 모드·asset_id·좌표 범위 밖·누락/손상/불투명 PNG를 표 기반 subTest로 거부한다.

```python
self.assertEqual(default_writing()['chars_per_second'], 5)
self.assertEqual(default_writing()['pencil_length_px'], 160)
self.assertEqual(load_writing(self.run, default_config())['mode'], 'typing')
self.assertEqual(default_writing('typing')['chars_per_second'], 7)
self.assertEqual(load_pencil_asset(S/'assets/pencil')['sha256'], '8f09ff6af2689c9cb50bab4382c4d18a46639312ea8d2edf42ad82c774d20269')
```

- [x] **Step 2: red 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_writing.py -v` → 새 writing 모듈/함수 부재로 FAIL; 환경 오류를 red로 세지 않는다.
- [x] **Step 3: 촉 좌표 보정.** 승인된 PNG를 실제 해상도로 보고 흑연 끝과 지우개 끝 중심의 픽셀 좌표를 metadata의 tip_px/end_px에 기록한다. 디버그 미리보기에서 촉 marker가 실제 끝과 1px 이내임을 확인한다. PNG를 편집하거나 bounding-box 모서리를 촉으로 쓰지 않는다.
- [x] **Step 4: 설정/asset 계약 구현.** 위 함수와 기본 JSON을 만들고 Pillow로 형식·alpha·실제 크기·해시·좌표를 검증한다. JSON과 검사 예외는 InputError로 정리한다. 명시적 설정은 누락 키를 조용히 legacy로 대체하지 않는다.
- [x] **Step 5: green 확인.** Step 2 명령 → 모든 새 테스트 PASS. PNG 원래 SHA256과 프롬프트 보존을 확인한다.
- [x] **Step 6: Commit.** 권한이 있으면 이 task의 설정/모듈/테스트와 승인된 asset 세 파일만 stage하고 `feat(ec2-video): define pencil writing settings`로 커밋한다.

## Task 2: 음성을 재사용하는 이동·작성 타이밍

**Files:** `S/scripts/solution_video/contracts.py:27`, `reveal.py:5`; `S/tests/test_reveal.py`.

**Interfaces:**
- Consumes Task 1의 validate_writing과 설정 dict, 기존 Manifest/PageLayers/AudioRecord.
- Produces `build_timeline(manifest, layers, audio, config, writing: dict | None = None) -> dict`. None은 기존 typing 결과를 유지한다.
- Timeline에 선택적 writing 설정과 writing_spans를 추가한다. 각 span은 kind(move|draw), id(대상 glyph), from_id(str|None), step_id, start_frame, end_frame을 가진다. 기존 events.frame은 완료 시점이다.

- [x] **Step 1: 실패 테스트 작성.** `test_pencil_six_frame_slots`, `test_lifted_moves_and_subscripts`, `test_whitespace_has_no_draw`, `test_legacy_timeline_unchanged`, `test_invalid_pcm_blocks_retime_data`를 추가한다. 동일 줄의 글자 2개는 move/draw가 각각 [0,1)/[1,6), [6,7)/[7,12)이고 완료 이벤트는 6/12다. 긴 이동은 move>=8, draw=5다. 공백은 draw 없이 6프레임, 원래 완료 순서·shape anchor는 유지한다. 짧은 PCM의 write 길이는 작성 종료+23프레임 이상, 긴 PCM은 음성 프레임+23 이상, total_samples=total_frames*800이다.

```python
self.assertEqual([(s['kind'], s['start_frame'], s['end_frame']) for s in t['writing_spans']], [('move',0,1),('draw',1,6),('move',6,7),('draw',7,12)])
self.assertEqual([e['frame'] for e in t['events'] if e['kind']=='glyph'], [6,12])
self.assertEqual(t['total_samples'], t['total_frames'] * 800)
```
- [x] **Step 2: red 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_reveal.py -v` → 새 writing 인자/구간 부재로 새 테스트 FAIL, 기존 검사는 유지.
- [x] **Step 3: 순수 타이밍 구현.** 인접 슬롯 N=ceil(30/chars_per_second), move=adjacent_move_frames, draw=max(2,N-move)로 계산한다. 기본은 1+5다. 다른 step, 이전 bbox 중심과의 거리>단계 대표 본문 높이*3, 또는 y 중심차>대표 높이*0.6이면서 x가 이전보다 작아진 경우를 긴 이동으로 분류하고 move=max(8,lifted_move_frames)로 늘린다. 대표 높이는 composition.py의 기존 단계별 비공백 glyph 높이 75 percentile 규칙을 공유한다. 첨자의 우측 이동을 줄바꿈으로 오인하지 않는다. 공백은 draw 없이 N프레임 이동하며 pencil은 숨긴다. from_id는 직전 비공백 glyph이고 첫 글자는 None이다. 글자 수가 없는 잘못된 write step/비공백의 0 크기 bbox는 InputError다.
- [x] **Step 4: green 확인.** Step 2 명령 → 기존/신규 PASS. writing을 생략한 결과의 이벤트·구간·길이가 기존 fixture와 같음을 확인한다.
- [x] **Step 5: Commit.** 권한이 있으면 contracts/reveal/test_reveal만 stage하고 `feat(ec2-video): schedule pencil moves and glyph draws`로 커밋한다.

## Task 3: 원본 SVG 점진 공개와 연필·카메라 연결

**Files:** Create `S/assets/writing.js`, `S/tests/test_writing_runtime.cjs`; modify `S/assets/player.js:8`, `layout.css:6`, `S/scripts/solution_video/composition.py:7`, `S/tests/browser_check.mjs:42`, `test_composition.py`.

**Interfaces:**
- Consumes Tasks 1–2와 기존 page_layout/camera viewbox. `assemble(..., runtime)`의 호출 인터페이스는 유지한다.
- Produces JS `EC2Writing.frameState(timeline, glyphs, frame) -> {span, progress}`; 활성 span이 없으면 span=null. draw/move progress는 clamp((frame-start)/(end-start-1),0,1), 1프레임 span은 1이다.
- Produces JS `EC2Writing.createRenderer(answerSvg, glyphs, pencilElement, assetMeta) -> {render(timeline, frame, camera, layout), snapshot()}`. frameState는 Node에서도 import 가능한 순수 함수, render는 모든 clip/연필 상태를 다시 계산한다.
- snapshot은 active_id, kind, progress, visible, tip_screen, pencil_length_px, pencil_bounds, masked_ids를 반환한다. 기존 `window.renderSolutionFrame(frame)`와 `window.__timelines.solution`은 유지한다.
- Timeline browser 결과에 writing: {seek_equal, precomplete_diff, complete_diff, hidden_leaks, tip_error_px, bounds_ok, final_visible}를 추가하고 기존 typing 결과 키는 유지한다.

- [x] **Step 1: 실패 테스트 작성.** JS `test draw/move endpoints and backward frameState`는 draw 프레임 1/3/5의 progress 0/0.5/1과 과거 seek 재현을 검사한다. Python `test_pencil_partial_and_precomplete`, `test_existing_clip_transform_and_grouped_glyph`, `test_camera_contains_pencil_at_four_edges`, `test_no_pencil_in_holds_or_whitespace`를 추가한다. synthetic SVG fixture에 공유 defs/중첩 clip/변환/다중 svg_ids/겹치는 첨자를 포함한다. partial은 미래 glyph 누출 0, 촉 경계 오차<=1px, 마지막 draw 프레임은 마스크 유지 상태로 원본 단일 glyph와 pixel_diff=0, 전체 완료는 전체 원본과 diff=0이어야 한다. 길이=160px±0.5, 기울기 절대값<=2°, 네 모서리 bounds가 [0,0,1920,900] 안이어야 한다.

```python
self.assertEqual(r['writing']['precomplete_diff'], 0)
self.assertEqual(r['writing']['complete_diff'], 0)
self.assertEqual(r['writing']['hidden_leaks'], 0)
self.assertLessEqual(r['writing']['tip_error_px'], 1)
self.assertTrue(r['writing']['bounds_ok'])
self.assertFalse(r['writing']['final_visible'])
```
- [x] **Step 2: red 확인.** `node --test .agents/skills/ec2-solution-video/tests/test_writing_runtime.cjs` 및 `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_composition.py -v` → 새 renderer/게이트 부재로 FAIL.
- [x] **Step 3: renderer 구현.** 각 glyph의 svg_ids마다 원본 요소를 변경하지 않는 wrapper와 추가 clip을 만든다. 페이지 bbox의 clip rect를 wrapper parent의 좌표로 변환한다: `parent.getScreenCTM().inverse().multiply(answerSvg.getScreenCTM())`. 기존 clip 속성을 덮어쓰거나 공유 defs를 바꾸지 않는다. 완료 글자의 clip을 해제하고 미래 글자는 opacity=0, 현재 글자는 현재 progress로만 공개한다. p=1에서도 추가 clip을 유지하는 테스트 모드를 둔다. draw 촉은 spec의 경계 좌표, 기울기는 2*sin(2*pi*progress)°다. move는 endpoint 사이에서 이동하고 lifted move는 위로 8*sin(pi*progress)px 들어 올린다. 미래 글자의 opacity를 이동 중 올리지 않는다.
- [x] **Step 4: composition/player 연결.** PNG·metadata·writing.js를 composition 최상위에 복사하고 runtime.json에 해시를 기록한다. `<img id=pencil>`은 화면 크기 고정, transform-origin은 보정한 촉이다. 기하학적 끝점 거리로 160px 배율을 계산하고 촉 기준 반전한다. pencil에서는 renderer가 glyph opacity/clip을 담당하고 player의 기존 opacity 루프는 shape만 처리해 현재 글자를 다시 숨기지 않게 한다. 기존 #cursor와 전체 opacity 루프는 typing 전용으로 유지한다. 브라우저 테스트는 img.decode를 기다려 로딩 경쟁을 막고 production asset 로딩 실패도 확인한다.
- [x] **Step 5: camera_keys 확장.** typing은 현재 경로를 유지한다. pencil은 move 시작 시점에 대상 glyph·최대 기울기 연필 envelope를 포함하는 viewbox를 선택하고 draw 동안 고정한다. 현재 카메라에 envelope가 들어가면 유지하고, 필요하면 반전/이동/배율 조정한다. 네 모서리의 연필 여백 확보에 필요한 만큼만 viewbox를 페이지 밖으로 확장해 흰 배경을 보이게 할 수 있다. 현재 본문 26px 및 최종 전체 페이지 hold 검사를 유지한다. 긴 move의 시작점은 직전 화면 좌표, 도착점은 새 카메라의 대상 좌표로 계산해 카메라 변경 시 연필이 화면 밖에서 시작하지 않게 한다. 정상 후보가 없으면 InputError다.
- [x] **Step 6: green 확인.** Step 2 두 명령 → PASS. browser_check의 writing 게이트에서 seek_equal=true, precomplete_diff=complete_diff=hidden_leaks=0, tip_error_px<=1, bounds_ok=true, final_visible=false를 확인한다. 원래 typing seek/final_cursor 검사도 통과해야 한다.
- [x] **Step 7: Commit.** 권한이 있으면 이 task Files만 stage하고 `feat(ec2-video): animate pencil over original PDF glyphs`로 커밋한다.

## Task 4: 무료 retime과 올바른 stage 재개

**Files:** `S/scripts/video.py:20,68,121`, `S/scripts/solution_video/state.py:6`; `S/tests/test_cli.py`, `test_state.py`.

**Interfaces:**
- Consumes default_writing/load_writing/load_pencil_asset와 새 build_timeline.
- Produces `prepare_batch(repo, selector, problem_ids=None, review=False, writing_mode='pencil') -> Path` 및 CLI `prepare ... --writing-mode pencil|typing`.
- Produces CLI `retime --run RUN [--writing-config JSON]`; 성공 JSON은 status=passed, paid_requests=0, total_frames를 포함한다. run_stage에 action=retime/stage=timing을 추가한다.
- stage_fingerprint의 timing projection은 mode/chars_per_second/adjacent_move_frames/lifted_move_frames/read_hold_seconds만 포함한다. composition은 전체 writing 설정, 선택한 asset 파일/metadata, writing.js를 포함한다. writing.py는 timing 도구 지문에 포함한다. source/config.json의 기존 voice 지문은 유지한다.

- [x] **Step 1: 실패 테스트 작성.** `test_prepare_writing_mode`, `test_retime_uses_current_verified_pcm_without_paid_calls`, `test_retime_rejects_tampered_or_stale_voice`, `test_writing_and_asset_first_invalid_stage`를 추가한다. config와 WAV를 고정한 채 속도 변경→timing, 길이/각도/유효하게 갱신한 asset→composition, 음성 설정→voice를 기대한다. legacy run은 typing이고 관련 없는 pencil asset 변경으로 무효가 되지 않아야 한다. generate_voice를 호출하면 즉시 실패하는 mock으로 retime의 paid_requests=0을 검사하고 WAV hash가 같음을 단언한다. state의 도구/asset 경로를 임시 복사본으로 patch해 실제 skill 파일을 테스트에서 변조하지 않는다.

```python
voice.assert_not_called()
self.assertEqual(result['paid_requests'], 0)
self.assertEqual(result['status'], 'passed')
self.assertEqual(file_hash(wav_path), original_hash)
# 독립 state fixture에서 speed만 바꾼 경우:
self.assertEqual(recover_run(self.run), 'timing')
```
- [x] **Step 2: red 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_cli.py -v` 및 같은 명령의 `-p test_state.py` → 새 명령/지문 동작 부재로 FAIL.
- [x] **Step 3: prepare/tts/retime 연결.** prepare는 명시적 writing 파일을 동결하고 tts 뒤 timing 생성도 load_writing을 사용한다. retime은 현재 manifest/coverage/gate 및 recover_run을 검사해 voice 이전 단계가 무효면 거부한다. source/audio.json의 전체 ID 대응, WAV sha256/mono/16-bit/24kHz/샘플 수를 검사한 뒤 build_timeline을 호출한다. 성공 음성·승인 파일·ledger를 수정하지 않는다. --writing-config는 실행 내부에 검증 후 원자적으로 저장한다. 잘못된 설정/PCM은 timeline을 덮어쓰기 전에 실패한다.
- [x] **Step 4: 지문 분리 구현.** writing 파일 전체를 timing glob에 넣지 말고 위 projection의 digest를 계산한다. composition부터 선택 asset 및 JS 지문을 추가한다. 하위 폴더 PNG는 재귀 탐색이 아니라 현재 선택된 명시 파일만 포함한다. assemble 출력 PNG/metadata도 finish_stage의 산출물 해시에 넣는다.
- [x] **Step 5: green 확인.** Step 2 두 suite → PASS; 기존 test_voice suite도 실행해 기존 review gate/음성 캐시 계약이 유지됨을 확인한다.
- [x] **Step 6: Commit.** 권한이 있으면 CLI/state와 관련 테스트만 stage하고 `feat(ec2-video): retime writing without regenerating voice`로 커밋한다.

## Task 5: 실제 composition 게이트·샘플·문서 인계

**Files:** `S/scripts/solution_video/verify.py:22`, `S/tests/test_verify.py`, `test_acceptance.py`, `acceptance.py`, `S/SKILL.md`, references 2개, 신규 review 문서.

**Interfaces:**
- Consumes Task 3 browser writing 결과와 Task 4의 명시적 writing/retime 동작.
- Produces verify_run의 writing_animation 검사. pencil은 실제 현재 composition에서 얻은 Task 3 게이트를 요구하고 검증 evidence와 현재 지문을 기록한다. typing은 기존 게이트를 유지한다.
- acceptance.py에 선택적 `--problems ID,ID`를 추가한다. 기본 대표 3문항은 그대로이고 선택 실행은 요청한 ID만 처리한다. acceptance.json에 selected_ids를 기록하고 test_acceptance는 그 목록에 맞춰 개수를 검사한다. 기존 로컬 PCM/production 게시 거부 정책을 유지한다.

- [x] **Step 1: 실패 테스트 작성.** `test_pencil_gate_failure_blocks_verify`, `test_typing_requires_no_pencil`, `test_selected_real_pdf_acceptance`를 추가한다. 원래 추출 gate가 통과해도 실제 composition의 partial leak/잘못된 촉/final pencil/diff/seek 실패는 complete=false여야 한다. 브라우저 결과 JSON을 임의 passed 파일로 대체하지 않는다. 선택 ID 수와 실제 hash를 검사한다.

```python
self.assertFalse(report['complete'])
self.assertEqual(report['checks']['writing_animation']['status'], 'unverified')
self.assertEqual(data['selected_ids'], ['E10.11'])
self.assertEqual(data['paid_requests'], 0)
self.assertEqual(data['live_audio'], 'unverified')
self.assertTrue(data['production_publish_blocked'])
```
- [x] **Step 2: red 확인.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_verify.py -v` → writing_animation 부재로 새 검사 FAIL.
- [x] **Step 3: 게이트와 선택 수용 구현.** verify_run에서 browser_check --mode timeline을 실행해 실제 현재 HTML/asset/frame 상태를 검사하고 게이트 증거를 verification에 저장한다. 모든 span의 수치상 촉/영역/순서 invariant를 확인하고, 각 step의 첫/중간/마지막 draw의 시작·중간·마지막 마스크 프레임과 모든 카메라 변경/긴 move/최종 hold를 screenshot 검사한다. pixel 비교는 연필 overlay를 제외한 answer SVG를 동일 카메라·배치로 렌더하고, partial 기준은 완료 glyph+현재 glyph의 기대 clip이며 미래 glyph는 숨긴 상태다. precomplete 기준은 완료 glyph+현재 glyph의 원본 윤곽이고 테스트 대상 마스크는 유지한다. 최종 기준은 원래 SVG의 상단 내용 영역이다. 검증 screenshot은 verification 폴더에 둔다. acceptance의 technical 판정에는 pencil일 때 writing_animation도 필수로 포함한다. fake PCM 검사는 live_audio=unverified/complete=false이며 publish는 계속 거부해야 한다.
- [x] **Step 4: 전체 코드 검증.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v` 및 Task 3 Node suite → PASS. opt-in 실제 미디어 suite skip은 실제 렌더 통과와 구분한다.
- [x] **Step 5: 짧은 무료 샘플 렌더.** Task 3 synthetic glyph fixture의 한글·첨자·분수·줄바꿈으로 scratch composition/PCM/MP4를 만들고 local HyperFrames check/render 및 libass 자막/전체 디코드를 실행한다. 1920×1080/30fps/24kHz, A/V 차이<=1프레임을 확인하고 시작/중간/줄바꿈/마지막 프레임을 직접 본다. 모든 중간 파일은 scratch의 제작자료에 둔다.
- [x] **Step 6: 실제 E10.11 수용 렌더.** 실행 시 로컬 HyperFrames entry를 찾아 절대 경로로 다음을 실행한다. `python3 .agents/skills/ec2-solution-video/tests/acceptance.py --dest "$EC2_PENCIL_SCRATCH" --hyperframes-entry "$EC2_HYPERFRAMES_ENTRY" --problems E10.11`. 출력된 BATCH를 `EC2_ACCEPTANCE_BATCH`에 지정하고 test_acceptance.py를 실행한다. 성공 기준은 writing gate/미디어 검사 통과, paid_requests=0, live_audio=unverified, production_publish_blocked=true다. 원본 native PDF와 실제 자막 영상을 대조하고 연필 크기·가림·움직임을 직접 검토한다. 기술 검사가 초록이어도 연출이 부자연스러우면 본 task를 완료하지 않는다.
- [x] **Step 7: 사용 문서와 검증 기록 갱신.** SKILL/references에 pencil 기본, typing 선택, retime, 5글자/초, 획순 한계, asset 검증/실패, 소리 없음, 실제 청취 구분을 반영한다. review 문서에는 실제 명령/버전/샘플 경로·hash/통과 수/skip/시각 검토/미검증 음성을 기록한다. 아직 실행하지 않은 검사나 실제 청취를 완료라고 쓰지 않는다.
- [x] **Step 8: Commit.** 권한이 있으면 이 task Files만 stage하고 `test(ec2-video): verify pencil writing on real PDF output`로 커밋한다. production 영상·scratch media를 stage하지 않는다.

## 계획 자체 검토

- 설계의 원본 보존/연필/카메라/도형/hold는 Tasks 2–3, 설정·호환은 Tasks 1/4, 게이트·실제 렌더·문서는 Task 5가 담당한다.
- 새 인터페이스 이름과 writing_spans의 완료 시점을 전 task에서 통일했다. 기존 4인자 build_timeline/assemble/typing 테스트와 prepare의 기존 positional 인자를 보존한다.
- Review Focus 다섯 항목 각각을 해당 task의 실패 테스트에 연결했다. PNG 보정은 이미지 생성/편집이 아닌 metadata 변경이다.
- 사용자는 Native/별도 워크트리를 선택했고 Tasks 1–5의 구현·검증을 마쳤다. Commit 단계는 권한이 없어 생략했다. 실제 미디어 수용이 통과했고 독립 리뷰를 진행 중이다. 결과는 review 문서와 ledger에서 추적한다. 5개 task가 timeline·렌더러·지문을 연속적으로 공유하므로 Native 구현 뒤 전체 독립 리뷰를 권장한다.
