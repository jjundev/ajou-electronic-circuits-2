# 회로 주석과 풀이 포커스 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 상단 회로·표와 원본 풀이 사이의 포커스 이동 및 회로 위 주석 필기를 추가한다.

**Architecture:** 선택적인 focus/annotations 파일을 원본 공개 데이터와 분리한다. 실측 음성에 연출 최소 시간을 반영하고, 별도 SVG 그룹과 공통 카메라·연필 제어로 원본과 주석을 렌더한다. 연출의 시간/시각 지문을 분리하며 원본 및 주석을 각각 검증한다.

**Tech Stack:** Python 3 / unittest / PyMuPDF / Pillow, JavaScript / Node node:test / SVG / 로컬 GSAP / puppeteer-core / Chrome / HyperFrames / libass FFmpeg, 로컬 Pretendard-Bold.ttf.

**Spec:** [2026-10-07-ec2-focus-annotations-design.md](../specs/2026-10-07-ec2-focus-annotations-design.md). 원본 계약은 [ec2-solution-video 설계](../specs/2026-10-07-ec2-solution-video-design.md), [연필 설계](../specs/2026-10-07-ec2-pencil-writing-design.md), `.agents/skills/ec2-solution-video/SKILL.md`를 함께 읽는다. 설명 중 연필 숨김·도형 필기 제외는 새 spec의 주석 span에 한해 확장한다.

## Global Constraints

- PDF 답안의 문장·기호·수치·순서·줄바꿈·윤곽을 보존하며 완성 화면은 원본과 같아야 한다. 재조판·원본 이미지 교체로 결함을 숨기지 않는다.
- 1920×1080 / 30fps / mono PCM 24kHz를 유지한다. PDF 전체의 기존 16:9 또는 legacy 배치를 유지하고 자막 예약 영역은 하단 180px다.
- 원본 풀이 작성 본문은 화면상 최소 26px, 기존 연필 기본 길이는 160px, 기울기는 최대 ±2°다. 연필 전체는 1920×900 안에 있어야 한다.
- 전환 기본은 12프레임(0.4초), 작성 후 확인 시간은 최소 30프레임(1초), 주석 대상 간 연필 이동은 8프레임이다.
- 주석 도형 기본 작성 시간은 18프레임(0.6초), 명시적 시간도 18프레임 이상이다. 주석 글자는 초당 최대 5글자(글자당 6프레임: 이동 1 + 공개 5)다.
- 주석 기본 색은 #1565C0, 도형 선 두께는 화면상 3px다. 원본 기호를 덮지 않도록 실제 PDF에서 위치와 의미를 검토한다.
- 주석은 최종 전체 화면 직전까지 누적 유지한다. 명시적 hide_at을 지정한 주석만 더 일찍 숨긴다.
- TTS 공급자·모델·Aoede 설정은 유지한다. retime과 개발 검증은 유료 호출 0이며 fake PCM을 production 게시/실제 음성 검토로 승인하지 않는다.
- 자동 전역 설치·CLI 업그레이드를 하지 않는다. 실행 시 로컬 의존성 경로를 확인하고 누락은 명시적으로 보고한다.
- 기존 production 영상·PDF·노트·ec2-review-video 코드는 수정하지 않는다. 해당 스킬의 기존 로컬 글꼴만 읽기 전용으로 재사용한다.
- 구현 커밋은 사용자 커밋 권한이 있을 때만 수행한다. push/merge는 별도 명시 요청이 있어야 한다.

## Review Focus

1. 다른 답안의 region, NaN/bool 좌표, 존재하지 않는 segment, annotations 단독 입력: 해당 ID와 이유로 실패하며 무주석 모드로 대체하지 않는다 — Task 1.
2. 아주 짧은 PCM, 중간 check cue, 명시적 offset/hide, 긴 2단 풀이: 무음만 늘리고 이후 글자·WAV 배치·자막을 같은 시간 축으로 이동한다 — Task 2.
3. 극단적 비율의 표, 가장자리 기호, 누적 주석으로 넓어진 영역: 이름/주석/연필을 함께 포함하고 가독성과 경계가 양립하지 않으면 실패한다 — Task 3.
4. 중첩 clip/shared defs, 첨자·공백, legacy typing에 주석, 주석 완료 뒤 되감기: 원본과 주석을 보존하고 단일 연필 상태를 재구성한다 — Tasks 4, 5.
5. 파일 추가·삭제, 색/위치 수정, 시간 수정, 누락 주석·잔류·촉 변조: WAV를 보존하며 올바른 단계에서 재개하고 실제 composition 검증은 변조를 거부한다 — Tasks 5, 6.

---

## 파일 구조와 인터페이스 지도

아래 S는 `.agents/skills/ec2-solution-video`의 경로 약칭이다. 구현 계획의 모든 명령은 repo 루트에서 실행한다. 새 의존성은 추가하지 않는다. 기존 tests/fixtures.py의 Sandbox와 make_audio를 재사용한다. 실행 시 using-git-worktrees로 격리를 확인하고 이 spec/plan이 checkout에 존재하는지도 확인한다.

| 파일 | 책임 |
|---|---|
| Create `S/scripts/solution_video/annotations.py` | TeachingPlan/Annotation 정의, sidecar 검증, label/도형 geometry 동결 |
| Create `S/scripts/solution_video/teaching.py` | 최소 설명 시간, 연출 schedule, timing 지문, 기존 reveal 조합 |
| Create `S/scripts/solution_video/focus.py` | 그림/누적 주석/연필 bounds와 기존 카메라 합성 |
| Create `S/assets/camera.js` | 공통 cameraAt와 pageToScreen, 프레임 보간 |
| Create `S/assets/annotations.js` | path/label 상태와 PenState 반환 |
| Create `S/assets/pencil.js` | 단일 연필 PNG 제어·경계·mirror 상태 |
| Modify `S/scripts/solution_video/reveal.py:6-48` | keyword-only minimum_frames로 segment 뒤 무음 연장 |
| Modify `S/scripts/solution_video/composition.py:8-144` | geometry/카메라/asset 연결, typing 주석 지원 |
| Modify `S/assets/writing.js:8-69`, `S/assets/player.js:7-29` | 공통 카메라 사용 및 연필 상태 반환·중재 |
| Modify `S/scripts/video.py:91-139`, `S/scripts/solution_video/state.py:6-40` | 초기 TTS/retime의 동일 타이밍 빌더, 시각/시간 지문 |
| Modify `S/scripts/solution_video/verify.py:34-50`, `S/tests/browser_check.mjs:42-139` | 원본·주석·포커스·단일 연필 검증 |
| Create `S/tests/test_annotations.py`, `test_teaching.py`, `test_focus.py`, `test_teaching_runtime.cjs` | 순수 계약·타이밍·카메라·JS 테스트 |
| Modify `S/tests/test_{reveal,composition,cli,state,verify,media}.py`; create `test_subtitles.py` | 회귀/CLI/미디어 연동 테스트 |
| Create `S/tests/teaching_acceptance.py`, `test_teaching_acceptance.py` | 별도 opt-in 실자료 수용 검증 |
| Modify `S/SKILL.md`, `S/references/{pdf-and-coverage,narration-and-timing,verification}.md` | 저작·retime·검증 절차 |

Python의 TeachingPlan은 정규화된 `{schema_version,regions,cues,items}` dict이며 모든 기본값과 glyph 공개 단위 수를 가진다. CompiledAnnotations는 `{items,svg,font_sha256}`이고 items는 page bbox/path 또는 label glyph outlines 및 대표 본문 높이를 가진다. 타입 정의는 annotations.py에 둔다. TeachingSchedule은 timeline.teaching의 `{schema_version,timing_hash,cues,spans}`이며 geometry를 담지 않는다. PenState는 JS `{visible,tip_screen:[x,y]|null,tilt_degrees,mirror,owner}`다. owner는 writing 또는 annotation이다. Geometry/색은 composition에만, schedule은 source/timeline.json에도 동결한다.

### Task 1: 선택적 연출 파일과 검증 계약

**Files:** Create `S/scripts/solution_video/annotations.py`; create `S/tests/test_annotations.py`.

**Interfaces:** Consumes manifest segments, layers.metadata/map, spec의 JSON. Produces `load_teaching(run:Path,manifest:dict,layers:dict)->TeachingPlan|None`, `validate_teaching(focus:dict|None,annotations:dict|None,manifest:dict,layers:dict)->TeachingPlan|None`. 오류는 기존 InputError이며 파일/주석/segment ID를 포함한다.

- [ ] **Step 1: 실패 테스트 작성.** `AnnotationContractTests.test_optional_legacy_and_focus_only`는 파일 없음/빈 cue가 None, focus-only는 items=[]임을 검사한다. `test_invalid_authored_inputs`는 annotations 단독, stale source_sha256, 중복 ID, 없는 target/segment, write/problem cue, manual cameras 혼용, NaN/Infinity/bool, work_bbox 교차, 0길이 선/0면적 타원, label 25자·줄바꿈·LaTeX·지원하지 않는 문자, duration<18/label duration, offset<12/겹침에 모두 InputError를 기대한다. `test_normalized_defaults_and_label_runs`는 색 #1565C0, 도형 duration 18, hide_at='final', 첫 offset 12와 본문/첨자 run 순서를 검사한다. 유효 synthetic layers/manifest와 make_teaching_plan fixture도 이 테스트 파일에 정의해 후속 테스트가 import한다.

테스트 helper `teaching_fixture()->(focus,annotations,manifest,layers)`는 source 해시가 일치하는 400×300 페이지, 상단 region [20,40,180,90], work_bbox [100,100,300,240], intro/problem→r/reason→w/write 순서, a/arrow 한 개를 반환한다. arrow는 [60,50]→[60,80]이다. `make_teaching_plan()->TeachingPlan`은 이를 validate_teaching에 전달한 결과다. 대표 assertion:

```python
focus, annotations, manifest, layers = teaching_fixture()
plan = validate_teaching(focus, annotations, manifest, layers)
self.assertEqual(plan['items'][0]['duration_frames'], 18)
self.assertEqual(plan['items'][0]['offset_frames'], 12)
self.assertEqual(plan['items'][0]['hide_at'], 'final')
```
- [ ] **Step 2: 실패 확인.** Run `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_annotations.py' -v`; 새 함수 부재로 FAIL이어야 한다.
- [ ] **Step 3: 검증 구현.** annotations.py에 위 두 함수를 작성하고 spec의 각 geometry/선택 필드를 정규화한다. 입력 목록 순서를 유지한다. label font는 `S.parent/ec2-review-video/assets/fonts/Pretendard-Bold.ttf`, PyMuPDF Font.has_glyph로 검사하고 없어지면 실패한다. 원본 manifest/layers는 변경하지 않는다.
- [ ] **Step 4: 통과 확인.** Step 2 명령을 반복해 모든 계약 테스트 PASS 확인.
- [ ] **Step 5: 권한이 있으면 커밋.** `git add .agents/skills/ec2-solution-video/scripts/solution_video/annotations.py .agents/skills/ec2-solution-video/tests/test_annotations.py` 후 `git commit -m "feat(ec2-video): validate focus and annotation plans"`. 권한 없으면 커밋을 보류하고 검증 결과를 기록한다.

### Task 2: 음성을 보존하는 연출 타이밍

**Files:** Create `S/scripts/solution_video/teaching.py`, `S/tests/test_teaching.py`, `S/tests/test_subtitles.py`; modify `S/scripts/solution_video/reveal.py:6-48`, `S/tests/test_reveal.py`, `S/tests/test_media.py`.

**Interfaces:** Consumes Task 1 TeachingPlan. Produces `teaching_timing_settings(plan:TeachingPlan|None)->dict`, `minimum_segment_frames(plan:TeachingPlan|None)->dict[str,int]`, `build_teaching_timeline(manifest,layers,audio,config,writing,plan)->dict`. Extend `build_timeline(manifest,layers,audio,config,writing=None,*,minimum_frames:dict[str,int]|None=None)->dict`. Existing positional API and no-plan output stay unchanged.

- [ ] **Step 1: 실패 테스트 작성.** `TeachingTimingTests.test_short_voice_appends_silence`는 reason PCM=800, arrow offset=12, move=8, draw=18에서 reason 길이가 80프레임(12+8+18+30+12), voice_samples=800, 다음 write 시작=reason 시작+80임을 검사한다. `test_focus_only_minimum`은 54프레임을 검사한다. `test_late_check_offsets_labels_and_hide`는 check cue, 24자 label, 중간 hide binding, 후속 2단 쓰기 events/spans가 정확한 delta만큼 이동하고 reveal_order가 그대로임을 검사한다. `test_no_plan_byte_equivalent`는 기본 build_timeline과 결과 dict가 동일함을 검사한다. `test_timing_projection`은 위치/색/font_size 수정은 같은 지문, glyph 수/offset/duration/hide/cue 추가삭제는 다른 지문임을 검사한다. `SubtitleTests.test_post_padding_preserves_measured_caption_duration`과 `MediaTests.test_padded_segments_place_pcm_at_shifted_start`는 두 번째 WAV/자막만 정확히 같은 samples만큼 뒤로 이동하고 첫 자막이 무음까지 연장되지 않음을 검사한다. media 테스트는 FFmpeg 호출을 mock하고 생성 WAV의 nonzero PCM 위치를 직접 검사한다.

```python
self.assertEqual(minimum_segment_frames(make_teaching_plan())['r'], 80)
self.assertEqual(reason['voice_samples'], 800)
self.assertEqual(reason['end_sample'] - reason['start_sample'], 80 * 800)
self.assertEqual(write['start_sample'], reason['end_sample'])
```
- [ ] **Step 2: 실패 확인.** Run `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_teaching.py' -v`; 새 빌더 부재로 FAIL 확인.
- [ ] **Step 3: 기존 reveal의 최소 시간 구현.** 최소 시간은 write 길이를 계산한 뒤 n=max(n,minimum_frames.get(id,0))로 적용한다. 승인한 segment 순서와 원본 이벤트 생성을 유지한다. 음성/작성 시간은 줄이지 않는다.
- [ ] **Step 4: teaching 빌더 구현.** 최소 시간 계산 → 원본 build_timeline → segment samples에 연출 상대 spans/hide를 binding하는 순서다. span은 `{id,unit_index,kind:'move'|'draw',start_frame,end_frame,hide_frame}`이며 unit_index는 도형 0 또는 label 문자 순서다. 오브젝트 진입 move=8, label 내부는 1+5프레임/문자, 공백은 draw 없이 6프레임이다. 연출이 있으면 timeline.teaching에 schedule과 `timing_hash=digest(teaching_timing_settings(plan))`를 추가하고 원본 events에 주석 ID를 넣지 않는다. hide가 작성 완료 전이면 InputError다.
- [ ] **Step 5: 타이밍/미디어 테스트 통과 확인.** Run `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_reveal.py' -v`, 다음 `test_teaching.py`, `test_subtitles.py`, `test_media.py`를 같은 방식으로 실행; 모두 PASS. 기존 media/subtitles 코드는 해당 테스트가 실제 실패한 경우에만 최소 수정한다.
- [ ] **Step 6: 권한이 있으면 커밋.** 이 Task의 명시된 파일만 stage하고 `git commit -m "feat(ec2-video): schedule teaching pauses without regenerating voice"`.

### Task 3: 그림·누적 주석을 포함하는 공통 카메라

**Files:** Create `S/scripts/solution_video/focus.py`, `S/assets/camera.js`, `S/tests/test_focus.py`, `S/tests/test_teaching_runtime.cjs`; modify `S/scripts/solution_video/composition.py:8-100`, `S/assets/writing.js:8-10`, `S/tests/test_composition.py`.

**Interfaces:** Consumes Task 2 timeline, TeachingPlan and synthetic CompiledAnnotations (Task 4 will produce actual geometry). Produces `compile_focus_keys(manifest:dict,layers:dict,timeline:dict,plan:TeachingPlan|None,compiled:CompiledAnnotations|None,base_keys:list[dict])->list[dict]`, JS `EC2Camera.cameraAt(keys,frame)->{viewbox,mirror}`, `EC2Camera.pageToScreen(point,viewbox,layout)->[x,y]`. CommonJS export and window export both work. base_keys comes from existing camera_keys; no-plan returns it unchanged. Compiled item의 bbox/대표 본문 높이로 정확한 26px 가독성 기준을 계산한다.

- [ ] **Step 1: 실패 테스트 작성.** `FocusTests.test_return_before_first_writing_and_final_full`는 reason의 시작/종료-12에 transition_frames=12, 복귀 endpoint와 첫 작성 카메라가 동일, 모든 draw 동안 카메라 고정, final은 full임을 검사한다. `test_label_and_accumulated_bounds`는 region 밖 새 label과 이전에 남은 동일 region 주석 모두가 viewport 안에 들어감을 검사한다. `test_table_edges_and_infeasible_readability`는 legacy/16:9 극단 비율 표와 네 모서리의 연필까지 1920×900에 포함하거나 해당 region ID의 InputError가 나는지 검사한다. `test_no_next_write_and_duplicate_boundaries`는 종료 cue 복귀 full, 같은 프레임의 키 유일/정렬, overlap transition 오류를 검사한다. JS `camera interpolation is pure`는 key0=[0,0,400,300], key12=[100,60,200,150], transition=12에서 frame12는 이전 box, frame18은 [50,30,300,225], frame24는 목적지임을 검사하고 frame18 재조회가 같다. transition 없는 기존 키는 at_frame에 즉시 적용한다.

```javascript
const keys=[{at_frame:0,viewbox:[0,0,400,300]},
  {at_frame:12,viewbox:[100,60,200,150],transition_frames:12}];
assert.deepEqual(EC2Camera.cameraAt(keys,18).viewbox,[50,30,300,225]);
assert.deepEqual(EC2Camera.cameraAt(keys,24).viewbox,[100,60,200,150]);
```
- [ ] **Step 2: 실패 확인.** Run `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_focus.py' -v` 및 `node --test .agents/skills/ec2-solution-video/tests/test_teaching_runtime.cjs`; 함수 부재로 FAIL 확인.
- [ ] **Step 3: 공통 좌표 계산 구현.** camera.js에 위 API와 smoothstep 보간을 작성한다. writing.js의 자체 cameraAt/screen은 공통 API에 위임하고 mirrored는 같은 cameraAt 결과를 사용한다. 기존 원본 필기 키의 zero transition은 유지한다.
- [ ] **Step 4: focus 합성 구현.** focus.py에서 현재 region/표·label bbox·누적 주석·연필 envelope의 fit을 계산한다. 26px label 본문 및 3px stroke 여백을 검사하고 가독성 충돌은 ID가 있는 오류다. 복귀 목적지는 spec대로 다음 작성 첫 카메라이며 첫 이벤트 전에도 유지한다. cue 밖 기존 키는 보존한다. base 카메라의 endpoint와 synthetic 경계를 정규화한다. 작성 중 pan을 추가하지 않는다.
- [ ] **Step 5: 통과 확인.** Step 2 명령 및 `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_composition.py' -v`, `node --test .agents/skills/ec2-solution-video/tests/test_writing_runtime.cjs` 모두 PASS. legacy HTML에도 camera.js를 포함시키는 최소 연결은 이 Task에 포함한다.
- [ ] **Step 6: 권한이 있으면 커밋.** 이 Task 파일만 stage하고 `git commit -m "feat(ec2-video): move focus between figures and writing"`.

### Task 4: 주석 geometry·점진 공개 렌더러

**Files:** Modify `S/scripts/solution_video/annotations.py`, `S/tests/test_annotations.py`; create `S/assets/annotations.js`; extend `S/tests/test_teaching_runtime.cjs`.

**Interfaces:** Consumes Task 1 plan, Task 2 TeachingSchedule, Task 3 cameraAt/pageToScreen. Produces `compile_annotations(plan:TeachingPlan,layers:dict,dest:Path)->CompiledAnnotations` and JS `EC2Annotations.frameState(schedule,frame)->{active,progress,visible_ids}`, `EC2Annotations.createRenderer(svg,compiled)->{render(schedule,frame,camera,layout):PenState,snapshot():dict}`. snapshot includes visible_ids, active_id, progress, tip_screen and bounds. Original glyph renderer is not called here.

- [ ] **Step 1: 실패 테스트 작성.** `AnnotationGeometryTests.test_arrow_ellipse_and_label_outlines`는 arrow shaft+두 head 경로, ellipse 위 중앙 시작/시계 방향, v/x 첨자 run 원래 위치·bbox·glyph 순서 및 font_sha256을 검사한다. `test_shared_defs_and_missing_glyph`는 label마다 namespace가 다르고 없는 글꼴/문자는 실패함을 검사한다. JS `annotation frame state is seek safe`는 시작/중간/끝 progress 0/0.5/1, 완료 후 누적 유지, hide_frame에 숨김, 미래 숨김, 뒤로 조회 상태 일치를 검사한다. `label whitespace consumes time without pen`도 추가한다.

```javascript
const schedule={spans:[{id:'a',unit_index:0,kind:'draw',
  start_frame:20,end_frame:25,hide_frame:80}]};
assert.equal(EC2Annotations.frameState(schedule,22).progress,0.5);
assert.deepEqual(EC2Annotations.frameState(schedule,26).visible_ids,['a']);
assert.deepEqual(EC2Annotations.frameState(schedule,80).visible_ids,[]);
```
- [ ] **Step 2: 실패 확인.** Task 1 Python 명령과 Task 3 Node 명령 반복; geometry/runtime 함수 부재로 FAIL 확인.
- [ ] **Step 3: geometry 동결 구현.** compile_annotations는 도형을 제한된 내부 path로 만들고 label은 로컬 Pretendard와 PyMuPDF의 text_as_path SVG export를 사용한다. 기존 util.browser inventory로 실제 SVG glyph bounds를 측정하고 svg_ids를 `annotation-<id>-...`로 namespace한다. run baseline/첨자/공백 순서를 유지한다. 생성 파일은 dest 아래에만 저장하고 원본 layers 파일을 바꾸지 않는다. 외부 SVG/임의 HTML/path 입력을 허용하지 않는다.
- [ ] **Step 4: 상태/렌더 구현.** annotations.js는 매 frame 모든 item opacity/mask/dash 상태를 재설정한다. path는 getTotalLength/getPointAtLength 기반 연필 위치와 dash 공개, label은 기존과 같은 outline clip 공개를 적용한다. renderer는 연필 DOM을 직접 변경하지 않고 PenState만 반환한다. path가 없는 공백·설명·hide/final에서는 visible=false다.
- [ ] **Step 5: 통과 확인.** Task 1 Python 및 Task 3 Node 명령 모두 PASS. synthetic outline fixture와 완성 SVG에서 label 위치/첨자 pixel 비교를 추가하고 실제 브라우저에서 PASS 확인한다.
- [ ] **Step 6: 권한이 있으면 커밋.** 이 Task 파일만 stage하고 `git commit -m "feat(ec2-video): draw figure annotations from frozen geometry"`.

### Task 5: 단일 연필·CLI·재개 통합

**Files:** Create `S/assets/pencil.js`; modify `S/assets/{writing.js,player.js}`, `S/scripts/solution_video/{composition,state}.py`, `S/scripts/video.py`, `S/tests/{test_composition,test_cli,test_state}.py`, `S/tests/test_teaching_runtime.cjs`.

**Interfaces:** Consumes Tasks 1–4 API. Produces `EC2Pencil.createController(element,meta,settings)->{apply(writing:PenState,annotation:PenState):PenState,snapshot():dict}`. Extend existing writing renderer.render to return PenState while preserving snapshot compatibility. assemble signature remains unchanged. No new CLI flags; existing sidecar paths and retime suffice.

- [ ] **Step 1: 실패 테스트 작성.** `CompositionTests.test_annotation_and_original_share_one_pen`는 이동 중 양쪽 숨김, arrow 작성 중 owner=annotation, 원본 작성 중 owner=writing, 둘 다 visible이면 오류를 검사한다. `test_typing_annotations_load_pencil_but_legacy_does_not`는 typing+주석만 pencil asset을 요구하고 no-sidecar legacy 화면/스냅샷이 그대로임을 검사한다. `CLITests.test_teaching_retime_preserves_pcm_and_captions`는 generate_voice mock이 호출되지 않고 WAV 해시와 paid_requests=0, shifted SRT 및 timeline.teaching 저장을 검사한다. `StateTests.test_teaching_visual_timing_add_delete`는 좌표/색→composition, offset/duration/글자 수/hide/cue 추가삭제→timing, 모든 연출 파일 삭제→timing, font/PNG 변조→composition, 원본 음성 설정 변경→voice를 검사한다.

```python
self.assertEqual(result['paid_requests'], 0)
voice.assert_not_called()
self.assertEqual(after_wav_hashes, before_wav_hashes)
self.assertEqual(recover_run(self.run), 'composition')  # 색만 변경한 fixture
```
- [ ] **Step 2: 실패 확인.** Run `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_cli.py' -v`, 다음 test_state.py/test_composition.py와 Node runtime; 새 통합 assertions FAIL 확인.
- [ ] **Step 3: 공통 연필 구현.** pencil.js에 현행 writing.js의 PNG transform·크기·mirror·bounds 계산을 옮긴다. writing와 annotations renderer는 PenState를 반환하고 player는 두 renderer를 실행한 뒤 controller.apply를 한 번 호출한다. 둘 다 visible인 상태는 오류다. 주석 path mirror는 오브젝트 시작에 정해 작성 중 유지한다. 원본 snapshot/기존 bounds·촉 테스트는 보존한다.
- [ ] **Step 4: 조립 연결.** assemble에서 current plan을 로드하고 timing 지문을 source/timeline.teaching.timing_hash와 비교해 stale이면 retime 요구. geometry를 `composition/annotations/`에 동결하고 CompiledAnnotations를 compile_focus_keys에 전달한다. namespace된 SVG group, camera/annotations/pencil JS와 font/geometry 해시를 runtime.json에 포함한다. 같은 함수는 no-plan 때 기존 branch를 보존한다. 주석이 있으면 typing이어도 PNG metadata/asset을 검사한다. finish_stage가 중첩 geometry까지 기록하도록 composition output 수집을 rglob으로 바꾼다.
- [ ] **Step 5: CLI/지문 연결.** tts 후 build와 retime은 build_teaching_timeline을 사용한다. retime은 현재 content/PCM 검사를 유지한다. sidecar 검증을 check/tts/retime/assemble 진입에 적용하되 시각 sidecar는 script/voice FACTORS에 넣지 않는다. check/tts는 paid 호출 전에 오류를 찾는다. state는 timing 단계부터 정규화된 timing projection·두 sidecar의 존재 여부·teaching.py 해시, composition부터 sidecar 전체·annotations.py/focus.py·font·관련 asset 해시를 포함한다. 입력 파싱 오류를 빈 plan으로 바꾸지 않는다. 파싱 오류는 main의 기존 실패 JSON으로 전달한다.
- [ ] **Step 6: 통합 회귀 통과 확인.** Step 2 명령과 `node --test .agents/skills/ec2-solution-video/tests/test_writing_runtime.cjs .agents/skills/ec2-solution-video/tests/test_teaching_runtime.cjs` 모두 PASS. PNG 손상/typing/final 숨김도 포함한다.
- [ ] **Step 7: 권한이 있으면 커밋.** 이 Task 파일만 stage하고 `git commit -m "feat(ec2-video): integrate teaching annotations and reusable timing"`.

### Task 6: 실제 composition 검증 게이트

**Files:** Modify `S/scripts/solution_video/verify.py`, `S/tests/browser_check.mjs`, `S/tests/test_verify.py`; extend `S/tests/test_composition.py`.

**Interfaces:** Consumes current source plan/audio, build_teaching_timeline, compile_focus_keys, compiled geometry. Produces browser mode `teaching` (same --entry/--layers/--timeline/--dest arguments) with `{timeline_equal,cameras_equal,seek_equal,gsap_seek_equal,bounds_ok,inactive_hidden,tip_error_px,original_pixel_diff,annotation_pixel_diff,future_leaks,final_visible,evidence}`. verify stores verification/teaching.json and requires all booleans true, diff/leaks=0, tip_error_px<=1, final_visible=false. No plan yields teaching_animation=passed without loading pencil.

- [ ] **Step 1: 실패 테스트 작성.** `VerifyTests.test_teaching_mutations_block_completion`는 주석 삭제, opacity 선공개, pen transform 이동, 최종 주석 잔류, camera endpoint 변조 각각 teaching_animation=unverified와 complete=false를 기대한다. `test_original_gate_survives_annotations`는 주석이 있는 실행에서도 원본 gate/각 표본의 주석 숨긴 비교가 0임을 검사한다. `test_typing_teaching_is_not_exempt`는 typing의 주석 검사도 실제 렌더를 읽음을 검사한다. `test_schedule_and_evidence_tamper`는 source/composition schedule 또는 증거 해시 변조를 거부한다.

```python
self.assertEqual(report['checks']['teaching_animation']['status'], 'unverified')
self.assertFalse(report['complete'])
self.assertEqual(report['checks']['original_svg']['status'], 'passed')
```
- [ ] **Step 2: 실패 확인.** Run `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_verify.py' -v`; 새 gate 부재로 FAIL 확인.
- [ ] **Step 3: 브라우저 oracle 구현.** teaching mode는 전환 시작/중간/끝, 모든 주석 move/draw 끝과 hide 전후, 각 단계 대표 원본 draw, final을 캡처한다. camera expected는 Python expected keys를 별도 평가, 주석 expected는 입력 geometry를 별도 SVG에 그려 정해진 부분만 공개하고 주 renderer의 mask/opacity를 복사하지 않는다. 원본 oracle에는 주석 그룹을 포함하지 않는다. 원본·주석 비교 시 pen만 제외하고 경계/촉은 별도로 검사한다. 역방향/무작위(고정된 명시 목록)/GSAP seek를 같은 프레임과 비교한다.
- [ ] **Step 4: verify 연결.** 현재 입력으로 build_teaching_timeline과 geometry/camera를 다시 계산한다. 원본 timeline 비교는 core와 teaching schedule 모두를 비교하며 geometry/compiled camera는 별도 비교한다. writing_animation은 원본 글자/span만 담당하고 최종 PenState의 writing owner를 검사한다. teaching_animation은 annotation/포커스를 담당한다. teaching 없는 기존 모드는 현행 검사를 유지한다. 검증 JSON에 도구·입력·증거 해시를 포함한다.
- [ ] **Step 5: 통과 확인.** Step 2 및 test_composition.py 모두 PASS. 변조 tests가 실제 HTML 상태를 바꾸고 검증 실패를 확인하는지 직접 읽어 확인한다.
- [ ] **Step 6: 권한이 있으면 커밋.** 이 Task 파일만 stage하고 `git commit -m "test(ec2-video): verify annotation focus and rendered pen states"`.

### Task 7: 실자료 수용 검증과 제작 절차

**Files:** Create `S/tests/teaching_acceptance.py`, `S/tests/test_teaching_acceptance.py`; modify `S/SKILL.md`, `S/references/{pdf-and-coverage,narration-and-timing,verification}.md`.

**Interfaces:** Consumes Tasks 1–6 and existing acceptance.author(run) only for frozen source mapping. Produces opt-in CLI `python3 .agents/skills/ec2-solution-video/tests/teaching_acceptance.py --dest ABS_SCRATCH --hyperframes-entry ABS_CLI`; report `teaching-acceptance.json` with selected_ids, paid_requests=0, production_publish_blocked=true, live_audio='unverified', item teaching/media hashes and checks. `EC2_TEACHING_ACCEPTANCE_REPORT` optionally points to this report for test_teaching_acceptance.py.

- [ ] **Step 1: 실패 테스트 작성.** `TeachingAcceptanceTests.test_fake_voice_cannot_publish`는 fake PCM report가 production 검증/게시를 승인하지 못함을 검사한다. `test_current_report_media_hash_and_teaching_checks`는 opt-in report의 3문항 순서 E10.11/E10.13/2021-1_중간-Q3, final 파일 SHA256 일치, paid=0, live_audio='unverified', teaching 검증/원본 diff=0과 media decode/frame sync PASS를 검사한다. env 없으면 해당 실제 렌더 테스트만 명시 skip한다. synthetic 표/복수 그림/그림 없음/가장자리 fixtures는 기본 unit suite에서 이미 실행되므로 opt-in으로 숨기지 않는다.

```python
self.assertEqual(data['paid_requests'], 0)
self.assertEqual(data['live_audio'], 'unverified')
self.assertTrue(data['production_publish_blocked'])
self.assertEqual([i['problem_id'] for i in data['items']],
                 ['E10.11', 'E10.13', '2021-1_중간-Q3'])
```
- [ ] **Step 2: 실패 확인.** Run `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_teaching_acceptance.py' -v`; fake publish/report contract test가 FAIL, opt-in만 skip인지 확인한다.
- [ ] **Step 3: scratch 수용 runner 작성.** 기존 acceptance.py:56-60처럼 scratch에 복습노트/교과서/from_the_past의 읽기 전용 source view를 만들고 prepare의 repo를 scratch로 지정한다. 기존 acceptance.author를 사용한 뒤 실제 PDF를 보고 짧은 reason/check와 회로 좌표·화살표/label을 추가한다. 대본이 달라진 content review 해시를 다시 계산한다. synthetic PCM은 의미 검토와 구별하고 generate_voice를 호출하지 않는다. assemble→render→captions→teaching/browser/media gates를 수행해 report를 남긴다. 실제 의미/음성 검토 passed를 만들어 production verify를 우회하지 않는다. 원자료 해시를 전후 비교한다.
- [ ] **Step 4: 기본 전체 회귀 실행.** Run `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_*.py' -v` 및 `node --test .agents/skills/ec2-solution-video/tests/test_writing_runtime.cjs .agents/skills/ec2-solution-video/tests/test_teaching_runtime.cjs`; 모든 기본 테스트 PASS, opt-in skip만 허용한다.
- [ ] **Step 5: 실제 미디어 검증.** 실행 환경의 util.node_package('hyperframes')로 package.json 경로를 찾아 같은 package의 dist/cli.js를 확인하고 ABS_CLI로 지정한다. 새 임시 scratch 디렉터리 ABS_SCRATCH를 만들고 위 CLI를 실행한다. Run `EC2_TEACHING_ACCEPTANCE_REPORT=ABS_SCRATCH/teaching-acceptance.json python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_teaching_acceptance.py' -v`; opt-in까지 PASS. 최종 자막본의 회로→주석→풀이→복귀 및 긴 2단 이동 장면을 직접 확인한다. 로컬 도구 누락/렌더 실패는 미검증으로 남기고 다른 framework로 대체하지 않는다.
- [ ] **Step 6: 스킬/참조 갱신.** focus/annotations JSON, 주석 의미 검토, 두 렌더러와 공통 연필, typing 주석, 기본 누적 및 final 숨김, 무음 패딩/retime, timing/composition 지문, 원본/주석 검증과 증거 경로를 문서화한다. 기존 출력 디렉터리/파일명은 유지한다. 새 기능의 비용 0 개발 검증과 실제 Aoede 음성 검증을 구분한다.
- [ ] **Step 7: 권한이 있으면 커밋.** 이 Task 파일만 stage하고 `git commit -m "docs(ec2-video): document and validate annotated teaching videos"`.

## 계획 자체 검토

- Spec coverage: sidecar/저작 제약 T1, 시간·무음·자막 T2, 포커스/26px/경계 T3, geometry·누적·hide T4, 단일 연필/typing/재개 T5, 원본·주석 검증 T6, 실자료/출력/스킬 T7. 제외 범위는 구현하지 않는다.
- Step scan: tests는 이름/수치/assertion을 명시하고 code는 정확한 함수명·입출력·정책을 지정했다. code body를 전사하지 않는다. 각 Task는 독립 테스트·리뷰 단위다.
- Type consistency: TeachingPlan/CompiledAnnotations는 annotations.py, TeachingSchedule은 teaching.py가 생성한다. cameraAt는 상태 객체이고 render에 전달하는 camera는 그 viewbox다. 모든 PenState는 screen 좌표이며 controller만 DOM을 변경한다.
- Review Focus: 다섯 항목은 T1/T2/T3/T4–5/T5–6의 실패 테스트와 대응한다. opt-in 실제 미디어 외 기본 검증을 skip하지 않는다.
- Proportion: 설계에 없는 제품 기능·원본 계산을 추가하지 않았다. 수행 순서와 인터페이스를 잠갔으며 fixture는 기존 관례를 사용한다.

## 실행 결과

2026-10-07 사용자가 Native를 선택했다. `codex/ec2-focus-annotations` 작업트리에서 7개 작업을 구현했다. 사용자 커밋 권한이 없는 조건에 따라 커밋·push·merge는 보류했다.

- focus/annotations sidecar, 무음 패딩과 retime, 카메라 전환, 원본·주석의 단일 연필, 시각/시간 지문과 독립 SVG 검증을 연결했다.
- 독립 리뷰의 화살촉 선공개와 label oracle의 공유 defs를 각각 실패 테스트 후 수정했다. 실자료에서 발견한 복귀 연필 좌표 오류와 기존 긴 연필 설정의 경계도 실패 테스트 후 수정했다.
- 3개 실자료의 최종 자막 MP4를 로컬 HyperFrames로 렌더했다. 원본·필기·주석·카메라·촉·seek·미디어·자막 기술 검증을 통과했다. 추가 유료 호출은 0이다.
- 개발 음성은 synthetic PCM이다. 실제 Aoede 음성 및 최종 의미 검토를 승인하지 않았으며 production 게시는 차단된다.

검증 기록은 `.superpowers/sdd/2026-10-07-ec2-focus-annotations/progress.md`, 실자료 보고서는 `.superpowers/acceptance-focus/teaching-acceptance.json`에 있다. 미커밋 변경을 보존하기 위해 작업트리와 ledger를 유지한다.

최종 증거: Python 102개 중 100개 통과 / opt-in 2개 skip, 실자료 opt-in 2/2 및 Node 4/4 통과. 긴 연필 경계와 독립 실행 시 글꼴 참조도 회귀 검증했다. 최신 도구 지문으로 실자료 3개를 재검증하고 증거 해시를 확인했다.
