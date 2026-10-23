# EC2 Circuit Ink Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** P10.72 회로 설명에 음성 청크와 맞는 여러 색·굵기의 필기를 추가한다.

**Architecture:** 기존 annotations → teaching timeline → SVG/runtime → focus camera 흐름을 확장한다. 주석 계약은 annotations.py, 실측 시간 결정은 teaching.py, 화면 표시와 독립 검증은 JS에 둔다. 음성 생성 경로는 변경하지 않는다.

**Tech Stack:** Python unittest/PyMuPDF, SVG, JavaScript/node:test, GSAP/HyperFrames/Chrome, libass FFmpeg.

**Spec:** docs/superpowers/specs/2026-10-09-ec2-circuit-ink-design.md

## Global Constraints
- 도형 stroke_width_px는 유한한 숫자 2~12px, legacy 생략값3px, 신규 저작4·6·8px다. label에는 이 필드를 허용하지 않는다.
- 파랑 #1565C0 연결, 주황 #C45100 M4 유입, 초록 #237A43 I2, 자주 #8E348E RL 결과를 사용한다.
- 1920×1080/30fps, mono PCM24kHz/16bit, 1프레임800샘플을 유지한다.
- 원본 회로·중앙 풀이·나레이션·자막 내용·작성 속도 및66개 WAV 해시를 보존한다. 유료 호출0이다.
- 실제 음성 청취를 하지 않았다면 live_audio=unverified, complete=false; publish/latest를 갱신하지 않는다.
- 사용자가 계획 확인을 마치고 native 구현을 승인했다. 커밋·푸시는 별도 사용자 요청 시 실행한다.

## Review Focus
1. 서로 다른 청크의 offset이 같아도 절대시간은 다르다. 잘못된 상대시간 비교로 정상 주석을 거부하지 않는다(Task2).
2. 경계가800샘플 배수가 아닐 때 발화 밖으로 선이 나가지 않는다(Task2).
3. 최대12px 화살촉과 선 끝이 확대 화면 밖에 잘리지 않는다(Task3).
4. 과거 chunk 없는 주석은 기존3px·순차 오프셋·silence padding 동작을 유지한다(Task1/2).
5. 많은 label이 실제 발화보다 오래 걸리면 무음을 늘리지 않고 id를 포함한 오류를 반환한다(Task2/4).

---

## 파일 구조
경로 기준은 repository root, K=.agents/skills/ec2-solution-video다.
- K/scripts/solution_video/annotations.py: schema와 SVG에 굵기·청크 메타데이터 보존.
- K/scripts/solution_video/teaching.py: 청크 절대시간 해석·중첩/기한 검증·timing projection.
- K/assets/annotations.js: 카메라 배율로 보정한 주석별 선 굵기.
- K/scripts/solution_video/focus.py: stroke/화살촉과 펜을 포함한 구도.
- K/tests/teaching_check.mjs: 원본 입력에서 독립적으로 계산한 선 굵기/경계/시간 오라클.
- K/scripts/solution_video/lesson.py, K/tests/test_lesson.py: 필요 시 청크별 표시 프로브 추가; 기존 단계 근거 게이트 유지.
- K/tests/test_annotations.py, test_teaching.py, test_teaching_runtime.cjs, test_focus.py, test_state.py: 소유 기능의 회귀 검사.
- K/SKILL.md, references/pdf-and-coverage.md, references/narration-and-timing.md, references/verification.md: 저작·검증 정책.
- 새 실행의 source/annotations.json, focus.json, lesson.json과 verification/circuit-ink-review.json: 이번 문제의 필기 저작/근거. 기존 실행은 보존한다.

### Task 1: 주석별 색·굵기 계약과 화면상 굵기
**Files:** Modify K/scripts/solution_video/annotations.py:69-104,126-170; K/assets/annotations.js:25-33; K/tests/teaching_check.mjs:94-101; Test K/tests/test_annotations.py, K/tests/test_teaching_runtime.cjs.

**Interfaces:** Consumes 기존 validate_teaching(focus,annotations,manifest,layers)->dict|None. Produces 동일 반환 items에 도형별 stroke_width_px:float, compile_annotations(plan,layers,dest)->dict items에 동일 값. JS createRenderer(svg,compiled)의 외부 인터페이스 유지.

- [x] **Step1: 실패 검사 추가.** test_stroke_width_contract에서 생략값==3, 입력2/4/6/8/12/4.5 보존, 1.9/12.1/True/"6"/NaN/infinity 거부를 단언한다. test_label_rejects_stroke_width를 추가한다. test_compiled_stroke_and_color에서 SVG와 compiled item의6px/#C45100 보존을 단언한다. Node 테스트는 실제 renderer의 DOM mock 또는 browser fixture에서 두 카메라 배율의 strokeWidth×scale==6, 섞인4·8px 보존과 뒤로 seek한 결과 일치를 검사한다.
- [x] **Step2: RED 확인.** `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_annotations.py -v` 및 `node --test .agents/skills/ec2-solution-video/tests/test_teaching_runtime.cjs`. 기대: 새 계약/고정3px 때문에 새 검사 실패.
- [x] **Step3: 최소 구현.** 기존 함수에서 수치 계약을 검증·정규화하고 SVG/compiled JSON에 값을 유지한다. runtime은 item.stroke_width_px(legacy fallback3)/camera scale을 사용한다. teaching_check의 독립 오라클도 입력의 값을 사용하되 production helper를 호출하지 않는다.
- [x] **Step4: GREEN 확인.** Step2 명령 모두 PASS, 기존3px fixture 포함.
- [x] **Step5: 변경 검토.** `git diff --check` PASS; Task1 파일만 diff로 검토한다. 커밋 요청 시 메시지 `feat(ec2-video): support per-annotation ink width`로 이 범위만 stage한다.

### Task 2: PCM 청크 기준 필기 스케줄
**Files:** Modify K/scripts/solution_video/annotations.py:67-112, K/scripts/solution_video/teaching.py:6-34; Test K/tests/test_annotations.py, test_teaching.py, test_state.py.

**Interfaces:** Consumes Task1의 TeachingPlan 및 기존 timeline.caption_cues[{segment_id,chunk_id,start_sample,end_sample}]. Produces teaching.py의 resolve_annotation_windows(plan:dict,timeline:dict)->list[dict] with id,start_frame,end_frame,hide_frame. build_teaching_timeline(manifest,layers,audio,config,writing,plan)->dict 외부 서명 유지; 기존 teaching.spans를 이 windows에서 생성한다.

- [x] **Step1: 실패 검사 추가.** test_chunk_annotation_contract는 없는/다른 segment chunk와 legacy manifest의 chunk_id, 음수/bool offset, segment 안의 legacy/chunk 혼합 거부를 검사한다. test_chunk_absolute_windows는 segment start100frame, chunk starts80000/104001samples, offset0일 때 move starts112/131frame을 단언한다. start는ceil, end deadline은floor다. 같은offset0인 두 청크 허용, 같은청크 중첩 거부, draw18+move8이 기한을1frame 넘기면 오류를 검사한다. label24자는152frame 필요하므로 짧은청크에서 id를 포함한 오류를 검사한다. 카메라 복귀 직전 완료는 segment.end_frame-13 이내인지 검사한다. hide_at legacy segment 기준과 early hide 거부도 검사한다.
- [x] **Step2: RED 확인.** `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_teaching.py -v`; Task1 annotation 명령도 실행. 기대: chunk 시간 해석이 없어 새 검사 FAIL.
- [x] **Step3: 계약 검증 구현.** validate_teaching에서 chunk 참조를 검증하고 offset 기준을 정규화한다. chunk mode는 chunk별 authored order만 사전 검사하고 실제 샘플 시간 중첩은 다음 단계에 위임한다. legacy 계약은 그대로 유지한다.
- [x] **Step4: 시간 해석 구현.** resolve_annotation_windows는 ceil(start_sample/800)+offset과 first-camera floor를 사용하고 각 window의 전체 이동/필기 시간, 청크 end floor, 복귀 deadline, hide를 검증한다. build_teaching_timeline은 legacy minimum만 기존 방식으로 계산하고 chunk items 때문에 silence를 늘리지 않는다. 새 window 중첩은 절대 frame으로 검사한다. timing projection에 chunk_id/offset/duration/units/hide를 포함하고 색·굵기는 제외한다.
- [x] **Step5: GREEN과 invalidation 확인.** Step2와 `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_state.py -v` 모두 PASS. test_chunk_and_style_invalidation은 chunk 변경→timing 무효, 색/굵기 변경→composition 무효, voice fingerprint/WAV 해시 유지를 단언한다. 기존 short_voice_appends_silence 테스트를 유지한다.
- [x] **Step6: 변경 검토.** `git diff --check` PASS; 요청 시 Task2 파일만 `feat(ec2-video): bind circuit marks to speech chunks`로 커밋한다.

### Task 3: 굵은 필기의 구도·표시 검증과 지침
**Files:** Modify K/scripts/solution_video/focus.py:8-54, K/tests/teaching_check.mjs, K/scripts/solution_video/lesson.py:56-79, K/SKILL.md, K/references/pdf-and-coverage.md, narration-and-timing.md, verification.md; Test K/tests/test_focus.py, test_lesson.py, test_teaching_acceptance.py.

**Interfaces:** Consumes compiled.items의 bbox/stroke_width_px와 Task2 windows/spans. Produces 기존 compile_focus_keys(manifest,layers,timeline,plan,compiled,base_keys)->list[dict]의 안전한 viewbox 및 teaching_check 결과. lesson_expectations(lesson,manifest,timeline,teaching)->dict의 기존 probes를 유지하면서 chunk 주석에는 각 청크의 완료 frame/annotation_ids를 추가한다.

- [x] **Step1: 실패 검사 추가.** test_thick_arrow_screen_bounds는12px의 선/화살촉의 실제 painted extents가1920×900 안에 들어오는지 검사한다. test_label_fit_retains_26px는 여백의 label과 펜까지 fit하고 최소26px 유지 또는 명확한 fit 오류를 단언한다. test_chunk_evidence_probes는 마지막 표시 하나가 아니라 참조한 모든청크에 완료후/숨김전/안정카메라의 probe가 존재함을 단언한다.
- [x] **Step2: RED 확인.** `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_focus.py -v`와 동일 명령의 `-p test_lesson.py`. 기대: stroke 반경/청크 프로브 누락 검사 FAIL.
- [x] **Step3: 최소 구현.** focus fit 계산과 독립 화면검사에 stroke의 화면상 반경(width/2), round cap, 생성된 화살촉 좌표를 포함한다. label fit26px는 유지한다. lesson_expectations는 청크별 완료후 안정 frame을 추가하며 legacy 단계 프로브는 유지한다.
- [x] **Step4: GREEN 확인.** Step2와 `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_teaching_acceptance.py -v` PASS. acceptance가 실제 run 없이 skip하면 Task4 실제 영상 검증으로 보충한다.
- [x] **Step5: 지침 동기화.** 스킬과3개 reference에 굵기/색/청크 시간/정리 정책, '같은 타원 반복으로 회로 설명을 대신하지 않고 연결·방향·변화량을 해당 발화에 표시한다' 기준, 청크별 의미 검토와 실청취 한계를 명시한다.
- [x] **Step6: 변경 검토.** `git diff --check` PASS; 요청 시 이 범위를 `feat(ec2-video): verify circuit ink framing and teaching cues`로 커밋한다.

### Task 4: P10.72 필기 저작과 검토용 영상 재생성
**Files:** Create 새 실행 under 문제풀이영상/1007/1007_제작자료/실행/<실행ID>-circuit-ink/videos/problem-d885c8738da3/; Modify 그 실행의 source/annotations.json, source/focus.json, source/lesson.json; Create verification/circuit-ink-review.json, verification/circuit-ink-before-after.json 및 재생성 미디어.

**Interfaces:** Consumes Tasks1–3과 원본 run `문제풀이영상/1007/1007_제작자료/실행/20261009-200646-shape-speed/videos/problem-d885c8738da3`. Produces 재검증된 renders/final.mp4와 최종해시, 12청크 검토표, 기존66WAV 보존증거. 기존 CLI check/retime/assemble/render/captions/verify 인터페이스 유지.

- [x] **Step1: 작업본과 기준 동결.** 원본 실행·batch를 새 실행으로 복사하고 run/batch metadata의 경로만 새 위치로 조정한다. 경로가 들어 있는 이전 stage/parts/composition/report를 신뢰하지 않고 필요한 단계를 재계산한다. 변경 전66WAV SHA256, total_frames, segment start/end, caption start/end와 원본 final 해시를 비교 파일에 기록한다. 원본 실행과 기존 비교HTML은 수정하지 않는다.
- [x] **Step2: 회로 필기 저작.** 설계의12행에 맞춰 original native PNG/SVG·MD에서 좌표와 기호를 대조한다. 모든 item에 chunk_id/offset_frames/color/도형굵기/source_refs/meaning_notes/hide_at을 명시한다. label은 font_size와 첨자runs를 저작한다. lesson annotation_ids와 focus bbox를 실제 item에 맞춘다.
- [x] **Step3: 무비용 시간 검증.** `python3 .agents/skills/ec2-solution-video/scripts/video.py check --run "$EC2_INK_RUN"`, 다음 `retime --run "$EC2_INK_RUN"`. 둘 다 passed/paid_requests0이어야 한다. 초과는 표시 수·짧은label·offset을 수정해 해결하고 음성/영상 길이를 늘리지 않는다. 기존 stages가 도구 변경으로 stale이면 동일 내용의 prerequisite 검증을 refresh하되 tts를 호출하지 않는다.
- [x] **Step4: 조립·렌더·자막.** 현재 설치 경로를 확인하고 assemble의 --runtime, render의 --hyperframes-entry, captions를 차례로 실행한다. FFmpeg는 /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg 사용 가능 여부를 확인한다. CLI 경로는 이전 npx 캐시를 검증 후 사용하며 새 패키지를 자동 설치하지 않는다.
- [x] **Step5: 의미·화면 검토.** 각12청크에서 시작/작성중/완료 프레임을 실제 확인하고 circuit-ink-review.json에 segment_id/chunk_id/annotation_ids/source_refs/notes/evidence와 전류방향·부호·색역할·기호비가림 검토를 기록한다. reason_1/2의 I2 감소가 방향반전으로 표현되지 않았는지 확인한다. 짧은청크와 긴label의 에러테스트도 이 실제저작에 적용한다.
- [x] **Step6: 전체 회귀 검사.** `PYTHONPATH=.agents/skills/ec2-solution-video/scripts EC2_FFMPEG=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v`와 `node --test .agents/skills/ec2-solution-video/tests/test_teaching_runtime.cjs`. 기대: OK; skip이 있다면 항목·이유를 기록한다.
- [x] **Step7: 최종 검증.** CLI verify를 실행하고 원본SVG/필기/회로표시/lesson/가독성/captions/chunk_sync 기술검사의 통과를 확인한다. 변경전66WAV/총프레임/segment·caption경계와 일치를 단언한다. 실제 청취가 불가능하면 audio unverified 때문에 전체verify 비통과임을 그대로 기록한다.
- [x] **Step8: 전달.** final.mp4를 절대경로로 인라인 표시하고12청크 검토표·최종해시·검증범위·paid_requests0을 제공한다. 실제 음성 검토 없는 publish/latest 갱신이나 성공 주장은 하지 않는다. 요청 시 소스/지침/테스트/새영상·자료만 `feat(ec2-video): enrich P10.72 circuit narration with ink`로 커밋하며 기존 무관한 HTML은 제외한다.

## 실행 중 확인한 조정
- 28개 표시의 glyph/seek/oracle 전체 검사364프레임은120초 제한을 초과한다. verify의 teaching browser만600초로 늘리며 검사 수·렌더·음성·기타 browser 제한은 유지한다. 외부 subprocess 경계 회귀 테스트를 추가한다.

## Self-review
- Spec의 굵기/색(Task1), 청크계약/시간/legacy(Task2), camera/seek/가독성/저작정책(Task1·3), 12청크 저작/WAV보존/검토본(Task4)을 모두 매핑했다.
- Review Focus 5항목은 해당 task에 검사와 기대값을 명시했다. 외부 함수는 기존 signature를 유지하고 새 resolve_annotation_windows만 Task2에서 정의했다.
- 필기밀도는 confirmed by default, 실행방식은 기존native 유지. 구현 전 사용자가 계획을 확인한다.

## 실행 결과
- 12발화 청크·28표시,4색·도형별4/6/8px(지원2..12px), source/wave/시간 보존.
- 최종239tests OK(skipped2), Node4pass,24회 정적 반복 비교0, 이번영상12기술·화면검증통과. 실제청취미검증검토본.
- 정적 SVG 캡처는2RAF 대기와 gate 전용 --disable-gpu를 적용한다. 영상 렌더 입력은 동일하고 캐시 지문은 새0차이 게이트·비트 동일 payload·PCM 검증으로 갱신했다. 커밋·푸시·게시하지 않았다.
