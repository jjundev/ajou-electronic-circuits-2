# EC2 Chunk Speech Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** P10.72의 지침 발화를 제거하고 실측 음성 청크 경계에 맞춘 자막·최종 영상을 만든다.

**Architecture:** 문제풀이 전용 TTS는 읽을 대본만 전송하고 각 자막 청크의 WAV를 생성한다. 청크 PCM을 기존 segment WAV로 연결해 필기 시스템을 유지하고, 상대 샘플 경계를 영상의 절대 caption_cues로 변환한다. 기존 청크 없는 자료와 새 청크 모드를 명시적으로 구분한다.

**Tech Stack:** Python 3, unittest, wave/PCM16, 기존 Vertex AI Express transport·cache·budget, gemini-2.5-flash-tts/Aoede, HyperFrames/GSAP, Chrome, libass 지원 FFmpeg.

**Spec:** `docs/superpowers/specs/2026-10-09-ec2-chunk-speech-sync-design.md` — 실행 전에 이 파일과 계획을 모두 읽는다.

## Global Constraints

- 출력: 1920×1080, 30fps, mono PCM16 24kHz, 한국어 Aoede, vertex-ai-express, gemini-2.5-flash-tts. 공급자 대체 없음.
- 새 모드 식별자: `caption_timing: "pcm-chunks-v1"`; TTS 정책: `spoken-text-only-v1`.
- 읽을 텍스트 외 direction·“원고:”·caption_text를 TTS 입력에 넣지 않는다. API key는 기존 환경 로더로만 전달하며 저장·로그 금지.
- 공용 `.agents/skills/ec2-review-video/`를 수정하지 않는다. 자동 전역 설치·새 유료 공급자·STT 도입 없음.
- 기존 PDF·glyph·shape·step ID·연필 기본 7.5 chars/sec 및 원본 자료 보존. 숫자·기호 자막과 두 줄/34자 규칙 유지.
- SRT 샘플→밀리초 오차 1ms 이하; 영상 전환은 30fps에서 1프레임 이내. 청크 내부 단어 정렬을 주장하지 않는다.
- 추가 청크 간 무음 없음. 명시 절단만 허용하며 raw WAV 보존. 필기 hold까지 자막을 늘리지 않는다.
- paid_requests·캐시·부분 실패·재개 계약 유지. 실제 청취 없는 complete/publish 승인 금지.
- 계획 작성 턴은 코드·영상·음성 변경이나 유료 요청을 하지 않는다. 실행 시 기본 작업은 현재 체크아웃에서 수행하며 격리 방식은 선택한 실행 방법과 관련 스킬을 따른다.
- Git 범위: 이번 기능과 새 P10.72 자료만. 기존 미추적 `나레이션·자막 비교.html`을 자동으로 추가하지 않는다. 아래 커밋 지점은 커밋 지시가 있을 때만 실행하고 푸시는 별도 지시를 따른다.

## Review Focus

1. 청크 없는 legacy 또는 새 모드의 일부 segment만 청크가 있는 입력: legacy 보존, 새 모드 누락 차단 — Task 1.
2. 429·중간 실패·캐시 파일 변조: 요청 사용량 보존, 성공 캐시 재사용, 변조 캐시 재생성 — Task 2.
3. 조용한 발음·긴 앞뒤 무음·잘못된 절단: 자동 절단 없음, 명시 샘플/해시 검증, 원본 보존 — Task 3.
4. 수식 표기 축약·필기 hold·프레임 패딩: 실제 청크 경계 불변, 무음 hold에 자막 없음 — Task 4.
5. 대본 외 발화·청크 연결의 끊김·청취 불가능: 실제 청취 항목 없이는 완료 불가 — Task 5/6.

---

## File Structure

아래 P는 `.agents/skills/ec2-solution-video`를 뜻한다. 테스트와 구현 경로는 모두 저장소 기준이다.

| 파일 | 책임 |
|---|---|
| Create `P/scripts/solution_video/speech_chunks.py` | 청크 계약, 명시 절단 검증, segment PCM 연결, 상대 경계 |
| Create `P/scripts/solution_video/speech_tts.py` | 대본 전용 payload, 요청·영수증·캐시·재시도·budget |
| Modify `P/scripts/solution_video/review_adapter.py:6-42` | 기존 transport/config 재사용 및 legacy/청크 생성 연결 |
| Modify `P/scripts/solution_video/manifest.py:35-49` | 유료 요청 전 청크 대응 검사 |
| Modify `P/scripts/solution_video/subtitles.py:1-64,129-138` | 청크 notation 경고와 실측 cue SRT 생성 |
| Modify `P/scripts/solution_video/reveal.py:6-71` | segment 시작점에 청크 상대 경계 더하기 |
| Modify `P/scripts/solution_video/state.py:7-29` | 새 소스·모듈·WAV·정책의 재개 지문 |
| Modify `P/scripts/video.py:75-80,116-152` | 청크 영수증 단계 출력, retime 검증 |
| Modify `P/scripts/solution_video/verify.py:118-153` | 구조 동기화 게이트와 실제 청취 항목 |
| Create `P/tests/test_speech_chunks.py`, `test_speech_tts.py`, `test_chunk_acceptance.py` | 계약·요청·실측 타이밍·오류 회귀 |
| Modify `P/tests/test_voice.py`, `test_manifest.py`, `test_reveal.py`, `test_subtitles.py`, `test_state.py`, `test_cli.py`, `test_verify.py` | 기존 인터페이스와 호환/재개 검증 |
| Modify `P/SKILL.md`, `P/references/narration-and-timing.md`, `P/references/verification.md` | 저작·생성·검토·완료 기준 |
| Create 새 P10.72 sibling run | 원본 보존, 청크 대본·실제 음성·새 영상·검토 증거 |

테스트는 기존 `fixtures.py`의 Sandbox/make_audio를 사용한다. 별도 pytest 체계를 도입하지 않는다. 아래 Run 명령은 저장소 루트에서 실행한다.

### Task 1: 청크 대본 계약과 검증

**Files:** Create `P/scripts/solution_video/speech_chunks.py`, `P/tests/test_speech_chunks.py`; Modify `P/scripts/solution_video/manifest.py:35-49`, `P/scripts/solution_video/subtitles.py:1-64`, `P/tests/test_manifest.py`.

**Interfaces:**
- Consumes: 기존 `caption_text(segment)`, `split_caption(text)`, `validate_manifest(...)`.
- Produces: `validate_speech_chunks(segments: list[dict], *, required: bool) -> None`, `speech_items(segments: list[dict]) -> list[dict]`.
- speech_items row: id=`segment_id__chunk_id`, segment_id, chunk_id, text. Legacy row는 id/text만 유지한다. 검증 오류는 InputError이고 segment/chunk ID를 포함한다.

- [x] **Step 1: 실패 테스트 작성.** `test_requires_every_segment_in_chunk_mode`는 required=True에서 청크 없는 segment에 InputError를 기대한다. `test_legacy_unchanged`는 required=False/청크 없음에서 기존 id/text를 기대한다. `test_parent_reconstruction_and_atomic_caption`은 부모와 청크 text/caption 불일치·중복 ID·빈 값·caption 두 문장에 InputError를 기대하고 `(I₀ + ΔI)/2입니다.`는 허용한다. `test_caption_warnings_include_chunk_id`는 `이 R_L을 봅니다.` 경고에 부모와 chunk_id가 포함됨을 확인한다.
- [x] **Step 2: 실패 확인.** Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_speech_chunks.py -v`. Expected: 새 함수 import/동작 실패.
- [x] **Step 3: 계약 구현.** manifest의 pcm-chunks-v1 모드에 required=True를 전달한다. 모든 ID는 기존 안전한 ASCII 규칙으로 검사하고 합성 ID 전체 중복도 거부한다. 청크 본문에는 자동 수학 치환을 하지 않는다. 부모 text/caption은 공백 정규화한 join과 같아야 한다. 청크 없는 legacy는 기존 검사를 유지한다.
- [x] **Step 4: 통과 확인.** Step 2 명령과 `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_manifest.py -v`. Expected: OK.
- [x] **Step 5: 커밋 지점.** 위 Files만 stage하고 `feat(ec2-video): validate paired speech chunks`로 커밋한다. 커밋 지시가 없으면 체크포인트만 기록한다.

### Task 2: 지침이 없는 TTS 요청과 청크 캐시

**Files:** Create `P/scripts/solution_video/speech_tts.py`, `P/tests/test_speech_tts.py`; Modify `P/scripts/solution_video/review_adapter.py:6-42`, `P/tests/test_voice.py`.

**Interfaces:**
- Consumes: Task 1 `speech_items`, 기존 review_adapter `_modules()`가 반환하는 Vertex transport/load_key/VertexError 및 budget/cache 모듈.
- Produces: `make_speech_payload(text: str, config: dict) -> dict`; `synthesize_speech(items: list[dict], run: Path, config: dict, budget: object, transport: Callable, *, sleep: Callable = time.sleep) -> list[dict]`.
- 반환 영수증: id/path/samples/rate/key/sha256/output_sha256/usage/payload_hash/policy. 청크 모드 저장은 `source/chunk-audio.json`; generate_voice의 기존 호출 시그니처를 유지한다. segment 연결은 Task 3까지 별도다.

- [x] **Step 1: 실패 테스트 작성.** `test_payload_contains_only_spoken_text`에서 parts[0].text가 발음 사전 적용 후 읽을 대본과 정확히 같고 direction/“원고:”/caption_text가 없음, responseModalities=AUDIO, languageCode=ko-KR, voiceName=Aoede를 assert한다. `test_policy_invalidates_old_cache`, `test_caption_change_reuses_voice`, `test_429_retry_and_partial_resume`, `test_corrupt_cached_pcm_regenerates`, `test_error_does_not_expose_secret`를 만든다. 가짜 transport PCM을 사용하고 ledger에 실패 요청까지 남는지 확인한다.
- [x] **Step 2: 실패 확인.** Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_speech_tts.py -v`. Expected: 새 모듈/정책 계약 실패.
- [x] **Step 3: 전용 합성 구현.** 원고 텍스트만 payload에 넣고 발음 사전은 기존 순서로 적용한다. cache key는 정책·실제 payload·모델·원 대본/발음 설정으로 결정하고 caption을 제외한다. 기존 예산 reserve/settle, 최대 4회 재시도, 429 후 직렬 처리, usage·원자적 WAV/영수증 기록과 sanitized error 계약을 보존한다. 공용 Vertex 코드의 `_decode`, `_pricing` 재사용은 전용 모듈 안에 한정하고 해당 반환값을 테스트한다. 공용 make_payload/synthesize를 수정하거나 monkey-patch하지 않는다. 이 task에서는 legacy generate_voice를 새 합성기로 연결해 기존 source/audio.json과 반환 계약을 유지한다. 청크 합성기는 직접 테스트하고, 청크 generate_voice의 segment 연결은 Task 3에서 완성한다.
- [x] **Step 4: 통과 확인.** Step 2 명령과 `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_voice.py -v`. Expected: OK, 실제 유료 호출 0.
- [x] **Step 5: 커밋 지점.** 위 Files만 stage하고 `fix(ec2-video): send only spoken text to TTS`로 커밋한다.

### Task 3: 실측 PCM 연결과 재개 지문

**Files:** Modify `P/scripts/solution_video/speech_chunks.py`, `P/scripts/solution_video/review_adapter.py`, `P/scripts/solution_video/state.py:7-29`, `P/scripts/video.py:116-152`, `P/tests/test_speech_chunks.py`, `P/tests/test_voice.py`, `P/tests/test_state.py`, `P/tests/test_cli.py`.

**Interfaces:**
- Consumes: Task 1 speech_items, Task 2 synthesize_speech의 영수증.
- Produces: `join_segment_audio(segments: list[dict], chunk_audio: list[dict], run: Path, trims: dict | None = None) -> list[dict]`; `validate_chunk_audio(segments: list[dict], voices: list[dict], run: Path) -> None`.
- 반환은 기존 voices 형태이며 청크 모드에는 spec의 상대 chunks 필드를 추가한다. 합성/연결 성공 후에만 source/audio.json을 원자적으로 갱신한다. 검증 함수는 원본과 연결본 PCM/해시/범위/순서/대본 대응을 검사한다.

- [x] **Step 1: 실패 테스트 작성.** 두 PCM 청크 2400/7200 samples를 연결한 `test_join_measured_pcm`에서 결과 samples=9600, 상대 경계 [(0,2400),(2400,9600)], PCM 바이트가 원본 순서의 연결과 같음을 assert한다. `test_no_automatic_trim_of_quiet_speech`는 작은 진폭 PCM이 그대로 남는지 확인한다. `test_explicit_trim_preserves_raw`는 100..2300 절단의 길이=2200, raw hash 불변을 확인한다. `test_reject_bad_trim_and_provenance`는 음수·범위 밖·bool·중복 row·다른 raw hash·변조/누락 WAV를 거부한다. state/CLI 테스트는 새 모듈·청크 WAV·절단 변경이 retime/후속 단계를 무효화하고 paid_requests를 유지하는지 확인한다.
- [x] **Step 2: 실패 확인.** Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_speech_chunks.py -v`. Expected: PCM 연결 인터페이스 실패.
- [x] **Step 3: 연결·검증 구현.** raw bytes를 순서대로 연결해 mono PCM16/24kHz segment WAV를 만든다. 기본은 전체 길이, 명시 절단만 적용한다. 추가 무음을 넣지 않는다. generate_voice가 chunk receipts→join→audio.json 순으로 처리한다. retime도 validate_chunk_audio를 실행한다. state의 voice에는 speech_tts/speech_chunks, timing에는 speech_chunks/chunk-audio.json/chunk-trims.json/청크·segment WAV를 포함하고 finish_stage의 출력에 현재 영수증을 포함한다. 실패 시 성공 청크를 삭제하지 않는다.
- [x] **Step 4: 통과 확인.** Step 2 명령과 test_voice.py/test_state.py/test_cli.py를 각각 `unittest discover -p <파일명> -v`로 실행한다. Expected: 모두 OK.
- [x] **Step 5: 커밋 지점.** 위 Files만 stage하고 `feat(ec2-video): join measured chunk PCM with provenance`로 커밋한다.

### Task 4: 실측 청크 경계로 타임라인과 SRT 생성

**Files:** Modify `P/scripts/solution_video/reveal.py:6-71`, `P/scripts/solution_video/subtitles.py:129-138`, `P/tests/test_reveal.py`, `P/tests/test_subtitles.py`; Create `P/tests/test_chunk_acceptance.py`.

**Interfaces:**
- Consumes: Task 3 voices의 상대 chunks와 manifest chunks.
- Produces: 기존 `build_timeline(...) -> dict`에 caption_timing/caption_cues를 추가한다. 기존 `write_srt(timeline: dict, dest: Path) -> Path`는 pcm-chunks-v1에서 caption_cues를 사용한다. 레거시 반환·생성 방식은 유지한다.

- [x] **Step 1: 실패 테스트 작성.** `test_srt_uses_pcm_not_character_weights`의 segment start_sample=24000과 상대 [(0,2400),(2400,9600)]에서 두 cue 시간이 1.000..1.100, 1.100..1.400임을 assert한다. 같은 음성에서 caption 길이를 변경해도 시간은 같아야 한다. `test_frame_padding_and_hold_have_no_caption`은 1.400 뒤 segment hold에 cue 없음, 다음 segment의 frame-aligned start가 반영됨을 확인한다. `test_missing_or_reordered_chunk_boundaries_fail`과 `test_legacy_srt_unchanged`를 추가한다. acceptance는 fake transport→join→build_teaching_timeline→SRT까지 실제 연결 경계를 검증한다.
- [x] **Step 2: 실패 확인.** Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_chunk_acceptance.py -v`. Expected: caption_cues/실측 시간 불일치.
- [x] **Step 3: 타임라인/SRT 구현.** 각 상대 start/end에 해당 segment start_sample을 더한다. 전체 cue 순서/범위/부모 voice_samples/manifest 대응을 확인하며 청크 모드에서 누락된 경계는 InputError로 차단한다. cue 하나를 wrap_caption으로 최대 두 줄로 출력한다. 청크 모드에서는 글자 수 비례 분할을 호출하지 않는다. segment의 필기/카메라 최소 프레임과 hold는 유지한다.
- [x] **Step 4: 통과 확인.** Step 2 명령과 test_reveal.py/test_subtitles.py/test_teaching.py를 각각 실행한다. Expected: 모두 OK, legacy 시간 회귀 없음.
- [x] **Step 5: 커밋 지점.** 위 Files만 stage하고 `fix(ec2-video): synchronize captions to measured chunk audio`로 커밋한다.

### Task 5: 동기화·실제 청취 게이트와 문서

**Files:** Modify `P/scripts/solution_video/speech_chunks.py`, `P/scripts/solution_video/verify.py:118-153`, `P/tests/test_verify.py`, `P/tests/test_chunk_acceptance.py`, `P/SKILL.md`, `P/references/narration-and-timing.md`, `P/references/verification.md`.

**Interfaces:**
- Consumes: Task 3 validate_chunk_audio, Task 4 timeline.caption_cues/write_srt.
- Produces: `verify_chunk_sync(run: Path) -> dict`를 speech_chunks.py에 추가한다. status, input_hash, evidence_hashes, issues를 반환하고 `verification/chunk-sync.json`에 저장한다. verify_run은 chunk mode에 chunk_sync check를 추가한다. audio-review의 chunk_checks는 spec의 전 청크 목록/boolean/notes를 검증한다.

- [x] **Step 1: 실패 테스트 작성.** `test_modified_srt_or_chunk_pcm_fails_sync`는 시간 또는 WAV 변조 시 passed가 아님을 assert한다. `test_no_listening_or_incomplete_chunk_review_blocks_complete`는 mode=not-listened, 누락·중복 청크, false transcript_match/no_instruction_speech/natural_join/sync_passed, 오래된 fingerprint에서 audio_meaning 불통과를 확인한다. `test_synthetic_sync_does_not_approve_live_audio`는 합성 PCM 구조가 맞아도 live_audio=unverified임을 확인한다. legacy audio-review의 기존 계약은 유지한다.
- [x] **Step 2: 실패 확인.** Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_verify.py -v`. Expected: 새 게이트/검토 필드 검증 실패.
- [x] **Step 3: 게이트와 문서 구현.** source/audio.json·chunk-audio·raw/segment WAV·timeline·SRT를 검증하고 예상 SRT와 실제 SRT를 비교한다. 소스·미디어 구조 검증과 실제 청취 승인을 별도로 기록한다. docs에 청크 저작·지침 미전송·47 cue 후보·청취 미검증 처리·1ms/1프레임 허용치를 명시한다. 기존 지문 계산은 현재 증거를 기준으로 유지한다.
- [x] **Step 4: 통과 확인.** Step 2 명령 후 전체 suite를 실행한다.

```bash
PYTHONPATH=.agents/skills/ec2-solution-video/scripts EC2_FFMPEG=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v > /tmp/ec2-chunk-sync-tests.log 2>&1
```

Expected: `OK`와 설명 가능한 기존 skip만 있음. 새 청크 테스트는 skip하지 않는다. `git diff --check`도 exit 0이어야 한다.

- [x] **Step 5: 커밋 지점.** 위 Files만 stage하고 `test(ec2-video): gate chunk sync and actual speech review`로 커밋한다.

### Task 6: P10.72 재생성 및 최종 청취/싱크 확인

**Files:** 기존 `문제풀이영상/1007/1007_제작자료/실행/20261008-104109-55e6b8b7`은 보존한다. Create 새 sibling batch/run의 source/assets/composition/renders/verification 및 검증 후 자연스러운 제목의 최종 MP4. 실제 새 경로는 prepare 반환값을 기록한다.

**Interfaces:**
- Consumes: Task 1~5 CLI check/tts/retime/assemble/render/captions/verify/publish-set, 기존 동결 source/원본 PageMap/19 segment/47 SRT cue 후보.
- Produces: 새 manifest/chunk WAV/audio/timeline/SRT/final.mp4, 전체 청크 비교표, 현재 해시의 검토 및 자동 검증 보고서. 실제 청취 없으면 검토용 영상으로 전달하고 publish-set/latest를 갱신하지 않는다.

- [x] **Step 1: 새 실행 준비.** `python3 .agents/skills/ec2-solution-video/scripts/video.py prepare 1007 --repo "$PWD" --problems P10.72`로 새 batch/run을 만들고 그 경로를 기록한다. 기존 동결 PDF/MD hashes를 비교하고 기존 PageMap·writing·focus·annotations·lesson을 이식하되 새 run 내부 경로로 다시 연결한다. 원본 source가 달라졌으면 조용히 사용하지 말고 차이를 검토한다.
- [x] **Step 2: 대본·청크 저작.** 기존 47 cue에 발화 청크를 명시적으로 대응시키고 부모 대본/캡션을 재구성한다. 수식 의미는 기존 PDF/MD와 대조한다. `write_part_0_0`의 읽을 내용은 “먼저 전류 거울과 출력 노드의 관계를 정리합니다.”뿐이다. 지침 문구를 발화 text에 넣지 않는다. 내용 지문이 바뀌므로 coverage/circuit-review를 실제 대조 후 새 지문으로 갱신한다.
- [x] **Step 3: 유료 호출 전 게이트.** 새 RUN에서 extract 후 check를 실행한다. Expected: passed/paid_requests=0, 모든 segment 청크 있음, glyph·shape coverage/원본 게이트 통과. check 경고를 원문과 대조한다.
- [x] **Step 4: 실제 청크 음성 생성.** 새 RUN에서 `tts --run RUN --env-file ENV`를 실행한다. ENV는 기존 허가된 환경 파일의 존재/권한만 확인하고 내용은 출력하지 않는다. paid_requests/usage 기록을 확인한다. 47청크라면 최초 정상 요청 수는 47이며 재시도는 추가될 수 있다. 클립 형식/해시/대본-only 정책을 확인한다.
- [ ] **Step 5: 음성 청크 검토.** 전체 저장 WAV를 청취해 지침·추가 발화·누락·발음과 연결부를 확인한다. 긴 경계 무음에만 검토한 chunk-trims를 기록하고 tts를 다시 실행해 캐시 원본으로 연결본을 갱신한 뒤 retime을 실행한다. 동일 대본의 원본 청크는 새 유료 요청 없이 재사용한다. 잘못 읽은 청크는 대본을 명확히 수정하고 변경 청크만 새 캐시 키로 생성한다. 같은 잘못된 캐시를 반복 사용하지 않는다. 청취 수단이 없으면 이 step은 미완료로 기록한다.
- [x] **Step 6: 전체 영상 재생성.** 현재 GSAP/HyperFrames/Chrome 경로를 확인하고 assemble→render→captions를 실행한다. 이전 master 재사용은 금지한다. 음성 길이가 바뀌었으므로 필기·카메라·주석 타임라인을 모두 재생성한다. 이전 pacing/visual/audio 리뷰를 그대로 승인하지 않는다.
- [ ] **Step 7: 최종 검증.** 전체 청크의 영상 시각/대본/캡션/음성 비교표를 새 제작자료에 작성한다. 최종 MP4에서 문제였던 write_part_0_0과 전 청크 전환을 재생 확인한다. 실제 리뷰어가 검토한 뒤 현재 fingerprint와 모든 chunk_checks로 audio/visual/pacing review를 기록하고 verify를 실행한다. Expected: 구조 check 통과, 실제 검토가 끝났을 때만 complete=true/live_audio=verified. AAC/30fps 출력의 경계도 1프레임 이내인지 확인한다.
- [x] **Step 8: 전달 및 커밋 지점.** 검증 완료라면 publish-set을 사용해 자연스러운 제목의 최종 MP4와 해시를 갱신한다. 청취 미검증이면 검토용 final.mp4와 한계를 전달한다. 커밋 지시가 있다면 새 영상/제작자료와 이번 코드·docs만 stage하고 `fix(ec2-video): regenerate P10.72 with synchronized speech chunks`로 커밋한다. 기존 비교 HTML·다른 변경은 stage하지 않는다.

## Self-Review

- 설계의 지침 분리/모드/저작 대응은 Task 1/2, PCM/절단/캐시는 Task 2/3, 샘플 타이밍은 Task 4, 실제 청취/재생 검증은 Task 5/6에 대응한다.
- 반환 영수증→상대 chunks→절대 caption_cues의 이름/단위를 통일했다. 모든 시간은 24kHz 정수 sample이며 SRT 출력에서만 밀리초로 바꾼다.
- Review Focus 5항목마다 담당 task의 실패 테스트 또는 실제 리뷰 절차를 지정했다. 코드 검사로 TTS의 실제 의미를 승인하는 빈틈을 남기지 않았다.
- 미정 인터페이스·새 공급자·공용 스킬 변경·강제 자동 절단은 없다. 청취 불가능 시 전달 상태와 게시 금지를 명시했다.

## Execution Handoff

추천은 Native: 여섯 작업이 같은 청크/영수증/타임라인 계약에 의존하므로 한 구현자가 순서대로 연결하고 마지막에 독립 리뷰를 받는 방식이 적합하다. 대안은 task마다 구현자·리뷰어를 분리하는 Subagent-driven이다. 실행 방식과 계획 검토를 받은 다음 구현을 시작한다. 리뷰 모델은 명시적으로 요청받지 않으면 현재 모델 설정을 따른다.

## 현재 실행 결과

코드 작업 1–5와 P10.72 검토용 영상 재생성/자동 검증을 마쳤다. 전체 테스트 211개 통과, 기존 수용 테스트 2개 skip. 47개 실제 음성 청크의 PCM/SRT 경계 검증과 최종 미디어/화면 검증은 통과했다. 실제 음성 청취는 수행하지 못했으므로 Task 6의 Step 5 및 Step 7의 청취 부분은 미완료다. complete=false/live_audio=unverified로 보존하고 게시/latest는 갱신하지 않았다. 결과는 `문제풀이영상/1007/1007_제작자료/실행/20261009-193836-6994a849/delivery.json`에 기록했다. 커밋·푸시는 실행하지 않았다.
