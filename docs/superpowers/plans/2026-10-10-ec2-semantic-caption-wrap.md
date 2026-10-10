# 의미 단위 자막 줄바꿈 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 수식 내부를 보호하고 설명/수식 경계를 우선하는 줄바꿈을 적용해 현재 영상의 자막을 다시 생성한다.

**Architecture:** 기존 자막 모듈과 공개 인터페이스를 유지하고 보호 구간 및 후보 우선순위를 추가한다. SRT 내용·시간의 결정적 검증을 기존 자막 화면 검증에 결합한다. 기존 음성과 master를 재사용하는 별도 실행 사본에서 자막을 다시 입힌다.

**Tech Stack:** Python unittest, 정규식과 괄호 스택, FFmpeg/libass, Pretendard Bold, 기존 HyperFrames 검증 도구.

**Spec:** `docs/superpowers/specs/2026-10-10-ec2-semantic-caption-wrap-design.md`

## Global Constraints
- 최대 두 줄, 줄당 34자, 현재 글자 크기를 유지한다.
- 중첩 괄호 안, 식별자·첨자, 소수, 분수 내부는 나누지 않는다.
- 후보 우선순위는 설명/수식 경계, 일반 문장 공백, 수식 밖 연산 경계다.
- 긴 수식의 연산자는 다음 항과 같은 줄에 둔다.
- 자동 축약·글자 크기 축소·cue 분할은 하지 않는다.
- PCM 청크 시작/종료 시간, 음성, 회로 필기, 영상 길이를 유지한다. 유료 TTS 요청은 0이다.
- ec2-solution-video 외 다른 영상 스킬은 수정하지 않는다.
- 기존 미커밋 회로 필기 작업과 별도 나레이션·자막 비교 HTML을 보존한다.
- 게시, latest 변경, 커밋, 푸시는 별도 요청 전 하지 않는다. 각 Task의 commit은 승인 후 가능한 검토 경계만 기록한다.
- Native 실행: 실행 시 executing-plans를 사용하고 마지막에 스킬이 요구하는 독립 리뷰를 수행한다.

## Review Focus
1. 음수와 이항 연산이 혼재한 식: 단항 부호와 피연산자가 갈라지지 않아야 한다. Task 1의 test_signed_fraction_is_protected.
2. 수식처럼 보이는 문항 ID·식별자 점과 인용문: 기존 문장/cue 해석을 유지해야 한다. Task 1의 test_caption_boundary_compatibility.
3. 공백이 있는 분수와 중첩 괄호: 내부 공백도 줄바꿈 후보가 아니어야 한다. Task 1의 test_spaced_fraction_and_nested_group.
4. 한글/라틴 글꼴 폭과 libass 자체 줄바꿈: SRT와 실제 표시 줄 수가 같아야 한다. Task 2의 test_libass_respects_explicit_lines.
5. 자막만 변조하거나 시간이 바뀐 실행: 화면에 자막이 있다는 이유로 통과하면 안 된다. Task 2의 test_caption_srt_tampering_is_rejected.

## File Structure
- Modify `.agents/skills/ec2-solution-video/scripts/solution_video/subtitles.py`: 보호 구간, 후보 우선순위, 기대 SRT 검증과 libass 스타일.
- Modify `.agents/skills/ec2-solution-video/scripts/solution_video/verify.py`: 기존 captions gate에 SRT 내용/시간 대조 추가.
- Modify `.agents/skills/ec2-solution-video/tests/test_subtitles.py`: 줄바꿈 및 PCM 보존 회귀 테스트.
- Modify `.agents/skills/ec2-solution-video/tests/test_verify.py`: SRT 변조 검증.
- Create `.agents/skills/ec2-solution-video/tests/test_subtitle_layout_media.py`: 짧은 로컬 합성 영상에서 libass 출력 검사.
- Modify `.agents/skills/ec2-solution-video/SKILL.md`, `references/narration-and-timing.md`, `references/verification.md`: 동일 정책과 검증 절차.
- Create 별도 실행 `문제풀이영상/1007/1007_제작자료/실행/<실행시각>-semantic-caption-wrap/videos/problem-d885c8738da3`: SRT, final, 검증 증거. 기존 실행은 수정하지 않는다.

---

### Task 1: 수식 보호와 줄바꿈 후보 우선순위

**Files:** subtitles.py, tests/test_subtitles.py, SKILL.md, references/narration-and-timing.md.

**Interfaces:**
- Consumes: `caption_units(text: str) -> list[str]`, 기존 InputError.
- Produces: 기존 `wrap_caption(text: str, max_chars: int = 34, max_lines: int = 2) -> str`, `chunk_caption(text: str) -> str` 유지.
- Private helpers: `_protected_ranges(text: str) -> list[tuple[int, int]]` (끝 exclusive), `_wrap_candidates(text: str, max_chars: int) -> list[tuple[int, int, int, str, str]]` (priority, balance, split_index, left, right).

- [x] **Step 1: 실패할 회귀 테스트 작성**

`test_formula_boundary_precedes_balance`:
```python
self.assertEqual(
    wrap_caption('저항으로 흐르는 전류는 (I₀ + ΔI) − (I₀ − ΔI)입니다.'),
    '저항으로 흐르는 전류는\n(I₀ + ΔI) − (I₀ − ΔI)입니다.')
```
`test_spaced_fraction_and_nested_group`: `ΔI / 2`, `(R_L × ((I₀ + ΔI)/2 − (I₀ − ΔI)))` 보호 구간 내부에 선택된 split_index가 없음을 검사한다.
`test_signed_fraction_is_protected`: `−ΔI/2`와 `-ΔI / 2` 내부 분할 금지. 단항 부호 앞이 허용 후보여도 부호 뒤는 금지한다.
`test_long_formula_operator_stays_with_rhs`: 기존 test_atomic_formula_caption의 긴 식은 두 줄을 유지하되 연산자가 다음 항과 같은 줄에 있는지 검사한다. 공백 없는 입력은 개행을 제거했을 때 원문과 같아야 한다.
`test_unsplittable_group_reports_layout_error`: 34자를 넘는 보호 괄호/단일 토큰은 InputError.
`test_caption_boundary_compatibility`: `E10.13`, `0.5`, `1,000`, 인용문, 쉼표 cue, 일반 조사 `이`는 기존 결과를 유지한다. 짧은 `전류는 2ΔI입니다.`는 한 줄이다.

- [x] **Step 2: RED 확인**
Run: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_subtitles.py -v`
Expected: 대표 자막의 기대 줄바꿈에서 FAIL. 기존 성공 테스트 실패 원인도 기록한다.

- [x] **Step 3: 최소 구현**
보호 구간은 중첩 괄호/인용 스택과 수식 토큰을 사용한다. 수식 토큰에는 라틴 식별자·밑줄·숫자·유니코드 첨자·ΔλμΩ, 소수와 `/`로 연결된 분자/분모 및 단항 부호가 포함된다. 분수 주변 공백을 포함해 보호한다. 문장 온점은 수식 토큰에 포함하지 않는다.
수식 구간은 수식 atom/괄호 그룹을 연산자로 연결해 찾는다. 한글 설명을 넘어서 확장하지 않고 바로 붙은 조사/서술어는 마지막 항과 함께 둔다.
후보는 보호 구간 내부를 제외한다. priority 0=설명과 수식 경계, 1=수식 밖 일반 공백, 2=괄호 밖 이항 연산자 바로 앞이다. score `(priority, abs(len(left)-len(right)), split_index)`의 최솟값을 선택한다. 여닫는 괄호와 문장부호 고립을 거부하고 길이 제한을 유지한다. 모든 후보가 불가능하면 기존 InputError를 유지한다.
수식 아닌 일반 문장을 완전한 문법 분석 대상으로 확장하지 않는다. 기존 테스트가 허용한 operator fallback 기대는 새 연산자 위치 정책에 맞춰 명시적으로 갱신한다.

- [x] **Step 4: GREEN 및 청크 회귀 확인**
Run: 위 test_subtitles.py 명령 및 같은 discover의 `-p test_speech_chunks.py`.
Expected: 모두 OK. 기존 PCM cue 경계가 동일하다.

- [x] **Step 5: 저작 지침 동기화**
SKILL.md와 narration-and-timing.md의 ‘공백 우선’ 문구를 새 우선순위로 바꾼다. 수식 예시, 오류 처리, 자동 cue 분할 금지와 타이밍 보존을 명시한다.

- [x] **Step 6: 검토 가능한 변경 경계 기록**
Task 1 파일과 테스트 결과를 실행 ledger에 기록한다. 커밋 요청 전 staging/commit하지 않는다. 승인 시 메시지: `fix(ec2-video): wrap captions at semantic formula boundaries`.

### Task 2: 기대 SRT 및 실제 libass 줄바꿈 검증

**Files:** subtitles.py, verify.py, tests/test_subtitles.py, tests/test_verify.py, 새 tests/test_subtitle_layout_media.py, references/verification.md.

**Interfaces:**
- Consumes: Task 1 `wrap_caption`, 기존 `write_srt(timeline, dest)`와 `burn_subtitles(master, srt, dest, font)`.
- Produces: `caption_srt_matches(timeline: dict, srt: Path) -> bool`. 임시 디렉터리에 write_srt로 기대 SRT를 생성하고 UTF-8 내용 전체를 대조한다. 입력/원본 SRT를 수정하지 않는다. 파싱 실패는 기존 verify gate의 실패 처리로 전달한다.

- [x] **Step 1: 실패할 검증 테스트 작성**
`test_caption_srt_tampering_is_rejected`: 올바른 SRT는 True; 글자 교체, 괄호 내부 개행, 1ms 시작 시각 변경, cue 삭제는 각각 False.
`test_wrap_preserves_pcm_cue_bounds`: 동일 chunk timeline에서 줄바꿈 전후 모든 번호/start/end가 동일하며 줄 공백 연결 결과가 caption_text와 같다.
`test_libass_respects_explicit_lines`: FFmpeg로 1920×1080 검은 1초 master 생성 후 한 줄/대표 두 줄 자막을 각각 입힌다. 중간 프레임의 하단 흰 텍스트 픽셀을 수평 투영해 한 줄=1개, 두 줄=2개 y대역인지 검사한다. 색상 경계 픽셀은 white RGB 각 채널 >=230, 각 행의 white 픽셀 >=3으로 정하고 2px 이하 간격을 병합한다. 두 줄의 x범위가 프레임 안에 있으며 텍스트 bbox y가 900..1080에 있는지도 검사한다.

- [x] **Step 2: RED 확인**
Run: `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_subtitles.py -v`
Expected: 새 helper 미구현으로 FAIL. libass 테스트의 현재 출력도 기록한다.

- [x] **Step 3: 검증과 renderer 제어 구현**
caption_srt_matches를 구현하고 기존 verify.captions의 화면 비교 전에 호출한다. 새 자막 gate로 오디오 검토 상태를 대체하지 않는다. burn_subtitles의 스타일에 `WrapStyle=2`를 명시해 지정한 줄바꿈만 사용한다. 글꼴/크기/여백/박스/음성 copy 설정은 그대로 둔다.

- [x] **Step 4: GREEN 확인**
Run: 위 subtitles 테스트, discover `-p test_verify.py`, `PATH=/opt/homebrew/opt/ffmpeg-full/bin:$PATH PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_subtitle_layout_media.py -v`.
Expected: 모두 OK. libass 미설치 시 통과로 보고하지 않고 실제 ffmpeg-full을 사용한다.

- [x] **Step 5: 검증 문서 동기화**
references/verification.md에 SRT 전체 일치, 두 줄 libass 출력, cue 시간 불변, unverified 음성 검토 유지 원칙을 적는다.

- [x] **Step 6: 검토 경계 기록**
Task 2 파일과 결과를 ledger에 기록한다. 승인 시 메시지: `fix(ec2-video): verify caption layout and cue timestamps`.

### Task 3: 현재 영상의 자막 재생성 및 보존 증명

**Files:** 새 실행 사본의 renders/captions.srt, renders/final.mp4, verification/caption-wrap-before-after.json, verification/자막 줄바꿈 검토.md, verification/report.json.

**Interfaces:**
- Consumes: Task 1/2 구현; 원본 실행 `문제풀이영상/1007/1007_제작자료/실행/20261010-112616-circuit-ink/videos/problem-d885c8738da3`.
- Produces: 독립 실행 사본의 새 SRT/final 및 SHA256 보존 비교표. 원본 실행과 기존 최종 결과는 유지한다.

- [x] **Step 1: 원본 증거 저장**
66개 WAV, narration.wav, master.mp4, manifest.json, source/timeline.json, annotations.json 및 기존 final의 SHA256과 모든 cue 번호/시간을 JSON으로 기록한다. 기존 최종 7220프레임과 실제 음성 unverified를 기록한다.

- [x] **Step 2: 사본 생성과 현재 입력 검증**
새 실행 디렉터리에 원본을 복사한다. 절대 경로 참조는 사본에 대응하는 로컬 파일로만 재지정하고 실제 내용 해시를 비교한다. 새 validator로 모든 청크를 검사한다. 길이 실패가 있으면 청크 ID와 텍스트를 제시하고, 음성이나 시간을 변경하지 않는 표현만 저작하여 부모 caption_text/timeline의 동일성 계약을 유지한다. 수식 자체는 바꾸지 않는다.
state.py의 script 단계에 subtitles.py가 포함되므로 변경 후 보수적으로 script부터 무효화되는 것은 정상이다. WAV cache key와 파일 내용 증거 없이 fingerprint를 갱신하지 않는다. 저장 PCM을 재사용하는 기존 check/retime/assemble로 내용·타이밍·composition을 검증하고, 기존 master를 재사용할 경우 실제 composition/parts/media 내용이 동일하다는 증거와 출력 해시를 검증한 뒤 해당 receipt를 갱신한다. 불일치하면 기존 render 절차로 렌더링한다. 유료 tts는 호출하지 않는다.

- [x] **Step 3: SRT와 final 재생성**
Run: `python3 .agents/skills/ec2-solution-video/scripts/video.py captions --run "$EC2_WRAP_RUN"`
EC2_WRAP_RUN은 Step 2에서 검증한 절대 사본 경로다.
Expected: status passed, paid_requests 0. master 보존, 새 final/SRT 생성.

- [x] **Step 4: 보존 비교와 실제 화면 검토**
새/이전 SRT의 cue 번호와 시간, 공백 연결 문장을 비교한다. WAV 66개/narration/master/회로 필기 SHA256이 일치하고 7220프레임인지 확인한다. 원본 final SHA256이 유지되는지 확인한다.
각 변경 cue의 중간 시각에서 final 프레임을 추출해 줄바꿈·수식·폰트·하단 영역을 검토한다. 대표 자막은 설계 예시와 같아야 한다. 변경 없음 cue도 한 줄/두 줄 각 1개를 표본 확인한다. 이전/새 자막과 시각/이미지 링크를 자막 줄바꿈 검토.md에 기록한다.

- [x] **Step 5: 전체 회귀와 현재 영상 검증**
Run: `PATH=/opt/homebrew/opt/ffmpeg-full/bin:$PATH PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v`
Run: `git diff --check`
Run: `python3 .agents/skills/ec2-solution-video/scripts/video.py verify --run "$EC2_WRAP_RUN" --hyperframes-entry /Users/hyunjun_macbook_pro/.npm/_npx/702923228c2ce1e6/node_modules/hyperframes/dist/cli.js`
실행 전 HyperFrames entry가 존재하는지 확인한다. 없으면 현재 설치 경로를 읽기 도구로 찾고 ledger에 기록한다.
Expected: unittest OK(선택 실행 테스트의 skip은 별도 기재), diff check 성공, captions와 모든 기술 gate passed. audio_meaning은 기존 unverified를 유지하며 complete=true로 보고하지 않는다.

- [x] **Step 6: 독립 리뷰와 결과 제시**
Native 실행 스킬의 최종 리뷰어에게 차이·테스트 증거·보존 비교·자막 표본을 전달한다. 지적이 있으면 수정하고 재검증한다. 새 영상과 비교 문서를 절대 경로로 제시하고 음성 청취 미검증과 미커밋 상태를 명시한다. publish/latest는 변경하지 않는다.

## Self-review
- 설계 범위: 후보 우선순위/보호/오류=Task 1, SRT/실제 화면=Task 2, 영상/보존 증명=Task 3.
- 인터페이스: wrap_caption/chunk_caption/write_srt 유지. 새 helper는 Task 2에서 정의하고 해당 verify가 소비한다.
- Review Focus: 5개 모두 지정 테스트에 배정했다.
- 범위: 새 서브시스템과 자동 commit/push는 없다. Native 선택을 유지하고 계획 검토 답변까지 구현을 시작하지 않는다.

## 실행 결과

Native 구현 완료. 독립 리뷰의 Important 1개를 회귀 테스트로 수정했습니다. 최종 전체 테스트 250개 중 248개 통과, 선택 실행 2개 제외. 현재 영상의 기술·화면 검증 12개 통과, 음성 의미 청취 unverified 유지. 영상은 47개 cue 중 4개 줄바꿈만 변경됐고 음성·청크 시간·7,220프레임·회로 필기를 보존했습니다. 커밋/푸시/publish/latest 변경은 하지 않았습니다.
