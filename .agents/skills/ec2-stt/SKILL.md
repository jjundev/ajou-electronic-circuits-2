---
name: ec2-stt
description: "[Gemini Only] Use when transcribing electronic circuits 2 lecture audio or video recordings (.m4a, .mp3, .wav) into a verbatim transcript under STT/<MMDD> 전회2.md with domain-specific terminology guidance for ajou-electronic-circuits-2, or when invoking /ec2-stt. Strictly requires Gemini models; fails on Claude/GPT."
---

# EC2 STT (전자회로2 강의 음성 전사)

전자회로2(권익진 교수님) 강의 녹음 음성을 Gemini 네이티브 멀티모달(`read_file`)로 축어적(verbatim) 전사하고, 당일 진도(강의 슬라이드·Razavi 교과서·기존 복습노트)의 회로 고유명사 및 발음 교정 지침을 프롬프트에 주입하여 전문용어 오인식을 최소화한 마스터 전사본을 `STT/<MMDD> 전회2.md`로 산출한다.

> [!IMPORTANT]
> **Gemini 전용 스킬**: 본 스킬은 Gemini 모델의 네이티브 비디오/오디오 멀티모달(`read_file`) 인식 기능에 전적으로 의존합니다. 비디오/오디오 바이너리 입력을 처리할 수 없는 Claude, GPT 등의 비-Gemini 모델에서는 절대 실행하지 마십시오.

---

## 🧠 핵심 원칙

0. **모델 호환성 게이트 (Model Compatibility Gate - STRICT GEMINI ONLY)**:
   - 본 스킬은 Gemini 멀티모달 모델(예: Gemini 1.5, Gemini 2.0, Gemini 2.5, Gemini 3.x)을 필수적으로 요구합니다.
   - 현재 활성화된 모델이 Gemini가 아닌 경우(예: Claude 3.5/3.7, GPT-4o, o1/o3, Llama, DeepSeek 등):
     - **어떠한 명령어(ffmpeg, read_file 등)도 실행하지 말고 즉시 중단하십시오.**
     - 사용자에게 아래 안내 메시지를 출력하고 태스크를 즉시 종료합니다:
       > ⚠️ **ec2-stt 스킬은 Gemini 모델 전용입니다.**  
       > 본 스킬은 Gemini의 네이티브 오디오 멀티모달 인식(`read_file`)을 사용하므로, 비디오/오디오 바이너리 입력을 처리할 수 없는 Claude 및 GPT 모델에서는 동작하지 않습니다.  
       > 모델 선택을 **Gemini(Gemini 2.5 / 3.0 등)**로 변경하신 후 다시 요청해 주세요.

1. **도메인 특화 어휘 주입 (Context-Aware Prior)**:
   - 파일명에서 날짜(`MMDD`)를 자동 추출하고, 당일 진도 단원의 시드 어휘, 슬라이드 제목(`강의노트/2026F_Lec*.pdf` 각 쪽 첫 줄), 교과서 절 제목(`교과서/마이크로전자회로/chNN/README.md`)을 모아 서브에이전트 프롬프트에 힌트로 주입한다.
   - 단원별 제목·시드·발음 교정 규칙은 `scripts/infer_context.py`의 `CHAPTERS` 레지스트리 한 곳에 있다 (현재 9–12장). 새 강의노트가 올라오면 이 레지스트리를 보강한다.
   - 단원 전환기: 수업 날짜가 마지막 복습노트 이후이고 더 뒤 단원의 강의노트가 이미 올라와 있으면, 두 단원(`chapters: [이전, 새]`)의 어휘와 규칙을 함께 주입한다.
   - 발음이 뭉개지거나 일상 단어로 들리기 쉬운 어휘(예: *케스코드* $\rightarrow$ *캐스코드*, *디프런셜* $\rightarrow$ *디퍼렌셜*, *지엠* $\rightarrow$ *gm*, *씨지에스* $\rightarrow$ *C_GS*, *보데* $\rightarrow$ *보드 플롯*, *에프티* $\rightarrow$ *f_T*, *루프게인* $\rightarrow$ *루프 게인*, *셴트* $\rightarrow$ *션트* 등)는 전자회로 표준 용어로 전사한다.

2. **저장소 표준 경로 및 산출물 보존**:
   - 최종 마스터 전사본은 항상 `STT/<MMDD> 전회2.md`로 생성한다 (`ec2-review-pack`이 기대하는 표준 경로).
   - 포맷은 기존 전사본 규격과 일치하게 `# <MMDD> 전회2 전체 오디오 전사본` 및 `## Part 01`, `## Part 02` 헤더 아래 문단 단위 클린 텍스트로 저장한다.

3. **네이티브 멀티모달 전사 (외부 Whisper 절대 금지)**:
   - Whisper, mlx-whisper, faster-whisper 등 외부/로컬 STT 모델을 절대 설치하거나 사용하지 않는다.
   - 오디오를 1fps 블랙 비디오 래퍼(`color=c=black:s=320x240:r=1`)가 포함된 MP4로 변환한 뒤, Gemini의 `read_file` 기능으로 직접 듣고 전사한다.

4. **150초(2.5분) 안전 세그먼트 및 1-청크 1-에이전트 원칙**:
   - **안전 필터 오탐 차단**: 5분 단위 오디오는 강의 특유의 반복 추임새("어...", "음...")와 수식 반복으로 인해 Gemini 안전 필터에 빈번히 걸린다. 따라서 기본 분할 길이는 **150초(2.5분)**를 표준으로 한다.
   - **1-청크 1-에이전트(1-Chunk-1-Agent)**: 한 에이전트에게 여러 서브청크를 체이닝하면 Thinking 토큰 오염 및 딴짓(불필요한 진단 루프)이 발생한다. **반드시 서브에이전트 1개당 청크 1개**를 배정한다.
   - **직소(Direct-to-Disk)**: 서브에이전트는 채팅창이나 Thinking에 전사 텍스트를 일체 출력하지 않고 파일 디스크 쓰기(`write_file`)로만 직소하여 챗 레이어 필터 간섭을 원천 차단한다.
   - **배치 병렬화**: 503 동시성 부하를 방지하기 위해 5개 단위 배치(Batch of 5)로 순차 기동한다.

5. **복습팩 파이프라인 연계 안내**:
   - 전사 완료 후 `/ec2-review-pack <MMDD>` 실행을 안내하여 수업 STT $\rightarrow$ 복습팩 생성이 매끄럽게 연결되도록 한다. (자동 실행하지 않고 안내만 출력)

6. **화자 분리 (선택적 - Diarization)**:
   - 전자회로2 강의는 기본적으로 교수님 1인의 독강이므로, 특별한 언급이 없으면 단일 스트림으로 전사한다.
   - 질의응답이나 발표 등으로 사용자가 화자 구분을 명시적으로 요청한 경우(`--speakers`, `-s`, "화자 구분"):
     - `라벨: 특징` 설명이 사전에 제공되어야 한다 (예: `--speakers "교수: 50대 남성 / 학생: 20대 남성"`). 설명이 없으면 전사 전 사용자에게 확인한다.
     - 매 화자 변경마다 `**라벨:** 발화내용` 형식으로 구분한다.

---

## 🛠️ Workflow A: 단일 파일 (<= 3분)

0. **모델 호환성 확인 (Gate 0)**: Gemini 모델인지 확인. 비-Gemini 모델이면 즉시 중단.
1. **컨텍스트 추출**:
   ```bash
   REPO="$(git rev-parse --show-toplevel)"
   python3 "$REPO/.agents/skills/ec2-stt/scripts/infer_context.py" "<AUDIO_PATH>" --repo "$REPO" --json > "/tmp/ec2_stt_context.json"
   ```
2. **1fps 블랙 MP4 래핑 (정확한 재생 길이 매칭)**:
   ```bash
   dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "<AUDIO_PATH>")
   ffmpeg -y -f lavfi -i color=c=black:s=320x240:r=1 -i "<AUDIO_PATH>" -t "$dur" -c:v libx264 -c:a aac -b:a 128k "/tmp/_temp_ec2_stt.mp4" -loglevel error
   ```
3. **메인 에이전트 직접 `read_file` 전사**:
   - 서브에이전트 없이 메인 에이전트가 `/tmp/_temp_ec2_stt.mp4`에 `read_file`을 호출.
   - `infer_context.py`에서 추출한 도메인 프롬프트를 컨텍스트로 두고 축어적 전사.
4. **저장 및 정리**:
   - `STT/<MMDD> 전회2.md`로 저장.
   - `rm -f "/tmp/_temp_ec2_stt.mp4"`
5. **완료 보고 및 `/ec2-review-pack <MMDD>` 안내**.

---

## ⚡ Workflow B: 긴 오디오 (> 3분) - 고속 병렬 서브에이전트

0. **모델 호환성 확인 (Gate 0)**: Gemini 모델인지 확인. 비-Gemini 모델이면 즉시 중단.
1. **날짜 및 단원 컨텍스트 추출**:
   ```bash
   REPO="$(git rev-parse --show-toplevel)"
   python3 "$REPO/.agents/skills/ec2-stt/scripts/infer_context.py" "<AUDIO_PATH>" --repo "$REPO" --json > "/tmp/ec2_stt_context.json"
   ```
   - 파일명에서 날짜를 파싱할 수 없는 경우 임의 추측하지 않고 즉시 `--date MMDD` 입력을 안내하고 중단.

2. **150초 세그먼트 분할 및 병렬 MP4 래핑 (`prepare_segments.py`)**:
   ```bash
   DATE=$(python3 -c "import json; print(json.load(open('/tmp/ec2_stt_context.json'))['date'])")
   WORK_DIR="$REPO/STT/_temp_${DATE}"
   mkdir -p "$WORK_DIR"

   python3 "$REPO/.agents/skills/ec2-stt/scripts/prepare_segments.py" "<AUDIO_PATH>" \
     --work-dir "$WORK_DIR" \
     --prefix "${DATE} 전회2" \
     --segment-seconds 150 \
     --json > "/tmp/ec2_stt_segments.json"
   ```

3. **1-청크 1-에이전트 배치 병렬 기동 (Batch of 5)**:
   - `/tmp/ec2_stt_segments.json`의 `segments` 목록을 5개씩 묶어 순차적으로 서브에이전트를 기동한다.
   - 각 서브에이전트는 **오직 1개의 청크 파일**만 담당한다.
   - **초경량 Direct-to-Disk 프롬프트**:
     ```text
     You are a verbatim STT transcription agent for Electronic Circuits 2 (전자회로2, Prof. Ikjin Kwon).
     Target video: <WORK_DIR>/<DATE> 전회2_part<NN>_temp.mp4
     Output file: <WORK_DIR>/<DATE> 전회2_part<NN>.md

     Domain terms: gm, ro, r_pi, C_GS, C_GD, C_DB, f_T, Miller, Dominant pole, Bode plot, Feedback factor K, Loop gain, Open-loop, Closed-loop, Virtual ground, Virtual short, Desensitization, Transimpedance.

     Instructions:
     1. Call `read_file` on target video.
     2. Immediately call `write_file` to save ALL spoken Korean words verbatim into the output file (Overwrite=True). Group 2~4 sentences per paragraph.
     3. Strict Guardrails:
        - Output the transcript ONLY to disk via write_file; reply ONLY with 'Done'.
        - Do NOT output transcript text in your chat response.
        - Do NOT draft or analyze transcripts in thinking tokens.
        - Do NOT run ffmpeg, ffprobe, audio slicing, or search external tools.
     ```
   - **타임스탬프 요청 시 (`--timestamps` / `-t`) 변형**:
     지침 2에 타임스탬프 형식 지정 (`MM:SS\n발화내용`).

4. **마스터 전사본 병합 및 자동 정리 (`merge_transcripts.py`)**:
   - 150초 세그먼트 2개씩 묶어 최종 MD에는 5분 단위 `## Part 01`, `## Part 02`... 헤더로 깔끔하게 병합한다.
   ```bash
   REPO="$(git rev-parse --show-toplevel)"
   DATE=$(python3 -c "import json; print(json.load(open('/tmp/ec2_stt_context.json'))['date'])")
   WORK_DIR="$REPO/STT/_temp_${DATE}"

   python3 "$REPO/.agents/skills/ec2-stt/scripts/merge_transcripts.py" \
     --dir "$WORK_DIR" \
     --prefix "${DATE} 전회2" \
     --segment-seconds 150 \
     --group-parts 2 \
     --out "$REPO/STT/${DATE} 전회2.md"
   ```
   - 타임스탬프 필요 시: `--timestamps`
   - 중간 파일 보존 필요 시: `--keep-parts`
   - 화자 분리 적용 시: `--speakers "라벨1,라벨2"`

5. **완료 보고**:
   ```text
   ✅ 전자회로2 강의 전사 완료: STT/<DATE> 전회2.md
   - 대상 수업: <DATE> (<CHAPTERS_LABEL>)
   - 회로 전문용어 힌트 적용 완료

   👉 이 전사본으로 복습팩(정리노트 + 복습문제)을 생성하려면 다음 명령을 실행하세요:
   /ec2-review-pack <DATE>
   ```

---

## 🛡️ 안전 필터(Safety Filter) 자동 복구 프로토콜

만약 특정 청크에서 서브에이전트가 안전 필터(`blocked by Gemini's filters`)로 멈출 경우:
1. **Whisper 등 외부 툴 설치 절대 금지**.
2. **해당 150초 청크를 60~75초 단위로 반분할**:
   ```bash
   ffmpeg -y -ss 0 -t 75 -i "<FAILING_CHUNK>.mp3" -c copy "<FAILING_CHUNK>a.mp3" -loglevel error
   ffmpeg -y -ss 74 -t 76 -i "<FAILING_CHUNK>.mp3" -c copy "<FAILING_CHUNK>b.mp3" -loglevel error
   ```
3. 각각 1fps 블랙 MP4로 감싼 뒤, 단일 서브에이전트로 전사하여 하나의 파트 파일로 합치고 배치를 재개한다.

---

## ✅ 완료 기준 (Completion Criteria)

- [ ] 활성 모델이 Gemini인지 확인 완료 (Gate 0 준수, Claude/GPT 차단).
- [ ] 오디오 파일명에서 날짜(`MMDD`) 정상 파싱 (실패 시 `--date` 요구).
- [ ] 150초 안전 세그먼트 및 `prepare_segments.py` 고속 병렬 MP4 래핑 완료.
- [ ] 외부/로컬 모델(Whisper 등) 사용 배제 (네이티브 `read_file` 100% 사용).
- [ ] 1-청크 1-에이전트 원칙 준수 (서브에이전트 딴짓 및 Thinking 토큰 오염 차단).
- [ ] Direct-to-Disk 파일 쓰기로 챗 레이어 안전 필터 간섭 0% 보장.
- [ ] 최종 산출물이 5분 단위 `## Part 01` 헤더 규격으로 `STT/<MMDD> 전회2.md`에 올바르게 병합 및 저장됨.
- [ ] 중간 임시 파일 자동 정리 완료.
- [ ] 후속 작업으로 `/ec2-review-pack <MMDD>` 안내 메시지 출력.
