# 검증·재개·게시

`verify`는 최종 자막본 `renders/final.mp4`를 검사한다. 마스터만 있으면 완료가 아니다. HyperFrames check와 전체 디코드, 1920×1080/30fps, 실측 WAV 샘플/해시, 최종 A/V 길이 차이 ≤1프레임을 검사한다. 자막은 Pretendard Bold FontSize14/Alignment2/MarginV14/Outline0/Shadow4/BorderStyle4, 흰 글자/약70% 검정 박스다. 문장·쉼표에서 교체하고 cue당 최대 두 줄(줄당 34자)로 표시하며 자막 중간 프레임을 마스터와 비교해 상단 PDF 침범과 하단 표시를 검사한다. 현재 source_hashes와 gate 증거 해시도 확인한다.

pencil의 `writing_animation`은 현재 composition을 실제 브라우저에서 검사한다. 모든 구간의 촉/몸통 경계·길이·순서를 확인하고 단계별 시작/중간/마스크 유지 완료, 카메라 변경, 긴 이동, 최종 hold를 캡처한다. 연필 overlay를 제외한 원본 SVG와 비교해 부분 공개의 미래 글자 누출, 마지막 마스크의 윤곽 손실, 완성 차이가 없어야 한다. 임의 seek 재현, 촉 경계 오차<=1px, 연필이 1920×900 안에 존재하고 마지막에 사라지는 것도 필수다. snapshot은 verification/writing-frames, 값·증거 해시는 verification/writing.json에 기록한다. PNG decode/해시/좌표 실패는 검사 실패이며 조용한 타이핑 대체는 없다. typing·legacy는 연필 검사를 요구하지 않는다.

자동 검사는 내용·발음·회로 의미의 승인이 아니다. 동결 PDF/MD와 완성 프레임을 대조하고 최종 영상의 발음·수식·음성 동기화를 직접 검토한다. `verification/audio-review.json`, `visual-review.json`에 `{status:passed,input_hash,notes,evidence:{relative_path:sha256}}`를 작성한다. input_hash는 `verification_fingerprint(run)`으로 구한다. audio-review의 mode는 실제 청취한 경우에만 `live-listened`다. fake PCM은 live 음성 검토로 승인하지 않는다. 실제 음성 검토가 없으면 complete=false/live_audio=unverified이며 게시하지 않는다.

상태 순서: inputs → layers → script → voice → timing → composition → render → captions → verify → publish. `resume-set`은 각 단계 입력/출력 SHA256과 사용 도구 지문으로 처음 무효 단계를 돌려준다. map 변경은 layers부터, 음성 설정은 voice부터, 작성 속도·모드·이동/hold 변경은 timing부터, 연필 길이·각도·PNG·촉 metadata 변경은 composition부터, 자막본 변조는 captions부터 재개한다. `source/manifest.json` 변경 후 검토 input_hash도 새로 작성한다. 길이·각도 변경 후 assemble은 현재 writing.json의 시각 값을 조립에 동결하며 source/timeline.json과 voice/timing 기록은 보존한다. 화면 게이트는 원문·PCM으로 재계산한 현재 설정을 기준으로 검사한다. 성공 WAV는 물리적으로 삭제하지 않는다.

게시 직전에 최종 파일/검증 지문을 다시 확인한다. 같은 파일시스템 staging, 이전버전 backup, journal로 파일과 latest를 교체한다. 이동 실패 시 이미 교체한 파일도 복구한다. 중단된 pending journal은 다음 게시 때 복구한다. 같은 제목/문항 키 충돌은 오류다. 부분 성공은 현재 검증된 파일만 게시하되 latest를 유지한다. 기존 결과는 이전버전에 남고 마스터는 run에 남는다.

개발 수용 테스트는 실제 1002 E10.11/E10.13/2021-1_중간-Q3와 로컬 PCM을 별도 scratch에서 만든다. 개발 미디어 검사 통과와 실제 Aoede 청취 통과를 분리하여 기록한다. 승인 없는 유료 테스트·가짜 audio review로 게시하지 않는다.

수용 테스트 명령 (선택 실행은 `--problems E10.11`, 생략하면 대표 3문항):

```sh
python3 .agents/skills/ec2-solution-video/tests/acceptance.py --dest /ABS/SCRATCH --hyperframes-entry /ABS/hyperframes/dist/cli.js
EC2_ACCEPTANCE_BATCH=/ABS/SCRATCH/문제풀이영상/1002/1002_제작자료/실행/RUN_ID python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v
```

기본 suite의 실제 미디어 수용 테스트는 명시적 scratch batch가 없으면 skip한다. 출력 로그의 BATCH 경로를 지정하면 selected_ids에 기록된 문항의 전체 글자 공개·미디어·최종 해시와 비용 0을 검사한다. 입력 원본과 기존 스킬 해시 보존도 검사하고 fake PCM을 production publish가 거부해야 통과한다.

검증된 Manifest.title을 실제 파일명에 사용하며 금지된 파일명 문자는 공백으로 정리한다. 게시 영수증은 실제 MP4와 catalog SHA256을 저장한다. 정상 게시 후 재개는 완료로 판정하며, 게시된 파일이 바뀌면 publish 단계부터 다시 확인한다. 명시적 카메라도 마지막 전체 답안 hold를 덮을 수 없다.

## 회로 주석 게이트

verify의 teaching_animation은 현재 sidecar/WAV로 schedule, geometry, camera를 독립 재생성하여 실제 composition과 대조한다. verification/teaching.json과 teaching-frames에는 카메라 전환 시작/중간/끝, 주석 작성·숨김, 최종 전체 화면, 역방향·GSAP seek 증거와 해시를 남긴다. 원본은 주석을 숨긴 상태로 별도 기준 SVG와 비교하고, 주석은 렌더러의 opacity/mask를 복사하지 않는 기준 화면과 비교한다.

촉 오차는 최대 1px, 기본 연필 길이는 160±0.5px, 전체 경계는 1920×900이다. 원본 필기와 주석은 한 연필을 공유하며 동시에 표시하지 않는다. typing 풀이에서도 주석 검증은 필수다. 누락·선공개·최종 잔류·촉 또는 카메라 변조는 실패한다. label 본문은 화면상 26px 이상이며 그림/주석/연필을 동시에 맞출 수 없으면 영역 ID와 이유를 보고한다.

개발 수용 검증은 tests/teaching_acceptance.py의 scratch 실행을 사용한다. E10.11/E10.13/2021-1_중간-Q3의 frozen 원자료와 fake PCM으로 렌더·자막·브라우저·미디어를 검증한다. 유료 요청은 0이다. fake PCM은 audio_meaning을 승인하지 않으며 production 게시를 통과하지 못한다. 실제 Aoede 최종 음성·주석 의미를 직접 검토한 증거가 별도로 필요하다.

Spatial pencil verification additionally requires `writing_flow` and
`narration_pacing`. Original geometry/authored bands independently define
expected order, whole-chunk fit, fixed camera, and no draw during transitions.
Evidence is in `writing-flow.json`, `flow-frames`, and `narration-pacing.json`.
Current gap review is hash-bound; changed PCM invalidates it. Audio meaning
still requires actual listening, independently of all technical checks.

## 회로 근거와 필기 음성 저작

신규 교육 흐름은 `source/lesson.json`(schema_version=1)에 PageMap 순서의 steps를 작성한다. 각 row는 step_id, mode, reason_segment_ids, check_segment_ids, region_ids, annotation_ids, meaning_notes, source_refs를 가진다. circuit 단계는 관련 회로 reason과 표시가 각각 필요하며 식을 쓰기 전에 회로 연결/가정을 설명한다. calculation 단계는 회로 목록을 비우고 exemption_reason에 제목·기존 근거의 후속 정리 등 이유를 명시한다. 단순 제목이나 계산마다 왕복하지 않는다. 기존 lesson 없는 run은 재개 가능하다.

핵심 논리마다 회로 근거 → 해당 내용 필기를 배치하고 필요한 경우 check로 돌아온다. 필기 text에는 지금 쓰는 문장/식의 읽기와 기호·항의 의미를 넣는다. 긴 원고 하나를 붙이지 말고 PageMap을 의미 단위로 분할하며 glyph/shape 중복·누락을 막는다. 필기 기본 7.5 chars/sec를 유지하고 영상 길이는 이해 우선으로 늘린다.

guided manifest의 모든 segment에 음성 `text`와 표시 `caption_text`를 별도로 작성한다. ‘알 오 원’은 음성으로 읽고 자막에는 `r_O1`을 쓴다. `r_O3`, `g_m1`, `V_BE`, `R₁`, `Q₁`, `∥` 등의 기호와 원문 대소문자를 보존하며 LaTeX 원문을 자막에 출력하지 않는다. caption_text가 없는 기존 run만 text로 fallback한다. 기호 토큰을 줄 중간에서 자르지 않으며 34자를 넘는 단일 토큰은 저작 오류다. 자막만 변경해도 후속 결과를 갱신하되 동일 text의 WAV는 TTS cache로 재사용한다.

현재 입력에 대한 lesson_flow는 회로 근거의 순서/안정 화면/표시 가시성을 검사한다. 의미 검토에서는 원문 회로, 실제 표시, 음성, 기호 자막을 함께 대조한다. 필기 음성의 2초 초과 무음은 narration_pacing 검토 대상이고 70–85% 밀도는 저작 가이드다. 카메라/픽셀 검사 통과나 synthetic PCM으로 교육 품질과 실제 음성을 승인하지 않는다.

### 문장·쉼표 자막 경계
문장 종료 온점에서 자막을 교체하고 서로 다른 문장을 한 cue에 합치지 않는다. 수식·괄호 밖 쉼표에서도 교체하며 쉼표는 앞 cue에 남긴다. 화면 내 줄바꿈은 교체와 별개이며 cue당 최대 두 줄, 줄당 34자다. 설명과 수식 경계 → 수식 밖 일반 공백 → 괄호 밖 연산 경계 순으로 줄을 나누며, 같은 우선순위 안에서만 길이 균형을 비교한다. 한 줄에 들어가는 수식은 통째로 유지하고 중첩 괄호·식별자·첨자·소수·분수(주변 공백 및 부호가 붙은 괄호 분모 포함) 내부는 끊지 않는다. 긴 수식의 연산자는 다음 항과 같은 줄에 둔다. 안전한 두 줄이 불가능하면 해당 청크의 저작 오류를 알리며 자동 축약·글자 크기 축소·cue 분할은 하지 않는다. 기존 PCM 청크 시작/종료 시간을 유지한다. 예: `저항으로 흐르는 전류는` 다음 줄에 `(I₀ + ΔI) − (I₀ − ΔI)입니다.`를 표시한다. 일반 문장은 완전한 한국어 문법 분석 없이 보수적으로 처리한다. 숫자 내부 점/쉼표, 식별자 점, 괄호/인용 내부 구두점은 보호하고 완결된 인용 문장의 닫는 따옴표는 문장과 함께 표시한다.
마지막 온점이 없는 기존 text는 표시용 온점만 추가하며 저장 원고와 음성은 바꾸지 않는다. ?, !, … 종결 및 불균형 괄호/LaTeX 원문은 저작 오류다. 두 줄에 들어가지 않는 구절과 34자 초과 원자 토큰은 check/tts 전에 segment id와 문제 구절로 알린다. 작성자가 의미상 쉼표 경계 또는 간결한 표기를 지정한다.
청크 없는 legacy SRT 시간은 실측 voice_samples 안에서 원문 의미 단위의 글자 수 비율로 배분한다. 줄바꿈과 표시용 추가 온점은 시간 가중치에 넣지 않는다. cue 사이 임의 공백은 추가하지 않으며 실제 문장·쉼표 발화 시점과의 정밀 정렬은 제공하지 않는다. 자막만 바꾸어도 기존 final/SRT 검증은 다시 수행하고 같은 음성 WAV는 cache로 재사용한다. 두 줄 자막은 실제 libass 화면에서 하단 900..1080 영역과 기호 보존을 확인한다.

두 줄 자막 배경은 libass BorderStyle4/Outline0/Shadow4로 cue 전체에 하나의 균일한 박스를 그린다. 줄별 박스를 겹치는 BorderStyle3은 사용하지 않는다. 실제 두 줄·서로 다른 줄 길이에서 박스 가장자리와 불투명도 균일성 및 기호·글자 가독성을 확인한다.

## 렌더 작업자 설정

신규 RUN은 `workers: "auto"`로 파트별 캡처 작업자 수를 선택한다. 현재 검증된 Darwin / Apple M5 / 물리 CPU 10코어 / 16GiB 이상에서는 30초 이상 파트의 움직임 비율이 50%를 넘으면 6개, 그 외에는 2개다. 다른 호스트·탐지 실패·누락된 움직임 메타데이터에서도 2개를 사용한다. CPU 인코딩과 브라우저 GPU auto를 유지하고 실험적 고속 캡처는 명시적으로 끈다. 파트와 문항은 한 번에 하나씩 순차 렌더한다.

움직임 비율은 실제 HTML에 동결된 타임라인과 인접 timeline.json을 대조하여 계산한다. 연필 필기·이동, 회로 주석 작성·이동, 카메라 전환 시간을 겹침 없이 합산한다. 타이핑은 write 구간 시작부터 마지막 글자 공개까지를 작성 시간으로 계산한다. 설명·완성 hold와 주석 공백은 제외하며 순간 공개·카메라 변경은 한 프레임으로 센다. 화면 픽셀 분석이나 모든 문항에서 최단 시간을 보장하는 최적화는 아니다. 현재 조립기는 문항 전체를 하나의 파트로 만들므로 일반 실행은 문항 전체의 비율로 선택한다.

`source/render-options.json`은 음성 config와 별도인 schema_version=2 정책이다. `render --render-workers auto|1..6`이 최우선이고 schema2의 숫자는 호스트가 바뀌어도 수동 고정값으로 유지한다. schema1의 숫자는 당시 자동 기본값과 수동값을 구별하지 않았으므로 읽을 때 auto로 전환한다. 수동 고정이 필요하면 CLI 숫자를 다시 지정한다. 손상된 저장 정책은 override로 숨기지 않고 오류를 낸다. auto 모드에서는 존재하는 타임라인의 손상·불일치를 누락 fallback으로 숨기지 않는다. 숫자 고정값은 움직임 분석을 생략한다. `resume-set`과 분석은 파일을 추가·수정하지 않는다. 렌더 요청 시만 정책을 저장하며 변경은 render부터 재개한다. WAV·대본·타임라인은 그대로 사용한다.

```sh
python3 .agents/skills/ec2-solution-video/scripts/video.py render --run /ABS/RUN --hyperframes-entry /ABS/hyperframes/dist/cli.js --render-workers auto
# 수동 고정이나 메모리 압박이 있으면 같은 명령의 값을 4 또는 2로 낮춰 직접 재시도한다.
```

선택 후 실패했다고 다른 인코더나 작업자 수로 자동 재시도하지 않는다. 실패한 임시 출력은 제거하고 로그를 남긴다. 규격 검사를 통과한 파트만 교체하며 이전 마스터와 렌더 영수증은 실패 시 복구한다. `verification/render-receipt.json`에 실제 명령, workers 선택 이유·움직임 비율, 경과 시간, 프레임 수와 출력 해시를 남긴다. 자막과 기존 최종 검토·게시 절차는 그대로 수행한다.

### 2026-10-10 생산 렌더러 수용 검증

동결 P10.72(7,220프레임)를 production render_master로 각각 2/6개 작업자에서 렌더했다. 사전 check와 마스터 생성 포함 263.67→155.39초(41.1% 감소), 파트 렌더·규격 검사는 200.18→105.07초(47.5% 감소)다. 두 마스터 SHA256, 전체 프레임·PCM·AAC가 동일하고 동결 파일 86개는 불변이다. CLI 0.8.137/FFmpeg 9.0.2/현재 M5에서 각 설정 1회 재확인한 결과다. 최종 suite는 209개/3개 opt-in skip/실패 0, media 15/15, Node 5/5와 별도 실제 성능 수용 3/3 통과. 음성 청취·교육 의미 승인이나 게시를 뜻하지 않는다.

실제 수용검사는 EC2_RENDER_ACCEPTANCE=1, EC2_RENDER_FIXTURE(원본 또는 해시 일치 동결 RUN), EC2_RENDER_ACCEPTANCE_DEST(원본 외부의 새 폴더), EC2_HYPERFRAMES_ENTRY(검증된 로컬 CLI)를 지정하고 tests/test_render_performance_acceptance.py를 unittest discover로 실행한다. EC2_FFMPEG와 HYPERFRAMES_FFMPEG_PATH도 같은 검증된 FFmpeg에 고정한다. 미지정은 명시적으로 skip, 명시 실행의 누락 입력/다른 프레임 수는 실패다. 원본 승인/상태 영수증은 복사하지 않으며 유료 호출·게시를 금지한다.

마스터/영수증 교체 도중 Ctrl+C도 이전 쌍으로 복구한다. 복구 자체가 실패하면 `.rollback` 사본을 보존하고 오류에 경로를 남기며, 남은 사본을 덮어쓰는 재시도는 차단한다. 해당 사본과 오류 로그를 확인해 이전 마스터/영수증을 복원한 다음 재시도한다. 사본을 무조건 삭제해 오류를 숨기지 않는다.

### 자동 작업자 수용 검증

`tests/auto_workers_acceptance.py`는 기존 P10.72의 동결 composition·narration.wav를 읽어 정지 화면 구간 0–900프레임과 필기 구간 6269–7169프레임을 각각 30초씩 렌더한다. 원본 PDF 윤곽·글로벌 타임라인은 보존하고 시험용 GSAP 시계만 해당 구간으로 제한한다. 각각 고정2·고정6·auto를 실제 render_master에서 실행하고 모든 프레임·PCM·AAC와 마스터 SHA256을 비교한다. 혼합60초의 auto [2,6]도 고정 기준본을 독립 mux한 결과와 대조한다. 실제 입력과 원본 전체 파일 해시를 전후 비교하며 수용 폴더는 원본 밖의 새 경로여야 한다.

```sh
PATH=/opt/homebrew/opt/ffmpeg-full/bin:$PATH \
EC2_FFMPEG=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg \
HYPERFRAMES_FFMPEG_PATH=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg \
python3 .agents/skills/ec2-solution-video/tests/auto_workers_acceptance.py \
  --fixture /ABS/FROZEN_P1072_RUN \
  --destination /ABS/NEW_ACCEPTANCE_FOLDER \
  --hyperframes-entry /ABS/hyperframes/dist/cli.js
```

시험은 기존 PCM을 재사용하며 유료 TTS·production publish를 금지한다. 자막을 제한된 구간에 다시 배분한 시험본은 원본 발화 경계의 정밀 정렬이나 새 교육·음성 의미 승인을 증명하지 않는다. 시간은 현재 부하에서 각 설정 한 번의 관측치이며 메타데이터 기반 50% 기준의 보편적인 속도 우위를 증명하지 않는다.

`tests/auto_workers_browser_check.mjs`는 원본 전체 시계와 시험 구간 시계의 프레임·카메라 및 역방향 seek PNG를 소프트웨어 Chrome(`--disable-gpu`)으로 엄격 비교한다. GPU 기본 Chrome의 보조 탭 비교에서 정적 색상 24픽셀의 파랑 채널 차이 1이 관측되어 보조 화면 검사의 백엔드를 고정했다. 이는 생산 렌더의 브라우저 GPU auto/Metal과 별개다. 실제 인코딩 영상의 작업자별 전체 프레임·PCM·AAC 동일성은 GPU auto에서 검사하며 PNG 허용오차를 늘리지 않는다. 실행 백엔드·Chrome 경로와 비교 결과는 browser.json에 기록한다.

## 대본 전용 TTS와 실측 청크 자막

문제풀이 TTS는 `spoken-text-only-v1` 정책으로 읽을 대본만 텍스트 입력에 넣는다. direction·“원고:”·자막 표시 문구를 전송하지 않는다. Aoede·ko-KR·모델·출력 형식은 설정 필드로 전달하며 공용 review-video의 요청 방식은 바꾸지 않는다. 기존 direction을 읽은 WAV는 새 요청 캐시와 호환되지 않는다.

신규 manifest에는 `caption_timing: "pcm-chunks-v1"`을 넣고 모든 segment 내부에 `{id,text,caption_text}` 청크를 작성한다. 각 caption_text는 기존 문장/쉼표 규칙의 cue 하나이며 최대 두 줄/줄당 34자다. 수식·분수·괄호 내부는 보존한다. 부모 text/caption_text는 각각 청크의 공백 연결과 같아야 한다. 현재 P10.72의 47개 cue가 저작 출발점이다. 일부 청크가 빠진 새 모드는 자동 legacy fallback하지 않는다.

청크 WAV는 `source/chunk-audio.json`에 영수증을 저장하고 raw PCM으로 segment WAV에 연결한다. 자막은 실측 누적 샘플 위치를 사용하며 글자 수로 배분하지 않는다. SRT 반올림 오차는 1ms 이하, 30fps 영상의 표시 경계는 1프레임 이내다. 단어 내부 시점 정렬을 주장하지 않는다. 연결 사이에 임의 무음을 넣지 않고 segment의 필기 hold에 자막을 늘리지 않는다.

기본은 원본 청크 전체를 사용한다. 긴 앞뒤 무음은 실제 확인한 경우에만 `source/chunk-trims.json`에 schema_version=1 및 rows의 segment_id/chunk_id/raw_sha256/start_sample/end_sample/reason을 작성한다. 음성 생성 명령을 재실행하면 성공 청크 캐시를 재사용하며 새 절단본을 연결한다. 원본 WAV는 보존하고 자동 에너지 절단을 하지 않는다. 절단이 바뀐 연결 WAV를 retime이 검사 없이 사용해서는 안 된다.

`verification/chunk-sync.json`은 원본/연결 PCM·타임라인·SRT의 대응을 검사한다. 실제 의미 검토는 별도다. 청크 모드 audio-review의 mode는 실제 청취 후에만 live-listened이고, 전 청크 순서의 chunk_checks에 segment_id/chunk_id/transcript_match/no_instruction_speech/natural_join/sync_passed/notes를 기록한다. 네 boolean이 모두 true여야 한다. 지침·추가 발화·누락·잘못된 발음·부자연스러운 연결부·최종 MP4의 전환을 검토한다. 청취할 수 없으면 complete=false/live_audio=unverified 상태로 검토용 영상을 전달하고 publish/latest는 갱신하지 않는다.

### 도형 작성 시간과 필기 지연
spatial pencil은 원본 도형별 전체 가로 폭 W와 대표 글자 높이 H로 min(90, max(18, ceil(W/H × 글자 간격 프레임))) draw 예산을 정한 뒤 clip 폭에 비례해 배분한다. 조각마다 최소 1프레임, 합계는 전체 예산이며 조각 수가 예산보다 많으면 저작 오류다. 새 줄 들어 옮기기는 첫 대상에 한 번 적용한다. 음성 종료 후 필기 지연이 60프레임(2초)을 초과하면 별도 검토한다. narration-pacing의 voice_end_frame/writing_end_frame/writing_lag_frames/completed_hold_frames를 확인하고 필기 중 무음을 완성 화면 읽기로 기록하지 않는다. 예외는 현재 input_hash의 pacing-review writing_lags [{segment_id,voice_end_frame,writing_end_frame,reason}]로 명시한다. 기존 gaps 이유는 필기 지연을 승인하지 않으며 실제 청취/의미 검토를 대신하지 않는다.

글자 없는 도형 전용 chunk는 페이지 전체와 연필 여백이 들어오는 구도를 사용한다. 해당 구간의 검증은 페이지 맥락/도형/연필 경계로 수행하고 글자 chunk의 26px 최소 크기는 유지한다.

### 발화에 맞춘 회로 필기
같은 타원 반복으로 회로 설명을 대신하지 않고, 연결·방향·변화량을 해당 발화에 표시한다. 짧은 기호와 화살표를 원본 선·소자 이름 밖에 배치한다. 감소량 −ΔI는 전류 방향 반전으로 표시하지 않는다.
도형별 `stroke_width_px`는 유한한 숫자 2~12px(생략값3px)를 지원한다. 신규 저작은 보조4px·전류6px·강조8px를 사용한다. label에는 굵기 대신 runs의 font_size_pt를 지정한다. 파랑 #1565C0 연결·비율, 주황 #C45100 유입 전류, 초록 #237A43 분기 전류, 자주 #8E348E 결과의 역할로 쓰고 기호·위치로도 구분한다. P10.72에서는 각각 M3/M4 관계·M4 유입·I2·RL 결과에 대응한다.
`chunk_id`는 해당 reason/check segment의 실제 음성 청크를 참조한다. 청크 모드 offset_frames는 청크 시작 기준 정수>=0(기본0)이며 같은 segment에서 legacy offset과 혼합하지 않는다. 서로 다른 청크의 같은 offset은 허용한다. move8프레임과 필기 전체가 ceil(start_sample/800) 이후, floor(end_sample/800) 및 카메라 복귀 직전(segment end−13) 이내여야 한다. 넘치면 표시/label을 간소화하고 무음을 늘리지 않는다. legacy segment 기준 오프셋과 최소길이 보정은 유지한다.
설명 중 표시는 누적하고 다음 풀이에 복귀할 때 hide_at으로 정리하며 최종 원본에는 숨긴다. 굵은 선의 반경·화살촉·펜 여백과 label26px를 확인한다. 각 청크의 작성중/완료 프레임과 원문을 대조해 방향·부호·가림을 검토한다. 기술검사만으로 음성 청취를 승인하지 않으며 미청취는 live_audio=unverified/complete=false로 전달한다.

주석이 많으면 glyph·역방향/GSAP seek·독립 화면 오라클로 검증 시간이 늘어난다. verify의 teaching browser만600초를 허용하며 시간 단축을 위해 probe를 생략하지 않는다. 다른 browser의 기본 제한은 유지한다.

원본 SVG 게이트는 setContent·공개 상태 변경 뒤 두 requestAnimationFrame을 기다려 화면 갱신을 마친 후 캡처한다. 픽셀 차이·영역 밖 차이·선공개 기준은 정확한0을 유지하고, 비동기 중간 화면 때문에 기준을 완화하지 않는다.

정적 원본 SVG 게이트에만 --disable-gpu를 적용해 동일한 정적 비교 조건을 사용한다. 영상 렌더·필기·회로·inventory 검사의 렌더 방식은 바꾸지 않는다. 동일 SVG 반복 검사에서도 정확한0을 요구한다.

### 자막 줄바꿈 검증
생성한 SRT의 cue 번호·전체 텍스트·개행·실측 PCM 시간은 현재 timeline으로 생성한 기대 SRT와 일치해야 한다. 글자/줄바꿈/시간 변조는 captions gate에서 거부한다. libass에는 `WrapStyle=2`를 적용해 지정한 줄바꿈을 유지하며, 실제 한 줄/두 줄 렌더에서 하단 900..1080 영역과 수식 보존을 확인한다. 자막만 바꾸면 WAV와 청크 시작/종료 시간을 유지하고 새 final/SRT 검증을 수행한다. 이 검증은 음성 의미 청취를 대체하지 않으며 기존 unverified를 passed로 변경하지 않는다.
